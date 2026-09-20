"""Ce que contient le paquet qu'on remet — et ce qu'il ne doit jamais contenir.

Le paquet du 21/09 embarquait `standard.sqlite3`, une base créée par erreur en
lançant la console dans le dépôt. Elle était vide ce jour-là. La prochaine
contiendra des noms, des numéros et des transcriptions de vrais clients, et
elle partira dans une archive remise à un tiers.

Un dépôt ne transporte pas de données : c'est la règle, et elle se vérifie.
"""

import re
import pytest
import subprocess
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]


def fichiers_suivis():
    """Ce que git suit — ou rien, s'il n'y a pas de dépôt ici.

    Sur une machine de déploiement, le code arrive par `rsync` sans `.git` :
    ces vérifications portent sur le dépôt, pas sur le service. Les faire
    échouer là-bas apprendrait à ignorer un échec de la suite, ce qui coûte
    bien plus cher que la vérification qu'on perd.
    """
    try:
        sortie = subprocess.run(["git", "ls-files"], cwd=RACINE,
                                capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("hors dépôt git : ces règles portent sur ce qu'on livre, "
                    "pas sur ce qui tourne")
    return [ligne for ligne in sortie.splitlines() if ligne]


def test_aucune_base_de_donnees_n_est_livree():
    bases = [f for f in fichiers_suivis() if re.search(r"\.sqlite3?(-wal|-shm)?$", f)]
    assert bases == [], f"le paquet transporte des données : {bases}"


def test_aucun_journal_ni_audio_n_est_livre():
    interdits = [f for f in fichiers_suivis() if f.endswith((".log", ".wav"))]
    assert interdits == [], interdits


def test_les_mesures_restent_mais_pas_le_resultat_de_la_porte():
    """Les résultats des bancs de mesure sont la **preuve** sur laquelle repose
    chaque règle du produit : ils restent, et `docs/09` les cite.

    `porte-resultats.json` est différent : il est réécrit à chaque passage de la
    porte, donc plusieurs fois par jour. Le suivre transforme chaque vérification
    en modification, et on finit par valider un diff sans le lire."""
    suivis = fichiers_suivis()
    assert any(f.endswith("wer-resultats.json") for f in suivis), (
        "les mesures ne doivent pas disparaître : elles justifient les règles")
    assert "bancs/porte-resultats.json" not in suivis


def test_le_gitignore_couvre_ce_qui_se_crée_en_marchant():
    """Les fichiers qu'un service produit en tournant : la garde doit exister
    AVANT qu'on s'y reprenne."""
    if not (RACINE / ".gitignore").exists():
        pytest.skip("hors dépôt git")
    ignore = (RACINE / ".gitignore").read_text()
    for motif in ("*.sqlite3", "*.sqlite3-wal", "*.sqlite3-shm",
                  "bancs/porte-resultats.json"):
        assert motif in ignore, f"« {motif} » manque au .gitignore"


def test_les_dependances_du_chemin_hors_ligne_suffisent_a_la_demonstration():
    """`requirements.txt` est ce qu'un lecteur du README installe. Il doit
    suffire à `demonstration.py` et à la suite de tests — les moteurs réels ont
    leur propre fichier, parce qu'ils pèsent des centaines de mégaoctets."""
    requis = (RACINE / "requirements.txt").read_text().lower()
    assert "pyyaml" in requis and "pytest" in requis
    for lourd in ("piper", "sherpa", "onnx"):
        assert lourd not in requis, (
            f"« {lourd} » n'a rien à faire dans le fichier de base")
    assert (RACINE / "requirements-moteurs.txt").exists(), (
        "les moteurs réels doivent avoir leur fichier, et le README doit le dire")


def test_les_commandes_disent_quelle_base_elles_ouvrent():
    """La base par défaut est relative au répertoire courant : lancée d'ailleurs,
    la console ouvre un AUTRE fichier, vide, et le commerçant croit avoir tout
    perdu. C'est exactement comme cela qu'un `standard.sqlite3` s'est retrouvé
    commité dans le dépôt le 20/09 — personne ne voyait quel fichier servait."""
    import inspect

    from standard import __main__ as principal

    source = inspect.getsource(principal)
    assert "os.path.abspath" in source or "resolve()" in source, (
        "le chemin de la base doit être affiché en absolu au démarrage")
    assert source.count("base :") >= 1
