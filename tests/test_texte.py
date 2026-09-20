"""La normalisation — une seule fois pour tout le produit.

`texte` remplaçait quatre normaliseurs qui divergeaient : l'un enlevait les
accents, l'autre pas, un troisième gardait la ponctuation. Un « oui » reconnu
ici et pas là, c'est un rendez-vous perdu sans message d'erreur.

Elle n'avait aucun test à elle : elle était vérifiée de biais, par ses appelants.
Une pièce partagée par trente-six modules mérite ses propres cas.
"""

import pytest

from standard.texte import aplatir, sans_accents


@pytest.mark.parametrize("dit, attendu", [
    ("éàüî", "eaui"),
    # `sans_accents` met aussi en minuscules : c'est son contrat, et tout le
    # produit compare des minuscules sans accents.
    ("ÉÀÜÎ", "eaui"),
    ("Ça", "ca"),
    ("l'été", "l'ete"),
    ("sans accent", "sans accent"),
    ("", ""),
])
def test_les_accents_tombent_sans_rien_casser(dit, attendu):
    assert sans_accents(dit) == attendu


def test_l_oeil_du_moteur_et_celui_du_clavier_se_rejoignent():
    """Le moteur rend « JEUDI », le clavier tape « jeudi » : même chose."""
    assert aplatir("JEUDI", garder="a-z' ") == aplatir("jeudi", garder="a-z' ")


@pytest.mark.parametrize("dit, attendu", [
    # L'apostrophe devient une espace : « l'agent » et « l agent » sont le même
    # mot à l'oreille, et c'est l'oreille qui fait foi.
    ("Oui, c'est parfait !", "oui c est parfait"),
    ("15h30", "h"),
    ("  espaces   multiples  ", "espaces multiples"),
])
def test_ce_qui_n_est_pas_garde_disparait(dit, attendu):
    assert aplatir(dit, garder="a-z ") == attendu


def test_garder_les_chiffres_est_un_choix_explicite():
    assert aplatir("15h30", garder="a-z0-9") == "15h30"


def test_une_chaine_vide_ne_fait_pas_tomber_la_normalisation():
    assert aplatir("", garder="a-z") == ""
    assert aplatir(None or "", garder="a-z") == ""
