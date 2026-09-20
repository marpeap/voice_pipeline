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

from standard.regles import VERBES_DE_CONFIRMATION as INTERDITS


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


# --- quand il ne reste rien -------------------------------------------------
# Trouvé en utilisant la console d'essai le 20/09 : l'agent disait « Le jeudi
# 24 septembre, il me reste . Qu'est-ce qui vous va ? » — une phrase vide, et
# une question sans réponse possible.

def agenda_sans_creneau():
    from standard.decision import Agenda
    return Agenda(aujourd_hui=MARDI, horizon_jours=14, jours_fermes=(6, 0),
                  creneaux=set())


def test_un_jour_sans_creneau_se_dit_au_lieu_d_une_liste_vide():
    from standard.decision import Etat, decider

    sortie = decider({"intention": "rdv", "date": "2026-09-17", "heure": None,
                      "confiance": {"intention": 0.9, "date": 0.9}, "manque": []},
                     Etat(), agenda_sans_creneau())
    assert "il me reste ." not in sortie.phrase
    assert "plus rien" in sortie.phrase or "complet" in sortie.phrase


def test_une_heure_refusee_sans_alternative_ne_promet_pas_une_liste_vide():
    from standard.decision import Etat, decider

    sortie = decider({"intention": "rdv", "date": "2026-09-17", "heure": "15:30",
                      "confiance": {"intention": 0.9, "date": 0.9, "heure": 0.9},
                      "manque": []},
                     Etat(), agenda_sans_creneau())
    assert "Il me reste ." not in sortie.phrase
    assert "plus rien" in sortie.phrase or "complet" in sortie.phrase


# --- « pas libre » et « n'existe pas » ne sont pas la même chose ------------
# Mesure 15 : confondre « absent de l'agenda » et « fermé » fait mentir la
# machine, et c'est invérifiable par le client. La même règle vaut pour l'heure.

def agenda_avec(pris=None):
    from standard.decision import Agenda
    return Agenda(aujourd_hui=MARDI, horizon_jours=14, jours_fermes=(6, 0),
                  creneaux={"09:00", "10:30", "15:30"}, pris=pris or {})


def test_une_heure_hors_grille_ne_se_dit_pas_occupee():
    from standard.decision import Etat, decider

    sortie = decider({"intention": "rdv", "date": "2026-09-17", "heure": "10:00",
                      "confiance": {"intention": 0.9, "date": 0.9, "heure": 0.9},
                      "manque": []}, Etat(), agenda_avec())
    assert "pas libre" not in sortie.phrase, sortie.phrase
    assert "10 h 30" in sortie.phrase


def test_une_heure_de_la_grille_deja_prise_se_dit_occupee():
    from standard.decision import Etat, decider

    sortie = decider({"intention": "rdv", "date": "2026-09-17", "heure": "15:30",
                      "confiance": {"intention": 0.9, "date": 0.9, "heure": 0.9},
                      "manque": []}, Etat(),
                     agenda_avec({"2026-09-17": {"15:30"}}))
    assert "pas libre" in sortie.phrase, sortie.phrase


def test_un_hote_qui_cale_ne_rend_pas_l_agent_muet():
    """Un hôte injoignable doit dégrader, jamais faire taire l'agent.

    La lecture de l'hôte était appelée nue. Une lecture qui expire remontait
    donc en exception jusqu'au serveur, où elle se comptait en
    `pannes_pendant_appel` — et l'appelant n'entendait RIEN. Mesuré le 20/09 :
    `TimeoutError: the read operation timed out`, aucune phrase.

    Ce n'est pas théorique : la machine qui sert l'agenda tiers a un seul vCPU
    et swappe (mesure de la session Crenolo : load 5,68 à 3 h du matin). Une
    requête peut caler plusieurs secondes sans qu'aucune erreur ne soit
    journalisée côté hôte.

    On retombe alors sur la fiche du salon — ce que la machine sait d'elle-même.
    Un créneau proposé qui serait pris chez l'hôte se fera refuser à l'écriture,
    et l'agent proposera autre chose : c'est un désagrément, le silence est une
    panne.
    """
    from datetime import date

    from standard.decision import Agenda

    def hote_qui_cale(jour_iso):
        raise TimeoutError("the read operation timed out")

    agenda = Agenda(aujourd_hui=date(2026, 9, 15), creneaux={"09:00", "15:30"},
                    jours_fermes=(6, 0), libres_du_jour=hote_qui_cale)

    libres = agenda.libres("2026-09-17")
    assert libres == ["09:00", "15:30"], "l'agent doit garder la parole"
    assert agenda.lectures_hote_perdues == 1, "la dégradation doit se compter"


def test_une_lecture_d_hote_reussie_ne_compte_aucune_perte():
    from datetime import date

    from standard.decision import Agenda

    agenda = Agenda(aujourd_hui=date(2026, 9, 15), creneaux={"09:00", "15:30"},
                    jours_fermes=(6, 0), libres_du_jour=lambda jour: ["15:30"])
    assert agenda.libres("2026-09-17") == ["15:30"]
    assert agenda.lectures_hote_perdues == 0


def test_l_hote_n_est_pas_relu_quinze_fois_par_tour_de_parole():
    """Un tour de parole reconstruit tout le calendrier : horizon de 14 jours,
    donc quinze lectures de l'hôte. Mesuré le 20/09 : 14 lectures pour UNE
    phrase. Crenolo limite la lecture publique à 120 requêtes/minute par IP :
    huit tours de parole saturaient le quota, et l'agent aurait pris des 429
    qui n'ont rien à voir avec un refus de réservation.

    Une mémoire très courte suffit : ce qu'un agenda dit d'un jour ne change pas
    en une seconde de conversation, et la fenêtre reste assez brève pour qu'un
    créneau pris ailleurs soit vu au tour suivant.
    """
    from datetime import date

    from standard.decision import Agenda

    appels = []

    def hote(jour_iso):
        appels.append(jour_iso)
        return ["09:00", "15:30"]

    agenda = Agenda(aujourd_hui=date(2026, 9, 15), creneaux={"09:00", "15:30"},
                    jours_fermes=(6, 0), libres_du_jour=hote)

    for _ in range(5):
        agenda.libres("2026-09-17")
    assert len(appels) == 1, f"{len(appels)} lectures là où une suffit"

    agenda.libres("2026-09-18")
    assert len(appels) == 2, "un autre jour est une autre question"


def test_un_tour_de_parole_ne_lit_l_hote_que_pour_les_jours_envisages():
    """Treize lectures pour une phrase saturaient le quota de l'hôte.

    `LECTURE_PUBLIQUE` vaut 120 requêtes/minute par IP chez Crenolo. À treize
    lectures par tour, un échange parlé de 8 à 15 s consomme 52 à 156
    lectures/minute : le produit ne portait qu'un à deux appels simultanés.

    La description du calendrier donnée au modèle n'a pas besoin de l'hôte :
    elle dit quels jours le salon ouvre, ce que la machine sait d'elle-même.
    L'hôte, lui, reste consulté pour le jour réellement envisagé — c'est la
    couche de décision qui le fait, et c'est elle qui décide ce qu'on propose.
    Calcul de la session qui tient marpeap/crenolo, vérifié ici.
    """
    import os

    from standard.demarrage import construire_serveur

    racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    serveur = construire_serveur({
        "STANDARD_TENANT": "salon-1",
        "STANDARD_PACK": os.path.join(racine, "packs", "coiffure.json"),
        "STANDARD_REPONSES": '{"A1": "Salon Elegance"}',
        "STANDARD_CRENEAUX": "09:00,10:30,14:00,15:30",
        "STANDARD_AUJOURDHUI": "2026-09-15",
        "STANDARD_PORT": "0", "STANDARD_PORT_SANTE": "0", "STANDARD_PORT_TOILE": "0",
        "STANDARD_BASE": ":memory:", "STANDARD_STT": "muet", "STANDARD_TTS": "muet",
    })
    suivi = serveur.fabrique_agent()
    lectures = []
    suivi._appel.agenda.libres_du_jour = (
        lambda jour: (lectures.append(jour) or ["09:00", "10:30", "14:00", "15:30"]))

    reponse = suivi.tour("je voudrais un rendez-vous jeudi à quinze heures trente")

    assert reponse.phrase, "l'agent doit répondre"
    assert len(lectures) <= 3, (
        f"{len(lectures)} lectures de l'hôte pour un tour — le quota de l'hôte "
        "ne le supporte pas")
    assert len(set(lectures)) <= 2, "un tour n'envisage pas dix jours"


def test_le_calendrier_donne_au_modele_ne_touche_jamais_l_hote():
    """La description des jours ouverts est une connaissance locale."""
    from datetime import date

    from standard.decision import Agenda

    lectures = []
    agenda = Agenda(aujourd_hui=date(2026, 9, 15), creneaux={"09:00", "15:30"},
                    jours_fermes=(6, 0),
                    libres_du_jour=lambda jour: (lectures.append(jour) or ["09:00"]))

    assert agenda.libres("2026-09-17", sans_l_hote=True) == ["09:00", "15:30"]
    assert lectures == [], "le calendrier local a interrogé l'hôte"
    assert agenda.libres("2026-09-17") == ["09:00"], "l'hôte reste la vérité"
    assert lectures == ["2026-09-17"]
