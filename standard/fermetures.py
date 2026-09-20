"""Les fermetures — jours fériés et congés, que le pack ne savait pas dire.

Le questionnaire ne parle que d'horaires **hebdomadaires** : lundi fermé,
samedi 9 h-18 h. Rien ne disait « du 1er au 15 août », ni « le 25 décembre ».
Un agent qui réserve un créneau un jour férié fait déplacer un client devant un
rideau baissé, et c'est la faute que le commerçant ne pardonne pas : elle lui
coûte un client, pas une minute.

Deux sources, et elles ne se mélangent pas :

- **les jours fériés français**, calculés — pas recopiés. Une liste figée dans
  le code vieillit en silence, et personne ne s'aperçoit qu'elle s'est arrêtée
  à l'an dernier. Le salon décide s'il ferme ces jours-là (beaucoup de coiffeurs
  ouvrent le 14 juillet) ;
- **les fermetures exceptionnelles**, écrites par le commerçant.
"""

from __future__ import annotations

import re
from datetime import date, timedelta

from standard.regles import MOIS
from standard.texte import sans_accents

FERIES_FIXES = ((1, 1), (5, 1), (5, 8), (7, 14), (8, 15), (11, 1), (11, 11), (12, 25))
"""Jour de l'an, fête du Travail, 8-Mai, fête nationale, Assomption,
Toussaint, Armistice, Noël. Le Vendredi saint et la Saint-Étienne, fériés en
Alsace-Moselle, ne sont pas ici : ils dépendent du département, et un salon
concerné les écrira dans ses fermetures."""


def paques(annee: int) -> date:
    """Le dimanche de Pâques, par l'algorithme de Meeus — jamais une table.

    Une table de dates recopiee s'arrete a l'annee ou on l'a ecrite, et rien ne
    le signale : l'agent rouvrirait tranquillement le lundi de Paques suivant.
    """
    a = annee % 19
    b, c = divmod(annee, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mois, jour = divmod(h + l - 7 * m + 114, 31)
    return date(annee, mois, jour + 1)


def jours_feries(annee: int) -> set:
    """Les onze jours fériés français d'une année."""
    dimanche = paques(annee)
    feries = {date(annee, mois, jour) for mois, jour in FERIES_FIXES}
    feries.add(dimanche + timedelta(days=1))    # lundi de Pâques
    feries.add(dimanche + timedelta(days=39))   # Ascension
    feries.add(dimanche + timedelta(days=50))   # lundi de Pentecôte
    return feries


# --- ce que le commerçant écrit ---------------------------------------------

_ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
_FRANCAIS = re.compile(r"(\d{1,2})\s*[/.]\s*(\d{1,2})\s*[/.]\s*(\d{4})")
_EN_LETTRES = re.compile(r"(\d{1,2})\s*(?:er)?\s+([a-zéûôà]+)\s+(\d{4})", re.IGNORECASE)


def _une_date(morceau: str) -> date | None:
    """Une date, dans les trois formes qu'un commerçant écrit spontanément."""
    trouve = _ISO.search(morceau)
    if trouve:
        return _sure(int(trouve.group(1)), int(trouve.group(2)), int(trouve.group(3)))
    trouve = _FRANCAIS.search(morceau)
    if trouve:
        return _sure(int(trouve.group(3)), int(trouve.group(2)), int(trouve.group(1)))
    trouve = _EN_LETTRES.search(morceau)
    if trouve:
        nom = sans_accents(trouve.group(2)).lower()
        mois = next((rang + 1 for rang, m in enumerate(MOIS)
                     if sans_accents(m).lower() == nom), None)
        if mois:
            return _sure(int(trouve.group(3)), mois, int(trouve.group(1)))
    return None


def _sure(annee: int, mois: int, jour: int) -> date | None:
    try:
        return date(annee, mois, jour)
    except ValueError:
        return None          # le 31 février d'un formulaire mal rempli


def _complete(morceau: str, reference: date | None) -> date | None:
    """« du 1er au 3 août 2026 » : le debut n'a ni mois ni annee.

    On les prend a la fin de la plage — c'est ainsi qu'on ecrit une plage en
    francais, et refuser la ligne ferait perdre les conges entiers.
    """
    if reference is None:
        return None
    nombres = re.findall(r"\d{1,2}", morceau)
    if not nombres:
        return None
    jour = int(nombres[0])
    mois_ecrit = _EN_LETTRES.search(f"{jour} {morceau}")
    if mois_ecrit:
        return _une_date(f"{jour} {mois_ecrit.group(2)} {reference.year}")
    return _sure(reference.year, reference.month, jour)


def lire_les_fermetures(texte: str) -> list:
    """Chaque ligne : une date, ou une plage. Ce qui ne se lit pas est ignoré.

    Une ligne illisible ne doit pas emporter les autres — le commerçant en écrit
    plusieurs et ne les relit pas. Une plage à l'envers ne rend rien : mieux
    vaut une fermeture oubliée qu'une année entière fermée par erreur.
    """
    fermetures: list = []
    for ligne in (texte or "").splitlines():
        ligne = ligne.strip()
        if not ligne:
            continue
        separateur = re.split(r"\bau\b|\bjusqu'au\b|\.\.", ligne, maxsplit=1)
        if len(separateur) == 2:
            fin = _une_date(separateur[1])
            debut = _une_date(separateur[0]) or _complete(separateur[0], fin)
            if not debut or not fin or fin < debut:
                continue
            jour = debut
            while jour <= fin:
                fermetures.append(jour)
                jour += timedelta(days=1)
            continue
        seule = _une_date(ligne)
        if seule:
            fermetures.append(seule)
    return sorted(set(fermetures))


def est_ferme(jour: date, fermetures=(), feries: bool = True) -> bool:
    """Ce jour-là, le salon est-il fermé pour une autre raison que son planning ?"""
    if jour in set(fermetures):
        return True
    return bool(feries) and jour in jours_feries(jour.year)
