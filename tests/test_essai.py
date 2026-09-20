"""« Essayer mon agent » — entendre ce qu'il répondra, avant de brancher le numéro.

Confrontation du 20/09 avec les produits du marché : tous font tester l'agent
avant la mise en ligne — requêtes courantes, questions ambiguës, cas à risque.
Le nôtre n'offrait rien : le commerçant remplissait un questionnaire, et
découvrait le résultat sur son premier vrai client.

Deux exigences que rien ne doit trahir :
  - l'essai n'écrit **jamais** dans l'agenda réel ;
  - il utilise **la configuration du commerçant**, sinon il ne prouve rien.
"""

import json

from standard.console import Console
from standard.depot import Depot
from standard.journal import JournalDAppels

PACK = json.load(open("packs/coiffure.json"))


def console(reponses=None):
    depot = Depot(":memory:")
    depot.pour("salon-1").enregistrer_reponses(
        reponses or {"A1": "Chez Amina", "A2": {"jeudi": ["09:00-19:00"]}})
    return Console(journal=JournalDAppels(depot), tenant="salon-1",
                   depot=depot, pack=PACK, creneaux=("09:00", "15:30"))


def page(console, chemin="/essayer", methode="GET", corps=None):
    statut, _, contenu = console.repondre(methode, chemin, corps)
    return statut, contenu


def test_l_ecran_propose_des_phrases_toutes_faites():
    """B2 : un défaut recommandé. Un gérant ne sait pas quoi taper à un agent."""
    _, contenu = page(console())
    assert "rendez-vous" in contenu.lower()
    assert contenu.lower().count("<button") >= 2


def test_l_agent_repond_avec_le_nom_du_salon():
    c = console()
    page(c, "/essayer", "POST", {"dire": "bonjour"})
    _, contenu = page(c)
    assert "Chez Amina" in contenu


def test_un_essai_n_ecrit_jamais_dans_l_agenda_reel():
    """La garantie qui rend l'essai utilisable : on peut tout tenter."""
    c = console()
    for phrase in ("je voudrais un rendez-vous jeudi à quinze heures trente",
                   "oui c'est parfait", "au nom de Dupont"):
        page(c, "/essayer", "POST", {"dire": phrase})
    assert c.depot.lister("salon-1") == []


def test_l_essai_montre_la_conversation_dans_l_ordre():
    c = console()
    page(c, "/essayer", "POST", {"dire": "je voudrais un rendez-vous jeudi"})
    page(c, "/essayer", "POST", {"dire": "à quinze heures trente"})
    _, contenu = page(c)
    assert contenu.index("rendez-vous jeudi") < contenu.index("quinze heures trente")


def test_on_peut_recommencer_un_essai():
    c = console()
    page(c, "/essayer", "POST", {"dire": "bonjour"})
    page(c, "/essayer", "POST", {"recommencer": "1"})
    _, contenu = page(c)
    assert "bonjour" not in contenu.lower().split("<form")[0]


def test_l_essai_utilise_les_reponses_du_commercant():
    c = console({"A1": "Le Salon d'à côté", "A2": {"jeudi": ["09:00-19:00"]}})
    page(c, "/essayer", "POST", {"dire": "vous êtes ouverts quand ?"})
    _, contenu = page(c)
    assert "9 h" in contenu


def test_chaque_ecran_mene_a_l_essai_et_aux_reglages():
    """B10 : aucune fin en cul-de-sac. Un gérant qui vient de répondre doit
    pouvoir écouter tout de suite ce que ça donne."""
    c = console()
    for chemin in ("/", "/reglages"):
        _, contenu = page(c, chemin)
        assert "/essayer" in contenu, chemin
        assert "/reglages" in contenu, chemin


def test_la_console_lancee_en_ligne_de_commande_recoit_les_creneaux():
    """Sans eux, l'essai montre un agenda vide et le gérant croit son agent
    cassé — c'est exactement ce qui est arrivé le 20/09 en l'essayant."""
    import inspect

    from standard import __main__ as principal

    assert "creneaux=config.creneaux" in inspect.getsource(principal)


def test_une_phrase_toute_faite_recommence_un_appel_neuf():
    """Les quatre phrases proposées sont des DÉBUTS d'appel. Les envoyer au
    milieu d'une conversation déjà aboutie montrait l'agent sous un faux jour —
    le démarchage, par exemple, n'est filtré que dans les premiers tours."""
    c = console()
    for phrase in ("je voudrais un rendez-vous jeudi à quinze heures trente",
                   "oui c'est parfait", "au nom de Dupont"):
        page(c, "/essayer", "POST", {"dire": phrase})

    page(c, "/essayer", "POST",
         {"dire": "Je vous appelle pour vous proposer notre solution de référencement.",
          "nouveau": "1"})
    _, contenu = page(c)
    assert "démarchages" in contenu.lower()
    assert "Dupont" not in contenu, "l'appel précédent traîne encore à l'écran"
