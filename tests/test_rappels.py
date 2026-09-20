"""Le rappel de la veille — la seule chose qui fasse baisser les no-shows.

Recherche du 20/09 : un SMS envoyé 24 h avant réduit les absences de 30 à 35 %,
et les études du secteur parlent d'une division par cinq des absences non
annoncées. C'est le premier bénéfice mesurable qu'un salon attend d'un
logiciel de rendez-vous — et le produit n'en avait aucun.

Trois gardes, parce qu'un rappel mal fait coûte plus qu'il ne rapporte :
  - **un seul rappel par rendez-vous**, jamais deux ;
  - **une fenêtre horaire** : la charte AF2M place les SMS entre 8 h et 21 h 30,
    et le métier recommande la fin de matinée de la veille ;
  - **rien de promotionnel** : un seul mot de pub ferait basculer ce message
    transactionnel en prospection commerciale (750 € par message, CPCE).
"""

from datetime import date, datetime

import pytest

from standard.depot import Depot
from standard.rappels import Rappels


class EnvoyeurFactice:
    def __init__(self, marche=True):
        self.envois = []
        self.marche = marche
        self.peut_promettre = True

    def confirmer(self, telephone, rendez_vous):
        from standard.sms import Envoi
        self.envois.append((telephone, dict(rendez_vous)))
        return Envoi(self.marche, segments=1, accuse_de_remise=self.marche)


def base(tmp_path, **extra):
    depot = Depot(str(tmp_path / "essai.sqlite3"))
    depot.pour("salon-1").inserer("cle-1", {"date": "2026-09-17", "heure": "15:30",
                                            "nom": "Dupont",
                                            "telephone": "0612345678", **extra})
    return depot


def rappels(depot, envoyeur, quand="2026-09-16T11:00:00"):
    return Rappels(depot=depot, tenant="salon-1", envoyeur=envoyeur,
                   horloge=lambda: datetime.fromisoformat(quand))


def test_le_rendez_vous_de_demain_recoit_son_rappel(tmp_path):
    depot, envoyeur = base(tmp_path), EnvoyeurFactice()
    assert rappels(depot, envoyeur).passer() == 1
    assert envoyeur.envois[0][0] == "0612345678"


def test_un_rendez_vous_n_est_rappele_qu_une_fois(tmp_path):
    depot, envoyeur = base(tmp_path), EnvoyeurFactice()
    rappels(depot, envoyeur).passer()
    assert rappels(depot, envoyeur).passer() == 0
    assert len(envoyeur.envois) == 1


def test_hors_de_la_fenetre_on_n_envoie_rien(tmp_path):
    depot, envoyeur = base(tmp_path), EnvoyeurFactice()
    assert rappels(depot, envoyeur, "2026-09-16T06:30:00").passer() == 0
    assert rappels(depot, envoyeur, "2026-09-16T23:00:00").passer() == 0


def test_un_rendez_vous_plus_lointain_attend_son_tour(tmp_path):
    depot, envoyeur = base(tmp_path), EnvoyeurFactice()
    assert rappels(depot, envoyeur, "2026-09-14T11:00:00").passer() == 0


def test_sans_numero_on_ne_rappelle_personne(tmp_path):
    depot = Depot(str(tmp_path / "essai.sqlite3"))
    depot.pour("salon-1").inserer("cle-1", {"date": "2026-09-17", "heure": "15:30"})
    envoyeur = EnvoyeurFactice()
    assert rappels(depot, envoyeur).passer() == 0


def test_un_envoi_rate_sera_retente_au_passage_suivant(tmp_path):
    """Marquer avant d'envoyer perdrait le rappel sur un incident réseau."""
    depot = base(tmp_path)
    casse = EnvoyeurFactice(marche=False)
    assert rappels(depot, casse).passer() == 0
    bon = EnvoyeurFactice()
    assert rappels(depot, bon).passer() == 1


def test_le_message_ne_porte_rien_de_promotionnel(tmp_path):
    from standard.sms import composer_rappel, verifier_message

    message = composer_rappel({"date": "2026-09-17", "heure": "15:30",
                               "salon": "Salon Elegance"})
    verdict = verifier_message(message, exiger_conformite=True)
    assert verdict.nature == "transactionnel", verdict.motifs
    assert verdict.stop_requis is False, "un message transactionnel n'impose pas de STOP"
    assert verdict.segments == 1, "un rappel doit tenir en un seul SMS facturé"
    assert "17 septembre" in message
    for mot in ("promo", "offre", "réduction", "-10%"):
        assert mot not in message.lower()


def test_sans_envoyeur_le_passage_ne_tombe_pas(tmp_path):
    assert Rappels(depot=base(tmp_path), tenant="salon-1", envoyeur=None).passer() == 0


def test_les_rappels_tournent_avec_le_service(tmp_path):
    """Un cron posé à la main sur un VPS recréé est la façon habituelle dont
    ces choses-là cessent de tourner : les rappels vivent dans le fil qui
    tourne déjà."""
    import os

    from standard.demarrage import construire_serveur

    racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    serveur = construire_serveur({
        "STANDARD_TENANT": "salon-1",
        "STANDARD_PACK": os.path.join(racine, "packs", "coiffure.json"),
        "STANDARD_REPONSES": '{"A1": "Salon Elegance"}',
        "STANDARD_PORT": "0", "STANDARD_PORT_SANTE": "0",
        "STANDARD_BASE": str(tmp_path / "essai.sqlite3"),
        "STANDARD_STT": "muet", "STANDARD_TTS": "muet",
    })
    assert serveur.entretien.rappels is not None
    assert serveur.entretien.rappels.nom_du_salon == "Salon Elegance"
    # Sans passerelle SMS déclarée, il n'y a pas d'envoyeur : le passage ne
    # tombe pas, il ne fait rien.
    assert serveur.entretien.passer() == 0
