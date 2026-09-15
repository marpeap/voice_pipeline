#!/usr/bin/env python3
"""Courbe de degradation au bruit — la mesure que la litterature ne donne pas.

Les WER publies sont mesures sur de l'audio propre. Un salon ne l'est jamais :
seche-cheveux, musique, conversations, rue. docs/07 demande de tracer NOTRE
courbe ; ce banc la trace, sur la bande qui nous concerne (8 kHz), avec les deux
moteurs locaux, a quatre rapports signal/bruit.

Le bruit est synthetique et de deux natures, parce qu'elles ne detruisent pas la
meme chose :
  - bruit rose large bande, qui imite un seche-cheveux ou une hotte ;
  - babil (babble), fabrique en superposant des enonces du corpus lui-meme,
    qui imite une salle pleine — c'est le bruit qui trompe le plus un STT,
    puisqu'il a la structure de la parole.

Usage : cd bancs && PYTHONPATH=. ~/bancs-stt/bin/python bruit.py
"""

import argparse
import json
import os
import random
import wave

import numpy as np

from wer import distance_mots, normaliser


def lire(chemin):
    with wave.open(chemin, "rb") as w:
        taux = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
    return x, taux


def ecrire(chemin, x, taux):
    x = np.clip(x, -32768, 32767).astype(np.int16)
    with wave.open(chemin, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(taux)
        w.writeframes(x.tobytes())


def bruit_rose(n, rng):
    """Bruit rose par filtrage d'un bruit blanc (Voss-McCartney simplifie)."""
    blanc = rng.standard_normal(n)
    spectre = np.fft.rfft(blanc)
    frequences = np.arange(len(spectre))
    frequences[0] = 1
    spectre = spectre / np.sqrt(frequences)
    rose = np.fft.irfft(spectre, n)
    return rose / (np.std(rose) or 1)


def babil(n, banque, rng):
    """Six voix superposees et decalees : le bruit qui ressemble a de la parole."""
    melange = np.zeros(n, dtype=np.float32)
    for _ in range(6):
        source = banque[rng.integers(len(banque))]
        if len(source) < n:
            source = np.tile(source, int(np.ceil(n / len(source))))
        debut = rng.integers(0, max(1, len(source) - n))
        melange += source[debut:debut + n]
    return melange / (np.std(melange) or 1)


def melanger(signal, bruit, rsb_db):
    """Ajoute le bruit au niveau exact demande, en rapport signal/bruit."""
    p_signal = np.mean(signal.astype(np.float64) ** 2)
    p_bruit = np.mean(bruit.astype(np.float64) ** 2) or 1.0
    facteur = np.sqrt(p_signal / (p_bruit * (10 ** (rsb_db / 10))))
    return signal + facteur * bruit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=os.path.expanduser("~/corpus-fr"))
    ap.add_argument("--bande", default="8k")
    ap.add_argument("--rsb", default="20,15,10,5")
    ap.add_argument("--travail", default=os.path.expanduser("~/corpus-bruit"))
    args = ap.parse_args()

    rng = np.random.default_rng(20260915)
    manifeste = json.load(open(os.path.join(args.corpus, "manifeste.json")))
    niveaux = [int(v) for v in args.rsb.split(",")]

    # Banque de voix pour le babil : le corpus lui-meme, ce qui garantit le bon
    # spectre et la bonne prosodie sans telecharger quoi que ce soit.
    banque = []
    for entree in manifeste[:20]:
        chemin = os.path.join(args.corpus, args.bande, entree["id"] + ".wav")
        if os.path.exists(chemin):
            x, _ = lire(chemin)
            banque.append(x)

    os.makedirs(args.travail, exist_ok=True)
    fabriques = {}
    for nature in ("rose", "babil"):
        for rsb in niveaux:
            dossier = os.path.join(args.travail, f"{nature}-{rsb}db")
            os.makedirs(dossier, exist_ok=True)
            fabriques[(nature, rsb)] = dossier
            for entree in manifeste:
                src = os.path.join(args.corpus, args.bande, entree["id"] + ".wav")
                dst = os.path.join(dossier, entree["id"] + ".wav")
                if not os.path.exists(src) or os.path.exists(dst):
                    continue
                x, taux = lire(src)
                b = bruit_rose(len(x), rng) if nature == "rose" else babil(len(x), banque, rng)
                ecrire(dst, melanger(x, b * np.std(x), rsb), taux)
    print(f"Corpus bruites fabriques : {len(fabriques)} conditions x {len(manifeste)} enonces")

    # --- evaluation ---
    from vosk import Model, SetLogLevel
    SetLogLevel(-1)
    import wer_vosk
    import wer_sherpa

    modele_vosk = Model(os.path.expanduser("~/modeles/vosk-model-small-fr-0.22"))
    sherpa = wer_sherpa.construire(os.path.expanduser(
        "~/modeles/sherpa-onnx-streaming-zipformer-fr-2023-04-14"))

    resultats = []
    conditions = [("propre", None)] + [(n, r) for n in ("rose", "babil") for r in niveaux]
    for nature, rsb in conditions:
        dossier = (os.path.join(args.corpus, args.bande) if rsb is None
                   else fabriques[(nature, rsb)])
        for nom_moteur in ("vosk", "sherpa"):
            e = m = 0
            for entree in manifeste:
                chemin = os.path.join(dossier, entree["id"] + ".wav")
                if not os.path.exists(chemin):
                    continue
                if nom_moteur == "vosk":
                    hyp, _, _ = wer_vosk.transcrire(chemin, modele_vosk)
                else:
                    hyp, _, _ = wer_sherpa.transcrire(chemin, sherpa)
                de, dm = distance_mots(normaliser(entree["texte"]), normaliser(hyp))
                e += de
                m += dm
            ligne = {"bruit": nature, "rsb_db": rsb, "moteur": nom_moteur,
                     "wer_pct": round(100 * e / m, 2), "mots": m}
            resultats.append(ligne)
            print(f"{nature:7s} {str(rsb):>5s} dB  {nom_moteur:7s} WER {ligne['wer_pct']:6.2f} %")

    json.dump(resultats, open(os.path.join(os.path.dirname(__file__),
              "bruit-resultats.json"), "w"), indent=2, ensure_ascii=False)
    print("\nEcrit : bancs/bruit-resultats.json")


if __name__ == "__main__":
    main()
