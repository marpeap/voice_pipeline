"""La piste d'audit — qui a changé quoi, et quand.

Le journal d'appel dit ce que l'**agent** a fait. La piste d'audit dit ce que les
**humains** ont fait : posé une correction, changé une réponse du questionnaire,
révoqué une clé. Sans elle, « l'agent s'est mis à refuser tout le monde » n'a
aucune explication, et on cherche dans le code un défaut qui est un réglage.

Deux règles :

- **En ajout seul.** Une piste d'audit qu'on peut modifier ne prouve rien, et il
  n'existe donc aucune méthode pour corriger un événement.
- **Aucun secret.** Une clé d'API dans un journal d'audit est une clé publiée :
  l'écriture est refusée plutôt que filtrée en silence.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

CHAMPS_SECRETS = ("secret", "cle", "mot_de_passe", "token", "authorization")

SCHEMA = """
CREATE TABLE IF NOT EXISTS audit (
    numero      INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id   TEXT NOT NULL,
    horodatage  TEXT NOT NULL,
    acteur      TEXT NOT NULL,
    action      TEXT NOT NULL,
    cible       TEXT NOT NULL,
    correlation TEXT,
    detail      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS audit_par_tenant ON audit (tenant_id, numero DESC);
"""


@dataclass
class PisteDAudit:
    depot: Any

    def __post_init__(self):
        self.depot._connexion.executescript(SCHEMA)

    def noter(self, tenant: str, acteur: str, action: str, cible: str,
              detail: dict | None = None, correlation: str | None = None) -> None:
        detail = detail or {}
        fuites = [champ for champ in detail if champ.lower() in CHAMPS_SECRETS]
        if fuites:
            raise ValueError(f"la piste d'audit ne conserve aucun secret : {fuites[0]!r}")

        with self.depot._verrou:
            self.depot._connexion.execute(
            "INSERT INTO audit (tenant_id, horodatage, acteur, action, cible, "
            "correlation, detail) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (tenant, datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 acteur, action, cible, correlation,
                 json.dumps(detail, ensure_ascii=False)))

    def lister(self, tenant: str, limite: int = 200) -> list[dict[str, Any]]:
        return [{"horodatage": ligne["horodatage"], "acteur": ligne["acteur"],
                 "action": ligne["action"], "cible": ligne["cible"],
                 "correlation": ligne["correlation"],
                 "detail": json.loads(ligne["detail"])}
                for ligne in self.depot._connexion.execute(
                    "SELECT * FROM audit WHERE tenant_id = ? ORDER BY numero DESC LIMIT ?",
                    (tenant, limite))]
