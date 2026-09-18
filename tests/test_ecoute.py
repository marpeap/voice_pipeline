"""L'ecoute : de l'audio au texte, sans perdre le premier mot.

Mesure 9 : un moteur streaming perd le premier mot d'**un enonce sur quatre**
(24 %, contre 5 % pour un decodage de fichier entier) — « Mon numero c'est le
zero six » devient « NUMERO C'EST LE ZERO SIX ». Or c'est la syllabe qui porte le
« zero » d'un numero ou le « non » d'un refus.
Mesure 10 : a 10-15 dB, le WER double et la strategie doit changer.
Mesure 4 : une connexion rouverte coute 2 040 ms, gardee 378 ms.
"""

import pytest

from standard.ecoute import (
    Ecoute,
    ReserveDeConnexions,
    TamponDePreRoll,
    estimer_rsb_db,
)


def bruit(n, amplitude=100):
    return bytes(bytearray([amplitude % 256]) * (2 * n))


def parole(n, amplitude=8000):
    """Un signal franchement au-dessus du bruit de fond."""
    import struct
    return b"".join(struct.pack("<h", amplitude if i % 2 else -amplitude) for i in range(n))


# --- le pre-roll : ce qui sauve le premier mot (mesure 9) -------------------

def test_le_tampon_garde_l_audio_d_avant_le_seuil():
    tampon = TamponDePreRoll(duree_ms=300, taux=8000)
    for _ in range(10):
        tampon.ajouter(bruit(400))          # 50 ms chacun : du silence qui precede
    garde = tampon.vider()
    assert len(garde) == int(0.300 * 8000) * 2, "le pre-roll ne fait pas 300 ms"


def test_le_tampon_ne_grossit_pas_indefiniment():
    tampon = TamponDePreRoll(duree_ms=200, taux=8000)
    for _ in range(100):
        tampon.ajouter(bruit(800))
    assert len(tampon.vider()) <= int(0.200 * 8000) * 2


def test_le_premier_mot_est_transmis_au_moteur():
    """Le flux STT doit etre alimente AVANT que l'appelant ne parle : ce qui est
    entendu commence avant le seuil de declenchement, pas apres."""
    recu = []

    def moteur(flux):
        for morceau in flux:
            recu.append(morceau)
        return "transcription"

    ecoute = Ecoute(moteur=moteur, preroll_ms=100, taux=8000)
    ecoute.ouvrir()
    for _ in range(4):
        ecoute.alimenter(bruit(200))        # avant le seuil
    ecoute.alimenter(parole(800))           # l'appelant parle
    ecoute.alimenter(parole(800))
    resultat = ecoute.fermer()

    assert resultat.texte == "transcription"
    assert len(recu) >= 3, "le moteur n'a pas recu l'audio d'avant le seuil"


# --- le rapport signal/bruit, connu des les premieres secondes (mesure 10) --

def test_le_rsb_est_estime_et_transmis():
    ecoute = Ecoute(moteur=lambda flux: "".join("" for _ in flux) or "texte",
                    preroll_ms=100, taux=8000)
    ecoute.ouvrir()
    ecoute.alimenter(bruit(800, amplitude=2))
    ecoute.alimenter(parole(1600))
    resultat = ecoute.fermer()
    assert resultat.rsb_db is not None
    assert resultat.rsb_db > 0


def test_un_appel_bruite_est_marque_comme_tel():
    """A 10-15 dB, le WER double et l'agent doit changer de strategie — passer au
    clavier pour le numero des le premier essai, au lieu d'attendre deux echecs."""
    ecoute = Ecoute(moteur=lambda flux: [None for _ in flux] and "texte",
                    preroll_ms=50, taux=8000, seuil_bruite_db=15)
    ecoute.ouvrir()
    ecoute.alimenter(parole(800, amplitude=300))
    ecoute.alimenter(parole(800, amplitude=400))
    resultat = ecoute.fermer()
    assert resultat.bruite is True


def test_estimer_rsb_sur_du_silence_ne_plante_pas():
    assert estimer_rsb_db(b"\x00\x00" * 100, b"\x00\x00" * 100) is not None


# --- les connexions s'ouvrent au demarrage, pas pendant l'appel (mesure 4) --

def test_la_reserve_ouvre_tout_au_demarrage():
    ouvertures = []
    reserve = ReserveDeConnexions(fabrique=lambda: ouvertures.append(1) or object(), taille=3)
    reserve.amorcer()
    assert len(ouvertures) == 3


def test_aucune_connexion_n_est_ouverte_pendant_un_appel():
    """2 040 ms contre 378 ms : le premier levier de latence est le client, et il
    est gratuit."""
    ouvertures = []
    reserve = ReserveDeConnexions(fabrique=lambda: ouvertures.append(1) or object(), taille=2)
    reserve.amorcer()
    avant = len(ouvertures)
    with reserve.emprunter():
        pass
    with reserve.emprunter():
        pass
    assert len(ouvertures) == avant, "une connexion a ete ouverte en cours d'appel"


def test_une_connexion_rendue_est_reutilisee():
    reserve = ReserveDeConnexions(fabrique=object, taille=1)
    reserve.amorcer()
    with reserve.emprunter() as premiere:
        identifiant = id(premiere)
    with reserve.emprunter() as seconde:
        assert id(seconde) == identifiant


def test_la_sonde_de_maintien_passe_sur_toutes_les_connexions():
    """Sans sonde, le fournisseur ferme une connexion inactive et le premier
    appel apres un creux repaie les deux secondes."""
    touchees = []
    reserve = ReserveDeConnexions(fabrique=lambda: object(), taille=3,
                                  maintenir=lambda c: touchees.append(c))
    reserve.amorcer()
    reserve.entretenir()
    assert len(touchees) == 3
