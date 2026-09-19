"""La langue : servir à moitié est pire que passer la main.

L'AI Act demande que l'annonce soit faite « dans la langue de la conversation ».
Le produit ne parle que français : un appelant qui s'adresse à lui en anglais
doit donc être **transféré**, pas servi approximativement. C'est l'écart relevé
par la confrontation du 19/09, et voici la parade.
"""

import pytest

from standard.langue import FRANCAIS, detecter_langue, phrase_de_passage


@pytest.mark.parametrize("dit", [
    "bonjour je voudrais un rendez-vous jeudi",
    "est-ce que vous êtes ouverts samedi matin",
    "mon numéro c'est le zéro six douze trente-quatre",
    "oui",
])
def test_le_francais_est_reconnu(dit):
    assert detecter_langue(dit) == FRANCAIS


@pytest.mark.parametrize("dit, langue", [
    ("hello i would like to book an appointment", "en"),
    ("good morning do you have anything on thursday", "en"),
    ("hola quisiera una cita para el jueves", "es"),
])
def test_une_autre_langue_est_reconnue(dit, langue):
    assert detecter_langue(dit) == langue


def test_un_enonce_trop_court_ne_declenche_rien():
    """Sur trois mots, une detection de langue se trompe plus qu'elle n'aide —
    et transferer un appelant francais parce qu'il a dit « allo » serait pire
    que le defaut qu'on repare."""
    assert detecter_langue("allo") == FRANCAIS


def test_une_transcription_abimee_reste_du_francais():
    """Le STT rend parfois du charabia : ce n'est pas une langue etrangere."""
    assert detecter_langue("PLUTÔT DE M'A ENFIN D'APRÈS MIDI SUS EST POSSIBLE") == FRANCAIS


def test_la_phrase_de_passage_existe_dans_la_langue_detectee():
    phrase = phrase_de_passage("en")
    assert "someone" in phrase.lower() or "transfer" in phrase.lower()
    assert phrase_de_passage("es")


def test_une_langue_inconnue_a_quand_meme_une_phrase():
    phrase = phrase_de_passage("xx")
    assert phrase, "un appelant ne doit jamais rester sans reponse"


def test_le_pipeline_transfere_un_appelant_anglophone():
    import json
    from datetime import date

    from standard.appel import Appel
    from standard.decision import Agenda

    class ModeleQuiRepondQuandMeme:
        appels = 0

        def completer(self, messages, **parametres):
            ModeleQuiRepondQuandMeme.appels += 1
            return json.dumps({"intention": "rdv", "date": "2026-09-17", "heure": "15:30",
                               "confiance": {"intention": 0.9, "date": 0.9, "heure": 0.9}})

    class Base:
        def inserer(self, cle, donnees): return "rdv-1"
        def relire(self, reference): return {"date": "2026-09-17", "heure": "15:30"}

    appel = Appel(client_modele=ModeleQuiRepondQuandMeme(),
                  agenda=Agenda(aujourd_hui=date(2026, 9, 15), creneaux={"15:30"}),
                  base=Base(), memoire="", consignes_communes="c",
                  tenant="t", identifiant="a")
    reponse = appel.tour("hello i would like to book an appointment please")
    assert reponse.genre == "transfert"
    assert ModeleQuiRepondQuandMeme.appels == 0, "le modele a ete appele pour rien"


@pytest.mark.parametrize("dit", [
    "je voudrais un rendez-vous pour le week-end",
    "bonjour c'est pour un brushing et un soin",
    "est-ce que vous avez de la place ce soir",
])
def test_une_phrase_francaise_ordinaire_ne_declenche_jamais_de_transfert(dit):
    """La revue du 19/09 notait que les indices anglais incluaient « i », « do »,
    « the », « you » — sur cinq mots, deux suffisaient. Transférer un client
    français parce qu'il a dit « week-end » serait pire que le défaut réparé."""
    assert detecter_langue(dit) == FRANCAIS
