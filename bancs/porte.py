#!/usr/bin/env python3
"""La porte de non-regression — elle rejoue les fautes mesurees contre le produit.

`bancs/porte.json` dit ce qu'il faut verifier et d'ou vient chaque cas ; ce
script l'execute. Rien n'y est simule au hasard : les scenarios sont ceux des
mesures 7, 14, 15, 16, 17, 18 et 19, et le modele de test se comporte comme celui
qui a faute.

Deux regles de comptage, ecrites dans le fichier de donnees :
  - **pass^5** : chaque scenario est rejoue cinq fois et le succes doit etre
    INTEGRAL. Un scenario reussi quatre fois sur cinq est un scenario echoue —
    la demonstration mesure pass^1, le commerce mesure pass^k.
  - **deux passages d'affilee** : le lot n'est fini que si la porte passe deux
    fois de suite.

Usage :
    .venv/bin/python bancs/porte.py            # un passage
    .venv/bin/python bancs/porte.py --passages 2
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)

from standard.appel import Appel                     # noqa: E402
from standard.decision import Agenda, enoncer_date   # noqa: E402
from standard.grammaire import enoncer_numero, lire_numero  # noqa: E402

MARDI = date(2026, 9, 15)
from standard.regles import VERBES_DE_CONFIRMATION as INTERDITS  # noqa: E402


class ModeleScripte:
    """Un fournisseur de test : il rend ce qu'on lui a dit de rendre."""

    def __init__(self, reponses):
        self.reponses = list(reponses)
        self.appels = 0

    def completer(self, messages, **parametres):
        charge = self.reponses[min(self.appels, len(self.reponses) - 1)]
        self.appels += 1
        return json.dumps({"prestation": None, "manque": [],
                           "confiance": {"intention": 0.95, "date": 0.95, "heure": 0.95},
                           **charge})


class BaseFactice:
    def __init__(self, muette=False):
        self.lignes, self.par_cle, self.muette = {}, {}, muette

    def inserer(self, cle, donnees):
        if cle in self.par_cle:
            return self.par_cle[cle]
        reference = f"rdv-{len(self.lignes) + 1:04d}"
        self.lignes[reference] = dict(donnees)
        self.par_cle[cle] = reference
        return reference

    def relire(self, reference):
        return None if self.muette else self.lignes.get(reference)


def agenda():
    return Agenda(aujourd_hui=MARDI, horizon_jours=14, jours_fermes=(6, 0),
                  creneaux={"09:00", "09:45", "10:30", "11:15",
                            "14:00", "14:45", "15:30", "16:15", "17:00"})


def appel(reponses, base=None):
    return Appel(client_modele=ModeleScripte(reponses), agenda=agenda(),
                 base=base or BaseFactice(), memoire="# Salon\n",
                 consignes_communes="Consignes. " * 40,
                 tenant="porte", identifiant="appel")


# --- les familles, chacune rendant (succes, detail) -------------------------

def famille_confirmation_orpheline():
    """Mesure 14 : « c'est note » et « votre rendez-vous est annule » sur du vide."""
    conversation = appel([{"intention": "rdv", "date": "2026-09-15", "heure": "18:15"},
                          {"intention": "annulation"}])
    phrases = [conversation.tour("MARDI DIX SEPT À DIX HUIT HEURES QUINZ").phrase,
               conversation.tour("DOIS ANNULER MON RENDEZ VOUS DE DEMAIN MATIN").phrase,
               conversation.confirmer().phrase]
    fautives = [p for p in phrases if any(m in p.lower() for m in INTERDITS)]
    return not fautives, fautives


def famille_entite_inventee():
    """Mesure 14 : « neuf heures moins le quart » devenu 9 h 15."""
    conversation = appel([{"intention": "rdv", "date": "2026-09-19", "heure": "09:15"}])
    reponse = conversation.tour("SAMEDI NEUF HEURES MOIS LE QUART CAR VOUS IREZ")
    return "9 h 15" not in reponse.phrase, reponse.phrase


def famille_absence_prise_pour_information():
    """Mesure 15 : une date hors horizon n'est jamais « ferme »."""
    conversation = appel([{"intention": "rdv", "date": "2026-12-24", "heure": "11:00"}])
    reponse = conversation.tour("VINGT QUATRE DÉCEMBRE À ONZE HEUR")
    return (reponse.genre == "hors horizon" and "fermé" not in reponse.phrase.lower()), reponse.phrase


def famille_boucle():
    """Mesures 16 a 18 : trois appelants, trois issues attendues."""
    resultats = []

    # 1. insiste puis cede : doit aboutir
    conversation = appel([{"intention": "rdv", "date": "2026-09-17", "heure": "18:30"},
                          {"intention": "rdv", "date": "2026-09-17", "heure": "18:30"},
                          {"intention": "rdv", "date": "2026-09-17", "heure": "15:30"}])
    genres = [conversation.tour("samedi dix-huit heures trente").genre for _ in range(3)]
    resultats.append(("insiste puis cede", genres[-1] == "proposition", genres))

    # 2. insiste toujours : doit etre transfere, jamais boucler
    conversation = appel([{"intention": "rdv", "date": "2026-09-17", "heure": "18:30"}])
    genres = [conversation.tour("samedi dix-huit heures trente").genre for _ in range(5)]
    resultats.append(("insiste toujours", "transfert" in genres, genres))

    # 3. demande un humain : transfert immediat, sans appel au modele
    modele = ModeleScripte([{"intention": "rdv"}])
    conversation = Appel(client_modele=modele, agenda=agenda(), base=BaseFactice(),
                         memoire="", consignes_communes="c", tenant="p", identifiant="a")
    reponse = conversation.tour("passez-moi quelqu'un s'il vous plait")
    resultats.append(("demande un humain",
                      reponse.genre == "transfert" and modele.appels == 0, reponse.genre))

    echecs = [nom for nom, ok, _ in resultats if not ok]
    return not echecs, resultats


def famille_numero():
    """Mesures 7 et 21 : les quatre echecs reels, plus les regles T1 a T10."""
    cas = [
        ("zero six douze trente-quatre cinquante-six soixante-dix-huit", "accepte", "0612345678"),
        ("01 40 3 22 11 09", "accepte", "0143221109"),
        ("zero six douze quatorze non quinze quarante soixante", "accepte", "0612154060"),
        ("zero six pardon zero sept douze trente-quatre cinquante-six soixante-dix-huit",
         "accepte", "0712345678"),
        ("plus trente-trois six douze trente-quatre cinquante-six soixante-dix-huit",
         "accepte", "0612345678"),
        ("zero huit douze trente-quatre cinquante-six", "refus", None),
        ("zero six douze trente-quatre cinquante-six", "relecture", None),
    ]
    echecs = []
    for dit, issue, attendu in cas:
        lecture = lire_numero(dit)
        if lecture.issue != issue or (attendu and lecture.numero != attendu):
            echecs.append({"dit": dit, "attendu": (issue, attendu),
                           "obtenu": (lecture.issue, lecture.numero)})
    return not echecs, echecs


def famille_parole_de_l_agent():
    """Mesure 19 : E1 (jour + quantieme + mois) et la relecture par groupes de deux."""
    echecs = []
    dit = enoncer_date("2026-09-17")
    if "jeudi" not in dit or "septembre" not in dit:
        echecs.append({"regle": "E1", "obtenu": dit})
    relu = enoncer_numero("0612345678")
    if relu.count(",") != 4:
        echecs.append({"regle": "relecture par groupes de deux", "obtenu": relu})
    return not echecs, echecs


FAMILLES = {
    "confirmation_orpheline": famille_confirmation_orpheline,
    "entite_inventee": famille_entite_inventee,
    "absence_prise_pour_information": famille_absence_prise_pour_information,
    "boucle": famille_boucle,
    "numero": famille_numero,
    "parole_de_l_agent": famille_parole_de_l_agent,
}


def familles_de_corrections(registre):
    """Chaque correction active devient une famille de la porte.

    `docs/06` : « toute correction alimente automatiquement le corpus de
    regression ». Le registre savait rendre ces scenarios, la porte ne les
    jouait pas — la console promettait donc au gerant une garantie qui n'existait
    pas : sans rejeu, une correction tient jusqu'au prochain changement de
    modele, et personne ne voit la rechute.
    """
    from datetime import date as _date

    from standard.correction import appliquer
    from standard.hors_ligne import ModeleHorsLigne
    from standard.service import Configuration, Service

    familles = {}
    for scenario in registre.scenarios_de_regression():
        corrections = [registre.par_identifiant(scenario["identifiant"])]

        def executer(scenario=scenario, corrections=corrections):
            attendu = scenario["attendu"] or {}
            if scenario["faute"] == "creneau_inexistant":
                heure = attendu.get("heure")
                if not heure:
                    return False, "correction sans creneau : rien a verifier"
                service = _service_avec(corrections, heure)
                jour = "2026-09-17"
                libres = service._agenda().libres(jour)
                return (heure not in libres,
                        f"le creneau {heure} est encore propose : {libres}")

            if scenario["faute"] == "promesse_interdite":
                interdit = attendu.get("interdit")
                if not interdit:
                    return False, "correction sans interdit : rien a verifier"
                service = _service_avec(corrections, "15:30")
                appel = service.nouvel_appel("regression")
                dite = appel._appel._garde_de_sortie(f"Je peux vous {interdit}.")
                return (interdit not in dite.lower(),
                        f"la phrase interdite est sortie : {dite!r}")

            # Les autres fautes agissent sur la memoire : on verifie qu'elles y
            # sont bien appliquees, ce qui est ce qu'elles promettent.
            reponses, corps, _ = appliquer(corrections, {}, "")
            trace = json.dumps({"reponses": reponses, "corps": corps}, ensure_ascii=False)
            valeurs = [str(v) for v in attendu.values() if v]
            if not valeurs:
                return False, "correction sans valeur : rien a verifier"
            manquantes = [v for v in valeurs if v not in trace]
            return (not manquantes, f"non applique : {manquantes}")

        familles[f"correction {scenario['identifiant']} ({scenario['faute']})"] = executer
    return familles


def _service_avec(corrections, heure):
    """Un service minimal portant ces corrections — assez pour les verifier."""
    from standard.correction import RegistreDeCorrections
    from standard.depot import Depot
    from standard.hors_ligne import ModeleHorsLigne
    from standard.service import Configuration, Service

    pack = json.load(open(os.path.join(RACINE, "packs", "coiffure.json")))
    depot = Depot(":memory:")

    class RegistreFige:
        def actives(self_inner):
            return corrections

    config = Configuration(tenant="regression", pack=pack,
                           reponses={"A1": "Salon"}, aujourd_hui=MARDI,
                           creneaux=(heure, "15:30", "17:00"))
    service = Service(config, client_modele=ModeleHorsLigne(aujourd_hui=MARDI),
                      base=depot.pour("regression"), corrections=RegistreFige())
    service.demarrer()
    return service


def un_passage(repetitions: int = 5, bavard: bool = True, registre=None):
    """Rejoue chaque famille `repetitions` fois. Le succes doit etre integral."""
    resultats = []
    familles = dict(FAMILLES)
    if registre is not None:
        familles.update(familles_de_corrections(registre))
    for nom, executer in familles.items():
        succes, echecs = 0, []
        for _ in range(repetitions):
            ok, detail = executer()
            succes += 1 if ok else 0
            if not ok:
                echecs.append(detail)
        integral = succes == repetitions
        resultats.append({"famille": nom, "succes": succes, "sur": repetitions,
                          "integral": integral, "echecs": echecs[:2]})
        if bavard:
            marque = "OK " if integral else "ECHEC"
            print(f"  {marque} {nom:34s} {succes}/{repetitions}")
            for echec in echecs[:1]:
                print(f"        {echec}")
    return resultats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repetitions", type=int, default=5, help="pass^k, cinq par defaut")
    ap.add_argument("--passages", type=int, default=1,
                    help="le lot n'est fini que si la porte passe deux fois d'affilee")
    ap.add_argument("--base", default=None,
                    help="la base d'un salon : ses corrections deviennent des familles")
    ap.add_argument("--tenant", default="salon-1")
    args = ap.parse_args()

    registre = None
    if args.base:
        from standard.correction import RegistreDeCorrections
        from standard.depot import Depot

        registre = RegistreDeCorrections(depot=Depot(args.base), tenant=args.tenant)
        print(f"{len(registre.actives())} correction(s) rejouee(s) depuis {args.base}")

    definition = json.load(open(os.path.join(os.path.dirname(__file__), "porte.json")))
    declarees = {f["nom"] for f in definition["familles"]}
    non_couvertes = declarees - set(FAMILLES) - {"bruit", "latence"}
    if non_couvertes:
        print(f"Familles declarees mais non executees : {sorted(non_couvertes)}")

    tous = []
    for passage in range(1, args.passages + 1):
        print(f"Passage {passage} sur {args.passages} — pass^{args.repetitions}")
        tous.append(un_passage(args.repetitions, registre=registre))

    echecs = [r for passage in tous for r in passage if not r["integral"]]
    json.dump({"passages": tous}, open(os.path.join(os.path.dirname(__file__),
              "porte-resultats.json"), "w"), indent=2, ensure_ascii=False, default=str)
    print("\nLes familles « bruit » et « latence » ne s'executent pas ici : "
          "elles demandent l'audio et un service qui tourne (bancs/bruit.py, mesure 13).")
    if echecs:
        print(f"PORTE FERMEE — {len(echecs)} famille(s) en echec.")
        return 1
    print(f"PORTE OUVERTE — {args.passages} passage(s), pass^{args.repetitions}, tout integral.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
