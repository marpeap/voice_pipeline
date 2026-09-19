"""Normaliser du texte français — une seule fois pour tout le produit.

Quatre modules avaient chacun leur normaliseur d'accents, tous légèrement
différents : `conformite`, `sms`, `langue`, `comprehension`. Quatre versions
d'une même règle, c'est trois occasions de diverger — et la divergence se voit
d'abord chez le client, quand une phrase est reconnue à un endroit et pas à un
autre.
"""

from __future__ import annotations

import re
import unicodedata


def sans_accents(texte: str) -> str:
    """Minuscules, accents ôtés. Rien d'autre n'est touché."""
    plat = unicodedata.normalize("NFD", texte.lower())
    return "".join(c for c in plat if unicodedata.category(c) != "Mn")


def aplatir(texte: str, garder: str = "a-z0-9 ") -> str:
    """Minuscules, sans accents, sans ponctuation — pour comparer des mots.

    L'apostrophe devient une espace : « l'agent » et « l agent » sont le même
    mot à l'oreille, et c'est l'oreille qui fait foi dans ce produit.
    """
    plat = sans_accents(texte).replace("'", " ")
    return re.sub(r"\s+", " ", re.sub(fr"[^{garder}]", " ", plat)).strip()
