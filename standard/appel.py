"""Le tour de parole complet — l'assemblage, et l'endroit ou les regles tiennent.

Un appel, c'est cinq pieces enchainees : ecoute, comprehension, decision,
ecriture, parole. Ce module les tient ensemble et fait respecter la seule regle
qui compte vraiment (mesure 14, puis 15) :

> **le modele propose, la machine dispose, et seule une ecriture relue confirme.**

Le test de ce module rejoue les douze tours qui avaient produit six fautes, avec
un modele de test qui se comporte comme celui qui a faute. Aucune de ses
inventions ne doit atteindre l'appelant.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from standard.comprehension import Comprehension, ErreurFournisseur
from standard.decision import Agenda, Etat, decider
from standard.assentiment import est_un_refus, est_un_oui
from standard.regles import contient_une_confirmation
from standard.langue import FRANCAIS, detecter_langue, phrase_de_passage
from standard.ecriture import (
    BaseRendezVous,
    Ecriture,
    JournalEcriture,
    cle_idempotence,
    ecrire_rendez_vous,
)


@dataclass
class Reponse:
    genre: str
    phrase: str
    entites: dict = field(default_factory=dict)


@dataclass
class Journal:
    """Ce qu'il faut pour diagnostiquer un appel sans le reecouter.

    Sans lui, une plainte « l'agent comprend mal » n'est pas diagnosticable ; avec
    lui, on sait tout de suite si le probleme est le moteur, le pack, ou la rue
    (mesure 10).
    """
    tours: list[dict[str, Any]] = field(default_factory=list)
    ecriture: JournalEcriture = field(default_factory=JournalEcriture)

    @property
    def confirmations_orphelines(self) -> int:
        return self.ecriture.orphelines

    def noter(self, **champs: Any) -> None:
        self.tours.append(champs)


class Appel:
    """Un appel en cours. Un objet par appel, jamais partage."""

    def __init__(self, client_modele, agenda: Agenda, base: BaseRendezVous,
                 memoire: str, consignes_communes: str,
                 tenant: str = "inconnu", identifiant: str = "appel",
                 nom_salon: str = "le salon",
                 modele: str | None = None, parametres: dict | None = None):
        self.comprehension = Comprehension(
            client=client_modele, consignes_communes=consignes_communes,
            **({"modele": modele} if modele else {}),
            **({"parametres": parametres} if parametres else {}))
        self.agenda = agenda
        self.base = base
        self.memoire = memoire
        self.tenant = tenant
        self.identifiant = identifiant
        self.nom_salon = nom_salon
        self.etat = Etat()
        self.journal = Journal()
        self.numero_de_tour = 0
        self.envoyeur_sms = None                 # branché par le service, facultatif
        self._en_attente: dict | None = None     # la proposition que l'appelant doit confirmer

    def _calendrier(self) -> dict:
        """Ce que la machine donne au modele : ses propres creneaux, rien d'autre."""
        from datetime import timedelta
        calendrier = {}
        for delta in range(self.agenda.horizon_jours + 1):
            jour = (self.agenda.aujourd_hui + timedelta(days=delta)).isoformat()
            if self.agenda.statut(jour) == "ouvert":
                calendrier[jour] = self.agenda.libres(jour)
        return calendrier

    def tour(self, transcription: str, bruite: bool = False) -> Reponse:
        """Un tour de parole : ce que l'appelant a dit, ce que l'agent repond."""
        self.numero_de_tour += 1

        # Avant toute chose : parle-t-il une langue que nous ne servons pas ?
        # Le servir a moitie serait pire que passer la main — et l'AI Act demande
        # l'annonce « dans la langue de la conversation ».
        # Le « oui » d'un appelant a qui l'on vient de proposer un creneau n'est
        # pas une nouvelle demande : c'est CE moment qui ecrit en base, et rien
        # d'autre dans le produit ne le fait.
        if self._en_attente is not None:
            if est_un_oui(transcription):
                return self.confirmer()
            if est_un_refus(transcription):
                self._en_attente = None

        langue = detecter_langue(transcription)
        if langue != FRANCAIS:
            phrase = phrase_de_passage(langue)
            self.journal.noter(transcription=transcription, genre="transfert",
                               phrase=phrase, langue=langue)
            return Reponse("transfert", phrase, {"langue": langue})

        try:
            proposition = self.comprehension.analyser(transcription, self.memoire,
                                                      self._calendrier())
        except ErreurFournisseur as erreur:
            # L'erreur du fournisseur est journalisee telle quelle, jamais dite au
            # client : lui n'entend qu'une phrase d'attente honnete.
            self.journal.noter(transcription=transcription, genre="panne",
                               phrase="", erreur=str(erreur))
            return Reponse("panne", "Je rencontre un problème technique. "
                                    "Je vous passe quelqu'un du salon.")

        sortie = decider(proposition, self.etat, self.agenda)
        sortie.phrase = self._garde_de_sortie(sortie.phrase)
        self._en_attente = sortie.entites if sortie.genre == "proposition" else None
        self.journal.noter(transcription=transcription, genre=sortie.genre,
                           phrase=sortie.phrase, bruite=bruite,
                           entites=dict(sortie.entites))
        return Reponse(sortie.genre, sortie.phrase, sortie.entites)

    def _garde_de_sortie(self, phrase: str) -> str:
        """Le dernier filet : aucune phrase venue d'ailleurs que de l'ecriture
        relue ne peut affirmer qu'un rendez-vous existe.

        Ce garde ne devrait jamais servir — la decision ne produit pas ces mots,
        et le modele n'ecrit rien. C'est precisement pourquoi il existe : un
        invariant garde par un compteur que rien ne peut incrementer n'est pas
        garde du tout, et c'est ce qu'une revue independante a trouve le 19/09.
        """
        if not contient_une_confirmation(phrase):
            return phrase
        self.journal.ecriture.noter_confirmation_orpheline(
            self.identifiant, f"phrase bloquee : {phrase!r}")
        return ("Je vérifie votre demande, un instant.")

    def confirmer(self) -> Reponse:
        """L'appelant a dit oui. C'est ici, et seulement ici, qu'on ecrit.

        Sans proposition en cours, il n'y a rien a confirmer — et surtout rien a
        annoncer : c'est exactement la faute qui produisait « c'est note » sur du
        vide (mesure 14).
        """
        if not self._en_attente:
            return Reponse("question", "Je n'ai pas encore de créneau à vous confirmer. "
                                       "Quel jour vous conviendrait ?")

        donnees = dict(self._en_attente)
        donnees.setdefault("prestation", self.etat.connu.get("prestation"))
        telephone = donnees.get("telephone") or self.etat.connu.get("telephone")
        promet_sms = self.envoyeur_sms is not None and bool(telephone)
        cle = cle_idempotence(self.tenant, self.identifiant, self.numero_de_tour)
        ecriture: Ecriture = ecrire_rendez_vous(self.base, cle, donnees,
                                                self.journal.ecriture, promet_sms)

        genre = "confirmation" if ecriture.statut in ("confirme", "rejoue") else "incertain"
        trace = {"transcription": "[confirmation de l'appelant]", "genre": genre,
                 "phrase": ecriture.phrase, "reference": ecriture.reference}

        if genre == "confirmation":
            self._en_attente = None
            # Le SMS suit l'ecriture relue, jamais la proposition : promettre un
            # message pour un rendez-vous qui n'existe pas serait doubler la faute.
            if promet_sms:
                envoi = self.envoyeur_sms.confirmer(telephone, {**donnees,
                                                                "salon": self.nom_salon})
                trace["sms"] = "envoyé" if envoi.envoye else "échec"
                if envoi.reserve:
                    # L'agent a deja dit « vous recevrez un SMS » : un echec muet
                    # transforme cette phrase en mensonge.
                    trace["sms_reserve"] = envoi.reserve

        self.journal.noter(**trace)
        return Reponse(genre, ecriture.phrase, donnees)
