"""Le tour de parole complet — l'assemblage, et l'endroit ou les regles tiennent.

Un appel, c'est cinq pieces enchainees : ecoute, comprehension, decision,
ecriture, parole. Ce module les tient ensemble et fait respecter la seule regle
qui compte vraiment (mesure 14, puis 15) :

> **le modele propose, la machine dispose, et seule une ecriture relue confirme.**

Le test de ce module rejoue les douze tours qui avaient produit six fautes, avec
un modele de test qui se comporte comme celui qui a faute. Aucune de ses
inventions ne doit atteindre l'appelant.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from standard.comprehension import Comprehension, ErreurFournisseur
from standard.decision import (
    Agenda,
    Etat,
    decider,
    enoncer_date,
    enoncer_heure,
    espacer,
)
from standard.assentiment import est_un_refus, est_un_oui
from standard.fiche import repondre as repondre_depuis_la_fiche
from standard.grammaire import enoncer_numero, lire_numero
from standard.identite import lire_nom
from standard.locataire import lire_memoire
from standard.regles import (
    RELANCES_MUETTES_AVANT_TRANSFERT,
    contient_une_confirmation,
)
from standard.langue import FRANCAIS, detecter_langue, phrase_de_passage
from standard.ecriture import (
    BaseRendezVous,
    Ecriture,
    JournalEcriture,
    cle_idempotence,
    ecrire_rendez_vous,
)


@dataclass
class Reponse:
    genre: str
    phrase: str
    entites: dict = field(default_factory=dict)


@dataclass
class Journal:
    """Ce qu'il faut pour diagnostiquer un appel sans le reecouter.

    Sans lui, une plainte « l'agent comprend mal » n'est pas diagnosticable ; avec
    lui, on sait tout de suite si le probleme est le moteur, le pack, ou la rue
    (mesure 10).
    """
    tours: list[dict[str, Any]] = field(default_factory=list)
    ecriture: JournalEcriture = field(default_factory=JournalEcriture)

    @property
    def confirmations_orphelines(self) -> int:
        return self.ecriture.orphelines

    def noter(self, **champs: Any) -> None:
        self.tours.append(champs)


class Appel:
    """Un appel en cours. Un objet par appel, jamais partage."""

    def __init__(self, client_modele, agenda: Agenda, base: BaseRendezVous,
                 memoire: str, consignes_communes: str,
                 tenant: str = "inconnu", identifiant: str = "appel",
                 nom_salon: str = "le salon",
                 prestations: tuple[str, ...] = (),
                 modele: str | None = None, parametres: dict | None = None):
        self.comprehension = Comprehension(
            client=client_modele, consignes_communes=consignes_communes,
            prestations=prestations,
            **({"modele": modele} if modele else {}),
            **({"parametres": parametres} if parametres else {}))
        self.agenda = agenda
        self.base = base
        self.memoire = memoire
        # La fiche du salon, lue une fois : l'agent y prend ses reponses de fait
        # (horaires), au lieu de repondre « Que puis-je faire pour vous ? » a une
        # question dont il a la reponse ecrite (banc du 19/09).
        try:
            self.fiche = lire_memoire(memoire).frontmatter
        except Exception:
            self.fiche = {}
        self.tenant = tenant
        self.identifiant = identifiant
        self.nom_salon = nom_salon
        self.etat = Etat()
        self._relances_muettes = 0
        self._demande_le_nom = False
        self._echecs_nom = 0
        self._nom_abandonne = False
        self.journal = Journal()
        self.numero_de_tour = 0
        self.envoyeur_sms = None                 # branché par le service, facultatif
        self.basculer_clavier = None             # branché par la session (DTMF, règle T7)
        self._numero_propose: str | None = None  # en attente de relecture
        self._echecs_numero = 0
        self._demande_le_numero = False
        self._en_attente: dict | None = None     # la proposition que l'appelant doit confirmer

    def _calendrier(self) -> dict:
        """Ce que la machine donne au modele : ses propres creneaux, rien d'autre."""
        from datetime import timedelta
        calendrier = {}
        for delta in range(self.agenda.horizon_jours + 1):
            jour = (self.agenda.aujourd_hui + timedelta(days=delta)).isoformat()
            if self.agenda.statut(jour) == "ouvert":
                calendrier[jour] = self.agenda.libres(jour)
        return calendrier

    def tour(self, transcription: str, bruite: bool = False) -> Reponse:
        """Un tour de parole : ce que l'appelant a dit, ce que l'agent repond."""
        self.numero_de_tour += 1
        self._relances_muettes = 0        # on l'a entendu : le compteur repart

        # Avant toute chose : parle-t-il une langue que nous ne servons pas ?
        # Le servir a moitie serait pire que passer la main — et l'AI Act demande
        # l'annonce « dans la langue de la conversation ».
        # Le numero en cours de relecture passe avant tout : « oui » repond a la
        # question posee, pas a une nouvelle demande.
        if self._numero_propose is not None:
            if est_un_oui(transcription):
                numero, self._numero_propose = self._numero_propose, None
                self.etat.connu["telephone"] = numero
                return self.confirmer()
            self._numero_propose = None          # il corrige : on reprend l'ecoute

        if self._demande_le_nom:
            return self._entendre_un_nom(transcription)

        if self._attend_un_numero:
            return self._entendre_un_numero(transcription)

        # Le « oui » d'un appelant a qui l'on vient de proposer un creneau n'est
        # pas une nouvelle demande : c'est CE moment qui ecrit en base, et rien
        # d'autre dans le produit ne le fait.
        if self._en_attente is not None:
            if est_un_oui(transcription):
                return self._apres_accord()
            if est_un_refus(transcription):
                self._en_attente = None

        langue = detecter_langue(transcription)
        if langue != FRANCAIS:
            phrase = phrase_de_passage(langue)
            self.journal.noter(transcription=transcription, genre="transfert",
                               phrase=phrase, langue=langue)
            return Reponse("transfert", phrase, {"langue": langue})

        try:
            proposition = self.comprehension.analyser(transcription, self.memoire,
                                                      self._calendrier())
        except ErreurFournisseur as erreur:
            # L'erreur du fournisseur est journalisee telle quelle, jamais dite au
            # client : lui n'entend qu'une phrase d'attente honnete.
            self.journal.noter(transcription=transcription, genre="panne",
                               phrase="", erreur=str(erreur))
            return Reponse("panne", "Je rencontre un problème technique. "
                                    "Je vous passe quelqu'un du salon.")

        # Une question de fait se repond avant toute logique d'agenda : elle ne
        # demande ni creneau, ni confirmation, ni ecriture.
        if proposition.get("intention") == "question":
            depuis_la_fiche = repondre_depuis_la_fiche(transcription, self.fiche)
            if depuis_la_fiche:
                self.journal.noter(transcription=transcription, genre="question",
                                   phrase=depuis_la_fiche, bruite=bruite,
                                   source="fiche")
                return Reponse("question", depuis_la_fiche)

        sortie = decider(proposition, self.etat, self.agenda)
        sortie.phrase = self._garde_de_sortie(sortie.phrase)
        self._en_attente = sortie.entites if sortie.genre == "proposition" else None
        self.journal.noter(transcription=transcription, genre=sortie.genre,
                           phrase=sortie.phrase, bruite=bruite,
                           entites=dict(sortie.entites))
        return Reponse(sortie.genre, sortie.phrase, sortie.entites)

    # --- le numero de l'appelant -------------------------------------------

    @property
    def _attend_un_numero(self) -> bool:
        return self._en_attente is not None and self._demande_le_numero

    def _demande_du_nom(self) -> bool:
        """Le pack decide (question D5), pas le code.

        Un salon prend un nom ; un depanneur en urgence peut vouloir aller plus
        vite. La valeur vit dans la fiche, comme toutes les autres.
        """
        return str((self.fiche.get("reservation") or {}).get("nom", "oui")) != "non"

    def _entendre_un_nom(self, transcription: str) -> Reponse:
        """Lit le nom, ou redemande une fois — puis abandonne le nom, pas l'appel.

        Faire repeter un appelant jusqu'a ce qu'il raccroche coute plus cher
        qu'un rendez-vous sans nom : le salon peut toujours rappeler le numero.
        """
        lecture = lire_nom(transcription)
        if lecture.issue == "accepte":
            self._demande_le_nom = False
            self.etat.connu["nom"] = lecture.nom
            return self._apres_accord()

        self._echecs_nom += 1
        if self._echecs_nom >= 2:
            # On abandonne le nom, pas l'appel — et on ne le redemande plus,
            # sans quoi la conversation tournerait en rond.
            self._demande_le_nom = False
            self._nom_abandonne = True
            return self._apres_accord()
        phrase = "Je n'ai pas saisi votre nom. Pouvez-vous me le redonner ?"
        self.journal.noter(transcription=transcription, genre="question", phrase=phrase)
        return Reponse("question", phrase)

    def _apres_accord(self) -> Reponse:
        """L'appelant a dit oui. Reste a savoir a quel nom, et ou confirmer.

        L'agent ne peut pas lire le numero sur son ecran : l'Arcep recommande aux
        operateurs de masquer l'identifiant d'appelant sur les renvois complexes
        (docs/19). Il le demande donc — mais seulement s'il en fera quelque chose.
        """
        if (self._demande_du_nom() and not self.etat.connu.get("nom")
                and not self._nom_abandonne):
            self._demande_le_nom = True
            phrase = "Très bien. C'est à quel nom ?"
            self.journal.noter(transcription="[accord de l'appelant]", genre="question",
                               phrase=phrase)
            return Reponse("question", phrase)

        if self.envoyeur_sms is None or self.etat.connu.get("telephone"):
            return self.confirmer()
        self._demande_le_numero = True
        # Formulation choisie pour ne rien affirmer : a ce stade, RIEN n'est
        # encore ecrit en base, et le garde de sortie refuserait « c'est note ».
        phrase = ("Parfait. À quel numéro de mobile puis-je vous envoyer "
                  "la confirmation ?")
        self.journal.noter(transcription="[accord de l'appelant]", genre="question",
                           phrase=phrase)
        return Reponse("question", phrase)

    def _entendre_un_numero(self, transcription: str) -> Reponse:
        """Lit le numero sous contrainte, et le fait relire. Jamais de supposition."""
        lecture = lire_numero(transcription)

        if lecture.issue == "accepte":
            self._numero_propose = lecture.numero
            self._echecs_numero = 0
            phrase = f"Je relis : {lecture.relecture}. C'est bien cela ?"
            self.journal.noter(transcription=transcription, genre="question",
                               phrase=phrase, numero_lu=lecture.numero)
            return Reponse("question", phrase)

        self._echecs_numero += 1
        if lecture.issue == "refus":
            phrase = ("Ce numéro ne peut pas recevoir de SMS. "
                      "Avez-vous un numéro de mobile ?")
        elif self._echecs_numero >= 2:
            # Regle T7 : apres deux echecs, le clavier. Mesure 7 : quatre numeros
            # sur dix se perdent a l'oral, et insister ne les rattrape pas.
            if self.basculer_clavier is not None:
                self.basculer_clavier()
            phrase = ("Je n'arrive pas à noter votre numéro. Composez-le sur "
                      "le clavier de votre téléphone, puis faites dièse.")
        else:
            phrase = ("Je n'ai pas tout saisi. Pouvez-vous me redonner votre "
                      "numéro, chiffre par chiffre ?")
        self.journal.noter(transcription=transcription, genre="question", phrase=phrase,
                           lecture=lecture.issue)
        return Reponse("question", phrase)

    def numero_au_clavier(self, numero: str) -> Reponse:
        """Le numero compose au clavier. Il passe par les memes regles que l'oral.

        Dix chiffres, pas neuf, et pas de 08 : un numero saisi n'est pas plus
        vrai qu'un numero dicte, il est seulement mieux transmis.
        """
        lecture = lire_numero(numero)
        if lecture.issue != "accepte":
            phrase = "Ce numéro ne convient pas. Le salon vous rappellera pour confirmer."
            self.journal.noter(transcription=f"[clavier] {numero}", genre="question",
                               phrase=phrase, lecture=lecture.issue)
            return Reponse("question", phrase)
        self.etat.connu["telephone"] = lecture.numero
        self._demande_le_numero = False
        return self.confirmer()

    def _garde_de_sortie(self, phrase: str) -> str:
        """Le dernier filet : aucune phrase venue d'ailleurs que de l'ecriture
        relue ne peut affirmer qu'un rendez-vous existe.

        Ce garde ne devrait jamais servir — la decision ne produit pas ces mots,
        et le modele n'ecrit rien. C'est precisement pourquoi il existe : un
        invariant garde par un compteur que rien ne peut incrementer n'est pas
        garde du tout, et c'est ce qu'une revue independante a trouve le 19/09.
        """
        if not contient_une_confirmation(phrase):
            return phrase
        self.journal.ecriture.noter_confirmation_orpheline(
            self.identifiant, f"phrase bloquee : {phrase!r}")
        return ("Je vérifie votre demande, un instant.")

    def rien_entendu(self) -> Reponse:
        """L'appelant a parle, et le moteur n'a rien rendu.

        Banc du 19/09 : « oui », dit seul et vite, revient vide du moteur local.
        L'agent se taisait — ligne ouverte, personne au bout, et le rendez-vous
        deja propose ne s'ecrivait jamais. On relance, en rappelant ce qu'on
        attend ; deux fois au plus, puis un humain.
        """
        self._relances_muettes += 1
        if self._relances_muettes > RELANCES_MUETTES_AVANT_TRANSFERT:
            phrase = ("Je ne vous entends pas bien. "
                      "Je préfère vous passer quelqu'un du salon.")
            self.journal.noter(transcription="[rien entendu]", genre="transfert",
                               phrase=phrase)
            return Reponse("transfert", phrase)

        if self._en_attente:
            quand = enoncer_date(self._en_attente["date"])
            heure = enoncer_heure(self._en_attente["heure"])
            phrase = (f"Je n'ai pas entendu votre réponse. "
                      f"Je vous réserve le {quand} à {heure} ?")
        else:
            phrase = "Je n'ai pas entendu, pouvez-vous répéter ?"
        self.journal.noter(transcription="[rien entendu]", genre="question",
                           phrase=phrase)
        return Reponse("question", phrase)

    def confirmer(self) -> Reponse:
        """L'appelant a dit oui. C'est ici, et seulement ici, qu'on ecrit.

        Sans proposition en cours, il n'y a rien a confirmer — et surtout rien a
        annoncer : c'est exactement la faute qui produisait « c'est note » sur du
        vide (mesure 14).
        """
        if not self._en_attente:
            return Reponse("question", "Je n'ai pas encore de créneau à vous confirmer. "
                                       "Quel jour vous conviendrait ?")

        donnees = dict(self._en_attente)
        donnees.setdefault("prestation", self.etat.connu.get("prestation"))
        if self.etat.connu.get("nom"):
            donnees.setdefault("nom", self.etat.connu["nom"])
        telephone = donnees.get("telephone") or self.etat.connu.get("telephone")
        promet_sms = (self.envoyeur_sms is not None and bool(telephone)
                      and getattr(self.envoyeur_sms, "peut_promettre", True))
        cle = cle_idempotence(self.tenant, self.identifiant, self.numero_de_tour)
        ecriture: Ecriture = ecrire_rendez_vous(self.base, cle, donnees,
                                                self.journal.ecriture, promet_sms)

        if ecriture.statut == "occupe":
            # Quelqu'un a pris la place pendant la conversation. On ne laisse pas
            # l'appelant sur un constat : on regarde ce qu'il reste le meme jour.
            self._en_attente = None
            self._demande_le_numero = False
            libres = espacer(self.agenda.libres(donnees["date"]))
            if libres:
                reste = " ou ".join(enoncer_heure(heure) for heure in libres)
                phrase = (f"{ecriture.phrase} Il me reste {reste}. "
                          "Qu'est-ce qui vous va ?")
            else:
                phrase = (f"{ecriture.phrase} Il n'y a plus rien ce jour-là. "
                          "Quel autre jour vous conviendrait ?")
            self.journal.noter(transcription="[créneau perdu]", genre="question",
                               phrase=phrase)
            return Reponse("question", phrase)

        genre = "confirmation" if ecriture.statut in ("confirme", "rejoue") else "incertain"
        trace = {"transcription": "[confirmation de l'appelant]", "genre": genre,
                 "phrase": ecriture.phrase, "reference": ecriture.reference}

        if genre == "confirmation":
            self._en_attente = None
            self._demande_le_numero = False
            # Le SMS suit l'ecriture relue, jamais la proposition : promettre un
            # message pour un rendez-vous qui n'existe pas serait doubler la faute.
            if promet_sms:
                envoi = self.envoyeur_sms.confirmer(telephone, {**donnees,
                                                                "salon": self.nom_salon})
                trace["sms"] = "envoyé" if envoi.envoye else "échec"
                if envoi.reserve:
                    # L'agent a deja dit « vous recevrez un SMS » : un echec muet
                    # transforme cette phrase en mensonge.
                    trace["sms_reserve"] = envoi.reserve

        self.journal.noter(**trace)
        return Reponse(genre, ecriture.phrase, donnees)
