"""Le rappel de la veille — la seule chose qui fasse baisser les absences.

Recherche du 20/09 : un SMS envoye 24 h avant reduit les no-shows de 30 a 35 %,
et les sources metier parlent d'une division par cinq des absences non
annoncees. C'est le premier benefice mesurable qu'un salon attend, et le produit
n'en avait aucun.

Trois gardes, parce qu'un rappel mal fait coute plus qu'il ne rapporte :

1. **un seul rappel par rendez-vous.** La marque est posee APRES l'envoi reussi :
   marquer avant perdrait le rappel sur un incident reseau ;
2. **une fenetre horaire** (`regles.FENETRE_DE_RAPPEL`) ;
3. **rien de promotionnel** : un seul mot de pub ferait basculer ce message
   transactionnel en prospection commerciale, a 750 € le message (CPCE).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Callable

from standard.regles import FENETRE_DE_RAPPEL


@dataclass
class Rappels:
    """Un passage de rappels pour un locataire. Sans envoyeur, il ne fait rien."""

    depot: Any
    tenant: str
    envoyeur: Any = None
    nom_du_salon: str = "le salon"
    horloge: Callable[[], datetime] = datetime.now
    fenetre: tuple = field(default_factory=lambda: FENETRE_DE_RAPPEL)
    envoyes: int = 0
    echecs: int = 0

    def passer(self) -> int:
        """Rend le nombre de rappels partis. Zero n'est pas une erreur."""
        if self.envoyeur is None:
            return 0
        maintenant = self.horloge()
        if not self.fenetre[0] <= maintenant.hour < self.fenetre[1]:
            return 0

        demain = (maintenant.date() + timedelta(days=1)).isoformat()
        partis = 0
        for ligne in self.depot.lister(self.tenant):
            if ligne.get("date") != demain or ligne.get("rappel_envoye"):
                continue
            telephone = ligne.get("telephone")
            if not telephone:
                # Sans numero, pas de rappel — et ce n'est pas un incident : le
                # rendez-vous a ete pris sans que le client donne son numero.
                continue
            envoi = self._envoyer(ligne, telephone)
            if not envoi:
                self.echecs += 1
                continue
            partis += 1
            self.envoyes += 1
            self._marquer(ligne)
        return partis

    def _envoyer(self, ligne: dict, telephone: str) -> bool:
        try:
            envoi = self.envoyeur.confirmer(
                telephone, {**ligne, "salon": self.nom_du_salon, "rappel": True})
        except Exception:
            return False
        return bool(getattr(envoi, "envoye", False))

    def _marquer(self, ligne: dict) -> None:
        """Apres l'envoi, jamais avant : un incident reseau ne doit pas faire
        disparaitre le rappel."""
        corriger = getattr(self.depot.pour(self.tenant), "corriger", None)
        reference = ligne.get("reference")
        if callable(corriger) and reference:
            corriger(reference, {"rappel_envoye": self.horloge().isoformat(
                timespec="seconds")})
