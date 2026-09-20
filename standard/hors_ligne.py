"""Comprendre sans modele — pour demontrer, et pour tenir quand le modele tombe.

Deux usages, et le second n'est pas un pis-aller.

1. **Demontrer** : rejouer un appel sans cle d'API ni telephone. Un produit qu'on
   ne peut pas montrer sans depenser n'est pas demontrable.
2. **Tenir** : mesure 20, la latence d'un fournisseur distant est une variable
   aleatoire bornee par le haut — jusqu'a 8 751 ms sur un tour. Un repli
   deterministe vaut mieux qu'un silence.

Il applique la grammaire de docs/10 §4 et **il ne comble jamais** : ce qu'il n'a
pas lu reste nul, avec une confiance nulle. C'est sa raison d'etre.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, timedelta

from standard.grammaire import SIMPLES, _valeur_composee, normaliser
from standard.regles import JOURS as JOURS_ACCENTUES
from standard.regles import indice_dans, indice_dans_les_mots
from standard.regles import MOIS as MOIS_ACCENTUES
from standard.texte import sans_accents

# Les formes sans accents se DERIVENT du calendrier unique : « fevrier » recopie
# a la main finit par ne plus correspondre a « février ».
JOURS = tuple(sans_accents(jour) for jour in JOURS_ACCENTUES)
MOIS = tuple(sans_accents(mois) for mois in MOIS_ACCENTUES)

VERBES_ANNULATION = ("annuler", "annule", "supprimer", "je ne pourrai pas", "empechement")
VERBES_REPORT = ("decaler", "deplacer", "reporter", "avancer", "changer")
VERBES_RDV = ("rendez vous", "reserver", "prendre", "creneau", "disponible", "place")
VERBES_QUESTION = ("combien", "quel prix", "ouvert", "ouverts", "horaire", "adresse", "ou etes")


def _mots(texte: str) -> list[str]:
    """Les traits d'union se defont ici : « apres-demain » et « apres demain »
    sont le meme mot a l'oreille, et c'est l'oreille qui fait foi."""
    return normaliser(texte).replace("-", " ").split()


def _nombre(fenetre: str) -> int | None:
    """Un nombre ecrit en chiffres ou en toutes lettres — les deux se disent."""
    fenetre = fenetre.strip()
    if fenetre.isdigit():
        return int(fenetre)
    return _valeur_composee(fenetre.replace("-", " ").split())


@dataclass
class ModeleHorsLigne:
    """Meme interface qu'un fournisseur : il se branche exactement au meme endroit."""

    aujourd_hui: date
    # Le catalogue du salon. Sans lui, on ne devine RIEN : inventer un
    # vocabulaire de metier ferait ecrire « massage » sur l'agenda d'un coiffeur.
    prestations: tuple[str, ...] = ()

    # --- interface de fournisseur ------------------------------------------

    def completer(self, messages: list[dict], **parametres) -> str:
        transcription = next((m["content"] for m in reversed(messages)
                              if m.get("role") == "user"), "")
        return json.dumps(self.analyser(transcription), ensure_ascii=False)

    # --- lecture ------------------------------------------------------------

    def analyser(self, transcription: str) -> dict:
        mots = _mots(transcription)
        jour = self._lire_date(mots)
        heure = self._lire_heure(mots)
        intention = self._lire_intention(mots, jour, heure)
        prestation = self._lire_prestation(mots)
        return {
            "intention": intention,
            "date": jour,
            "heure": heure,
            "prestation": prestation,
            "confiance": {
                "intention": 0.9 if intention != "inconnu" else 0.0,
                "date": 0.9 if jour else 0.0,
                "heure": 0.9 if heure else 0.0,
                "prestation": 0.9 if prestation else 0.0,
            },
            "manque": [champ for champ, valeur in (("date", jour), ("heure", heure))
                       if valeur is None],
        }

    def _lire_prestation(self, mots: list[str]) -> str | None:
        """La prestation nommee par l'appelant, si elle est AU CATALOGUE.

        Le modele hors ligne rendait toujours `None` : la confirmation disait
        « votre rendez-vous » au lieu de « votre coloration », la duree n'etait
        jamais appliquee — donc le salon se double-bookait — et l'agenda ne
        disait pas ce qu'il fallait preparer.

        On tolere ce que le canal abime en fin de mot (« colorations »), avec la
        meme regle que le calendrier, et on refuse des que deux prestations
        correspondent : « coupe » et « coupe enfant » ne se devinent pas.
        """
        if not self.prestations:
            return None
        catalogue = [sans_accents(p).lower() for p in self.prestations]
        for mot in mots:
            rang = indice_dans(sans_accents(mot).lower(), catalogue, SIMPLES)
            if rang is not None:
                return self.prestations[rang]
        # Les prestations en plusieurs mots (« coupe enfant ») : on essaie les
        # paires avant d'abandonner.
        for premier, second in zip(mots, mots[1:]):
            colle = sans_accents(f"{premier} {second}").lower()
            rang = indice_dans(colle, catalogue, SIMPLES)
            if rang is not None:
                return self.prestations[rang]
        return None

    # --- les jours ----------------------------------------------------------

    def _lire_date(self, mots: list[str]) -> str | None:
        texte = " ".join(mots)
        if "apres demain" in texte:
            return (self.aujourd_hui + timedelta(days=2)).isoformat()
        if "demain" in texte:
            return (self.aujourd_hui + timedelta(days=1)).isoformat()
        if "aujourd hui" in texte:
            return self.aujourd_hui.isoformat()

        # « le dix-sept septembre », « le 24 decembre »
        for index, mot in enumerate(mots):
            rang = indice_dans(mot, MOIS, SIMPLES)
            if rang is not None:
                quantieme = self._quantieme_avant(mots, index)
                if quantieme:
                    mois = rang + 1
                    annee = self.aujourd_hui.year
                    candidat = date(annee, mois, quantieme)
                    if candidat < self.aujourd_hui:
                        candidat = date(annee + 1, mois, quantieme)
                    return candidat.isoformat()

        rang = indice_dans_les_mots(mots, JOURS, SIMPLES)
        if rang is not None:
            return self._prochain(rang).isoformat()
        return None

    def _quantieme_avant(self, mots: list[str], index: int) -> int | None:
        """Le quantieme qui precede un mois — en chiffres ou en toutes lettres.

        On essaie la fenetre la PLUS LONGUE d'abord : « dix sept septembre » vaut
        le 17, pas le 7. Depuis que les traits d'union se defont a l'entree, un
        compose arrive en plusieurs mots et la fenetre courte le tronque.
        """
        for recul in (3, 2, 1):
            if index - recul < 0:
                continue
            fenetre = " ".join(mots[index - recul:index])
            valeur = _nombre(fenetre)
            if valeur and 1 <= valeur <= 31:
                return valeur
        return None

    def _prochain(self, indice_jour: int) -> date:
        """Le jour qui vient. « Lundi » dit un mardi, c'est le lundi suivant."""
        ecart = (indice_jour - self.aujourd_hui.weekday()) % 7
        return self.aujourd_hui + timedelta(days=ecart or 7)

    # --- les heures ---------------------------------------------------------

    def _lire_heure(self, mots: list[str]) -> str | None:
        texte = " ".join(mots)
        # « apres-midi » est un moment de la journee, pas une heure : le lire
        # comme midi produisait un creneau que personne n'avait demande.
        sans_moment = texte.replace("apres midi", " ")
        if "midi" in sans_moment and "heure" not in sans_moment:
            return "12:00"

        for index, mot in enumerate(mots):
            if not mot.startswith("heure"):
                continue
            heures = self._heures_avant(mots, index)
            if heures is None:
                continue
            suite = " ".join(mots[index + 1:index + 4])
            minutes = 0
            if suite.startswith("moins le quart"):
                # « neuf heures moins le quart » vaut 8 h 45, jamais 9 h 15 :
                # c'est l'invention qu'un modele a produite a la mesure 14.
                heures, minutes = (heures - 1) % 24, 45
            elif suite.startswith("et quart"):
                minutes = 15
            elif suite.startswith("et demie") or suite.startswith("et demi"):
                minutes = 30
            elif suite.startswith("moins"):
                retire = _nombre(mots[index + 2]) if index + 2 < len(mots) else None
                if retire:
                    heures, minutes = (heures - 1) % 24, 60 - retire
            else:
                valeur = self._minutes_apres(mots, index)
                if valeur is not None:
                    minutes = valeur
            if "apres midi" in texte or "soir" in texte:
                if heures < 12:
                    heures += 12
            return f"{heures:02d}:{minutes:02d}"
        return None

    def _heures_avant(self, mots: list[str], index: int) -> int | None:
        # Fenetre la plus longue d'abord, pour la meme raison : « dix huit
        # heures » vaut 18 h, jamais 8 h.
        for recul in (3, 2, 1):
            if index - recul < 0:
                continue
            fenetre = " ".join(mots[index - recul:index])
            valeur = _nombre(fenetre)
            if valeur is not None and 0 <= valeur <= 23:
                return valeur
        return None

    def _minutes_apres(self, mots: list[str], index: int) -> int | None:
        for avance in (3, 2, 1):
            fenetre = " ".join(mots[index + 1:index + 1 + avance])
            if not fenetre:
                continue
            valeur = _nombre(fenetre)
            if valeur is not None and 0 <= valeur <= 59:
                return valeur
        return None

    # --- l'intention --------------------------------------------------------

    def _lire_intention(self, mots: list[str], jour, heure) -> str:
        texte = " ".join(mots)
        if any(verbe in texte for verbe in VERBES_ANNULATION):
            return "annulation"
        if any(verbe in texte for verbe in VERBES_REPORT):
            return "report"
        if any(verbe in texte for verbe in VERBES_QUESTION):
            return "question"
        if any(verbe in texte for verbe in VERBES_RDV) or (jour and heure):
            return "rdv"
        if jour or heure:
            return "rdv"
        return "inconnu"
