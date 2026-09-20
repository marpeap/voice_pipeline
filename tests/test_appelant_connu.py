"""Le numéro de l'appelant, quand l'opérateur le transmet.

`docs/19` rappelle que l'Arcep recommande de masquer l'identifiant d'appelant
sur les renvois complexes : l'agent ne peut donc **jamais compter** dessus, et
c'est pour cela qu'il demande le numéro à voix haute. Mais quand il est là, ne
pas s'en servir coûte deux tours de conversation à chaque appel — et un client
qui a déjà donné son numéro la semaine dernière ne comprend pas qu'on le
redemande.

Le plan de numérotation le dépose avant de brancher l'audio ; le standard le
reprend par l'UUID de l'appel. Rien d'autre ne change : sans lui, tout se passe
comme avant.
"""

import json
import os
import socket
import struct
import time
import urllib.request

import pytest

from standard.audiosocket import TYPE_AUDIO_8K, TYPE_UUID, Trame, encoder
from standard.demarrage import construire_serveur

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UUID = b"\x02" * 16
UUID_TEXTE = Trame(TYPE_UUID, UUID).uuid()


@pytest.fixture
def serveur(tmp_path):
    serveur = construire_serveur({
        "STANDARD_TENANT": "salon-1",
        "STANDARD_PACK": os.path.join(RACINE, "packs", "coiffure.json"),
        "STANDARD_REPONSES": '{"A1": "Salon Elegance"}',
        "STANDARD_CRENEAUX": "15:30",
        "STANDARD_AUJOURDHUI": "2026-09-15",
        "STANDARD_PORT": "0", "STANDARD_PORT_SANTE": "0",
        "STANDARD_BASE": str(tmp_path / "essai.sqlite3"),
        "STANDARD_STT": "muet", "STANDARD_TTS": "muet",
    })
    serveur.demarrer()
    yield serveur
    serveur.arreter()


def deposer(serveur, numero, uuid_texte=UUID_TEXTE):
    url = (f"http://127.0.0.1:{serveur.sante.port}/appelant/{uuid_texte}"
           f"?numero={numero}")
    with urllib.request.urlopen(url, timeout=3) as reponse:
        return reponse.status, reponse.read().decode().strip()


def test_le_plan_depose_le_numero_et_le_standard_le_reprend(serveur):
    statut, corps = deposer(serveur, "0612345678")
    assert statut == 200
    assert serveur.numeros_appelants[UUID_TEXTE] == "0612345678"


def test_un_numero_masque_ne_pollue_rien(serveur):
    """« anonymous », « unknown », vide : Asterisk en envoie de toutes sortes."""
    for masque in ("anonymous", "unknown", "", "+"):
        deposer(serveur, masque, uuid_texte=f"masque-{masque}")
        assert f"masque-{masque}" not in serveur.numeros_appelants


def test_un_numero_etranger_est_refuse(serveur):
    """La grammaire française vaut ici aussi : dix chiffres, pas de 08."""
    deposer(serveur, "0899123456", uuid_texte="premium")
    assert "premium" not in serveur.numeros_appelants


def test_l_appel_part_avec_le_numero_quand_il_a_ete_depose(serveur):
    deposer(serveur, "0612345678")
    serveur.transcrire = lambda audio, frequence: "je voudrais annuler mon rendez-vous"

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

    tours = serveur.journal.lister("salon-1")[0]["tours"]
    dit = " ".join(t.get("phrase", "") for t in tours)
    # Le numéro étant connu, l'agent ne le redemande pas : il cherche direct.
    assert "À quel numéro" not in dit, dit


def test_le_plan_de_numerotation_livre_depose_le_numero():
    plan = open(os.path.join(RACINE, "deploiement", "extensions.conf")).read()
    assert "/appelant/${APPEL_UUID}" in plan
    assert "CALLERID(num)" in plan
