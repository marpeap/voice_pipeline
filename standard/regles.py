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

# --- l'ecoute (mesures 9 et 10) ---------------------------------------------

PREROLL_MS = 300
"""Mesure 9 : un moteur streaming perd le premier mot d'un enonce sur quatre.
Le flux garde ce qui precede le seuil de parole."""

SEUIL_BRUITE_DB = 15
"""Mesure 10 : a 10-15 dB — la rue, la voiture — le WER double, et il double sur
les entites. En dessous de ce seuil, la strategie de capture change."""

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


def indice_dans(mot: str, vocabulaire, reserves=()) -> int | None:
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
               if _correspond(mot, entree)]
    return trouves[0] if len(trouves) == 1 else None


def _correspond(mot: str, entree: str) -> bool:
    if mot == entree:
        return True
    if len(mot) < LONGUEUR_MINIMALE_POUR_UN_PREFIXE:
        return False
    if mot.startswith(entree) or entree.startswith(mot):
        return True
    # « JEDI » pour « jeudi » : le milieu du mot aussi se perd, pas seulement sa
    # fin (banc du 19/09). Une lettre d'ecart, jamais deux : au-dela, on
    # rapprocherait « mardi » de « mars ».
    return _une_lettre_d_ecart(mot, entree)


def _une_lettre_d_ecart(a: str, b: str) -> bool:
    """Vrai si une seule insertion, suppression ou substitution les separe."""
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) == 1
    court, long = (a, b) if len(a) < len(b) else (b, a)
    for coupe in range(len(long)):
        if long[:coupe] + long[coupe + 1:] == court:
            return True
    return False
