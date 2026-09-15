#!/usr/bin/env python3
"""Tenue en charge du STT : combien de flux simultanes une machine soutient.

C'est le chiffre qui manque au chiffrage (docs/11 §6-2) : il decide du nombre de
salons par machine, donc de la marge. Le banc distant etant hors ligne, la mesure
est faite ici — la machine differe, mais la FORME du resultat (a partir de quel
nombre de flux le temps reel n'est plus tenu) se transpose.

Protocole : K flux simultanes, chacun decodant le corpus en boucle pendant une
duree fixe. On mesure le RTF agrege (temps de calcul / temps d'audio traite) et
la memoire residente. Le seuil est atteint quand le RTF par flux depasse 1,0 :
au-dela, le decodeur prend du retard sur la parole et l'agent repond trop tard.

Les flux partagent UN modele en memoire — c'est ce que fera le service, et c'est
aussi ce qui rend l'arithmetique du chiffrage valable.

Usage : cd bancs && PYTHONPATH=. ~/bancs-stt/bin/python charge_stt.py --max 8
"""

import argparse
import json
import os
import threading
import time

import wer_sherpa


def travailleur(reconnaisseur, fichiers, duree, resultats, index):
    audio = 0.0
    calcul = 0.0
    fin = time.perf_counter() + duree
    i = 0
    erreur = None
    try:
        while time.perf_counter() < fin:
            chemin = fichiers[i % len(fichiers)]
            i += 1
            _, ms, secondes = wer_sherpa.transcrire(chemin, reconnaisseur)
            calcul += ms / 1000
            audio += secondes
    except Exception as e:  # un fil qui meurt ne doit pas effacer la mesure
        erreur = f"{type(e).__name__}: {e}"
    resultats[index] = (calcul, audio, i, erreur)


def rss_mo():
    with open("/proc/self/status") as f:
        for ligne in f:
            if ligne.startswith("VmRSS:"):
                return int(ligne.split()[1]) / 1024
    return 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=os.path.expanduser("~/corpus-fr/8k"))
    ap.add_argument("--modele", default=os.path.expanduser(
        "~/modeles/sherpa-onnx-streaming-zipformer-fr-2023-04-14"))
    ap.add_argument("--duree", type=float, default=20.0, help="secondes par palier")
    ap.add_argument("--max", type=int, default=8)
    args = ap.parse_args()

    fichiers = sorted(os.path.join(args.corpus, f)
                      for f in os.listdir(args.corpus) if f.endswith(".wav"))
    # Un seul fil par reconnaisseur cote onnxruntime : le parallelisme mesure est
    # celui des APPELS, pas celui du decodeur. Sinon on mesure deux choses a la fois.
    reconnaisseur = wer_sherpa.construire(args.modele, fils=1)
    avant = rss_mo()

    lignes = []
    for k in range(1, args.max + 1):
        resultats = [None] * k
        fils = [threading.Thread(target=travailleur,
                                 args=(reconnaisseur, fichiers, args.duree, resultats, i))
                for i in range(k)]
        depart = time.perf_counter()
        for f in fils:
            f.start()
        for f in fils:
            f.join()
        mur = time.perf_counter() - depart

        calcul = sum(r[0] for r in resultats if r)
        audio = sum(r[1] for r in resultats if r)
        enonces = sum(r[2] for r in resultats if r)
        erreurs = [r[3] for r in resultats if r and r[3]]
        ligne = {
            "flux": k,
            "rtf_par_flux": round(calcul / audio, 4) if audio else None,
            "audio_traite_s": round(audio, 1),
            "debit_x_temps_reel": round(audio / mur, 2),
            "enonces": enonces,
            "rss_mo": round(rss_mo(), 1),
            "erreurs": erreurs[:3],
        }
        lignes.append(ligne)
        print(f"{k} flux : RTF/flux {ligne['rtf_par_flux']:.3f} · "
              f"debit {ligne['debit_x_temps_reel']:.1f}x temps reel · "
              f"RSS {ligne['rss_mo']:.0f} Mo", flush=True)
        if ligne["rtf_par_flux"] and ligne["rtf_par_flux"] > 1.0:
            print("  -> le temps reel n'est plus tenu, arret du banc")
            break

    json.dump({"machine": os.uname().nodename, "rss_avant_mo": round(avant, 1),
               "paliers": lignes},
              open(os.path.join(os.path.dirname(__file__), "charge-stt-resultats.json"), "w"),
              indent=2, ensure_ascii=False)
    print("\nEcrit : bancs/charge-stt-resultats.json")


if __name__ == "__main__":
    main()
