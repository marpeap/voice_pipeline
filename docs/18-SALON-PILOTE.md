# Le salon pilote — ce qu'on lui demande, et dans quel ordre

> Le corpus de test (`07`) exige **60 à 100 appels réels français**. C'est la seule chose du chantier qu'aucune mesure, aucune recherche et aucun agent ne peut produire : **il faut un vrai salon et de vrais appelants.**
> Ce document contient les pièces prêtes à l'emploi. **Deux étapes, et la première ne demande aucune technique.**

---

## Étape A — Compter les appels pendant une semaine

**Ce que ça donne** : les **deux chiffres qui manquent** à tout le chiffrage — le volume réel d'appels d'un salon (posé à 10/jour, au doigt mouillé) et la répartition des intentions. Toute la colonne de coût variable en dépend **linéairement**.

**Ce que ça coûte au salon** : une feuille près du téléphone, une barre par appel. **Aucun enregistrement, aucune donnée personnelle, aucune installation, aucun changement chez lui.**

> ⚠️ **Conséquence utile** : même un salon dont le produit est gelé peut faire l'étape A — une feuille de papier ne touche ni au site, ni à l'API, ni à quoi que ce soit.

### La feuille (à imprimer telle quelle)

```
SEMAINE DU ____ AU ____            SALON : ________________

Une barre par appel reçu, dans la colonne qui correspond.
Si vous ne savez pas, mettez la barre dans « Autre ». Ce n'est pas grave.

                     Lun   Mar   Mer   Jeu   Ven   Sam
Prise de RDV        ____  ____  ____  ____  ____  ____
Report / annulation ____  ____  ____  ____  ____  ____
Question (prix,
horaires, conseil)  ____  ____  ____  ____  ____  ____
Autre               ____  ____  ____  ____  ____  ____

Appels manqués (sonnerie sans réponse), si vous les voyez : ______

Une remarque, si l'envie vous prend :
_______________________________________________________
```

### Ce qu'on en tire
- **Volume** → le coût variable par salon, donc le prix.
- **Répartition des intentions** → l'ordre des missions à construire. La recherche A6 suggère que **« comme la dernière fois »** et **le report tardif** dominent, contre l'intuition qui place la prise de rendez-vous en tête. Cette feuille le confirmera ou l'infirmera.
- **Appels manqués** → l'argument de vente le plus direct qui soit, et **chiffré chez lui**, pas emprunté à une étude.

---

## Étape B — Enregistrer 60 à 100 appels réels

**Uniquement après L1**, et sous cadre écrit. C'est ce qui donnera le **vrai WER français au téléphone** — celui d'aujourd'hui (7,8 %) est mesuré sur de la **parole de synthèse**, plus propre que la vraie. **C'est le risque n°1 du lot L1.**

### Ce qu'il faut réunir
1. **Accord écrit du salon** (modèle ci-dessous) — il reste responsable de traitement, nous sommes sous-traitant.
2. **Annonce en début d'appel**, non désactivable.
3. **Rétention bornée** : transcription conservée, **audio supprimé après transcription** — c'est la bonne pratique que la CNIL érige elle-même, et l'enregistrement systématique est proscrit (« ni permanent ni systématique »).

### L'annonce (à dire, pas à écrire)

> « Bonjour, vous êtes bien au salon [NOM]. Je suis **l'assistant automatique** du salon. Cet appel est **enregistré pour améliorer le service**, et l'enregistrement est supprimé après transcription. Que puis-je faire pour vous ? »

Trois obligations tenues en une phrase : l'**annonce d'IA** (AI Act art. 50 §1, applicable depuis le 02/08/2026), l'**information d'enregistrement** et sa **finalité**. Et elle est courte — ce qui, d'après la mesure 1, la fait partir en quelques dizaines de millisecondes.

### L'accord (une page, à signer)

```
ACCORD DE TEST — AGENT TÉLÉPHONIQUE

Entre [SALON], représenté par ________, et Marpeap Digitals.

1. OBJET. Le salon accepte qu'un numéro de test réponde à ses appels
   pendant [DURÉE], afin de mesurer la qualité de compréhension du
   français au téléphone.

2. CE QUI EST ENREGISTRÉ. Les appels reçus sur le numéro de test.
   Chaque appelant est informé dès la première phrase qu'il parle à un
   assistant automatique et que l'appel est enregistré.

3. CE QUI EST CONSERVÉ. La transcription écrite. L'audio est supprimé
   après transcription, et au plus tard sous 30 jours.

4. CE QUI N'EST PAS FAIT. Aucune donnée n'est vendue, cédée, ni utilisée
   pour autre chose que la mise au point de l'agent. Aucun appel n'est
   écouté par un tiers.

5. ARRÊT. Le salon peut arrêter le test à tout moment, sans motif et
   sans délai, par simple message. Les enregistrements sont alors
   supprimés sous 7 jours.

6. RÔLES. Le salon est responsable de traitement, Marpeap Digitals
   sous-traitant au sens de l'article 28 du RGPD.

Fait à ______, le ______.        Signatures :
```

⚠️ **À faire relire par un juriste avant signature** — c'est l'un des huit points identifiés comme relevant d'un avocat. Ce modèle sert à **discuter**, pas à engager.

---

## L'argumentaire, si le salon demande « pourquoi moi ? »

Trois phrases, et aucune ne promet quoi que ce soit :

1. **« Vous ratez des appels et vous ne savez pas combien. »** L'étape A le lui dit — et c'est **son** chiffre, pas une statistique de brochure.
2. **« Ça ne change rien chez vous. »** Étape A : une feuille. Étape B : un numéro de test, en plus du sien, qu'il peut couper d'un message.
3. **« Vous verrez le résultat avant tout le monde. »** Le premier salon équipé sera celui dont les remarques ont façonné le produit — et la boucle de correction (`06`) est faite pour que ses corrections tiennent.

**Ce qu'on ne lui promet pas** : ni un agent qui marche pendant le test (L1 n'est pas L5), ni une remise, ni une date. Un pilote qui se sent client déçu vaut moins qu'un pilote qui se sait pilote.

---

## Ce qu'il reste à faire, et par qui

| Quoi | Qui |
|---|---|
| Trouver le salon, remettre la feuille de comptage | **Adnan** |
| Faire relire l'accord par un juriste | **Adnan** |
| Dépouiller la feuille et corriger le chiffrage | moi, dès réception |
| Préparer le numéro de test et l'annonce | moi, au lot L1 |
