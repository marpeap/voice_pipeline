"""Le registre des traitements (RGPD art. 30), dérivé du code qui tourne.

Un registre recopié à la main devient faux au premier changement de moteur. Les
mentions obligatoires — finalité, base légale, catégories, destinataires,
durée, transferts hors UE — sont donc **lues dans la configuration réelle** :
si le salon branche un moteur distant, le sous-traitant apparaît ; s'il reste
en local, la ligne dit qu'aucune donnée ne sort de la machine.
"""

from standard.registre import registre_des_traitements, rendre_en_texte
from standard.regles import CONSERVATION_JOURS

MENTIONS = ("finalite", "base_legale", "categories", "destinataires",
            "duree_conservation_jours", "transferts_hors_ue", "responsable",
            "mesures_de_securite")


def local():
    return {"STANDARD_TENANT": "salon-1", "STANDARD_STT": "local",
            "STANDARD_TTS": "piper"}


def test_les_mentions_obligatoires_sont_toutes_presentes():
    registre = registre_des_traitements(local())
    for traitement in registre["traitements"]:
        for mention in MENTIONS:
            assert mention in traitement, f"{traitement['nom']} sans {mention}"


def test_la_duree_annoncee_est_celle_que_le_menage_applique():
    """Une durée écrite ici et purgée là-bas ne doit jamais diverger."""
    registre = registre_des_traitements(local())
    appels = next(t for t in registre["traitements"] if t["nom"] == "appels")
    assert appels["duree_conservation_jours"] == CONSERVATION_JOURS


def test_en_tout_local_le_registre_dit_qu_aucune_donnee_ne_sort():
    registre = registre_des_traitements(local())
    appels = next(t for t in registre["traitements"] if t["nom"] == "appels")
    assert appels["transferts_hors_ue"] == "aucun"
    assert all("machine" in d or "aucun" in d for d in appels["destinataires"])


def test_un_moteur_distant_apparait_comme_destinataire():
    env = {**local(), "STANDARD_STT": "distant",
           "STANDARD_STT_BASE": "https://api.exemple.fr/v1", "STANDARD_STT_CLE": "x"}
    appels = next(t for t in registre_des_traitements(env)["traitements"]
                  if t["nom"] == "appels")
    assert any("api.exemple.fr" in d for d in appels["destinataires"])
    # La clé ne doit jamais se retrouver dans un document qu'on imprime.
    assert "x" not in str(appels["destinataires"]).replace("exemple", "")


def test_le_sms_n_apparait_que_s_il_est_branche():
    sans = registre_des_traitements(local())
    assert not any(t["nom"] == "sms" for t in sans["traitements"])
    avec = registre_des_traitements({**local(), "STANDARD_SMS_EXPEDITEUR": "Elegance",
                                     "STANDARD_SMS_BASE": "https://sms.exemple.fr"})
    assert any(t["nom"] == "sms" for t in avec["traitements"])


def test_le_registre_se_rend_en_texte_lisible():
    texte = rendre_en_texte(registre_des_traitements(local()))
    assert "Registre des traitements" in texte
    assert str(CONSERVATION_JOURS) in texte
    assert "art. 30" in texte


def test_le_registre_dit_que_le_service_n_appelle_jamais():
    """La loi du 11 août 2026 impose un consentement préalable pour prospecter.
    Le service ne prospecte pas : il faut que le registre le dise, parce que
    c'est la première question qu'on lui posera."""
    appels = next(t for t in registre_des_traitements(local())["traitements"]
                  if t["nom"] == "appels")
    mesures = " ".join(appels["mesures_de_securite"])
    assert "aucun appel sortant" in mesures
    assert "11 août 2026" in mesures
