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
import threading
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
from standard.ecoute import TamponDePreRoll, estimer_rsb_db
from standard.regles import SEUIL_BRUITE_DB, SEUIL_PAROLE, SILENCE_DE_FIN_MS

# Interruption (barge-in). Etat de l'art releve le 19/09/2026 : ecart de reprise
# de parole de 200 a 400 ms, moins de 2 % d'interruptions a tort, coupure de la
# synthese en moins de 60 ms. Le garde-fou le plus efficace est une DUREE
# MINIMALE de parole avant de couper — il divise par plus de deux les
# interruptions a tort, la premiere cause etant l'echo de notre propre voix
# renvoye par le reseau telephonique.
DUREE_MINIMALE_INTERRUPTION_MS = 240
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
    duree_minimale_interruption_ms: int = DUREE_MINIMALE_INTERRUPTION_MS

    identifiant: str | None = None
    fermee: bool = False
    rsb_db: float | None = None
    audio_recu: int = 0
    saisie_terminee: bool = False
    interruptions: int = 0
    transfert_demande: bool = False
    preuve_d_annonce: dict | None = None
    erreurs: list[bytes] = field(default_factory=list)

    _decodeur: Decodeur = field(default_factory=Decodeur, repr=False)
    _audio: bytearray = field(default_factory=bytearray, repr=False)
    _fond: bytearray = field(default_factory=bytearray, repr=False)
    _tampon: TamponDePreRoll = field(default_factory=TamponDePreRoll, repr=False)
    _frequence_entrante: int = TYPE_AUDIO_8K and 8000
    _silence_ms: int = 0
    _a_parle: bool = False
    _chiffres: list[str] = field(default_factory=list, repr=False)
    _attend_un_numero: bool = False
    _a_dire: list[bytes] = field(default_factory=list, repr=False)
    _source: object = None                      # synthese en cours, consommee au fil de l'eau
    # Un verrou, parce que DEUX fils touchent a la parole : celui qui lit la
    # socket (et qui declenche une nouvelle phrase) et celui qui emet. Sans lui,
    # les deux entrent ensemble dans le meme generateur et Python leve
    # « generator already executing » — le fil d'emission meurt, et l'appel reste
    # ouvert en silence. Trouve par une seconde revue, invisible a 424 tests
    # parce que toutes les doublures synthetisaient en zero milliseconde.
    _parole_verrou: threading.RLock = field(default_factory=threading.RLock, repr=False)
    _parole_continue_ms: int = 0

    # --- ouverture ----------------------------------------------------------

    def _brancher_le_clavier(self) -> None:
        """Donne a l'agent le moyen de demander le clavier, et de recevoir sa saisie.

        Sans ce branchement, la regle T7 — apres deux echecs sur un numero, on
        bascule au clavier — restait une phrase dans un document : `session.py`
        savait ramasser les touches, et personne ne les lui demandait.
        """
        if hasattr(self.agent, "basculer_clavier"):
            self.agent.basculer_clavier = self.attendre_un_numero

    def ouvrir(self) -> list[bytes]:
        """Joue l'annonce, et **en garde la preuve**.

        L'AI Act ne demande pas seulement d'informer : il demande de pouvoir le
        prouver. Une annonce prononcee dont il ne reste aucune trace ne vaut rien
        le jour ou quelqu'un la conteste — et la sanction associee monte a 15 M€
        ou 3 % du chiffre d'affaires mondial.
        """
        from datetime import datetime, timezone

        from standard.conformite import verifier_annonce

        self._brancher_le_clavier()
        phrase = self.agent.salutation()
        verdict = verifier_annonce(phrase)
        self.preuve_d_annonce = {
            "phrase": phrase,
            "formulation": verdict.formulation,
            "conforme": verdict.conforme,
            "horodatage": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        return self._jouer(phrase)

    # --- ce que l'agent est en train de dire --------------------------------

    @property
    def en_train_de_parler(self) -> bool:
        with self._parole_verrou:
            return bool(self._a_dire) or self._source is not None

    @property
    def reste_a_emettre(self) -> int:
        """Paquets encore a jouer. Ils sont JETES si l'appelant reprend la parole :
        les reprendre apres l'interruption ferait parler l'agent par-dessus lui."""
        return len(self._a_dire)

    def emettre(self) -> bytes | None:
        """Le prochain paquet a envoyer, ou rien. C'est le serveur qui rythme.

        La synthese est consommee **au fil de l'eau** : le premier paquet part
        avant que la phrase entiere ne soit fabriquee. Materialiser d'abord,
        c'etait le defaut du binaire — 372 ms contre 162 (mesure 13).
        """
        with self._parole_verrou:
            if not self._a_dire and self._source is not None:
                source = self._source
                for fragment in source:
                    self._empiler(fragment)
                    if self._a_dire:
                        break
                else:
                    if self._source is source:
                        self._source = None
            return self._a_dire.pop(0) if self._a_dire else None

    def _interrompre(self) -> None:
        with self._parole_verrou:
            self.interruptions += 1
            self._a_dire.clear()
            self._source = None      # ce qui restait a synthetiser ne sera pas dit

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
        """Trie chaque paquet : parole, ou bruit de fond.

        Les deux servent. La parole part au moteur ; le fond sert a mesurer le
        rapport signal/bruit — et c'est lui, pas le texte, qui dit a l'agent
        qu'il doit changer de strategie (mesure 10).
        """
        self._frequence_entrante = trame.frequence() or self._frequence_entrante
        self.audio_recu += len(trame.charge)

        if _amplitude(trame.charge) >= SEUIL_PAROLE:
            if not self._a_parle:
                # Le pre-roll part AVANT la premiere syllabe : mesure 9, un
                # moteur streaming perd un premier mot sur quatre, et c'est celui
                # qui porte le « zero » d'un numero ou le « non » d'un refus.
                garde = self._tampon.vider()
                if garde:
                    self._audio.extend(garde)
            self._a_parle = True
            self._silence_ms = 0
            self._audio.extend(trame.charge)
            self._parole_continue_ms += DUREE_PAQUET_MS
            # On ne coupe qu'apres une parole assez longue pour ne pas etre un
            # « mm », une porte qui claque, ou notre propre voix qui revient.
            if self.en_train_de_parler and \
                    self._parole_continue_ms >= self.duree_minimale_interruption_ms:
                self._interrompre()
            return []

        self._parole_continue_ms = 0
        self._fond.extend(trame.charge)
        if not self._a_parle:
            self._tampon.ajouter(trame.charge)
            return []                                # silence d'avant la parole

        self._audio.extend(trame.charge)             # la fin de phrase compte aussi
        self._silence_ms += DUREE_PAQUET_MS
        if self._silence_ms < self.silence_de_fin_ms:
            return []
        return self._fin_de_tour()

    def _fin_de_tour(self) -> list[bytes]:
        """L'appelant a fini de parler : on transcrit, on repond, on rejoue."""
        audio = reechantillonner(bytes(self._audio), self._frequence_entrante,
                                 self.frequence_moteur)
        # Mesure 10 : a 10-15 dB le taux d'erreur double SUR LES ENTITES. L'agent
        # doit le savoir pour changer de strategie — passer au clavier des le
        # premier essai plutot qu'attendre deux echecs.
        self.rsb_db = estimer_rsb_db(bytes(self._fond), bytes(self._audio))
        bruite = self.rsb_db is not None and self.rsb_db < SEUIL_BRUITE_DB
        self._audio.clear()
        self._fond.clear()
        self._a_parle = False
        self._silence_ms = 0
        texte = self.transcrire(audio, self.frequence_moteur)
        if not texte:
            return []
        reponse = self.agent.tour(texte, bruite=bruite)
        morceaux = self._jouer(reponse.phrase)
        if getattr(reponse, "genre", "") == "transfert":
            # Le bord telephonique doit VRAIMENT passer la main : une phrase sans
            # signal, c'est raccrocher au nez de l'appelant en musique.
            self.transfert_demande = True
        return morceaux

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
                return self._rendre_le_numero()
        return []

    def _rendre_le_numero(self) -> list[bytes]:
        """Le numero complet repart vers l'agent, qui decide ce qu'il en fait."""
        numero = self.numero_compose()
        if numero is None or not hasattr(self.agent, "numero_au_clavier"):
            return []
        reponse = self.agent.numero_au_clavier(numero)
        return self._jouer(reponse.phrase)

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
        with self._parole_verrou:
            self._source = iter(self.synthetiser(texte))
            # On amorce un premier paquet tout de suite : le reste suivra a la
            # demande, pendant que l'agent parle deja.
            premier = self.emettre()
            if premier is None:
                return []
            self._a_dire.insert(0, premier)
            return list(self._a_dire)

    def _empiler(self, fragment: bytes) -> None:
        # Toujours appele sous `_parole_verrou`.
        audio = reechantillonner(fragment, self.frequence_moteur, 8000) \
            if self.frequence_moteur != 8000 else fragment
        self._a_dire.extend(encoder_audio(audio, TYPE_AUDIO_8K, PAQUET_20MS_8K))
