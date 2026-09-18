"""Le locataire — du questionnaire au fichier de connaissance de l'agent.

Parti pris de docs/05 : **le commercant ne voit jamais un prompt.** Il repond a
des questions issues d'un pack sectoriel, et le systeme ecrit le fichier.

Deux invariants tiennent tout le reste :

1. **L'interface remplace le bloc frontmatter, jamais le corps.** Le Markdown
   ecrit par le commercant n'est jamais reparse ni reecrit — sinon un aller-retour
   abime ce qu'il a voulu dire, et il ne le sait pas.
2. **Un salon qui ne repond rien obtient quand meme un agent qui fonctionne.**
   Les defauts ne sont pas ecrits ici : ils sont **derives du pack**, seule source.
"""

from __future__ import annotations

import yaml

from dataclasses import dataclass, field
from typing import Any

SEPARATEUR = "---"


def questions_du_pack(pack: dict) -> list[dict]:
    """Les questions, a plat, dans l'ordre des paliers puis des blocs.

    Le palier 0 est ce qu'il faut pour decrocher ; on ne fait pas remplir le
    palier 2 a quelqu'un qui n'a pas encore d'agent qui repond.
    """
    questions = []
    for bloc in pack.get("blocs", []):
        for question in bloc.get("questions", []):
            questions.append({**question,
                              "bloc": bloc["id"],
                              "palier": question.get("palier", bloc.get("palier", 0))})
    return sorted(questions, key=lambda q: (q["palier"], q["bloc"]))


def _defaut_de_question(question: dict) -> Any:
    """Le defaut d'une question, tel que le pack le declare — jamais devine."""
    if "defaut" in question:
        return question["defaut"]
    options = question.get("options", [])
    coches = [o["valeur"] for o in options if o.get("defaut")]
    if not coches:
        return [] if question.get("type") == "choix_multiple" else None
    return coches if question.get("type") == "choix_multiple" else coches[0]


def reponses_par_defaut(pack: dict) -> dict[str, Any]:
    """Toutes les reponses par defaut du pack, derivees et non recopiees."""
    return {q["id"]: _defaut_de_question(q) for q in questions_du_pack(pack)}


def paliers_manquants(pack: dict, reponses: dict) -> list[str]:
    """Les questions critiques encore sans reponse.

    Tant qu'il en reste une, l'agent ne peut pas etre active : ce sont exactement
    celles dont l'absence produit une erreur **entendue par le client**.
    """
    manquants = []
    for question in questions_du_pack(pack):
        if not question.get("critique"):
            continue
        valeur = reponses.get(question["id"], _defaut_de_question(question))
        if valeur in (None, "", [], {}):
            manquants.append(question["id"])
    return manquants


def _poser(racine: dict, chemin: str, valeur: Any) -> None:
    """Ecrit `valeur` a `chemin` (« horaires.coupure ») dans un dictionnaire."""
    morceaux = chemin.split(".")
    courant = racine
    for morceau in morceaux[:-1]:
        courant = courant.setdefault(morceau, {})
    courant[morceaux[-1]] = valeur


def _rendre_yaml(donnees: dict) -> str:
    """Rendu par une bibliotheque eprouvee, pas par un YAML maison.

    J'avais ecrit le mien : il rendait les listes comme des dictionnaires vides,
    et les tests l'ont attrape tout de suite. Un format qu'on lit ET qu'on ecrit
    n'est jamais « assez simple pour etre bricole » — surtout quand un commercant
    relit le fichier a l'oeil.
    """
    return yaml.safe_dump(donnees, allow_unicode=True, sort_keys=False,
                          default_flow_style=False).rstrip("\n")


def _vocabulaire(pack: dict, reponses: dict) -> list[str]:
    """Le lexique injecte suit les prestations cochees.

    C'est ce qui tient la limite recommandee de 20 a 50 termes, au lieu de
    deverser tout le vocabulaire du metier dans le prompt (docs/05, regle 5).
    """
    termes = list(pack.get("keyterms", {}).get("groupe1", []))
    groupe3 = pack.get("keyterms", {}).get("groupe3", {})
    coches = reponses.get("C1")
    if coches is None:
        coches = _defaut_de_question(
            next((q for q in questions_du_pack(pack) if q["id"] == "C1"), {})) or []
    if isinstance(coches, str):
        coches = [coches]
    for prestation in coches:
        termes.extend(groupe3.get(prestation, []))
    return termes


@dataclass
class Memoire:
    """Ce que l'agent sait d'un salon : un bloc machine, et une prose intacte."""
    frontmatter: dict = field(default_factory=dict)
    corps: str = ""

    @property
    def interdits(self) -> list[str]:
        return list(self.frontmatter.get("interdits", []))

    @property
    def vocabulaire(self) -> list[str]:
        return list(self.frontmatter.get("vocabulaire", []))


def composer_memoire(pack: dict, reponses: dict, corps: str) -> str:
    """Regenere le frontmatter a partir des reponses, et **recolle le corps tel quel**.

    Le corps n'est ni analyse, ni normalise, ni meme relu : il est concatene. Une
    ligne de tirets au milieu de la prose du commercant ne casse donc rien.
    """
    donnees: dict[str, Any] = {}
    for question in questions_du_pack(pack):
        cible = question.get("ecrit", {})
        if cible.get("cible") != "frontmatter":
            continue
        valeur = reponses.get(question["id"], _defaut_de_question(question))
        if valeur in (None, "", []):
            # Une question non repondue ne cree pas de cle vide, SAUF si le pack
            # la declare non desactivable : l'annonce doit toujours exister.
            if not question.get("obligatoire_non_desactivable"):
                continue
            valeur = _defaut_de_question(question)
        _poser(donnees, cible["chemin"], valeur)

    interdits = list(pack.get("interdits", []))
    interdits += [regle["regle"] for regle in pack.get("interdits_cables", [])]
    if interdits:
        donnees["interdits"] = interdits
    vocabulaire = _vocabulaire(pack, reponses)
    if vocabulaire:
        donnees["vocabulaire"] = vocabulaire
    donnees["pack"] = f"{pack['pack']} {pack['version']}"

    return f"{SEPARATEUR}\n{_rendre_yaml(donnees)}\n{SEPARATEUR}\n\n{corps}"


def lire_memoire(texte: str) -> Memoire:
    """Separe le bloc machine de la prose, sans jamais toucher a la seconde.

    Seul le **premier** bloc delimite compte : tout ce qui suit appartient au
    commercant, y compris d'autres lignes de tirets.
    """
    if not texte.startswith(SEPARATEUR):
        return Memoire({}, texte)
    fin = texte.find(f"\n{SEPARATEUR}\n", len(SEPARATEUR))
    if fin == -1:
        return Memoire({}, texte)
    brut = texte[len(SEPARATEUR) + 1:fin]
    corps = texte[fin + len(SEPARATEUR) + 2:]
    if corps.startswith("\n"):
        corps = corps[1:]
    return Memoire(_lire_yaml(brut), corps)


def _lire_yaml(brut: str) -> dict:
    """Le bloc que nous avons ecrit, relu par la meme bibliotheque."""
    charge = yaml.safe_load(brut)
    return charge if isinstance(charge, dict) else {}
