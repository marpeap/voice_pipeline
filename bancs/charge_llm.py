#!/usr/bin/env python3
"""Combien de requetes simultanees un fournisseur de LLM accepte ?

C'est le dernier chiffre de capacite qui manque : les mesures 11 et 13 ont
montre que la machine tient une dizaine d'appels, et la mesure 14 que toute la
variance du temps de reponse vient du LLM. Reste a savoir ce qui se passe quand
dix appels parlent en meme temps.

Mesure, par palier de K requetes lancees ensemble : le TTFT median, le nombre de
refus (429) et le delai d'attente que le fournisseur impose. Le palier gratuit
n'est pas un fournisseur de production — mais sa facon de refuser l'est.

Usage : GROQ_API_KEY=... cd bancs && PYTHONPATH=. ~/bancs-stt/bin/python charge_llm.py
"""

import http.client
import json
import os
import statistics
import threading
import time

SYSTEME = ("Tu es l'accueil d'un salon de coiffure. Une phrase courte, en francais.")
QUESTION = "Bonjour, je voudrais un rendez-vous jeudi matin."
MODELE = os.environ.get("MODELE_LLM", "openai/gpt-oss-20b")


def une_requete(cle, resultats, index):
    corps = json.dumps({
        "model": MODELE, "stream": True, "max_tokens": 40, "temperature": 0.2,
        "reasoning_effort": "low",
        "messages": [{"role": "system", "content": SYSTEME},
                     {"role": "user", "content": QUESTION}],
    })
    conn = http.client.HTTPSConnection("api.groq.com", timeout=60)
    depart = time.perf_counter()
    try:
        conn.request("POST", "/openai/v1/chat/completions", body=corps,
                     headers={"Authorization": f"Bearer {cle}",
                              "Content-Type": "application/json",
                              "User-Agent": "marpeap-banc-charge-llm/1.0",
                              "Accept": "text/event-stream"})
        r = conn.getresponse()
        if r.status != 200:
            charge = r.read()
            attente = r.getheader("retry-after")
            resultats[index] = ("refus", r.status, attente, charge[:160].decode(errors="replace"))
            return
        ttft = None
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
                if d.get("content") and ttft is None:
                    ttft = (time.perf_counter() - depart) * 1000
        resultats[index] = ("ok", ttft, None, None)
    except Exception as e:
        resultats[index] = ("erreur", type(e).__name__, None, str(e)[:120])
    finally:
        conn.close()


def main():
    cle = os.environ["GROQ_API_KEY"]
    lignes = []
    for k in (1, 2, 4, 6, 8, 10):
        resultats = [None] * k
        fils = [threading.Thread(target=une_requete, args=(cle, resultats, i)) for i in range(k)]
        depart = time.perf_counter()
        for f in fils:
            f.start()
        for f in fils:
            f.join()
        mur = (time.perf_counter() - depart) * 1000

        ok = [r[1] for r in resultats if r and r[0] == "ok" and r[1]]
        refus = [r for r in resultats if r and r[0] == "refus"]
        ligne = {"simultanees": k, "servies": len(ok), "refusees": len(refus),
                 "ttft_p50_ms": round(statistics.median(ok)) if ok else None,
                 "ttft_max_ms": round(max(ok)) if ok else None,
                 "mur_ms": round(mur),
                 "codes": sorted({r[1] for r in refus}),
                 "attente_imposee_s": sorted({r[2] for r in refus if r[2]}),
                 "exemple_refus": refus[0][3] if refus else None}
        lignes.append(ligne)
        print(f"{k:2d} simultanees : {len(ok)} servies, {len(refus)} refusees · "
              f"TTFT p50 {ligne['ttft_p50_ms']} ms, max {ligne['ttft_max_ms']} ms", flush=True)
        if refus:
            print(f"      refus {ligne['codes']} attente {ligne['attente_imposee_s']} · "
                  f"{(ligne['exemple_refus'] or '')[:120]}", flush=True)
        time.sleep(20)  # on laisse la fenetre de quota se reconstituer entre paliers

    json.dump(lignes, open(os.path.join(os.path.dirname(__file__), "charge-llm-resultats.json"), "w"),
              indent=2, ensure_ascii=False)
    print("\nEcrit : bancs/charge-llm-resultats.json")


if __name__ == "__main__":
    main()
