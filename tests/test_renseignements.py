"""Les appels qui ne veulent aucun rendez-vous — et qui sont la moitié du flux.

`docs/18` classe les appels d'un salon en quatre : prise de rendez-vous, report
ou annulation, **question (prix, horaires, conseil)**, et autre. Le produit
répondait à une seule de ces questions : les horaires. Pour tout le reste —
l'adresse, un tarif, une réclamation — il disait « Que puis-je faire pour
vous ? », deux fois, puis passait la main. Trois tours pour dire « je ne sais
pas », c'est ce qu'un standard doit faire en un.
"""

import json

import pytest

from standard.fiche import repondre

FICHE = {
    "salon": {"nom": "Salon Elegance", "adresse": "12 rue des Lilas, 72000 Le Mans"},
    "horaires": {"ouverture": {"mardi": ["09:00-19:00"]}},
    "prix": {"annonce": "oui", "tarifs": {"coupe": 28, "coloration": 65}},
}


# --- l'adresse --------------------------------------------------------------

@pytest.mark.parametrize("dit", [
    "vous êtes où exactement",
    "quelle est votre adresse",
    "comment on vient chez vous",
    "vous êtes situés où",
])
def test_l_adresse_se_dit_quand_elle_est_dans_la_fiche(dit):
    reponse = repondre(dit, FICHE)
    assert reponse and "rue des Lilas" in reponse


def test_sans_adresse_l_agent_ne_l_invente_pas():
    reponse = repondre("quelle est votre adresse", {"salon": {"nom": "Salon"}})
    assert reponse and "rue" not in reponse.lower()
    assert "quelqu'un du salon" in reponse


# --- les prix ---------------------------------------------------------------

def test_un_tarif_saisi_se_dit():
    reponse = repondre("c'est combien une coupe", FICHE)
    assert "28" in reponse


def test_un_tarif_non_saisi_ne_s_invente_pas():
    reponse = repondre("c'est combien un balayage", FICHE)
    assert "€" not in reponse or "28" not in reponse
    assert "hasard" in reponse or "quelqu'un du salon" in reponse


def test_quand_le_salon_refuse_d_annoncer_les_prix_l_agent_se_tait():
    """La question C2 du pack décide : « il oriente vers le salon »."""
    fiche = {**FICHE, "prix": {"annonce": "non", "tarifs": {"coupe": 28}}}
    reponse = repondre("c'est combien une coupe", fiche)
    assert "28" not in reponse


def test_sans_prestation_nommee_l_agent_renvoie_au_salon():
    reponse = repondre("vous êtes chers", FICHE)
    assert reponse is None or "quelqu'un du salon" in reponse


# --- une réclamation --------------------------------------------------------

@pytest.mark.parametrize("dit", [
    "je ne suis pas content du tout de ma couleur",
    "je veux faire une réclamation",
    "c'est inadmissible ce qui s'est passé hier",
])
def test_une_reclamation_ne_tourne_pas_en_rond(dit):
    """Faire répéter un client mécontent est la pire réponse possible : il faut
    un humain, tout de suite, et sans négocier (même règle que « passez-moi
    quelqu'un », mesure 17)."""
    from standard.comprehension import demande_un_humain

    assert demande_un_humain(dit) is True


# --- la fiche est la dernière chance avant « je n'ai pas compris » ----------

def test_une_question_mal_classee_trouve_quand_meme_sa_reponse(tmp_path):
    """Banc du 20/09 : « vous êtes situés où exactement » a été classé
    « inconnu » par le modèle hors ligne, et l'agent a répondu « je n'ai pas
    bien saisi » alors que l'adresse était dans sa fiche."""
    import os

    from standard.demarrage import construire_serveur

    racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    serveur = construire_serveur({
        "STANDARD_TENANT": "salon-1",
        "STANDARD_PACK": os.path.join(racine, "packs", "coiffure.json"),
        "STANDARD_REPONSES": json.dumps({"A1": "Salon", "A7": "12 rue des Lilas"}),
        "STANDARD_CRENEAUX": "15:30",
        "STANDARD_PORT": "0", "STANDARD_PORT_SANTE": "0",
        "STANDARD_BASE": str(tmp_path / "essai.sqlite3"),
        "STANDARD_STT": "muet", "STANDARD_TTS": "muet",
    })
    appel = serveur.service.nouvel_appel("appel-1")
    assert "rue des Lilas" in appel.tour("vous êtes situés où exactement").phrase


# --- dire au revoir ---------------------------------------------------------

@pytest.mark.parametrize("dit", [
    "merci au revoir",
    "c'est tout, merci beaucoup",
    "parfait merci bonne journée",
])
def test_un_au_revoir_est_entendu_comme_tel(dit):
    from standard.assentiment import est_un_au_revoir

    assert est_un_au_revoir(dit) is True


@pytest.mark.parametrize("dit", [
    "merci, et je voudrais aussi un rendez-vous jeudi",
    "bonjour",
    "oui c'est parfait",
])
def test_ce_qui_n_est_pas_un_au_revoir_ne_l_est_pas(dit):
    from standard.assentiment import est_un_au_revoir

    assert est_un_au_revoir(dit) is False


def test_l_agent_repond_a_un_au_revoir_et_rend_la_ligne(tmp_path):
    """« Merci au revoir » recevait « Je vais faire autrement : dites-moi le
    jour qui vous arrange ». L'appelant a dit qu'il avait fini."""
    import os

    from standard.demarrage import construire_serveur

    racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    serveur = construire_serveur({
        "STANDARD_TENANT": "salon-1",
        "STANDARD_PACK": os.path.join(racine, "packs", "coiffure.json"),
        "STANDARD_REPONSES": '{"A1": "Salon"}',
        "STANDARD_CRENEAUX": "15:30",
        "STANDARD_PORT": "0", "STANDARD_PORT_SANTE": "0",
        "STANDARD_BASE": str(tmp_path / "essai.sqlite3"),
        "STANDARD_STT": "muet", "STANDARD_TTS": "muet",
    })
    appel = serveur.service.nouvel_appel("appel-1")
    reponse = appel.tour("merci au revoir")
    assert reponse.genre == "fin"
    assert "journée" in reponse.phrase.lower()
    assert appel.fin_demandee is True
