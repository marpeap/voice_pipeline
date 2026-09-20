"""La durée d'une prestation — déclarée partout, utilisée nulle part.

Les packs portent une durée par prestation (coupe 30 min, brushing 45,
coloration 120), la boucle de correction sait la changer, et **rien ne s'en
servait** : un rendez-vous occupait un créneau, un seul. Une coloration de deux
heures à 17 h laissait donc 17 h 30 réservable — le salon se double-bookait
tout seul, et le découvrait le jour venu.
"""

from datetime import date

import pytest

from standard.decision import Agenda, creneaux_couverts

MARDI = date(2026, 9, 15)
GRILLE = ("09:00", "09:45", "10:30", "11:15", "14:00", "14:45", "15:30",
          "16:15", "17:00")


# --- ce qu'une prestation occupe -------------------------------------------

@pytest.mark.parametrize("heure, duree, attendu", [
    ("15:30", 30, ["15:30"]),
    ("15:30", 45, ["15:30"]),
    ("15:30", 46, ["15:30", "16:15"]),
    ("15:30", 120, ["15:30", "16:15", "17:00"]),
    ("15:30", None, ["15:30"]),
])
def test_une_prestation_occupe_ce_qu_elle_dure(heure, duree, attendu):
    assert creneaux_couverts(heure, duree, GRILLE) == attendu


def test_une_prestation_qui_deborde_de_la_journee_n_est_pas_tronquee():
    """Deux heures à 17 h, alors que le dernier créneau est 17 h : la liste
    rendue dit ce qui manque, elle ne fait pas semblant que ça rentre."""
    assert creneaux_couverts("17:00", 120, GRILLE) == ["17:00", None, None]


# --- ce que l'agenda en fait ------------------------------------------------

def agenda(pris=None):
    return Agenda(aujourd_hui=MARDI, horizon_jours=14, jours_fermes=(6, 0),
                  creneaux=set(GRILLE), pris=pris or {})


def test_un_creneau_est_libre_pour_une_coupe_et_pas_pour_une_coloration():
    a = agenda({"2026-09-17": {"17:00"}})
    assert "15:30" in a.libres("2026-09-17", duree_minutes=30)
    # 15:30 + 2 h mordrait sur 17:00, déjà pris.
    assert "15:30" not in a.libres("2026-09-17", duree_minutes=120)


def test_une_prestation_trop_longue_pour_la_fin_de_journee_disparait():
    a = agenda()
    assert "17:00" in a.libres("2026-09-17", duree_minutes=30)
    assert "17:00" not in a.libres("2026-09-17", duree_minutes=120)


def test_sans_duree_rien_ne_change():
    a = agenda({"2026-09-17": {"17:00"}})
    assert a.libres("2026-09-17") == [h for h in GRILLE if h != "17:00"]


# --- de bout en bout --------------------------------------------------------

def test_l_agenda_connait_la_duree_d_une_prestation():
    a = Agenda(aujourd_hui=MARDI, creneaux=set(GRILLE), jours_fermes=(6, 0),
               durees={"coloration": 120, "coupe": 30})
    assert a.duree_de("coloration") == 120
    assert a.duree_de("coupe") == 30
    assert a.duree_de(None) is None
    assert a.duree_de("inconnue") is None


def test_une_coloration_ne_se_propose_pas_en_fin_de_journee():
    from standard.decision import Etat, decider

    a = Agenda(aujourd_hui=MARDI, creneaux={"15:30", "16:15", "17:00"},
               jours_fermes=(6, 0), durees={"coloration": 120})
    sortie = decider({"intention": "rdv", "date": "2026-09-17", "heure": "17:00",
                      "prestation": "coloration",
                      "confiance": {"intention": 0.9, "date": 0.9, "heure": 0.9},
                      "manque": []}, Etat(), a)
    assert sortie.genre != "proposition", sortie.phrase


def test_la_meme_heure_convient_pour_une_coupe():
    from standard.decision import Etat, decider

    a = Agenda(aujourd_hui=MARDI, creneaux={"15:30", "16:15", "17:00"},
               jours_fermes=(6, 0), durees={"coupe": 30})
    sortie = decider({"intention": "rdv", "date": "2026-09-17", "heure": "17:00",
                      "prestation": "coupe",
                      "confiance": {"intention": 0.9, "date": 0.9, "heure": 0.9},
                      "manque": []}, Etat(), a)
    assert sortie.genre == "proposition"


def test_un_rendez_vous_long_bloque_les_creneaux_qu_il_occupe(tmp_path):
    """Le vrai dégât : une coloration de deux heures à 15 h 30 laissait 16 h 15
    réservable, et deux clients arrivaient ensemble."""
    import os

    from standard.demarrage import construire_serveur

    racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    serveur = construire_serveur({
        "STANDARD_TENANT": "salon-1",
        "STANDARD_PACK": os.path.join(racine, "packs", "coiffure.json"),
        "STANDARD_REPONSES": '{"A1": "Salon", "C1": ["coupe", "coloration"]}',
        "STANDARD_CRENEAUX": "15:30,16:15,17:00",
        "STANDARD_PORT": "0", "STANDARD_PORT_SANTE": "0",
        "STANDARD_BASE": str(tmp_path / "essai.sqlite3"),
        "STANDARD_STT": "muet", "STANDARD_TTS": "muet",
    })
    depot_acces = serveur.service.base
    depot_acces.inserer("cle-1", {"date": "2026-09-17", "heure": "15:30",
                                  "prestation": "coloration", "duree_minutes": 120})
    libres = serveur.service._agenda().libres("2026-09-17")
    assert "16:15" not in libres, f"16:15 est encore libre : {libres}"
    assert "17:00" not in libres


def test_les_durees_du_pack_arrivent_jusqu_a_l_agenda():
    """Déclarées dans le pack, corrigeables par la console : encore faut-il
    qu'elles atteignent l'objet qui décide."""
    import json

    from standard.hors_ligne import ModeleHorsLigne
    from standard.service import Configuration, Service
    from standard.depot import Depot

    pack = json.load(open("packs/coiffure.json"))
    service = Service(Configuration(tenant="salon-1", pack=pack,
                                    reponses={"A1": "Salon",
                                              "C1": ["coupe", "coloration"]},
                                    aujourd_hui=MARDI, creneaux=GRILLE),
                      client_modele=ModeleHorsLigne(aujourd_hui=MARDI),
                      base=Depot(":memory:").pour("salon-1"))
    service.demarrer()
    agenda = service._agenda()
    assert agenda.duree_de("coupe") == 30
    assert agenda.duree_de("coloration") and agenda.duree_de("coloration") > 60


def test_une_correction_de_duree_l_emporte_sur_le_pack():
    import json

    from standard.correction import Correction, RegistreDeCorrections
    from standard.depot import Depot
    from standard.hors_ligne import ModeleHorsLigne
    from standard.service import Configuration, Service

    pack = json.load(open("packs/coiffure.json"))
    depot = Depot(":memory:")
    registre = RegistreDeCorrections(depot=depot, tenant="salon-1")
    registre.ajouter(Correction(faute="duree", appel="a-1", empan="",
                                valeur={"prestation": "coupe", "duree_minutes": 60}))
    service = Service(Configuration(tenant="salon-1", pack=pack,
                                    reponses={"A1": "Salon", "C1": ["coupe"]},
                                    aujourd_hui=MARDI, creneaux=GRILLE),
                      client_modele=ModeleHorsLigne(aujourd_hui=MARDI),
                      base=depot.pour("salon-1"), corrections=registre)
    service.demarrer()
    assert service._agenda().duree_de("coupe") == 60


def test_le_rendez_vous_ecrit_porte_sa_duree(tmp_path):
    """Sans la durée sur la ligne, l'agenda du lendemain ne sait plus ce que
    ce rendez-vous occupe."""
    import json

    from standard.appel import Appel
    from standard.depot import Depot
    from standard.hors_ligne import ModeleHorsLigne

    depot = Depot(str(tmp_path / "essai.sqlite3"))
    appel = Appel(client_modele=ModeleHorsLigne(aujourd_hui=MARDI),
                  agenda=Agenda(aujourd_hui=MARDI, creneaux=set(GRILLE),
                                jours_fermes=(6, 0), durees={"coupe": 30}),
                  base=depot.pour("salon-1"), memoire="", consignes_communes="c",
                  tenant="salon-1", identifiant="appel-1")
    appel.fiche = {"reservation": {"nom": "non"}}
    appel.etat.connu["prestation"] = "coupe"
    appel.tour("je voudrais un rendez-vous jeudi à quinze heures trente")
    appel.confirmer()
    assert depot.lister("salon-1")[0]["duree_minutes"] == 30
