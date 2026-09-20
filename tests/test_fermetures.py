"""Les fermetures — l'agent prenait des rendez-vous le 25 décembre.

Le pack ne parle que d'horaires **hebdomadaires** : lundi fermé, samedi
9 h-18 h. Rien ne disait « du 1er au 15 août », ni « le 25 décembre ». Un agent
qui réserve un créneau un jour férié ou pendant les congés fait déplacer un
client devant un rideau baissé — et c'est la faute que le commerçant ne
pardonne pas, parce qu'elle lui coûte un client, pas une minute.
"""

from datetime import date

import pytest

from standard.fermetures import (
    jours_feries,
    lire_les_fermetures,
    est_ferme,
)


# --- les jours fériés français ---------------------------------------------

def test_les_jours_fixes_sont_la():
    feries = jours_feries(2026)
    for jour in ("2026-01-01", "2026-05-01", "2026-05-08", "2026-07-14",
                 "2026-08-15", "2026-11-01", "2026-11-11", "2026-12-25"):
        assert date.fromisoformat(jour) in feries, jour


def test_les_jours_mobiles_suivent_paques():
    """Pâques 2026 tombe le 5 avril : lundi de Pâques le 6, Ascension le 14 mai,
    lundi de Pentecôte le 25 mai."""
    feries = jours_feries(2026)
    assert date(2026, 4, 6) in feries      # lundi de Pâques
    assert date(2026, 5, 14) in feries     # Ascension
    assert date(2026, 5, 25) in feries     # lundi de Pentecôte


def test_paques_change_d_annee_en_annee():
    assert date(2027, 3, 29) in jours_feries(2027)   # lundi de Pâques 2027
    assert date(2027, 3, 29) not in jours_feries(2026)


def test_un_jour_ordinaire_n_est_pas_ferie():
    assert date(2026, 9, 17) not in jours_feries(2026)


# --- ce que le commerçant écrit --------------------------------------------

@pytest.mark.parametrize("dit, attendus", [
    ("2026-12-25", ["2026-12-25"]),
    ("25/12/2026", ["2026-12-25"]),
    ("du 1er au 3 août 2026", ["2026-08-01", "2026-08-02", "2026-08-03"]),
    ("2026-08-01 au 2026-08-03", ["2026-08-01", "2026-08-02", "2026-08-03"]),
])
def test_une_fermeture_se_lit_comme_le_commercant_l_ecrit(dit, attendus):
    lues = lire_les_fermetures(dit)
    assert [j.isoformat() for j in lues] == attendus


def test_ce_qui_ne_se_lit_pas_est_ignore_sans_tout_perdre():
    """Une ligne illisible ne doit pas effacer les autres : le commerçant en
    écrit plusieurs, et il ne relit pas."""
    lues = lire_les_fermetures("2026-12-25\nn'importe quoi\n2026-12-26")
    assert [j.isoformat() for j in lues] == ["2026-12-25", "2026-12-26"]


def test_une_plage_a_l_envers_ne_bloque_pas_l_annee():
    assert lire_les_fermetures("du 2026-12-26 au 2026-12-25") == []


# --- la décision ------------------------------------------------------------

def test_un_jour_ferie_est_ferme_si_le_salon_l_a_dit():
    assert est_ferme(date(2026, 12, 25), fermetures=(), feries=True)
    assert not est_ferme(date(2026, 12, 25), fermetures=(), feries=False)


def test_une_fermeture_exceptionnelle_ferme_le_jour():
    assert est_ferme(date(2026, 8, 3), fermetures=(date(2026, 8, 3),), feries=False)


def test_un_jour_ordinaire_reste_ouvert():
    assert not est_ferme(date(2026, 9, 17), fermetures=(), feries=True)


# --- de bout en bout --------------------------------------------------------

def service_avec(fermetures="", feries="oui", tmp_path=None):
    import json

    from standard.depot import Depot
    from standard.hors_ligne import ModeleHorsLigne
    from standard.service import Configuration, Service

    pack = json.load(open("packs/coiffure.json"))
    depot = Depot(":memory:")
    depot.pour("salon-1").enregistrer_reponses({"A1": "Salon",
                                                "A5": feries,
                                                "A6": fermetures})
    service = Service(Configuration(tenant="salon-1", pack=pack,
                                    aujourd_hui=date(2026, 12, 21),
                                    horizon_jours=30,
                                    creneaux=("09:00", "15:30")),
                      client_modele=ModeleHorsLigne(aujourd_hui=date(2026, 12, 21)),
                      base=depot.pour("salon-1"), reponses_du_depot=depot)
    service.demarrer()
    return service


def test_l_agenda_ferme_le_jour_de_noel():
    agenda = service_avec()._agenda()
    assert agenda.statut("2026-12-25") == "ferme"
    assert agenda.statut("2026-12-24") == "ouvert"


def test_un_salon_qui_ouvre_les_jours_feries_reste_ouvert():
    agenda = service_avec(feries="non")._agenda()
    assert agenda.statut("2026-12-25") == "ouvert"


def test_les_conges_ecrits_par_le_commercant_ferment_l_agenda():
    agenda = service_avec(fermetures="du 2026-12-26 au 2026-12-31")._agenda()
    assert agenda.statut("2026-12-28") == "ferme"
    assert agenda.statut("2027-01-02") == "ouvert"


def test_l_agent_dit_quand_le_salon_rouvre():
    """Sans cela, l'appelant essaie des jours au hasard — et chaque essai est
    un tour de conversation payé par le salon."""
    from standard.decision import Etat, decider

    service = service_avec(fermetures="du 2026-12-26 au 2027-01-04")
    agenda = service._agenda()
    sortie = decider({"intention": "rdv", "date": "2026-12-28", "heure": None,
                      "confiance": {"intention": 0.9, "date": 0.9}, "manque": []},
                     Etat(), agenda)
    assert "5 janvier" in sortie.phrase, sortie.phrase


def test_la_reouverture_saute_aussi_les_jours_de_planning():
    """Le salon est fermé le dimanche : annoncer une réouverture un dimanche
    serait un rendez-vous manqué de plus. Le 2 janvier 2027 est un samedi, le
    3 un dimanche — la réouverture après une fermeture du 2 est donc le 4."""
    service = service_avec(fermetures="2027-01-02")
    agenda = service._agenda()
    assert agenda.reouverture(date(2027, 1, 2)).isoformat() == "2027-01-04"


def test_sans_reouverture_dans_l_horizon_on_ne_raconte_rien():
    """Au-delà de l'horizon, l'agent ne sait pas : il ne doit pas inventer une
    date de réouverture."""
    service = service_avec(fermetures="du 2026-12-22 au 2027-06-30")
    assert service._agenda().reouverture(date(2026, 12, 25)) is None
