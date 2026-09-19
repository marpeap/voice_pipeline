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
    rapport = verifier_le_deploiement(environnement(STANDARD_STT="muet",
                                                    STANDARD_TTS="muet"))
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


def test_pret_veut_dire_capable_de_decrocher_et_d_entendre():
    """Trouvé en lisant la sortie réelle : le rapport disait « prêt » alors
    qu'aucun moteur de transcription n'était configuré. Un déploiement « prêt »
    qui décroche sans entendre est exactement le piège que ce rapport doit
    éviter."""
    sans_moteur = environnement()
    sans_moteur.pop("STANDARD_STT", None)
    rapport = verifier_le_deploiement(sans_moteur)
    assert rapport["pret"] is False
    assert rapport["questions_manquantes"] == [], "ce n'est pas le pack qui manque"


def test_avec_les_moteurs_muets_le_deploiement_est_pret():
    rapport = verifier_le_deploiement(environnement(STANDARD_STT="muet",
                                                    STANDARD_TTS="muet"))
    assert rapport["pret"] is True


def test_les_fabrications_simultanees_sont_bornees():
    """Mesure 13 : au-delà de quatre synthèses simultanées, le premier son passe
    400 ms sur une machine à quatre cœurs.

    Ce test mesurait auparavant la concurrence pendant la **lecture** — et il
    passait, parce que le jeton était gardé jusqu'à la fin de la phrase. C'était
    le mauvais invariant : borner la lecture fait attendre le cinquième appelant
    en silence. Ce qu'il faut borner, c'est la fabrication.
    """
    import threading
    import time

    from standard.demarrage import _synthese_tolerante

    en_cours, maximum, verrou = [], [0], threading.Lock()

    def fabrique(texte):
        for _ in range(2):
            with verrou:
                en_cours.append(1)
                maximum[0] = max(maximum[0], len(en_cours))
            time.sleep(0.02)
            with verrou:
                en_cours.pop()
            yield b"x"

    synthetiser = _synthese_tolerante(environnement(STANDARD_TTS="muet",
                                                    STANDARD_SYNTHESES="2"),
                                      fabrique=lambda: fabrique)

    fils = [threading.Thread(target=lambda: list(synthetiser("bonjour")))
            for _ in range(6)]
    for fil in fils:
        fil.start()
    for fil in fils:
        fil.join()
    assert maximum[0] <= 2, f"{maximum[0]} fabrications simultanées, le plafond est 2"


def test_le_jeton_de_synthese_est_rendu_entre_deux_fragments():
    """Seconde revue (19/09) : le jeton était pris au premier fragment et rendu
    à l'épuisement du générateur — c'est-à-dire à la fin de la **lecture** de la
    phrase, puisque les paquets sont consommés au rythme de 20 ms. Le plafond de
    synthèses devenait un plafond d'appels qui parlent, et le cinquième appelant
    décrochait sur plusieurs secondes de silence.

    Ce qui doit être borné, c'est la **fabrication** — elle seule coûte du
    processeur (mesure 13)."""
    import threading
    import time

    from standard.demarrage import _synthese_tolerante

    en_fabrication, maximum, verrou = [], [0], threading.Lock()

    def fabrique_lente(texte):
        for _ in range(3):
            with verrou:
                en_fabrication.append(1)
                maximum[0] = max(maximum[0], len(en_fabrication))
            time.sleep(0.02)                  # fabrication
            with verrou:
                en_fabrication.pop()
            yield b"x"

    env = environnement(STANDARD_TTS="muet", STANDARD_SYNTHESES="2")
    synthetiser = _synthese_tolerante(env, fabrique=lambda: fabrique_lente)

    debuts = {}

    def lire(index):
        source = synthetiser("bonjour")
        debut = time.perf_counter()
        premier = next(source)
        debuts[index] = time.perf_counter() - debut
        for _ in source:
            time.sleep(0.05)                  # lecture, au rythme du canal
        assert premier == b"x"

    fils = [threading.Thread(target=lire, args=(i,)) for i in range(6)]
    for fil in fils:
        fil.start()
    for fil in fils:
        fil.join()

    assert maximum[0] <= 2, f"{maximum[0]} fabrications simultanées, le plafond est 2"
    # Et surtout : personne n'attend la LECTURE des autres pour commencer à parler.
    assert max(debuts.values()) < 0.25, (
        f"le dernier appelant a attendu {max(debuts.values()):.2f} s "
        "avant le premier son : le plafond borne la lecture, pas la fabrication")


def test_sans_expediteur_declare_aucun_sms_n_est_promis():
    """Seconde revue (19/09) : `envoyeur_sms` n'était posé nulle part, donc la
    promesse conditionnelle était conditionnée à une condition toujours fausse —
    une réparation faite par le bas."""
    from standard.demarrage import _envoyeur_sms

    config = configuration_depuis_environnement(environnement())
    assert _envoyeur_sms(environnement(), config) is None


def test_un_expediteur_declare_branche_l_envoyeur():
    from standard.demarrage import _envoyeur_sms

    env = environnement(STANDARD_SMS_EXPEDITEUR="SalonEleg",
                        STANDARD_SMS_NOM="Salon Élégance")
    config = configuration_depuis_environnement(env)
    assert _envoyeur_sms(env, config) is not None


def test_un_expediteur_invalide_ne_branche_rien():
    """Un expéditeur refusé par l'opérateur ferait tomber TOUS les messages :
    mieux vaut n'en promettre aucun que les perdre tous."""
    from standard.demarrage import _envoyeur_sms

    env = environnement(STANDARD_SMS_EXPEDITEUR="PROMO2026",
                        STANDARD_SMS_NOM="Salon Élégance")
    config = configuration_depuis_environnement(env)
    assert _envoyeur_sms(env, config) is None
