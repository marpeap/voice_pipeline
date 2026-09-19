"""La correction posée dans la console atteint le service qui tourne.

La console promet au gérant : « elle s'applique dès maintenant ». Elle tourne
dans un **autre processus** que le standard — ils ne partagent que la base. Le
service composait sa mémoire une fois, au démarrage, et ne la relisait jamais :
la correction n'arrivait qu'au prochain redémarrage, c'est-à-dire jamais sur une
machine qui marche bien.
"""

import json
from datetime import date

from standard.correction import Correction, RegistreDeCorrections
from standard.depot import Depot
from standard.hors_ligne import ModeleHorsLigne
from standard.service import Configuration, Service

MARDI = date(2026, 9, 15)
PACK = json.load(open("packs/coiffure.json"))


def service_et_base(tmp_path):
    chemin = str(tmp_path / "salon.sqlite3")
    depot = Depot(chemin)
    config = Configuration(tenant="salon-1", pack=PACK, reponses={"A1": "Salon"},
                           aujourd_hui=MARDI, creneaux=("09:00", "12:30", "15:30"))
    service = Service(config, client_modele=ModeleHorsLigne(aujourd_hui=MARDI),
                      base=depot.pour("salon-1"),
                      corrections=RegistreDeCorrections(depot=depot, tenant="salon-1"))
    service.demarrer()
    return service, chemin


def poser_depuis_la_console(chemin, correction):
    """Ce que fait la console : un autre processus, la même base."""
    registre = RegistreDeCorrections(depot=Depot(chemin), tenant="salon-1")
    registre.ajouter(correction)


def test_une_correction_posee_ailleurs_atteint_le_prochain_appel(tmp_path):
    service, chemin = service_et_base(tmp_path)
    assert "12:30" in service._agenda().libres("2026-09-17")

    poser_depuis_la_console(chemin, Correction(
        faute="creneau_inexistant", appel="a-1", empan="midi et demi",
        valeur={"heure": "12:30"}))

    service.nouvel_appel("appel-1")          # un appel arrive : on relit
    assert "12:30" not in service._agenda().libres("2026-09-17")


def test_relire_ne_recompose_rien_quand_rien_n_a_change(tmp_path):
    """Relire à chaque appel ne doit pas refabriquer la mémoire à chaque fois :
    c'est le prompt caché qui en dépend (4 096 tokens, mesure 23)."""
    service, _ = service_et_base(tmp_path)
    service.nouvel_appel("appel-1")
    empreinte = id(service._memoire[0])
    service.nouvel_appel("appel-2")
    assert id(service._memoire[0]) == empreinte


def test_une_correction_revoquee_ailleurs_cesse_de_s_appliquer(tmp_path):
    service, chemin = service_et_base(tmp_path)
    poser_depuis_la_console(chemin, Correction(
        faute="creneau_inexistant", appel="a-1", empan="", valeur={"heure": "12:30"}))
    service.nouvel_appel("appel-1")
    assert "12:30" not in service._agenda().libres("2026-09-17")

    registre = RegistreDeCorrections(depot=Depot(chemin), tenant="salon-1")
    registre.revoquer(registre.actives()[0].identifiant)
    service.nouvel_appel("appel-2")
    assert "12:30" in service._agenda().libres("2026-09-17")
