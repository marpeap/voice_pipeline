# A7 — Hôtes de greffe pour le module vocal

> Audit **en lecture seule** du code local, 2026-09-13. Aucune connexion base, aucun appel réseau, aucune modification.
> Dépôts lus : `~/Bureau/Marpeap Digitals/rdv.marpeap.com/` (branche `crenolo-v3`, HEAD `14a965a`) · `~/Bureau/Marpeap Digitals/notes.marpeap.com/` + backend `~/Bureau/Marpeap Digitals/app.marpeap.com/apps/api/` · `~/Bureau/Marpeap Digitals/campaign.marpeap.com/`.

---

## 1. Crenolo

### 1.1 Règles du dépôt (CLAUDE.md)
`rdv.marpeap.com/CLAUDE.md:9` — `main` **gelé** au commit `85faec7`, promesse écrite à une cliente. **Toute évolution d'API est additive** : jamais un champ requis, jamais un renommage, jamais une route supprimée ; un nouveau paramètre porte un défaut qui reproduit le comportement d'avant. API FastAPI déployée **manuellement** (`CLAUDE.md:31-45`), front Vercel automatique. Les plans sont dans `docs/superpowers/plans/`, les specs dans `docs/superpowers/specs/`. **Aucun document ne mentionne un agent vocal.**

### 1.2 Modèle de données de l'agenda

| Table | Fichier | Colonnes clés |
|---|---|---|
| `businesses` | `api/models/business.py:11` | `id` uuid PK, `slug` unique, `name`, `email` unique, `password_hash`, `phone`, `address`, `hours` JSONB, `settings` JSONB, `domaine`, `active`, `billing_*`, `stripe_*`, `trial_ends_at` |
| `services` | `api/models/service.py:10` | `id`, `business_id` FK, `name`, `duration_minutes` (int, **planifiée**), `price_cents` (NULL = sur devis), `price_max_cents`, `category`, `active`, `sort_order` |
| `practitioners` | `api/models/practitioner.py:50` | `id`, `business_id` FK CASCADE, `name`, `role`, `bio`, `photo_url`, `active`, `sort_order`, `hours` JSONB, `absences` JSONB `[{date,start,end}]` |
| `practitioner_services` | `api/models/practitioner.py:37` | (`practitioner_id`,`service_id`) — **aucune ligne = assuré par tout le monde** |
| `bookings` | `api/models/booking.py:10` | `id`, `business_id` FK, `service_id` FK, `practitioner_id` nullable (**NULL = bloque tout le monde**, `booking.py:21-29`), `date`, `start_time`/`end_time`, `client_name`, `client_email` (**NOT NULL**), `client_phone` nullable, `status`, `extra_service_ids` JSONB, `notes`, `promo_code`, `remise_cents`, `sms_consenti`, `avis_demande_le`, `created_at` |
| `fiches_clients` | `api/models/fiche_client.py:36` | PK composite (`business_id`,`email` minuscule), `note` (chiffrée), `nom`, `telephone`, `origine`, `etiquette`, `bloque`, `motif_blocage`, `recompenses_accordees` |
| `comptes_clients` | `api/models/compte_client.py:24` | `id`, `email` unique (clé réseau), `nom`, `telephone` (migration 030), `dernier_acces_le` ; + `jetons_client`, `parcours_evenements` |
| `sms_sortants` / `sms_stop` | `api/migrations/023_sms.sql:8` et `:33` | file d'envoi + liste STOP par numéro |

**Horaires** : `businesses.hours` JSONB `{"monday":{"open":"HH:MM","close":"HH:MM"}, …}` — une seule plage par jour, **pas de pause déjeuner exprimable** autrement que par une fermeture ponctuelle.
**Fermetures** : `businesses.settings["blocked_slots"]` = `[{date,start,end}]` ; absences praticien = `practitioners.absences`, **cumulatives** (`practitioner.py:76-81`).
**Réglages agenda** (`business.py:25-56`) : `slot_duration` (défaut 30), `min_booking_hours`, `max_booking_days`, `phone_required`, `self_cancellation`, `cancellation_policy`, `cancellation_contact_message`, `sms_rappels`, `flux_agenda`.

### 1.3 Calcul de disponibilité
- Route : `GET /public/{slug}/slots` — `api/routers/public/creneaux.py:26`. Paramètres : `service_id`, `date`, `extra_service_ids` (CSV), `praticien_id`. Rate-limit **120/minute** (`core/ratelimit.py:98`).
- Réponse **à deux formes** (additif) : `{"slots":[…]}` sans praticien ; `{"praticiens":[…],"par_praticien":{…},"slots":[union]}` dès qu'un praticien actif existe (`creneaux.py:79-97`).
- Moteur : `api/services/slot_service.py:34` `get_available_slots(...)`. Grille = `generate_slots` (`:18`), pas de `slot_duration`, dernier créneau tel que `début+durée ≤ close`. Chevauchement strict `slot < booking_end and slot_end > booking_start` (`:107`). États occupants : `("confirmed","completed")` (`services/etats.py:54`). Date passée → `[]` (`:64`).
- Multi-praticien : `creneaux_avec_praticiens` (`slot_service.py:172`) — `None` si zéro praticien actif (repli exact sur l'ancien calcul).
- **Durée = somme des `duration_minutes`** (`creneaux.py:55-63`). **Aucune notion de pause, de temps de pose ou de tampon entre rendez-vous.** ⚠️ C'est précisément la contrainte métier n°1 d'un salon de coiffure.

### 1.4 Écriture d'un rendez-vous
- **Public** : `POST /public/{slug}/book` — `api/routers/public/reservation.py:74`, rate-limit **10/hour** (`ratelimit.py:92`). `BookRequest` (`:54-72`) : `service_id`, `extra_service_ids[]`, `date`, `start_time`, `client_name`, **`client_email` obligatoire**, `client_phone?`, `sms_rappel?`, `notes?`, `promo_code?`, `practitioner_id?`.
- **Onze refus** avant écriture (`:78-188`) : facturation fermée (403), client bloqué (403), >3 RDV actifs par e-mail (429), téléphone requis (422), prestation inconnue (404), date illisible (422), créneau passé (422), jour fermé (422), hors horaires (422), créneau bloqué (422), `min_booking_hours`/`max_booking_days` (422).
- **Transaction** : verrou pessimiste. Sans praticien, `SELECT businesses.id … FOR UPDATE` puis `check_overlap` (`:199-203`). Avec praticiens, `SELECT practitioners.id … FOR UPDATE` **ordonné par id** (anti-deadlock, `:222-225`), calcul des libres sous verrou, puis choix du **moins chargé du jour** (`:264-274`). Conflit → **409**.
- ⚠️ **Contrainte d'unicité SQL : absente.** Aucun `UNIQUE`/`EXCLUDE` sur `bookings`. Seul index : `bookings (practitioner_id, date) WHERE practitioner_id IS NOT NULL` (`migrations/014_praticiens.sql:68`). **La non-superposition ne tient que par le verrou applicatif** — tout écrivain tiers qui ne le reproduit pas peut double-booker.
- **Côté pro** : `POST /dashboard/bookings` (`routers/dashboard/agenda.py:126`), `client_email` **facultatif**, `end_time` libre, même verrou.
- **Report** : `PUT /dashboard/bookings/{id}/horaire` (`agenda.py:222`) — durée conservée, `check_overlap(..., sauf=rid)`.
- **États** : `PUT /dashboard/bookings/{id}/status` (`agenda.py:288`) — `confirmed|completed|cancelled|no_show`.
- **Annulation client** : `GET/POST /public/{slug}/cancel/{token}` (`routers/public/annulation.py:33`, `:68`), jeton signé (`services/cancel_token.py`), verrou `annulation.autonome_ouverte(settings)`. **La date d'annulation n'est pas stockée.**
- **Clôture automatique** : `services/booking_cron.py:24` passe `confirmed → completed` toutes les 15 min.

### 1.5 Authentification et multi-tenant
- Établissement identifié par **`slug`** en public, par `business_id` du JWT côté pro.
- **Pro** : JWT HS256, `sub` = business_id, `role="pro"`, 7 jours, empreinte `pwd` du hash qui invalide tous les jetons au changement de mot de passe (`core/security.py:55-120`). Beaucoup de routes agenda ajoutent `require_active_billing` → **402 `billing_required`**.
- **Service à service** : en-tête **`X-Internal-Secret`** (`routers/internal/_commun.py:25-42`), déjà utilisé par la passerelle SMS (`api/scripts/passerelle_sms.py:72`). ⚠️ **Non scopé par salon** : ce secret voit tous les établissements.
- **Lecture sans compte** : `GET /agenda/{jeton}.ics` (`routers/flux.py:34`), jeton 32 octets dans `businesses.settings["flux_agenda"]`. Le flux **exclut l'e-mail**, **inclut le téléphone**.
- ⚠️ **Aucune RLS Postgres** (grep `ROW LEVEL|POLICY` : zéro résultat). Isolation **purement applicative**.
- **Pas de clé d'API par établissement** pour un tiers.

### 1.6 Téléphone et SMS existants
- `bookings.client_phone` VARCHAR(50) **stocké brut** ; `fiches_clients.telephone` ; `comptes_clients.telephone` ; `businesses.phone`.
- **Normalisation existante** : `services/sms.py:49` `numero_normalise()` → E.164 `+33…`, **mobiles français uniquement** (`06`/`07`), sinon `None`.
- Rappel veille 18 h (`sms.py:37`, `:98`), ≤160 caractères, GSM-7, suffixe « STOP » (`:78`). Consentement `bookings.sms_consenti`.
- File `sms_sortants` + passerelle SIM : `GET /internal/sms/a-envoyer`, `POST /internal/sms/{id}/resultat`, `POST /internal/sms/entrant` (`routers/internal/sms.py:40,67,91`), lot 20, 5 tentatives.
- **Aucune téléphonie vocale, aucun SIP, aucun enregistrement d'appel.**

### 1.7 Historique exploitable — la mauvaise nouvelle
- Disponible : `date`, `start_time`, `end_time`, `service_id`, **`extra_service_ids`** (associations de prestations mesurables), `practitioner_id`, `status`, `created_at`, `client_email`.
- ⚠️ **Les durées réelles n'existent pas** : `end_time` est la durée **planifiée** (`reservation.py:189`), il n'y a **ni heure d'arrivée ni heure de fin réelle**, et `completed` est posé par un cron, pas par un geste humain. Meilleure approximation disponible et non exploitée : l'horodatage d'encaissement (`migrations/025_caisse.sql:50`, `caisse_tickets.booking_id`).
- **Volumétrie : non mesurable** sans toucher la production (base dans le volume `db_data` du conteneur `rdv_db`).

> **Conséquence directe sur le concept produit** : « l'agent apprend sur l'historique » (notre trou de marché n°1) ne tient aujourd'hui que pour les **associations de prestations** et les **noms de clients** (keyterms). Les **durées réelles** demandent d'abord deux colonnes additives dans Crenolo — `arrivee_le`, `fin_reelle_le` — et un geste dans l'interface pro. À intégrer au plan, sinon la promesse est creuse.

### 1.8 Règles métier déjà codées
- **Acompte** : `POST /public/{slug}/acompte/{jeton}` (`routers/public/acompte.py:47`), Stripe Connect, jeton 7 jours. `obligatoire` existe mais **le paiement ne conditionne jamais la réservation** (`acompte.py:17-22`).
- **Délais** : `min_booking_hours` (défaut 0), `max_booking_days` (⚠️ divergence réelle : 30 dans `business.py:34`, 60 en repli dans `reservation.py:186`).
- **Quota** : 3 réservations actives par e-mail et par salon.
- **Annulation** : `self_cancellation`, `cancellation_policy` (texte libre). **Aucun délai ni pénalité codés.**
- **Blocage client** : `fiches_clients.bloque` → 403.
- **Promotions**, **fidélité**, **facturation** (402 bloquant) : présents.

### 1.9 Tableau — connecteur Crenolo

| Ce que le connecteur peut exposer aujourd'hui | Ce qui manque | Effort |
|---|---|---|
| Lire prestations, praticiens, horaires (`GET /public/{slug}`, `routers/public/fiche.py:93`) | Rien | nul |
| Lire créneaux libres, par praticien (`GET /public/{slug}/slots`) | Filtre « prochaine dispo sur N jours » (une requête par jour aujourd'hui) | S — route additive `/slots-range` |
| Créer un RDV (`POST /public/{slug}/book`) | `client_email` obligatoire (un appelant n'en donne pas) ; pas de clé d'idempotence ; rate-limit 10/h par IP tuerait un standard | M |
| Annuler (`POST /public/{slug}/cancel/{token}`) | Le connecteur ne détient pas le jeton signé ; pas de route « annuler par téléphone + identité » | M |
| Reporter (`PUT /dashboard/bookings/{id}/horaire`) | Réservé au JWT pro + `require_active_billing` | M |
| Reconnaître un client | Aucune recherche par téléphone : pas d'index, aucune route, numéros non normalisés en base | M |
| Auth machine (`X-Internal-Secret`) | Secret **global**, non scopé, non révocable unitairement, non journalisé | M — table `api_cles(business_id, empreinte, portees, revoquee_le)` |
| Historique des associations (`extra_service_ids`) | **Durées réelles inexistantes** | L — colonnes `arrivee_le`/`fin_reelle_le`, additives |
| Garantie anti-double-booking | **Aucune contrainte SQL** | S→M — `EXCLUDE USING gist` partiel, additif, à valider contre l'historique qui peut déjà contenir des chevauchements |

### 1.10 Interface proposée — `crenolo.agenda.v1`

Principe : **tout additif**. Nouveau routeur `api/routers/connecteur/` sous `/connecteur/v1`, garde `X-Api-Key` → table `api_cles (id, business_id, empreinte, libelle, portees TEXT[], expire_le, revoquee_le, derniere_utilisation_le)`, calquée sur `inkra_api_tokens` (`app.marpeap.com/apps/api/models/inkra/api_token.py:9`). Portées : `agenda:lire`, `agenda:ecrire`, `client:lire`.

| Opération | S'appuie sur | Statut |
|---|---|---|
| `catalogue()` | `GET /public/{slug}` (`routers/public/fiche.py:93`) | existe |
| `disponibilites(service_ids[], du, au, praticien_id?)` | boucle sur `slot_service.creneaux_avec_praticiens` (`:172`) | à écrire, additif |
| `identifier_client(telephone_e164)` | `services/sms.numero_normalise` (`:49`) + nouvel index `lower(telephone)` | à écrire |
| `reserver(…, canal="vocal", cle_idempotence)` → 201 / **409** | reprend **mot pour mot** le verrou de `reservation.py:196-274` ; e-mail synthétisé si absent | à écrire, additif |
| `deplacer(booking_id, …)` | logique de `agenda.py:222` | à exposer |
| `annuler(booking_id, motif?)` | respecte `annulation.autonome_ouverte` (`services/annulation.py:15`) | à exposer |
| `confirmer_par_sms(booking_id)` | `sms_sortants` + `services/sms.texte_rappel` | existe, à câbler |

**Cinq invariants que le connecteur doit honorer, sous peine de casser l'agenda :**
1. verrou `FOR UPDATE` sur `practitioners` **triés par id**, ou sur `businesses.id` si zéro praticien ;
2. `practitioner_id IS NULL` bloque **tout le monde** ;
3. états occupants = `("confirmed","completed")` **seulement** ;
4. la réponse de `/slots` a **deux formes** — ne jamais supposer `{"slots":[…]}` ;
5. `main` est gelé : toute migration est `ADD COLUMN … IF NOT EXISTS` ou index partiel, **jamais** `NOT NULL` sans défaut.

---

## 2. Inkra

Front `notes.marpeap.com/` (Next.js) ; ⚠️ **le README du dépôt est périmé** (il décrit des routes `app/api/*` disparues). Le vrai backend est `api.marpeap.com`, code dans `app.marpeap.com/apps/api/routers/inkra/`.

- **Deux surfaces** : interne `/inkra/*` (JWT, cookie `inkra_token`) ; **externe `/api/vault/v1/*`** — `routers/inkra/external_api.py:1-45`, **Bearer haché dans `inkra_api_tokens`** (`models/inkra/api_token.py:9` : `vault_id`, `token_hash` unique, `expires_at`, `last_used_at`), **100 req/heure par token**.
- Actions vocales disponibles **sans rien écrire** : `POST /api/vault/v1/notes/from-markdown` (dicter une note), `POST …/notes/{id}/append`, `GET …/notes/search`, `POST …/ai/search` (RAG), `GET …/processes` + `POST …/processes/{id}/run` + `PATCH …/process-runs/{id}/advance` (piloter un process à la voix), `GET …/files/{id}/content`.
- Un client de référence existe : `notes.marpeap.com/agent/inkra_agent.py` (boucle d'outils Anthropic sur `/api/vault/v1`). ⚠️ **Il contient un token en dur ligne 49 — à révoquer.**

| Peut exposer aujourd'hui | Manque | Effort |
|---|---|---|
| CRUD notes, append, recherche sémantique, fichiers, process, stats, par token de vault | Rien côté API | nul |
| Auth machine propre (token haché, expirable, par vault) | Rotation/révocation depuis l'UI : non vérifiée | S |
| — | Pas de webhook sortant ; rendu BlockNote/TipTap, le connecteur doit convertir texte↔blocs (`inkra_agent.py:66`) | S |

---

## 3. Kompagnon / M-Campaign

`campaign.marpeap.com/campaign-api/` (FastAPI) + `dashboard/` (Next.js). API prod `https://api.campaign.marpeap.digital`.

- **Auth machine déjà conçue pour un agent** : en-tête **`X-Gateway-Token`** (`routers/agent.py:1-6, 62-68`). Chaîne d'isolation : `gateway_token → Instance (models/instance.py:24) → client_id → resolve_customer_id`. Le `customer_id` Google Ads n'est **jamais** accepté du client. Contrôle d'abonnement via `Subscription` + `is_trial_expired`.
- **~45 routes `/agent/*`** : campagnes (pause, enable, budget, enchères, renommage, création), mots-clés et négatifs, annonces RSA, ciblage géo, planning horaire, extensions, rapports (`/agent/reports`, `…/search-terms`, `…/impression-share`), `GET /agent/keyword-ideas`, recommandations Google, **`GET /agent/capabilities`**, `GET /agent/health`, `GET /agent/weekly-report`.
- Actions vocales évidentes : « combien j'ai dépensé cette semaine », « mets en pause la campagne X », « monte le budget à 30 € », « ajoute un mot-clé négatif ».

| Peut exposer aujourd'hui | Manque | Effort |
|---|---|---|
| Lecture des performances + pilotage complet Google Ads via un seul en-tête | Rien à construire côté API | nul |
| Isolation par instance garantie serveur | **Pas de confirmation à deux temps** pour les actions coûteuses (budget, création) — indispensable en vocal | S, côté connecteur |
| `GET /agent/capabilities` = découverte d'outils prête pour un LLM | Pas de journal d'action attribuable à un appel | S |

---

## Conclusion transverse

**Kompagnon et Inkra sont greffables tels quels** — token machine et routes déjà orientées agent. **Crenolo est le seul chantier**, et il lui manque quatre choses : une clé d'API scopée par établissement, une recherche client par téléphone, une écriture idempotente tolérant l'absence d'e-mail, et — le point dur — **une contrainte d'exclusion SQL sur `bookings`**, la non-superposition ne reposant aujourd'hui que sur un verrou applicatif qu'aucun écrivain tiers n'est obligé de reproduire.

**Deux points de sécurité relevés en passant, sans rapport avec ce chantier** : le token Inkra en dur dans `inkra_agent.py:49`, et le `X-Internal-Secret` de Crenolo qui n'est scopé par aucun établissement.
