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
         "oui c'est parfait",
         "c'est au nom de Dupont"],
        {"date": "2026-09-17", "heure": "15:30"},
    ),
    "demain-matin": (
        ["bonjour est-ce que vous auriez quelque chose demain à dix heures trente",
         "très bien",
         "au nom de Lefevre"],
        {"date": "2026-09-16", "heure": "10:30"},
    ),
    "jour-seul-puis-heure": (
        ["bonjour je voudrais venir vendredi",
         "à quatorze heures",
         "d'accord",
         "monsieur Martin"],
        {"date": "2026-09-18", "heure": "14:00"},
    ),
    "refus-puis-accord": (
        ["bonjour un rendez-vous jeudi à quinze heures trente",
         "non pas à cette heure-là",
         "à dix-sept heures",
         "c'est parfait",
         "au nom de Nguyen"],
        {"date": "2026-09-17", "heure": "17:00"},
    ),
    "jour-ferme": (
        ["bonjour je voudrais un rendez-vous dimanche à quinze heures trente",
         "alors jeudi à quinze heures trente",
         "oui c'est parfait",
         "au nom de Dupont"],
        {"date": "2026-09-17", "heure": "15:30"},
    ),
    "heure-hors-creneaux": (
        ["bonjour je voudrais un rendez-vous jeudi à onze heures",
         "va pour dix heures trente",
         "oui c'est parfait",
         "au nom de Dupont"],
        {"date": "2026-09-17", "heure": "10:30"},
    ),
    # Un « oui » seul dure six dixiemes de seconde et revient vide du moteur
    # local. L'agent doit relancer, et l'appel doit aboutir quand meme.
    "oui-trop-court": (
        ["bonjour je voudrais un rendez-vous jeudi à quinze heures trente",
         "oui",
         "oui c'est parfait",
         "au nom de Dupont"],
        {"date": "2026-09-17", "heure": "15:30"},
    ),
    # Pendant que l'appelant confirme, quelqu'un d'autre prend la place. L'agent
    # doit le dire et proposer autre chose, pas promettre un rappel du salon.
    "creneau-pris-entre-temps": (
        ["bonjour je voudrais un rendez-vous jeudi à quinze heures trente",
         "oui c'est parfait",
         "au nom de Dupont",
         "alors dix heures trente",
         "oui c'est parfait",
         "au nom de Dupont"],
        {"date": "2026-09-17", "heure": "10:30"},
        None,
        (1, {"date": "2026-09-17", "heure": "15:30"}),
    ),
    # Le salon a choisi « prendre un message » : l'agent ne transfère pas vers
    # un téléphone que personne ne décroche, il note et raccroche proprement.
    "prise-de-message": (
        ["bonjour je voudrais parler à quelqu'un du salon s'il vous plaît",
         "dites-lui que je cherche une coloration végétale pour samedi",
         "zéro six douze trente-quatre cinquante-six soixante-dix-huit",
         # Que le numéro dicté soit relu ou refusé, la suite est la même : le
         # clavier, seul chemin qui ne perd pas de chiffre (mesure 7).
         "non ce n'est pas ça",
         CLAVIER + "0612345678#"],
        {"message": "COLORATION", "telephone": "0612345678"},
        {"STANDARD_REPONSES": '{"A1": "Salon Elegance", "D4": "message"}'},
    ),
    # Le moteur rend « Le Fora » pour « Lefevre » : l'agent redit le nom, et la
    # correction doit atteindre la base sans créer un second rendez-vous.
    "correction-du-nom": (
        ["bonjour je voudrais un rendez-vous jeudi à quinze heures trente",
         "oui c'est parfait",
         "au nom de Dupond",
         "non c'est au nom de Martin",
         # Le moteur rend parfois « NON S'ÉTONNANT DE MARTIN » : l'agent
         # redemande le nom seul, et l'appelant le redit.
         "Martin"],
        {"date": "2026-09-17", "heure": "15:30", "nom": "Martin"},
    ),
    # Un démarcheur : l'agent refuse en une phrase, n'écrit rien, rend la ligne.
    "demarchage": (
        ["bonjour je vous appelle pour vous proposer notre solution de "
         "référencement sur internet"],
        None,
    ),
    # Annuler : le deuxième motif d'appel d'un salon, et une impasse jusqu'au
    # 20/09. Le rendez-vous est semé avant l'appel, comme s'il avait été pris
    # la veille.
    "annulation": (
        ["bonjour je voudrais annuler mon rendez-vous",
         "zéro six douze trente-quatre cinquante-six soixante-dix-huit",
         CLAVIER + "0612345678#",       # si la voix se perd, le clavier prend
         "oui c'est bien ça",
         "oui"],                        # si le « oui » se perd, l'agent redemande
        {"annule": True},
        None,
        (0, {"date": "2026-09-17", "heure": "15:30", "nom": "Dupont",
             "telephone": "0612345678"}),
    ),
    # Déplacer : l'agent doit écrire le nouveau ET annuler l'ancien. Le
    # rendez-vous de la veille est semé avant l'appel.
    "report": (
        ["bonjour je voudrais décaler mon rendez-vous",
         "zéro six douze trente-quatre cinquante-six soixante-dix-huit",
         CLAVIER + "0612345678#",
         "à dix-sept heures jeudi",
         "oui c'est parfait"],
        {"date": "2026-09-17", "heure": "17:00", "nom": "Dupont"},
        None,
        (0, {"date": "2026-09-17", "heure": "15:30", "nom": "Dupont",
             "telephone": "0612345678"}),
    ),
    # Une prestation nommée : elle doit atteindre la ligne écrite, et sa durée
    # doit occuper ce qu'elle dure.
    "prestation-nommee": (
        ["bonjour je voudrais une coloration jeudi à dix heures trente",
         "oui c'est parfait",
         "au nom de Dupont"],
        {"date": "2026-09-17", "heure": "10:30", "prestation": "coloration"},
        # La coloration n'est pas cochée par défaut dans le pack : c'est le
        # salon qui décide de ce que l'agent sait réserver.
        {"STANDARD_REPONSES": '{"A1": "Salon Elegance", '
                              '"C1": ["coupe", "brushing", "coloration"]}'},
    ),
    # Congés : l'agent refuse le jour ET dit quand le salon rouvre.
    "conges": (
        ["bonjour je voudrais un rendez-vous jeudi à quinze heures trente",
         "alors mardi prochain à quinze heures trente",
         "oui c'est parfait",
         "au nom de Dupont"],
        {"date": "2026-09-22", "heure": "15:30"},
        {"STANDARD_REPONSES": '{"A1": "Salon Elegance", '
                              '"A6": "du 2026-09-16 au 2026-09-20"}'},
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
         "au nom de Dupont",
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
        except ConnectionResetError:
            # Le serveur a rendu la main au bord téléphonique (transfert) : côté
            # Asterisk c'est une fin d'appel normale, pas une panne du banc.
            break
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


def intrus(base: str, quand: dict) -> None:
    """Un autre appelant prend la place, pendant que le premier hésite.

    C'est la course que l'index unique de la base est là pour trancher : une
    vérification applicative la perdrait.
    """
    from standard.depot import Depot

    Depot(base).pour("salon-1").inserer("cle-intrus", quand)
    print(f"intrus   : {quand['date']} {quand['heure']} vient d'être pris par un autre")


def jouer(nom: str, repliques, attendu, supplement=None, intrusion=None) -> bool:
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

        for rang, replique in enumerate(repliques_du_tour):
            if intrusion and intrusion[0] == rang:
                intrus(base, intrusion[1])
            if prise.fileno() == -1:
                print("appel terminé par l'agent avant la fin du scénario")
                break
            if replique.startswith(CLAVIER):
                touches = replique[len(CLAVIER):]
                print(f"appelant : [clavier] {touches}")
                for touche in touches:
                    prise.sendall(encoder(TYPE_DTMF, touche.encode()))
                    time.sleep(0.02)
            else:
                print(f"appelant : « {replique} »")
                try:
                    envoyer(prise, voix(replique))
                    envoyer(prise, silence(900))   # de quoi clore le tour
                except (BrokenPipeError, ConnectionResetError):
                    print("l'agent a raccroché ou transféré : fin de l'appel")
                    break
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
    depot = Depot(base)
    rendez_vous = depot.lister("salon-1")
    print()
    for index, audio in enumerate(entendu):
        texte = transcrire_la_reponse(audio)
        if texte:
            print(f"ce que l'appelant a entendu [{index}] : {texte[:220]}")

    print(f"\nrendez-vous en base : {rendez_vous}")
    if attendu and attendu.get("annule"):
        if rendez_vous:
            print(f"ÉCHEC : le rendez-vous est encore là — {rendez_vous}")
            return False
        print("SUCCÈS : le rendez-vous a bien été annulé.")
        return True
    if attendu and "message" in attendu:
        messages = depot.messages("salon-1")
        print(f"messages en base : {messages}")
        if not messages:
            print("ÉCHEC : aucun message n'a été pris.")
            return False
        if attendu["message"] not in messages[0].get("texte", ""):
            print(f"ÉCHEC : le message ne contient pas « {attendu['message']} ».")
            return False
        if attendu.get("telephone") and messages[0].get("telephone") != attendu["telephone"]:
            print(f"ÉCHEC : le numéro de rappel manque ou diffère — {messages[0]}")
            return False
        print("SUCCÈS : le message est en base, avec le numéro de rappel.")
        return True
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
    # Un scenario peut avoir sema un rendez-vous intrus : on cherche le notre
    # parmi les lignes, au lieu de supposer qu'il est arrive le premier.
    if not any(all(ligne.get(champ) == valeur for champ, valeur in attendu.items())
               for ligne in rendez_vous):
        print(f"ÉCHEC : le rendez-vous attendu {attendu} n'est pas dans la base.")
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
        intrusion = scenario[3] if len(scenario) > 3 else None
        print(f"\n========== {nom} ==========")
        resultats[nom] = jouer(nom, repliques, attendu, supplement, intrusion)
    print("\n---------- bilan ----------")
    for nom, reussi in resultats.items():
        print(f"  {'OK  ' if reussi else 'RATÉ'} {nom}")
    rates = [nom for nom, reussi in resultats.items() if not reussi]
    return 1 if rates else 0


if __name__ == "__main__":
    raise SystemExit(main())
