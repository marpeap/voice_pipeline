"""Les valeurs qui font foi — une seule source, jamais recopiee.

Chaque nombre de ce fichier vient d'une mesure, et chaque mesure est citee. Un
seuil recopie a deux endroits derive en silence le jour ou l'un des deux bouge ;
ici, il n'existe qu'en un exemplaire, et les tests comme la porte de
non-regression le lisent au meme endroit que le produit.
"""

# --- ce que l'agent n'a pas le droit de dire --------------------------------

VERBES_DE_CONFIRMATION = (
    "c'est noté", "c'est enregistré", "est annulé", "j'ai enregistré", "c'est fait",
)
"""Mesure 14 : deux confirmations orphelines en douze tours.

Ces formulations n'appartiennent qu'a `standard.ecriture`, et seulement apres une
relecture reussie. Partout ailleurs — decision, comprehension, assemblage — leur
presence dans une phrase est un defaut, et c'est ce que verifient les tests.
"""


def contient_une_confirmation(phrase: str) -> bool:
    """Vrai si la phrase affirme qu'une ecriture a eu lieu."""
    plat = phrase.lower()
    return any(verbe in plat for verbe in VERBES_DE_CONFIRMATION)


# --- les seuils de la machine a etats (mesures 15 a 18) ---------------------

SEUIL_CONFIANCE = 0.7
"""En dessous, une entite est douteuse : elle devient une question, pas une supposition."""

REFUS_AVANT_OUBLI = 2
"""Mesure 16 : deux refus de suite sur la meme entite l'invalident. Sans cela, la
machine garde une valeur que l'appelant ne peut plus corriger — la boucle infinie
polie."""

TOURS_SANS_PROGRES_AVANT_TRANSFERT = 2
"""Mesure 18 : un compteur d'anti-boucle compte des VALEURS NEUVES, pas des tours.
Deux tours steriles suffisent au telephone."""

ECART_MINIMAL_ENTRE_HORAIRES_MIN = 60
"""Regle E2, mesuree sur l'audio (mesure 19) : « neuf heures, neuf heures
quarante-cinq » est revenu du canal sans sa premiere option."""

# --- la parole (mesures 13, 14, 20) -----------------------------------------

SEUIL_GARDE_MS = 700
"""Au-dela, l'agent parle plutot que de laisser le silence : 935 ms au p90 et
8 751 ms au pire chez le fournisseur."""

SILENCE_DE_FIN_MS = 700
"""Au-dela, on considere que l'appelant a fini de parler.

Meme valeur que le delai de garde, et ce n'est pas un hasard : c'est la duree
au-dela de laquelle un silence cesse d'etre une respiration. Les deux constantes
existent separement parce qu'elles peuvent diverger — l'une se regle sur la
patience de l'appelant, l'autre sur celle du fournisseur."""

PARALLELISME_SYNTHESE = 4
"""Mesure 13 : au-dela de quatre syntheses simultanees, le premier son passe
400 ms sur une machine a quatre coeurs."""

APPELS_SIMULTANES_MAX = 2 * PARALLELISME_SYNTHESE
"""Au-dela, la machine ne tient plus la promesse de 400 ms.

La mesure 13 plafonne la synthese a quatre voix simultanees ; au-dela, les
appels attendent leur tour de parole. Le double laisse respirer les tours ou
personne ne parle, et rend la ligne au-dela — mieux vaut un appel que le bord
telephonique renvoie vers le poste du salon qu'un appel qui gresille."""

# --- l'ecoute (mesures 9 et 10) ---------------------------------------------

PREROLL_MS = 300
"""Mesure 9 : un moteur streaming perd le premier mot d'un enonce sur quatre.
Le flux garde ce qui precede le seuil de parole."""

DUREE_MINIMALE_D_UN_VRAI_APPEL_S = 10
"""En dessous, l'appel n'a pas eu lieu : personne ne prend un rendez-vous en six
secondes. C'est la premiere des quatre regles de detection d'echec (docs/17 T6)."""

REFORMULATIONS_AVANT_ECHEC = 3
"""Trois fois « je vais faire autrement » : l'agent tourne, et l'appelant le
sait avant nous."""

TOURS_OU_LE_DEMARCHAGE_SE_COUPE = 2
"""Passe les premiers mots, une phrase commerciale peut venir d'un client qui
explique son metier : on ne coupe pas une conversation deja engagee. Le faux
positif coute un client, le faux negatif trente secondes."""

TOURS_FENETRE_CORRECTION_NOM = 2
"""Combien de tours apres la confirmation un nom seul vaut encore correction.

Banc du 19/09 : la phrase de correction est souvent abimee (« N'EN S'ÉTONNANT
DE MARTIN » pour « non c'est au nom de Martin »), et l'appelant redit alors le
nom seul au tour suivant. Un seul tour de fenetre ratait ce rattrapage ; deux le
couvrent. La fenetre se ferme des qu'une nouvelle demande est comprise."""

RAPPEL_LA_VEILLE = True
"""Un SMS envoye 24 h avant reduit les absences de 30 a 35 % (recherche du
20/09, sources metier concordantes). C'est le premier benefice mesurable qu'un
salon attend d'un logiciel de rendez-vous."""

FENETRE_DE_RAPPEL = (10, 12)
"""Fin de matinee la veille : la charte AF2M place les SMS entre 8 h et 21 h 30,
et le metier recommande ce creneau — assez tot pour que le client reorganise sa
journee, assez tard pour ne pas le reveiller."""

CONSERVATION_JOURS = 90
"""Duree de conservation des appels et de leurs transcriptions.

La CNIL recommande **six mois au maximum** pour les enregistrements d'appels et
leurs transcriptions, hors obligation sectorielle. Un standard de salon n'a
aucune raison d'aller au bout : 90 jours couvrent la saison et les litiges de
rendez-vous. C'est cette valeur que le registre des traitements annonce, et
`entretien` la rend vraie en purgeant."""

SEUIL_BRUITE_DB = 15
"""Mesure 10 : a 10-15 dB — la rue, la voiture — le WER double, et il double sur
les entites. En dessous de ce seuil, la strategie de capture change."""

RELANCES_MUETTES_AVANT_TRANSFERT = 2
"""Deux relances, puis un humain. Banc du 19/09 : un « oui » de six dixiemes de
seconde revient vide du moteur — et l'agent restait muet, ligne ouverte, ce qui
est le pire etat d'un standard. Au-dela de deux, ce n'est plus l'audio qui est
en cause."""

DUREE_MINIMALE_POUR_UNE_RELANCE_MS = 300
"""En dessous, ce n'etait pas une parole : une porte, une toux, un blanc. On ne
relance pas sur du bruit."""

SEUIL_PAROLE = 500
"""Amplitude moyenne au-dela de laquelle on considere que l'appelant parle."""


# --- le calendrier, ecrit une seule fois -------------------------------------

JOURS = ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche")
MOIS = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre")
"""`decision` les prononce, `sms` les écrit, `hors_ligne` les lit.

Ils étaient recopiés dans les trois — or la confirmation écrite est censée
reprendre **exactement** la date que l'agent a prononcée (règle E1, mesure 19).
Deux listes qui divergent d'un accent, et la promesse tombe.
"""


LONGUEUR_MINIMALE_POUR_UN_PREFIXE = 4
"""En deca, un prefixe ne designe plus rien : « mar » vaut mardi et mars."""


def indice_dans(mot: str, vocabulaire, reserves=(), ecart: int = 1) -> int | None:
    """Retrouve un mot du calendrier **meme abime a la fin**.

    Mesure du 19/09, cinq appels joues avec les vrais moteurs : « jeudi » revient
    « JEUDI », « JEUDIS » ou « JEUDIRE » selon l'endroit ou le flux est coupe. La
    fin d'un mot est ce que le canal telephonique abime le plus, et la refuser
    coutait **un rendez-vous sur deux** sur ce banc.

    On accepte donc le prefixe commun, et lui seul. Deux entrees qui
    correspondent rendent `None` : on ne devine pas un jour, on redemande.
    Les deux comparants sont supposes deja aplatis (minuscules, sans accents).

    `reserves` protege les mots qui veulent deja dire quelque chose : « sept »
    est un prefixe de « septembre », mais c'est d'abord un nombre — sans cette
    garde, « le dix sept septembre » devenait le 10 septembre.
    """
    if mot in reserves:
        return vocabulaire.index(mot) if mot in vocabulaire else None

    trouves = [index for index, entree in enumerate(vocabulaire)
               if _correspond(mot, entree, ecart)]
    return trouves[0] if len(trouves) == 1 else None


FUSION_PREMIER_FRAGMENT_MAX = 3
"""Au-dela, ce n'est plus un mot coupe en deux : c'est deux mots."""


def indice_dans_les_mots(mots, vocabulaire, reserves=()) -> int | None:
    """Comme `indice_dans`, mais sur une phrase — et en recollant les mots coupes.

    Banc du 19/09 : le moteur rend « jeudi » en deux morceaux, « JE DIS ». Le
    mot existe, il est simplement fendu ; on tente donc la fusion des paires
    dont le premier fragment est minuscule, et **seulement** quand aucun mot
    entier n'a repondu.

    Ce que cela coute : « je dis » dans une autre phrase pourrait devenir jeudi.
    Une date lue ne s'ecrit jamais seule — l'agent l'enonce et attend un accord
    (regle E1) —, donc le pire cas est une question de trop, pas un rendez-vous
    faux.
    """
    for mot in mots:
        rang = indice_dans(mot, vocabulaire, reserves)
        if rang is not None:
            return rang
    for premier, second in zip(mots, mots[1:]):
        if len(premier) > FUSION_PREMIER_FRAGMENT_MAX:
            continue
        # Deux lettres d'ecart tolerees ICI seulement : « je dis » recolle donne
        # « jedis », et « jeudi » en est a deux operations. Le risque est borne
        # par les trois gardes ci-dessus — fragment minuscule, aucun mot entier
        # reconnu, et une seule entree correspondante.
        rang = indice_dans(premier + second, vocabulaire, reserves, ecart=2)
        if rang is not None:
            return rang
    return None


def _correspond(mot: str, entree: str, ecart: int = 1) -> bool:
    if mot == entree:
        return True
    if len(mot) < LONGUEUR_MINIMALE_POUR_UN_PREFIXE:
        return False
    if mot.startswith(entree) or entree.startswith(mot):
        return True
    # « JEDI » pour « jeudi » : le milieu du mot aussi se perd, pas seulement sa
    # fin (banc du 19/09). Une lettre d'ecart par defaut, jamais deux sur un mot
    # entier : au-dela, on rapprocherait « mardi » de « mars ».
    return distance(mot, entree) <= ecart


def distance(a: str, b: str) -> int:
    """Levenshtein, sur des mots de calendrier — jamais sur des phrases."""
    if a == b:
        return 0
    precedente = list(range(len(b) + 1))
    for i, lettre_a in enumerate(a, start=1):
        courante = [i]
        for j, lettre_b in enumerate(b, start=1):
            courante.append(min(precedente[j] + 1,
                                courante[j - 1] + 1,
                                precedente[j - 1] + (lettre_a != lettre_b)))
        precedente = courante
    return precedente[-1]
