"""Les moteurs : brancher la voix réelle, ou dire clairement qu'elle manque.

Le service savait décrocher et répondre, mais `transcrire` rendait une chaîne
vide : il n'y avait aucun chemin, dans le code, pour brancher les moteurs qu'on a
mesurés. C'est ce que ce module répare.

Deux règles, tirées des mesures :
  - **le nom du moteur et ses paramètres vivent en configuration** (mesure 17 :
    le catalogue a bougé trois fois en quarante-huit heures) ;
  - **un moteur absent se dit**, il ne se devine pas : un service qui décroche et
    n'entend rien est pire qu'un service qui refuse de démarrer.
"""

import pytest

from standard.moteurs import (
    MoteurAbsent,
    choisir_transcription,
    choisir_synthese,
    inventaire,
)


class FauxPiper:
    def __init__(self, *args, **kwargs):
        self.dits = []

    def synthesize(self, texte):
        self.dits.append(texte)
        yield type("Fragment", (), {"audio_int16_bytes": b"\x00\x01", "sample_rate": 22050})()


# --- le choix vient de la configuration -------------------------------------

def test_le_moteur_de_transcription_se_choisit_par_son_nom():
    appels = {}

    def faux_distant(audio, frequence, **kw):
        appels["vu"] = (len(audio), frequence)
        return "bonjour"

    transcrire = choisir_transcription({"STANDARD_STT": "essai"},
                                       moteurs={"essai": lambda **kw: faux_distant})
    assert transcrire(b"\x00" * 320, 8000) == "bonjour"
    assert appels["vu"] == (320, 8000)


def test_un_moteur_inconnu_est_refuse_par_son_nom():
    with pytest.raises(MoteurAbsent, match="fantome"):
        choisir_transcription({"STANDARD_STT": "fantome"}, moteurs={})


def test_sans_moteur_configure_le_service_le_dit():
    """Pas de silence poli : décrocher sans entendre est le pire des états.

    Le refus arrive au CHOIX, pas au premier appel — sinon l'inventaire de
    déploiement répond « disponible » pour un moteur qui n'existe pas."""
    with pytest.raises(MoteurAbsent, match="STANDARD_STT"):
        choisir_transcription({}, moteurs={})


def test_le_moteur_muet_est_explicitement_demandable():
    """Il sert à vérifier un déploiement avant d'avoir un STT — mais il faut
    l'avoir demandé."""
    transcrire = choisir_transcription({"STANDARD_STT": "muet"})
    assert transcrire(b"\x00" * 320, 8000) == ""


# --- la synthèse ------------------------------------------------------------

def test_la_synthese_locale_rend_des_fragments():
    synthetiser = choisir_synthese({"STANDARD_TTS": "piper",
                                    "STANDARD_VOIX": "/inexistant.onnx"},
                                   charger_voix=lambda chemin: FauxPiper())
    fragments = list(synthetiser("Bonjour."))
    assert fragments == [b"\x00\x01"]


def test_une_voix_absente_est_signalee_au_demarrage_pas_pendant_l_appel():
    """Découvrir qu'il manque une voix au premier appelant est inacceptable."""
    def charger_qui_echoue(chemin):
        raise FileNotFoundError(chemin)

    with pytest.raises(MoteurAbsent, match="voix"):
        choisir_synthese({"STANDARD_TTS": "piper", "STANDARD_VOIX": "/inexistant.onnx"},
                         charger_voix=charger_qui_echoue)


def test_la_voix_par_defaut_est_celle_qui_a_ete_mesuree():
    """Mesure 22 : siwis rend 6,4 % de WER après le canal contre 20 % pour mls,
    à latence identique. Ce n'est pas un choix de goût."""
    from standard.moteurs import VOIX_PAR_DEFAUT
    assert "siwis" in VOIX_PAR_DEFAUT


def test_la_synthese_muette_existe_pour_les_essais():
    synthetiser = choisir_synthese({"STANDARD_TTS": "muet"})
    assert list(synthetiser("Bonjour.")) == [b""]


# --- l'inventaire -----------------------------------------------------------

def test_l_inventaire_dit_ce_qui_est_disponible_sur_la_machine():
    etat = inventaire({"STANDARD_STT": "muet", "STANDARD_TTS": "muet"})
    assert etat["transcription"]["nom"] == "muet"
    assert etat["synthese"]["nom"] == "muet"
    assert etat["transcription"]["disponible"] is True


def test_l_inventaire_ne_ment_pas_sur_un_moteur_absent():
    etat = inventaire({"STANDARD_STT": "fantome"})
    assert etat["transcription"]["disponible"] is False
    assert "fantome" in etat["transcription"]["detail"]


# --- l'inventaire ne doit pas se rassurer lui-même ---------------------------

def test_sans_moteur_configure_l_inventaire_dit_indisponible():
    """Trouvé en lançant la commande pour de vrai : l'inventaire répondait
    « disponible » alors qu'aucun moteur n'était configuré, parce que le refus
    n'arrivait qu'au premier appel. Un rapport de déploiement qui rassure à tort
    est pire que pas de rapport."""
    etat = inventaire({"STANDARD_TTS": "muet"})
    assert etat["transcription"]["disponible"] is False
    assert "STANDARD_STT" in etat["transcription"]["detail"]


def test_une_bibliotheque_manquante_ne_se_deguise_pas_en_voix_introuvable():
    """Deux causes différentes appellent deux gestes différents : installer une
    dépendance, ou corriger un chemin."""
    def charger_sans_bibliotheque(chemin):
        raise ImportError("No module named 'piper'")

    with pytest.raises(MoteurAbsent, match="install"):
        choisir_synthese({"STANDARD_TTS": "piper", "STANDARD_VOIX": "/x.onnx"},
                         charger_voix=charger_sans_bibliotheque)
