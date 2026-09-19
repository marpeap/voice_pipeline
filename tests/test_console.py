"""La console du commerçant — voir ses appels, corriger en trois gestes.

Règle qui domine `docs/06` : **le commerçant ne voit jamais un prompt, sous
aucune forme « avancée »**. La console doit donc rendre une correction possible
*sans clavier* et sans jamais montrer une consigne rédigée.

Conception : règles Barthez. Action primaire = corriger un appel raté. Pic = la
faute choisie en un geste. Fin = « la correction est active, et rejouée à chaque
changement ».
"""

import pytest

from standard.console import Console
from standard.depot import Depot
from standard.journal import JournalDAppels

APPEL = {
    "uuid": "7f3a1c5e-0000-4000-8000-000000000001",
    "debut": "2026-09-19T10:00:00+00:00", "duree_s": 74.2, "issue": "rendez-vous",
    "rsb_db": 18.4, "bruite": False, "interruptions": 0,
    "preuve_annonce": {"conforme": True, "formulation": "assistant automatique"},
    "tours": [{"genre": "question", "phrase": "Quel jour vous conviendrait ?",
               "transcription": "je voudrais une permanente"}],
}


@pytest.fixture
def console():
    depot = Depot(":memory:")
    journal = JournalDAppels(depot)
    journal.enregistrer("salon-1", APPEL)
    return Console(journal=journal, tenant="salon-1")


def page(console, chemin="/", methode="GET", corps=None):
    statut, entetes, contenu = console.repondre(methode, chemin, corps)
    return statut, contenu


# --- le fil -----------------------------------------------------------------

def test_le_fil_montre_les_appels(console):
    statut, contenu = page(console)
    assert statut == 200
    assert "rendez-vous" in contenu
    assert APPEL["uuid"][:8] in contenu


def test_un_salon_sans_appel_voit_un_etat_vide_utile(console):
    vide = Console(journal=console.journal, tenant="salon-2")
    statut, contenu = page(vide)
    assert statut == 200
    assert "aucun appel" in contenu.lower()


def test_le_fil_ne_montre_jamais_les_appels_d_un_autre(console):
    autre = Console(journal=console.journal, tenant="salon-2")
    assert APPEL["uuid"][:8] not in page(autre)[1]


def test_les_incidents_passent_devant(console):
    console.journal.enregistrer("salon-1", APPEL | {
        "uuid": "incident-1", "confirmations_orphelines": 1})
    contenu = page(console)[1]
    assert contenu.index("incident") < contenu.index("Fil des appels")


# --- le détail --------------------------------------------------------------

def test_le_detail_montre_la_transcription(console):
    statut, contenu = page(console, f"/appel/{APPEL['uuid']}")
    assert statut == 200
    assert "je voudrais une permanente" in contenu


def test_un_appel_inconnu_rend_404(console):
    assert page(console, "/appel/inexistant")[0] == 404


def test_les_sept_fautes_sont_proposees_sans_clavier(console):
    contenu = page(console, f"/appel/{APPEL['uuid']}")[1]
    from standard.correction import FAUTES
    for faute, definition in FAUTES.items():
        assert definition["libelle"] in contenu
    # Une seule entrée libre, et elle est annoncée comme telle.
    assert contenu.count("<textarea") <= 1


def test_aucun_prompt_n_est_visible_nulle_part(console):
    """Le mot lui-même n'a rien à faire dans une interface de commerçant."""
    for chemin in ("/", f"/appel/{APPEL['uuid']}"):
        contenu = page(console, chemin).__getitem__(1).lower()
        assert "prompt" not in contenu
        assert "system message" not in contenu


# --- la correction ----------------------------------------------------------

def test_une_correction_se_pose_en_un_envoi(console):
    statut, contenu = page(console, "/correction", "POST", {
        "appel": APPEL["uuid"], "faute": "prestation",
        "empan": "je voudrais une permanente",
        "terme": "permanente", "prestation": "permanente_classique"})
    assert statut == 303
    assert console.registre.actives()


def test_la_correction_dit_ce_qu_elle_change_et_la_suite(console):
    page(console, "/correction", "POST", {
        "appel": APPEL["uuid"], "faute": "duree",
        "empan": "une coupe", "prestation": "coupe", "duree_minutes": "45"})
    contenu = page(console)[1]
    assert "correction" in contenu.lower()
    assert "rejouée" in contenu or "rejouee" in contenu


def test_une_faute_inconnue_est_refusee_proprement(console):
    statut, contenu = page(console, "/correction", "POST", {
        "appel": APPEL["uuid"], "faute": "n-importe-quoi", "empan": "x"})
    assert statut == 400
    assert "faute" in contenu.lower()


def test_une_correction_devient_un_scenario_rejoue(console):
    page(console, "/correction", "POST", {
        "appel": APPEL["uuid"], "faute": "prestation", "empan": "une permanente",
        "terme": "permanente", "prestation": "permanente_classique"})
    scenarios = console.registre.scenarios_de_regression()
    assert scenarios and scenarios[0]["repetitions"] == 5


# --- conception (règles Barthez) --------------------------------------------

def test_la_palette_est_celle_du_systeme_et_l_accent_est_unique(console):
    contenu = page(console)[1]
    assert "#F2F0EB" in contenu and "#0A0A0C" in contenu
    assert "#0A0AEA" in contenu
    assert "#FFFFFF" not in contenu and "#000000" not in contenu


def test_les_cibles_tactiles_sont_assez_grandes(console):
    contenu = page(console, f"/appel/{APPEL['uuid']}")[1]
    assert "min-height:44px" in contenu.replace(" ", "")


def test_le_pic_et_la_fin_sont_nommes_dans_le_code(console):
    """Barthez B10 : si on ne peut pas les nommer, ils n'ont pas été conçus."""
    import standard.console as module
    assert "pic" in module.__doc__.lower() and "fin" in module.__doc__.lower()


def test_le_mouvement_respecte_le_reglage_systeme(console):
    """Le gate mécanique ne voit pas cette règle : la feuille de style vit dans
    un fichier Python, pas dans un .css. C'est donc à la suite de tests de la
    garder — le mouvement déclenche nausées et migraines chez qui a réglé son
    système exprès."""
    contenu = page(console)[1]
    assert "prefers-reduced-motion" in contenu


# --- ce que la console laisse comme trace ------------------------------------

def test_une_correction_laisse_une_trace_d_audit():
    """Sinon « l'agent s'est mis à refuser tout le monde » n'a pas d'explication,
    et on cherche dans le code un défaut qui est un réglage."""
    from standard.audit import PisteDAudit
    from standard.journal import JournalDAppels

    depot = Depot(":memory:")
    journal = JournalDAppels(depot)
    journal.enregistrer("salon-1", APPEL)
    piste = PisteDAudit(depot)
    console = Console(journal=journal, tenant="salon-1", audit=piste, acteur="gérant")

    console.repondre("POST", "/correction", {
        "appel": APPEL["uuid"], "faute": "duree", "empan": "une coupe",
        "prestation": "coupe", "duree_minutes": "45"})

    [evenement] = piste.lister("salon-1")
    assert evenement["action"] == "correction.posee"
    assert evenement["acteur"] == "gérant"
    assert evenement["correlation"] == APPEL["uuid"]


def test_sans_piste_d_audit_la_console_fonctionne_quand_meme(console):
    """Une console qui refuserait de corriger faute de journal serait pire que le
    manque de trace."""
    statut, _ = page(console, "/correction", "POST", {
        "appel": APPEL["uuid"], "faute": "duree", "empan": "x",
        "prestation": "coupe", "duree_minutes": "30"})
    assert statut == 303


def test_le_formulaire_propose_les_champs_que_la_correction_utilise(console):
    """Seconde revue (19/09) : le formulaire n'envoyait qu'une note libre, donc
    `appliquer` levait `KeyError` sur toute correction issue de la console."""
    contenu = page(console, f"/appel/{APPEL['uuid']}")[1]
    for champ in ("prestation", "duree_minutes", "interdit"):
        assert f'name={champ}' in contenu or f'name="{champ}"' in contenu


def test_une_duree_illisible_ne_fait_pas_tomber_la_console(console):
    statut, _ = page(console, "/correction", "POST", {
        "appel": APPEL["uuid"], "faute": "duree", "empan": "x",
        "prestation": "coupe", "duree_minutes": "quarante-cinq"})
    assert statut == 303


# --- les messages à rappeler -------------------------------------------------
# Un message pris et jamais montré vaut moins que pas de message du tout : le
# commerçant croit que l'agent a transféré.

@pytest.fixture
def console_avec_message():
    depot = Depot(":memory:")
    journal = JournalDAppels(depot)
    journal.enregistrer("salon-1", APPEL)
    depot.pour("salon-1").enregistrer_message(
        {"texte": "je cherche une coloration végétale pour samedi",
         "nom": "Dupont", "telephone": "0612345678"})
    return Console(journal=journal, tenant="salon-1", depot=depot)


def test_le_fil_montre_les_messages_a_rappeler(console_avec_message):
    _, contenu = page(console_avec_message)
    assert "coloration végétale" in contenu
    assert "06 12 34 56 78" in contenu, "le numéro doit être lisible d'un coup d'œil"


def test_un_message_passe_avant_le_fil_des_appels(console_avec_message):
    """B7 : ce qui appelle une action est en position 1, pas au milieu."""
    _, contenu = page(console_avec_message)
    assert contenu.index("rappeler") < contenu.index("Fil des appels")


def test_sans_message_la_console_n_affiche_pas_la_section(console):
    _, contenu = page(console)
    assert "à rappeler" not in contenu


def test_les_messages_d_un_autre_salon_ne_s_affichent_pas():
    depot = Depot(":memory:")
    journal = JournalDAppels(depot)
    journal.enregistrer("salon-1", APPEL)
    depot.pour("salon-2").enregistrer_message({"texte": "message du voisin"})
    _, contenu = page(Console(journal=journal, tenant="salon-1", depot=depot))
    assert "voisin" not in contenu


def test_la_console_lancee_en_ligne_de_commande_recoit_le_depot():
    """Sans le dépôt, la section « à rappeler » est invisible en production —
    la même faute que le clavier posé sur un objet qui ne le délègue pas."""
    import inspect

    import standard.__main__ as principal

    source = inspect.getsource(principal)
    assert "depot=depot" in source


def test_un_rendez_vous_a_rattraper_se_distingue_d_un_message():
    """Un rendez-vous que l'agenda n'a pas confirmé n'est pas un message de
    rappel : c'est une action à faire avant que le client ne se déplace."""
    depot = Depot(":memory:")
    journal = JournalDAppels(depot)
    journal.enregistrer("salon-1", APPEL)
    depot.pour("salon-1").enregistrer_message({
        "type": "rendez_vous_a_rattraper",
        "texte": "Rendez-vous à confirmer : jeudi 17 septembre à 15 h 30.",
        "nom": "Dupont", "telephone": "0612345678"})
    _, contenu = page(Console(journal=journal, tenant="salon-1", depot=depot))
    assert "À confirmer" in contenu
    assert contenu.index("À confirmer") < contenu.index("Fil des appels")
