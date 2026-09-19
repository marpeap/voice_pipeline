"""Le service : ce qui demarre, ce qui refuse de demarrer, et ce qu'il sait dire.

Trois choses sont verifiees ici, et chacune vient d'une mesure ou d'une regle
ecrite : la reserve de connexions est amorcee AVANT le premier appel (mesure 4),
un agent dont les questions critiques sont vides ne s'active pas (docs/05), et la
supervision expose les trois chiffres qui disent si le service va bien.
"""

import json
from datetime import date
from pathlib import Path

import pytest

from standard.service import Configuration, Service

PACKS = Path(__file__).resolve().parents[1] / "packs"


class ModeleFactice:
    def __init__(self):
        self.appels = 0

    def completer(self, messages, **parametres):
        self.appels += 1
        return json.dumps({"intention": "rdv", "date": "2026-09-17", "heure": "15:30",
                           "prestation": None, "manque": [],
                           "confiance": {"intention": 0.95, "date": 0.95, "heure": 0.95}})


class BaseFactice:
    def __init__(self):
        self.lignes, self.par_cle = {}, {}

    def inserer(self, cle, donnees):
        if cle in self.par_cle:
            return self.par_cle[cle]
        reference = f"rdv-{len(self.lignes) + 1:04d}"
        self.lignes[reference] = dict(donnees)
        self.par_cle[cle] = reference
        return reference

    def relire(self, reference):
        return self.lignes.get(reference)


def configuration(**remplacements):
    base = {
        "tenant": "salon-1",
        "pack": str(PACKS / "coiffure.json"),
        "reponses": {"A1": "Salon Elegance"},
        "corps": "# Particularites\nRien de special.\n",
        "modele": "un-modele", "parametres": {"temperature": 0.0},
        "aujourd_hui": "2026-09-15", "horizon_jours": 14,
        "creneaux": ["09:00", "10:30", "14:00", "15:30", "17:00"],
        "jours_fermes": [6, 0],
        "connexions": 3,
    }
    base.update(remplacements)
    return Configuration.depuis(base)


def service(**remplacements):
    ouvertures = []
    s = Service(configuration(**remplacements),
                client_modele=ModeleFactice(), base=BaseFactice(),
                fabrique_connexion=lambda: ouvertures.append(1) or object())
    s.ouvertures = ouvertures
    return s


# --- la configuration ne se devine pas --------------------------------------

def test_la_configuration_vient_du_dehors():
    config = configuration()
    assert config.modele == "un-modele"
    assert config.aujourd_hui == date(2026, 9, 15)
    assert config.tenant == "salon-1"


def test_les_seuils_ont_les_valeurs_mesurees_sauf_si_on_les_change():
    from standard import regles
    assert configuration().seuil_bruite_db == regles.SEUIL_BRUITE_DB
    assert configuration(seuil_bruite_db=20).seuil_bruite_db == 20


def test_une_configuration_sans_pack_est_refusee():
    with pytest.raises(ValueError, match="pack"):
        Configuration.depuis({"tenant": "x"})


# --- le demarrage -----------------------------------------------------------

def test_aucune_connexion_n_est_ouverte_a_l_arrivee_d_un_appel():
    """Mesure 4 : une connexion rouverte coûte 2 040 ms, gardée 378 ms.

    Ce test vérifiait auparavant qu'une « réserve » fabriquait quatre objets au
    démarrage. C'était une garantie en trompe-l'œil : personne n'empruntait ces
    objets, et le vrai trafic ouvrait une connexion neuve à chaque tour. Ce qui
    compte est ici : prendre un appel n'ouvre rien.
    """
    class ClientQuiCompte(ModeleFactice):
        def __init__(self):
            super().__init__()
            self.ouvertures = 0

        def amorcer(self):
            self.ouvertures += 1

    client = ClientQuiCompte()
    s = Service(configuration(), client_modele=client, base=BaseFactice())
    s.demarrer()
    avant = client.ouvertures
    s.nouvel_appel("appel-1")
    s.nouvel_appel("appel-2")
    assert client.ouvertures == avant, "prendre un appel a ouvert une connexion"


def test_un_agent_incomplet_ne_s_active_pas():
    """docs/05 : les questions critiques sont celles dont l'absence produit une
    erreur ENTENDUE PAR LE CLIENT. Tant qu'il en manque, l'agent ne decroche pas."""
    s = service(reponses={})
    with pytest.raises(RuntimeError) as erreur:
        s.demarrer()
    assert "A1" in str(erreur.value)


def test_le_demarrage_dit_ce_qui_manque_plutot_que_d_echouer_sechement():
    s = service(reponses={})
    assert "A1" in s.questions_manquantes()


# --- l'annonce, non negociable ----------------------------------------------

def test_la_premiere_phrase_annonce_l_agent_automatique():
    """AI Act art. 50 §1, et mesure 19 : l'annonce survit au canal. Elle est dans
    la premiere phrase, pas au milieu de la conversation."""
    s = service()
    s.demarrer()
    appel = s.nouvel_appel("appel-1")
    assert "automatique" in appel.salutation().lower()


def test_l_annonce_suit_la_formulation_choisie_par_le_salon():
    s = service(reponses={"A1": "Salon Elegance", "E3": "assistant_virtuel"})
    s.demarrer()
    assert "virtuel" in s.nouvel_appel("a").salutation().lower()


# --- la supervision ---------------------------------------------------------

def test_la_supervision_expose_les_trois_chiffres_qui_comptent():
    s = service()
    s.demarrer()
    appel = s.nouvel_appel("appel-1")
    appel.tour("JE VOUDRAIS JEUDI A QUINZE HEURES TRENTE")
    appel.confirmer()
    etat = s.supervision()
    assert etat["confirmations_orphelines"] == 0
    assert etat["appels"] == 1
    assert "part_bruitee_pct" in etat


def test_les_appels_bruites_sont_comptes():
    """Mesure 10 : sans le rapport signal/bruit au journal, « l'agent comprend
    mal » n'est pas diagnosticable."""
    s = service()
    s.demarrer()
    appel = s.nouvel_appel("appel-1")
    appel.tour("JEUDI QUINZE HEURES TRENTE", bruite=True)
    assert s.supervision()["part_bruitee_pct"] == 100.0


def test_chaque_appel_a_son_etat_a_lui():
    s = service()
    s.demarrer()
    premier, second = s.nouvel_appel("a1"), s.nouvel_appel("a2")
    premier.tour("JEUDI QUINZE HEURES TRENTE")
    assert second.etat.connu == {}, "deux appels partagent leur etat"


def test_deux_confirmations_orphelines_distinctes_comptent_pour_deux():
    """Relevé par la revue du 19/09 : `absorber` faisait un `max()`, donc deux
    incidents dans deux appels différents comptaient pour un. Sur un indicateur
    dont la cible est zéro, c'est la différence entre « un incident » et « un
    incident par appel »."""
    from standard.service import Supervision

    supervision = Supervision()
    supervision.absorber(1)
    supervision.absorber(1)
    assert supervision.etat()["confirmations_orphelines"] == 2


def test_un_meme_incident_n_est_compte_qu_une_fois():
    """L'appelant transmet l'écart, pas le total : sinon le même incident
    compterait à chaque tour suivant."""
    from standard.service import Supervision

    supervision = Supervision()
    supervision.absorber(1)
    supervision.absorber(0)
    assert supervision.etat()["confirmations_orphelines"] == 1


# --- ce que le service doit transmettre à la session -------------------------

def test_l_appel_suivi_expose_le_clavier():
    """Seconde revue (19/09) : la session cherchait `basculer_clavier` sur
    l'agent — mais l'agent réel est `AppelSuivi`, qui ne l'exposait pas. Le
    `hasattr` échouait en silence, et la règle T7 n'était jamais armée."""
    s = service()
    s.demarrer()
    appel = s.nouvel_appel("appel-1")
    assert hasattr(appel, "basculer_clavier")
    assert hasattr(appel, "numero_au_clavier")


def test_poser_le_clavier_sur_l_appel_suivi_atteint_l_appel():
    class EnvoyeurFactice:
        def confirmer(self, telephone, rendez_vous):
            from standard.sms import Envoi
            return Envoi(True)

    # Le clavier ne s'arme que si l'agent demande un numero — donc seulement
    # quand un SMS peut partir. Sans envoyeur, la question ne se pose pas.
    s = Service(configuration(), client_modele=ModeleFactice(), base=BaseFactice(),
                envoyeur_sms=EnvoyeurFactice())
    s.demarrer()
    appel = s.nouvel_appel("appel-1")
    temoin = []
    appel.basculer_clavier = lambda: temoin.append(True)
    appel.tour("JE VOUDRAIS JEUDI A QUINZE HEURES TRENTE")
    appel.tour("oui")
    appel.tour("Dupont")                     # l'agent demande le nom d'abord
    appel.tour("zéro six douze")
    appel.tour("je ne sais plus")
    assert temoin, "la bascule posée sur l'agent n'atteint pas l'appel"


def test_l_envoyeur_de_sms_est_transmis_quand_il_existe():
    class EnvoyeurFactice:
        def confirmer(self, telephone, rendez_vous):
            from standard.sms import Envoi
            return Envoi(True)

    envoyeur = EnvoyeurFactice()
    s = Service(configuration(), client_modele=ModeleFactice(), base=BaseFactice(),
                envoyeur_sms=envoyeur)
    s.demarrer()
    appel = s.nouvel_appel("appel-1")
    appel.tour("JE VOUDRAIS JEUDI A QUINZE HEURES TRENTE")
    appel.tour("oui")
    reponse = appel.tour("Dupont")           # le nom vient avant le numéro
    assert "numéro" in reponse.phrase.lower(), \
        "sans envoyeur transmis, l'agent ne demande jamais le numéro"


def test_le_demarrage_chauffe_la_connexion_du_modele():
    """Seconde revue (19/09) : la « réserve de connexions » fabriquait quatre
    `object()` vides que personne n'empruntait, pendant que le vrai trafic
    ouvrait une connexion neuve à chaque tour. La mesure 4 dit 2 040 ms contre
    378 ms : ce qu'il faut chauffer, c'est la connexion qui sert."""
    class ClientQuiCompte(ModeleFactice):
        def __init__(self):
            super().__init__()
            self.amorces = 0

        def amorcer(self):
            self.amorces += 1

    client = ClientQuiCompte()
    s = Service(configuration(), client_modele=client, base=BaseFactice())
    s.demarrer()
    assert client.amorces == 1


def test_un_client_sans_amorcage_ne_fait_pas_tomber_le_demarrage():
    s = Service(configuration(), client_modele=ModeleFactice(), base=BaseFactice())
    s.demarrer()          # ne lève pas


def test_les_corrections_actives_entrent_dans_la_memoire_de_l_agent():
    """La console dit au commerçant « la correction s'applique tout de suite ».
    Seconde revue (19/09) : rien ne les lisait. C'était faux."""
    from standard.correction import Correction, RegistreDeCorrections

    registre = RegistreDeCorrections()
    registre.ajouter(Correction(faute="promesse_interdite", appel="a",
                                empan="on peut se garer devant",
                                valeur={"interdit": "promettre une place de parking"}))

    s = Service(configuration(), client_modele=ModeleFactice(), base=BaseFactice(),
                corrections=registre)
    s.demarrer()
    appel = s.nouvel_appel("appel-1")
    assert "place de parking" in appel.memoire
