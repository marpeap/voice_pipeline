#!/usr/bin/env python3
"""Les memes douze tours, mais avec les garde-fous. Combien de fautes restent ?

La mesure 14 a montre qu'un agent « prompt seul » ment six fois sur douze :
creneaux inventes, faits calendaires inventes, confirmations orphelines. Ce banc
rejoue exactement les memes enonces avec l'architecture que docs/15 prescrit :

  1. le modele ne redige rien — il rend une PROPOSITION structuree ;
  2. aucune date ne vient de lui : le calendrier est injecte, calcule par la machine ;
  3. la machine valide la proposition contre l'agenda et compose la phrase ;
  4. toute entite absente, douteuse ou refusee devient une QUESTION, jamais un comblement.

Ce qui est mesure : combien de fois le modele invente une entite que la
transcription ne contient pas, et combien de fautes survivent a la validation.

Usage : GROQ_API_KEY=... cd bancs && PYTHONPATH=. ~/bancs-stt/bin/python tour_garde.py
"""

import http.client
import json
import os
import re
import time
from datetime import date, timedelta

import wer_sherpa

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]

# --- ce que la machine sait, et que le modele ne doit jamais deviner ---
AUJOURD_HUI = date(2026, 9, 15)  # un mardi
CRENEAUX = {}
for delta in range(0, 14):
    j = AUJOURD_HUI + timedelta(days=delta)
    if j.weekday() in (0, 6):        # lundi et dimanche fermes
        continue
    CRENEAUX[j.isoformat()] = ["09:00", "09:45", "10:30", "11:15", "12:00",
                               "14:00", "14:45", "15:30", "16:15", "17:00", "17:45"]


def calendrier_texte():
    lignes = []
    for iso, heures in list(CRENEAUX.items())[:8]:
        j = date.fromisoformat(iso)
        lignes.append(f"{JOURS[j.weekday()]} {j.day:02d}/{j.month:02d} : " + " ".join(heures))
    return "\n".join(lignes)


SYSTEME = f"""Tu analyses UNE phrase d'appelant pour un salon de coiffure.
Tu ne rediges AUCUNE reponse au client : la machine s'en charge.
Tu ne confirmes RIEN : tu n'as acces a aucune base.
Tu n'inventes AUCUNE date : le calendrier ci-dessous est la seule verite.

Aujourd'hui : {JOURS[AUJOURD_HUI.weekday()]} {AUJOURD_HUI.day:02d}/{AUJOURD_HUI.month:02d}/{AUJOURD_HUI.year}.
Creneaux libres :
{calendrier_texte()}

Rends UNIQUEMENT un objet JSON, sans texte autour :
{{"intention": "rdv|report|annulation|question|inconnu",
  "date": "AAAA-MM-JJ ou null",
  "heure": "HH:MM ou null",
  "prestation": "texte ou null",
  "confiance": {{"date": 0.0, "heure": 0.0, "prestation": 0.0, "intention": 0.0}},
  "manque": ["champ", ...]}}

Regle absolue : si la transcription est incomplete ou abimee, mets null et une
confiance basse. Ne comble jamais un trou par une valeur plausible."""


class Client:
    def __init__(self, cle, modele):
        self.cle, self.modele = cle, modele
        self.conn = http.client.HTTPSConnection("api.groq.com", timeout=60)

    def proposer(self, transcription):
        corps = json.dumps({
            "model": self.modele, "temperature": 0.0, "max_tokens": 300,
            "reasoning_effort": REFLEXION,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": SYSTEME},
                         {"role": "user", "content": transcription}],
        })
        self.conn.request("POST", "/openai/v1/chat/completions", body=corps,
                          headers={"Authorization": f"Bearer {self.cle}",
                                   "Content-Type": "application/json",
                                   "User-Agent": "marpeap-banc-garde/1.0"})
        r = self.conn.getresponse()
        charge = json.loads(r.read())
        if "choices" not in charge:
            # Le message d'erreur du fournisseur vaut mieux qu'un KeyError muet.
            raise RuntimeError(f"HTTP {r.status} : {json.dumps(charge)[:300]}")
        return charge["choices"][0]["message"]["content"]


SEUIL = 0.7

# Le catalogue bouge sous les pieds : "none" est refuse par gpt-oss, accepte
# ailleurs. La valeur vit donc ici, pas en dur dans la requete.
REFLEXION = os.environ.get("REFLEXION_LLM", "low")


def decider(proposition):
    """La machine compose la phrase. Le modele n'ecrit jamais au client."""
    faibles = [c for c, v in proposition.get("confiance", {}).items() if v < SEUIL]
    manque = list(proposition.get("manque") or [])
    intention = proposition.get("intention", "inconnu")

    if intention == "inconnu" or "intention" in faibles:
        return "question", "Je n'ai pas bien saisi votre demande, pouvez-vous repeter ?"

    if intention in ("rdv", "report"):
        d, h = proposition.get("date"), proposition.get("heure")
        if not d or "date" in faibles or "date" in manque:
            return "question", "Quel jour vous conviendrait ?"
        if d not in CRENEAUX:
            # Piege trouve au premier essai : l'absence du calendrier ne veut pas
            # dire « ferme ». Hors horizon et ferme sont deux reponses differentes,
            # et confondre les deux fait mentir la machine a son tour.
            jour = date.fromisoformat(d)
            if jour > max(date.fromisoformat(x) for x in CRENEAUX):
                return "hors horizon", ("Je ne prends pas encore les rendez-vous aussi loin. "
                                        "Rappelez-nous quelques semaines avant.")
            if jour.weekday() in (0, 6):
                return "refus", "Nous sommes fermes ce jour-la, souhaitez-vous un autre jour ?"
            return "question", "Ce jour n'apparait pas dans mon agenda, pouvez-vous le repeter ?"
        if not h or "heure" in faibles or "heure" in manque:
            return "question", f"Quelle heure preferez-vous ? Il reste {len(CRENEAUX[d])} creneaux."
        if h not in CRENEAUX[d]:
            voisins = ", ".join(CRENEAUX[d][:3])
            return "refus", f"Ce creneau n'est pas libre. Il reste {voisins}."
        # Jamais « c'est note » : une PROPOSITION, que l'ecriture en base confirmera.
        return "proposition", f"Je peux vous reserver le {d} a {h}. Je confirme ?"

    if intention == "annulation":
        return "question", "Pour annuler, pouvez-vous me donner votre nom et votre numero ?"
    return "question", "Que puis-je faire pour vous ?"


def entites_dans_le_texte(proposition, transcription):
    """Le modele a-t-il invente une heure que la transcription ne porte pas ?"""
    h = proposition.get("heure")
    if not h:
        return True
    heure = int(h.split(":")[0])
    t = transcription.lower()
    mots = {0: ["minuit"], 12: ["midi"]}
    chiffres = ["zero", "une", "deux", "trois", "quatre", "cinq", "six", "sept", "huit",
                "neuf", "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize"]
    formes = [str(heure)]
    if heure < len(chiffres):
        formes.append(chiffres[heure])
    if heure > 12 and (heure - 12) < len(chiffres):
        formes += [chiffres[heure - 12], str(heure - 12)]
    formes += mots.get(heure, [])
    return any(re.search(rf"\b{f}\b", t) for f in formes)


def main():
    cle = os.environ["GROQ_API_KEY"]
    corpus = os.path.expanduser("~/corpus-fr")
    manifeste = json.load(open(os.path.join(corpus, "manifeste.json")))
    choisis = [e for e in manifeste if e["famille"] in ("rdv", "date", "report", "prix")][:12]

    reconnaisseur = wer_sherpa.construire(os.path.expanduser(
        "~/modeles/sherpa-onnx-streaming-zipformer-fr-2023-04-14"), fils=2)
    client = Client(cle, "openai/gpt-oss-20b")

    lignes = []
    inventions = 0
    for entree in choisis:
        chemin = os.path.join(corpus, "8k", entree["id"] + ".wav")
        transcription, _, _ = wer_sherpa.transcrire(chemin, reconnaisseur)
        if not transcription.strip():
            continue
        try:
            brut = client.proposer(transcription)
            proposition = json.loads(brut)
        except Exception as e:
            print(f"{entree['id']}: {type(e).__name__}", flush=True)
            client.conn = http.client.HTTPSConnection("api.groq.com", timeout=60)
            continue
        genre, phrase = decider(proposition)
        ancree = entites_dans_le_texte(proposition, transcription)
        if not ancree:
            inventions += 1
        lignes.append({"id": entree["id"], "reference": entree["texte"],
                       "transcription": transcription, "proposition": proposition,
                       "genre": genre, "phrase": phrase, "heure_ancree": ancree})
        print(f"{entree['id']:14s} {genre:11s} | {phrase[:58]:58s} | "
              f"heure ancree: {'oui' if ancree else 'NON'}", flush=True)
        time.sleep(1.0)

    resume = {"tours": len(lignes),
              "questions": sum(1 for l in lignes if l["genre"] == "question"),
              "refus": sum(1 for l in lignes if l["genre"] == "refus"),
              "propositions": sum(1 for l in lignes if l["genre"] == "proposition"),
              "hors_horizon": sum(1 for l in lignes if l["genre"] == "hors horizon"),
              "heures_inventees": inventions,
              "confirmations_orphelines": sum(
                  1 for l in lignes if re.search(r"c'est note|annul|enregistr", l["phrase"], re.I))}
    json.dump({"resume": resume, "detail": lignes},
              open(os.path.join(os.path.dirname(__file__), "tour-garde-resultats.json"), "w"),
              indent=2, ensure_ascii=False)
    print("\n" + json.dumps(resume, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
