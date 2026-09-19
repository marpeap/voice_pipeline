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
    appel.tour("zéro six douze trente-quatre cinquante-six soixante-dix-huit")
    reponse = appel.tour("oui c'est bien ça")      # la relecture, mesure 21
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


# --- corriger le nom après la confirmation ----------------------------------
# Banc du 19/09 : le moteur rend « Le Fora » pour « Lefevre ». L'agent redit le
# nom, l'appelant corrige — et la correction doit atteindre la base.

def conversation_avec_rdv(base):
    from standard.appel import Appel

    appel = Appel(client_modele=ModeleHorsLigne(aujourd_hui=MARDI),
                  agenda=Agenda(aujourd_hui=MARDI, creneaux={"15:30"}, jours_fermes=(6, 0)),
                  base=base, memoire="", consignes_communes="c",
                  tenant="salon-1", identifiant="appel-1")
    appel.tour("je voudrais un rendez-vous jeudi à quinze heures trente")
    appel.tour("oui c'est parfait")
    appel.tour("au nom de Le Fora")
    return appel


def test_le_nom_se_corrige_apres_la_confirmation(tmp_path):
    base = Depot(str(tmp_path / "essai.sqlite3"))
    appel = conversation_avec_rdv(base.pour("salon-1"))
    assert base.lister("salon-1")[0]["nom"] == "Le Fora"

    reponse = appel.tour("non c'est au nom de Lefevre")
    assert "Lefevre" in reponse.phrase
    assert base.lister("salon-1")[0]["nom"] == "Lefevre"
    assert len(base.lister("salon-1")) == 1, "la correction a créé un second rendez-vous"


def test_un_refus_sans_nom_fait_redemander_le_nom(tmp_path):
    base = Depot(str(tmp_path / "essai.sqlite3"))
    appel = conversation_avec_rdv(base.pour("salon-1"))
    reponse = appel.tour("non ce n'est pas ça")
    assert "nom" in reponse.phrase.lower()
    appel.tour("Lefevre")
    assert base.lister("salon-1")[0]["nom"] == "Lefevre"


def test_un_au_revoir_ne_corrige_rien(tmp_path):
    base = Depot(str(tmp_path / "essai.sqlite3"))
    appel = conversation_avec_rdv(base.pour("salon-1"))
    appel.tour("merci au revoir")
    assert base.lister("salon-1")[0]["nom"] == "Le Fora"


def test_un_nom_seul_juste_apres_la_confirmation_corrige(tmp_path):
    """Le moteur abîme souvent la phrase de correction (« JE VAIS FAIRE
    AUTREMENT » pour « non c'est au nom de Martin ») mais rend le nom seul
    correctement au tour suivant. Juste après la confirmation, un nom seul n'a
    pas d'autre sens que celui-là."""
    base = Depot(str(tmp_path / "essai.sqlite3"))
    appel = conversation_avec_rdv(base.pour("salon-1"))
    reponse = appel.tour("Martin")
    assert reponse.genre == "correction"
    assert base.lister("salon-1")[0]["nom"] == "Martin"


def test_passe_la_fenetre_un_mot_isole_ne_reecrit_plus_la_fiche(tmp_path):
    """La fenêtre vaut deux tours (`regles.TOURS_FENETRE_CORRECTION_NOM`) :
    au-delà, « Martin » peut vouloir dire autre chose."""
    base = Depot(str(tmp_path / "essai.sqlite3"))
    appel = conversation_avec_rdv(base.pour("salon-1"))
    appel.tour("merci beaucoup")
    appel.tour("c'est très aimable à vous")
    appel.tour("Martin")
    assert base.lister("salon-1")[0]["nom"] == "Le Fora"


def test_la_fenetre_survit_a_un_tour_incompris(tmp_path):
    """La phrase de correction est souvent abîmée par le moteur ; l'appelant
    redit alors le nom seul au tour suivant, et il doit encore être entendu."""
    base = Depot(str(tmp_path / "essai.sqlite3"))
    appel = conversation_avec_rdv(base.pour("salon-1"))
    appel.tour("n'en s'étonnant de Martin")      # ce que le moteur a rendu
    appel.tour("Martin")
    assert base.lister("salon-1")[0]["nom"] == "Martin"


def test_une_nouvelle_demande_ferme_la_fenetre(tmp_path):
    base = Depot(str(tmp_path / "essai.sqlite3"))
    appel = conversation_avec_rdv(base.pour("salon-1"))
    appel.tour("je voudrais aussi un rendez-vous vendredi à quinze heures trente")
    appel.tour("Martin")
    assert base.lister("salon-1")[0]["nom"] == "Le Fora"


def test_le_numero_de_rappel_est_relu_avant_d_etre_gardé(tmp_path):
    """Banc du 20/09 : « 0612345678 » dicté est revenu « 0612345078 », et le
    message est parti avec un numéro faux. La relecture est systématique depuis
    la mesure 21 — elle ne peut pas l'être seulement pour les rendez-vous."""
    base = Depot(str(tmp_path / "essai.sqlite3"))
    appel = conversation(base.pour("salon-1"))
    appel.tour("je voudrais parler à quelqu'un du salon")
    appel.tour("dites-lui que je passerai jeudi")
    reponse = appel.tour("zéro six douze trente-quatre cinquante-six soixante-dix-huit")
    assert "relis" in reponse.phrase.lower()
    assert base.messages("salon-1") == [], "le message est parti sans relecture"

    final = appel.tour("oui c'est ça")
    assert final.genre == "message"
    assert base.messages("salon-1")[0]["telephone"] == "0612345678"


def test_un_numero_mal_relu_se_corrige_avant_le_depot(tmp_path):
    base = Depot(str(tmp_path / "essai.sqlite3"))
    appel = conversation(base.pour("salon-1"))
    temoin = []
    appel.basculer_clavier = lambda: temoin.append(True)
    appel.tour("je voudrais parler à quelqu'un du salon")
    appel.tour("dites-lui que je passerai jeudi")
    appel.tour("zéro six douze trente-quatre cinquante-six soixante-dix-huit")
    reponse = appel.tour("non ce n'est pas ça")
    assert temoin, "après un refus de relecture, le clavier doit s'armer"
    assert "clavier" in reponse.phrase.lower()
    assert base.messages("salon-1") == []


def test_pendant_que_l_appelant_compose_on_ne_depose_pas_le_message(tmp_path):
    """Le clavier armé, ce qu'on entend de l'appelant n'est pas un nouvel échec :
    déposer là jetterait le numéro qu'il est en train de taper."""
    base = Depot(str(tmp_path / "essai.sqlite3"))
    appel = conversation(base.pour("salon-1"))
    appel.basculer_clavier = lambda: None
    appel.tour("je voudrais parler à quelqu'un du salon")
    appel.tour("dites-lui que je passerai jeudi")
    appel.tour("euh je ne sais plus")                 # numéro incompréhensible
    appel.tour("attendez je cherche")                 # il tape
    assert base.messages("salon-1") == []
    appel.numero_au_clavier("0612345678")
    assert base.messages("salon-1")[0]["telephone"] == "0612345678"
