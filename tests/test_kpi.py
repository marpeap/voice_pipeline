"""Les six indicateurs de `docs/06` — promis, affichés en partie.

Le document liste exactement ce que la console doit montrer : confirmation
orpheline (cible 0), **taux d'impasse**, passage à l'humain **par motif**,
**silence perçu p50/p95**, **rendez-vous pris sans intervention**, spams filtrés.
La console en montrait trois. Les trois autres existent dans le journal depuis
que chaque tour porte ses latences et chaque appel son motif d'échec — personne
ne les additionnait.
"""

from standard.console import Console
from standard.depot import Depot
from standard.journal import JournalDAppels


def appel(uuid, issue="rendez-vous", echec=None, mesures=(), tours=()):
    return {"uuid": uuid, "debut": "2026-09-21T10:00:00+00:00", "duree_s": 60.0,
            "issue": issue, "echec": echec, "mesures": list(mesures),
            "tours": list(tours) or [{"genre": "question", "transcription": "jeudi"}]}


def journal(appels):
    depot = Depot(":memory:")
    journal = JournalDAppels(depot)
    for un in appels:
        journal.enregistrer("salon-1", un)
    return journal


def indicateurs(appels):
    return journal(appels).indicateurs("salon-1")


def test_sans_appel_les_indicateurs_ne_mentent_pas():
    vide = indicateurs([])
    assert vide["appels"] == 0
    assert vide["taux_d_impasse_pct"] == 0.0
    assert vide["silence_p50_ms"] is None


def test_le_taux_d_impasse_compte_les_appels_qui_n_ont_rien_donne():
    """Impasse = l'agent n'a ni pris de rendez-vous ni passé la main : le
    client a raccroché avec rien."""
    valeurs = indicateurs([
        appel("a", issue="rendez-vous"),
        appel("b", issue="sans suite", echec="reformulations"),
        appel("c", issue="transfert", echec="demande_humain"),
        appel("d", issue="sans suite", echec="silence"),
    ])
    assert valeurs["taux_d_impasse_pct"] == 50.0


def test_les_passages_a_l_humain_se_comptent_par_motif():
    valeurs = indicateurs([
        appel("a", issue="transfert", echec="demande_humain"),
        appel("b", issue="transfert", echec="demande_humain"),
        appel("c", issue="transfert", echec="reformulations"),
    ])
    assert valeurs["transferts_par_motif"] == {"demande_humain": 2, "reformulations": 1}


def test_le_silence_percu_se_lit_dans_les_mesures():
    """Ce que l'appelant attend vraiment : la fin de sa parole détectée, plus
    le temps que met l'agent à sortir son premier son."""
    valeurs = indicateurs([
        appel("a", mesures=[{"total_ms": 400, "fin_de_parole_ms": 700},
                            {"total_ms": 600, "fin_de_parole_ms": 700}]),
        appel("b", mesures=[{"total_ms": 800, "fin_de_parole_ms": 700}]),
    ])
    assert valeurs["silence_p50_ms"] == 1300     # 600 + 700
    assert valeurs["silence_p95_ms"] == 1500     # 800 + 700


def test_les_rendez_vous_sans_intervention_excluent_les_transferts():
    valeurs = indicateurs([
        appel("a", issue="rendez-vous"),
        appel("b", issue="rendez-vous", echec="demande_humain"),
        appel("c", issue="transfert", echec="demande_humain"),
    ])
    assert valeurs["rdv_sans_intervention"] == 1


def test_la_console_affiche_les_six_indicateurs():
    import json

    depot = Depot(":memory:")
    fil = JournalDAppels(depot)
    fil.enregistrer("salon-1", appel("a", mesures=[{"total_ms": 400,
                                                    "fin_de_parole_ms": 700}]))
    fil.enregistrer("salon-1", appel("b", issue="sans suite", echec="silence"))
    console = Console(journal=fil, tenant="salon-1", depot=depot,
                      pack=json.load(open("packs/coiffure.json")))
    _, _, contenu = console.repondre("GET", "/")
    assert "impasse" in contenu.lower()
    assert "silence" in contenu.lower()
    assert "sans intervention" in contenu.lower()
