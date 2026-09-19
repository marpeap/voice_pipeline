"""La piste d'audit : qui a changé quoi, et quand.

Le journal d'appel dit ce que l'agent a fait. La piste d'audit dit ce que les
**humains** ont fait : posé une correction, changé une réponse du questionnaire,
révoqué une clé. Sans elle, « l'agent s'est mis à refuser tout le monde » n'a pas
d'explication.
"""

import pytest

from standard.audit import PisteDAudit
from standard.depot import Depot


@pytest.fixture
def piste():
    return PisteDAudit(Depot(":memory:"))


def test_un_evenement_se_relit(piste):
    piste.noter("salon-1", acteur="gerant@salon", action="correction.posee",
                cible="cor-0001", detail={"faute": "duree"})
    [evenement] = piste.lister("salon-1")
    assert evenement["action"] == "correction.posee"
    assert evenement["acteur"] == "gerant@salon"


def test_la_piste_est_en_ajout_seul(piste):
    """Une piste d'audit qu'on peut modifier ne prouve rien."""
    piste.noter("salon-1", acteur="a", action="x", cible="1")
    with pytest.raises(AttributeError):
        piste.modifier  # noqa: B018


def test_chaque_evenement_porte_son_horodatage_et_son_correlation(piste):
    piste.noter("salon-1", acteur="a", action="x", cible="1", correlation="appel-42")
    [evenement] = piste.lister("salon-1")
    assert evenement["horodatage"]
    assert evenement["correlation"] == "appel-42"


def test_un_locataire_ne_lit_pas_la_piste_d_un_autre(piste):
    piste.noter("salon-1", acteur="a", action="x", cible="1")
    assert piste.lister("salon-2") == []


def test_la_piste_ne_conserve_aucun_secret(piste):
    """Une clé d'API dans un journal d'audit, c'est une clé publiée."""
    with pytest.raises(ValueError, match="secret"):
        piste.noter("salon-1", acteur="a", action="cle.emise", cible="1",
                    detail={"secret": "sk-123"})


def test_les_evenements_sortent_du_plus_recent_au_plus_ancien(piste):
    for index in range(3):
        piste.noter("salon-1", acteur="a", action=f"action-{index}", cible=str(index))
    actions = [e["action"] for e in piste.lister("salon-1")]
    assert actions == ["action-2", "action-1", "action-0"]


def test_ecrire_sans_locataire_est_refuse(piste):
    """La règle « pas de locataire, pas de données » était appliquée à deux
    endroits sur trois : une écriture d'audit sans locataire devenait invisible
    de toute lecture cloisonnée — donc perdue, tout en donnant l'illusion d'une
    trace. Relevé par la revue du 19/09."""
    with pytest.raises(ValueError, match="locataire"):
        piste.noter("", acteur="a", action="x", cible="1")


def test_lire_sans_locataire_est_refuse(piste):
    with pytest.raises(ValueError, match="locataire"):
        piste.lister("")
