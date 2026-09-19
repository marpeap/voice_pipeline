"""Le serveur : ce qui manquait pour qu'un appel réel puisse arriver.

La vérification d'avant-livraison a trouvé que tout le produit était une
bibliothèque — aucun point d'entrée n'écoutait quoi que ce soit. Un standard
téléphonique qui ne peut pas recevoir de connexion n'est pas livrable, quel que
soit le nombre de tests.

Ici on ouvre un vrai socket, sur la boucle locale, et on parle le protocole.
"""

import socket
import threading
import time

import pytest

from standard.audiosocket import TYPE_AUDIO_8K, TYPE_FIN, Decodeur, encoder
from standard.serveur import ServeurAudioSocket


def parole(n, amplitude=8000):
    import struct
    return b"".join(struct.pack("<h", amplitude if i % 2 else -amplitude) for i in range(n))


class AgentFactice:
    def __init__(self):
        self.entendus = []

    def salutation(self):
        return "Bonjour, assistant automatique."

    def tour(self, transcription, bruite=False):
        from standard.appel import Reponse
        self.entendus.append(transcription)
        return Reponse("question", "J'ai bien entendu.")


@pytest.fixture
def serveur():
    agents = []

    def fabrique():
        agent = AgentFactice()
        agents.append(agent)
        return agent

    s = ServeurAudioSocket(fabrique_agent=fabrique,
                           transcrire=lambda audio, frequence: "une phrase",
                           synthetiser=lambda texte: [texte.encode()],
                           hote="127.0.0.1", port=0, rythme=False)
    s.demarrer()
    s.agents = agents
    yield s
    s.arreter()


def client(serveur):
    prise = socket.create_connection(("127.0.0.1", serveur.port), timeout=2)
    prise.settimeout(2)
    return prise


def lire_trames(prise, attendu=1, delai=1.5):
    decodeur = Decodeur()
    trames = []
    fin = time.time() + delai
    while len(trames) < attendu and time.time() < fin:
        try:
            morceau = prise.recv(65536)
        except socket.timeout:
            break
        if not morceau:
            break
        trames += list(decodeur.avaler(morceau))
    return trames


def test_le_serveur_ecoute_vraiment():
    """Le test le plus bête du dépôt, et celui qui manquait."""
    s = ServeurAudioSocket(fabrique_agent=AgentFactice,
                           transcrire=lambda a, f: "", synthetiser=lambda t: [b""],
                           hote="127.0.0.1", port=0)
    s.demarrer()
    try:
        assert s.port > 0
        prise = socket.create_connection(("127.0.0.1", s.port), timeout=2)
        prise.close()
    finally:
        s.arreter()


def test_l_annonce_part_des_la_connexion(serveur):
    prise = client(serveur)
    trames = lire_trames(prise, attendu=1)
    assert trames and trames[0].type == TYPE_AUDIO_8K
    prise.close()


def test_un_appel_complet_se_deroule(serveur):
    prise = client(serveur)
    lire_trames(prise, attendu=1)
    for _ in range(5):
        prise.sendall(encoder(TYPE_AUDIO_8K, parole(160)))
    for _ in range(40):
        prise.sendall(encoder(TYPE_AUDIO_8K, bytes(320)))
    trames = lire_trames(prise, attendu=1, delai=2)
    prise.close()
    time.sleep(0.2)
    assert serveur.agents and serveur.agents[0].entendus == ["une phrase"]
    assert trames, "l'agent n'a rien repondu"


def test_deux_appels_simultanes_ne_se_melangent_pas(serveur):
    premiere, seconde = client(serveur), client(serveur)
    lire_trames(premiere, attendu=1)
    lire_trames(seconde, attendu=1)
    premiere.close()
    seconde.close()
    time.sleep(0.2)
    assert len(serveur.agents) == 2, "les deux appels partagent le meme agent"


def test_le_raccrochage_libere_l_appel(serveur):
    prise = client(serveur)
    lire_trames(prise, attendu=1)
    prise.sendall(encoder(TYPE_FIN))
    time.sleep(0.3)
    prise.close()
    assert serveur.appels_en_cours == 0


def test_une_coupure_brutale_ne_tue_pas_le_serveur(serveur):
    """Un appelant qui raccroche mal ferme le socket sans prevenir : le serveur
    doit survivre, sinon un seul appel rate emporte tous les autres."""
    prise = client(serveur)
    prise.close()
    time.sleep(0.2)
    autre = client(serveur)
    assert lire_trames(autre, attendu=1)
    autre.close()


def test_le_serveur_compte_ses_appels(serveur):
    prise = client(serveur)
    lire_trames(prise, attendu=1)
    assert serveur.appels_en_cours == 1
    prise.close()
    time.sleep(0.3)
    assert serveur.appels_en_cours == 0
    assert serveur.appels_total == 1
