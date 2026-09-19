"""Le client du modèle de langage — celui qui manquait.

Seconde revue (19/09) : aucun client HTTP de modèle n'existait dans le dépôt.
`construire_serveur` câblait toujours le moteur hors ligne, et
`python -m standard verifier` annonçait pourtant le modèle qu'on avait configuré.
Un rapport de déploiement qui dit autre chose que ce qui tourne est pire que pas
de rapport.
"""

import json

import pytest

from standard.modele import ClientModeleHttp, ErreurModele


class TransportFactice:
    def __init__(self, reponses):
        self.reponses = list(reponses)
        self.appels = []
        self.connexions = 0

    def nouvelle_connexion(self):
        self.connexions += 1
        return self

    def envoyer(self, corps, entetes, chemin):
        self.appels.append({"corps": json.loads(corps), "entetes": entetes,
                            "chemin": chemin})
        reponse = self.reponses.pop(0) if self.reponses else (200, {})
        if isinstance(reponse, Exception):
            raise reponse
        return reponse


def contenu(texte):
    return (200, {"choices": [{"message": {"content": texte}}]})


def client(reponses, **kw):
    transport = TransportFactice(reponses)
    return ClientModeleHttp(transport, modele="un-modele", cle="secrete", **kw), transport


# --- ce qu'il envoie --------------------------------------------------------

def test_il_rend_le_contenu_du_modele():
    c, _ = client([contenu('{"intention": "rdv"}')])
    assert c.completer([{"role": "user", "content": "bonjour"}]) == '{"intention": "rdv"}'


def test_le_nom_du_modele_et_les_parametres_partent_dans_la_requete():
    c, transport = client([contenu("{}")])
    c.completer([{"role": "user", "content": "x"}], temperature=0.2)
    assert transport.appels[0]["corps"]["model"] == "un-modele"
    assert transport.appels[0]["corps"]["temperature"] == 0.2


def test_la_cle_voyage_dans_l_entete_jamais_dans_l_url():
    c, transport = client([contenu("{}")])
    c.completer([{"role": "user", "content": "x"}])
    assert "secrete" in transport.appels[0]["entetes"]["Authorization"]
    assert "secrete" not in transport.appels[0]["chemin"]


def test_il_demande_du_json_puisque_c_est_ce_qu_on_attend():
    c, transport = client([contenu("{}")])
    c.completer([{"role": "user", "content": "x"}])
    assert transport.appels[0]["corps"]["response_format"]["type"] == "json_object"


# --- la connexion est gardée (mesure 4) -------------------------------------

def test_la_connexion_est_ouverte_une_fois_et_reutilisee():
    """Mesure 4 : 2 040 ms pour une connexion neuve, 378 ms pour une gardée.
    C'est le premier levier de latence, et il est gratuit."""
    c, transport = client([contenu("{}"), contenu("{}"), contenu("{}")])
    for _ in range(3):
        c.completer([{"role": "user", "content": "x"}])
    assert transport.connexions == 1


def test_une_connexion_cassee_est_refaite_une_fois():
    c, transport = client([ConnectionResetError("coupée"), contenu('{"ok": 1}')])
    assert c.completer([{"role": "user", "content": "x"}]) == '{"ok": 1}'
    assert transport.connexions == 2


# --- les erreurs remontent telles quelles -----------------------------------

def test_l_erreur_du_fournisseur_remonte_avec_son_message():
    """Mesure 17 : un KeyError muet a coûté trois quarts d'heure là où le
    fournisseur disait exactement ce qui n'allait pas."""
    c, _ = client([(400, {"error": {"message": "reasoning_effort must be one of low"}})])
    with pytest.raises(ErreurModele, match="reasoning_effort"):
        c.completer([{"role": "user", "content": "x"}])


def test_une_reponse_sans_choix_est_une_erreur_lisible():
    c, _ = client([(200, {"rien": "du tout"})])
    with pytest.raises(ErreurModele, match="choices"):
        c.completer([{"role": "user", "content": "x"}])


def test_un_429_dit_qu_il_faut_ralentir():
    c, _ = client([(429, {"error": {"message": "rate limited"}})])
    with pytest.raises(ErreurModele, match="429"):
        c.completer([{"role": "user", "content": "x"}])
