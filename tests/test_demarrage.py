"""Le démarrage en exploitation : configuration par l'environnement, arrêt propre.

Un service qu'on ne peut pas lancer avec des variables d'environnement et arrêter
proprement n'est pas exploitable — il est démontrable, ce qui n'est pas la même
chose.
"""

import json
import os
from pathlib import Path

import pytest

from standard.demarrage import (
    configuration_depuis_environnement,
    construire_serveur,
    verifier_le_deploiement,
)

RACINE = Path(__file__).resolve().parents[1]


def environnement(**remplacements):
    base = {
        "STANDARD_TENANT": "salon-1",
        "STANDARD_PACK": str(RACINE / "packs" / "coiffure.json"),
        "STANDARD_REPONSES": json.dumps({"A1": "Salon Élégance"}),
        "STANDARD_CRENEAUX": "09:00,09:45,10:30,14:00,15:30",
        "STANDARD_JOURS_FERMES": "6,0",
        "STANDARD_PORT": "0",
        "STANDARD_BASE": ":memory:",
    }
    base.update(remplacements)
    return base


def test_la_configuration_se_lit_dans_l_environnement():
    config = configuration_depuis_environnement(environnement())
    assert config.tenant == "salon-1"
    assert "15:30" in config.creneaux
    assert config.jours_fermes == (6, 0)


def test_une_variable_obligatoire_manquante_est_dite_par_son_nom():
    """« configuration invalide » ne se répare pas. « STANDARD_PACK manque », si."""
    incomplet = environnement()
    del incomplet["STANDARD_PACK"]
    with pytest.raises(ValueError, match="STANDARD_PACK"):
        configuration_depuis_environnement(incomplet)


def test_les_creneaux_mal_formes_sont_refuses_au_demarrage():
    """Mieux vaut refuser de démarrer que décrocher avec un agenda faux."""
    with pytest.raises(ValueError, match="créneau"):
        configuration_depuis_environnement(environnement(STANDARD_CRENEAUX="9h,midi"))


def test_le_modele_et_ses_parametres_viennent_aussi_de_l_environnement():
    config = configuration_depuis_environnement(environnement(
        STANDARD_MODELE="un-modele",
        STANDARD_PARAMETRES=json.dumps({"temperature": 0.2})))
    assert config.modele == "un-modele"
    assert config.parametres["temperature"] == 0.2


# --- la vérification de déploiement -----------------------------------------

def test_la_verification_dit_ce_qui_va_et_ce_qui_ne_va_pas():
    rapport = verifier_le_deploiement(environnement())
    assert rapport["pack_valide"] is True
    assert rapport["questions_manquantes"] == []
    assert rapport["pret"] is True


def test_un_agent_incomplet_n_est_pas_pret():
    rapport = verifier_le_deploiement(environnement(STANDARD_REPONSES="{}"))
    assert rapport["pret"] is False
    assert "A1" in rapport["questions_manquantes"]


# --- le serveur ---------------------------------------------------------------

def test_le_serveur_se_construit_et_s_arrete_proprement():
    serveur = construire_serveur(environnement())
    serveur.demarrer()
    try:
        assert serveur.port > 0
    finally:
        serveur.arreter()
    assert serveur.appels_en_cours == 0


def test_sans_cle_d_api_le_service_tourne_quand_meme():
    """Le moteur hors ligne prend le relais : un service qui refuse de démarrer
    faute de clé est un service qu'on ne peut pas essayer."""
    serveur = construire_serveur(environnement())
    serveur.demarrer()
    serveur.arreter()


# --- les fichiers de déploiement --------------------------------------------

def test_le_plan_de_numerotation_restreint_les_codecs():
    """Relevé le 19/09 : restreindre les codecs (alaw, ulaw, slin16) évite les
    problèmes de négociation, première cause d'appels muets."""
    conf = (RACINE / "deploiement" / "pjsip.conf").read_text()
    assert "allow=" in conf
    assert "ulaw" in conf or "alaw" in conf
    assert "disallow=all" in conf


def test_le_plan_de_numerotation_appelle_audiosocket_avec_un_uuid():
    plan = (RACINE / "deploiement" / "extensions.conf").read_text()
    assert "AudioSocket(" in plan
    assert "UUID" in plan or "uuid" in plan


def test_l_unite_systemd_redemarre_le_service():
    unite = (RACINE / "deploiement" / "standard.service").read_text()
    assert "Restart=" in unite


@pytest.mark.parametrize("durcissement, degat", [
    ("MemoryDenyWriteExecute", "tue ONNX, donc le detecteur de parole"),
    ("RestrictRealtime", "introduit de la gigue audio"),
])
def test_les_durcissements_qui_cassent_l_audio_ne_sont_pas_actifs(durcissement, degat):
    """On verifie la DIRECTIVE, pas le mot : le fichier a le droit d'expliquer
    pourquoi elle est absente, et il vaut mieux qu'il l'explique."""
    lignes = (RACINE / "deploiement" / "standard.service").read_text().splitlines()
    actives = [l.strip() for l in lignes if not l.strip().startswith((";", "#"))]
    assert not any(l.startswith(f"{durcissement}=") for l in actives), degat
