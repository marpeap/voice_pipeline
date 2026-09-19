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


# --- le corpus de régression, alimenté par les corrections ------------------
# `docs/06` : « toute correction alimente automatiquement le corpus de
# régression ». Le registre savait rendre ces scénarios, la porte ne les jouait
# pas : la console promettait au gérant une garantie qui n'existait pas.

def registre_avec_une_correction(tmp_path):
    from standard.correction import Correction, RegistreDeCorrections
    from standard.depot import Depot

    registre = RegistreDeCorrections(depot=Depot(str(tmp_path / "essai.sqlite3")),
                                     tenant="salon-1")
    registre.ajouter(Correction(faute="creneau_inexistant", appel="a-1",
                                empan="midi et demi", valeur={"heure": "12:30"}))
    registre.ajouter(Correction(faute="promesse_interdite", appel="a-2",
                                empan="une remise", valeur={"interdit": "offrir une remise"}))
    return registre


def test_les_corrections_deviennent_des_familles_de_la_porte(tmp_path):
    familles = porte.familles_de_corrections(registre_avec_une_correction(tmp_path))
    assert len(familles) == 2
    for nom, executer in familles.items():
        ok, detail = executer()
        assert ok, f"{nom} : {detail}"


def test_une_correction_qui_ne_tient_plus_ferme_la_porte(tmp_path, monkeypatch):
    """C'est tout l'intérêt : si un changement fait rechuter une correction, la
    porte doit se fermer — sinon la correction tient jusqu'au prochain modèle et
    personne ne voit la rechute.

    On simule la rechute en construisant le service **sans** les corrections,
    exactement ce qui arriverait si le branchement se défaisait."""
    vrai = porte._service_avec
    monkeypatch.setattr(porte, "_service_avec",
                        lambda corrections, heure: vrai([], heure))

    familles = porte.familles_de_corrections(registre_avec_une_correction(tmp_path))
    resultats = [executer()[0] for executer in familles.values()]
    assert False in resultats, "la porte n'a pas vu la rechute"


def test_un_passage_sans_registre_ne_change_rien():
    resultats = porte.un_passage(repetitions=1, bavard=False, registre=None)
    assert all(r["integral"] for r in resultats)
