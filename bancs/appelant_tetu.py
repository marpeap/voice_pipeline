#!/usr/bin/env python3
"""L'appelant qui n'est pas coopératif — la machine sait-elle passer la main ?

La mesure 16 a mesure une boucle avec un appelant souple : il acceptait
l'alternative. Ce banc mesure l'inverse, qui est le cas difficile et le plus
courant au telephone : quelqu'un qui tient a son creneau, se repete, s'agace,
puis demande un humain.

Deux choses sont mesurees :
  1. la machine applique-t-elle les deux regles nees de la mesure 16 — oublier
     une valeur refusee deux fois, ne jamais se repeter mot pour mot ;
  2. combien de tours avant qu'elle ne passe la main, au lieu de negocier.

Trois variantes d'appelant, chacune jouee avec les memes garde-fous :
  A. insiste deux fois puis accepte ;
  B. insiste jusqu'au bout, sans jamais demander d'humain ;
  C. demande explicitement un humain au deuxieme tour.

Usage : GROQ_API_KEY=... cd bancs && PYTHONPATH=. ~/bancs-stt/bin/python appelant_tetu.py
"""

import json
import os
import re
import time

import boucle_clarification as boucle
import tour_garde
import wer_sherpa
from piper import PiperVoice

MAX_TOURS = 6

SCENARIOS = {
    "A_insiste_puis_cede": [
        "Je voudrais samedi a dix-huit heures trente.",
        "Non, samedi dix-huit heures trente, c'est ce qui m'arrange.",
        "Bon, tant pis, alors jeudi a quinze heures trente.",
    ],
    "B_insiste_toujours": [
        "Je voudrais samedi a dix-huit heures trente.",
        "Non, samedi dix-huit heures trente.",
        "Je vous ai deja dit, samedi dix-huit heures trente.",
        "Samedi dix-huit heures trente, je ne comprends pas.",
        "Samedi dix-huit heures trente.",
        "Samedi dix-huit heures trente.",
    ],
    "C_demande_un_humain": [
        "Je voudrais samedi a dix-huit heures trente.",
        "Passez-moi quelqu'un, une vraie personne s'il vous plait.",
        "Je veux parler a la patronne.",
    ],
}

MOTS_HUMAIN = ("quelqu un", "une vraie personne", "la patronne", "le patron",
               "un humain", "parler a quelqu un", "responsable")


def demande_un_humain(transcription):
    t = re.sub(r"[^a-z ]", " ", transcription.lower().replace("'", " "))
    t = re.sub(r"\s+", " ", t)
    return any(m in t for m in MOTS_HUMAIN)


def decider_v2(proposition, etat):
    """Le decideur de tour_garde, plus les deux regles nees de la mesure 16."""
    genre, phrase = tour_garde.decider(proposition)

    # Regle 1 — une entite refusee deux fois de suite est oubliee.
    if genre == "refus":
        etat["refus_consecutifs"] += 1
        if etat["refus_consecutifs"] >= 2:
            etat["oubliees"].add("heure")
            etat["refus_consecutifs"] = 0
            jour = proposition.get("date")
            libres = tour_garde.CRENEAUX.get(jour, [])[:3]
            genre = "question"
            phrase = ("Je n'ai pas ce creneau. Parmi " + ", ".join(libres)
                      + ", lequel vous conviendrait ?") if libres else \
                     "Quel autre jour vous conviendrait ?"
    else:
        etat["refus_consecutifs"] = 0

    # Regle 3 — compteur de progres : la seule qui attrape l'alternance.
    # Les regles 1 et 2 sont locales ; un appelant qui alterne question et refus
    # ne les declenche jamais. Celle-ci ne regarde pas les phrases mais l'avancement.
    if etat["tours_sans_progres"] >= 2:  # deux tours sans progres suffisent au telephone
        etat["derniere_phrase"] = None
        return "transfert", "Je prefere vous passer quelqu'un du salon, ce sera plus simple."

    # Regle 2 — jamais deux fois la meme phrase. Mais se repeter ne veut pas dire
    # abandonner : la premiere fois on CHANGE DE STRATEGIE (choix explicites,
    # une seule entite a la fois), et c'est seulement si cela echoue aussi qu'on
    # passe la main. Mesure 17 : transferer des la premiere repetition renvoyait
    # au salon des appelants qui allaient ceder au tour suivant.
    if phrase == etat.get("derniere_phrase"):
        etat["repetitions"] += 1
        if etat["repetitions"] == 1:
            jour = proposition.get("date")
            libres = tour_garde.CRENEAUX.get(jour, [])[:3] if jour else []
            genre = "reformulation"
            phrase = ("Je vais faire autrement : dites-moi seulement l'heure, "
                      + ("par exemple " + " ou ".join(libres) + "." if libres
                         else "par exemple neuf heures ou dix heures trente."))
        else:
            genre = "transfert"
            phrase = "Je crois que je ne vous aide pas. Je vous passe quelqu'un du salon."
    etat["derniere_phrase"] = phrase
    return genre, phrase


def main():
    cle_api = os.environ["GROQ_API_KEY"]
    voix = PiperVoice.load(os.path.expanduser("~/piper/fr_FR-siwis-medium.onnx"))
    reconnaisseur = wer_sherpa.construire(os.path.expanduser(
        "~/modeles/sherpa-onnx-streaming-zipformer-fr-2023-04-14"), fils=2)
    client = tour_garde.Client(cle_api, "openai/gpt-oss-20b")

    resultats = []
    for nom, repliques in SCENARIOS.items():
        etat = {"refus_consecutifs": 0, "repetitions": 0, "oubliees": set(),
                "derniere_phrase": None, "tours_sans_progres": 0,
                "deja_essayees": {"date": set(), "heure": set()}}
        connu = {"date": None, "heure": None}
        echanges = []
        issue = "boucle"
        for tour in range(1, MAX_TOURS + 1):
            texte = repliques[min(tour - 1, len(repliques) - 1)]
            fichier = boucle.voix_degradee(voix, f"{nom}-{tour}", texte)
            transcription, _, _ = wer_sherpa.transcrire(fichier, reconnaisseur)

            # Demande explicite d'humain : transfert immediat, sans negociation.
            if demande_un_humain(transcription):
                echanges.append({"tour": tour, "dit": texte, "transcription": transcription,
                                 "genre": "transfert", "phrase": "Je vous passe quelqu'un."})
                issue = "transfert_demande"
                break

            contexte = transcription
            if connu["date"] or connu["heure"]:
                contexte = (f"[deja connu : date={connu['date']} heure={connu['heure']}] "
                            + transcription)
            proposition = None
            for essai in range(4):
                try:
                    proposition = json.loads(client.proposer(contexte))
                    break
                except Exception:
                    time.sleep(8 * (essai + 1))
                    client.conn = tour_garde.http.client.HTTPSConnection("api.groq.com", timeout=60)
            if proposition is None:
                issue = "quota"
                break

            for champ in ("date", "heure"):
                if champ in etat["oubliees"]:
                    connu[champ] = None
                    proposition[champ] = None
                    continue
                v = proposition.get(champ)
                if v and proposition.get("confiance", {}).get(champ, 0) >= tour_garde.SEUIL:
                    connu[champ] = v
            fusion = dict(proposition)
            fusion.setdefault("confiance", {})
            for champ in ("date", "heure"):
                if connu[champ]:
                    fusion[champ] = connu[champ]
                    fusion["confiance"][champ] = 1.0
            # Le progres se compte sur les entites VALIDEES, pas sur les tours.
            # Le progres, c'est une entite qui passe de vide a remplie. Oublier une
            # valeur refusee n'en est PAS un : compter tout changement remettait le
            # compteur a zero a chaque oubli, et la boucle repartait pour un tour.
            # Troisieme definition, la bonne : un progres est une valeur JAMAIS
            # ENCORE ESSAYEE. Un appelant qui repete « samedi dix-huit heures
            # trente » refait passer l'entite de vide a remplie a chaque tour ;
            # compter cela comme un progres rendait le compteur inoperant.
            gagne = False
            for champ in ("date", "heure"):
                v = connu[champ]
                if v and v not in etat["deja_essayees"][champ]:
                    etat["deja_essayees"][champ].add(v)
                    gagne = True
            if gagne:
                etat["tours_sans_progres"] = 0
            else:
                etat["tours_sans_progres"] += 1
            genre, phrase = decider_v2(fusion, etat)
            echanges.append({"tour": tour, "dit": texte, "transcription": transcription,
                             "genre": genre, "phrase": phrase})
            if genre == "proposition":
                issue = "aboutie"
                break
            if genre == "transfert":
                issue = "transfert_machine"
                break
            time.sleep(1.0)

        resultats.append({"scenario": nom, "issue": issue, "tours": len(echanges),
                          "repetitions_bloquees": etat["repetitions"],
                          "tours_sans_progres": etat["tours_sans_progres"], "echanges": echanges})
        print(f"{nom:22s} {issue:18s} en {len(echanges)} tours", flush=True)
        for e in echanges:
            print(f"   {e['tour']} [{e['genre']:11s}] {e['phrase'][:62]}", flush=True)

    json.dump(resultats, open(os.path.join(os.path.dirname(__file__),
              "tetu-resultats.json"), "w"), indent=2, ensure_ascii=False, default=str)
    print("\nEcrit : bancs/tetu-resultats.json")


if __name__ == "__main__":
    main()
