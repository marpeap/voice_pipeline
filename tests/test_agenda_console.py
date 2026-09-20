"""L'agenda du commerçant — l'outil ne montrait pas ce qu'il produit.

La console montre le fil des appels, les messages, les corrections… et pas les
rendez-vous. Un salon qui ne peut pas lire sa journée dans l'outil retourne à
son cahier, et l'agent devient une source de plus à recopier — exactement ce
qu'il est censé supprimer.

Conception : règles Barthez. Action primaire = voir la journée d'aujourd'hui.
Pic = « voilà ce que l'agent vous a pris pendant que vous coiffiez ». Fin = le
retour au fil, jamais un cul-de-sac.
"""

import json
from datetime import date, timedelta

import pytest

from standard.console import Console
from standard.depot import Depot
from standard.journal import JournalDAppels

PACK = json.load(open("packs/coiffure.json"))
AUJOURD_HUI = date(2026, 9, 15)


def console(rendez_vous=()):
    depot = Depot(":memory:")
    acces = depot.pour("salon-1")
    for rang, ligne in enumerate(rendez_vous):
        acces.inserer(f"cle-{rang}", ligne)
    return Console(journal=JournalDAppels(depot), tenant="salon-1", depot=depot,
                   pack=PACK, aujourd_hui=lambda: AUJOURD_HUI)


def page(console, chemin="/agenda", methode="GET", corps=None):
    statut, _, contenu = console.repondre(methode, chemin, corps)
    return statut, contenu


DEMAIN = (AUJOURD_HUI + timedelta(days=1)).isoformat()


def test_l_agenda_montre_les_rendez_vous_du_jour():
    _, contenu = page(console([
        {"date": AUJOURD_HUI.isoformat(), "heure": "15:30", "nom": "Dupont",
         "prestation": "coupe", "telephone": "0612345678"},
    ]))
    assert "15 h 30" in contenu and "Dupont" in contenu and "coupe" in contenu
    assert "06 12 34 56 78" in contenu


def test_aujourd_hui_passe_avant_demain():
    """B7 : ce qui compte est en position 1. Un gérant ouvre sa console entre
    deux clients, pas pour explorer."""
    _, contenu = page(console([
        {"date": DEMAIN, "heure": "09:00", "nom": "Demain"},
        {"date": AUJOURD_HUI.isoformat(), "heure": "15:30", "nom": "Aujourdhui"},
    ]))
    assert contenu.index("Aujourdhui") < contenu.index("Demain")


def test_un_agenda_vide_dit_quoi_faire():
    """B9 : un état vide ne dit pas « aucune donnée »."""
    _, contenu = page(console())
    assert "aucun rendez-vous" in contenu.lower()


def test_les_rendez_vous_passes_ne_polluent_pas_la_journee():
    hier = (AUJOURD_HUI - timedelta(days=1)).isoformat()
    _, contenu = page(console([
        {"date": hier, "heure": "15:30", "nom": "Hier"},
        {"date": AUJOURD_HUI.isoformat(), "heure": "15:30", "nom": "Aujourdhui"},
    ]))
    assert "Hier" not in contenu


def test_un_rendez_vous_s_annule_depuis_la_console():
    c = console([{"date": AUJOURD_HUI.isoformat(), "heure": "15:30", "nom": "Dupont"}])
    reference = c.depot.lister("salon-1")[0]["reference"]
    statut, _ = page(c, "/agenda/annuler", "POST", {"reference": reference})
    assert statut == 303
    assert c.depot.lister("salon-1") == []


def test_une_annulation_sans_reference_ne_fait_rien():
    c = console([{"date": AUJOURD_HUI.isoformat(), "heure": "15:30", "nom": "Dupont"}])
    page(c, "/agenda/annuler", "POST", {"reference": "rdv-inexistant"})
    assert len(c.depot.lister("salon-1")) == 1


def test_l_annulation_laisse_une_trace_d_audit():
    """Qui a annulé quoi : un rendez-vous disparu sans trace est une dispute."""
    class AuditFactice:
        def __init__(self):
            self.lignes = []

        def noter(self, tenant, acteur, action, cible, detail=None, correlation=""):
            self.lignes.append((action, cible))

    c = console([{"date": AUJOURD_HUI.isoformat(), "heure": "15:30", "nom": "Dupont"}])
    c.audit = AuditFactice()
    reference = c.depot.lister("salon-1")[0]["reference"]
    page(c, "/agenda/annuler", "POST", {"reference": reference})
    assert ("agenda.annule", reference) in c.audit.lignes


def test_le_fil_mene_a_l_agenda():
    _, contenu = page(console(), "/")
    assert "/agenda" in contenu


def test_aujourd_hui_et_demain_se_disent_comme_dans_un_agenda():
    """B1 : tous les agendas du monde écrivent « Aujourd'hui », pas « mardi
    15 septembre » pour le jour même."""
    _, contenu = page(console([
        {"date": AUJOURD_HUI.isoformat(), "heure": "09:00", "nom": "A"},
        {"date": DEMAIN, "heure": "09:00", "nom": "B"},
    ]))
    assert "Aujourd'hui" in contenu and "Demain" in contenu


def test_une_ligne_sans_detail_ne_laisse_pas_de_trou():
    _, contenu = page(console([
        {"date": AUJOURD_HUI.isoformat(), "heure": "09:00", "nom": "Martin"},
    ]))
    assert "<p></p>" not in contenu


def test_le_pied_de_page_ne_renvoie_pas_a_la_page_ouverte():
    """Un lien vers la page qu'on regarde est un lien mort : il fait douter le
    gérant d'avoir cliqué."""
    _, agenda = page(console())
    assert "href='/agenda'" not in agenda
    _, fil = page(console(), "/")
    assert "href='/agenda'" in fil
