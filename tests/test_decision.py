"""La machine a etats : « le modele propose, la machine dispose ».

Seuils et cas : docs/15-RIGUEUR-EXECUTION.md, mesures 14 a 19, et bancs/porte.json.
Aucun cas n'est invente — chacun vient d'un tour reellement joue.
"""

from datetime import date

import pytest

from standard.decision import Agenda, Etat, decider

MARDI = date(2026, 9, 15)  # aujourd'hui, dans tous les tests


def agenda():
    """Agenda de reference : ouvert mardi a samedi, horizon de 14 jours."""
    return Agenda(aujourd_hui=MARDI, horizon_jours=14,
                  jours_fermes=(6, 0),  # dimanche et lundi
                  creneaux={"09:00", "09:45", "10:30", "11:15",
                            "14:00", "14:45", "15:30", "16:15", "17:00"})


def proposition(**champs):
    base = {"intention": "rdv", "date": None, "heure": None, "prestation": None,
            "confiance": {"intention": 1.0, "date": 1.0, "heure": 1.0}, "manque": []}
    base.update(champs)
    return base


# --- ce que la machine a le droit de dire -----------------------------------

INTERDITS = ("c'est noté", "c'est enregistré", "est annulé", "j'ai enregistré", "c'est fait")


def test_aucune_confirmation_sans_ecriture_relue():
    """Mesure 14 : deux confirmations orphelines en douze tours. La machine ne
    peut pas prononcer ces mots — seule une ecriture relue le peut."""
    etat = Etat()
    for prop in [proposition(date="2026-09-17", heure="15:30"),
                 proposition(intention="annulation"),
                 proposition(intention="inconnu", confiance={"intention": 0.2})]:
        sortie = decider(prop, etat, agenda())
        assert not any(mot in sortie.phrase.lower() for mot in INTERDITS), sortie.phrase


def test_creneau_libre_donne_une_proposition_a_confirmer():
    sortie = decider(proposition(date="2026-09-17", heure="15:30"), Etat(), agenda())
    assert sortie.genre == "proposition"
    assert "17 septembre" in sortie.phrase and "jeudi" in sortie.phrase.lower()


# --- l'absence n'est pas une information (mesure 15) ------------------------

def test_hors_horizon_n_est_pas_une_fermeture():
    """Piege paye le 15/09 : « le premier du mois prochain » tombait hors de
    l'horizon et l'agent repondait « nous sommes fermes ce jour-la ». Faux, et
    invérifiable par le client."""
    sortie = decider(proposition(date="2026-12-24", heure="10:30"), Etat(), agenda())
    assert sortie.genre == "hors horizon"
    assert "fermé" not in sortie.phrase.lower()


def test_jour_ferme_est_dit_comme_tel():
    sortie = decider(proposition(date="2026-09-21", heure="10:30"), Etat(), agenda())  # un lundi
    assert sortie.genre == "refus"
    assert "fermé" in sortie.phrase.lower()


def test_creneau_occupe_propose_ce_qui_reste():
    sortie = decider(proposition(date="2026-09-17", heure="18:15"), Etat(), agenda())
    assert sortie.genre == "refus"
    assert "09:00" in sortie.phrase or "9 h" in sortie.phrase


# --- entites manquantes ou douteuses ----------------------------------------

def test_entite_douteuse_devient_une_question():
    sortie = decider(proposition(date="2026-09-17", heure="15:30",
                                 confiance={"intention": 1.0, "date": 0.3, "heure": 1.0}),
                     Etat(), agenda())
    assert sortie.genre == "question"


def test_intention_inconnue_fait_repeter():
    sortie = decider(proposition(intention="inconnu"), Etat(), agenda())
    assert sortie.genre == "question"


# --- les cinq seuils (mesure 18) --------------------------------------------

def test_demande_d_humain_transfere_immediatement():
    sortie = decider(proposition(intention="humain"), Etat(), agenda())
    assert sortie.genre == "transfert"


def test_deux_refus_de_suite_oublient_l_entite():
    etat = Etat()
    a = agenda()
    decider(proposition(date="2026-09-17", heure="18:15"), etat, a)
    sortie = decider(proposition(date="2026-09-18", heure="18:15"), etat, a)
    assert sortie.genre == "question"
    assert "heure" not in etat.connu or etat.connu.get("heure") is None
    assert "09:00" in sortie.phrase or "9 h" in sortie.phrase


def test_repetition_change_de_strategie_puis_transfere():
    """Mesure 18 : se repeter ne veut pas dire abandonner. La reformulation a
    transforme un transfert en rendez-vous pris."""
    etat = Etat()
    a = agenda()
    premiere = decider(proposition(intention="inconnu"), etat, a)
    deuxieme = decider(proposition(intention="inconnu"), etat, a)
    troisieme = decider(proposition(intention="inconnu"), etat, a)
    assert premiere.genre == "question"
    assert deuxieme.genre == "reformulation"
    assert troisieme.genre == "transfert"


def test_deux_tours_sans_valeur_neuve_transferent():
    """Mesure 18 : un compteur d'anti-boucle compte des VALEURS NEUVES, pas des
    tours ni des changements. Repeter la meme demande n'est pas un progres."""
    etat = Etat()
    a = agenda()
    for _ in range(3):
        sortie = decider(proposition(date="2026-09-17", heure="18:15"), etat, a)
    assert sortie.genre == "transfert"


def test_une_valeur_neuve_remet_le_compteur_a_zero():
    etat = Etat()
    a = agenda()
    decider(proposition(date="2026-09-17", heure="18:15"), etat, a)
    sortie = decider(proposition(date="2026-09-17", heure="15:30"), etat, a)
    assert sortie.genre == "proposition"


# --- regles d'enonciation mesurees sur l'audio (mesure 19) ------------------

def test_la_date_porte_le_jour_de_la_semaine():
    """E1 : le quantieme est le mot le plus fragile de tout ce que l'agent dit.
    C'est la redondance du jour de la semaine qui permet de detecter l'erreur."""
    sortie = decider(proposition(date="2026-09-17", heure="15:30"), Etat(), agenda())
    assert "jeudi" in sortie.phrase.lower()
    assert "septembre" in sortie.phrase.lower()


def test_jamais_deux_horaires_trop_proches_dans_une_phrase():
    """E2 : « neuf heures, neuf heures quarante-cinq » a perdu sa premiere option
    dans le canal. Les horaires proposes sont espaces d'au moins une heure."""
    sortie = decider(proposition(date="2026-09-17", heure="18:15"), Etat(), agenda())
    heures = [h for h in agenda().creneaux if h in sortie.phrase]
    minutes = sorted(int(h[:2]) * 60 + int(h[3:]) for h in heures)
    assert all(b - a >= 60 for a, b in zip(minutes, minutes[1:])), sortie.phrase


def test_jamais_la_meme_phrase_deux_fois_de_suite():
    etat = Etat()
    a = agenda()
    vues = set()
    for _ in range(4):
        sortie = decider(proposition(intention="inconnu"), etat, a)
        assert sortie.phrase not in vues, "la machine se repete mot pour mot"
        vues.add(sortie.phrase)
        if sortie.genre == "transfert":
            break
