"""La console, servie pour de vrai — un serveur HTTP sur la boucle locale.

Même leçon que pour le bord téléphonique : **une console qui ne se sert pas
n'est pas une console.** Le point d'entrée existe donc, et les tests vont
chercher les pages par le réseau plutôt que d'appeler les fonctions.

Le défaut d'écoute est `127.0.0.1`, volontairement : une console de commerçant
exposée sur toutes les interfaces, c'est un journal d'appels ouvert à qui passe.
Publier demande un geste explicite, et devrait passer par un accès authentifié.
"""

from __future__ import annotations

import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from standard.acces import TropDeDemandes

HOTE_PAR_DEFAUT = "127.0.0.1"
PORT_PAR_DEFAUT = 8091


class ServeurConsole:
    def __init__(self, console, hote: str = HOTE_PAR_DEFAUT, port: int = PORT_PAR_DEFAUT,
                 limiteur=None):
        self.console = console
        self.limiteur = limiteur
        self.hote = hote
        self.port = port
        self._serveur: ThreadingHTTPServer | None = None
        self._fil: threading.Thread | None = None

    def demarrer(self) -> None:
        console = self.console
        limiteur = self.limiteur

        class Poignee(BaseHTTPRequestHandler):
            def _repondre(self, methode, corps=None):
                if limiteur is not None:
                    try:
                        limiteur.autoriser(console.tenant, self.client_address[0])
                    except TropDeDemandes as refus:
                        # On refuse poliment, et on dit quand revenir : un service
                        # qui tombe parce qu'on rafraichit trop vite n'est pas
                        # exploitable.
                        self.send_response(429)
                        self.send_header("Retry-After", str(int(refus.reessayer_dans_s) + 1))
                        self.send_header("Content-Type", "text/plain; charset=utf-8")
                        message = str(refus).encode()
                        self.send_header("Content-Length", str(len(message)))
                        self.end_headers()
                        self.wfile.write(message)
                        return
                statut, entetes, contenu = console.repondre(methode, self.path, corps)
                self.send_response(statut)
                for cle, valeur in entetes.items():
                    self.send_header(cle, valeur)
                octets = contenu.encode("utf-8")
                self.send_header("Content-Length", str(len(octets)))
                self.end_headers()
                if octets:
                    self.wfile.write(octets)

            def do_GET(self):
                self._repondre("GET")

            def do_POST(self):
                longueur = int(self.headers.get("Content-Length", 0))
                brut = self.rfile.read(longueur).decode("utf-8") if longueur else ""
                corps = {cle: valeurs[0] for cle, valeurs
                         in urllib.parse.parse_qs(brut).items()}
                self._repondre("POST", corps)

            def log_message(self, *args):
                pass          # le journal d'appel est ailleurs, et mieux fait

        self._serveur = ThreadingHTTPServer((self.hote, self.port), Poignee)
        self.port = self._serveur.server_address[1]
        self._fil = threading.Thread(target=self._serveur.serve_forever, daemon=True)
        self._fil.start()

    def arreter(self) -> None:
        if self._serveur:
            self._serveur.shutdown()
            self._serveur.server_close()
        if self._fil:
            self._fil.join(timeout=2)
