"""La conformité, vérifiée par le produit plutôt que promise par un document.

Trois obligations, et chacune est **testable** — c'est la différence entre une
politique et une garantie :

1. **Annoncer** que l'interlocuteur parle à une machine, dans la première phrase
   (AI Act art. 50 §1, applicable depuis le 02/08/2026). La mesure 19 a montré
   que cette phrase survit au canal téléphonique chez deux moteurs indépendants :
   il n'existe donc aucune raison technique de l'abréger.
2. **Ne pas garder l'audio** une fois la transcription faite. Ce qu'on ne
   conserve pas ne fuit pas, et ne se demande pas non plus.
3. **Ne jamais collecter une adresse e-mail à l'oral.** Un caractère de trop et
   la confirmation part chez quelqu'un d'autre : mobile et SMS, point.

Le registre des traitements (RGPD art. 30) se **dérive** de la configuration.
Un registre tenu à part est un registre périmé.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# Les formulations autorisées viennent des packs (question E3). On ne reconnaît
# pas « une phrase qui parle d'IA » : on reconnaît le fait d'être annoncé comme
# automatique ou virtuel, ce que le commerçant a choisi.
MARQUEURS_ANNONCE = ("assistant automatique", "assistante automatique",
                     "assistant virtuel", "assistante virtuelle",
                     "standard automatique", "répondeur automatique")

# Dictées d'adresse : « arobase », « arrobase », « at », ou le caractère lui-même.
MOTS_AROBASE = ("arobase", "arrobase", " at ", "@")


from standard.texte import sans_accents as _plat


@dataclass
class VerdictAnnonce:
    conforme: bool
    formulation: str | None = None


def verifier_annonce(phrase: str) -> VerdictAnnonce:
    """L'annonce est-elle présente, telle qu'elle sera entendue ?"""
    plat = _plat(phrase)
    for marqueur in MARQUEURS_ANNONCE:
        if _plat(marqueur) in plat:
            return VerdictAnnonce(True, marqueur)
    return VerdictAnnonce(False)


def est_une_adresse_email(texte: str) -> bool:
    """Reconnaît une adresse, écrite ou **dictée**.

    Un appelant ne dit pas « arobase » par hasard : dès que le mot apparaît avec
    un « point » ou un domaine, c'est une adresse qu'on est en train de nous
    donner — et qu'il faut refuser de prendre.
    """
    plat = _plat(texte)
    if re.search(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", plat):
        return True
    if any(mot in plat for mot in MOTS_AROBASE) and "point" in plat:
        return True
    return False


@dataclass
class ControleConformite:
    """Suit un appel et dit, à la fin, ce qui a été respecté et ce qui ne l'a pas été."""

    effacer_l_audio: bool = True
    audio_conserve: int = 0
    donnees_collectees: list[tuple[str, str]] = field(default_factory=list)
    _phrases: list[str] = field(default_factory=list, repr=False)
    _emails_refuses: int = 0
    _transcriptions: int = 0

    # --- ce que l'agent dit -------------------------------------------------

    def tour(self, phrase: str) -> None:
        self._phrases.append(phrase)

    # --- ce que l'agent entend ----------------------------------------------

    def audio_recu(self, morceau: bytes) -> None:
        self.audio_conserve += len(morceau)

    def transcrit(self, texte: str) -> None:
        """Le texte existe : l'audio n'a plus de raison d'être."""
        self._transcriptions += 1
        if self.effacer_l_audio:
            self.audio_conserve = 0
        if est_une_adresse_email(texte):
            # On ne l'enregistre pas, et on compte le refus : c'est ce compteur
            # qui prouve que la règle tient, plutôt qu'une note dans un document.
            self._emails_refuses += 1

    def entite(self, nom: str, valeur: str) -> bool:
        """Enregistre une donnée — sauf si c'est une adresse e-mail."""
        if nom == "email" or est_une_adresse_email(valeur):
            self._emails_refuses += 1
            return False
        self.donnees_collectees.append((nom, valeur))
        return True

    # --- le verdict ---------------------------------------------------------

    def rapport(self) -> dict:
        annonce = verifier_annonce(self._phrases[0]) if self._phrases else VerdictAnnonce(False)
        manquements = []
        if not annonce.conforme:
            manquements.append("l'annonce d'agent automatique n'est pas dans la première phrase")
        if self.audio_conserve:
            manquements.append(f"audio conservé après transcription : {self.audio_conserve} octets")
        return {
            "annonce_conforme": annonce.conforme,
            "formulation": annonce.formulation,
            "audio_conserve_octets": self.audio_conserve,
            "emails_refuses": self._emails_refuses,
            "donnees_collectees": [nom for nom, _ in self.donnees_collectees],
            "manquements": manquements,
        }


@dataclass
class RegistreDesTraitements:
    """Le registre RGPD art. 30, dérivé de la configuration du service.

    Il ne décrit que ce que le produit fait réellement : **on ne déclare pas une
    catégorie qu'on ne collecte pas**, sous peine de devoir la justifier — et de
    laisser croire qu'on la garde.
    """

    responsable: str
    sous_traitant: str
    finalite: str
    conservation_jours: int
    destinataires: list[str] = field(default_factory=list)

    def rendre(self) -> str:
        destinataires = ", ".join(self.destinataires) if self.destinataires \
            else "aucun, hors hébergeur"
        return f"""# Registre des traitements — {self.responsable}

*Établi au titre de l'article 30 du RGPD. Ce document est **produit par le
service** à partir de sa configuration : il ne peut pas décrire autre chose que
ce que le logiciel fait.*

| | |
|---|---|
| **Responsable de traitement** | {self.responsable} |
| **Sous-traitant** | {self.sous_traitant}, au titre de l'**article 28** du RGPD |
| **Finalité** | {self.finalite} |
| **Base légale** | exécution de mesures précontractuelles à la demande de la personne (art. 6.1.b) |
| **Durée de conservation** | {self.conservation_jours} jours |
| **Destinataires** | {destinataires} |

## Catégories de données

- **nom** tel que donné par l'appelant ;
- **numéro de mobile**, pour la confirmation par SMS ;
- **date, heure et prestation** du rendez-vous ;
- **transcription** de l'appel, et métadonnées techniques (durée, rapport signal/bruit).

## Ce qui n'est pas collecté, et pourquoi

- **L'enregistrement audio n'est pas conservé** : il est effacé dès que la
  transcription existe. Ce qu'on ne garde pas ne fuit pas.
- **Aucune adresse électronique n'est collectée par la voix.** Une adresse dictée
  est mal comprise plus souvent qu'un numéro, et une erreur d'un caractère envoie
  la confirmation à un inconnu.

## Information des personnes

L'appelant est informé **dès la première phrase** qu'il s'adresse à un système
automatique (AI Act, article 50 §1). Cette annonce n'est pas désactivable par le
commerçant : il en choisit la formulation, pas l'existence.
"""
