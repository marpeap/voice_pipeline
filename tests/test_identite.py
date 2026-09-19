"""Le nom de l'appelant — ce qu'un salon lit sur son agenda le matin.

Confrontation du 19/09 avec ce que vendent les standards IA du marché : tous
capturent le nom. Le nôtre écrivait des rendez-vous anonymes, et un salon qui
lit « jeudi 15 h 30 » sans nom ne sait pas qui vient.
"""

import pytest

from standard.identite import lire_nom


@pytest.mark.parametrize("dit, attendu", [
    ("Dupont", "Dupont"),
    ("c'est au nom de Dupont", "Dupont"),
    ("au nom de madame Lefevre", "Lefevre"),
    ("je m'appelle Karim Benali", "Karim Benali"),
    ("mon nom c'est Nguyen", "Nguyen"),
    ("monsieur Martin", "Martin"),
])
def test_le_nom_se_degage_de_la_phrase(dit, attendu):
    lecture = lire_nom(dit)
    assert lecture.issue == "accepte"
    assert lecture.nom == attendu


@pytest.mark.parametrize("dit", [
    "",
    "   ",
    "euh",
    # Une phrase entière n'est pas un nom : l'écrire produirait une ligne
    # d'agenda illisible, et la confirmation orale deviendrait absurde.
    "je voudrais plutôt venir un autre jour si c'est possible pour vous",
])
def test_ce_qui_n_est_pas_un_nom_est_refuse(dit):
    assert lire_nom(dit).issue == "refus"


def test_le_nom_est_capitalise_comme_on_l_ecrit():
    """Le moteur rend tout en capitales : « DUPONT » s'écrit « Dupont »."""
    assert lire_nom("DUPONT").nom == "Dupont"
    assert lire_nom("LE GALL").nom == "Le Gall"


def test_le_nom_garde_ses_traits_d_union_et_ses_apostrophes():
    assert lire_nom("Jean-Pierre D'Amico").nom == "Jean-Pierre D'Amico"


def test_un_nom_trop_long_est_refuse():
    assert lire_nom("a" * 60).issue == "refus"
