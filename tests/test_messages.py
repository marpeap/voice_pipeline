"""Prendre un message — ce que le pack promet depuis le début.

La question D4 des packs offre « transférer » ou « prendre un message ». Le
code ne lisait jamais la réponse : tout finissait en transfert, y compris chez
un salon qui avait explicitement choisi le message. Un transfert vers un
téléphone que personne ne décroche, c'est l'appel perdu que le produit existe
pour rattraper.
"""

from datetime import date

import pytest

from standard.appel import Appel
from standard.decision import Agenda
from standard.depot import Depot
from standard.hors_ligne import ModeleHorsLigne

MARDI = date(2026, 9, 15)


def depot(tmp_path):
    return Depot(str(tmp_path / "essai.sqlite3"))


def conversation(base, escalade="message"):
    appel = Appel(client_modele=ModeleHorsLigne(aujourd_hui=MARDI),
                  agenda=Agenda(aujourd_hui=MARDI, creneaux={"15:30"}, jours_fermes=(6, 0)),
                  base=base, memoire="", consignes_communes="c",
                  tenant="salon-1", identifiant="appel-1")
    appel.fiche = {"escalade": {"humain": escalade}, "reservation": {"nom": "non"}}
    return appel


# --- le dépôt ---------------------------------------------------------------

def test_un_message_s_ecrit_et_se_relit(tmp_path):
    base = depot(tmp_path)
    reference = base.pour("salon-1").enregistrer_message(
        {"texte": "rappelez-moi pour une couleur", "nom": "Dupont",
         "telephone": "0612345678"})
    messages = base.messages("salon-1")
    assert len(messages) == 1
    assert messages[0]["texte"] == "rappelez-moi pour une couleur"
    assert messages[0]["reference"] == reference


def test_les_messages_d_un_salon_ne_fuient_pas_chez_un_autre(tmp_path):
    base = depot(tmp_path)
    base.pour("salon-1").enregistrer_message({"texte": "pour le salon 1"})
    assert base.messages("salon-2") == []


def test_lister_les_messages_sans_locataire_refuse(tmp_path):
    with pytest.raises(ValueError):
        depot(tmp_path).messages(None)


# --- l'appel ----------------------------------------------------------------

def test_quand_le_salon_a_choisi_le_message_l_agent_ne_transfere_pas(tmp_path):
    appel = conversation(depot(tmp_path).pour("salon-1"))
    reponse = appel.tour("je voudrais parler à quelqu'un du salon")
    assert reponse.genre == "message"
    assert "message" in reponse.phrase.lower()


def test_le_message_dicte_est_ecrit_puis_confirme(tmp_path):
    base = depot(tmp_path)
    appel = conversation(base.pour("salon-1"))
    appel.tour("je voudrais parler à quelqu'un du salon")
    appel.tour("je voudrais savoir si vous faites des colorations végétales")
    reponse = appel.tour("zéro six douze trente-quatre cinquante-six soixante-dix-huit")
    assert reponse.genre == "message"
    messages = base.messages("salon-1")
    assert len(messages) == 1
    assert "colorations" in messages[0]["texte"]
    assert messages[0]["telephone"] == "0612345678"


def test_sans_numero_le_message_est_quand_meme_garde(tmp_path):
    """Un message sans rappel possible vaut mieux qu'un message perdu."""
    base = depot(tmp_path)
    appel = conversation(base.pour("salon-1"))
    appel.tour("je voudrais parler à quelqu'un du salon")
    appel.tour("dites-lui que je passerai jeudi")
    appel.tour("je ne préfère pas donner mon numéro")
    appel.tour("non merci")
    assert len(base.messages("salon-1")) == 1


def test_le_salon_qui_a_choisi_le_transfert_transfere_toujours(tmp_path):
    appel = conversation(depot(tmp_path).pour("salon-1"), escalade="transfert")
    assert appel.tour("je voudrais parler à quelqu'un du salon").genre == "transfert"


def test_un_numero_de_rappel_mal_dit_bascule_au_clavier(tmp_path):
    """Un message sans numéro de rappel ne sert presque à rien : on passe au
    clavier dès le premier échec, au lieu d'attendre le second (mesure 7)."""
    base = depot(tmp_path)
    appel = conversation(base.pour("salon-1"))
    temoin = []
    appel.basculer_clavier = lambda: temoin.append(True)
    appel.tour("je voudrais parler à quelqu'un du salon")
    appel.tour("dites-lui que je passerai jeudi")
    reponse = appel.tour("euh je ne sais plus mon numéro")
    assert temoin, "le clavier n'a pas été armé"
    assert "clavier" in reponse.phrase.lower()
    assert base.messages("salon-1") == [], "le message a été déposé trop tôt"

    final = appel.numero_au_clavier("0612345678")
    assert final.genre == "message"
    messages = base.messages("salon-1")
    assert messages[0]["telephone"] == "0612345678"
