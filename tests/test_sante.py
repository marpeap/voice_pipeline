"""L'état de santé, lisible par une machine — sinon personne ne le lit.

Un standard téléphonique tourne sans écran. Sans point d'état, l'exploitant
apprend qu'il est tombé par un commerçant qui téléphone, ce qui est la
définition d'un service non exploitable. Ce que le point doit dire vient des
mesures : le délai avant premier fragment dit qu'une machine est pleine bien
avant la charge processeur (mesure 13), et toute confirmation orpheline est un
incident, pas une statistique.
"""

import json
import os
import urllib.request

import pytest

from standard.demarrage import construire_serveur

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def serveur(tmp_path):
    serveur = construire_serveur({
        "STANDARD_TENANT": "salon-1",
        "STANDARD_PACK": os.path.join(RACINE, "packs", "coiffure.json"),
        "STANDARD_REPONSES": '{"A1": "Salon Elegance"}',
        "STANDARD_PORT": "0", "STANDARD_PORT_SANTE": "0",
        "STANDARD_BASE": str(tmp_path / "essai.sqlite3"),
        "STANDARD_STT": "muet", "STANDARD_TTS": "muet",
    })
    serveur.demarrer()
    yield serveur
    serveur.arreter()


def lire(serveur, chemin="/sante"):
    url = f"http://127.0.0.1:{serveur.sante.port}{chemin}"
    with urllib.request.urlopen(url, timeout=3) as reponse:
        return reponse.status, json.loads(reponse.read())


def test_le_point_de_sante_repond_quand_le_service_ecoute(serveur):
    statut, corps = lire(serveur)
    assert statut == 200
    assert corps["vivant"] is True
    assert corps["port_audiosocket"] == serveur.port


def test_il_porte_les_chiffres_qui_disent_si_le_service_va_bien(serveur):
    _, corps = lire(serveur)
    for cle in ("appels", "confirmations_orphelines", "premier_fragment_p50_ms",
                "appels_en_cours", "archivages_perdus", "pannes_pendant_appel"):
        assert cle in corps, cle


def test_il_dit_si_le_menage_tourne_et_ce_qu_il_conserve(serveur):
    _, corps = lire(serveur)
    from standard.regles import CONSERVATION_JOURS
    assert corps["entretien"]["conservation_jours"] == CONSERVATION_JOURS
    assert corps["entretien"]["vivant"] is True


def test_il_ne_publie_aucune_donnee_d_appelant(serveur):
    """Un point d'état est joignable sans jeton : il ne doit porter que des
    compteurs — jamais un nom, un numéro ou une transcription."""
    _, corps = lire(serveur)
    brut = json.dumps(corps, ensure_ascii=False).lower()
    for interdit in ("transcription", "telephone", "téléphone", "nom_appelant"):
        assert interdit not in brut


def test_une_page_inconnue_rend_404(serveur):
    import urllib.error

    with pytest.raises(urllib.error.HTTPError) as refus:
        lire(serveur, "/autre")
    assert refus.value.code == 404


def test_un_port_d_etat_deja_pris_n_empeche_pas_de_decrocher(tmp_path):
    """Trouvé en s'y cognant : deux salons sur une machine, ou une mesure qui
    tourne encore, et le service refusait de démarrer. Un port de diagnostic
    occupé ne doit jamais empêcher de répondre au téléphone."""
    import socket as s

    from standard.demarrage import construire_serveur

    squatteur = s.socket()
    squatteur.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1)
    squatteur.bind(("127.0.0.1", 0))
    squatteur.listen(1)
    port_pris = squatteur.getsockname()[1]

    serveur = construire_serveur({
        "STANDARD_TENANT": "salon-1",
        "STANDARD_PACK": os.path.join(RACINE, "packs", "coiffure.json"),
        "STANDARD_REPONSES": '{"A1": "Salon Elegance"}',
        "STANDARD_PORT": "0", "STANDARD_PORT_SANTE": str(port_pris),
        "STANDARD_BASE": str(tmp_path / "essai.sqlite3"),
        "STANDARD_STT": "muet", "STANDARD_TTS": "muet",
    })
    try:
        serveur.demarrer()                 # ne doit pas lever
        assert serveur.port > 0, "le standard n'écoute pas"
        assert serveur.sante.erreur, "l'incident doit être visible"
    finally:
        serveur.arreter()
        squatteur.close()
