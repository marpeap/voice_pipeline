"""Ce que le standard occupe en mémoire, avec les vrais moteurs.

Mesure 25 de `docs/09`. La question décide de la machine : petites-claques et
petites-frappes ont 1 Go, et l'API Marpeap tourne déjà sur la première. Un
service qui n'y tient pas demande un VPS de plus, donc une dépense.

    .venv/bin/python bancs/empreinte.py                 # moteurs locaux
    VARIANTE_STT=muet APPELS=14 .venv/bin/python bancs/empreinte.py

Deux pièges que ce banc a rencontrés, et qui valent pour toute mesure de
mémoire :
  - `ru_maxrss` est un **pic** : il ne peut que monter, et ne dit donc rien
    d'une fuite. Il faut lire `/proc/self/statm` pour voir la mémoire
    redescendre ;
  - trois appels ne suffisent pas à conclure. La courbe monte encore au
    sixième, et ne se stabilise qu'ensuite.
"""
import os
import resource
import socket
import sys
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
sys.path.insert(0, os.path.join(RACINE, "bancs"))
from appel_reel import MODELE_STT, VOIX_APPELANT, MARDI, voix, envoyer, silence, ecouter
from standard.audiosocket import Decodeur
from standard.demarrage import construire_serveur


def rss_mo():
    """La RSS COURANTE, pas le pic.

    `ru_maxrss` ne peut que monter : il ne dit rien d'une fuite, seulement du
    plus haut jamais atteint. Pour savoir si la memoire redescend entre deux
    appels, il faut lire `/proc/self/statm`.
    """
    with open("/proc/self/statm") as fichier:
        pages = int(fichier.read().split()[1])
    return pages * os.sysconf("SC_PAGE_SIZE") / (1024 * 1024)


def pic_mo():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


print(f"variante STT : {os.environ.get('VARIANTE_STT', 'local')}")
print(f"au démarrage du processus       : {rss_mo():7.0f} Mo")

base = "/tmp/empreinte.sqlite3"
if os.path.exists(base):
    os.remove(base)
serveur = construire_serveur({
    "STANDARD_TENANT": "salon-marpeap",
    "STANDARD_PACK": os.path.join(RACINE, "packs", "coiffure.json"),
    "STANDARD_REPONSES": '{"A1": "Salon Marpeap"}',
    "STANDARD_CRENEAUX": "09:00,10:30,14:00,15:30,17:00",
    "STANDARD_JOURS_FERMES": "6,0", "STANDARD_AUJOURDHUI": MARDI,
    "STANDARD_PORT": "0", "STANDARD_PORT_SANTE": "0", "STANDARD_PORT_TOILE": "0",
    "STANDARD_BASE": base,
    "STANDARD_STT": os.environ.get("VARIANTE_STT", "local"),
    "STANDARD_STT_MODELE": MODELE_STT,
    "STANDARD_TTS": "piper", "STANDARD_VOIX": VOIX_APPELANT,
})
serveur.demarrer()
print(f"service démarré, moteurs chargés : {rss_mo():7.0f} Mo")

REPLIQUES = ["bonjour je voudrais un rendez-vous jeudi à quinze heures trente",
             "oui c'est parfait", "au nom de Dupont"]
import gc

for tour in range(int(os.environ.get("APPELS", "3"))):
    prise = socket.create_connection(("127.0.0.1", serveur.port), timeout=5)
    decodeur = Decodeur()
    ecouter(prise, decodeur, 1.5)
    for replique in REPLIQUES:
        envoyer(prise, voix(replique))
        envoyer(prise, silence(900))
        ecouter(prise, decodeur, 2.0)
    prise.close()
    time.sleep(0.3)
    gc.collect()
    if (tour + 1) % 2 == 0 or tour == 0:
        print(f"après {tour + 1:2d} appel(s)               : {rss_mo():7.0f} Mo")

serveur.arreter()
print(f"\nRSS finale                      : {rss_mo():7.0f} Mo")
print(f"pic depuis le démarrage         : {pic_mo():7.0f} Mo")
print("(les VPS petites-claques et petites-frappes ont 1024 Mo, API comprise)")
