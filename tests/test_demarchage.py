"""Filtrer le démarchage — un KPI promis dans `docs/06`, jamais implémenté.

« Spams filtrés et non facturés » figure parmi les indicateurs que la console
doit montrer. Rien ne les filtrait, et rien ne les comptait : un salon payait
donc ses appels de prospection au même prix que ses clients.

Depuis le 11 août 2026, la prospection téléphonique vers un consommateur exige
un consentement préalable (loi du 11/08/2026, décret n° 2026-662). Le salon, lui,
est un professionnel : ces appels lui arrivent encore. L'agent doit les
reconnaître, refuser en une phrase, et ne rien écrire.

**On ne devine pas.** Un doute profite à l'appelant : mieux vaut servir un
démarcheur que raccrocher au nez d'un client.
"""

import pytest

from standard.demarchage import est_un_demarchage


@pytest.mark.parametrize("dit", [
    "bonjour je vous appelle pour vous proposer notre solution de référencement Google",
    "bonjour c'est au sujet de votre visibilité sur internet",
    "je vous appelle concernant les aides à la rénovation énergétique de votre local",
    "nous proposons une formation éligible au CPF pour vos salariés",
    "je suis partenaire de votre fournisseur d'électricité, je vous appelle pour une offre",
])
def test_un_appel_de_prospection_se_reconnait(dit):
    assert est_un_demarchage(dit) is True


@pytest.mark.parametrize("dit", [
    "bonjour je voudrais un rendez-vous jeudi à quinze heures trente",
    "bonjour je vous appelle pour prendre rendez-vous",
    "je voudrais proposer un créneau à ma fille",
    "bonjour c'est pour une coupe et un brushing",
    "je vous appelle pour savoir si vous êtes ouverts samedi",
    "",
])
def test_un_vrai_client_n_est_jamais_pris_pour_un_demarcheur(dit):
    assert est_un_demarchage(dit) is False


def test_une_demande_de_rendez_vous_l_emporte_toujours():
    """Un démarcheur qui parle de rendez-vous est servi comme un client : le
    faux positif coûte un client, le faux négatif coûte trente secondes."""
    assert est_un_demarchage(
        "je vous appelle pour vous proposer un rendez-vous commercial") is False


# --- ce que l'agent en fait -------------------------------------------------

def conversation(tmp_path):
    from datetime import date

    from standard.appel import Appel
    from standard.decision import Agenda
    from standard.depot import Depot
    from standard.hors_ligne import ModeleHorsLigne

    mardi = date(2026, 9, 15)
    base = Depot(str(tmp_path / "essai.sqlite3"))
    appel = Appel(client_modele=ModeleHorsLigne(aujourd_hui=mardi),
                  agenda=Agenda(aujourd_hui=mardi, creneaux={"15:30"}, jours_fermes=(6, 0)),
                  base=base.pour("salon-1"), memoire="", consignes_communes="c",
                  tenant="salon-1", identifiant="appel-1")
    return appel, base


def test_l_agent_refuse_en_une_phrase_et_met_fin(tmp_path):
    appel, base = conversation(tmp_path)
    reponse = appel.tour("bonjour je vous appelle pour vous proposer notre solution "
                         "de référencement Google")
    assert reponse.genre == "demarchage"
    assert appel.fin_demandee is True
    assert base.lister("salon-1") == []


def test_le_demarchage_est_compte_pour_ne_pas_etre_facture(tmp_path):
    appel, _ = conversation(tmp_path)
    appel.tour("bonjour nous vous proposons une offre commerciale")
    assert appel.journal.demarchages == 1


def test_passe_les_premiers_tours_l_agent_ne_raccroche_plus(tmp_path):
    """Au-delà des premiers mots, une phrase commerciale peut venir d'un client
    qui explique son métier : on ne coupe pas une conversation engagée."""
    appel, _ = conversation(tmp_path)
    appel.tour("bonjour je voudrais un rendez-vous jeudi")
    appel.tour("à quinze heures trente")
    reponse = appel.tour("au fait je vous propose notre solution de référencement")
    assert reponse.genre != "demarchage"
    assert appel.fin_demandee is False


def test_a_travers_le_serveur_la_ligne_se_libere_apres_le_refus(tmp_path):
    """Un démarcheur ne doit pas garder la ligne ouverte : la phrase se dit en
    entier, puis on raccroche."""
    import os
    import socket
    import time

    from standard.audiosocket import TYPE_AUDIO_8K, encoder
    from standard.demarrage import construire_serveur

    racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    serveur = construire_serveur({
        "STANDARD_TENANT": "salon-1",
        "STANDARD_PACK": os.path.join(racine, "packs", "coiffure.json"),
        "STANDARD_REPONSES": '{"A1": "Salon Elegance"}',
        "STANDARD_CRENEAUX": "15:30",
        "STANDARD_PORT": "0", "STANDARD_PORT_SANTE": "0",
        "STANDARD_BASE": str(tmp_path / "essai.sqlite3"),
        "STANDARD_STT": "muet", "STANDARD_TTS": "muet",
    })
    serveur.transcrire = lambda audio, frequence: (
        "bonjour je vous appelle pour vous proposer notre solution de référencement")
    serveur.demarrer()
    try:
        prise = socket.create_connection(("127.0.0.1", serveur.port), timeout=3)
        prise.settimeout(3)
        import struct

        parole = b"".join(struct.pack("<h", 8000 if i % 2 else -8000)
                          for i in range(160))
        for _ in range(5):
            prise.sendall(encoder(TYPE_AUDIO_8K, parole))
        for _ in range(50):
            prise.sendall(encoder(TYPE_AUDIO_8K, bytes(320)))
        for _ in range(60):
            if serveur.appels_en_cours == 0:
                break
            time.sleep(0.05)
        assert serveur.appels_en_cours == 0, "la ligne est restée ouverte"
        assert serveur.demarchages_filtres == 1
        prise.close()
    finally:
        serveur.arreter()
