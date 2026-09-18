"""La machine a etats : le modele propose, la machine dispose.

Mesure 14 : un agent « prompt seul » faute sur six tours sur douze — creneaux
inventes, faits calendaires inventes, deux confirmations orphelines. Mesure 15 :
avec les garde-fous, zero. La difference n'est pas que le modele s'ameliore,
c'est qu'**il n'a plus la parole**. Ce module ecrit toutes les phrases que
l'appelant entend.

Trois regles, nees de tours reellement joues (docs/15) :
  1. une entite refusee deux fois de suite est oubliee, puis redemandee avec ses
     valeurs possibles ;
  2. jamais deux fois la meme phrase — la premiere repetition change de
     strategie, la seconde passe la main ;
  3. un compteur de progres qui compte des **valeurs neuves**, pas des tours :
     c'est la seule regle que l'alternance ne dejoue pas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]

from standard.regles import (          # une seule source pour les seuils
    ECART_MINIMAL_ENTRE_HORAIRES_MIN,
    REFUS_AVANT_OUBLI,
    SEUIL_CONFIANCE,
    TOURS_SANS_PROGRES_AVANT_TRANSFERT,
)


@dataclass
class Agenda:
    """Ce que la machine sait du temps. Le modele, lui, n'en sait rien (mesure 14)."""
    aujourd_hui: date
    horizon_jours: int = 14
    jours_fermes: tuple[int, ...] = (6,)
    creneaux: set[str] = field(default_factory=set)
    pris: dict[str, set[str]] = field(default_factory=dict)

    def statut(self, jour_iso: str) -> str:
        """hors horizon · ferme · ouvert — trois reponses, jamais une seule.

        Confondre « absent de l'agenda » et « ferme » fait mentir la machine a
        son tour, et de facon invérifiable par le client (mesure 15).
        """
        try:
            jour = date.fromisoformat(jour_iso)
        except (TypeError, ValueError):
            return "inconnu"
        if jour < self.aujourd_hui:
            return "passe"
        if jour > self.aujourd_hui + timedelta(days=self.horizon_jours):
            return "hors horizon"
        if jour.weekday() in self.jours_fermes:
            return "ferme"
        return "ouvert"

    def libres(self, jour_iso: str) -> list[str]:
        return sorted(self.creneaux - self.pris.get(jour_iso, set()))


@dataclass
class Etat:
    """L'etat de la conversation, tenu par la machine et par elle seule."""
    connu: dict[str, str | None] = field(default_factory=dict)
    refus_consecutifs: int = 0
    entite_refusee: str | None = None
    derniere_phrase: str | None = None
    repetitions: int = 0
    valeurs_essayees: dict[str, set[str]] = field(default_factory=dict)
    tours_sans_valeur_neuve: int = 0
    oubliees: set[str] = field(default_factory=set)


@dataclass
class Sortie:
    genre: str          # question | refus | hors horizon | reformulation | proposition | transfert
    phrase: str
    entites: dict[str, str] = field(default_factory=dict)


def enoncer_date(jour_iso: str) -> str:
    """Jour de la semaine + quantieme + mois (regle E1, mesure 19).

    Le quantieme est le mot le plus fragile de tout ce que l'agent dit — « jeudi
    dix-sept » devient « jeudi dix ». C'est la redondance du jour de la semaine
    qui permet au client de detecter l'erreur.
    """
    jour = date.fromisoformat(jour_iso)
    return f"{JOURS[jour.weekday()]} {jour.day} {MOIS[jour.month - 1]}"


def enoncer_heure(heure: str) -> str:
    h, m = heure.split(":")
    return f"{int(h)} h" if m == "00" else f"{int(h)} h {int(m)}"


def espacer(heures: list[str], combien: int = 2) -> list[str]:
    """Des horaires espaces d'au moins une heure (regle E2, mesure 19).

    « neuf heures, neuf heures quarante-cinq, ou dix heures trente » est revenu du
    canal sans sa premiere option : deux horaires proches enonces d'affilee
    fusionnent. Au telephone, le choix se paie en intelligibilite.
    """
    retenus: list[str] = []
    for heure in heures:
        minutes = int(heure[:2]) * 60 + int(heure[3:])
        if all(abs(minutes - (int(r[:2]) * 60 + int(r[3:]))) >= ECART_MINIMAL_ENTRE_HORAIRES_MIN
               for r in retenus):
            retenus.append(heure)
        if len(retenus) == combien:
            break
    return retenus


def _fusionner(proposition: dict, etat: Etat) -> dict:
    """Ce que la machine retient : ce qu'elle savait, plus ce qui est sûr."""
    confiance = proposition.get("confiance") or {}
    manque = set(proposition.get("manque") or [])
    retenu = dict(etat.connu)
    for champ in ("date", "heure", "prestation"):
        if champ in etat.oubliees:
            retenu[champ] = None
            continue
        valeur = proposition.get(champ)
        if valeur and confiance.get(champ, 1.0) >= SEUIL_CONFIANCE and champ not in manque:
            retenu[champ] = valeur
    return retenu


def _progres(retenu: dict, etat: Etat) -> bool:
    """Une valeur JAMAIS ESSAYEE, et rien d'autre.

    Deux definitions ont ete essayees avant celle-ci, et elles echouaient en
    silence (mesure 18) : « le couple a change » comptait un oubli comme une
    avancee, et « une entite est passee de vide a remplie » se laissait rejouer a
    chaque tour par un appelant qui repete la meme phrase.
    """
    neuf = False
    for champ, valeur in retenu.items():
        if not valeur:
            continue
        essayees = etat.valeurs_essayees.setdefault(champ, set())
        if valeur not in essayees:
            essayees.add(valeur)
            neuf = True
    return neuf


def _repondre(genre: str, phrase: str, etat: Etat, entites: dict | None = None) -> Sortie:
    """Applique la regle 2 : jamais deux fois la meme phrase.

    Se repeter ne veut pas dire abandonner : la premiere fois, on change de
    strategie ; c'est seulement si cela echoue aussi qu'on passe la main.
    """
    if phrase == etat.derniere_phrase:
        etat.repetitions += 1
        if etat.repetitions == 1:
            genre = "reformulation"
            phrase = ("Je vais faire autrement : dites-moi seulement le jour qui vous "
                      "arrange, et je vous donnerai les heures libres.")
        else:
            genre = "transfert"
            phrase = "Je crois que je ne vous aide pas. Je vous passe quelqu'un."
    etat.derniere_phrase = phrase
    return Sortie(genre, phrase, entites or {})


def decider(proposition: dict, etat: Etat, agenda: Agenda) -> Sortie:
    """Rend le genre de reponse et **la phrase exacte** que l'agent prononcera.

    Aucune phrase de confirmation n'est prononcable ici : dire qu'un rendez-vous
    est pris appartient a l'ecriture relue, jamais a la decision (mesure 14).
    """
    intention = proposition.get("intention", "inconnu")
    confiance = proposition.get("confiance") or {}

    # Demande d'un humain : transfert immediat, sans negociation (mesure 17).
    if intention == "humain":
        return _repondre("transfert", "Je vous passe quelqu'un du salon, un instant.", etat)

    retenu = _fusionner(proposition, etat)
    etat.connu = retenu
    etat.oubliees.clear()

    if _progres(retenu, etat):
        etat.tours_sans_valeur_neuve = 0
    elif etat.derniere_phrase is not None:
        # Le premier tour ne compte pas : la machine n'a encore rien demande,
        # l'appelant ne peut donc pas avoir « echoue » a faire avancer les choses.
        etat.tours_sans_valeur_neuve += 1
    if etat.tours_sans_valeur_neuve >= TOURS_SANS_PROGRES_AVANT_TRANSFERT:
        return _repondre("transfert",
                         "Je préfère vous passer quelqu'un du salon, ce sera plus simple.", etat)

    if intention == "inconnu" or confiance.get("intention", 1.0) < SEUIL_CONFIANCE:
        return _repondre("question",
                         "Je n'ai pas bien saisi votre demande, pouvez-vous répéter ?", etat)

    if intention == "annulation":
        return _repondre("question",
                         "Pour annuler, pouvez-vous me donner votre nom et votre numéro ?", etat)

    if intention not in ("rdv", "report"):
        return _repondre("question", "Que puis-je faire pour vous ?", etat)

    jour, heure = retenu.get("date"), retenu.get("heure")

    if not jour:
        return _repondre("question", "Quel jour vous conviendrait ?", etat)

    statut = agenda.statut(jour)
    if statut == "hors horizon":
        etat.refus_consecutifs = 0
        return _repondre("hors horizon",
                         "Je ne prends pas encore les rendez-vous aussi loin. "
                         "Rappelez-nous quelques semaines avant.", etat)
    if statut == "ferme":
        return _refuser("Nous sommes fermés ce jour-là, souhaitez-vous un autre jour ?",
                        "date", etat, agenda, jour)
    if statut in ("inconnu", "passe"):
        return _repondre("question",
                         "Je n'ai pas compris la date, pouvez-vous me la redonner ?", etat)

    libres = agenda.libres(jour)
    if not heure:
        propositions = espacer(libres)
        dites = " ou ".join(enoncer_heure(h) for h in propositions)
        return _repondre("question",
                         f"Le {enoncer_date(jour)}, il me reste {dites}. Qu'est-ce qui vous va ?",
                         etat)

    if heure not in libres:
        return _refuser(None, "heure", etat, agenda, jour)

    etat.refus_consecutifs = 0
    return _repondre("proposition",
                     f"Je peux vous réserver le {enoncer_date(jour)} à {enoncer_heure(heure)}. "
                     "Je confirme ?", etat, {"date": jour, "heure": heure})


def _refuser(phrase: str | None, entite: str, etat: Etat, agenda: Agenda, jour: str) -> Sortie:
    """Regle 1 : deux refus de suite sur la meme entite l'invalident.

    Sans elle, la machine garde une valeur que l'appelant ne peut plus corriger —
    et le refus se repete a l'identique jusqu'a l'abandon (mesure 16, la boucle
    infinie polie).
    """
    if etat.entite_refusee == entite:
        etat.refus_consecutifs += 1
    else:
        etat.entite_refusee, etat.refus_consecutifs = entite, 1

    if etat.refus_consecutifs >= REFUS_AVANT_OUBLI:
        etat.refus_consecutifs = 0
        etat.oubliees.add(entite)
        etat.connu[entite] = None
        libres = espacer(agenda.libres(jour), 3)
        dites = ", ".join(enoncer_heure(h) for h in libres)
        return _repondre("question",
                         f"Je n'ai pas ce créneau. Parmi {dites}, lequel vous conviendrait ?",
                         etat)

    if phrase is None:
        libres = espacer(agenda.libres(jour), 2)
        dites = " ou ".join(enoncer_heure(h) for h in libres)
        phrase = f"Ce créneau n'est pas libre. Il me reste {dites}."
    return _repondre("refus", phrase, etat)
