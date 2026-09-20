"""Deux appels en même temps sur le même créneau — la course réelle.

Le banc joue déjà la course avec un « intrus » écrit directement en base. Ce
n'est pas tout à fait le cas réel : deux **appels téléphoniques** simultanés
négocient la même heure, chacun avec sa session, son agent, son agenda lu au
décrochage. L'agenda des deux dit « libre », et les deux appelants disent oui.

Ce que le produit doit garantir : **un seul rendez-vous**, et l'autre appelant
prévenu tout de suite avec ce qui reste — jamais un doublon, jamais un silence.
"""

import os
import socket
import struct
import threading
import time

import pytest

from standard.audiosocket import TYPE_AUDIO_8K, encoder
from standard.demarrage import construire_serveur
from standard.depot import Depot

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAROLE = b"".join(struct.pack("<h", 8000 if i % 2 else -8000) for i in range(160))


class ScriptePorFil:
    """Ce que dit chaque appelant, par fil : deux conversations, un moteur."""

    def __init__(self, repliques):
        self.repliques = repliques
        self.tours = {}

    def __call__(self, audio, frequence):
        fil = threading.get_ident()
        rang = self.tours.get(fil, 0)
        self.tours[fil] = rang + 1
        return self.repliques[rang] if rang < len(self.repliques) else ""


def parler(prise, silence_ms=900):
    for _ in range(10):
        prise.sendall(encoder(TYPE_AUDIO_8K, PAROLE))
    for _ in range(int(silence_ms / 20) + 5):
        prise.sendall(encoder(TYPE_AUDIO_8K, bytes(320)))


@pytest.fixture
def serveur(tmp_path):
    chemin = str(tmp_path / "essai.sqlite3")
    serveur = construire_serveur({
        "STANDARD_TENANT": "salon-1",
        "STANDARD_PACK": os.path.join(RACINE, "packs", "coiffure.json"),
        "STANDARD_REPONSES": '{"A1": "Salon Elegance"}',
        "STANDARD_CRENEAUX": "09:00,10:30,15:30",
        "STANDARD_AUJOURDHUI": "2026-09-15",
        "STANDARD_PORT": "0", "STANDARD_PORT_SANTE": "0",
        "STANDARD_BASE": chemin,
        "STANDARD_STT": "muet", "STANDARD_TTS": "muet",
    })
    serveur.transcrire = ScriptePorFil([
        "je voudrais un rendez-vous jeudi à quinze heures trente",
        "oui c'est parfait",
        "au nom de Dupont",
    ])
    serveur.chemin_base = chemin
    serveur.demarrer()
    yield serveur
    serveur.arreter()


def un_appel(serveur, resultats, cle):
    prise = socket.create_connection(("127.0.0.1", serveur.port), timeout=5)
    try:
        for _ in range(3):
            parler(prise)
            time.sleep(0.2)
    except OSError as erreur:
        resultats[cle] = f"coupé : {erreur}"
    finally:
        prise.close()


def test_deux_appelants_sur_le_meme_creneau_ne_font_qu_un_rendez_vous(serveur):
    resultats = {}
    fils = [threading.Thread(target=un_appel, args=(serveur, resultats, cle))
            for cle in ("a", "b")]
    for fil in fils:
        fil.start()
    for fil in fils:
        fil.join(timeout=30)
    time.sleep(0.5)

    rendez_vous = Depot(serveur.chemin_base).lister("salon-1")
    assert len(rendez_vous) == 1, f"doublon : {rendez_vous}"
    assert rendez_vous[0]["heure"] == "15:30"


def test_le_perdant_de_la_course_s_entend_proposer_autre_chose(serveur):
    resultats = {}
    fils = [threading.Thread(target=un_appel, args=(serveur, resultats, cle))
            for cle in ("a", "b")]
    for fil in fils:
        fil.start()
    for fil in fils:
        fil.join(timeout=30)
    time.sleep(0.5)

    appels = serveur.journal.lister("salon-1")
    assert len(appels) == 2, f"les deux appels doivent être journalisés : {appels}"
    phrases = " ".join(t.get("phrase", "") for appel in appels
                       for t in appel.get("tours", []))
    assert "vient d'être pris" in phrases, phrases
    assert "Il me reste" in phrases


def test_aucun_des_deux_appels_ne_finit_en_panne(serveur):
    fils = [threading.Thread(target=un_appel, args=(serveur, {}, cle))
            for cle in ("a", "b")]
    for fil in fils:
        fil.start()
    for fil in fils:
        fil.join(timeout=30)
    time.sleep(0.5)

    assert serveur.pannes_pendant_appel == 0
    assert serveur.archivages_perdus == 0
    for appel in serveur.journal.lister("salon-1"):
        genres = [t.get("genre") for t in appel.get("tours", [])]
        assert "panne" not in genres, appel
