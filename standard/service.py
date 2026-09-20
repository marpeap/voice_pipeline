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

    @property
    def attend_un_numero(self) -> bool:
        """La session le demande a chaque touche : sans cette delegation, un
        appelant qui compose spontanement n'est pas entendu."""
        return bool(self._appel._attend_un_numero
                    or self._appel._annulation is not None)

    @property
    def interdits(self) -> list:
        """Ce que le serveur empeche de dire, quelle que soit la phrase."""
        return self._appel.interdits

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
                 secours: Any = None,
                 reponses_du_depot: Any = None):
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
        # Le questionnaire du commercant (docs/05) vit en base : la console
        # ecrit, le standard lit. Sans cela, le formulaire ne sert a rien.
        self.reponses_du_depot = reponses_du_depot
        self.metriques = Supervision()
        self._memoire = None
        self._demarre = False

    # --- demarrage ----------------------------------------------------------

    def _reponses_enregistrees(self) -> dict:
        """Ce que le commercant a repondu depuis la console, s'il y a une base."""
        if self.reponses_du_depot is None:
            return {}
        try:
            return dict(self.reponses_du_depot.reponses(self.configuration.tenant))
        except Exception:
            # Une base qui ne repond pas ne doit pas empecher de decrocher : on
            # garde ce que la configuration porte deja.
            return {}

    def questions_manquantes(self) -> list[str]:
        """Les questions critiques encore vides. Dire ce qui manque vaut mieux
        qu'echouer sechement : le commercant peut agir."""
        return paliers_manquants(self.configuration.pack,
                                 {**self.configuration.reponses,
                                  **self._reponses_enregistrees()})

    def demarrer(self) -> None:
        manquantes = self.questions_manquantes()
        if manquantes:
            raise RuntimeError(
                "l'agent ne peut pas etre active, ces questions critiques sont sans "
                f"reponse : {', '.join(manquantes)}")
        reponses = {**self.configuration.reponses, **self._reponses_enregistrees()}
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

        # Le modele hors ligne ne connait le catalogue que si on le lui donne :
        # sans lui, il rendait toujours `prestation: None`, la duree n'etait
        # jamais appliquee et le salon se double-bookait malgre tout.
        catalogue = tuple(self._memoire[1].frontmatter.get("prestations") or ())
        if hasattr(self.client_modele, "prestations"):
            self.client_modele.prestations = catalogue
        # `empreinte` est facultative : un registre fige (banc, test) n'en a
        # pas, et il n'a rien a relire non plus.
        empreinte = getattr(self.corrections, "empreinte", None)
        self._empreinte_des_corrections = empreinte() if callable(empreinte) else ""
        self._empreinte_des_reponses = repr(sorted(reponses.items()))

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

    def _creneaux_ouverts(self, jour_iso: str | None = None) -> set[str]:
        """Les creneaux de la fiche, moins ceux qu'une correction a supprimes.

        `docs/06` : « ce qui doit etre vrai a 100 % est evalue cote serveur ».
        La regle etait calculee et stockee — personne ne la lisait, et le gerant
        qui corrigeait « ce creneau n'existe pas » se l'entendait proposer au
        client suivant.
        """
        ouverts = set(self.configuration.creneaux)
        for regle in getattr(self, "regles_serveur", []):
            if regle.get("type") != "agenda" or not regle.get("heure"):
                continue
            jour_vise = regle.get("jour")
            if jour_vise and jour_iso:
                from standard.regles import JOURS
                from standard.texte import sans_accents

                nom_du_jour = JOURS[date.fromisoformat(jour_iso).weekday()]
                if sans_accents(jour_vise).lower() != sans_accents(nom_du_jour):
                    continue
            elif jour_vise and not jour_iso:
                continue          # regle d'un seul jour : elle ne ferme pas tout
            ouverts.discard(regle["heure"])
        return ouverts

    def _fermetures(self) -> tuple:
        """Les conges ecrits par le commercant, lus comme il les a ecrits."""
        from standard.fermetures import lire_les_fermetures

        horaires = (self._memoire[1].frontmatter.get("horaires") or {}
                    ) if self._memoire else {}
        return tuple(lire_les_fermetures(str(horaires.get("fermetures") or "")))

    def _ferme_les_feries(self) -> bool:
        horaires = (self._memoire[1].frontmatter.get("horaires") or {}
                    ) if self._memoire else {}
        return str(horaires.get("feries", "oui")) != "non"

    def _agenda(self) -> Agenda:
        return Agenda(aujourd_hui=self.configuration.aujourd_hui,
                      horizon_jours=self.configuration.horizon_jours,
                      jours_fermes=tuple(self.configuration.jours_fermes),
                      creneaux=self._creneaux_ouverts(),
                      creneaux_du_jour=self._creneaux_ouverts,
                      pris=self.creneaux_pris(),
                      libres_du_jour=self.libres_du_jour,
                      durees=dict(self._memoire[1].frontmatter.get("durees") or {})
                      if self._memoire else {},
                      fermetures=self._fermetures(),
                      ferme_les_feries=self._ferme_les_feries())

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

    def _relire_le_questionnaire(self) -> None:
        """Une reponse changee dans la console vaut pour le prochain appel.

        Meme raison que pour les corrections : la console tourne dans un autre
        processus, et son « c'est enregistre » doit etre vrai sans redemarrage.
        """
        if self.reponses_du_depot is None:
            return
        attendues = repr(sorted({**self.configuration.reponses,
                                 **self._reponses_enregistrees()}.items()))
        if attendues != getattr(self, "_empreinte_des_reponses", None):
            self.demarrer()

    def _relire_les_corrections(self) -> None:
        """Une fois par appel, jamais par tour.

        Recomposer la memoire coute : c'est elle qui porte le prefixe cachable
        du prompt (4 096 tokens, mesure 23). On ne la refabrique donc que si la
        base a bouge — la console tourne dans un autre processus, et sa promesse
        « elle s'applique des maintenant » ne tient qu'a cette relecture.
        """
        empreinte = getattr(self.corrections, "empreinte", None)
        recharger = getattr(self.corrections, "recharger", None)
        if not callable(empreinte) or not callable(recharger):
            return
        recharger()
        if empreinte() == getattr(self, "_empreinte_des_corrections", ""):
            return
        self.demarrer()

    def nouvel_appel(self, identifiant: str) -> AppelSuivi:
        if not self._demarre:
            raise RuntimeError("le service doit etre demarre avant de prendre un appel")
        self._relire_les_corrections()
        self._relire_le_questionnaire()
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
                      secours=self.secours,
                      interdits=[r["interdit"] for r in getattr(self, "regles_serveur", [])
                                 if r.get("type") == "interdit" and r.get("interdit")])
        appel.envoyeur_sms = self.envoyeur_sms
        return AppelSuivi(appel, self._annonce(), self.metriques)
