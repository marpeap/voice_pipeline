#!/usr/bin/env python3
"""Combien de tours coute la rigueur ?

La mesure 15 a montre qu'un agent a garde-fous ne ment plus mais fait repeter :
sept tours sur dix finissent en question. Reste la question qui decide de
l'utilisabilite : **quand l'agent demande une precision, obtient-il sa reponse ?**

Ce banc ferme la boucle. L'appelant est simule, mais ses reponses passent par la
meme chaine que le reste : elles sont SYNTHETISEES, degradees en 8 kHz mu-law,
puis retranscrites. Une reponse de clarification est donc aussi abimee que la
demande initiale — c'est tout l'interet, un banc qui rendrait le texte parfait
a la deuxieme question mesurerait une conversation qui n'existe pas.

Mesure : nombre de tours jusqu'a une paire (date, heure) valide, ou abandon.

Usage : GROQ_API_KEY=... cd bancs && PYTHONPATH=. ~/bancs-stt/bin/python boucle_clarification.py
"""

import json
import os
import subprocess
import time

import tour_garde
import wer_sherpa
from piper import PiperVoice

MAX_TOURS = 4
CACHE = os.path.expanduser("~/corpus-clarification")

# Ce que l'appelant repond, selon ce que la machine lui demande.
REPONSES = {
    "jour": "Jeudi, jeudi prochain.",
    "heure": "Quinze heures trente.",
    "repeter": "Je voudrais un rendez-vous jeudi prochain a quinze heures trente.",
    "autre_jour": "Alors vendredi, a la meme heure.",
}


def voix_degradee(voix, cle, texte):
    """Synthetise, passe en 8 kHz mu-law aller-retour, rend le chemin du fichier."""
    os.makedirs(CACHE, exist_ok=True)
    final = os.path.join(CACHE, f"{cle}.wav")
    if os.path.exists(final):
        return final
    brut = os.path.join(CACHE, f"{cle}.brut.wav")
    import wave
    with wave.open(brut, "wb") as f:   # synthesize_wav attend un objet wave, pas un flux
        voix.synthesize_wav(texte, f)
    mulaw = os.path.join(CACHE, f"{cle}.ulaw.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", brut, "-ar", "8000",
                    "-ac", "1", "-c:a", "pcm_mulaw", "-f", "wav", mulaw], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mulaw, "-ar", "8000",
                    "-ac", "1", "-c:a", "pcm_s16le", final], check=True)
    os.remove(brut)
    os.remove(mulaw)
    return final


def quelle_reponse(phrase):
    p = phrase.lower()
    if "quel jour" in p:
        return "jour"
    if "quelle heure" in p:
        return "heure"
    if "autre jour" in p or "fermes" in p or "pas libre" in p:
        return "autre_jour"
    return "repeter"


def main():
    cle_api = os.environ["GROQ_API_KEY"]
    corpus = os.path.expanduser("~/corpus-fr")
    manifeste = json.load(open(os.path.join(corpus, "manifeste.json")))
    scenarios = [e for e in manifeste if e["famille"] in ("rdv", "date", "report")][:10]

    reconnaisseur = wer_sherpa.construire(os.path.expanduser(
        "~/modeles/sherpa-onnx-streaming-zipformer-fr-2023-04-14"), fils=2)
    voix = PiperVoice.load(os.path.expanduser("~/piper/fr_FR-siwis-medium.onnx"))
    client = tour_garde.Client(cle_api, "qwen/qwen3.6-27b")

    lignes = []
    for entree in scenarios:
        chemin = os.path.join(corpus, "8k", entree["id"] + ".wav")
        if not os.path.exists(chemin):
            continue
        connu = {"date": None, "heure": None}
        echanges = []
        issue = "abandon"
        for tour in range(1, MAX_TOURS + 1):
            transcription, _, _ = wer_sherpa.transcrire(chemin, reconnaisseur)
            # Le contexte deja obtenu est rappele au modele, comme le ferait la machine.
            entree_modele = transcription
            if connu["date"] or connu["heure"]:
                entree_modele = (f"[deja connu : date={connu['date']} heure={connu['heure']}] "
                                 + transcription)
            proposition = None
            for essai in range(4):
                try:
                    proposition = json.loads(client.proposer(entree_modele))
                    break
                except Exception:
                    time.sleep(8 * (essai + 1))
                    client.conn = tour_garde.http.client.HTTPSConnection("api.groq.com", timeout=60)
            if proposition is None:
                issue = "quota"
                break
            for champ in ("date", "heure"):
                v = proposition.get(champ)
                if v and proposition.get("confiance", {}).get(champ, 0) >= tour_garde.SEUIL:
                    connu[champ] = v
            proposition.setdefault("confiance", {})
            fusion = dict(proposition)
            fusion["date"] = connu["date"] or proposition.get("date")
            fusion["heure"] = connu["heure"] or proposition.get("heure")
            for champ in ("date", "heure"):
                if connu[champ]:
                    fusion["confiance"][champ] = 1.0
            genre, phrase = tour_garde.decider(fusion)
            echanges.append({"tour": tour, "transcription": transcription,
                             "genre": genre, "phrase": phrase})
            if genre == "proposition":
                issue = "aboutie"
                break
            besoin = quelle_reponse(phrase)
            chemin = voix_degradee(voix, besoin, REPONSES[besoin])
            time.sleep(1.0)

        lignes.append({"id": entree["id"], "reference": entree["texte"],
                       "issue": issue, "tours": len(echanges), "echanges": echanges,
                       "retenu": connu})
        print(f"{entree['id']:14s} {issue:8s} en {len(echanges)} tours "
              f"| date={connu['date']} heure={connu['heure']}", flush=True)
        if issue == "quota":
            break

    abouties = [l for l in lignes if l["issue"] == "aboutie"]
    resume = {"scenarios": len(lignes),
              "abouties": len(abouties),
              "tours_moyens_si_aboutie": round(sum(l["tours"] for l in abouties) / len(abouties), 2)
              if abouties else None,
              "abandons": sum(1 for l in lignes if l["issue"] == "abandon"),
              "arret_quota": sum(1 for l in lignes if l["issue"] == "quota")}
    json.dump({"resume": resume, "detail": lignes},
              open(os.path.join(os.path.dirname(__file__), "boucle-resultats.json"), "w"),
              indent=2, ensure_ascii=False)
    print("\n" + json.dumps(resume, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
