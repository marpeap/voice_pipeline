"""Les accès — clés par locataire, rotation sans coupure, limitation d'usage.

Écarts relevés par la troisième confrontation (19/09) : un service multi-locataire
professionnel porte des clés **par locataire**, une rotation **à fenêtre de
recouvrement**, et une limitation d'usage **par locataire et par adresse**.

Trois choix, et chacun répare une panne connue :

1. **Le secret n'est jamais conservé en clair.** Une base volée ne doit pas
   livrer les clés de tous les salons — on garde une empreinte, comme pour un
   mot de passe.
2. **La rotation laisse les deux clés valides quelques minutes.** Sans fenêtre de
   recouvrement, elle coupe les requêtes en vol : c'est la panne classique de la
   rotation « bien faite ».
3. **La limitation compte par locataire ET par adresse.** Une seule adresse qui
   essaie tous les locataires n'est pas un usage, c'est une attaque.
"""

from __future__ import annotations

import hashlib
import secrets
from secrets import compare_digest
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable

PREFIXE = "std_"
FENETRE_S = 60.0
PAR_MINUTE_PAR_DEFAUT = 120
PAR_MINUTE_ADRESSE_PAR_DEFAUT = 300


class CleRefusee(RuntimeError):
    """La clé n'existe pas, est révoquée, a expiré, ou n'a pas la portée demandée."""


class TropDeDemandes(RuntimeError):
    def __init__(self, motif: str, reessayer_dans_s: float):
        super().__init__(f"{motif} — réessayer dans {reessayer_dans_s:.0f} s")
        self.reessayer_dans_s = reessayer_dans_s


def _empreinte(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


@dataclass
class Cle:
    identifiant: str
    tenant: str
    empreinte: str
    portees: tuple[str, ...]
    emise_le: float
    expire_le: float | None = None      # posé au moment de la rotation
    revoquee: bool = False


@dataclass
class Cles:
    """Le trousseau. Une clé par salon, révocable seule — contrairement à un
    secret partagé qui, lui, voit tous les salons à la fois."""

    horloge: Callable[[], float] = time.time
    _cles: list[Cle] = field(default_factory=list)
    _compteur: int = 0

    def emettre(self, tenant: str, portees: list[str] | None = None) -> str:
        self._compteur += 1
        secret = PREFIXE + secrets.token_urlsafe(24)
        self._cles.append(Cle(identifiant=f"cle-{self._compteur:04d}", tenant=tenant,
                              empreinte=_empreinte(secret),
                              portees=tuple(portees or ["agenda:lire", "agenda:ecrire"]),
                              emise_le=self.horloge()))
        return secret

    def verifier(self, secret: str, portee_requise: str | None = None) -> Cle:
        empreinte = _empreinte(secret)
        maintenant = self.horloge()
        for cle in self._cles:
            # A temps constant : c'est la seule primitive d'authentification du
            # depot, et une comparaison naive fuit par le temps de reponse.
            if not compare_digest(cle.empreinte, empreinte):
                continue
            if cle.revoquee:
                raise CleRefusee("clé révoquée")
            if cle.expire_le is not None and maintenant >= cle.expire_le:
                raise CleRefusee("clé expirée après rotation")
            if portee_requise and portee_requise not in cle.portees:
                raise CleRefusee(f"portée manquante : {portee_requise}")
            return cle
        raise CleRefusee("clé inconnue")

    def tourner(self, tenant: str, recouvrement_s: float = 300.0) -> str:
        """Émet une nouvelle clé, et fait expirer l'ancienne **plus tard**.

        La fenêtre de recouvrement n'est pas un confort : les requêtes déjà
        parties portent encore l'ancienne clé, et les couper ferait tomber des
        appels en cours.
        """
        maintenant = self.horloge()
        for cle in self._cles:
            if cle.tenant == tenant and not cle.revoquee and cle.expire_le is None:
                cle.expire_le = maintenant + recouvrement_s
        return self.emettre(tenant)

    def revoquer(self, identifiant: str) -> bool:
        for cle in self._cles:
            if cle.identifiant == identifiant:
                cle.revoquee = True
                return True
        return False

    def inventaire(self) -> list[dict[str, Any]]:
        """Ce qu'on peut montrer : jamais le secret, seulement son empreinte."""
        return [{"identifiant": c.identifiant, "tenant": c.tenant,
                 "empreinte": c.empreinte[:12], "portees": list(c.portees),
                 "revoquee": c.revoquee, "expire_le": c.expire_le} for c in self._cles]


@dataclass
class Limiteur:
    """Fenêtre glissante, par locataire et par adresse."""

    par_minute: int = PAR_MINUTE_PAR_DEFAUT
    par_minute_adresse: int = PAR_MINUTE_ADRESSE_PAR_DEFAUT
    horloge: Callable[[], float] = time.time
    _par_tenant: dict[str, deque] = field(default_factory=dict)
    _par_adresse: dict[str, deque] = field(default_factory=dict)

    def autoriser(self, tenant: str, adresse: str) -> None:
        maintenant = self.horloge()
        self._verifier(self._par_tenant, tenant, self.par_minute, maintenant,
                       f"locataire {tenant}")
        self._verifier(self._par_adresse, adresse, self.par_minute_adresse, maintenant,
                       f"adresse {adresse}")

    def _oublier_les_inactifs(self, table: dict, maintenant: float) -> None:
        """Une entree par adresse jamais purgee, sur un service expose, c'est une
        fuite de memoire lente. On oublie ce qui est sorti de la fenetre."""
        for cle in [c for c, passages in table.items()
                    if not passages or maintenant - passages[-1] >= FENETRE_S]:
            del table[cle]

    def _verifier(self, table: dict, cle: str, plafond: int, maintenant: float,
                  motif: str) -> None:
        self._oublier_les_inactifs(table, maintenant)
        passages = table.setdefault(cle, deque())
        while passages and maintenant - passages[0] >= FENETRE_S:
            passages.popleft()
        if len(passages) >= plafond:
            # On dit QUAND réessayer : un refus sans délai fait boucler l'appelant.
            raise TropDeDemandes(motif, FENETRE_S - (maintenant - passages[0]))
        passages.append(maintenant)
