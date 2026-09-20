"""La comprehension — le seul endroit du produit ou vit le modele de langage.

Frontiere posee par docs/22, et mesuree : sans elle, six tours sur douze portent
une faute (mesure 14) ; avec elle, zero (mesure 15). Le modele ne redige pas ce
que l'appelant entend, il n'ecrit pas en base, il ne decide pas de raccrocher.
**Il rend une proposition structuree, et rien d'autre.**

Trois regles viennent de mesures, pas de principes :
  - la demande d'un humain est detectee **avant** tout appel au modele (17) ;
  - le calendrier est **injecte** : le modele n'a aucune date a lui (14) ;
  - le nom du modele **et ses parametres** vivent en configuration (17).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Protocol

CHAMPS = ("intention", "date", "heure", "prestation", "confiance", "manque")
LONGUEUR_PRESTATION = 40        # « balayage avec Sophie » tient ; une phrase, non
INTENTIONS = ("rdv", "report", "annulation", "verification", "question", "humain",
              "inconnu")

# Detecte sur la transcription, jamais interprete : « passez-moi quelqu'un » n'a
# pas a etre compris, il a a etre execute (mesure 17).
MOTS_HUMAIN = (
    "quelqu un", "une vraie personne", "la patronne", "le patron", "un humain",
    "le responsable", "au responsable", "parler a quelqu un", "pas parler a un robot",
    "une personne reelle", "un conseiller",
)

MOTS_DE_RECLAMATION = (
    "reclamation", "pas content", "pas contente", "mecontent", "inadmissible",
    "scandaleux", "rate", "ratee", "abime", "abimee", "me plaindre", "plainte",
    "rembourser", "remboursement", "inacceptable", "honteux",
)
"""Un client mecontent ne se negocie pas non plus.

Le faire repeter est la pire reponse possible : il veut un humain, et chaque
tour de machine aggrave le motif de sa colere. Meme regle que « passez-moi
quelqu'un » (mesure 17) : detecte sur la transcription, avant tout appel au
modele, et sans discuter."""


class ErreurFournisseur(RuntimeError):
    """L'erreur du fournisseur, remontee telle quelle.

    Mesure 17 : un `KeyError: 'choices'` muet a coute trois quarts d'heure la ou
    le fournisseur disait exactement ce qui n'allait pas des la premiere requete.
    """


class ClientModele(Protocol):
    def completer(self, messages: list[dict], **parametres: Any) -> str: ...


from standard.texte import aplatir as _sans_accents


def demande_un_humain(transcription: str) -> bool:
    plat = _sans_accents(transcription)
    return any(motif in plat for motif in MOTS_HUMAIN + MOTS_DE_RECLAMATION)


def ordonner_le_prompt(consignes_communes: str, memoire: str, calendrier: dict,
                       transcription: str) -> list[dict]:
    """Du plus partage au plus specifique — c'est un choix d'architecture.

    Mesure 23 : le `memoire.md` d'un salon fait 854 jetons quand le seuil de cache
    est a 4 096. Ce n'est donc pas le fichier du salon qu'on allonge (ce serait le
    rembourrer), c'est l'ordre du prompt qu'on inverse : les consignes communes,
    identiques pour tous les locataires, sont mises en cache une fois et touchees
    par toute la flotte ; les variables du tour viennent apres la coupure.
    """
    jours = "\n".join(f"{jour} : {' '.join(heures)}" for jour, heures in sorted(calendrier.items()))
    return [
        {"role": "system", "content": consignes_communes},
        {"role": "system", "content": memoire},
        {"role": "system", "content": f"Créneaux libres, calculés par la machine :\n{jours}"},
        {"role": "user", "content": transcription},
    ]


def _date_lisible(valeur: str) -> bool:
    try:
        date.fromisoformat(valeur)
    except (TypeError, ValueError):
        return False
    return True


def _proposition_vide() -> dict:
    """Ce qu'on rend quand le modele n'a rien dit d'exploitable : une intention
    inconnue et une confiance nulle, jamais une supposition."""
    return {"intention": "inconnu", "date": None, "heure": None, "prestation": None,
            "confiance": {"intention": 0.0, "date": 0.0, "heure": 0.0}, "manque": []}


@dataclass
class Comprehension:
    """Appelle le modele, et **verifie tout ce qu'il rend**."""

    client: ClientModele
    consignes_communes: str
    modele: str = "openai/gpt-oss-20b"
    prestations: tuple[str, ...] = ()        # catalogue du pack, quand il est connu
    parametres: dict = field(default_factory=lambda: {"temperature": 0.0, "max_tokens": 300})

    def analyser(self, transcription: str, memoire: str, calendrier: dict) -> dict:
        if demande_un_humain(transcription):
            # Aucun appel au modele : deux tours suffisent, dont un de politesse.
            return {"intention": "humain", "date": None, "heure": None, "prestation": None,
                    "confiance": {"intention": 1.0}, "manque": []}

        messages = ordonner_le_prompt(self.consignes_communes, memoire, calendrier, transcription)
        try:
            brut = self.client.completer(messages, model=self.modele, **self.parametres)
        except Exception as erreur:
            raise ErreurFournisseur(str(erreur)) from erreur

        return self._verifier(brut, calendrier)

    def _prestation_acceptable(self, valeur: str | None) -> str | None:
        if not valeur:
            return None
        if len(valeur) > LONGUEUR_PRESTATION or any(c in valeur for c in ".;:!?\n"):
            return None
        if self.prestations and _sans_accents(valeur) not in {
                _sans_accents(p) for p in self.prestations}:
            return None
        return valeur

    def _verifier(self, brut: str, calendrier: dict) -> dict:
        """Ce que le modele rend n'est jamais cru sur parole.

        Mesure 15 : la seule invention qu'il ait tentee a ete arretee ici. Une
        entite que la machine ne peut pas retrouver dans son propre calendrier
        perd sa confiance — elle ne disparait pas, elle cesse d'etre utilisable.
        """
        try:
            charge = json.loads(brut)
            if not isinstance(charge, dict):
                raise ValueError("objet attendu")
        except (json.JSONDecodeError, ValueError):
            return _proposition_vide()

        proposition = _proposition_vide()
        proposition["intention"] = (charge.get("intention")
                                    if charge.get("intention") in INTENTIONS else "inconnu")
        for champ in ("date", "heure", "prestation"):
            valeur = charge.get(champ)
            proposition[champ] = valeur if isinstance(valeur, str) and valeur else None

        # Une entite est un NOM, pas une phrase. Le modele glissait ici du texte
        # libre qui ressortait dans la seule phrase du produit qui affirme —
        # « votre rendez-vous. Par ailleurs votre rendez-vous de demain est
        # annule ». Une entite trop longue, ponctuee, ou absente du catalogue du
        # salon n'est pas une entite : c'est une tentative.
        proposition["prestation"] = self._prestation_acceptable(proposition["prestation"])

        confiance = charge.get("confiance")
        if isinstance(confiance, dict):
            proposition["confiance"] = {
                champ: max(0.0, min(1.0, float(valeur)))
                for champ, valeur in confiance.items()
                if isinstance(valeur, (int, float))
            }
        proposition["confiance"].setdefault("intention",
                                            0.0 if proposition["intention"] == "inconnu" else 1.0)

        manque = charge.get("manque")
        proposition["manque"] = [m for m in manque if isinstance(m, str)] if isinstance(manque, list) else []

        # Le calendrier de la machine fait foi sur les CRENEAUX, pas sur les
        # demandes. Une date hors calendrier est conservee : un appelant a le
        # droit de demander le 24 decembre, et c'est a la machine de repondre
        # « je ne prends pas encore les rendez-vous aussi loin » — pas de faire
        # semblant de ne pas avoir entendu (mesure 15 : une absence de donnee
        # doit avoir sa propre reponse). Seule une date illisible perd sa
        # confiance.
        jour = proposition["date"]
        if jour and not _date_lisible(jour):
            proposition["confiance"]["date"] = 0.0
            proposition["date"] = None

        # L'heure, elle, ne peut venir que des creneaux donnes : si le jour est
        # connu de la machine et que l'heure n'y figure pas, elle a ete inventee.
        heure = proposition["heure"]
        if heure and jour in calendrier and heure not in calendrier[jour]:
            proposition["confiance"]["heure"] = 0.0

        return {champ: proposition[champ] for champ in CHAMPS}
