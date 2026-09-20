"""La prestation — le catalogue existe, personne ne l'entend.

Le pack déclare les prestations réservables, `comprehension` refuse celles qui
n'y sont pas, la durée de chacune pilote l'agenda depuis ce matin… et le modèle
hors ligne — **celui qui tourne par défaut, sans clé payante** — rendait
toujours `prestation: None`. Conséquences en chaîne :

  - la confirmation disait « votre rendez-vous » au lieu de « votre coloration » ;
  - la durée n'était jamais appliquée, donc le salon se double-bookait quand
    même ;
  - le salon lisait une ligne d'agenda sans savoir ce qu'il devait préparer.
"""

from datetime import date

import json

import pytest

from standard.hors_ligne import ModeleHorsLigne

MARDI = date(2026, 9, 15)
CATALOGUE = ("coupe", "brushing", "coloration")


def analyser(dit, prestations=CATALOGUE):
    modele = ModeleHorsLigne(aujourd_hui=MARDI, prestations=prestations)
    return json.loads(modele.completer([{"role": "user", "content": dit}]))


@pytest.mark.parametrize("dit, attendu", [
    ("je voudrais une coupe jeudi à quinze heures", "coupe"),
    ("bonjour, un brushing vendredi", "brushing"),
    ("je voudrais une coloration", "coloration"),
    # Le canal abîme la fin des mots : « coloration » revient « COLORATIONS ».
    ("je voudrais une colorations jeudi", "coloration"),
])
def test_une_prestation_du_catalogue_est_entendue(dit, attendu):
    assert analyser(dit)["prestation"] == attendu


@pytest.mark.parametrize("dit", [
    "je voudrais un rendez-vous jeudi",
    "je voudrais un massage",          # hors catalogue : on n'invente pas
    "bonjour",
])
def test_ce_qui_n_est_pas_au_catalogue_reste_vide(dit):
    assert analyser(dit)["prestation"] is None


def test_sans_catalogue_on_ne_devine_rien():
    """Sans pack, le modèle ne doit pas inventer un vocabulaire de salon."""
    assert analyser("je voudrais une coupe", prestations=())["prestation"] is None


def test_la_confiance_suit_la_prestation():
    charge = analyser("je voudrais une coupe jeudi")
    assert charge["confiance"].get("prestation", 0) >= 0.7


# --- de bout en bout --------------------------------------------------------

def test_la_prestation_atteint_la_ligne_ecrite_et_la_duree_avec_elle(tmp_path):
    import os

    from standard.demarrage import construire_serveur

    racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    serveur = construire_serveur({
        "STANDARD_TENANT": "salon-1",
        "STANDARD_PACK": os.path.join(racine, "packs", "coiffure.json"),
        "STANDARD_REPONSES": '{"A1": "Salon", "C1": ["coupe", "coloration"]}',
        "STANDARD_CRENEAUX": "09:00,10:30,14:00,15:30,17:00",
        "STANDARD_AUJOURDHUI": "2026-09-15",
        "STANDARD_PORT": "0", "STANDARD_PORT_SANTE": "0",
        "STANDARD_BASE": str(tmp_path / "essai.sqlite3"),
        "STANDARD_STT": "muet", "STANDARD_TTS": "muet",
    })
    appel = serveur.service.nouvel_appel("appel-1")
    appel.tour("je voudrais une coloration jeudi à dix heures trente")
    appel.tour("oui c'est parfait")
    appel.tour("au nom de Dupont")

    from standard.depot import Depot
    ligne = Depot(str(tmp_path / "essai.sqlite3")).lister("salon-1")[0]
    assert ligne["prestation"] == "coloration"
    assert ligne["duree_minutes"] and ligne["duree_minutes"] > 60


def test_la_confirmation_nomme_la_prestation(tmp_path):
    import os

    from standard.demarrage import construire_serveur

    racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    serveur = construire_serveur({
        "STANDARD_TENANT": "salon-1",
        "STANDARD_PACK": os.path.join(racine, "packs", "coiffure.json"),
        "STANDARD_REPONSES": '{"A1": "Salon", "C1": ["coupe"]}',
        "STANDARD_CRENEAUX": "15:30",
        "STANDARD_AUJOURDHUI": "2026-09-15",
        "STANDARD_PORT": "0", "STANDARD_PORT_SANTE": "0",
        "STANDARD_BASE": str(tmp_path / "essai.sqlite3"),
        "STANDARD_STT": "muet", "STANDARD_TTS": "muet",
    })
    appel = serveur.service.nouvel_appel("appel-1")
    appel.tour("je voudrais une coupe jeudi à quinze heures trente")
    appel.tour("oui")
    phrase = appel.tour("au nom de Dupont").phrase
    assert "coupe" in phrase.lower()
