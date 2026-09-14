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
| Piper (TTS, voix FR) | **136 Mo** au repos, **362 Mo** au pic | **résident, partagé** |
| Nemotron 3.5 (STT) | modèle 742 Mo, **chargement 2,8 s** | **résident, partagé** — jamais un processus par appel |
| Orchestration par appel | ~150–320 Mo [H, d'après LiveKit] | **par appel** |
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
2. **La tenue en charge** : combien d'appels simultanés une machine à 4 Go soutient réellement avec les modèles résidents. Le RTF de 0,53 le laisse penser, il ne le prouve pas.
3. **Le prix des machines**, à relever chez deux ou trois hébergeurs avant de figer la grille.
