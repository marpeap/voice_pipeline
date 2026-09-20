"""Annuler par téléphone — une impasse promise en trois endroits.

L'agent répondait « Pour annuler, pouvez-vous me donner votre nom et votre
numéro ? » … et rien ne se passait ensuite. Pendant ce temps, le SMS de
confirmation dit « pour annuler, rappelez-nous », et le registre des
traitements annonce la finalité « prendre, déplacer ou **annuler** un
rendez-vous ». Trois promesses, zéro implémentation — et c'est le deuxième motif
d'appel d'un salon.

Règle qui gouverne tout ce fichier : **on n'annule jamais sans relire.** Un
rendez-vous annulé par erreur est pire qu'un rendez-vous manqué : le client se
présente, et la place a été donnée à quelqu'un d'autre.
"""

from datetime import date

import pytest

from standard.appel import Appel
from standard.decision import Agenda
from standard.depot import Depot
from standard.hors_ligne import ModeleHorsLigne

MARDI = date(2026, 9, 15)


def base_avec_rendez_vous(tmp_path, **extra):
    depot = Depot(str(tmp_path / "essai.sqlite3"))
    depot.pour("salon-1").inserer("cle-1", {"date": "2026-09-17", "heure": "15:30",
                                            "nom": "Dupont",
                                            "telephone": "0612345678", **extra})
    return depot


# --- retrouver le rendez-vous ----------------------------------------------

def test_on_retrouve_un_rendez_vous_par_son_numero(tmp_path):
    depot = base_avec_rendez_vous(tmp_path)
    trouves = depot.pour("salon-1").chercher(telephone="0612345678",
                                             a_partir_de="2026-09-15")
    assert len(trouves) == 1
    assert trouves[0]["heure"] == "15:30"


def test_un_rendez_vous_passe_ne_remonte_pas(tmp_path):
    depot = base_avec_rendez_vous(tmp_path)
    assert depot.pour("salon-1").chercher(telephone="0612345678",
                                          a_partir_de="2026-09-18") == []


def test_le_numero_d_un_autre_ne_rend_rien(tmp_path):
    depot = base_avec_rendez_vous(tmp_path)
    assert depot.pour("salon-1").chercher(telephone="0699999999",
                                          a_partir_de="2026-09-15") == []


def test_la_recherche_est_cloisonnee_par_locataire(tmp_path):
    depot = base_avec_rendez_vous(tmp_path)
    assert depot.pour("salon-2").chercher(telephone="0612345678",
                                          a_partir_de="2026-09-15") == []


# --- l'appel ----------------------------------------------------------------

def conversation(depot):
    appel = Appel(client_modele=ModeleHorsLigne(aujourd_hui=MARDI),
                  agenda=Agenda(aujourd_hui=MARDI, creneaux={"15:30"}, jours_fermes=(6, 0)),
                  base=depot.pour("salon-1"), memoire="", consignes_communes="c",
                  tenant="salon-1", identifiant="appel-1")
    appel.fiche = {"reservation": {"nom": "non"}}
    return appel


def test_l_agent_demande_le_numero_puis_relit_le_rendez_vous(tmp_path):
    depot = base_avec_rendez_vous(tmp_path)
    appel = conversation(depot)
    assert "numéro" in appel.tour("je voudrais annuler mon rendez-vous").phrase.lower()

    reponse = appel.tour("zéro six douze trente-quatre cinquante-six soixante-dix-huit")
    assert "17 septembre" in reponse.phrase and "15 h 30" in reponse.phrase
    assert depot.lister("salon-1"), "rien ne doit être annulé avant l'accord"


def test_l_accord_annule_et_la_relecture_le_prouve(tmp_path):
    depot = base_avec_rendez_vous(tmp_path)
    appel = conversation(depot)
    appel.tour("je voudrais annuler mon rendez-vous")
    appel.tour("zéro six douze trente-quatre cinquante-six soixante-dix-huit")
    reponse = appel.tour("oui c'est bien ça")
    assert reponse.genre == "annulation"
    assert "annulé" in reponse.phrase
    assert depot.lister("salon-1") == []


def test_un_refus_n_annule_rien(tmp_path):
    depot = base_avec_rendez_vous(tmp_path)
    appel = conversation(depot)
    appel.tour("je voudrais annuler mon rendez-vous")
    appel.tour("zéro six douze trente-quatre cinquante-six soixante-dix-huit")
    appel.tour("non ce n'est pas celui-là")
    assert depot.lister("salon-1"), "un « non » ne doit rien annuler"


def test_sans_rendez_vous_a_ce_numero_l_agent_le_dit(tmp_path):
    depot = Depot(str(tmp_path / "vide.sqlite3"))
    appel = conversation(depot)
    appel.tour("je voudrais annuler mon rendez-vous")
    reponse = appel.tour("zéro six douze trente-quatre cinquante-six soixante-dix-huit")
    assert "ne trouve" in reponse.phrase.lower()
    assert "annulé" not in reponse.phrase.lower()


def test_le_numero_compose_au_clavier_retrouve_aussi_le_rendez_vous(tmp_path):
    """Un numéro dicté se perd quatre fois sur dix (mesure 7) : le clavier doit
    mener au même endroit, sinon l'annulation reste une impasse pour un appelant
    sur deux."""
    depot = base_avec_rendez_vous(tmp_path)
    appel = conversation(depot)
    appel.basculer_clavier = lambda: None
    appel.tour("je voudrais annuler mon rendez-vous")
    appel.tour("euh je ne sais plus")                  # numéro incompréhensible
    reponse = appel.numero_au_clavier("0612345678")
    assert "17 septembre" in reponse.phrase
    assert depot.lister("salon-1"), "rien n'est annulé avant l'accord"
    assert appel.tour("oui").genre == "annulation"
    assert depot.lister("salon-1") == []
