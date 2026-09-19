"""L'ecriture — la seule piece du produit qui ait le droit de dire que c'est fait.

Mesure 14 : sur douze tours, un agent « prompt seul » a produit **deux
confirmations orphelines**, dont « votre rendez-vous de demain matin est
annule » — rien n'etait ecrit nulle part, et le client s'organise la-dessus.

D'ou la regle, qui n'est pas une precaution mais la definition du module :
**aucune phrase de confirmation n'existe ailleurs dans le code.** La decision
propose, l'ecriture confirme — et seulement apres avoir **relu** ce qu'elle
vient d'ecrire (docs/04 §C2.3).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Protocol

from standard.decision import enoncer_date, enoncer_heure
from standard.depot import ChevauchementRefuse
from standard.regles import VERBES_DE_CONFIRMATION


class BaseRendezVous(Protocol):
    """Ce que l'ecriture attend d'une base, et rien de plus."""

    def inserer(self, cle: str, donnees: dict) -> str: ...
    def relire(self, reference: str) -> dict | None: ...


def cle_idempotence(tenant: str, appel: str, tour: int) -> str:
    """Cle generee **au debut du tour de parole**, jamais a l'envoi.

    Si elle etait calculee au moment de la requete, deux tentatives du meme tour
    porteraient deux cles differentes et creeraient deux rendez-vous — le defaut
    que l'idempotence est censee empecher.
    """
    graine = f"{tenant}|{appel}|{tour}".encode()
    return hashlib.sha256(graine).hexdigest()[:32]


@dataclass
class JournalEcriture:
    """Le taux de confirmation orpheline est un incident, pas une statistique.

    Cible : **zero**. Toute occurrence se lit dans `incidents`, avec de quoi
    remonter a l'appel.
    """
    incidents: list[dict[str, Any]] = field(default_factory=list)
    ecritures: int = 0
    relectures_muettes: int = 0
    creneaux_perdus: int = 0        # pris par quelqu'un d'autre pendant l'appel

    @property
    def orphelines(self) -> int:
        return len(self.incidents)

    def noter_confirmation_orpheline(self, reference: str, detail: str = "") -> None:
        self.incidents.append({"reference": reference, "detail": detail})


@dataclass
class Ecriture:
    statut: str               # confirme | rejoue | incertain
    phrase: str               # ce que l'agent prononce, et lui seul
    reference: str | None = None


def _phrase_de_confirmation(donnees: dict, promet_sms: bool = False) -> str:
    """La seule phrase du produit qui affirme qu'un rendez-vous existe.

    Elle porte le jour de la semaine en plus du quantieme (regle E1, mesure 19) :
    « jeudi dix-sept » devient « jeudi dix » dans le canal, et c'est la
    redondance du jour qui permet au client de detecter l'erreur.
    """
    quand = f"{enoncer_date(donnees['date'])} à {enoncer_heure(donnees['heure'])}"
    prestation = donnees.get("prestation")
    quoi = f"votre {prestation}" if prestation else "votre rendez-vous"
    # Le verbe vient de la source unique : c'est la seule phrase du produit
    # autorisee a le porter, et elle ne peut pas diverger de la liste que les
    # tests interdisent partout ailleurs.
    # On ne promet un SMS que si un SMS peut reellement partir. Annoncer par la
    # voix quelque chose qui n'aura pas lieu est exactement la faute que ce
    # module existe pour empecher — la commettre ici serait la doubler.
    suite = " Vous recevrez un SMS de confirmation." if promet_sms else ""
    return f"{VERBES_DE_CONFIRMATION[1].capitalize()} : {quoi}, {quand}.{suite}"


def _phrase_de_creneau_pris(donnees: dict) -> str:
    """Quelqu'un a pris la place pendant la conversation. On ne promet rien.

    Le cas existe des deux appels simultanes, et l'index unique de la base est
    ce qui l'empeche — pas une verification applicative, qui perd la course.
    """
    quand = f"{enoncer_date(donnees['date'])} à {enoncer_heure(donnees['heure'])}"
    return f"Le {quand} vient d'être pris à l'instant."


def _phrase_d_incertitude() -> str:
    """Quand on ne peut pas relire, on ne promet rien — et on le dit sans mentir."""
    return ("Je n'arrive pas à vérifier que votre rendez-vous est bien enregistré. "
            "Je préfère vous le dire : le salon vous rappellera pour le confirmer.")


def ecrire_rendez_vous(base: BaseRendezVous, cle: str, donnees: dict,
                       journal: JournalEcriture | None = None,
                       promet_sms: bool = False) -> Ecriture:
    """Ecrit, **relit**, et ne confirme que sur une relecture reussie.

    Trois issues, et une seule autorise la phrase de confirmation :
      - `confirme` : ecrit et relu ;
      - `rejoue`   : la meme cle avait deja produit cette ligne, relue elle aussi ;
      - `incertain`: la base n'a pas repondu, ou la relecture n'a rien rendu.
        L'agent dit alors qu'il ne peut pas verifier. Ce n'est pas une
        confirmation orpheline — c'en est exactement le contraire.
    """
    journal = journal or JournalEcriture()

    try:
        reference = base.inserer(cle, donnees)
    except ChevauchementRefuse:
        # Rien d'incertain ici : la place est prise, et le dire est plus utile
        # que « le salon vous rappellera ». La base a tranche, pas le reseau.
        journal.creneaux_perdus += 1
        return Ecriture("occupe", _phrase_de_creneau_pris(donnees))
    except Exception:
        # Une base qui ne repond pas ne se traduit jamais par une promesse.
        return Ecriture("incertain", _phrase_d_incertitude())

    relu = base.relire(reference)
    if relu is None:
        journal.relectures_muettes += 1
        return Ecriture("incertain", _phrase_d_incertitude(), reference)

    journal.ecritures += 1
    return Ecriture("confirme", _phrase_de_confirmation(relu, promet_sms), reference)
