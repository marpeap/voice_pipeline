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
from standard.identite import lire_correction_de_nom, lire_nom, lire_nom_seul
from standard.locataire import lire_memoire
from standard.demarchage import est_un_demarchage
from standard.texte import aplatir
from standard.regles import (
    RELANCES_MUETTES_AVANT_TRANSFERT,
    TOURS_FENETRE_CORRECTION_NOM,
    TOURS_OU_LE_DEMARCHAGE_SE_COUPE,
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
    # Un appel de demarchage filtre ne doit pas etre facture au salon : il se
    # compte ici, et la supervision le remonte (docs/06, KPI promis).
    demarchages: int = 0

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
                 modele: str | None = None, parametres: dict | None = None,
                 secours=None, interdits: list[str] | None = None):
        self.comprehension = Comprehension(
            client=client_modele, consignes_communes=consignes_communes,
            prestations=prestations,
            **({"modele": modele} if modele else {}),
            **({"parametres": parametres} if parametres else {}))
        self.agenda = agenda
        self.base = base
        # Le filet : quand l'ecriture n'aboutit pas, l'agent dit « le salon vous
        # rappellera ». Encore faut-il que le salon SACHE qu'il doit rappeler —
        # sinon la phrase honnete devient une promesse en l'air.
        self.secours = secours
        # Les interdits poses par une correction. Le corps du memoire les dit au
        # modele ; ici, le serveur les EMPECHE — une consigne redigee peut ne pas
        # etre retenue sur un tour donne, et « la plupart du temps » n'est pas
        # une regle (docs/06).
        self.interdits = list(interdits or [])
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
        self.fin_demandee = False
        self._message_en_cours: str | None = None
        self._message_dicte = ""
        self._rappel_propose: str | None = None
        self._relances_clavier = 0
        # L'annulation : « numero » puis « relecture ». On n'annule jamais sans
        # avoir relu le rendez-vous a voix haute et obtenu un accord — un
        # rendez-vous annule par erreur est pire qu'un rendez-vous manque, le
        # client se presente et la place a ete donnee a un autre.
        self._annulation: str | None = None
        self._a_annuler: dict | None = None
        self._deplace: dict | None = None
        self._but_de_la_recherche = "annuler"
        self._doute_sur_l_annulation = False
        self._reference_ecrite: str | None = None
        self._corrige_le_nom = False
        self._tours_depuis_ecriture = 0
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

        # Un appel de prospection ne se negocie pas non plus : on refuse en une
        # phrase et on rend la ligne. Seulement dans les premiers tours — ensuite
        # une phrase commerciale peut venir d'un client qui explique son metier.
        if (self.numero_de_tour <= TOURS_OU_LE_DEMARCHAGE_SE_COUPE
                and est_un_demarchage(transcription)):
            self.journal.demarchages += 1
            phrase = ("Le salon ne donne pas suite aux démarchages par téléphone. "
                      "Bonne journée.")
            self.journal.noter(transcription=transcription, genre="demarchage",
                               phrase=phrase)
            self.fin_demandee = True
            return Reponse("demarchage", phrase)

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

        # Juste apres la confirmation, l'agent a redit le nom a voix haute :
        # c'est la seule occasion qu'a l'appelant de corriger ce que le moteur a
        # compris — « Le Fora » pour « Lefevre » (banc du 19/09).
        if self._reference_ecrite is not None:
            corrigee = self._corriger_le_nom(transcription)
            if corrigee is not None:
                return corrigee

        if self._annulation is not None:
            return self._poursuivre_l_annulation(transcription)

        if self._message_en_cours is not None:
            return self._poursuivre_le_message(transcription)

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

        if proposition.get("intention") == "annulation":
            return self._commencer_l_annulation(transcription)

        if proposition.get("intention") == "report" and self._deplace is None:
            # « report » etait traite comme une prise : l'agent ecrivait un
            # second rendez-vous et laissait le premier. Le salon se retrouvait
            # avec deux creneaux pour un client, et un trou invendable.
            self._deplace = self._rendez_vous_a_deplacer()
            if self._deplace and self._deplace.get("nom"):
                # Le rendez-vous deplace porte deja le nom : le redemander fait
                # repeter l'appelant pour rien.
                self.etat.connu.setdefault("nom", self._deplace["nom"])
            if self._deplace is None and not self.etat.connu.get("telephone"):
                # Sans numero, on ne peut RIEN retrouver : on le demande, comme
                # pour une annulation, au lieu de prendre un second creneau.
                return self._commencer_l_annulation(transcription, but="deplacer")

        sortie = decider(proposition, self.etat, self.agenda)
        if sortie.genre == "proposition":
            # L'appelant est passe a autre chose : la fenetre de correction du
            # nom se ferme, sinon un mot isole reecrirait la fiche precedente.
            self._reference_ecrite = None
        # Le salon a pu choisir « prendre un message » plutot que « transferer »
        # (question D4 des packs). Cette reponse n'etait lue nulle part : tout
        # finissait en transfert, y compris vers un telephone que personne ne
        # decroche — l'appel perdu que le produit existe pour rattraper.
        if sortie.genre == "transfert" and self._prend_des_messages():
            return self._commencer_un_message(transcription)
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

    # --- corriger le nom apres la confirmation ------------------------------

    def _corriger_le_nom(self, transcription: str) -> Reponse | None:
        """Rend une reponse si le tour corrigeait le nom, sinon `None`.

        `None` renvoie l'appel au chemin normal : la plupart des tours qui
        suivent une confirmation sont des remerciements, pas des corrections.
        """
        dans_la_fenetre = self._tours_depuis_ecriture < TOURS_FENETRE_CORRECTION_NOM
        self._tours_depuis_ecriture += 1

        nom = lire_correction_de_nom(transcription)
        if nom is None and (self._corrige_le_nom or dans_la_fenetre):
            # Juste apres la confirmation, un nom seul n'a pas d'autre sens :
            # le moteur abime souvent la phrase de correction mais rend le nom.
            # La fenetre est d'UN tour — au-dela, « Martin » peut vouloir dire
            # autre chose, et on ne reecrit pas la fiche a chaque mot isole.
            lecture = (lire_nom(transcription) if self._corrige_le_nom
                       else lire_nom_seul(transcription))
            nom = lecture.nom if lecture.issue == "accepte" else None

        if nom is None:
            if self._corrige_le_nom or not est_un_refus(transcription):
                self._corrige_le_nom = False
                return None
            # Un refus sans nom : on ne devine pas, on redemande.
            self._corrige_le_nom = True
            phrase = "Pardon. C'est à quel nom, alors ?"
            self.journal.noter(transcription=transcription, genre="question", phrase=phrase)
            return Reponse("question", phrase)

        self._corrige_le_nom = False
        corriger = getattr(self.base, "corriger", None)
        if not callable(corriger):
            return None
        relu = corriger(self._reference_ecrite, {"nom": nom})
        if relu is None or relu.get("nom") != nom:
            # On ne dit « corrige » que sur une relecture reussie, exactement
            # comme on ne dit « enregistre » que sur une ecriture relue.
            phrase = ("Je n'arrive pas à corriger votre nom. "
                      "Le salon le fera, je le lui signale.")
            self.journal.noter(transcription=transcription, genre="incertain", phrase=phrase)
            return Reponse("incertain", phrase)

        self.etat.connu["nom"] = nom
        phrase = f"C'est corrigé : au nom de {nom}."
        self.journal.noter(transcription=transcription, genre="correction", phrase=phrase,
                           reference=self._reference_ecrite)
        return Reponse("correction", phrase)

    def _rendez_vous_a_deplacer(self) -> dict | None:
        """Le rendez-vous existant de cet appelant, s'il en a un.

        Sans numero connu, on ne cherche pas : deviner le rendez-vous d'un
        appelant sur son seul nom annulerait celui d'un homonyme.
        """
        telephone = self.etat.connu.get("telephone")
        chercher = getattr(self.base, "chercher", None)
        if not telephone or not callable(chercher):
            return None
        try:
            trouves = chercher(telephone=telephone,
                               a_partir_de=self.agenda.aujourd_hui.isoformat())
        except Exception:
            return None
        return trouves[0] if trouves else None

    def _liberer_l_ancien(self) -> str:
        """Annule le rendez-vous deplace, et dit ce qui reste a faire s'il tient.

        L'ordre compte : on a ecrit le nouveau d'abord. Si l'annulation echoue,
        le client a deux rendez-vous — il doit l'apprendre de l'agent, pas du
        salon le jour venu.
        """
        ancien, self._deplace = self._deplace, None
        if not ancien or not ancien.get("reference"):
            return ""
        annuler = getattr(self.base, "annuler", None)
        if not callable(annuler):
            return ""
        try:
            libere = annuler(ancien["reference"])
        except Exception as erreur:
            self.journal.noter(transcription="[report]", genre="incertain",
                               phrase="", erreur=str(erreur))
            libere = False
        quand = f"{enoncer_date(ancien['date'])} à {enoncer_heure(ancien['heure'])}"
        if libere:
            self.journal.noter(transcription="[report]", genre="annulation",
                               phrase="", reference=ancien["reference"])
            return f" Votre rendez-vous du {quand} est annulé, à la place."
        return (f" Attention : je n'ai pas pu annuler votre ancien rendez-vous "
                f"du {quand}. Le salon s'en occupe.")

    # --- annuler (le deuxieme motif d'appel d'un salon) ---------------------

    def _commencer_l_annulation(self, transcription: str, but: str = "annuler") -> Reponse:
        self._but_de_la_recherche = but
        connu = self.etat.connu.get("telephone")
        if connu:
            return self._retrouver_a_annuler(connu, transcription)
        self._annulation = "numero"
        verbe = "annuler" if but == "annuler" else "le déplacer"
        phrase = f"Je peux {verbe}. À quel numéro le rendez-vous a-t-il été pris ?"
        self.journal.noter(transcription=transcription, genre="question", phrase=phrase)
        return Reponse("question", phrase)

    def _poursuivre_l_annulation(self, transcription: str) -> Reponse:
        if self._annulation == "relecture":
            if est_un_oui(transcription):
                return self._annuler_pour_de_bon(transcription)
            if not est_un_refus(transcription) and not self._doute_sur_l_annulation:
                # Banc du 20/09 : « oui c'est bien ça » est revenu « JE N'A N ».
                # Abandonner la oblige l'appelant a tout recommencer ; insister
                # sans fin l'epuise. Une fois, puis on passe la main.
                self._doute_sur_l_annulation = True
                quand = (f"{enoncer_date(self._a_annuler['date'])} à "
                         f"{enoncer_heure(self._a_annuler['heure'])}")
                phrase = f"Je n'ai pas compris. Le {quand} : je l'annule, oui ou non ?"
                self.journal.noter(transcription=transcription, genre="question",
                                   phrase=phrase)
                return Reponse("question", phrase)
            # Un « non » n'annule rien, et ne laisse pas l'appelant en plan.
            self._annulation = None
            self._a_annuler = None
            phrase = ("Je n'annule rien, alors. Voulez-vous que je vous passe "
                      "quelqu'un du salon ?")
            self.journal.noter(transcription=transcription, genre="question",
                               phrase=phrase)
            return Reponse("question", phrase)

        lecture = lire_numero(transcription)
        if lecture.issue != "accepte":
            self._echecs_numero += 1
            if self._echecs_numero == 1 and self.basculer_clavier is not None:
                self.basculer_clavier()
                phrase = ("Je n'ai pas saisi le numéro. Composez-le sur le clavier, "
                          "puis faites dièse.")
            else:
                self._annulation = None
                phrase = ("Je n'arrive pas à retrouver votre rendez-vous. "
                          "Je vous passe quelqu'un du salon.")
                self.journal.noter(transcription=transcription, genre="transfert",
                                   phrase=phrase)
                return Reponse("transfert", phrase)
            self.journal.noter(transcription=transcription, genre="question", phrase=phrase)
            return Reponse("question", phrase)

        return self._retrouver_a_annuler(lecture.numero, transcription)

    def _retrouver_a_annuler(self, telephone: str, transcription: str) -> Reponse:
        chercher = getattr(self.base, "chercher", None)
        trouves = []
        if callable(chercher):
            try:
                trouves = chercher(telephone=telephone,
                                   a_partir_de=self.agenda.aujourd_hui.isoformat())
            except Exception as erreur:
                self.journal.noter(transcription=transcription, genre="panne",
                                   phrase="", erreur=str(erreur))

        if not trouves:
            self._annulation = None
            phrase = ("Je ne trouve aucun rendez-vous à ce numéro. "
                      "Voulez-vous que je vous passe quelqu'un du salon ?")
            self.journal.noter(transcription=transcription, genre="question", phrase=phrase)
            return Reponse("question", phrase)

        self.etat.connu["telephone"] = telephone
        if self._but_de_la_recherche == "deplacer":
            # On a retrouve le rendez-vous : la suite est une prise normale, et
            # c'est la confirmation qui liberera l'ancien.
            self._deplace = trouves[0]
            if self._deplace.get("nom"):
                self.etat.connu.setdefault("nom", self._deplace["nom"])
            self._annulation = None
            quand = (f"{enoncer_date(self._deplace['date'])} à "
                     f"{enoncer_heure(self._deplace['heure'])}")
            phrase = (f"J'ai votre rendez-vous du {quand}. "
                      "Pour quand voulez-vous le déplacer ?")
            self.journal.noter(transcription=transcription, genre="question",
                               phrase=phrase)
            return Reponse("question", phrase)

        # Le plus proche d'abord : c'est celui qu'on annule neuf fois sur dix,
        # et le relire evite d'annuler le mauvais quand il y en a plusieurs.
        self._a_annuler = trouves[0]
        self._annulation = "relecture"
        quand = (f"{enoncer_date(self._a_annuler['date'])} à "
                 f"{enoncer_heure(self._a_annuler['heure'])}")
        reste = (f" Vous en avez {len(trouves)} : je commence par celui-là."
                 if len(trouves) > 1 else "")
        phrase = f"J'ai votre rendez-vous du {quand}.{reste} Je l'annule ?"
        self.journal.noter(transcription=transcription, genre="question", phrase=phrase)
        return Reponse("question", phrase)

    def _annuler_pour_de_bon(self, transcription: str) -> Reponse:
        """Annule, **relit**, et ne confirme que sur une relecture reussie.

        Meme regle que pour l'ecriture : dire « c'est annule » sans l'avoir
        verifie serait la faute symetrique de la confirmation orpheline.
        """
        a_annuler, self._a_annuler = self._a_annuler, None
        self._annulation = None
        annuler = getattr(self.base, "annuler", None)
        reference = (a_annuler or {}).get("reference")
        if not callable(annuler) or not reference:
            phrase = ("Je n'arrive pas à annuler moi-même. "
                      "Je vous passe quelqu'un du salon.")
            self.journal.noter(transcription=transcription, genre="transfert", phrase=phrase)
            return Reponse("transfert", phrase)

        try:
            annule = annuler(reference)
            reste = self.base.relire(reference) if annule else a_annuler
        except Exception as erreur:
            self.journal.noter(transcription=transcription, genre="incertain",
                               phrase="", erreur=str(erreur))
            annule, reste = False, a_annuler

        if not annule or reste is not None:
            phrase = ("Je n'arrive pas à vérifier que votre rendez-vous est bien "
                      "annulé. Le salon vous rappellera pour le confirmer.")
            self.journal.noter(transcription=transcription, genre="incertain", phrase=phrase)
            return Reponse("incertain", phrase)

        quand = f"{enoncer_date(a_annuler['date'])} à {enoncer_heure(a_annuler['heure'])}"
        phrase = f"C'est annulé : votre rendez-vous du {quand} n'est plus dans l'agenda."
        self.journal.noter(transcription=transcription, genre="annulation",
                           phrase=phrase, reference=reference)
        return Reponse("annulation", phrase)

    # --- la prise de message (question D4) ----------------------------------

    def _prend_des_messages(self) -> bool:
        """La fiche decide ; le code ne decide pas a sa place."""
        return str((self.fiche.get("escalade") or {}).get("humain", "")) == "message"

    def _commencer_un_message(self, transcription: str) -> Reponse:
        self._message_en_cours = "texte"
        phrase = "Je peux prendre un message pour le salon. Je vous écoute."
        self.journal.noter(transcription=transcription, genre="message", phrase=phrase)
        return Reponse("message", phrase)

    def _poursuivre_le_message(self, transcription: str) -> Reponse:
        if self._message_en_cours == "texte":
            self._message_dicte = transcription.strip()
            if self.etat.connu.get("telephone"):
                return self._deposer_le_message()
            self._message_en_cours = "numero"
            phrase = "C'est noté. À quel numéro le salon peut-il vous rappeler ?"
            self.journal.noter(transcription=transcription, genre="message", phrase=phrase)
            return Reponse("message", phrase)

        if self._message_en_cours == "relecture":
            if est_un_oui(transcription):
                self.etat.connu["telephone"] = self._rappel_propose
                self._rappel_propose = None
                return self._deposer_le_message()
            # Refus, ou autre chose : le numero relu etait faux. On ne le garde
            # pas, et on passe au clavier — insister a l'oral ne rattrape pas
            # (mesure 7).
            self._rappel_propose = None
            self._message_en_cours = "numero"
            return self._numero_de_rappel_au_clavier(transcription)

        lecture = lire_numero(transcription)
        if lecture.issue == "accepte":
            # Relecture systematique depuis la mesure 21 : « 0612345678 » dicte
            # est revenu « 0612345078 » sur le banc du 20/09, et le message
            # serait parti avec un numero faux — donc sans rappel possible.
            # Un attribut a part : `_numero_propose` est celui du rendez-vous,
            # et `tour` l'intercepte avant tout le reste.
            self._rappel_propose = lecture.numero
            self._message_en_cours = "relecture"
            phrase = f"Je relis : {lecture.relecture}. C'est bien cela ?"
            self.journal.noter(transcription=transcription, genre="message",
                               phrase=phrase, numero_lu=lecture.numero)
            return Reponse("message", phrase)

        # Un numero dicte se perd quatre fois sur dix (mesure 7) — et un message
        # sans numero de rappel ne sert presque a rien. On passe donc au clavier
        # des le premier echec, comme la regle T7 le fait pour le rendez-vous.
        return self._numero_de_rappel_au_clavier(transcription)

    def _numero_de_rappel_au_clavier(self, transcription: str) -> Reponse:
        """Le clavier des le premier echec : un message sans numero de rappel ne
        sert presque a rien, et insister a l'oral ne rattrape pas (mesure 7)."""
        if self._echecs_numero and self._relances_clavier == 0:
            # Le clavier est deja arme : l'appelant compose, et ce qu'on entend
            # de lui pendant ce temps n'est pas un nouvel echec. Deposer ici
            # jetterait le numero qu'il est en train de taper.
            self._relances_clavier += 1
            phrase = "Je vous écoute, composez votre numéro puis faites dièse."
            self.journal.noter(transcription=transcription, genre="message",
                               phrase=phrase)
            return Reponse("message", phrase)

        self._echecs_numero += 1
        if self._echecs_numero == 1 and self.basculer_clavier is not None:
            self.basculer_clavier()
            phrase = ("Je n'ai pas saisi votre numéro. Composez-le sur le clavier "
                      "de votre téléphone, puis faites dièse.")
            self.journal.noter(transcription=transcription, genre="message",
                               phrase=phrase)
            return Reponse("message", phrase)

        # Deuxieme echec, ou pas de clavier : on garde le message quand meme.
        # Un message sans rappel possible vaut mieux qu'un message perdu, et
        # insister ferait raccrocher.
        return self._deposer_le_message()

    def _deposer_le_message(self) -> Reponse:
        """Ecrit le message, et ne confirme que ce qui est ecrit."""
        contenu = {"texte": self._message_dicte,
                   "nom": self.etat.connu.get("nom"),
                   "telephone": self.etat.connu.get("telephone"),
                   "appel": self.identifiant}
        self._message_en_cours = None
        deposer = getattr(self.base, "enregistrer_message", None)
        if not callable(deposer):
            phrase = "Je préfère vous passer quelqu'un du salon, un instant."
            self.journal.noter(transcription="[message]", genre="transfert", phrase=phrase)
            return Reponse("transfert", phrase)
        try:
            reference = deposer(contenu)
        except Exception as erreur:
            self.journal.noter(transcription="[message]", genre="incertain",
                               phrase="", erreur=str(erreur))
            phrase = ("Je n'arrive pas à enregistrer votre message. "
                      "Je préfère vous passer quelqu'un du salon.")
            return Reponse("transfert", phrase)

        phrase = "C'est noté, je transmets au salon. Bonne journée."
        self.journal.noter(transcription="[message]", genre="message", phrase=phrase,
                           reference=reference)
        return Reponse("message", phrase)

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
        if self._annulation is not None:
            # Le clavier mene au meme endroit que la voix : sinon l'annulation
            # reste une impasse pour l'appelant sur deux dont le numero se perd.
            if lecture.issue != "accepte":
                self._annulation = None
                phrase = ("Ce numéro ne convient pas. "
                          "Je vous passe quelqu'un du salon.")
                self.journal.noter(transcription=f"[clavier] {numero}",
                                   genre="transfert", phrase=phrase)
                return Reponse("transfert", phrase)
            return self._retrouver_a_annuler(lecture.numero, f"[clavier] {numero}")

        if lecture.issue == "accepte" and self._message_en_cours is not None:
            self.etat.connu["telephone"] = lecture.numero
            return self._deposer_le_message()
        if lecture.issue != "accepte" and self._message_en_cours is not None:
            return self._deposer_le_message()
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
        # Les interdits poses par une correction : le corps du memoire les dit
        # au modele, ici le serveur les EMPECHE. Une consigne redigee peut ne
        # pas etre retenue sur un tour donne, et « la plupart du temps » n'est
        # pas une regle (docs/06, cas Intercom).
        plat = aplatir(phrase, garder="a-z' ")
        for interdit in self.interdits:
            if aplatir(interdit, garder="a-z' ") in plat:
                self.journal.noter(transcription="[garde de sortie]", genre="bloquee",
                                   phrase="", interdit=interdit)
                return "Je préfère vous passer quelqu'un du salon sur ce point."

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
        # La duree va SUR LA LIGNE : sans elle, l'agenda du lendemain ne sait
        # plus ce que ce rendez-vous occupe.
        duree = self.agenda.duree_de(donnees.get("prestation"))
        if duree:
            donnees.setdefault("duree_minutes", duree)
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
            # L'agenda a ete lu au debut de l'appel : il ignore ce que la base
            # vient de refuser, et reproposerait le creneau perdu au tour
            # suivant. On le lui apprend ici.
            self.agenda.pris.setdefault(donnees["date"], set()).add(donnees["heure"])
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
            self._reference_ecrite = ecriture.reference
            self._tours_depuis_ecriture = 0
            # Le nouveau est ecrit ET relu : on peut liberer l'ancien.
            ecriture.phrase += self._liberer_l_ancien()
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

        if genre == "incertain":
            self._laisser_a_rattraper(donnees)

        self.journal.noter(**trace)
        return Reponse(genre, ecriture.phrase, donnees)

    def _laisser_a_rattraper(self, donnees: dict) -> None:
        """Consigne le rendez-vous que l'hote (ou la base) n'a pas confirme.

        Il n'y a rien a promettre ici, et rien a redire a l'appelant : on ecrit
        ce qu'il faudra rappeler, la ou le commercant le lira — la console
        montre ces lignes avant le fil des appels.
        """
        deposer = getattr(self.secours, "enregistrer_message", None)
        if not callable(deposer):
            return
        try:
            quand = f"{enoncer_date(donnees['date'])} à {enoncer_heure(donnees['heure'])}"
            deposer({
                "type": "rendez_vous_a_rattraper",
                "texte": f"Rendez-vous à confirmer : {quand}. "
                         "L'agenda n'a pas confirmé l'écriture pendant l'appel.",
                "nom": donnees.get("nom") or self.etat.connu.get("nom"),
                "telephone": donnees.get("telephone") or self.etat.connu.get("telephone"),
                "appel": self.identifiant,
            })
        except Exception as erreur:
            # Le filet qui tombe ne doit pas emporter la fin de l'appel.
            self.journal.noter(transcription="[rattrapage]", genre="incertain",
                               phrase="", erreur=str(erreur))
