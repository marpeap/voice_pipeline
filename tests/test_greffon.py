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
