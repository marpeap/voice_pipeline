"""La porte de non-regression tourne avec les tests, en un seul passage rapide.

Le passage complet (pass^5, deux passages) reste une commande a part —
`bancs/porte.py --passages 2` —, mais rien ne doit pouvoir casser la porte sans
que la suite de tests le dise.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bancs"))

import porte  # noqa: E402


def test_toutes_les_familles_passent_en_un_coup():
    resultats = porte.un_passage(repetitions=1, bavard=False)
    echecs = [r["famille"] for r in resultats if not r["integral"]]
    assert echecs == [], f"familles en echec : {echecs}"


def test_le_fichier_de_donnees_et_le_code_ne_divergent_pas():
    """Une famille declaree dans porte.json doit etre executee, ou explicitement
    exemptee (bruit et latence demandent l'audio et un service qui tourne)."""
    import json
    definition = json.loads((Path(porte.__file__).parent / "porte.json").read_text())
    declarees = {f["nom"] for f in definition["familles"]}
    manquantes = declarees - set(porte.FAMILLES) - {"bruit", "latence"}
    assert manquantes == set(), f"declarees mais jamais executees : {sorted(manquantes)}"
