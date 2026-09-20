"""Le mode greffon : l'agent écrit dans le logiciel du commerçant, pas chez lui.

C'est la moitié de la promesse du produit — « un greffon, pas une île ». Le
connecteur existait, testé et documenté, et **n'était branché nulle part** : le
service écrivait toujours dans sa propre base. Un module non branché ne sert à
rien, c'est la quatrième fois que ce dépôt s'y fait prendre.
"""

import json
import os
from datetime import date

import pytest

from standard.connecteur import BaseViaConnecteur, ConnecteurHttp, Indisponible
from standard.demarrage import construire_serveur
from standard.depot import ChevauchementRefuse

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARDI = date(2026, 9, 15)


class HoteFactice:
    """Un logiciel hôte, réduit à ce que le contrat exige."""

    def __init__(self, libres=("09:00", "15:30"), statut_reservation=201):
        self.libres = list(libres)
        self.statut_reservation = statut_reservation
        self.recu = []
        self.lignes = {}

    def __call__(self, methode, url, corps=None, entetes=None, delai=None):
        self.recu.append((methode, url, corps))
        if "/disponibilites" in url:
            return 200, {"creneaux": self.libres}
        if methode == "POST":
            if self.statut_reservation != 201:
                return self.statut_reservation, {"detail": "refusé"}
            reference = f"hote-{len(self.lignes) + 1}"
            self.lignes[reference] = dict(corps or {})
            return 201, {"reference": reference}
        reference = url.rsplit("/", 1)[-1]
        return (200, self.lignes[reference]) if reference in self.lignes else (404, {})


def base(hote):
    return BaseViaConnecteur(ConnecteurHttp(hote, base="https://hote.exemple.fr",
                                            cle_api="secret"))


# --- l'adaptateur -----------------------------------------------------------

def test_une_reservation_part_chez_l_hote_et_se_relit(tmp_path):
    hote = HoteFactice()
    adaptee = base(hote)
    reference = adaptee.inserer("cle-1", {"date": "2026-09-17", "heure": "15:30",
                                          "nom": "Dupont"})
    assert adaptee.relire(reference)["nom"] == "Dupont"
    assert any(methode == "POST" for methode, _, _ in hote.recu)


def test_un_creneau_refuse_par_l_hote_devient_un_chevauchement():
    """409 veut dire « pris ». L'agent doit proposer autre chose, pas annoncer
    une panne."""
    adaptee = base(HoteFactice(statut_reservation=409))
    with pytest.raises(ChevauchementRefuse):
        adaptee.inserer("cle-1", {"date": "2026-09-17", "heure": "15:30"})


def test_un_hote_qui_tousse_n_est_jamais_lu_comme_un_refus():
    """Un 500 n'est pas un « non » : dire « c'est pris » parce que le serveur
    de l'hôte tousse, c'est mentir au client avec aplomb."""
    adaptee = base(HoteFactice(statut_reservation=500))
    with pytest.raises(Indisponible):
        adaptee.inserer("cle-1", {"date": "2026-09-17", "heure": "15:30"})


def test_les_disponibilites_viennent_de_l_hote():
    adaptee = base(HoteFactice(libres=("10:30",)))
    assert adaptee.libres_du_jour("2026-09-17") == ["10:30"]


# --- le branchement ---------------------------------------------------------

def test_le_serveur_branche_l_hote_quand_il_est_configure(tmp_path, monkeypatch):
    """Sans ce branchement, `STANDARD_HOTE_BASE` ne servait à rien et le
    commerçant voyait ses rendez-vous rester dans une base parallèle."""
    serveur = construire_serveur({
        "STANDARD_TENANT": "salon-1",
        "STANDARD_PACK": os.path.join(RACINE, "packs", "coiffure.json"),
        "STANDARD_REPONSES": '{"A1": "Salon Elegance"}',
        "STANDARD_PORT": "0", "STANDARD_PORT_SANTE": "0",
        "STANDARD_BASE": str(tmp_path / "essai.sqlite3"),
        "STANDARD_HOTE_BASE": "https://hote.exemple.fr",
        "STANDARD_HOTE_CLE": "secret",
        "STANDARD_STT": "muet", "STANDARD_TTS": "muet",
    })
    assert isinstance(serveur.service.base, BaseViaConnecteur)


def test_sans_hote_le_service_ecrit_chez_lui(tmp_path):
    serveur = construire_serveur({
        "STANDARD_TENANT": "salon-1",
        "STANDARD_PACK": os.path.join(RACINE, "packs", "coiffure.json"),
        "STANDARD_REPONSES": '{"A1": "Salon Elegance"}',
        "STANDARD_PORT": "0", "STANDARD_PORT_SANTE": "0",
        "STANDARD_BASE": str(tmp_path / "essai.sqlite3"),
        "STANDARD_STT": "muet", "STANDARD_TTS": "muet",
    })
    assert not isinstance(serveur.service.base, BaseViaConnecteur)


# --- ce que l'appelant entend quand l'hôte ne répond pas --------------------

def test_un_hote_muet_ne_fait_jamais_promettre(tmp_path):
    from standard.appel import Appel
    from standard.decision import Agenda
    from standard.hors_ligne import ModeleHorsLigne

    appel = Appel(client_modele=ModeleHorsLigne(aujourd_hui=MARDI),
                  agenda=Agenda(aujourd_hui=MARDI, creneaux={"15:30"}, jours_fermes=(6, 0)),
                  base=base(HoteFactice(statut_reservation=503)),
                  memoire="", consignes_communes="c",
                  tenant="salon-1", identifiant="appel-1")
    appel.fiche = {"reservation": {"nom": "non"}}
    appel.tour("je voudrais un rendez-vous jeudi à quinze heures trente")
    reponse = appel.confirmer()
    assert reponse.genre == "incertain"
    # La phrase d'incertitude contient le mot « enregistré » dans une négation ;
    # ce qu'on vérifie, c'est qu'elle n'AFFIRME rien — la règle du produit.
    assert "n'arrive pas à vérifier" in reponse.phrase
    assert "rappellera" in reponse.phrase


# --- ce qui reste quand l'écriture n'a pas abouti ---------------------------
# L'agent dit honnêtement « le salon vous rappellera ». Encore faut-il que le
# salon SACHE qu'il doit rappeler : sinon la phrase est une promesse en l'air.

def test_une_ecriture_incertaine_laisse_une_trace_a_rattraper(tmp_path):
    from standard.appel import Appel
    from standard.decision import Agenda
    from standard.depot import Depot
    from standard.hors_ligne import ModeleHorsLigne

    local = Depot(str(tmp_path / "essai.sqlite3"))
    appel = Appel(client_modele=ModeleHorsLigne(aujourd_hui=MARDI),
                  agenda=Agenda(aujourd_hui=MARDI, creneaux={"15:30"}, jours_fermes=(6, 0)),
                  base=base(HoteFactice(statut_reservation=503)),
                  memoire="", consignes_communes="c",
                  tenant="salon-1", identifiant="appel-1",
                  secours=local.pour("salon-1"))
    appel.fiche = {"reservation": {"nom": "non"}}
    appel.tour("je voudrais un rendez-vous jeudi à quinze heures trente")
    reponse = appel.confirmer()

    assert reponse.genre == "incertain"
    a_rattraper = local.messages("salon-1")
    assert len(a_rattraper) == 1
    assert "17 septembre" in a_rattraper[0]["texte"]
    assert a_rattraper[0]["type"] == "rendez_vous_a_rattraper"


def test_sans_secours_l_appel_se_termine_quand_meme(tmp_path):
    """Le rattrapage est un filet, pas une dépendance : sans dépôt local, la
    phrase honnête reste dite."""
    from standard.appel import Appel
    from standard.decision import Agenda
    from standard.hors_ligne import ModeleHorsLigne

    appel = Appel(client_modele=ModeleHorsLigne(aujourd_hui=MARDI),
                  agenda=Agenda(aujourd_hui=MARDI, creneaux={"15:30"}, jours_fermes=(6, 0)),
                  base=base(HoteFactice(statut_reservation=503)),
                  memoire="", consignes_communes="c",
                  tenant="salon-1", identifiant="appel-1")
    appel.fiche = {"reservation": {"nom": "non"}}
    appel.tour("je voudrais un rendez-vous jeudi à quinze heures trente")
    assert appel.confirmer().genre == "incertain"


def test_le_service_pose_toujours_le_filet_local(tmp_path):
    """Même branché sur un hôte, le service garde un dépôt local pour ce qui
    n'a pas abouti : sinon la trace se perdrait avec la panne qui l'a causée."""
    serveur = construire_serveur({
        "STANDARD_TENANT": "salon-1",
        "STANDARD_PACK": os.path.join(RACINE, "packs", "coiffure.json"),
        "STANDARD_REPONSES": '{"A1": "Salon Elegance"}',
        "STANDARD_PORT": "0", "STANDARD_PORT_SANTE": "0",
        "STANDARD_BASE": str(tmp_path / "essai.sqlite3"),
        "STANDARD_HOTE_BASE": "https://hote.exemple.fr",
        "STANDARD_STT": "muet", "STANDARD_TTS": "muet",
    })
    assert serveur.service.secours is not None
    assert hasattr(serveur.service.secours, "enregistrer_message")


# --- la taxonomie réelle de Crenolo (session marpeap-ea, 21/09) -------------
# Quinze refus possibles, dans l'ordre où ils tombent, documentés en tête de
# `api/services/reservation.py`. Ce qui compte pour l'agent n'est pas leur
# nombre : c'est de ne jamais confondre un refus définitif, un refus qu'on peut
# contourner, et une indisponibilité.

@pytest.mark.parametrize("statut, detail, attendu", [
    (409, "Time slot no longer available", "creneau_pris"),
    (422, "Horaires", "donnees_refusees"),
    (404, "Service inconnu", "inconnu"),
    (403, "Facturation fermée", "acces_refuse"),
    (429, "3 réservations actives", "trop_de_reservations"),
])
def test_chaque_refus_de_crenolo_a_son_sens(statut, detail, attendu):
    from standard.connecteur import CODES_DE_REFUS, Refus

    assert CODES_DE_REFUS[statut] == attendu

    adaptee = base(HoteFactice(statut_reservation=statut))
    # Le créneau pris traverse l'adaptateur sous le nom que l'agent sait dire :
    # c'est le seul refus qu'il contourne en proposant autre chose.
    attendue = ChevauchementRefuse if attendu == "creneau_pris" else Refus
    with pytest.raises(attendue) as refus:
        adaptee.inserer("cle-1", {"date": "2026-09-17", "heure": "15:30"})
    if attendue is Refus:
        assert refus.value.code == attendu


def test_un_plafond_de_reservations_n_est_pas_un_creneau_pris():
    """429 : le client a déjà trois rendez-vous en attente. Lui proposer un
    autre créneau ne servirait à rien — c'est lui qu'il faut renvoyer au salon."""
    from standard.connecteur import Refus

    adaptee = base(HoteFactice(statut_reservation=429))
    with pytest.raises(Refus) as refus:
        adaptee.inserer("cle-1", {"date": "2026-09-17", "heure": "15:30"})
    assert refus.value.code != "creneau_pris"


def test_ce_que_l_appelant_entend_pour_chaque_refus(tmp_path):
    """Un code HTTP ne se dit pas au téléphone. Chaque refus a sa phrase, et
    aucune ne prétend que le rendez-vous existe."""
    from standard.connecteur import phrase_de_refus

    for code in ("creneau_pris", "donnees_refusees", "acces_refuse", "inconnu",
                 "trop_de_reservations"):
        phrase = phrase_de_refus(code)
        assert phrase and phrase[0].isupper(), code
        assert "erreur" not in phrase.lower(), code
        assert "http" not in phrase.lower(), code


def test_un_salon_qui_refuse_l_annulation_par_telephone_le_dit(tmp_path):
    """`self_cancellation` est à False chez Nail Beauté Nguyen : l'API rend un
    403. L'agent ne doit pas dire « c'est annulé », ni faire répéter."""
    from standard.appel import Appel
    from standard.decision import Agenda
    from standard.depot import Depot
    from standard.hors_ligne import ModeleHorsLigne

    class HoteQuiRefuseL_Annulation(HoteFactice):
        def __call__(self, methode, url, corps=None, entetes=None, delai=None):
            if "/annulation" in url or methode == "DELETE":
                return 403, {"detail": "Annulation en ligne désactivée"}
            return super().__call__(methode, url, corps, entetes, delai)

    depot = Depot(str(tmp_path / "essai.sqlite3"))
    depot.pour("salon-1").inserer("cle-1", {"date": "2026-09-17", "heure": "15:30",
                                            "telephone": "0612345678"})
    adaptee = depot.pour("salon-1")
    adaptee.annuler = lambda reference: False

    appel = Appel(client_modele=ModeleHorsLigne(aujourd_hui=MARDI),
                  agenda=Agenda(aujourd_hui=MARDI, creneaux={"15:30"}, jours_fermes=(6, 0)),
                  base=adaptee, memoire="", consignes_communes="c",
                  tenant="salon-1", identifiant="appel-1")
    appel.fiche = {"reservation": {"nom": "non"}}
    appel.etat.connu["telephone"] = "0612345678"
    appel.tour("je voudrais annuler mon rendez-vous")
    phrase = appel.tour("oui c'est bien ça").phrase
    assert "annulé" not in phrase.lower() or "n'arrive pas" in phrase.lower()
    # Pas de « le salon vous rappellera » ici : c'est une promesse faite au nom
    # du salon, et rien ne la garantit. Pour une annulation ratée, on passe la
    # main tout de suite — le client est au téléphone, autant en profiter.
    assert "passe" in phrase.lower()
