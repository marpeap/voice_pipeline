"""Le rendez-vous pris au comptoir — sans lui, l'agenda est faux par construction.

Un client entre dans le salon et prend rendez-vous de vive voix ; un autre
appelle le fixe pendant que le gérant coupe. Ces rendez-vous-là n'existent nulle
part pour l'agent, qui propose donc leurs créneaux au premier appelant venu. La
console montrait l'agenda depuis hier soir : elle ne permettait pas d'y écrire.

C'est le cas le plus banal du métier, et celui qui rend l'outil inutilisable
s'il manque : deux clients à la même heure, et le gérant débranche l'agent.
"""

import json
from datetime import date, timedelta

import pytest

from standard.console import Console
from standard.depot import Depot
from standard.journal import JournalDAppels

PACK = json.load(open("packs/coiffure.json"))
AUJOURD_HUI = date(2026, 9, 15)
DEMAIN = (AUJOURD_HUI + timedelta(days=1)).isoformat()


def console():
    depot = Depot(":memory:")
    depot.pour("salon-1").enregistrer_reponses({"A1": "Salon", "C1": ["coupe"]})
    return Console(journal=JournalDAppels(depot), tenant="salon-1", depot=depot,
                   pack=PACK, creneaux=("09:00", "10:30", "15:30"),
                   aujourd_hui=lambda: AUJOURD_HUI)


def page(console, chemin="/agenda", methode="GET", corps=None):
    statut, _, contenu = console.repondre(methode, chemin, corps)
    return statut, contenu


def test_l_agenda_porte_un_formulaire_d_ajout():
    _, contenu = page(console())
    assert "Ajouter un rendez-vous" in contenu
    assert "name=heure" in contenu and "name=nom" in contenu


def test_un_rendez_vous_ajoute_a_la_main_apparait():
    c = console()
    statut, _ = page(c, "/agenda/ajouter", "POST",
                     {"date": DEMAIN, "heure": "10:30", "nom": "Dupont",
                      "prestation": "coupe"})
    assert statut == 303
    lignes = c.depot.lister("salon-1")
    assert len(lignes) == 1
    assert lignes[0]["nom"] == "Dupont" and lignes[0]["heure"] == "10:30"


def test_un_rendez_vous_ajoute_bloque_le_creneau_pour_l_agent():
    """C'est tout l'intérêt : l'agent ne doit plus proposer cette heure-là."""
    c = console()
    page(c, "/agenda/ajouter", "POST",
         {"date": DEMAIN, "heure": "10:30", "nom": "Dupont"})
    pris = {ligne["heure"] for ligne in c.depot.lister("salon-1")
            if ligne["date"] == DEMAIN}
    assert pris == {"10:30"}


def test_on_ne_peut_pas_ajouter_sur_un_creneau_deja_pris():
    c = console()
    page(c, "/agenda/ajouter", "POST", {"date": DEMAIN, "heure": "10:30", "nom": "A"})
    page(c, "/agenda/ajouter", "POST", {"date": DEMAIN, "heure": "10:30", "nom": "B"})
    lignes = [l for l in c.depot.lister("salon-1") if l["date"] == DEMAIN]
    assert len(lignes) == 1 and lignes[0]["nom"] == "A"


def test_une_date_ou_une_heure_absente_ne_cree_rien():
    c = console()
    page(c, "/agenda/ajouter", "POST", {"date": DEMAIN, "nom": "Sans heure"})
    page(c, "/agenda/ajouter", "POST", {"heure": "10:30", "nom": "Sans date"})
    assert c.depot.lister("salon-1") == []


def test_l_ajout_laisse_une_trace_d_audit():
    class AuditFactice:
        def __init__(self):
            self.lignes = []

        def noter(self, tenant, acteur, action, cible, detail=None, correlation=""):
            self.lignes.append(action)

    c = console()
    c.audit = AuditFactice()
    page(c, "/agenda/ajouter", "POST", {"date": DEMAIN, "heure": "10:30", "nom": "A"})
    assert "agenda.ajoute" in c.audit.lignes
