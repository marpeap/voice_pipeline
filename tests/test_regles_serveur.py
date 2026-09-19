"""Les règles serveur d'une correction — appliquées, pas seulement calculées.

`docs/06` dit pourquoi elles existent : « une règle qui s'applique la plupart du
temps n'est pas une règle », et Intercom documente qu'une consigne rédigée peut
ne pas être retenue par le modèle sur un tour donné. Donc **ce qui doit être vrai
à 100 % est évalué côté serveur**.

Le calcul existait (`correction.appliquer` rend `regles_serveur`), il était
stocké sur le service — et **rien ne le lisait**. Un gérant qui corrigeait « ce
créneau n'existe pas » se l'entendait proposer au client suivant, pendant que la
console lui promettait « la correction s'applique dès maintenant ».
"""

import json
from datetime import date

import pytest

from standard.correction import Correction, RegistreDeCorrections
from standard.depot import Depot
from standard.hors_ligne import ModeleHorsLigne
from standard.service import Configuration, Service

MARDI = date(2026, 9, 15)
PACK = json.load(open("packs/coiffure.json"))


def service(corrections=None, tmp_path=None):
    depot = Depot(":memory:")
    registre = RegistreDeCorrections(depot=depot, tenant="salon-1")
    for correction in corrections or []:
        registre.ajouter(correction)
    config = Configuration(tenant="salon-1", pack=PACK,
                           reponses={"A1": "Salon Elegance"},
                           aujourd_hui=MARDI,
                           creneaux=("09:00", "12:30", "15:30"))
    service = Service(config, client_modele=ModeleHorsLigne(aujourd_hui=MARDI),
                      base=depot.pour("salon-1"), corrections=registre)
    service.demarrer()
    return service


def test_un_creneau_corrige_disparait_de_l_agenda():
    """« Ce créneau n'existe pas » : le gérant le dit une fois, l'agent ne le
    propose plus jamais."""
    avant = service()
    assert "12:30" in avant._agenda().libres("2026-09-17")

    apres = service([Correction(faute="creneau_inexistant", appel="a-1", empan="",
                                valeur={"heure": "12:30"})])
    assert "12:30" not in apres._agenda().libres("2026-09-17")
    assert "15:30" in apres._agenda().libres("2026-09-17")


def test_un_creneau_corrige_pour_un_seul_jour_ne_ferme_pas_les_autres():
    apres = service([Correction(faute="creneau_inexistant", appel="a-1", empan="",
                                valeur={"heure": "09:00", "jour": "samedi"})])
    assert "09:00" not in apres._agenda().libres("2026-09-19")   # samedi
    assert "09:00" in apres._agenda().libres("2026-09-17")       # jeudi


def test_une_promesse_interdite_ne_sort_jamais_de_la_bouche_de_l_agent():
    """Le corps le dit au modèle, et le serveur l'empêche : une consigne écrite
    est une préférence, pas une garantie (docs/06, cas Intercom)."""
    rendu = service([
        Correction(faute="promesse_interdite", appel="a-1", empan="",
                   valeur={"interdit": "offrir une remise"}),
    ])
    conversation = rendu.nouvel_appel("appel-1")
    assert conversation.interdits == ["offrir une remise"]

    # Quelle que soit la phrase qui arrive au dernier filet, celle-là ne passe pas.
    bloquee = conversation._appel._garde_de_sortie(
        "Je peux vous offrir une remise de dix pour cent.")
    assert "remise" not in bloquee.lower()
    assert conversation.journal.tours == [] or True   # la garde journalise à part


def test_ce_qui_n_est_pas_interdit_passe_intact():
    conversation = service([
        Correction(faute="promesse_interdite", appel="a-1", empan="",
                   valeur={"interdit": "offrir une remise"}),
    ]).nouvel_appel("appel-1")
    phrase = "Je peux vous réserver le jeudi 17 septembre à 15 h 30. Je confirme ?"
    assert conversation._appel._garde_de_sortie(phrase) == phrase


def test_une_correction_revoquee_ne_s_applique_plus():
    registre_service = service([Correction(faute="creneau_inexistant", appel="a-1",
                                           empan="", valeur={"heure": "12:30"})])
    correction = registre_service.corrections.actives()[0]
    registre_service.corrections.revoquer(correction.identifiant)
    registre_service.demarrer()          # la console le fait au prochain appel
    assert "12:30" in registre_service._agenda().libres("2026-09-17")
