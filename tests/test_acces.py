"""Les accès : clés par locataire, rotation sans coupure, limitation d'usage.

Écarts relevés par la troisième confrontation (19/09) : un service multi-locataire
professionnel porte des **clés par locataire avec rotation à fenêtre de
recouvrement**, une **limitation d'usage par locataire et par adresse**, et une
**piste d'audit append-only**. Nous n'avions rien de tout cela.
"""

import time

import pytest

from standard.acces import (
    CleRefusee,
    Cles,
    Limiteur,
    TropDeDemandes,
)


# --- les clés ---------------------------------------------------------------

def test_une_cle_ouvre_son_locataire_et_lui_seul():
    cles = Cles()
    secret = cles.emettre("salon-1", portees=["agenda:lire"])
    assert cles.verifier(secret).tenant == "salon-1"


def test_le_secret_n_est_jamais_conserve_en_clair():
    """Une base volée ne doit pas livrer les clés de tous les salons."""
    cles = Cles()
    secret = cles.emettre("salon-1")
    assert all(secret not in str(ligne) for ligne in cles.inventaire())


def test_une_cle_inconnue_est_refusee():
    with pytest.raises(CleRefusee):
        Cles().verifier("gsk_inventee")


def test_une_portee_absente_est_refusee():
    cles = Cles()
    secret = cles.emettre("salon-1", portees=["agenda:lire"])
    with pytest.raises(CleRefusee, match="portée"):
        cles.verifier(secret, portee_requise="agenda:ecrire")


def test_une_cle_revoquee_ne_vaut_plus_rien():
    cles = Cles()
    secret = cles.emettre("salon-1")
    cles.revoquer(cles.verifier(secret).identifiant)
    with pytest.raises(CleRefusee):
        cles.verifier(secret)


# --- la rotation ------------------------------------------------------------

def test_la_rotation_laisse_les_deux_cles_valides_un_moment():
    """Sans fenêtre de recouvrement, la rotation coupe les requêtes en vol :
    c'est la panne classique d'une rotation « propre »."""
    cles = Cles()
    ancienne = cles.emettre("salon-1")
    nouvelle = cles.tourner("salon-1", recouvrement_s=60)
    assert cles.verifier(ancienne).tenant == "salon-1"
    assert cles.verifier(nouvelle).tenant == "salon-1"


def test_l_ancienne_cle_expire_a_la_fin_du_recouvrement():
    cles = Cles(horloge=lambda: 1000.0)
    ancienne = cles.emettre("salon-1")
    cles.tourner("salon-1", recouvrement_s=10)
    cles.horloge = lambda: 1011.0
    with pytest.raises(CleRefusee, match="expirée"):
        cles.verifier(ancienne)


def test_la_rotation_ne_touche_pas_aux_autres_locataires():
    cles = Cles()
    autre = cles.emettre("salon-2")
    cles.emettre("salon-1")
    cles.tourner("salon-1", recouvrement_s=0)
    assert cles.verifier(autre).tenant == "salon-2"


# --- la limitation d'usage --------------------------------------------------

def test_un_locataire_ne_peut_pas_saturer_le_service():
    limiteur = Limiteur(par_minute=3, horloge=lambda: 0.0)
    for _ in range(3):
        limiteur.autoriser("salon-1", "10.0.0.1")
    with pytest.raises(TropDeDemandes):
        limiteur.autoriser("salon-1", "10.0.0.1")


def test_la_limite_d_un_locataire_n_affecte_pas_l_autre():
    limiteur = Limiteur(par_minute=1, horloge=lambda: 0.0)
    limiteur.autoriser("salon-1", "10.0.0.1")
    limiteur.autoriser("salon-2", "10.0.0.2")      # ne lève pas


def test_une_adresse_est_limitee_meme_en_changeant_de_locataire():
    """Une seule adresse qui essaie tous les locataires, c'est une attaque, pas
    un usage."""
    limiteur = Limiteur(par_minute=10, par_minute_adresse=2, horloge=lambda: 0.0)
    limiteur.autoriser("salon-1", "10.0.0.9")
    limiteur.autoriser("salon-2", "10.0.0.9")
    with pytest.raises(TropDeDemandes, match="adresse"):
        limiteur.autoriser("salon-3", "10.0.0.9")


def test_la_fenetre_se_libere_avec_le_temps():
    maintenant = [0.0]
    limiteur = Limiteur(par_minute=1, horloge=lambda: maintenant[0])
    limiteur.autoriser("salon-1", "10.0.0.1")
    maintenant[0] = 61.0
    limiteur.autoriser("salon-1", "10.0.0.1")      # ne lève pas


def test_le_refus_dit_quand_reessayer():
    limiteur = Limiteur(par_minute=1, horloge=lambda: 0.0)
    limiteur.autoriser("salon-1", "10.0.0.1")
    with pytest.raises(TropDeDemandes) as erreur:
        limiteur.autoriser("salon-1", "10.0.0.1")
    assert erreur.value.reessayer_dans_s > 0
