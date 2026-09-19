"""La langue de l'appelant — servir à moitié est pire que passer la main.

L'AI Act demande que l'information soit donnée « dans la langue de la
conversation ». Le produit ne parle que français : un appelant qui s'adresse à
lui en anglais doit donc être **transféré**, et l'entendre dans sa langue.

La détection est volontairement grossière et **prudente** : en cas de doute, on
répond français. Transférer un appelant français parce qu'il a dit « allô »
serait pire que le défaut qu'on répare — et une transcription abîmée par le STT
n'est pas une langue étrangère, c'est du charabia français.
"""

from __future__ import annotations

from standard.texte import aplatir

FRANCAIS = "fr"
MOTS_MINIMUM = 4        # en dessous, une detection se trompe plus qu'elle n'aide

# Des mots frequents et **discriminants** : ils n'existent pas, ou tres peu, dans
# les autres langues de la liste. On ne compte pas « no », « la », « un ».
INDICES = {
    # Des mots qui n'existent PAS en francais : « you », « do », « the » ou
    # « i » traineraient dans une phrase francaise ordinaire — « week-end »,
    # « brushing », « soin » — et deux d'entre eux suffiraient a transferer un
    # client francais. Transferer a tort est pire que le defaut qu'on repare.
    "en": {"hello", "would", "like", "book", "appointment", "please", "thanks",
           "morning", "afternoon", "tomorrow", "could", "anything", "speak",
           "thursday", "friday", "monday", "tuesday", "wednesday", "saturday",
           "sunday", "available", "booking", "english", "sorry", "help"},
    "es": {"hola", "quisiera", "cita", "gracias", "buenos", "manana", "jueves",
           "viernes", "para", "el", "una", "por", "favor"},
    "de": {"hallo", "guten", "termin", "bitte", "danke", "morgen", "donnerstag",
           "hatten", "ich", "sie", "haben"},
}

PASSAGES = {
    "en": "I only speak French. Let me transfer you to someone, one moment please.",
    "es": "Solo hablo francés. Le paso con alguien, un momento por favor.",
    "de": "Ich spreche nur Französisch. Ich verbinde Sie, einen Moment bitte.",
}
PASSAGE_PAR_DEFAUT = ("Je vous passe quelqu'un du salon. "
                      "One moment please, I am transferring you.")


def _mots(texte: str) -> list[str]:
    return aplatir(texte, garder="a-z ").split()


def detecter_langue(transcription: str) -> str:
    """Rend un code de langue — et **français en cas de doute**."""
    mots = _mots(transcription)
    if len(mots) < MOTS_MINIMUM:
        return FRANCAIS

    scores = {langue: sum(1 for mot in mots if mot in indices)
              for langue, indices in INDICES.items()}
    meilleure = max(scores, key=scores.get)
    # Il faut une proportion franche, pas un mot isole : « un rendez-vous pour
    # le week-end » contient des mots anglais sans etre de l'anglais.
    # Il faut au moins deux mots franchement etrangers, et un tiers de l'enonce.
    if scores[meilleure] >= max(2, len(mots) // 3) and scores[meilleure] >= 2:
        return meilleure
    return FRANCAIS


def phrase_de_passage(langue: str) -> str:
    """Ce que l'agent dit avant de transférer. Un appelant ne reste jamais sans
    réponse, même dans une langue qu'on n'a pas prévue."""
    return PASSAGES.get(langue, PASSAGE_PAR_DEFAUT)
