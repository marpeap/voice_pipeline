"""« J'ai bien rendez-vous jeudi ? » — l'appel le plus court d'un salon.

Un client qui vérifie son rendez-vous appelle trente secondes. L'agent n'avait
aucun chemin pour lui : la phrase partait dans l'analyse générale, ressortait en
« prise de rendez-vous », et il s'entendait proposer un **second** créneau — ou,
au mieux, « je n'ai pas bien saisi ».

C'est aussi l'appel qui suit un SMS de rappel : celui qu'on provoque soi-même.
"""

from datetime import date

import pytest

from standard.appel import Appel
from standard.decision import Agenda
from standard.depot import Depot
from standard.hors_ligne import ModeleHorsLigne

MARDI = date(2026, 9, 15)


def base_avec(rendez_vous=(), tmp_path=None):
    depot = Depot(str(tmp_path / "essai.sqlite3"))
    for rang, ligne in enumerate(rendez_vous):
        depot.pour("salon-1").inserer(f"cle-{rang}", ligne)
    return depot


def conversation(depot, telephone="0612345678"):
    appel = Appel(client_modele=ModeleHorsLigne(aujourd_hui=MARDI),
                  agenda=Agenda(aujourd_hui=MARDI, creneaux={"15:30", "17:00"},
                                jours_fermes=(6, 0)),
                  base=depot.pour("salon-1"), memoire="", consignes_communes="c",
                  tenant="salon-1", identifiant="appel-1")
    appel.fiche = {"reservation": {"nom": "non"}}
    if telephone:
        appel.etat.connu["telephone"] = telephone
    return appel


@pytest.mark.parametrize("dit", [
    "bonjour j'ai bien rendez-vous jeudi ?",
    "je voulais vérifier mon rendez-vous",
    "c'est bien jeudi que j'ai rendez-vous ?",
    "je voulais confirmer mon rendez-vous",
])
def test_une_verification_se_reconnait(dit):
    from standard.hors_ligne import ModeleHorsLigne as Modele

    charge = Modele(aujourd_hui=MARDI).analyser(dit)
    assert charge["intention"] == "verification", dit


@pytest.mark.parametrize("dit", [
    "je voudrais un rendez-vous jeudi",
    "je voudrais annuler mon rendez-vous",
    "je voudrais décaler mon rendez-vous",
])
def test_ce_qui_n_est_pas_une_verification_ne_l_est_pas(dit):
    from standard.hors_ligne import ModeleHorsLigne as Modele

    assert Modele(aujourd_hui=MARDI).analyser(dit)["intention"] != "verification"


def test_l_agent_relit_le_rendez_vous_trouve(tmp_path):
    depot = base_avec([{"date": "2026-09-17", "heure": "15:30", "nom": "Dupont",
                        "telephone": "0612345678"}], tmp_path)
    reponse = conversation(depot).tour("j'ai bien rendez-vous jeudi ?")
    assert "17 septembre" in reponse.phrase and "15 h 30" in reponse.phrase
    assert depot.lister("salon-1"), "une vérification n'écrit ni n'efface rien"


def test_sans_rendez_vous_l_agent_le_dit_et_en_propose_un(tmp_path):
    depot = base_avec([], tmp_path)
    reponse = conversation(depot).tour("j'ai bien rendez-vous jeudi ?")
    assert "ne trouve" in reponse.phrase.lower()
    assert "rendez-vous" in reponse.phrase.lower()


def test_sans_numero_connu_l_agent_le_demande(tmp_path):
    depot = base_avec([{"date": "2026-09-17", "heure": "15:30",
                        "telephone": "0612345678"}], tmp_path)
    appel = conversation(depot, telephone=None)
    assert "numéro" in appel.tour("je voulais vérifier mon rendez-vous").phrase.lower()
    suite = appel.tour("zéro six douze trente-quatre cinquante-six soixante-dix-huit")
    assert "17 septembre" in suite.phrase


def test_avec_deux_rendez_vous_l_agent_les_dit_tous_les_deux(tmp_path):
    depot = base_avec([
        {"date": "2026-09-17", "heure": "15:30", "telephone": "0612345678"},
        {"date": "2026-09-24", "heure": "17:00", "telephone": "0612345678"},
    ], tmp_path)
    phrase = conversation(depot).tour("j'ai bien rendez-vous jeudi ?").phrase
    assert "17 septembre" in phrase and "24 septembre" in phrase
