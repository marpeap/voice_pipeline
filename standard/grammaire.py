"""Grammaire francaise des nombres — la piece qui decide si le rendez-vous existe.

Mesure 7 : quatre numeros de telephone sur dix sont perdus, et **exactement de la
meme facon en 16 kHz et en 8 kHz**. Le canal n'y est pour rien ; ce qui casse,
c'est la lecture des nombres francais. Ce module est donc le filet, et les regles
qu'il applique (T1 a T10) sont ecrites dans docs/10-GRAMMAIRE-FRANCAISE.md.

Principe directeur : **on ne devine jamais.** Un numero qui ne se reconstruit pas
sous contrainte se fait relire a voix haute, il ne se complete pas.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# --- vocabulaire -------------------------------------------------------------

SIMPLES = {
    "zero": 0, "un": 1, "une": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5,
    "six": 6, "sept": 7, "huit": 8, "neuf": 9, "dix": 10, "onze": 11, "douze": 12,
    "treize": 13, "quatorze": 14, "quinze": 15, "seize": 16,
}
DIZAINES = {"vingt": 20, "vingts": 20, "trente": 30, "quarante": 40,
            "cinquante": 50, "soixante": 60}

# Un marqueur de correction annule le dernier groupe enonce, et lui seul (T9).
# Mesure 7 : l'auto-correction est parfaitement transcrite — l'echec etait a
# l'interpretation, donc c'est ici qu'il se repare.
MARQUEURS = {"non", "pardon", "plutot", "excusez", "excusez-moi", "erreur", "trompe"}

PREFIXES_VALIDES = tuple(f"0{c}" for c in "123456789")
PREFIXES_INTERDITS = ("08",)  # numeros speciaux : T1


def normaliser(texte: str) -> str:
    texte = unicodedata.normalize("NFD", texte.lower())
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    texte = texte.replace("'", " ")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9+\- ]", " ", texte)).strip()


def _jetons(texte: str) -> list[str]:
    """Decoupe en jetons, en gardant les composes (« quatre-vingt-dix-huit »)."""
    return [j for j in normaliser(texte).split(" ") if j]


def _valeur_composee(morceaux: list[str]) -> int | None:
    """Valeur d'un groupe francais ecrit en toutes lettres, ou None.

    Couvre les pieges du francais : soixante-dix, quatre-vingts, quatre-vingt-douze,
    soixante et onze. Le compose ne se casse JAMAIS en ses morceaux — c'est
    exactement la faute qui produit onze chiffres (T8).
    """
    morceaux = [m for m in morceaux if m and m != "et"]
    if not morceaux:
        return None

    if morceaux[0] in ("quatre",) and len(morceaux) >= 2 and morceaux[1] in ("vingt", "vingts"):
        reste = morceaux[2:]
        if not reste:
            return 80
        suite = _valeur_composee(reste)
        return 80 + suite if suite is not None and suite < 20 else None

    if morceaux[0] in DIZAINES:
        base = DIZAINES[morceaux[0]]
        reste = morceaux[1:]
        if not reste:
            return base
        suite = _valeur_composee(reste)
        if suite is None:
            return None
        if base == 60 and suite <= 19:      # soixante-dix a soixante-dix-neuf
            return 60 + suite
        if suite <= 9:
            return base + suite
        return None

    if morceaux[0] in SIMPLES:
        base = SIMPLES[morceaux[0]]
        reste = morceaux[1:]
        if not reste:
            return base
        if base == 10:                      # dix-sept, dix-huit, dix-neuf
            suite = _valeur_composee(reste)
            if suite is not None and 7 <= suite <= 9:
                return 10 + suite
        return None

    return None


@dataclass
class Groupe:
    """Un groupe prononce : « douze » ou « trente-quatre », jamais deux nombres."""
    valeur: int
    chiffres: str
    source: str


def _composables(jetons: list[str], depart: int) -> int:
    """Combien de jetons consecutifs forment UN SEUL nombre francais.

    « quarante trois » vaut 43 comme « quarante-trois » : a l'oral, l'espace et le
    trait d'union ne s'entendent pas. En revanche « six douze » reste deux groupes
    — seules les formes que le francais compose reellement sont fusionnees
    (dizaine + unite, soixante + 10-19, quatre-vingt(s) + unite, « et un »).
    """
    meilleure = 1
    for fin in range(depart + 1, min(depart + 4, len(jetons)) + 1):
        morceaux = []
        for jeton in jetons[depart:fin]:
            morceaux.extend(jeton.split("-"))
        if _valeur_composee(morceaux) is not None and fin - depart > meilleure:
            # Une forme plus longue n'est retenue que si elle compose vraiment.
            meilleure = fin - depart
    return meilleure


def _groupes(texte: str) -> list[Groupe]:
    """Suite de groupes, marqueurs de correction appliques (T9)."""
    groupes: list[Groupe] = []
    jetons = _jetons(texte)
    # Une reprise apres marqueur peut recommencer plus tot que le dernier groupe :
    # « zero six, pardon, zero sept » refait le debut, il ne corrige pas « six ».
    reprise = False
    index = 0
    while index < len(jetons):
        longueur = _composables(jetons, index)
        jeton = " ".join(jetons[index:index + longueur])
        index += longueur
        if jeton in MARQUEURS or jeton.rstrip("-") in MARQUEURS:
            if groupes:
                groupes.pop()          # le marqueur annule le dernier groupe enonce
            reprise = True
            continue
        if jeton.startswith("+"):
            jeton = jeton[1:]
            if not jeton:
                continue
        if jeton.isdigit():
            valeur, chiffres = int(jeton), jeton
        else:
            morceaux = []
            for part in jeton.split(" "):
                morceaux.extend(part.split("-"))
            valeur = _valeur_composee(morceaux)
            if valeur is None:
                continue                # mot inintelligible : il ne porte pas de chiffre
            chiffres = f"{valeur:02d}" if valeur >= 10 else str(valeur)

        if reprise and groupes and groupes[-1].valeur == valeur:
            # La reprise repete le groupe d'avant : c'est tout le debut qu'on refait.
            groupes.pop()
        reprise = False
        groupes.append(Groupe(valeur, chiffres, jeton))
    return groupes


def mots_vers_chiffres(texte: str) -> str:
    """Suite de chiffres portee par un texte, composes respectes."""
    return "".join(g.chiffres for g in _groupes(texte))


# --- lecture d'un numero -----------------------------------------------------

@dataclass
class Lecture:
    """Ce que la machine a compris, et ce qu'elle a le droit d'en faire."""
    issue: str                       # accepte | relecture | refus
    numero: str | None = None
    relecture: str | None = None     # ce que l'agent doit prononcer (T6)
    confirmation_obligatoire: bool = True
    explication: str = ""            # pour le journal d'appel, jamais pour le client
    groupes: list[str] = field(default_factory=list)


def _prefixe_acceptable(numero: str) -> bool:
    return (len(numero) == 10 and numero.startswith("0")
            and numero[:2] not in PREFIXES_INTERDITS
            and numero[:2] in PREFIXES_VALIDES)


def _refusions_possibles(groupes: list[Groupe]) -> list[tuple[str, str]]:
    """Refusions d'une sur-segmentation : une dizaine suivie d'une unite (T8).

    Mesure 7 : « quarante-trois » ressort en « 40 3 » chez le moteur qui ecrit des
    chiffres. Si UNE SEULE refusion ramene a dix chiffres, on la propose et on la
    fait confirmer ; s'il y en a plusieurs, on ne tranche pas.
    """
    candidats = []
    for i in range(len(groupes) - 1):
        a, b = groupes[i], groupes[i + 1]
        if a.valeur in (20, 30, 40, 50, 60, 80) and 1 <= b.valeur <= 9:
            fusion = a.valeur + b.valeur
            chiffres = "".join(
                g.chiffres for g in groupes[:i]
            ) + f"{fusion:02d}" + "".join(g.chiffres for g in groupes[i + 2:])
            candidats.append((chiffres, f"« {a.source} » et « {b.source} » relus comme {fusion}"))
    return candidats


def lire_numero(texte: str) -> Lecture:
    """Applique T1 a T9 et rend une lecture, jamais une supposition."""
    groupes = _groupes(texte)
    chiffres = "".join(g.chiffres for g in groupes)
    trace = [g.source for g in groupes]

    # T5 — format international : +33 suivi de neuf chiffres vaut 0 + les memes.
    if chiffres.startswith("33") and len(chiffres) == 11:
        chiffres = "0" + chiffres[2:]

    if not chiffres:
        return Lecture("relecture", relecture=None, explication="aucun chiffre entendu",
                       groupes=trace)

    # T2 et T3 — le zero initial ne se croit jamais : neuf chiffres lisibles et un
    # debut inintelligible se reconstruisent sous contrainte.
    if len(chiffres) == 9 and _prefixe_acceptable("0" + chiffres):
        chiffres = "0" + chiffres

    if len(chiffres) == 10:
        if chiffres[:2] in PREFIXES_INTERDITS:
            return Lecture("refus", explication="numero special (08), non pris en charge",
                           groupes=trace)
        if not _prefixe_acceptable(chiffres):
            return Lecture("refus", explication=f"prefixe impossible : {chiffres[:2]}",
                           groupes=trace)
        return Lecture("accepte", numero=chiffres, relecture=enoncer_numero(chiffres),
                       confirmation_obligatoire=True, groupes=trace)

    # T8 — onze chiffres : une seule refusion valide, ou rien.
    if len(chiffres) == 11:
        candidats = [(c, pourquoi) for c, pourquoi in _refusions_possibles(groupes)
                     if _prefixe_acceptable(c)]
        uniques = {c for c, _ in candidats}
        if len(uniques) == 1:
            numero, pourquoi = candidats[0]
            return Lecture("accepte", numero=numero, relecture=enoncer_numero(numero),
                           confirmation_obligatoire=True, explication=pourquoi, groupes=trace)

    # T4 — on ne complete jamais : on relit ce qu'on a compris et on redemande.
    return Lecture("relecture", explication=f"{len(chiffres)} chiffres entendus, il en faut dix",
                   groupes=trace)


# --- enonciation -------------------------------------------------------------

_UNITES = ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit",
           "neuf", "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize",
           "dix-sept", "dix-huit", "dix-neuf"]
_DIZAINES = {2: "vingt", 3: "trente", 4: "quarante", 5: "cinquante", 6: "soixante"}


def en_lettres(n: int) -> str:
    """Un nombre de 0 a 99 en toutes lettres, pieges du francais compris."""
    if n < 20:
        return _UNITES[n]
    if n < 70:
        d, u = divmod(n, 10)
        if u == 0:
            return _DIZAINES[d]
        if u == 1:
            return f"{_DIZAINES[d]} et un"
        return f"{_DIZAINES[d]}-{_UNITES[u]}"
    if n < 80:
        reste = n - 60
        return "soixante et onze" if reste == 11 else f"soixante-{_UNITES[reste]}"
    reste = n - 80
    if reste == 0:
        return "quatre-vingts"
    return f"quatre-vingt-{_UNITES[reste]}"


def enoncer_numero(numero: str) -> str:
    """Relecture par groupes de deux (T6), inconditionnelle depuis la mesure 21.

    Le moteur qui ecrit des chiffres tranche les ambiguites en silence : il n'y a
    plus de doute observable en aval, donc la relecture ne peut plus etre
    conditionnee a un doute. Mesure 19 : cette relecture survit au canal.
    """
    paires = [numero[i:i + 2] for i in range(0, len(numero), 2)]
    dits = []
    for index, paire in enumerate(paires):
        if index == 0:
            dits.append(f"{en_lettres(int(paire[0]))} {en_lettres(int(paire[1]))}")
        else:
            dits.append(en_lettres(int(paire)))
    return ", ".join(dits)
