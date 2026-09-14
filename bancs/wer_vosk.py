#!/usr/bin/env python3
"""Meme corpus, meme metrique, mais moteur local sans compilateur.

But : verifier que l'ecart 16 kHz / 8 kHz mesure sur un gros modele distant
(mesure 7) se retrouve — ou pas — sur un petit modele local. Un petit modele
n'a pas les memes reserves acoustiques : c'est la ou la bande telephonique
devrait mordre.

Vosk s'installe par pip, sans compilateur, et tourne sur processeur.
Le modele attend du 16 kHz en entree : on lui donne donc le fichier 8 kHz
reechantillonne a 16 kHz, ce qui est exactement ce qu'un pipeline ferait —
la bande passante perdue ne revient pas.

Usage : bancs-stt/bin/python bancs/wer_vosk.py --corpus ~/corpus-fr \
            --modele ~/modeles/vosk-model-small-fr-0.22
"""

import argparse
import json
import os
import subprocess
import time
import wave

from wer import distance_mots, normaliser, chiffres  # meme metrique, meme normalisation


def transcrire(chemin, modele, cible=16000):
    from vosk import KaldiRecognizer, Model
    with wave.open(chemin, "rb") as w:
        taux = w.getframerate()
    if taux != cible:
        temporaire = chemin + f".{cible}.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", chemin,
                        "-ar", str(cible), "-ac", "1", temporaire], check=True)
        chemin_lu = temporaire
    else:
        chemin_lu, temporaire = chemin, None

    depart = time.perf_counter()
    with wave.open(chemin_lu, "rb") as w:
        rec = KaldiRecognizer(modele, w.getframerate())
        morceaux = []
        while True:
            donnees = w.readframes(4000)
            if not donnees:
                break
            if rec.AcceptWaveform(donnees):
                morceaux.append(json.loads(rec.Result()).get("text", ""))
        morceaux.append(json.loads(rec.FinalResult()).get("text", ""))
        duree = w.getnframes() / w.getframerate()
    ms = (time.perf_counter() - depart) * 1000
    if temporaire:
        os.remove(temporaire)
    return " ".join(m for m in morceaux if m), ms, duree


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=os.path.expanduser("~/corpus-fr"))
    ap.add_argument("--modele", default=os.path.expanduser("~/modeles/vosk-model-small-fr-0.22"))
    args = ap.parse_args()

    from vosk import Model, SetLogLevel
    SetLogLevel(-1)
    modele = Model(args.modele)

    manifeste = json.load(open(os.path.join(args.corpus, "manifeste.json")))
    cumul = {"16k": [0, 0], "8k": [0, 0]}
    temps = {"16k": [0.0, 0.0], "8k": [0.0, 0.0]}
    tel = {"16k": [], "8k": []}
    detail = []

    for entree in manifeste:
        ligne = {"id": entree["id"], "famille": entree["famille"], "texte": entree["texte"]}
        for bande in ("16k", "8k"):
            chemin = os.path.join(args.corpus, bande, entree["id"] + ".wav")
            if not os.path.exists(chemin):
                continue
            hypothese, ms, duree = transcrire(chemin, modele)
            erreurs, mots = distance_mots(normaliser(entree["texte"]), normaliser(hypothese))
            cumul[bande][0] += erreurs
            cumul[bande][1] += mots
            temps[bande][0] += ms / 1000
            temps[bande][1] += duree
            ligne[bande] = {"hypothese": hypothese, "erreurs": erreurs, "mots": mots}
            attendu = entree["entites"].get("tel")
            if attendu:
                obtenu = chiffres(hypothese)
                ok = attendu in obtenu
                tel[bande].append(ok)
                ligne[bande]["tel_ok"] = ok
                ligne[bande]["tel_lu"] = obtenu
        detail.append(ligne)
        print(f"{entree['id']:16s} 16k={ligne.get('16k',{}).get('erreurs','?')} "
              f"8k={ligne.get('8k',{}).get('erreurs','?')}")

    resume = {}
    for bande in ("16k", "8k"):
        e, m = cumul[bande]
        if m:
            resume[bande] = {"wer_pct": round(100 * e / m, 2), "erreurs": e, "mots": m,
                             "rtf": round(temps[bande][0] / temps[bande][1], 4)}
            if tel[bande]:
                resume[bande]["tel_exact_pct"] = round(100 * sum(tel[bande]) / len(tel[bande]), 1)
                resume[bande]["tel_n"] = len(tel[bande])
    json.dump({"moteur": "vosk-model-small-fr-0.22", "resume": resume, "detail": detail},
              open(os.path.join(os.path.dirname(__file__), "wer-vosk-resultats.json"), "w"),
              indent=2, ensure_ascii=False)
    print("\n" + json.dumps(resume, indent=2, ensure_ascii=False))
    if "16k" in resume and "8k" in resume:
        print(f"\nEcart bande telephonique : x{resume['8k']['wer_pct']/max(resume['16k']['wer_pct'],0.01):.2f}")


if __name__ == "__main__":
    main()
