#!/usr/bin/env python3
"""Ce que l'agent dit survit-il au canal telephonique ?

Tout le projet mesure ce que l'agent ENTEND. Personne n'a mesure ce que
l'appelant, lui, recoit — alors que deux choses en dependent :

  1. **l'annonce legale** « assistant automatique » (AI Act art. 50 §1), qui doit
     etre comprise, pas seulement prononcee ;
  2. **la relecture du numero par groupes de deux**, qui est notre seul filet
     contre le mauvais SMS (docs/10, T6) — si le canal la detruit, le client ne
     peut pas verifier ce qu'il confirme.

Protocole : on synthetise la phrase de l'agent, on la fait passer par le canal
(8 kHz mu-law aller-retour), et on la fait retranscrire. Le transcripteur joue
ici le role de l'oreille de l'appelant : ce n'est pas un humain, mais un mot que
deux moteurs independants ne retrouvent pas est un mot que le canal a abime.

Usage : GROQ_API_KEY=... cd bancs && PYTHONPATH=. ~/bancs-stt/bin/python agent_audible.py
"""

import json
import os
import subprocess
import wave

from piper import PiperVoice

from wer import chiffres, distance_mots, normaliser, transcrire as transcrire_distant

SORTIE = os.path.expanduser("~/corpus-agent")

PHRASES = [
    ("annonce", "Bonjour, vous etes bien au salon Elegance. Je suis un assistant "
                "automatique, je peux prendre votre rendez-vous.",
     ["assistant", "automatique"]),
    ("annonce_courte", "Bonjour, assistant automatique du salon, je vous ecoute.",
     ["assistant", "automatique"]),
    ("relecture_numero", "Je relis votre numero : zero six, douze, trente-quatre, "
                         "cinquante-six, soixante-dix-huit. C'est bien cela ?",
     ["0612345678"]),
    ("relecture_numero_2", "Votre numero : zero sept, quatre-vingt-neuf, zero un, "
                           "vingt-trois, quarante-cinq.",
     ["0789012345"]),
    ("creneau", "Je peux vous proposer jeudi dix-sept a quinze heures trente.",
     ["jeudi", "quinze", "trente"]),
    ("creneau_2", "Il me reste neuf heures, neuf heures quarante-cinq, ou dix "
                  "heures trente.", ["neuf", "quarante", "dix"]),
    ("confirmation", "C'est enregistre : coupe et brushing, mardi quinze octobre a "
                     "dix heures.", ["mardi", "octobre", "dix"]),
    ("refus", "Nous sommes fermes entre treize heures et quatorze heures.",
     ["fermes", "treize", "quatorze"]),
    ("transfert", "Je vous passe quelqu'un du salon, un instant.",
     ["passe", "salon"]),
    ("prix", "La coupe est a vingt-huit euros, le balayage a quatre-vingt-quinze "
             "euros.", ["vingt", "huit", "euros"]),
]


def fabriquer(voix, cle, texte):
    os.makedirs(SORTIE, exist_ok=True)
    final = os.path.join(SORTIE, f"{cle}.8k.wav")
    if os.path.exists(final):
        return final
    brut = os.path.join(SORTIE, f"{cle}.wav")
    with wave.open(brut, "wb") as f:
        voix.synthesize_wav(texte, f)
    mulaw = os.path.join(SORTIE, f"{cle}.ulaw.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", brut, "-ar", "8000",
                    "-ac", "1", "-c:a", "pcm_mulaw", "-f", "wav", mulaw], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mulaw, "-ar", "8000",
                    "-ac", "1", "-c:a", "pcm_s16le", final], check=True)
    os.remove(mulaw)
    return final


def mots_retrouves(hypothese, attendus):
    n = normaliser(hypothese)
    d = chiffres(hypothese)
    manquants = []
    for attendu in attendus:
        if attendu.isdigit():
            if attendu not in d:
                manquants.append(attendu)
        elif normaliser(attendu) not in n:
            manquants.append(attendu)
    return manquants


def main():
    cle_api = os.environ["GROQ_API_KEY"]
    voix = PiperVoice.load(os.path.expanduser("~/piper/fr_FR-siwis-medium.onnx"))
    from vosk import Model, SetLogLevel
    SetLogLevel(-1)
    import wer_vosk
    modele_vosk = Model(os.path.expanduser("~/modeles/vosk-model-small-fr-0.22"))

    lignes = []
    for cle, texte, attendus in PHRASES:
        chemin = fabriquer(voix, cle, texte)
        distant, _ = transcrire_distant(chemin, cle_api, "whisper-large-v3-turbo")
        local, _, _ = wer_vosk.transcrire(chemin, modele_vosk)
        e_d, m = distance_mots(normaliser(texte), normaliser(distant))
        e_l, _ = distance_mots(normaliser(texte), normaliser(local))
        manque_d = mots_retrouves(distant, attendus)
        manque_l = mots_retrouves(local, attendus)
        lignes.append({"cle": cle, "texte": texte,
                       "distant": distant.strip(), "local": local.strip(),
                       "wer_distant": round(100 * e_d / m, 1),
                       "wer_local": round(100 * e_l / m, 1),
                       "manquants_distant": manque_d, "manquants_local": manque_l})
        print(f"{cle:18s} WER distant {100*e_d/m:5.1f} % · local {100*e_l/m:5.1f} % · "
              f"manquants: {manque_d or '-'} / {manque_l or '-'}", flush=True)

    critiques = [l for l in lignes if l["manquants_distant"] or l["manquants_local"]]
    resume = {"phrases": len(lignes),
              "phrases_avec_mot_cle_perdu": len(critiques),
              "perdu_chez_les_deux": sum(1 for l in lignes
                                         if l["manquants_distant"] and l["manquants_local"])}
    json.dump({"resume": resume, "detail": lignes},
              open(os.path.join(os.path.dirname(__file__), "agent-audible-resultats.json"), "w"),
              indent=2, ensure_ascii=False)
    print("\n" + json.dumps(resume, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
