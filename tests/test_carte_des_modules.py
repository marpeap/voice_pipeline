"""Le dépôt et sa carte ne doivent pas diverger.

`docs/22-SPEC-MODULES.md` prétend donner, pour chaque module, son contrat et le
test qui le prouve. Il décrivait cinq modules ; il y en a trente-sept. Un
document exhaustif qui ment par omission envoie le prochain lecteur dans le
mur — et ce prochain lecteur, c'est souvent moi trois jours plus tard.

Ce fichier ne relit pas la prose : il vérifie deux choses mécaniques, celles
qui se périment toutes seules.
"""

import ast
import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
CARTE = RACINE / "docs" / "22-SPEC-MODULES.md"

SANS_CONTRAT = {"__init__", "__main__"}
"""Le point d'entrée et le paquet n'ont pas de contrat propre : ils assemblent."""


def modules():
    return sorted(chemin.stem for chemin in (RACINE / "standard").glob("*.py")
                  if chemin.stem not in SANS_CONTRAT)


def test_il_y_a_bien_des_modules_a_verifier():
    """Sans cette garde, les deux tests suivants passeraient sur du vide."""
    assert len(modules()) > 20


@pytest.mark.parametrize("module", modules())
def test_chaque_module_figure_sur_la_carte(module):
    texte = CARTE.read_text()
    assert f"`{module}`" in texte, (
        f"« {module} » n'est nulle part dans docs/22 : la carte ment par omission")


@pytest.mark.parametrize("module", modules())
def test_chaque_module_est_couvert_par_au_moins_un_test(module):
    """« Chaque module naît avec le test qui l'échoue » — la règle du document.
    On vérifie qu'un test l'importe vraiment, pas qu'un fichier porte son nom."""
    importe = False
    for fichier in (RACINE / "tests").glob("test_*.py"):
        arbre = ast.parse(fichier.read_text())
        for noeud in ast.walk(arbre):
            if isinstance(noeud, ast.ImportFrom) and noeud.module:
                if noeud.module == f"standard.{module}":
                    importe = True
            elif isinstance(noeud, ast.Import):
                if any(a.name == f"standard.{module}" for a in noeud.names):
                    importe = True
        if importe:
            break
    assert importe, f"aucun test n'importe « standard.{module} »"


def test_la_carte_ne_promet_pas_de_module_qui_n_existe_pas():
    """L'inverse compte autant : un module décrit et jamais écrit se cherche
    pendant une heure."""
    texte = CARTE.read_text()
    cites = set(re.findall(r"`standard\.(\w+)`", texte))
    manquants = {nom for nom in cites
                 if not (RACINE / "standard" / f"{nom}.py").exists()}
    assert manquants == set(), f"décrits mais absents : {sorted(manquants)}"
