"""Ce que l'agent sait déjà, et qu'il ne disait pas.

Banc du 19/09 : à « je voulais connaître vos horaires », l'agent répondait
« Que puis-je faire pour vous ? » alors que la réponse était dans sa fiche.
"""

from standard.fiche import repondre

FICHE = {"horaires": {"ouverture": {
    "mardi": ["09:00-19:00"], "mercredi": ["09:00-19:00"],
    "jeudi": ["09:00-19:00"], "vendredi": ["09:00-19:00"],
    "samedi": ["09:00-18:00"]}}}


def test_les_horaires_se_disent_depuis_la_fiche():
    dit = repondre("vous êtes ouverts à quelles heures", FICHE)
    assert "du mardi au vendredi de 9 h à 19 h" in dit
    assert "le samedi de 9 h à 18 h" in dit


def test_les_jours_de_memes_horaires_sont_regroupes():
    """Cinq phrases d'horaires ne s'écoutent pas : on regroupe (Miller, 4±1)."""
    dit = repondre("vos horaires", FICHE)
    assert dit.count("de 9 h") == 2


def test_deux_jours_contigus_se_disent_avec_et():
    fiche = {"horaires": {"ouverture": {"mardi": ["09:00-12:00"],
                                        "mercredi": ["09:00-12:00"]}}}
    assert "le mardi et le mercredi de 9 h à 12 h" in repondre("vos horaires", fiche)


def test_une_journee_en_deux_plages_se_dit_en_entier():
    fiche = {"horaires": {"ouverture": {"jeudi": ["09:00-12:00", "14:00-19:00"]}}}
    dit = repondre("vous ouvrez quand", fiche)
    assert "de 9 h à 12 h" in dit and "de 14 h à 19 h" in dit


def test_sans_horaires_dans_la_fiche_l_agent_ne_les_invente_pas():
    dit = repondre("vos horaires d'ouverture", {})
    assert "quelqu'un du salon" in dit
    assert "9 h" not in dit


def test_un_prix_non_saisi_ne_s_invente_jamais():
    """Interdit du pack : ne jamais annoncer un prix que le salon n'a pas saisi.

    Sans réponse à la question C2, le salon est réputé ne pas vouloir que
    l'agent annonce les prix : il oriente, et ne cite aucun montant."""
    dit = repondre("c'est combien coûte une coupe", FICHE)
    assert "quelqu'un du salon" in dit
    assert not any(caractere.isdigit() for caractere in dit)


def test_une_demande_de_rendez_vous_n_est_pas_une_question_de_fiche():
    assert repondre("je voudrais un rendez-vous jeudi", FICHE) is None


def test_la_reponse_se_termine_par_une_relance():
    """Une confirmation n'est jamais un cul-de-sac : on propose la suite."""
    assert repondre("vos horaires", FICHE).rstrip().endswith("?")
