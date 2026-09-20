"""Quand deux choses tombent en même temps.

Chaque incident a son chemin — moteur muet, base verrouillée, passerelle SMS
sourde — et chacun est testé seul. Un vrai standard ne tombe pas proprement :
la machine qui rame fait aussi expirer la base, et l'opérateur SMS répond mal
au même moment.

La règle ne change pas : **l'agent ne promet que ce qui est vérifié.** Ce
fichier vérifie qu'elle tient quand deux garanties s'appuient l'une sur l'autre.
"""

from datetime import date

import pytest

from standard.appel import Appel
from standard.decision import Agenda
from standard.hors_ligne import ModeleHorsLigne

MARDI = date(2026, 9, 15)


class BaseFactice:
    def __init__(self, muette=False):
        self.lignes, self.par_cle, self.muette = {}, {}, muette

    def inserer(self, cle, donnees):
        if cle in self.par_cle:
            return self.par_cle[cle]
        reference = f"rdv-{len(self.lignes) + 1}"
        self.lignes[reference] = dict(donnees)
        self.par_cle[cle] = reference
        return reference

    def relire(self, reference):
        return None if self.muette else self.lignes.get(reference)

    def corriger(self, reference, champs):
        if reference not in self.lignes:
            return None
        self.lignes[reference].update(champs)
        return None if self.muette else self.lignes[reference]


class PasserelleSourde:
    peut_promettre = True

    def __init__(self, motif="délai dépassé"):
        self.motif = motif
        self.tentatives = 0

    def confirmer(self, telephone, rendez_vous):
        from standard.sms import Envoi
        self.tentatives += 1
        return Envoi(False, reserve=self.motif)


def conversation(base=None, envoyeur=None, telephone=None):
    appel = Appel(client_modele=ModeleHorsLigne(aujourd_hui=MARDI),
                  agenda=Agenda(aujourd_hui=MARDI, creneaux={"15:30"}, jours_fermes=(6, 0)),
                  base=base or BaseFactice(), memoire="", consignes_communes="c",
                  tenant="salon-1", identifiant="appel-1")
    appel.fiche = {"reservation": {"nom": "non"}}
    appel.envoyeur_sms = envoyeur
    if telephone:
        appel.etat.connu["telephone"] = telephone
    return appel


# --- une passerelle sourde ne doit pas faire mentir la confirmation ---------

def test_un_sms_qui_ne_part_pas_n_est_jamais_promis():
    """Le numéro est connu d'avance (identifiant d'appelant) : la phrase de
    confirmation partait AVANT l'envoi, et promettait un SMS qui échouait."""
    passerelle = PasserelleSourde()
    appel = conversation(envoyeur=passerelle, telephone="0612345678")
    appel.tour("je voudrais un rendez-vous jeudi à quinze heures trente")
    phrase = appel.tour("oui c'est parfait").phrase

    assert passerelle.tentatives == 1, "l'envoi doit être tenté"
    assert "SMS" not in phrase, phrase
    assert "enregistré" in phrase, "le rendez-vous, lui, est bien pris"


def test_un_sms_qui_part_est_annonce():
    class Passerelle(PasserelleSourde):
        def confirmer(self, telephone, rendez_vous):
            from standard.sms import Envoi
            self.tentatives += 1
            return Envoi(True, segments=1, accuse_de_remise=True)

    appel = conversation(envoyeur=Passerelle(), telephone="0612345678")
    appel.tour("je voudrais un rendez-vous jeudi à quinze heures trente")
    assert "SMS" in appel.tour("oui c'est parfait").phrase


def test_l_echec_d_envoi_est_journalise_avec_son_motif():
    passerelle = PasserelleSourde(motif="HTTP 502")
    appel = conversation(envoyeur=passerelle, telephone="0612345678")
    appel.tour("je voudrais un rendez-vous jeudi à quinze heures trente")
    appel.tour("oui c'est parfait")
    traces = [t for t in appel.journal.tours if t.get("sms")]
    assert traces and traces[-1]["sms"] == "échec"
    assert "502" in str(traces[-1].get("sms_reserve", ""))


# --- base muette ET passerelle sourde --------------------------------------

def test_une_base_muette_ne_promet_rien_meme_avec_un_sms_possible():
    """Deux garanties qui tombent ensemble : l'écriture n'est pas relue, donc
    rien n'est confirmé — et aucun SMS ne part pour un rendez-vous incertain."""
    passerelle = PasserelleSourde()
    appel = conversation(base=BaseFactice(muette=True), envoyeur=passerelle,
                         telephone="0612345678")
    appel.tour("je voudrais un rendez-vous jeudi à quinze heures trente")
    phrase = appel.tour("oui c'est parfait").phrase

    assert "n'arrive pas à vérifier" in phrase
    assert passerelle.tentatives == 0, "aucun SMS pour un rendez-vous non relu"


# --- moteur en panne puis base en panne ------------------------------------

def test_deux_pannes_de_nature_differente_ne_se_compensent_pas():
    """Une panne de moteur suivie d'une écriture incertaine : chacune dit la
    vérité, et la seconde n'efface pas la première."""
    appel = conversation(base=BaseFactice(muette=True))
    appel.tour("je voudrais un rendez-vous jeudi à quinze heures trente")
    reponse = appel.tour("oui c'est parfait")
    assert reponse.genre == "incertain"
    genres = [t.get("genre") for t in appel.journal.tours]
    assert "confirmation" not in genres


def test_la_promesse_de_sms_n_a_qu_une_source():
    """Trois exemplaires de la même phrase, c'est trois endroits où la promettre
    par erreur. Et le paramètre qui la posait AVANT l'envoi ne doit plus
    exister : un chemin mort se remprunte."""
    import inspect

    from standard import appel as module_appel
    from standard import ecriture, sms

    assert hasattr(sms, "PROMESSE_DE_CONFIRMATION")
    for module in (ecriture, module_appel):
        source = inspect.getsource(module)
        assert "Vous recevrez un SMS" not in source, module.__name__
    assert "promet_sms" not in inspect.getsource(ecriture)
