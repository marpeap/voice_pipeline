"""La parole — le dernier metre, et celui qui fixe la capacite d'une machine.

Mesure 13 : le TTS ne limite pas en debit (RTF 0,245 a six flux) mais **en
latence** — 162 ms avant le premier son a un flux, 614 ms a six, pendant que le
processeur reste bas. Une machine pleine a donc l'air inactive sur tous les
tableaux de bord habituels, et c'est le delai avant premier fragment qui doit
etre surveille.

Deux mecanismes en decoulent, et un troisieme vient du LLM :
  - une file bornee, pour que le dixieme appel n'abime pas les neuf autres ;
  - la mesure systematique du premier fragment, comme metrique de production ;
  - un delai de garde : au-dela du seuil, l'agent parle plutot que de laisser le
    silence s'installer (mesures 14 et 20 : 935 ms au p90, 8 751 ms au pire).
"""

from __future__ import annotations

import statistics
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Callable, Iterator

from standard.regles import PARALLELISME_SYNTHESE, SEUIL_GARDE_MS

# Plusieurs formulations, parce qu'une machine qui repete mot pour mot la meme
# phrase est une machine qui boucle (mesure 16).
ATTENTES = (
    "Je vérifie, un instant.",
    "Je regarde ça tout de suite.",
    "Un instant, je consulte l'agenda.",
)


class FileDeSynthese:
    """Borne le nombre de syntheses simultanees.

    Sans borne, le dixieme appel degrade les neuf autres ; avec borne, il attend
    quelques dizaines de millisecondes et personne ne s'en apercoit.
    """

    def __init__(self, parallelisme: int = PARALLELISME_SYNTHESE):
        self.parallelisme = parallelisme
        self._jetons = threading.Semaphore(parallelisme)

    @contextmanager
    def place(self):
        self._jetons.acquire()
        try:
            yield
        finally:
            self._jetons.release()


class DelaiDeGarde:
    """Au-dela du seuil sans reponse, l'agent parle. Il ne laisse pas le silence.

    Le silence au telephone n'est pas neutre : l'appelant croit que la ligne a
    coupe. Et la mesure 20 a montre que la latence d'un fournisseur distant est
    une variable aleatoire bornee par le haut, pas un service a latence garantie.
    """

    def __init__(self, seuil_ms: int = SEUIL_GARDE_MS, attentes=ATTENTES):
        self.seuil_ms = seuil_ms
        self._attentes = list(attentes)
        self._prochaine = 0

    def _phrase_d_attente(self) -> str:
        phrase = self._attentes[self._prochaine % len(self._attentes)]
        self._prochaine += 1
        return phrase

    def attendre(self, producteur: Callable[[], object],
                 sur_attente: Callable[[str], None] | None = None):
        """Lance `producteur`, et fait parler l'agent si le seuil est depasse."""
        resultat: list = []
        erreur: list = []

        def travail():
            try:
                resultat.append(producteur())
            except Exception as e:      # l'erreur remonte a l'appelant, jamais au client
                erreur.append(e)

        fil = threading.Thread(target=travail, daemon=True)
        fil.start()
        fil.join(self.seuil_ms / 1000)
        if fil.is_alive() and sur_attente is not None:
            sur_attente(self._phrase_d_attente())
        fil.join()
        if erreur:
            raise erreur[0]
        return resultat[0] if resultat else None


@dataclass
class Parole:
    """Synthetise en flux, sous quota, et mesure ce qui dit qu'on est plein."""

    synthetiseur: Callable[[str], Iterator[bytes]]
    file: FileDeSynthese = field(default_factory=FileDeSynthese)
    mesures: list[float] = field(default_factory=list)
    dernier_premier_fragment_ms: float | None = None

    def dire(self, texte: str) -> Iterator[bytes]:
        """Rend les fragments **au fil de l'eau** : rien n'est materialise en entier.

        Le binaire Piper synthetisait la phrase complete avant d'ecrire son
        fichier — 372 ms de TTFB contre 162 ms par l'API en flux (mesure 13).
        """
        with self.file.place():
            depart = time.perf_counter()
            premier = True
            for fragment in self.synthetiseur(texte):
                if premier:
                    self.dernier_premier_fragment_ms = (time.perf_counter() - depart) * 1000
                    self.mesures.append(self.dernier_premier_fragment_ms)
                    premier = False
                yield fragment

    @property
    def p50_premier_fragment_ms(self) -> float | None:
        """La metrique de supervision : c'est elle qui dit qu'une machine est pleine,
        bien avant la charge processeur, qui reste basse jusqu'au bout."""
        return statistics.median(self.mesures) if self.mesures else None
