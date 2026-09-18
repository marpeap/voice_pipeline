"""Le bord telephonique — le protocole AudioSocket d'Asterisk.

Verifie contre la documentation officielle (docs.asterisk.org, consultee le
18/09/2026) plutot que de memoire : l'en-tete fait **trois octets** — un octet de
type, puis deux octets de longueur **en gros-boutien** —, suivis de la charge.

| Type | Ce que c'est |
|---|---|
| `0x00` | fin de connexion |
| `0x01` | UUID de l'appel, **16 octets binaires** |
| `0x03` | un chiffre DTMF, un octet ASCII |
| `0x10`-`0x18` | audio PCM 16 bits mono **petit-boutien**, de 8 kHz a 192 kHz |
| `0xff` | erreur, avec un code applicatif facultatif |

Deux pieges sont traites ici, et ils ne se voient qu'en production : **TCP ne
respecte aucune frontiere de trame** — une trame arrive en morceaux, deux trames
arrivent collees — et **la longueur tient sur deux octets**, donc une charge de
plus de 65 535 octets doit etre decoupee, jamais tronquee en silence.
"""

from __future__ import annotations

import uuid as _uuid
from dataclasses import dataclass
from typing import Iterator

TYPE_FIN = 0x00
TYPE_UUID = 0x01
TYPE_DTMF = 0x03
TYPE_AUDIO_8K = 0x10
TYPE_ERREUR = 0xFF

# Les frequences sont portees par le type de trame : elles ne se devinent pas,
# et cette table est la seule source (docs.asterisk.org).
FREQUENCES = {
    0x10: 8000, 0x11: 12000, 0x12: 16000, 0x13: 24000, 0x14: 32000,
    0x15: 44100, 0x16: 48000, 0x17: 96000, 0x18: 192000,
}

TAILLE_ENTETE = 3
CHARGE_MAXIMALE = 0xFFFF          # deux octets de longueur, pas un de plus
PAQUET_20MS_8K = 320              # 160 echantillons de 16 bits


@dataclass(frozen=True)
class Trame:
    type: int
    charge: bytes

    @property
    def est_audio(self) -> bool:
        return self.type in FREQUENCES

    @property
    def est_dtmf(self) -> bool:
        return self.type == TYPE_DTMF

    @property
    def est_uuid(self) -> bool:
        return self.type == TYPE_UUID

    @property
    def est_fin(self) -> bool:
        return self.type == TYPE_FIN

    @property
    def est_erreur(self) -> bool:
        return self.type == TYPE_ERREUR

    def frequence(self) -> int | None:
        return FREQUENCES.get(self.type)

    def chiffre(self) -> str:
        """Le chiffre compose par l'appelant. C'est le filet de la regle T7 :
        apres deux echecs sur un numero, on bascule au clavier."""
        if not self.est_dtmf or len(self.charge) != 1:
            raise ValueError("trame DTMF malformee")
        return self.charge.decode("ascii", errors="replace")

    def uuid(self) -> str:
        if not self.est_uuid or len(self.charge) != 16:
            raise ValueError(f"UUID attendu sur 16 octets, recu {len(self.charge)}")
        return str(_uuid.UUID(bytes=self.charge))


class Decodeur:
    """Recolle le flux TCP en trames. Il garde ce qui est incomplet.

    Un decodeur qui suppose « un paquet = une trame » marche en test et casse au
    premier appel reel : c'est le defaut classique de tout protocole a longueur
    prefixee.
    """

    def __init__(self):
        self._tampon = bytearray()

    def avaler(self, morceau: bytes) -> Iterator[Trame]:
        self._tampon.extend(morceau)
        while len(self._tampon) >= TAILLE_ENTETE:
            longueur = int.from_bytes(self._tampon[1:3], "big")
            if len(self._tampon) < TAILLE_ENTETE + longueur:
                return                      # trame incomplete : on attend la suite
            type_trame = self._tampon[0]
            charge = bytes(self._tampon[TAILLE_ENTETE:TAILLE_ENTETE + longueur])
            del self._tampon[:TAILLE_ENTETE + longueur]
            yield Trame(type_trame, charge)

    @property
    def en_attente(self) -> int:
        """Octets gardes faute de trame complete — utile au journal d'appel."""
        return len(self._tampon)


def encoder(type_trame: int, charge: bytes = b"") -> bytes:
    if len(charge) > CHARGE_MAXIMALE:
        raise ValueError("charge trop longue pour une seule trame ; utiliser encoder_audio")
    return bytes([type_trame]) + len(charge).to_bytes(2, "big") + charge


def encoder_audio(audio: bytes, type_trame: int = TYPE_AUDIO_8K,
                  taille_paquet: int = CHARGE_MAXIMALE) -> list[bytes]:
    """Decoupe l'audio en trames. Par defaut au maximum permis ; en production,
    on passe `taille_paquet=PAQUET_20MS_8K` pour coller au rythme du canal."""
    taille = min(taille_paquet, CHARGE_MAXIMALE)
    return [encoder(type_trame, audio[debut:debut + taille])
            for debut in range(0, len(audio), taille)] or [encoder(type_trame, b"")]
