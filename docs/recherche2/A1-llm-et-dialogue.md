# A1 — Choix du LLM et conception du dialogue

**Agent vocal téléphonique français, prise de rendez-vous avec appel d'outils**
Date de la recherche : **13 septembre 2026**. Toutes les consultations d'URL datent de ce jour.
Cible visée : TTFT LLM **250 ms p50 / 500 ms p95**, hébergement UE souhaité, budget quasi nul, français principal.

## Convention de marquage

| Marque | Sens |
|---|---|
| **[F]** | Fait vérifié dans une source officielle citée, avec URL et date |
| **[H]** | Hypothèse de travail, explicitement posée, non vérifiée |
| **[R]** | Recommandation de l'auteur du rapport |
| **[NV]** | Non vérifié — la documentation officielle ne le dit pas, ou la source n'a pas pu être atteinte |

## Limites de la collecte (à lire avant d'utiliser les chiffres)

- **[F]** Le budget de recherche web de la session était **épuisé** (200/200 appels `WebSearch` consommés avant le début de ce travail). Tout ce rapport a donc été construit par **récupération directe d'URL officielles connues** (`WebFetch`). Conséquence : aucune découverte de page dont je ne connaissais pas déjà l'adresse. Les trous signalés `[NV]` sont majoritairement dus à cela, pas à une absence d'information chez le fournisseur.
- **[F]** Pages officielles **non atteignables** ce jour (404/403) : `docs.mistral.ai/deployment/laplateforme/prompt_caching/`, `docs.mistral.ai/capabilities/prompt_caching/`, `docs.mistral.ai/deployment/laplateforme/overview/`, `console.groq.com/docs/pricing`, `console.groq.com/pricing`, `openai.com/api/pricing/` (403), `docs.livekit.io/agents/build/prompting/`, `docs.pipecat.ai/guides/fundamentals/context-management`.
- **[F] Le résultat le plus important de la section 2 est négatif** : **aucun** des fournisseurs consultés ne publie de **TTFT p50/p95** officiel pour ses modèles texte. Groq et Cerebras publient des **tokens/seconde**, ce qui est un débit, pas une latence de premier jeton. Toute affirmation de TTFT dans une comparaison commerciale est donc, à ce jour, non sourçable chez l'éditeur. La cible 250/500 ms **devra être mesurée sur banc**, pas choisie sur catalogue.

---

# 1. Prompt caching — mécanique exacte par fournisseur

C'est le point décisif : le fichier de connaissance du commerçant (horaires, prestations, durées, règles d'annulation, définitions d'outils) vit dans le prompt système et est **réémis à chaque tour de parole**. Sur un appel de 3 minutes à 12 tours, il est donc envoyé 12 fois. Le cache décide à la fois du coût et du TTFT.

## 1.1 Tableau comparatif

| | **OpenAI** | **Anthropic** | **Google Gemini** | **Groq** | **Mistral** |
|---|---|---|---|---|---|
| Activation | **[F]** « Prompt caching is enabled by default for supported OpenAI models. » Breakpoints explicites à partir de GPT‑5.6 ; « Only implicit caching is supported » sur GPT‑5.5/5.4 et antérieurs | **[F]** Deux modes : `cache_control` au niveau racine (automatique) ou breakpoints explicites sur blocs | **[F]** « Implicit caching is enabled by default for all Gemini 2.5 and newer models. » Explicite en plus (hors Interactions API) | **[F]** Automatique, par préfixe | **[NV]** |
| **Préfixe minimum** | **[F]** « 1,024 tokens for GPT‑5.6 and later » ; « varies by request settings for earlier models » | **[F]** 512 tok (Fable 5.1, Mythos 5.1, Opus 5, Fable 5, Mythos 5) · 1 024 tok (Opus 4.8, Sonnet 5, Sonnet 4.6/4.5, Opus 4.1/4, Sonnet 4) · 2 048 tok (Mythos Preview, Opus 4.7, Haiku 3.5) · **4 096 tok (Opus 4.6, Opus 4.5, Haiku 4.5)** | **[F]** 4 096 tok (Gemini 3.8/3.7/3.6/3.5 Flash, 3.1 Pro Preview) · 2 048 tok (Gemini 2.5 Flash et Pro). Flash‑Lite non listé → **[NV]** | **[F]** « varies by model, ranging from 128 to 1024 tokens » | **[NV]** |
| **Durée de vie** | **[F]** GPT‑5.6+ : « 30 minutes after its most recent write or reuse ». Antérieurs : « typically around 5 to 10 minutes of inactivity, up to one hour » | **[F]** 5 min (défaut, `ephemeral`) ou **1 h** via `"ttl": "1h"` | **[NV]** — la page Caching n'énonce ni TTL par défaut ni TTL configurable pour le cache implicite | **[F]** « All cached data automatically expires after 2 hours without use. » | **[NV]** |
| **Coût d'écriture** | **[F]** GPT‑5.6+ : « 1.25× the standard, uncached input-token rate ». **Modèles antérieurs : aucun surcoût d'écriture** | **[F]** 1,25× le prix input (TTL 5 min) · **2×** (TTL 1 h) | **[F]** Cache *explicite* facturé au prix « Context Caching » + **stockage à l'heure**. Cache *implicite* : pas de frais d'écriture ni de stockage documentés | **[F]** « no additional fees » | **[NV]** |
| **Coût de lecture** | **[F]** GPT‑5.6+ : « 0.1× that rate ». Antérieurs : tarif « cached input » par modèle (≈ 0,1× ; 0,0125× sur gpt‑5.5) | **[F]** **0,1×** le prix input ; **0,025×** sur Fable 5.1 et Mythos 5.1 | **[F]** ~0,1× l'input (ex. Flash‑Lite 3.5 : 0,03 $ vs 0,30 $) | **[F]** « a 50% discount for cached input tokens » — **le moins bon ratio du panel** | **[F]** « cached input tokens reduce input cost by up to 90% for repeated prompts » (page tarifs, sans grille chiffrée) |
| **Invalidation** | **[F]** Changement de `model`, `tools`, `parallel_tool_calls`, `text.format`, `reasoning.effort`, `text.verbosity`, `context_management` ; « if content or a relevant setting changes before a breakpoint, the prefix after that change cannot match » | **[F]** Hiérarchie `tools` → `system` → `messages` : un changement à un niveau invalide ce niveau **et tous les suivants**. Invalident aussi : modification des définitions d'outils, bascule web search / citations, changement de `speed`, ajout/retrait d'image, changement des paramètres de *thinking* / *effort*, changement de `tool_choice` | **[NV]** | **[F]** « Changes to cached sections, including `tool_choice` and image usage, will invalidate the cache » | **[NV]** |
| Breakpoints | **[F]** Explicites (GPT‑5.6+) | **[F]** « up to 4 cache breakpoints » par requête | n/a (implicite) | n/a | **[NV]** |
| Modèles couverts | **[F]** GPT‑5.6+ complet ; implicite seulement en dessous | **[F]** « all active Claude models » | **[F]** Gemini 2.5 et plus récents | **[F]** `openai/gpt-oss-20b`, `openai/gpt-oss-120b`, `openai/gpt-oss-safeguard-20b` **uniquement** | **[NV]** |

## 1.2 Ce qu'il faut retenir pour l'architecture

1. **[F] Le seuil de 4 096 tokens de Claude Haiku 4.5 est un piège de conception.** Un prompt système de 3 000 tokens n'est **pas cachable** sur ce modèle : il sera facturé plein tarif à chaque tour, 12 fois par appel. Sur Opus 4.6 et Opus 4.5, même seuil. **[R]** Si l'on retient Haiku 4.5, il faut soit **rembourrer délibérément** le préfixe au‑delà de 4 096 tokens (ce qui coûte des tokens mais les fait passer à 0,1×), soit changer de modèle. Le calcul de bascule est immédiat : au‑delà de ~2 tours, un préfixe rembourré et caché coûte moins qu'un préfixe court non caché.
2. **[F] La hiérarchie d'invalidation d'Anthropic (`tools` → `system` → `messages`) dicte l'ordre du prompt.** Les définitions d'outils doivent être **absolument figées** pendant un appel ; toute injection dynamique (heure courante, nom de l'appelant, créneaux déjà proposés) doit venir **après** le bloc caché, jamais dedans. Le même raisonnement vaut chez OpenAI (« the prefix after that change cannot match »).
3. **[F] Chez OpenAI sur les modèles antérieurs à GPT‑5.6, l'écriture de cache est gratuite.** Le cache y est donc rentable **dès la première relecture**, sans seuil d'amortissement. Sur GPT‑5.6+ et sur Anthropic (1,25×), il faut **une** relecture pour amortir en TTL court, **deux** pour le TTL 1 h d'Anthropic (2×) — ce que la doc Anthropic écrit explicitement.
4. **[F] Groq est hors jeu sur ce critère.** Remise de 50 % seulement, et caching limité aux trois modèles `gpt-oss-*`. Pour une charge dominée par un long préfixe système, c'est cinq fois moins bon qu'un cache à 0,1×.
5. **[F] Un appel téléphonique de 3 minutes tient dans tous les TTL**, y compris les 5 minutes d'Anthropic par défaut. **[R]** Ne pas payer le TTL 1 h (2× à l'écriture) : il ne sert que si l'on veut partager le cache **entre appels successifs** du même commerçant. **[H]** Sur un commerçant à fort trafic (appels espacés de moins de 5 min), le TTL court se renouvelle de lui‑même à chaque appel ; le TTL 1 h ne devient intéressant que sur un trafic espacé de 5 à 60 minutes — soit le régime le plus probable d'un petit commerce. **[R]** À arbitrer par mesure, pas a priori.
6. **[F] Google est le seul à ne pas documenter le TTL de son cache implicite** sur la page consultée, ni ses conditions d'invalidation. C'est un angle mort à lever avant tout engagement.

---

# 2. Candidats LLM pour le vocal français

## 2.1 Tarifs publiés (USD par million de tokens sauf mention)

### OpenAI — `developers.openai.com/api/docs/pricing`, consulté le 13/09/2026 **[F]**

| Modèle | Input | Cached input | Output |
|---|---|---|---|
| gpt‑5.5 | 5,00 | 0,50 | 30,00 |
| gpt‑5.4 | 2,50 | 0,25 | 15,00 |
| **gpt‑5.4‑mini** | **0,75** | **0,075** | **4,50** |
| **gpt‑5.4‑nano** | **0,20** | **0,02** | **1,25** |
| gpt‑5.2 | 1,75 | 0,175 | 14,00 |
| gpt‑5.1 / gpt‑5 | 1,25 | 0,125 | 10,00 |
| **gpt‑5‑mini** | **0,25** | **0,025** | **2,00** |
| **gpt‑5‑nano** | **0,05** | **0,005** | **0,40** |
| gpt‑realtime‑2.1 | audio 32,00 / texte 4,00 | 0,40 | audio 64,00 / texte 24,00 |
| gpt‑realtime‑2.1‑mini | audio 10,00 / texte 0,60 | 0,30 / 0,06 | audio 20,00 / texte 2,40 |

### Anthropic — `platform.claude.com/docs/en/about-claude/pricing`, consulté le 13/09/2026 **[F]**

| Modèle | Input | Write 5 min | Write 1 h | Cache hit | Output |
|---|---|---|---|---|---|
| **Claude Haiku 4.5** | **1,00** | 1,25 | 2,00 | **0,10** | **5,00** |
| Claude Sonnet 5 | 2,00 | 2,50 | 4,00 | 0,20 | 10,00 |
| Claude Opus 5 | 5,00 | 6,25 | 10,00 | 0,50 | 25,00 |
| Claude Fable 5.1 | 10,00 | 12,50 | 20,00 | **0,25** (0,025×) | 50,00 |

**[F]** Note du même document, à ne pas négliger sur du français : « Claude 4.7 and later models and Claude Mythos Preview use a newer tokenizer… This tokenizer produces approximately 30% more tokens for the same text. » Haiku 4.5 et Sonnet 4.6 utilisent **l'ancien** tokenizer ; Opus 4.7+, Opus 5, Fable 5.x le nouveau. Sur un modèle à nouveau tokenizer, le prix affiché par million de tokens **n'est pas comparable à l'identique** : il faut majorer le volume d'environ 30 %.
**[F]** Surcoût d'outillage : la présence d'au moins un outil ajoute un prompt système caché de **496 tokens** (`auto`/`none`) ou **588 tokens** (`any`/`tool`) sur Haiku 4.5, et **354/474** sur Sonnet 5. À compter dans le préfixe cachable.

### Google — `ai.google.dev/gemini-api/docs/pricing`, consulté le 13/09/2026 **[F]**

| Modèle | Input | Output | Context caching | Stockage cache |
|---|---|---|---|---|
| Gemini 3.8 Flash | 0,75 (1,50 au 01/01/2027) | 3,75 (7,50 au 01/01/2027) | 0,075 (0,15) | 0,50 /M tok/h (1,00) |
| **Gemini 3.5 Flash‑Lite** | **0,30** | **2,50** | **0,03** | 1,00 /M tok/h |
| Gemini 3.1 Pro Preview | 2,00 (≤200k) / 4,00 | 12,00 / 18,00 | 0,20 / 0,40 | 4,50 /M tok/h |

**[F]** La page modèles décrit Gemini 3.5 Flash‑Lite comme « Our fastest, most cost-effective 3.5 model for high-throughput execution ». Aucun chiffre de latence n'accompagne cette formule.

### Mistral — `mistral.ai/pricing` et `docs.mistral.ai/getting-started/models/models_overview/`, consultés le 13/09/2026

**[F]** Modèles actifs : **Mistral Medium 3.5** (`mistral-medium-3504`), **Mistral Small 4** (`mistral-small-2603`, Apache 2.0), **Mistral Large 3** (v25.12, Apache 2.0), **Ministral 3** en 14B / 8B / 3B (v25.12), **Voxtral Mini Transcribe 2** et **Voxtral Mini Transcribe Realtime** (v26.02, transcription temps réel).
**[F]** La page tarifs ne publie **pas** de grille par modèle ; elle se contente d'un exemple (« Mistral Large costs $0.5 /M tokens in and $1.5 /M tokens out ») et d'une mention de caching (« up to 90% »). **[NV]** Tarifs de Mistral Small 4, Medium 3.5 et Ministral 3 sur La Plateforme : non obtenus. **[R]** À obtenir avant tout chiffrage définitif — c'est le principal trou de ce rapport, et il porte sur le candidat européen le plus évident.

### Hébergeurs rapides et européens

| Fournisseur | Ce qui est publié **[F]** | Source |
|---|---|---|
| **Groq** | Débits : GPT‑OSS 20B **1000 tps**, GPT‑OSS 120B **500 tps**, Llama 3.1 8B **560 tps**, Llama 3.3 70B **280 tps**, Compound / Compound Mini **450 tps**. GPT‑OSS 120B : support outils (web search, code execution) | `console.groq.com/docs/models` |
| **Cerebras** | `gpt-oss-120b` **~3000 tokens/s**, contexte 65k–131k ; `qwen-3.8-27b` **~1850 tokens/s**, contexte 64k–128k. Tiers gratuit + pay‑as‑you‑go | `inference-docs.cerebras.ai/models/overview` |
| **Scaleway** (Paris) | `mistral-small-3.2-24b-instruct-2506` **0,15 €/M in — 0,35 €/M out** · `mistral-medium-3.5-128b` 1,50 / 7,50 · `gemma-4-26b-a4b-it` 0,25 / 0,50 · `qwen3.6-35b-a3b` 0,25 / 1,50 · `deepseek-v4-flash-0731` 0,40 / 0,80 · `llama-3.3-70b-instruct` 0,90 / 0,90 · `glm-5.2` 1,80 / 5,50. Palier gratuit 1M tokens. Déploiement dédié GPU en **région Paris** : L4‑1‑24G 0,93 €/h, L40S‑1‑48G 1,72 €/h, H100‑1‑80G 3,40 €/h | `scaleway.com/en/pricing/model-as-a-service/` |
| **OVHcloud AI Endpoints** | `Meta-Llama-3.3-70B-Instruct` **0,67 €/M** in et out, contexte 131k · `gpt-oss-120b` **0,08 €/M in — 0,40 €/M out** · `gpt-oss-20b` **0,04 €/M in — 0,15 €/M out** | `ovhcloud.com/en/public-cloud/ai-endpoints/catalog/` |

**[F]** `gpt-oss-20b` sur OVHcloud à 0,04 €/M en entrée est, de loin, le tarif le plus bas relevé dans tout ce panel, et il est européen.
**[NV]** OVHcloud : la page catalogue ne détaille ni la région précise par modèle, ni une politique de rétention explicite ; elle évoque « OVHcloud's robust and confidential infrastructure ». À faire confirmer contractuellement.
**[NV]** Cerebras et Groq : aucune information de région ou de rétention sur les pages consultées. **[H]** Les deux sont réputés opérer aux États‑Unis — à traiter comme **hors UE** jusqu'à preuve contractuelle du contraire.

## 2.2 TTFT, point de présence UE, rétention

| Critère | Constat |
|---|---|
| **TTFT publié** | **[F] Aucun fournisseur du panel ne publie de TTFT p50/p95.** Groq et Cerebras publient un **débit** (tokens/s), qui ne dit rien du délai avant le premier jeton. OpenAI publie une doctrine, pas des chiffres : « Cutting 50% of your output tokens may cut ~50% of your latency » et, symétriquement, « Cutting 50% of your prompt may only result in a 1–5% latency improvement » (`developers.openai.com/api/docs/guides/latency-optimization`). **C'est une donnée de conception majeure** : réduire le prompt système n'achète presque pas de latence ; réduire la longueur des réponses en achète beaucoup. |
| **UE — OpenAI** | **[F]** Résidence des données disponible : « Europe (EEA + Switzerland) » avec le préfixe de domaine **`eu.api.openai.com`**. Rétention par défaut : « abuse monitoring logs are generated for all API feature usage and retained for up to 30 days ». Zero Data Retention éligible sur `/v1/chat/completions`, `/v1/responses`, `/v1/realtime`, `/v1/audio/*` (non éligible sur `/v1/conversations`, `/v1/assistants`, `/v1/threads`). Le cache de prompt est retenu **24 h**. (`developers.openai.com/api/docs/guides/your-data`) |
| **UE — Anthropic** | **[F] Pas d'option UE sur l'API de premier rang.** « Inference geo: Only `"us"` and `"global"` are available. » et « Workspace geo: Only `"us"` is currently available. » `inference_geo: "us"` coûte **1,1×** sur toutes les catégories de tokens, et n'est supporté qu'à partir de Claude 4.6 — **Haiku 4.5 renvoie une 400** si le paramètre est présent. (`platform.claude.com/docs/en/manage-claude/data-residency`) → **Un déploiement UE strict avec Haiku 4.5 en direct est impossible aujourd'hui.** Restent Bedrock et Google Cloud en régions européennes, dont la tarification est indépendante et non vérifiée ici **[NV]**. |
| **UE — Google** | **[NV]** La page de localisation Vertex AI n'a pas pu être lue (redirection puis contenu sans la table des régions). Les régions `europe-west*` et les garanties de résidence n'ont **pas** été vérifiées. |
| **UE — Scaleway** | **[F]** Déploiements dédiés en **région Paris**. **[NV]** La page tarifs ne formule pas d'engagement de rétention ; à confirmer. |
| **UE — Mistral** | **[NV]** Aucun engagement d'hébergement ni de rétention trouvé sur les pages atteintes. |
| **Qualité du français** | **[NV] pour tous.** Aucun fournisseur du panel ne publie de score de qualité en français, ni de benchmark francophone officiel, sur les pages consultées. **[R]** Ce critère ne peut être tranché que par une évaluation interne sur transcriptions réelles d'appels francophones — accents, chiffres parlés (« quatorze heures trente », « le 1er »), noms propres, coupures de la reconnaissance vocale. |

---

# 3. Coût réel d'un appel de 3 minutes en français

## 3.1 Hypothèses, écrites et assumées **[H]**

Aucune de ces valeurs n'est publiée par un fournisseur ; ce sont mes hypothèses de travail, à réviser dès les premières mesures.

| Paramètre | Valeur retenue | Justification |
|---|---|---|
| Durée d'appel | 3 min | Cahier des charges |
| Nombre de tours LLM | **12** | ~15 s par cycle complet (parole appelant + traitement + parole agent) |
| Prompt système (persona + règles + fiche commerçant + schémas d'outils) | **4 200 tokens** | Fixé délibérément **au‑dessus du seuil de 4 096** de Haiku 4.5 et de Gemini Flash (voir §1.2‑1). Inclut les ~496 tokens de prompt d'outillage d'Anthropic. |
| Tokens ajoutés à l'historique par tour | **110** | ~40 tok de transcription FR + ~55 tok de réponse agent + amortissement des blocs `tool_use`/`tool_result` sur les 3 tours outillés |
| Tokens de sortie par tour | **55** | Consigne « une à deux phrases », appliquée par Retell et Vapi (§5) |
| Cache | **1 écriture + 11 lectures** du préfixe système | Le TTL le plus court du panel (5 min) couvre les 3 min d'appel |
| Historique | **non caché** (facturé plein tarif) | Choix conservateur. Somme cumulée sur 12 tours = 110 × (1+2+…+12) = **8 580 tokens** d'entrée fraîche |
| Sortie totale | 55 × 12 = **660 tokens** | |

Formule appliquée :
`coût = S × p_write + S × 11 × p_read + 8 580 × p_in + 660 × p_out`, avec S = 4 200.

## 3.2 Modèle A — Claude Haiku 4.5 **[F]** sur les prix, **[H]** sur les volumes

| Poste | Calcul | Coût |
|---|---|---|
| Écriture de cache (5 min) | 4 200 × 1,25 $/M | 0,005250 $ |
| Lectures de cache (11) | 46 200 × 0,10 $/M | 0,004620 $ |
| Entrée fraîche | 8 580 × 1,00 $/M | 0,008580 $ |
| Sortie | 660 × 5,00 $/M | 0,003300 $ |
| **Total** | | **0,021750 $** ≈ **2,18 ¢ / appel** |

Contrefactuel sans cache : (4 200 × 12 + 8 580) × 1,00 $/M + 0,0033 $ = 0,05898 $. **Le cache divise la facture par 2,7.**
Contrefactuel avec un prompt système de 3 000 tokens — donc **sous le seuil de 4 096 et non cachable** : (3 000 × 12 + 8 580) × 1,00 $/M + 0,0033 $ = **0,048180 $**, soit **2,2× plus cher** qu'un prompt *plus long* mais cachable. C'est le résultat contre‑intuitif le plus important de ce rapport.

## 3.3 Modèle B — gpt‑5.4‑mini **[F]** sur les prix, **[H]** sur les volumes

**[F]** Rappel : sur les modèles antérieurs à GPT‑5.6, « Earlier models have no additional write charge » — le premier tour est facturé au tarif input normal, sans majoration.

| Poste | Calcul | Coût |
|---|---|---|
| Tour 1 (écriture, sans surcoût) | 4 200 × 0,75 $/M | 0,003150 $ |
| Lectures de cache (11) | 46 200 × 0,075 $/M | 0,003465 $ |
| Entrée fraîche | 8 580 × 0,75 $/M | 0,006435 $ |
| Sortie | 660 × 4,50 $/M | 0,002970 $ |
| **Total** | | **0,016020 $** ≈ **1,60 ¢ / appel** |

Variante **gpt‑5‑mini** (0,25 / 0,025 / 2,00) : 0,001050 + 0,001155 + 0,002145 + 0,001320 = **0,005670 $** ≈ **0,57 ¢ / appel**.
Variante **gpt‑5‑nano** (0,05 / 0,005 / 0,40) : 0,000210 + 0,000231 + 0,000429 + 0,000264 = **0,001134 $** ≈ **0,11 ¢ / appel**.
**[H]** Le cache implicite des modèles antérieurs à 5.6 dépend de « request settings » non spécifiés ; si le préfixe n'est pas capté, gpt‑5.4‑mini remonte à (4 200×12 + 8 580) × 0,75 $/M + 0,00297 = **0,047205 $**.

## 3.4 Modèle C — Gemini 3.5 Flash‑Lite **[F]** sur les prix, **[H]** sur les volumes et sur l'éligibilité au cache

**[NV]** Le seuil de cache implicite de Flash‑Lite n'est pas documenté (la doc liste 4 096 pour les Flash, 2 048 pour les 2.5). On suppose ici **[H]** que 4 200 tokens suffisent. Cache implicite : ni frais d'écriture ni stockage.

| Poste | Calcul | Coût |
|---|---|---|
| Tour 1 (plein tarif) | 4 200 × 0,30 $/M | 0,001260 $ |
| Lectures de cache (11) | 46 200 × 0,03 $/M | 0,001386 $ |
| Entrée fraîche | 8 580 × 0,30 $/M | 0,002574 $ |
| Sortie | 660 × 2,50 $/M | 0,001650 $ |
| **Total** | | **0,006870 $** ≈ **0,69 ¢ / appel** |

## 3.5 Contrepoint européen — Scaleway `mistral-small-3.2-24b` (hors périmètre demandé, ajouté car décisif)

**[NV]** Aucun cache documenté chez Scaleway. Calcul **sans cache**, donc pessimiste : entrée totale = 4 200 × 12 + 8 580 = 58 980 tokens.

| Poste | Calcul | Coût |
|---|---|---|
| Entrée | 58 980 × 0,15 €/M | 0,008847 € |
| Sortie | 660 × 0,35 €/M | 0,000231 € |
| **Total** | | **0,009078 €** ≈ **0,91 ¢€ / appel** |

**[F]→[R] Conclusion du chiffrage : un modèle européen sans aucun cache (0,91 ¢€) coûte moins cher qu'un Haiku 4.5 parfaitement caché (2,18 ¢) et se situe au niveau de Gemini Flash‑Lite caché (0,69 ¢).** L'argument « il faut un modèle américain pour le prix » ne tient pas. Sur OVHcloud, `gpt-oss-20b` à 0,04 €/M en entrée descendrait encore d'un facteur ~3,5 sur la ligne d'entrée.

## 3.6 Récapitulatif et mise à l'échelle **[H]**

| Modèle | Coût / appel 3 min | 1 000 appels/mois | UE ? |
|---|---|---|---|
| gpt‑5‑nano | 0,11 ¢ | ~1,13 $ | **[F]** oui (`eu.api.openai.com`) |
| gpt‑5‑mini | 0,57 ¢ | ~5,67 $ | **[F]** oui |
| Gemini 3.5 Flash‑Lite | 0,69 ¢ | ~6,87 $ | **[NV]** |
| Scaleway Mistral Small 3.2 (sans cache) | 0,91 ¢€ | ~9,08 € | **[F]** Paris |
| gpt‑5.4‑mini | 1,60 ¢ | ~16,02 $ | **[F]** oui |
| Claude Haiku 4.5 | 2,18 ¢ | ~21,75 $ | **[F]** **non** (us / global uniquement) |

**[F]** À cette échelle, **le coût du LLM n'est jamais le poste dominant d'un agent vocal** : la téléphonie, l'ASR et la TTS pèsent davantage. Le vrai critère de choix est donc la latence et la fiabilité d'appel d'outils, pas le prix.

---

# 4. Appel d'outils — sorties structurées, streaming, fiabilité

## 4.1 OpenAI **[F]**

- **Mode strict** : `"strict": true` dans la définition de fonction. « Setting `strict` to `true` will ensure function calls reliably adhere to the function schema, instead of being best effort. »
- **Contraintes de schéma** : « `additionalProperties` must be set to `false` for each object » ; « All fields in `properties` must be marked as `required` ». Les champs optionnels se déclarent `"type": ["string", "null"]`. Un schéma non conforme fait **rejeter la requête**.
- **Latence ajoutée** : « The first request you make with any schema will have additional latency as our API processes the schema, but subsequent requests with the same schema will not have additional latency. » **[R]** Conséquence opérationnelle directe : **faire un appel de préchauffage au démarrage du service**, pas au décroché du premier appelant. Sinon le tout premier client entend le surcoût.
- **Rétention** : « Schemas are cached for performance, and are not eligible for zero data retention. » **[F]** Point de conformité à noter : imposer ZDR **n'exclut pas** la mise en cache des schémas d'outils.
- **Streaming des appels d'outils** : événements `response.output_item.added` (appel initié, arguments vides) → `response.function_call_arguments.delta` (fragments d'arguments) → `response.function_call_arguments.done`. Les deltas sont à agréger côté client.
- **Invalidation croisée** **[F]** : modifier `tools`, `parallel_tool_calls` ou `text.format` **invalide le cache de prompt**. Outils et sorties structurées sont donc **couplés au cache** : on ne peut pas faire varier les outils par tour sans payer le préfixe entier.

## 4.2 Anthropic **[F]**

- Surcoût de tokens du prompt d'outillage : **496** (`auto`/`none`) ou **588** (`any`/`tool`) sur Haiku 4.5 ; **354/474** sur Sonnet 5 ; **286/406** sur Opus 5.
- « If no `tools` are provided, then a tool choice of `none` uses 0 additional system prompt tokens. »
- Les tokens d'outils viennent du paramètre `tools` (noms, descriptions, schémas) et des blocs `tool_use` / `tool_result`.
- **[F]** Changer `tool_choice` en cours d'appel **invalide le cache**.

## 4.3 Benchmarks publiés

- **[F] BFCL** : « The Berkeley Function-Calling Leaderboard is now at V4 », qui « evaluates the LLM's ability to call functions (aka tools) accurately » et introduit une « holistic agentic evaluation ». « Overall accuracy is the unweighted average of all the sub-categories. » (`gorilla.cs.berkeley.edu/leaderboard.html`)
- **[NV] Scores BFCL v4 par modèle** : la table est rendue dynamiquement et n'a pas pu être extraite. Aucun score ne sera cité ici plutôt que d'en inventer.
- **[NV] τ‑bench** : non consulté (budget de recherche épuisé, URL exacte inconnue). Aucun chiffre ne sera avancé.
- **[R]** Ces deux benchmarks sont **anglophones et généralistes**. Pour un agent de prise de rendez‑vous français, ils ne prédisent pas grand‑chose de ce qui casse réellement : dates relatives (« jeudi prochain », « après‑demain »), heures parlées, corrections en cours de phrase (« non, plutôt 15 h »). **Un jeu d'évaluation maison de 50 à 100 transcriptions réelles vaut mieux que n'importe quel classement public.**

---

# 5. Structure de prompt recommandée par les acteurs du vocal

## 5.1 Les trois structures officielles, côte à côte **[F]**

| Rang | **Vapi** (`docs.vapi.ai/prompting-guide`) | **Retell AI** (`docs.retellai.com/build/prompt-engineering-guide`) | **ElevenLabs Agents** (`elevenlabs.io/docs/agents-platform/best-practices/prompting-guide`) |
|---|---|---|---|
| 1 | **Identity & Personality** — « Who the assistant is, tone, communication style » | **Identity** | **Personality** |
| 2 | **Response Guidelines** — « How to speak — brevity, formatting, pacing » | **Style Guardrails** | **Environment** |
| 3 | **Guardrails** — « Hard constraints that override all other instructions » | **Response Guidelines** | **Tone** |
| 4 | **Context** — « Runtime info — caller data, current time, company info » | **Task Instructions** | **Goal** |
| 5 | **Workflow / Use Cases** — « Step-by-step playbooks for each scenario » | **Objection Handling** | **Guardrails** |
| 6 | **Examples** — « Few-shot transcripts of ideal behavior » | — | **Tools** |
| 7 | — | — | **Error handling** |

## 5.2 Les points sur lesquels les trois convergent **[F]**

- **Brièveté imposée.** Vapi : « Keep responses to one or two sentences maximum ». Retell : « Be concise: Keep responses under 2 sentences unless explaining » des sujets complexes.
- **Une question à la fois.** Retell : « Ask one question at a time: Avoid overwhelming the caller ».
- **Sectionner.** Retell : « Break large prompts into focused sections for better organization and LLM comprehension ».
- **Le coût en latence est explicite.** Vapi : « Every token costs latency. The system prompt loads into the model's context on every turn. A bloated prompt increases time to first token, which the caller experiences as dead air. »
- **Définitions d'outils actionnables.** ElevenLabs : « Clear, action-oriented tool definitions help the model invoke them correctly and recover gracefully from errors », avec un « quand l'utiliser » explicite, des exemples de format de paramètres et une consigne de récupération d'erreur **par outil**.
- **[F]** ElevenLabs est le seul à recommander des modèles nommément : « GPT‑4o or GLM 4.5 Air (recommended starting point): Best for general-purpose enterprise agents where latency, accuracy, and cost must all be balanced » ; « Gemini 2.5 Flash Lite (ultra-low latency): Best for high-frequency, simple interactions where speed is critical » ; « Claude Sonnet 4 or 4.5 (complex reasoning): Best for multi-step problem-solving, nuanced judgment, and complex tool orchestration ». **[H]** Cette liste semble dater d'une génération de modèles antérieure à celle du catalogue de septembre 2026 — à traiter comme une indication de **catégorie**, pas de modèle.
- **[NV]** LiveKit et Pipecat : pages de prompting non atteintes (404). La page d'introduction LiveKit ne contient « no specific guidance on agent instructions, system prompts, structure, brevity, tool calling patterns, latency figures, or recommended LLMs ». Rien ne sera attribué à ces deux acteurs.

## 5.3 La tension à trancher **[R]**

Il y a une **contradiction frontale** entre la doctrine des acteurs du vocal (« un prompt gonflé augmente le TTFT », Vapi) et deux faits vérifiés :

1. **[F] OpenAI** : « Cutting 50% of your prompt may only result in a 1–5% latency improvement ».
2. **[F] Anthropic / Google** : sous 4 096 tokens, **il n'y a pas de cache du tout** sur Haiku 4.5 et sur les Gemini Flash — donc raccourcir le prompt sous ce seuil **augmente** le coût et probablement le TTFT, puisque le préfixe est recalculé entier à chaque tour.

**[R] Arbitrage recommandé :** la brièveté à optimiser est celle **des réponses**, pas celle du prompt système. Concrètement :
- **Prompt système long et figé** (≥ 4 200 tokens), entièrement cachable, structuré selon l'ordre Vapi, placé **avant** tout contenu variable.
- **Définitions d'outils immuables** pendant toute la durée d'un appel (sinon invalidation en cascade, §1.2‑2).
- **Contexte dynamique** (heure, nom de l'appelant, créneaux déjà proposés, résultats d'outils) **après** le point de rupture de cache, jamais dans le préfixe.
- **Sorties bridées à une ou deux phrases**, via `max_tokens` **et** via la consigne — c'est le seul levier qui achète vraiment de la latence (« ~50% of your latency »).

---

# 6. Recommandation

**[R] 1 — Architecture de prompt, indépendante du modèle retenu.**
Préfixe système figé de **4 200 à 5 000 tokens** : ordre Vapi (Identité → Règles de réponse → Garde‑fous → Contexte statique du commerçant → Playbooks de rendez‑vous → Exemples), puis les schémas d'outils, puis **un point de rupture de cache**, puis seulement le variable. Ce dimensionnement n'est pas un luxe : il est ce qui rend le préfixe cachable chez Anthropic (4 096) et chez Google (4 096), et il est **moins cher** qu'un prompt de 3 000 tokens non cachable (§3.2). Réponses bridées à une à deux phrases.

**[R] 2 — Choix du modèle : deux pistes à départager par mesure, pas par catalogue.**
- **Piste UE stricte** : **Scaleway `mistral-small-3.2-24b`** (0,15 / 0,35 €/M, région Paris, ~0,91 ¢€ par appel **sans aucun cache**) ou **OVHcloud `gpt-oss-20b`** (0,04 / 0,15 €/M). Le coût est déjà au niveau des meilleurs américains, la souveraineté est acquise, et il reste une marge de cache non exploitée.
- **Piste qualité/outillage** : **gpt‑5‑mini** ou **gpt‑5.4‑mini** via **`eu.api.openai.com`** — c'est **[F]** le seul grand fournisseur généraliste du panel offrant une résidence « Europe (EEA + Switzerland) » documentée, avec ZDR éligible sur `/v1/chat/completions` et `/v1/responses`, et le mode `strict` de function calling.

**[R] 3 — Écarter Claude Haiku 4.5 tant que l'exigence UE tient.** **[F]** L'API de premier rang n'offre que `us` et `global` ; `inference_geo` renvoie une 400 sur Haiku 4.5. C'est un fait de plateforme, pas une question de prix. Réexaminer uniquement via Bedrock ou Google Cloud en région européenne, dont la tarification reste **[NV]**.

**[R] 4 — Écarter Groq pour cette charge.** **[F]** Remise de cache de 50 % seulement (contre 90 % ailleurs), cache limité aux trois `gpt-oss-*`, aucune région UE documentée. Le débit de 1000 tps est séduisant mais il concerne la génération, pas le TTFT — et nos réponses font 55 tokens : le débit n'est pas le goulet.

**[R] 5 — Traiter la cible 250/500 ms comme une hypothèse à valider, pas comme un critère de sélection.** **[F]** Aucun fournisseur ne publie de TTFT. Construire un banc : 200 appels synthétiques en français, préfixe caché chaud, mesure de TTFT p50/p95 depuis un point de présence UE, sur les trois candidats retenus. C'est le seul chiffre qui tranchera.

**[R] 6 — Préchauffer les schémas au démarrage du service.** **[F]** « The first request you make with any schema will have additional latency ». Un appel factice au boot évite que le premier client réel paie cette latence.

**[R] 7 — Trous à combler avant décision finale** (tous dus à l'épuisement du budget de recherche) : tarifs Mistral La Plateforme par modèle ; existence, seuil et TTL du prompt caching chez Mistral ; TTL et invalidation du cache implicite Gemini ; seuil de cache de Gemini Flash‑Lite ; régions `europe-west*` et garanties de résidence Vertex AI ; scores BFCL v4 ; τ‑bench ; engagements de rétention Scaleway et OVHcloud.

---

# Sources

Toutes consultées le **13 septembre 2026**.

| # | URL | Ce qui en est tiré |
|---|---|---|
| 1 | https://developers.openai.com/api/docs/guides/prompt-caching | Seuil 1 024 tok (5.6+), TTL 30 min, écriture 1,25×, lecture 0,1×, liste d'invalidation, `prompt_cache_key` |
| 2 | https://platform.claude.com/docs/en/build-with-claude/prompt-caching | Seuils par modèle (512 / 1 024 / 2 048 / 4 096), TTL 5 min et 1 h, hiérarchie `tools`→`system`→`messages`, 4 breakpoints |
| 3 | https://platform.claude.com/docs/en/about-claude/pricing | Grille complète Claude, multiplicateurs de cache, tokens de prompt d'outillage, note tokenizer +30 % |
| 4 | https://ai.google.dev/gemini-api/docs/caching | Cache implicite par défaut dès Gemini 2.5, seuils 4 096 / 2 048 |
| 5 | https://ai.google.dev/gemini-api/docs/pricing | Tarifs Gemini 3.8 Flash, 3.5 Flash‑Lite, 3.1 Pro, context caching, stockage horaire |
| 6 | https://ai.google.dev/gemini-api/docs/models | Catalogue Gemini, description Flash‑Lite « fastest, most cost-effective » |
| 7 | https://console.groq.com/docs/prompt-caching | Seuil 128–1024 tok, TTL 2 h, remise 50 %, 3 modèles, invalidation par `tool_choice` et images |
| 8 | https://console.groq.com/docs/models | Débits tps par modèle |
| 9 | https://developers.openai.com/api/docs/pricing | Grille GPT‑5.x complète + modèles realtime |
| 10 | https://developers.openai.com/api/docs/guides/structured-outputs | Mode strict, latence du premier schéma, function calling + `json_schema` |
| 11 | https://developers.openai.com/api/docs/guides/function-calling | `strict: true`, contraintes de schéma, événements de streaming d'arguments, non‑éligibilité ZDR des schémas |
| 12 | https://developers.openai.com/api/docs/guides/latency-optimization | 7 principes, « ~50% of your latency » (sortie) vs « 1–5% » (prompt), streaming |
| 13 | https://developers.openai.com/api/docs/guides/your-data | Résidence « Europe (EEA + Switzerland) », `eu.api.openai.com`, rétention 30 j, éligibilité ZDR, cache 24 h |
| 14 | https://platform.claude.com/docs/en/manage-claude/data-residency | `inference_geo` limité à `us`/`global`, workspace `us` seul, 1,1×, 400 sur Haiku 4.5 |
| 15 | https://mistral.ai/pricing | Structure tarifaire, exemple Large, mention cache « up to 90% » |
| 16 | https://docs.mistral.ai/getting-started/models/models_overview/ | Catalogue Mistral Medium 3.5 / Small 4 / Large 3 / Ministral 3 / Voxtral |
| 17 | https://docs.mistral.ai/ | Arborescence documentaire (absence de page caching/latence/function calling) |
| 18 | https://inference-docs.cerebras.ai/models/overview | `gpt-oss-120b` ~3000 tps, `qwen-3.8-27b` ~1850 tps, contextes |
| 19 | https://www.scaleway.com/en/pricing/model-as-a-service/ | Grille serverless en €/M, GPU dédiés région Paris |
| 20 | https://www.ovhcloud.com/en/public-cloud/ai-endpoints/catalog/ | Llama 3.3 70B 0,67 €/M, gpt‑oss‑120b 0,08/0,40, gpt‑oss‑20b 0,04/0,15 |
| 21 | https://docs.vapi.ai/prompting-guide | Structure en 6 sections, « Every token costs latency », 1–2 phrases |
| 22 | https://docs.retellai.com/build/prompt-engineering-guide | Structure en 5 sections, « under 2 sentences », « one question at a time » |
| 23 | https://elevenlabs.io/docs/agents-platform/best-practices/prompting-guide | 7 blocs, recommandations de modèles par catégorie, doctrine d'outillage |
| 24 | https://gorilla.cs.berkeley.edu/leaderboard.html | BFCL en V4, évaluation agentique holistique, définition de l'exactitude globale |
| 25 | https://docs.livekit.io/agents/build/ | Absence de doctrine de prompting sur la page d'introduction |

**Pages officielles inaccessibles le 13/09/2026** (404 ou 403, aucune donnée retenue) : `docs.mistral.ai/deployment/laplateforme/prompt_caching/` · `docs.mistral.ai/capabilities/prompt_caching/` · `docs.mistral.ai/deployment/laplateforme/overview/` · `console.groq.com/docs/pricing` · `console.groq.com/pricing` · `groq.com/pricing` · `openai.com/api/pricing/` (403) · `docs.livekit.io/agents/build/prompting/` · `docs.pipecat.ai/guides/fundamentals/context-management` · `www.cerebras.ai/pricing` (table non rendue) · `docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/locations` (table de régions non rendue).
