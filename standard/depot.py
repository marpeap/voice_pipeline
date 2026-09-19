"""Le depot — des rendez-vous, cloisonnes par locataire, sans chevauchement.

`docs/02` : tables partagees et `tenant_id`, jamais une base par client — avec
`max_connections` a 100 par defaut, une base par salon plafonne le produit avant
le centieme client.

Le cloisonnement ne repose pas sur la bonne volonte de l'appelant : **on
n'obtient un acces qu'en nommant le locataire** (`depot.pour("salon-1")`), et une
lecture globale sans locataire echoue au lieu de tout rendre. Le pire defaut d'un
multi-locataire n'est pas l'erreur : c'est la requete qui reussit et rend les
donnees de tout le monde.

En production, PostgreSQL ajoute la meme regle **sous** l'application
(`migrations/001-rendez-vous.sql`, `ENABLE` **et** `FORCE`). Ici, SQLite suffit a
faire tourner le produit sans rien installer — et les deux portent la meme regle.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from typing import Any


class ChevauchementRefuse(RuntimeError):
    """Deux rendez-vous ne peuvent pas occuper le meme creneau chez le meme salon.

    C'est un refus, pas une erreur technique : la contrainte est la regle metier
    elle-meme, et elle vit dans la base plutot que dans une verification que
    quelqu'un oubliera d'appeler.
    """


SCHEMA = """
CREATE TABLE IF NOT EXISTS rendez_vous (
    reference       TEXT PRIMARY KEY,
    tenant_id       TEXT NOT NULL,
    cle_idempotence TEXT NOT NULL,
    date            TEXT NOT NULL,
    heure           TEXT NOT NULL,
    annule          INTEGER NOT NULL DEFAULT 0,
    donnees         TEXT NOT NULL
);
-- Une cle d'idempotence appartient a UN locataire : deux salons peuvent produire
-- la meme sans que leurs rendez-vous se melangent.
CREATE UNIQUE INDEX IF NOT EXISTS rendez_vous_cle
    ON rendez_vous (tenant_id, cle_idempotence);
-- Le creneau ne se reserve qu'une fois — index partiel, pour qu'une annulation
-- libere la place au lieu de la bloquer pour toujours.
CREATE UNIQUE INDEX IF NOT EXISTS rendez_vous_creneau
    ON rendez_vous (tenant_id, date, heure) WHERE annule = 0;

-- Les messages pris quand le salon a choisi « prendre un message » plutot que
-- « transferer » (question D4 des packs). Aucune contrainte d'unicite : deux
-- appelants peuvent laisser le meme message, et les deux comptent.
CREATE TABLE IF NOT EXISTS messages (
    reference  TEXT PRIMARY KEY,
    tenant_id  TEXT NOT NULL,
    recu_le    TEXT NOT NULL,
    donnees    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS messages_locataire ON messages (tenant_id, recu_le);
"""


class AccesLocataire:
    """La seule facon de toucher aux donnees : au nom d'un locataire nomme."""

    def __init__(self, depot: "Depot", tenant: str):
        if not tenant:
            raise ValueError("acces sans locataire refuse")
        self._depot = depot
        self._tenant = tenant

    def inserer(self, cle: str, donnees: dict) -> str:
        return self._depot._inserer(self._tenant, cle, donnees)

    def enregistrer_message(self, donnees: dict) -> str:
        return self._depot._enregistrer_message(self._tenant, donnees)

    def relire(self, reference: str) -> dict | None:
        return self._depot._relire(self._tenant, reference)

    def annuler(self, reference: str) -> bool:
        return self._depot._annuler(self._tenant, reference)

    def corriger(self, reference: str, champs: dict) -> dict | None:
        return self._depot._corriger(self._tenant, reference, champs)


class Depot:
    def __init__(self, chemin: str = ":memory:"):
        self._connexion = sqlite3.connect(chemin, check_same_thread=False,
                                          isolation_level=None, timeout=5.0)
        self._connexion.row_factory = sqlite3.Row
        # Une seule connexion partagee par tous les fils d'appel : sans verrou,
        # le commit d'un fil validait la transaction en cours d'un autre. Le
        # verrou serialise les ecritures ; `isolation_level=None` rend les
        # transactions explicites au lieu de les laisser s'emboiter.
        self._verrou = threading.RLock()
        with self._verrou:
            self._connexion.executescript(SCHEMA)

    def pour(self, tenant: str) -> AccesLocataire:
        return AccesLocataire(self, tenant)

    # --- operations, toutes portant le locataire ----------------------------

    def _inserer(self, tenant: str, cle: str, donnees: dict) -> str:
        with self._verrou:
            return self._inserer_sous_verrou(tenant, cle, donnees)

    def _inserer_sous_verrou(self, tenant: str, cle: str, donnees: dict) -> str:
        deja = self._connexion.execute(
            "SELECT reference FROM rendez_vous WHERE tenant_id = ? AND cle_idempotence = ?",
            (tenant, cle)).fetchone()
        if deja:
            return deja["reference"]          # idempotence : la meme cle, la meme ligne

        reference = f"rdv-{tenant}-{cle[:12]}"
        try:
            self._connexion.execute(
                "INSERT INTO rendez_vous (reference, tenant_id, cle_idempotence, date, "
                "heure, donnees) VALUES (?, ?, ?, ?, ?, ?)",
                (reference, tenant, cle, donnees.get("date"), donnees.get("heure"),
                 json.dumps(donnees, ensure_ascii=False)))
        except sqlite3.IntegrityError as erreur:
            # SQLite nomme les colonnes de l'index, pas l'index : on reconnait la
            # contrainte par ses colonnes plutot que par un nom qu'il ne donne pas.
            message = str(erreur)
            if "date" in message and "heure" in message:
                raise ChevauchementRefuse(
                    f"{donnees.get('date')} {donnees.get('heure')} est deja pris") from erreur
            raise
        return reference

    def _relire(self, tenant: str, reference: str) -> dict | None:
        with self._verrou:
                ligne = self._connexion.execute(
                "SELECT donnees FROM rendez_vous WHERE tenant_id = ? AND reference = ? "
                "AND annule = 0", (tenant, reference)).fetchone()
        return json.loads(ligne["donnees"]) if ligne else None

    def _annuler(self, tenant: str, reference: str) -> bool:
        with self._verrou:
            curseur = self._connexion.execute(
                "UPDATE rendez_vous SET annule = 1 WHERE tenant_id = ? AND reference = ?",
                (tenant, reference))
            return curseur.rowcount > 0

    def _corriger(self, tenant: str, reference: str, champs: dict) -> dict | None:
        """Corrige des champs d'un rendez-vous existant, et rend la ligne relue.

        Ni la date ni l'heure ne passent par ici : les deplacer touche a
        l'unicite du creneau, et se fait en annulant puis en reecrivant. Ce
        chemin sert a ce qui ne peut pas entrer en conflit — le nom, d'abord,
        que le moteur rend « Le Fora » pour « Lefevre ».
        """
        interdits = {"date", "heure"} & set(champs)
        if interdits:
            raise ValueError(f"corriger ne deplace pas un rendez-vous : {sorted(interdits)}")
        with self._verrou:
            ligne = self._connexion.execute(
                "SELECT donnees FROM rendez_vous WHERE tenant_id = ? AND reference = ? "
                "AND annule = 0", (tenant, reference)).fetchone()
            if ligne is None:
                return None
            donnees = {**json.loads(ligne["donnees"]), **champs}
            self._connexion.execute(
                "UPDATE rendez_vous SET donnees = ? WHERE tenant_id = ? AND reference = ?",
                (json.dumps(donnees, ensure_ascii=False), tenant, reference))
            self._connexion.commit()
        return donnees

    def _enregistrer_message(self, tenant: str, donnees: dict) -> str:
        """Un message pris pour le salon. Il n'y a rien a relire : personne
        n'attend au bout du fil, et le message ne promet rien a personne."""
        from datetime import datetime, timezone

        reference = f"msg-{uuid.uuid4().hex[:12]}"
        recu_le = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._verrou:
            self._connexion.execute(
                "INSERT INTO messages (reference, tenant_id, recu_le, donnees) "
                "VALUES (?, ?, ?, ?)",
                (reference, tenant, recu_le,
                 json.dumps({**donnees, "reference": reference, "recu_le": recu_le},
                            ensure_ascii=False)))
            self._connexion.commit()
        return reference

    def messages(self, tenant: str | None) -> list[dict[str, Any]]:
        """Les messages d'un locataire, du plus recent au plus ancien."""
        if not tenant:
            raise ValueError("messages sans locataire : refuse, pour ne pas tout rendre")
        with self._verrou:
            return [json.loads(ligne["donnees"]) for ligne in self._connexion.execute(
                "SELECT donnees FROM messages WHERE tenant_id = ? "
                "ORDER BY recu_le DESC", (tenant,))]

    def lister(self, tenant: str | None) -> list[dict[str, Any]]:
        """Liste les rendez-vous d'un locataire. **Sans locataire, elle refuse.**"""
        if not tenant:
            raise ValueError("lister sans locataire : refuse, pour ne pas tout rendre")
        with self._verrou:
            return [json.loads(ligne["donnees"]) for ligne in self._connexion.execute(
                "SELECT donnees FROM rendez_vous WHERE tenant_id = ? AND annule = 0 "
                "ORDER BY date, heure", (tenant,))]
