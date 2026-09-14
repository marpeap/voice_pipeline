# Passe de brainstorming n°2 — Architecture

> Toujours aucune ligne de code. Ce document fixe **les frontières** : ce qui est un module, ce qui est un contrat, ce qui est jetable.
> ⚠️ **Recadré le 14/09** : le produit est un **service indépendant** (`docs/14-RECADRAGE-PRODUIT.md`). Les frontières décrites ici restent exactes — elles ont même **gagné en importance**, puisque c'est leur respect qui évite que le mode autonome soit une réécriture. Partout où ce document dit « l'hôte », lire « l'adaptateur, **s'il y en a un** ».
> Faits et chiffres : `docs/00-SYNTHESE.md` et `docs/recherche/`.

---

## 1. Le principe directeur

**Trois frontières décident de tout le reste :**

1. **L'inférence sort de la machine.** Le VPS porte la téléphonie et l'orchestration, jamais les modèles (plancher S2S : 16 Go de VRAM). ⚠️ **Mais la capacité est bien plus faible qu'estimé au départ** : Pipecat Cloud dimensionne **1 Go pour UNE session vocale**, LiveKit ≈ 320 Mo/session — **1 Go = un appel simultané** (correction A4 ; le chiffre de 90 Mo venait d'un test sans STT, LLM ni TTS). Tout fournisseur STT/LLM/TTS est **derrière une interface**, choisi par configuration de tenant — c'est ce qui rendra le rapatriement progressif possible (LLM → STT → TTS) sans réécriture.
2. **La logique vit dans des paquets, jamais dans un script hébergé.** C'est ce qui rend possibles simultanément le loader web, le custom element, le wrapper React et — plus tard — l'extension MV3, **qui interdit le code distant**.
3. **Le LLM ne touche jamais la base.** Il n'appelle que des outils typés, au périmètre étroit, validés côté serveur. Il n'existe aucune fonction de listage global : elle n'est pas restreinte, **elle n'existe pas**.

---

## 2. Vue d'ensemble

```
                 ┌──────────────────────────────────────────────┐
  RTC/PSTN ──►   │  BORD TÉLÉPHONIQUE   (driver interchangeable)│
   (09 …)        │  Asterisk+AudioSocket | Telnyx | Twilio | Web │
                 └───────────────┬──────────────────────────────┘
                                 │ audio 8 kHz + événements d'appel
                 ┌───────────────▼──────────────────────────────┐
                 │  RUNTIME D'APPEL  (Pipecat, 1 process/appel) │
                 │  VAD → endpointing → STT → LLM → TTS         │
                 │  barge-in · timers · masquage de latence     │
                 └───────┬───────────────────────┬──────────────┘
                         │ outils typés          │ métriques/tour
          ┌──────────────▼─────────┐   ┌─────────▼──────────────┐
          │  NOYAU AGENT           │   │  OBSERVABILITÉ         │
          │  mémoire .md + règles  │   │  1 ligne/tour en SQL   │
          │  politique d'escalade  │   │  détection d'échec     │
          └──────────────┬─────────┘   └────────────────────────┘
                         │ CONTRAT DE CONNECTEUR (le seul point d'extension)
      ┌──────────────────┼──────────────────┬───────────────────┐
   ┌──▼───────┐    ┌─────▼──────┐     ┌─────▼──────┐     ┌──────▼─────┐
   │ Crenolo  │    │   Inkra    │     │ Kompagnon  │     │ tiers /    │
   │ connecteur│   │ connecteur │     │    (?)     │     │ webhooks   │
   └──────────┘    └────────────┘     └────────────┘     └────────────┘

   PLAN DE CONFIGURATION : questionnaire → schéma → memoire.md (git) + config JSONB
   SURFACES : widget embarquable (custom element) · console · extension (plus tard)
```

---

## 3. Le contrat de connecteur — le cœur de la réutilisabilité

Un hôte devient « équipable » en implémentant **six choses**, et rien d'autre.

| # | Élément | Nature | Détail |
|---|---|---|---|
| 1 | `profile()` | lecture | Identité de l'établissement : nom, métier, adresse, horaires, langues, fuseau |
| 2 | `catalog()` | lecture | Prestations, durées **réelles**, tarifs, praticiens, contraintes (temps de pose, cabine, praticien imposé) |
| 3 | `availability(query)` | lecture | Créneaux libres — **la seule source de vérité**, jamais un cache local |
| 4 | `book / reschedule / cancel` | écriture | Idempotent, avec contrainte d'unicité côté hôte sur `(établissement, praticien, créneau)` |
| 5 | `history()` | lecture, optionnel | L'historique de RDV : durées réelles, associations, annulations, noms de famille → **keyterms** |
| 6 | `events` (webhooks) | sortant | Appel terminé, RDV créé, escalade déclenchée, correction appliquée |

**Trois règles de contrat :**
- **Toute écriture est idempotente** : clé générée au **début du tour de parole**, propagée à tous les essais (modèle Stripe : jusqu'à 255 caractères, résultat mémorisé y compris pour les erreurs, purge à 24 h).
- **Toute écriture est relue avant confirmation orale** (`read-after-write`). Un connecteur qui ne sait pas relire ce qu'il a écrit n'est pas conforme.
- **Aucun outil ne prend l'identité du client en paramètre.** Le serveur l'injecte. ⚠️ Et comme le CLI peut être masqué après un renvoi d'appel (recommandation ARCEP), l'identification pour une action sur un RDV existant passe par **SMS avec code ou DTMF**, jamais par le seul numéro appelant.

**Deux niveaux de conformité**, pour qu'un hôte pauvre puisse quand même être équipé :
- **Niveau 1 — lecture seule** : l'agent informe, prend des messages, transfère. Éléments 1, 2, 6.
- **Niveau 2 — transactionnel** : l'agent réserve, déplace, annule. Éléments 1 à 6.
Crenolo vise le niveau 2 ; **Kompagnon** (ex M-Campaign, agent Google Ads) relève du niveau 1 avec une capacité propre — `ad_call_tracking` : numéro de suivi par campagne, qualification, et **renvoi de la conversion d'appel vers Google Ads** ; Inkra n'a pas d'agenda et relève d'un profil différent (dictée, message, recherche) — donc **le contrat doit être un jeu de capacités déclarées, pas une interface monolithique** : l'hôte publie un manifeste `capabilities: [faq, message, booking, transfer, dictation…]`, et le noyau n'expose au LLM que les outils réellement déclarés.

---

## 4. Découpage en paquets

| Paquet | Langage | Rôle | Dépend de |
|---|---|---|---|
| `core-agent` | Python | Machine à états de l'appel, politique d'escalade, assemblage du prompt, appel d'outils | — |
| `runtime-pipecat` | Python | Pipeline audio : VAD, endpointing, STT, TTS, barge-in, métriques | `core-agent` |
| `providers/*` | Python | Un module par fournisseur (STT, LLM, TTS) derrière une interface commune | — |
| `telephony/*` | Python | Un driver par bord téléphonique (asterisk-audiosocket, telnyx, twilio, webrtc) | — |
| `connector-sdk` (py) | Python | Le contrat §3, ses types, sa validation, son banc de conformité | — |
| `connector-sdk` (ts) | TypeScript | Le même contrat côté hôtes Next.js | — |
| `config-schema` | Python (Pydantic) | **Source de vérité unique** du questionnaire et de la config | — |
| `memoire` | Python | Lecture/écriture disciplinée du `.md` + versionnage git | `config-schema` |
| `widget-core` | TypeScript | Cœur headless d'UI : état d'appel, transport, événements | — |
| `widget-element` | TypeScript | `<vp-widget>` custom element, Shadow DOM | `widget-core` |
| `widget-react` | TypeScript | Wrapper mince (`useRef` + `useEffect`) | `widget-element` |
| `console` | Next.js | Administration : appels, transcriptions, corrections, config | `widget-react` |

**Pourquoi ce découpage précis** : Cal.com fait exactement ce rapport `embed-react` → `embed-core`, et maintient **en parallèle** une voie « headless API + UI React optionnelle » (`@calcom/atoms`). C'est le précédent le plus transposable. **Module Federation est écarté** : il suppose un pipeline de build synchronisé des deux côtés — impossible pour une page servie par FastAPI/Jinja.

---

## 5. Configuration : un schéma, deux artefacts

```
Pydantic (config-schema)
   │  model_json_schema(mode="validation")     ← attention : pas "serialization"
   ├──► JSON Schema 2020-12 ──► JSONForms (MIT) ──► questionnaire (front)
   └──► validation serveur ──► frontmatter YAML de memoire.md
                              └──► tenant_config (JSONB, append-only, versionné)
```

- **JSONForms plutôt que rjsf** : rjsf documente lui-même `dependencies` comme obsolète (« not part of the latest JSON Schema spec ») et n'a **aucune page** sur `if`/`then`/`else` — dirimant pour un questionnaire à branchements sectoriels. JSONForms sépare schéma de données et schéma d'UI, et porte une section « Rules » de visibilité conditionnelle. (SurveyJS reste une option : la Form Library est MIT, seul le constructeur visuel est payant — et nous n'en avons pas besoin, nos schémas sont écrits par nous.)
- **Pydantic et Zod ciblent le même draft (2020-12)** : le schéma sort du back et pilote le front sans double définition. Piège : `z.date()` et `z.transform()` ne traversent pas la frontière — les horaires se modélisent en chaînes formatées, jamais en dates.
- **L'UI ne réécrit jamais le fichier entier** : elle remplace le bloc frontmatter (via la couche Document de `ruamel.yaml`, qui préserve commentaires et ordre — PyYAML en est incapable et ne le fera jamais, cf. issue #90) et **reconcatène le corps octet pour octet**.
- **Versionnage** : `memoire.md` vit dans un dépôt git sur le VPS, un commit par sauvegarde, **auteur = l'utilisateur réel** (`GIT_AUTHOR_NAME`), committer technique fixe. Bibliothèque : **Dulwich** — pur Python, aucune dépendance système ; GitPython est explicitement déconseillé dans un processus long (« tends to leak system resources »), ce qu'est un serveur FastAPI.
- **Deux modes d'édition dès le départ** : le wizard pour la configuration initiale, et une **édition directe non séquentielle** pour « changer un horaire six mois plus tard ». NN/g le dit sans détour : un wizard est *« tedious for repetitive tasks »*.

---

## 6. Données et multi-tenant

**Table partagée + `tenant_id` + RLS**, pas de base ni de schéma par tenant (coût opérationnel injustifiable sur 1–2 Go).

- `ENABLE` **et** `FORCE ROW LEVEL SECURITY` — sinon le propriétaire de la table contourne les policies.
- Rôle applicatif **non-propriétaire, sans `BYPASSRLS`**.
- Contexte posé par `set_config('app.tenant_id', …, true)` **dans la transaction** — jamais `SET` simple : avec un pool, la valeur survit à la requête et la suivante hérite du tenant précédent.
- Index composite préfixé par `tenant_id` partout.
- **RLS est un filet, pas la sécurité primaire** : le filtre applicatif reste, RLS rattrape l'oubli. Un test d'intégration qui tente une lecture croisée entre deux tenants et **doit** échouer vaut plus que toute la doc.
- Pièges documentés à connaître : les fonctions `leakproof` peuvent être évaluées **avant** le contrôle RLS ; les contraintes d'intégrité (unicité, FK) **contournent toujours** RLS et peuvent donc révéler l'existence d'une ligne d'un autre tenant.

**Secrets par tenant** : chiffrement **applicatif**, pas pgcrypto — la documentation PostgreSQL avertit que « all the data and passwords move between pgcrypto and client applications in clear text » et conclut « better do crypto inside client application ». Envelope encryption : clé maître en variable d'environnement systemd (0600, hors dépôt) → clé de données par tenant → secrets. Vault écarté (empreinte).

**Facturation** : Stripe Billing avec **Meters** (l'API `usage records` a disparu en `2025-03-31.basil`). Deux règles dès le premier événement : identifiant d'événement **déterministe dérivé de l'identifiant d'appel** (un rejeu ne facture pas deux fois), et **réconciliation quotidienne** — notre table d'appels est la source de vérité, Stripe un miroir. Lago écarté (Postgres + Redis + Sidekiq + Rails ne tiennent pas dans le budget mémoire).

**Quotas** : ne pas confondre anti-abus (slowapi, MIT — ⚠️ **ne supporte pas les WebSocket**, donc limitation à l'ouverture de session) et quota métier (compteur **transactionnel en base**, incrémenté dans la même transaction que l'écriture de l'appel — un quota en cache est un quota offert au redémarrage).

---

## 7. Surfaces d'intégration

### 7.1 Le widget — et le problème du micro
La contrainte la plus structurante du volet front : **une iframe cross-origin n'hérite pas de l'accès micro**. Sans `allow="microphone"` explicite sur la balise, `getUserMedia()` échoue ; et si la page hôte envoie un header `Permissions-Policy`, les deux politiques se combinent au plus restrictif. Chromium a délibérément déprécié ces permissions en iframe cross-origin.

Conséquence : le « je colle un script, ça marche » d'Intercom **ne transpose pas** à un widget vocal. Donc :
- **Le loader crée lui-même son iframe** avec le bon `allow` — l'intégrateur n'a pas à y penser.
- **Same-origin quand c'est possible** (nos produits maison, via reverse proxy) : tout le problème disparaît.
- **Page « CSP & Permissions Policy » publiée dès le jour 1**, avec la ligne à copier, comme Stripe le fait. Trois lignes de doc qui économisent des heures de support. Les directives qui cassent : `script-src` (rien ne se charge), `frame-src` (cadre vide, **sans erreur JS**), `connect-src` (widget monté mais muet), `worker-src` (AudioWorklet/VAD côté client).
- **Versionnage inversé, à la Stripe** : loader **non** versionné dans son URL (rétrocompatibilité assumée), **contrat de données versionné par date et épinglé par tenant**. L'erreur inverse condamne à ne jamais pouvoir corriger un bug côté client.

### 7.2 L'extension navigateur — reportée, mais rendue possible dès maintenant
MV2 est mort (plus aucun mécanisme d'exécution sur Chrome stable après le 28/07/2026). Le cas d'usage est faisable en MV3 par assemblage de patterns officiels : service worker (orchestration) + **offscreen document** (`USER_MEDIA` + `WEB_RTC`, puisqu'un service worker n'a ni `AudioContext` ni `getUserMedia`) + side panel (UI).

Mais : les trois quarts du besoin (voir les appels, la fiche appelant, éditer la config) sont couverts par une **application web ou une PWA**. Seuls « déclencher un appel depuis n'importe quelle page » et « voir l'appel sans changer d'onglet » justifient l'extension. Donc **lot ultérieur, Chrome + Edge uniquement** (5 USD une fois, base Chromium commune). Firefox reste un chantier distinct tant que l'**absence d'équivalent à `chrome.offscreen` n'est pas levée** — risque non levé. Safari ne se justifie pas à 99 USD/an avant demande client.

**La décision d'aujourd'hui** : l'interdiction de code distant en MV3 impose que la logique soit **bundlable**. Un greffon conçu uniquement comme « un script hébergé chez nous » ne sera **jamais** publiable en extension. D'où `widget-core` en paquet npm, dès le premier jour.

---

## 8. Observabilité et évaluation

**Instrumenter tout de suite, outiller le plus tard possible.**

1. **Une ligne par tour de parole en PostgreSQL** : `end_of_utterance_delay`, `llm_ttft`, `tts_ttfb`, `total_latency`, tokens entrée/sortie/**cachés**, `speech_id`, `tenant_id`. Un index sur `(tenant_id, created_at)`. Ces colonnes répondent déjà à « pourquoi cet agent est lent » et « combien cet appel a coûté ».
2. **Détection d'échec par règles avant tout LLM** : appel raccroché sous 10 s · plus de trois reformulations consécutives · silence de l'agent au-delà du seuil · demande explicite d'un humain. Quelques dizaines de lignes pour la majorité des échecs réels.
3. **Évaluation LLM-as-judge en CI** (cadre de test LiveKit, ou promptfoo MIT, 100 % local) : une vingtaine de scénarios par métier, rejoués à chaque modification. Coût d'infrastructure nul. **Mais jamais de juge LLM pour valider une entité** : un numéro se compare par égalité de chaîne.
4. **Corpus de régression** : 60 à 100 appels réels français, **rééchantillonnés 8 kHz / G.711** (tester en 16 kHz donne des résultats qui ne veulent rien dire), couvrant accents, sèche-cheveux, haut-parleur, hésitations, **auto-corrections** (« zéro six douze… non, quatorze » — mode d'échec le plus constant selon Full-Duplex-Bench v3), injections de prompt. Rejoué **k = 5 fois**, succès **intégraux** comptés.
5. **Langfuse : non** (ClickHouse à lui seul dépasse le budget mémoire ; ≥ 4 Go recommandés). **Phoenix : à tester**, sans engagement avant mesure. Une vue maison sur la table du point 1 rend 80 % du service pour 0 % de la RAM.
6. **OpenTelemetry GenAI** : utile mais **aucun attribut `gen_ai.*` n'est encore stable**, et il n'existe **aucune convention pour l'audio** — donc les attributs vocaux sont nommés d'après le vocabulaire LiveKit, derrière une petite couche d'émission maison pour absorber les changements à venir.

---

## 9. Séquence de construction proposée

| Lot | Contenu | Porte de sortie (mesurable) |
|---|---|---|
| **L0 — Mesures** | RTF NeMo-Speech.cpp sur le VPS · **WER FR 8 kHz** · RTF/RAM Piper · coût réel d'un appel témoin | Les trois inconnues bloquantes sont chiffrées. **Aucune décision de pile n'est figée avant.** |
| **L1 — Squelette d'appel** | Un bord téléphonique (D2), Pipecat, Silero + Smart Turn, STT/LLM/TTS en API, un `memoire.md` écrit à la main | L'agent décroche un vrai numéro et tient une conversation. SLO p50 ≤ 700 ms mesuré, pas estimé |
| **L2 — Contrat + connecteur Crenolo** | `connector-sdk`, banc de conformité, prise de RDV réelle | **Taux de confirmation orpheline = 0** sur 100 appels de test |
| **L3 — Plan de configuration** | `config-schema`, questionnaire JSONForms, `memoire.md` généré, git | Un commerçant configure seul en < 15 min, sans appel d'onboarding |
| **L4 — Console et boucle de correction** | Appels, transcriptions, **correction en un clic**, KPI (impasse, orpheline) | Une correction depuis une transcription modifie l'agent sans toucher un prompt |
| **L5 — Widget embarquable** | `widget-core` / `-element` / `-react`, page CSP | Le widget tourne dans Crenolo **et** dans une page non-React |
| **L6 — Deuxième greffe** | Inkra (ou Kompagnon), au niveau 1 du contrat | Le contrat tient sans modification du noyau — **c'est le vrai test de la modularité** |
| **L7 — Extension** | Chrome + Edge, offscreen + side panel | Seulement si les lots précédents sont en production |

L0 avant tout : trois chiffres qu'aucune source au monde ne publie décident du reste.

---

## 10. Ce que l'architecture refuse

- **Pas de base vectorielle**, pas de ClickHouse, pas de Vault, pas de Lago : quatre services pour quatre problèmes que le volume réel ne pose pas encore.
- **Pas de jambonz** (4 vCPU / 8 Go **et** clé commerciale en v11+), **pas de TEN** (clause de non-concurrence Agora), **pas du turn-detector LiveKit** hors LiveKit (la licence l'interdit noir sur blanc), **pas de Vocode** (mort depuis 22 mois), **pas de Rasa** (« maintenance mode » écrit dans son README), **pas de XTTS/Coqui** (CPML : usage générant du revenu interdit).
- **Pas de `libpiper` lié dans notre code** : Piper est GPL-3.0 depuis 2026 — service HTTP séparé, sans exception.
- **Pas de prompt exposé au commerçant**, jamais, sous aucune forme « avancée ».
