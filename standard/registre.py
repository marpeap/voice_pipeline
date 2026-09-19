"""Le registre des traitements (RGPD art. 30), **dérivé de ce qui tourne**.

Un registre recopié à la main devient faux au premier changement de moteur — et
un registre faux est pire qu'un registre absent, parce qu'il affirme. Les
mentions obligatoires sont donc lues dans la configuration réelle et dans
`regles` : la durée annoncée ici est exactement celle que `entretien` applique.

Ce que la recherche du 19/09 confirme : la CNIL recommande **six mois au
maximum** pour les enregistrements d'appels et leurs transcriptions, hors
obligation sectorielle ; le produit tient 90 jours. L'appel lui-même n'est
jamais enregistré — seules les transcriptions le sont, ce que le registre dit.
"""

from __future__ import annotations

import os
from typing import Mapping
from urllib.parse import urlsplit

from standard.regles import CONSERVATION_JOURS

MENTION_LEGALE = "art. 30 du règlement (UE) 2016/679"


def _hote(url: str) -> str:
    """L'hôte seul : une URL complète peut porter une clé en paramètre."""
    decoupe = urlsplit(url if "//" in url else f"https://{url}")
    return decoupe.hostname or url


def _moteurs(env: Mapping[str, str]) -> list[str]:
    """Qui voit la voix et les transcriptions, en clair, dans ce déploiement."""
    destinataires = []
    if env.get("STANDARD_STT", "local") == "distant" and env.get("STANDARD_STT_BASE"):
        destinataires.append(f"transcription : {_hote(env['STANDARD_STT_BASE'])}")
    else:
        destinataires.append("transcription : aucun — le moteur tourne sur la machine")
    if env.get("STANDARD_MODELE_BASE"):
        destinataires.append(f"compréhension : {_hote(env['STANDARD_MODELE_BASE'])}")
    else:
        destinataires.append("compréhension : aucun — aucune requête ne sort de la machine")
    return destinataires


def registre_des_traitements(environnement: Mapping[str, str] | None = None) -> dict:
    """Le registre, tel que ce déploiement-ci le remplit."""
    env = dict(environnement if environnement is not None else os.environ)
    responsable = env.get("STANDARD_RESPONSABLE") or env.get("STANDARD_TENANT", "inconnu")
    destinataires = _moteurs(env)
    hors_ue = "aucun" if all("aucun" in d for d in destinataires) else \
        "à vérifier auprès de chaque fournisseur nommé ci-dessus"

    traitements = [
        {
            "nom": "appels",
            "finalite": "prendre, déplacer ou annuler un rendez-vous par téléphone, "
                        "et prendre un message quand le salon l'a choisi",
            "base_legale": "intérêt légitime du commerçant à répondre aux appels "
                           "(art. 6.1.f) ; mesures précontractuelles pour le "
                           "rendez-vous lui-même (art. 6.1.b)",
            "categories": ["transcription de ce qui est dit pendant l'appel",
                           "nom donné par l'appelant",
                           "numéro de mobile, s'il est donné",
                           "date, heure et prestation du rendez-vous"],
            "personnes_concernees": ["clients et prospects du commerçant"],
            "destinataires": destinataires,
            "duree_conservation_jours": CONSERVATION_JOURS,
            "transferts_hors_ue": hors_ue,
            "responsable": responsable,
            "mesures_de_securite": [
                "aucun enregistrement audio conservé : seule la transcription l'est",
                "cloisonnement par locataire dans la base (RLS ENABLE et FORCE)",
                "purge automatique au-delà de la durée annoncée (standard.entretien)",
                "annonce automatique de la nature artificielle de l'agent "
                "(AI Act art. 50), conservée comme preuve datée",
            ],
        },
        {
            "nom": "journal d'exploitation",
            "finalite": "diagnostiquer un appel raté sans le réécouter, et corriger "
                        "l'agent depuis la console du commerçant",
            "base_legale": "intérêt légitime (art. 6.1.f)",
            "categories": ["transcriptions", "phrases dites par l'agent",
                           "indicateurs techniques (bruit, interruptions)"],
            "personnes_concernees": ["clients et prospects du commerçant"],
            "destinataires": ["le commerçant, par la console"],
            "duree_conservation_jours": CONSERVATION_JOURS,
            "transferts_hors_ue": "aucun",
            "responsable": responsable,
            "mesures_de_securite": ["accès par jeton, débit borné, piste d'audit "
                                    "de chaque correction posée"],
        },
    ]

    if env.get("STANDARD_SMS_EXPEDITEUR"):
        passerelle = env.get("STANDARD_SMS_BASE")
        traitements.append({
            "nom": "sms",
            "finalite": "confirmer par écrit un rendez-vous pris à l'oral",
            "base_legale": "exécution de mesures précontractuelles (art. 6.1.b) ; "
                           "message transactionnel, sans contenu promotionnel",
            "categories": ["numéro de mobile", "date et heure du rendez-vous",
                           "nom du commerçant"],
            "personnes_concernees": ["clients ayant donné leur numéro"],
            "destinataires": [f"passerelle SMS : {_hote(passerelle)}" if passerelle
                              else "passerelle SMS : aucune — les messages sont consignés"],
            "duree_conservation_jours": CONSERVATION_JOURS,
            "transferts_hors_ue": "à vérifier auprès de la passerelle" if passerelle
                                  else "aucun",
            "responsable": responsable,
            "mesures_de_securite": ["aucun contenu promotionnel — un seul mot "
                                    "publicitaire ferait basculer le message en "
                                    "prospection commerciale (CPCE)"],
        })

    return {"mention": MENTION_LEGALE, "responsable": responsable,
            "traitements": traitements}


def rendre_en_texte(registre: dict) -> str:
    """Le même registre, imprimable — c'est sous cette forme qu'on le remet."""
    lignes = [f"Registre des traitements — {MENTION_LEGALE}",
              f"Responsable : {registre['responsable']}", ""]
    for traitement in registre["traitements"]:
        lignes.append(f"## {traitement['nom']}")
        for cle, valeur in traitement.items():
            if cle == "nom":
                continue
            libelle = cle.replace("_", " ")
            if isinstance(valeur, list):
                lignes.append(f"- {libelle} :")
                lignes.extend(f"    - {element}" for element in valeur)
            else:
                lignes.append(f"- {libelle} : {valeur}")
        lignes.append("")
    return "\n".join(lignes)
