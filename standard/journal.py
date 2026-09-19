"""Le journal d'appel — ce qui reste quand l'appel est fini.

Sans lui, « l'agent comprend mal » n'est pas diagnosticable (mesure 10 : le
rapport signal/bruit décide de la moitié du résultat), la console n'a rien à
montrer au commerçant, et l'annonce légale n'est pas prouvable.

Avec lui, la question s'inverse : **qu'est-ce qu'on n'a pas le droit de garder ?**
Le journal **refuse** un champ audio plutôt que de l'écrire discrètement — la
conformité ne se vérifie pas à la relecture d'une politique, elle se code.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

CONSERVATION_PAR_DEFAUT_JOURS = 90
CHAMPS_INTERDITS = ("audio", "enregistrement", "wav", "pcm")

SCHEMA = """
CREATE TABLE IF NOT EXISTS appels (
    uuid       TEXT NOT NULL,
    tenant_id  TEXT NOT NULL,
    debut      TEXT NOT NULL,
    donnees    TEXT NOT NULL,
    PRIMARY KEY (tenant_id, uuid)
);
CREATE INDEX IF NOT EXISTS appels_par_date ON appels (tenant_id, debut);
"""


@dataclass
class JournalDAppels:
    """Les appels d'un salon — cloisonnés comme le reste (`docs/02`)."""

    depot: Any

    def __post_init__(self):
        self.depot._connexion.executescript(SCHEMA)

    # --- écriture -----------------------------------------------------------

    def enregistrer(self, tenant: str, appel: dict) -> None:
        if not tenant:
            raise ValueError("enregistrer sans locataire : refusé")
        interdits = [champ for champ in appel if champ.lower() in CHAMPS_INTERDITS]
        if interdits:
            # Mieux vaut un appel qui échoue qu'un enregistrement conservé par
            # inadvertance : en France, garder l'audio ferait entrer le service
            # dans le régime d'opt-in applicable depuis août 2026.
            raise ValueError(f"le journal ne conserve pas d'audio : champ {interdits[0]!r}")

        self.depot._connexion.execute(
            "INSERT OR REPLACE INTO appels (uuid, tenant_id, debut, donnees) "
            "VALUES (?, ?, ?, ?)",
            (appel["uuid"], tenant, appel["debut"], json.dumps(appel, ensure_ascii=False)))
        self.depot._connexion.commit()

    # --- lecture ------------------------------------------------------------

    def lister(self, tenant: str | None, limite: int = 100) -> list[dict]:
        if not tenant:
            raise ValueError("lister sans locataire : refusé, pour ne pas tout rendre")
        return [json.loads(ligne["donnees"]) for ligne in self.depot._connexion.execute(
            "SELECT donnees FROM appels WHERE tenant_id = ? ORDER BY debut DESC LIMIT ?",
            (tenant, limite))]

    def incidents(self, tenant: str) -> list[dict]:
        """Ce qui doit remonter tout de suite, et non figurer dans une moyenne.

        Une confirmation orpheline n'est pas une statistique : c'est un client
        qui s'organise sur un rendez-vous qui n'existe pas (mesure 14).
        """
        incidents = []
        for appel in self.lister(tenant):
            if appel.get("confirmations_orphelines"):
                incidents.append({"uuid": appel["uuid"], "motif": "confirmation orpheline",
                                  "gravite": "incident", "debut": appel["debut"]})
            preuve = appel.get("preuve_annonce") or {}
            if not preuve.get("conforme"):
                incidents.append({"uuid": appel["uuid"], "motif": "annonce absente",
                                  "gravite": "incident", "debut": appel["debut"]})
        return incidents

    def resume(self, tenant: str) -> dict[str, Any]:
        """Ce que la console montre en tête : quatre chiffres, pas quarante."""
        appels = self.lister(tenant)
        if not appels:
            return {"appels": 0, "rendez_vous": 0, "transferts": 0,
                    "part_bruitee_pct": 0.0, "confirmations_orphelines": 0}
        bruites = sum(1 for a in appels if a.get("bruite"))
        return {
            "appels": len(appels),
            "rendez_vous": sum(1 for a in appels if a.get("issue") == "rendez-vous"),
            "transferts": sum(1 for a in appels if a.get("issue") == "transfert"),
            "part_bruitee_pct": round(100 * bruites / len(appels), 1),
            "confirmations_orphelines": sum(a.get("confirmations_orphelines", 0)
                                            for a in appels),
        }

    # --- conservation -------------------------------------------------------

    def purger(self, conservation_jours: int = CONSERVATION_PAR_DEFAUT_JOURS,
               tenant: str | None = None) -> int:
        """Efface ce qui a dépassé la durée annoncée au registre des traitements.

        Une durée écrite dans un document et jamais appliquée est une durée
        fausse : c'est cette fonction qui rend la ligne du registre vraie.
        """
        limite = (date.today() - timedelta(days=conservation_jours)).isoformat()
        if tenant:
            curseur = self.depot._connexion.execute(
                "DELETE FROM appels WHERE tenant_id = ? AND debut < ?", (tenant, limite))
        else:
            curseur = self.depot._connexion.execute(
                "DELETE FROM appels WHERE debut < ?", (limite,))
        self.depot._connexion.commit()
        return curseur.rowcount
