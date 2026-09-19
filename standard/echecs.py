"""Les quatre règles de détection d'échec (T6 de `docs/17`).

Un appel « réussi » se reconnaît mal : l'agent a parlé, personne n'a crié. Ces
quatre règles disent l'inverse — ce qui n'a pas marché — et elles sont
volontairement grossières, parce qu'un signal grossier qu'on regarde vaut mieux
qu'un score fin que personne ne lit.

La quatrième est la plus contre-intuitive : **un transfert compte comme un
échec**. Ce n'est pas une panne, c'est un appel que l'agent n'a pas su traiter.
Le sortir du compte rendrait le taux flatteur, et c'est précisément le chiffre
sur lequel on décide d'élargir le pack.
"""

from __future__ import annotations

from standard.regles import DUREE_MINIMALE_D_UN_VRAI_APPEL_S, REFORMULATIONS_AVANT_ECHEC


def detecter_l_echec(appel: dict) -> str | None:
    """Rend le motif d'échec, ou `None` si l'appel s'est passé normalement."""
    tours = appel.get("tours") or []

    if float(appel.get("duree_s") or 0) < DUREE_MINIMALE_D_UN_VRAI_APPEL_S:
        # Personne ne prend un rendez-vous en six secondes : soit l'appelant a
        # raccroche, soit la ligne a lache.
        return "raccroche_tot"

    if sum(1 for t in tours if t.get("genre") == "reformulation") >= REFORMULATIONS_AVANT_ECHEC:
        return "reformulations"

    if tours and not any((t.get("transcription") or "").strip() for t in tours):
        # L'agent a parle dans le vide : rien de l'appelant n'a ete compris.
        return "silence"

    if any(t.get("genre") == "transfert" for t in tours):
        return "demande_humain"

    return None


# Ce que le commercant lit — jamais le nom technique du motif.
LIBELLES = {
    "raccroche_tot": "l'appelant a raccroché tout de suite",
    "reformulations": "l'agent a tourné en rond",
    "silence": "l'agent n'a rien entendu de l'appelant",
    "demande_humain": "l'appelant a demandé quelqu'un du salon",
}


def libelle(motif: str | None) -> str:
    """Le motif en francais courant, ou une chaine vide s'il n'y en a pas."""
    return LIBELLES.get(motif or "", "")
