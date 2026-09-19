"""Le test qui manquait : prendre un rendez-vous **à travers une socket**.

Une revue indépendante a trouvé le 19/09 que le produit ne pouvait pas prendre un
seul rendez-vous par téléphone : aucune ligne ne traduisait le « oui » de
l'appelant en écriture. Trois cent soixante-douze tests étaient verts, et la
porte ouverte — parce qu'ils mesuraient une bibliothèque, pas le service.

Ce fichier ferme cette porte. Il part d'une connexion TCP et s'arrête à la ligne
écrite en base. Tant qu'il passe, le chemin complet existe.
"""

import socket
import time
from datetime import date

import pytest

from standard.audiosocket import TYPE_AUDIO_8K, Decodeur, encoder
from standard.demarrage import construire_serveur
from standard.depot import Depot
from standard.journal import JournalDAppels

MARDI = date(2026, 9, 15)


def parole(n=160, amplitude=8000):
    import struct
    return b"".join(struct.pack("<h", amplitude if i % 2 else -amplitude) for i in range(n))


def environnement(base, **remplacements):
    from pathlib import Path
    env = {
        "STANDARD_TENANT": "salon-1",
        "STANDARD_PACK": str(Path(__file__).resolve().parents[1] / "packs" / "coiffure.json"),
        "STANDARD_REPONSES": '{"A1": "Salon Élégance"}',
        "STANDARD_CRENEAUX": "09:00,10:30,15:30",
        "STANDARD_JOURS_FERMES": "6,0",
        "STANDARD_AUJOURDHUI": MARDI.isoformat(),
        "STANDARD_PORT": "0",
        "STANDARD_BASE": base,
        "STANDARD_STT": "muet",
        "STANDARD_TTS": "muet",
    }
    env.update(remplacements)
    return env


class STTScripte:
    """Ce que l'appelant dit, tour après tour."""

    def __init__(self, repliques):
        self.repliques = list(repliques)
        self.tours = 0

    def __call__(self, audio, frequence):
        if self.tours >= len(self.repliques):
            return ""
        texte = self.repliques[self.tours]
        self.tours += 1
        return texte


def parler(prise, session_ms=900):
    """Un tour de parole : du son, puis assez de silence pour clore le tour."""
    for _ in range(5):
        prise.sendall(encoder(TYPE_AUDIO_8K, parole()))
    for _ in range(int(session_ms / 20) + 5):
        prise.sendall(encoder(TYPE_AUDIO_8K, bytes(320)))
    time.sleep(0.3)


@pytest.fixture
def service(tmp_path):
    chemin = str(tmp_path / "essai.sqlite3")
    stt = STTScripte(["je voudrais un rendez-vous jeudi à quinze heures trente",
                      "oui c'est parfait",
                      "c'est au nom de Dupont"])
    serveur = construire_serveur(environnement(chemin))
    serveur.transcrire = stt
    serveur.demarrer()
    serveur.chemin_base = chemin
    yield serveur
    serveur.arreter()


def test_un_rendez_vous_se_prend_a_travers_une_socket(service):
    """Le test central du dépôt. S'il tombe, le produit ne sert à rien."""
    prise = socket.create_connection(("127.0.0.1", service.port), timeout=3)
    prise.settimeout(3)
    try:
        parler(prise)      # la demande
        parler(prise)      # le « oui »
        parler(prise)      # le nom
    finally:
        prise.close()
    time.sleep(0.4)

    depot = Depot(service.chemin_base)
    rendez_vous = depot.lister("salon-1")
    assert rendez_vous, "aucun rendez-vous écrit : le « oui » de l'appelant s'est perdu"
    assert rendez_vous[0]["heure"] == "15:30"


def test_l_appel_laisse_une_trace_au_journal(service):
    prise = socket.create_connection(("127.0.0.1", service.port), timeout=3)
    prise.settimeout(3)
    try:
        parler(prise)
        parler(prise)
    finally:
        prise.close()
    time.sleep(0.4)

    journal = JournalDAppels(Depot(service.chemin_base))
    appels = journal.lister("salon-1")
    assert appels, "l'appel n'a laissé aucune trace : la console serait vide"
    assert appels[0]["preuve_annonce"]["conforme"] is True, \
        "la preuve d'annonce exigée par l'AI Act n'a pas été conservée"


def test_un_creneau_deja_pris_n_est_plus_propose(tmp_path):
    """Sans cela, le deuxième appelant se voit proposer le créneau du premier."""
    chemin = str(tmp_path / "occupe.sqlite3")
    depot = Depot(chemin)
    depot.pour("salon-1").inserer("deja", {"date": "2026-09-17", "heure": "15:30"})

    serveur = construire_serveur(environnement(chemin))
    serveur.transcrire = STTScripte(["je voudrais jeudi à quinze heures trente"])
    serveur.demarrer()
    try:
        prise = socket.create_connection(("127.0.0.1", serveur.port), timeout=3)
        prise.settimeout(3)
        decodeur = Decodeur()
        recu = bytearray()
        try:
            parler(prise)
            fin = time.time() + 1.0
            while time.time() < fin:
                try:
                    morceau = prise.recv(65536)
                except socket.timeout:
                    break
                if not morceau:
                    break
                recu.extend(morceau)
        finally:
            prise.close()
        dit = b"".join(t.charge for t in decodeur.avaler(bytes(recu))).decode("utf-8", "replace")
        assert "15 h 30" not in dit, "un créneau déjà réservé a été proposé à un autre appelant"
    finally:
        serveur.arreter()


def test_la_supervision_rend_un_delai_reel_apres_un_appel(service):
    """La métrique qui dit qu'une machine est pleine doit valoir autre chose que
    `None` une fois qu'un appel a eu lieu."""
    prise = socket.create_connection(("127.0.0.1", service.port), timeout=3)
    prise.settimeout(3)
    try:
        parler(prise)
        parler(prise)
    finally:
        prise.close()
    time.sleep(0.5)
    etat = service.service.supervision()
    assert etat["premier_fragment_p50_ms"] is not None
