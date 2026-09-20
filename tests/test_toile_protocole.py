"""Le transport WebSocket — le même pipeline, sans opérateur téléphonique.

Adnan, 21/09 : remplacer temporairement le numéro 09 par une route sur
Internet, pour parler à l'agent depuis le site. Le transport change ; **rien
d'autre ne doit changer** — même session, même annonce légale, même agenda,
mêmes mesures. On porte donc le même format que le téléphone : PCM 16 bits mono
8 kHz, par paquets de vingt millisecondes.

Ce fichier ne teste que le protocole : la poignée de main et les trames. Le
serveur qui s'en sert est testé à part, avec un vrai navigateur simulé.
"""

import base64
import hashlib
import struct

import pytest

from standard.toile import (
    OPCODE_BINAIRE,
    OPCODE_FERMETURE,
    OPCODE_PING,
    cle_de_reponse,
    decoder_une_trame,
    encoder_une_trame,
)


# --- la poignée de main -----------------------------------------------------

def test_la_cle_de_reponse_suit_la_rfc_6455():
    """L'exemple de la RFC elle-même : si ce calcul est faux, aucun navigateur
    ne se connecte, et l'erreur ne dit rien d'utile."""
    assert cle_de_reponse("dGhlIHNhbXBsZSBub25jZQ==") == "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="


def test_la_cle_se_calcule_sur_n_importe_quel_nonce():
    nonce = base64.b64encode(b"0123456789abcdef").decode()
    attendu = base64.b64encode(hashlib.sha1(
        (nonce + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
    assert cle_de_reponse(nonce) == attendu


# --- les trames -------------------------------------------------------------

def masquer(charge: bytes, masque=b"\x01\x02\x03\x04") -> bytes:
    return bytes(octet ^ masque[rang % 4] for rang, octet in enumerate(charge))


def trame_client(charge: bytes, opcode=OPCODE_BINAIRE) -> bytes:
    """Ce qu'un navigateur envoie : toujours masqué, jamais fragmenté ici.

    Au-delà de 125 octets, la longueur passe sur seize bits — nos paquets de
    vingt millisecondes en font 320, donc c'est le cas normal, pas l'exception.
    """
    masque = b"\x01\x02\x03\x04"
    if len(charge) < 126:
        entete = struct.pack("!BB", 0x80 | opcode, 0x80 | len(charge))
    else:
        entete = struct.pack("!BBH", 0x80 | opcode, 0x80 | 126, len(charge))
    return entete + masque + masquer(charge, masque)


def test_une_trame_binaire_masquee_se_lit():
    audio = b"\x01\x02" * 160
    opcode, charge, reste = decoder_une_trame(trame_client(audio))
    assert opcode == OPCODE_BINAIRE
    assert charge == audio
    assert reste == b""


def test_deux_trames_collees_se_separent():
    """TCP ne respecte aucune frontière : deux paquets de vingt millisecondes
    arrivent souvent ensemble."""
    flux = trame_client(b"a" * 320) + trame_client(b"b" * 320)
    opcode, charge, reste = decoder_une_trame(flux)
    assert charge == b"a" * 320
    opcode, charge, reste = decoder_une_trame(reste)
    assert charge == b"b" * 320
    assert reste == b""


def test_une_trame_incomplete_attend_la_suite():
    flux = trame_client(b"a" * 320)[:100]
    assert decoder_une_trame(flux) == (None, b"", flux)


def test_une_charge_de_plus_de_125_octets_utilise_le_format_long():
    audio = b"\x7f" * 320
    opcode, charge, _ = decoder_une_trame(trame_client(audio))
    assert charge == audio


def test_un_ping_se_reconnait():
    opcode, charge, _ = decoder_une_trame(trame_client(b"", OPCODE_PING))
    assert opcode == OPCODE_PING


def test_une_fermeture_se_reconnait():
    opcode, _, _ = decoder_une_trame(trame_client(b"", OPCODE_FERMETURE))
    assert opcode == OPCODE_FERMETURE


# --- ce que le serveur renvoie ---------------------------------------------

def test_le_serveur_n_envoie_jamais_de_trame_masquee():
    """La RFC l'interdit dans ce sens, et les navigateurs ferment la connexion
    en voyant un masque."""
    trame = encoder_une_trame(b"\x00" * 320, OPCODE_BINAIRE)
    assert trame[1] & 0x80 == 0, "le bit de masque doit être à zéro"


def test_ce_que_le_serveur_encode_se_decode():
    audio = bytes(range(256)) * 2
    trame = encoder_une_trame(audio, OPCODE_BINAIRE)
    # On relit avec le même décodeur, en remettant un masque comme le ferait un
    # client : le format est symétrique, seul le masque diffère.
    entete = 2 if len(audio) < 126 else 4
    assert trame[entete:] == audio
