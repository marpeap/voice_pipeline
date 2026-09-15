# Chiffrage — palier matériel et grille tarifaire

> Fondé sur les **mesures** de `docs/09-L0-MESURES.md` et les coûts vérifiés de `docs/recherche2/`.
> Les hypothèses de trafic sont marquées **[H]** : le volume d'appels d'un salon n'est publié nulle part (A6), il sera **notre donnée propriétaire** dès les premiers clients.

---

## 1. Le fait qui change le dimensionnement : les lignes se mutualisent

Un salon n'a pas besoin d'une ligne à lui. Le trafic s'additionne, mais les **pics ne coïncident pas**. Calcul d'Erlang B, hypothèses [H] : 10 appels/jour/salon, 2 minutes en moyenne, 60 % du trafic concentré sur 4 heures de pointe.

| Salons | Trafic (erlangs) | 2 lignes | 3 lignes | 4 lignes | 6 lignes |
|---|---|---|---|---|---|
| 5 | 0,25 | 2,4 % | 0,2 % | 0,01 % | ~0 |
| **10** | 0,50 | 7,7 % | 1,3 % | **0,16 %** | ~0 |
| **20** | 1,00 | 20 % | 6,3 % | **1,5 %** | 0,05 % |
| 40 | 2,00 | 40 % | 21 % | 9,5 % | **1,2 %** |

*(Le pourcentage est le taux d'appels qui trouveraient toutes les lignes occupées.)*

**Lecture : 20 salons tiennent sur 4 lignes simultanées avec 1,5 % de blocage.** Le palier matériel ne se calcule donc **pas par salon** — c'est l'erreur qui ferait tripler le prix.

---

## 2. Mémoire réelle, mesurée

A4 donnait « 1 Go = un appel simultané », en supposant **l'inférence déportée**. Nos mesures permettent d'être plus précis, parce que **les modèles résidents sont partagés entre les appels** :

| Poste | Mesuré | Nature |
|---|---|---|
| Piper (TTS, voix FR) | **136 Mo** au repos, **362 Mo** au pic | **résident, partagé** — ⚠️ mais **+150 Mo par synthèse simultanée** (mesure 13) : c'est **le** poste mémoire par appel |
| Nemotron 3.5 (STT) | modèle 742 Mo, **chargement 2,8 s** | **résident, partagé** — jamais un processus par appel |
| Orchestration par appel | ~150–320 Mo [H, d'après LiveKit] | **par appel** — ⚠️ **et la part STT n'y est pour rien** : mesuré le 15/09, un flux STT supplémentaire coûte **11 Mo** (mesure 11), modèle partagé. Cette ligne est donc à réattribuer à l'orchestration, au TTS et au LLM, où elle n'est pas encore mesurée |
| Asterisk + PostgreSQL + système | ~400–600 Mo [H] | fixe |

**Donc, pour une machine à 4 Go** : ~1,2 Go de modèles résidents + ~0,5 Go de socle + 4 à 6 appels simultanés. **Soit, d'après le §1, de l'ordre de 20 à 40 salons sur une seule machine.**

⚠️ **Deux conditions à cette arithmétique**, toutes deux vérifiées par la mesure : les modèles tournent en **services résidents** (le chargement de 2,8 s interdit le processus par appel), et le RTF de 0,53 laisse assez de marge pour que plusieurs appels partagent le même processeur — **à vérifier en charge réelle**, c'est la mesure qui manque encore.

---

## 3. Coût variable par salon et par mois

Hypothèses [H] : 10 appels/jour × 22 jours × 2 min = **440 minutes**, 150 rendez-vous, confirmation + rappel = 300 SMS.

| Poste | Tout-API | STT+TTS auto-hébergés |
|---|---|---|
| STT + TTS | 6,51 $ | **0 $** |
| LLM | 1,32 $ | 1,32 $ |
| Téléphonie entrante (Telnyx 0,006 $/min) | 2,64 $ | 2,64 $ |
| Numéro | 0,50 $ | 0,50 $ |
| **SMS (300 × 0,058 €)** | **17,40 €** | **17,40 €** |
| **Total** | **≈ 28 $** | **≈ 22 $** |

### Le résultat contre-intuitif : **le SMS est le premier poste de coût**

**17,40 € de SMS contre 4 à 10 $ d'inférence et de téléphonie réunies.** Tout le travail de rapatriement des modèles (LLM → STT → TTS) économise **6,50 $ par salon et par mois** ; supprimer un seul SMS sur deux en économise **8,70 €**. Trois conséquences :

1. **Le rappel de la veille est déjà envoyé par Crenolo** et déjà payé par le salon. **Notre coût incrémental, c'est la confirmation seule** — 150 SMS, soit **≈ 8,70 €**, et le total tombe à **≈ 13 €** par salon.
2. **Ne pas envoyer de SMS aux appels qui n'aboutissent pas** à un rendez-vous. Évident, mais c'est le genre de règle qu'on oublie d'écrire.
3. Le tarif dégressif ne s'ouvre qu'en **mutualisant** : l'abonnement Octopush à 0,045 € exige 1 000 SMS/mois, soit **au moins 7 salons** (A3). C'est un argument de plus pour une infrastructure commune plutôt qu'une instance par client.

⚠️ **À vérifier avant de s'engager** : les accusés de remise par webhook ne sont documentés que chez SMSFactor (+2,40 €/mois par salon). Un SMS sans accusé ne prouve rien — et c'est toute la valeur qu'on lui prête.

---

## 4. Grille tarifaire proposée

**Doctrine, rappelée** : pas de facturation à la minute (plainte n°1 des exploitants), spam filtré et **non facturé**, forfait par établissement.

| | Coût variable | Prix proposé | Marge brute |
|---|---|---|---|
| **Salon seul** | ≈ 13 € (confirmation seule) | **39 € HT/mois** | ≈ 26 € |
| Palier haut (volume double) | ≈ 26 € | **59 € HT/mois** | ≈ 33 € |

**Repères de marché** (A3, A6, R4) : Tala **29 €** · Sylen **49 €** · Elio **79 €** · Kronos **249 €** · Vokai **299 € + 0,29 €/min** · Fresha **94,95 €/site** · Boulevard **125 $ / 200 min**.

**39 € nous place entre Tala et Sylen** — pas le moins cher, et c'est voulu : le moins cher du marché est aussi celui qui n'est intégré à aucun logiciel de réservation. L'argument n'est pas le prix, c'est que **l'agent écrit dans le vrai agenda**, avec les vraies durées et les vraies règles.

**Ce qui reste à trancher par Adnan** : le plafond d'appels uniques par mois (modèle Goodcall), et la remise pour un salon déjà client de Crenolo — c'est le seul endroit où la greffe peut se payer deux fois ou une seule.

---

## 5. Le coût fixe, et le seuil de rentabilité

Le prix d'un VPS à 4 Go n'est **pas vérifié** dans cette recherche — les grilles des hébergeurs n'ont pas été relevées à la source, et je ne les invente pas. Ordre de grandeur **[H, à confirmer]** : 10 à 25 € HT/mois.

À 39 € par salon et ~13 € de coût variable, **le premier salon paie déjà la machine**. Le modèle tient donc dès le deuxième client, ce qui est exactement ce qu'on attend d'une infrastructure mutualisée — et c'est l'inverse du tout-OSS sur GPU loué, dont R2 avait montré qu'il ne devenait rentable qu'au-delà de 17 100 minutes par mois.

---

## 6. Les trois chiffres qui manquent encore

1. **Le volume d'appels réel d'un salon** — aucune source publiée, hypothèse à 10/jour. Toute la colonne de coût variable en dépend linéairement.
   ⚠️ **Et la base de Crenolo ne peut pas y répondre** — vérifié le 14/09. Le seul proxy disponible est la saisie manuelle de rendez-vous (`services/rdv_manuel.py`, dont la docstring dit « saisi par le salon lui-même — au comptoir, **au téléphone** ») : **11 saisies au total sur 252 réservations et 69 jours, dont 9 chez un seul salon le même jour**. Ce n'est pas un signal, c'est un artefact, et il ne doit pas servir à étayer quoi que ce soit.
   **Mais le silence est lui-même instructif** : le salon le plus actif compte **224 réservations en ligne sur 59 jours et zéro saisie manuelle**. Soit il ne reçoit aucun appel — invraisemblable pour un salon —, soit **il en reçoit et ne les écrit nulle part**. Autrement dit : **aujourd'hui, les appels ne laissent aucune trace dans le produit.** C'est exactement le vide que le greffon comble, et c'est aussi pourquoi aucune source interne ne donnera jamais ce volume.
   **Conséquence pratique** : la mesure sera **externe** — demander à un salon volontaire de compter pendant une semaine, ou obtenir un relevé d'opérateur. À joindre à la recherche du salon pilote pour le corpus (L1).
2. **La tenue en charge — ⚠️ partiellement levée le 15/09 (mesure 11).** Côté STT, huit flux simultanés partageant un modèle tiennent un RTF de 0,27 par flux et coûtent 11 Mo chacun : **le STT n'est pas le mur**, l'extrapolation prudente donne 25 à 30 appels simultanés sur une machine à 4 cœurs. **Ce qui reste à mesurer, et qui portera la limite réelle : l'orchestration par appel, le TTS, et le nombre de requêtes simultanées qu'un fournisseur de LLM accepte.**
   ⚠️ **Mesure tentée le 14/09 à 12 h 30, interrompue** : le banc `marpeap-series` est passé **hors ligne** en cours d'exécution (Tailscale : « offline, last seen 10m ago »). Le protocole est prêt (1, 2, 3 puis 4 transcriptions simultanées du même fichier, temps mur et RSS relevés à mi-parcours) et sera rejoué dès que la machine répond. **À noter : cette machine porte aussi AGENT-OS** — son indisponibilité dépasse le cadre de ce chantier.
3. **Le prix des machines**, à relever chez deux ou trois hébergeurs avant de figer la grille.

---

## 7. Révision du 15/09 — le dimensionnement, désormais mesuré

Les mesures 11, 13 et 14 remplacent trois estimations par trois chiffres. Cette section prime sur les §2 et §5 partout où elle les contredit.

### 7.1 La capacité d'une machine se lit sur la latence, pas sur le processeur

| Poste | Ce que le chiffrage supposait | **Ce qui est mesuré** |
|---|---|---|
| Mémoire par appel | 150 à 320 Mo, attribués à l'ensemble | **STT : 11 Mo** · **TTS : ~150 Mo par synthèse simultanée** |
| Limite de la machine | 4 à 6 appels sur 4 Go, faute de mieux | **STT : 25 à 30 flux** · **TTS : 4 synthèses avant de dépasser 400 ms avant le premier son** |
| Charge processeur | supposée déterminante | **jamais atteinte** : RTF 0,27 (STT) et 0,245 (TTS) à pleine charge |

**Le poste qui fixe la capacité est le TTS, et il la fixe en latence.** Le délai avant le premier son passe de 162 ms à une synthèse à 614 ms à six, pendant que le processeur reste largement libre. Une machine « pleine » aura donc l'air inactive sur tous les tableaux de bord habituels.

**Capacité retenue : ~10 appels simultanés par machine à 4 cœurs** — quatre synthèses simultanées, un agent parlant environ 40 % du temps d'un appel. C'est le premier chiffre de capacité du dossier qui ne soit pas une extrapolation de documentation tierce.

### 7.2 Ce que ça change pour le nombre de salons par machine

Le §1 reste vrai et devient plus fort : **les lignes se mutualisent**. Avec 10 appels simultanés soutenus et un blocage cible sous 2 %, la même table d'Erlang B donne :

| Appels simultanés soutenus | Salons desservis (hypothèses du §1) |
|---|---|
| 4 | ~20 |
| **10** | **~60 à 70** |

**Une seule machine couvre donc l'ordre de grandeur de soixante salons**, contre les vingt retenus jusqu'ici. À 39 € HT par salon, ce n'est plus le coût machine qui décide de la marge — c'est le SMS, comme le §3 l'avait déjà établi, et désormais sans concurrent.

### 7.3 Deux règles d'exploitation qui découlent des mesures

1. **Borner le nombre de synthèses simultanées** (file à parallélisme fixe, ~4 pour 4 cœurs). Sans borne, le dixième appel dégrade les neuf autres ; avec borne, il attend quelques dizaines de millisecondes sans que personne le remarque.
2. **Surveiller le délai avant premier fragment audio**, pas la charge processeur. C'est la seule métrique qui dira qu'une machine est pleine. À mettre au même rang que le taux de confirmation orpheline.

### 7.4 Ce qui reste ouvert, et qui a changé de nature

Le chiffre manquant n'est plus « combien d'appels tient une machine » mais **« combien de requêtes simultanées un fournisseur de LLM accepte, et à quel prix »** — mesure 14 : toute la variance du temps de réponse vient de lui (165 ms en médiane, 935 ms au p90, 2 401 ms au pire), quand les deux étages locaux sont stables à ±30 ms.

**Et le gain du cache de prompt reste non mesuré** : le palier gratuit plafonne à 8 000 jetons par minute, soit un refus dès la deuxième requête avec un prompt calibré au-dessus du seuil de cache. **C'est la seule mesure du dossier qui attende une dépense.**
