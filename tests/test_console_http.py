"""La console servie pour de vrai : un serveur HTTP, sur la boucle locale.

Même leçon que pour le bord téléphonique : une console qui ne se sert pas n'est
pas une console. Ici on démarre le serveur et on va chercher les pages.
"""

import urllib.error
import urllib.request

import pytest

from standard.console import Console
from standard.console_http import ServeurConsole
from standard.depot import Depot
from standard.journal import JournalDAppels

APPEL = {
    "uuid": "7f3a1c5e-0000-4000-8000-000000000001",
    "debut": "2026-09-19T10:00:00+00:00", "duree_s": 40, "issue": "rendez-vous",
    "tours": [{"genre": "question", "phrase": "Quel jour ?", "transcription": "jeudi"}],
    "preuve_annonce": {"conforme": True},
}


@pytest.fixture
def serveur():
    depot = Depot(":memory:")
    journal = JournalDAppels(depot)
    journal.enregistrer("salon-1", APPEL)
    s = ServeurConsole(Console(journal=journal, tenant="salon-1"),
                       hote="127.0.0.1", port=0)
    s.demarrer()
    yield s
    s.arreter()


@pytest.fixture
def serveur_limite():
    from standard.acces import Limiteur

    depot = Depot(":memory:")
    journal = JournalDAppels(depot)
    journal.enregistrer("salon-1", APPEL)
    s = ServeurConsole(Console(journal=journal, tenant="salon-1"),
                       hote="127.0.0.1", port=0,
                       limiteur=Limiteur(par_minute=2, par_minute_adresse=2))
    s.demarrer()
    yield s
    s.arreter()


def lire(serveur, chemin="/"):
    with urllib.request.urlopen(f"http://127.0.0.1:{serveur.port}{chemin}", timeout=2) as r:
        return r.status, r.read().decode()


def test_la_console_se_sert_vraiment(serveur):
    statut, contenu = lire(serveur)
    assert statut == 200
    assert "Vos appels" in contenu


def test_une_page_inconnue_rend_404_et_une_porte_de_sortie(serveur):
    with pytest.raises(urllib.error.HTTPError) as erreur:
        lire(serveur, "/nimporte-quoi")
    assert erreur.value.code == 404
    assert "fil des appels" in erreur.value.read().decode().lower()


def test_la_page_est_bien_de_l_html_en_utf8(serveur):
    with urllib.request.urlopen(f"http://127.0.0.1:{serveur.port}/", timeout=2) as reponse:
        assert "text/html" in reponse.headers["Content-Type"]
        assert "utf-8" in reponse.headers["Content-Type"].lower()


def test_une_correction_postee_redirige_vers_le_fil(serveur):
    import urllib.parse
    donnees = urllib.parse.urlencode({
        "appel": APPEL["uuid"], "faute": "duree", "empan": "une coupe",
        "prestation": "coupe", "duree_minutes": "45"}).encode()
    with urllib.request.urlopen(
            f"http://127.0.0.1:{serveur.port}/correction", data=donnees, timeout=2) as r:
        # urllib suit la redirection : on doit retomber sur le fil, avec le message.
        contenu = r.read().decode()
    assert "Correction enregistrée" in contenu


def test_la_console_n_ecoute_pas_le_monde_entier_par_defaut():
    """Une console de commerçant exposée sur toutes les interfaces, c'est un
    journal d'appels ouvert à qui passe. Le défaut est la boucle locale."""
    from standard.console_http import HOTE_PAR_DEFAUT
    assert HOTE_PAR_DEFAUT == "127.0.0.1"


def test_la_console_resiste_a_un_matraquage(serveur_limite):
    """Un service de commerçant qui tombe parce que quelqu'un rafraîchit trop
    vite n'est pas exploitable. On refuse poliment, on ne s'effondre pas."""
    codes = []
    for _ in range(4):
        try:
            codes.append(lire(serveur_limite)[0])
        except urllib.error.HTTPError as erreur:
            codes.append(erreur.code)
    assert 429 in codes
    assert codes.count(200) >= 1


def test_le_refus_dit_quand_reessayer(serveur_limite):
    for _ in range(5):
        try:
            lire(serveur_limite)
        except urllib.error.HTTPError as erreur:
            if erreur.code == 429:
                assert erreur.headers.get("Retry-After")
                return
    pytest.fail("aucun refus alors que la limite est de deux par minute")


def test_la_commande_console_cable_l_audit_et_la_limitation(tmp_path, monkeypatch):
    """La revue du 19/09 : `acces` et `audit` existaient, testés, documentés — et
    n'étaient branchés nulle part. Un garde-fou non branché ne garde rien."""
    import inspect

    from standard import __main__ as commande

    source = inspect.getsource(commande.main)
    assert "PisteDAudit" in source, "la console ne laisse aucune trace de qui corrige"
    assert "Limiteur" in source, "la console n'est pas protégée d'un matraquage"
