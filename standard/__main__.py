"""Point d'entrée : `python -m standard`.

    python -m standard verifier   # dit si le service peut décrocher
    python -m standard servir     # écoute les appels d'Asterisk
    python -m standard console    # la console du commerçant, sur la boucle locale
    python -m standard registre   # le registre des traitements (RGPD art. 30)
"""

from __future__ import annotations

import json
import signal
import sys
import threading

from standard.demarrage import construire_serveur, verifier_le_deploiement


def main(arguments: list[str]) -> int:
    """Le point d'entree, et le seul endroit qui traduit une erreur en message.

    Une trace Python de neuf lignes n'aide personne a sept heures du matin
    devant un service qui ne demarre pas : une configuration incomplete se dit
    en une phrase, avec le nom des variables qui manquent.
    """
    try:
        return _executer(arguments)
    except ValueError as manque:
        print(f"configuration incomplète : {manque}", file=sys.stderr)
        print("voir `deploiement/standard.service` et docs/24-EXPLOITATION.md",
              file=sys.stderr)
        return 1
    except FileNotFoundError as absent:
        print(f"fichier introuvable : {absent}", file=sys.stderr)
        return 1


def _cle_fournie(trousseau, tenant: str, secret: str):
    """Inscrit une cle choisie par l'exploitant, sans jamais la reafficher."""
    import time

    from standard.acces import Cle, _empreinte

    trousseau._compteur += 1
    return Cle(identifiant=f"cle-{trousseau._compteur:04d}", tenant=tenant,
               empreinte=_empreinte(secret), portees=("console",),
               emise_le=time.time())


def _executer(arguments: list[str]) -> int:
    commande = arguments[0] if arguments else "verifier"

    if commande == "verifier":
        rapport = verifier_le_deploiement()
        print(json.dumps(rapport, indent=2, ensure_ascii=False))
        return 0 if rapport["pret"] else 1

    if commande == "registre":
        # Derive de la configuration qui tourne : un registre recopie a la main
        # devient faux au premier changement de moteur.
        from standard.registre import registre_des_traitements, rendre_en_texte

        registre = registre_des_traitements()
        if "--json" in arguments:
            print(json.dumps(registre, indent=2, ensure_ascii=False))
        else:
            print(rendre_en_texte(registre))
        return 0

    if commande == "servir":
        serveur = construire_serveur()
        serveur.demarrer()
        print(f"en écoute sur {serveur.hote}:{serveur.port}", flush=True)
        sante = getattr(serveur, "sante", None)
        if sante is not None:
            print(f"état sur http://{sante.hote}:{sante.port}/sante", flush=True)

        arret = threading.Event()
        # Un arret propre : les appels en cours se terminent, aucun n'est coupe
        # au milieu d'une phrase.
        for signal_recu in (signal.SIGINT, signal.SIGTERM):
            signal.signal(signal_recu, lambda *_: arret.set())
        arret.wait()
        print("arrêt demandé, fermeture…", flush=True)
        serveur.arreter()
        return 0

    if commande == "console":
        from standard.console import Console
        from standard.console_http import ServeurConsole
        from standard.demarrage import configuration_depuis_environnement
        from standard.depot import Depot
        from standard.journal import JournalDAppels

        import os

        from standard.acces import Cles, Limiteur
        from standard.audit import PisteDAudit

        config = configuration_depuis_environnement()
        depot = Depot(os.environ.get("STANDARD_BASE", "standard.sqlite3"))
        journal = JournalDAppels(depot)
        # Qui a pose quelle correction, et un debit borne : les deux existaient
        # sans etre branches, ce qu'une revue independante a releve.
        console = Console(journal=journal, tenant=config.tenant,
                          # Sans le pack, l'ecran de reglages n'existe pas en
                          # production : le commercant ne peut pas configurer son
                          # agent, et le produit ne se vend pas seul (docs/05).
                          pack=config.pack,
                          depot=depot,          # sans lui, les messages pris
                          audit=PisteDAudit(depot),
                          acteur=os.environ.get("STANDARD_ACTEUR", "console"))
        # La console montre des transcriptions, des noms et des numeros de
        # clients. Des qu'elle sort de la boucle locale, elle exige une cle ;
        # sur 127.0.0.1 on laisse le mode d'essai ouvert, sans quoi personne ne
        # l'essaie et elle finit exposee sans cle du tout.
        hote = os.environ.get("STANDARD_HOTE_CONSOLE", "127.0.0.1")
        trousseau, secret = None, None
        if hote not in ("127.0.0.1", "localhost", "::1"):
            trousseau = Cles()
            secret = os.environ.get("STANDARD_CONSOLE_CLE")
            if secret:
                # Une cle fournie par l'exploitant : on l'inscrit telle quelle,
                # sans jamais la reafficher.
                trousseau._cles.append(_cle_fournie(trousseau, config.tenant, secret))
            else:
                secret = trousseau.emettre(config.tenant, ["console"])

        serveur = ServeurConsole(console, hote=hote, limiteur=Limiteur(),
                                 trousseau=trousseau, portee="console",
                                 port=int(os.environ.get("STANDARD_PORT_CONSOLE", "8091")))
        serveur.demarrer()
        adresse = f"http://{serveur.hote}:{serveur.port}"
        if trousseau is not None and not os.environ.get("STANDARD_CONSOLE_CLE"):
            # Affichee UNE fois, au demarrage : elle n'est stockee qu'en
            # empreinte, personne ne pourra la relire.
            print(f"console sur {adresse}/?cle={secret}", flush=True)
            print("cette clé ne sera plus affichée", flush=True)
        else:
            print(f"console sur {adresse}", flush=True)
        arret = threading.Event()
        for signal_recu in (signal.SIGINT, signal.SIGTERM):
            signal.signal(signal_recu, lambda *_: arret.set())
        arret.wait()
        serveur.arreter()
        return 0

    print(f"commande inconnue : {commande}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
