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
import time
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
from standard.regles import (
    DUREE_MAXIMALE_D_APPEL_S,
    DUREE_MINIMALE_POUR_UNE_RELANCE_MS,
    SILENCE_AVANT_DE_RENDRE_LA_LIGNE_S,
    SEUIL_BRUITE_DB,
    SEUIL_PAROLE,
    SILENCE_DE_FIN_MS,
)

PANNES_AVANT_TRANSFERT = 2

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
    seuil_bruite_db: int = SEUIL_BRUITE_DB

    identifiant: str | None = None
    fermee: bool = False
    rsb_db: float | None = None
    audio_recu: int = 0
    saisie_terminee: bool = False
    interruptions: int = 0
    trames_ignorees: int = 0
    premiers_fragments_ms: list = field(default_factory=list)
    # T6 de docs/17 : une ligne par tour. Sans elles, « l'agent est lent » n'est
    # pas diagnosticable — et la mesure 13 dit que c'est le delai avant premier
    # fragment qui signale une machine pleine, pas la charge processeur.
    mesures: list = field(default_factory=list)
    debut: float = field(default_factory=time.monotonic)
    annonce_delivree: bool = False
    fin_demandee: bool = False      # l'agent a rendu la ligne
    raison_de_fin: str = ""         # « demarchage » ou « fin » : ce n'est pas pareil
    numero_connu: object = None     # rend l'identifiant d'appelant, s'il existe
    horloge: object = time.monotonic
    _dernier_mot: float = 0.0       # quand l'appelant a parle pour la derniere fois
    pannes: int = 0
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
    _annonce_en_cours: bool = False
    _amorcage: bool = False
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

    def __post_init__(self):
        # L'horloge est injectable (les tests avancent le temps a la main) : le
        # depart doit venir d'ELLE, sinon les bornes comparent deux horloges.
        self.debut = self.horloge()
        self._dernier_mot = self.debut

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
        sortant = self._jouer(phrase, annonce=True)
        if not sortant:
            self.annonce_delivree = True     # rien a dire : rien a proteger
        return sortant

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
            paquet = self._a_dire.pop(0) if self._a_dire else None
            # L'annonce legale est delivree quand son DERNIER paquet est parti —
            # pas quand la file se vide pendant l'amorcage de la synthese, ou le
            # premier paquet est aussitot remis dans la file par `_jouer`.
            if (self._annonce_en_cours and not self._amorcage
                    and not self._a_dire and self._source is None):
                self._annonce_en_cours = False
                self.annonce_delivree = True
            return paquet

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
            if self.fermee:
                # Ce qui suit un raccrochage dans le meme paquet TCP appartient a
                # un appel qui n'existe plus.
                self.trames_ignorees += 1
                continue
            sortant += self._traiter(trame)
        return sortant

    def _traiter(self, trame: Trame) -> list[bytes]:
        """Le bord telephonique n'est pas sous notre controle.

        Un UUID de cinq octets, un DTMF vide : un octet de travers ne vaut pas
        un raccrochage. On compte, on ignore, et l'appel continue.
        """
        try:
            return self._traiter_trame(trame)
        except ValueError:
            self.trames_ignorees += 1
            return []

    def _traiter_trame(self, trame: Trame) -> list[bytes]:
        if trame.est_fin:
            self.fermee = True
            return []
        if trame.est_erreur:
            # Une erreur du bord telephonique est gardee, jamais avalee.
            self.erreurs.append(trame.charge)
            return []
        if trame.est_uuid:
            self.identifiant = trame.uuid()
            # Le plan de numerotation a pu deposer l'identifiant d'appelant
            # avant de brancher l'audio : c'est le seul moment ou l'on peut le
            # relier a cet appel-ci.
            if self.numero_connu is not None:
                numero = self.numero_connu(self.identifiant)
                poser = getattr(self.agent, "poser_le_numero", None)
                if numero and callable(poser):
                    poser(numero)
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

        maintenant = self.horloge()
        if not self._dernier_mot:
            self._dernier_mot = self.debut
        if self._borne_depassee(maintenant):
            return self._rendre_la_ligne()

        if _amplitude(trame.charge) >= SEUIL_PAROLE:
            if not self._a_parle:
                # Le pre-roll part AVANT la premiere syllabe : mesure 9, un
                # moteur streaming perd un premier mot sur quatre, et c'est celui
                # qui porte le « zero » d'un numero ou le « non » d'un refus.
                garde = self._tampon.vider()
                if garde:
                    self._audio.extend(garde)
            self._a_parle = True
            self._dernier_mot = maintenant
            self._silence_ms = 0
            self._audio.extend(trame.charge)
            self._parole_continue_ms += DUREE_PAQUET_MS
            # On ne coupe qu'apres une parole assez longue pour ne pas etre un
            # « mm », une porte qui claque, ou notre propre voix qui revient.
            # L'annonce legale ne se coupe pas. Trouve en jouant un vrai appel :
            # un appelant qui parle en meme temps la faisait interrompre, et
            # l'obligation d'information de l'AI Act tombait avec elle. Apres
            # elle, tout est interruptible — c'est la premiere phrase, et elle
            # seule, qui doit etre entendue.
            if (self.en_train_de_parler and self.annonce_delivree
                    and self._parole_continue_ms >= self.duree_minimale_interruption_ms):
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

    @property
    def duree_s(self) -> float:
        """Depuis le decrochage. Elle valait zero pour tous les appels."""
        # Deux decimales : un appel transfere au premier mot dure quelques
        # centiemes, et un arrondi au dixieme le ramenait a zero — c'est-a-dire
        # a la valeur ecrite en dur qu'on vient de corriger.
        return round(time.monotonic() - self.debut, 2)

    def _borne_depassee(self, maintenant: float) -> bool:
        """Deux bornes, et elles ne se confondent pas : le silence du debut
        (personne n'a parle) et la duree totale (quelque chose est coince)."""
        if maintenant - self._dernier_mot >= SILENCE_AVANT_DE_RENDRE_LA_LIGNE_S:
            self._motif_de_borne = "silence"
            return True
        if maintenant - self.debut >= DUREE_MAXIMALE_D_APPEL_S:
            self._motif_de_borne = "trop long"
            return True
        return False

    def _rendre_la_ligne(self) -> list[bytes]:
        """On prend conge — poliment, parce qu'un client peut etre revenu juste
        au moment ou l'on raccroche — et le serveur ferme."""
        if self.fin_demandee:
            return []
        self.fin_demandee = True
        self.raison_de_fin = getattr(self, "_motif_de_borne", "silence")
        return self._jouer("Je ne vous entends plus. Bonne journée !")

    def _fin_de_tour(self) -> list[bytes]:
        """L'appelant a fini de parler : on transcrit, on repond, on rejoue."""
        import uuid

        depart = time.perf_counter()
        mesure = {
            "speech_id": uuid.uuid4().hex[:12],
            # Le temps qu'il a fallu pour decider que l'appelant avait fini :
            # c'est un choix de reglage, et il se relit ici.
            "fin_de_parole_ms": self.silence_de_fin_ms,
            "transcription_ms": 0.0, "agent_ms": 0.0,
            "premier_fragment_ms": 0.0, "total_ms": 0.0,
        }
        self.mesures.append(mesure)
        audio = reechantillonner(bytes(self._audio), self._frequence_entrante,
                                 self.frequence_moteur)
        # Mesure 10 : a 10-15 dB le taux d'erreur double SUR LES ENTITES. L'agent
        # doit le savoir pour changer de strategie — passer au clavier des le
        # premier essai plutot qu'attendre deux echecs.
        self.rsb_db = estimer_rsb_db(bytes(self._fond), bytes(self._audio))
        bruite = self.rsb_db is not None and self.rsb_db < self.seuil_bruite_db
        self._audio.clear()
        self._fond.clear()
        self._a_parle = False
        self._silence_ms = 0
        try:
            texte = self.transcrire(audio, self.frequence_moteur)
            mesure["transcription_ms"] = (time.perf_counter() - depart) * 1000
        except Exception:
            # Une panne du moteur — reseau coupe, 429, moteur absent — ne doit
            # jamais se traduire par un silence : c'est le pire etat d'un
            # standard, la ligne ouverte et personne au bout.
            return self._panne("Je n'ai pas réussi à vous entendre, "
                               "pouvez-vous répéter ?")
        if not texte:
            # Le silence est le pire etat d'un standard : si l'appelant a
            # vraiment parle, on relance plutot que de laisser la ligne ouverte
            # (banc du 19/09, un « oui » revenu vide du moteur).
            assez_parle = (len(audio) / 2 / self.frequence_moteur * 1000
                           >= DUREE_MINIMALE_POUR_UNE_RELANCE_MS)
            relancer = getattr(self.agent, "rien_entendu", None)
            if assez_parle and callable(relancer):
                return self._dire(relancer())
            return []

        avant_l_agent = time.perf_counter()
        try:
            reponse = self.agent.tour(texte, bruite=bruite)
        except Exception:
            return self._panne("Je rencontre un problème technique, un instant.")
        mesure["agent_ms"] = (time.perf_counter() - avant_l_agent) * 1000

        self.pannes = 0
        morceaux = self._dire(reponse)
        if self.premiers_fragments_ms:
            mesure["premier_fragment_ms"] = self.premiers_fragments_ms[-1]
        mesure["total_ms"] = (time.perf_counter() - depart) * 1000
        return morceaux

    def _dire(self, reponse) -> list[bytes]:
        """Joue une reponse d'agent — et honore ce qu'elle demande ensuite."""
        morceaux = self._jouer(reponse.phrase)
        if getattr(self.agent, "fin_demandee", False):
            # La phrase se dit en ENTIER avant que la ligne ne se ferme : c'est
            # le serveur qui raccroche, une fois la file vidée. Le motif compte :
            # un au revoir poli n'est pas un démarchage filtré, et c'est ce mot
            # que la console montre au commerçant.
            self.fin_demandee = True
            self.raison_de_fin = getattr(reponse, "genre", "") or "fin"
        if getattr(reponse, "genre", "") == "transfert":
            # Le bord telephonique doit VRAIMENT passer la main : une phrase sans
            # signal, c'est raccrocher au nez de l'appelant en musique.
            self.transfert_demande = True
        return morceaux

    def _panne(self, phrase: str) -> list[bytes]:
        """L'agent parle, ou il passe la main. Il ne se tait jamais.

        Insister ne repare pas une panne : au deuxieme tour perdu, on transfere
        plutot que de faire repeter un appelant a qui l'on ne peut rien offrir.
        """
        self.pannes += 1
        if self.pannes >= PANNES_AVANT_TRANSFERT:
            self.transfert_demande = True
            phrase = "Je rencontre un problème technique. Je vous passe quelqu'un."
        return self._jouer(phrase)

    # --- le clavier (regle T7) ----------------------------------------------

    def attendre_un_numero(self) -> None:
        """Bascule au clavier : apres deux echecs a l'oral, c'est le seul filet."""
        self._attend_un_numero = True
        self.saisie_terminee = False
        self._chiffres.clear()

    def _chiffre(self, touche: str) -> list[bytes]:
        if not self._attend_un_numero:
            # L'agent a demande un numero a voix haute : un appelant qui le
            # compose sans attendre qu'on l'y invite doit etre entendu. Banc du
            # 20/09 : ses touches tombaient dans le vide, et il ne les retape pas.
            if touche.isdigit() and getattr(self.agent, "attend_un_numero", False):
                self._attend_un_numero = True
                self._chiffres.clear()
                self.saisie_terminee = False
            else:
                return []                            # un appui hors saisie ne pollue rien
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

    def _jouer(self, texte: str, annonce: bool = False) -> list[bytes]:
        """Synthetise et decoupe en paquets de vingt millisecondes.

        C'est le rythme qu'attend un canal telephonique : 160 echantillons de
        16 bits a 8 kHz. Envoyer plus gros fait saccader, plus fin ne sert a rien.
        """
        with self._parole_verrou:
            depart = time.perf_counter()
            self._annonce_en_cours = annonce
            self._source = iter(self.synthetiser(texte))
            # On amorce un premier paquet tout de suite : le reste suivra a la
            # demande, pendant que l'agent parle deja.
            self._amorcage = True
            try:
                premier = self.emettre()
            finally:
                self._amorcage = False
            # C'est CE delai qui dit qu'une machine est pleine — bien avant la
            # charge processeur, qui reste basse jusqu'au bout (mesure 13).
            self.premiers_fragments_ms.append((time.perf_counter() - depart) * 1000)
            if premier is None:
                if annonce:
                    self.annonce_delivree = True   # rien a dire : rien a proteger
                    self._annonce_en_cours = False
                return []
            self._a_dire.insert(0, premier)
            return list(self._a_dire)

    def _empiler(self, fragment: bytes) -> None:
        # Toujours appele sous `_parole_verrou`.
        audio = reechantillonner(fragment, self.frequence_moteur, 8000) \
            if self.frequence_moteur != 8000 else fragment
        self._a_dire.extend(encoder_audio(audio, TYPE_AUDIO_8K, PAQUET_20MS_8K))
