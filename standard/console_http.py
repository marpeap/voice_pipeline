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
NOM_DU_COOKIE = "acces_console"


class ServeurConsole:
    def __init__(self, console, hote: str = HOTE_PAR_DEFAUT, port: int = PORT_PAR_DEFAUT,
                 limiteur=None, trousseau=None, portee: str | None = None):
        self.console = console
        self.limiteur = limiteur
        # Sans trousseau, la console reste ouverte : c'est le mode d'essai, et
        # elle n'ecoute alors que la boucle locale. Des qu'on l'expose, le
        # trousseau devient obligatoire — elle montre des transcriptions, des
        # noms et des numeros de clients.
        self.trousseau = trousseau
        self.portee = portee
        self.hote = hote
        self.port = port
        self._serveur: ThreadingHTTPServer | None = None
        self._fil: threading.Thread | None = None

    def demarrer(self) -> None:
        console = self.console
        limiteur = self.limiteur
        trousseau = self.trousseau
        portee = self.portee

        class Poignee(BaseHTTPRequestHandler):
            def _cle_presentee(self):
                """La cle, d'ou qu'elle vienne — en-tete, lien, ou cookie.

                Un gerant ne colle pas un en-tete HTTP : il ouvre un lien. La
                cle y passe donc une fois, puis un cookie prend le relais pour
                qu'elle ne reste pas dans l'historique du navigateur.
                """
                entete = self.headers.get("Authorization", "")
                if entete.startswith("Bearer "):
                    return entete[len("Bearer "):].strip(), False
                depuis_l_url = urllib.parse.parse_qs(
                    urllib.parse.urlsplit(self.path).query).get("cle")
                if depuis_l_url:
                    return depuis_l_url[0], True
                for morceau in self.headers.get("Cookie", "").split(";"):
                    nom, _, valeur = morceau.strip().partition("=")
                    if nom == NOM_DU_COOKIE:
                        return valeur, False
                return None, False

            def _refuser(self):
                # Un refus ne dit rien de ce qu'il protege : ni le locataire, ni
                # le nombre d'appels, ni la raison exacte.
                message = ("Accès refusé. Ouvrez la console avec le lien qui "
                           "porte votre clé.").encode("utf-8")
                self.send_response(401)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(message)))
                self.end_headers()
                self.wfile.write(message)

            def _autorise(self) -> bool:
                if trousseau is None:
                    return True
                secret, poser_le_cookie = self._cle_presentee()
                if not secret:
                    self._refuser()
                    return False
                try:
                    trousseau.verifier(secret, portee)
                except Exception:
                    self._refuser()
                    return False
                self._cookie_a_poser = secret if poser_le_cookie else None
                return True

            def _repondre(self, methode, corps=None):
                if not self._autorise():
                    return
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
                chemin = urllib.parse.urlsplit(self.path).path
                statut, entetes, contenu = console.repondre(methode, chemin, corps)
                self.send_response(statut)
                if getattr(self, "_cookie_a_poser", None):
                    self.send_header("Set-Cookie",
                                     f"{NOM_DU_COOKIE}={self._cookie_a_poser}; "
                                     "HttpOnly; SameSite=Strict; Path=/")
                    self._cookie_a_poser = None
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
