"""La comprehension : le seul endroit ou vit le modele de langage.

Frontiere posee par docs/22 : il ne redige pas ce que l'appelant entend, il
n'ecrit pas en base, il ne decide pas de raccrocher. Il rend une proposition
structuree, et rien d'autre.
"""

import json

import pytest

from standard.comprehension import (
    Comprehension,
    ErreurFournisseur,
    demande_un_humain,
    ordonner_le_prompt,
)


class ClientFactice:
    """Un fournisseur de test : on choisit ce qu'il repond, et on voit ce qu'il recoit."""

    def __init__(self, reponse=None, exception=None):
        self.reponse = reponse if reponse is not None else json.dumps(
            {"intention": "rdv", "date": "2026-09-17", "heure": "15:30",
             "prestation": None, "confiance": {"intention": 0.9, "date": 0.9, "heure": 0.9},
             "manque": []})
        self.exception = exception
        self.appels = []

    def completer(self, messages, **parametres):
        self.appels.append({"messages": messages, "parametres": parametres})
        if self.exception:
            raise self.exception
        return self.reponse


CALENDRIER = {"2026-09-17": ["09:00", "15:30"], "2026-09-18": ["10:30"]}
MEMOIRE = "# Salon\nLe balayage se fait avec Sophie ou Lea."
CONSIGNES = "Consignes communes " * 50


def comprehension(client, **kw):
    return Comprehension(client=client, consignes_communes=CONSIGNES, **kw)


# --- la demande d'humain ne passe jamais par le modele (mesure 17) ----------

@pytest.mark.parametrize("dit", [
    "PASSEZ MOI QUELQU'UN UNE VRAIE PERSONNE S'IL VOUS PLAIT",
    "je veux parler a la patronne",
    "non mais je ne veux pas parler a un robot",
    "je veux parler au responsable",
])
def test_demande_d_humain_detectee_sur_la_transcription(dit):
    assert demande_un_humain(dit) is True


def test_une_demande_d_humain_n_appelle_pas_le_modele():
    """« Passez-moi quelqu'un » n'a pas a etre interprete, il a a etre execute."""
    client = ClientFactice()
    proposition = comprehension(client).analyser("passez-moi quelqu'un", MEMOIRE, CALENDRIER)
    assert proposition["intention"] == "humain"
    assert client.appels == [], "le modele a ete appele pour rien"


def test_une_phrase_ordinaire_appelle_bien_le_modele():
    client = ClientFactice()
    comprehension(client).analyser("je voudrais un rendez-vous", MEMOIRE, CALENDRIER)
    assert len(client.appels) == 1


# --- l'ordre du prompt est un choix d'architecture (mesure 23) --------------

def test_le_prompt_va_du_plus_partage_au_plus_specifique():
    """Le memoire.md d'un salon fait 854 jetons, le seuil de cache 4 096 : ce
    n'est pas le fichier du salon qu'on allonge, c'est l'ordre qu'on inverse."""
    morceaux = ordonner_le_prompt(CONSIGNES, MEMOIRE, CALENDRIER, "jeudi matin")
    textes = [m["content"] for m in morceaux]
    assert textes[0].startswith("Consignes communes")
    position_memoire = next(i for i, t in enumerate(textes) if "balayage" in t)
    position_calendrier = next(i for i, t in enumerate(textes) if "2026-09-17" in t)
    position_appelant = next(i for i, t in enumerate(textes) if "jeudi matin" in t)
    assert position_memoire < position_calendrier < position_appelant


def test_le_calendrier_est_injecte_le_modele_ne_l_invente_pas():
    """Mesure 14 : « le premier du mois prochain est un dimanche » — le modele
    n'avait aucune date. Il en a une, maintenant, et elle vient de la machine."""
    client = ClientFactice()
    comprehension(client).analyser("jeudi ?", MEMOIRE, CALENDRIER)
    envoye = " ".join(m["content"] for m in client.appels[0]["messages"])
    assert "2026-09-17" in envoye and "15:30" in envoye


# --- le modele est une piece d'usure (mesure 17) ----------------------------

def test_le_nom_du_modele_et_ses_parametres_vivent_en_configuration():
    client = ClientFactice()
    c = comprehension(client, modele="un-modele", parametres={"reasoning_effort": "low"})
    c.analyser("bonjour", MEMOIRE, CALENDRIER)
    assert client.appels[0]["parametres"]["model"] == "un-modele"
    assert client.appels[0]["parametres"]["reasoning_effort"] == "low"


def test_l_erreur_du_fournisseur_remonte_telle_quelle():
    """Un KeyError muet a coute trois quarts d'heure : le fournisseur disait
    exactement ce qui n'allait pas des la premiere requete."""
    client = ClientFactice(exception=RuntimeError("HTTP 400 : reasoning_effort must be one of low"))
    with pytest.raises(ErreurFournisseur) as erreur:
        comprehension(client).analyser("bonjour", MEMOIRE, CALENDRIER)
    assert "reasoning_effort" in str(erreur.value)


# --- ce que le modele rend est toujours verifie -----------------------------

def test_une_reponse_illisible_devient_une_intention_inconnue():
    client = ClientFactice(reponse="je ne suis pas du JSON")
    proposition = comprehension(client).analyser("bonjour", MEMOIRE, CALENDRIER)
    assert proposition["intention"] == "inconnu"
    assert proposition["confiance"]["intention"] == 0.0


def test_une_date_hors_calendrier_est_conservee_pour_que_la_machine_reponde():
    """Un appelant a le droit de demander le premier janvier. La machine doit
    pouvoir repondre « je ne prends pas encore les rendez-vous aussi loin » —
    pas faire semblant de ne pas avoir entendu (mesure 15 : toute absence de
    donnee a sa propre reponse)."""
    client = ClientFactice(reponse=json.dumps(
        {"intention": "rdv", "date": "2027-01-01", "heure": "15:30",
         "confiance": {"intention": 0.9, "date": 0.9, "heure": 0.9}}))
    proposition = comprehension(client).analyser("le premier janvier", MEMOIRE, CALENDRIER)
    assert proposition["date"] == "2027-01-01"
    assert proposition["confiance"]["date"] == 0.9


def test_une_date_illisible_est_jetee():
    client = ClientFactice(reponse=json.dumps(
        {"intention": "rdv", "date": "jeudi prochain", "heure": None,
         "confiance": {"intention": 0.9, "date": 0.9}}))
    proposition = comprehension(client).analyser("jeudi prochain", MEMOIRE, CALENDRIER)
    assert proposition["date"] is None
    assert proposition["confiance"]["date"] == 0.0


def test_une_heure_absente_du_jour_perd_sa_confiance():
    """La ou la machine CONNAIT le jour, elle connait ses creneaux : une heure
    qui n'y figure pas a ete inventee."""
    client = ClientFactice(reponse=json.dumps(
        {"intention": "rdv", "date": "2026-09-18", "heure": "15:30",
         "confiance": {"intention": 0.9, "date": 0.9, "heure": 0.9}}))
    proposition = comprehension(client).analyser("jeudi a quinze heures trente", MEMOIRE, CALENDRIER)
    assert proposition["confiance"]["heure"] == 0.0


def test_aucune_phrase_ne_sort_de_ce_module():
    """Il rend des entites, jamais du texte a prononcer."""
    client = ClientFactice()
    proposition = comprehension(client).analyser("bonjour", MEMOIRE, CALENDRIER)
    assert set(proposition) <= {"intention", "date", "heure", "prestation", "confiance", "manque"}
