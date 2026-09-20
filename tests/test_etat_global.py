"""Un mot, pas douze chiffres — ce qu'une sonde peut surveiller.

`/sante` rend une quinzaine de compteurs. C'est ce qu'il faut pour diagnostiquer,
et c'est inutilisable pour alerter : personne n'écrit une sonde qui compare
quinze nombres, et personne ne relit quinze nombres à trois heures du matin.

Le point d'état rend donc aussi **un mot** — `ok`, `dégradé`, `en panne` — et la
liste des raisons. Un mot se surveille ; les chiffres restent pour comprendre.
"""

import pytest

from standard.sante import etat_du_serveur


class ServeurFactice:
    def __init__(self, **champs):
        self.port = 8090
        self.appels_en_cours = 0
        self.interruptions_totales = 0
        self.paroles_perdues = 0
        self.pannes_pendant_appel = 0
        self.archivages_perdus = 0
        self.demarchages_filtres = 0
        self.appels_refuses = 0
        self.lignes_rendues = 0
        self.appels_simultanes_max = 8
        self.service = None
        self.entretien = None
        self.__dict__.update(champs)


class EntretienFactice:
    def __init__(self, vivant=True, pannes=0):
        self.vivant = vivant
        self._pannes = pannes

    def etat(self):
        return {"passages": 3, "lignes_effacees": 0, "rappels_envoyes": 0,
                "pannes": self._pannes, "conservation_jours": 90}


class ServiceFactice:
    def __init__(self, orphelines=0):
        self._orphelines = orphelines

    def supervision(self):
        return {"appels": 10, "part_bruitee_pct": 0.0,
                "confirmations_orphelines": self._orphelines,
                "premier_fragment_p50_ms": 220}


def test_tout_va_bien_se_dit_en_un_mot():
    etat = etat_du_serveur(ServeurFactice(entretien=EntretienFactice(),
                                          service=ServiceFactice()))
    assert etat["etat"] == "ok"
    assert etat["raisons"] == []


def test_une_confirmation_orpheline_degrade_l_etat():
    """Cible zéro : toute occurrence est un incident, pas une statistique."""
    etat = etat_du_serveur(ServeurFactice(entretien=EntretienFactice(),
                                          service=ServiceFactice(orphelines=1)))
    assert etat["etat"] == "dégradé"
    assert any("orpheline" in raison for raison in etat["raisons"])


def test_le_menage_arrete_degrade_l_etat():
    """Sans lui, la durée de conservation annoncée au registre devient fausse."""
    etat = etat_du_serveur(ServeurFactice(entretien=EntretienFactice(vivant=False),
                                          service=ServiceFactice()))
    assert etat["etat"] == "dégradé"
    assert any("ménage" in raison for raison in etat["raisons"])


def test_des_pannes_pendant_les_appels_degradent_l_etat():
    etat = etat_du_serveur(ServeurFactice(pannes_pendant_appel=2,
                                          entretien=EntretienFactice(),
                                          service=ServiceFactice()))
    assert etat["etat"] == "dégradé"


def test_un_standard_qui_n_ecoute_pas_est_en_panne():
    etat = etat_du_serveur(ServeurFactice(port=0, entretien=EntretienFactice(),
                                          service=ServiceFactice()))
    assert etat["etat"] == "en panne"


def test_les_raisons_se_cumulent():
    etat = etat_du_serveur(ServeurFactice(archivages_perdus=1,
                                          entretien=EntretienFactice(vivant=False),
                                          service=ServiceFactice(orphelines=2)))
    assert len(etat["raisons"]) >= 3


def test_les_chiffres_restent_pour_comprendre():
    etat = etat_du_serveur(ServeurFactice(entretien=EntretienFactice(),
                                          service=ServiceFactice()))
    for cle in ("appels", "confirmations_orphelines", "premier_fragment_p50_ms"):
        assert cle in etat
