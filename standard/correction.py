"""La boucle de correction — une faute choisie, jamais une phrase ecrite.

Regle qui domine `docs/06` : **le commercant ne voit jamais un prompt, sous
aucune forme « avancee »**. Une correction n'est pas du texte. C'est une faute
choisie dans une liste courte, appliquee a un empan de transcription, qui produit
une **contrainte typee**.

Deux partis pris expliquent presque tout le fichier.

**Ce qui doit etre vrai a cent pour cent ne va pas dans le prompt.** Une regle
redigee en langue naturelle peut ne pas etre retenue par le modele sur un tour
donne — Intercom le documente, et ce n'est meme pas considere comme une erreur de
configuration. Une regle qui s'applique « la plupart du temps » n'est pas une
regle : les contraintes d'agenda et les interdits partent donc cote **serveur**.

**Toute correction alimente le corpus de regression.** Personne ne le fait sur le
marche, et c'est pourtant ce qui transforme un correctif ponctuel en garantie :
l'appel rate devient un scenario rejoue a chaque changement, cinq fois de suite.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


REPETITIONS_REGRESSION = 5      # pass^5, comme le reste de la porte

FAUTES: dict[str, dict[str, Any]] = {
    "prestation": {
        "libelle": "Ce n'est pas la bonne prestation",
        "cible": "pack", "prompt": True, "texte_libre": False,
        "ecrit": "correspondance terme vers prestation, et desambiguisation",
    },
    "duree": {
        "libelle": "La durée est fausse",
        "cible": "frontmatter", "prompt": True, "texte_libre": False,
        "ecrit": "duree_minutes sur la prestation",
    },
    "creneau_inexistant": {
        "libelle": "Ce créneau n'existe pas",
        "cible": "serveur", "prompt": False, "texte_libre": False,
        "ecrit": "contrainte d'agenda evaluee cote serveur",
    },
    "promesse_interdite": {
        "libelle": "Il n'aurait pas dû promettre ça",
        "cible": "corps", "prompt": True, "texte_libre": False,
        "ecrit": "interdit explicite, double d'une garde serveur",
    },
    "escalade": {
        "libelle": "Il fallait passer la main",
        "cible": "frontmatter", "prompt": False, "texte_libre": False,
        "ecrit": "regle d'escalade : motif et seuil",
    },
    "mauvaise_information": {
        "libelle": "Mauvaise information",
        "cible": "frontmatter", "prompt": True, "texte_libre": False,
        "ecrit": "correction de la fiche : horaire, tarif, acces",
    },
    "autre": {
        "libelle": "Autre",
        "cible": "a_revoir", "prompt": False, "texte_libre": True,
        "ecrit": "note datee, mise en file pour arbitrage",
    },
}

EN_ESSAI = "en essai"
EN_CONFLIT = "en conflit"
SUSPENDUE = "suspendue"
REVOQUEE = "revoquee"
A_ARBITRER = "a arbitrer"
ETATS_ACTIFS = (EN_ESSAI, "active")

_compteur = itertools.count(1)


@dataclass
class Correction:
    """Une faute choisie, ancree sur un empan de transcription."""

    faute: str
    appel: str
    empan: str
    valeur: dict[str, Any] = field(default_factory=dict)
    identifiant: str = ""
    etat: str = ""
    posee_le: str = ""

    def __post_init__(self):
        if self.faute not in FAUTES:
            raise ValueError(f"faute inconnue : {self.faute!r} — la liste est fermee, "
                             f"et c'est ce qui evite le clavier")
        self.identifiant = self.identifiant or f"cor-{next(_compteur):04d}"
        self.posee_le = self.posee_le or datetime.now(timezone.utc).isoformat(timespec="seconds")
        # Une dictee ne devient pas une regle sans que quelqu'un l'ait lue.
        self.etat = self.etat or (A_ARBITRER if self.faute == "autre" else EN_ESSAI)

    @property
    def cible(self) -> str:
        return FAUTES[self.faute]["cible"]

    @property
    def signature(self) -> tuple:
        """Ce sur quoi deux corrections peuvent se contredire.

        Deux corrections de duree sur la MEME prestation se contredisent ; deux
        corrections de duree sur des prestations differentes, non.
        """
        ancrage = (self.valeur.get("prestation") or self.valeur.get("terme")
                   or self.valeur.get("motif") or self.valeur.get("champ"))
        return (self.faute, ancrage)


SCHEMA = """
CREATE TABLE IF NOT EXISTS corrections (
    identifiant TEXT NOT NULL,
    tenant_id   TEXT NOT NULL,
    donnees     TEXT NOT NULL,
    PRIMARY KEY (tenant_id, identifiant)
);
"""


class RegistreDeCorrections:
    """Le cycle de vie des corrections d'un salon.

    **Ecriture a chaque appui** : un gerant interrompu toutes les deux minutes ne
    doit jamais perdre ce qu'il vient de poser. Cette phrase etait dans la
    docstring bien avant d'etre vraie — le registre etait une liste en memoire,
    et un redemarrage effacait tout. Une revue independante l'a releve.

    Sans depot, il reste en memoire : c'est ce qui permet de l'utiliser dans un
    test ou une demonstration sans fichier.
    """

    def __init__(self, depot=None, tenant: str = "inconnu"):
        self._corrections: list[Correction] = []
        self._depot = depot
        self._tenant = tenant
        if depot is not None:
            with depot._verrou:
                depot._connexion.executescript(SCHEMA)
            self._relire()

    # --- persistance --------------------------------------------------------

    def _relire(self) -> None:
        import json

        with self._depot._verrou:
            lignes = self._depot._connexion.execute(
                "SELECT donnees FROM corrections WHERE tenant_id = ?",
                (self._tenant,)).fetchall()
        for ligne in lignes:
            champs = json.loads(ligne["donnees"])
            self._corrections.append(Correction(**champs))

    def _ecrire(self, correction: "Correction") -> None:
        if self._depot is None:
            return
        import json

        champs = {"faute": correction.faute, "appel": correction.appel,
                  "empan": correction.empan, "valeur": correction.valeur,
                  "identifiant": correction.identifiant, "etat": correction.etat,
                  "posee_le": correction.posee_le}
        with self._depot._verrou:
            self._depot._connexion.execute(
                "INSERT OR REPLACE INTO corrections (identifiant, tenant_id, donnees) "
                "VALUES (?, ?, ?)",
                (correction.identifiant, self._tenant,
                 json.dumps(champs, ensure_ascii=False)))

    # --- poser ---------------------------------------------------------------

    def ajouter(self, correction: Correction) -> Correction:
        if correction.etat in (EN_ESSAI,) and self._contredit(correction):
            # Jamais de fusion muette : on montre les deux, et on demande
            # laquelle vaut.
            correction.etat = EN_CONFLIT
        self._corrections.append(correction)
        self._ecrire(correction)
        return correction

    def _contredit(self, candidate: Correction) -> bool:
        return any(autre.signature == candidate.signature
                   and autre.etat in ETATS_ACTIFS
                   and autre.valeur != candidate.valeur
                   for autre in self._corrections)

    # --- trancher ------------------------------------------------------------

    def trancher(self, identifiant: str) -> Correction:
        """Le gerant dit laquelle vaut : l'autre est suspendue, pas effacee."""
        gagnante = self.par_identifiant(identifiant)
        for autre in self._corrections:
            if autre is gagnante or autre.signature != gagnante.signature:
                continue
            if autre.etat in ETATS_ACTIFS or autre.etat == EN_CONFLIT:
                autre.etat = SUSPENDUE
        gagnante.etat = EN_ESSAI
        for correction in self._corrections:
            self._ecrire(correction)
        return gagnante

    def revoquer(self, identifiant: str) -> Correction:
        correction = self.par_identifiant(identifiant)
        correction.etat = REVOQUEE
        self._ecrire(correction)
        return correction

    # --- lire ----------------------------------------------------------------

    def par_identifiant(self, identifiant: str) -> Correction:
        for correction in self._corrections:
            if correction.identifiant == identifiant:
                return correction
        raise KeyError(identifiant)

    def empreinte(self) -> str:
        """Ce qui change quand une correction est posee, tranchee ou revoquee.

        La console tourne dans un AUTRE processus que le standard : ils ne
        partagent que la base. Sans cette empreinte, le service composait sa
        memoire une fois au demarrage et la correction n'arrivait jamais — alors
        que la console promet « elle s'applique des maintenant ».
        """
        if self._depot is None:
            return str(sorted((c.identifiant, c.etat) for c in self._corrections))
        import hashlib
        import json

        with self._depot._verrou:
            lignes = self._depot._connexion.execute(
                "SELECT identifiant, donnees FROM corrections WHERE tenant_id = ? "
                "ORDER BY identifiant", (self._tenant,)).fetchall()
        brut = json.dumps([[l["identifiant"], l["donnees"]] for l in lignes],
                          ensure_ascii=False)
        return hashlib.sha256(brut.encode()).hexdigest()

    def recharger(self) -> None:
        """Relit la base : ce qu'un autre processus a pose devient visible ici."""
        if self._depot is None:
            return
        self._corrections = []
        self._relire()

    def actives(self) -> list[Correction]:
        return [c for c in self._corrections if c.etat in ETATS_ACTIFS]

    def conflits(self) -> list[Correction]:
        return [c for c in self._corrections if c.etat == EN_CONFLIT]

    def a_arbitrer(self) -> list[Correction]:
        return [c for c in self._corrections if c.etat == A_ARBITRER]

    # --- le corpus -----------------------------------------------------------

    def scenarios_de_regression(self) -> list[dict[str, Any]]:
        """Chaque correction active devient un scenario rejoue a chaque changement.

        C'est le seul endroit du produit ou un appel rate se transforme en
        garantie : sans cela, la correction tient jusqu'au prochain changement de
        modele, et personne ne s'apercoit de la rechute.
        """
        return [{
            "identifiant": correction.identifiant,
            "origine": correction.appel,
            "enonce": correction.empan,
            "faute": correction.faute,
            "attendu": correction.valeur,
            "repetitions": REPETITIONS_REGRESSION,
        } for correction in self.actives()]


def appliquer(corrections: list[Correction], reponses: dict, corps: str):
    """Rend (reponses, corps, regles serveur) — sans jamais reecrire le corps.

    Le corps du commercant est **concatene**, jamais reanalyse : c'est le meme
    invariant que le questionnaire (docs/05).
    """
    reponses = dict(reponses)
    regles_serveur: list[dict[str, Any]] = []
    ajouts: list[str] = []

    for correction in corrections:
        if correction.etat not in ETATS_ACTIFS:
            continue
        valeur = correction.valeur

        # Une correction incomplete — la console peut n'avoir recu qu'une note —
        # se met de cote au lieu de faire tomber l'application des autres.
        try:
            if correction.faute == "duree":
                reponses.setdefault("durees", {})[valeur["prestation"]] = \
                    valeur["duree_minutes"]

            elif correction.faute == "prestation":
                reponses.setdefault("synonymes", {})[valeur["terme"]] = valeur["prestation"]

            elif correction.faute == "mauvaise_information":
                reponses.setdefault("fiche", {})[valeur["champ"]] = valeur["valeur"]

            elif correction.faute == "escalade":
                reponses.setdefault("escalade", {})[valeur["motif"]] = valeur.get("seuil", 1)

            elif correction.faute == "creneau_inexistant":
                # Cote serveur uniquement : une contrainte d'agenda ne se redige pas.
                regles_serveur.append({"type": "agenda", **valeur})

            elif correction.faute == "promesse_interdite":
                # Le corps le dit au modele, ET le serveur l'empeche. Une consigne
                # ecrite n'est pas une garantie, elle est une preference.
                ajouts.append(f"- Ne jamais {valeur['interdit']}.")
                regles_serveur.append({"type": "interdit", "interdit": valeur["interdit"]})
        except KeyError:
            continue

    if ajouts:
        corps = corps.rstrip("\n") + "\n\n## Ce que l'agent ne doit jamais faire\n\n" \
            + "\n".join(ajouts) + "\n"
    return reponses, corps, regles_serveur
