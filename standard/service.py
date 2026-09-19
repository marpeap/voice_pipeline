"""Le service — ce qui demarre, ce qui refuse de demarrer, et ce qu'il sait dire.

Trois responsabilites, toutes nees d'une mesure ou d'une regle ecrite :

- **amorcer la reserve de connexions au demarrage** (mesure 4 : 2 040 ms pour une
  connexion neuve contre 378 ms pour une connexion gardee) ;
- **refuser d'activer un agent incomplet** : tant qu'une question critique du pack
  est sans reponse, l'agent ne decroche pas — ce sont exactement celles dont
  l'absence produit une erreur entendue par le client ;
- **tenir le journal** qui rend un appel diagnosticable sans le reecouter :
  rapport signal/bruit, delai avant premier fragment, confirmations orphelines.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Callable

from standard import regles
from standard.appel import Appel
from standard.decision import Agenda
from standard.locataire import composer_memoire, lire_memoire, paliers_manquants


@dataclass
class Configuration:
    """Tout ce qui change d'un deploiement a l'autre, et rien d'autre.

    Les seuils prennent par defaut les valeurs **mesurees** (`standard.regles`) :
    on peut les changer, mais il faut le vouloir, et cela se voit dans la
    configuration plutot que dans le code.
    """

    tenant: str
    pack: dict
    reponses: dict = field(default_factory=dict)
    corps: str = ""
    modele: str | None = None
    parametres: dict = field(default_factory=dict)
    aujourd_hui: date = field(default_factory=date.today)
    horizon_jours: int = 14
    creneaux: tuple[str, ...] = ()
    jours_fermes: tuple[int, ...] = (6,)
    connexions: int = 4
    seuil_bruite_db: int = regles.SEUIL_BRUITE_DB
    consignes_communes: str = ""

    @classmethod
    def depuis(cls, source: dict) -> "Configuration":
        """Construit depuis un dictionnaire — fichier, variables d'environnement
        ou console : le service ne sait pas d'ou cela vient, et c'est voulu."""
        if "pack" not in source:
            raise ValueError("configuration sans pack : un agent sans pack n'a pas de questions")
        pack = source["pack"]
        if isinstance(pack, (str, Path)):
            pack = json.loads(Path(pack).read_text())
        return cls(
            tenant=source.get("tenant", "inconnu"),
            pack=pack,
            reponses=dict(source.get("reponses", {})),
            corps=source.get("corps", ""),
            modele=source.get("modele"),
            parametres=dict(source.get("parametres", {})),
            aujourd_hui=(date.fromisoformat(source["aujourd_hui"])
                         if isinstance(source.get("aujourd_hui"), str)
                         else source.get("aujourd_hui") or date.today()),
            horizon_jours=int(source.get("horizon_jours", 14)),
            creneaux=tuple(source.get("creneaux", ())),
            jours_fermes=tuple(source.get("jours_fermes", (6,))),
            connexions=int(source.get("connexions", 4)),
            seuil_bruite_db=int(source.get("seuil_bruite_db", regles.SEUIL_BRUITE_DB)),
            consignes_communes=source.get("consignes_communes", ""),
        )


class AppelSuivi:
    """Un appel, plus ce que le service doit en retenir."""

    def __init__(self, appel: Appel, annonce: str, supervision: "Supervision"):
        self._appel = appel
        self._annonce = annonce
        self._supervision = supervision
        self._supervision.appels += 1
        self._orphelines_comptees = 0

    # La session cherche ces deux-la sur l'agent. L'agent reel, c'est CET objet :
    # sans delegation, le `hasattr` echouait en silence et la regle T7 — le
    # clavier apres deux echecs — n'etait jamais armee.
    @property
    def memoire(self) -> str:
        """Ce que l'agent sait — utile au diagnostic, et verifiable par un test."""
        return self._appel.memoire

    @property
    def basculer_clavier(self):
        return self._appel.basculer_clavier

    @basculer_clavier.setter
    def basculer_clavier(self, fonction):
        self._appel.basculer_clavier = fonction

    def numero_au_clavier(self, numero: str):
        return self._appel.numero_au_clavier(numero)

    @property
    def fin_demandee(self) -> bool:
        """La session la cherche ici : sans delegation, la ligne resterait
        ouverte apres un demarchage refuse."""
        return self._appel.fin_demandee

    def rien_entendu(self):
        """La session la cherche ici : sans delegation, l'agent resterait muet."""
        return self._appel.rien_entendu()

    @property
    def etat(self):
        return self._appel.etat

    @property
    def journal(self):
        return self._appel.journal

    def salutation(self) -> str:
        """La premiere phrase, et elle annonce l'agent — non desactivable.

        Mesure 19 : cette phrase survit au canal telephonique, les deux moteurs la
        retrouvent intacte. Il n'y a donc aucune raison technique de la raccourcir
        ni de la deplacer.
        """
        return self._annonce

    def tour(self, transcription: str, bruite: bool = False):
        if bruite:
            self._supervision.appels_bruites += 1
        reponse = self._appel.tour(transcription, bruite=bruite)
        # Le garde de sortie peut avoir bloque une phrase mensongere pendant ce
        # tour : l'incident doit remonter tout de suite, pas seulement si
        # l'appelant va jusqu'a la confirmation.
        self._remonter_les_incidents()
        return reponse

    def confirmer(self):
        reponse = self._appel.confirmer()
        self._remonter_les_incidents()
        return reponse

    def _remonter_les_incidents(self) -> None:
        total = self._appel.journal.confirmations_orphelines
        self._supervision.absorber(total - self._orphelines_comptees)
        self._orphelines_comptees = total


@dataclass
class Supervision:
    """Les trois chiffres qui disent si le service va bien.

    Le troisieme n'est pas une statistique : **toute confirmation orpheline est un
    incident** (docs/07), et une machine pleine se voit au delai avant premier
    fragment, pas a la charge processeur (mesure 13).
    """
    appels: int = 0
    appels_bruites: int = 0
    confirmations_orphelines: int = 0
    premiers_fragments_ms: list[float] = field(default_factory=list)

    def absorber(self, nouvelles: int) -> None:
        """On ADDITIONNE des incidents NOUVEAUX, jamais un total.

        Deux pieges evites ici. Un `max()` comptait deux incidents dans deux
        appels pour un seul — sur un indicateur dont la cible est zero, c'est la
        difference entre « un incident » et « un incident par appel ». Et
        additionner un total a chaque tour compterait le meme incident autant de
        fois qu'il y a de tours : l'appelant transmet donc l'ECART.
        """
        self.confirmations_orphelines += max(0, nouvelles)

    def etat(self) -> dict[str, Any]:
        import statistics
        part = (100.0 * self.appels_bruites / self.appels) if self.appels else 0.0
        return {
            "appels": self.appels,
            "part_bruitee_pct": round(part, 1),
            "confirmations_orphelines": self.confirmations_orphelines,
            "premier_fragment_p50_ms": (round(statistics.median(self.premiers_fragments_ms))
                                        if self.premiers_fragments_ms else None),
        }


class Service:
    """Le point d'entree : on le configure, on le demarre, il rend des appels."""

    def __init__(self, configuration: Configuration, client_modele,
                 base, fabrique_connexion: Callable[[], Any] | None = None,
                 maintenir: Callable[[Any], None] | None = None,
                 creneaux_pris: Callable[[], dict[str, set[str]]] | None = None,
                 libres_du_jour: Callable[[str], list[str]] | None = None,
                 envoyeur_sms: Any = None,
                 corrections: Any = None,
                 secours: Any = None):
        self.configuration = configuration
        self.client_modele = client_modele
        self.base = base
        # Sans cette fonction, l'agenda ignore les rendez-vous deja pris et
        # propose au deuxieme appelant le creneau du premier.
        self.creneaux_pris = creneaux_pris or dict
        # En mode greffon, les creneaux libres viennent de l'hote : lui seul
        # sait ce qui a ete pris dans son logiciel depuis la derniere seconde.
        self.libres_du_jour = libres_du_jour
        self.envoyeur_sms = envoyeur_sms
        self.corrections = corrections
        # Toujours local, meme en mode greffon : c'est le filet qui garde la
        # trace d'un rendez-vous que l'hote n'a pas confirme.
        self.secours = secours
        self.metriques = Supervision()
        self._memoire = None
        self._demarre = False

    # --- demarrage ----------------------------------------------------------

    def questions_manquantes(self) -> list[str]:
        """Les questions critiques encore vides. Dire ce qui manque vaut mieux
        qu'echouer sechement : le commercant peut agir."""
        return paliers_manquants(self.configuration.pack, self.configuration.reponses)

    def demarrer(self) -> None:
        manquantes = self.questions_manquantes()
        if manquantes:
            raise RuntimeError(
                "l'agent ne peut pas etre active, ces questions critiques sont sans "
                f"reponse : {', '.join(manquantes)}")
        reponses = dict(self.configuration.reponses)
        corps = self.configuration.corps
        self.regles_serveur: list = []
        if self.corrections is not None:
            # La console promet au commercant que sa correction « s'applique tout
            # de suite ». Elle ne s'appliquait nulle part : rien ne la relisait.
            from standard.correction import appliquer

            reponses, corps, self.regles_serveur = appliquer(
                self.corrections.actives(), reponses, corps)
        texte = composer_memoire(self.configuration.pack, reponses, corps)
        self._memoire = (texte, lire_memoire(texte))

        # Mesure 4 : 2 040 ms pour une connexion neuve, 378 ms pour une gardee.
        # On chauffe donc la connexion QUI SERT — celle du modele — au lieu de
        # fabriquer une reserve d'objets que personne n'emprunte, ce qu'une revue
        # independante a justement qualifie de decoratif.
        amorcer = getattr(self.client_modele, "amorcer", None)
        if callable(amorcer):
            try:
                amorcer()
            except Exception:
                # Un fournisseur injoignable au demarrage ne doit pas empecher le
                # service de decrocher : la premiere requete reessaiera.
                pass
        self._demarre = True

    # --- appels -------------------------------------------------------------

    def _agenda(self) -> Agenda:
        return Agenda(aujourd_hui=self.configuration.aujourd_hui,
                      horizon_jours=self.configuration.horizon_jours,
                      jours_fermes=tuple(self.configuration.jours_fermes),
                      creneaux=set(self.configuration.creneaux),
                      pris=self.creneaux_pris(),
                      libres_du_jour=self.libres_du_jour)

    def _annonce(self) -> str:
        """La formulation choisie par le salon, jamais son existence."""
        _, memoire = self._memoire
        choix = memoire.frontmatter.get("annonce", {}).get("formulation", "assistant_automatique")
        nom = memoire.frontmatter.get("salon", {}).get("nom") \
            or memoire.frontmatter.get("etablissement", {}).get("nom") or "l'établissement"
        libelles = {
            "assistant_automatique": f"Bonjour, {nom}. Je suis l'assistant automatique, je vous écoute.",
            "assistant_virtuel": f"Bonjour, je suis l'assistant virtuel de {nom}, je vous écoute.",
        }
        if choix in libelles:
            return libelles[choix]
        return f"Bonjour, {nom}. {choix}"

    def supervision(self) -> dict[str, Any]:
        """L'etat du service, en trois chiffres : combien d'appels, quelle part
        d'entre eux etait bruitee, et combien de confirmations orphelines — ce
        dernier devant rester a zero."""
        return self.metriques.etat()

    def nouvel_appel(self, identifiant: str) -> AppelSuivi:
        if not self._demarre:
            raise RuntimeError("le service doit etre demarre avant de prendre un appel")
        texte, _ = self._memoire
        _, memoire_lue = self._memoire
        nom_salon = (memoire_lue.frontmatter.get("salon", {}).get("nom")
                     or memoire_lue.frontmatter.get("etablissement", {}).get("nom")
                     or "le salon")
        catalogue = tuple(memoire_lue.frontmatter.get("prestations", {}) or ())
        appel = Appel(client_modele=self.client_modele, agenda=self._agenda(),
                      nom_salon=nom_salon, prestations=catalogue,
                      base=self.base, memoire=texte,
                      consignes_communes=self.configuration.consignes_communes,
                      tenant=self.configuration.tenant, identifiant=identifiant,
                      modele=self.configuration.modele,
                      parametres=self.configuration.parametres or None,
                      secours=self.secours)
        appel.envoyeur_sms = self.envoyeur_sms
        return AppelSuivi(appel, self._annonce(), self.metriques)
