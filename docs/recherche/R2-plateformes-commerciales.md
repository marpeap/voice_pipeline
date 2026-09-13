# R2 — Plateformes commerciales d'agents vocaux téléphoniques
## État au 13 septembre 2026 · focus « utilisable gratuitement » · français · sortie du lock-in

**Toutes les données ci-dessous ont été relevées sur des pages officielles (pricing, docs, changelogs, APIs de tarification des fournisseurs) le 2026-09-13.** Les URLs sont en section *Sources*. Ce qui n'a pas pu être confirmé à la source est écrit **« non vérifié »** et n'a été remplacé par aucune estimation. Les prix sont en USD tels que publiés, sauf Vonage (publié en EUR).

Trois registres sont séparés dans tout le document :
- **[F] Fait vérifié** — lu sur une page officielle, URL citée.
- **[H] Hypothèse** — raisonnement ou calcul dérivé, dont les paramètres sont explicités.
- **[R] Recommandation** — mon avis, pas un fait.

---

## 0. Les cinq choses à retenir avant de lire le détail

1. **[F] Deux des dix plateformes demandées n'existent plus.** PlayAI : `play.ai` ne résout plus (ENOTFOUND au 13/09/2026) ; le produit standalone a été arrêté après l'acquisition par Meta. Air.ai : le domaine héberge aujourd'hui une société de defense tech sans rapport (« Air, formerly Govini »), aucune mention de voix, d'agents ni de pricing. À retirer de toute short-list.
2. **[F] La contrainte française n'est pas le prix, c'est le numéro.** Les guidelines réglementaires Twilio pour la France sont explicites : les numéros `+331`→`+335` (local) et `+339` (national) sont réservés aux **appels manuels / interpersonnels** ; l'**appel automatisé et le démarchage imposent un numéro « Polyvalent Vérifié » (NPV)** en `+3316229`, `+33948353` ou `+33948194`. L'achat exige une **adresse en France** (boîte postale refusée) + **K-bis / SIREN-SIRET** pour une entreprise, ou pièce d'identité + justificatif de domicile pour un particulier. **Aucun crédit d'essai ne couvre cela** : les essais gratuits servent à tester la boucle technique, pas à appeler de vrais numéros français.
3. **[F] Le plus gros crédit gratuit du marché est Deepgram : 200 $, sans minimum, sans expiration, sans carte bancaire.** Loin devant AssemblyAI (50 $), Telnyx pretrial (25 $ AI), Retell (10 $), Plivo (10 $), Vonage (2 €).
4. **[F] Le seul free tier permanent et réellement suffisant pour un agent complet est Google Gemini Live** : `gemini-3.1-flash-live-preview` est marqué « Free of charge » en entrée **et** en sortie sur le free tier — contrepartie officielle : « Used to improve our products: **Yes** » (vos audios servent à entraîner). En payant, il coûte **0,005 $/min en entrée + 0,018 $/min en sortie**, soit le speech-to-speech le moins cher du marché.
5. **[F] Deepgram fait expirer ses prix promotionnels demain, le 14 septembre 2026.** Voice Agent Standard passe de **0,056 $/min à 0,075 $/min** (+34 %), Flux TTS cesse d'être gratuit dans Voice Agent. Toute décision prise sur la grille actuelle doit être refaite avec la grille post-14/09.

---

## 1. Plateformes commerciales d'agents vocaux

### 1.1 Tableau comparatif

| Plateforme | Prix plateforme | Modèles (LLM/TTS/STT) | Essai gratuit / free tier | Latence **annoncée officiellement** | API | Français | Self-host | Lock-in |
|---|---|---|---|---|---|---|---|---|
| **Vapi** | **0,05 $/min** (+ 0,005 $/msg chat) | **At cost — « $0 if you bring your own API key »** | **non vérifié** (aucun crédit mentionné sur la page billing officielle) | **~800 ms** bout-en-bout (FAQ officielle) | REST + webhooks + SDK, API-first | **Oui** [F] — `fr-FR-DeniseNeural` documentée ; Deepgram Nova 2/3 « Multi » recommandé pour le FR | **Non** — « Vapi does not support on-premise deployments » | **Faible** |
| **Retell AI** | 0,055 $/min infra → **0,07–0,31 $/min** affiché tout compris | À la carte, chaque brique tarifée séparément | **10 $ de crédits** | **non vérifié** (docs = outils de mesure, aucun chiffre annoncé) | **REST + WebSocket** (LLM WS + monitor WS), SDK Node/Python | **Oui** [F] — `fr-FR` et `fr-CA`, 90+ langues | non vérifié | **Faible-moyen** — BYO LLM via WebSocket, officiel |
| **Bland AI** | Start **0,14 $/min** · Build **299 $/mois + 0,12 $/min** | **Tout inclus — « No token charges »** | **2 crédits + 1 numéro entrant (valeur 15 $/mo), sans carte** | **sub-400 ms** (docs officielles) | REST + WebSocket temps réel | **Oui** [F] — `fr`, `fr-CA` ; modèle Fluent multilingue | **Oui** — on-prem / VPC pour secteurs régulés | **Élevé sur les modèles** (pile propriétaire, BYO non documenté) / **faible sur les numéros** (API de portage complète) |
| **Synthflow** | **Contrats entreprise à partir de 30 000 $/an**, aucun tarif public à la minute | non vérifié | « build for free » (homepage) ; plafond **200 min** de trial pour les plans créés par revendeur | **sub-100 ms** (couche télécom) vs **sub-500 ms** (FAQ) — deux chiffres non comparables sur la même page | API documentée, type (REST/WS) **non vérifié** | **non vérifié** — « multilingual » annoncé, aucune liste de langues officielle | non vérifié | **Élevé (contrat)** |
| **ElevenLabs Agents** | **0,080 $/min** sur **tous** les tiers · burst au-delà de la concurrence **0,160 $/min** | **LLM facturé en sus** ; ASR + TTS + modèle de tour de parole **propriétaires** | **Free permanent : 15 min/mois + 4 appels concurrents** | **non vérifié** (« low-latency » sans chiffre) | **WebSocket + REST + SDK React/Swift/Kotlin/RN** | **Oui** [F] — 31 langues via l'option *All* | **Non** | **Moyen** — BYO LLM oui, voix non remplaçable |
| **Vogent** | **0,09 $/min** (voix standard) · **0,14 $/min** (premium) | Stack maison (« ultra-low-latency LLMs tuned on millions of conversations ») | **non vérifié** (la FAQ pose la question, aucun montant publié) | **200 ms** — le plus bas annoncé du panel, conditionné aux modèles et voix maison | REST + WebSocket TTS + Web SDK | **non vérifié** | **Oui** — page « On-premise Deployment », périmètre non précisé | **Moyen** — SIP ouvert (import Twilio/Vonage/Telnyx), LLM maison |
| **Millis AI** | **0,02 $/min** + pass-through at-cost (STT 0,0043 $/min, TTS 0,001→0,25 $/1k car.) | **At cost. « Your LLM: No charge for using your own custom LLM »** | **non vérifié** | **600 ms** — et **« 500 ms »** dans le header de la même page (**incohérence officielle**) | REST + SDK web/mobile/desktop + widget | **Oui** [F] — 32 langues listées nominativement, French inclus | non vérifié | **Le plus faible du panel** |
| **Thoughtly** | **500 $/mois minimum** (plan Flex), usage « illimité », **aucun $/min public** | **BYOK voix** (ElevenLabs, Cartesia…) ; BYO LLM non documenté | **14 jours**, appels internes uniquement, **compte supprimé automatiquement** ensuite | **non vérifié** | REST + spéc OpenAPI publiée | 34+ langues annoncées, **liste non publiée** → FR non vérifié | non vérifié | **Moyen-faible** techniquement (BYOK + BYOC Twilio/Telnyx) / **élevé** contractuellement |
| **PlayAI** | — | — | — | — | — | — | — | **Produit arrêté** (`play.ai` ne résout plus) |
| **Air.ai** | — | — | — | — | — | — | — | **Plateforme disparue** ; domaine repris par un acteur défense |

### 1.2 Lectures

- **[F] Trois plateformes seulement publient une décomposition at-cost honnête** : Vapi, Retell et Millis. Bland et Thoughtly vendent du tout-inclus (plus cher à la minute, mais prévisible). Synthflow ne publie plus rien sous 30 000 $/an.
- **[F] Le français est vérifié explicitement chez Vapi, Retell (`fr-FR`/`fr-CA`), Bland, ElevenLabs et Millis.** Il est **non vérifié** chez Synthflow, Vogent et Thoughtly — ce qui, pour un projet dont le français est la langue principale, les met hors jeu tant que ce point n'est pas confirmé par leur support.
- **[F] Self-host confirmé : Bland et Vogent uniquement.** Vapi le refuse explicitement par écrit. Pour ElevenLabs Agents, aucune option n'est documentée.
- **[F] Classement des latences annoncées** : Vogent 200 ms < Bland sub-400 ms < Millis 500/600 ms < Vapi ~800 ms. Retell, ElevenLabs et Thoughtly n'annoncent **aucun** chiffre. **[H]** Ces chiffres ne sont pas comparables entre eux : aucune plateforme ne publie sa méthodologie de mesure, et le « sub-100 ms » de Synthflow porte sur la couche télécom, pas sur le tour de parole.

---

## 2. APIs « voice agent » des grands fournisseurs

### 2.1 OpenAI Realtime API

Modèles au catalogue le 13/09/2026 : `gpt-realtime-2.1`, `gpt-realtime-2.1-mini`, `gpt-realtime-2`, `gpt-realtime-1.5`, `gpt-realtime-mini`, `gpt-realtime`, `gpt-audio-1.5`, `gpt-audio-mini`, `gpt-audio`.

| Modèle | Audio in /1M tok | Audio cached in /1M | Audio out /1M tok |
|---|---|---|---|
| gpt-realtime-2.1 / -2 / -1.5 / gpt-realtime | **32,00 $** | 0,40 $ | **64,00 $** |
| gpt-realtime-2.1-mini / gpt-realtime-mini | **10,00 $** | 0,30 $ | **20,00 $** |
| gpt-audio-1.5 / gpt-audio | 32,00 $ | n/a | 64,00 $ |
| gpt-audio-mini | 10,00 $ | n/a | 20,00 $ |

Texte sur `gpt-realtime-2.1` : 4,00 $ in /1M · 0,40 $ cached · 24,00 $ out /1M. Fenêtre 128 000 tokens, 32 000 tokens de sortie max, cutoff 30 sept. 2024.

- **Équivalent par minute : non vérifié** — OpenAI ne publie aucune table tokens/seconde audio.
- **Free tier : aucun.** La table de rate limits de `gpt-realtime-2.1` indique explicitement **Free = « Not supported »**. Tier 1 = 200 RPM / 1 000 RPD / 40 000 TPM.
- **Latence : non vérifié** (le guide parle de « low first-audio latency » sans chiffre).
- **Français : non vérifié** (aucune liste de langues sur les pages consultées).

### 2.2 Google Gemini Live API — **le seul à publier prix/token ET prix/minute**

| Modèle | Free tier | Audio in (payant) | Audio out (payant) |
|---|---|---|---|
| `gemini-3.1-flash-live-preview` | **Gratuit** (in et out) | **3,00 $/1M ou 0,005 $/min** | **12,00 $/1M ou 0,018 $/min** |
| `gemini-3.5-live-translate-preview` (70+ langues) | **Gratuit** | 3,50 $/1M ou 0,0053 $/min | 21,00 $/1M ou 0,0315 $/min |
| `gemini-3.5-transcribe-live` (STT streaming WS) | **Gratuit** | 3,50 $/1M ou 0,005 $/min | 21,00 $/1M ou 0,004 $/min (texte) |
| `gemini-3.5-transcribe` (STT batch) | **Gratuit** | 2,00 $/1M ou 0,003 $/min | 12,00 $/1M ou 0,002 $/min (texte) |
| `gemini-2.5-flash-native-audio-preview-12-2025` | **Gratuit** | 3,00 $/1M audio/vidéo · 0,50 $ texte | 12,00 $/1M audio · 2,00 $ texte |

- **[F] Base de conversion publiée par Google : 25 tokens audio par seconde.** C'est la seule équivalence token↔minute officielle de tout ce rapport. Elle donne « ~0,0368 $/min » blended pour Live Translate et « ~0,009 $/min » pour Transcribe Live (25 tok/s en entrée, 175 tokens texte/minute en sortie).
- **[F] Contrepartie du free tier, écrite noir sur blanc : « Used to improve our products: Yes »** en gratuit, **No** en payant. Sur des appels clients réels, c'est disqualifiant ; sur du prototypage, c'est le meilleur rapport du marché.
- **Quotas chiffrés du free tier (RPM/TPM/sessions simultanées) : non vérifié** (page rate-limits rendue en JS).
- **Français : non vérifié nominativement** — « 70+ languages » annoncé sur Live Translate, sans liste.
- Grounding Google Search sur Live 3.1 : 5 000 requêtes gratuites/mois partagées, puis 14 $/1 000 requêtes.

### 2.3 Deepgram Voice Agent API — **attention, grille qui change le 14/09/2026**

| Tier Voice Agent | Pay-As-You-Go | Growth |
|---|---|---|
| Standard | **0,056 $/min jusqu'au 14/09, puis 0,075 $/min** | 0,051 → 0,068 $/min |
| Standard – **BYO TTS** | 0,065 $/min | 0,051 $/min |
| Custom – **BYO LLM** | 0,050 → 0,065 $/min | 0,041 → 0,059 $/min |
| Custom – **BYO LLM + TTS** | **0,050 $/min** | 0,041 $/min |
| Advanced | 0,122 → 0,163 $/min | 0,110 → 0,146 $/min |

- **[F] Piège de facturation** : « calculated based on **websocket connection time** » — le temps de connexion, pas le temps de parole. Les silences et les blancs sont facturés.
- **[F] Crédit gratuit : 200 $ à l'inscription — « No minimums. No expiration. No credit card required. »** C'est le plus gros du marché.
- **[F] Concurrence** : 45 connexions WSS en PAYG, 60 en Growth.
- **[F] Langues** : `flux-general-en` (anglais seul) et `flux-general-multi`. La page Voice Agent annonce 10 langues sans liste → depuis la doc Deepgram STT, **`flux-general-multi` couvre EN/ES/FR/DE/HI/RU/PT/JA/IT/NL**, français inclus.
- **Latence : non vérifié** sur les pages pricing. Les publications produit annoncent une détection de fin de tour **~260 ms p50**, **< 400 ms** pour Flux Multilingual, et un gain de **200–600 ms** sur la latence de réponse versus pipeline classique.

### 2.4 AWS — Amazon Nova Sonic / Nova 2 Sonic (Bedrock)

Prix lus dans le flux de tarification officiel AWS (`b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/bedrock/USD/current/bedrock.json`), la page pricing étant rendue dynamiquement.

| Modèle | Modalité | Région | Input /1M | Output /1M |
|---|---|---|---|---|
| **Nova 2 Sonic** | Speech | us-east-1 / us-west-2 | **3,00 $** | **12,00 $** |
| Nova Sonic | Speech | us-east-1 | 3,40 $ | 13,60 $ |
| Nova Sonic | Speech | **eu-north-1 (Stockholm)** | **4,10 $** | **16,30 $** |
| Nova 2 Sonic | Text | us-east-1 | 0,33 $ | 2,75 $ |
| Nova Sonic | Text | us-east-1 | 0,06 $ | 0,24 $ |

- **Équivalent par minute : non vérifié** (AWS ne publie pas de taux tokens/seconde audio).
- **Free tier : aucun free tier spécifique vérifié** pour Nova Sonic ; la page renvoie au AWS Free Tier générique sans allocation chiffrée.
- **Latence et langues : non vérifié** (model card : « low latency and support for multiple languages », sans chiffre ni liste).
- **[F] Surcoût européen** : Nova Sonic à Stockholm coûte **+20 %** en sortie versus us-east-1. Nova 2 Sonic n'est pas listé en région européenne.

### 2.5 Azure Voice Live API

Prix extraits de l'**API officielle Azure Retail Prices** (la page pricing charge ses valeurs en JS). Identiques sur eastus / westeurope / **francecentral** sauf mention. Quatre tiers, définis par le LLM choisi.

| Compteur (par **1K tokens**) | Pro | Standard | Lite |
|---|---|---|---|
| LLM Audio Input | 0,032 $ (**32 $/1M**) | 0,011 $ (11 $/1M) | 0,004 $ (4 $/1M) |
| LLM Audio Output | 0,064 $ (**64 $/1M**) | 0,022 $ (22 $/1M) | **non vérifié** |
| LLM Audio Cached | 0,0004 $ | 0,00033 $ | 0,00004 $ |
| LLM Text Input / Output | 0,004 $ / 0,016 $ | 0,00066 $ / 0,00264 $ | 0,00011 $ / 0,00044 $ |
| **Standard Speech** Audio In / Out | 0,017 $ / 0,031 $ | 0,015 $ / 0,026 $ | 0,015 $ / 0,025 $ |
| **Custom Speech** Audio In / Out | 0,040 $ / 0,055 $ | 0,039 $ / 0,050 $ | 0,038 $ / 0,050 $ |
| **BYO** Standard Speech In / Out | 0,0125–0,015625 $ / 0,023–0,02875 $ | | |

Tiers : **Pro** = gpt-realtime, gpt-4o, gpt-4.1, gpt-5, gpt-realtime-2/2.1 · **Standard** = gpt-realtime-mini, gpt-4o-mini, gpt-4.1-mini, gpt-5-mini · **Lite** = gpt-5-nano, phi4-mm-realtime, phi4-mini · plus **Voice Live BYO** et **Voice Live Avatar**.

- **[F] Le coût réel = tokens LLM + tokens Speech additionnés.** Azure Voice Live Pro facture **exactement les tarifs OpenAI** sur la partie LLM, **plus** une couche Speech en sus. C'est structurellement le plus cher du panel.
- **[F] Free tier F0** : STT **5 h audio/mois**, TTS neural **0,5 M caractères/mois**, Speech Translation 5 h/mois. **Aucune allocation F0 dédiée à Voice Live** → non vérifié.
- **Latence : non vérifié.** **Français** sur Voice Live : non vérifié (Azure Speech supporte `fr-FR` et `fr-CA` par ailleurs — voir §4).
- **[F] Point positif** : région **francecentral** disponible aux mêmes tarifs, ce qui compte pour la résidence de données.

### 2.6 Cartesia

Modèle par **crédits mensuels + minutes d'agents prépayées**, pas de prix/caractère affiché.

| Plan | Prix | Crédits/mois | Agents prépayés | TTS Sonic-3.6 | STT Ink-2 | Concurrence TTS/STT/appels |
|---|---|---|---|---|---|---|
| **Free** | 0 $ | 20 K | **1 $** | ~27 min | ~1 h 51 | 2 / 8 / 8 |
| Pro | 5 $/mo | 100 K | 5 $ | ~133 min | ~9 h 16 | 3 / 12 / 12 |
| Startup | 49 $/mo | 1,25 M | 49 $ | ~1 667 min | — | – / – / 20 |
| Scale | 299 $/mo | 8 M | 299 $ | ~10 667 min | ~740 h 44 | 15 / 60 / 60 |

- **[F] Voice agents : 0,06 $/min** d'appel, tous tiers ; **téléphonie Cartesia 0,014 $/min** avec un numéro fourni.
- **[F] Le plan Free n'inclut pas la licence d'usage commercial** — elle commence au plan Pro (5 $/mois). Le clonage instantané aussi.
- **[H] Prix/minute TTS dérivé** (non affiché tel quel par Cartesia) : Pro 5 $ / 133 min ≈ **0,038 $/min** ; Scale 299 $ / 10 667 min ≈ **0,028 $/min**.
- **[F] Français : oui**, la page Languages liste explicitement **French** et **Canadian French** (44 langues au total).
- **Latence : non vérifié** — ni la page pricing ni la doc Sonic-3.6 n'affichent de chiffre en ms. Les ~190 ms qui circulent viennent de tiers.

### 2.7 Rime — **le seul fournisseur du rapport à publier des latences chiffrées**

| Plan | Prix | Inclus |
|---|---|---|
| **Starter** | **0,03 $ / 1 000 caractères** (« ~0,03 $ par minute d'audio ») | **~800 minutes gratuites (~800k caractères), sans carte bancaire**, 20 générations TTS simultanées |
| Enterprise | Custom | concurrence illimitée, SLA, **cloud / on-prem / VPC**, BAA HIPAA, SOC 2 Type II |

| | **Coda** | **Mist v3** |
|---|---|---|
| **TTFA P50** (concurrence 1) | **96 ms** | **37 ms** |
| **TTFA P90** | **98 ms** | **56 ms** |
| Latence **self-hosted** | sub-100 ms | ~70 ms |
| Langues production | EN, AR, **FR**, DE, HI, JA, PT, ES | EN, **FR**, DE, ES |
| Voix | 184 | 94 |
| Streaming | HTTP + WebSockets | HTTP + WebSockets |

- **[F] Le français est explicitement supporté sur les deux modèles**, et Rime propose officiellement du **on-prem / VPC** en Enterprise — combinaison rare.
- **[F] Attention aux sources périmées** : la grille « Mist 0,03 $ / Arcana 0,04 $ / Coda 0,05 $ » et les « 3 000 minutes gratuites » qui circulent chez des tiers **ne sont plus sur la page officielle** au 13/09/2026, qui n'affiche qu'un tarif Starter unique à 0,03 $/1k et ~800 minutes offertes.
- Intégrations annoncées : LiveKit, Pipecat, Twilio.

### 2.8 Récapitulatif §2

| Fournisseur | Unité | Prix speech-to-speech | Équiv./min **officiel** | Gratuit | Latence **officielle** | Français |
|---|---|---|---|---|---|---|
| OpenAI `gpt-realtime-2.1` | tokens | 32 $ in / 64 $ out /1M | non publié | **aucun** | non chiffrée | non vérifié |
| OpenAI `gpt-realtime-mini` | tokens | 10 $ in / 20 $ out /1M | non publié | aucun | non chiffrée | non vérifié |
| **Google Gemini 3.1 Flash Live** | tokens **ou minutes** | 3 $ in / 12 $ out /1M | **0,005 $ in / 0,018 $ out** | **oui, gratuit** (données réutilisées) | non chiffrée | non vérifié |
| **Deepgram Voice Agent Std** | min de **connexion WS** | — | **0,056 → 0,075 $/min** | **200 $ de crédit** | non chiffrée | FR dans `flux-general-multi` |
| Deepgram Voice Agent Adv. | min WS | — | 0,122 → 0,163 $/min | idem | non chiffrée | idem |
| AWS Nova 2 Sonic | tokens | 3,00 $ in / 12,00 $ out /1M | non publié | pas de free tier dédié | non chiffrée | non vérifié |
| Azure Voice Live Pro | tokens (LLM **+** Speech) | 32 $ / 64 $ audio LLM **+** 17 $ / 31 $ Speech /1M | non publié | F0 générique, rien pour Voice Live | non chiffrée | non vérifié |
| Azure Voice Live Lite | tokens | 4 $ in /1M audio LLM (+ Speech) | non publié | idem | non chiffrée | non vérifié |
| **Cartesia** Managed Agents | min d'appel | — | **0,06 $/min** (+ 0,014 $ téléphonie) | Free : 20K crédits + 1 $/mois | non chiffrée | **oui (FR + CA-FR)** |
| **Rime** Coda / Mist v3 | caractères | 0,03 $/1 000 car. | ~0,03 $/min | **~800 min offertes** | **TTFA P50 37–96 ms** | **oui** |

---

## 3. Téléphonie + IA intégrée — couverture France

### 3.1 Twilio — le seul à publier une grille France complète

| Poste | Prix |
|---|---|
| **ConversationRelay (couche IA)** | **0,07 $/min** |
| Appel **entrant**, numéro local FR | **0,0100 $/min** |
| Appel **sortant** vers fixe FR | **0,0187 $/min** |
| Appel sortant vers **mobile FR (depuis l'EEE)** | **0,0404 $/min** (Orange, SFR, Bouygues, Free) |
| Appel sortant vers mobile FR (hors EEE) | 0,1603 $/min |
| Services spéciaux FR | 0,5513 $/min |
| **Numéro local FR** | **1,35 $/mois** |
| Browser/app (WebRTC), SIP interface, **BYOC** | 0,0040 $/min |
| Media Streams / SIPREC | 0,0044 $/min |
| Transcription temps réel | 0,027 $/min (batch 0,024 $) |

- **Prix mensuel des numéros mobiles FR et NPV : non vérifié** — seul le local 1,35 $/mo est affiché ; il faut le CSV « Download Number Prices » ou la console.
- **[F] Essai gratuit, grille actuelle** : **75 minutes de voix**, 100 SMS, 3 000 e-mails. Restrictions : **numéros vérifiés uniquement (5 max)**, **limité au pays d'inscription**, gabarits de message imposés (pas de TwiML custom), **expiration à 30 jours**. Le « 15,50 $ de crédit » qui circule encore chez des tiers **ne figure plus dans la doc officielle** — à ne pas retenir.
- **[F] Réglementaire FR** : voir §0 point 2 (adresse FR obligatoire, K-bis, numéros NPV pour l'appel automatisé).

### 3.2 Telnyx

| Poste | Prix |
|---|---|
| Voice engine IA (orchestration + STT + TTS hébergés) | **0,05 $/min** |
| LLM (add-on, Kimi sur GPU Telnyx) | ≈ 0,004 $/min, facturé au token |
| Tout compris annoncé par Telnyx | ≈ **0,056 $/min** — **profil : entrant local US** |
| Voice API (plateforme) | 0,002 $/min |
| SIP trunking entrant / sortant | à partir de 0,0032 $ / 0,005 $/min |
| Media streaming WebSockets | 0,0035 $/min |
| Numéro local | **1,00 $/mois — tarif US** (dégressif jusqu'à 0,25 $ à 5 K+) |

- **France : non vérifié (page dynamique).** `/country-specific-requirements` est intégralement rendue côté client ; aucune occurrence de « France » dans le HTML servi. Le tarif vitrine est US et la page précise « Rates may vary by destination ».
- Plans : PAYG 0 $, Committed **500 $/mois** minimum, Enterprise **5 000 $/mois** minimum.
- **[F] Essai** : la doc officielle **ne chiffre aucun crédit** ; elle impose un **numéro vérifié** comme unique destination et **une seule commande de numéro**. Le help center mentionne un compte « pretrial » à **25 $ de crédits AI** (produits AI seuls, sans carte, + 1 numéro local US), remplacé par **5 $ de crédit universel** à l'upgrade — source help center, pas page pricing.

### 3.3 Vonage

**Prix entrant/sortant France et prix du numéro français : non vérifié (calculatrice JS + feuille de prix derrière authentification).** `vonage.com` renvoie 403 à toute récupération standard.

Valeurs **globales** statiquement présentes sur la page Voice API Pricing :

| Poste | EUR | USD |
|---|---|---|
| **Vonage AI Services — Voice Bot : NLU** | **0,05000 €/min** (arrondi à la minute supérieure) | 0,05500 $ |
| Pack Monitoring & Support | **4 630 €/mois** | 5 093 $ |
| Appel « internet » (SIP/WebRTC) | 0,00420 €/min | 0,00492 $ |
| Appel WebSocket | 0,00420 €/min | — |
| Transcription | 0,03855 €/min | 0,04510 $ |
| ASR Standard / Premier | 0,01690 €/15 s / 0,02060 €/60 s | 0,01978 $ / 0,0240 $ |
| TTS standard / premium / premier | 0,00067 € / 0,00280 € / 0,01111 € par 100 car. | — |
| Détection répondeur avancée | 0,00720 €/appel | 0,00843 $ |

- **[F] Mention réglementaire** : « For any other network (Virtual, Voice over IP, Outbound Toll Free…), the default price of **0,414 €** will be charged. » — un appel mal routé coûte 10× le tarif normal.
- **[F] Essai** : **2 € de crédit**, appels vocaux **limités au seul numéro enregistré**, et **le crédit d'essai ne permet pas d'acheter un numéro virtuel**. Source : help center, **page en 403** → à reconfirmer au dashboard.
- **Statut d'AI Studio : non vérifié** — la page pricing parle aujourd'hui de « Vonage AI Services: Voice Bot Package ».

### 3.4 Infobip

**Aucun chiffre France récupérable : non vérifié (page dynamique).** L'export officiel de la page le dit : « We display the average price across all supported networks for each country. Per-network pricing is available in Portal. » Seul add-on chiffré : **enregistrement voix et vidéo 0,0021 €/min**. La couche IA (« Voice AI Agents », « AgentOS ») est au catalogue **sans prix public**. Aucun montant d'essai gratuit indiqué.

### 3.5 Plivo — **disqualifié pour un agent vocal français entrant**

| Poste France | Prix |
|---|---|
| **Appels entrants France (local, mobile, SIP)** | **« Not Supported »** — les trois lignes |
| **Location de numéro français** | **Aucune section sur la page France** (elle existe pour les US : local 0,50 $/mo) |
| Sortant fixe FR depuis l'EEE | 0,0195 $/min (hors EEE : 0,0530 $) |
| Sortant mobile FR depuis l'EEE | 0,0426 $/min · **grands opérateurs 0,0495 $** |
| Sortant mobile FR hors EEE | 0,3030 $/min · grands opérateurs 0,3530 $ |
| Browser SDK / SIP | 0,0033 $/min |
| **Voice AI agent** | **0,03 $/min, hors téléphonie** |
| Téléphonie pour agents | sortant dès 0,0010 $/min, entrant 0,0028 $/min |

- **[F] Le plan Pay-as-you-go couvre uniquement « United States & India »** et plafonne à **2 500 $** d'usage mensuel. La couverture 190+ pays — donc la France — est réservée au plan **Enterprise à partir de 1 000 $/mois**.
- **[F] Essai : 10 $ de crédits, sans carte bancaire.** Mais il ne permet pas de monter un agent français.

### 3.6 Récapitulatif §3

| | Couche IA | Entrant FR | Sortant fixe FR | Sortant mobile FR (EEE) | Numéro FR/mois | Essai gratuit |
|---|---|---|---|---|---|---|
| **Twilio** | 0,07 $/min | **0,0100 $/min** | **0,0187 $/min** | **0,0404 $/min** | **1,35 $** (local) | 75 min voix, num. vérifiés, 30 j |
| **Telnyx** | **0,05 $/min** + LLM ≈0,004 $ | non vérifié | non vérifié | non vérifié | non vérifié (1,00 $ US) | pas de crédit chiffré ; pretrial 25 $ AI → 5 $ |
| **Vonage** | 0,05 €/min (NLU) + 4 630 €/mo | non vérifié | non vérifié | non vérifié | non vérifié | **2 €**, num. enregistré seul, pas d'achat de numéro |
| **Infobip** | non publié | non vérifié | non vérifié | non vérifié | non vérifié | non chiffré |
| **Plivo** | 0,03 $/min hors télécom | **non supporté** | 0,0195 $/min | 0,0426–0,0495 $/min | **non listé** | 10 $ sans CB — mais FR = Enterprise 1 000 $/mo |

---

## 4. STT / TTS commerciaux en pipeline — prix, FR, free tier

### 4.1 STT

| Fournisseur | Modèle | Prix streaming | Batch | Free tier | FR |
|---|---|---|---|---|---|
| **Deepgram** | Nova-3 mono | **0,0048 $/min** (normal 0,0077 $) | 0,0043 $/min | **200 $ de crédit** | ✅ `fr`, `fr-CA` |
| **Deepgram** | Nova-3 multilingue | **0,0058 $/min** (normal 0,0092 $) | 0,0052 $/min | idem | ✅ |
| **Deepgram** | **Flux** (agents vocaux) | 0,0065 $/min EN · **0,0078 $/min multi** | — | idem | ✅ via `flux-general-multi` |
| **AssemblyAI** | Universal-Streaming | **0,15 $/h = 0,0025 $/min** [H, calcul] | 0,15 $/h | **50 $ de crédits** | ✅ (EN, ES, **FR**, DE, IT, PT) |
| **AssemblyAI** | Universal-3.5 Pro Realtime | 0,45 $/h = **0,0075 $/min** [H] | 0,21 $/h | idem | ✅ |
| **Azure** | Speech to Text S1 temps réel | **1,00 $/h = 0,0167 $/min** [H] | Batch 0,18 $/h · Fast 0,36 $/h | **F0 : 5 h audio/mois** | ✅ `fr-FR`, `fr-CA` |
| **Google** | STT V2 Standard (dont Chirp) | **0,016 $/min** (0–500k min) | Dynamic Batch **0,003 $/min** | **aucun sur V2** (V1 : 60 min/mois) | ✅ |
| **OpenAI** | gpt-4o-transcribe | ~0,006 $/min | idem | aucun | ✅ |
| **OpenAI** | gpt-4o-mini-transcribe | ~0,003 $/min | idem | aucun | ✅ |

**[F] Deux pièges de facturation à connaître :**
- **AssemblyAI** : « Streaming is billed **per session duration** — the time the WebSocket connection is open, not the duration of audio sent. **Idle connection time counts.** » Sur un agent vocal, chaque silence est facturé. Même piège que Deepgram Voice Agent.
- **Google STT V2 n'a aucun free tier.** Les 60 minutes gratuites/mois n'existent que sur la table **V1**.

**[F] AssemblyAI vend aussi une Voice Agent API tout-en-un à 4,50 $/h = 0,075 $/min** (STT + LLM + TTS + orchestration).

**[F] Grille dégressive Google STT V2** : 0,016 $/min (0→500k) · 0,010 $ (500k→1M) · 0,008 $ (1M→2M) · 0,004 $ (>2M). Chirp est facturé au tarif « Standard ».

### 4.2 TTS

| Fournisseur | Modèle | Prix | Free tier | Latence officielle | Voix FR |
|---|---|---|---|---|---|
| **ElevenLabs** | **Flash v2.5** / Turbo / v3 Conversational | **0,05 $ / 1 000 car.** | Free : 10 000 crédits/mois → **20 000 car. Flash** | **~75 ms** | FR supporté (32 langues) — **nb de voix FR non vérifié** |
| **ElevenLabs** | v3 / Multilingual v2 | **0,10 $ / 1 000 car.** | 10 000 car./mois | ~280 ms (v3 Conv.) | ✅ `fr-FR` + `fr-CA` |
| **Rime** | **Mist v3** / Coda | **0,03 $ / 1 000 car.** | **~800 min offertes** | **TTFA P50 37 ms / 96 ms** | ✅ **explicite** |
| **Cartesia** | Sonic-3.6 | Pro ≈ **0,038 $/min** [H] | 20 000 crédits/mois, **sans licence commerciale** | **non vérifiée** | ✅ `fr`, `fr-FR`, `fr-CA` |
| **Azure** | Neural TTS (S1) | **15,00 $ / 1M car.** | **F0 : 0,5 M car./mois** | non vérifiée | **6 voix Neural HD fr-FR** + 3 multilingues + 11 standard |
| **Azure** | Neural HD | 22,00 $ / 1M car. | idem | non vérifiée | idem |
| **Google** | Chirp 3: HD | 30,00 $ / 1M car. | **1 M car./mois** | non vérifiée | **30 voix fr-FR** (+30 fr-CA) |
| **Google** | Neural2 / Polyglot | 16,00 $ / 1M car. | 1 M car./mois | non vérifiée | 3 voix Neural2 fr-FR |
| **Google** | WaveNet / Standard | **4,00 $ / 1M car.** | **4 M car./mois** | non vérifiée | 2 + 2 voix fr-FR |
| **OpenAI** | gpt-4o-mini-tts | 0,60 $/1M tok texte in · **12,00 $/1M tok audio out** | aucun | non vérifiée | ✅ |
| **OpenAI** | tts-1 / tts-1-hd | 15,00 $ / 30,00 $ par 1M car. | aucun | non vérifiée | ✅ |

**[F] Restrictions juridiques des free tiers TTS — critiques pour un usage client :**
- **ElevenLabs Free : pas d'usage commercial et attribution obligatoire.**
- **Cartesia Free : pas de licence d'usage commercial** (elle démarre au plan Pro à 5 $/mois).
- **Rime Starter : ~800 minutes offertes sans carte bancaire**, aucune restriction commerciale mentionnée sur la page → **[R] c'est le free tier TTS le plus exploitable légalement pour un projet réel en français.**

**[F] Plans ElevenLabs** : Free 0 $ (10 000 crédits) · Starter 6 $ (30 000) · Creator 22 $ (121 000) · Pro 99 $ (600 000) · Scale 299 $ (1,8 M) · Business 990 $ (6 M). Les modèles Flash consomment 0,5 crédit/caractère, d'où le rapport de 2 sur le nombre de caractères.
**[F] ElevenLabs Scribe (STT)** : v2 à 0,22 $/h, v2 Realtime à 0,39 $/h.
**[F] Google TTS facture les espaces, sauts de ligne et balises SSML** (sauf `<mark>`). Voix françaises : **43 pour fr-FR**, 45 pour fr-CA.
**[F] Azure** dispose de 6 voix Neural HD `fr-FR` (dont `Vivienne:DragonHDLatestNeural`, `Remy`, `Marc:MAI-Voice-2`, `Soleil`) — le catalogue français le plus travaillé du panel, avec 0,5 M car./mois gratuits à vie sur F0.

---

## 5. Coût réel d'une minute d'appel — trois assemblages, calcul détaillé

### 5.1 Hypothèses de calcul — **à lire avant les chiffres**

Ces cinq paramètres déterminent tout. Ils sont **[H]**, pas **[F]**, et chacun peut être ajusté.

| # | Hypothèse | Valeur retenue | Justification |
|---|---|---|---|
| H1 | Part de parole de l'agent dans l'appel | **50 %** — soit 0,5 min de TTS par minute d'appel | Convention pour un dialogue équilibré. Un agent bavard monte à 60–70 % et le coût TTS suit proportionnellement. |
| H2 | Débit de parole synthétisée en français | **150 mots/min**, ~6 caractères par mot espace comprise = **900 caractères par minute de parole** | Débit conversationnel courant. Le français est plus verbeux que l'anglais à contenu égal. |
| H3 | **Volume TTS facturé par minute d'appel** | **H1 × H2 = 450 caractères/min d'appel** | C'est le multiplicateur central de tous les calculs TTS ci-dessous. |
| H4 | Coût LLM par minute | **0,0011 $/min** (GPT-5 mini) ou **0,0013 $/min** (Gemini 3.5 Flash Lite) | **[F partiel]** — ce sont les valeurs par minute **publiées par LiveKit sur sa page pricing officielle**, qui convertit elle-même les tarifs modèles en $/min pour un usage agent vocal. C'est la seule conversion $/min disponible pour les LLM texte. |
| H5 | Appel **entrant** sur numéro français | Twilio **0,0100 $/min** + numéro **1,35 $/mois** | Seule grille FR complète publiée (§3.1). Le sortant coûte 2× à 4× plus (0,0187 $ fixe, 0,0404 $ mobile). |
| H6 | Facturation à la **connexion WebSocket** | ignorée dans les totaux | Deepgram Voice Agent et AssemblyAI Streaming facturent le temps de connexion, pas le temps de parole. **Sur un agent avec de longs blancs, le coût réel dépasse ces totaux.** |

> **Avertissement de méthode** : aucun des totaux ci-dessous n'est publié tel quel par un fournisseur. Ce sont des **additions de tarifs officiels** sous les hypothèses H1–H6. Changez H1 ou H2 et la ligne TTS bouge d'autant.

### 5.2 Assemblage A — tout-commercial clé en main

**Vapi (orchestration) + Twilio FR (téléphonie) + Deepgram Nova-3 multi (STT) + ElevenLabs Flash v2.5 (TTS) + GPT-5 mini (LLM), clés apportées**

| Poste | Tarif officiel | Calcul | $/min d'appel |
|---|---|---|---|
| Plateforme Vapi | 0,05 $/min | — | **0,0500** |
| Téléphonie Twilio, entrant FR | 0,0100 $/min | — | **0,0100** |
| STT Deepgram Nova-3 multilingue | 0,0058 $/min | — | **0,0058** |
| TTS ElevenLabs Flash v2.5 | 0,05 $ / 1 000 car. | 450 car. × 0,05 $ / 1 000 | **0,0225** |
| LLM GPT-5 mini | 0,0011 $/min (réf. LiveKit) | — | **0,0011** |
| | | **TOTAL** | **0,0894 $/min** |

**Fixe mensuel** : numéro FR Twilio 1,35 $/mois. Concurrence Vapi : 10 $/ligne/mois au-delà du socle.
**Coût de 1 000 minutes** : 1 000 × 0,0894 = **89,40 $** + 1,35 $ = **90,75 $/mois**.

**Variante A′ — ElevenLabs Agents (tout-en-un)** : 0,080 $/min + LLM 0,0011 $ + Twilio entrant FR 0,0100 $ = **0,0911 $/min**. Plus simple, mais le TTS et l'ASR ne sont pas remplaçables.
**Variante A″ — Bland AI (tout inclus)** : 0,14 $/min plan Start, téléphonie et modèles compris, **numéro FR non vérifié**. Le plus cher, le plus prévisible, zéro assemblage.

### 5.3 Assemblage B — hybride (orchestration auto-hébergée + APIs commerciales)

**Pipecat ou LiveKit Agents auto-hébergé sur VPS existant + Twilio FR + Deepgram Nova-3 multi + Rime Mist v3 + Gemini 3.5 Flash Lite**

| Poste | Tarif officiel | Calcul | $/min d'appel |
|---|---|---|---|
| Orchestration (Pipecat / LiveKit Agents, open source, sur VPS déjà payé) | 0 $ | — | **0,0000** |
| Téléphonie Twilio, entrant FR | 0,0100 $/min | — | **0,0100** |
| STT Deepgram Nova-3 multilingue | 0,0058 $/min | — | **0,0058** |
| TTS Rime Mist v3 | 0,03 $ / 1 000 car. | 450 car. × 0,03 $ / 1 000 | **0,0135** |
| LLM Gemini 3.5 Flash Lite | 0,0013 $/min (réf. LiveKit) | — | **0,0013** |
| | | **TOTAL** | **0,0306 $/min** |

**Coût de 1 000 minutes** : **30,60 $** + 1,35 $ de numéro = **31,95 $/mois**. **[H] Soit 66 % moins cher que l'assemblage A**, pour un travail d'intégration de quelques jours.

**Variante B′ — speech-to-speech Gemini Live, le moins cher vérifiable :**

| Poste | Tarif officiel | $/min |
|---|---|---|
| Gemini 3.1 Flash Live — audio **in** | 0,005 $/min (publié par Google) | **0,0050** |
| Gemini 3.1 Flash Live — audio **out** | 0,018 $/min (publié par Google) | **0,0180** |
| Téléphonie Twilio entrant FR | 0,0100 $/min | **0,0100** |
| | **TOTAL** | **0,0330 $/min** |

**[F] Et sur le free tier Gemini, les deux premières lignes tombent à 0 $** → **0,0100 $/min**, la téléphonie seule. **[F] Contrepartie : « Used to improve our products: Yes ».**

**Variante B″ — LiveKit Cloud sur le plan Build gratuit** : **[F]** 1 000 minutes d'agent + 2,50 $ de crédits Inference (≈ 50 min de modèles) + 1 000 minutes SIP tierces + 5 sessions concurrentes, **gratuits chaque mois**, en dur (« the included allowance is a hard cap and new requests fail after it's exceeded »). **[F] Le numéro gratuit inclus est américain** — pour la France il faut un trunk SIP tiers, facturé 0,004 $/min au-delà des 1 000 min incluses. **[F] Pipecat Cloud** : agent-1x à 0,01 $/min actif (0,0005 $ réservé), PSTN 0,018 $/min, SIP 0,003–0,02 $/min, WebRTC voix 1:1 **gratuit**, Krisp VIVA **gratuit jusqu'à 10 000 min/mois**.

### 5.4 Assemblage C — tout-OSS auto-hébergé (estimé)

**Pipecat + faster-whisper (STT) + un TTS neuronal libre + un LLM local, sur GPU loué, avec trunk SIP français**

C'est l'assemblage où le calcul change de nature : **il n'y a plus de coût par minute, il y a un coût par heure de GPU allumé**. Le prix à la minute dépend donc entièrement du **taux d'occupation**.

**Base de coût [F]** : RunPod, GPU **L4 24 Go à 0,49 $/h** (page pricing officielle, 13/09/2026) — suffisant [H] pour faire tourner simultanément faster-whisper + un TTS + un petit LLM quantifié.

- 0,49 $/h ÷ 60 = **0,00817 $ par minute de GPU allumé**
- Sur 30 jours en continu : 0,49 $ × 24 × 30 = **352,80 $/mois**

| Volume d'appels mensuel | GPU 24/7 | Coût GPU/min d'appel | + Twilio entrant FR | **Total $/min** |
|---|---|---|---|---|
| **1 000 min** (≈ 33 min/jour) | 352,80 $ | 0,3528 $ | 0,0100 $ | **0,3628 $/min** |
| **5 000 min** | 352,80 $ | 0,0706 $ | 0,0100 $ | **0,0806 $/min** |
| **20 000 min** | 352,80 $ | 0,0176 $ | 0,0100 $ | **0,0276 $/min** |
| **43 200 min** (100 % d'occupation, 1 appel continu) | 352,80 $ | 0,0082 $ | 0,0100 $ | **0,0182 $/min** |
| **129 600 min** (3 appels concurrents en continu) [H] | 352,80 $ | 0,0027 $ | 0,0100 $ | **0,0127 $/min** |

**[H] Conclusion du calcul C, et c'est le point le plus important du rapport : en dessous d'environ 5 000 minutes par mois, le tout-OSS sur GPU loué coûte plus cher que le tout-commercial.** Le point d'équilibre avec l'assemblage B (0,0306 $/min) se situe [H] autour de **17 000 minutes/mois**. Le self-host devient rentable par le volume, jamais par la petite échelle.

**Correctif si le GPU n'est pas loué** : sur une machine déjà payée et allumée (c'est le cas du parc VPS existant), le coût marginal d'une minute tombe à **la téléphonie seule, soit 0,0100 $/min** — mais **[H]** un VPS 1 Go sans GPU ne fera tourner ni un LLM local ni un TTS neuronal en temps réel ; seul un pipeline « STT local léger + LLM d'API + TTS d'API » y tient, ce qui est l'assemblage B, pas C.

**[H] Réserves sérieuses sur la qualité française de l'assemblage C** :
- **STT** : Whisper large-v3 est donné à **11,0 % de WER en français** sur la carte modèle OpenAI — c'est utilisable mais nettement au-dessus des STT commerciaux en conditions téléphoniques 8 kHz. Des variantes distillées francophones existent (`bofenghuang/whisper-large-v3-distil-fr-v0.2`).
- **TTS** : le catalogue libre est pauvre en français de qualité conversationnelle. Kokoro-82M supporte le français mais **[F, carte modèle]** « support for non-English languages may be absent or thin due to weak G2P and/or lack of training data », avec très peu de voix françaises. **[R] C'est la brique qui fera échouer un tout-OSS français, pas le STT ni le LLM.**

### 5.5 Synthèse des trois assemblages

| | **A — tout-commercial** | **B — hybride** | **B′ — Gemini Live** | **C — tout-OSS (GPU loué)** |
|---|---|---|---|---|
| **$/min (1 000 min/mois)** | **0,0894 $** | **0,0306 $** | **0,0330 $** (0,0100 $ en free tier) | **0,3628 $** |
| **$/min (20 000 min/mois)** | 0,0894 $ | 0,0306 $ | 0,0330 $ | **0,0276 $** |
| Coût mensuel à 1 000 min | 90,75 $ | 31,95 $ | 34,35 $ | 365,80 $ |
| Travail d'intégration | Quelques heures | Quelques jours | Quelques jours | Semaines |
| **Lock-in** | Faible (BYO clés) | **Très faible** | Faible (une API à remplacer) | **Nul** |
| **Qualité FR** | Élevée | Élevée | Non vérifiée nominativement | **Risquée (TTS)** |
| **Confidentialité** | Contractuelle | Contractuelle | **Free tier : audios réutilisés pour l'entraînement** | **Totale** |

---

## 6. Recommandation

**[R]** Ce qui suit est un avis, construit sur les faits ci-dessus, pour un budget quasi nul, le français en langue principale et la volonté de brancher son propre système plus tard.

### 6.1 Ce que je ferais, dans cet ordre

**Étape 1 — prototyper à coût nul, sans engager l'architecture (semaines 1–2).**
Ouvrir **Deepgram (200 $ de crédit, sans expiration, sans carte)** et **Rime Starter (~800 minutes TTS offertes, français explicite, sans carte)**. Ces deux crédits couvrent largement la phase de mise au point et **[F]** aucun des deux n'impose de restriction d'usage commercial comparable à celle d'ElevenLabs Free ou de Cartesia Free. Orchestrer avec **Pipecat** ou **LiveKit Agents**, tous deux open source, sur le VPS existant. **[F]** Le plan **LiveKit Build** ajoute 1 000 minutes d'agent + 1 000 minutes SIP gratuites par mois, à vie.

**Étape 2 — la question du numéro français avant tout le reste.**
**[R] C'est ici que le projet se joue, pas sur le prix à la minute.** Avant d'écrire une ligne de code d'agent, vérifier qu'on peut obtenir un numéro français conforme : adresse en France, K-bis, et **numéro NPV si l'agent appelle en sortant**. **[F]** Twilio est le seul fournisseur du panel à publier à la fois la grille FR complète (0,0100 $/min entrant, 1,35 $/mois le numéro) et les exigences réglementaires écrites. **[R] Commencer par l'entrant** : moins cher, réglementairement plus simple, et il évite entièrement la question du NPV.

**Étape 3 — se poser sur l'assemblage B.**
**[H] 0,0306 $/min**, soit trois fois moins que le tout-commercial, avec un lock-in quasi nul : l'orchestration est du code que vous possédez, et chacune des trois briques (STT, TTS, LLM) se remplace par une variable d'environnement. **[R] C'est l'assemblage qui répond exactement à la contrainte « exploiter les essais gratuits maintenant, brancher son propre système plus tard »** — parce que « plus tard » n'exige alors aucune migration, seulement un changement de fournisseur brique par brique.

**Étape 4 — n'envisager le tout-OSS (C) qu'au-delà de ~17 000 minutes/mois.**
**[H]** En dessous, il coûte plus cher que ce qu'il remplace, et **[R]** le TTS français libre n'est pas au niveau d'un usage client. La bonne trajectoire est de rapatrier les briques **une par une, dans l'ordre du rapport coût/risque** : le LLM d'abord (le plus mûr en local), le STT ensuite, le TTS en dernier — jamais l'inverse.

### 6.2 Ce que j'écarterais, et pourquoi

| À écarter | Motif |
|---|---|
| **PlayAI, Air.ai** | **[F]** N'existent plus. |
| **Plivo** | **[F]** Appels entrants France « Not Supported », aucun numéro FR listé, et la couverture FR impose l'Enterprise à 1 000 $/mois. |
| **Synthflow, Thoughtly** | **[F]** Tickets d'entrée de 30 000 $/an et 500 $/mois. Incompatibles avec un budget quasi nul, et français non vérifié pour les deux. |
| **Azure Voice Live Pro** | **[F]** Facture les tarifs OpenAI **plus** une couche Speech en sus. Structurellement le plus cher. (Le free tier F0 de Azure Speech pris séparément — 5 h STT + 0,5 M car. TTS/mois — reste, lui, intéressant.) |
| **OpenAI Realtime** | **[F]** Aucun free tier (« Free: Not supported »), 64 $/1M en sortie audio, soit ~5× Nova 2 Sonic et ~5× Gemini Live. À réserver au cas où sa qualité conversationnelle serait décisive. |
| **Gemini Live free tier en production client** | **[F]** « Used to improve our products: Yes ». Parfait pour prototyper, à proscrire sur des appels clients réels. |
| **ElevenLabs Free / Cartesia Free pour du réel** | **[F]** ElevenLabs Free interdit l'usage commercial et impose l'attribution ; Cartesia Free n'inclut pas la licence commerciale. |

### 6.3 Trois pièges de facturation à surveiller [F]

1. **Deepgram Voice Agent et AssemblyAI Streaming facturent le temps de connexion WebSocket, pas le temps de parole.** Les silences comptent. Sur un agent qui attend beaucoup, le coût réel peut doubler par rapport aux totaux du §5.
2. **Les prix promotionnels Deepgram expirent le 14 septembre 2026** (demain) : Voice Agent Standard passe de 0,056 $ à 0,075 $/min, Flux TTS cesse d'être gratuit. Refaire tout calcul sur la grille post-14/09.
3. **Vonage facture 0,414 € par minute par défaut** pour tout réseau autre que fixe et mobile (virtuel, VoIP, toll-free sortant) — soit environ 10× le tarif normal sur un appel mal routé.

---

## 7. Sources — toutes consultées le 2026-09-13

### Plateformes d'agents vocaux
**Vapi** — https://vapi.ai/pricing · https://docs.vapi.ai/faq · https://docs.vapi.ai/customization/multilingual · https://docs.vapi.ai/quickstart/billing
**Retell AI** — https://www.retellai.com/pricing · https://docs.retellai.com/build/language-support.md · https://docs.retellai.com/integrate-llm/overview.md · https://docs.retellai.com/api-references/llm-websocket.md · https://docs.retellai.com/reliability/check-actual-latency.md
**Bland AI** — https://www.bland.ai/pricing · https://docs.bland.ai/llms.txt · https://docs.bland.ai/api-v1/post/calls · https://docs.bland.ai/api-v1/get/sip-port-check.md · https://docs.bland.ai/api-v2/post/tts-ws.md
**Synthflow** — https://synthflow.ai/pricing · https://synthflow.ai/ · http://docs.synthflow.ai/pricing
**ElevenLabs Agents** — https://elevenlabs.io/pricing/agents · https://elevenlabs.io/docs/agents-platform/overview · https://elevenlabs.io/docs/eleven-agents/customization/voice/customization/language
**Vogent** — https://www.vogent.ai/ · https://docs.vogent.ai/platform-overview/billing.md · https://docs.vogent.ai/voicelab/on-premise.md · https://docs.vogent.ai/telephony/sip/overview.md
**Millis AI** — https://www.millis.ai/ · https://docs.millis.ai/pricing · https://docs.millis.ai/introduction
**Thoughtly** — https://www.thoughtly.com/pricing · https://docs.thoughtly.com/platform/billing.md · https://docs.thoughtly.com/agents/voice-byok.md · https://docs.thoughtly.com/phone-number/byoc.md
**Air.ai** — https://www.air.ai/ · https://air.ai/about (domaine repris par une société défense)
**PlayAI** — `play.ai` : domaine non résolu (ENOTFOUND) au 2026-09-13

### APIs voice agent des grands fournisseurs
**OpenAI** — https://developers.openai.com/api/docs/pricing (301 depuis platform.openai.com/docs/pricing) · https://developers.openai.com/api/docs/models/gpt-realtime-2.1 · https://developers.openai.com/api/docs/guides/realtime
**Google** — https://ai.google.dev/gemini-api/docs/pricing · https://ai.google.dev/gemini-api/docs/live
**Deepgram** — https://deepgram.com/pricing · https://developers.deepgram.com/docs/flux · https://developers.deepgram.com/docs/models-languages-overview · https://developers.deepgram.com/docs/flux/voice-agent-eager-eot
**AWS** — https://aws.amazon.com/bedrock/pricing/ + flux officiel https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/bedrock/USD/current/bedrock.json · https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-sonic.html
**Azure** — https://azure.microsoft.com/en-us/pricing/details/speech/ + https://prices.azure.com/api/retail/prices (filtre `contains(meterName,'Voice Live')`) · https://learn.microsoft.com/en-us/azure/ai-services/speech-service/voice-live
**Cartesia** — https://cartesia.ai/pricing · https://cartesia.ai/languages · https://docs.cartesia.ai/build-with-cartesia/tts-models/latest
**Rime** — https://www.rime.ai/pricing

### Téléphonie
**Twilio** — https://www.twilio.com/en-us/voice/pricing/fr · https://www.twilio.com/en-us/products/conversational-ai/pricing · https://www.twilio.com/en-us/guidelines/fr/regulatory · https://www.twilio.com/docs/usage/trials · https://www.twilio.com/docs/voice/twiml/connect/conversationrelay
**Telnyx** — https://telnyx.com/pricing/conversational-ai · https://telnyx.com/pricing/call-control · https://telnyx.com/pricing/numbers · https://developers.telnyx.com/docs/account-setup/using-trial-account · https://telnyx.com/country-specific-requirements (rendu client, FR non extractible)
**Vonage** — https://www.vonage.com/communications-apis/voice/pricing/ · https://api.support.vonage.com/hc/en-us/articles/212554438 (**403 en accès direct**)
**Infobip** — https://www.infobip.com/pricing · https://www.infobip.com/voice/pricing (calculatrices JS)
**Plivo** — https://www.plivo.com/voice/pricing/fr/ · https://www.plivo.com/pricing/ · https://www.plivo.com/voice/pricing/

### STT / TTS
https://deepgram.com/pricing · https://www.assemblyai.com/pricing · https://www.assemblyai.com/blog/introducing-multilingual-universal-streaming · https://azure.microsoft.com/en-us/pricing/details/cognitive-services/speech-services/ · https://prices.azure.com/api/retail/prices (West Europe, USD) · https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts · https://cloud.google.com/speech-to-text/pricing · https://cloud.google.com/text-to-speech/pricing · https://docs.cloud.google.com/text-to-speech/docs/list-voices-and-types · https://developers.openai.com/api/docs/pricing · https://elevenlabs.io/pricing · https://elevenlabs.io/pricing/api · https://elevenlabs.io/docs/models

### Infrastructure d'orchestration et self-host
**LiveKit** — https://livekit.io/pricing (relevé intégral de la page, y compris la table de tarifs Inference par minute) · https://docs.livekit.io/deploy/admin/quotas-and-limits/
**Pipecat Cloud / Daily** — https://www.daily.co/pricing/pipecat-cloud/
**RunPod** — https://www.runpod.io/pricing
**Modèles OSS** — https://huggingface.co/hexgrad/Kokoro-82M (limites annoncées sur les langues non anglaises) · https://huggingface.co/bofenghuang/whisper-large-v3-distil-fr-v0.2 · https://github.com/openai/whisper/discussions/1762 (WER français de large-v3)

### Non vérifié — liste explicite
Essai gratuit **Vapi**, **Vogent**, **Millis** · latence **Retell**, **ElevenLabs Agents**, **Thoughtly**, **Cartesia**, **OpenAI Realtime**, **Gemini Live**, **Deepgram Voice Agent**, **Nova Sonic**, **Azure Voice Live** · français **Synthflow**, **Vogent**, **Thoughtly**, **OpenAI Realtime**, **Gemini Live** (nominativement), **Nova Sonic**, **Azure Voice Live** · self-host **Retell**, **Synthflow**, **Millis**, **Thoughtly** · portage de numéros **Vapi**, **Retell**, **ElevenLabs**, **Millis** · **prix France Telnyx / Vonage / Infobip** (pages dynamiques) · prix des numéros **mobiles FR et NPV** chez Twilio · équivalence token↔minute chez **OpenAI**, **AWS**, **Azure** · quotas chiffrés du free tier **Gemini** · allocation F0 dédiée à **Azure Voice Live** · LLM Audio Output du tier **Azure Voice Live Lite** · nombre de voix FR chez **ElevenLabs** et **Cartesia** · tarif STT **Chirp3/HD** distinct du tarif Standard Google · statut actuel de **Vonage AI Studio** · tarif au **trunk SIP français d'OVHcloud** (page sans grille minute exploitable).
