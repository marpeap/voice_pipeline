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


# --- l'interruption, à travers le serveur réel -------------------------------
#
# Une revue indépendante a mesuré le 19/09 six secondes de parole d'agent
# par-dessus l'appelant : le test d'interruption passait parce qu'il appelait la
# session directement, sans serveur. Or le serveur émettait dans le fil qui lit
# la socket — tant qu'il parlait, il n'écoutait pas, et l'interruption ne pouvait
# pas être détectée.

class AgentBavard:
    def salutation(self):
        return "b" * 40          # ~40 paquets de 20 ms, soit près d'une seconde

    def tour(self, transcription, bruite=False):
        from standard.appel import Reponse
        return Reponse("question", "b" * 40)


def test_l_agent_se_tait_quand_on_lui_coupe_la_parole_a_travers_le_serveur():
    """Le test que la revue réclamait : à travers une vraie socket."""
    s = ServeurAudioSocket(fabrique_agent=AgentBavard,
                           transcrire=lambda audio, frequence: "",
                           # un paquet de synthèse par caractère, pour durer
                           synthetiser=lambda texte: [bytes(320) for _ in texte],
                           hote="127.0.0.1", port=0, rythme=True)
    s.demarrer()
    try:
        prise = socket.create_connection(("127.0.0.1", s.port), timeout=3)
        prise.settimeout(0.3)
        recu = 0
        depart = time.time()
        # L'appelant parle sans discontinuer dès la première seconde.
        while time.time() - depart < 1.2:
            prise.sendall(encoder(TYPE_AUDIO_8K, parole(160)))
            try:
                morceau = prise.recv(65536)
                recu += len(morceau)
            except socket.timeout:
                pass
            time.sleep(0.02)

        # On laisse retomber : plus rien ne doit arriver après l'interruption.
        time.sleep(0.4)
        apres = 0
        try:
            while True:
                morceau = prise.recv(65536)
                if not morceau:
                    break
                apres += len(morceau)
        except socket.timeout:
            pass
        prise.close()
    finally:
        s.arreter()

    assert recu > 0, "l'agent n'a rien dit du tout"
    assert apres < 3200, (
        f"{apres} octets emis apres l'interruption : l'agent parle encore "
        "par-dessus l'appelant")


def test_le_serveur_lit_pendant_qu_il_parle():
    """La cause racine : émettre dans le fil qui lit la socket rend toute
    interruption impossible."""
    import inspect

    from standard import serveur as module
    source = inspect.getsource(module.ServeurAudioSocket)
    assert "_emettre_en_continu" in source, \
        "l'emission doit vivre dans son propre fil, sinon le serveur n'ecoute pas"


def test_l_arret_attend_les_appels_en_cours():
    """`__main__` promet « les appels en cours se terminent, aucun n'est coupé au
    milieu d'une phrase ». Les fils étaient daemon et mouraient avec le processus."""
    s = ServeurAudioSocket(fabrique_agent=AgentFactice,
                           transcrire=lambda a, f: "", synthetiser=lambda t: [b""],
                           hote="127.0.0.1", port=0, rythme=False)
    s.demarrer()
    prise = socket.create_connection(("127.0.0.1", s.port), timeout=2)
    time.sleep(0.2)
    assert s.appels_en_cours == 1
    s.arreter()
    assert s.appels_en_cours == 0, "l'arrêt n'a pas attendu l'appel en cours"
    prise.close()
