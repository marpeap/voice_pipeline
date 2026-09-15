#!/usr/bin/env python3
"""Tenue en charge du TTS, et verite sur le premier fragment audio.

Deux questions, une seule mesure.

1. Combien de synthese simultanees une machine soutient — pendant que le STT,
   lui, ne limite rien (mesure 11). Le TTS est le suspect suivant.
2. Quand arrive le PREMIER fragment audio. La mesure 1 donnait 372 ms de TTFB
   en passant par le binaire, qui synthetise la phrase entiere avant d'ecrire.
   L'API Python rend un flux de fragments : on mesure donc le delai avant le
   premier, qui est le seul que l'appelant entend.

Les flux partagent une voix chargee en memoire, comme le fera le service.

Usage : cd bancs && PYTHONPATH=. ~/bancs-stt/bin/python charge_tts.py --max 8
"""

import argparse
import json
import os
import statistics
import threading
import time

from piper import PiperVoice

PHRASES = [
    "Bonjour, vous etes bien au salon. Je suis un assistant automatique.",
    "Jeudi quinze heures trente, c'est note.",
    "Je vous confirme : coupe et brushing, mardi dix heures.",
    "Pouvez-vous me redonner votre numero, par groupes de deux ?",
    "Un instant, je verifie les disponibilites.",
    "D'accord.",
]


def mesurer_premier_fragment(voix, phrase):
    """Retourne (ms avant le premier fragment, ms total, secondes d'audio)."""
    depart = time.perf_counter()
    premier = None
    echantillons = 0
    taux = 22050
    for fragment in voix.synthesize(phrase):
        if premier is None:
            premier = (time.perf_counter() - depart) * 1000
        # L'objet de fragment expose l'audio brut et son taux d'echantillonnage.
        brut = getattr(fragment, "audio_int16_bytes", None)
        if brut is None:
            brut = getattr(fragment, "audio_int16_array", b"").tobytes()
        taux = getattr(fragment, "sample_rate", taux)
        echantillons += len(brut) // 2
    total = (time.perf_counter() - depart) * 1000
    return premier, total, echantillons / taux


def travailleur(voix, duree, resultats, index):
    premiers, calcul, audio, n = [], 0.0, 0.0, 0
    erreur = None
    fin = time.perf_counter() + duree
    try:
        while time.perf_counter() < fin:
            phrase = PHRASES[n % len(PHRASES)]
            p, t, secondes = mesurer_premier_fragment(voix, phrase)
            premiers.append(p)
            calcul += t / 1000
            audio += secondes
            n += 1
    except Exception as e:
        erreur = f"{type(e).__name__}: {e}"
    resultats[index] = (premiers, calcul, audio, n, erreur)


def rss_mo():
    with open("/proc/self/status") as f:
        for ligne in f:
            if ligne.startswith("VmRSS:"):
                return int(ligne.split()[1]) / 1024
    return 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voix", default=os.path.expanduser("~/piper/fr_FR-siwis-medium.onnx"))
    ap.add_argument("--duree", type=float, default=15.0)
    ap.add_argument("--max", type=int, default=8)
    args = ap.parse_args()

    voix = PiperVoice.load(args.voix)
    lignes = []
    for k in range(1, args.max + 1):
        resultats = [None] * k
        fils = [threading.Thread(target=travailleur, args=(voix, args.duree, resultats, i))
                for i in range(k)]
        depart = time.perf_counter()
        for f in fils:
            f.start()
        for f in fils:
            f.join()
        mur = time.perf_counter() - depart

        premiers = [p for r in resultats if r for p in r[0] if p is not None]
        calcul = sum(r[1] for r in resultats if r)
        audio = sum(r[2] for r in resultats if r)
        erreurs = [r[4] for r in resultats if r and r[4]]
        ligne = {
            "flux": k,
            "premier_fragment_p50_ms": round(statistics.median(premiers)) if premiers else None,
            "premier_fragment_p90_ms": round(sorted(premiers)[int(0.9 * (len(premiers) - 1))]) if premiers else None,
            "rtf_par_flux": round(calcul / audio, 4) if audio else None,
            "debit_x_temps_reel": round(audio / mur, 2),
            "phrases": sum(r[3] for r in resultats if r),
            "rss_mo": round(rss_mo(), 1),
            "erreurs": erreurs[:2],
        }
        lignes.append(ligne)
        print(f"{k} flux : premier fragment p50 {ligne['premier_fragment_p50_ms']} ms · "
              f"RTF/flux {ligne['rtf_par_flux']} · debit {ligne['debit_x_temps_reel']}x · "
              f"RSS {ligne['rss_mo']:.0f} Mo", flush=True)
        if ligne["rtf_par_flux"] and ligne["rtf_par_flux"] > 1.0:
            print("  -> temps reel perdu, arret")
            break

    json.dump(lignes, open(os.path.join(os.path.dirname(__file__), "charge-tts-resultats.json"), "w"),
              indent=2, ensure_ascii=False)
    print("\nEcrit : bancs/charge-tts-resultats.json")


if __name__ == "__main__":
    main()
