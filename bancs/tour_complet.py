#!/usr/bin/env python3
"""Le tour de parole complet : combien de silence l'appelant entend vraiment.

Les mesures 11 et 13 donnent chaque etage separement. Celle-ci les enchaine,
parce que ce que l'appelant percoit n'est aucun des trois : c'est la somme des
delais AVANT le premier son de la reponse.

Chaine mesuree, sur un enonce reel du corpus en 8 kHz :
    STT (local, streaming)  ->  LLM (distant, connexion gardee)  ->  TTS (flux)

Ce qui est compte comme « silence percu » : finalisation du STT + premier token
du LLM + premier fragment audio. Ce qui suit se joue pendant que l'agent parle.

Usage : GROQ_API_KEY=... cd bancs && PYTHONPATH=. ~/bancs-stt/bin/python tour_complet.py
"""

import argparse
import http.client
import json
import os
import statistics
import time

import wer_sherpa
from piper import PiperVoice

SYSTEME = (
    "Tu es l'accueil telephonique d'un salon de coiffure. Tu reponds en une seule "
    "phrase courte, en francais, sans jamais inventer un horaire. Si la demande est "
    "un rendez-vous, tu proposes un creneau et tu demandes confirmation. "
    "Horaires : mardi a samedi, 9 h a 19 h, fermeture entre 13 h et 14 h. "
    "Prestations : coupe 30 min, brushing 45 min, coloration 1 h 30, balayage 2 h 15."
)


def percentile(v, p):
    o = sorted(v)
    return o[min(len(o) - 1, int(round(p / 100 * (len(o) - 1))))]


class ClientLLM:
    """Connexion gardee ouverte : mesure 4 a montre que c'est la que tout se joue."""

    def __init__(self, hote, chemin, cle, modele):
        self.hote, self.chemin, self.cle, self.modele = hote, chemin, cle, modele
        self.conn = http.client.HTTPSConnection(hote, timeout=60)
        self.entetes = {"Authorization": f"Bearer {cle}", "Content-Type": "application/json",
                        "User-Agent": "marpeap-banc-tour/1.0", "Accept": "text/event-stream"}

    def repondre(self, question):
        corps = json.dumps({
            "model": self.modele, "stream": True, "max_tokens": 80, "temperature": 0.2,
            "reasoning_effort": "none",
            "messages": [{"role": "system", "content": SYSTEME},
                         {"role": "user", "content": question}],
        })
        depart = time.perf_counter()
        self.conn.request("POST", self.chemin, body=corps, headers=self.entetes)
        r = self.conn.getresponse()
        ttft, morceaux = None, []
        while True:
            ligne = r.readline()
            if not ligne:
                break
            if ligne.startswith(b"data: "):
                charge = ligne[6:].strip()
                if charge == b"[DONE]":
                    break
                try:
                    d = json.loads(charge)["choices"][0]["delta"]
                except Exception:
                    continue
                if d.get("content"):
                    if ttft is None:
                        ttft = (time.perf_counter() - depart) * 1000
                    morceaux.append(d["content"])
        r.read()
        return "".join(morceaux), ttft, (time.perf_counter() - depart) * 1000


def premier_fragment(voix, texte):
    depart = time.perf_counter()
    for _ in voix.synthesize(texte):
        return (time.perf_counter() - depart) * 1000
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=os.path.expanduser("~/corpus-fr"))
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--modele-llm", default="qwen/qwen3.6-27b")
    args = ap.parse_args()

    cle = os.environ.get("GROQ_API_KEY")
    if not cle:
        raise SystemExit("GROQ_API_KEY absente")

    manifeste = json.load(open(os.path.join(args.corpus, "manifeste.json")))
    # Des enonces qui appellent une vraie reponse, pas des cas limites.
    choisis = [e for e in manifeste if e["famille"] in ("rdv", "date", "report", "prix")][:args.n]

    reconnaisseur = wer_sherpa.construire(os.path.expanduser(
        "~/modeles/sherpa-onnx-streaming-zipformer-fr-2023-04-14"), fils=2)
    voix = PiperVoice.load(os.path.expanduser("~/piper/fr_FR-siwis-medium.onnx"))
    llm = ClientLLM("api.groq.com", "/openai/v1/chat/completions", cle, args.modele_llm)

    etapes = {"stt": [], "llm": [], "tts": [], "total": []}
    lignes = []
    for entree in choisis:
        chemin = os.path.join(args.corpus, "8k", entree["id"] + ".wav")
        if not os.path.exists(chemin):
            continue
        texte, ms_stt, duree = wer_sherpa.transcrire(chemin, reconnaisseur)
        if not texte.strip():
            continue
        try:
            reponse, ttft, _ = llm.repondre(texte)
        except Exception as e:
            print(f"{entree['id']}: LLM {type(e).__name__}", flush=True)
            llm.conn = http.client.HTTPSConnection(llm.hote, timeout=60)
            continue
        if ttft is None or not reponse.strip():
            continue
        ms_tts = premier_fragment(voix, reponse.strip()[:200])
        total = ms_stt + ttft + (ms_tts or 0)
        for cle_etape, valeur in (("stt", ms_stt), ("llm", ttft), ("tts", ms_tts), ("total", total)):
            etapes[cle_etape].append(valeur)
        lignes.append({"id": entree["id"], "audio_s": round(duree, 2),
                       "stt_ms": round(ms_stt), "llm_ttft_ms": round(ttft),
                       "tts_premier_ms": round(ms_tts or 0), "total_ms": round(total),
                       "transcription": texte, "reponse": reponse.strip()[:120]})
        print(f"{entree['id']:14s} STT {ms_stt:5.0f} + LLM {ttft:5.0f} + TTS {ms_tts:5.0f} "
              f"= {total:5.0f} ms", flush=True)
        time.sleep(1.0)

    resume = {k: {"p50_ms": round(statistics.median(v)), "p90_ms": round(percentile(v, 90)),
                  "n": len(v)} for k, v in etapes.items() if v}
    json.dump({"modele_llm": args.modele_llm, "resume": resume, "detail": lignes},
              open(os.path.join(os.path.dirname(__file__), "tour-complet-resultats.json"), "w"),
              indent=2, ensure_ascii=False)
    print("\n" + json.dumps(resume, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
