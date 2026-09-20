"""Ce que les vrais moteurs mettent, tour par tour — mesuré, pas supposé.

Mesure 24 de `docs/09`. Neuf tours contre le serveur complet, avec la voix
synthétisée dégradée en 8 kHz et les moteurs locaux. Ce banc a d'abord servi à
découvrir que `premier_fragment_ms` valait zéro : il lisait la file d'attente
et pas la synthèse.

    .venv/bin/python bancs/latence.py
"""
import os, socket, statistics, struct, sys, time
RACINE_DU_DEPOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE_DU_DEPOT)
sys.path.insert(0, os.path.join(RACINE_DU_DEPOT, "bancs"))
from appel_reel import voix, MODELE_STT, VOIX_APPELANT, MARDI, envoyer, silence, ecouter
from standard.audiosocket import Decodeur
from standard.demarrage import construire_serveur

RACINE = RACINE_DU_DEPOT
base = "/tmp/latence.sqlite3"
if os.path.exists(base):
    os.remove(base)
serveur = construire_serveur({
    "STANDARD_TENANT": "salon-1",
    "STANDARD_PACK": os.path.join(RACINE, "packs", "coiffure.json"),
    "STANDARD_REPONSES": '{"A1": "Salon Elegance"}',
    "STANDARD_CRENEAUX": "09:00,10:30,14:00,15:30,17:00",
    "STANDARD_JOURS_FERMES": "6,0", "STANDARD_AUJOURDHUI": MARDI,
    "STANDARD_PORT": "0", "STANDARD_PORT_SANTE": "0", "STANDARD_BASE": base,
    "STANDARD_STT": "local", "STANDARD_STT_MODELE": MODELE_STT,
    "STANDARD_TTS": "piper", "STANDARD_VOIX": VOIX_APPELANT,
})
serveur.demarrer()
REPLIQUES = ["bonjour je voudrais un rendez-vous jeudi à quinze heures trente",
             "oui c'est parfait", "au nom de Dupont"]
for tour in range(3):
    prise = socket.create_connection(("127.0.0.1", serveur.port), timeout=5)
    decodeur = Decodeur()
    ecouter(prise, decodeur, 2.0)
    for replique in REPLIQUES:
        envoyer(prise, voix(replique))
        envoyer(prise, silence(900))
        ecouter(prise, decodeur, 3.0)
    prise.close()
    time.sleep(0.4)
serveur.arreter()

mesures = [m for appel in serveur.journal.lister("salon-1") for m in appel["mesures"]]
print(f"{len(mesures)} tours mesurés")
for cle in ("transcription_ms", "agent_ms", "premier_fragment_ms", "total_ms"):
    valeurs = sorted(m[cle] for m in mesures)
    if not valeurs:
        continue
    p50 = statistics.median(valeurs)
    p95 = valeurs[int(len(valeurs) * 0.95) - 1] if len(valeurs) > 1 else valeurs[0]
    print(f"  {cle:22s} p50 {p50:7.0f} ms   p95 {p95:7.0f} ms")
