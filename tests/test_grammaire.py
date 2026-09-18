"""Grammaire francaise des nombres — les cas viennent tous de mesures reelles.

Regles : docs/10-GRAMMAIRE-FRANCAISE.md (T1 a T10).
Origine des cas : mesures 3, 7 et 21 de docs/09-L0-MESURES.md. Aucun n'est invente.
"""

import pytest

from standard.grammaire import (
    Lecture,
    lire_numero,
    mots_vers_chiffres,
)


# --- Conversion des nombres ecrits en toutes lettres -------------------------

@pytest.mark.parametrize("dit, attendu", [
    ("zero six douze trente-quatre cinquante-six soixante-dix-huit", "0612345678"),
    ("zero sept quatre-vingt-neuf zero un vingt-trois quarante-cinq", "0789012345"),
    ("zero six zero six zero six zero six zero six", "0606060606"),
    ("zero un quarante-trois vingt-deux onze zero neuf", "0143221109"),
    ("zero six cinquante-cinq soixante-six soixante-dix-sept quatre-vingt-huit", "0655667788"),
    # quatre-vingts au pluriel, tel que Piper le prononce
    ("quatre-vingts", "80"),
    ("soixante et onze", "71"),
    ("quatre-vingt-quatorze", "94"),
])
def test_mots_vers_chiffres(dit, attendu):
    assert mots_vers_chiffres(dit) == attendu


def test_les_composes_ne_se_cassent_pas():
    """« quarante-trois » vaut 43, jamais 4 puis 3 — c'est la faute qui produit
    onze chiffres (mesure 7, regle T8)."""
    assert mots_vers_chiffres("quarante-trois") == "43"
    assert mots_vers_chiffres("quarante trois") == "43"


# --- T1 : ce qu'un numero francais peut etre --------------------------------

@pytest.mark.parametrize("entree, motif", [
    ("0812345678", "refus"),          # 08 : numero special, interdit
    ("0012345678", "refus"),          # second chiffre a zero : impossible (T3)
    ("061234567", "relecture"),       # neuf chiffres
    ("06123456789012", "relecture"),  # trop long pour etre repare
])
def test_numeros_refuses_ou_relus(entree, motif):
    lecture = lire_numero(entree)
    assert lecture.issue == motif, lecture


def test_un_08_se_refuse_des_les_premiers_chiffres():
    """Trouve par la porte : « zero huit douze trente-quatre cinquante-six » ne
    fait que huit chiffres, mais il n'y a aucune raison de le faire repeter —
    on ne rappellera pas un numero special, quelle que soit sa longueur."""
    lecture = lire_numero("zero huit douze trente-quatre cinquante-six")
    assert lecture.issue == "refus"


def test_numero_nominal():
    lecture = lire_numero("zero six douze trente-quatre cinquante-six soixante-dix-huit")
    assert lecture.issue == "accepte"
    assert lecture.numero == "0612345678"


# --- T2 : le zero initial ne se croit jamais --------------------------------

@pytest.mark.parametrize("dit", [
    "mon numero ses heros fit douze trente-quatre cinquante-six soixante-dix-huit",
    "MON NUMERO SES EUROS SIX DOUZE TRENTE-QUATRE CINQUANTE-SIX SOIXANTE-DIX-HUIT",
])
def test_zero_initial_reconstruit(dit):
    """Mesure 3 : le « zero » initial est massacre par tous les moteurs. Neuf
    chiffres lisibles et un debut inintelligible se reconstruisent en 0 + neuf."""
    lecture = lire_numero(dit)
    assert lecture.issue in ("accepte", "relecture")
    if lecture.issue == "accepte":
        assert lecture.numero.startswith("0")
        assert len(lecture.numero) == 10


# --- T5 : format international ----------------------------------------------

def test_format_international():
    lecture = lire_numero("plus trente-trois six douze trente-quatre cinquante-six soixante-dix-huit")
    assert lecture.issue == "accepte"
    assert lecture.numero == "0612345678"


def test_format_international_en_chiffres():
    assert lire_numero("+33 6 12 34 56 78").numero == "0612345678"


# --- T8 : onze chiffres, une seule refusion possible ------------------------

def test_sur_segmentation_reparee_mais_a_confirmer():
    """Mesure 7 : « 01 40 3 22 11 09 » — le moteur a coupe « quarante-trois ».
    Une seule refusion ramene a dix chiffres, donc on propose ET on fait confirmer."""
    lecture = lire_numero("01 40 3 22 11 09")
    assert lecture.issue == "accepte"
    assert lecture.numero == "0143221109"
    assert lecture.confirmation_obligatoire is True
    assert "40" in lecture.explication and "3" in lecture.explication


def test_sur_segmentation_ambigue_ne_devine_pas():
    """Si plusieurs refusions ramenent a dix chiffres, on ne tranche pas."""
    lecture = lire_numero("0 6 1 2 3 4 5 6 7 8 9")
    assert lecture.issue == "relecture"


# --- T9 : un marqueur de correction annule le dernier groupe ----------------

def test_marqueur_non():
    """Mesure 7 : « douze, quatorze, non, quinze, quarante, soixante » est
    parfaitement transcrit — l'echec est a l'interpretation."""
    lecture = lire_numero("zero six douze quatorze non quinze quarante soixante")
    assert lecture.issue == "accepte"
    assert lecture.numero == "0612154060"


def test_marqueur_pardon_sur_le_premier_groupe():
    lecture = lire_numero("zero six pardon zero sept douze trente-quatre cinquante-six soixante-dix-huit")
    assert lecture.issue == "accepte"
    assert lecture.numero == "0712345678"


@pytest.mark.parametrize("marqueur", ["non", "pardon", "plutot", "excusez-moi"])
def test_tous_les_marqueurs(marqueur):
    lecture = lire_numero(f"zero six douze quatorze {marqueur} quinze quarante soixante")
    assert lecture.numero == "0612154060"


# --- T4 : jamais completer un numero trop court -----------------------------

def test_jamais_completer():
    lecture = lire_numero("zero six douze trente-quatre cinquante-six")
    assert lecture.issue == "relecture"
    assert lecture.numero is None


# --- T6 : la relecture est inconditionnelle (mesure 21) ---------------------

def test_relecture_par_groupes_de_deux():
    from standard.grammaire import enoncer_numero
    assert enoncer_numero("0612345678") == "zéro six, douze, trente-quatre, cinquante-six, soixante-dix-huit"


def test_toute_lecture_acceptee_demande_confirmation():
    """Mesure 21 : un moteur qui ecrit des chiffres tranche les ambiguites en
    silence. Il n'y a plus de doute observable, donc la relecture est systematique."""
    for dit in ["0612345678", "zero six douze trente-quatre cinquante-six soixante-dix-huit"]:
        assert lire_numero(dit).relecture is not None
