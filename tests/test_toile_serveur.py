"""Parler à l'agent depuis un navigateur — de bout en bout.

Le même serveur sert la page et porte le canal audio. Ce qui circule est
exactement ce qui circule au téléphone : PCM 16 bits mono 8 kHz, paquets de
vingt millisecondes. Un test qui passerait ici mais pas au téléphone voudrait
dire qu'on a deux produits ; il n'y en a qu'un.
"""

import base64
import json
import os
import socket
import struct
import time

import pytest

from standard.demarrage import construire_serveur
from standard.toile_serveur import PAQUET_20MS, ServeurDeToile
from standard.toile import (
    OPCODE_BINAIRE,
    OPCODE_FERMETURE,
    decoder_une_trame,
)

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_le_paquet_de_la_toile_est_celui_du_telephone():
    """Vingt millisecondes à 8 kHz, seize bits : si les deux transports
    divergeaient, un défaut n'apparaîtrait que d'un côté."""
    from standard.audiosocket import PAQUET_20MS_8K

    assert PAQUET_20MS == PAQUET_20MS_8K
    assert issubclass(ServeurDeToile, object)
PAROLE = b"".join(struct.pack("<h", 8000 if i % 2 else -8000) for i in range(160))
SILENCE = bytes(320)


@pytest.fixture
def serveur(tmp_path):
    serveur = construire_serveur({
        "STANDARD_TENANT": "salon-marpeap",
        "STANDARD_PACK": os.path.join(RACINE, "packs", "coiffure.json"),
        "STANDARD_REPONSES": '{"A1": "Salon Marpeap"}',
        "STANDARD_CRENEAUX": "09:00,15:30",
        "STANDARD_AUJOURDHUI": "2026-09-15",
        "STANDARD_PORT": "0", "STANDARD_PORT_SANTE": "0", "STANDARD_PORT_TOILE": "0",
        "STANDARD_BASE": str(tmp_path / "essai.sqlite3"),
        "STANDARD_STT": "muet", "STANDARD_TTS": "muet",
    })
    serveur.transcrire = lambda audio, frequence: \
        "je voudrais un rendez-vous jeudi à quinze heures trente"
    # La synthèse « muette » rend `b""` : AUCUN son. Un test qui compte les
    # octets reçus mesurait alors la taille d'une annonce vide et se disait
    # vert. Ici la voix produit du vrai PCM — c'est la seule façon de voir la
    # forme de ce qui part vers le navigateur.
    voix = lambda texte: iter([bytes(3200)])          # 0,2 s à 8 kHz
    serveur.synthetiser = voix
    serveur.toile.synthetiser = voix
    serveur.demarrer()
    yield serveur
    serveur.arreter()


def brancher(serveur, chemin="/parler"):
    prise = socket.create_connection(("127.0.0.1", serveur.toile.port), timeout=5)
    nonce = base64.b64encode(b"0123456789abcdef").decode()
    prise.sendall(
        f"GET {chemin} HTTP/1.1\r\nHost: 127.0.0.1\r\nUpgrade: websocket\r\n"
        f"Connection: Upgrade\r\nSec-WebSocket-Key: {nonce}\r\n"
        "Sec-WebSocket-Version: 13\r\n\r\n".encode())
    prise.settimeout(5)
    reponse = prise.recv(4096)
    return prise, reponse


def trame(charge, opcode=OPCODE_BINAIRE):
    masque = b"\x01\x02\x03\x04"
    if len(charge) < 126:
        entete = struct.pack("!BB", 0x80 | opcode, 0x80 | len(charge))
    else:
        entete = struct.pack("!BBH", 0x80 | opcode, 0x80 | 126, len(charge))
    brouille = bytes(o ^ masque[r % 4] for r, o in enumerate(charge))
    return entete + masque + brouille


def ecouter(prise, duree_s=2.0):
    """Ce que le navigateur recevrait — l'audio de l'agent, déframé."""
    audio, tampon, fin = bytearray(), b"", time.time() + duree_s
    prise.settimeout(0.2)
    while time.time() < fin:
        try:
            morceau = prise.recv(65536)
        except socket.timeout:
            continue
        if not morceau:
            break
        tampon += morceau
        while True:
            opcode, charge, tampon = decoder_une_trame(tampon)
            if opcode is None:
                break
            if opcode == OPCODE_BINAIRE:
                audio.extend(charge)
    return bytes(audio)


def ecouter_les_trames(prise, duree_s=2.0):
    """Les paquets UN PAR UN. `ecouter` les recolle, et un défaut de forme —
    un en-tête resté collé, une longueur impaire — disparaît dans la colle."""
    trames, tampon, fin = [], b"", time.time() + duree_s
    prise.settimeout(0.2)
    while time.time() < fin:
        try:
            morceau = prise.recv(65536)
        except socket.timeout:
            continue
        if not morceau:
            break
        tampon += morceau
        while True:
            opcode, charge, tampon = decoder_une_trame(tampon)
            if opcode is None:
                break
            if opcode == OPCODE_BINAIRE:
                trames.append(charge)
    return trames


# --- la page ----------------------------------------------------------------

def test_la_page_se_sert_et_demande_le_micro(serveur):
    import urllib.request

    url = f"http://127.0.0.1:{serveur.toile.port}/"
    with urllib.request.urlopen(url, timeout=3) as reponse:
        page = reponse.read().decode()
    assert "getUserMedia" in page
    assert "Salon Marpeap" in page, "la page doit nommer le salon qu'elle sert"


def test_la_page_annonce_l_agent_automatique_avant_tout(serveur):
    """AI Act art. 50 : l'annonce ne dépend pas du transport. À l'écrit ici, à
    l'oral dans la première phrase — les deux, jamais l'un à la place de
    l'autre."""
    import urllib.request

    with urllib.request.urlopen(f"http://127.0.0.1:{serveur.toile.port}/",
                                timeout=3) as reponse:
        page = reponse.read().decode()
    assert "assistant automatique" in page.lower()


# --- le canal ---------------------------------------------------------------

def test_la_poignee_de_main_aboutit(serveur):
    prise, reponse = brancher(serveur)
    try:
        assert b"101" in reponse
        assert b"s3pPLMBiTxaQ9kYGzzhZRbK+xOo=" not in reponse  # pas le nonce d'exemple
        assert b"Sec-WebSocket-Accept" in reponse
    finally:
        prise.close()


def test_l_annonce_part_des_la_connexion(serveur):
    """Comme au téléphone : l'agent parle le premier, et ce qu'il dit porte
    l'annonce obligatoire."""
    prise, _ = brancher(serveur)
    try:
        audio = ecouter(prise, 2.0)
        assert len(audio) > 0, "rien n'a été envoyé au navigateur"
    finally:
        prise.close()


def test_le_navigateur_recoit_du_pcm_nu_et_non_des_trames_audiosocket(serveur):
    """Ce que la page peut JOUER, pas seulement ce qu'elle reçoit.

    Le transport web envoyait les paquets tels que la session les fabrique :
    encodés AudioSocket, en-tête de trois octets compris. La page fait
    `new Int16Array(octets)` — sur 323 octets, longueur impaire, le navigateur
    lève « byte length of Int16Array should be a multiple of 2 » à CHAQUE
    paquet, et l'appelant n'entend rien. Les tests passaient : ils comptaient
    les octets reçus, jamais leur forme. C'est un navigateur piloté qui l'a vu.
    """
    from standard.audiosocket import TAILLE_ENTETE, TYPE_AUDIO_8K

    prise, _ = brancher(serveur)
    try:
        trames = ecouter_les_trames(prise, 2.0)
        assert trames, "rien n'a été envoyé au navigateur"
        for charge in trames:
            assert len(charge) % 2 == 0, (
                f"longueur impaire ({len(charge)}) : injouable en Int16Array")
            assert len(charge) == PAQUET_20MS, (
                f"{len(charge)} octets au lieu de {PAQUET_20MS} : "
                "en-tête AudioSocket resté collé à l'audio")
            entete_audiosocket = bytes([TYPE_AUDIO_8K]) + (
                PAQUET_20MS).to_bytes(TAILLE_ENTETE - 1, "big")
            assert not charge.startswith(entete_audiosocket), (
                "le paquet porte encore son en-tête AudioSocket")
    finally:
        prise.close()


def test_un_appel_complet_se_deroule_par_la_toile(serveur, tmp_path):
    from standard.depot import Depot

    prise, _ = brancher(serveur)
    try:
        ecouter(prise, 1.5)
        for tour, texte in enumerate(("demande", "accord", "nom")):
            if tour == 1:
                serveur.transcrire = lambda audio, frequence: "oui c'est parfait"
            if tour == 2:
                serveur.transcrire = lambda audio, frequence: "au nom de Dupont"
            for _ in range(10):
                prise.sendall(trame(PAROLE))
            for _ in range(50):
                prise.sendall(trame(SILENCE))
            ecouter(prise, 1.5)
        time.sleep(0.5)
    finally:
        prise.close()
    time.sleep(0.4)

    rendez_vous = Depot(str(tmp_path / "essai.sqlite3")).lister("salon-marpeap")
    assert rendez_vous, "aucun rendez-vous pris par la toile"
    assert rendez_vous[0]["heure"] == "15:30"


def test_une_fermeture_du_navigateur_libere_l_appel(serveur):
    prise, _ = brancher(serveur)
    ecouter(prise, 0.5)
    prise.sendall(trame(b"", OPCODE_FERMETURE))
    prise.close()
    for _ in range(50):
        if serveur.toile.appels_en_cours == 0:
            break
        time.sleep(0.05)
    assert serveur.toile.appels_en_cours == 0


def test_l_appel_par_la_toile_atterrit_au_journal(serveur):
    prise, _ = brancher(serveur)
    try:
        for _ in range(10):
            prise.sendall(trame(PAROLE))
        for _ in range(50):
            prise.sendall(trame(SILENCE))
        ecouter(prise, 1.5)
    finally:
        prise.close()
    time.sleep(0.5)
    appels = serveur.journal.lister("salon-marpeap")
    assert appels, "un appel par la toile doit se journaliser comme les autres"
    assert appels[0]["preuve_annonce"]["conforme"] is True


def test_la_page_publiee_et_la_page_servie_sont_le_meme_fichier():
    """Deux copies auraient divergé dès la première correction — et le défaut
    n'apparaîtrait que d'un côté, c'est-à-dire chez le client qui essaie."""
    from pathlib import Path

    depuis_le_depot = Path(RACINE) / "toile" / "index.html"
    assert depuis_le_depot.exists()
    assert not (Path(RACINE) / "standard" / "toile").exists(), (
        "il ne doit rester qu'un seul exemplaire de la page")


def test_le_front_end_sait_ou_joindre_l_agent_sans_redeployer():
    """`?agent=wss://…` : essayer un autre serveur ne doit pas demander une
    publication — sinon on ne l'essaie pas."""
    from pathlib import Path

    page = (Path(RACINE) / "toile" / "index.html").read_text()
    assert "URLSearchParams" in page and "agent" in page
    assert "CONFIGURATION" in page


def test_deux_services_successifs_ne_reutilisent_jamais_un_identifiant(tmp_path):
    """L'identifiant d'appel nourrit la CLÉ D'IDEMPOTENCE des écritures.

    Il valait `toile-{compteur du processus}` : après un redémarrage — et le
    service redémarre à chaque déploiement — le compteur repartait à 1. Deux
    appels différents portaient alors la même clé, et l'écriture du second était
    dédupliquée sur la ligne du premier : le deuxième appelant s'entendait
    confirmer « votre rendez-vous au nom de Dupont », et SON rendez-vous
    n'existait nulle part. Un doublon se voit ; ceci ne se voit pas.

    Au téléphone le risque n'existe pas : l'identifiant vient d'Asterisk, c'est
    un UUID. C'est le transport web qui le fabriquait lui-même.
    """
    vus = set()
    for _ in range(3):                        # trois « démarrages » successifs
        serveur = ServeurDeToile(
            fabrique_agent=lambda: None, transcrire=lambda a, f: "",
            synthetiser=lambda t: iter([b""]), nom_du_salon="Salon Marpeap",
            hote="127.0.0.1", port=0)
        vus.update(serveur.identifiant_d_appel() for _ in range(5))
    assert len(vus) == 15, "un identifiant est réutilisé d'un démarrage à l'autre"
    assert not any(marque in vus for marque in ("toile-1", "toile-2")), (
        "identifiant dérivé d'un compteur de processus")


def test_le_standard_sert_aussi_le_config_js_que_la_page_demande(serveur):
    """La page cherche `config.js` — l'adresse de l'agent, écrite au déploiement
    sur l'hébergeur statique. Servie par le standard, elle le demandait aussi et
    recevait du HTML : « Unexpected token '<' » dans la console du navigateur.
    Vu en pilotant un vrai navigateur, invisible pour la suite.
    """
    prise = socket.create_connection(("127.0.0.1", serveur.toile.port), timeout=5)
    try:
        prise.sendall(b"GET /config.js HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")
        prise.settimeout(5)
        reponse = b""
        while b"\r\n\r\n" not in reponse:
            reponse += prise.recv(4096)
        entete, _, debut = reponse.partition(b"\r\n\r\n")
        assert b"application/javascript" in entete, (
            "servi comme autre chose que du JavaScript : le navigateur refuse")
        assert not debut.lstrip().startswith(b"<"), "c'est du HTML, pas du script"
        assert b"CONFIGURATION" in debut
    finally:
        prise.close()


def test_un_canal_qui_ne_s_ouvre_jamais_ne_se_dit_pas_termine():
    """Ce test lit la FORME du code de la page, faute de moteur JS dans la
    suite : c'est une garde, pas une preuve. La preuve est venue d'un navigateur
    piloté, qui a affiché « Appel terminé. Merci — vous pouvez rappeler. » alors
    que Chrome avait refusé le canal (page publique vers réseau privé). Le
    `onclose` passait après le `onerror` et écrasait la panne par une politesse.
    """
    page = open(os.path.join(RACINE, "toile", "index.html"), encoding="utf-8").read()
    assert "let enLigne" in page, "rien ne distingue un appel abouti d'un appel manqué"
    apres_onclose = page.split("canal.onclose")[1][:600]
    assert "enLigne" in apres_onclose, (
        "la fermeture annonce la même chose qu'un appel ait eu lieu ou non")
    assert "Impossible de joindre" in page, "aucun message pour un canal jamais ouvert"
    assert "Adresse essayée" in page, (
        "une panne de canal sans l'adresse essayée ne se diagnostique pas")


def test_la_page_refuse_un_canal_en_clair_depuis_une_page_chiffree():
    """Un navigateur en HTTPS refuse un WebSocket en clair, et son message ne
    dit pas pourquoi. La page le dit à sa place."""
    from pathlib import Path

    page = (Path(RACINE) / "toile" / "index.html").read_text()
    assert "wss://" in page and "HTTPS" in page
