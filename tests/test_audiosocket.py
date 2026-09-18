"""Le bord telephonique : le protocole AudioSocket d'Asterisk.

Verifie contre la documentation officielle (docs.asterisk.org, consultee le
18/09/2026) : en-tete de trois octets — un octet de type, deux octets de
longueur en gros-boutien —, types 0x00 raccrochage, 0x01 UUID sur 16 octets,
0x03 chiffre DTMF en un octet ASCII, 0x10 a 0x18 audio PCM 16 bits mono petit-
boutien a des frequences croissantes, 0xff erreur.
"""

import pytest

from standard.audiosocket import (
    FREQUENCES,
    Trame,
    TYPE_AUDIO_8K,
    TYPE_DTMF,
    TYPE_ERREUR,
    TYPE_FIN,
    TYPE_UUID,
    Decodeur,
    encoder,
    encoder_audio,
)


def trame(type_octet, charge=b""):
    return bytes([type_octet]) + len(charge).to_bytes(2, "big") + charge


# --- decodage ---------------------------------------------------------------

def test_une_trame_complete_se_decode():
    decodeur = Decodeur()
    trames = list(decodeur.avaler(trame(TYPE_AUDIO_8K, b"\x01\x02")))
    assert trames == [Trame(TYPE_AUDIO_8K, b"\x01\x02")]


def test_plusieurs_trames_dans_un_meme_paquet():
    decodeur = Decodeur()
    flux = trame(TYPE_UUID, b"0" * 16) + trame(TYPE_AUDIO_8K, b"ab") + trame(TYPE_FIN)
    types = [t.type for t in decodeur.avaler(flux)]
    assert types == [TYPE_UUID, TYPE_AUDIO_8K, TYPE_FIN]


def test_une_trame_coupee_en_deux_est_recollee():
    """TCP ne respecte aucune frontiere de trame : une trame arrive en morceaux,
    et deux trames arrivent parfois collees. Un decodeur qui suppose le contraire
    marche en test et casse en production."""
    decodeur = Decodeur()
    complet = trame(TYPE_AUDIO_8K, b"\x01\x02\x03\x04")
    assert list(decodeur.avaler(complet[:2])) == []
    assert list(decodeur.avaler(complet[2:5])) == []
    assert list(decodeur.avaler(complet[5:])) == [Trame(TYPE_AUDIO_8K, b"\x01\x02\x03\x04")]


def test_un_entete_seul_est_une_trame_valide():
    """La documentation le dit : le message minimal fait trois octets."""
    decodeur = Decodeur()
    assert list(decodeur.avaler(trame(TYPE_FIN))) == [Trame(TYPE_FIN, b"")]


def test_la_longueur_est_en_gros_boutien():
    decodeur = Decodeur()
    charge = b"x" * 300
    brut = bytes([TYPE_AUDIO_8K]) + b"\x01\x2c" + charge      # 0x012c = 300
    assert list(decodeur.avaler(brut))[0].charge == charge


# --- ce que chaque type veut dire -------------------------------------------

def test_le_uuid_fait_seize_octets():
    decodeur = Decodeur()
    [t] = list(decodeur.avaler(trame(TYPE_UUID, bytes(range(16)))))
    assert t.est_uuid and len(t.charge) == 16


def test_un_uuid_de_mauvaise_taille_est_signale():
    decodeur = Decodeur()
    [t] = list(decodeur.avaler(trame(TYPE_UUID, b"court")))
    assert t.est_uuid
    with pytest.raises(ValueError):
        t.uuid()


def test_le_dtmf_rend_un_chiffre():
    decodeur = Decodeur()
    [t] = list(decodeur.avaler(trame(TYPE_DTMF, b"7")))
    assert t.est_dtmf and t.chiffre() == "7"


def test_chaque_type_audio_porte_sa_frequence():
    """La frequence n'est pas devinee : elle est portee par le type de trame."""
    assert FREQUENCES[0x10] == 8000
    assert FREQUENCES[0x12] == 16000
    assert FREQUENCES[0x16] == 48000
    decodeur = Decodeur()
    [t] = list(decodeur.avaler(trame(0x12, b"ab")))
    assert t.est_audio and t.frequence() == 16000


def test_l_erreur_n_est_pas_avalee():
    """Mesure 17 : une erreur muette coute plus cher que l'erreur elle-meme."""
    decodeur = Decodeur()
    [t] = list(decodeur.avaler(trame(TYPE_ERREUR, b"\x01")))
    assert t.est_erreur


def test_un_type_inconnu_ne_fait_pas_tomber_la_session():
    """Asterisk peut ajouter des types : on les ignore, on ne plante pas."""
    decodeur = Decodeur()
    trames = list(decodeur.avaler(trame(0x42, b"quelque chose") + trame(TYPE_FIN)))
    assert [t.type for t in trames] == [0x42, TYPE_FIN]
    assert not trames[0].est_audio


# --- encodage ---------------------------------------------------------------

def test_encoder_produit_un_entete_conforme():
    brut = encoder(TYPE_AUDIO_8K, b"\x01\x02")
    assert brut[0] == TYPE_AUDIO_8K
    assert int.from_bytes(brut[1:3], "big") == 2
    assert brut[3:] == b"\x01\x02"


def test_une_charge_trop_longue_est_decoupee():
    """Deux octets de longueur : 65 535 au maximum. Au-dela, on decoupe plutot
    que de tronquer en silence."""
    morceaux = encoder_audio(b"\x00" * 70000)
    assert len(morceaux) == 2
    decodeur = Decodeur()
    trames = [t for morceau in morceaux for t in decodeur.avaler(morceau)]
    assert sum(len(t.charge) for t in trames) == 70000


def test_l_audio_sortant_part_par_paquets_de_vingt_millisecondes():
    """Un paquet de 20 ms est ce qu'attend un canal telephonique : 160
    echantillons de 16 bits a 8 kHz."""
    morceaux = encoder_audio(b"\x00" * 3200, taille_paquet=320)
    assert len(morceaux) == 10
    assert all(int.from_bytes(m[1:3], "big") == 320 for m in morceaux)
