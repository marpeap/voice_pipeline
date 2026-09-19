"""Reconnaître un appel de prospection — et ne rien lui promettre.

`docs/06` promet parmi les indicateurs de la console : « spams filtrés et non
facturés ». Rien ne les filtrait, rien ne les comptait, et le salon payait donc
ses appels de démarchage au prix de ses clients.

Depuis le 11 août 2026 (loi du 11/08/2026, décret n° 2026-662), la prospection
téléphonique vers un **consommateur** exige un consentement préalable. Un salon
est un professionnel : ces appels lui arrivent encore, et c'est à l'agent de les
tenir à distance.

**Deux gardes, parce que le faux positif est bien plus cher que le faux
négatif** : raccrocher au nez d'un client coûte un client, servir un démarcheur
coûte trente secondes.

1. il faut une **formule de prospection** explicite ;
2. et **aucune demande de rendez-vous** dans la même phrase — un démarcheur qui
   parle de rendez-vous est servi comme un client, sans discuter.
"""

from __future__ import annotations

from standard.texte import aplatir

# Ce qu'on entend au premier tour d'un appel de prospection. Chaque entree est
# une formule ENTIERE : un mot isole comme « offre » ou « proposer » se dit
# aussi bien chez un client.
FORMULES = (
    "pour vous proposer", "je vous propose", "nous vous proposons",
    "notre solution", "notre offre", "une offre commerciale",
    "votre referencement", "votre visibilite sur internet", "votre site internet",
    "renovation energetique", "isolation", "panneaux solaires",
    "eligible au cpf", "compte personnel de formation",
    "je suis partenaire", "nous sommes partenaires",
    "votre contrat d energie", "votre fournisseur d electricite",
    "mutuelle", "assurance professionnelle", "votre tresorerie",
    "developper votre chiffre d affaires", "gagner de nouveaux clients",
)

# Ce qui, dans la meme phrase, rend l'appel legitime quoi qu'il arrive.
MOTIFS_DE_CLIENT = (
    "rendez vous", "rdv", "creneau", "disponibilite", "reserver", "reservation",
    "prendre date", "ouvert", "ouverts", "horaire", "horaires", "annuler",
    "decaler", "deplacer", "reporter", "coupe", "couleur", "brushing",
)


def _plat(texte: str) -> str:
    return aplatir(texte, garder="a-z' ").replace("'", " ")


def est_un_demarchage(transcription: str) -> bool:
    """Vrai seulement si la formule est explicite **et** qu'aucun motif de
    client ne figure dans la meme phrase. Le doute profite a l'appelant."""
    plat = _plat(transcription)
    if not plat:
        return False
    if any(_plat(motif) in plat for motif in MOTIFS_DE_CLIENT):
        return False
    return any(_plat(formule) in plat for formule in FORMULES)
