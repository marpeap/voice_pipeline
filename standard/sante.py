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
        "appels_refuses": getattr(serveur, "appels_refuses", 0),
        "lignes_rendues": getattr(serveur, "lignes_rendues", 0),
        "appels_simultanes_max": getattr(serveur, "appels_simultanes_max", None),
    }
    if service is not None:
        etat.update(service.supervision())
    if entretien is not None:
        etat["entretien"] = {**entretien.etat(), "vivant": entretien.vivant}

    # Un mot, pas quinze chiffres : personne n'ecrit une sonde qui compare
    # quinze nombres, et personne ne les relit a trois heures du matin. Les
    # chiffres restent pour comprendre, le mot sert a alerter.
    etat["raisons"] = _ce_qui_ne_va_pas(etat, serveur)
    etat["etat"] = _resumer(etat)
    return etat


def _ce_qui_ne_va_pas(etat: dict, serveur) -> list:
    """Les raisons, en francais, dans l'ordre de gravite."""
    raisons = []
    if not etat.get("port_audiosocket"):
        raisons.append("le standard n'écoute aucun port : aucun appel ne peut arriver")
    if etat.get("confirmations_orphelines"):
        # Cible zero : toute occurrence est un incident, pas une statistique.
        raisons.append(f"{etat['confirmations_orphelines']} confirmation(s) "
                       "orpheline(s) — un client s'organise sur un rendez-vous "
                       "qui n'existe pas")
    entretien = etat.get("entretien") or {}
    if entretien and not entretien.get("vivant"):
        raisons.append("le ménage est arrêté : la durée de conservation annoncée "
                       "au registre devient fausse")
    if etat.get("pannes_pendant_appel"):
        raisons.append(f"{etat['pannes_pendant_appel']} panne(s) pendant un appel")
    if etat.get("archivages_perdus"):
        raisons.append(f"{etat['archivages_perdus']} appel(s) que le journal n'a "
                       "pas voulu : la trace est perdue")
    if etat.get("paroles_perdues"):
        raisons.append(f"{etat['paroles_perdues']} phrase(s) fabriquée(s) que "
                       "l'appelant n'a pas entendue(s)")
    if getattr(getattr(serveur, "sante", None), "erreur", None):
        raisons.append(getattr(serveur.sante, "erreur"))
    return raisons


def _resumer(etat: dict) -> str:
    """`ok`, `dégradé`, `en panne` — et rien d'autre : trois mots se surveillent."""
    if not etat.get("port_audiosocket"):
        return "en panne"
    return "dégradé" if etat.get("raisons") else "ok"


class ServeurDeSante:
    """Un point `GET /sante`, sur la boucle locale par defaut."""

    def __init__(self, source, hote: str = HOTE_PAR_DEFAUT, port: int = PORT_PAR_DEFAUT):
        self.source = source
        self.hote = hote
        self.port = port
        self._serveur: ThreadingHTTPServer | None = None
        self._fil: threading.Thread | None = None
        # Ce qui a empeche le point d'etat de s'ouvrir, s'il y a lieu. Il n'y a
        # pas de raison de refuser de decrocher parce qu'un port de diagnostic
        # est pris — deux salons sur une machine, une mesure qui tourne encore,
        # et le standard entier serait reste muet.
        self.erreur: str | None = None

    def demarrer(self) -> None:
        if self._serveur is not None:
            return
        source = self.source

        class Poignee(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path.startswith("/appelant/"):
                    # Le plan de numerotation depose l'identifiant d'appelant
                    # AVANT de brancher l'audio : AudioSocket ne le transporte
                    # pas, et l'agent ne peut pas le lire sur un ecran. Quand il
                    # est la, ne pas s'en servir coute deux tours par appel.
                    from urllib.parse import parse_qs, urlsplit

                    decoupe = urlsplit(self.path)
                    identifiant = decoupe.path[len("/appelant/"):].strip("/")
                    numero = (parse_qs(decoupe.query).get("numero") or [""])[0]
                    retenu = source.retenir_le_numero(identifiant, numero) \
                        if hasattr(source, "retenir_le_numero") else False
                    octets = (b"ok" if retenu else b"ignore")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.send_header("Content-Length", str(len(octets)))
                    self.end_headers()
                    self.wfile.write(octets)
                    return
                if self.path.startswith("/issue/"):
                    # Le plan de numerotation demande comment l'appel s'est
                    # termine : « transfert » le renvoie au poste du salon,
                    # « demarchage » ou « fin » raccrochent. Une reponse en
                    # texte brut, parce qu'un dialplan ne lit pas du JSON.
                    identifiant = self.path[len("/issue/"):].strip("/")
                    issue = getattr(source, "issues", {}).get(identifiant, "inconnu")
                    octets = issue.encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("Content-Length", str(len(octets)))
                    self.end_headers()
                    self.wfile.write(octets)
                    return
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

        try:
            self._serveur = ThreadingHTTPServer((self.hote, self.port), Poignee)
        except OSError as erreur:
            self.erreur = f"point d'état indisponible sur {self.hote}:{self.port} — {erreur}"
            print(self.erreur, flush=True)
            self._serveur = None
            return
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
