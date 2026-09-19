"""Le point d'état — le seul moyen qu'a une machine de savoir que ça tourne.

Un standard téléphonique tourne sans écran. Sans ce point, l'exploitant apprend
que le service est tombé par un commerçant qui l'appelle : c'est la définition
d'un service non exploitable, et c'est ce qui manquait au dépôt.

Ce qu'il porte vient des mesures, pas d'une habitude :
- **le délai avant premier fragment** dit qu'une machine est pleine bien avant
  la charge processeur (mesure 13) ;
- **toute confirmation orpheline est un incident**, cible zéro (docs/07) ;
- les paroles perdues, pannes et archivages perdus disent ce qui s'est abîmé
  en silence pendant les appels.

Il ne porte **aucune donnée d'appelant** : il est joignable sans jeton, donc il
ne dit que des compteurs — jamais un nom, un numéro ou une transcription.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOTE_PAR_DEFAUT = "127.0.0.1"
PORT_PAR_DEFAUT = 8092


def etat_du_serveur(serveur) -> dict:
    """Les chiffres du serveur et de ce qu'il porte, sans rien d'autre."""
    service = getattr(serveur, "service", None)
    entretien = getattr(serveur, "entretien", None)
    etat = {
        "vivant": True,
        "port_audiosocket": serveur.port,
        "appels_en_cours": getattr(serveur, "appels_en_cours", 0),
        "interruptions": getattr(serveur, "interruptions_totales", 0),
        "paroles_perdues": getattr(serveur, "paroles_perdues", 0),
        "pannes_pendant_appel": getattr(serveur, "pannes_pendant_appel", 0),
        "archivages_perdus": getattr(serveur, "archivages_perdus", 0),
        "demarchages_filtres": getattr(serveur, "demarchages_filtres", 0),
    }
    if service is not None:
        etat.update(service.supervision())
    if entretien is not None:
        etat["entretien"] = {**entretien.etat(), "vivant": entretien.vivant}
    return etat


class ServeurDeSante:
    """Un point `GET /sante`, sur la boucle locale par defaut."""

    def __init__(self, source, hote: str = HOTE_PAR_DEFAUT, port: int = PORT_PAR_DEFAUT):
        self.source = source
        self.hote = hote
        self.port = port
        self._serveur: ThreadingHTTPServer | None = None
        self._fil: threading.Thread | None = None

    def demarrer(self) -> None:
        if self._serveur is not None:
            return
        source = self.source

        class Poignee(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path.rstrip("/") not in ("/sante", "/health"):
                    self.send_response(404)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                try:
                    corps = json.dumps(etat_du_serveur(source), ensure_ascii=False)
                    statut = 200
                except Exception as erreur:
                    # Un point d'etat qui tombe en meme temps que ce qu'il
                    # observe ne sert a rien : il repond quand meme, et il dit
                    # quoi.
                    corps = json.dumps({"vivant": False, "erreur": str(erreur)})
                    statut = 503
                octets = corps.encode("utf-8")
                self.send_response(statut)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(octets)))
                self.end_headers()
                self.wfile.write(octets)

            def log_message(self, *_):
                pass                      # le journal d'appels suffit

        self._serveur = ThreadingHTTPServer((self.hote, self.port), Poignee)
        self.port = self._serveur.server_address[1]
        self._fil = threading.Thread(target=self._serveur.serve_forever,
                                     name="sante", daemon=True)
        self._fil.start()

    def arreter(self, delai_s: float = 2.0) -> None:
        if self._serveur is None:
            return
        self._serveur.shutdown()
        self._serveur.server_close()
        if self._fil is not None:
            self._fil.join(timeout=delai_s)
        self._serveur, self._fil = None, None
