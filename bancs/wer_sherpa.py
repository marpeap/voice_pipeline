#!/usr/bin/env python3
"""Troisieme moteur sur le meme corpus : sherpa-onnx zipformer streaming francais.

But precis : verifier si le compromis vu a la mesure 8 — un moteur qui rend des
chiffres contre un moteur qui rend des mots — est une propriete de ces deux
moteurs-la ou une regle generale. Un troisieme point le dira.

Modele streaming : c'est aussi celui qui ressemble le plus a ce que le produit
fera reellement, puisqu'un agent telephonique transcrit au fil de la parole.

Usage : cd bancs && PYTHONPATH=. ~/bancs-stt/bin/python wer_sherpa.py
"""

import argparse
import json
import os
import subprocess
import threading
import time
import wave

from wer import distance_mots, normaliser, chiffres


def construire(dossier, fils=2):
    import sherpa_onnx
    return sherpa_onnx.OnlineRecognizer.from_transducer(
        tokens=os.path.join(dossier, "tokens.txt"),
        encoder=os.path.join(dossier, "encoder-epoch-29-avg-9-with-averaged-model.int8.onnx"),
        decoder=os.path.join(dossier, "decoder-epoch-29-avg-9-with-averaged-model.int8.onnx"),
        joiner=os.path.join(dossier, "joiner-epoch-29-avg-9-with-averaged-model.int8.onnx"),
        num_threads=fils,
        sample_rate=16000,
        feature_dim=80,
        enable_endpoint_detection=False,
        decoding_method="greedy_search",
    )


def transcrire(chemin, reconnaisseur):
    import numpy as np
    with wave.open(chemin, "rb") as w:
        taux = w.getframerate()
    lu = chemin
    temporaire = None
    if taux != 16000:
        # Nom unique : plusieurs flux simultanes convertissent le meme fichier.
        temporaire = f"{chemin}.{os.getpid()}.{threading.get_ident()}.16k.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", chemin,
                        "-ar", "16000", "-ac", "1", temporaire], check=True)
        lu = temporaire
    with wave.open(lu, "rb") as w:
        brut = w.readframes(w.getnframes())
        duree = w.getnframes() / w.getframerate()
    echantillons = np.frombuffer(brut, dtype=np.int16).astype(np.float32) / 32768.0

    depart = time.perf_counter()
    flux = reconnaisseur.create_stream()
    flux.accept_waveform(16000, echantillons)
    # Queue de silence : sans elle, la fin de l'enonce n'est jamais decodee.
    flux.accept_waveform(16000, np.zeros(int(0.5 * 16000), dtype=np.float32))
    flux.input_finished()
    while reconnaisseur.is_ready(flux):
        reconnaisseur.decode_stream(flux)
    texte = reconnaisseur.get_result(flux)
    ms = (time.perf_counter() - depart) * 1000
    if temporaire:
        os.remove(temporaire)
    return texte, ms, duree


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=os.path.expanduser("~/corpus-fr"))
    ap.add_argument("--modele", default=os.path.expanduser(
        "~/modeles/sherpa-onnx-streaming-zipformer-fr-2023-04-14"))
    args = ap.parse_args()

    reconnaisseur = construire(args.modele)
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
            hypothese, ms, duree = transcrire(chemin, reconnaisseur)
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
                ligne[bande].update({"tel_ok": ok, "tel_lu": obtenu})
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
    json.dump({"moteur": "sherpa-onnx-streaming-zipformer-fr-2023-04-14 int8",
               "resume": resume, "detail": detail},
              open(os.path.join(os.path.dirname(__file__), "wer-sherpa-resultats.json"), "w"),
              indent=2, ensure_ascii=False)
    print("\n" + json.dumps(resume, indent=2, ensure_ascii=False))
    if "16k" in resume and "8k" in resume:
        print(f"\nEcart bande telephonique : x{resume['8k']['wer_pct']/max(resume['16k']['wer_pct'],0.01):.2f}")


if __name__ == "__main__":
    main()
