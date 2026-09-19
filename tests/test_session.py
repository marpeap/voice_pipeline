"""La session telephonique : le protocole branche sur le pipeline.

Ce qui est verifie ici tient en une phrase : un appel entier peut se derouler
sans qu'aucun processus externe ne soit lance, sans qu'une trame coupee ne casse
quoi que ce soit, et sans qu'un chiffre compose au clavier ne se perde.
"""

import time

import pytest

from standard.audiosocket import (
    TYPE_AUDIO_8K,
    TYPE_DTMF,
    TYPE_FIN,
    TYPE_UUID,
    Decodeur,
    encoder,
)
from standard.session import SessionTelephonique, reechantillonner


def parole(n, amplitude=8000):
    import struct
    return b"".join(struct.pack("<h", amplitude if i % 2 else -amplitude) for i in range(n))


class AgentFactice:
    """Un agent de test : il rend une phrase, on regarde ce qui est joue."""

    def __init__(self):
        self.entendus = []

    def salutation(self):
        return "Bonjour, assistant automatique."

    def tour(self, transcription, bruite=False):
        self.entendus.append(transcription)
        from standard.appel import Reponse
        return Reponse("question", f"J'ai entendu : {transcription}")


def session(agent=None, moteur=None):
    return SessionTelephonique(
        agent=agent or AgentFactice(),
        transcrire=moteur or (lambda audio, frequence: "une phrase"),
        synthetiser=lambda texte: [texte.encode()],
    )


# --- le reechantillonnage se fait dans le processus (mesure 6) --------------

def test_reechantillonner_ne_lance_aucun_processus(monkeypatch):
    """Mesure 6 : 11 ms de travail reel, mais 45 ms rien que pour lancer ffmpeg.
    Un processus externe par fragment ajoute plus d'un tiers du budget."""
    import subprocess

    def interdit(*args, **kwargs):
        raise AssertionError("un processus externe a ete lance")

    monkeypatch.setattr(subprocess, "run", interdit)
    monkeypatch.setattr(subprocess, "Popen", interdit)
    sortie = reechantillonner(parole(160), 8000, 16000)
    assert len(sortie) == 160 * 2 * 2


def test_reechantillonner_sans_changement_rend_le_meme_audio():
    audio = parole(80)
    assert reechantillonner(audio, 8000, 8000) is audio


def test_reechantillonner_vers_le_bas():
    assert len(reechantillonner(parole(160), 16000, 8000)) == 160


# --- l'appel, de la premiere trame a la derniere ----------------------------

def test_la_salutation_part_des_l_ouverture():
    s = session()
    sortant = s.ouvrir()
    decodeur = Decodeur()
    trames = [t for morceau in sortant for t in decodeur.avaler(morceau)]
    assert trames and all(t.type == TYPE_AUDIO_8K for t in trames)


def test_l_uuid_identifie_l_appel():
    s = session()
    s.ouvrir()
    s.recevoir(encoder(TYPE_UUID, bytes(range(16))))
    assert s.identifiant is not None and len(s.identifiant) == 36


def test_une_trame_coupee_ne_casse_rien():
    s = session()
    s.ouvrir()
    brut = encoder(TYPE_AUDIO_8K, parole(160))
    assert s.recevoir(brut[:5]) == []
    s.recevoir(brut[5:])
    assert s.audio_recu > 0


def test_le_silence_apres_la_parole_declenche_le_tour():
    agent = AgentFactice()
    s = session(agent)
    s.ouvrir()
    for _ in range(10):
        s.recevoir(encoder(TYPE_AUDIO_8K, parole(160)))
    sortant = []
    for _ in range(int(s.silence_de_fin_ms / 20) + 1):
        sortant += s.recevoir(encoder(TYPE_AUDIO_8K, bytes(320)))
    assert agent.entendus == ["une phrase"], "le tour n'a pas ete declenche"
    assert sortant, "rien n'a ete joue en reponse"


def test_le_raccrochage_ferme_la_session():
    s = session()
    s.ouvrir()
    s.recevoir(encoder(TYPE_FIN))
    assert s.fermee is True
    with pytest.raises(RuntimeError):
        s.recevoir(encoder(TYPE_AUDIO_8K, parole(80)))


# --- le clavier, filet de la regle T7 ---------------------------------------

def test_les_chiffres_composes_forment_un_numero():
    """Regle T7 : apres deux echecs sur un numero, on bascule au clavier. Encore
    faut-il ramasser les chiffres — Asterisk les envoie un par un."""
    s = session()
    s.ouvrir()
    s.attendre_un_numero()
    for chiffre in "0612345678":
        s.recevoir(encoder(TYPE_DTMF, chiffre.encode()))
    assert s.numero_compose() == "0612345678"


def test_le_diese_termine_la_saisie_avant_dix_chiffres():
    s = session()
    s.ouvrir()
    s.attendre_un_numero()
    for chiffre in "061234#":
        s.recevoir(encoder(TYPE_DTMF, chiffre.encode()))
    assert s.saisie_terminee is True
    assert s.numero_compose() is None, "six chiffres ne font pas un numero"


def test_l_etoile_efface_la_saisie():
    s = session()
    s.ouvrir()
    s.attendre_un_numero()
    for chiffre in "0612*0687654321":
        s.recevoir(encoder(TYPE_DTMF, chiffre.encode()))
    assert s.numero_compose() == "0687654321"


def test_les_chiffres_hors_saisie_ne_polluent_pas():
    s = session()
    s.ouvrir()
    s.recevoir(encoder(TYPE_DTMF, b"5"))
    assert s.numero_compose() is None


# --- l'interruption (barge-in) ----------------------------------------------
#
# Etat de l'art relevé le 19/09/2026 : écart de reprise de parole de 200 à
# 400 ms, moins de 2 % d'interruptions à tort, et une coupure de la synthèse en
# moins de 60 ms. Le garde-fou le plus efficace est une durée minimale de parole
# avant de couper — il divise par plus de deux les interruptions à tort.

def test_l_agent_se_tait_quand_l_appelant_reprend_la_parole():
    s = session()
    s.ouvrir()
    assert s.en_train_de_parler
    for _ in range(int(s.duree_minimale_interruption_ms / 20) + 1):
        s.recevoir(encoder(TYPE_AUDIO_8K, parole(160)))
    assert not s.en_train_de_parler, "l'agent parle encore alors qu'on lui coupe la parole"
    assert s.interruptions == 1


def test_un_bruit_bref_ne_coupe_pas_la_parole():
    """Un « mm », une porte qui claque, l'écho de notre propre voix sur le
    réseau : rien de tout cela n'est une reprise de parole."""
    s = session()
    s.ouvrir()
    s.recevoir(encoder(TYPE_AUDIO_8K, parole(160)))   # 20 ms
    assert s.en_train_de_parler
    assert s.interruptions == 0


def test_ce_qui_restait_a_dire_est_jete_et_non_repris_plus_tard():
    s = session()
    s.ouvrir()
    assert s.reste_a_emettre > 0
    for _ in range(int(s.duree_minimale_interruption_ms / 20) + 1):
        s.recevoir(encoder(TYPE_AUDIO_8K, parole(160)))
    assert s.reste_a_emettre == 0, "l'agent reprendra sa phrase par-dessus l'appelant"


def test_apres_l_interruption_le_tour_de_l_appelant_est_bien_pris():
    agent = AgentFactice()
    s = session(agent)
    s.ouvrir()
    for _ in range(int(s.duree_minimale_interruption_ms / 20) + 2):
        s.recevoir(encoder(TYPE_AUDIO_8K, parole(160)))
    for _ in range(int(s.silence_de_fin_ms / 20) + 1):
        s.recevoir(encoder(TYPE_AUDIO_8K, bytes(320)))
    assert agent.entendus == ["une phrase"]


# --- le transfert et la preuve de l'annonce ---------------------------------

def test_le_transfert_est_un_signal_et_pas_seulement_une_phrase():
    """Dire « je vous passe quelqu'un » sans rien signaler au bord telephonique,
    c'est raccrocher au nez de l'appelant en musique."""
    class AgentQuiTransfere(AgentFactice):
        def tour(self, transcription, bruite=False):
            from standard.appel import Reponse
            return Reponse("transfert", "Je vous passe quelqu'un du salon.")

    s = session(AgentQuiTransfere())
    s.ouvrir()
    for _ in range(3):
        s.recevoir(encoder(TYPE_AUDIO_8K, parole(160)))
    for _ in range(int(s.silence_de_fin_ms / 20) + 1):
        s.recevoir(encoder(TYPE_AUDIO_8K, bytes(320)))
    assert s.transfert_demande is True


def test_l_annonce_est_prouvable_apres_coup():
    """L'AI Act demande que l'information soit donnee « de facon prouvable ».
    Une annonce prononcee dont il ne reste rien n'est pas une preuve."""
    s = session()
    s.ouvrir()
    preuve = s.preuve_d_annonce
    assert preuve is not None
    assert preuve["formulation"]
    assert preuve["horodatage"].endswith("+00:00") or "T" in preuve["horodatage"]
    assert preuve["conforme"] is True


# --- ce que les mesures imposent, applique par le chemin reel ----------------
#
# La revue du 19/09 : `ecoute.py` et `parole.py` portent le pre-roll, le rapport
# signal/bruit, le delai de garde et le plafond de syntheses — et ne sont
# importes par personne. Les mesures etaient documentees, pas appliquees.

def test_le_rapport_signal_bruit_remonte_jusqu_a_l_agent():
    """Mesure 10 : a 10-15 dB le taux d'erreur double SUR LES ENTITES. L'agent
    doit le savoir pour changer de strategie, pas le decouvrir."""
    vus = []

    class AgentQuiNote(AgentFactice):
        def tour(self, transcription, bruite=False):
            vus.append(bruite)
            return super().tour(transcription, bruite=bruite)

    s = session(AgentQuiNote())
    s.ouvrir()
    # De la parole a peine au-dessus du bruit de fond : ligne bruitee.
    for _ in range(6):
        s.recevoir(encoder(TYPE_AUDIO_8K, parole(160, amplitude=600)))
        s.recevoir(encoder(TYPE_AUDIO_8K, parole(160, amplitude=520)))
    for _ in range(int(s.silence_de_fin_ms / 20) + 1):
        s.recevoir(encoder(TYPE_AUDIO_8K, parole(160, amplitude=300)))
    assert vus and vus[0] is True
    assert s.rsb_db is not None


def test_une_ligne_propre_n_est_pas_marquee_bruitee():
    vus = []

    class AgentQuiNote(AgentFactice):
        def tour(self, transcription, bruite=False):
            vus.append(bruite)
            return super().tour(transcription, bruite=bruite)

    s = session(AgentQuiNote())
    s.ouvrir()
    for _ in range(4):
        s.recevoir(encoder(TYPE_AUDIO_8K, bytes(320)))          # silence franc
    for _ in range(6):
        s.recevoir(encoder(TYPE_AUDIO_8K, parole(160, amplitude=9000)))
    for _ in range(int(s.silence_de_fin_ms / 20) + 1):
        s.recevoir(encoder(TYPE_AUDIO_8K, bytes(320)))
    assert vus and vus[0] is False


def test_la_synthese_est_consommee_paresseusement():
    """Mesure 13 : le premier son doit partir avant que toute la phrase ne soit
    synthetisee. Materialiser d'abord, c'est le defaut du binaire — 372 ms
    contre 162."""
    produits = []

    def synthetiseur_lent(texte):
        for index in range(5):
            produits.append(index)
            yield bytes(320)

    s = SessionTelephonique(agent=AgentFactice(), transcrire=lambda a, f: "",
                            synthetiser=synthetiseur_lent)
    s.ouvrir()
    premier = s.emettre()
    assert premier is not None
    assert len(produits) < 5, "toute la phrase a ete synthetisee avant le premier paquet"


def test_le_clavier_est_branche_sur_l_agent():
    """Règle T7 : `session.py` savait ramasser les touches, et personne ne les
    lui demandait. Relevé par la revue du 19/09."""
    class AgentAvecClavier(AgentFactice):
        def __init__(self):
            super().__init__()
            self.basculer_clavier = None
            self.numeros = []

        def numero_au_clavier(self, numero):
            from standard.appel import Reponse
            self.numeros.append(numero)
            return Reponse("confirmation", "C'est enregistré.")

    agent = AgentAvecClavier()
    s = session(agent)
    s.ouvrir()
    assert callable(agent.basculer_clavier), "l'agent ne peut pas demander le clavier"

    agent.basculer_clavier()
    for chiffre in "0612345678":
        s.recevoir(encoder(TYPE_DTMF, chiffre.encode()))
    assert agent.numeros == ["0612345678"]


# --- la course que les doublures instantanees cachaient ---------------------

def test_une_synthese_lente_ne_casse_pas_l_emission_concurrente():
    """Regression trouvee par la seconde revue (19/09), invisible aux 424 tests.

    Toutes nos doublures synthetisaient en zero milliseconde, donc les deux fils
    ne se croisaient jamais. Avec les 162 ms que le projet a lui-meme mesures,
    le fil de lecture et le fil d'emission entraient ensemble dans le meme
    generateur : « generator already executing », le fil d'emission mourait, et
    l'appel restait ouvert **en silence pour toujours**.
    """
    import threading

    def synthese_lente(texte):
        for _ in range(4):
            time.sleep(0.05)
            yield bytes(320)

    incidents = []
    s = SessionTelephonique(agent=AgentFactice(), transcrire=lambda a, f: "x",
                            synthetiser=synthese_lente)

    def emetteur():
        for _ in range(80):
            try:
                s.emettre()
            except Exception as erreur:      # noqa: BLE001 — c'est ce qu'on teste
                incidents.append(f"{type(erreur).__name__}: {erreur}")
                return
            time.sleep(0.005)

    fil = threading.Thread(target=emetteur, daemon=True)
    fil.start()
    s.ouvrir()
    time.sleep(0.35)
    assert incidents == [], f"course entre les deux fils : {incidents[0]}"


def test_l_emission_et_la_lecture_ne_se_marchent_pas_dessus():
    """Deux fils, deux tours de parole, et rien qui casse."""
    import threading

    def synthese_lente(texte):
        for _ in range(3):
            time.sleep(0.03)
            yield bytes(320)

    s = SessionTelephonique(agent=AgentFactice(), transcrire=lambda a, f: "une phrase",
                            synthetiser=synthese_lente)
    erreurs = []

    def emetteur():
        fin = time.time() + 1.0
        while time.time() < fin:
            try:
                s.emettre()
            except Exception as erreur:      # noqa: BLE001
                erreurs.append(erreur)
                return
            time.sleep(0.004)

    fil = threading.Thread(target=emetteur, daemon=True)
    fil.start()
    s.ouvrir()
    for _ in range(6):
        s.recevoir(encoder(TYPE_AUDIO_8K, parole(160)))
    for _ in range(int(s.silence_de_fin_ms / 20) + 2):
        s.recevoir(encoder(TYPE_AUDIO_8K, bytes(320)))
    time.sleep(0.3)
    assert erreurs == []
