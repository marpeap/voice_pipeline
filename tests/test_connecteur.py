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
    # 429 chez Crenolo : « trois réservations actives pour ce client », pas un
    # débit trop rapide. Les deux mènent au même geste — passer la main —, et
    # le nom suit le sens que lui donne l'hôte réel (confirmé le 21/09).
    (429, {"erreur": "rate_limited"}, "trop_de_reservations"),
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


def test_un_409_apres_une_reprise_n_est_pas_un_creneau_pris(tmp_path=None):
    """Le cas moche, et il ne duplique pas le créneau : il duplique la PERSONNE.

    Écriture partie, aboutie chez l'hôte, réponse perdue. La reprise rejoue la
    même clé ; l'hôte, qui refuse les chevauchements, voit NOTRE PROPRE ligne et
    répond 409. Ce 409 est indiscernable d'une vraie course — sauf qu'il est
    contournable dans notre taxonomie : l'agent dirait « c'est pris » et
    proposerait 15 h au lieu de 14 h. Celle-là passerait. L'appelant repartirait
    avec DEUX rendez-vous, dont un qu'il ignore, et le plafond de l'hôte
    compterait les deux.

    Tant que l'hôte ne rejoue pas la réponse déjà rendue pour une clé déjà
    servie, un 409 en reprise n'est pas un « non » : c'est un « je ne sais
    pas ». Règle 1 du fichier. Sur une PREMIÈRE tentative, rien n'a été écrit :
    le 409 y garde tout son sens.

    Diagnostic dû à la session qui tient `marpeap/crenolo` (20/09).
    """
    connecteur, transport = connecteur_http(
        [Indisponible("réponse perdue"), (409, {"erreur": "slot_taken"})])
    with pytest.raises(Indisponible):
        connecteur.reserver("cle-1", RDV, reessais=1)
    assert len(transport.requetes) == 2, "la reprise doit bien avoir eu lieu"


def test_un_429_apres_une_reprise_est_tout_aussi_ambigu():
    """Le plafond de rendez-vous actifs est un ÉTAT : notre propre écriture a pu
    le faire franchir. Même raisonnement que le 409."""
    connecteur, _ = connecteur_http(
        [Indisponible("réponse perdue"), (429, {"erreur": "too_many"})])
    with pytest.raises(Indisponible):
        connecteur.reserver("cle-1", RDV, reessais=1)


def test_un_refus_deterministe_reste_un_refus_meme_en_reprise():
    """422, 403, 404, 400 ne dépendent pas de ce qu'on vient d'écrire : jour
    fermé, accès coupé, prestation inconnue. Les rendre incertains ferait
    transférer des appels que l'agent sait traiter."""
    connecteur, _ = connecteur_http(
        [Indisponible("réponse perdue"), (422, {"erreur": "closed_day"})])
    with pytest.raises(Refus) as refus:
        connecteur.reserver("cle-1", RDV, reessais=1)
    assert refus.value.code == "donnees_refusees"


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


# --- Crenolo : la vraie forme de ses routes ---------------------------------

def test_le_connecteur_crenolo_construit_la_route_que_crenolo_sert():
    """Crenolo ne sert PAS `/disponibilites?jour=`.

    Il sert `GET /public/{slug}/slots?date=…&service_id=…`. Branché tel quel, le
    connecteur générique prenait un 404 à chaque lecture. Les valeurs ci-dessous
    sont celles de la vraie API, relevées le 20/09 contre
    `https://rdv-api.marpeap.com`.
    """
    from standard.connecteur import ConnecteurCrenolo

    transport = TransportFactice([(200, {"slots": ["09:00", "09:30", "13:00"]})])
    connecteur = ConnecteurCrenolo(
        transport, base="https://rdv-api.marpeap.com", slug="nail-beaute-nguyen",
        service_id="0766f0fe-8015-4064-9937-4331b42d13b4")

    assert connecteur.disponibilites("2026-09-22") == ["09:00", "09:30", "13:00"]
    url = transport.requetes[0]["chemin"]
    assert url == ("https://rdv-api.marpeap.com/public/nail-beaute-nguyen/slots"
                   "?date=2026-09-22&service_id=0766f0fe-8015-4064-9937-4331b42d13b4")


def test_un_jour_de_fermeture_rend_une_liste_vide_et_non_une_panne():
    """Dimanche, le salon est fermé : `{"slots": []}`. Le confondre avec une
    indisponibilité ferait dire à l'agent qu'il n'a pas pu vérifier, alors qu'il
    sait très bien quoi répondre."""
    from standard.connecteur import ConnecteurCrenolo

    transport = TransportFactice([(200, {"slots": []})])
    connecteur = ConnecteurCrenolo(transport, base="https://rdv-api.marpeap.com",
                                   slug="nail-beaute-nguyen", service_id="s-1")
    assert connecteur.disponibilites("2026-09-27") == []


def test_ecrire_chez_crenolo_echoue_franchement_tant_que_la_route_n_existe_pas():
    """Aucune route d'écriture authentifiée n'existe chez Crenolo aujourd'hui.

    Rendre un succès, ou échouer obscurément, ferait promettre un rendez-vous
    que personne n'a pris. On refuse en le disant, et l'agent passe la main.
    """
    from standard.connecteur import ConnecteurCrenolo

    connecteur = ConnecteurCrenolo(TransportFactice([]), base="https://x",
                                   slug="s", service_id="i")
    with pytest.raises(Indisponible) as panne:
        connecteur.reserver("cle-1", RDV)
    assert "écriture" in str(panne.value)


def test_relire_chez_crenolo_ne_ment_pas():
    """`GET /reservations/{ref}` n'existe pas non plus : le seul GET qui rende
    une réservation exige un jeton d'annulation généré côté serveur. Rendre
    `None` est la vérité — et l'écriture se déclare alors « incertaine »."""
    from standard.connecteur import ConnecteurCrenolo

    connecteur = ConnecteurCrenolo(TransportFactice([]), base="https://x",
                                   slug="s", service_id="i")
    assert connecteur.relire("rdv-1") is None


def test_la_configuration_choisit_crenolo_des_qu_un_slug_est_donne():
    """`STANDARD_HOTE_SLUG` suffit à basculer sur les routes de Crenolo : sans
    lui, le service parlait à Crenolo dans une langue qu'il ne sert pas."""
    from standard.connecteur import ConnecteurCrenolo
    from standard.demarrage import _base_des_rendez_vous
    from standard.depot import Depot

    class Config:
        tenant = "salon-1"

    base = _base_des_rendez_vous({
        "STANDARD_HOTE_BASE": "https://rdv-api.marpeap.com",
        "STANDARD_HOTE_SLUG": "nail-beaute-nguyen",
        "STANDARD_HOTE_SERVICE": "0766f0fe-8015-4064-9937-4331b42d13b4",
    }, Depot(":memory:"), Config())

    assert isinstance(base._connecteur, ConnecteurCrenolo)
    assert base._connecteur.slug == "nail-beaute-nguyen"
    assert base._connecteur.service_id == "0766f0fe-8015-4064-9937-4331b42d13b4"


def test_sans_slug_l_hote_generique_reste_le_defaut():
    """Un autre logiciel de rendez-vous ne sert pas les routes de Crenolo."""
    from standard.connecteur import ConnecteurCrenolo
    from standard.demarrage import _base_des_rendez_vous
    from standard.depot import Depot

    class Config:
        tenant = "salon-1"

    base = _base_des_rendez_vous({"STANDARD_HOTE_BASE": "https://autre.fr"},
                                 Depot(":memory:"), Config())
    assert not isinstance(base._connecteur, ConnecteurCrenolo)
