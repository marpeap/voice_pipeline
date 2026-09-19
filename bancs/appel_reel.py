#!/usr/bin/env python3
"""Un appel complet, avec les VRAIS moteurs — sans ligne téléphonique.

C'est la chose la plus proche d'un appel réel qu'on puisse faire sans numéro :
la voix de l'appelant est synthétisée, dégradée en 8 kHz comme le ferait le
réseau, envoyée au serveur en trames AudioSocket ; le serveur transcrit avec le
moteur local, décide, répond ; et l'on vérifie qu'un rendez-vous atterrit en base.

Rien n'est simulé ici sauf la ligne : ni la transcription, ni la synthèse, ni le
protocole, ni la base.

    .venv/bin/python bancs/appel_reel.py
"""

from __future__ import annotations

import os
import socket
import struct
import sys
import time
import wave

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)

from standard.audiosocket import (  # noqa: E402
    PAQUET_20MS_8K,
    TYPE_AUDIO_8K,
    TYPE_DTMF,
    Decodeur,
    encoder,
)
from standard.demarrage import construire_serveur  # noqa: E402
from standard.depot import Depot  # noqa: E402

VOIX_APPELANT = os.path.expanduser("~/piper/fr_FR-siwis-medium.onnx")
MODELE_STT = os.path.expanduser("~/modeles/sherpa-onnx-streaming-zipformer-fr-2023-04-14")
MARDI = "2026-09-15"

# Chaque scenario : un nom, ce que l'appelant dit, ce qu'on doit trouver en base
# a la fin, et — au besoin — ce qui change dans l'environnement du serveur.
# `None` veut dire « rien ne doit s'ecrire » : un appel qui n'aboutit pas est un
# resultat, pas une panne.
CLAVIER = "clavier:"     # une replique composee au clavier, pas dite

SCENARIOS = {
    "creneau-explicite": (
        ["bonjour je voudrais un rendez-vous jeudi à quinze heures trente",
         "oui c'est parfait"],
        {"date": "2026-09-17", "heure": "15:30"},
    ),
    "demain-matin": (
        ["bonjour est-ce que vous auriez quelque chose demain à dix heures trente",
         "très bien"],
        {"date": "2026-09-16", "heure": "10:30"},
    ),
    "jour-seul-puis-heure": (
        ["bonjour je voudrais venir vendredi",
         "à quatorze heures",
         "d'accord"],
        {"date": "2026-09-18", "heure": "14:00"},
    ),
    "refus-puis-accord": (
        ["bonjour un rendez-vous jeudi à quinze heures trente",
         "non pas à cette heure-là",
         "à dix-sept heures",
         "c'est parfait"],
        {"date": "2026-09-17", "heure": "17:00"},
    ),
    "jour-ferme": (
        ["bonjour je voudrais un rendez-vous dimanche à quinze heures trente",
         "alors jeudi à quinze heures trente",
         "oui c'est parfait"],
        {"date": "2026-09-17", "heure": "15:30"},
    ),
    "heure-hors-creneaux": (
        ["bonjour je voudrais un rendez-vous jeudi à onze heures",
         "va pour dix heures trente",
         "oui"],
        {"date": "2026-09-17", "heure": "10:30"},
    ),
    "question-horaires": (
        ["bonjour je voulais juste connaître vos horaires d'ouverture",
         "non merci au revoir"],
        None,
    ),
    # Avec une passerelle SMS, l'agent demande le numero, le fait relire, puis
    # ecrit. C'est le seul chemin du produit qui touche a la fois la grammaire
    # des numeros, l'ecriture et l'envoi.
    "numero-et-sms": (
        ["bonjour je voudrais un rendez-vous jeudi à quinze heures trente",
         "oui c'est parfait",
         # Deux échecs à l'oral suffisent à armer le clavier (règle T7) : c'est
         # ce chemin-là qu'on veut voir marcher de bout en bout.
         "zéro six douze trente-quatre cinquante-six soixante-dix-huit",
         "c'est bien ça",
         CLAVIER + "0612345678#"],
        {"date": "2026-09-17", "heure": "15:30"},
        {"STANDARD_SMS_EXPEDITEUR": "Elegance", "STANDARD_SMS_NOM": "Elegance"},
    ),
}

REPLIQUES = SCENARIOS["creneau-explicite"][0]


def voix(texte: str) -> bytes:
    """La voix de l'appelant, en 8 kHz — la bande du téléphone."""
    from piper import PiperVoice

    if not hasattr(voix, "_voix"):
        voix._voix = PiperVoice.load(VOIX_APPELANT)
    brut, taux = b"", 22050
    for fragment in voix._voix.synthesize(texte):
        brut += getattr(fragment, "audio_int16_bytes", b"")
        taux = getattr(fragment, "sample_rate", taux)

    from standard.session import reechantillonner
    return reechantillonner(brut, taux, 8000)


def silence(duree_ms: int) -> bytes:
    return bytes(int(8000 * duree_ms / 1000) * 2)


def envoyer(prise: socket.socket, audio: bytes) -> None:
    """Au rythme du canal : vingt millisecondes par paquet, comme Asterisk."""
    for debut in range(0, len(audio), PAQUET_20MS_8K):
        prise.sendall(encoder(TYPE_AUDIO_8K, audio[debut:debut + PAQUET_20MS_8K]))
        time.sleep(0.005)          # plus vite que le temps reel : c'est un banc


def ecouter(prise: socket.socket, decodeur: Decodeur, duree_s: float) -> bytes:
    audio = bytearray()
    fin = time.time() + duree_s
    prise.settimeout(0.2)
    while time.time() < fin:
        try:
            morceau = prise.recv(65536)
        except socket.timeout:
            continue
        if not morceau:
            break
        for trame in decodeur.avaler(morceau):
            if trame.est_audio:
                audio.extend(trame.charge)
    return bytes(audio)


def transcrire_la_reponse(audio: bytes) -> str:
    """Ce que l'appelant aurait entendu, relu par un moteur — pour le rapport."""
    if not audio:
        return ""
    sys.path.insert(0, os.path.join(RACINE, "bancs"))
    import wer_sherpa

    chemin = "/tmp/reponse_agent.wav"
    with wave.open(chemin, "wb") as sortie:
        sortie.setnchannels(1)
        sortie.setsampwidth(2)
        sortie.setframerate(8000)
        sortie.writeframes(audio)
    reconnaisseur = wer_sherpa.construire(MODELE_STT, fils=2)
    texte, _, _ = wer_sherpa.transcrire(chemin, reconnaisseur)
    return texte


def passerelle_sms(recus: list):
    """Une passerelle SMS minuscule, en local : elle accuse reception.

    Sans accuse, l'envoyeur refuse de considerer le message comme parti — c'est
    la regle du produit, et le banc doit la respecter comme un vrai fournisseur.
    """
    import json
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Guichet(BaseHTTPRequestHandler):
        def do_POST(self):
            corps = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            recus.append(json.loads(corps or b"{}"))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"id": "sms-1", "delivered": True}).encode())

        def log_message(self, *_):
            pass

    serveur = HTTPServer(("127.0.0.1", 0), Guichet)
    threading.Thread(target=serveur.serve_forever, daemon=True).start()
    return serveur


def jouer(nom: str, repliques, attendu, supplement=None) -> bool:
    """Un appel complet, du decrochage a la verification en base."""
    base = f"/tmp/appel_reel_{nom}.sqlite3"
    if os.path.exists(base):
        os.remove(base)

    supplement = dict(supplement or {})
    messages: list = []
    guichet = None
    if supplement.get("STANDARD_SMS_EXPEDITEUR") and "STANDARD_SMS_BASE" not in supplement:
        guichet = passerelle_sms(messages)
        supplement["STANDARD_SMS_BASE"] = f"http://127.0.0.1:{guichet.server_port}"
        supplement["STANDARD_SMS_CLE"] = "cle-de-banc"

    serveur = construire_serveur({
        "STANDARD_TENANT": "salon-1",
        "STANDARD_PACK": os.path.join(RACINE, "packs", "coiffure.json"),
        "STANDARD_REPONSES": '{"A1": "Salon Elegance"}',
        "STANDARD_CRENEAUX": "09:00,10:30,14:00,15:30,17:00",
        "STANDARD_JOURS_FERMES": "6,0",
        "STANDARD_AUJOURDHUI": MARDI,
        "STANDARD_PORT": "0",
        "STANDARD_BASE": base,
        "STANDARD_STT": "local",
        "STANDARD_STT_MODELE": MODELE_STT,
        "STANDARD_TTS": "piper",
        "STANDARD_VOIX": VOIX_APPELANT,
        **(supplement or {}),
    })
    serveur.demarrer()
    print(f"serveur en écoute sur {serveur.port}\n")

    prise = socket.create_connection(("127.0.0.1", serveur.port), timeout=5)
    repliques_du_tour = repliques
    decodeur = Decodeur()
    entendu = []
    try:
        annonce = ecouter(prise, decodeur, 2.0)
        entendu.append(annonce)
        print(f"annonce  : {len(annonce)} octets reçus")

        for replique in repliques_du_tour:
            if replique.startswith(CLAVIER):
                touches = replique[len(CLAVIER):]
                print(f"appelant : [clavier] {touches}")
                for touche in touches:
                    prise.sendall(encoder(TYPE_DTMF, touche.encode()))
                    time.sleep(0.02)
            else:
                print(f"appelant : « {replique} »")
                envoyer(prise, voix(replique))
                envoyer(prise, silence(900))    # de quoi clore le tour
            reponse = ecouter(prise, decodeur, 3.0)
            entendu.append(reponse)
            print(f"agent    : {len(reponse)} octets audio")
    finally:
        prise.close()
        time.sleep(0.3)
        serveur.arreter()
        if guichet is not None:
            guichet.shutdown()

    print(f"\ninterruptions : {serveur.interruptions_totales} · "
          f"paroles perdues : {serveur.paroles_perdues} · "
          f"pannes pendant l'appel : {serveur.pannes_pendant_appel}")
    rendez_vous = Depot(base).lister("salon-1")
    print()
    for index, audio in enumerate(entendu):
        texte = transcrire_la_reponse(audio)
        if texte:
            print(f"ce que l'appelant a entendu [{index}] : {texte[:220]}")

    print(f"\nrendez-vous en base : {rendez_vous}")
    if attendu is None:
        if rendez_vous:
            print("ÉCHEC : un rendez-vous a été écrit alors qu'on n'en demandait pas.")
            return False
        print("SUCCÈS : rien n'a été écrit, et c'est ce qu'on attendait.")
        return True
    if not rendez_vous:
        print("ÉCHEC : aucun rendez-vous n'a été pris.")
        return False
    if guichet is not None:
        print(f"SMS partis : {len(messages)}")
        if not messages:
            print("ÉCHEC : aucun SMS n'est parti alors qu'une passerelle répondait.")
            return False
        texte = str(messages[0])
        print(f"SMS : {texte[:160]}")
        quand = f"{attendu['date']} {attendu['heure']}" if attendu else ""
        from standard.decision import enoncer_date
        if attendu and enoncer_date(attendu["date"]).split()[0] not in texte.lower():
            print(f"ÉCHEC : le SMS ne porte pas la date confirmée ({quand}).")
            return False
    pris = rendez_vous[0]
    ecart = {champ: (valeur, pris.get(champ)) for champ, valeur in attendu.items()
             if pris.get(champ) != valeur}
    if ecart:
        print(f"ÉCHEC : ce n'est pas le rendez-vous attendu — {ecart}")
        return False
    print("SUCCÈS : le rendez-vous attendu est en base.")
    return True


def main() -> int:
    voulus = sys.argv[1:] or list(SCENARIOS)
    resultats = {}
    for nom in voulus:
        scenario = SCENARIOS[nom]
        repliques, attendu = scenario[0], scenario[1]
        supplement = scenario[2] if len(scenario) > 2 else None
        print(f"\n========== {nom} ==========")
        resultats[nom] = jouer(nom, repliques, attendu, supplement)
    print("\n---------- bilan ----------")
    for nom, reussi in resultats.items():
        print(f"  {'OK  ' if reussi else 'RATÉ'} {nom}")
    rates = [nom for nom, reussi in resultats.items() if not reussi]
    return 1 if rates else 0


if __name__ == "__main__":
    raise SystemExit(main())
