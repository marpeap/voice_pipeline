#!/usr/bin/env python3
"""Quelle voix francaise embarquer par defaut ?

Deux voix sont licenciees pour un usage commercial (CC-BY 4.0) : `siwis` et
`mls`. Tout le dossier a ete mesure avec `siwis` sans jamais comparer. Or le
choix n'est pas cosmetique : il decide du delai avant le premier son (mesure 13)
et de ce que l'appelant comprend au travers du canal (mesure 19).

Trois criteres, tous mesurables ici :
  1. delai avant le premier fragment, voix chargee et flux ouvert ;
  2. debit de synthese (RTF) ;
  3. intelligibilite apres passage en 8 kHz mu-law, jugee par deux moteurs
     independants sur les phrases reelles de l'agent.

Usage : GROQ_API_KEY=... cd bancs && PYTHONPATH=. ~/bancs-stt/bin/python voix.py
"""

import json
import os
import statistics
import subprocess
import time
import wave

from piper import PiperVoice

import agent_audible
from wer import chiffres, distance_mots, normaliser, transcrire as transcrire_distant

VOIX = {
    "siwis": os.path.expanduser("~/piper/fr_FR-siwis-medium.onnx"),
    "mls": os.path.expanduser("~/piper/fr_FR-mls-medium.onnx"),
}
SORTIE = os.path.expanduser("~/corpus-voix")


def premier_fragment(voix, phrase):
    depart = time.perf_counter()
    echantillons, taux = 0, 22050
    premier = None
    for fragment in voix.synthesize(phrase):
        if premier is None:
            premier = (time.perf_counter() - depart) * 1000
        brut = getattr(fragment, "audio_int16_bytes", b"")
        taux = getattr(fragment, "sample_rate", taux)
        echantillons += len(brut) // 2
    return premier, (time.perf_counter() - depart) * 1000, echantillons / taux


def fabriquer(voix, nom, cle, texte):
    os.makedirs(SORTIE, exist_ok=True)
    final = os.path.join(SORTIE, f"{nom}-{cle}.8k.wav")
    if os.path.exists(final):
        return final
    brut = os.path.join(SORTIE, f"{nom}-{cle}.wav")
    with wave.open(brut, "wb") as f:
        voix.synthesize_wav(texte, f)
    mulaw = final + ".ulaw.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", brut, "-ar", "8000",
                    "-ac", "1", "-c:a", "pcm_mulaw", "-f", "wav", mulaw], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mulaw, "-ar", "8000",
                    "-ac", "1", "-c:a", "pcm_s16le", final], check=True)
    os.remove(mulaw)
    return final


def main():
    cle_api = os.environ["GROQ_API_KEY"]
    from vosk import Model, SetLogLevel
    SetLogLevel(-1)
    import wer_vosk
    modele_vosk = Model(os.path.expanduser("~/modeles/vosk-model-small-fr-0.22"))

    resume = {}
    detail = []
    for nom, chemin in VOIX.items():
        if not os.path.exists(chemin):
            print(f"-- {nom} absente, sautee")
            continue
        voix = PiperVoice.load(chemin)

        # 1 et 2 — latence et debit, sur les phrases d'agent, trois passages
        premiers, calculs, audios = [], 0.0, 0.0
        for _ in range(3):
            for _, texte, _a in agent_audible.PHRASES:
                p, total, duree = premier_fragment(voix, texte)
                premiers.append(p)
                calculs += total / 1000
                audios += duree

        # 3 — intelligibilite apres le canal
        erreurs_d = mots_d = erreurs_l = mots_l = 0
        manquants = []
        for cle, texte, attendus in agent_audible.PHRASES:
            fichier = fabriquer(voix, nom, cle, texte)
            d, _ = transcrire_distant(fichier, cle_api, "whisper-large-v3-turbo")
            l, _, _ = wer_vosk.transcrire(fichier, modele_vosk)
            e, m = distance_mots(normaliser(texte), normaliser(d))
            erreurs_d += e
            mots_d += m
            e2, m2 = distance_mots(normaliser(texte), normaliser(l))
            erreurs_l += e2
            mots_l += m2
            perdus = []
            for a in attendus:
                absent = (a not in chiffres(l)) if a.isdigit() else (normaliser(a) not in normaliser(l))
                if absent:
                    perdus.append(a)
            if perdus:
                manquants.append({"phrase": cle, "perdus": perdus})
            detail.append({"voix": nom, "phrase": cle, "distant": d.strip(), "local": l.strip()})

        resume[nom] = {
            "premier_fragment_p50_ms": round(statistics.median(premiers)),
            "premier_fragment_p90_ms": round(sorted(premiers)[int(0.9 * (len(premiers) - 1))]),
            "rtf": round(calculs / audios, 4),
            "wer_apres_canal_distant_pct": round(100 * erreurs_d / mots_d, 1),
            "wer_apres_canal_local_pct": round(100 * erreurs_l / mots_l, 1),
            "mots_cles_perdus": manquants,
        }
        r = resume[nom]
        print(f"{nom:6s} premier fragment p50 {r['premier_fragment_p50_ms']:4d} ms · "
              f"RTF {r['rtf']:.3f} · WER apres canal : distant {r['wer_apres_canal_distant_pct']} % "
              f"local {r['wer_apres_canal_local_pct']} % · mots-cles perdus : {len(manquants)}",
              flush=True)

    json.dump({"resume": resume, "detail": detail},
              open(os.path.join(os.path.dirname(__file__), "voix-resultats.json"), "w"),
              indent=2, ensure_ascii=False)
    print("\nEcrit : bancs/voix-resultats.json")


if __name__ == "__main__":
    main()
