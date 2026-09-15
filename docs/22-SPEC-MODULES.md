# Spécification des modules de l'étape 1 — prête à coder

> **Ce document existe pour que le feu vert soit immédiatement exécutable.** Il fixe les frontières entre modules, ce qui entre et ce qui sort de chacun, et le test qui prouve qu'il marche. Il ne contient **aucun code produit** : des signatures, des contrats et des cas de test, tous dérivés de mesures, jamais d'intuition.
>
> Règle qui traverse tout le document : **chaque module naît avec le test qui l'échoue.** Les vingt mesures ont déjà produit les cas ; il n'y a pas à les inventer.

---

## 0. La frontière qui commande toutes les autres

```
    audio ──▶ [ecoute] ──▶ texte ──▶ [comprehension] ──▶ proposition
                                                              │
                                                              ▼
    audio ◀── [parole] ◀── phrase ◀────────────────── [decision] ──▶ [ecriture]
```

**Le modèle de langage vit dans `comprehension`, et nulle part ailleurs.** Il ne rédige pas la phrase entendue par l'appelant (`decision` le fait), il n'écrit pas en base (`ecriture` le fait), il ne décide pas de raccrocher. Mesuré : sans cette frontière, 6 tours sur 12 portent une faute, dont 2 confirmations orphelines (mesure 14) ; avec elle, 0 (mesure 15).

---

## 1. `ecoute` — de l'audio au texte

**Entre** : des fragments audio 8 kHz, tels qu'ils arrivent du téléphone.
**Sort** : des transcriptions partielles puis une transcription finale, chacune horodatée.

**Contrat**

| Obligation | Origine |
|---|---|
| Le flux est **ouvert et alimenté avant que l'appelant parle** ; le détecteur d'activité vocale conserve l'audio d'**avant** son seuil (pré-roll) | Mesure 9 : un moteur streaming perd **un premier mot sur quatre** |
| Le rééchantillonnage se fait **dans le processus**, jamais par un processus externe | Mesure 6 : 11 ms de travail, 45 ms pour lancer `ffmpeg` |
| Les connexions vers un moteur distant sont **ouvertes au démarrage et maintenues** | Mesure 4 : 2 040 ms contre 378 ms |
| Le **rapport signal/bruit** est estimé sur les premières secondes et attaché à chaque transcription | Mesure 10 : à 10-15 dB le WER double, et la stratégie doit changer |
| Le moteur (nom, paramètres, fournisseur) vit **en configuration** | Mesure 17 : catalogue modifié 3 fois en 48 h |

**Tests qui doivent échouer avant d'être écrits**
- Sur dix appels simulés, **le premier mot de la première phrase est transcrit dix fois** (recette de `docs/17` T-préroll).
- Un fichier à 10 dB de bruit produit une transcription **marquée « bruité »**, et cette marque remonte jusqu'à `decision`.
- Couper le réseau du moteur distant en cours d'appel : `ecoute` bascule sur le moteur de repli **sans perdre le tour en cours**.

---

## 2. `comprehension` — du texte à une proposition

**Entre** : une transcription, l'état connu de la conversation, le calendrier **calculé par la machine**.
**Sort** : une proposition structurée, jamais une phrase.

```
proposition = {
  intention   : rdv | report | annulation | question | inconnu,
  date        : AAAA-MM-JJ | null,
  heure       : HH:MM | null,
  prestation  : texte | null,
  confiance   : { champ -> 0.0 a 1.0 },
  manque      : [ champ, ... ]
}
```

**Contrat**

| Obligation | Origine |
|---|---|
| **Aucune date ne vient du modèle** : le calendrier est injecté | Mesure 14 : « le premier du mois prochain est un dimanche », inventé |
| Le modèle n'a **aucun verbe de confirmation** à sa disposition | Mesure 14 : « votre rendez-vous de demain matin est annulé », rien en base |
| Une entité que la transcription ne porte pas **doit sortir à `null`**, avec une confiance basse | Mesure 15 : la seule invention tentée a été arrêtée par la validation |
| **La demande explicite d'un humain est détectée sur la transcription, avant l'appel au modèle** | Mesure 17 : ça n'a pas à être interprété, ça a à être exécuté |
| Le nom du modèle **et ses paramètres d'appel** vivent en configuration | Mesure 17 : le remplaçant refusait un paramètre que le précédent acceptait |
| Toute erreur du fournisseur **remonte telle quelle** | Mesure 17 : un `KeyError` muet a coûté trois quarts d'heure |

**Tests**
- Les douze énoncés de la mesure 14 : **zéro entité inventée**, chaque trou sorti à `null`.
- « passez-moi quelqu'un » : traité **sans qu'aucune requête ne parte** vers le modèle.
- Réponse du fournisseur non conforme (JSON tronqué, 429, 400) : l'erreur est journalisée **avec son message d'origine**, et le tour bascule sur le repli.

---

## 3. `decision` — la machine à états

**Entre** : une proposition, l'état de la conversation, l'agenda réel.
**Sort** : un genre (`question`, `refus`, `hors horizon`, `reformulation`, `proposition`, `transfert`) et **la phrase que dira l'agent** — composée par la machine, jamais par le modèle.

**Les cinq seuils, tous mesurés (mesure 18)**

| Déclencheur | Seuil | Effet |
|---|---|---|
| Demande explicite d'un humain | immédiat | transfert |
| Même entité refusée | 2 fois de suite | l'entité est **oubliée** et redemandée **avec ses valeurs possibles** |
| Phrase identique à la précédente | 1ʳᵉ fois | **changement de stratégie** : une entité à la fois, choix explicites énoncés |
| Phrase identique à la précédente | 2ᵉ fois | transfert |
| Tours sans **valeur neuve** | 2 | transfert |

**Deux pièges déjà payés, à ne pas repayer**

1. **« Absent de l'agenda » n'est pas « fermé ».** Trois réponses distinctes : hors horizon, fermé (jour non ouvré vérifié), non reconnu. Sinon la machine ment à son tour, et de façon invérifiable par le client (mesure 15).
2. **Un compteur d'anti-boucle compte des valeurs neuves**, pas des tours ni des changements. Les deux autres définitions échouent **en silence** : oublier une valeur passe pour un progrès, et un appelant qui se répète fait repasser l'entité de vide à remplie à chaque tour (mesure 18).

**Règles d'énonciation, mesurées sur l'audio (mesure 19)**
- La date s'énonce **jour + quantième + mois** ; aucune confirmation ne repose sur le seul quantième — c'est le mot le plus fragile de tout ce que l'agent dit.
- **Jamais deux horaires séparés de moins d'une heure dans la même phrase** : la première option disparaît dans le canal.
- L'annonce « assistant automatique » est dans la **première phrase**, non désactivable, et vérifiée par le corpus.

**Tests**
- Les trois appelants de la mesure 18 : rendez-vous au tour 3 · transfert au tour 5 · transfert au tour 2.
- Aucun état ne peut produire une phrase contenant « c'est noté », « enregistré » ou « annulé » **sans un identifiant d'écriture confirmée**.
- Une date hors horizon ne produit **jamais** « nous sommes fermés ».

---

## 4. `ecriture` — la seule à pouvoir dire que c'est fait

**Contrat**

| Obligation | Origine |
|---|---|
| **`read-after-write`** : relire l'enregistrement par son identifiant avant toute confirmation orale | `docs/04` §C2.3 |
| Clé d'idempotence générée **au début du tour de parole**, pas à l'envoi | `docs/02` |
| L'agent ne peut confirmer **que** sur un enregistrement relu | Mesure 14 : deux confirmations orphelines en douze tours |
| Métrique **taux de confirmation orpheline**, cible **0**, incident si ≠ 0 | `docs/07` |

**Test** : simuler une écriture qui échoue **après** l'insertion (relecture impossible) → l'agent dit qu'il ne peut pas confirmer, et **ne dit jamais que c'est noté**.

---

## 5. `parole` — de la phrase à l'audio

**Contrat**

| Obligation | Origine |
|---|---|
| Synthèse **en flux**, jamais par fichier complet | Mesure 13 : 162 ms par l'API contre 372 ms par le binaire |
| **Nombre de synthèses simultanées borné** (file à parallélisme fixe, ~4 pour 4 cœurs) | Mesure 13 : 614 ms à six flux |
| Le **délai avant premier fragment** est une métrique de production, au même rang que la confirmation orpheline | Mesure 13 : le processeur reste bas quand la machine est pleine |
| Piper tourne en **service HTTP séparé** (GPL-3.0), voix `fr_FR-siwis-medium` ou `fr_FR-mls-medium` | `CLAUDE.md` |
| **Délai de garde** : au-delà de ~700 ms sans premier token du modèle, l'agent dit « je vérifie » | Mesures 14 et 20 : 935 ms au p90, 8 751 ms au pire |

**Test** : injecter un modèle qui répond en 3 s → l'appelant entend « je vérifie » **avant** la troisième seconde, et la réponse s'enchaîne sans coupure.

---

## 6. Ce que le corpus doit vérifier à chaque changement

Le corpus existe déjà (`bancs/corpus.py`, 79 énoncés, 11 familles). La porte de non-régression rejoue :

1. les **quatre échecs de numéro** mesurés, avec les règles T8, T9, T10 de `docs/10` ;
2. les **douze tours** de la mesure 14, qui doivent tous rester sans faute ;
3. les **trois appelants** de la mesure 18, avec leurs issues attendues ;
4. les **dix phrases d'agent** de la mesure 19, dont l'annonce légale ;
5. `pass^5`, pas `pass^1` : un scénario réussi 4 fois sur 5 est un scénario **échoué**.

**Le lot n'est fini que si la porte passe deux fois d'affilée.**
