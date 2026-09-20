"""L'appel que personne ne termine — poche, faux numéro, client parti.

Un appelant qui ne dit **rien du tout** ne déclenche aucun tour : la relance
muette suppose qu'on a entendu de la parole. La ligne restait donc ouverte
indéfiniment, avec son fil, sa session et sa place sous le plafond d'appels
simultanés — un téléphone au fond d'une poche pouvait occuper le standard toute
la journée.

Deux bornes, et elles ne se confondent pas :
  - **le silence du début** : personne n'a parlé, on prend congé et on rend la
    ligne ;
  - **la durée totale** : quelque chose est coincé, on rend la ligne aussi.
"""

import struct
import time

import pytest

from standard.audiosocket import TYPE_AUDIO_8K, encoder
from standard.regles import DUREE_MAXIMALE_D_APPEL_S, SILENCE_AVANT_DE_RENDRE_LA_LIGNE_S
from standard.session import SessionTelephonique

PAROLE = b"".join(struct.pack("<h", 8000 if i % 2 else -8000) for i in range(160))


class AgentFactice:
    memoire = ""
    fin_demandee = False

    def salutation(self):
        return "Bonjour, je suis l'assistant automatique."

    def tour(self, transcription, bruite=False):
        from standard.appel import Reponse
        return Reponse("question", "Oui ?")


def session(horloge=None):
    """L'horloge se passe au constructeur : la session date son départ dès sa
    naissance, et la poser après coup comparerait deux horloges."""
    return SessionTelephonique(
        agent=AgentFactice(),
        transcrire=lambda audio, frequence: "une phrase",
        synthetiser=lambda texte: [texte.encode()],
        **({"horloge": horloge} if horloge is not None else {}))


def vider(s):
    while s.emettre() is not None:
        pass


def test_un_silence_complet_finit_par_rendre_la_ligne():
    temps = [1000.0]
    s = session(horloge=lambda: temps[0])
    s.ouvrir()
    vider(s)

    for _ in range(5):
        s.recevoir(encoder(TYPE_AUDIO_8K, bytes(320)))
    assert not s.fin_demandee, "on ne raccroche pas au bout de cent millisecondes"

    temps[0] += SILENCE_AVANT_DE_RENDRE_LA_LIGNE_S + 1
    s.recevoir(encoder(TYPE_AUDIO_8K, bytes(320)))
    assert s.fin_demandee
    assert s.raison_de_fin == "silence"


def test_une_parole_repousse_l_echeance():
    """Quelqu'un qui parle n'est pas un téléphone au fond d'une poche."""
    temps = [1000.0]
    s = session(horloge=lambda: temps[0])
    s.ouvrir()
    vider(s)

    temps[0] += SILENCE_AVANT_DE_RENDRE_LA_LIGNE_S - 1
    for _ in range(10):
        s.recevoir(encoder(TYPE_AUDIO_8K, PAROLE))
    temps[0] += 3
    s.recevoir(encoder(TYPE_AUDIO_8K, bytes(320)))
    assert not s.fin_demandee


def test_un_appel_interminable_est_rendu_aussi():
    """Quelqu'un qui parle sans arrêt pendant dix minutes n'est pas un silence :
    c'est l'autre borne, et le motif doit le dire."""
    temps = [1000.0]
    s = session(horloge=lambda: temps[0])
    s.ouvrir()
    vider(s)

    for _ in range(int(DUREE_MAXIMALE_D_APPEL_S / 10) + 2):
        temps[0] += 10          # il parle toutes les dix secondes
        s.recevoir(encoder(TYPE_AUDIO_8K, PAROLE))
        if s.fin_demandee:
            break
    assert s.fin_demandee
    assert s.raison_de_fin == "trop long"


def test_ces_fins_ne_sont_pas_des_demarchages():
    """La console compte les démarchages filtrés : une poche n'en est pas un."""
    temps = [1000.0]
    s = session(horloge=lambda: temps[0])
    s.ouvrir()
    vider(s)
    temps[0] += SILENCE_AVANT_DE_RENDRE_LA_LIGNE_S + 1
    s.recevoir(encoder(TYPE_AUDIO_8K, bytes(320)))
    assert s.raison_de_fin != "demarchage"


def test_le_serveur_compte_les_lignes_rendues_a_part(tmp_path):
    """Ni un démarchage filtré, ni un appel servi : confondre les trois
    fausserait les trois chiffres que le commerçant regarde."""
    import os
    import socket

    from standard.demarrage import construire_serveur

    racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    serveur = construire_serveur({
        "STANDARD_TENANT": "salon-1",
        "STANDARD_PACK": os.path.join(racine, "packs", "coiffure.json"),
        "STANDARD_REPONSES": '{"A1": "Salon"}',
        "STANDARD_PORT": "0", "STANDARD_PORT_SANTE": "0",
        "STANDARD_BASE": str(tmp_path / "essai.sqlite3"),
        "STANDARD_STT": "muet", "STANDARD_TTS": "muet",
    })
    serveur.demarrer()
    try:
        assert serveur.lignes_rendues == 0
        assert "lignes_rendues" in __import__(
            "standard.sante", fromlist=["etat_du_serveur"]).etat_du_serveur(serveur)
    finally:
        serveur.arreter()
