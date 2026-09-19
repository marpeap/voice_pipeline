"""La boucle de correction : une faute choisie, jamais une phrase ecrite.

Regle qui domine docs/06 : **le commercant ne voit jamais un prompt, sous aucune
forme « avancee ».** Une correction n'est pas du texte — c'est une faute choisie
dans une liste courte, appliquee a un empan de transcription, qui produit une
contrainte typee.

Et le point que personne ne fait sur le marche : **toute correction alimente le
corpus de regression**. C'est ce qui transforme un correctif ponctuel en garantie
durable.
"""

import pytest

from standard.correction import (
    FAUTES,
    Correction,
    RegistreDeCorrections,
    appliquer,
)


def correction(faute="prestation", **champs):
    base = {"faute": faute, "appel": "appel-1", "empan": "je voudrais une permanente",
            "valeur": {"terme": "permanente", "prestation": "permanente_classique"}}
    base.update(champs)
    return Correction(**base)


# --- la liste est courte, fermee, et sans clavier ---------------------------

def test_il_y_a_exactement_sept_fautes():
    """Sept choix : au-dela, c'est un menu ; en dessous, on force l'entree libre."""
    assert len(FAUTES) == 7


def test_une_seule_faute_accepte_du_texte_libre():
    libres = [nom for nom, definition in FAUTES.items() if definition["texte_libre"]]
    assert libres == ["autre"]


def test_une_faute_inconnue_est_refusee():
    with pytest.raises(ValueError, match="faute"):
        correction(faute="ce-que-je-veux")


# --- chaque faute ecrit au bon endroit --------------------------------------

@pytest.mark.parametrize("faute, cible", [
    ("prestation", "pack"),
    ("duree", "frontmatter"),
    ("creneau_inexistant", "serveur"),
    ("promesse_interdite", "corps"),
    ("escalade", "frontmatter"),
    ("mauvaise_information", "frontmatter"),
    ("autre", "a_revoir"),
])
def test_chaque_faute_a_sa_cible(faute, cible):
    assert FAUTES[faute]["cible"] == cible


def test_les_regles_d_agenda_ne_vont_jamais_dans_le_prompt():
    """Une regle redigee en langue naturelle peut ne pas etre retenue par le
    modele sur un tour donne. Ce qui doit etre vrai a 100 % est evalue cote
    serveur — le modele ne propose qu'un creneau deja valide."""
    assert FAUTES["creneau_inexistant"]["cible"] == "serveur"
    assert FAUTES["creneau_inexistant"]["prompt"] is False


# --- le cycle de vie --------------------------------------------------------

def test_une_correction_nait_en_essai():
    registre = RegistreDeCorrections()
    enregistree = registre.ajouter(correction())
    assert enregistree.etat == "en essai"


def test_une_correction_en_essai_s_applique_deja():
    registre = RegistreDeCorrections()
    registre.ajouter(correction())
    assert registre.actives(), "une correction en essai doit s'appliquer"


def test_le_gerant_peut_revoquer():
    registre = RegistreDeCorrections()
    enregistree = registre.ajouter(correction())
    registre.revoquer(enregistree.identifiant)
    assert registre.actives() == []


def test_deux_corrections_contradictoires_ne_sont_jamais_fusionnees():
    """On montre les deux et on demande laquelle vaut — jamais de fusion muette."""
    registre = RegistreDeCorrections()
    registre.ajouter(correction(faute="duree",
                                valeur={"prestation": "coupe", "duree_minutes": 30}))
    seconde = registre.ajouter(correction(faute="duree",
                                          valeur={"prestation": "coupe", "duree_minutes": 45}))
    assert seconde.etat == "en conflit"
    assert len(registre.conflits()) == 1


def test_un_conflit_se_tranche_et_l_autre_est_suspendue():
    registre = RegistreDeCorrections()
    premiere = registre.ajouter(correction(faute="duree",
                                           valeur={"prestation": "coupe", "duree_minutes": 30}))
    seconde = registre.ajouter(correction(faute="duree",
                                          valeur={"prestation": "coupe", "duree_minutes": 45}))
    registre.trancher(seconde.identifiant)
    assert registre.par_identifiant(premiere.identifiant).etat == "suspendue"
    assert registre.par_identifiant(seconde.identifiant).etat == "en essai"


def test_une_note_libre_ne_s_applique_jamais_seule():
    """« Autre » est mis en file pour arbitrage : une dictee ne devient pas une
    regle sans que quelqu'un l'ait lue."""
    registre = RegistreDeCorrections()
    enregistree = registre.ajouter(correction(faute="autre",
                                              valeur={"note": "il parle trop vite"}))
    assert enregistree.etat == "a arbitrer"
    assert registre.actives() == []


# --- l'application ----------------------------------------------------------

def test_une_duree_corrigee_atterrit_dans_le_frontmatter():
    reponses, corps, regles = appliquer([correction(
        faute="duree", valeur={"prestation": "coupe", "duree_minutes": 45})], {}, "")
    assert reponses["durees"]["coupe"] == 45


def test_un_interdit_atterrit_dans_le_corps_et_dans_les_regles_serveur():
    """« Il n'aurait pas du promettre ca » : le corps le dit au modele, et le
    serveur l'empeche — parce qu'une consigne ecrite n'est pas une garantie."""
    reponses, corps, regles = appliquer([correction(
        faute="promesse_interdite", valeur={"interdit": "promettre un délai de livraison"})],
        {}, "# Particularités\n")
    assert "délai de livraison" in corps
    assert any("délai de livraison" in r["interdit"] for r in regles)


def test_le_corps_existant_n_est_jamais_reecrit():
    corps_origine = "# Particularités\n\nDéjà écrit par le salon.\n"
    _, corps, _ = appliquer([correction(faute="promesse_interdite",
                                        valeur={"interdit": "X"})], {}, corps_origine)
    assert corps.startswith(corps_origine)


# --- le corpus de regression ------------------------------------------------

def test_toute_correction_produit_un_scenario_rejouable():
    """Personne ne le fait sur le marche, et c'est pourtant ce qui transforme un
    correctif ponctuel en garantie durable."""
    registre = RegistreDeCorrections()
    registre.ajouter(correction())
    scenarios = registre.scenarios_de_regression()
    assert len(scenarios) == 1
    assert scenarios[0]["repetitions"] == 5, "pass^5, comme le reste de la porte"
    assert scenarios[0]["enonce"] == "je voudrais une permanente"


def test_une_correction_revoquee_sort_du_corpus():
    registre = RegistreDeCorrections()
    enregistree = registre.ajouter(correction())
    registre.revoquer(enregistree.identifiant)
    assert registre.scenarios_de_regression() == []


# --- la persistance : un gérant interrompu ne perd rien ----------------------

def test_les_corrections_survivent_au_redemarrage(tmp_path):
    """Seconde revue (19/09) : le registre était une liste en mémoire, alors que
    sa docstring promettait « écriture à chaque appui ». Un redémarrage effaçait
    tout ce que le gérant avait posé."""
    from standard.depot import Depot

    chemin = str(tmp_path / "corrections.sqlite3")
    registre = RegistreDeCorrections(depot=Depot(chemin), tenant="salon-1")
    registre.ajouter(correction(faute="duree",
                                valeur={"prestation": "coupe", "duree_minutes": 45}))

    repris = RegistreDeCorrections(depot=Depot(chemin), tenant="salon-1")
    assert len(repris.actives()) == 1
    assert repris.actives()[0].valeur["duree_minutes"] == 45


def test_un_salon_ne_relit_pas_les_corrections_d_un_autre(tmp_path):
    from standard.depot import Depot

    chemin = str(tmp_path / "corrections.sqlite3")
    RegistreDeCorrections(depot=Depot(chemin), tenant="salon-1").ajouter(correction())
    assert RegistreDeCorrections(depot=Depot(chemin), tenant="salon-2").actives() == []


def test_une_revocation_est_persistee(tmp_path):
    from standard.depot import Depot

    chemin = str(tmp_path / "corrections.sqlite3")
    registre = RegistreDeCorrections(depot=Depot(chemin), tenant="salon-1")
    posee = registre.ajouter(correction())
    registre.revoquer(posee.identifiant)
    assert RegistreDeCorrections(depot=Depot(chemin), tenant="salon-1").actives() == []


# --- ce que la console envoie doit pouvoir être appliqué ---------------------

def test_une_correction_incomplete_ne_fait_pas_tomber_l_application():
    """La console n'envoyait qu'une note libre : `appliquer` levait `KeyError`
    sur `valeur["prestation"]`. Une correction incomplète se met de côté, elle
    ne casse rien."""
    incomplete = Correction(faute="duree", appel="a", empan="x", valeur={"note": "trop long"})
    reponses, corps, regles = appliquer([incomplete], {}, "")
    assert reponses == {} and regles == []
