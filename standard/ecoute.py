"""L'ecoute — de l'audio au texte, sans perdre le premier mot.

Trois mesures commandent ce module.

**Mesure 9** : un moteur streaming perd le premier mot d'un enonce sur quatre —
« Mon numero c'est le zero six » devient « NUMERO C'EST LE ZERO SIX ». Or la
syllabe perdue est celle qui porte le « zero » d'un numero ou le « non » d'un
refus. Le flux est donc ouvert et alimente **avant** que l'appelant ne parle, et
le detecteur garde l'audio d'**avant** son seuil de declenchement.

**Mesure 10** : a 10-15 dB — l'environnement reel d'un appelant, rue ou voiture —
le WER double, et il double **sur les entites**. Le rapport signal/bruit est donc
estime des les premieres secondes et transmis a la decision, qui change de
strategie plutot que de subir.

**Mesure 4** : une connexion rouverte coute 2 040 ms, gardee ouverte 378 ms. Les
connexions s'ouvrent au demarrage du service, jamais a l'arrivee d'un appel.
"""

from __future__ import annotations

import array
import math
import threading
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator

from standard.regles import PREROLL_MS, SEUIL_BRUITE_DB, SEUIL_PAROLE


def _amplitude_moyenne(morceau: bytes) -> float:
    if len(morceau) < 2:
        return 0.0
    echantillons = array.array("h")
    echantillons.frombytes(morceau[: len(morceau) - len(morceau) % 2])
    if not echantillons:
        return 0.0
    return sum(abs(e) for e in echantillons) / len(echantillons)


def estimer_rsb_db(fond: bytes, parole: bytes) -> float | None:
    """Rapport signal/bruit, en decibels, a partir de deux extraits.

    Calcul de deux lignes, connu avant la premiere question : il ne coute rien et
    il decide de la strategie de capture des entites.
    """
    bruit = _amplitude_moyenne(fond)
    signal = _amplitude_moyenne(parole)
    if signal <= 0:
        return 0.0
    if bruit <= 0:
        return 60.0                      # pas de bruit mesurable : plafond arbitraire
    return round(20 * math.log10(signal / bruit), 1)


class TamponDePreRoll:
    """Garde les derniers millisecondes d'audio, et rien de plus.

    C'est ce tampon qui sauve le premier mot : quand le seuil de parole est
    franchi, ce qui part au moteur commence **avant** le declenchement.
    """

    def __init__(self, duree_ms: int = PREROLL_MS, taux: int = 8000):
        self.octets_max = int(duree_ms / 1000 * taux) * 2
        self._morceaux: deque[bytes] = deque()
        self._taille = 0

    def ajouter(self, morceau: bytes) -> None:
        self._morceaux.append(morceau)
        self._taille += len(morceau)
        while self._taille > self.octets_max and self._morceaux:
            perdu = self._morceaux.popleft()
            self._taille -= len(perdu)

    def vider(self) -> bytes:
        garde = b"".join(self._morceaux)
        self._morceaux.clear()
        self._taille = 0
        return garde[-self.octets_max:] if len(garde) > self.octets_max else garde


@dataclass
class Transcription:
    texte: str
    rsb_db: float | None = None
    bruite: bool = False


class Ecoute:
    """Alimente le moteur en continu, et lui donne l'audio d'avant le seuil."""

    def __init__(self, moteur: Callable[[Iterator[bytes]], str],
                 preroll_ms: int = PREROLL_MS, taux: int = 8000,
                 seuil_bruite_db: int = SEUIL_BRUITE_DB):
        self.moteur = moteur
        self.taux = taux
        self.seuil_bruite_db = seuil_bruite_db
        self._tampon = TamponDePreRoll(preroll_ms, taux)
        self._file: deque[bytes] = deque()
        self._fond: list[bytes] = []
        self._parole: list[bytes] = []
        self._ouverte = False
        self._a_parle = False

    def ouvrir(self) -> None:
        """Ouvre le flux **avant** que l'appelant ne parle."""
        self._ouverte = True

    def alimenter(self, morceau: bytes) -> None:
        if not self._ouverte:
            raise RuntimeError("le flux doit etre ouvert avant que l'appelant ne parle")
        if _amplitude_moyenne(morceau) >= SEUIL_PAROLE:
            if not self._a_parle:
                # Le seuil vient d'etre franchi : on envoie d'abord ce qui precede.
                self._a_parle = True
                garde = self._tampon.vider()
                if garde:
                    self._file.append(garde)
            self._parole.append(morceau)
            self._file.append(morceau)
        else:
            self._fond.append(morceau)
            self._tampon.ajouter(morceau)

    def fermer(self) -> Transcription:
        texte = self.moteur(iter(list(self._file)))
        rsb = estimer_rsb_db(b"".join(self._fond), b"".join(self._parole))
        return Transcription(texte=texte if isinstance(texte, str) else str(texte),
                             rsb_db=rsb,
                             bruite=rsb is not None and rsb < self.seuil_bruite_db)


@dataclass
class ReserveDeConnexions:
    """Des connexions ouvertes au demarrage, et maintenues ouvertes.

    Mesure 4 : 2 040 ms pour une connexion neuve contre 378 ms pour une connexion
    gardee, avec un minimum a 85 ms vers un fournisseur americain. La distance ne
    peut pas expliquer 400 ms — ce sont le DNS et les deux poignees de main,
    repayes a chaque tour de parole si le client ne reutilise rien.
    """

    fabrique: Callable[[], Any]
    taille: int = 4
    maintenir: Callable[[Any], None] | None = None
    _libres: deque = field(default_factory=deque, repr=False)
    _toutes: list = field(default_factory=list, repr=False)
    _verrou: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def amorcer(self) -> None:
        """A appeler au demarrage du service. Jamais a l'arrivee d'un appel."""
        with self._verrou:
            while len(self._toutes) < self.taille:
                connexion = self.fabrique()
                self._toutes.append(connexion)
                self._libres.append(connexion)

    @contextmanager
    def emprunter(self):
        with self._verrou:
            connexion = self._libres.popleft() if self._libres else None
        if connexion is None:
            # La reserve est vide : on attend une connexion plutot que d'en ouvrir
            # une neuve, qui couterait cinq fois plus cher que l'attente.
            connexion = self.fabrique()
            with self._verrou:
                self._toutes.append(connexion)
        try:
            yield connexion
        finally:
            with self._verrou:
                self._libres.append(connexion)

    def entretenir(self) -> None:
        """Sonde de maintien : sans elle, le fournisseur ferme une connexion
        inactive et le premier appel apres un creux repaie les deux secondes."""
        if self.maintenir is None:
            return
        for connexion in list(self._toutes):
            self.maintenir(connexion)
