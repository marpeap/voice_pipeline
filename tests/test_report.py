"""Déplacer un rendez-vous — pire qu'une impasse : un doublon.

« report » est une intention reconnue depuis le début (`comprehension`), et
`decider` la traitait **comme une prise de rendez-vous**. L'agent écrivait donc
un second rendez-vous et laissait le premier en place : le salon se retrouvait
avec deux créneaux pour un client, et un trou qu'il ne pouvait pas revendre.

Règle : on écrit le nouveau, on le relit, **puis** on annule l'ancien. Dans cet
ordre — si l'écriture échoue, le client garde au moins son rendez-vous.
"""

from datetime import date

import pytest

from standard.appel import Appel
from standard.decision import Agenda
from standard.depot import Depot
from standard.hors_ligne import ModeleHorsLigne

MARDI = date(2026, 9, 15)


def base_avec_rendez_vous(tmp_path):
    depot = Depot(str(tmp_path / "essai.sqlite3"))
    depot.pour("salon-1").inserer("cle-1", {"date": "2026-09-17", "heure": "15:30",
                                            "nom": "Dupont",
                                            "telephone": "0612345678"})
    return depot


def conversation(depot):
    appel = Appel(client_modele=ModeleHorsLigne(aujourd_hui=MARDI),
                  agenda=Agenda(aujourd_hui=MARDI, creneaux={"15:30", "17:00"},
                                jours_fermes=(6, 0)),
                  base=depot.pour("salon-1"), memoire="", consignes_communes="c",
                  tenant="salon-1", identifiant="appel-1")
    appel.fiche = {"reservation": {"nom": "non"}}
    appel.etat.connu["telephone"] = "0612345678"
    return appel


def test_un_report_ne_laisse_jamais_deux_rendez_vous(tmp_path):
    depot = base_avec_rendez_vous(tmp_path)
    appel = conversation(depot)
    appel.tour("je voudrais décaler mon rendez-vous à dix-sept heures jeudi")
    appel.tour("oui c'est parfait")
    restants = depot.lister("salon-1")
    assert len(restants) == 1, f"doublon : {restants}"
    assert restants[0]["heure"] == "17:00"


def test_le_report_dit_qu_il_a_deplace_et_non_qu_il_a_pris(tmp_path):
    depot = base_avec_rendez_vous(tmp_path)
    appel = conversation(depot)
    appel.tour("je voudrais décaler mon rendez-vous à dix-sept heures jeudi")
    phrase = appel.tour("oui c'est parfait").phrase
    assert "déplacé" in phrase or "à la place" in phrase


def test_sans_rendez_vous_existant_un_report_devient_une_prise(tmp_path):
    """Un appelant qui croit avoir un rendez-vous et n'en a pas ne doit pas
    s'entendre dire non : on lui en prend un."""
    depot = Depot(str(tmp_path / "vide.sqlite3"))
    appel = conversation(depot)
    appel.tour("je voudrais décaler mon rendez-vous à dix-sept heures jeudi")
    appel.tour("oui c'est parfait")
    assert len(depot.lister("salon-1")) == 1


def test_si_l_ancien_ne_peut_pas_etre_annule_l_agent_le_dit(tmp_path):
    """L'ordre compte : on écrit d'abord, on annule ensuite. Si l'annulation
    échoue, le client a deux rendez-vous — il doit l'apprendre de l'agent, pas
    du salon le jour venu."""
    depot = base_avec_rendez_vous(tmp_path)
    appel = conversation(depot)

    acces = depot.pour("salon-1")
    acces.annuler = lambda reference: False
    appel.base = acces

    appel.tour("je voudrais décaler mon rendez-vous à dix-sept heures jeudi")
    phrase = appel.tour("oui c'est parfait").phrase
    assert "ancien" in phrase.lower()


def test_sans_numero_connu_le_report_demande_le_numero(tmp_path):
    """Un appelant qui dit « je voudrais décaler » ne donne pas son numéro
    spontanément : sans lui, l'agent ne peut pas retrouver le rendez-vous, et
    il prenait un second créneau à la place."""
    depot = base_avec_rendez_vous(tmp_path)
    appel = conversation(depot)
    appel.etat.connu.pop("telephone")

    reponse = appel.tour("bonjour je voudrais décaler mon rendez-vous")
    assert "numéro" in reponse.phrase.lower()

    trouve = appel.tour("zéro six douze trente-quatre cinquante-six soixante-dix-huit")
    assert "17 septembre" in trouve.phrase
    assert "déplac" in trouve.phrase.lower()

    appel.tour("à dix-sept heures jeudi")
    appel.tour("oui c'est parfait")
    restants = depot.lister("salon-1")
    assert len(restants) == 1 and restants[0]["heure"] == "17:00"


def test_un_report_ne_redemande_pas_un_nom_deja_connu(tmp_path):
    """Le rendez-vous déplacé porte déjà le nom : le redemander fait répéter
    l'appelant pour rien, et rallonge un appel qui doit être court."""
    depot = base_avec_rendez_vous(tmp_path)
    appel = conversation(depot)
    appel.fiche = {"reservation": {"nom": "oui"}}
    appel.tour("je voudrais décaler mon rendez-vous à dix-sept heures jeudi")
    reponse = appel.tour("oui c'est parfait")
    assert reponse.genre == "confirmation"
    assert "Dupont" in reponse.phrase
