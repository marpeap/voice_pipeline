"""Ce que le plan de numérotation doit savoir : comment l'appel s'est terminé.

Le dialplan livré appelait `AudioSocket()` puis `Hangup()`. Trois conséquences,
toutes mauvaises et toutes silencieuses :

  - un **transfert** demandé par l'agent raccrochait au nez de l'appelant,
    alors que le code dit « le bord téléphonique reprend la main » ;
  - le standard **arrêté** ou **au plafond** (la ligne est rendue tout de suite)
    donnait un appel qui décroche et ne dit rien ;
  - un **démarchage** filtré aurait été renvoyé au salon si l'on se contentait
    de basculer par défaut.

Le plan a donc besoin d'une réponse : `GET /issue/<uuid>`.
"""

import json
import os
import socket
import struct
import time
import urllib.request

import pytest

from standard.audiosocket import TYPE_AUDIO_8K, TYPE_UUID, encoder
from standard.demarrage import construire_serveur

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UUID = b"\x01" * 16


@pytest.fixture
def serveur(tmp_path):
    serveur = construire_serveur({
        "STANDARD_TENANT": "salon-1",
        "STANDARD_PACK": os.path.join(RACINE, "packs", "coiffure.json"),
        "STANDARD_REPONSES": '{"A1": "Salon Elegance"}',
        "STANDARD_CRENEAUX": "15:30",
        "STANDARD_PORT": "0", "STANDARD_PORT_SANTE": "0",
        "STANDARD_BASE": str(tmp_path / "essai.sqlite3"),
        "STANDARD_STT": "muet", "STANDARD_TTS": "muet",
    })
    serveur.demarrer()
    yield serveur
    serveur.arreter()


def issue(serveur, uuid_texte):
    url = f"http://127.0.0.1:{serveur.sante.port}/issue/{uuid_texte}"
    with urllib.request.urlopen(url, timeout=3) as reponse:
        return reponse.read().decode().strip()


def jouer(serveur, transcription):
    serveur.transcrire = lambda audio, frequence: transcription
    prise = socket.create_connection(("127.0.0.1", serveur.port), timeout=3)
    prise.sendall(encoder(TYPE_UUID, UUID))
    parole = b"".join(struct.pack("<h", 8000 if i % 2 else -8000) for i in range(160))
    for _ in range(10):
        prise.sendall(encoder(TYPE_AUDIO_8K, parole))
    for _ in range(60):
        prise.sendall(encoder(TYPE_AUDIO_8K, bytes(320)))
    time.sleep(0.8)
    prise.close()
    time.sleep(0.4)
    from standard.audiosocket import Trame
    return Trame(TYPE_UUID, UUID).uuid()


def test_un_appel_qui_demande_un_humain_se_dit_transfert(serveur):
    uuid_texte = jouer(serveur, "je voudrais parler à quelqu'un du salon")
    assert issue(serveur, uuid_texte) == "transfert"


def test_un_demarchage_filtre_ne_se_renvoie_pas_au_salon(serveur):
    uuid_texte = jouer(
        serveur, "bonjour je vous appelle pour vous proposer notre solution")
    assert issue(serveur, uuid_texte) == "demarchage"


def test_un_appel_ordinaire_se_dit_fin(serveur):
    uuid_texte = jouer(serveur, "bonjour je voudrais un rendez-vous jeudi")
    assert issue(serveur, uuid_texte) == "fin"


def test_un_appel_inconnu_ne_fait_pas_tomber_le_plan(serveur):
    """Le dialplan interroge avec un UUID qu'il vient de fabriquer : s'il
    n'existe pas encore, la réponse doit rester exploitable."""
    assert issue(serveur, "00000000-0000-0000-0000-000000000000") == "inconnu"


def test_le_plan_de_numerotation_livre_demande_bien_l_issue():
    """Un plan qui raccroche après `AudioSocket()` perd tous les transferts.
    Le fichier livré est la seule chose que l'installateur recopie : c'est lui
    qu'on vérifie, pas une intention."""
    plan = (open(os.path.join(RACINE, "deploiement", "extensions.conf"))
            .read())
    assert "/issue/${APPEL_UUID}" in plan
    assert "Dial(${POSTE_DU_SALON}" in plan
    # Le défaut penche du bon côté : inconnu → le poste du salon sonne.
    assert plan.index('"${ISSUE}" = "demarchage"') < plan.index("Dial(${POSTE_DU_SALON}")
