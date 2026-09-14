#!/usr/bin/env python3
"""WER francais 16 kHz contre 8 kHz, sur un moteur STT accessible par API.

Pourquoi ce banc existe : aucune source publique ne donne le WER francais en
bande telephonique. Les chiffres publies le sont tous en 16 kHz propre. On
mesure donc le MEME corpus dans les deux bandes, et c'est l'ECART qui nous
interesse — il est transposable a d'autres moteurs, la ou le taux absolu ne
l'est pas.

Deux metriques, jamais confondues (docs/07-CORPUS-DE-TEST.md §4) :
  - le WER, qui compte tous les mots a egalite ;
  - le taux d'erreur par entite, ou un seul chiffre faux fait perdre le client.

Usage : GROQ_API_KEY=... python3 bancs/wer.py --corpus ~/corpus-fr
"""

import argparse
import json
import mimetypes
import os
import re
import time
import unicodedata
import urllib.request
import uuid

MOTS_NOMBRES = {
    "zero": "0", "un": "1", "une": "1", "deux": "2", "trois": "3", "quatre": "4",
    "cinq": "5", "six": "6", "sept": "7", "huit": "8", "neuf": "9", "dix": "10",
    "onze": "11", "douze": "12", "treize": "13", "quatorze": "14", "quinze": "15",
    "seize": "16", "vingt": "20", "vingts": "20", "trente": "30", "quarante": "40",
    "cinquante": "50", "soixante": "60", "cent": "100", "cents": "100",
}


def normaliser(texte):
    texte = unicodedata.normalize("NFD", texte.lower())
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    texte = texte.replace("'", " ").replace("-", " ")
    texte = re.sub(r"[^a-z0-9 ]", " ", texte)
    return re.sub(r"\s+", " ", texte).strip()


def chiffres(texte):
    """Suite de chiffres reconstruite depuis un texte mixte mots/chiffres.

    Volontairement grossier : il ne s'agit pas d'implementer la grammaire
    francaise (docs/10) mais de comparer deux transcriptions du meme enonce.
    """
    sortie = []
    for mot in normaliser(texte).split():
        if mot.isdigit():
            sortie.append(mot)
        elif mot in MOTS_NOMBRES:
            sortie.append(MOTS_NOMBRES[mot])
    return "".join(sortie)


def distance_mots(reference, hypothese):
    r, h = reference.split(), hypothese.split()
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        precedent, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            courant = d[j]
            d[j] = min(d[j] + 1, d[j - 1] + 1, precedent + (r[i - 1] != h[j - 1]))
            precedent = courant
    return d[len(h)], len(r)


def transcrire(chemin, cle, modele, base="https://api.groq.com/openai/v1"):
    limite = uuid.uuid4().hex
    nom = os.path.basename(chemin)
    corps = bytearray()

    def champ(nom_champ, valeur):
        corps.extend(f"--{limite}\r\nContent-Disposition: form-data; "
                     f'name="{nom_champ}"\r\n\r\n{valeur}\r\n'.encode())

    with open(chemin, "rb") as f:
        donnees = f.read()
    corps.extend(f"--{limite}\r\nContent-Disposition: form-data; name=\"file\"; "
                 f'filename="{nom}"\r\nContent-Type: '
                 f'{mimetypes.guess_type(nom)[0] or "audio/wav"}\r\n\r\n'.encode())
    corps.extend(donnees)
    corps.extend(b"\r\n")
    champ("model", modele)
    champ("language", "fr")
    champ("response_format", "json")
    corps.extend(f"--{limite}--\r\n".encode())

    requete = urllib.request.Request(
        f"{base}/audio/transcriptions", data=bytes(corps),
        headers={"Authorization": f"Bearer {cle}",
                 "Content-Type": f"multipart/form-data; boundary={limite}",
                 "User-Agent": "marpeap-banc-wer/1.0"})
    depart = time.perf_counter()
    with urllib.request.urlopen(requete, timeout=120) as rep:
        texte = json.load(rep).get("text", "")
    return texte, (time.perf_counter() - depart) * 1000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=os.path.expanduser("~/corpus-fr"))
    ap.add_argument("--modele", default="whisper-large-v3-turbo")
    ap.add_argument("--pause", type=float, default=1.0, help="secondes entre appels")
    args = ap.parse_args()

    cle = os.environ.get("GROQ_API_KEY")
    if not cle:
        raise SystemExit("GROQ_API_KEY absente")

    manifeste = json.load(open(os.path.join(args.corpus, "manifeste.json")))
    resultats = {"16k": [], "8k": []}
    detail = []

    for entree in manifeste:
        ligne = {"id": entree["id"], "famille": entree["famille"], "texte": entree["texte"]}
        for bande in ("16k", "8k"):
            chemin = os.path.join(args.corpus, bande, entree["id"] + ".wav")
            if not os.path.exists(chemin):
                continue
            try:
                hypothese, ms = transcrire(chemin, cle, args.modele)
            except Exception as e:
                ligne[bande] = {"erreur": f"{type(e).__name__}: {e}"}
                time.sleep(args.pause)
                continue
            erreurs, mots = distance_mots(normaliser(entree["texte"]), normaliser(hypothese))
            resultats[bande].append((erreurs, mots))
            ligne[bande] = {"hypothese": hypothese.strip(), "erreurs": erreurs,
                            "mots": mots, "latence_ms": round(ms)}
            attendu = entree["entites"].get("tel")
            if attendu:
                ligne[bande]["tel_ok"] = chiffres(hypothese).endswith(attendu[1:]) \
                    or attendu in chiffres(hypothese)
            time.sleep(args.pause)
        detail.append(ligne)
        marque = {b: ligne.get(b, {}).get("erreurs", "?") for b in ("16k", "8k")}
        print(f"{entree['id']:16s} erreurs 16k={marque['16k']} 8k={marque['8k']}")

    sortie = os.path.join(os.path.dirname(__file__), "wer-resultats.json")
    resume = {}
    for bande, paires in resultats.items():
        if paires:
            e = sum(p[0] for p in paires)
            m = sum(p[1] for p in paires)
            resume[bande] = {"wer_pct": round(100 * e / m, 2), "mots": m, "erreurs": e,
                             "enonces": len(paires)}
    # Taux d'erreur par entite : seuls les enonces qui portent un numero comptent.
    for bande in ("16k", "8k"):
        tests = [l[bande]["tel_ok"] for l in detail
                 if bande in l and "tel_ok" in l.get(bande, {})]
        if tests:
            resume.setdefault(bande, {})["tel_exact_pct"] = round(100 * sum(tests) / len(tests), 1)
            resume[bande]["tel_n"] = len(tests)

    json.dump({"modele": args.modele, "resume": resume, "detail": detail},
              open(sortie, "w"), indent=2, ensure_ascii=False)
    print("\n" + json.dumps(resume, indent=2, ensure_ascii=False))
    if "16k" in resume and "8k" in resume:
        ecart = resume["8k"]["wer_pct"] / max(resume["16k"]["wer_pct"], 0.01)
        print(f"\nEcart bande telephonique : x{ecart:.2f} sur le WER.")
    print(f"Ecrit : {sortie}")


if __name__ == "__main__":
    main()
