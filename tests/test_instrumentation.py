"""T6 de `docs/17` — l'instrumentation, dès le premier appel.

Trois manques mesurés le 20/09 :

1. la durée d'un appel était **écrite en dur à zéro** dans le journal — la
   console affichait donc « 0 s » pour tous les appels, et la première règle de
   détection d'échec (raccroché avant dix secondes) ne pouvait pas exister ;
2. aucune latence par tour, alors que `docs/17` en demande cinq : sans elles,
   « l'agent est lent » n'est pas diagnosticable, et la mesure 13 dit que c'est
   le délai avant premier fragment qui signale une machine pleine ;
3. aucune des quatre règles de détection d'échec.
"""

from datetime import date

import pytest

from standard.echecs import detecter_l_echec


# --- les quatre règles ------------------------------------------------------

def test_un_appel_raccroche_avant_dix_secondes_est_un_echec():
    assert detecter_l_echec({"duree_s": 6.0, "tours": []}) == "raccroche_tot"


def test_trois_reformulations_sont_un_echec():
    tours = [{"genre": "reformulation"}] * 3
    assert detecter_l_echec({"duree_s": 60, "tours": tours}) == "reformulations"


def test_un_appel_sans_un_mot_de_l_appelant_est_un_echec():
    tours = [{"genre": "question", "transcription": ""},
             {"genre": "question", "transcription": ""}]
    assert detecter_l_echec({"duree_s": 40, "tours": tours}) == "silence"


def test_une_demande_d_humain_est_un_echec_meme_reussi():
    """Un transfert n'est pas une panne, mais c'est un appel que l'agent n'a
    pas su traiter : il doit se compter, sinon le taux reste flatteur."""
    tours = [{"genre": "question", "transcription": "bonjour"},
             {"genre": "transfert", "transcription": "passez-moi quelqu'un"}]
    assert detecter_l_echec({"duree_s": 30, "tours": tours}) == "demande_humain"


def test_un_appel_qui_aboutit_n_est_pas_un_echec():
    tours = [{"genre": "proposition", "transcription": "jeudi à quinze heures"},
             {"genre": "confirmation", "transcription": "oui"}]
    assert detecter_l_echec({"duree_s": 45, "tours": tours}) is None


# --- ce que la session mesure ----------------------------------------------

def test_chaque_tour_porte_ses_latences_et_son_identifiant():
    import struct

    from standard.audiosocket import TYPE_AUDIO_8K, encoder
    from standard.session import SessionTelephonique

    class AgentFactice:
        memoire = ""

        def salutation(self):
            return "Bonjour, je suis l'assistant automatique."

        def tour(self, transcription, bruite=False):
            from standard.appel import Reponse
            return Reponse("question", "Quel jour vous conviendrait ?")

    session = SessionTelephonique(agent=AgentFactice(),
                                  transcrire=lambda audio, frequence: "jeudi",
                                  synthetiser=lambda texte: [texte.encode()])
    session.ouvrir()
    while session.emettre() is not None:
        pass
    parole = b"".join(struct.pack("<h", 8000 if i % 2 else -8000) for i in range(160))
    for _ in range(10):
        session.recevoir(encoder(TYPE_AUDIO_8K, parole))
    for _ in range(int(session.silence_de_fin_ms / 20) + 2):
        session.recevoir(encoder(TYPE_AUDIO_8K, bytes(320)))

    assert session.mesures, "aucune mesure de tour"
    mesure = session.mesures[-1]
    for cle in ("speech_id", "fin_de_parole_ms", "transcription_ms",
                "agent_ms", "premier_fragment_ms", "total_ms"):
        assert cle in mesure, cle
    assert mesure["total_ms"] >= mesure["transcription_ms"]


def test_la_duree_d_un_appel_n_est_plus_ecrite_en_dur():
    """Elle valait zéro pour tous les appels, et la console l'affichait."""
    import inspect

    from standard import demarrage

    source = inspect.getsource(demarrage)
    assert '"duree_s": 0' not in source
    assert "duree_s" in source


def test_l_appel_archive_porte_son_motif_d_echec_et_ses_mesures(tmp_path):
    """Le journal doit suffire au diagnostic : sans motif ni latences, il faut
    réécouter un appel qu'on n'a pas enregistré."""
    import os
    import socket
    import struct
    import time

    from standard.audiosocket import TYPE_AUDIO_8K, encoder
    from standard.demarrage import construire_serveur

    racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    serveur = construire_serveur({
        "STANDARD_TENANT": "salon-1",
        "STANDARD_PACK": os.path.join(racine, "packs", "coiffure.json"),
        "STANDARD_REPONSES": '{"A1": "Salon Elegance"}',
        "STANDARD_CRENEAUX": "15:30",
        "STANDARD_PORT": "0", "STANDARD_PORT_SANTE": "0",
        "STANDARD_BASE": str(tmp_path / "essai.sqlite3"),
        "STANDARD_STT": "muet", "STANDARD_TTS": "muet",
    })
    serveur.transcrire = lambda audio, frequence: "je voudrais parler à quelqu'un"
    serveur.demarrer()
    try:
        prise = socket.create_connection(("127.0.0.1", serveur.port), timeout=3)
        parole = b"".join(struct.pack("<h", 8000 if i % 2 else -8000) for i in range(160))
        for _ in range(10):
            prise.sendall(encoder(TYPE_AUDIO_8K, parole))
        for _ in range(60):
            prise.sendall(encoder(TYPE_AUDIO_8K, bytes(320)))
        time.sleep(0.6)
        prise.close()
        time.sleep(0.4)
    finally:
        serveur.arreter()

    appels = serveur.journal.lister("salon-1")
    assert appels, "l'appel n'a pas été archivé"
    appel = appels[0]
    assert appel["echec"] in ("raccroche_tot", "demande_humain")
    assert appel["mesures"], "aucune mesure de tour dans le journal"
    assert appel["duree_s"] > 0, "la durée est encore écrite en dur"
