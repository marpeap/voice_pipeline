"""Le démarrage en exploitation — variables d'environnement, vérification, arrêt propre.

Un service qu'on ne peut pas lancer avec des variables d'environnement et
arrêter proprement n'est pas exploitable : il est démontrable, ce qui n'est pas
la même chose.

Deux partis pris :

- **Refuser de démarrer plutôt que décrocher avec un agenda faux.** Un créneau
  mal écrit dans une variable produit, sinon, des rendez-vous à des heures qui
  n'existent pas — et personne ne s'en aperçoit avant le client.
- **Tourner sans clé d'API.** Le moteur hors ligne prend le relais. Un service
  qui refuse de démarrer faute de clé est un service qu'on ne peut pas essayer.
"""

from __future__ import annotations

import json
import os
import re
from datetime import date
from pathlib import Path
from typing import Any, Mapping

from standard.depot import Depot
from standard.hors_ligne import ModeleHorsLigne
from standard.serveur import ServeurAudioSocket
from standard.service import Configuration, Service

OBLIGATOIRES = ("STANDARD_TENANT", "STANDARD_PACK")
FORME_HEURE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _creneaux(brut: str) -> tuple[str, ...]:
    creneaux = tuple(c.strip() for c in brut.split(",") if c.strip())
    mauvais = [c for c in creneaux if not FORME_HEURE.match(c)]
    if mauvais:
        raise ValueError(f"créneau mal écrit : {', '.join(mauvais)} — attendu HH:MM")
    return creneaux


def configuration_depuis_environnement(environnement: Mapping[str, str] | None = None) -> Configuration:
    env = dict(environnement if environnement is not None else os.environ)
    manquantes = [nom for nom in OBLIGATOIRES if not env.get(nom)]
    if manquantes:
        # On nomme la variable : « configuration invalide » ne se repare pas.
        raise ValueError(f"variable(s) manquante(s) : {', '.join(manquantes)}")

    return Configuration.depuis({
        "tenant": env["STANDARD_TENANT"],
        "pack": env["STANDARD_PACK"],
        "reponses": json.loads(env.get("STANDARD_REPONSES", "{}")),
        "corps": Path(env["STANDARD_CORPS"]).read_text() if env.get("STANDARD_CORPS") else "",
        "modele": env.get("STANDARD_MODELE"),
        "parametres": json.loads(env.get("STANDARD_PARAMETRES", "{}")),
        "aujourd_hui": env.get("STANDARD_AUJOURDHUI") or date.today().isoformat(),
        "horizon_jours": int(env.get("STANDARD_HORIZON", "14")),
        "creneaux": _creneaux(env.get("STANDARD_CRENEAUX", "")),
        "jours_fermes": tuple(int(j) for j in env.get("STANDARD_JOURS_FERMES", "6").split(",") if j),
        "connexions": int(env.get("STANDARD_CONNEXIONS", "4")),
        "consignes_communes": Path(env["STANDARD_CONSIGNES"]).read_text()
        if env.get("STANDARD_CONSIGNES") else "",
    })


def verifier_le_deploiement(environnement: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Dit si le service peut décrocher, **et ce qui manque sinon**.

    À lancer avant de brancher un numéro : il vaut mieux découvrir un pack
    incomplet ici que sur le premier appelant.
    """
    config = configuration_depuis_environnement(environnement)
    service = Service(config, client_modele=ModeleHorsLigne(aujourd_hui=config.aujourd_hui),
                      base=Depot(":memory:").pour(config.tenant))
    manquantes = service.questions_manquantes()
    return {
        "tenant": config.tenant,
        "pack": config.pack["pack"],
        "pack_valide": bool(config.pack.get("blocs")),
        "creneaux": len(config.creneaux),
        "questions_manquantes": manquantes,
        "modele": config.modele or "hors ligne",
        "pret": not manquantes and bool(config.creneaux),
    }


def construire_serveur(environnement: Mapping[str, str] | None = None) -> ServeurAudioSocket:
    """Assemble le service complet, prêt à recevoir des appels."""
    env = dict(environnement if environnement is not None else os.environ)
    config = configuration_depuis_environnement(env)
    depot = Depot(env.get("STANDARD_BASE", "standard.sqlite3"))

    service = Service(config,
                      client_modele=ModeleHorsLigne(aujourd_hui=config.aujourd_hui),
                      base=depot.pour(config.tenant))
    service.demarrer()

    compteur = {"appels": 0}

    def fabrique_agent():
        compteur["appels"] += 1
        return service.nouvel_appel(f"appel-{compteur['appels']}")

    return ServeurAudioSocket(
        fabrique_agent=fabrique_agent,
        # Sans moteur de transcription branche, le service tourne et repond :
        # c'est ce qui permet de verifier un deploiement avant d'avoir un STT.
        transcrire=lambda audio, frequence: "",
        synthetiser=lambda texte: [texte.encode()],
        hote=env.get("STANDARD_HOTE", "0.0.0.0"),
        port=int(env.get("STANDARD_PORT", "8090")))
