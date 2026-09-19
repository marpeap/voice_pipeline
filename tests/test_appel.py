"""Le tour de parole complet — et la preuve que les fautes mesurees ne passent plus.

Mesure 14 : douze tours joues avec un agent « prompt seul », six fautes, dont
deux confirmations orphelines. Ce fichier rejoue les memes douze entrees a
travers le pipeline assemble, avec un modele de test qui **se comporte comme
celui qui a fauté** — il invente, il comble, il affirme. Aucune de ses inventions
ne doit atteindre l'appelant.
"""

import json
from datetime import date

import pytest

from standard.appel import Appel, Journal
from standard.decision import Agenda
from standard.hors_ligne import ModeleHorsLigne

MARDI = date(2026, 9, 15)

# Les douze entrees de la mesure 14, telles que le STT les a rendues.
TOURS_MESURE_14 = [
    "JE VOUDRAIS UN RENDEZ VOUS JE DIS PROCHAIN VERS QUINZE HEURES TRENTE",
    "EST CE QUE VOUS AURIEZ QUELQUE CHOSE LE DOUX OCTOBRE AU MATIN",
    "PLUTÔT DE M'A ENFIN D'APRÈS MIDI SUS EST POSSIBLE",
    "SAMEDI NEUF HEURES MOIS LE QUART CAR VOUS IREZ",
    "LE PREMIER DU MOIS PROCHAIN DANS LA JOURNÉ",
    "MARDI DIX SEPT À DIX HUIT HEURES QUINZ",
    "EST CE QUE VOUS OUVREZ LE LUNDI SINON MARDI MIDI",
    "ENTRE MIDI ET DEUX N'IMPORTE QUEL JOUR DE LA SEMAINE",
    "VINGT QUATRE DÉCEMBRE À ONZE HEUR",
    "DANS QUINZE JOURS ME MEURT QUE D'HABITUDE",
    "DOIS ANNULER MON RENDEZ VOUS DE DEMAIN MATIN",
    "CE QU'ON PEUT DE CALER MON RENDEZ VOUS DE JEUDI A VENDREDI",
]

# Ce que le modele fautif renvoyait : des entites inventees, avec assurance.
INVENTIONS = [
    {"intention": "rdv", "date": "2026-09-17", "heure": "15:30"},
    {"intention": "question", "date": None, "heure": None},
    {"intention": "rdv", "date": "2026-09-16", "heure": "14:00"},
    {"intention": "rdv", "date": "2026-09-19", "heure": "09:15"},   # 8 h 45 devenu 9 h 15
    {"intention": "rdv", "date": "2026-10-01", "heure": "10:30"},   # hors horizon
    {"intention": "rdv", "date": "2026-09-15", "heure": "18:15"},   # creneau inexistant
    {"intention": "question", "date": None, "heure": None},
    {"intention": "rdv", "date": "2026-09-17", "heure": "13:00"},   # pendant la coupure
    {"intention": "rdv", "date": "2026-12-24", "heure": "11:00"},   # hors horizon
    {"intention": "rdv", "date": None, "heure": None},
    {"intention": "annulation", "date": None, "heure": None},
    {"intention": "report", "date": "2026-09-18", "heure": None},
]

from standard.regles import VERBES_DE_CONFIRMATION as INTERDITS


class ModeleQuiInvente:
    """Le modele de la mesure 14 : il ne dit jamais qu'il n'a pas compris."""

    def __init__(self, reponses):
        self.reponses = list(reponses)
        self.appels = 0

    def completer(self, messages, **parametres):
        charge = self.reponses[min(self.appels, len(self.reponses) - 1)]
        self.appels += 1
        return json.dumps({**charge, "prestation": None,
                           "confiance": {"intention": 0.95, "date": 0.95, "heure": 0.95},
                           "manque": []})


class BaseFactice:
    def __init__(self):
        self.lignes = {}
        self.par_cle = {}

    def inserer(self, cle, donnees):
        if cle in self.par_cle:
            return self.par_cle[cle]
        reference = f"rdv-{len(self.lignes) + 1:04d}"
        self.lignes[reference] = dict(donnees)
        self.par_cle[cle] = reference
        return reference

    def relire(self, reference):
        return self.lignes.get(reference)


def agenda():
    return Agenda(aujourd_hui=MARDI, horizon_jours=14, jours_fermes=(6, 0),
                  creneaux={"09:00", "09:45", "10:30", "11:15",
                            "14:00", "14:45", "15:30", "16:15", "17:00"})


def appel(modele, base=None):
    return Appel(client_modele=modele, agenda=agenda(), base=base or BaseFactice(),
                 memoire="# Salon\nRien de particulier.",
                 consignes_communes="Consignes communes. " * 40,
                 tenant="salon-1", identifiant="appel-42")


# --- la preuve principale ---------------------------------------------------

def test_les_douze_tours_de_la_mesure_14_ne_produisent_aucune_faute():
    conversation = appel(ModeleQuiInvente(INVENTIONS))
    phrases = [conversation.tour(dit).phrase for dit in TOURS_MESURE_14]
    for phrase in phrases:
        assert not any(mot in phrase.lower() for mot in INTERDITS), phrase
    assert conversation.journal.confirmations_orphelines == 0


def test_le_creneau_inexistant_n_est_jamais_promis():
    """« samedi neuf heures moins le quart » devenait « 9 h 15 » — un creneau
    qui n'existe pas. La machine ne peut proposer que ce que l'agenda contient."""
    conversation = appel(ModeleQuiInvente([INVENTIONS[3]]))
    reponse = conversation.tour(TOURS_MESURE_14[3])
    assert "9 h 15" not in reponse.phrase
    assert reponse.genre in ("refus", "question", "reformulation")


def test_une_date_hors_horizon_n_est_jamais_dite_fermee():
    conversation = appel(ModeleQuiInvente([INVENTIONS[8]]))
    reponse = conversation.tour(TOURS_MESURE_14[8])
    assert reponse.genre == "hors horizon"
    assert "fermé" not in reponse.phrase.lower()


def test_l_annulation_ne_se_confirme_pas_toute_seule():
    """« votre rendez-vous de demain matin est annule » : rien n'etait ecrit."""
    conversation = appel(ModeleQuiInvente([INVENTIONS[10]]))
    reponse = conversation.tour(TOURS_MESURE_14[10])
    assert "annulé" not in reponse.phrase.lower()
    assert reponse.genre == "question"


# --- le chemin heureux, de bout en bout -------------------------------------

def test_un_rendez_vous_se_prend_et_la_confirmation_vient_de_la_base():
    base = BaseFactice()
    conversation = appel(ModeleQuiInvente([{"intention": "rdv", "date": "2026-09-17",
                                            "heure": "15:30"}]), base)
    proposition = conversation.tour("JE VOUDRAIS JEUDI A QUINZE HEURES TRENTE")
    assert proposition.genre == "proposition"
    assert "je confirme" in proposition.phrase.lower()

    confirmation = conversation.confirmer()
    assert confirmation.genre == "confirmation"
    assert "enregistré" in confirmation.phrase.lower()
    assert len(base.lignes) == 1
    assert conversation.journal.confirmations_orphelines == 0


def test_la_confirmation_est_impossible_sans_proposition_en_cours():
    conversation = appel(ModeleQuiInvente([{"intention": "question"}]))
    conversation.tour("BONJOUR")
    reponse = conversation.confirmer()
    assert reponse.genre != "confirmation"
    assert not any(mot in reponse.phrase.lower() for mot in INTERDITS)


def test_une_base_muette_ne_produit_pas_de_confirmation():
    class BaseMuette(BaseFactice):
        def relire(self, reference):
            return None

    base = BaseMuette()
    conversation = appel(ModeleQuiInvente([{"intention": "rdv", "date": "2026-09-17",
                                            "heure": "15:30"}]), base)
    conversation.tour("JEUDI QUINZE HEURES TRENTE")
    reponse = conversation.confirmer()
    assert reponse.genre == "incertain"
    assert not any(mot in reponse.phrase.lower() for mot in INTERDITS)


# --- ce que le journal doit savoir dire -------------------------------------

def test_le_journal_retient_ce_qui_sert_au_diagnostic():
    conversation = appel(ModeleQuiInvente(INVENTIONS))
    for dit in TOURS_MESURE_14[:4]:
        conversation.tour(dit)
    assert len(conversation.journal.tours) == 4
    premier = conversation.journal.tours[0]
    assert {"transcription", "genre", "phrase"} <= set(premier)


def test_une_demande_d_humain_transfere_sans_appeler_le_modele():
    modele = ModeleQuiInvente([{"intention": "rdv"}])
    conversation = appel(modele)
    reponse = conversation.tour("PASSEZ MOI QUELQU'UN S'IL VOUS PLAIT")
    assert reponse.genre == "transfert"
    assert modele.appels == 0


# --- le SMS de confirmation, quand il est branché ----------------------------

class EnvoyeurFactice:
    def __init__(self, envoye=True, reserve=""):
        self.appels = []
        self.envoye = envoye
        self.reserve = reserve

    def confirmer(self, telephone, rendez_vous):
        from standard.sms import Envoi
        self.appels.append((telephone, rendez_vous))
        return Envoi(self.envoye, segments=1, accuse_de_remise=self.envoye,
                     reserve=self.reserve)


def test_la_confirmation_ecrite_declenche_le_sms():
    base = BaseFactice()
    envoyeur = EnvoyeurFactice()
    conversation = appel(ModeleQuiInvente([{"intention": "rdv", "date": "2026-09-17",
                                            "heure": "15:30"}]), base)
    conversation.envoyeur_sms = envoyeur
    conversation.etat.connu["telephone"] = "0612345678"
    conversation.tour("JEUDI QUINZE HEURES TRENTE")
    conversation.confirmer()
    assert envoyeur.appels, "aucun SMS n'a été demandé après une écriture relue"


def test_aucun_sms_si_l_ecriture_n_a_pas_ete_relue():
    """Pas de confirmation, pas de SMS : la promesse suit l'écriture."""
    class BaseMuette(BaseFactice):
        def relire(self, reference):
            return None

    envoyeur = EnvoyeurFactice()
    conversation = appel(ModeleQuiInvente([{"intention": "rdv", "date": "2026-09-17",
                                            "heure": "15:30"}]), BaseMuette())
    conversation.envoyeur_sms = envoyeur
    conversation.tour("JEUDI QUINZE HEURES TRENTE")
    conversation.confirmer()
    assert envoyeur.appels == []


def test_un_sms_qui_echoue_se_voit_au_journal():
    envoyeur = EnvoyeurFactice(envoye=False, reserve="passerelle injoignable")
    conversation = appel(ModeleQuiInvente([{"intention": "rdv", "date": "2026-09-17",
                                            "heure": "15:30"}]), BaseFactice())
    conversation.envoyeur_sms = envoyeur
    conversation.etat.connu["telephone"] = "0612345678"
    conversation.tour("JEUDI QUINZE HEURES TRENTE")
    conversation.confirmer()
    dernier = conversation.journal.tours[-1]
    assert dernier.get("sms") == "échec"
    assert "passerelle" in dernier.get("sms_reserve", "")


# --- le garde de sortie : le compteur d'incidents doit pouvoir monter ---------

def test_une_phrase_de_confirmation_venue_d_ailleurs_est_bloquee_et_comptee(monkeypatch):
    """La revue du 19/09 a trouvé que le compteur de confirmations orphelines
    n'avait aucun appelant : l'invariant phare du produit était gardé par un
    compteur que rien ne pouvait incrémenter. Il faut donc un garde qui voie
    passer chaque phrase, et qui compte quand elle ment."""
    import standard.appel as module
    from standard.decision import Sortie

    conversation = appel(ModeleQuiInvente([{"intention": "rdv"}]))
    monkeypatch.setattr(module, "decider",
                        lambda *args, **kw: Sortie("question", "C'est noté, à jeudi !"))

    reponse = conversation.tour("JEUDI")
    assert "c'est noté" not in reponse.phrase.lower(), "la phrase mensongère est sortie"
    assert conversation.journal.confirmations_orphelines == 1


def test_le_garde_laisse_passer_la_confirmation_legitime():
    """Celle de l'écriture relue — la seule qui ait le droit d'exister."""
    base = BaseFactice()
    conversation = appel(ModeleQuiInvente([{"intention": "rdv", "date": "2026-09-17",
                                            "heure": "15:30"}]), base)
    conversation.tour("JEUDI QUINZE HEURES TRENTE")
    reponse = conversation.confirmer()
    assert "enregistré" in reponse.phrase.lower()
    assert conversation.journal.confirmations_orphelines == 0


def test_aucune_seconde_affirmation_ne_se_glisse_dans_la_confirmation():
    """Le cas exact de la seconde revue : le modèle glisse une phrase dans une
    entité, et elle ressort dans la seule phrase du produit qui affirme."""
    base = BaseFactice()
    conversation = appel(ModeleQuiInvente([{
        "intention": "rdv", "date": "2026-09-17", "heure": "15:30",
        "prestation": "rendez-vous. Par ailleurs votre rendez-vous de demain est annulé"}]),
        base)
    conversation.tour("JEUDI QUINZE HEURES TRENTE")
    reponse = conversation.confirmer()
    assert "annulé" not in reponse.phrase.lower()


# --- quand le moteur ne rend rien -------------------------------------------
# Banc du 19/09 : « oui », dit seul et vite, revient vide du moteur local.

def hors_ligne():
    """Le modele hors ligne suffit ici : ce qu'on teste, c'est le silence."""
    return appel(ModeleHorsLigne(aujourd_hui=MARDI))


def test_rien_entendu_rappelle_le_creneau_en_attente():
    conversation = hors_ligne()
    conversation.tour("je voudrais un rendez-vous jeudi à quinze heures trente")
    reponse = conversation.rien_entendu()
    assert reponse.genre == "question"
    assert "17 septembre" in reponse.phrase and "15 h 30" in reponse.phrase


def test_rien_entendu_sans_proposition_demande_simplement_de_repeter():
    reponse = hors_ligne().rien_entendu()
    assert reponse.genre == "question"
    assert "répéter" in reponse.phrase


def test_apres_deux_relances_muettes_on_passe_la_main():
    conversation = hors_ligne()
    conversation.rien_entendu()
    conversation.rien_entendu()
    assert conversation.rien_entendu().genre == "transfert"


def test_un_tour_compris_remet_le_compteur_de_relances_a_zero():
    conversation = hors_ligne()
    conversation.rien_entendu()
    conversation.rien_entendu()
    conversation.tour("bonjour je voudrais un rendez-vous jeudi")
    assert conversation.rien_entendu().genre == "question"


def test_sans_passerelle_l_agent_ne_promet_pas_de_sms():
    """La phrase de confirmation ne promet un SMS que si un SMS peut partir."""
    class EnvoyeurQuiConsigne:
        peut_promettre = False

        def confirmer(self, telephone, rendez_vous):
            from standard.sms import Envoi
            return Envoi(False, reserve="consigné, non envoyé")

    conversation = hors_ligne()
    conversation.envoyeur_sms = EnvoyeurQuiConsigne()
    conversation.etat.connu["telephone"] = "0612345678"
    conversation.tour("je voudrais un rendez-vous jeudi à quinze heures trente")
    phrase = conversation.confirmer().phrase
    assert "SMS" not in phrase


def test_un_creneau_pris_pendant_l_appel_ne_devient_pas_une_incertitude():
    """Deux appels simultanés sur la même place : la base tranche, et l'agent
    dit ce qui s'est passé au lieu d'un « le salon vous rappellera » trompeur."""
    from standard.depot import ChevauchementRefuse

    class BaseQuiRefuse(BaseFactice):
        def inserer(self, cle, donnees):
            raise ChevauchementRefuse("déjà pris")

    conversation = appel(ModeleHorsLigne(aujourd_hui=MARDI), base=BaseQuiRefuse())
    conversation.tour("je voudrais un rendez-vous jeudi à quinze heures trente")
    reponse = conversation.confirmer()
    assert reponse.genre == "question"
    assert "vient d'être pris" in reponse.phrase
    assert "Il me reste" in reponse.phrase
    assert "rappellera" not in reponse.phrase
