#!/usr/bin/env python3
"""Le fichier de connaissance d'un salon franchit-il le seuil du cache de prompt ?

Fait etabli par la recherche (A1) : en dessous d'un prefixe de 4 096 jetons,
**rien n'est mis en cache**. Un prompt plus long peut donc couter MOINS cher
qu'un prompt court. Encore faut-il savoir ou se situe le notre — personne ne
l'avait compte.

Methode : composer le `memoire.md` reel d'un salon a partir du pack coiffure et
de donnees plausibles, l'envoyer comme prompt systeme avec `max_tokens=1`, et
lire `usage.prompt_tokens` renvoye par le fournisseur. C'est le seul compte
exact — une estimation en caracteres divises par quatre se trompe de 20 % sur du
francais accentue.

Usage : GROQ_API_KEY=... cd bancs && PYTHONPATH=. ~/bancs-stt/bin/python taille_memoire.py
"""

import http.client
import json
import os

SEUIL_CACHE = 4096

SALON = """---
salon:
  nom: Salon Elegance
  adresse: 14 rue des Lilas, 93200 Saint-Denis
horaires:
  ouverture:
    mardi: ["09:00-19:00"]
    mercredi: ["09:00-19:00"]
    jeudi: ["09:00-19:00"]
    vendredi: ["09:00-19:00"]
    samedi: ["09:00-18:00"]
  coupure: {debut: "12:30", fin: "13:30"}
agenda:
  horizon_jours: 14
prestations:
  - {id: coupe, libelle: "Coupe", duree: 30, prix: 28}
  - {id: brushing, libelle: "Brushing", duree: 45, prix: 25}
  - {id: coloration, libelle: "Coloration", duree: 90, prix: 62}
  - {id: balayage, libelle: "Balayage", duree: 135, prix: 95}
  - {id: soin, libelle: "Soin", duree: 30, prix: 18}
praticiens:
  - {nom: Sophie, prestations: [coupe, brushing, coloration, balayage]}
  - {nom: Lea, prestations: [coupe, brushing, balayage]}
  - {nom: Karim, prestations: [coupe, brushing]}
prix: {annonce: true}
reservation: {somme: aucun}
escalade: {humain: transfert, numero: "0148000000"}
annonce: {formulation: assistant_automatique}
---

# Ce qu'il faut savoir sur le salon

Le salon est ferme le lundi et le dimanche. La coupure du midi est commune a
toute l'equipe : aucun rendez-vous entre douze heures trente et treize heures
trente, y compris pour une prestation courte.

Le balayage se fait uniquement avec Sophie ou Lea, jamais avec Karim. Une
coloration demande une heure trente et ne se prend pas apres dix-sept heures
trente, parce que la pose deborderait sur la fermeture.

Les clients qui demandent « comme la derniere fois » sont frequents. Dans ce
cas, l'agent reprend la derniere prestation enregistree et la relit a voix haute
avant de la confirmer.

En cas de retard de plus de dix minutes, la prestation est raccourcie, jamais
annulee. Le salon prefere qu'on le dise au telephone plutot que de decouvrir le
retard a l'arrivee.

Le salon ne pratique pas les extensions de cheveux et n'en pose pas ; ce sont
les extensions de cils qui sont proposees, et uniquement sur rendez-vous d'une
heure. Cette distinction revient souvent au telephone.

Les tarifs affiches sont des tarifs de base : une chevelure tres longue ou tres
epaisse peut donner lieu a un supplement, que seul le coiffeur peut annoncer sur
place.

Le salon accepte la carte bancaire a partir de dix euros, les especes et les
cheques. Aucun paiement n'est demande a la reservation.

Le parking de la rue est payant jusqu'a dix-neuf heures ; il existe un parking
gratuit derriere l'eglise, a deux minutes a pied.
"""

CONSIGNES = """Tu es l'accueil telephonique du salon. Tu analyses UNE phrase
d'appelant et tu rends une proposition structuree. Tu ne rediges jamais la
reponse au client : la machine s'en charge. Tu ne confirmes rien : tu n'as acces
a aucune base. Tu n'inventes aucune date : le calendrier t'est fourni.
"""


def compter(texte, cle, modele="openai/gpt-oss-20b"):
    corps = json.dumps({
        "model": modele, "max_tokens": 1, "temperature": 0,
        "messages": [{"role": "system", "content": texte},
                     {"role": "user", "content": "."}],
    })
    conn = http.client.HTTPSConnection("api.groq.com", timeout=60)
    conn.request("POST", "/openai/v1/chat/completions", body=corps,
                 headers={"Authorization": f"Bearer {cle}", "Content-Type": "application/json",
                          "User-Agent": "marpeap-banc-taille/1.0"})
    charge = json.loads(conn.getresponse().read())
    conn.close()
    if "usage" not in charge:
        raise RuntimeError(json.dumps(charge)[:200])
    return charge["usage"]["prompt_tokens"]


def main():
    cle = os.environ["GROQ_API_KEY"]
    morceaux = {
        "consignes seules": CONSIGNES,
        "memoire.md seule": SALON,
        "prompt complet (consignes + memoire)": CONSIGNES + SALON,
    }
    resultats = {}
    for nom, texte in morceaux.items():
        n = compter(texte, cle)
        caracteres = len(texte)
        resultats[nom] = {"jetons": n, "caracteres": caracteres,
                          "caracteres_par_jeton": round(caracteres / n, 2)}
        print(f"{nom:38s} {n:5d} jetons · {caracteres:5d} caracteres · "
              f"{caracteres/n:.2f} car/jeton", flush=True)

    complet = resultats["prompt complet (consignes + memoire)"]["jetons"]
    manque = max(0, SEUIL_CACHE - complet)
    print(f"\nSeuil de cache : {SEUIL_CACHE} jetons.")
    if manque:
        print(f"Il manque {manque} jetons, soit environ "
              f"{round(manque * resultats['memoire.md seule']['caracteres_par_jeton'])} caracteres "
              f"— environ {round(manque / complet * 100)} % de plus que le prompt actuel.")
    else:
        print("Le prompt franchit le seuil : le prefixe est cachable tel quel.")
    resultats["_seuil"] = {"seuil": SEUIL_CACHE, "manque_jetons": manque}
    json.dump(resultats, open(os.path.join(os.path.dirname(__file__), "taille-memoire.json"), "w"),
              indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
