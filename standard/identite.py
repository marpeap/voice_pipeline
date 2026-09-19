"""Le nom de l'appelant : ce que le salon lira sur son agenda.

Confrontation du 19/09 avec les standards telephoniques IA du marche : tous
capturent le nom de l'appelant, et le notre ecrivait des rendez-vous anonymes.
Une ligne « jeudi 15 h 30 » sans nom ne dit pas qui vient — le salon doit alors
rappeler tout le monde, ce que le produit est cense eviter.

**On ne devine pas.** Ce qui ne ressemble pas a un nom est refuse, et l'agent
redemande : un nom invente sur un agenda est pire qu'un nom absent.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

LONGUEUR_NOM_MAX = 40
"""Au-dela, ce n'est plus un nom : c'est une phrase que le moteur a rendue en
bloc. Meme raison que pour la prestation (`comprehension`)."""

LONGUEUR_NOM_MIN = 2
MOTS_MAX = 4
"""« Jean-Pierre de La Tour » tient en quatre mots ; au-dela, c'est une phrase."""

# Ce qui precede le nom et n'en fait pas partie.
AMORCES = (
    "c'est au nom de", "au nom de", "c'est de la part de", "de la part de",
    "je m'appelle", "mon nom c'est", "mon nom est", "mon nom", "c'est",
    "moi c'est", "je suis",
    # Le moteur mange le « au » : « au nom de Nguyen » revient « NOM DE NGUYEN »,
    # et l'agenda affichait « Nom De Nguyen ». Les amorces sont essayees de la
    # plus longue a la plus courte, donc celle-ci ne prend jamais la place des
    # precedentes.
    "nom de",
)
CIVILITES = ("monsieur", "madame", "mademoiselle", "m", "mr", "mme", "mlle", "docteur")
HESITATIONS = ("euh", "heu", "hum", "ben", "bah", "alors", "voila", "oui", "non")

# Un nom ne peut pas etre une formule de politesse. Sans cette garde, « merci
# au revoir » devenait « Merci Au Revoir » sur l'agenda du salon.
POLITESSES = ("merci", "revoir", "bonjour", "bonsoir", "salut", "journee",
              "parfait", "accord", "bien", "pardon", "excusez")

# Les mots de la langue qui ne sont jamais un nom de famille. Ils servent au
# seul cas ou l'on accepte un nom SANS amorce : le tour qui suit la
# confirmation. « non ce n'est pas ca » y devenait « Ce N'Est Pas Ca ».
MOTS_VIDES = (
    "ce", "c", "n", "ne", "est", "pas", "ca", "cela", "je", "tu", "il", "elle",
    "on", "nous", "vous", "ils", "le", "la", "les", "un", "une", "des", "du",
    "de", "et", "ou", "mais", "plus", "rien", "tout", "que", "qui", "quoi",
    "moi", "toi", "lui", "mon", "ma", "mes", "votre", "vos", "son", "sa",
    "plutot", "autre", "encore", "toujours", "jamais", "ai", "suis", "sais",
)

MOTS_MAX_SANS_AMORCE = 2
"""Sans amorce, un nom tient en deux mots au plus : au-dela, c'est une phrase."""

# Ce qui annonce explicitement un nom. Une correction ne se devine pas : on
# n'accepte un nouveau nom que si l'appelant dit qu'il en donne un.
AMORCES_EXPLICITES = ("c'est au nom de", "au nom de", "nom de",
                      "c'est de la part de", "de la part de", "je m'appelle",
                      "mon nom c'est", "mon nom est", "mon nom", "moi c'est")


def _racine(mot: str) -> str:
    """De quoi rapprocher « journee » de « journée » sans table d'exceptions."""
    from standard.texte import sans_accents

    return sans_accents(mot).lower().strip("'-")


@dataclass(frozen=True)
class LectureNom:
    issue: str          # accepte | refus
    nom: str = ""


def _capitaliser(mot: str) -> str:
    """« DUPONT » devient « Dupont », « d'amico » devient « D'Amico ».

    Les separateurs d'un nom francais sont le trait d'union et l'apostrophe ;
    ce qui les suit porte une majuscule, comme sur une carte d'identite.
    """
    morceau = mot.lower()
    for separateur in ("-", "'", "’"):
        morceau = separateur.join(part[:1].upper() + part[1:]
                                  for part in morceau.split(separateur))
    return morceau[:1].upper() + morceau[1:]


def lire_nom(transcription: str) -> LectureNom:
    """Degage le nom d'une phrase, ou refuse. Jamais de supposition."""
    texte = (transcription or "").strip()
    if not texte:
        return LectureNom("refus")

    plat = texte.lower()
    for amorce in sorted(AMORCES, key=len, reverse=True):
        if plat.startswith(amorce + " "):
            texte = texte[len(amorce):].strip()
            break

    mots = [mot for mot in re.split(r"[\s,.;!?]+", texte) if mot]
    if any(_racine(mot) in POLITESSES for mot in mots):
        return LectureNom("refus")
    while mots and mots[0].lower().strip(".") in CIVILITES + HESITATIONS:
        mots.pop(0)

    if not mots or len(mots) > MOTS_MAX:
        return LectureNom("refus")

    for mot in mots:
        if not re.fullmatch(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’-]*", mot):
            return LectureNom("refus")

    nom = " ".join(_capitaliser(mot) for mot in mots)
    if not LONGUEUR_NOM_MIN <= len(nom) <= LONGUEUR_NOM_MAX:
        return LectureNom("refus")
    return LectureNom("accepte", nom)


def lire_correction_de_nom(transcription: str) -> str | None:
    """Le nom que l'appelant corrige, ou `None` si ce n'en est pas un.

    L'agent redit le nom a voix haute avant de confirmer (regle E1 etendue au
    nom) : c'est la que l'appelant corrige, et c'est le seul moment ou il peut
    le faire avant que le salon ne lise sa fiche. On exige une amorce explicite
    — « c'est au nom de », « je m'appelle » — parce qu'un nom devine dans les
    mots qui suivent un « non » serait pire que pas de correction du tout.
    """
    texte = (transcription or "").strip()
    if not texte:
        return None

    plat = texte.lower()
    for refus in ("non, ", "non "):      # « non c'est Lefevre » : le refus se retire
        if plat.startswith(refus):
            plat = plat[len(refus):]
            break
    plat = plat.strip()
    for amorce in sorted(AMORCES_EXPLICITES, key=len, reverse=True):
        if plat.startswith(amorce):
            lecture = lire_nom(plat)
            return lecture.nom if lecture.issue == "accepte" else None
    if plat.startswith("c'est "):
        # « c'est » tout seul annonce un nom comme il annonce n'importe quoi :
        # « c'est tres aimable a vous » y devenait un nom. On exige donc la
        # lecture stricte — deux mots au plus, aucun mot de la langue.
        lecture = lire_nom_seul(plat)
        return lecture.nom if lecture.issue == "accepte" else None
    return None


def lire_nom_seul(transcription: str) -> LectureNom:
    """Un nom donne sans amorce — le cas du tour qui suit la confirmation.

    Beaucoup plus strict que `lire_nom` : deux mots au plus, et aucun mot de la
    langue. Sans cela, « non ce n'est pas ca » s'ecrivait « Ce N'Est Pas Ca »
    sur l'agenda du salon.
    """
    lecture = lire_nom(transcription)
    if lecture.issue != "accepte":
        return lecture
    mots = lecture.nom.split()
    if len(mots) > MOTS_MAX_SANS_AMORCE:
        return LectureNom("refus")
    if any(_racine(mot) in MOTS_VIDES for mot in mots):
        return LectureNom("refus")
    return lecture
