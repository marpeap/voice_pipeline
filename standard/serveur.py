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

from standard.regles import APPELS_SIMULTANES_MAX

MEMOIRE_DES_ISSUES = 500
"""Le plan interroge dans la seconde qui suit : garder plus serait un journal,
et le journal existe deja."""
from standard.session import DUREE_PAQUET_MS, SessionTelephonique

TAILLE_LECTURE = 4096


class ServeurAudioSocket:
    """Un fil par appel. Simple, et suffisant : la mesure 13 plafonne une machine
    à une dizaine d'appels simultanés, très loin du seuil où les fils coûtent."""

    def __init__(self, fabrique_agent: Callable[[], object],
                 transcrire: Callable[[bytes, int], str],
                 synthetiser: Callable[[str], list[bytes]],
                 hote: str = "0.0.0.0", port: int = 8090,
                 seuil_bruite_db: int | None = None,
                 rythme: bool = True,
                 sur_fin: Callable[[SessionTelephonique], None] | None = None,
                 appels_simultanes_max: int | None = APPELS_SIMULTANES_MAX):
        self.fabrique_agent = fabrique_agent
        self.transcrire = transcrire
        self.synthetiser = synthetiser
        self.hote = hote
        self.port = port
        self.seuil_bruite_db = seuil_bruite_db
        self.rythme = rythme          # respecter 20 ms entre paquets ; faux en test
        self.sur_fin = sur_fin
        self.appels_simultanes_max = appels_simultanes_max
        self.archivages_perdus = 0     # un appel fini dont le journal n'a pas voulu
        self.demarchages_filtres = 0   # non factures au salon (docs/06)
        self.appels_refuses = 0        # au-dela du plafond : la ligne est rendue
        # Comment chaque appel s'est termine, pour que le plan de numerotation
        # puisse le demander : sans cette reponse, un transfert raccroche au nez
        # de l'appelant et un demarchage filtre repart vers le salon.
        self.issues: dict[str, str] = {}

        self.appels_en_cours = 0
        self.appels_total = 0
        self.paroles_perdues = 0
        self.pannes_pendant_appel = 0
        self.interruptions_totales = 0
        self._prise: socket.socket | None = None
        self._fil: threading.Thread | None = None
        self._arret = threading.Event()
        self._verrou = threading.Lock()
        self._fils_d_appel: list[threading.Thread] = []

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
        # Le menage tourne avec le service, ou il ne tourne pas du tout : un cron
        # pose a la main sur un VPS recree est la facon habituelle dont une duree
        # de conservation devient fausse.
        for accessoire in ("entretien", "sante"):
            compagnon = getattr(self, accessoire, None)
            if compagnon is not None:
                compagnon.demarrer()

    def arreter(self, attente_s: float = 5.0) -> None:
        """Arret propre : on attend les appels en cours, on ne les coupe pas.

        Les fils sont `daemon` — ils mourraient avec le processus, au milieu
        d'une phrase. La promesse etait dans `__main__` bien avant d'etre tenue.
        """
        self._arret.set()
        for accessoire in ("entretien", "sante"):
            compagnon = getattr(self, accessoire, None)
            if compagnon is not None:
                compagnon.arreter()
        if self._fil:
            self._fil.join(timeout=2)
        with self._verrou:
            fils = list(self._fils_d_appel)
        for fil in fils:
            fil.join(timeout=attente_s)
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
            if self.appels_simultanes_max is not None:
                with self._verrou:
                    complet = self.appels_en_cours >= self.appels_simultanes_max
                    if complet:
                        self.appels_refuses += 1
                if complet:
                    # On rend la ligne TOUT DE SUITE : le bord telephonique peut
                    # alors basculer sur le poste du salon. Un appel qui gresille
                    # ou qui attend une voix est pire qu'un appel rendu.
                    try:
                        connexion.close()
                    except OSError:
                        pass
                    continue

            fil = threading.Thread(target=self._servir, args=(connexion,), daemon=True)
            with self._verrou:
                self._fils_d_appel = [f for f in self._fils_d_appel if f.is_alive()]
                self._fils_d_appel.append(fil)
            fil.start()

    # --- un appel -----------------------------------------------------------

    def _servir(self, connexion: socket.socket) -> None:
        with self._verrou:
            self.appels_en_cours += 1
            self.appels_total += 1
        session = SessionTelephonique(
            agent=self.fabrique_agent(), transcrire=self.transcrire,
            synthetiser=self.synthetiser,
            **({"seuil_bruite_db": self.seuil_bruite_db}
               if self.seuil_bruite_db is not None else {}))
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
                # Verifie AVANT la lecture : un demarcheur qui se tait n'envoie
                # plus rien, et la ligne serait restee ouverte a l'attendre.
                if session.fin_demandee and not session.en_train_de_parler:
                    self.demarchages_filtres += 1
                    break
                try:
                    morceau = connexion.recv(TAILLE_LECTURE)
                except socket.timeout:
                    continue
                if not morceau:
                    break                     # l'appelant a raccroche
                try:
                    session.recevoir(morceau)
                except Exception:
                    # `urllib.error.URLError` herite d'`OSError` : la garde
                    # ecrite pour les sockets avalait aussi les pannes reseau,
                    # et l'appel se fermait sans un mot. On compte et on continue.
                    self.pannes_pendant_appel += 1
                    continue
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
            self.interruptions_totales += session.interruptions
            emetteur.join(timeout=1)
            try:
                connexion.close()
            except OSError:
                pass
            self._retenir_l_issue(session)
            if self.sur_fin:
                try:
                    self.sur_fin(session)
                except Exception:
                    # Le journal peut tomber — base verrouillee, disque plein.
                    # L'appel, lui, est fini : si l'exception remontait, le
                    # compteur ne redescendait pas et l'arret propre attendait
                    # un appel qui n'existe plus.
                    self.archivages_perdus += 1
            with self._verrou:
                self.appels_en_cours -= 1

    def _retenir_l_issue(self, session) -> None:
        """Garde les dernieres issues, et seulement elles : c'est un relais vers
        le plan de numerotation, pas un journal."""
        identifiant = getattr(session, "identifiant", None)
        if not identifiant:
            return
        if session.transfert_demande:
            issue = "transfert"
        elif getattr(session, "fin_demandee", False):
            issue = "demarchage"
        else:
            issue = "fin"
        with self._verrou:
            self.issues[identifiant] = issue
            if len(self.issues) > MEMOIRE_DES_ISSUES:
                for vieux in list(self.issues)[:-MEMOIRE_DES_ISSUES]:
                    del self.issues[vieux]

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
            try:
                paquet = session.emettre()
            except Exception:
                # Un fil d'emission qui meurt laisse l'appel ouvert et MUET : on
                # abandonne la phrase en cours, on ne quitte pas le fil.
                self.paroles_perdues += 1
                time.sleep(0.02)
                continue
            if paquet is None:
                time.sleep(0.005)       # rien à dire : on rend la main
                continue
            try:
                connexion.sendall(paquet)
            except OSError:
                return                  # l'appelant a raccroché pendant qu'on parlait
            if self.rythme:
                time.sleep(DUREE_PAQUET_MS / 1000)
