"""Le démarrage en exploitation — variables d'environnement, vérification, arrêt propre.

Un service qu'on ne peut pas lancer avec des variables d'environnement et
arrêter proprement n'est pas exploitable : il est démontrable, ce qui n'est pas
la même chose.

Deux partis pris :

- **Refuser de démarrer plutôt que décrocher avec un agenda faux.** Un créneau
  mal écrit dans une variable produit, sinon, des rendez-vous à des heures qui
  n'existent pas — et personne ne s'en aperçoit avant le client.
- **Tourner sans clé d'API.** Le moteur hors ligne prend le relais. Un service
  qui refuse de démarrer faute de clé est un service qu'on ne peut pas essayer.
"""

from __future__ import annotations

import json
import os
import re
import threading
from datetime import datetime, timezone
from uuid import uuid4
from datetime import date
from pathlib import Path
from typing import Any, Mapping

from standard.depot import Depot
from standard.correction import RegistreDeCorrections
from standard.echecs import detecter_l_echec
from standard.entretien import Entretien
from standard.journal import JournalDAppels
from standard.sante import ServeurDeSante
from standard.hors_ligne import ModeleHorsLigne
from standard.parole import FileDeSynthese
from standard.regles import PARALLELISME_SYNTHESE
from standard.moteurs import (
    MoteurAbsent,
    choisir_synthese,
    choisir_transcription,
    inventaire,
)
from standard.serveur import ServeurAudioSocket
from standard.service import Configuration, Service

OBLIGATOIRES = ("STANDARD_TENANT", "STANDARD_PACK")
FORME_HEURE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _creneaux(brut: str) -> tuple[str, ...]:
    creneaux = tuple(c.strip() for c in brut.split(",") if c.strip())
    mauvais = [c for c in creneaux if not FORME_HEURE.match(c)]
    if mauvais:
        raise ValueError(f"créneau mal écrit : {', '.join(mauvais)} — attendu HH:MM")
    return creneaux


def configuration_depuis_environnement(environnement: Mapping[str, str] | None = None) -> Configuration:
    env = dict(environnement if environnement is not None else os.environ)
    manquantes = [nom for nom in OBLIGATOIRES if not env.get(nom)]
    if manquantes:
        # On nomme la variable : « configuration invalide » ne se repare pas.
        raise ValueError(f"variable(s) manquante(s) : {', '.join(manquantes)}")

    return Configuration.depuis({
        "tenant": env["STANDARD_TENANT"],
        "pack": env["STANDARD_PACK"],
        "reponses": json.loads(env.get("STANDARD_REPONSES", "{}")),
        "corps": Path(env["STANDARD_CORPS"]).read_text() if env.get("STANDARD_CORPS") else "",
        "modele": env.get("STANDARD_MODELE"),
        "parametres": json.loads(env.get("STANDARD_PARAMETRES", "{}")),
        "aujourd_hui": env.get("STANDARD_AUJOURDHUI") or date.today().isoformat(),
        "horizon_jours": int(env.get("STANDARD_HORIZON", "14")),
        "creneaux": _creneaux(env.get("STANDARD_CRENEAUX", "")),
        "jours_fermes": tuple(int(j) for j in env.get("STANDARD_JOURS_FERMES", "6").split(",") if j),
        "connexions": int(env.get("STANDARD_CONNEXIONS", "4")),
        "consignes_communes": Path(env["STANDARD_CONSIGNES"]).read_text()
        if env.get("STANDARD_CONSIGNES") else "",
    })


def verifier_le_deploiement(environnement: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Dit si le service peut décrocher, **et ce qui manque sinon**.

    À lancer avant de brancher un numéro : il vaut mieux découvrir un pack
    incomplet ici que sur le premier appelant.
    """
    env = dict(environnement if environnement is not None else os.environ)
    config = configuration_depuis_environnement(env)
    service = Service(config, client_modele=ModeleHorsLigne(aujourd_hui=config.aujourd_hui),
                      base=Depot(":memory:").pour(config.tenant))
    manquantes = service.questions_manquantes()
    moteurs = inventaire(env)

    # « pret: false » sans motif oblige a relire le code pour comprendre. Le
    # creneau manquant est le cas le plus traitre : l'agent decroche, comprend,
    # et n'a jamais rien a proposer — aucune erreur, aucun rendez-vous.
    manque = []
    if manquantes:
        manque.append("questions critiques sans réponse : " + ", ".join(manquantes))
    if not config.creneaux:
        manque.append("aucun créneau proposable : poser STANDARD_CRENEAUX "
                      "(par exemple « 09:00,10:30,14:00 »)")
    for role, etat in moteurs.items():
        if not etat["disponible"]:
            manque.append(f"{role} : {etat['detail'] or 'indisponible'}")

    return {
        "tenant": config.tenant,
        "pack": config.pack["pack"],
        "pack_valide": bool(config.pack.get("blocs")),
        "creneaux": len(config.creneaux),
        "questions_manquantes": manquantes,
        # On annonce ce qui TOURNERA, pas ce qui est ecrit dans la configuration :
        # un nom de modele sans cle ne sert a rien, et l'afficher ferait croire
        # qu'un modele repond alors que c'est le moteur de repli.
        "modele": (config.modele if (config.modele and env.get("STANDARD_MODELE_CLE"))
                   else "hors ligne"),
        "moteurs": moteurs,
        # « Pret » veut dire capable de decrocher ET d'entendre : un service qui
        # repond sans comprendre est pire qu'un service qui refuse de demarrer.
        "manque": manque,
        "pret": not manque,
    }


def _client_modele(env, config):
    """Le modele configure, ou le moteur hors ligne — et on ne ment pas sur lequel.

    Sans cle, on rend le moteur deterministe : un service qui refuse de demarrer
    faute de cle est un service qu'on ne peut pas essayer. Mais la commande de
    verification dit alors « hors ligne », et non le nom qu'on aurait aime lire.
    """
    from standard.modele import ClientModeleHttp, TransportHttps

    if not (config.modele and env.get("STANDARD_MODELE_CLE")):
        return ModeleHorsLigne(aujourd_hui=config.aujourd_hui)

    hote = env.get("STANDARD_MODELE_HOTE", "api.groq.com")
    base = env.get("STANDARD_MODELE_BASE", "/openai/v1")
    return ClientModeleHttp(TransportHttps(hote, base), modele=config.modele,
                            cle=env["STANDARD_MODELE_CLE"],
                            parametres=config.parametres)


def _envoyeur_sms(env, config):
    """L'envoyeur, ou rien du tout — jamais un envoyeur qui ne peut pas envoyer.

    Sans expediteur declare, on ne branche rien : l'agent ne demandera pas le
    numero et ne promettra pas de SMS. Avec un expediteur mais sans passerelle,
    on consigne ce qui aurait ete envoye — ce qui permet de relire les messages
    avant de payer le premier, sans que l'agent promette quoi que ce soit.
    """
    from standard.sms import (
        Envoyeur,
        MessageRefuse,
        TransporteurConsigne,
        TransporteurHttp,
    )

    expediteur = env.get("STANDARD_SMS_EXPEDITEUR")
    if not expediteur:
        return None

    nom = (env.get("STANDARD_SMS_NOM")
           or config.reponses.get("A1")
           or config.tenant)
    base, cle = env.get("STANDARD_SMS_BASE"), env.get("STANDARD_SMS_CLE")
    if base and cle:
        import json as _json
        import urllib.request

        def transport(methode, url, corps=None, entetes=None, delai=None):
            requete = urllib.request.Request(
                url, data=_json.dumps(corps).encode(), headers=entetes or {},
                method=methode)
            with urllib.request.urlopen(requete, timeout=delai) as reponse:
                return reponse.status, _json.load(reponse)

        transporteur = TransporteurHttp(transport, base=base, cle=cle)
    else:
        transporteur = TransporteurConsigne(lambda trace: None)

    try:
        return Envoyeur(transporteur, expediteur=expediteur, nom_commercial=nom)
    except MessageRefuse:
        # Un expediteur refuse par l'operateur ferait tomber TOUS les messages :
        # mieux vaut n'en promettre aucun que les perdre tous.
        return None


def _synthese_tolerante(env, fabrique=None):
    """La synthese, bornee, paresseuse, et tolerante a son absence.

    **Bornee** : au-dela de quatre syntheses simultanees, le premier son depasse
    400 ms sur une machine a quatre coeurs (mesure 13). Le plafond vivait dans
    `standard/parole.py` et n'etait applique nulle part — une revue l'a releve.

    **Paresseuse** : on rend le generateur tel quel, sans le materialiser. Le
    premier paquet part avant que la phrase entiere ne soit fabriquee.
    """
    file = FileDeSynthese(int(env.get("STANDARD_SYNTHESES", PARALLELISME_SYNTHESE)))
    try:
        synthetiser = fabrique() if fabrique else choisir_synthese(env)
    except MoteurAbsent:
        return lambda texte: iter([b""])

    def synthese_bornee(texte):
        """Le jeton est pris **le temps de fabriquer un fragment**, et rendu aussitot.

        Le garder jusqu'a l'epuisement du generateur revenait a le garder pendant
        toute la LECTURE de la phrase — les paquets partant au rythme de vingt
        millisecondes. Le plafond de syntheses devenait alors un plafond d'appels
        qui parlent, et le cinquieme appelant decrochait sur plusieurs secondes de
        silence. Ce qui coute du processeur, c'est la fabrication ; c'est donc
        elle, et elle seule, qu'on borne.
        """
        source = synthetiser(texte)
        while True:
            with file.place():
                try:
                    fragment = next(source)
                except StopIteration:
                    return
            yield fragment

    return synthese_bornee


def _base_des_rendez_vous(env, depot, config):
    """La base du service : celle du commercant, ou la notre.

    C'est la moitie de la promesse du produit — « un greffon, pas une ile ». Le
    connecteur existait, teste et documente, et n'etait branche nulle part : le
    service ecrivait toujours chez lui, et `STANDARD_HOTE_BASE` ne servait a
    rien. Un module non branche ne sert a rien.
    """
    hote = env.get("STANDARD_HOTE_BASE")
    if not hote:
        return depot.pour(config.tenant)

    import json as _json
    import urllib.request

    from standard.connecteur import BaseViaConnecteur, ConnecteurHttp

    def transport(methode, url, corps=None, entetes=None, delai=None):
        donnees = _json.dumps(corps).encode() if corps is not None else None
        requete = urllib.request.Request(url, data=donnees, headers=entetes or {},
                                         method=methode)
        try:
            with urllib.request.urlopen(requete, timeout=delai) as reponse:
                brut = reponse.read()
                return reponse.status, (_json.loads(brut) if brut else {})
        except urllib.error.HTTPError as refus:
            # Un code de refus est une REPONSE, pas une panne : le connecteur
            # doit pouvoir distinguer un 409 d'un reseau coupe.
            brut = refus.read()
            return refus.code, (_json.loads(brut) if brut else {})

    return BaseViaConnecteur(ConnecteurHttp(transport, base=hote,
                                            cle_api=env.get("STANDARD_HOTE_CLE", "")))


def construire_serveur(environnement: Mapping[str, str] | None = None) -> ServeurAudioSocket:
    """Assemble le service complet, prêt à recevoir des appels."""
    env = dict(environnement if environnement is not None else os.environ)
    config = configuration_depuis_environnement(env)
    depot = Depot(env.get("STANDARD_BASE", "standard.sqlite3"))

    def creneaux_pris() -> dict[str, set[str]]:
        """Ce que la base sait deja, a chaque appel : un agenda qui ne lit pas
        les rendez-vous existants n'est pas un agenda."""
        from standard.decision import creneaux_couverts

        grille = sorted(config.creneaux)
        occupes: dict[str, set[str]] = {}
        for ligne in depot.lister(config.tenant):
            if not (ligne.get("date") and ligne.get("heure")):
                continue
            # Une coloration de deux heures occupe ce qu'elle dure : sans cela,
            # le creneau suivant restait reservable et deux clients arrivaient
            # ensemble.
            for creneau in creneaux_couverts(ligne["heure"],
                                             ligne.get("duree_minutes"), grille):
                if creneau:
                    occupes.setdefault(ligne["date"], set()).add(creneau)
        return occupes

    base_des_rendez_vous = _base_des_rendez_vous(env, depot, config)

    service = Service(config,
                      client_modele=_client_modele(env, config),
                      base=base_des_rendez_vous,
                      creneaux_pris=creneaux_pris,
                      libres_du_jour=getattr(base_des_rendez_vous,
                                             "libres_du_jour", None),
                      envoyeur_sms=_envoyeur_sms(env, config),
                      corrections=RegistreDeCorrections(depot=depot,
                                                        tenant=config.tenant),
                      secours=depot.pour(config.tenant),
                      # Le questionnaire rempli dans la console : sans ce
                      # branchement, le commercant configure dans le vide.
                      reponses_du_depot=depot)
    service.demarrer()

    journal = JournalDAppels(depot)
    verrou = threading.Lock()
    compteur = {"appels": 0}

    def fabrique_agent():
        with verrou:
            compteur["appels"] += 1
            numero = compteur["appels"]
        # L'identifiant doit etre unique : deux appels simultanes qui partagent
        # le leur produiraient la meme cle d'idempotence, donc le rendez-vous de
        # l'un confirme a l'autre.
        return service.nouvel_appel(f"appel-{numero}-{uuid4().hex[:8]}")

    def archiver(session) -> None:
        """Verser l'appel au journal. Sans cela, la console est vide par
        construction et la preuve d'annonce exigee par l'AI Act est jetee avec
        l'objet de session."""
        agent = getattr(session, "agent", None)
        journal_appel = getattr(agent, "journal", None)
        if journal_appel is None:
            return
        tours = list(journal_appel.tours)
        issue = tours[-1]["genre"] if tours else "sans suite"
        service.metriques.premiers_fragments_ms.extend(
            getattr(session, "premiers_fragments_ms", []))
        journal.enregistrer(config.tenant, {
            "uuid": session.identifiant or f"sans-uuid-{uuid4().hex[:8]}",
            "debut": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            # Elle valait zero pour tous les appels : la console affichait
            # « 0 s » partout, et la premiere regle de detection d'echec —
            # raccroche avant dix secondes — ne pouvait pas exister.
            "duree_s": getattr(session, "duree_s", 0),
            "issue": {"confirmation": "rendez-vous"}.get(issue, issue),
            "bruite": any(t.get("bruite") for t in tours),
            "interruptions": getattr(session, "interruptions", 0),
            "preuve_annonce": session.preuve_d_annonce or {"conforme": False},
            "confirmations_orphelines": journal_appel.confirmations_orphelines,
            "tours": tours,
            # T6 : une ligne par tour, avec ses latences et son identifiant.
            "mesures": list(getattr(session, "mesures", [])),
            # Et le motif d'echec, s'il y en a un : un appel « reussi » se
            # reconnait mal, un appel rate se reconnait a quatre signes.
            "echec": detecter_l_echec({
                "duree_s": getattr(session, "duree_s", 0), "tours": tours}),
        })

    try:
        transcrire = choisir_transcription(env)
    except MoteurAbsent:
        # On demarre quand meme, mais l'agent le DIRA au lieu de faire semblant
        # d'ecouter : c'est la seule facon d'essayer un deploiement incomplet
        # sans se mentir.
        def transcrire(audio, frequence):
            raise MoteurAbsent("aucun moteur de transcription : l'appel ne peut pas "
                               "etre compris")

    serveur = ServeurAudioSocket(
        seuil_bruite_db=config.seuil_bruite_db,
        fabrique_agent=fabrique_agent,
        transcrire=transcrire,
        synthetiser=_synthese_tolerante(env),
        hote=env.get("STANDARD_HOTE", "0.0.0.0"),
        port=int(env.get("STANDARD_PORT", "8090")),
        sur_fin=archiver)
    # La supervision n'est utile que si elle est ATTEIGNABLE depuis ce qui tourne.
    serveur.service = service
    serveur.journal = journal
    # La duree de conservation annoncee au registre n'est vraie que si quelqu'un
    # purge : c'est ce fil-la, demarre et arrete avec le serveur.
    serveur.entretien = Entretien(journal)
    # Sans point d'etat, l'exploitant apprend la panne par un commercant qui
    # telephone. Sur la boucle locale par defaut : ce qui doit sortir de la
    # machine passe par un proxy, pas par ce port.
    serveur.sante = ServeurDeSante(serveur, hote=env.get("STANDARD_HOTE_SANTE", "127.0.0.1"),
                                   port=int(env.get("STANDARD_PORT_SANTE", "8092")))
    return serveur
