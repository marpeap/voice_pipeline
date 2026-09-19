"""Capter le numéro de l'appelant — sans quoi aucun SMS ne peut partir.

Trois faits se rejoignent ici :
  - l'agent ne peut pas compter sur l'identifiant d'appelant : l'Arcep recommande
    de le masquer sur les renvois complexes (`docs/19`), donc **le numéro se
    demande à voix haute** ;
  - quatre numéros sur dix se perdent à l'oral, et de la même façon en 16 et en
    8 kHz (mesure 7) — d'où la relecture, systématique depuis la mesure 21 ;
  - après deux échecs, on bascule au clavier (règle T7), et `session.py` sait
    déjà ramasser les touches DTMF.
"""

import json
from datetime import date

import pytest

from standard.appel import Appel
from standard.decision import Agenda

MARDI = date(2026, 9, 15)


class ModeleScripte:
    def __init__(self, reponses):
        self.reponses = list(reponses)
        self.appels = 0

    def completer(self, messages, **parametres):
        charge = self.reponses[min(self.appels, len(self.reponses) - 1)]
        self.appels += 1
        return json.dumps({"prestation": None, "manque": [],
                           "confiance": {"intention": 0.95, "date": 0.95, "heure": 0.95},
                           **charge})


class Base:
    def __init__(self):
        self.lignes = {}

    def inserer(self, cle, donnees):
        self.lignes[cle] = dict(donnees)
        return f"rdv-{len(self.lignes)}"

    def relire(self, reference):
        return list(self.lignes.values())[int(reference.split("-")[1]) - 1]


class EnvoyeurFactice:
    def __init__(self):
        self.envois = []

    def confirmer(self, telephone, rendez_vous):
        from standard.sms import Envoi
        self.envois.append((telephone, rendez_vous))
        return Envoi(True, segments=1, accuse_de_remise=True)


def conversation(base=None, envoyeur=None):
    appel = Appel(client_modele=ModeleScripte([{"intention": "rdv", "date": "2026-09-17",
                                                "heure": "15:30"}]),
                  agenda=Agenda(aujourd_hui=MARDI, creneaux={"15:30"}, jours_fermes=(6, 0)),
                  base=base or Base(), memoire="", consignes_communes="c",
                  tenant="salon-1", identifiant="appel-1")
    appel.envoyeur_sms = envoyeur
    # Ces tests portent sur le numéro : la fiche désactive la demande du nom
    # (question D5), qui a son propre fichier de tests.
    appel.fiche = {"reservation": {"nom": "non"}}
    return appel


# --- le numéro se demande ---------------------------------------------------

def test_apres_l_accord_l_agent_demande_le_numero():
    """Il ne peut pas le lire sur l'écran : l'identifiant d'appelant est souvent
    masqué après un renvoi (Arcep)."""
    appel = conversation(envoyeur=EnvoyeurFactice())
    appel.tour("JEUDI QUINZE HEURES TRENTE")
    reponse = appel.tour("oui c'est parfait")
    assert reponse.genre == "question"
    assert "numéro" in reponse.phrase.lower()


def test_sans_envoyeur_de_sms_on_ne_demande_rien():
    """Demander un numéro dont on ne fera rien est une question de trop."""
    appel = conversation()
    appel.tour("JEUDI QUINZE HEURES TRENTE")
    reponse = appel.tour("oui")
    assert reponse.genre == "confirmation"


# --- la relecture -----------------------------------------------------------

def test_le_numero_donne_est_relu_avant_d_etre_garde():
    """Mesure 21 : un moteur qui écrit des chiffres tranche les ambiguïtés en
    silence. Il n'y a plus de doute observable, donc la relecture est
    inconditionnelle."""
    appel = conversation(envoyeur=EnvoyeurFactice())
    appel.tour("JEUDI QUINZE HEURES TRENTE")
    appel.tour("oui")
    reponse = appel.tour("zéro six douze trente-quatre cinquante-six soixante-dix-huit")
    assert "zéro six" in reponse.phrase.lower()
    assert "?" in reponse.phrase


def test_le_numero_confirme_declenche_ecriture_et_sms():
    envoyeur = EnvoyeurFactice()
    base = Base()
    appel = conversation(base, envoyeur)
    appel.tour("JEUDI QUINZE HEURES TRENTE")
    appel.tour("oui")
    appel.tour("zéro six douze trente-quatre cinquante-six soixante-dix-huit")
    reponse = appel.tour("oui c'est ça")
    assert reponse.genre == "confirmation"
    assert envoyeur.envois and envoyeur.envois[0][0] == "0612345678"


def test_un_numero_incomplet_est_redemande_jamais_complete():
    appel = conversation(envoyeur=EnvoyeurFactice())
    appel.tour("JEUDI QUINZE HEURES TRENTE")
    appel.tour("oui")
    reponse = appel.tour("zéro six douze trente-quatre")
    assert reponse.genre == "question"
    assert "0612" not in reponse.phrase


# --- le clavier, après deux échecs (règle T7) -------------------------------

def test_apres_deux_echecs_l_agent_bascule_au_clavier():
    bascules = []
    appel = conversation(envoyeur=EnvoyeurFactice())
    appel.basculer_clavier = lambda: bascules.append(True)
    appel.tour("JEUDI QUINZE HEURES TRENTE")
    appel.tour("oui")
    appel.tour("zéro six douze")             # premier échec
    reponse = appel.tour("euh je ne sais plus")   # second échec
    assert bascules, "le filet DTMF de la règle T7 n'a pas été déclenché"
    assert "clavier" in reponse.phrase.lower() or "touches" in reponse.phrase.lower()


def test_le_numero_compose_au_clavier_est_accepte():
    envoyeur = EnvoyeurFactice()
    appel = conversation(envoyeur=envoyeur)
    appel.tour("JEUDI QUINZE HEURES TRENTE")
    appel.tour("oui")
    reponse = appel.numero_au_clavier("0612345678")
    assert reponse.genre == "confirmation"
    assert envoyeur.envois[0][0] == "0612345678"


def test_un_numero_special_est_refuse_meme_au_clavier():
    appel = conversation(envoyeur=EnvoyeurFactice())
    appel.tour("JEUDI QUINZE HEURES TRENTE")
    appel.tour("oui")
    reponse = appel.numero_au_clavier("0812345678")
    assert reponse.genre != "confirmation"
