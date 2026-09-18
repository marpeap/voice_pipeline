"""La session telephonique — le protocole branche sur le pipeline.

Un appel entier se deroule ici : les trames arrivent, l'audio s'accumule, le
silence declenche un tour de parole, la reponse repart en trames de vingt
millisecondes, et les chiffres composes au clavier sont ramasses.

Deux regles mesurees s'y appliquent sans discussion :

- **aucun processus externe par fragment audio** (mesure 6 : 11 ms de travail
  reel contre 45 ms rien que pour lancer `ffmpeg`) — le reechantillonnage se fait
  dans le processus ;
- **le flux d'ecoute est nourri des l'ouverture**, avant que l'appelant ne parle
  (mesure 9 : un moteur streaming perd un premier mot sur quatre).
"""

from __future__ import annotations

import array
from dataclasses import dataclass, field
from typing import Callable

from standard.audiosocket import (
    FREQUENCES,
    PAQUET_20MS_8K,
    TYPE_AUDIO_8K,
    Decodeur,
    Trame,
    encoder_audio,
)
from standard.regles import SEUIL_PAROLE

SILENCE_DE_FIN_MS = 700       # au-dela, on considere que l'appelant a fini de parler
DUREE_PAQUET_MS = 20
FIN_DE_SAISIE = "#"
EFFACER_LA_SAISIE = "*"
LONGUEUR_NUMERO = 10


def reechantillonner(audio: bytes, depuis: int, vers: int) -> bytes:
    """Change la frequence **dans le processus**, par interpolation lineaire.

    Ni `ffmpeg`, ni `audioop` : le premier coute un lancement de processus par
    fragment, le second a disparu de la bibliotheque standard en 3.13. Vingt
    lignes ici valent mieux qu'une dependance qui s'evapore.
    """
    if depuis == vers or not audio:
        return audio
    entree = array.array("h")
    entree.frombytes(audio[: len(audio) - len(audio) % 2])
    if not entree:
        return b""
    nombre = max(1, round(len(entree) * vers / depuis))
    sortie = array.array("h", [0] * nombre)
    for index in range(nombre):
        position = index * (len(entree) - 1) / max(1, nombre - 1) if nombre > 1 else 0
        gauche = int(position)
        droite = min(gauche + 1, len(entree) - 1)
        reste = position - gauche
        sortie[index] = int(entree[gauche] * (1 - reste) + entree[droite] * reste)
    return sortie.tobytes()


def _amplitude(morceau: bytes) -> float:
    echantillons = array.array("h")
    echantillons.frombytes(morceau[: len(morceau) - len(morceau) % 2])
    return sum(abs(e) for e in echantillons) / len(echantillons) if echantillons else 0.0


@dataclass
class SessionTelephonique:
    """Un appel. Un objet par appel, detruit avec lui."""

    agent: object                                   # ce qui sait tenir une conversation
    transcrire: Callable[[bytes, int], str]         # audio -> texte
    synthetiser: Callable[[str], list[bytes]]       # texte -> fragments audio
    frequence_moteur: int = 16000
    silence_de_fin_ms: int = SILENCE_DE_FIN_MS

    identifiant: str | None = None
    fermee: bool = False
    audio_recu: int = 0
    saisie_terminee: bool = False
    erreurs: list[bytes] = field(default_factory=list)

    _decodeur: Decodeur = field(default_factory=Decodeur, repr=False)
    _audio: bytearray = field(default_factory=bytearray, repr=False)
    _frequence_entrante: int = TYPE_AUDIO_8K and 8000
    _silence_ms: int = 0
    _a_parle: bool = False
    _chiffres: list[str] = field(default_factory=list, repr=False)
    _attend_un_numero: bool = False

    # --- ouverture ----------------------------------------------------------

    def ouvrir(self) -> list[bytes]:
        """Joue l'annonce. Elle est la premiere phrase, jamais une autre."""
        return self._jouer(self.agent.salutation())

    # --- reception ----------------------------------------------------------

    def recevoir(self, morceau: bytes) -> list[bytes]:
        """Avale un morceau de flux TCP et rend ce qu'il faut jouer en retour."""
        if self.fermee:
            raise RuntimeError("session fermee : l'appelant a raccroche")
        sortant: list[bytes] = []
        for trame in self._decodeur.avaler(morceau):
            sortant += self._traiter(trame)
        return sortant

    def _traiter(self, trame: Trame) -> list[bytes]:
        if trame.est_fin:
            self.fermee = True
            return []
        if trame.est_erreur:
            # Une erreur du bord telephonique est gardee, jamais avalee.
            self.erreurs.append(trame.charge)
            return []
        if trame.est_uuid:
            self.identifiant = trame.uuid()
            return []
        if trame.est_dtmf:
            return self._chiffre(trame.chiffre())
        if trame.est_audio:
            return self._audio_entrant(trame)
        return []                                    # type inconnu : on l'ignore

    def _audio_entrant(self, trame: Trame) -> list[bytes]:
        self._frequence_entrante = trame.frequence() or self._frequence_entrante
        self._audio.extend(trame.charge)
        self.audio_recu += len(trame.charge)

        if _amplitude(trame.charge) >= SEUIL_PAROLE:
            self._a_parle = True
            self._silence_ms = 0
            return []

        if not self._a_parle:
            return []                                # silence d'avant la parole
        self._silence_ms += DUREE_PAQUET_MS
        if self._silence_ms < self.silence_de_fin_ms:
            return []
        return self._fin_de_tour()

    def _fin_de_tour(self) -> list[bytes]:
        """L'appelant a fini de parler : on transcrit, on repond, on rejoue."""
        audio = reechantillonner(bytes(self._audio), self._frequence_entrante,
                                 self.frequence_moteur)
        self._audio.clear()
        self._a_parle = False
        self._silence_ms = 0
        texte = self.transcrire(audio, self.frequence_moteur)
        if not texte:
            return []
        reponse = self.agent.tour(texte)
        return self._jouer(reponse.phrase)

    # --- le clavier (regle T7) ----------------------------------------------

    def attendre_un_numero(self) -> None:
        """Bascule au clavier : apres deux echecs a l'oral, c'est le seul filet."""
        self._attend_un_numero = True
        self.saisie_terminee = False
        self._chiffres.clear()

    def _chiffre(self, touche: str) -> list[bytes]:
        if not self._attend_un_numero:
            return []                                # un appui hors saisie ne pollue rien
        if touche == EFFACER_LA_SAISIE:
            self._chiffres.clear()
            return []
        if touche == FIN_DE_SAISIE:
            self.saisie_terminee = True
            self._attend_un_numero = False
            return []
        if touche.isdigit():
            self._chiffres.append(touche)
            if len(self._chiffres) == LONGUEUR_NUMERO:
                self.saisie_terminee = True
                self._attend_un_numero = False
        return []

    def numero_compose(self) -> str | None:
        """Le numero saisi, **seulement s'il en est un** : dix chiffres, pas neuf.

        On ne complete jamais une saisie trop courte — c'est la meme regle qu'a
        l'oral (T4), et pour la meme raison.
        """
        numero = "".join(self._chiffres)
        return numero if len(numero) == LONGUEUR_NUMERO else None

    # --- emission -----------------------------------------------------------

    def _jouer(self, texte: str) -> list[bytes]:
        """Synthetise et decoupe en paquets de vingt millisecondes.

        C'est le rythme qu'attend un canal telephonique : 160 echantillons de
        16 bits a 8 kHz. Envoyer plus gros fait saccader, plus fin ne sert a rien.
        """
        morceaux: list[bytes] = []
        for fragment in self.synthetiser(texte):
            audio = reechantillonner(fragment, self.frequence_moteur, 8000) \
                if self.frequence_moteur != 8000 else fragment
            morceaux += encoder_audio(audio, TYPE_AUDIO_8K, PAQUET_20MS_8K)
        return morceaux
