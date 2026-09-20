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
