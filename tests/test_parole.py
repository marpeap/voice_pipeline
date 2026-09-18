"""La parole : le dernier metre, celui que l'appelant entend.

Mesure 13 : le TTS fixe la capacite d'une machine, et il la fixe **en latence**
— 162 ms avant le premier son a un flux, 614 ms a six, pendant que le processeur
reste bas. Mesures 14 et 20 : le premier token du modele arrive a 935 ms au p90
et 8 751 ms au pire, donc le silence n'est pas une hypothese d'ecole.
"""

import threading
import time

import pytest

from standard.parole import DelaiDeGarde, FileDeSynthese, Parole


def synthetiseur_factice(duree_avant_premier=0.0, fragments=3):
    """Un TTS de test : rend des fragments, apres un delai qu'on choisit."""
    def synthetiser(texte):
        time.sleep(duree_avant_premier)
        for i in range(fragments):
            yield f"{texte}|{i}".encode()
    return synthetiser


# --- la file bornee (mesure 13) ---------------------------------------------

def test_la_file_borne_les_syntheses_simultanees():
    """Sans borne, le dixieme appel degrade les neuf autres. Avec borne, il
    attend quelques dizaines de millisecondes et personne ne s'en apercoit."""
    file = FileDeSynthese(parallelisme=4)
    simultanees = []
    maximum = [0]
    verrou = threading.Lock()

    def travail():
        with file.place():
            with verrou:
                simultanees.append(1)
                maximum[0] = max(maximum[0], len(simultanees))
            time.sleep(0.05)
            with verrou:
                simultanees.pop()

    fils = [threading.Thread(target=travail) for _ in range(10)]
    for f in fils:
        f.start()
    for f in fils:
        f.join()
    assert maximum[0] <= 4, f"{maximum[0]} syntheses simultanees, le maximum est 4"


def test_la_file_sert_tout_le_monde():
    file = FileDeSynthese(parallelisme=2)
    servis = []
    fils = []
    for i in range(6):
        def travail(i=i):
            with file.place():
                servis.append(i)
        fils.append(threading.Thread(target=travail))
    for f in fils:
        f.start()
    for f in fils:
        f.join()
    assert sorted(servis) == list(range(6))


# --- le delai de garde (mesures 14 et 20) -----------------------------------

def test_le_delai_de_garde_parle_plutot_que_de_laisser_le_silence():
    garde = DelaiDeGarde(seuil_ms=50)
    dit = []
    lent = (x for x in [])   # rien ne vient

    def producteur_lent():
        time.sleep(0.2)
        return "La réponse arrive enfin."

    resultat = garde.attendre(producteur_lent, sur_attente=dit.append)
    assert dit, "l'agent est reste muet plus longtemps que le seuil"
    assert "vérifie" in dit[0].lower()
    assert resultat == "La réponse arrive enfin."


def test_pas_de_remplissage_quand_la_reponse_est_rapide():
    garde = DelaiDeGarde(seuil_ms=200)
    dit = []
    resultat = garde.attendre(lambda: "Tout de suite.", sur_attente=dit.append)
    assert dit == [], "l'agent a parle pour ne rien dire"
    assert resultat == "Tout de suite."


def test_le_remplissage_ne_se_repete_jamais_mot_pour_mot():
    """Regle de la mesure 16 : deux fois la meme phrase, c'est une boucle."""
    garde = DelaiDeGarde(seuil_ms=10)
    dits = []
    for _ in range(3):
        garde.attendre(lambda: time.sleep(0.05) or "ok", sur_attente=dits.append)
    assert len(dits) == len(set(dits)), dits


# --- la metrique qui dit qu'une machine est pleine (mesure 13) --------------

def test_le_delai_avant_premier_fragment_est_mesure():
    parole = Parole(synthetiseur_factice(duree_avant_premier=0.03), file=FileDeSynthese(2))
    fragments = list(parole.dire("Bonjour, assistant automatique du salon."))
    assert len(fragments) == 3
    assert parole.dernier_premier_fragment_ms >= 25
    assert parole.mesures, "aucune mesure enregistree"


def test_les_mesures_s_accumulent_pour_la_supervision():
    parole = Parole(synthetiseur_factice(), file=FileDeSynthese(2))
    for _ in range(3):
        list(parole.dire("Une phrase."))
    assert len(parole.mesures) == 3
    assert parole.p50_premier_fragment_ms is not None


def test_la_synthese_est_rendue_en_flux():
    """Le binaire synthetisait la phrase entiere avant d'ecrire : 372 ms contre
    162 ms par l'API en flux (mesure 13). On ne materialise jamais le tout."""
    parole = Parole(synthetiseur_factice(fragments=5), file=FileDeSynthese(2))
    flux = parole.dire("Phrase.")
    premier = next(flux)
    assert premier.endswith(b"|0")
    reste = list(flux)
    assert len(reste) == 4
