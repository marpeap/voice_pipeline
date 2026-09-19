"""La durée de conservation, appliquée — pas seulement annoncée.

« Une durée écrite dans un document et jamais appliquée est une durée fausse »,
dit `journal.purger`. Personne ne l'appelait : en production, les transcriptions
restaient indéfiniment. La CNIL recommande six mois au maximum pour les appels
et leurs transcriptions ; le produit tient 90 jours, à condition de purger.
"""

from datetime import date, timedelta

from standard.depot import Depot
from standard.entretien import Entretien
from standard.journal import JournalDAppels
from standard.regles import CONSERVATION_JOURS


def journal_avec_un_vieil_appel(tmp_path, age_jours):
    depot = Depot(str(tmp_path / "essai.sqlite3"))
    journal = JournalDAppels(depot)
    journal.enregistrer("salon-1", {
        "uuid": f"vieux-{age_jours}",
        "debut": (date.today() - timedelta(days=age_jours)).isoformat() + "T10:00:00+00:00",
        "duree_s": 30, "issue": "rendez-vous", "tours": [
            {"genre": "question", "phrase": "Quel jour ?", "transcription": "jeudi"}],
    })
    return depot, journal


def test_un_passage_d_entretien_efface_ce_qui_a_depasse_la_duree(tmp_path):
    depot, journal = journal_avec_un_vieil_appel(tmp_path, CONSERVATION_JOURS + 5)
    assert journal.lister("salon-1")
    efface = Entretien(journal).passer()
    assert efface == 1
    assert journal.lister("salon-1") == []


def test_ce_qui_est_dans_la_duree_reste(tmp_path):
    depot, journal = journal_avec_un_vieil_appel(tmp_path, CONSERVATION_JOURS - 5)
    assert Entretien(journal).passer() == 0
    assert journal.lister("salon-1")


def test_l_entretien_tourne_tout_seul_et_s_arrete_proprement(tmp_path):
    depot, journal = journal_avec_un_vieil_appel(tmp_path, CONSERVATION_JOURS + 5)
    entretien = Entretien(journal, intervalle_s=0.05)
    entretien.demarrer()
    try:
        for _ in range(100):
            if entretien.passages >= 1 and not journal.lister("salon-1"):
                break
            import time
            time.sleep(0.02)
    finally:
        entretien.arreter()
    assert journal.lister("salon-1") == []
    assert not entretien.vivant


def test_une_panne_de_purge_n_arrete_pas_le_service(tmp_path):
    """Le ménage qui tombe ne doit pas emporter le standard téléphonique."""
    class JournalQuiCasse:
        def purger(self, *a, **k):
            raise RuntimeError("base verrouillée")

    entretien = Entretien(JournalQuiCasse())
    assert entretien.passer() == 0
    assert entretien.pannes == 1


def test_le_serveur_demarre_et_arrete_le_menage(tmp_path):
    """Un cron posé à la main sur un VPS recréé est la façon habituelle dont une
    durée de conservation devient fausse : le ménage tourne avec le service."""
    import os

    from standard.demarrage import construire_serveur

    serveur = construire_serveur({
        "STANDARD_TENANT": "salon-1",
        "STANDARD_PACK": os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "packs", "coiffure.json"),
        "STANDARD_REPONSES": '{"A1": "Salon Elegance"}',
        "STANDARD_PORT": "0",
        "STANDARD_BASE": str(tmp_path / "essai.sqlite3"),
        "STANDARD_STT": "muet", "STANDARD_TTS": "muet",
    })
    serveur.demarrer()
    try:
        assert serveur.entretien.vivant
    finally:
        serveur.arreter()
    assert not serveur.entretien.vivant
