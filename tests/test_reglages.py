"""Le questionnaire du commerçant — la moitié du produit qui n'existait pas.

`docs/05` : le commerçant répond à des questions, le système écrit le fichier,
et **il ne voit jamais un prompt**. Les questions étaient là (les packs), la
composition aussi (`locataire.composer_memoire`) — mais rien ne permettait à un
commerçant de répondre : les réponses arrivaient par une variable
d'environnement en JSON. Autant dire que le produit ne se vendait pas seul.

Conception : règles Barthez. Action primaire = répondre à la prochaine question
sans réponse. Pic = « votre agent peut décrocher » quand les questions critiques
sont remplies. Fin = le retour au fil des appels, jamais un cul-de-sac.
"""

import json

import pytest

from standard.console import Console
from standard.depot import Depot
from standard.journal import JournalDAppels

PACK = json.load(open("packs/coiffure.json"))


def console(reponses=None):
    depot = Depot(":memory:")
    if reponses:
        depot.pour("salon-1").enregistrer_reponses(reponses)
    return Console(journal=JournalDAppels(depot), tenant="salon-1",
                   depot=depot, pack=PACK)


def page(console, chemin="/reglages", methode="GET", corps=None):
    statut, _, contenu = console.repondre(methode, chemin, corps)
    return statut, contenu


# --- le dépôt ---------------------------------------------------------------

def test_les_reponses_se_gardent_et_se_relisent():
    depot = Depot(":memory:")
    depot.pour("salon-1").enregistrer_reponses({"A1": "Salon Elegance"})
    assert depot.reponses("salon-1") == {"A1": "Salon Elegance"}


def test_les_reponses_d_un_salon_ne_fuient_pas_chez_un_autre():
    depot = Depot(":memory:")
    depot.pour("salon-1").enregistrer_reponses({"A1": "Salon Elegance"})
    assert depot.reponses("salon-2") == {}


def test_une_reponse_en_remplace_une_autre_sans_effacer_les_voisines():
    depot = Depot(":memory:")
    acces = depot.pour("salon-1")
    acces.enregistrer_reponses({"A1": "Elegance", "C2": "non"})
    acces.enregistrer_reponses({"A1": "Salon Elegance"})
    assert depot.reponses("salon-1") == {"A1": "Salon Elegance", "C2": "non"}


# --- l'écran ----------------------------------------------------------------

def test_l_ecran_montre_les_questions_du_pack_et_jamais_un_prompt():
    _, contenu = page(console())
    assert "Quel nom l'agent doit-il prononcer" in contenu
    # « system-ui » est dans la pile de polices : on cherche les mots du métier
    # du modèle, pas des sous-chaînes.
    for interdit in ("prompt", "consigne", "température", "system prompt"):
        assert interdit not in contenu.lower()


def test_il_dit_ce_qui_manque_avant_que_l_agent_puisse_decrocher():
    """B7 : l'essentiel en position 1. Tant qu'une question critique est vide,
    l'agent ne décroche pas — c'est la première chose à dire."""
    _, contenu = page(console())
    assert "ne peut pas encore décrocher" in contenu


def test_quand_tout_est_repondu_l_ecran_le_dit(tmp_path):
    complet = {q["id"]: (q.get("defaut") or "oui")
               for bloc in PACK["blocs"] for q in bloc["questions"]
               if q.get("critique")}
    complet["A1"] = "Salon Elegance"
    _, contenu = page(console(complet))
    assert "peut décrocher" in contenu
    assert "ne peut pas encore décrocher" not in contenu


def test_une_reponse_postee_est_gardee_et_renvoie_au_fil():
    c = console()
    statut, _ = page(c, "/reglages", "POST", {"A1": "Salon Elegance"})
    assert statut == 303
    assert c.depot.reponses("salon-1")["A1"] == "Salon Elegance"


def test_une_question_inconnue_est_refusee():
    """Le formulaire vient du navigateur : on n'écrit que ce que le pack déclare."""
    c = console()
    page(c, "/reglages", "POST", {"XX9": "n'importe quoi"})
    assert "XX9" not in c.depot.reponses("salon-1")


def test_le_fil_renvoie_vers_les_reglages_tant_qu_il_manque_une_reponse():
    _, contenu = page(console(), "/")
    assert "/reglages" in contenu


# --- ce que le standard en fait ---------------------------------------------

def test_le_service_lit_les_reponses_du_questionnaire(tmp_path):
    """Sans cela, le commerçant remplit un formulaire qui ne sert à rien."""
    from datetime import date

    from standard.hors_ligne import ModeleHorsLigne
    from standard.service import Configuration, Service

    mardi = date(2026, 9, 15)
    depot = Depot(str(tmp_path / "salon.sqlite3"))
    depot.pour("salon-1").enregistrer_reponses({"A1": "Chez Amina"})

    service = Service(Configuration(tenant="salon-1", pack=PACK, aujourd_hui=mardi),
                      client_modele=ModeleHorsLigne(aujourd_hui=mardi),
                      base=depot.pour("salon-1"), reponses_du_depot=depot)
    service.demarrer()
    assert "Chez Amina" in service.nouvel_appel("appel-1").salutation()


def test_une_reponse_changee_pendant_le_service_s_applique_au_prochain_appel(tmp_path):
    from datetime import date

    from standard.hors_ligne import ModeleHorsLigne
    from standard.service import Configuration, Service

    mardi = date(2026, 9, 15)
    depot = Depot(str(tmp_path / "salon.sqlite3"))
    depot.pour("salon-1").enregistrer_reponses({"A1": "Chez Amina"})
    service = Service(Configuration(tenant="salon-1", pack=PACK, aujourd_hui=mardi),
                      client_modele=ModeleHorsLigne(aujourd_hui=mardi),
                      base=depot.pour("salon-1"), reponses_du_depot=depot)
    service.demarrer()

    # La console, autre processus, même base.
    Depot(str(tmp_path / "salon.sqlite3")).pour("salon-1").enregistrer_reponses(
        {"A1": "Salon Amina"})
    assert "Salon Amina" in service.nouvel_appel("appel-2").salutation()


def test_la_console_lancee_en_ligne_de_commande_recoit_le_pack():
    """Sans le pack, l'écran de réglages n'existe pas en production — la même
    faute que le dépôt non transmis."""
    import inspect

    from standard import __main__ as principal

    assert "pack=" in inspect.getsource(principal)


def test_le_serveur_branche_le_questionnaire(tmp_path):
    import os

    from standard.demarrage import construire_serveur

    racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    chemin = str(tmp_path / "salon.sqlite3")
    Depot(chemin).pour("salon-1").enregistrer_reponses({"A1": "Chez Amina"})
    serveur = construire_serveur({
        "STANDARD_TENANT": "salon-1",
        "STANDARD_PACK": os.path.join(racine, "packs", "coiffure.json"),
        "STANDARD_CRENEAUX": "15:30",
        "STANDARD_PORT": "0", "STANDARD_PORT_SANTE": "0",
        "STANDARD_BASE": chemin,
        "STANDARD_STT": "muet", "STANDARD_TTS": "muet",
    })
    assert "Chez Amina" in serveur.service.nouvel_appel("appel-1").salutation()


def test_l_accord_suit_le_nombre_de_reponses_manquantes():
    """« Il manque 1 réponse : sans elles » — une faute d'accord sur l'écran le
    plus lu du produit."""
    _, contenu = page(console({"A1": "Salon Elegance"}))
    if "Il manque 1 réponse" in contenu:
        assert "sans elle," in contenu and "sans elles," not in contenu


def test_les_defauts_du_pack_sont_deja_dans_le_formulaire():
    """B8 : le produit absorbe la complexité. Un salon qui ne change rien a
    quand même des horaires justes."""
    _, contenu = page(console())
    assert "09:00-19:00" in contenu


# --- les tarifs (question C3) -----------------------------------------------

def test_les_tarifs_se_saisissent_une_ligne_par_prestation():
    c = console({"C1": ["coupe", "coloration"]})
    _, contenu = page(c)
    assert "Vos tarifs" in contenu
    assert "coupe" in contenu


def test_un_tarif_saisi_devient_un_montant_et_pas_du_texte():
    c = console()
    page(c, "/reglages", "POST", {"C3": "coupe 28\ncoloration 65"})
    assert c.depot.reponses("salon-1")["C3"] == {"coupe": 28, "coloration": 65}


def test_une_ligne_de_tarif_illisible_n_emporte_pas_les_autres():
    c = console()
    page(c, "/reglages", "POST", {"C3": "coupe 28\nn'importe quoi\ncoloration 65"})
    assert c.depot.reponses("salon-1")["C3"] == {"coupe": 28, "coloration": 65}


def test_un_tarif_avec_des_centimes_et_un_euro_se_lit():
    c = console()
    page(c, "/reglages", "POST", {"C3": "coupe 28,50 €"})
    assert c.depot.reponses("salon-1")["C3"] == {"coupe": 28.5}
