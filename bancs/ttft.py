#!/usr/bin/env python3
"""Banc TTFT — temps jusqu'au premier mot, sur des fournisseurs compatibles OpenAI.

Ce que ce banc mesure, et que personne ne publie pour la France : le delai entre
la fin de la requete et le PREMIER octet de contenu, depuis une machine situee en
France, avec un prompt de la taille reelle d'un agent telephonique.

Deux tailles de prompt, parce que le cache de prompt a un seuil : en dessous de
~4096 tokens de prefixe, rien n'est mis en cache, et un prompt plus long peut
donc etre moins cher ET plus rapide qu'un prompt court.

Aucune cle n'est ecrite ici. Chaque fournisseur est saute si sa variable
d'environnement est absente :
    GROQ_API_KEY · MISTRAL_API_KEY · SCW_SECRET_KEY · OPENAI_API_KEY · CEREBRAS_API_KEY

Usage :
    GROQ_API_KEY=... python3 bancs/ttft.py            # tous les fournisseurs disponibles
    GROQ_API_KEY=... python3 bancs/ttft.py --tours 15
"""

import argparse
import json
import os
import statistics
import time
import urllib.error
import urllib.request

FOURNISSEURS = [
    # (nom, variable d'env, base_url, [modeles], zone annoncee)
    ("groq", "GROQ_API_KEY", "https://api.groq.com/openai/v1",
     ["openai/gpt-oss-20b", "qwen/qwen3.6-27b"], "US"),
    ("mistral", "MISTRAL_API_KEY", "https://api.mistral.ai/v1",
     ["mistral-small-latest"], "UE (Paris)"),
    ("scaleway", "SCW_SECRET_KEY", "https://api.scaleway.ai/v1",
     ["llama-3.3-70b-instruct"], "UE (Paris)"),
    ("cerebras", "CEREBRAS_API_KEY", "https://api.cerebras.ai/v1",
     ["llama-3.3-70b"], "US"),
    ("openai", "OPENAI_API_KEY", "https://api.openai.com/v1",
     ["gpt-4o-mini"], "US"),
]

# Le prefixe long doit depasser le seuil de cache (4096 tokens). On le fabrique
# a partir d'un bloc de connaissance realiste, repete : c'est exactement la forme
# du memoire.md d'un salon (horaires, prestations, regles, interdits).
BLOC = (
    "Regle du salon : les couleurs ne se prennent jamais apres 17 h 30 le samedi. "
    "Le balayage dure deux heures quinze et se fait uniquement avec Sophie ou Lea. "
    "Une coupe homme dure trente minutes. Un brushing seul, quarante-cinq minutes. "
    "En cas de retard de plus de dix minutes, la prestation est raccourcie, jamais annulee. "
    "Le salon ne prend aucun rendez-vous le lundi. Les extensions se devisent en personne. "
)

# Certains modeles raisonnent avant de parler : on leur demande de ne pas le faire.
EXTRA = {
    "openai/gpt-oss-20b": {"reasoning_effort": "low"},
    "openai/gpt-oss-120b": {"reasoning_effort": "low"},
    "qwen/qwen3.6-27b": {"reasoning_effort": "none"},
}

QUESTION = "Bonjour, je voudrais un rendez-vous pour une coupe jeudi matin si possible."


def prefixe(cible_tokens: int) -> str:
    # ~1 token pour 4 caracteres en francais : approximation suffisante pour
    # se placer franchement au-dessus ou en dessous du seuil.
    repetitions = max(1, (cible_tokens * 4) // len(BLOC))
    return BLOC * repetitions


def un_tour(base_url: str, cle: str, modele: str, systeme: str, timeout=60.0,
            extra=None):
    """Retourne (ttft_contenu_ms, ttft_premier_token_ms, total_ms) ou leve.

    Les deux mesures different sur un modele de raisonnement : le flux commence
    par des tokens de raisonnement (`reasoning` / `reasoning_content`), et le
    premier mot PRONONCABLE n'arrive qu'apres. Pour un agent telephonique, seule
    la premiere compte.
    """
    charge_requete = {
        "model": modele,
        "messages": [
            {"role": "system", "content": systeme},
            {"role": "user", "content": QUESTION},
        ],
        "stream": True,
        "max_tokens": 200,
        "temperature": 0.2,
    }
    if extra:
        charge_requete.update(extra)
    corps = json.dumps(charge_requete).encode()

    requete = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=corps,
        headers={
            "Authorization": f"Bearer {cle}",
            "Content-Type": "application/json",
            # Sans User-Agent, certains fournisseurs repondent 403 la ou curl passe.
            "User-Agent": "marpeap-banc-ttft/1.0",
            "Accept": "text/event-stream",
        },
    )

    depart = time.perf_counter()
    ttft = None
    ttft_any = None
    with urllib.request.urlopen(requete, timeout=timeout) as reponse:
        for ligne in reponse:
            if not ligne.startswith(b"data: "):
                continue
            charge = ligne[6:].strip()
            if charge == b"[DONE]":
                break
            try:
                delta = json.loads(charge)["choices"][0]["delta"]
            except (json.JSONDecodeError, KeyError, IndexError):
                continue
            if ttft_any is None and (delta.get("content") or delta.get("reasoning")
                                     or delta.get("reasoning_content")):
                ttft_any = (time.perf_counter() - depart) * 1000
            if delta.get("content") and ttft is None:
                # Premier octet de CONTENU, pas le premier evenement du flux :
                # certains fournisseurs envoient d'abord un delta de role vide.
                ttft = (time.perf_counter() - depart) * 1000
    total = (time.perf_counter() - depart) * 1000
    if ttft is None:
        raise RuntimeError("flux termine sans aucun contenu prononcable")
    return ttft, ttft_any, total


def percentile(valeurs, p):
    if not valeurs:
        return float("nan")
    ordonnees = sorted(valeurs)
    rang = min(len(ordonnees) - 1, int(round(p / 100 * (len(ordonnees) - 1))))
    return ordonnees[rang]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tours", type=int, default=10, help="mesures par (modele, taille)")
    ap.add_argument("--chauffe", type=int, default=2, help="tours jetes, pour amorcer le cache")
    args = ap.parse_args()

    tailles = [("court (~200 tokens)", 200), ("long (~5000 tokens)", 5000)]
    resultats = []

    for nom, var, base, modeles, zone in FOURNISSEURS:
        cle = os.environ.get(var)
        if not cle:
            print(f"-- {nom:10s} saute : {var} absente")
            continue
        for modele in modeles:
            for etiquette, cible in tailles:
                systeme = prefixe(cible)
                mesures, premiers, erreurs = [], [], []
                for i in range(args.tours + args.chauffe):
                    try:
                        ttft, ttft_any, total = un_tour(base, cle, modele, systeme,
                                                        extra=EXTRA.get(modele))
                        if i >= args.chauffe:
                            mesures.append(ttft)
                            premiers.append(ttft_any or ttft)
                    except urllib.error.HTTPError as e:
                        erreurs.append(f"HTTP {e.code}")
                        break
                    except Exception as e:  # reseau, timeout, flux vide
                        erreurs.append(type(e).__name__)
                    time.sleep(0.3)  # on ne martele pas un quota gratuit
                if mesures:
                    ligne = {
                        "fournisseur": nom, "zone": zone, "modele": modele,
                        "prompt": etiquette, "n": len(mesures),
                        "p50_ms": round(statistics.median(mesures)),
                        "p90_ms": round(percentile(mesures, 90)),
                        "min_ms": round(min(mesures)),
                        "premier_token_p50_ms": round(statistics.median(premiers)),
                        "erreurs": erreurs,
                    }
                    resultats.append(ligne)
                    print(f"{nom:10s} {modele:28s} {etiquette:20s} "
                          f"p50 {ligne['p50_ms']:5d} ms  p90 {ligne['p90_ms']:5d} ms  (n={ligne['n']})")
                else:
                    print(f"{nom:10s} {modele:28s} {etiquette:20s} ECHEC {erreurs[:3]}")

    if resultats:
        sortie = os.path.join(os.path.dirname(__file__), "ttft-resultats.json")
        with open(sortie, "w") as f:
            json.dump(resultats, f, indent=2, ensure_ascii=False)
        print(f"\nEcrit : {sortie}")
        print("Rappel : le budget vise est 250 ms p50. Au-dela, c'est souvent la "
              "distance, pas le modele — comparer les zones avant de changer de modele.")


if __name__ == "__main__":
    main()
