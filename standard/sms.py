"""Le SMS de confirmation — premier poste de coût, et piège réglementaire.

Deux choses à savoir avant d'écrire une ligne, toutes deux vérifiées le
19/09/2026.

**Un rappel ou une confirmation de rendez-vous est un SMS transactionnel** : ni
opt-in marketing, ni mention STOP, ni restriction d'horaire. C'est ce qui rend le
produit possible — un rendez-vous pris à 22 h se confirme à 22 h.

**Mais une seule phrase promotionnelle le fait basculer** dans le régime
commercial : STOP obligatoire, horaires imposés, consentement préalable. Le
manquement coûte **750 € par message** au titre du code des postes et des
communications électroniques. D'où le garde-fou principal de ce module : on
**détecte** la bascule au lieu de la subir.

Et le coût : le SMS est le premier poste de dépense du produit, devant le STT, le
TTS, le modèle et la téléphonie réunis. Un message qui déborde d'un caractère
coûte deux fois plus cher — d'où le compte de segments, et l'attention portée aux
caractères hors alphabet GSM.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

JOURS = ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche")
MOIS = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre")

# Alphabet GSM 03.38 (jeu de base). Tout caractère absent force l'UCS-2, et fait
# tomber la capacité de 160 à 70 caractères.
GSM = set("@£$¥èéùìòÇØøÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?"
          "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà\n\r")
GSM_ETENDU = set("^{}\\[~]|€")          # ces caractères comptent double

CAPACITE_GSM = 160
CAPACITE_GSM_MULTI = 153                # l'en-tête de concaténation mange 7 caractères
CAPACITE_UCS2 = 70
CAPACITE_UCS2_MULTI = 67

EXPEDITEUR_MAX = 11                     # limite de l'expéditeur alphanumérique

MOTS_PROMOTIONNELS = (
    "%", "promo", "offre", "réduction", "reduction", "gratuit", "profitez",
    "découvrez", "decouvrez", "parrainez", "soldes", "nouveauté", "nouveaute",
    "exclusif", "bon plan",
)


class MessageRefuse(RuntimeError):
    """Le message ne peut pas partir tel quel."""


@dataclass
class Verdict:
    nature: str                 # transactionnel | commercial
    stop_requis: bool
    horaires_imposes: bool
    segments: int
    motifs: list[str]


def _sans_accents(texte: str) -> str:
    plat = unicodedata.normalize("NFD", texte.lower())
    return "".join(c for c in plat if unicodedata.category(c) != "Mn")


def compter_segments(message: str) -> int:
    """Nombre de SMS facturés. Un caractère hors alphabet GSM change tout."""
    if not message:
        return 0
    if all(c in GSM or c in GSM_ETENDU for c in message):
        longueur = sum(2 if c in GSM_ETENDU else 1 for c in message)
        if longueur <= CAPACITE_GSM:
            return 1
        return -(-longueur // CAPACITE_GSM_MULTI)
    longueur = len(message)
    if longueur <= CAPACITE_UCS2:
        return 1
    return -(-longueur // CAPACITE_UCS2_MULTI)


def composer_confirmation(rendez_vous: dict) -> str:
    """Le message le plus court qui dise tout — et tienne en un seul segment.

    On écrit la date comme l'agent l'a prononcée (jour, quantième, mois) pour que
    le client retrouve à l'écrit ce qu'il a entendu au téléphone.
    """
    from datetime import date

    jour = date.fromisoformat(rendez_vous["date"])
    quand = f"{JOURS[jour.weekday()]} {jour.day} {MOIS[jour.month - 1]}"
    heure = rendez_vous["heure"].replace(":", "h")
    prestation = rendez_vous.get("prestation")
    quoi = f" ({prestation})" if prestation else ""
    return (f"{rendez_vous['salon']} : rendez-vous confirmé {quand} à {heure}{quoi}. "
            f"Pour annuler, rappelez-nous.")


def verifier_message(message: str, exiger_conformite: bool = False) -> Verdict:
    """Dit si le message est transactionnel, et ce que cela impose.

    Le sens de la vérification compte : on ne cherche pas à prouver que le
    message est conforme, on cherche **ce qui le ferait basculer**.
    """
    plat = _sans_accents(message)
    motifs = [mot for mot in MOTS_PROMOTIONNELS if _sans_accents(mot) in plat]
    commercial = bool(motifs)

    verdict = Verdict(
        nature="commercial" if commercial else "transactionnel",
        stop_requis=commercial,
        horaires_imposes=commercial,
        segments=compter_segments(message),
        motifs=motifs)

    if exiger_conformite and commercial and "stop" not in plat:
        raise MessageRefuse(
            "message commercial sans mention STOP : 750 € par message. "
            f"Termes relevés : {', '.join(motifs)}")
    return verdict


def expediteur_valide(expediteur: str, nom_commercial: str) -> bool:
    """L'expéditeur alphanumérique doit être le nom du salon, pas un slogan.

    Charte AF2M du 1er mars 2026 : il correspond au nom commercial de l'annonceur
    ou à une marque dont il est titulaire. Onze caractères au maximum, et rien
    d'autre que des lettres et des chiffres.
    """
    if not expediteur or len(expediteur) > EXPEDITEUR_MAX:
        return False
    if not re.fullmatch(r"[A-Za-z0-9]+", expediteur):
        return False
    if expediteur.isdigit():
        return False                    # un numéro court n'est pas un nom de marque

    # Le nom doit se retrouver dans le nom commercial, accents et espaces ôtés.
    reference = re.sub(r"[^a-z0-9]", "", _sans_accents(nom_commercial))
    candidat = _sans_accents(expediteur)
    return candidat in reference or reference.startswith(candidat[:6])
