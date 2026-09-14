# Lots C1 à C7 — le chantier côté Crenolo

> Tâches exécutables, dans l'ordre des dépendances. Porté par la **session qui tient Crenolo** — c'est son code.
> Trois contraintes encadrent tout ce document :
> - **`main` gelé**, promesse écrite à une cliente. Toute évolution **additive**.
> - **Les migrations partent de `032`** et sont **appliquées au démarrage de l'API**. Une migration qui échoue **empêche l'API de démarrer pour `crenolo.com` ET pour le domaine gelé**. Chacune se teste sur une copie avant d'approcher la production.
> - **L'API ne se déploie pas toute seule** (le front Vercel, si) : `ssh root@151.241.228.72 'cd /opt/rdv && git pull -q origin crenolo-v3 && bash scripts/deploy.sh'`, et le code vit **dans l'image Docker** — `docker compose up -d` sans `--build` ne déploie rien.

---

## C0 — Extraction du service de réservation ⏸ **en attente d'arbitrage**

**Pourquoi c'est C0 et pas C2** : sans lui, `reserver()` ne peut ni réutiliser le verrou ni éviter le rate-limit. C'est le seul obstacle du chemin critique.

| # | Tâche | État |
|---|---|---|
| C0.1 | 14 tests de caractérisation **avant** remaniement, 4 mutations rouges | ✅ fait le 14/09 (992 tests verts) |
| C0.2 | Extraire la logique de `routers/public/reservation.py` vers `services/reservation.py` | branche locale, non poussée |
| C0.3 | La route publique reste **le seul appelant**, signature et réponses inchangées | — |
| C0.4 | Déploiement séparé, vérifié, **avant** que le connecteur s'appuie dessus | — |

**Bloqué par** : l'accord d'Adnan (§6 de `04-CONNECTEUR-CRENOLO.md`). **Rien ne se déploie sans lui.**

---

## C1 — Clés d'API par établissement

| # | Tâche | Détail |
|---|---|---|
| C1.1 | Migration **032** : table `api_cles` | modèle exact au §4.1 de la spec, calqué sur `inkra_api_tokens` |
| C1.2 | Garde `X-Api-Key` dans `api/routers/connecteur/_commun.py` | empreinte SHA-256, jamais la clé en clair ; portées `agenda:lire`, `agenda:ecrire`, `client:lire` |
| C1.3 | Routeur `connecteur` monté sous `/connecteur/v1` dans `main.py` | aucune route existante touchée |
| C1.4 | `GET /connecteur/v1/catalogue` | réutilise `routers/public/fiche.py:93` |
| C1.5 | `GET /connecteur/v1/disponibilites?service_ids=&du=&au=` | boucle sur `slot_service.creneaux_avec_praticiens` — **renvoyer les deux formes** de réponse, jamais supposer `{"slots":[…]}` |
| C1.6 | Émission et révocation d'une clé depuis la console pro | une clé par salon, révocable unitairement — contrairement au `X-Internal-Secret` actuel, qui voit tous les salons |

**Recette** : une clé du salon A ne lit rien du salon B (test d'intégration qui **doit** échouer).

---

## C2 — Écriture idempotente

| # | Tâche | Détail |
|---|---|---|
| C2.1 | `POST /connecteur/v1/reservations` appelant **le service extrait** (C0) | jamais d'écriture directe en base |
| C2.2 | En-tête `Idempotency-Key` : mémoriser code **et** corps de la première réponse, y compris les erreurs | modèle Stripe ; purge à 24 h |
| C2.3 | **`read-after-write`** : relire le rendez-vous par son `id` avant de répondre `201` | l'agent n'a le droit de dire « c'est noté » que sur un 201 relu |
| C2.4 | Mapper les **dix-huit refus** en codes machine | `422` × 11 · `403` × 2 · `404` × 2 · `409` × 2 · `429` × 1 — table tenue par les tests de C0.1, pas par une lecture de code |
| C2.5 | Exempter `/connecteur/v1/*` du `10/hour`, limiter **par clé d'API** | une IP unique ne doit jamais être l'unité de compte |
| C2.6 | Migration **033** : `bookings.client_email` → `DROP NOT NULL` | 11 lignes portent déjà une chaîne vide : la contrainte est déjà contournée, salement |

⚠️ **C2.6 ne se livre pas seul** — voir C3, qui en est la condition.

---

## C3 — Le téléphone reprend les rôles de l'e-mail ⚠️ **condition de livraison de C2**

Sans ce lot, **le canal vocal devient la porte dérobée du produit**.

| # | Tâche | Détail |
|---|---|---|
| C3.1 | Migration **034** : `telephone_e164` sur `bookings` et `fiches_clients`, + index `(business_id, telephone_e164)` | normalisation par `services/sms.numero_normalise` |
| C3.2 | **Étendre la normalisation aux fixes** | aujourd'hui elle n'accepte que `06`/`07` : un client qui appelle de sa ligne fixe serait introuvable |
| C3.3 | **`est_bloque` par téléphone** en plus de l'e-mail | sinon un client que le salon a bloqué réserve en appelant |
| C3.4 | **Plafond de réservations actives par téléphone** | second garde-fou (429) qui saute avec l'e-mail |
| C3.5 | `GET /connecteur/v1/client?telephone=` | sert l'accueil et les keyterms, **jamais** à autoriser une écriture |
| C3.6 | Script de rattrapage des numéros existants | sans toucher aux colonnes d'origine |

**Recette** : le test de C0.1 qui échoue si `client_email` cesse d'être requis **doit repasser au vert** une fois C3 livré — et pas avant.

---

## C4 — Report, annulation, vérification d'identité

| # | Tâche | Détail |
|---|---|---|
| C4.1 | `PATCH /connecteur/v1/reservations/{id}/horaire` | logique de `agenda.py:222`, `check_overlap(..., sauf=)` |
| C4.2 | `POST /connecteur/v1/reservations/{id}/annulation` | respecte `annulation.autonome_ouverte(settings)` |
| C4.3 | **Vérification d'identité par code SMS** avant toute modification | le CLI peut être masqué après un renvoi (recommandation ARCEP) : le numéro appelant est un indice, jamais une preuve |
| C4.4 | Stocker la date d'annulation | elle n'est pas enregistrée aujourd'hui |

---

## C5 — Journal d'appel et durées réelles

| # | Tâche | Détail |
|---|---|---|
| C5.1 | Migration **035** : table `appels` | porte le **taux de confirmation orpheline** et le **taux d'impasse** |
| C5.2 | Migration **036** : `bookings.canal`, `arrivee_le`, `fin_reelle_le` | additives, nullables |
| C5.3 | Geste « le client est arrivé » / « terminé » dans la console pro | ⚠️ **sans ce geste, les colonnes restent vides** et « l'agent apprend sur l'historique » reste une promesse creuse |
| C5.4 | À défaut, exploiter `caisse_tickets.booking_id` | meilleure approximation déjà présente, aujourd'hui inexploitée |
| C5.5 | **Réconciliation nocturne** : appels marqués « RDV pris » contre rendez-vous réellement en base | alerte le lendemain matin ; troisième barrière anti-échec-silencieux |

---

## C6 — Le filet SQL

| # | Tâche | Détail |
|---|---|---|
| C6.1 | Migration **037** : `CREATE EXTENSION btree_gist` + `EXCLUDE` sur les lignes **avec** praticien | audit : 0 chevauchement, la migration passe |
| C6.2 | Seconde `EXCLUDE` sur les lignes **sans** praticien (`business_id` + plage) | couvre le cas dominant : 241 lignes sur 251 |
| C6.3 | **Écrire les deux à la main** | Alembic **ne détecte ni les contraintes `EXCLUDE` ni les renommages** |
| C6.4 | Déclencheur pour le cas croisé NULL ↔ praticien nommé | **en réserve** : audit à 0, à n'ouvrir que si le cas apparaît |

⚠️ **Aucune de ces deux contraintes ne couvre « une ligne sans praticien bloque tout le monde »** — `EXCLUDE` compare deux à deux sur des clés égales. Le verrou applicatif reste la protection principale ; c'est pourquoi passer par la route est non négociable.

---

## C7 — Les trois défauts de la couche SMS

Le SMS est notre preuve de bout en bout : ces défauts l'empêchent d'en être une.

| # | Tâche | Détail |
|---|---|---|
| C7.1 | Élargir l'unicité de `booking_id` à `(booking_id, type)` | aujourd'hui (`023_sms.sql:28`) **on ne peut pas avoir confirmation ET rappel** sur le même rendez-vous |
| C7.2 | **Péremption de la file** | une confirmation partie trois heures après l'appel ne vérifie plus rien : au-delà du délai, marquer « à vérifier » plutôt qu'envoyer |
| C7.3 | Rendre l'abandon **bruyant** après cinq tentatives | marquer le rendez-vous et alerter : c'est le signal qui révèle un numéro mal capté |
| C7.4 | Adaptateur vers un fournisseur A2P | ⚠️ **la passerelle SIM est juridiquement inutilisable** (Arcep n° 2018-0881 consolidée au 01/01/2026) **et** ne produit aucun accusé de remise |

---

## Ordre et dépendances

```
C0 (arbitrage) ──► C1 ──► C2 ──┬──► C4
                               └──► C5
C3 conditionne C2.6  ·  C6 indépendant  ·  C7 indépendant, mais bloquant pour la promesse « le SMS est la preuve »
```

**C1 + C2 + C3 suffisent pour un premier appel qui prend un vrai rendez-vous sans ouvrir de porte dérobée.** Le reste rend le produit défendable.
