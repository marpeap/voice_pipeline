"""Répondre à une question de fait — et seulement quand la fiche le permet.

Banc du 19/09, scénario `aucune-demande` joué avec les vrais moteurs : à
« je voulais connaître vos horaires d'ouverture », l'agent répondait « Que
puis-je faire pour vous ? ». Deux tours de ce genre et il passe la main. Or le
salon a répondu à la question A2 du pack : **l'information était là, personne
n'allait la chercher.**

Ce module ne fabrique rien. Il lit le frontmatter, et si le champ manque, il le
dit — c'est l'interdit du pack, « ne jamais annoncer un prix qui n'a pas été
saisi par le salon », appliqué à toutes les questions de fait.
"""

from __future__ import annotations

from standard.decision import enoncer_heure
from standard.regles import JOURS
from standard.texte import aplatir

MOTS_HORAIRES = ("horaire", "horaires", "ouvert", "ouverte", "ouverts", "ouverture",
                 "fermez", "fermeture", "fermes", "ouvrez", "ouvre")
MOTS_PRIX = ("prix", "tarif", "tarifs", "combien coute", "combien ca coute",
             "combien coutent", "c est combien", "ca coute combien")

MOTS_ADRESSE = ("adresse", "ou etes vous", "vous etes ou", "ou vous etes",
                "vous etes situes", "comment on vient", "comment venir",
                "ou se trouve", "vous trouver", "y aller")
"""L'adresse est la question la plus posee apres les horaires — et le produit
n'y repondait pas, faute d'un champ pour l'ecrire."""


def _plat(texte: str) -> str:
    return aplatir(texte, garder="a-z' ")


def _plage(plage: str) -> str:
    """« 09:00-19:00 » se dit « de 9 h à 19 h »."""
    debut, fin = plage.split("-")
    return f"de {enoncer_heure(debut)} à {enoncer_heure(fin)}"


def _enoncer_les_horaires(ouverture: dict) -> str | None:
    """Regroupe les jours consécutifs de mêmes horaires.

    Sept phrases d'horaires ne s'écoutent pas au téléphone : « du mardi au
    vendredi de 9 h à 19 h » est ce qu'un humain dirait (loi de Miller, 4±1).
    """
    ouverts = [(jour, ouverture[jour]) for jour in JOURS
               if ouverture.get(jour)]
    if not ouverts:
        return None

    groupes: list[list] = []
    for jour, plages in ouverts:
        dites = ", ".join(_plage(plage) for plage in plages)
        precedent_contigu = (groupes
                             and groupes[-1][2] == dites
                             and JOURS.index(jour) - JOURS.index(groupes[-1][1]) == 1)
        if precedent_contigu:
            groupes[-1][1] = jour
        else:
            groupes.append([jour, jour, dites])

    morceaux = []
    for premier, dernier, dites in groupes:
        if premier == dernier:
            morceaux.append(f"le {premier} {dites}")
        elif JOURS.index(dernier) - JOURS.index(premier) == 1:
            morceaux.append(f"le {premier} et le {dernier} {dites}")
        else:
            morceaux.append(f"du {premier} au {dernier} {dites}")
    if len(morceaux) == 1:
        corps = morceaux[0]
    else:
        corps = ", ".join(morceaux[:-1]) + ", et " + morceaux[-1]
    return f"Nous sommes ouverts {corps}."


def repondre(transcription: str, frontmatter: dict) -> str | None:
    """La réponse tirée de la fiche, ou `None` si la question n'en est pas une.

    `None` renvoie l'appel au chemin normal : ne pas savoir répondre n'est pas
    une panne, c'est le cas ordinaire.
    """
    plat = _plat(transcription)
    if not plat:
        return None

    if any(mot in plat for mot in MOTS_HORAIRES):
        ouverture = (frontmatter.get("horaires") or {}).get("ouverture") or {}
        dites = _enoncer_les_horaires(ouverture) if isinstance(ouverture, dict) else None
        if dites:
            return dites + " Souhaitez-vous un rendez-vous ?"
        return ("Je n'ai pas les horaires sous les yeux. "
                "Souhaitez-vous que je vous passe quelqu'un du salon ?")

    if any(mot in plat for mot in MOTS_ADRESSE):
        adresse = ((frontmatter.get("salon") or {}).get("adresse")
                   or (frontmatter.get("etablissement") or {}).get("adresse"))
        if adresse:
            return f"Nous sommes au {adresse}. Souhaitez-vous un rendez-vous ?"
        return ("Je n'ai pas l'adresse sous les yeux. "
                "Souhaitez-vous que je vous passe quelqu'un du salon ?")

    if any(mot in plat for mot in MOTS_PRIX):
        return _repondre_sur_le_prix(plat, frontmatter)

    return None


def _repondre_sur_le_prix(plat: str, frontmatter: dict) -> str:
    """Le tarif saisi par le salon, ou rien — jamais une fourchette.

    Le pack decide d'abord si l'agent annonce les prix (question C2) : quand le
    salon a repondu « non, il oriente vers moi », aucun tarif ne sort, meme
    saisi. Et un prix qui n'a pas ete saisi ne s'invente pas : c'est le premier
    interdit ecrit dans les trois packs.
    """
    prix = frontmatter.get("prix") or {}
    if str(prix.get("annonce", "non")) != "oui":
        return ("Je préfère vous passer quelqu'un du salon pour les tarifs. "
                "Souhaitez-vous un rendez-vous en attendant ?")

    tarifs = prix.get("tarifs") or {}
    for prestation, montant in tarifs.items():
        if _plat(prestation) in plat:
            # « Comptez X euros pour Y » evite l'article : « le tarif pour
            # coupe » s'entend mal, et « une coloration » / « un brushing » ne
            # se devinent pas depuis le catalogue.
            return (f"Comptez {montant} euros pour {prestation}. "
                    "Souhaitez-vous un rendez-vous ?")
    return ("Je préfère ne pas vous donner un prix au hasard. "
            "Souhaitez-vous que je vous passe quelqu'un du salon ?")
