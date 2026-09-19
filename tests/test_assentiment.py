"""Dire oui, dire non. Trouvé manquant par la revue du 19/09."""

import pytest

from standard.assentiment import est_un_oui, est_un_refus


@pytest.mark.parametrize("dit", [
    "oui", "oui c'est parfait", "d'accord", "ça me va", "très bien merci",
    "OUI C'EST PARFAIT", "je confirme", "allez-y", "entendu",
])
def test_les_accords_sont_reconnus(dit):
    assert est_un_oui(dit) is True


@pytest.mark.parametrize("dit", [
    "non", "non merci", "pas possible", "plutôt vendredi", "laissez tomber",
])
def test_les_refus_sont_reconnus(dit):
    assert est_un_refus(dit) is True
    assert est_un_oui(dit) is False


@pytest.mark.parametrize("dit", [
    "oui mais pas jeudi",
    "oui enfin non attendez",
    "d'accord mais jamais le matin",
])
def test_un_accord_assorti_d_une_negation_n_en_est_pas_un(dit):
    """Écrire le rendez-vous sur un « oui mais » est la faute la plus chère du
    produit : le client croit avoir dit autre chose."""
    assert est_un_oui(dit) is False


@pytest.mark.parametrize("dit", [
    "je voudrais un rendez-vous jeudi", "combien coûte un balayage", "",
])
def test_ce_qui_n_est_ni_l_un_ni_l_autre_retourne_au_chemin_normal(dit):
    assert est_un_oui(dit) is False
    assert est_un_refus(dit) is False
