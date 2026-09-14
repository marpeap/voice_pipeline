"""Banc L0 mesure 5 — un tatouage audio survit-il au canal telephonique ?

Aucune publication de 2023 a 2026 ne teste un tatouage neuronal sous codec
telephonique (le point le plus proche est Opus 16 kbit/s en 16 kHz). Cette
mesure est donc la piece qui transforme notre dossier d'exemption AI Act
(lignes directrices C(2026) 5054, point 88 : « marquage techniquement
infaisable ») d'une opinion en une preuve.

Protocole : Piper genere la parole -> AudioSeal tatoue -> degradation reelle
du canal (8 kHz + G.711 mu-law, puis retour) -> detection. On mesure le taux
de detection avant et apres, plus un temoin non tatoue pour verifier que le
detecteur ne voit pas de tatouage la ou il n'y en a pas.

Prerequis sur le banc (budget zero, licences MIT) :
    ~/miniforge3/bin/python -m pip install --target ~/bancs/l0-tatouage/lib audioseal
Lancement :
    cd ~/bancs && PYTHONPATH=$HOME/bancs/l0-piper/lib:$HOME/bancs/l0-tatouage/lib \
        ~/miniforge3/bin/python bench_tatouage.py
"""
import json, os, statistics, subprocess, time, wave
import numpy as np
import torch
from audioseal import AudioSeal
from piper import PiperVoice

RACINE = os.path.expanduser("~/bancs")
SORTIE = f"{RACINE}/l0-tatouage/audio"
os.makedirs(SORTIE, exist_ok=True)
TAUX_AUDIOSEAL = 16000          # AudioSeal travaille en 16 kHz

PHRASES = [
    "Bonjour, salon Nguyen, je suis l'assistant automatique du salon.",
    "J'ai un créneau jeudi dix-sept septembre à dix heures trente.",
    "Je vous relis votre numéro : zéro six, douze, trente-quatre, cinquante-six.",
    "Très bien, c'est noté. Vous recevrez un SMS de confirmation.",
    "Pour un balayage avec coupe, il faut compter environ deux heures.",
    "Je vous passe quelqu'un tout de suite.",
]

def ff(entree, sortie, args):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", entree] + args + [sortie], check=True)

def ecrire(chemin, pcm_flottant, taux):
    pcm = np.clip(pcm_flottant, -1.0, 1.0)
    with wave.open(chemin, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(taux)
        w.writeframes((pcm * 32767).astype("<i2").tobytes())

def lire(chemin):
    with wave.open(chemin) as w:
        brut = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
        return brut.astype(np.float32) / 32768.0, w.getframerate()

def degrader_canal(entree, sortie_base):
    """Degradation reelle du canal : 8 kHz + G.711 mu-law, puis retour en 16 kHz."""
    mu = f"{sortie_base}_8k_mulaw.wav"
    ff(entree, mu, ["-ar", "8000", "-ac", "1", "-c:a", "pcm_mulaw"])
    retour = f"{sortie_base}_retour16k.wav"
    ff(mu, retour, ["-ar", str(TAUX_AUDIOSEAL), "-ac", "1"])
    return retour

voix = PiperVoice.load(os.path.expanduser("~/bancs/l0-piper/voix/fr_FR-siwis-medium.onnx"))
tatoueur = AudioSeal.load_generator("audioseal_wm_16bits")
detecteur = AudioSeal.load_detector("audioseal_detector_16bits")

def detecter(signal):
    tenseur = torch.from_numpy(signal).unsqueeze(0).unsqueeze(0)
    t0 = time.perf_counter()
    with torch.no_grad():
        resultat, message = detecteur.detect_watermark(tenseur, sample_rate=TAUX_AUDIOSEAL), None
    return float(resultat), time.perf_counter() - t0

resultats = []
for i, texte in enumerate(PHRASES):
    base = f"{SORTIE}/{i:02d}"
    # 1. Piper -> 16 kHz
    morceaux = list(voix.synthesize(texte))
    pcm = np.frombuffer(b"".join(m.audio_int16_bytes for m in morceaux), dtype="<i2").astype(np.float32) / 32768.0
    brut = f"{base}_brut.wav"; ecrire(brut, pcm, morceaux[0].sample_rate)
    propre = f"{base}_16k.wav"; ff(brut, propre, ["-ar", str(TAUX_AUDIOSEAL), "-ac", "1"])
    signal, _ = lire(propre)

    # 2. Tatouage
    tenseur = torch.from_numpy(signal).unsqueeze(0).unsqueeze(0)
    t0 = time.perf_counter()
    with torch.no_grad():
        tatoue = tatoueur.get_watermark(tenseur, TAUX_AUDIOSEAL)
        signal_tatoue = (tenseur + tatoue).squeeze().numpy()
    cout_tatouage = time.perf_counter() - t0
    f_tatoue = f"{base}_tatoue.wav"; ecrire(f_tatoue, signal_tatoue, TAUX_AUDIOSEAL)

    # 3. Trois conditions
    score_propre, dt1 = detecter(signal_tatoue)
    signal_canal, _ = lire(degrader_canal(f_tatoue, f"{base}_tatoue"))
    score_canal, dt2 = detecter(signal_canal)
    signal_temoin, _ = lire(degrader_canal(propre, f"{base}_temoin"))
    score_temoin, dt3 = detecter(signal_temoin)

    resultats.append({"phrase": texte[:45], "duree_s": round(len(signal) / TAUX_AUDIOSEAL, 2),
                      "tatoue_16k": round(score_propre, 4), "tatoue_apres_canal": round(score_canal, 4),
                      "temoin_apres_canal": round(score_temoin, 4),
                      "cout_tatouage_s": round(cout_tatouage, 4), "cout_detection_s": round(dt2, 4)})
    print(f"{i:02d} 16 kHz {score_propre:.3f} | apres canal {score_canal:.3f} | temoin {score_temoin:.3f}", flush=True)

json.dump(resultats, open(f"{RACINE}/resultats_tatouage.json", "w"), ensure_ascii=False, indent=1)
med = lambda c: statistics.median(r[c] for r in resultats)
print(f"""
--- Synthese ---
Detection sur audio tatoue 16 kHz      : {med('tatoue_16k'):.3f}
Detection apres 8 kHz + G.711 mu-law   : {med('tatoue_apres_canal'):.3f}   <-- LE CHIFFRE
Faux positifs (temoin non tatoue)      : {med('temoin_apres_canal'):.3f}
Cout du tatouage (median)              : {med('cout_tatouage_s')*1000:.0f} ms
Cout de la detection (median)          : {med('cout_detection_s')*1000:.0f} ms

Lecture : si la detection apres canal s'effondre vers le niveau du temoin,
le marquage est techniquement infaisable sur notre canal — et c'est
exactement la premiere des deux conditions du point (88) des lignes
directrices. Le resultat negatif est donc aussi utile que le positif.
""")
