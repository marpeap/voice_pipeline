"""Le serveur de la toile — la page, et le canal audio qui la prolonge.

Il remplace l'opérateur téléphonique, et **rien d'autre** : chaque connexion
ouvre exactement la même `SessionTelephonique` qu'un appel AudioSocket, avec le
même agent, la même annonce légale et le même journal. Un défaut qui
n'apparaîtrait que d'un côté voudrait dire qu'on entretient deux produits.

Le format transporté est celui du téléphone — PCM 16 bits mono 8 kHz, paquets
de vingt millisecondes — pour que les mesures faites au téléphone restent
vraies ici, et inversement.
"""

from __future__ import annotations

import socket
import threading
from pathlib import Path

from standard.session import SessionTelephonique
from standard.toile import (
    OPCODE_BINAIRE,
    OPCODE_SUITE,
    OPCODE_FERMETURE,
    OPCODE_PING,
    OPCODE_PONG,
    OPCODE_TEXTE,
    decoder_une_trame,
    encoder_une_trame,
    poignee_de_main,
)

PAQUET_20MS = 320
"""160 échantillons de 16 bits à 8 kHz : le rythme du canal téléphonique, gardé
tel quel pour que les deux transports se mesurent avec la même règle."""

HOTE_PAR_DEFAUT = "127.0.0.1"
PORT_PAR_DEFAUT = 8093


class ServeurDeToile:
    """Sert la page d'essai et porte les conversations qui en partent."""

    def __init__(self, fabrique_agent, transcrire, synthetiser,
                 page: Path | str | None = None, nom_du_salon: str = "le salon",
                 hote: str = HOTE_PAR_DEFAUT, port: int = PORT_PAR_DEFAUT,
                 sur_fin=None, seuil_bruite_db: int | None = None,
                 appels_simultanes_max: int | None = None):
        self.fabrique_agent = fabrique_agent
        self.transcrire = transcrire
        self.synthetiser = synthetiser
        self.nom_du_salon = nom_du_salon
        # La page a UNE source : celle que Vercel publie. Le standard sert le
        # meme fichier, avec le nom du salon substitue — deux copies auraient
        # diverge des la premiere correction.
        self.page = Path(page) if page else (
            Path(__file__).resolve().parent.parent / "toile" / "index.html")
        self.hote, self.port = hote, port
        self.sur_fin = sur_fin
        self.seuil_bruite_db = seuil_bruite_db
        self.appels_simultanes_max = appels_simultanes_max
        self.appels_en_cours = 0
        self.appels_total = 0
        self.erreur: str | None = None
        self._prise: socket.socket | None = None
        self._fil: threading.Thread | None = None
        self._arret = threading.Event()
        self._verrou = threading.Lock()

    # --- cycle de vie -------------------------------------------------------

    def demarrer(self) -> None:
        if self._prise is not None:
            return
        try:
            prise = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            prise.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            prise.bind((self.hote, self.port))
            prise.listen(8)
        except OSError as erreur:
            # Comme le point d'etat : un port pris n'empeche pas le telephone
            # de sonner. On le dit, et le reste tourne.
            self.erreur = f"toile indisponible sur {self.hote}:{self.port} — {erreur}"
            print(self.erreur, flush=True)
            return
        self.port = prise.getsockname()[1]
        prise.settimeout(0.2)
        self._prise = prise
        self._arret.clear()
        self._fil = threading.Thread(target=self._accepter, name="toile", daemon=True)
        self._fil.start()

    def arreter(self, attente_s: float = 3.0) -> None:
        self._arret.set()
        if self._fil is not None:
            self._fil.join(timeout=attente_s)
        if self._prise is not None:
            try:
                self._prise.close()
            except OSError:
                pass
        self._prise, self._fil = None, None

    # --- accueil ------------------------------------------------------------

    def _accepter(self) -> None:
        while not self._arret.is_set():
            try:
                connexion, _ = self._prise.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=self._servir, args=(connexion,),
                             daemon=True).start()

    def _servir(self, connexion: socket.socket) -> None:
        try:
            connexion.settimeout(5.0)
            entete = self._lire_l_entete(connexion)
            if entete is None:
                return
            lignes = entete.decode("latin-1").split("\r\n")
            entetes = {}
            for ligne in lignes[1:]:
                if ":" in ligne:
                    cle, _, valeur = ligne.partition(":")
                    entetes[cle.strip().lower()] = valeur.strip()

            reponse = poignee_de_main(entetes)
            if reponse is None:
                self._servir_la_page(connexion)
                return
            connexion.sendall(reponse)
            self._conversation(connexion)
        except (OSError, ValueError):
            # Un navigateur qui ferme mal ne doit pas emporter le serveur.
            pass
        finally:
            try:
                connexion.close()
            except OSError:
                pass

    def _lire_l_entete(self, connexion: socket.socket) -> bytes | None:
        tampon = b""
        while b"\r\n\r\n" not in tampon:
            morceau = connexion.recv(4096)
            if not morceau:
                return None
            tampon += morceau
            if len(tampon) > 32768:
                return None
        return tampon.split(b"\r\n\r\n", 1)[0]

    def _servir_la_page(self, connexion: socket.socket) -> None:
        corps = self.page.read_text(encoding="utf-8").replace(
            "{{SALON}}", self.nom_du_salon).encode("utf-8")
        connexion.sendall(
            b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n"
            + f"Content-Length: {len(corps)}\r\n".encode()
            + b"Cache-Control: no-store\r\nConnection: close\r\n\r\n" + corps)

    # --- une conversation ---------------------------------------------------

    def _conversation(self, connexion: socket.socket) -> None:
        with self._verrou:
            if (self.appels_simultanes_max is not None
                    and self.appels_en_cours >= self.appels_simultanes_max):
                return
            self.appels_en_cours += 1
            self.appels_total += 1

        session = SessionTelephonique(
            agent=self.fabrique_agent(), transcrire=self.transcrire,
            synthetiser=self.synthetiser,
            **({"seuil_bruite_db": self.seuil_bruite_db}
               if self.seuil_bruite_db is not None else {}))
        session.identifiant = f"toile-{self.appels_total}"
        fini = threading.Event()
        emetteur = threading.Thread(
            target=self._emettre, args=(connexion, session, fini), daemon=True)
        try:
            session.ouvrir()
            emetteur.start()
            tampon = b""
            connexion.settimeout(0.2)
            while not self._arret.is_set() and not session.fermee:
                if session.fin_demandee and not session.en_train_de_parler:
                    break
                try:
                    morceau = connexion.recv(65536)
                except socket.timeout:
                    continue
                if not morceau:
                    break
                tampon += morceau
                while True:
                    opcode, charge, tampon = decoder_une_trame(tampon)
                    if opcode is None:
                        break
                    if opcode == OPCODE_FERMETURE:
                        session.fermee = True
                        break
                    if opcode == OPCODE_PING:
                        connexion.sendall(encoder_une_trame(charge, OPCODE_PONG))
                        continue
                    if opcode in (OPCODE_BINAIRE, OPCODE_SUITE):
                        self._avaler(session, charge)
        finally:
            fini.set()
            emetteur.join(timeout=1)
            if self.sur_fin:
                try:
                    self.sur_fin(session)
                except Exception:
                    pass
            with self._verrou:
                self.appels_en_cours -= 1

    def _avaler(self, session: SessionTelephonique, audio: bytes) -> None:
        """L'audio du navigateur, decoupe au rythme du canal.

        Le navigateur envoie ce que sa carte son lui donne : des morceaux de
        taille quelconque. La session, elle, raisonne en paquets de vingt
        millisecondes — c'est sur eux que reposent la detection de parole et
        toutes les mesures.
        """
        from standard.audiosocket import TYPE_AUDIO_8K, encoder

        for debut in range(0, len(audio) - PAQUET_20MS + 1, PAQUET_20MS):
            session.recevoir(encoder(TYPE_AUDIO_8K,
                                     audio[debut:debut + PAQUET_20MS]))

    def _emettre(self, connexion: socket.socket, session, fini: threading.Event) -> None:
        """La voix de l'agent, au rythme du canal — comme au téléphone.

        La session fabrique des trames AudioSocket : trois octets d'en-tete
        devant l'audio. Le navigateur, lui, attend du PCM nu — il fait
        `new Int16Array(octets)`, et 323 octets n'est pas un multiple de deux :
        il levait « byte length of Int16Array should be a multiple of 2 » a
        chaque paquet, et l'appelant n'entendait rien. On enleve l'en-tete ICI,
        au bord : la session garde un seul format pour les deux transports.
        """
        import time

        from standard.audiosocket import Decodeur, TYPE_AUDIO_8K

        decodeur = Decodeur()
        while not fini.is_set():
            paquet = session.emettre()
            if paquet is None:
                time.sleep(0.01)
                continue
            for trame in decodeur.avaler(paquet):
                # Une trame vide — ou d'un autre type que l'audio — n'a rien a
                # faire sur le canal du navigateur : il la jouerait comme un
                # blanc, ou s'y casserait.
                if trame.type != TYPE_AUDIO_8K or not trame.charge:
                    continue
                try:
                    connexion.sendall(encoder_une_trame(trame.charge, OPCODE_BINAIRE))
                except OSError:
                    return
            time.sleep(PAQUET_20MS / 2 / 8000)
