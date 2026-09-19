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

    # Le module entier, pas `main` : le dispatch vit dans `_executer` depuis que
    # les erreurs de configuration se disent en une phrase.
    source = inspect.getsource(commande)
    assert "PisteDAudit" in source, "la console ne laisse aucune trace de qui corrige"
    assert "Limiteur" in source, "la console n'est pas protégée d'un matraquage"


# --- la console ne s'ouvre pas à qui passe par là ---------------------------
# Elle montre des transcriptions, des noms et des numéros de clients. Un
# garde-fou existait (`acces.Cles`, clés hachées, portées, rotation) et n'était
# branché nulle part : la console répondait à quiconque atteignait le port.

def serveur_protege(tmp_path):
    from standard.acces import Cles
    from standard.console import Console
    from standard.console_http import ServeurConsole
    from standard.depot import Depot
    from standard.journal import JournalDAppels

    depot = Depot(":memory:")
    journal = JournalDAppels(depot)
    journal.enregistrer("salon-1", APPEL)
    trousseau = Cles()
    secret = trousseau.emettre("salon-1", ["console"])
    serveur = ServeurConsole(Console(journal=journal, tenant="salon-1"),
                             port=0, trousseau=trousseau, portee="console")
    serveur.demarrer()
    return serveur, secret


def lire_protege(serveur, chemin="/", entetes=None):
    import urllib.error
    import urllib.request

    requete = urllib.request.Request(f"http://127.0.0.1:{serveur.port}{chemin}",
                                     headers=entetes or {})
    try:
        with urllib.request.urlopen(requete, timeout=3) as reponse:
            return reponse.status, reponse.read().decode(), reponse.headers
    except urllib.error.HTTPError as refus:
        return refus.code, refus.read().decode(), refus.headers


def test_sans_cle_la_console_refuse_et_ne_montre_rien(tmp_path):
    serveur, _ = serveur_protege(tmp_path)
    try:
        statut, contenu, _ = lire_protege(serveur)
        assert statut == 401
        assert "permanente" not in contenu, "une transcription a fuité dans le refus"
    finally:
        serveur.arreter()


def test_avec_la_cle_en_entete_la_console_repond(tmp_path):
    serveur, secret = serveur_protege(tmp_path)
    try:
        statut, contenu, _ = lire_protege(serveur, entetes={"Authorization": f"Bearer {secret}"})
        assert statut == 200
        assert "Vos appels" in contenu
    finally:
        serveur.arreter()


def test_une_cle_fausse_est_refusee(tmp_path):
    serveur, _ = serveur_protege(tmp_path)
    try:
        statut, _, _ = lire_protege(serveur, entetes={"Authorization": "Bearer stdk_faux"})
        assert statut == 401
    finally:
        serveur.arreter()


def test_le_lien_porte_la_cle_une_fois_puis_un_cookie_prend_le_relais(tmp_path):
    """Un gérant ne colle pas un en-tête HTTP : il ouvre un lien. La clé n'y
    passe qu'une fois, et le cookie évite qu'elle reste dans l'historique."""
    serveur, secret = serveur_protege(tmp_path)
    try:
        statut, _, entetes = lire_protege(serveur, f"/?cle={secret}")
        assert statut == 200
        cookie = entetes.get("Set-Cookie", "")
        assert "HttpOnly" in cookie and "SameSite=Strict" in cookie
        statut, contenu, _ = lire_protege(serveur, entetes={"Cookie": cookie.split(";")[0]})
        assert statut == 200 and "Vos appels" in contenu
    finally:
        serveur.arreter()


def test_sans_trousseau_la_console_reste_ouverte_sur_la_boucle_locale(tmp_path):
    """Le mode d'essai ne doit pas demander une clé : il n'écoute que 127.0.0.1."""
    from standard.console import Console
    from standard.console_http import ServeurConsole
    from standard.depot import Depot
    from standard.journal import JournalDAppels

    depot = Depot(":memory:")
    journal = JournalDAppels(depot)
    journal.enregistrer("salon-1", APPEL)
    serveur = ServeurConsole(Console(journal=journal, tenant="salon-1"), port=0)
    serveur.demarrer()
    try:
        assert lire_protege(serveur)[0] == 200
    finally:
        serveur.arreter()


def test_la_commande_console_exige_une_cle_des_qu_elle_sort_de_la_boucle_locale():
    """Sur 127.0.0.1 le mode d'essai reste ouvert — sinon personne ne l'essaie,
    et il finit exposé sans clé du tout. Dès qu'on change d'hôte, la clé devient
    obligatoire."""
    import inspect

    from standard import __main__ as commande

    source = inspect.getsource(commande)
    assert "STANDARD_HOTE_CONSOLE" in source
    assert "trousseau=trousseau" in source
    assert "cette clé ne sera plus affichée" in source
