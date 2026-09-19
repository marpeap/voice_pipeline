"""Le client du modèle de langage — celui qui manquait au chemin réel.

Une seconde revue indépendante a trouvé le 19/09 qu'**aucun client HTTP de
modèle n'existait dans le dépôt** : le service câblait toujours le moteur hors
ligne, et la commande de vérification annonçait pourtant le modèle configuré. Un
rapport de déploiement qui dit autre chose que ce qui tourne est pire que pas de
rapport.

Trois règles, toutes tirées des mesures :

- **La connexion est ouverte une fois et gardée** (mesure 4 : 2 040 ms pour une
  connexion neuve contre 378 ms pour une connexion maintenue — c'est le premier
  levier de latence, et il est gratuit).
- **Le nom du modèle et ses paramètres viennent d'ailleurs** (mesure 17 : le
  catalogue a bougé trois fois en quarante-huit heures, et le remplaçant
  refusait un paramètre que le précédent acceptait).
- **L'erreur du fournisseur remonte avec son message** (même mesure : un
  `KeyError` muet a coûté trois quarts d'heure là où la réponse disait
  exactement ce qui n'allait pas).
"""

from __future__ import annotations

import json
from typing import Any

CHEMIN_COMPLETIONS = "/chat/completions"
DELAI_S = 8.0


class ErreurModele(RuntimeError):
    """Ce que le fournisseur a répondu, tel qu'il l'a dit."""


class TransportHttps:
    """Une connexion HTTPS maintenue ouverte, refaite si elle casse."""

    def __init__(self, hote: str, base: str = "/openai/v1", delai_s: float = DELAI_S):
        self.hote = hote
        self.base = base.rstrip("/")
        self.delai = delai_s
        self._connexion = None

    def nouvelle_connexion(self):
        import http.client

        self._connexion = http.client.HTTPSConnection(self.hote, timeout=self.delai)
        return self._connexion

    def envoyer(self, corps: str, entetes: dict, chemin: str) -> tuple[int, dict]:
        connexion = self._connexion or self.nouvelle_connexion()
        connexion.request("POST", f"{self.base}{chemin}", body=corps, headers=entetes)
        reponse = connexion.getresponse()
        charge = reponse.read()
        try:
            return reponse.status, json.loads(charge)
        except json.JSONDecodeError:
            return reponse.status, {"error": {"message": charge[:200].decode(
                "utf-8", "replace")}}


class ClientModeleHttp:
    """Compatible avec l'interface qu'attend `standard.comprehension`."""

    def __init__(self, transport, modele: str, cle: str, parametres: dict | None = None):
        self._transport = transport
        self._modele = modele
        self._cle = cle
        self._parametres = dict(parametres or {})
        self._connectee = False

    def completer(self, messages: list[dict], **parametres: Any) -> str:
        charge = {
            "model": self._modele,
            "messages": messages,
            # On attend un objet structuré : le demander évite la moitié des
            # réponses illisibles, et l'autre moitié est rattrapée en aval.
            "response_format": {"type": "json_object"},
            **self._parametres,
            **{cle: valeur for cle, valeur in parametres.items() if cle != "model"},
        }
        entetes = {"Authorization": f"Bearer {self._cle}",
                   "Content-Type": "application/json",
                   "User-Agent": "standard-telephonique/0.1"}

        for tentative in (1, 2):
            if not self._connectee:
                self._transport.nouvelle_connexion()
                self._connectee = True
            try:
                statut, reponse = self._transport.envoyer(
                    json.dumps(charge), entetes, CHEMIN_COMPLETIONS)
            except (ConnectionError, OSError) as erreur:
                # Une connexion gardee finit par etre fermee de l'autre cote :
                # on la refait UNE fois, puis on rend la main.
                self._connectee = False
                if tentative == 2:
                    raise ErreurModele(f"connexion au modèle impossible : {erreur}") from erreur
                continue
            break

        if statut != 200:
            message = (reponse.get("error", {}) or {}).get("message", reponse)
            raise ErreurModele(f"HTTP {statut} : {message}")
        if "choices" not in reponse:
            raise ErreurModele(f"réponse sans « choices » : {json.dumps(reponse)[:200]}")
        return reponse["choices"][0]["message"]["content"]
