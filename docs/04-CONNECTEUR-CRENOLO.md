# Spécification du connecteur `crenolo.agenda.v1`

> Écrite à partir de l'audit en lecture seule `docs/recherche2/A7-hotes-de-greffe.md` (2026-09-13) — **les noms de tables, de routes et de colonnes ci-dessous sont ceux du code réel**, pas des inventions.
> Contrainte encadrante, non négociable : `rdv.marpeap.com/CLAUDE.md:9` — **`main` gelé, toute évolution strictement additive**. Jamais un champ requis ajouté, jamais un renommage, jamais une route supprimée.

---

## 1. Ce que le vocal impose et que Crenolo ne sait pas encore faire

Cinq écarts, tous issus de l'audit. Ils commandent les migrations du §4.

| # | L'écart | Pourquoi le vocal le révèle |
|---|---|---|
| E1 | **`bookings.client_email` est NOT NULL** et obligatoire dans `BookRequest` (`reservation.py:54-72`) | Un appelant ne dicte pas son e-mail — et la règle produit l'interdit (`R6` : jamais d'e-mail par la voix). Le téléphone devient l'identifiant |
| E2 | **Aucune contrainte d'unicité SQL sur `bookings`** ; la non-superposition tient au verrou applicatif (`reservation.py:196-274`) | Un deuxième écrivain (nous) qui ne reproduit pas le verrou **double-booke**. Et un double-booking par un agent vocal est le pire échec possible : le client est confiant, le salon découvre le jour J |
| E3 | **Rate-limit `10/hour`** sur `POST /public/{slug}/book` (`ratelimit.py:92`) | Un standard sérieux dépasse 10 réservations/heure. Notre trafic vient d'une IP unique : nous serions bloqués par notre propre volume |
| E4 | **Aucune recherche client par téléphone** — numéros stockés bruts, pas d'index | Le seul identifiant dont dispose l'agent est le numéro… et encore (§2.3) |
| E5 | **Les durées réelles n'existent pas** : `end_time` = durée planifiée, `completed` posé par un cron (`booking_cron.py:24`) | « L'agent apprend sur l'historique » se réduit sinon aux associations de prestations et aux noms de clients |

---

## 2. Les invariants à respecter — recopiés du code, pas réinventés

### 2.1 Le verrou, mot pour mot
Le connecteur **n'écrit pas directement en base**. Il appelle une route de Crenolo qui **réutilise la fonction de réservation existante**, donc le verrou reste unique et au même endroit. C'est le seul moyen d'éviter deux implémentations divergentes de la même règle.

1. zéro praticien actif → `SELECT businesses.id … FOR UPDATE` puis `check_overlap` ;
2. praticiens actifs → `SELECT practitioners.id … FOR UPDATE` **ordonné par `id`** (anti-deadlock), calcul des libres **sous verrou**, choix du **moins chargé du jour** ;
3. conflit → **409**, jamais d'écriture optimiste.

### 2.2 Les trois règles silencieuses qui cassent un intégrateur naïf
- `practitioner_id IS NULL` sur un `booking` **bloque tout le monde**, ce n'est pas « non assigné » (`booking.py:21-29`).
- Les seuls états occupants sont **`("confirmed","completed")`** (`services/etats.py:54`) — `cancelled` et `no_show` libèrent le créneau.
- `GET /public/{slug}/slots` répond sous **deux formes** selon qu'un praticien actif existe (`creneaux.py:79-97`). Ne jamais supposer `{"slots":[…]}`.

### 2.3 L'identité de l'appelant n'est pas fiable
L'ARCEP recommande le **masquage du CLI** après un renvoi d'appel (`R3 §2`). Donc :
- le numéro appelant est un **indice**, jamais une preuve ;
- toute action sur un rendez-vous **existant** (report, annulation) exige une vérification indépendante : **code envoyé par SMS**, ou DTMF, ou un fait que seul le client connaît ;
- `identifier_client()` sert à personnaliser l'accueil et à alimenter les keyterms, **jamais** à autoriser une écriture.

---

## 3. Surface du connecteur

Nouveau routeur `api/routers/connecteur/`, monté sous **`/connecteur/v1`**. Aucune route existante n'est touchée.

**Authentification** : en-tête `X-Api-Key`, clé **scopée par établissement** (§4.1) — contrairement à `X-Internal-Secret`, qui voit aujourd'hui tous les salons (`routers/internal/_commun.py:25-42`).

| Opération | Méthode et chemin | S'appuie sur | Statut |
|---|---|---|---|
| `catalogue()` | `GET /connecteur/v1/catalogue` | `routers/public/fiche.py:93` | existe, à exposer |
| `disponibilites()` | `GET /connecteur/v1/disponibilites?service_ids=&du=&au=&praticien_id=` | boucle sur `slot_service.creneaux_avec_praticiens` (`:172`) | **à écrire** |
| `identifier_client()` | `GET /connecteur/v1/client?telephone=+336…` | `services/sms.numero_normalise` (`sms.py:49`) + index `lower(telephone)` | **à écrire** |
| `reserver()` | `POST /connecteur/v1/reservations` | **réutilise** la fonction de `reservation.py:196-274` | **à écrire** |
| `deplacer()` | `PATCH /connecteur/v1/reservations/{id}/horaire` | logique de `agenda.py:222` (`check_overlap(..., sauf=)`) | **à écrire** |
| `annuler()` | `POST /connecteur/v1/reservations/{id}/annulation` | respecte `annulation.autonome_ouverte` (`services/annulation.py:15`) | **à écrire** |
| `confirmer_par_sms()` | `POST /connecteur/v1/reservations/{id}/sms` | insertion `sms_sortants` + `services/sms.texte_rappel` | existe, à câbler |
| `journal_appel()` | `POST /connecteur/v1/appels` | nouvelle table `appels` (§4.5) | **à écrire** |

### 3.1 `reserver()` — le contrat exact

```
POST /connecteur/v1/reservations
X-Api-Key: <clé scopée>
Idempotency-Key: <uuid v4, généré au DÉBUT du tour de parole>

{ "service_id": …, "extra_service_ids": [], "date": "2026-09-17", "start_time": "10:30",
  "client_name": "Nguyen", "telephone": "+33612345678", "email": null,
  "praticien_id": null, "canal": "vocal", "appel_id": "…" }
```

- **`email` facultatif.** Si absent, l'API synthétise une valeur interne pour satisfaire le `NOT NULL` existant (E1) — **sans jamais l'afficher au salon ni lui envoyer de courriel**. Alternative plus propre au §4.2.
- **`Idempotency-Key`** : rejouée, la requête renvoie **le même résultat, y compris l'erreur** (modèle Stripe). Générée au début du tour, pas à l'appel d'outil : c'est ce qui rend un retry réseau inoffensif.
- **Réponses** : `201` avec le rendez-vous complet · **`409`** créneau pris entre-temps (l'agent le dit et propose l'alternative suivante) · `422` règle métier violée, avec **un code machine** (`jour_ferme`, `hors_horaires`, `delai_minimum`, `client_bloque`…) et non un message français à interpréter · `402` facturation fermée.
- **`read-after-write` obligatoire** : l'API relit le rendez-vous par son `id` avant de répondre `201`. **L'agent n'a le droit de dire « c'est noté » que sur un `201` relu.**

### 3.2 Ce que le connecteur n'expose pas, délibérément
Aucune route de **listage global** (« les rendez-vous de demain »). Elle n'est pas restreinte : **elle n'existe pas**. Un appelant qui obtient l'agenda du salon est le scénario de fuite le plus vraisemblable, et le seul moyen sûr de l'empêcher est l'absence de l'outil.

---

## 4. Migrations à ajouter dans Crenolo — toutes additives

### 4.1 `api_cles` — clés d'API par établissement
Calquée sur `inkra_api_tokens` (`app.marpeap.com/apps/api/models/inkra/api_token.py:9`), qui fait déjà exactement cela et fonctionne.

```sql
CREATE TABLE IF NOT EXISTS api_cles (
  id UUID PRIMARY KEY, business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
  empreinte TEXT NOT NULL UNIQUE,        -- SHA-256, jamais la clé en clair
  libelle TEXT, portees TEXT[] NOT NULL DEFAULT '{}',
  expire_le TIMESTAMPTZ, revoquee_le TIMESTAMPTZ,
  derniere_utilisation_le TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_api_cles_business ON api_cles(business_id) WHERE revoquee_le IS NULL;
```
Portées : `agenda:lire`, `agenda:ecrire`, `client:lire`.

### 4.2 `bookings.client_email` — desserrer sans casser (E1)
`ALTER COLUMN … DROP NOT NULL` **est** additif au sens du gel (aucun appelant existant ne casse : ils envoient tous un e-mail). C'est plus propre que de synthétiser une adresse. **À arbitrer avec Adnan** : `DROP NOT NULL` contre e-mail synthétique. Recommandation : `DROP NOT NULL`, et le code lit `client_email or telephone` là où il affiche un contact.

### 4.3 La contrainte qui manque (E2)

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;
ALTER TABLE bookings ADD CONSTRAINT bookings_pas_de_chevauchement
  EXCLUDE USING gist (
    business_id WITH =, practitioner_id WITH =,
    tsrange((date + start_time), (date + end_time)) WITH &&
  ) WHERE (status IN ('confirmed','completed') AND practitioner_id IS NOT NULL);
```
⚠️ **À valider d'abord en lecture** : si l'historique contient déjà des chevauchements, la création échoue. Procédure : requête de détection → correction manuelle par le salon → `ADD CONSTRAINT NOT VALID` puis `VALIDATE CONSTRAINT` hors heures d'ouverture. Le cas `practitioner_id IS NULL` (blocage global) reste couvert par le verrou applicatif seul.

### 4.4 Recherche par téléphone (E4)
Normaliser à l'écriture avec la fonction **existante** `numero_normalise` (`services/sms.py:49`), stocker en E.164 dans une colonne additive `telephone_e164`, et indexer :
```sql
ALTER TABLE bookings        ADD COLUMN IF NOT EXISTS telephone_e164 VARCHAR(20);
ALTER TABLE fiches_clients  ADD COLUMN IF NOT EXISTS telephone_e164 VARCHAR(20);
CREATE INDEX IF NOT EXISTS idx_bookings_tel   ON bookings(business_id, telephone_e164);
CREATE INDEX IF NOT EXISTS idx_fiches_tel     ON fiches_clients(business_id, telephone_e164);
```
Remplissage rétroactif par un script de rattrapage, sans toucher aux colonnes d'origine. ⚠️ `numero_normalise` ne reconnaît **que les mobiles français** (`06`/`07`) : les fixes doivent être acceptés séparément, sinon un client qui appelle de sa ligne fixe devient introuvable.

### 4.5 Durées réelles et journal d'appel (E5)
```sql
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS arrivee_le    TIMESTAMPTZ;
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS fin_reelle_le TIMESTAMPTZ;
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS canal VARCHAR(20);   -- 'web' | 'vocal' | 'pro'
```
Plus une table `appels` (identifiant d'appel, `business_id`, horodatages, issue, transcription, coût, `booking_id` éventuel) — c'est elle qui porte le **taux de confirmation orpheline** et le **taux d'impasse**.
**Sans le geste humain** (« le client est arrivé », « c'est terminé ») dans l'interface pro, ces colonnes resteront vides : la meilleure approximation immédiate est l'horodatage d'encaissement (`caisse_tickets.booking_id`, `migrations/025_caisse.sql:50`), déjà présent et inexploité.

### 4.5 bis Le SMS — trois corrections avant de s'en servir comme preuve

L'audit A3 a trouvé trois défauts dans la couche SMS existante, qui empêchent de l'utiliser comme mécanisme de vérification de bout en bout :

1. **L'index unique sur `booking_id`** (`023_sms.sql:28`) **interdit d'envoyer une confirmation *et* un rappel** pour le même rendez-vous. Il faut élargir la clé au couple `(booking_id, type)`.
2. **La file n'a aucune péremption.** Une confirmation partie trois heures après l'appel ne prouve plus rien : si elle n'est pas remise dans les minutes qui suivent l'écriture, le rendez-vous doit basculer « à vérifier », pas partir quand même.
3. **L'abandon après cinq tentatives est silencieux.** Il doit marquer le rendez-vous et alerter le commerçant — c'est exactement le signal qui révèle un numéro mal capté.

Et la sortie change : **la passerelle SIM est juridiquement inutilisable** (décision Arcep n° 2018-0881 consolidée au 01/01/2026, interdiction absolue pour un 06/07 d'émettre au nom d'un système automatisé) **et techniquement inadaptée** (aucun accusé de remise). Les routes internes existantes deviennent l'**adaptateur** vers un fournisseur A2P ; tout le reste du code est conservé.

### 4.6 Rate-limit (E3)
Exempter les routes `/connecteur/v1/*` du `10/hour`, et poser à la place une limite **par clé d'API** (donc par salon), dimensionnée sur le volume d'appels réel. Une IP unique côté agent ne doit jamais être l'unité de compte.

---

## 5. Effort, et ordre

| Lot | Contenu | Dépend de |
|---|---|---|
| C1 | `api_cles` + garde `X-Api-Key` + `catalogue()` + `disponibilites()` | rien |
| C2 | `reserver()` avec idempotence et read-after-write, exemption de rate-limit | C1, §4.2 |
| C3 | `telephone_e164` + index + `identifier_client()` | C1 |
| C4 | `deplacer()`, `annuler()` avec vérification d'identité par SMS | C2, C3 |
| C5 | Table `appels`, colonnes `canal`/`arrivee_le`/`fin_reelle_le`, KPI | C2 |
| C6 | Contrainte `EXCLUDE` (après audit des chevauchements existants) | C2, fenêtre hors service |

**C1 et C2 suffisent pour un premier appel qui prend un vrai rendez-vous.** Le reste rend le produit défendable.

---

## 6. Les deux autres hôtes, en une page

**Inkra** — rien à construire côté API : `/api/vault/v1/*` existe, avec token haché par vault et limite de 100 requêtes/heure. Un agent vocal peut dicter une note (`POST …/notes/from-markdown`), compléter (`…/append`), chercher (`POST …/ai/search`), et **piloter un process à la voix** (`…/processes/{id}/run`, `…/process-runs/{id}/advance`). Le connecteur doit seulement convertir texte ↔ blocs BlockNote. ⚠️ Révoquer le token en dur de `agent/inkra_agent.py:49`.

**Kompagnon (M-Campaign)** — rien à construire non plus : en-tête `X-Gateway-Token`, isolation par instance garantie côté serveur, ~45 routes `/agent/*`, et `GET /agent/capabilities` qui expose la découverte d'outils. **Le seul ajout est côté connecteur** : une **confirmation à deux temps** sur toute action coûteuse (changement de budget, création de campagne). Dire « d'accord, je passe le budget à 30 € » et l'exécuter dans le même tour est acceptable en écrit, jamais en vocal.
