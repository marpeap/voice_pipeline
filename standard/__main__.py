"""Point d'entrée : `python -m standard`.

    python -m standard verifier   # dit si le service peut décrocher
    python -m standard servir     # écoute les appels d'Asterisk
    python -m standard console    # la console du commerçant, sur la boucle locale
"""

from __future__ import annotations

import json
import signal
import sys
import threading

from standard.demarrage import construire_serveur, verifier_le_deploiement


def main(arguments: list[str]) -> int:
    commande = arguments[0] if arguments else "verifier"

    if commande == "verifier":
        rapport = verifier_le_deploiement()
        print(json.dumps(rapport, indent=2, ensure_ascii=False))
        return 0 if rapport["pret"] else 1

    if commande == "servir":
        serveur = construire_serveur()
        serveur.demarrer()
        print(f"en écoute sur {serveur.hote}:{serveur.port}", flush=True)

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
        config = configuration_depuis_environnement()
        journal = JournalDAppels(Depot(os.environ.get("STANDARD_BASE", "standard.sqlite3")))
        serveur = ServeurConsole(Console(journal=journal, tenant=config.tenant),
                                 port=int(os.environ.get("STANDARD_PORT_CONSOLE", "8091")))
        serveur.demarrer()
        print(f"console sur http://{serveur.hote}:{serveur.port}", flush=True)
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
