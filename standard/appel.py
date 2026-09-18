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
        self.etat = Etat()
        self.journal = Journal()
        self.numero_de_tour = 0
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
        self._en_attente = sortie.entites if sortie.genre == "proposition" else None
        self.journal.noter(transcription=transcription, genre=sortie.genre,
                           phrase=sortie.phrase, bruite=bruite,
                           entites=dict(sortie.entites))
        return Reponse(sortie.genre, sortie.phrase, sortie.entites)

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
        cle = cle_idempotence(self.tenant, self.identifiant, self.numero_de_tour)
        ecriture: Ecriture = ecrire_rendez_vous(self.base, cle, donnees, self.journal.ecriture)

        genre = "confirmation" if ecriture.statut in ("confirme", "rejoue") else "incertain"
        if genre == "confirmation":
            self._en_attente = None
        self.journal.noter(transcription="[confirmation de l'appelant]", genre=genre,
                           phrase=ecriture.phrase, reference=ecriture.reference)
        return Reponse(genre, ecriture.phrase, donnees)
