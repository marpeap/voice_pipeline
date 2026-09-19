"""Le serveur — ce qui manquait pour qu'un appel réel puisse arriver.

La vérification d'avant-livraison a trouvé que tout le produit était une
bibliothèque : neuf modules, deux cent soixante tests, une porte de
non-régression… et **aucun point d'entrée qui écoute**. Un standard téléphonique
qui ne peut pas recevoir de connexion n'est pas livrable, quel que soit le nombre
de tests. C'est exactement le genre d'angle mort qu'on ne voit pas depuis
l'intérieur du chantier.

Asterisk se connecte ici en TCP (`AudioSocket(<hôte>:<port>,<uuid>)` dans le
plan de numérotation). Un appel = une connexion = **une session, un agent, un
état**. Rien n'est partagé entre deux appels : c'est ce qui empêche le pire
défaut d'un standard, celui où un client entend la réponse destinée à un autre.
"""

from __future__ import annotations

import socket
import threading
import time
from typing import Callable

from standard.session import DUREE_PAQUET_MS, SessionTelephonique

TAILLE_LECTURE = 4096


class ServeurAudioSocket:
    """Un fil par appel. Simple, et suffisant : la mesure 13 plafonne une machine
    à une dizaine d'appels simultanés, très loin du seuil où les fils coûtent."""

    def __init__(self, fabrique_agent: Callable[[], object],
                 transcrire: Callable[[bytes, int], str],
                 synthetiser: Callable[[str], list[bytes]],
                 hote: str = "0.0.0.0", port: int = 8090,
                 rythme: bool = True,
                 sur_fin: Callable[[SessionTelephonique], None] | None = None):
        self.fabrique_agent = fabrique_agent
        self.transcrire = transcrire
        self.synthetiser = synthetiser
        self.hote = hote
        self.port = port
        self.rythme = rythme          # respecter 20 ms entre paquets ; faux en test
        self.sur_fin = sur_fin

        self.appels_en_cours = 0
        self.appels_total = 0
        self._prise: socket.socket | None = None
        self._fil: threading.Thread | None = None
        self._arret = threading.Event()
        self._verrou = threading.Lock()

    # --- cycle de vie -------------------------------------------------------

    def demarrer(self) -> None:
        self._prise = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._prise.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._prise.bind((self.hote, self.port))
        self._prise.listen(16)
        self.port = self._prise.getsockname()[1]      # port 0 : le système choisit
        self._prise.settimeout(0.2)
        self._fil = threading.Thread(target=self._accepter, daemon=True)
        self._fil.start()

    def arreter(self) -> None:
        self._arret.set()
        if self._fil:
            self._fil.join(timeout=2)
        if self._prise:
            self._prise.close()

    # --- boucle d'acceptation ----------------------------------------------

    def _accepter(self) -> None:
        while not self._arret.is_set():
            try:
                connexion, _ = self._prise.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=self._servir, args=(connexion,), daemon=True).start()

    # --- un appel -----------------------------------------------------------

    def _servir(self, connexion: socket.socket) -> None:
        with self._verrou:
            self.appels_en_cours += 1
            self.appels_total += 1
        session = SessionTelephonique(agent=self.fabrique_agent(),
                                      transcrire=self.transcrire,
                                      synthetiser=self.synthetiser)
        fini = threading.Event()
        # L'emission vit dans SON PROPRE FIL. Tant qu'elle partageait celui de la
        # lecture, le serveur n'ecoutait pas pendant qu'il parlait : l'appelant
        # pouvait crier, l'interruption n'etait detectee qu'une fois la phrase
        # terminee. Une revue independante a mesure six secondes de parole
        # par-dessus l'appelant.
        emetteur = threading.Thread(target=self._emettre_en_continu,
                                    args=(connexion, session, fini), daemon=True)
        try:
            connexion.settimeout(0.2)
            session.ouvrir()
            emetteur.start()
            while not self._arret.is_set() and not session.fermee:
                try:
                    morceau = connexion.recv(TAILLE_LECTURE)
                except socket.timeout:
                    continue
                if not morceau:
                    break                     # l'appelant a raccroche
                session.recevoir(morceau)
                if session.transfert_demande:
                    # Le bord telephonique reprend la main : on lui rend l'appel
                    # plutot que de raccrocher au nez de l'appelant.
                    break
        except (ConnectionResetError, BrokenPipeError, OSError):
            # Un appelant qui raccroche mal ferme le socket sans prevenir. Un
            # seul appel rate ne doit jamais emporter les autres.
            pass
        finally:
            fini.set()
            emetteur.join(timeout=1)
            try:
                connexion.close()
            except OSError:
                pass
            if self.sur_fin:
                self.sur_fin(session)
            with self._verrou:
                self.appels_en_cours -= 1

    def _emettre_en_continu(self, connexion: socket.socket,
                            session: SessionTelephonique,
                            fini: threading.Event) -> None:
        """Envoie ce que l'agent a à dire, **au rythme du canal**, sans bloquer la lecture.

        Vingt millisecondes entre les paquets : plus vite, le canal saccade ;
        plus lentement, l'appelant entend des trous. Et si l'appelant reprend la
        parole, la session vide la file — ce fil s'en aperçoit au paquet suivant,
        donc en moins de vingt millisecondes, et ce qui restait n'est jamais
        rejoué par-dessus lui.
        """
        while not fini.is_set() and not self._arret.is_set():
            paquet = session.emettre()
            if paquet is None:
                time.sleep(0.005)       # rien à dire : on rend la main
                continue
            try:
                connexion.sendall(paquet)
            except OSError:
                return                  # l'appelant a raccroché pendant qu'on parlait
            if self.rythme:
                time.sleep(DUREE_PAQUET_MS / 1000)
