#!/usr/bin/env python3
"""Rejouer un appel entier, sans telephone, sans cle d'API, sans depense.

C'est le mode de demonstration du produit : tout tourne en local, avec le moteur
hors ligne (`standard.hors_ligne`) a la place du fournisseur. Ce qui s'affiche
est exactement ce que l'appelant entendrait, phrase par phrase, plus le journal
que le salon consulterait apres coup.

    python3 demonstration.py                 # l'appel nominal
    python3 demonstration.py --scenario tetu # l'appelant qui insiste
    python3 demonstration.py --scenario faute # ce qu'un agent sans garde-fous disait
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from standard.hors_ligne import ModeleHorsLigne
from standard.service import Configuration, Service

RACINE = Path(__file__).resolve().parent
AUJOURD_HUI = date(2026, 9, 15)     # un mardi, comme dans toutes les mesures


class BaseEnMemoire:
    """Une base de rendez-vous qui vit le temps de la demonstration."""

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


class BaseMuette(BaseEnMemoire):
    """Une base qui accepte l'ecriture mais ne la rend pas.

    C'est le cas qui produisait « c'est note » sur du vide (mesure 14). Ici,
    l'agent dit qu'il ne peut pas verifier — et c'est tout l'interet.
    """

    def relire(self, reference):
        return None


SCENARIOS = {
    "nominal": [
        "bonjour je voudrais un rendez-vous jeudi a quinze heures trente",
        "oui c'est parfait",
    ],
    "tetu": [
        "je voudrais samedi a dix-huit heures trente",
        "non samedi dix-huit heures trente",
        "samedi dix-huit heures trente",
        "samedi dix-huit heures trente",
    ],
    "humain": [
        "bonjour je voudrais un rendez-vous",
        "passez-moi quelqu'un une vraie personne s'il vous plait",
    ],
    "faute": [       # la base perd l'ecriture : l'agent ne doit rien promettre
        "je voudrais un rendez-vous jeudi a quinze heures trente",
        "oui",
    ],
}

def configuration(pack: str) -> Configuration:
    return Configuration.depuis({
        "tenant": "demonstration",
        "pack": str(RACINE / "packs" / f"{pack}.json"),
        "reponses": {"A1": "Salon Élégance"},
        "corps": "# Particularités\n\nLe balayage se fait avec Sophie ou Léa.\n",
        "aujourd_hui": AUJOURD_HUI.isoformat(),
        "horizon_jours": 14,
        "jours_fermes": [6, 0],
        "creneaux": ["09:00", "09:45", "10:30", "11:15",
                     "14:00", "14:45", "15:30", "16:15", "17:00"],
        "connexions": 2,
        "consignes_communes": "Analyse une phrase d'appelant. Rends un objet JSON.",
    })


def jouer(scenario: str, pack: str, base_muette: bool) -> int:
    service = Service(configuration(pack),
                      client_modele=ModeleHorsLigne(aujourd_hui=AUJOURD_HUI),
                      base=BaseMuette() if base_muette else BaseEnMemoire())
    service.demarrer()
    appel = service.nouvel_appel("demo-1")

    print(f"— Agent   : {appel.salutation()}")
    for dit in SCENARIOS[scenario]:
        print(f"— Appelant: {dit}")
        # Tout passe par `tour()`, y compris le « oui » : c'est le produit qui
        # reconnait un accord, pas la demonstration. Court-circuiter ici revenait
        # a montrer un chemin que l'appelant reel n'emprunte jamais.
        reponse = appel.tour(dit)
        print(f"— Agent   : {reponse.phrase}   [{reponse.genre}]")

    print("\nJournal de l'appel, tel que le salon le verrait :")
    for tour in appel.journal.tours:
        print(f"  · {tour['genre']:13s} {tour.get('entites') or ''}")
    print("\nSupervision :", json.dumps(service.supervision(), ensure_ascii=False))
    orphelines = service.supervision()["confirmations_orphelines"]
    print("Confirmations orphelines :", orphelines, "(cible : 0)")
    return 0 if orphelines == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scenario", choices=sorted(SCENARIOS), default="nominal")
    ap.add_argument("--pack", default="coiffure")
    args = ap.parse_args()
    return jouer(args.scenario, args.pack, base_muette=args.scenario == "faute")


if __name__ == "__main__":
    raise SystemExit(main())
