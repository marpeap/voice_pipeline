"""Le depot : des rendez-vous, cloisonnes par locataire, sans chevauchement.

Regle de `docs/02` : tables partagees, `tenant_id`, et un cloisonnement qui ne
depend pas de la bonne volonte de l'appelant. Une requete qui « oublie » le
locataire ne doit pas rendre tout le monde — elle doit echouer.
"""

import re

import pytest

from standard.depot import Depot, ChevauchementRefuse


@pytest.fixture
def depot():
    return Depot(":memory:")


RDV = {"date": "2026-09-17", "heure": "15:30", "prestation": "coupe",
       "telephone": "0612345678"}


# --- le contrat attendu par l'ecriture --------------------------------------

def test_le_depot_se_branche_la_ou_l_ecriture_attend_une_base(depot):
    from standard.ecriture import cle_idempotence, ecrire_rendez_vous
    base = depot.pour("salon-1")
    ecriture = ecrire_rendez_vous(base, cle_idempotence("salon-1", "appel-1", 1), RDV)
    assert ecriture.statut == "confirme"
    assert base.relire(ecriture.reference)["heure"] == "15:30"


def test_la_relecture_rend_ce_qui_a_ete_ecrit(depot):
    base = depot.pour("salon-1")
    reference = base.inserer("cle-1", RDV)
    relu = base.relire(reference)
    assert relu["date"] == RDV["date"] and relu["telephone"] == RDV["telephone"]


# --- le cloisonnement -------------------------------------------------------

def test_un_locataire_ne_voit_pas_les_rendez_vous_d_un_autre(depot):
    reference = depot.pour("salon-1").inserer("cle-1", RDV)
    assert depot.pour("salon-2").relire(reference) is None


def test_lister_sans_locataire_echoue_au_lieu_de_tout_rendre(depot):
    """Le pire defaut d'un multi-locataire n'est pas l'erreur : c'est la requete
    qui reussit et rend les donnees de tout le monde."""
    depot.pour("salon-1").inserer("cle-1", RDV)
    with pytest.raises(ValueError, match="locataire"):
        depot.lister(tenant=None)


def test_chaque_locataire_compte_ses_propres_lignes(depot):
    depot.pour("salon-1").inserer("cle-1", RDV)
    depot.pour("salon-2").inserer("cle-1", RDV)      # meme cle, autre locataire
    assert len(depot.lister("salon-1")) == 1
    assert len(depot.lister("salon-2")) == 1


# --- idempotence ------------------------------------------------------------

def test_la_meme_cle_ne_cree_qu_une_ligne(depot):
    base = depot.pour("salon-1")
    premiere = base.inserer("cle-1", RDV)
    seconde = base.inserer("cle-1", RDV)
    assert premiere == seconde
    assert len(depot.lister("salon-1")) == 1


def test_la_cle_est_propre_a_un_locataire(depot):
    """Deux salons peuvent produire la meme cle : elle ne les melange pas."""
    a = depot.pour("salon-1").inserer("cle-partagee", RDV)
    b = depot.pour("salon-2").inserer("cle-partagee", RDV)
    assert a != b


# --- le chevauchement -------------------------------------------------------

def test_deux_rendez_vous_ne_peuvent_pas_occuper_le_meme_creneau(depot):
    base = depot.pour("salon-1")
    base.inserer("cle-1", RDV)
    with pytest.raises(ChevauchementRefuse):
        base.inserer("cle-2", RDV | {"telephone": "0700000000"})


def test_le_meme_creneau_chez_deux_salons_est_permis(depot):
    depot.pour("salon-1").inserer("cle-1", RDV)
    depot.pour("salon-2").inserer("cle-2", RDV)      # rien a voir l'un avec l'autre


def test_un_creneau_libere_redevient_disponible(depot):
    base = depot.pour("salon-1")
    reference = base.inserer("cle-1", RDV)
    base.annuler(reference)
    base.inserer("cle-2", RDV)                        # ne leve pas


def test_annuler_le_rendez_vous_d_un_autre_ne_fait_rien(depot):
    reference = depot.pour("salon-1").inserer("cle-1", RDV)
    assert depot.pour("salon-2").annuler(reference) is False
    assert depot.pour("salon-1").relire(reference) is not None


# --- la migration de production ---------------------------------------------

def test_la_migration_postgres_active_ET_force_la_securite_par_ligne():
    """`ENABLE` seul ne protege pas le proprietaire de la table : sans `FORCE`,
    la politique est contournee par celui-la meme qui fait tourner l'API."""
    from pathlib import Path
    sql = (Path(__file__).resolve().parents[1] / "migrations" /
           "001-rendez-vous.sql").read_text().lower()
    assert "enable row level security" in sql
    assert "force row level security" in sql
    assert "current_setting" in sql


def test_la_migration_interdit_le_chevauchement_en_base():
    from pathlib import Path
    sql = (Path(__file__).resolve().parents[1] / "migrations" /
           "001-rendez-vous.sql").read_text().lower()
    assert "exclude" in sql or "unique" in sql


# --- concurrence ------------------------------------------------------------

def test_deux_appels_simultanes_ne_corrompent_pas_la_base(tmp_path):
    """La revue du 19/09 : une seule connexion SQLite partagée par tous les fils,
    sans verrou, avec `SELECT` puis `INSERT` puis `commit()` — le `commit()` d'un
    fil validait la transaction en cours d'un autre."""
    import threading

    depot = Depot(str(tmp_path / "concurrent.sqlite3"))
    erreurs = []
    barriere = threading.Barrier(8)

    def reserver(index):
        barriere.wait()
        try:
            depot.pour("salon-1").inserer(f"cle-{index}", {
                "date": "2026-09-17", "heure": f"{9 + index:02d}:00"})
        except Exception as erreur:
            erreurs.append(erreur)

    fils = [threading.Thread(target=reserver, args=(i,)) for i in range(8)]
    for fil in fils:
        fil.start()
    for fil in fils:
        fil.join()

    assert erreurs == [], f"erreurs en concurrence : {erreurs[:2]}"
    assert len(depot.lister("salon-1")) == 8


def test_deux_fils_ne_peuvent_pas_prendre_le_meme_creneau(tmp_path):
    """Le cas qui compte vraiment : deux appelants sur le même horaire."""
    import threading

    depot = Depot(str(tmp_path / "course.sqlite3"))
    resultats = []
    barriere = threading.Barrier(2)

    def reserver(index):
        barriere.wait()
        try:
            depot.pour("salon-1").inserer(f"cle-{index}", RDV)
            resultats.append("pris")
        except ChevauchementRefuse:
            resultats.append("refuse")

    fils = [threading.Thread(target=reserver, args=(i,)) for i in range(2)]
    for fil in fils:
        fil.start()
    for fil in fils:
        fil.join()

    assert sorted(resultats) == ["pris", "refuse"], \
        "les deux appelants ont obtenu le même créneau"


def test_toute_table_de_production_porte_la_meme_isolation():
    """Une table ajoutée sans politique est une fuite : on vérifie le lot entier,
    pas le fichier qu'on vient d'écrire."""
    from pathlib import Path

    migrations = sorted((Path(__file__).resolve().parents[1] / "migrations").glob("*.sql"))
    assert migrations, "aucune migration : le test ne prouverait rien"
    for chemin in migrations:
        sql = chemin.read_text().lower()
        for table in re.findall(r"create table if not exists (\w+)", sql):
            assert f"alter table {table} enable row level security" in sql, chemin.name
            assert f"alter table {table} force row level security" in sql, chemin.name
            assert f"on {table}" in sql and "current_setting" in sql, chemin.name
