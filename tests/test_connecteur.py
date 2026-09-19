"""Le connecteur : brancher l'agent sur le logiciel que le commerçant utilise déjà.

C'est la promesse du produit — « un greffon branchable sur n'importe quelle
application » — et c'est aussi là qu'on peut faire le plus de dégâts : une
écriture rejouée crée un doublon, un refus mal lu fait promettre l'impossible.

Contrat : `docs/04-CONNECTEUR-CRENOLO.md`.
"""

import pytest

from standard.connecteur import (
    ConnecteurHttp,
    ConnecteurInterne,
    Indisponible,
    Refus,
)
from standard.depot import Depot


RDV = {"date": "2026-09-17", "heure": "15:30", "prestation": "coupe",
       "telephone": "0612345678"}


# --- le connecteur interne : celui qui marche sans personne -----------------

def test_l_agenda_interne_reserve_et_relit():
    connecteur = ConnecteurInterne(Depot(":memory:"), tenant="salon-1",
                                   creneaux=["09:00", "15:30"])
    reference = connecteur.reserver("cle-1", RDV)
    assert connecteur.relire(reference)["heure"] == "15:30"


def test_l_agenda_interne_refuse_un_creneau_deja_pris():
    connecteur = ConnecteurInterne(Depot(":memory:"), tenant="salon-1",
                                   creneaux=["15:30"])
    connecteur.reserver("cle-1", RDV)
    with pytest.raises(Refus) as refus:
        connecteur.reserver("cle-2", RDV)
    assert refus.value.code == "creneau_pris"


def test_l_agenda_interne_refuse_un_creneau_inexistant():
    connecteur = ConnecteurInterne(Depot(":memory:"), tenant="salon-1",
                                   creneaux=["09:00"])
    with pytest.raises(Refus) as refus:
        connecteur.reserver("cle-1", RDV)
    assert refus.value.code == "creneau_inconnu"


def test_les_disponibilites_viennent_du_connecteur():
    connecteur = ConnecteurInterne(Depot(":memory:"), tenant="salon-1",
                                   creneaux=["09:00", "15:30"])
    connecteur.reserver("cle-1", RDV)
    assert connecteur.disponibilites("2026-09-17") == ["09:00"]


# --- le connecteur HTTP -----------------------------------------------------

class TransportFactice:
    """Un transport de test : on choisit les réponses, on relit les requêtes."""

    def __init__(self, reponses):
        self.reponses = list(reponses)
        self.requetes = []

    def __call__(self, methode, chemin, corps=None, entetes=None, delai=None):
        self.requetes.append({"methode": methode, "chemin": chemin, "corps": corps,
                              "entetes": entetes or {}, "delai": delai})
        reponse = self.reponses.pop(0) if self.reponses else (200, {})
        if isinstance(reponse, Exception):
            raise reponse
        return reponse


def connecteur_http(reponses):
    transport = TransportFactice(reponses)
    return ConnecteurHttp(transport, base="https://exemple.fr", cle_api="secrete"), transport


def test_la_cle_d_idempotence_part_dans_l_entete():
    """Modèle Stripe : la clé voyage dans l'en-tête, elle n'est pas un champ du
    corps qu'un serveur peut ignorer sans le dire."""
    connecteur, transport = connecteur_http([(201, {"id": "rdv-9"})])
    connecteur.reserver("cle-1", RDV)
    assert transport.requetes[0]["entetes"]["Idempotency-Key"] == "cle-1"


def test_la_cle_d_api_ne_se_promene_pas_dans_l_url():
    connecteur, transport = connecteur_http([(201, {"id": "rdv-9"})])
    connecteur.reserver("cle-1", RDV)
    assert "secrete" not in transport.requetes[0]["chemin"]
    assert transport.requetes[0]["entetes"]["X-Api-Key"] == "secrete"


def test_un_rejeu_ne_cree_pas_un_second_rendez_vous():
    connecteur, transport = connecteur_http([(201, {"id": "rdv-9"}), (200, {"id": "rdv-9"})])
    premiere = connecteur.reserver("cle-1", RDV)
    seconde = connecteur.reserver("cle-1", RDV)
    assert premiere == seconde == "rdv-9"


@pytest.mark.parametrize("statut, corps, code", [
    (409, {"erreur": "slot_taken"}, "creneau_pris"),
    (422, {"erreur": "invalid_phone"}, "donnees_refusees"),
    (403, {"erreur": "forbidden"}, "acces_refuse"),
    (404, {"erreur": "not_found"}, "inconnu"),
    (429, {"erreur": "rate_limited"}, "trop_de_demandes"),
])
def test_chaque_refus_a_un_code_machine(statut, corps, code):
    """Dix-huit refus possibles côté hôte : l'agent doit savoir lequel il essuie,
    sinon il annonce « c'est pris » pour une erreur d'authentification."""
    connecteur, _ = connecteur_http([(statut, corps)])
    with pytest.raises(Refus) as refus:
        connecteur.reserver("cle-1", RDV)
    assert refus.value.code == code


def test_une_panne_du_serveur_n_est_pas_un_refus():
    """500 n'est pas « non » : c'est « je ne sais pas ». L'agent ne doit surtout
    pas dire au client que son créneau est pris."""
    connecteur, _ = connecteur_http([(500, {})])
    with pytest.raises(Indisponible):
        connecteur.reserver("cle-1", RDV)


def test_un_reessai_reutilise_la_meme_cle():
    """Réessayer avec une clé neuve, c'est fabriquer un doublon."""
    connecteur, transport = connecteur_http([Indisponible("réseau"), (201, {"id": "rdv-9"})])
    connecteur.reserver("cle-1", RDV, reessais=1)
    cles = [r["entetes"]["Idempotency-Key"] for r in transport.requetes]
    assert cles == ["cle-1", "cle-1"]


def test_un_refus_n_est_jamais_reessaye():
    """Un « non » répété reste « non » — et chaque tentative coûte une seconde
    d'appel."""
    connecteur, transport = connecteur_http([(409, {"erreur": "slot_taken"})])
    with pytest.raises(Refus):
        connecteur.reserver("cle-1", RDV, reessais=3)
    assert len(transport.requetes) == 1


def test_le_delai_est_borne():
    connecteur, transport = connecteur_http([(201, {"id": "rdv-9"})])
    connecteur.reserver("cle-1", RDV)
    assert 0 < transport.requetes[0]["delai"] <= 5


def test_aucune_adresse_email_ne_part_vers_l_hote():
    """Le produit n'en collecte pas ; il ne doit pas non plus en transmettre une
    qui traînerait dans les données."""
    connecteur, transport = connecteur_http([(201, {"id": "rdv-9"})])
    connecteur.reserver("cle-1", RDV | {"email": "jean@exemple.fr"})
    assert "email" not in transport.requetes[0]["corps"]


def test_la_relecture_suit_l_ecriture():
    connecteur, transport = connecteur_http([(201, {"id": "rdv-9"}),
                                             (200, {"id": "rdv-9", "heure": "15:30"})])
    reference = connecteur.reserver("cle-1", RDV)
    assert connecteur.relire(reference)["heure"] == "15:30"
    assert transport.requetes[1]["methode"] == "GET"


def test_une_relecture_vide_ne_ment_pas():
    connecteur, _ = connecteur_http([(404, {})])
    assert connecteur.relire("rdv-inexistant") is None
