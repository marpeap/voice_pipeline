"""Dire oui, dire non — la moitié la plus courte d'une conversation, et la plus décisive.

Une revue indépendante a trouvé le 19/09 que le produit ne pouvait prendre aucun
rendez-vous : l'agent proposait un créneau, l'appelant disait « oui », et ce
« oui » repartait dans l'analyse générale comme une nouvelle demande. **Rien ne
s'écrivait jamais.**

Ce module existe pour que ce moment-là soit traité explicitement. Il ne fait
appel à aucun modèle : reconnaître un « oui » ne se sous-traite pas à un service
distant dont la latence est une variable aléatoire, et dont le catalogue peut
changer du jour au lendemain.

**On ne devine pas.** Ce qui n'est ni un accord ni un refus reconnu retourne au
chemin normal — l'appelant sera simplement compris comme s'il posait une nouvelle
demande, ce qui est le comportement sûr.
"""

from __future__ import annotations

import re
import unicodedata

OUI = (
    "oui", "ouais", "c'est parfait", "parfait", "d'accord", "daccord", "ok",
    "ca me va", "ça me va", "ca marche", "ça marche", "tres bien", "très bien",
    "c'est note", "c'est bon", "allez-y", "allons-y", "je confirme", "confirmez",
    "va pour", "entendu", "impeccable", "nickel", "super",
)

NON = (
    "non", "pas possible", "ca ne va pas", "ça ne va pas", "ca m'arrange pas",
    "autre", "plutot", "plutôt", "annulez", "laissez tomber", "finalement non",
    "ca ne marche pas", "ça ne marche pas", "j'aimerais autre chose",
)

# « non merci » est un refus, « oui merci » un accord : le premier mot decide.
NEGATIONS = ("non", "pas", "jamais", "aucun")


def _plat(texte: str) -> str:
    plat = unicodedata.normalize("NFD", texte.lower())
    plat = "".join(c for c in plat if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z' ]", " ", plat)).strip()


def est_un_refus(transcription: str) -> bool:
    plat = _plat(transcription)
    if not plat:
        return False
    return any(_plat(marque) in plat for marque in NON)


def est_un_oui(transcription: str) -> bool:
    """Vrai seulement si l'accord est net **et** qu'aucune négation ne le précède.

    « oui mais pas jeudi » n'est pas un accord : c'est une nouvelle demande, et la
    traiter comme un « oui » écrirait le mauvais rendez-vous — la faute la plus
    chère du produit.
    """
    plat = _plat(transcription)
    if not plat or est_un_refus(transcription):
        return False
    if not any(_plat(marque) in plat for marque in OUI):
        return False
    return not any(f" {negation} " in f" {plat} " for negation in NEGATIONS)
