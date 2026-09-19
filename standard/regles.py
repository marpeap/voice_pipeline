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
