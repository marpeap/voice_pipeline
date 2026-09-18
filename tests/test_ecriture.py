"""L'ecriture : la seule piece qui ait le droit de dire que c'est fait.

Mesure 14 : deux confirmations orphelines en douze tours — « votre rendez-vous de
demain matin est annule », rien en base. Le client s'organise la-dessus.
Regles : docs/04 §C2.3 (read-after-write), docs/07 (taux de confirmation
orpheline, cible 0).
"""

import pytest

from standard.ecriture import (
    Ecriture,
    JournalEcriture,
    cle_idempotence,
    ecrire_rendez_vous,
)

from standard.regles import VERBES_DE_CONFIRMATION as INTERDITS


class BaseFactice:
    """Base de test : on peut lui faire perdre une ecriture, ou la faire echouer."""

    def __init__(self, relecture_muette=False, insertion_casse=False):
        self.lignes = {}
        self.par_cle = {}
        self.relecture_muette = relecture_muette
        self.insertion_casse = insertion_casse
        self.insertions = 0

    def inserer(self, cle, donnees):
        if self.insertion_casse:
            raise RuntimeError("la base ne repond pas")
        if cle in self.par_cle:
            return self.par_cle[cle]
        self.insertions += 1
        reference = f"rdv-{self.insertions:04d}"
        self.lignes[reference] = dict(donnees)
        self.par_cle[cle] = reference
        return reference

    def relire(self, reference):
        if self.relecture_muette:
            return None
        return self.lignes.get(reference)


DONNEES = {"date": "2026-09-17", "heure": "15:30", "prestation": "coupe",
           "telephone": "0612345678"}


def test_ecriture_relue_donne_la_seule_confirmation_du_produit():
    base = BaseFactice()
    journal = JournalEcriture()
    ecriture = ecrire_rendez_vous(base, cle_idempotence("t1", "appel-1", 3), DONNEES, journal)
    assert ecriture.statut == "confirme"
    assert ecriture.reference == "rdv-0001"
    assert "jeudi 17 septembre" in ecriture.phrase
    assert "15 h 30" in ecriture.phrase
    assert journal.orphelines == 0


def test_relecture_muette_interdit_toute_confirmation():
    """Le cas qui a produit deux fautes sur douze tours : l'ecriture part, la
    relecture ne rend rien, et l'agent dit quand meme que c'est note."""
    base = BaseFactice(relecture_muette=True)
    journal = JournalEcriture()
    ecriture = ecrire_rendez_vous(base, cle_idempotence("t1", "appel-1", 3), DONNEES, journal)
    assert ecriture.statut == "incertain"
    assert not any(mot in ecriture.phrase.lower() for mot in INTERDITS), ecriture.phrase
    assert "vérifier" in ecriture.phrase.lower() or "rappel" in ecriture.phrase.lower()
    assert journal.orphelines == 0, "une relecture muette n'est PAS une confirmation orpheline"


def test_base_injoignable_ne_promet_rien():
    base = BaseFactice(insertion_casse=True)
    ecriture = ecrire_rendez_vous(base, cle_idempotence("t1", "appel-1", 3), DONNEES)
    assert ecriture.statut == "incertain"
    assert not any(mot in ecriture.phrase.lower() for mot in INTERDITS)


def test_meme_cle_une_seule_ecriture():
    """Idempotence : un reessai dans le meme tour de parole ne cree pas un
    deuxieme rendez-vous."""
    base = BaseFactice()
    cle = cle_idempotence("t1", "appel-1", 3)
    premiere = ecrire_rendez_vous(base, cle, DONNEES)
    seconde = ecrire_rendez_vous(base, cle, DONNEES)
    assert base.insertions == 1
    assert premiere.reference == seconde.reference
    assert seconde.statut in ("confirme", "rejoue")


def test_cle_generee_au_debut_du_tour_est_stable():
    """docs/02 : la cle se genere au DEBUT du tour de parole, pas a l'envoi —
    sinon deux tentatives du meme tour portent deux cles et creent deux lignes."""
    assert cle_idempotence("t1", "appel-1", 3) == cle_idempotence("t1", "appel-1", 3)
    assert cle_idempotence("t1", "appel-1", 3) != cle_idempotence("t1", "appel-1", 4)
    assert cle_idempotence("t1", "appel-1", 3) != cle_idempotence("t2", "appel-1", 3)


def test_le_journal_compte_ce_qui_ne_doit_jamais_arriver():
    """Le taux de confirmation orpheline est un incident, pas une statistique.
    Il ne peut monter que si quelqu'un confirme sans relecture reussie."""
    journal = JournalEcriture()
    journal.noter_confirmation_orpheline("rdv-9999")
    assert journal.orphelines == 1
    assert journal.incidents[0]["reference"] == "rdv-9999"


def test_la_phrase_porte_le_jour_de_la_semaine():
    """Regle E1 (mesure 19) : le quantieme est le mot le plus fragile de tout ce
    que l'agent dit. La confirmation ne fait pas exception."""
    base = BaseFactice()
    ecriture = ecrire_rendez_vous(base, cle_idempotence("t1", "a", 1), DONNEES)
    assert "jeudi" in ecriture.phrase.lower()
    assert "septembre" in ecriture.phrase.lower()
