"""Le transport par la toile — le même pipeline, sans opérateur téléphonique.

Demande d'Adnan le 21/09 : remplacer temporairement le numéro 09 par une route
sur Internet, pour parler à l'agent depuis le site. Le transport change, **rien
d'autre** : même session, même annonce légale de l'AI Act, même agenda, mêmes
mesures. On porte donc exactement le format du téléphone — PCM 16 bits mono
8 kHz, par paquets de vingt millisecondes.

Pourquoi écrire le protocole plutôt que d'ajouter une bibliothèque : le produit
n'a que deux dépendances, et elles tiennent en deux lignes de `requirements`.
Ce qu'il faut ici est un sous-ensemble minuscule de la RFC 6455 — poignée de
main, trames binaires masquées par le client, ping, fermeture — et nos trames
font 320 octets, donc jamais fragmentées. Ce qui sort du cadre est refusé
plutôt que deviné.
"""

from __future__ import annotations

import base64
import hashlib
import struct

MAGIE = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
"""La constante de la RFC 6455. Sans elle, aucun navigateur ne se connecte — et
l'erreur qu'il affiche ne dit rien d'utile."""

OPCODE_SUITE = 0x0
OPCODE_TEXTE = 0x1
OPCODE_BINAIRE = 0x2
OPCODE_FERMETURE = 0x8
OPCODE_PING = 0x9
OPCODE_PONG = 0xA

TAILLE_MAXIMALE = 1 << 20
"""Un mégaoctet. Nos paquets font 320 octets : au-delà, ce n'est pas notre
client, et on ferme plutôt que d'allouer ce qu'on nous demande d'allouer."""


def cle_de_reponse(nonce: str) -> str:
    """La réponse à `Sec-WebSocket-Key`, telle que la RFC la définit."""
    empreinte = hashlib.sha1((nonce.strip() + MAGIE).encode()).digest()
    return base64.b64encode(empreinte).decode()


def poignee_de_main(entetes: dict[str, str]) -> bytes | None:
    """La réponse HTTP qui ouvre le canal, ou `None` si ce n'est pas un client
    WebSocket — auquel cas l'appelant sert la page, pas un canal."""
    nonce = entetes.get("sec-websocket-key")
    if not nonce or "websocket" not in entetes.get("upgrade", "").lower():
        return None
    return ("HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {cle_de_reponse(nonce)}\r\n\r\n").encode()


def decoder_une_trame(flux: bytes):
    """Rend `(opcode, charge, reste)`. `opcode` vaut `None` s'il manque des octets.

    TCP ne respecte aucune frontière : deux paquets de vingt millisecondes
    arrivent souvent collés, et une trame arrive souvent coupée en deux.
    """
    if len(flux) < 2:
        return None, b"", flux
    premier, second = flux[0], flux[1]
    opcode = premier & 0x0F
    masque_present = bool(second & 0x80)
    longueur = second & 0x7F
    curseur = 2

    if longueur == 126:
        if len(flux) < curseur + 2:
            return None, b"", flux
        longueur = struct.unpack("!H", flux[curseur:curseur + 2])[0]
        curseur += 2
    elif longueur == 127:
        if len(flux) < curseur + 8:
            return None, b"", flux
        longueur = struct.unpack("!Q", flux[curseur:curseur + 8])[0]
        curseur += 8

    if longueur > TAILLE_MAXIMALE:
        raise ValueError(f"trame de {longueur} octets : ce n'est pas notre client")

    masque = b""
    if masque_present:
        if len(flux) < curseur + 4:
            return None, b"", flux
        masque = flux[curseur:curseur + 4]
        curseur += 4

    if len(flux) < curseur + longueur:
        return None, b"", flux

    charge = flux[curseur:curseur + longueur]
    if masque:
        charge = bytes(octet ^ masque[rang % 4] for rang, octet in enumerate(charge))
    return opcode, charge, flux[curseur + longueur:]


def encoder_une_trame(charge: bytes, opcode: int = OPCODE_BINAIRE) -> bytes:
    """Une trame du serveur vers le client : **jamais masquée**.

    La RFC l'interdit dans ce sens, et un navigateur ferme la connexion en
    voyant un masque — sans rien dire de plus.
    """
    entete = struct.pack("!B", 0x80 | opcode)
    longueur = len(charge)
    if longueur < 126:
        entete += struct.pack("!B", longueur)
    elif longueur < (1 << 16):
        entete += struct.pack("!BH", 126, longueur)
    else:
        entete += struct.pack("!BQ", 127, longueur)
    return entete + charge
