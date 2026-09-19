"""Le journal d'appel : ce qui reste quand l'appel est fini.

Sans lui, « l'agent comprend mal » n'est pas diagnosticable, la console n'a rien à
montrer, et l'annonce légale n'est pas prouvable. Avec lui, il faut se demander
l'inverse : **qu'est-ce qu'on n'a pas le droit de garder ?**
"""

from datetime import date, timedelta

import pytest

from standard.depot import Depot
from standard.journal import JournalDAppels

APPEL = {
    "uuid": "7f3a1c5e-0000-4000-8000-000000000001",
    "debut": "2026-09-19T10:00:00+00:00",
    "duree_s": 74.2,
    "issue": "rendez-vous",
    "rsb_db": 18.4,
    "bruite": False,
    "interruptions": 1,
    "preuve_annonce": {"conforme": True, "formulation": "assistant automatique",
                       "horodatage": "2026-09-19T10:00:01+00:00"},
    "tours": [
        {"genre": "proposition", "phrase": "Je peux vous réserver…",
         "transcription": "jeudi quinze heures trente"},
        {"genre": "confirmation", "phrase": "C'est enregistré…", "reference": "rdv-0001"},
    ],
}


@pytest.fixture
def journal():
    return JournalDAppels(Depot(":memory:"))


def test_un_appel_se_relit_apres_coup(journal):
    journal.enregistrer("salon-1", APPEL)
    [appel] = journal.lister("salon-1")
    assert appel["uuid"] == APPEL["uuid"]
    assert appel["issue"] == "rendez-vous"
    assert len(appel["tours"]) == 2


def test_un_salon_ne_voit_que_ses_appels(journal):
    journal.enregistrer("salon-1", APPEL)
    assert journal.lister("salon-2") == []


def test_lister_sans_locataire_est_refuse(journal):
    journal.enregistrer("salon-1", APPEL)
    with pytest.raises(ValueError, match="locataire"):
        journal.lister(None)


def test_l_audio_n_est_jamais_stocke(journal):
    """La conformité ne se vérifie pas à la relecture d'une politique : ici, le
    journal refuse un champ audio plutôt que de l'écrire discrètement."""
    with pytest.raises(ValueError, match="audio"):
        journal.enregistrer("salon-1", APPEL | {"audio": b"\x00\x01"})


def test_la_preuve_de_l_annonce_est_conservee(journal):
    journal.enregistrer("salon-1", APPEL)
    [appel] = journal.lister("salon-1")
    assert appel["preuve_annonce"]["conforme"] is True
    assert appel["preuve_annonce"]["horodatage"]


def test_un_appel_sans_annonce_conforme_ressort_dans_les_incidents(journal):
    journal.enregistrer("salon-1", APPEL | {
        "uuid": "sans-annonce", "preuve_annonce": {"conforme": False}})
    incidents = journal.incidents("salon-1")
    assert any(i["motif"] == "annonce absente" for i in incidents)


def test_une_confirmation_orpheline_est_un_incident(journal):
    journal.enregistrer("salon-1", APPEL | {
        "uuid": "orpheline", "confirmations_orphelines": 1})
    incidents = journal.incidents("salon-1")
    assert any(i["motif"] == "confirmation orpheline" for i in incidents)
    assert incidents[0]["gravite"] == "incident"


# --- conservation -----------------------------------------------------------

def test_les_appels_trop_vieux_sont_effaces(journal):
    vieux = (date.today() - timedelta(days=120)).isoformat() + "T10:00:00+00:00"
    journal.enregistrer("salon-1", APPEL | {"uuid": "vieux", "debut": vieux})
    journal.enregistrer("salon-1", APPEL)
    efface = journal.purger(conservation_jours=90)
    assert efface == 1
    assert [a["uuid"] for a in journal.lister("salon-1")] == [APPEL["uuid"]]


def test_la_purge_ne_touche_pas_les_autres_locataires(journal):
    vieux = (date.today() - timedelta(days=200)).isoformat() + "T10:00:00+00:00"
    journal.enregistrer("salon-2", APPEL | {"uuid": "vieux-2", "debut": vieux})
    journal.purger(conservation_jours=90, tenant="salon-1")
    assert journal.lister("salon-2") != []


# --- ce que la console affiche ----------------------------------------------

def test_le_resume_donne_les_chiffres_de_la_semaine(journal):
    journal.enregistrer("salon-1", APPEL)
    journal.enregistrer("salon-1", APPEL | {"uuid": "b", "issue": "transfert",
                                            "bruite": True})
    resume = journal.resume("salon-1")
    assert resume["appels"] == 2
    assert resume["rendez_vous"] == 1
    assert resume["transferts"] == 1
    assert resume["part_bruitee_pct"] == 50.0
    assert resume["confirmations_orphelines"] == 0
