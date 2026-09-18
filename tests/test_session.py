"""La session telephonique : le protocole branche sur le pipeline.

Ce qui est verifie ici tient en une phrase : un appel entier peut se derouler
sans qu'aucun processus externe ne soit lance, sans qu'une trame coupee ne casse
quoi que ce soit, et sans qu'un chiffre compose au clavier ne se perde.
"""

import pytest

from standard.audiosocket import (
    TYPE_AUDIO_8K,
    TYPE_DTMF,
    TYPE_FIN,
    TYPE_UUID,
    Decodeur,
    encoder,
)
from standard.session import SessionTelephonique, reechantillonner


def parole(n, amplitude=8000):
    import struct
    return b"".join(struct.pack("<h", amplitude if i % 2 else -amplitude) for i in range(n))


class AgentFactice:
    """Un agent de test : il rend une phrase, on regarde ce qui est joue."""

    def __init__(self):
        self.entendus = []

    def salutation(self):
        return "Bonjour, assistant automatique."

    def tour(self, transcription, bruite=False):
        self.entendus.append(transcription)
        from standard.appel import Reponse
        return Reponse("question", f"J'ai entendu : {transcription}")


def session(agent=None, moteur=None):
    return SessionTelephonique(
        agent=agent or AgentFactice(),
        transcrire=moteur or (lambda audio, frequence: "une phrase"),
        synthetiser=lambda texte: [texte.encode()],
    )


# --- le reechantillonnage se fait dans le processus (mesure 6) --------------

def test_reechantillonner_ne_lance_aucun_processus(monkeypatch):
    """Mesure 6 : 11 ms de travail reel, mais 45 ms rien que pour lancer ffmpeg.
    Un processus externe par fragment ajoute plus d'un tiers du budget."""
    import subprocess

    def interdit(*args, **kwargs):
        raise AssertionError("un processus externe a ete lance")

    monkeypatch.setattr(subprocess, "run", interdit)
    monkeypatch.setattr(subprocess, "Popen", interdit)
    sortie = reechantillonner(parole(160), 8000, 16000)
    assert len(sortie) == 160 * 2 * 2


def test_reechantillonner_sans_changement_rend_le_meme_audio():
    audio = parole(80)
    assert reechantillonner(audio, 8000, 8000) is audio


def test_reechantillonner_vers_le_bas():
    assert len(reechantillonner(parole(160), 16000, 8000)) == 160


# --- l'appel, de la premiere trame a la derniere ----------------------------

def test_la_salutation_part_des_l_ouverture():
    s = session()
    sortant = s.ouvrir()
    decodeur = Decodeur()
    trames = [t for morceau in sortant for t in decodeur.avaler(morceau)]
    assert trames and all(t.type == TYPE_AUDIO_8K for t in trames)


def test_l_uuid_identifie_l_appel():
    s = session()
    s.ouvrir()
    s.recevoir(encoder(TYPE_UUID, bytes(range(16))))
    assert s.identifiant is not None and len(s.identifiant) == 36


def test_une_trame_coupee_ne_casse_rien():
    s = session()
    s.ouvrir()
    brut = encoder(TYPE_AUDIO_8K, parole(160))
    assert s.recevoir(brut[:5]) == []
    s.recevoir(brut[5:])
    assert s.audio_recu > 0


def test_le_silence_apres_la_parole_declenche_le_tour():
    agent = AgentFactice()
    s = session(agent)
    s.ouvrir()
    for _ in range(10):
        s.recevoir(encoder(TYPE_AUDIO_8K, parole(160)))
    sortant = []
    for _ in range(int(s.silence_de_fin_ms / 20) + 1):
        sortant += s.recevoir(encoder(TYPE_AUDIO_8K, bytes(320)))
    assert agent.entendus == ["une phrase"], "le tour n'a pas ete declenche"
    assert sortant, "rien n'a ete joue en reponse"


def test_le_raccrochage_ferme_la_session():
    s = session()
    s.ouvrir()
    s.recevoir(encoder(TYPE_FIN))
    assert s.fermee is True
    with pytest.raises(RuntimeError):
        s.recevoir(encoder(TYPE_AUDIO_8K, parole(80)))


# --- le clavier, filet de la regle T7 ---------------------------------------

def test_les_chiffres_composes_forment_un_numero():
    """Regle T7 : apres deux echecs sur un numero, on bascule au clavier. Encore
    faut-il ramasser les chiffres — Asterisk les envoie un par un."""
    s = session()
    s.ouvrir()
    s.attendre_un_numero()
    for chiffre in "0612345678":
        s.recevoir(encoder(TYPE_DTMF, chiffre.encode()))
    assert s.numero_compose() == "0612345678"


def test_le_diese_termine_la_saisie_avant_dix_chiffres():
    s = session()
    s.ouvrir()
    s.attendre_un_numero()
    for chiffre in "061234#":
        s.recevoir(encoder(TYPE_DTMF, chiffre.encode()))
    assert s.saisie_terminee is True
    assert s.numero_compose() is None, "six chiffres ne font pas un numero"


def test_l_etoile_efface_la_saisie():
    s = session()
    s.ouvrir()
    s.attendre_un_numero()
    for chiffre in "0612*0687654321":
        s.recevoir(encoder(TYPE_DTMF, chiffre.encode()))
    assert s.numero_compose() == "0687654321"


def test_les_chiffres_hors_saisie_ne_polluent_pas():
    s = session()
    s.ouvrir()
    s.recevoir(encoder(TYPE_DTMF, b"5"))
    assert s.numero_compose() is None
