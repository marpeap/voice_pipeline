"""Plusieurs salons sur une machine — l'un ne doit pas éteindre les autres.

Le runtime est **mono-locataire par processus** (un salon, un service, un port),
et la base est partagée : c'est ce qui permet à la console d'un salon de voir
ses appels pendant que le standard d'un autre écrit les siens. Deux processus
qui écrivent dans le même fichier SQLite, c'est exactement le cas où l'on
récolte « database is locked » — et un rendez-vous perdu.

Ce que ce fichier vérifie : deux salons qui travaillent en même temps
aboutissent tous les deux, et aucun ne voit les données de l'autre.
"""

import json
import os
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from standard.depot import Depot

RACINE = Path(__file__).resolve().parents[1]


def test_le_journal_est_en_mode_wal(tmp_path):
    """Sans WAL, un lecteur bloque un écrivain : la console d'un salon suffisait
    à faire attendre le standard d'un autre."""
    depot = Depot(str(tmp_path / "essai.sqlite3"))
    with depot._verrou:
        mode = depot._connexion.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode.lower() == "wal"


def test_deux_processus_ecrivent_dans_la_meme_base_sans_se_bloquer(tmp_path):
    """Le cas réel : deux salons, deux services, un fichier."""
    chemin = str(tmp_path / "partagee.sqlite3")
    Depot(chemin)          # crée le schéma

    script = (
        "import sys; sys.path.insert(0, %r)\n"
        "from standard.depot import Depot\n"
        "depot = Depot(%r)\n"
        "acces = depot.pour(sys.argv[1])\n"
        "for i in range(40):\n"
        "    acces.inserer(f'{sys.argv[1]}-{i}', "
        "{'date': '2026-09-17', 'heure': f'{9 + i // 6:02d}:{(i %% 6) * 10:02d}'})\n"
        "print('fini')\n" % (str(RACINE), chemin)
    )
    fichier = tmp_path / "ecrivain.py"
    fichier.write_text(script)

    processus = [subprocess.Popen([sys.executable, str(fichier), salon],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  text=True)
                 for salon in ("salon-1", "salon-2")]
    sorties = [p.communicate(timeout=60) for p in processus]
    for (sortie, erreur), p in zip(sorties, processus):
        assert p.returncode == 0, erreur
        assert "fini" in sortie

    depot = Depot(chemin)
    assert len(depot.lister("salon-1")) == 40
    assert len(depot.lister("salon-2")) == 40


def test_deux_salons_ne_se_prennent_pas_leurs_creneaux(tmp_path):
    """Le même créneau, le même jour, chez deux salons : les deux doivent
    aboutir. L'unicité porte sur (locataire, date, heure), pas sur (date, heure)."""
    depot = Depot(str(tmp_path / "essai.sqlite3"))
    depot.pour("salon-1").inserer("cle-1", {"date": "2026-09-17", "heure": "15:30"})
    depot.pour("salon-2").inserer("cle-1", {"date": "2026-09-17", "heure": "15:30"})
    assert len(depot.lister("salon-1")) == 1
    assert len(depot.lister("salon-2")) == 1


def test_l_unite_systemd_est_un_gabarit_par_salon():
    """Un fichier d'unité figé ne sert qu'un salon : le deuxième s'installe en
    recopiant à la main, et les deux divergent au premier changement."""
    unite = (RACINE / "deploiement" / "standard@.service").read_text()
    assert "%i" in unite, "l'unité ne porte pas le nom du salon"
    assert "STANDARD_TENANT" in unite


# --- un salon saturé ne doit pas saturer la machine -------------------------

def serveur_bride(maximum):
    from standard.serveur import ServeurAudioSocket

    class AgentLent:
        memoire = ""

        def salutation(self):
            return "Bonjour."

        def tour(self, transcription, bruite=False):
            from standard.appel import Reponse
            return Reponse("question", "Oui ?")

    serveur = ServeurAudioSocket(
        fabrique_agent=lambda: AgentLent(),
        transcrire=lambda audio, frequence: "",
        synthetiser=lambda texte: [b"\x00" * 320],
        port=0, appels_simultanes_max=maximum)
    serveur.demarrer()
    return serveur


def test_au_dela_du_plafond_la_ligne_est_rendue_tout_de_suite():
    """Au-delà, le bord téléphonique doit pouvoir basculer sur le poste du
    salon : mieux vaut une ligne rendue qu'un appel qui grésille."""
    import socket as s
    import time

    serveur = serveur_bride(2)
    prises = []
    try:
        for _ in range(2):
            prises.append(s.create_connection(("127.0.0.1", serveur.port), timeout=3))
        for _ in range(50):
            if serveur.appels_en_cours == 2:
                break
            time.sleep(0.05)

        refusee = s.create_connection(("127.0.0.1", serveur.port), timeout=3)
        refusee.settimeout(3)
        assert refusee.recv(4096) == b"", "la ligne en trop n'a pas été rendue"
        prises.append(refusee)
        assert serveur.appels_refuses == 1
    finally:
        for prise in prises:
            prise.close()
        serveur.arreter()


def test_sans_plafond_rien_ne_change():
    serveur = serveur_bride(None)
    try:
        assert serveur.appels_simultanes_max is None
    finally:
        serveur.arreter()
