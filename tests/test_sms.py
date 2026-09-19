"""Le SMS de confirmation — le premier poste de coût, et un piège réglementaire.

Relevé le 19/09/2026 : un rappel ou une confirmation de rendez-vous est un SMS
**transactionnel** — ni opt-in marketing, ni mention STOP, ni restriction
d'horaire. Mais **une seule phrase promotionnelle le fait basculer** dans le
régime commercial, où l'absence de STOP coûte 750 € par message.

L'expéditeur alphanumérique doit par ailleurs correspondre au nom commercial du
salon (charte AF2M du 1er mars 2026), et il est limité à onze caractères.
"""

import pytest

from standard.sms import (
    MessageRefuse,
    composer_confirmation,
    compter_segments,
    expediteur_valide,
    verifier_message,
)

RDV = {"date": "2026-09-17", "heure": "15:30", "prestation": "coupe",
       "salon": "Salon Élégance"}


# --- ce que le message dit --------------------------------------------------

def test_la_confirmation_porte_le_jour_le_quantieme_et_l_heure():
    """Règle E1 (mesure 19) : le quantième seul est le mot le plus fragile.
    À l'écrit il n'est pas fragile, mais le client compare avec ce qu'il a
    entendu — les deux doivent se ressembler."""
    message = composer_confirmation(RDV)
    assert "jeudi" in message.lower()
    assert "17" in message and "septembre" in message.lower()
    assert "15h30" in message or "15 h 30" in message


def test_la_confirmation_nomme_le_salon():
    assert "Salon Élégance" in composer_confirmation(RDV)


def test_la_confirmation_tient_en_un_seul_sms():
    """Deux segments, c'est deux fois le prix — et le SMS est déjà le premier
    poste de coût du produit, devant l'intelligence artificielle."""
    assert compter_segments(composer_confirmation(RDV)) == 1


# --- transactionnel ou commercial -------------------------------------------

def test_un_rappel_de_rendez_vous_est_transactionnel():
    verdict = verifier_message(composer_confirmation(RDV))
    assert verdict.nature == "transactionnel"
    assert verdict.stop_requis is False
    assert verdict.horaires_imposes is False


@pytest.mark.parametrize("phrase", [
    "Profitez de -20% sur votre prochaine couleur !",
    "Découvrez nos nouvelles offres du moment",
    "Parrainez une amie et gagnez un soin gratuit",
])
def test_une_phrase_promotionnelle_fait_basculer_le_message(phrase):
    """Le piège coûte 750 € par message : une promo glissée dans une
    confirmation transforme tout l'envoi en prospection."""
    verdict = verifier_message(composer_confirmation(RDV) + " " + phrase)
    assert verdict.nature == "commercial"
    assert verdict.stop_requis is True
    assert verdict.horaires_imposes is True


def test_un_message_commercial_sans_stop_est_refuse():
    with pytest.raises(MessageRefuse, match="STOP"):
        verifier_message("Profitez de -20% cette semaine", exiger_conformite=True)


def test_un_message_commercial_avec_stop_passe():
    verdict = verifier_message("Profitez de -20% cette semaine. STOP au 36111",
                               exiger_conformite=True)
    assert verdict.nature == "commercial"


# --- l'expéditeur -----------------------------------------------------------

@pytest.mark.parametrize("nom, valide", [
    ("SalonEleg", True),
    ("Salon Élégance", False),      # trop long, et accentué
    ("36111", False),               # un numéro court n'est pas un nom de marque
    ("PROMO2026", False),           # ne correspond à aucun nom commercial
])
def test_l_expediteur_doit_ressembler_au_nom_du_salon(nom, valide):
    assert expediteur_valide(nom, "Salon Élégance") is valide


def test_un_expediteur_trop_long_est_refuse():
    assert expediteur_valide("SalonElegance", "Salon Élégance") is False


# --- le coût ----------------------------------------------------------------

def test_un_caractere_hors_alphabet_gsm_double_la_facture():
    """« œ » n'est pas dans l'alphabet GSM. La capacité tombe de 160 à 70
    caractères : un message ordinaire d'une centaine de signes passe alors de un
    à deux segments — le prix double pour une lettre.

    (Premier jet de ce test : je comparais un message de 64 signes, qui tient
    dans les 70 de l'UCS-2 et ne montrait donc rien. C'est la longueur ordinaire
    d'un message qui rend le piège visible.)"""
    ordinaire = ("Salon Elegance : rendez-vous confirme jeudi 17 septembre a 15h30 "
                 "(coupe). Pour annuler, rappelez-nous.")
    assert 70 < len(ordinaire) <= 160
    assert compter_segments(ordinaire) == 1
    assert compter_segments(ordinaire + " œ") == 2


def test_un_message_trop_long_est_compte_en_plusieurs_segments():
    assert compter_segments("a" * 161) == 2
    assert compter_segments("a" * 400) == 3
