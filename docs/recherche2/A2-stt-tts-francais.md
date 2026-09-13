# A2 — STT et TTS en API pour le français téléphonique (8 kHz / G.711)

> **Date de consultation de toutes les sources : 2026-09-13.** Aucune source secondaire, aucun benchmark de blog tiers, aucun prix reconstitué de mémoire.
> **Périmètre** : agent vocal de prise de rendez-vous, français principal, audio téléphonique 8 kHz G.711 (µ-law), cibles **STT finalisation ≤ 200 ms p95** et **TTS TTFB ≤ 150 ms p50**, UE souhaitée, verrouillage à éviter (rapatriement auto-hébergé prévu).
> **Budget WebSearch épuisé en cours de travail** (200/200). Tout ce qui suit a été obtenu par **WebFetch direct des URL officielles** (docs éditeurs, pages de tarifs éditeurs, API de tarifs Azure Retail). C'est signalé ici parce que cela réduit la couverture : quelques pages n'ont pas pu être retrouvées faute de recherche, elles sont listées en §10.

## Légende

| Marque | Sens |
|---|---|
| **[F]** | Fait, lu dans une source officielle citée, avec URL |
| **[H]** | Hypothèse de travail, explicitement mienne, à vérifier en L0 |
| **[R]** | Risque identifié, conséquence chiffrée quand c'est possible |
| **[NV]** | Non vérifié — l'information n'a pas été trouvée dans une source officielle ; **elle n'est pas inventée, elle manque** |

---

## 1. Le piège de facturation, d'abord

C'est le point qui déplace le plus le coût réel d'un standard téléphonique, parce qu'un appel de prise de rendez-vous est fait de silences.

| Fournisseur | Base de facturation du STT streaming | Source |
|---|---|---|
| **AssemblyAI** | **Temps de connexion WebSocket**, pas le volume d'audio. Verbatim : « Streaming Speech-to-Text is billed on the total duration that your WebSocket connection stays open, not on the amount of audio you send. » **[F]** | [docs](https://www.assemblyai.com/docs/speech-to-text/universal-streaming) · 13/09/2026 |
| **AssemblyAI** (rappel tarifaire) | « session duration (connection open-to-close time) is billable, not actual audio duration. Idle connection time counts toward the charge » **[F]** | [pricing](https://www.assemblyai.com/pricing) · 13/09/2026 |
| **Deepgram — Voice Agent API** | « calculated based on websocket connection time » **[F]** | [pricing](https://deepgram.com/pricing) · 13/09/2026 |
| **Deepgram — STT streaming seul** (Nova-3, Flux) | Lignes tarifaires libellées **$/minute d'audio** ; aucune mention de facturation au temps de connexion pour ces SKU **[F]**. Que le silence *envoyé* dans le flux compte comme de l'audio reste **[H]** — à mesurer en L0 sur un appel réel. | [pricing](https://deepgram.com/pricing) · 13/09/2026 |
| **Google STT v2** | « priced based on the amount of audio **successfully processed** […] measured in increments of one second » ; « Each request is rounded up to the nearest increment of 1 seconds » **[F]** | [pricing](https://cloud.google.com/speech-to-text/pricing) · 13/09/2026 |
| **Azure Speech** | Compteur `S1 Speech To Text`, unité **1 Hour** d'audio **[F]** | [Azure Retail Prices API](https://prices.azure.com/api/retail/prices) · 13/09/2026 |
| **ElevenLabs Scribe** | « per hour of audio » **[F]** | [docs STT](https://elevenlabs.io/docs/capabilities/speech-to-text) · 13/09/2026 |
| **Speechmatics, Mistral Voxtral, OpenAI** | **[NV]** — base de facturation du streaming non retrouvée dans une page officielle |

**[R] Conséquence chiffrée.** Un appel de prise de rendez-vous dure typiquement 90–150 s **[H]**, dont **35 % de parole du client** **[H]**. Sur AssemblyAI, facturer la connexion et non la parole multiplie la facture STT par ≈ 2,9 par rapport à une facturation à la parole. À $0,15/h cela reste $0,0025/min de connexion, donc l'écart absolu est faible — **le piège est structurel, pas budgétaire, tant que le tarif horaire est bas**. Il redevient budgétaire si on ouvre la socket avant le décrochage, ou si on la laisse ouverte pendant que le LLM et le TTS parlent.

**Règle d'implémentation qui en découle [H]** : ouvrir la socket STT au décrochage, la fermer à la première des deux conditions (fin d'appel, ou inactivité > `eot_timeout`), et **ne jamais** la garder ouverte pendant la synthèse vocale si le fournisseur facture la connexion.

---

## 2. STT streaming — tableau de synthèse

Prix en USD, tarif public pay-as-you-go, hors remises de volume.

| Fournisseur / modèle | FR streaming | Prix | Base | 8 kHz / µ-law | Endpointing réglable | UE |
|---|---|---|---|---|---|---|
| **Deepgram Flux** `flux-general-multi` | Oui (français listé dans les 10 langues) **[F]** | **$0,0078/min** (multi) · $0,0065/min (EN promo) | audio **[F]** | `mulaw` + 8000 Hz supportés **[F]** | `eot_threshold`, `eager_eot_threshold`, `eot_timeout_ms` **[F]** | **[NV]** |
| **Deepgram Nova-3** streaming | Oui, `fr` et `fr-CA` **[F]** | **$0,0058/min** (multi) · $0,0048/min (mono, promo) | audio **[F]** | `mulaw` + 8000 Hz **[F]** | endpointing classique **[NV]** (params non relus) | **[NV]** |
| **AssemblyAI Universal-Streaming** | **[NV]** pour le français en streaming | **$0,15/h = $0,0025/min** (EN et multilingue, même prix) **[F]** | **connexion [F]** | `pcm_mulaw`, `sample_rate` 8000–96000 **[F]** | `end_of_turn_confidence_threshold` (déf. 0.4), `min_turn_silence`, `max_turn_silence` (déf. 1536 ms) **[F]** | **Oui** : `streaming.eu.assemblyai.com`, « EU region is the same price as US » **[F]** |
| **AssemblyAI universal-3-5-pro realtime** | **[NV]** | $0,45/h = $0,0075/min **[F]** | connexion **[F]** | idem **[F]** | idem **[F]** | idem **[F]** |
| **Google STT v2 / Chirp 3** | Oui, `fr-FR` et `fr-CA` en **GA**, `StreamingRecognize` supporté **[F]** | **$0,016/min** (0–500 k min/mois) ; $0,010 au-delà de 500 k ; $0,008 > 1 M ; $0,004 > 2 M **[F]** | audio, arrondi à la seconde **[F]** | `MULAW` dans l'enum `AudioEncoding`, `sampleRateHertz` 8000–48000 **[F]** | `enable_voice_activity_events`, `voice_activity_timeout` (**> 500 ms et < 60 s**) **[F]** ; sensibilité Chirp 3 `STANDARD` / `SHORT` / `SUPERSHORT` **[F]** | **Oui**, multi-région `eu` en GA **[F]** |
| **Azure Speech** temps réel | `fr-FR` supporté **[F]** | **$1,00/heure = $0,01667/min** (`S1 Speech To Text`, francecentral et westeurope) **[F]** | audio **[F]** | **[NV]** (page format audio non relue) | **[NV]** | **Oui**, `francecentral` au même tarif que `westeurope` **[F]** |
| **Azure Fast Transcription** (batch rapide) | **[NV]** | $0,36/h ; promo $0,10/h **[F]** | audio **[F]** | — | — | westeurope **[F]** |
| **Speechmatics** temps réel | « Global French […] France, Canada, Belgium » ; **support temps réel du français non confirmé explicitement** **[NV]** | page affiche « $0.129 » sans unité claire pour le palier Pro **[F, mais inexploitable]** ; remises de volume > 500 h/mois **[F]** | **[NV]** | `mulaw` supporté ; `pcm_s16le`, `pcm_f32le` **[F]** ; `sample_rate` requis, valeurs non énumérées **[NV]** | `max_delay` **0,7–4 s, défaut 4 s** ; `max_delay_mode` `flexible`/`fixed` ; `end_of_utterance_silence_trigger` **0–2 s, défaut 0 (désactivé)** ; `model` `standard`/`enhanced`/`melia-1` **[F]** | SaaS ou **on-premises** annoncé, détail EU **[NV]** |
| **Mistral Voxtral** | `voxtral-mini-transcribe-realtime-26-02` existe, « optimized for live transcription » **[F]** ; français **[NV]** | **[NV]** — la page tarifs dit seulement « speech models are priced per minute », sans chiffre récupérable (page rendue en JS) | **[NV]** | **[NV]** | **[NV]** | **Mistral = UE**, mais résidence formelle **[NV]** |
| **ElevenLabs Scribe v2 Realtime** | 90+ langues, français « Excellent (≤ 5 % WER) » pour Scribe v2 **[F]** | **$0,39/h = $0,0065/min** (Scribe v2 batch : $0,22/h) **[F]** | heure d'audio **[F]** | **`ulaw_8000` supporté** dans `audio_format` **[F]** | `commit_strategy` `manual`/`vad`, `vad_threshold`, `vad_silence_threshold_secs`, `min_speech_duration_ms`, `min_silence_duration_ms` **[F]** | **[NV]** |
| **OpenAI** `gpt-live-transcribe` / `gpt-transcribe` | `fr` accepté comme code langue **[F]** | `gpt-4o-transcribe` **$0,006/min** estimé ; `gpt-4o-mini-transcribe` **$0,003/min** ; Realtime audio in **$32/1M tokens** **[F]** | tokens / minute selon le modèle **[F]** | doc realtime ne mentionne que **PCM 24 kHz** ; `g711_ulaw` **[NV]** sur cette page | `server_vad` (`threshold`, `prefix_padding_ms`, `silence_duration_ms` — **défauts non publiés sur la page lue [NV]**), `semantic_vad` avec `eagerness` `low`/`medium`/`high`/`auto` (auto = medium) **[F]**, **sans valeur en ms [NV]** | **[NV]** |

### 2.1 Latences publiées

| Fournisseur | Latence publiée | Source |
|---|---|---|
| ElevenLabs Scribe v2 Realtime | **« ~150 ms »** pour les transcriptions partielles **[F]** | [docs STT](https://elevenlabs.io/docs/capabilities/speech-to-text) |
| Deepgram Flux | **[NV]** — aucun chiffre de latence sur `/docs/flux/` ni `/docs/flux/configuration` ; les pages blog `deepgram.com/learn/flux*` et `/product/flux` renvoient **404** au 13/09/2026 |
| AssemblyAI | **[NV]** — aucune latence publiée sur la page de démarrage streaming |
| Google, Azure, Speechmatics, Mistral, OpenAI | **[NV]** — aucune latence de finalisation publiée dans les pages consultées |

**[R] Aucun fournisseur ne publie une latence de finalisation p95.** La cible « ≤ 200 ms p95 » **ne peut donc pas être tranchée sur documentation**. Elle se mesure, et elle se mesure en 8 kHz — pas en 16 kHz de démo.

**Ce que la documentation permet quand même de raisonner [F]** : la latence de finalisation est dominée par le silence exigé avant de déclarer la fin de tour, et ce silence est un paramètre.
- AssemblyAI : `max_turn_silence` par défaut **1536 ms** → **la valeur par défaut est 7,7× au-dessus de la cible**. Le seuil de confiance `end_of_turn_confidence_threshold` (0.4) permet de finaliser plus tôt que ce plancher quand le modèle est confiant.
- Deepgram Flux : `eot_timeout_ms` par défaut **5000 ms**, plage 500–60000 ; `eot_threshold` 0.5–1.0 défaut **0.7** ; `eager_eot_threshold` 0.3–0.9, **non activé par défaut**, déclenche `EagerEndOfTurn` / `TurnResumed` — c'est le mécanisme conçu pour parler avant la certitude et se rétracter si le client reprend.
- Speechmatics : `max_delay` par défaut **4 s**, plancher **0,7 s** → **le plancher documenté est 3,5× la cible**. C'est le seul fournisseur dont la borne basse rend la cible inatteignable par construction **[F]**.
- Google Chirp 3 : `SUPERSHORT` existe explicitement pour « the trade-off between latency and accuracy » **[F]**.

---

## 3. Le 8 kHz : qui l'accepte vraiment

| Fournisseur | µ-law 8 kHz en entrée STT | Détail |
|---|---|---|
| Deepgram (Nova + Flux) | **Oui [F]** | Encodages : `linear16, linear32, flac, alaw, mulaw, amr-nb, amr-wb, opus, ogg-opus, speex, g729`. Flux non conteneurisé : `linear16, linear32, mulaw, alaw, opus, ogg-opus`. |
| AssemblyAI | **Oui [F]** | `encoding` ∈ `pcm_s16le, pcm_mulaw, opus, ogg_opus, aac` ; `sample_rate` 8000–96000, défaut 16000. |
| Google STT v2 | **Oui [F]** | `ExplicitDecodingConfig.encoding` ∈ `LINEAR16, MULAW, ALAW, AMR, AMR_WB, FLAC, MP3, OGG_OPUS, WEBM_OPUS, MP4_AAC, M4A_AAC, MOV_AAC` ; `sampleRateHertz` 8000–48000. |
| ElevenLabs Scribe v2 Realtime | **Oui [F]** | `audio_format` ∈ `pcm_8000, pcm_16000, pcm_22050, pcm_24000, pcm_44100, pcm_48000, ulaw_8000` ; défaut `pcm_16000`. |
| Speechmatics | **Oui [F]** pour `mulaw` ; valeurs de `sample_rate` **[NV]**. |
| Azure, Mistral, OpenAI | **[NV]** |

**[R] Accepter du 8 kHz n'est pas être bon en 8 kHz.** Aucune des pages consultées ne publie de WER français en bande téléphonique. Deepgram conserve un modèle historique `phone_call` côté Google (`Standard¹ models include: default, command_and_search, latest_short, latest_long, **phone_call**, video, chirp` **[F]**) — c'est le seul indice documentaire d'un modèle spécialisé téléphonie, et il est chez Google, pas chez les challengers. C'est une **dette de mesure L0**, cohérente avec la règle projet « aucune décision de pile avant L0 ».

---

## 4. Ce qui décide de la qualité en français : amorçage lexical, formatage, PII

### 4.1 Amorçage lexical (le levier n° 1 pour les noms de prestations et de praticiennes)

| Fournisseur | Mécanisme | Limites chiffrées | Français |
|---|---|---|---|
| **Deepgram** | `keyterm` (Keyterm Prompting) | **500 tokens au total** pour l'ensemble des keyterms ; message d'erreur officiel : « Keyterm limit exceeded. The maximum number of tokens across all keyterms is 500. » Recommandation officielle : « focus on the most important **20-50 terms** ». Pas de poids ni d'intensificateur (contrairement à l'ancien `keywords`). Encodage URL obligatoire (`%20` ou `+`) pour les expressions multi-mots ; virgules/points-virgules/retours ligne interdits comme séparateurs. **[F]** | Nova-3 **et** Flux, mono **et** multilingue **[F]**. **Flux permet de mettre à jour les keyterms en cours de flux** via un message `Configure`, sans reconnexion **[F]** — décisif pour injecter le catalogue du commerçant quand l'appel bascule sur un praticien précis. | Oui (Nova-3 fr, Flux multi) **[F]** |
| **AssemblyAI** | `keyterms_prompt` | **max 100 termes** **[F]**. Modifiable en cours de session via `UpdateConfiguration` (avec `prompt`, `min_turn_silence`, `max_turn_silence`, `end_of_turn_confidence_threshold`, `vad_threshold`, `language_codes`, `agent_context`…) **[F]** | **[NV]** pour le français |
| **Google STT v2** | `PhraseSet` + `CustomClass` + `adaptation` + `transcriptNormalization` | **5000 phrases par requête**, **100 000 caractères au total**, **100 caractères par phrase** **[F]** ; `boost` > 0, « practical maximum limit for boost values is **20** » **[F]** | Support de l'adaptation **par Chirp / Chirp 2 / Chirp 3 non confirmé** dans la page lue **[NV]** — **[R] c'est précisément le modèle qu'on voudrait**. Jetons de classe pré-construits type `$ADDRESSNUM` : « availability varies by model and language » **[F]**, donc **[NV]** en français. |
| **Azure Speech** | Phrase List (runtime, endpoint) | « a phrase list shouldn't have more than **2,000 phrases**. Note that a longer phrase list will impact quality and latency » **[F]** ; poids réglable **0.0 → 2.0**, défaut **1.0**, 0.0 désactive **[F]** ; caractères autorisés : lettres et chiffres **spécifiques à la locale**, espaces, et `+ - $ : ( ) { } _ . ? @ \ ' & # % ^ * \` < > ; /` — les autres sont supprimés **[F]**. Fonctionne en temps réel, **pas** en batch **[F]**. | Locales supportées **[NV]** (la note renvoie à la table de language support sans l'expliciter). |
| **OpenAI** | `prompt` (contexte libre) + `keywords` (« hints for product names, acronyms, and other literal terms ») **[F]** | limites chiffrées **[NV]** | `fr` accepté **[F]** |
| **ElevenLabs Scribe v2 Realtime** | `keyterms` : « List of keyterms the model is biased towards » **[F]** | limites chiffrées **[NV]** | 90+ langues **[F]** |
| **Speechmatics, Mistral** | **[NV]** |

**Lecture pour le projet.** Le catalogue d'un salon de beauté (prestations + prénoms des praticiennes) tient largement sous les 20–50 termes recommandés par Deepgram et sous les 100 d'AssemblyAI **[H]**. Les 5000 phrases de Google sont surdimensionnées et **inutilisables si Chirp 3 ne supporte pas l'adaptation** — à vérifier avant de compter dessus.

### 4.2 Formatage des nombres et ponctuation

| Fournisseur | Paramètre | Français |
|---|---|---|
| **Deepgram** | `numerals=true` — convertit « nine hundred » → « 900 » **[F]** | **Français explicitement supporté, `fr` et `fr-CA`** **[F]**. Modèles : Nova (pré-enregistré et streaming), Flux EN et Flux multi **[F]**. Restriction connue : « Numeral formatting is not currently supported for Hindi or Japanese » — **le français n'est pas dans la liste d'exclusion** **[F]**. Activable **en cours de flux** via `Configure` pour tout sauf Flux **[F]**. |
| **Deepgram** | `smart_format=true` — ponctuation, paragraphes, dates, heures, devises, numéros de téléphone, e-mails, URL **[F]** | **[R] Dégradé hors anglais.** Verbatim : « Smart Format has the **broadest support for English-language models** » et « On non-English models, Smart Format will apply all available formatters for that language. This will always include **punctuation and paragraphs**, with **numerals support also available for select languages** » **[F]**. Autrement dit : en français on obtient ponctuation + paragraphes, et les numéraux **parce que `numerals` couvre le français**, mais **le formateur de numéro de téléphone n'est pas garanti en français** **[H]** — la page ne le dit ni dans un sens ni dans l'autre **[NV]**. |
| **AssemblyAI** | `format_turns` (défaut `false`) **[F]** | comportement en français **[NV]** |
| **Google STT v2** | `transcriptNormalization` (règles de remplacement automatique), ponctuation automatique, ponctuation dictée **[F]** | disponibilité par langue **[NV]** |
| **Azure** | formatage inverse du texte (ITN) intégré **[NV]** pour les détails |

### 4.3 Anonymisation PII

**[R] Point dur, et il est net.** Deepgram : « Entity redaction […] is available for **English only**, regardless of model » ; « entity redaction — names, addresses, PHI, and other `pii`/`phi` entities — is applied for **English only**, even when you request `true` » ; en français **seule la rédaction de nombres fonctionne** (`numbers`, `aggressive_numbers`, `true`) **[F]**.

Conséquence pour un agent de prise de rendez-vous qui manipule des noms et des numéros de mobile : **l'anonymisation des noms côté Deepgram n'existe pas en français**. Si le RGPD impose de ne pas persister les noms en clair dans les transcriptions, **la rédaction doit être faite par nous**, en aval, sur notre infrastructure — ce qui est de toute façon cohérent avec le rapatriement auto-hébergé prévu **[H]**. Les autres fournisseurs : **[NV]**.

---

## 5. Le piège des nombres français — « quatre-vingt-dix-huit »

C'est le point où je dois être le plus honnête sur ce que la documentation dit et ne dit pas.

**Ce qui est documenté [F].**
1. Deepgram `numerals` **supporte explicitement le français** (`fr`, `fr-CA`) et la seule exclusion nommée est hindi/japonais. La fonction est décrite génériquement : « converts written numbers to numerical format », avec des exemples **anglais uniquement** (« nine hundred » → « 900 »).
2. Deepgram `smart_format` **admet lui-même** que hors anglais on perd des formateurs.
3. Google propose `transcriptNormalization` (règles de remplacement) et les jetons de classe type `$ADDRESSNUM`, dont la disponibilité « varies by model and language ».
4. Azure Phrase List autorise les **chiffres et lettres spécifiques à la locale**.

**Ce qui n'est documenté nulle part [NV].**
- **Aucun fournisseur ne documente le comportement sur les composés français** : « quatre-vingt-dix-huit » → 98, « soixante-quinze » → 75, « quatre-vingts » → 80, ni le cas belge/suisse « nonante-huit » / « septante-cinq ».
- **Aucun fournisseur ne documente la capture d'entité structurée en français** (date, heure, numéro de téléphone, durée) sous forme d'objet typé. AssemblyAI mentionne « entity detection » pour Scribe/Universal **[F, ElevenLabs Scribe v2 : « entity detection »]**, sans grille de langues.
- **Aucun retour officiel** (post-mortem, note de version, benchmark éditeur) sur les nombres français n'a pu être retrouvé — le budget de recherche web étant épuisé, je n'ai pas pu balayer les changelogs.

**[R] Le risque, formulé précisément.** Un numéro de mobile français dicté à l'oral est une suite de **cinq nombres à deux chiffres** (« zéro six, quatre-vingt-douze, quatre-vingt-dix-huit, soixante-quinze, zéro trois »). Il combine les deux pièges d'un coup : composés à trait d'union **et** groupement par paires. Le mode d'échec attendu **[H]** n'est pas « le modèle entend mal » — c'est « le modèle transcrit correctement en lettres et le normaliseur produit `4 20 12` ou `80 18` ». C'est un bug de **post-traitement**, pas d'acoustique.

**Décision recommandée [H], et elle est structurante.**
1. **Ne pas déléguer la normalisation des nombres au STT** pour les champs critiques (numéro de mobile, heure du rendez-vous, date). Demander `numerals=false` ou ignorer le champ formaté, et **récupérer le texte en lettres**.
2. **Normaliser nous-mêmes**, avec une grammaire française déterministe couvrant : 70/80/90 composés, variantes belges/suisses, « et un » (« vingt-et-un »), élision (« quatre-vingt » vs « quatre-vingts »), et les paires téléphoniques. Un parseur français des nombres écrits est un objet borné, testable, et **il n'a pas de coût par appel**.
3. **Confirmer à l'oral, chiffre par chiffre, avant d'écrire** — ce que la règle projet impose déjà (`read-after-write`, métrique *taux de confirmation orpheline*, cible 0). Le parseur alimente la confirmation ; la confirmation rattrape le parseur.
4. Amorcer le STT avec les **keyterms des dizaines composées** est inutile (ce sont des mots courants), mais amorcer avec les **prénoms des praticiennes et les noms de prestations** l'est beaucoup **[H]**.

---

## 6. TTS streaming — tableau de synthèse

| Fournisseur / modèle | Voix françaises réellement disponibles | TTFB publié | Prix | µ-law 8 kHz | Licence commerciale du free tier |
|---|---|---|---|---|---|
| **ElevenLabs Flash v2.5** `eleven_flash_v2_5` | 32 langues, français (France **et** Canada) hérité de Multilingual v2 **[F]** ; **noms de voix FR [NV]** | **« ~75 ms† »** **[F]** (le † renvoie à une note de conditions non lue **[NV]**) | **$0,05 / 1 000 caractères** (Flash/Turbo) ; $0,10 / 1 000 car. pour v2/v3 **[F]** | **Oui**, `ulaw_8000` dans la liste `output_format` **[F]** | **[NV]** — la page `pricing/api` ne documente pas les droits du palier gratuit |
| **ElevenLabs v3 / Multilingual v2** | v3 : 70+ langues ; Multilingual v2 : 29 langues dont « French (France, Canada) » **[F]** | **[NV]** | $0,10 / 1 000 car. **[F]** | Oui **[F]** | **[NV]** |
| **Cartesia Sonic 3.6** | « French (`fr`) » parmi 44 langues ; accepte `fr-FR` / `fr-CA` et « pick the closest accent the voice supports » **[F]** ; **noms de voix FR [NV]** | **[NV]** — aucun chiffre de TTFB dans les pages accessibles ; `docs.cartesia.ai` passe derrière un login pour plusieurs pages **[F, constaté : redirection 307 vers `play.cartesia.ai/docs-auth-login`]** | Crédits : Free 20 k/mois (~27 min TTS), Pro 100 k (~133 min), Startup 1,25 M (~1 667 min), Scale 8 M (~10 667 min) **[F]** ; **conversion crédits→caractères et prix au crédit [NV]** ; « Voice Agent » à **$0,06/min** tous paliers payants, + $0,014/min si numéro fourni par Cartesia **[F]** | **Oui** : `pcm_mulaw` / `pcm_alaw` et 8000 Hz dans les taux supportés **[F]** | **Non** : « The Free plan does not include commercial use. The Pro plan and higher include a commercial use license. » **[F]** |
| **Rime Mist v3** | « Supports English, French, German, and Spanish » **[F]** | **« Typical time to first byte is well below 100 ms »** **[F]** | **$0,03 / 1 000 caractères ≈ $0,03/minute** (palier Starter) **[F]** | **[NV]** | Commercial autorisé sur tous les paliers ; ~800 min incluses, jusqu'à 3 000 min gratuites à l'ouverture de compte **[F]** |
| **Rime Coda** | 9 langues dont le français **[F]** | **« Sub-100 ms model latency on the GPU engine »** + 25–50 ms réseau sur l'API cloud **[F]** | **$0,05 / 1 000 caractères ≈ $0,05/minute** **[F]** | **[NV]** | idem **[F]** |
| **Rime Mist v2** | EN/FR/DE/ES **[F]** | 175 ms médian sur A10G, phrases de 40–50 caractères **[F]** | non listé sur la page tarifs **[F]** | **[NV]** | — |
| **Azure Neural (fr-FR)** | **Le catalogue le plus explicite [F]** : `fr-FR-DeniseNeural`, `fr-FR-HenriNeural` (styles cheerful/excited/sad/whispering) ; HD : `fr-FR-Vivienne:DragonHDLatestNeural`, `fr-FR-Remy:DragonHDLatestNeural` ; MAI-Voice-2 : `fr-FR-Marc:MAI-Voice-2(-Flash)`, `fr-FR-Soleil:MAI-Voice-2(-Flash)` (18 styles émotionnels) ; multilingues : `fr-FR-VivienneMultilingualNeural`, `fr-FR-RemyMultilingualNeural`, `fr-FR-LucienMultilingualNeural` ; + Alain, Brigitte, Celeste, Claude, Coralie, Eloise, Jacqueline, Jerome, Josephine, Maurice, Yves, Yvette | **[NV]** | **$15 / 1 M car.** (`S1 Neural Text To Speech Characters`, westeurope & francecentral) ; **HD $22 / 1 M car.** ; voix standard legacy $4 / 1 M ; custom neural temps réel $24 / 1 M **[F]** | **[NV]** | Palier F0 : **0,5 M caractères gratuits/mois** **[F]** ; droits commerciaux **[NV]** |
| **Google Chirp 3: HD** | `fr-FR` supporté **[F]** ; **noms de voix FR non listés dans la page** **[NV]** | **[NV]** | **$30 / 1 M caractères** ($0,00003/car.), **1 M car. gratuits/mois** **[F]** ; Neural2 $16/1M ; WaveNet et Standard $4/1M (4 M gratuits) ; Studio $160/1M ; Instant Custom Voice $60/1M **[F]** | **[NV]** | 1 M car./mois gratuits, pas d'attribution documentée **[F pour le quota, NV pour la licence]** |
| **Google Gemini TTS** | Gemini 2.5 Flash TTS : in $0,50/1M tokens texte, out $10/1M tokens audio ; Gemini 3.1 Flash TTS (Preview) et 2.5 Pro TTS : in $1,00 / out $20,00 par 1M ; « Audio tokens correspond to **25 tokens per second of audio** » **[F]** → **$0,50/heure d'audio = $0,0083/min** pour 2.5 Flash **[calcul, hypothèse explicite : 25 tok/s × 3600 s × $10/1M]** | **[NV]** | voir ci-contre | **[NV]** | pas de palier gratuit (« Not available ») **[F]** |
| **Deepgram Aura-2** | **Deux voix françaises nommées [F]** : `aura-2-agathe-fr` (féminine — « Charismatic, Cheerful, Enthusiastic, Friendly, Natural ») et `aura-2-hector-fr` (masculine — « Confident, Empathetic, Expressive, Friendly, Patient »), toutes deux positionnées « customer service ». Langues Aura : en, es, de, **fr**, nl, it, ja **[F]** | **Pas de TTFB publié [F]** : « You will notice variation in latency; these numbers are an illustration of general trends and concepts, not a fixed result ». Exemple illustratif d'un run : total 745 ms, **TTFB 616 ms**, synthèse 406 ms ; modèle linéaire ≈ **600 ms de base + ~40 ms / 100 caractères** **[F]** | **Aura-2 $0,030 / 1 000 car.** ; Aura-1 $0,015 / 1 000 car. ; Flux TTS $0,045 / 1 000 car. (gratuit jusqu'au 14/09) **[F]** | **Oui** : REST — `mulaw` 8000 (défaut) et 16000 ; WebSocket — `linear16`, `mulaw`, `alaw` uniquement **[F]** | **[NV]** |
| **OpenAI** `gpt-4o-mini-tts` | **[NV]** pour les voix françaises | **[NV]** | $12 / 1M tokens audio en sortie + $0,60 / 1M tokens texte ; `tts-1` **$15 / 1M caractères** **[F]** | **[NV]** | **[NV]** |
| **LMNT** | **Service arrêté [F]** : la page officielle affiche « Our speech generation journey has come to an end. » — **à retirer de toute comparaison** | — | — | — | — |

**[R] L'écart TTFB est le plus grand écart de tout ce rapport.** Rime publie « bien en dessous de 100 ms » et ElevenLabs Flash « ~75 ms » ; Deepgram publie un exemple à **616 ms** et refuse explicitement d'en faire une garantie. **Si la cible TTS TTFB ≤ 150 ms p50 est ferme, Aura-2 est éliminé sur ses propres chiffres**, malgré ses deux voix françaises nommées et son prix. C'est le fait le plus décisif de la section TTS.

---

## 7. Forcer la lecture d'un numéro de téléphone par groupes de deux chiffres

C'est la fonction produit qui rend un standard crédible : « je vous rappelle au zéro six · quatre-vingt-douze · quatre-vingt-dix-huit · soixante-quinze · zéro trois ». Voici ce que chaque fournisseur permet **vraiment**.

| Fournisseur | Mécanisme documenté | Verdict |
|---|---|---|
| **Azure Neural** | **SSML `say-as` complet [F].** `interpret-as="number_digit"` → « `<say-as interpret-as="number_digit">123456789</say-as>` » lu « 1 2 3 4 5 6 7 8 9 ». `interpret-as="alphanumeric" format="spell"` → « A B C ⟨pause⟩ D E F », **et le tiret force la pause** : « `AB-CD-EF` » lu « A B ⟨pause⟩ C D ⟨pause⟩ E F ». `interpret-as="telephone"` existe aussi. **Note officielle décisive** : « The `characters` and `spell-out` values […] are supported for **all** text to speech locales. Other `interpret-as` attribute values are supported for all locales of the following languages: Arabic, Catalan, Chinese, Danish, Dutch, English, **French**, Finnish, German, Hindi, Italian, Japanese, Korean, Norwegian, Polish, Portuguese, Russian, Spanish, and Swedish. » **[F]** — **le français est explicitement couvert**. En complément : lexique personnalisé PLS (≤ 100 Ko, cache 15 min), alphabet `sapi` défini pour `fr-FR`, `fr-CA`, `fr-BE`, `fr-CH` **[F]**. | **Seul fournisseur avec une solution native, documentée, et explicitement valide en français.** |
| **Google Chirp 3: HD** | SSML supporté (`say-as`, `phoneme`, `sub`, `break`, `prosody`…) **[F]** — **mais** : « **SSML tags are not currently supported for streaming requests** » **[F]**. | **[R] Contradiction frontale avec notre besoin.** On veut du streaming *et* du `say-as`. Chez Google il faut choisir. Repli : synthèse non-streaming pour la seule phrase du numéro **[H]**, au prix d'un TTFB dégradé sur la phrase la plus sensible. |
| **ElevenLabs** | **Pas de `say-as` [F].** Normalisation automatique activée par défaut « for all TTS models », pilotable par `apply_text_normalization` ∈ **`auto` / `on` / `off`** **[F]**. La doc recommande explicitement de **pré-normaliser en amont** : « 555-555-5555 » → « five five five, five five five, five five five five », par regex ou par prompt LLM **[F]**. Prononciation fine : IPA entre slashes (v3), balises `phoneme` SSML (v2), `<lexeme>`/alias. **`<break>` non supporté par v3** **[F]**. | **Faisable, mais c'est nous qui écrivons le texte parlé.** Avantage caché : cela nous rend **portables**, et donc cohérents avec l'objectif anti-verrouillage. |
| **Deepgram Aura-2** | **Pas de SSML [F].** Recommandation officielle : insérer des **points tous les 3–4 caractères** — exemple verbatim « Your phone number is 203.912.3456. » ; et pour les nombres, écrire « 1235, or twelve hundred and thirty-five » **[F]**. | Bricolage typographique, **documenté en anglais uniquement** ; transposition au français **[NV]**. |
| **Cartesia Sonic 3.6** | Pas de SSML ni de dictionnaire de prononciation dans les pages accessibles **[F/NV]** ; la doc affirme que Sonic 3.6 « voices confirmation codes and heteronyms correctly **without preprocessing** » **[F]**. | **[R] Promesse non vérifiable** : aucune page publique ne montre le comportement sur un numéro français, et la page « custom pronunciations » exige un login. À tester, pas à croire. |
| **Rime** | **[NV]** — aucune information sur le contrôle de prononciation dans les pages consultées. |
| **OpenAI** | **[NV]** — `gpt-4o-mini-tts` se pilote par instructions en langage naturel, mais aucune garantie documentée trouvée. |

**Conclusion opérationnelle [H].** Quel que soit le TTS retenu, **le pipeline doit produire lui-même la chaîne parlée du numéro** (« zéro six, quatre-vingt-douze, … ») dans le texte envoyé au TTS, et n'utiliser `say-as` que comme ceinture de sécurité quand le fournisseur le permet (Azure). C'est la seule stratégie qui survit à un changement de fournisseur — et un changement de fournisseur est planifié.

---

## 8. Trois assemblages recommandés

### Hypothèses de calcul (communes, explicites)

| Hypothèse | Valeur | Statut |
|---|---|---|
| H1 — Débit de parole du TTS en français | **14 caractères/seconde** | **[H]** — à mesurer ; aucune source officielle ne le publie |
| H2 — Part de l'appel où l'agent parle | **35 %** | **[H]** |
| H3 — Caractères TTS par minute d'appel | 0,35 × 60 × 14 = **294 car./min**, arrondi à **300** | **[H]** dérivé de H1·H2 |
| H4 — Socket STT ouverte 100 % de la durée d'appel | oui | **[H]** conservateur |
| H5 — Tarifs | pay-as-you-go public, hors remise de volume, USD, 13/09/2026 | **[F]** |
| H6 — Coût LLM, téléphonie, VPS | **exclu** de ces chiffres | — |

### Assemblage A — Qualité maximale, UE, contrôle total de la prononciation

**Azure Speech STT temps réel (`francecentral`) + Azure Neural HD `fr-FR-Vivienne:DragonHDLatestNeural`**

| Poste | Calcul | $/min d'appel |
|---|---|---|
| STT | $1,00/h ÷ 60 | **0,01667** |
| TTS HD | 300 car. × $22 / 1 000 000 | **0,00660** |
| **Total** | | **$0,0233 / min** |

Variante voix Neural standard (`fr-FR-DeniseNeural`, $15/1M) : 300 × 15/1e6 = $0,0045 → **$0,0212/min**.

**Pourquoi.** C'est le seul assemblage qui réunit : hébergement **France Central au même tarif que West Europe** **[F]**, `say-as` **explicitement valide en français** **[F]**, le catalogue de voix `fr-FR` le plus riche et le plus nommé de tout le marché **[F]**, phrase list à 2 000 entrées avec poids 0–2 **[F]**, et 0,5 M caractères gratuits/mois **[F]**.
**Ce qui manque [NV]** : le TTFB Azure n'est publié nulle part, et le support 8 kHz µ-law en entrée STT n'a pas été confirmé. **Deux mesures L0 avant de valider.**
**[R]** Verrouillage moyen : le SSML `say-as` est un standard W3C, mais les extensions `mstts:` et les noms de voix ne le sont pas.

### Assemblage B — Équilibre (recommandé comme défaut)

**Deepgram Nova-3 multilingue (streaming, 8 kHz µ-law) + Rime Mist v3**

| Poste | Calcul | $/min d'appel |
|---|---|---|
| STT Nova-3 multi | $0,0058/min | **0,00580** |
| TTS Rime Mist v3 | 300 car. × $0,03 / 1 000 | **0,00900** |
| **Total** | | **$0,0148 / min** |

**Pourquoi.** Français confirmé des deux côtés **[F]** ; µ-law 8 kHz confirmé côté STT **[F]** ; `numerals` explicitement supporté en `fr`/`fr-CA` **[F]** ; keyterm prompting avec mise à jour **en cours de flux** si on passe à Flux **[F]** ; **le seul TTFB publié sous 100 ms avec du français, hors ElevenLabs** **[F]** ; usage commercial autorisé dès le palier gratuit de Rime **[F]**.
**Variante latence** : remplacer Nova-3 par **Flux multilingue** ($0,0078/min → total **$0,0168/min**) pour obtenir `eager_eot_threshold` et les événements `EagerEndOfTurn`/`TurnResumed` **[F]**, qui sont le mécanisme conçu exactement pour un agent qui doit commencer à répondre avant d'être certain que le client a fini.
**Ce qui manque [NV]** : format audio de sortie de Rime (µ-law 8 kHz ?), résidence UE chez Deepgram et chez Rime, contrôle de prononciation chez Rime.
**[R]** PII : pas de rédaction d'entités en français chez Deepgram **[F]** → à faire chez nous.

### Assemblage C — Coût minimal

**AssemblyAI Universal-Streaming multilingue (région EU) + Azure Neural `fr-FR-DeniseNeural`**

| Poste | Calcul | $/min d'appel |
|---|---|---|
| STT | $0,15/h ÷ 60 | **0,00250** |
| TTS | 300 car. × $15 / 1 000 000 | **0,00450** |
| **Total** | | **$0,0070 / min** |

**Pourquoi.** Le STT le moins cher du panel, **en région EU au même prix qu'aux États-Unis** **[F]**, µ-law 8 kHz supporté **[F]**, endpointing très finement réglable et **modifiable en cours de session** **[F]** ; le TTS le moins cher parmi ceux qui ont des voix françaises nommées et `say-as` valide en français **[F]**.
**[R] Le blocage.** **Le support du français par Universal-Streaming n'a pas pu être confirmé sur une page officielle** **[NV]** — la page « supported languages » ne couvre que le pré-enregistré, et les URL de la doc streaming multilingue renvoient 404. **Cet assemblage est conditionné à cette vérification.** S'il tombe, le repli coût minimal devient **Deepgram Nova-3 multi + Azure Neural = $0,0058 + $0,0045 = $0,0103/min**, avec le français confirmé des deux côtés.
**[R] Facturation à la connexion** **[F]** : à $0,0025/min l'impact absolu est faible, mais la discipline de fermeture de socket reste obligatoire.

### Comparatif

| | A — Qualité max | B — Équilibre | C — Coût min | C' — Repli coût min |
|---|---|---|---|---|
| $/min d'appel | **0,0233** | **0,0148** | **0,0070** | **0,0103** |
| $ pour un appel de 2 min | 0,047 | 0,030 | 0,014 | 0,021 |
| $ pour 1 000 appels de 2 min | **46,60** | **29,60** | **14,00** | **20,60** |
| Français confirmé STT + TTS | Oui / Oui | Oui / Oui | **[NV]** / Oui | Oui / Oui |
| UE documentée | **Oui (France)** | [NV] | Oui (EU) | [NV] / Oui |
| `say-as` FR natif | **Oui** | Non | Oui (côté TTS) | Oui (côté TTS) |
| TTFB TTS publié | [NV] | **< 100 ms** | [NV] | [NV] |

---

## 9. Ce que ce rapport ne permet pas de décider

Trois cibles du cahier des charges **ne peuvent pas être tranchées sur documentation** :

1. **STT finalisation ≤ 200 ms p95** — aucun fournisseur ne publie de p95. Les seuls chiffres exploitables sont des **défauts de silence** (AssemblyAI 1536 ms, Flux 5000 ms, Speechmatics 4000 ms avec plancher 700 ms). Seul Speechmatics est **éliminable sur documentation** : son plancher `max_delay` de 0,7 s est 3,5× la cible **[F]**.
2. **WER français en 8 kHz** — inexistant chez tous. Confirme la dette L0 déjà inscrite au `CLAUDE.md` du projet.
3. **TTS TTFB ≤ 150 ms p50** — seuls Rime (« bien sous 100 ms ») et ElevenLabs Flash (« ~75 ms ») publient un chiffre ; Deepgram publie **616 ms** en exemple et se dédouane explicitement **[F]**.

---

## 10. Dettes de recherche déclarées

| # | Ce qui manque | Pourquoi |
|---|---|---|
| D1 | Support **français** d'AssemblyAI Universal-Streaming | pages `/universal-streaming/multilingual` et `/message-types` → **404** ; la page langues ne couvre que le pré-enregistré |
| D2 | Tarifs **Mistral Voxtral** (mini-transcribe, realtime, TTS) | `mistral.ai/pricing` rendu en JS, aucun chiffre extractible ; `docs.mistral.ai/.../pricing` → 404 |
| D3 | **Latence Flux** | `deepgram.com/learn/flux*`, `/learn/introducing-flux`, `/product/flux`, `/docs/flux/overview` → **404** au 13/09/2026 |
| D4 | **Tarif horaire Speechmatics** exploitable | page tarifs affiche « $0.129 » sans unité ; `docs.speechmatics.com/introduction/pricing` → 404 |
| D5 | **Cartesia** : conversion crédits→caractères, TTFB, contrôle de prononciation, noms de voix FR | plusieurs pages `docs.cartesia.ai` redirigent vers un **login** (`play.cartesia.ai/docs-auth-login`) |
| D6 | **TTFB Azure TTS** et **formats audio d'entrée du STT Azure** (µ-law 8 kHz) | non couverts par les pages lues |
| D7 | **Noms de voix françaises** ElevenLabs, Google Chirp 3 HD, Cartesia, Rime, OpenAI | les catalogues de voix nécessitent l'API ou une page non retrouvée |
| D8 | **Locales supportées par la Phrase List Azure** | la doc renvoie à une table de language support non explicite sur ce point |
| D9 | **Adaptation de contexte sur Chirp 3** (Google) | la page `adaptation-model` ne dit pas quels modèles la supportent — **et c'est le point qui décide de l'usage de Chirp 3 chez nous** |
| D10 | **Défauts en ms du `server_vad` OpenAI** et timings du `semantic_vad` | la page VAD décrit les paramètres sans publier leurs valeurs |
| D11 | Le budget **WebSearch de la session (200/200) a été épuisé** | tout le reste a été fait en WebFetch direct ; une passe de recherche ciblée lèverait D1–D5 rapidement |

---

## 11. Sources (toutes consultées le 2026-09-13)

**STT**
- Deepgram — [tarifs](https://deepgram.com/pricing) · [Flux](https://developers.deepgram.com/docs/flux/) · [Flux configuration](https://developers.deepgram.com/docs/flux/configuration) · [modèles et langues](https://developers.deepgram.com/docs/models-languages-overview) · [encodages](https://developers.deepgram.com/docs/encoding) · [keyterm prompting](https://developers.deepgram.com/docs/keyterm) · [smart_format](https://developers.deepgram.com/docs/smart-format) · [numerals](https://developers.deepgram.com/docs/numerals) · [redaction](https://developers.deepgram.com/docs/redaction)
- AssemblyAI — [Universal Streaming](https://www.assemblyai.com/docs/speech-to-text/universal-streaming) · [API streaming v3](https://www.assemblyai.com/docs/api-reference/streaming-api/streaming-api) · [tarifs](https://www.assemblyai.com/pricing)
- Google Cloud — [tarifs STT](https://cloud.google.com/speech-to-text/pricing) · [Chirp 3](https://docs.cloud.google.com/speech-to-text/v2/docs/chirp_3-model) · [model adaptation](https://docs.cloud.google.com/speech-to-text/v2/docs/adaptation-model) · [quotas](https://docs.cloud.google.com/speech-to-text/quotas) · [recognizers / decoding](https://docs.cloud.google.com/speech-to-text/v2/docs/reference/rest/v2/projects.locations.recognizers) · [voice activity events](https://docs.cloud.google.com/speech-to-text/v2/docs/voice-activity-events)
- Microsoft Azure — [Azure Retail Prices API](https://prices.azure.com/api/retail/prices) (compteurs `S1 Speech To Text`, `S1 Neural Text To Speech Characters`, `Neural HD Text to Speech Characters`, `Fast Transcription`, régions `francecentral` / `westeurope`) · [phrase list](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/improve-accuracy-phrase-list) · [language support TTS/STT](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts) · [tarifs (valeurs masquées)](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/speech-services/)
- Speechmatics — [référence API temps réel](https://docs.speechmatics.com/rt-api-ref) · [langues](https://docs.speechmatics.com/introduction/supported-languages) · [tarifs](https://www.speechmatics.com/pricing)
- Mistral — [vue d'ensemble des modèles](https://docs.mistral.ai/getting-started/models/models_overview/) · [tarifs](https://mistral.ai/pricing)
- ElevenLabs — [STT](https://elevenlabs.io/docs/capabilities/speech-to-text) · [API STT realtime](https://elevenlabs.io/docs/api-reference/speech-to-text/v-1-speech-to-text-realtime) · [modèles](https://elevenlabs.io/docs/models) · [tarifs API](https://elevenlabs.io/pricing/api)
- OpenAI — [tarifs](https://developers.openai.com/api/docs/pricing) · [realtime transcription](https://developers.openai.com/api/docs/guides/realtime-transcription) · [realtime VAD](https://developers.openai.com/api/docs/guides/realtime-vad)

**TTS**
- ElevenLabs — [TTS](https://elevenlabs.io/docs/capabilities/text-to-speech) · [convert (paramètres)](https://elevenlabs.io/docs/api-reference/text-to-speech/convert) · [normalisation](https://elevenlabs.io/docs/best-practices/prompting/normalization)
- Cartesia — [API TTS](https://docs.cartesia.ai/api-reference/tts/tts) · [modèles TTS](https://docs.cartesia.ai/build-with-cartesia/models/tts) · [tarifs](https://cartesia.ai/pricing) · [tarifs docs](https://docs.cartesia.ai/pricing)
- Rime — [modèles](https://docs.rime.ai/api-reference/models) · [tarifs](https://rime.ai/pricing)
- Azure — [SSML prononciation / say-as](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-synthesis-markup-pronunciation) · [language support](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts)
- Google — [Chirp 3 HD](https://docs.cloud.google.com/text-to-speech/docs/chirp3-hd) · [tarifs TTS](https://cloud.google.com/text-to-speech/pricing)
- Deepgram — [modèles TTS et voix](https://developers.deepgram.com/docs/tts-models) · [formats de sortie](https://developers.deepgram.com/docs/tts-media-output-settings) · [prompting TTS](https://developers.deepgram.com/docs/text-to-speech-prompting) · [latence TTS](https://developers.deepgram.com/docs/text-to-speech-latency)
- LMNT — [documentation](https://docs.lmnt.com/api-reference/speech/synthesize-speech-bytes) (**service arrêté**)
