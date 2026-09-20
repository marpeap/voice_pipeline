"""Le droit à l'effacement — promis par écrit, jamais implémenté.

L'accord de test remis au salon pilote (`docs/18`) promet : « le salon peut
arrêter le test à tout moment (…) les enregistrements sont alors supprimés sous
sept jours ». Le RGPD dit la même chose (art. 17). Rien dans le produit ne
savait effacer un locataire : il aurait fallu ouvrir la base à la main, table
par table, en espérant n'en oublier aucune.

Une table oubliée est une promesse trahie — c'est pourquoi le test parcourt
**toutes** les tables qui portent un `tenant_id`, au lieu d'en nommer cinq.
"""

import pytest

from standard.audit import PisteDAudit
from standard.correction import Correction, RegistreDeCorrections
from standard.depot import Depot
from standard.journal import JournalDAppels

APPEL = {"uuid": "u-1", "debut": "2026-09-19T10:00:00+00:00", "duree_s": 30,
         "issue": "rendez-vous", "tours": [{"genre": "question",
                                            "transcription": "jeudi"}]}


def base_pleine(tmp_path, tenant="salon-1"):
    depot = Depot(str(tmp_path / "essai.sqlite3"))
    acces = depot.pour(tenant)
    acces.inserer("cle-1", {"date": "2026-09-17", "heure": "15:30", "nom": "Dupont"})
    acces.enregistrer_message({"texte": "rappelez-moi", "telephone": "0612345678"})
    acces.enregistrer_reponses({"A1": "Salon Elegance"})
    JournalDAppels(depot).enregistrer(tenant, APPEL)
    PisteDAudit(depot).noter(tenant, acteur="console", action="correction.posee",
                             cible="cor-0001", detail={})
    RegistreDeCorrections(depot=depot, tenant=tenant).ajouter(
        Correction(faute="creneau_inexistant", appel="u-1", empan="",
                   valeur={"heure": "12:30"}))
    return depot


def lignes_par_table(depot, tenant):
    """Compte, table par table, ce qui reste de ce locataire."""
    with depot._verrou:
        tables = [ligne["name"] for ligne in depot._connexion.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'")]
        restes = {}
        for table in tables:
            colonnes = [c["name"] for c in depot._connexion.execute(
                f"PRAGMA table_info({table})")]
            if "tenant_id" not in colonnes:
                continue
            restes[table] = depot._connexion.execute(
                f"SELECT COUNT(*) AS n FROM {table} WHERE tenant_id = ?",
                (tenant,)).fetchone()["n"]
    return restes


def test_avant_effacement_toutes_les_tables_portent_quelque_chose(tmp_path):
    depot = base_pleine(tmp_path)
    restes = lignes_par_table(depot, "salon-1")
    assert restes and all(n > 0 for n in restes.values()), restes


def test_effacer_un_locataire_ne_laisse_rien_derriere(tmp_path):
    depot = base_pleine(tmp_path)
    compte = depot.effacer_le_locataire("salon-1")
    assert sum(compte.values()) > 0
    assert all(n == 0 for n in lignes_par_table(depot, "salon-1").values())


def test_effacer_un_locataire_ne_touche_pas_a_son_voisin(tmp_path):
    depot = base_pleine(tmp_path)
    base_pleine(tmp_path, "salon-2")        # même fichier, autre locataire
    depot.effacer_le_locataire("salon-1")
    assert all(n > 0 for n in lignes_par_table(depot, "salon-2").values())


def test_effacer_sans_locataire_refuse(tmp_path):
    with pytest.raises(ValueError):
        base_pleine(tmp_path).effacer_le_locataire("")


def test_le_compte_rendu_dit_ce_qui_a_ete_efface(tmp_path):
    compte = base_pleine(tmp_path).effacer_le_locataire("salon-1")
    assert compte["rendez_vous"] == 1
    assert compte["messages"] == 1
    assert compte["appels"] == 1


# --- la commande d'exploitation ---------------------------------------------

def test_la_commande_exige_le_nom_du_locataire_deux_fois(tmp_path, capsys, monkeypatch):
    """Une commande qui efface ne doit pas s'exécuter par erreur de flèche haute :
    le nom se retape, sinon rien ne se passe."""
    from standard.__main__ import main

    depot = base_pleine(tmp_path)
    chemin = str(tmp_path / "essai.sqlite3")
    monkeypatch.setenv("STANDARD_BASE", chemin)

    code = main(["effacer", "--tenant", "salon-1"])
    sortie = capsys.readouterr().out + capsys.readouterr().err
    assert code == 1
    assert lignes_par_table(depot, "salon-1")["rendez_vous"] == 1

    code = main(["effacer", "--tenant", "salon-1", "--confirmer", "salon-2"])
    assert code == 1
    assert lignes_par_table(depot, "salon-1")["rendez_vous"] == 1


def test_la_commande_efface_quand_le_nom_est_confirme(tmp_path, capsys, monkeypatch):
    from standard.__main__ import main

    depot = base_pleine(tmp_path)
    monkeypatch.setenv("STANDARD_BASE", str(tmp_path / "essai.sqlite3"))
    code = main(["effacer", "--tenant", "salon-1", "--confirmer", "salon-1"])
    assert code == 0
    assert all(n == 0 for n in lignes_par_table(depot, "salon-1").values())
    assert "rendez_vous" in capsys.readouterr().out
