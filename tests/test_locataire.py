"""Le locataire : du questionnaire au fichier de connaissance de l'agent.

Regles : docs/05. Le commercant ne voit jamais un prompt — il repond a des
questions, et le systeme ecrit le fichier. Deux invariants tiennent tout :
l'interface **remplace le bloc frontmatter, jamais le corps**, et un salon qui ne
repond rien obtient quand meme un agent qui fonctionne.
"""

import json
from pathlib import Path

import pytest

from standard.locataire import (
    Memoire,
    composer_memoire,
    lire_memoire,
    paliers_manquants,
    questions_du_pack,
    reponses_par_defaut,
)

PACKS = Path(__file__).resolve().parents[1] / "packs"


def pack(nom="coiffure"):
    return json.loads((PACKS / f"{nom}.json").read_text())


# --- le questionnaire se derive du pack, il ne se recopie pas ---------------

@pytest.mark.parametrize("nom", ["coiffure", "artisan-depannage", "restaurant"])
def test_chaque_pack_livre_rend_un_questionnaire(nom):
    questions = questions_du_pack(pack(nom))
    assert questions, f"le pack {nom} ne rend aucune question"
    assert all("libelle" in q and "id" in q for q in questions)


def test_les_questions_sortent_dans_l_ordre_des_paliers():
    questions = questions_du_pack(pack())
    paliers = [q["palier"] for q in questions]
    assert paliers == sorted(paliers), "un palier 2 passe avant un palier 0"


def test_un_salon_qui_ne_repond_rien_obtient_un_agent_qui_fonctionne():
    defauts = reponses_par_defaut(pack())
    assert defauts, "aucun defaut derive du pack"
    assert defauts["A3"] == "commune"
    assert "coupe" in defauts["C1"] and "brushing" in defauts["C1"]
    assert defauts["E3"] == "assistant_automatique"


def test_les_questions_critiques_sans_reponse_bloquent_l_activation():
    manquants = paliers_manquants(pack(), reponses={})
    assert "A1" in manquants, "le nom du salon est critique et vide"
    assert paliers_manquants(pack(), reponses_par_defaut(pack()) | {"A1": "Salon X"}) == []


# --- le fichier de connaissance ---------------------------------------------

CORPS = """# Ce qu'il faut savoir

Le balayage se fait uniquement avec Sophie ou Lea.

---

Une ligne de tirets au milieu du corps, pour voir.
"""


def test_le_frontmatter_est_ecrit_et_le_corps_rendu_tel_quel():
    reponses = reponses_par_defaut(pack()) | {"A1": "Salon Elegance"}
    texte = composer_memoire(pack(), reponses, CORPS)
    assert texte.startswith("---\n")
    assert "salon:" in texte and "Salon Elegance" in texte
    assert texte.endswith(CORPS)


def test_relire_rend_exactement_le_corps_d_origine():
    reponses = reponses_par_defaut(pack()) | {"A1": "Salon Elegance"}
    memoire = lire_memoire(composer_memoire(pack(), reponses, CORPS))
    assert memoire.corps == CORPS, "le corps a ete abime par l'aller-retour"


def test_une_reponse_qui_change_ne_touche_pas_au_corps():
    """L'UI remplace le bloc frontmatter, jamais le fichier : le corps Markdown
    n'est JAMAIS reparse ni reecrit (docs/05)."""
    reponses = reponses_par_defaut(pack()) | {"A1": "Salon Elegance"}
    premier = composer_memoire(pack(), reponses, CORPS)
    corps_avant = lire_memoire(premier).corps
    second = composer_memoire(pack(), reponses | {"A1": "Salon Renove"}, corps_avant)
    memoire = lire_memoire(second)
    assert memoire.corps == CORPS
    assert "Salon Renove" in second


def test_l_annonce_figure_toujours_dans_le_frontmatter():
    """E3 est obligatoire et non desactivable : meme sans reponse, la valeur par
    defaut est ecrite. Un pack ne peut pas produire un agent muet sur ce point."""
    texte = composer_memoire(pack(), {}, "")
    assert "annonce" in texte
    assert "assistant_automatique" in texte


def test_les_interdits_du_pack_entrent_dans_la_memoire():
    """Les quatre interdits cables de l'artisan ne sont pas des suggestions."""
    texte = composer_memoire(pack("artisan-depannage"), {}, "")
    memoire = lire_memoire(texte)
    assert memoire.interdits, "aucun interdit reporte"
    assert any("prix total" in i.lower() for i in memoire.interdits)


def test_le_vocabulaire_injecte_suit_les_prestations_cochees():
    """keyterms.groupe3 est indexe par prestation : on n'injecte que ce qui est
    coche, au lieu de deverser tout le lexique du metier."""
    reponses = {"C1": ["coupe"]}
    memoire = lire_memoire(composer_memoire(pack(), reponses, ""))
    assert "coupe homme" in memoire.vocabulaire
    assert "tie and dye" not in memoire.vocabulaire


def test_le_fichier_reste_lisible_par_un_humain():
    texte = composer_memoire(pack(), reponses_par_defaut(pack()) | {"A1": "Salon"}, CORPS)
    assert texte.count("---") >= 2
    assert "\n\n" in texte
