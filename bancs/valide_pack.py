#!/usr/bin/env python3
"""Verifie qu'un pack sectoriel respecte les cinq regles de format de docs/05.

Les packs sont de la donnee, pas du code — mais une donnee fausse produit un
agent faux, et en silence. Ce validateur est donc le premier test du produit,
et il tourne avant meme qu'il existe.

Usage : python3 bancs/valide_pack.py packs/*.json
"""

import json
import sys


def questions(pack):
    for bloc in pack.get("blocs", []):
        for q in bloc.get("questions", []):
            yield bloc["id"], q


def valide(chemin):
    pack = json.load(open(chemin))
    fautes = []

    for bloc_id, q in questions(pack):
        ident = f"{bloc_id}/{q.get('id', '?')}"
        options = q.get("options", [])

        # Regle 1 — au plus 5 options, et toujours un defaut.
        if len(options) > 5:
            fautes.append(f"{ident} : {len(options)} options, maximum 5")
        # Un choix multiple peut legitimement n'avoir rien de coche — mais il doit
        # le DIRE (`defaut_vide`), sinon on ne distingue pas l'intention de l'oubli.
        if options and not any(o.get("defaut") for o in options):
            if q.get("type") == "choix_multiple" and q.get("defaut_vide"):
                pass
            else:
                fautes.append(f"{ident} : aucune option par defaut — un commercant qui "
                              "ne repond rien doit obtenir un agent qui fonctionne "
                              "(un choix multiple sans defaut doit porter \"defaut_vide\": true)")

        # Regle 2 — toute reponse va quelque part.
        if "ecrit" not in q:
            fautes.append(f"{ident} : pas de cible 'ecrit' — la reponse irait nulle part")
        elif q["ecrit"].get("cible") not in ("frontmatter", "corps"):
            fautes.append(f"{ident} : cible '{q['ecrit'].get('cible')}' inconnue")

        # Regle 3 — le branchement ne descend que d'un niveau.
        for o in options:
            if "ouvre" in o and any("ouvre" in c for c in o.get("champs", [])):
                fautes.append(f"{ident} : deux niveaux de branchement")

    # Regle 4 — l'annonce existe, et elle n'est pas desactivable.
    annonce = [q for _, q in questions(pack) if q.get("id") == "E3"]
    if not annonce:
        fautes.append("pack : aucune question d'annonce (E3) — obligation AI Act art. 50")
    elif not annonce[0].get("obligatoire_non_desactivable"):
        fautes.append("E3 : l'annonce doit etre marquee non desactivable")

    # Regle 5 — le vocabulaire specialise est indexe par prestation.
    g3 = pack.get("keyterms", {}).get("groupe3")
    if not isinstance(g3, dict):
        fautes.append("keyterms.groupe3 : doit etre indexe par prestation, "
                      "pour ne pas deverser tout le lexique du metier")

    return pack, fautes


if __name__ == "__main__":
    total = 0
    for chemin in sys.argv[1:]:
        pack, fautes = valide(chemin)
        n = sum(1 for _ in questions(pack))
        critiques = sum(1 for _, q in questions(pack) if q.get("critique"))
        etat = "OK" if not fautes else f"{len(fautes)} faute(s)"
        print(f"{pack['pack']:20s} {n:2d} questions ({critiques} critiques) · {etat}")
        for f in fautes:
            print(f"   - {f}")
        total += len(fautes)
    sys.exit(1 if total else 0)
