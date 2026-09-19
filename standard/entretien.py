"""Le ménage — ce qui rend vraie la durée annoncée au registre.

`journal.purger` porte cette phrase depuis le début : « une durée écrite dans un
document et jamais appliquée est une durée fausse ». Personne ne l'appelait. En
production, les transcriptions d'appels seraient restées indéfiniment, alors que
la CNIL recommande six mois au maximum pour les appels et leurs transcriptions.

Deux exigences, et elles se contredisent presque :
- le ménage doit tourner **sans que personne y pense** — un cron oublié sur un
  VPS recréé est la façon habituelle dont ces durées deviennent fausses ;
- il ne doit **jamais emporter le standard téléphonique**. Une base verrouillée
  pendant la purge est un incident de ménage, pas une panne d'appel.
"""

from __future__ import annotations

import threading

from standard.regles import CONSERVATION_JOURS

INTERVALLE_PAR_DEFAUT_S = 24 * 3600
"""Une fois par jour suffit : la durée se compte en jours, pas en minutes."""


class Entretien:
    """Purge periodique, demarree avec le service et arretee avec lui."""

    def __init__(self, journal, conservation_jours: int = CONSERVATION_JOURS,
                 intervalle_s: float = INTERVALLE_PAR_DEFAUT_S):
        self.journal = journal
        self.conservation_jours = conservation_jours
        self.intervalle_s = intervalle_s
        self.passages = 0
        self.effaces = 0
        self.pannes = 0
        self._arret = threading.Event()
        self._fil: threading.Thread | None = None

    # --- un passage ---------------------------------------------------------

    def passer(self) -> int:
        """Un passage de ménage. Rend le nombre de lignes effacées."""
        try:
            efface = int(self.journal.purger(self.conservation_jours) or 0)
        except Exception:
            # Le ménage qui tombe ne doit pas emporter le standard : on compte
            # l'incident, il se lit en supervision, et le passage suivant
            # rattrapera ce que celui-ci n'a pas fait.
            self.pannes += 1
            return 0
        self.passages += 1
        self.effaces += efface
        return efface

    # --- le fil -------------------------------------------------------------

    @property
    def vivant(self) -> bool:
        return self._fil is not None and self._fil.is_alive()

    def demarrer(self) -> None:
        if self.vivant:
            return
        self._arret.clear()
        self._fil = threading.Thread(target=self._boucle, name="entretien", daemon=True)
        self._fil.start()

    def _boucle(self) -> None:
        while not self._arret.is_set():
            self.passer()
            # `wait` plutot qu'un `sleep` : l'arret est immediat, sans attendre
            # la journee entiere.
            self._arret.wait(self.intervalle_s)

    def arreter(self, delai_s: float = 2.0) -> None:
        self._arret.set()
        if self._fil is not None:
            self._fil.join(timeout=delai_s)
            self._fil = None

    def etat(self) -> dict:
        return {"passages": self.passages, "lignes_effacees": self.effaces,
                "pannes": self.pannes, "conservation_jours": self.conservation_jours}
