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

-- Les reponses du commercant au questionnaire (docs/05). Une ligne par
-- locataire : la mise a jour est une FUSION, jamais un remplacement, sans quoi
-- un ecran qui ne porte qu'une question effacerait les autres.
CREATE TABLE IF NOT EXISTS reponses (
    tenant_id  TEXT PRIMARY KEY,
    donnees    TEXT NOT NULL,
    modifie_le TEXT NOT NULL
);
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

    def enregistrer_reponses(self, reponses: dict) -> dict:
        return self._depot._enregistrer_reponses(self._tenant, reponses)

    def relire(self, reference: str) -> dict | None:
        return self._depot._relire(self._tenant, reference)

    def annuler(self, reference: str) -> bool:
        return self._depot._annuler(self._tenant, reference)

    def corriger(self, reference: str, champs: dict) -> dict | None:
        return self._depot._corriger(self._tenant, reference, champs)

    def chercher(self, telephone: str | None = None, nom: str | None = None,
                 a_partir_de: str | None = None) -> list[dict]:
        return self._depot._chercher(self._tenant, telephone, nom, a_partir_de)


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
            # WAL : plusieurs salons tournent sur la meme machine, un service
            # par salon, un seul fichier. Sans lui, la console d'un salon qui
            # lit bloque le standard d'un autre qui ecrit — et un rendez-vous se
            # perd sur un « database is locked ». `busy_timeout` laisse le temps
            # a l'ecrivain d'en finir plutot que d'echouer tout de suite.
            # En memoire, WAL n'existe pas : on ne l'y demande pas.
            if chemin != ":memory:":
                self._connexion.execute("PRAGMA journal_mode=WAL")
                self._connexion.execute("PRAGMA busy_timeout=5000")
                self._connexion.execute("PRAGMA synchronous=NORMAL")
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

    def _enregistrer_reponses(self, tenant: str, reponses: dict) -> dict:
        """Fusionne : un ecran qui ne porte qu'une question ne doit pas effacer
        les reponses des autres blocs."""
        from datetime import datetime, timezone

        with self._verrou:
            ligne = self._connexion.execute(
                "SELECT donnees FROM reponses WHERE tenant_id = ?", (tenant,)).fetchone()
            fusion = {**(json.loads(ligne["donnees"]) if ligne else {}), **reponses}
            self._connexion.execute(
                "INSERT INTO reponses (tenant_id, donnees, modifie_le) VALUES (?, ?, ?) "
                "ON CONFLICT(tenant_id) DO UPDATE SET donnees = excluded.donnees, "
                "modifie_le = excluded.modifie_le",
                (tenant, json.dumps(fusion, ensure_ascii=False),
                 datetime.now(timezone.utc).isoformat(timespec="seconds")))
            self._connexion.commit()
        return fusion

    def reponses(self, tenant: str | None) -> dict[str, Any]:
        """Les reponses d'un locataire. **Sans locataire, elle refuse.**"""
        if not tenant:
            raise ValueError("reponses sans locataire : refuse, pour ne pas tout rendre")
        with self._verrou:
            ligne = self._connexion.execute(
                "SELECT donnees FROM reponses WHERE tenant_id = ?", (tenant,)).fetchone()
        return json.loads(ligne["donnees"]) if ligne else {}

    def _chercher(self, tenant: str, telephone: str | None, nom: str | None,
                  a_partir_de: str | None) -> list[dict]:
        """Les rendez-vous a venir d'un appelant, du plus proche au plus loin.

        Sert a l'annulation et au report : sans elle, l'agent demandait un
        numero et n'en faisait rien. La comparaison porte sur les CHIFFRES du
        numero — « 06 12 34 56 78 » et « 0612345678 » sont le meme numero, et
        l'appelant ne sait pas lequel on a garde.
        """
        chiffres = "".join(c for c in (telephone or "") if c.isdigit())
        plat = (nom or "").strip().lower()
        with self._verrou:
            lignes = self._connexion.execute(
                "SELECT reference, donnees FROM rendez_vous WHERE tenant_id = ? "
                "AND annule = 0 AND (? IS NULL OR date >= ?) ORDER BY date, heure",
                (tenant, a_partir_de, a_partir_de)).fetchall()
        trouves = []
        for ligne in lignes:
            # La reference vit dans la colonne, pas dans les donnees : sans elle
            # on saurait retrouver un rendez-vous sans pouvoir l'annuler.
            donnees = {**json.loads(ligne["donnees"]), "reference": ligne["reference"]}
            son_numero = "".join(c for c in str(donnees.get("telephone") or "")
                                 if c.isdigit())
            if chiffres and son_numero == chiffres:
                trouves.append(donnees)
            elif plat and plat == str(donnees.get("nom") or "").strip().lower():
                trouves.append(donnees)
        return trouves

    def effacer_le_locataire(self, tenant: str | None) -> dict[str, int]:
        """Efface tout ce qui appartient a ce locataire, et dit quoi.

        L'accord de test remis au salon pilote (docs/18) promet la suppression
        « sous sept jours » a la demande, et le RGPD dit la meme chose (art. 17).
        Rien ne savait le faire : il aurait fallu ouvrir la base a la main,
        table par table, en esperant n'en oublier aucune.

        On ne nomme donc AUCUNE table : on parcourt celles qui portent un
        `tenant_id`. Une table ajoutee demain sera effacee sans que personne y
        pense — c'est exactement la faute qu'on evite ici, et une table oubliee
        est une promesse trahie.
        """
        if not tenant:
            raise ValueError("effacer sans locataire : refuse, pour ne pas tout effacer")
        efface: dict[str, int] = {}
        with self._verrou:
            tables = [ligne["name"] for ligne in self._connexion.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'")]
            for table in tables:
                colonnes = [c["name"] for c in self._connexion.execute(
                    f"PRAGMA table_info({table})")]
                if "tenant_id" not in colonnes:
                    continue
                curseur = self._connexion.execute(
                    f"DELETE FROM {table} WHERE tenant_id = ?", (tenant,))
                efface[table] = curseur.rowcount
            self._connexion.commit()
        return efface

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
