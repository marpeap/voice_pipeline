"""Ce qui se passe quand ça tombe pendant l'appel.

Seconde revue (19/09) : une panne du moteur de transcription, un 429 du
fournisseur, ou un octet de travers dans le protocole **raccrochaient au nez de
l'appelant, en silence**. `urllib.error.URLError` hérite d'`OSError`, donc la
garde du serveur — écrite pour les sockets — avalait aussi les pannes réseau.

La règle : **l'agent parle, ou il passe la main. Il ne se tait jamais.**
"""

import socket
import time
import urllib.error

import pytest

from standard.audiosocket import TYPE_AUDIO_8K, TYPE_DTMF, TYPE_UUID, Decodeur, encoder
from standard.serveur import ServeurAudioSocket
from standard.session import SessionTelephonique


def parole(n=160, amplitude=8000):
    import struct
    return b"".join(struct.pack("<h", amplitude if i % 2 else -amplitude) for i in range(n))


class AgentFactice:
    def salutation(self):
        return "Bonjour, assistant automatique."

    def tour(self, transcription, bruite=False):
        from standard.appel import Reponse
        return Reponse("question", "J'ai entendu.")


def session_avec(transcrire=None, agent=None):
    return SessionTelephonique(
        agent=agent or AgentFactice(),
        transcrire=transcrire or (lambda audio, frequence: "une phrase"),
        synthetiser=lambda texte: [texte.encode()])


def un_tour(session):
    for _ in range(6):
        session.recevoir(encoder(TYPE_AUDIO_8K, parole()))
    sortant = []
    for _ in range(int(session.silence_de_fin_ms / 20) + 2):
        sortant += session.recevoir(encoder(TYPE_AUDIO_8K, bytes(320)))
    return sortant


# --- les pannes du moteur ----------------------------------------------------

@pytest.mark.parametrize("panne", [
    urllib.error.URLError("réseau coupé"),
    urllib.error.HTTPError("https://x", 429, "Too Many Requests", {}, None),
    RuntimeError("moteur absent"),
    TimeoutError("délai dépassé"),
])
def test_une_panne_de_transcription_fait_parler_l_agent(panne):
    """Le pire état d'un standard : la ligne ouverte et personne au bout."""
    def transcrire_qui_tombe(audio, frequence):
        raise panne

    session = session_avec(transcrire_qui_tombe)
    session.ouvrir()
    sortant = un_tour(session)
    assert sortant, "l'agent est resté muet pendant une panne"
    assert not session.fermee, "l'appel a été coupé au nez de l'appelant"


def test_une_panne_repetee_passe_la_main():
    """Insister ne répare pas une panne : au bout de deux tours, on transfère."""
    def transcrire_qui_tombe(audio, frequence):
        raise urllib.error.URLError("toujours coupé")

    session = session_avec(transcrire_qui_tombe)
    session.ouvrir()
    un_tour(session)
    un_tour(session)
    assert session.transfert_demande is True


def test_une_panne_de_l_agent_fait_aussi_parler():
    class AgentQuiTombe(AgentFactice):
        def tour(self, transcription, bruite=False):
            raise RuntimeError("le modèle a explosé")

    session = session_avec(agent=AgentQuiTombe())
    session.ouvrir()
    sortant = un_tour(session)
    assert sortant
    assert not session.fermee


# --- les octets de travers ---------------------------------------------------

@pytest.mark.parametrize("trame", [
    encoder(TYPE_UUID, b"court"),          # 5 octets au lieu de 16
    encoder(TYPE_DTMF, b""),               # aucun chiffre
    encoder(TYPE_DTMF, b"ab"),             # deux caractères
    encoder(TYPE_UUID, b""),               # vide
])
def test_une_trame_malformee_ne_coupe_pas_l_appel(trame):
    """Le bord téléphonique n'est pas sous notre contrôle : un octet de travers
    ne doit pas valoir un raccrochage."""
    session = session_avec()
    session.ouvrir()
    session.recevoir(trame)
    assert not session.fermee
    assert session.trames_ignorees >= 1


def test_une_trame_malformee_n_empeche_pas_la_suite():
    session = session_avec()
    session.ouvrir()
    session.recevoir(encoder(TYPE_UUID, b"court") + encoder(TYPE_UUID, bytes(range(16))))
    assert session.identifiant is not None


# --- à travers le serveur réel ------------------------------------------------

def test_le_serveur_survit_a_une_panne_du_moteur():
    def transcrire_qui_tombe(audio, frequence):
        raise urllib.error.URLError("réseau coupé")

    serveur = ServeurAudioSocket(fabrique_agent=AgentFactice,
                                 transcrire=transcrire_qui_tombe,
                                 synthetiser=lambda texte: [texte.encode()],
                                 hote="127.0.0.1", port=0, rythme=False)
    serveur.demarrer()
    try:
        prise = socket.create_connection(("127.0.0.1", serveur.port), timeout=3)
        prise.settimeout(1)
        decodeur = Decodeur()
        recu = bytearray()
        for _ in range(6):
            prise.sendall(encoder(TYPE_AUDIO_8K, parole()))
        for _ in range(45):
            prise.sendall(encoder(TYPE_AUDIO_8K, bytes(320)))
        time.sleep(0.5)
        try:
            while True:
                morceau = prise.recv(65536)
                if not morceau:
                    break
                recu.extend(morceau)
        except socket.timeout:
            pass
        prise.close()
    finally:
        serveur.arreter()

    trames = list(decodeur.avaler(bytes(recu)))
    dit = b"".join(t.charge for t in trames).decode("utf-8", "replace")
    assert len(dit) > len("Bonjour, assistant automatique."), \
        "l'appelant n'a rien entendu après l'annonce : la panne l'a laissé seul"


def test_un_archivage_qui_tombe_ne_fausse_pas_le_compteur_d_appels():
    """Le journal peut échouer — base verrouillée, disque plein. L'appel est
    fini : le compteur d'appels en cours doit revenir à zéro quand même, sinon
    l'arrêt propre attend un appel qui n'existe plus."""
    import socket
    import time

    from standard.serveur import ServeurAudioSocket

    def archiver_qui_casse(session):
        raise RuntimeError("base verrouillée")

    serveur = ServeurAudioSocket(
        fabrique_agent=lambda: AgentFactice(),
        transcrire=lambda audio, frequence: "",
        synthetiser=lambda texte: [b"\x00" * 320],
        port=0, sur_fin=archiver_qui_casse)
    serveur.demarrer()
    try:
        prise = socket.create_connection(("127.0.0.1", serveur.port), timeout=2)
        time.sleep(0.2)
        prise.close()
        for _ in range(50):
            if serveur.appels_en_cours == 0:
                break
            time.sleep(0.05)
        assert serveur.appels_en_cours == 0, "un appel fantôme reste compté"
        assert serveur.archivages_perdus == 1
    finally:
        serveur.arreter()
