"""La conformité, vérifiée par le produit et non promise par un document.

Trois obligations, et chacune est testable :
  - **annoncer** que l'interlocuteur parle à une machine (AI Act art. 50 §1) ;
  - **ne pas garder** l'audio une fois la transcription faite ;
  - **ne jamais collecter une adresse e-mail à l'oral** — mobile et SMS.

Plus le registre des traitements (RGPD art. 30), qui se **dérive** de la
configuration au lieu d'être un document tenu à part, et donc périmé.
"""

import pytest

from standard.conformite import (
    ControleConformite,
    RegistreDesTraitements,
    est_une_adresse_email,
    verifier_annonce,
)


# --- l'annonce --------------------------------------------------------------

@pytest.mark.parametrize("phrase, conforme", [
    ("Bonjour, Salon Élégance. Je suis l'assistant automatique, je vous écoute.", True),
    ("Bonjour, je suis l'assistant virtuel de Salon Élégance.", True),
    ("Bonjour, Salon Élégance, je vous écoute.", False),
    ("Bonjour.", False),
])
def test_l_annonce_est_verifiee_sur_la_phrase_reelle(phrase, conforme):
    """Mesure 19 : l'annonce survit au canal. Encore faut-il qu'elle soit là."""
    assert verifier_annonce(phrase).conforme is conforme


def test_l_annonce_doit_etre_dans_la_premiere_phrase():
    controle = ControleConformite()
    controle.tour("Bonjour, je vous écoute.")
    controle.tour("Je suis l'assistant automatique, d'ailleurs.")
    assert controle.rapport()["annonce_conforme"] is False


def test_une_annonce_placee_des_l_ouverture_est_conforme():
    controle = ControleConformite()
    controle.tour("Bonjour, assistant automatique du salon, je vous écoute.")
    controle.tour("Quel jour vous conviendrait ?")
    assert controle.rapport()["annonce_conforme"] is True


# --- l'audio ne survit pas à la transcription -------------------------------

def test_l_audio_est_efface_des_que_le_texte_existe():
    controle = ControleConformite()
    controle.audio_recu(b"\x00" * 16000)
    controle.transcrit("je voudrais un rendez-vous")
    assert controle.audio_conserve == 0
    assert controle.rapport()["audio_conserve_octets"] == 0


def test_garder_l_audio_est_un_manquement_visible():
    controle = ControleConformite(effacer_l_audio=False)
    controle.audio_recu(b"\x00" * 800)
    controle.transcrit("texte")
    rapport = controle.rapport()
    assert rapport["audio_conserve_octets"] == 800
    assert "audio" in " ".join(rapport["manquements"])


# --- jamais d'e-mail à l'oral -----------------------------------------------

@pytest.mark.parametrize("dit", [
    "mon email c'est jean arobase exemple point fr",
    "jean.dupont@exemple.fr",
    "j point dupont arrobase gmail point com",
])
def test_une_adresse_dictee_est_reconnue(dit):
    assert est_une_adresse_email(dit) is True


@pytest.mark.parametrize("dit", [
    "je voudrais un rendez-vous jeudi",
    "mon numéro c'est le zéro six douze trente-quatre",
])
def test_une_phrase_ordinaire_n_est_pas_une_adresse(dit):
    assert est_une_adresse_email(dit) is False


def test_une_adresse_dictee_n_est_jamais_enregistree():
    """Jamais de collecte d'e-mail par la voix : un caractère de trop et le SMS
    de confirmation part chez quelqu'un d'autre."""
    controle = ControleConformite()
    controle.transcrit("mon email c'est jean arobase exemple point fr")
    assert controle.rapport()["emails_refuses"] == 1
    assert controle.donnees_collectees == []


def test_un_numero_de_mobile_est_lui_accepte():
    controle = ControleConformite()
    controle.entite("telephone", "0612345678")
    assert controle.donnees_collectees == [("telephone", "0612345678")]


# --- le registre des traitements --------------------------------------------

def test_le_registre_se_derive_de_la_configuration():
    """Un registre tenu à part est un registre périmé. Celui-ci sort des mêmes
    valeurs que le produit."""
    registre = RegistreDesTraitements(
        responsable="Salon Élégance", sous_traitant="Marpeap",
        finalite="prise de rendez-vous par téléphone",
        conservation_jours=90, destinataires=["fournisseur de téléphonie"])
    document = registre.rendre()
    assert "Salon Élégance" in document and "Marpeap" in document
    assert "90 jours" in document
    assert "article 28" in document.lower()


def test_le_registre_nomme_les_categories_reellement_collectees():
    registre = RegistreDesTraitements(responsable="X", sous_traitant="Y",
                                      finalite="Z", conservation_jours=30)
    document = registre.rendre()
    assert "numéro de mobile" in document
    assert "adresse e-mail" not in document, "on ne déclare pas ce qu'on ne collecte pas"


def test_le_registre_dit_que_l_audio_n_est_pas_conserve():
    registre = RegistreDesTraitements(responsable="X", sous_traitant="Y",
                                      finalite="Z", conservation_jours=30)
    assert "audio" in registre.rendre().lower()
