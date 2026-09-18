"""Le moteur hors ligne : comprendre sans modele, quand il le faut.

Deux usages, et le second n'est pas un pis-aller. Rejouer un appel sans cle ni
telephone — c'est ce qui rend le produit demontrable. Et **tenir quand le
fournisseur tombe** : mesure 20, sa latence est une variable aleatoire bornee par
le haut, jusqu'a 8 751 ms sur un tour.

La grammaire des dates et heures est celle de docs/10 §4, et les cas viennent des
enonces reellement transcrits.
"""

from datetime import date

import pytest

from standard.hors_ligne import ModeleHorsLigne

MARDI = date(2026, 9, 15)


def analyser(dit, calendrier=None):
    modele = ModeleHorsLigne(aujourd_hui=MARDI)
    import json
    return json.loads(modele.completer([{"role": "user", "content": dit}]))


# --- les jours --------------------------------------------------------------

@pytest.mark.parametrize("dit, attendu", [
    ("je voudrais un rendez-vous jeudi", "2026-09-17"),
    ("jeudi prochain", "2026-09-17"),
    ("demain", "2026-09-16"),
    ("apres-demain", "2026-09-17"),
    ("samedi", "2026-09-19"),
    ("le dix-sept septembre", "2026-09-17"),
    ("le 24 decembre", "2026-12-24"),
])
def test_les_jours_se_lisent(dit, attendu):
    assert analyser(dit)["date"] == attendu


def test_un_jour_deja_passe_dans_la_semaine_bascule_a_la_suivante():
    """On est mardi : « lundi » veut dire le lundi qui vient, pas celui d'hier."""
    assert analyser("lundi")["date"] == "2026-09-21"


# --- les heures -------------------------------------------------------------

@pytest.mark.parametrize("dit, attendu", [
    ("a quinze heures trente", "15:30"),
    ("a quinze heures", "15:00"),
    ("neuf heures moins le quart", "08:45"),
    ("neuf heures et quart", "09:15"),
    ("neuf heures et demie", "09:30"),
    ("a midi", "12:00"),
    ("a dix-huit heures quinze", "18:15"),
])
def test_les_heures_se_lisent(dit, attendu):
    assert analyser(dit)["heure"] == attendu


def test_le_cas_qui_avait_produit_un_creneau_invente():
    """Mesure 14 : « samedi neuf heures moins le quart » etait devenu 9 h 15.
    Ici, c'est lu tel quel — ou pas lu du tout, jamais approxime."""
    charge = analyser("samedi neuf heures moins le quart ca vous irait")
    assert charge["date"] == "2026-09-19"
    assert charge["heure"] == "08:45"


# --- les intentions ---------------------------------------------------------

@pytest.mark.parametrize("dit, intention", [
    ("je voudrais un rendez-vous jeudi", "rdv"),
    ("je dois annuler mon rendez-vous de demain", "annulation"),
    ("est-ce qu'on peut decaler mon rendez-vous a vendredi", "report"),
    ("combien coute un balayage", "question"),
    ("vous etes ouverts samedi", "question"),
])
def test_les_intentions_se_reconnaissent(dit, intention):
    assert analyser(dit)["intention"] == intention


def test_ce_qui_n_est_pas_compris_reste_inconnu():
    """Le moteur hors ligne ne comble pas : c'est meme sa raison d'etre."""
    charge = analyser("PLUTÔT DE M'A ENFIN D'APRÈS MIDI SUS EST POSSIBLE")
    assert charge["intention"] == "inconnu" or charge["heure"] is None


def test_la_confiance_est_franche_ou_nulle():
    charge = analyser("jeudi a quinze heures trente")
    assert charge["confiance"]["date"] >= 0.7
    vide = analyser("bonjour")
    assert vide["confiance"]["date"] == 0.0


# --- il se branche la ou le modele se branche -------------------------------

def test_il_expose_la_meme_interface_qu_un_fournisseur():
    modele = ModeleHorsLigne(aujourd_hui=MARDI)
    rendu = modele.completer([{"role": "system", "content": "consignes"},
                              {"role": "user", "content": "jeudi a quinze heures trente"}],
                             model="ignore", temperature=0)
    import json
    assert set(json.loads(rendu)) >= {"intention", "date", "heure", "confiance"}
