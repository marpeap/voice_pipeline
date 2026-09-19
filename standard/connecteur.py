"""Le connecteur — brancher l'agent sur le logiciel que le commerçant utilise déjà.

C'est la promesse du produit : un greffon, pas une île. C'est aussi l'endroit où
l'on peut faire le plus de dégâts — une écriture rejouée crée un doublon, un
refus mal lu fait promettre l'impossible.

Trois règles gouvernent ce fichier, et chacune répare une faute connue :

1. **Un « non » et un « je ne sais pas » ne se confondent jamais.** Un `500` n'est
   pas un refus : dire « ce créneau est pris » parce que le serveur de l'hôte
   tousse, c'est mentir au client avec aplomb.
2. **Un réessai réutilise la même clé d'idempotence.** Réessayer avec une clé
   neuve, c'est fabriquer le doublon qu'on croyait éviter.
3. **Un refus ne se réessaie pas.** Un « non » répété reste « non », et chaque
   tentative coûte une seconde de conversation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol

DELAI_PAR_DEFAUT_S = 3.0        # un appel téléphonique n'attend pas davantage

# Les refus de l'hôte, ramenés à des codes que l'agent sait dire à voix haute.
CODES_DE_REFUS = {
    409: "creneau_pris",
    422: "donnees_refusees",
    403: "acces_refuse",
    404: "inconnu",
    429: "trop_de_demandes",
    400: "demande_malformee",
}

# Jamais transmis, même si ça traîne dans les données : le produit ne collecte
# pas d'adresse électronique, il n'a donc aucune raison d'en propager une.
CHAMPS_INTERDITS = ("email", "courriel", "mail")


class Refus(RuntimeError):
    """L'hôte a dit non, et on sait pourquoi."""

    def __init__(self, code: str, detail: Any = None):
        super().__init__(f"{code} : {detail}" if detail else code)
        self.code = code
        self.detail = detail


class Indisponible(RuntimeError):
    """L'hôte n'a pas répondu, ou a répondu qu'il était en panne.

    Ce n'est **pas** un refus. L'agent doit dire qu'il n'a pas pu vérifier, et
    surtout pas que le créneau est pris.
    """


class Connecteur(Protocol):
    def disponibilites(self, jour: str) -> list[str]: ...
    def reserver(self, cle: str, donnees: dict, reessais: int = 0) -> str: ...
    def relire(self, reference: str) -> dict | None: ...


def _sans_champs_interdits(donnees: dict) -> dict:
    return {cle: valeur for cle, valeur in donnees.items()
            if cle.lower() not in CHAMPS_INTERDITS}


@dataclass
class ConnecteurInterne:
    """L'agenda du produit lui-même — celui qui marche sans dépendre de personne.

    C'est le chemin par défaut : un salon peut être servi le premier jour, sans
    intégration, sans compte tiers, sans OAuth plafonné à cent utilisateurs.
    """

    depot: Any
    tenant: str
    creneaux: list[str]

    def disponibilites(self, jour: str) -> list[str]:
        pris = {ligne["heure"] for ligne in self.depot.lister(self.tenant)
                if ligne.get("date") == jour}
        return [heure for heure in self.creneaux if heure not in pris]

    def reserver(self, cle: str, donnees: dict, reessais: int = 0) -> str:
        from standard.depot import ChevauchementRefuse

        if donnees.get("heure") not in self.creneaux:
            raise Refus("creneau_inconnu", donnees.get("heure"))
        try:
            return self.depot.pour(self.tenant).inserer(cle, _sans_champs_interdits(donnees))
        except ChevauchementRefuse as erreur:
            raise Refus("creneau_pris", str(erreur)) from erreur

    def relire(self, reference: str) -> dict | None:
        return self.depot.pour(self.tenant).relire(reference)


class ConnecteurHttp:
    """Un hôte tiers, joint par HTTP. Le transport est injecté : il se teste."""

    def __init__(self, transport: Callable[..., tuple[int, dict]], base: str,
                 cle_api: str, delai_s: float = DELAI_PAR_DEFAUT_S):
        self._transport = transport
        self._base = base.rstrip("/")
        self._cle_api = cle_api
        self._delai = delai_s

    # --- lecture ------------------------------------------------------------

    def disponibilites(self, jour: str) -> list[str]:
        statut, corps = self._appeler("GET", f"/disponibilites?jour={jour}")
        if statut != 200:
            raise Indisponible(f"disponibilités : HTTP {statut}")
        # L'hôte peut rendre deux formes ; on ne suppose pas la sienne.
        creneaux = corps.get("creneaux", corps.get("slots", []))
        return [c["heure"] if isinstance(c, dict) else c for c in creneaux]

    def relire(self, reference: str) -> dict | None:
        statut, corps = self._appeler("GET", f"/reservations/{reference}")
        if statut == 404:
            return None
        if statut != 200:
            raise Indisponible(f"relecture : HTTP {statut}")
        return corps

    # --- écriture -----------------------------------------------------------

    def reserver(self, cle: str, donnees: dict, reessais: int = 0) -> str:
        tentative = 0
        while True:
            try:
                statut, corps = self._appeler(
                    "POST", "/reservations", corps=_sans_champs_interdits(donnees),
                    idempotence=cle)
            except Indisponible:
                if tentative >= reessais:
                    raise
                tentative += 1
                continue                      # même clé : c'est tout l'intérêt

            if statut in (200, 201):
                return corps.get("id") or corps.get("reference")
            if statut in CODES_DE_REFUS:
                # Un refus est définitif : le réessayer coûte une seconde de
                # conversation et rend exactement le même « non ».
                raise Refus(CODES_DE_REFUS[statut], corps.get("erreur"))
            if tentative >= reessais:
                raise Indisponible(f"réservation : HTTP {statut}")
            tentative += 1

    # --- transport ----------------------------------------------------------

    def _appeler(self, methode: str, chemin: str, corps: dict | None = None,
                 idempotence: str | None = None) -> tuple[int, dict]:
        entetes = {"X-Api-Key": self._cle_api, "Content-Type": "application/json"}
        if idempotence:
            # Dans l'en-tête, comme Stripe : un champ de corps se perd en silence
            # quand l'hôte ne le connaît pas.
            entetes["Idempotency-Key"] = idempotence
        return self._transport(methode, f"{self._base}{chemin}", corps=corps,
                               entetes=entetes, delai=self._delai)


class BaseViaConnecteur:
    """L'hôte, vu comme une base de rendez-vous — c'est ce qui branche le greffon.

    `ecriture.ecrire_rendez_vous` ne connaît qu'un contrat : `inserer` puis
    `relire`. Le connecteur, lui, parle `reserver` / `relire` / `disponibilites`.
    Cet adaptateur est le seul endroit où les deux se rencontrent, et il traduit
    surtout **les échecs**, qui n'ont pas le même sens :

    - un refus de créneau devient `ChevauchementRefuse`, que l'agent sait dire
      (« ce créneau vient d'être pris, il me reste… ») ;
    - une indisponibilité de l'hôte remonte telle quelle, et l'écriture rend
      « incertain » — l'agent dit qu'il ne peut pas vérifier, il ne promet rien.

    Confondre les deux ferait annoncer « c'est pris » parce que le serveur de
    l'hôte tousse : mentir au client avec aplomb, et sans qu'il puisse le savoir.
    """

    def __init__(self, connecteur: Connecteur, reessais: int = 1):
        self._connecteur = connecteur
        # Un seul reessai, avec LA MEME cle : un appel telephonique n'attend pas
        # davantage, et une cle neuve fabriquerait le doublon qu'on evite.
        self._reessais = reessais

    def inserer(self, cle: str, donnees: dict) -> str:
        from standard.depot import ChevauchementRefuse

        try:
            return self._connecteur.reserver(cle, donnees, reessais=self._reessais)
        except Refus as refus:
            if refus.code == "creneau_pris":
                raise ChevauchementRefuse(
                    f"{donnees.get('date')} {donnees.get('heure')} refusé par l'hôte"
                ) from refus
            raise

    def relire(self, reference: str) -> dict | None:
        return self._connecteur.relire(reference)

    def libres_du_jour(self, jour_iso: str) -> list[str]:
        """Les créneaux de l'hôte pour ce jour — jamais une liste devinée."""
        return self._connecteur.disponibilites(jour_iso)
