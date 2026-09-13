# R1 — Briques open source pour agents vocaux téléphoniques
## État de l'art au 13 septembre 2026

**Date de consultation de toutes les sources : 2026-09-13.**

**Contraintes client retenues pour l'évaluation** : VPS modestes (1–2 Go RAM, pas de GPU), budget ~0, préférence forte auto-hébergement, licence permissive exigée (usage commercial), **français langue principale des appelants**.

### Convention de fiabilité

| Marque | Signification |
|---|---|
| ✅ **Fait vérifié** | Confirmé sur source officielle (API GitHub, flux `.atom`, fichier `LICENSE` brut, model card HuggingFace, doc éditeur, papier arXiv). URL en §9. |
| 🔶 **Hypothèse** | Déduction argumentée à partir de faits vérifiés, explicitement signalée. |
| ⚠️ **Non vérifié** | Information trouvée mais non confirmable sur source officielle, ou source inaccessible. **Aucun chiffre non vérifié n'a été inventé ni extrapolé.** |

### Limites méthodologiques de cette recherche (à lire)

- L'**API GitHub non authentifiée** a été rate-limitée (60 req/h) en cours de session. Bascule sur les flux `releases.atom` / `commits.atom` et `git ls-remote --tags`, qui donnent des dates fiables mais pas les licences SPDX.
- Le **budget WebSearch de la session a été épuisé**. Les vérifications ultérieures se sont faites par récupération directe des pages et fichiers bruts.
- **Aucun benchmark n'a été exécuté** dans le cadre de cette recherche. Tous les chiffres de latence/WER proviennent de sources tierces citées, mesurées sur du matériel qui n'est pas le vôtre.
- ⚠️ **Trou de vérification transversal et important** : tous les WER cités sont mesurés sur de l'audio **16 kHz large bande** (FLEURS, MLS, CommonVoice). L'audio téléphonique est en **8 kHz bande étroite**, ce qui dégrade systématiquement ces chiffres. **Aucune source consultée ne publie de WER français en bande téléphonique.** C'est la première mesure à faire vous-même.

---

## 1. Frameworks d'orchestration d'agents vocaux

### 1.1 Tableau comparatif

| Projet | Licence code | Langage | Dernière release | Dernier push | ★ | Architecture | Téléphonie/SIP | Barge-in | Statut |
|---|---|---|---|---|---|---|---|---|---|
| **LiveKit Agents** | **Apache-2.0** ✅ | Python (+ Node `agents-js`) | **`livekit-agents@1.8.1`, 2026-09-10** ✅ | **2026-09-13** ✅ | 14 169 ✅ | Cascade STT→LLM→TTS **et** speech-to-speech (OpenAI Realtime, Gemini Live) ✅ | ✅ natif via `livekit/sip` (Apache-2.0, push 2026-09-11) | ✅ (VAD + turn detector) | **Le plus mature, très actif** |
| **Pipecat** (Daily) | **BSD-2-Clause** ✅ | Python | **`v1.10.0`, 2026-09-12** ✅ | **2026-09-13** ✅ | 15 494 ✅ | Pipeline de frames, cascade + realtime ✅ | ✅ via exemples Twilio/Telnyx/Plivo/Exotel/Daily PSTN-SIP (`pipecat-examples`, BSD-2) | ✅ (Silero VAD + Smart Turn intégrés) | **Le plus ouvert sur le local, très actif** |
| **Jambonz** | **MIT** sur les repos v10/0.9.x ✅ — ⚠️ **clé de licence commerciale requise pour auto-héberger v11+** | JS/Node | v11.1.4 (août 2026) ⚠️ | feature-server **2026-09-13** ✅ | 97 ✅ | Voice gateway CPaaS (webhooks + WebSocket) | ✅ c'est sa raison d'être | ✅ | **Actif mais licence durcie en 2026** |
| **Vocode** (`vocode-core`) | MIT ✅ | Python | **`v0.1.113`, 2024-06-18** ✅ | **2024-11-15** ✅ | 3 795 ✅ | Cascade | ✅ (Twilio/Vonage) | ✅ | ⛔ **MORT — 22 mois sans commit.** Ne pas bâtir dessus |
| **Ultravox** (`fixie-ai/ultravox`) | MIT ✅ | Python | **`v0.6`, 2025-08-18** ✅ | **2025-12-12** ✅ | — | Modèle audio→**texte** (pas un framework d'orchestration) | non | — | ⚠️ **Stagnant (9 mois)** |
| **Rasa Open Source** | Apache-2.0 ✅ | Python | 3.6.21 (2025-01) ⚠️ | **2025-12-18** ✅ | — | NLU/dialogue textuel, pas de pipeline audio temps réel | non | non | ⛔ **« currently in maintenance mode » — écrit noir sur blanc dans le README** ✅ |
| **TEN Framework** (Agora) | ⚠️ **« Apache-2.0 with additional conditions »** — interdit de déployer « in a way that competes with Agora's offerings » ✅ | C/Go/Python | `0.11.71`, 2026-07-31 ✅ | 2026-09-10 ✅ | — | Graphe temps réel multimodal | ✅ | ✅ | **Actif mais licence NON permissive / non OSI** |
| **Bolna** | MIT ✅ | Python | `0.10.237`, **2026-09-11** ✅ | 2026-09-11 ✅ | — | Cascade, orienté téléphonie | ✅ | ✅ | Actif, communauté plus petite |
| **Unmute** (Kyutai) | MIT ✅ | Python/Rust | — | **2026-09-09** ✅ | — | Cascade STT→LLM→TTS optimisée latence | non (WebRTC/WS navigateur) | ✅ (VAD sémantique Kyutai STT) | Actif — ⛔ **exige GPU CUDA ≥ 16 Go VRAM, x86_64** ✅ |
| **OVOS** (OpenVoiceOS) | Apache-2.0 ✅ | Python | `3.5.4a2`, 2026-09-11 ✅ | **2026-09-13** ✅ | — | Assistant vocal (successeur Mycroft), pas téléphonique | non nativement | ✅ | Actif, mais hors cible téléphonie |

### 1.2 Ressources réelles — le chiffre qui décide

✅ **LiveKit** (doc officielle, `docs.livekit.io/agents/ops/deployment/custom/`) :
> « LiveKit recommends **4 cores and 8 GB per agent server** as a starting rule for most voice AI apps », pour **10–25 jobs concurrents**. Test de charge cité : **30 agents simultanés à ~3,8 cœurs et ~2,8 Go de RAM**.

🔶 **Lecture décisive pour votre cas** : 2,8 Go pour 30 sessions ≈ **~90 Mo par session**, *quand STT/TTS/LLM sont déportés en API*. Autrement dit, **l'orchestrateur n'est pas le problème sur un VPS 1–2 Go — l'inférence locale l'est.** C'est l'arbitrage central de tout ce rapport.

✅ **Jambonz mini** (doc officielle, `docs.jambonz.org/self-hosting/bare-metal-vps/debian-package`) : Debian 12, « At least **4 vCPU, 8 GB RAM, 100 GB disk** ». Installe drachtio + rtpengine + MariaDB + Redis + nginx + Grafana + InfluxDB + Node. **Hors périmètre 1–2 Go, sans discussion.**

⚠️ Pipecat ne publie **aucun minimum RAM officiel**. 🔶 Par construction (un process Python asyncio + services distants), l'empreinte est du même ordre que LiveKit, voire inférieure puisqu'il n'impose pas de SFU WebRTC.

### 1.3 Support des modèles locaux (critère décisif)

| Framework | STT local | TTS local | LLM local | VAD / turn |
|---|---|---|---|---|
| **Pipecat** ✅ | Whisper (faster-whisper, CPU/CUDA, `tiny`→`large-v3-turbo`, `compute_type="int8"`), Moonshine, FunASR, Whisper MLX | **Piper** (local + serveur HTTP), **Kokoro** (ONNX local, cache `~/.cache/pipecat/kokoro-onnx/`), XTTS-vLLM, Fish | **Ollama** | Silero VAD intégré, **Smart Turn** intégré |
| **LiveKit** | ⚠️ docs centrées sur les fournisseurs commerciaux ; override `base_url` pour tout endpoint compatible OpenAI | idem | idem via endpoint compatible | Silero + **turn-detector propriétaire** (voir §6) |

🔶 **Pipecat est nettement mieux outillé que LiveKit pour une pile 100 % auto-hébergée**, et sa licence BSD-2 est plus permissive qu'Apache-2.0 (aucune clause brevet à propager). Les voix françaises de Kokoro sont documentées côté Pipecat (`fr-fr`, `fr-be`, `fr-ca`, `fr-ch`) ✅ — mais voir §4 sur la faiblesse réelle du français dans Kokoro.

---

## 2. Stack téléphonie open source

### 2.1 Tableau comparatif

| Projet | Licence exacte | Dernière version | Dernier push | Langage | Rôle | Empreinte |
|---|---|---|---|---|---|---|
| **Asterisk** | **GPL-2.0** (+ exception OpenSSL) ✅ | **23.5.0 — 2026-08-27** ; LTS **22.11.0** ✅ | actif ✅ | C | PBX / media server | 🔶 la plus frugale des media servers (modules à la carte via `make menuselect`) |
| **FreeSWITCH** | **MPL-1.1** ✅ (fichier `LICENSE` du master, vérifié en brut — **pas de bascule propriétaire constatée**) | **1.11.3 — 2026-08-28** ✅ | 2026-09-09 ✅ | C | Media server / B2BUA | 🔶 historiquement plus gourmand qu'Asterisk ; la 1.11 a supprimé ~30 modules legacy |
| **Kamailio** | **GPL-2.0-or-later** ✅ | 6.1.4 (tag) ; 6.1.0 le 2026-02-18 ✅ | **2026-09-13** ✅ | C | Proxy SIP (**pas de média**) | 🔶 le plus léger du lot |
| **OpenSIPS** | **GPL** (+ exception OpenSSL) ✅ | 4.0.2 (tag) ✅ | 2026-09-11 ✅ | C | Proxy SIP (pas de média) | 🔶 idem |
| **drachtio-server** | **MIT** ✅ | **v0.9.11 — 2026-08-14** ✅ | **2026-08-20** ✅ | C++ | Contrôle SIP piloté en Node.js | 🔶 léger (pas de média : rtpengine à côté) |
| **baresip** | **BSD-3-Clause** ✅ | 4.11.0 (tag) ✅ | **2026-09-13** ✅ | C | User-agent SIP modulaire (client) | 🔶 très léger |
| **Jambonz** | MIT (v10) / ⚠️ clé commerciale (v11+) | v11.1.4 (août 2026) ⚠️ | 2026-09-13 ✅ | Node | Voice gateway | ⛔ **4 vCPU / 8 Go minimum** ✅ |

⚠️ **Aucun de ces projets ne publie de minimum RAM officiel.** Le README d'Asterisk n'énonce que des prérequis de compilation ; la doc self-hosting de jambonz ne chiffre pas par taille de déploiement. Toute valeur circulant sur les blogs est **non vérifiée**. Les colonnes « empreinte » ci-dessus sont des 🔶 hypothèses fondées sur l'architecture (C vs Node, média vs pas de média).

### 2.2 Comment brancher un agent IA sur le flux audio

| Voie | Stack | Licence / état | Verdict 1–2 Go |
|---|---|---|---|
| **AudioSocket** | Asterisk 16+ ; TCP bidirectionnel, PCM brut, header 3 octets + payload | Dans le cœur Asterisk (GPL-2.0) ✅. Wideband (G.722) requiert **Asterisk 20.17+ / 21.12+ / 22.7+ / 23.1+** ✅ | ✅ **Le meilleur rapport simplicité/poids.** Protocole trivial à implémenter |
| **ARI External Media** | Asterisk `externalMedia` → RTP vers un process externe | GPL-2.0, cœur Asterisk ✅ | ✅ Solide, plus verbeux |
| **mod_audio_stream** | FreeSWITCH + WebSocket | ⚠️ **L'édition communautaire est uni-directionnelle ; la bidirectionnelle v1.0.3 est un produit commercial, gratuit ≤ 10 canaux, source payante** | ⚠️ Acceptable à petite échelle, **pas du vrai OSS permissif** |
| **mod_audio_fork** | FreeSWITCH + WebSocket (ancêtre) | ⛔ **MORT — `drachtio/drachtio-freeswitch-modules` renvoie HTTP 404** (vérifié par curl le 2026-09-13) ✅ | ⛔ **Tout tutoriel FreeSWITCH+IA antérieur à 2026 qui le cite est périmé** |
| **WebSocket jambonz** | API custom speech, streaming LLM/TTS | MIT en v10, clé de licence en v11 ⚠️ | ⛔ écarté (RAM + licence) |
| **SIP → WebRTC** | `livekit/sip` (Apache-2.0, 465★, push 2026-09-11) ✅ | Pont SIP↔LiveKit, Go | ⚠️ impose serveur média LiveKit + Redis : **trop lourd pour 1 Go** |

⚠️ **Piège documenté** (source tierce, `phonesstillexist.com`, 2026-05-20) : avec `mod_audio_stream`, l'appel via `${api(…)}` dans le dialplan détache l'audio bug quasi immédiatement (~0,3 s capturées) — il faut passer par un script Lua ; et la spec de format doit être un nombre littéral (`8000`, pas `8k`).

### 2.3 Trunks SIP en France

| Fournisseur | Abonnement | Minute | Notes |
|---|---|---|---|
| **Zadarma** (numéro France) | **2 € à 7,50 €/mois** selon type ; connexion **0 €** ✅ | **Entrants gratuits** (sauf 0800) ✅ | **3 lignes simultanées incluses** ✅. SIP natif explicitement supporté ✅. Exige passeport/CNI + adresse dans le pays du numéro ✅ |
| **OVHcloud VoIP** (ligne) | **0,99 € HT/mois** (Découverte) ; 4,99 € HT (Entreprise) ✅ | Entreprise : fixes FR+BE illimités ✅ | ⚠️ Caractère « trunk SIP exploitable par un PBX tiers » sur l'offre d'entrée : **non vérifié** |
| **OVHcloud SIP Trunk** | **4 € HT/mois** (à l'usage) ou **19,99 € HT/mois** (illimité) ; setup **9,99 € HT** ✅ | entrants inclus ✅ | Jusqu'à **100 canaux simultanés** ✅ |
| **Twilio** Elastic SIP Trunking (page FR) | **$1,3500/mois** (local long-code) ✅ | Entrant local **$0,0060/min** ; sortant fixe FR **$0,0147/min** ; mobile FR $0,0364 ✅ | Enregistrement +$0,0025/min ✅ |
| **Telnyx** | ⚠️ **non vérifié pour la France** (page tarifs ne ventile que les US) | ⚠️ non vérifié | — |
| **VoIP.ms** | ⚠️ **non vérifié** — `voip.ms/en/rates` renvoie HTTP 403 | ⚠️ non vérifié | — |

⚠️ **Numéro SIP français gratuit : rien de vérifié.** Aucune offre de numéro géographique FR gratuit n'a pu être confirmée sur source officielle. **Le moins cher vérifié avec entrants gratuits et 3 canaux est Zadarma à 2 €/mois** — exactement le profil d'un standard IA à faible volume.

---

## 3. STT open source temps réel

### 3.1 WER français — comparatif homogène

Source unique et standardisée : **Open ASR Leaderboard**, arXiv:2510.06961v4 (révision 2026-03-30), Table 4, piste multilingue (FLEURS, CoVoST-2, MLS). ✅

| Modèle | Ouvert | WER moy. multiling. | RTFx | **WER FR** |
|---|---|---|---|---|
| ElevenLabs Scribe v2 | Non | 2,67 | – | **3,28** |
| AssemblyAI Universal 3 Pro | Non | 3,23 | – | **3,74** |
| **Cohere Labs Transcribe** | Oui | 3,83 | 491 | **4,05** |
| **Mistral Voxtral Small 24B** | Oui | 3,70 | 42,0 | **4,13** |
| **NVIDIA Canary 1B v2** | Oui | 4,60 | 634 | **4,83** |
| **Microsoft Phi-4 Multimodal** | Oui | 4,41 | 78,2 | **5,20** |
| **Meta Omnilingual ASR LLM 7B v2** | Oui | 4,39 | 21,2 | **5,34** |
| **NVIDIA Parakeet TDT 0.6B v3** | Oui | 4,81 | **1 720** | **5,42** |
| **Qwen3-ASR 1.7B** | Oui | 5,11 | 113 | **5,74** |
| **OpenAI Whisper large-v3** | Oui | 4,81 | 111 | **6,36** |

**Lecture** : le meilleur ouvert en FR est Cohere Labs Transcribe (4,05) puis Voxtral Small 24B (4,13), mais taille et RTFx les mettent hors CPU. **Parakeet TDT 0.6B v3 à 5,42 pour un RTFx de 1 720 est le meilleur compromis qualité/compute de la liste.**

### 3.2 WER FR par dataset (model cards officielles)

| Modèle | FLEURS fr | MLS french | CoVoST-2 fr | CommonVoice fr |
|---|---|---|---|---|
| `nvidia/canary-1b-v2` | **5,02** ✅ | **3,36** ✅ | 6,30 ✅ | n/p |
| `nvidia/parakeet-tdt-0.6b-v3` | **5,15** ✅ | 4,97 ✅ | 6,05 ✅ | n/p |
| `bofenghuang/whisper-large-v3-french` (MIT) | **4,84** ✅ | 3,98 ✅ | n/p | 7,28 ✅ |
| `bofenghuang/whisper-large-v3-french-distil-dec16` (MIT) | 5,03 ✅ | **3,57** ✅ | n/p | 7,18 ✅ |
| `nvidia/nemotron-3.5-asr-streaming-0.6b` (chunk 1,12 s) | **9,03** ✅ | n/p | n/p | n/p |
| `vosk-model-fr-0.22` (1,4 Go) | n/p | 11,64 ✅ | n/p | 14,72 ✅ |
| `vosk-model-small-fr-0.22` (41 Mo) | n/p | n/p | n/p | **23,95** ✅ |

⚠️ Les WER de `bofenghuang` sont calculés **après normalisation** (nombres en lettres, ponctuation retirée, minuscules) — non comparables tels quels aux autres colonnes.

### 3.3 Candidats CPU — activité, licence, empreinte

| Projet / modèle | Licence code | Licence poids | Dernière release | Dernier commit | Streaming natif | Empreinte | Verdict 1–2 Go |
|---|---|---|---|---|---|---|---|
| **`nvidia/nemotron-3.5-asr-streaming-0.6b`** + **NeMo-Speech.cpp** | **Apache-2.0** ✅ | **OpenMDW-1.1**, model card : « ready for commercial use » ✅ | — | **2026-09-08** ✅ | ✅ **cache-aware**, chunks 80/160/320/560/1120 ms | **GGUF q8_0 = 742 Mo** ✅ | ✅ **Candidat n°1 sur 2 Go** |
| **`nvidia/parakeet-tdt-0.6b-v3`** (via NeMo-Speech.cpp) | Apache-2.0 ✅ | **CC-BY-4.0** ✅ | HF 2025-08-14 ✅ | — | ❌ (plein contexte) | **GGUF q8_0 = 714 Mo** ✅ | ✅ possible avec fenêtrage applicatif |
| **sherpa-onnx** (`k2-fsa`) + Zipformer FR | **Apache-2.0** ✅ | Apache-2.0 ✅ | **v1.13.8, 2026-09-10** ✅ | 2026-09-11 ✅ | ✅ transducer + endpointing | **~123 Mo int8** ✅ | ✅ le plus léger crédible — ⚠️ **modèle figé au 2023-04-14, CommonVoice FR seul, WER non publié** |
| **whisper.cpp** (`ggml-org`) | MIT ✅ | MIT ✅ | **v1.9.4, 2026-09-11** ✅ | 2026-09-11 ✅ | ❌ fenêtre 30 s, **pas de cache inter-appels** | RAM officielle : tiny ~273 Mo, base ~388 Mo, **small ~852 Mo**, medium ~2,1 Go ✅ | ⚠️ `tiny`/`base` seuls sur 1 Go ; `small` sur 2 Go |
| **Vosk** (`alphacep/vosk-api`) | Apache-2.0 ✅ | Apache-2.0 (small-fr / fr-0.22) ✅ | ⚠️ **v0.3.50 — 2024-04-22 (29 mois)** ✅ | 2026-08-09 ✅ | ✅ natif | **41 Mo** (small-fr) ✅ | ⚠️ seul à tenir dans 1 Go, mais **WER 23,95 % = inexploitable en conversationnel** |
| **faster-whisper** (`SYSTRAN`) | MIT ✅ | — | v1.2.1, 2025-10-31 ✅ | ⚠️ **2025-11-19 (~10 mois)** ✅ | ❌ | dépend du modèle | ⚠️ **Stagnant**, 322 issues. Socle CTranslate2 reste actif (2026-08-31) ✅ |
| **WhisperLive** (`collabora`) | MIT ✅ | — | **v0.10.0, 2026-09-07** ✅ | 2026-09-10 ✅ | ✅ (fenêtrage) | — | Actif |
| **WhisperLiveKit** (`QuentinFuxa`) | **Apache-2.0** ✅ | Apache-2.0 ✅ | v0.2.26, 2026-08-29 ✅ | 2026-08-30 ✅ | ✅ SimulStreaming/AlignAtt, Qwen3-ASR causal | — | ✅ **L'état de l'art algorithmique du streaming** |
| **Kyutai STT** (`stt-1b-en_fr`) | Apache-2.0 ✅ | **CC-BY-4.0** ✅ | ⚠️ aucune release | ⚠️ **2026-01-26 (~7,5 mois)** ✅ | ✅ natif, VAD sémantique, délai 0,5 s ✅ | 1 Md params, **pas de GGUF officiel** | ⛔ hors 2 Go. ⚠️ **WER FR non publié** ; entraîné sur seulement **600 h de FR** ✅ |
| **Moonshine** (`moonshine-ai`) | MIT ✅ | MIT ✅ | v0.1.5, 2026-08-24 ✅ | 2026-08-24 ✅ | ✅ | 34–245 M params | ⛔ **Aucun modèle STT français** (le FR n'existe qu'en TTS) ✅ |
| **Silero models** | ⚠️ **CC-BY-NC-4.0** (non commercial) ✅ | — | — | 2026-07-31 ✅ | — | — | ⛔ licence + **pas de modèle STT FR publié** |
| `openai/whisper` | MIT ✅ | MIT ✅ | v20250625 (2025-06-26) ✅ | 2026-08-31 ✅ | ❌ | — | Maintenance minimale |
| `huggingface/distil-whisper` | MIT ✅ | MIT ✅ | — | ⛔ **2025-01-08 (20 mois) — MORT** ✅ | ❌ | — | ⛔ et **anglais uniquement** |
| `ufal/whisper_streaming` | MIT ✅ | — | ⚠️ aucune release | ⚠️ **2025-11-12** ✅ | ✅ LocalAgreement-2 | — | Figé, rôle historique (repris dans WhisperLiveKit) |
| **Voxtral-Mini-3B** (Mistral) | Apache-2.0 ✅ | Apache-2.0 ✅ | 2025-07-28 ✅ | — | ❌ | **~9,5 Go VRAM** ✅ | ⛔ |
| **Qwen3-ASR-0.6B** | Apache-2.0 ✅ | Apache-2.0 ✅ | HF 2026-01-28 ✅ | 2026-06-26 ✅ | ✅ mais **backend vLLM seulement** ✅ | 0,6 Md, ⚠️ pas de GGUF officiel constaté | ⚠️ à explorer |
| **IBM granite-4.0-1b-speech** | Apache-2.0 ✅ | Apache-2.0 ✅ | 2026-03-06 ✅ | — | ❌ | GGUF Q4_K_M 1 139 Mo + mmproj 1 159 Mo = **~2,3 Go** ✅ | ⛔ dépasse 2 Go |

### 3.4 Pourquoi Whisper n'est plus la bonne réponse en 2026

Argument structurel (formulé par Moonshine, méthodologie publiée) ✅ : Whisper impose une **fenêtre fixe de 30 s** (padding inutile sur de la parole courte) et **ne conserve aucun cache entre appels** — tout est recalculé à chaque incrément. Sur 82 langues listées par OpenAI, seules 33 passent sous 20 % de WER en `large-v3`, et **seulement 5 en taille `base`** ✅. C'est l'argument décisif contre `whisper-tiny`/`base` en français sur VPS.

⚠️ Latences CPU x86 publiées par Moonshine (source tierce, à traiter comme ordre de grandeur) : Whisper Tiny **1 141 ms**, Whisper Small **3 425 ms**, Whisper Large-v3 **16 919 ms**.

⚠️ **Inconnue bloquante** : **aucune source officielle ne publie de RTF CPU pour NeMo-Speech.cpp.** La doc expose une commande `nemo-speech bench asr` mais aucun chiffre. C'est le premier test à faire sur le VPS cible.

---

## 4. TTS open source temps réel

### 4.1 Licences et activité

| Moteur | Licence CODE | Licence POIDS | Commercial | Dernière release | Dernier commit |
|---|---|---|---|---|---|
| **Piper** (`OHF-Voice/piper1-gpl`) | ⚠️ **GPL-3.0-or-later** ✅ | MIT (repo voix) + **licence du dataset par voix** ✅ | ✅ sous conditions GPL | **v1.8.0 — 2026-09-04** ✅ | **2026-09-09** ✅ |
| Piper legacy (`rhasspy/piper`) | MIT ✅ | idem | ✅ | 2023-11-14 ✅ | 2025-08-26 ✅ (gelé) |
| **Kokoro-82M** | Apache-2.0 ✅ | **Apache-2.0** ✅ | ✅ **sans condition** | pypi `kokoro` 0.9.4, 2025-04-05 ✅ | 2025-08-06 ✅ |
| **XTTS-v2 / Coqui** | MPL-2.0 ✅ | ⛔ **CPML 1.0 — non commercial** ✅ | ⛔ **NON** | — | ⛔ **2024-08-16 (mort)** ✅ |
| `idiap/coqui-ai-TTS` (fork vivant) | MPL-2.0 ✅ | ⚠️ **ne relicencie PAS les poids XTTS** | ⛔ NON pour XTTS | pypi `coqui-tts` 0.27.5, 2026-01-26 ✅ | 2026-06-10 ✅ |
| **F5-TTS** | MIT ✅ | ⛔ **CC-BY-NC-4.0** ✅ | ⛔ NON | — | 2026-07-23 ✅ |
| **Orpheus TTS** | Apache-2.0 ✅ | Apache-2.0 ✅ | ✅ | — | ⚠️ **2025-12-05** ✅ |
| **Chatterbox** (Resemble) | MIT ✅ | **MIT** ✅ | ✅ | v0.1.2, 2025-06-13 ✅ | 2026-07-21 ✅ |
| **Kyutai TTS** (`tts-1.6b-en_fr`) | Apache-2.0 ✅ | **CC-BY-4.0** ✅ | ✅ (attribution) | — | ⚠️ 2026-01-26 ✅ |
| **Dia** (Nari Labs) | Apache-2.0 ✅ | Apache-2.0 ✅ | ✅ | — | ⚠️ 2025-11-19 ✅ |
| **Fish-Speech / OpenAudio** | ⛔ Fish Audio Research License ✅ | ⛔ **CC-BY-NC-SA-4.0** ✅ | ⛔ NON | — | 2026-08-22 ✅ |
| **Sesame CSM-1B** | Apache-2.0 ✅ | Apache-2.0 ✅ | ✅ | — | ⛔ **2025-05-27 (mort)** ✅ |
| **MeloTTS** | MIT ✅ | MIT ✅ | ✅ | — | ⛔ **2024-12-24 (mort)** ✅ |
| **StyleTTS2** | MIT ✅ | MIT ✅ | ✅ | — | ⛔ **2024-03-07 (mort)** ✅ |
| **Parler-TTS** | Apache-2.0 ✅ | Apache-2.0 ✅ | ✅ | — | ⛔ **2024-12-10 (mort)** ✅ |
| **VibeVoice** (Microsoft) | MIT ✅ | MIT ✅ | ✅ | VibeVoice-ASR-Streaming, 2026-09-03 ✅ | 2026-09-03 ✅ — ⚠️ **le TTS a été retiré du repo (avis du 2025-09-05)**, le projet a pivoté vers l'ASR |
| **Higgs Audio v2** | Apache-2.0 (repo) ✅ | ⚠️ Boson Community License (dérivée Llama 3) ✅ | ✅ sous attribution | — | 2026-06-05 ✅ |
| **Supertonic** | MIT ✅ | ⚠️ **OpenRAIL-M** ✅ | ✅ avec restrictions d'usage | — | ⛔ **repo ARCHIVÉ le 2026-09-09** ✅ |

### 4.2 Français réel, empreinte, streaming

| Moteur | Français | Empreinte | Streaming | Clonage | Verdict 1–2 Go CPU |
|---|---|---|---|---|---|
| **Piper** | ✅ **6 voix FR** (`gilles`, `mls`, `mls_1840`, `siwis`, `tom`, `upmc`) | `fr_FR-siwis-medium.onnx` = **63,2 Mo** ; `fr_FR-upmc-medium.onnx` = **76,7 Mo** ✅ | serveur HTTP `/synthesize` ; ⚠️ streaming granulaire non documenté | ❌ | ✅ **LA référence** |
| **Kokoro-82M** | ⚠️ **1 seule voix FR** (`ff_siwis`), **grade B-** ; model card : « Total French training data: < 11 hours » ✅ | ONNX `model_q8f16` = **86 Mo** ; `model_quantized` = **92 Mo** ✅ | ❌ natif | ❌ | ✅ techniquement, ⚠️ qualité FR faible |
| **Supertonic 3** | ✅ `fr` parmi 31 langues | ~99 M params ONNX ; RTF **0,3×** mesuré (liseuse Onyx Boox) ✅ | ONNX Runtime | ⚠️ non vérifié | ⚠️ **archivé, plus de correctifs** |
| **Chatterbox** | ✅ `fr` parmi 23 langues ✅ | 0,5 Md params (v3) ; variantes nano/flash/turbo-ONNX taguées **`en` uniquement** ✅ | ⚠️ non vérifié en OSS | ✅ zero-shot | ⛔ GPU |
| **Kyutai TTS** | ✅ **natif** (`tts-1.6b-en_fr`) | 1,8 Md params ; délai audio **1,28 s** ✅ | ✅ natif ✅ | ⚠️ restreint (embeddings pré-calculés) | ⛔ GPU |
| **Orpheus** | ✅ `canopylabs/3b-fr-ft-research_release` (Apache-2.0) — ⚠️ **147 dl/mois, figé depuis 2025-04-09** ✅ | 3 Md (Llama-3B) ; **~200 ms** latence streaming ✅ | ✅ | ✅ | ⛔ GPU |
| **NeuTTS-Nano French** | ✅ | 0,2 Md, GGUF Q4/Q8 ; « real-time or better on laptop-class CPUs » ✅ | — | ✅ (3–15 s d'audio) | ⚠️ **repo gated, licence `other` non lisible sans accepter l'accord, sorties filigranées** ⛔ |
| **Dia** | ⛔ « English generation only » ✅ | 1,6 Md, ~10 Go VRAM ✅ | ❌ | ✅ | ⛔ |
| **Higgs Audio v2** | ⛔ (tags `en, zh, de, ko`) ✅ | 6 Md ✅ | ⚠️ | ✅ | ⛔ |
| KittenTTS nano 0.1 | ⚠️ **langues non documentées — FR non vérifié** | **15 M params, < 25 Mo**, Apache-2.0 ✅ | — | ❌ | ⚠️ à explorer |

### 4.3 Pièges juridiques du TTS — à lire avant de choisir

**1. ⛔ Coqui XTTS-v2 est juridiquement mort pour un usage facturé.** Texte exact de la CPML 1.0 (`LICENSE.txt` du dépôt HF) ✅ :
> « This license allows **only non-commercial use** of a machine learning model and its outputs. » — « Use for **revenue-generating activity** […] **is not a non-commercial purpose**. »

Le dépôt `coqui-ai/TTS` n'a pas bougé depuis 2024-08-16 et `https://coqui.ai/cpml` renvoie **404** (société fermée) ✅. Le fork `idiap/coqui-ai-TTS` est vivant et sous MPL-2.0 — **mais un fork du code ne relicencie pas les poids**, qui restent CPML.

**2. ⚠️ Piper : deux pièges.**
- Le code est passé de **MIT** (`rhasspy/piper`) à **GPL-3.0-or-later** (`OHF-Voice/piper1-gpl`, PyPI `piper-tts` 1.8.0) ✅. 🔶 Appeler le binaire ou le serveur HTTP en sous-processus reste hors du périmètre copyleft ; **lier `libpiper` dans du code propriétaire le déclenche**. → **Architecture obligatoire : Piper en service HTTP séparé.**
- Les voix FR n'ont **pas la même licence de dataset** ✅ :

| Voix FR | Dataset | Licence | Verdict commercial |
|---|---|---|---|
| `fr_FR-siwis-medium` / `-low` | SIWIS (Edinburgh DataShare) | **CC-BY 4.0** | ✅ **OK**, attribution requise |
| `fr_FR-mls-medium` (125 locuteurs) | OpenSLR 94 | **CC-BY 4.0** | ✅ OK |
| `fr_FR-mls_1840-low` | OpenSLR 94 | CC-BY 4.0 | ✅ OK |
| `fr_FR-upmc-medium` (2 locuteurs) | marytts/upmc-pierre-data | **CC-BY-SA 4.0** | ✅ OK mais **partage à l'identique** |
| `fr_FR-tom-medium` | git.bksp.space/Tjiho | ⛔ **AGPLv3** | ⛔ **À ÉVITER — copyleft réseau** |
| `fr_FR-gilles-low` | MODEL_CARD vide | ⚠️ **non vérifié** | ⚠️ à éviter par prudence |

- ⚠️ Gouvernance : le README de `piper1-gpl` porte « **The Open Home Foundation is looking for maintainers for Piper!** » ✅. Projet très actif mais en recherche de mainteneurs — risque à surveiller.

**3. ⚠️ Supertonic a été archivé il y a 4 jours** (2026-09-09) ✅ : « This repository is archived. Development and support have ended. » Poids migrés vers `supertone-oss-archive`. Licences toujours valides, mais **plus aucun correctif**. 258 téléchargements/mois pour supertonic-3.

**4. ⛔ Fish-Speech : double verrou.** Code = Fish Audio Research License (« Commercial Purpose requires a separate written license agreement ») ✅ ; poids = CC-BY-NC-SA-4.0 ✅.

**5. ⛔ Projets morts** : MeloTTS (2024-12-24), StyleTTS2 (2024-03-07), Parler-TTS (2024-12-10), GLM-4-Voice (2024-12-05), Zonos (2025-03-05), Sesame CSM (2025-05-27), Hibiki (2025-04-15) ✅.

⚠️ **Non vérifiés** : RTF chiffré de Piper sur CPU x86/ARM (aucun benchmark officiel dans `piper1-gpl`) ; consommation RAM à l'exécution (distincte de la taille du fichier) de Piper et Kokoro ; classement TTS Arena v2 (ELO non exposé en HTML statique) ; Artificial Analysis (non consulté).

---

## 5. Speech-to-speech / duplex

| Modèle | Licence | Taille | VRAM | Latence | FR | Activité |
|---|---|---|---|---|---|---|
| **Moshi** (Kyutai) | CC-BY-4.0 (poids), Apache-2.0 (code) ✅ | **8 Md** (BF16) | ⚠️ non documentée | **160 ms théorique, 200 ms en pratique** ✅ | ⛔ **anglais uniquement** ✅ | code 2026-09-09 ✅ ; ⚠️ **poids figés au 2024-09-18** ✅ |
| **Unmute** (Kyutai, cascade) | MIT ✅ | — | ⛔ **16 Go VRAM minimum, CUDA x86_64** ✅ | TTS ~750 ms sur 1 GPU → ~450 ms multi-GPU ✅ | ✅ via `tts-1.6b-en_fr` | **2026-09-09**, très actif ✅ |
| **Ultravox** (Fixie) | MIT ✅ | 8 Md | ⚠️ non documentée | ⚠️ non chiffrée | ⚠️ non documenté | ⚠️ **2025-12-12** ✅ |
| **Qwen3-Omni-30B-A3B** | `license_name: apache-2.0` ✅ | 35 Md (MoE) | ⛔ **78,85 Go** (vidéo 15 s) ✅ | temps réel revendiqué | ✅ **entrée ET sortie audio FR** ✅ | 2026-04-23 ✅ |
| **MiniCPM-o 2.6** | Apache-2.0 ✅ | 8 Md | **7 Go en int4** ✅ | ⚠️ non chiffrée | ⛔ parole **EN/ZH seulement** ✅ | 2026-09-08 ✅ |
| **Voxtral-Mini-3B** | Apache-2.0 ✅ | 3 Md | **~9,5 Go** ✅ | ⚠️ | ✅ FR natif | 2025-07-28 ✅ |
| **GLM-4-Voice** | Apache-2.0 (code) ✅ | 9 Md | ⚠️ | — | ⛔ ZH/EN | ⛔ **2024-12-05 — MORT** ✅ |
| **Step-Audio 2 mini** | Apache-2.0 ✅ | ⚠️ | ⚠️ | — | ⛔ pas de FR documenté | 2026-03-16 ✅ |

### Conclusion de section — sans ambiguïté

⚠️ **Point important à ne pas confondre** : Ultravox et Voxtral **ne produisent pas de parole**. Model card Ultravox : « Ultravox currently takes in audio and **emits streaming text**. » ✅ Voxtral : « accepts audio […] but produces **text responses only** » ✅. Ce ne sont pas des modèles speech-to-speech au sens plein.

✅ **Aucun modèle speech-to-speech n'est self-hostable sur un VPS 1–2 Go sans GPU.** Le plancher le plus bas officiellement documenté de toute la catégorie est **16 Go de VRAM** (Unmute). Le seul S2S réellement francophone en sortie audio est **Qwen3-Omni, à 79 Go de VRAM minimum**. Moshi, malgré ses 200 ms remarquables, est anglais uniquement et ses poids n'ont pas bougé depuis septembre 2024.

🔶 **Conséquence structurelle : pour un agent téléphonique FR à budget ~0, la voie duplex de bout en bout n'existe pas. Il faut une cascade STT → LLM → TTS.**

---

## 6. Détection de tour de parole / VAD / endpointing

C'est le facteur n°1 de qualité perçue. Un agent qui coupe la parole passe pour stupide ; un agent qui attend une seconde passe pour mort.

### 6.1 Tableau comparatif

| Modèle | Licence | Taille | Latence CPU | FR | Activité | Verdict |
|---|---|---|---|---|---|---|
| **Silero VAD v6** | ✅ **MIT**, sans télémétrie ni clé | **~1,2 Mo / ~309 K params** ✅ | chunks de 30 ms **en < 1 ms** ✅ ; fenêtre native 512 éch. (32 ms @16 kHz) | agnostique | **v6.2.1 2026-02-24**, commits **2026-08-24** ✅ | ✅ **Le choix par défaut** |
| **Smart Turn v3 / v3.1** (pipecat-ai) | ✅ **BSD-2-Clause — poids + données + script d'entraînement ouverts** | **8 Mo / ~8 M params**, int8 QAT ; encodeur Whisper Tiny + têtes | **12,6 ms** (c7a.2xlarge) · 15,2 ms (c8g.2xlarge) · 33,8 ms (t3.2xlarge) · **59,8 ms (c8g.medium)** — **sans GPU** ✅ | ✅ **23 langues dont le français** ✅ | ⚠️ repo `pipecat-ai/smart-turn` dernier commit **2026-01-29** ; le code v3 vit désormais **dans Pipecat** (`LocalSmartTurnAnalyzerV3`) + HF ✅ | ✅ **Le meilleur endpointing sémantique réellement libre** |
| **LiveKit Turn Detector v1 / v1-mini** | ⛔ Code Apache-2.0, **poids sous « LiveKit Model License »** : « you may use these LiveKit models freely but **can only use them together with the LiveKit Agents framework**. You cannot use the LiveKit models on a standalone basis or with any other frameworks » ✅ | 0,1–0,5 Md params, ONNX INT8 ; **v1-mini : < 500 Mo RAM, CPU local** ✅ | ⚠️ chiffre absolu non publié. **9,9 % de faux-coupures à 300 ms ; 4,5 % à 600 ms** ; 543 ms de latence moyenne à 5 % de faux-coupures ✅ | ✅ FR parmi **14 langues** ✅ | actif (agents 1.8.1, 2026-09-10) ✅ | ⛔ **Éliminé par la licence hors LiveKit** |
| **TEN VAD** (Agora) | ⚠️ **Apache-2.0 *avec conditions additionnelles*** — interdit de déployer « in a way that competes with Agora's offerings » ✅ | lib **277 Ko – 731 Ko** selon plateforme ; RTF 0,0086–0,0570 ✅ | très faible ; RAM ⚠️ non chiffrée | agnostique | ⚠️ **2026-02-02 → stagnant ~7 mois** ✅ | ⚠️ **Ni vraiment libre, ni maintenu** |
| **WebRTC VAD** (`py-webrtcvad`) | NOASSERTION (code Google, BSD) ✅ | quelques Ko, GMM | µs | agnostique | ⚠️ **2024-07-04 → stagnant ~26 mois** ✅ | ⚠️ **Legacy.** PCM 16 bits mono 8/16/32/48 kHz, trames 10/20/30 ms. Utile comme garde-fou ultra-léger |
| **Krisp Turn-Taking** (`krisp-viva-tt-v2`) | ⛔ Propriétaire, SDK VIVA sur candidature ✅ | n/a | ⚠️ pas de chiffre absolu | ⚠️ non publié | billet 2025-10-27 ✅ | ⛔ hors périmètre OSS |

### 6.2 L'état du problème, expliqué

**Le VAD acoustique ne résout pas le tour de parole.** Silero/WebRTC/TEN répondent à « y a-t-il de la voix dans cette trame ? ». Le tour de parole répond à « l'humain a-t-il fini et attend-il une réponse ? ».

Un endpointing purement acoustique se règle par un **seuil de silence**, et ce seuil est un arbitrage indépassable : court (200–300 ms) → l'agent coupe sur la moindre hésitation ; long (800–1000 ms) → l'agent paraît mort. ✅ C'est exactement ce que chiffre LiveKit : **9,9 % de faux-coupures à 300 ms contre 4,5 % à 600 ms**.

**L'endpointing sémantique casse cet arbitrage** en ajoutant un signal de contenu. Deux écoles :

- **Texte** (LiveKit v0.4.x, basé Qwen2.5-0.5B-Instruct, désormais déprécié) : petit LLM sur la transcription partielle. ⚠️ Contrainte structurelle documentée : « Cannot be used with audio-native realtime models […] without adding a separate STT service » — il faut donc un STT en plus, ce qui alourdit un VPS 1 Go.
- **Audio natif** (Smart Turn v3, LiveKit v1) : le modèle écoute la forme d'onde et capte prosodie, intonation montante/descendante, allongements. ✅ Smart Turn v3 est le seul du lot où **modèle, données et code d'entraînement sont tous ouverts** — donc reproductible et auditable.

**Tolérance aux hésitations** — le gain concret : « je voudrais réserver pour… euh… » ne doit pas déclencher de réponse. Un VAD acoustique voit 700 ms de silence et parle par-dessus ; un modèle sémantique reconnaît un énoncé inachevé. ✅ LiveKit revendique **−39,23 % de faux positifs d'interruption** entre v0.3.0-intl et v0.4.1-intl, sans surcoût de latence.

**Barge-in** — problème distinct, resté acoustique : il faut un VAD rapide **plus** une annulation d'écho. 🔶 Sur un canal téléphonique, l'audio de l'agent revient en écho dans le flux entrant et, sans AEC, le VAD s'auto-déclenche. C'est une raison technique de piloter le barge-in par une boucle de contrôle stricte (couper le TTS dès détection acoustique) plutôt que par le modèle sémantique, dont les 12–60 ms sont acceptables mais qui n'est pas conçu pour ça.

✅ **Précisions par langue de Smart Turn v3** : TR 97,10 % · KO 96,85 % · JA 96,76 % … BN 84,10 % · VI 81,27 %. ⚠️ **Le chiffre exact pour le français n'a pas été relevé dans les sources consultées** — le français est confirmé comme langue supportée, sa précision précise est **non vérifiée**.

---

## 7. Solutions OSS « AI receptionist » clé en main

### 7.1 Ce qui existe réellement

| Projet | Licence | ★ | Dernier push | Langage | Maturité |
|---|---|---|---|---|---|
| **`hkjarral/AVA-AI-Voice-Agent-for-Asterisk`** | **MIT** ✅ | **1 212** ✅ | **2026-09-11** ✅ | Python | **Le seul candidat sérieux.** Asterisk/FreePBX via AudioSocket/RTP/WebSocket, 7 « golden baselines » validées, UI d'admin web, tool calling (transferts, mail, messagerie), historique d'appels ; sortant en alpha |
| **`agentvoiceresponse/avr-infra`** (AVR) | MIT ✅ | 97 ✅ | 2026-06-12 ✅ | — | Microservices Docker autour d'Asterisk AudioSocket ; briques séparées (`avr-asr-vosk`, `avr-tts-kokoro`, `avr-llm-openai`, `avr-sts-ultravox`) ⚠️ dont plusieurs **datent de 2025 et stagnent** |
| **`kirklandsig/AIReceptionist`** | ⚠️ **AGPL-3.0** ✅ | 108 ✅ | 2026-06-15 ✅ | Python | ⚠️ Auto-hébergeable mais **adossé à l'API OpenAI Realtime** — pas de pile locale. **AGPL = non permissive** |
| **`ictinnovations/asterisk-ai-voice-agent`** | MIT ✅ | 19 ✅ | 2026-09-05 ✅ | Python | Actif mais jeune : STT streaming → LLM → TTS sur AudioSocket, avec barge-in |
| `BB-AI-Arena/helix-ai-virtual-receptionist` | MIT ✅ | 5 ✅ | 2026-04-29 ✅ | Python | Embryonnaire (Asterisk ARI, multilingue) |
| `redwoodmeridian/cicero` | MIT ✅ | 1 ✅ | 2026-07-24 ✅ | TS | Embryonnaire |
| `edwinux/didww-voice-agent` | MIT ✅ | 2 ✅ | 2026-06-07 ✅ | JS | Démonstrateur (drachtio + rtpengine + Gemini Live) |
| `vocodedev/vocode-core` | MIT ✅ | 3 795 ✅ | ⛔ **2024-11-15** ✅ | Python | ⛔ **MORT.** Le README appelle des mainteneurs communautaires |

### 7.2 Verdict franc

✅ Une recherche GitHub sur « AI receptionist / phone agent » retourne **72 dépôts**, dont la quasi-totalité sous les 10 étoiles, sans licence, et qui sont des wrappers Vapi/Retell/n8n — **ni open source, ni auto-hébergeables**. Le champ « standardiste IA clé en main auto-hébergeable » est **quasi désert** : un seul projet dépasse les 1 000 étoiles.

✅ **Et ce projet ne tient pas dans vos contraintes.** Prérequis annoncés par AVA : x86_64 Linux (Ubuntu 20.04+, Debian 11+, RHEL 8+), Docker + Compose v2, Asterisk 18+, et **4 Go de RAM minimum avec des providers cloud ; 8 Go+ en hybride ; 8–16 Go en tout-local CPU**.

⛔ **Conclusion : sur un VPS 1–2 Go, aucune solution clé en main auto-hébergée avec IA locale n'existe aujourd'hui.**

---

## 8. Recommandation

### 8.1 Le constat qui commande tout

Trois faits vérifiés, mis bout à bout, ferment la porte au « tout-local sur petit VPS » :

1. Le plancher speech-to-speech open source est **16 Go de VRAM** (Unmute) ✅ ; le seul S2S francophone en sortie audio demande **79 Go** (Qwen3-Omni) ✅.
2. La seule solution clé en main crédible (AVA, MIT, 1 212★) annonce **8–16 Go pour du tout-local CPU** ✅.
3. Un STT français exploitable pèse **714–742 Mo de poids** (GGUF q8_0) ✅, et le seul modèle tenant réellement dans 1 Go — Vosk small-fr, 41 Mo — affiche un **WER de 23,95 %** ✅, c'est-à-dire un mot sur quatre faux : inexploitable en conversationnel.

🔶 **Mais le même corpus de faits ouvre une porte** : LiveKit mesure **~90 Mo de RAM par session** quand l'inférence est déportée (2,8 Go pour 30 agents) ✅. **L'orchestration et la téléphonie tiennent très bien dans 1–2 Go. C'est uniquement l'inférence qui doit sortir de la machine.**

### 8.2 Architecture recommandée (recommandation, pas un fait)

**Asterisk 22 LTS/23 + AudioSocket + agent Python Pipecat + Silero VAD + Smart Turn v3.1 + inférence déportée.**

| Couche | Choix | Licence | Pourquoi ce choix |
|---|---|---|---|
| **Téléphonie** | **Asterisk 22 LTS** (ou 23.5.0) | GPL-2.0 | La plus frugale des media servers, modules à la carte. **AudioSocket** est le chemin le plus simple et le plus léger vers un process IA (TCP, header 3 octets). Évite FreeSWITCH dont la seule voie bidirectionnelle libre est morte (`mod_audio_fork` 404) ou payante (`mod_audio_stream`) |
| **Numéro / trunk** | **Zadarma** (2 €/mois, entrants gratuits, 3 canaux) | — | La seule offre FR vérifiée avec entrants gratuits et multi-canal à ce prix. Alternative : OVH VoIP 0,99 € HT ⚠️ (exploitabilité en trunk non vérifiée) |
| **Orchestration** | **Pipecat** (BSD-2) | BSD-2-Clause | Licence plus permissive qu'Apache-2.0, **le mieux outillé pour les modèles locaux** (Whisper/Moonshine/Piper/Kokoro/Ollama en first-class), v1.10.0 du 2026-09-12, très actif. Exemples téléphonie fournis |
| **VAD** | **Silero VAD v6** (1,2 Mo, < 1 ms/chunk) | **MIT** | Aucun concurrent sérieux : MIT franc, minuscule, actif (2026-08-24) |
| **Endpointing** | **Smart Turn v3.1** (8 Mo, 12–60 ms CPU, FR couvert) | **BSD-2** | **Le seul endpointing sémantique réellement libre** (poids + données + entraînement ouverts). Évite les deux pièges du secteur : le modèle LiveKit (utilisable *uniquement* dans LiveKit Agents) et TEN VAD (non-concurrence Agora) |
| **STT** | **API** en phase 1. Si local : `nemotron-3.5-asr-streaming-0.6b` GGUF q8_0 (742 Mo) via **NeMo-Speech.cpp** | Apache-2.0 / OpenMDW-1.1 (« ready for commercial use ») | Seul modèle **nativement streaming cache-aware** avec licence commerciale, runtime C++/ggml officiel NVIDIA et support CPU documenté. Plan B qualité : Parakeet TDT 0.6B v3 (714 Mo, CC-BY-4.0, WER FR 5,15) avec fenêtrage applicatif |
| **TTS** | **Piper `fr_FR-siwis-medium`** (63 Mo), **lancé en service HTTP séparé** | code GPL-3.0 / voix CC-BY 4.0 | Le seul TTS FR de qualité correcte tenant sur CPU dans quelques dizaines de Mo, et actif (v1.8.0 du 2026-09-04). **Le lancer en process séparé est obligatoire** pour rester hors du copyleft GPL-3.0 |
| **LLM** | **API externe** | — | Rien de local n'est possible sous 2 Go |

### 8.3 Décisions à ne pas prendre

- ⛔ **Ne pas bâtir sur Vocode** (mort depuis 22 mois, malgré 3 795★), **ni sur Rasa Open Source** (« maintenance mode » écrit dans le README).
- ⛔ **Ne pas utiliser XTTS-v2 / Coqui** dans un produit facturé : la CPML interdit explicitement l'usage générant du revenu, et le fork idiap ne relicencie pas les poids.
- ⛔ **Ne pas utiliser la voix Piper `fr_FR-tom-medium`** (dataset AGPLv3, copyleft réseau) ni `fr_FR-gilles-low` (licence non vérifiée). Rester sur `siwis` (CC-BY 4.0) ou `mls` (CC-BY 4.0).
- ⛔ **Ne pas compter sur le turn detector de LiveKit** hors du framework LiveKit — la licence l'interdit noir sur blanc.
- ⛔ **Ne pas partir sur jambonz** : 4 vCPU / 8 Go minimum, **et** clé de licence commerciale requise pour auto-héberger v11+ depuis janvier 2026.
- ⛔ **Ne pas partir sur TEN Framework ni TEN VAD** : clause de non-concurrence Agora, ce n'est ni OSI ni permissif.
- ⛔ **Ne pas choisir Whisper par réflexe** : fenêtre 30 s, aucun cache inter-appels, et seulement 5 langues sous 20 % de WER en taille `base`.
- ⚠️ **Ne pas s'engager sur Supertonic** (archivé le 2026-09-09) ni **NeuTTS-Nano French** (repo gated, licence illisible, sorties filigranées).

### 8.4 Les trois mesures à faire avant tout engagement client

1. ⚠️ **RTF de NeMo-Speech.cpp sur le VPS cible** (`nemo-speech bench asr --concurrency 1`). **Aucun chiffre CPU officiel n'existe.** C'est l'inconnue bloquante n°1.
2. ⚠️ **WER français en bande téléphonique 8 kHz** pour Nemotron 3.5 et Parakeet v3. Tous les WER publiés sont en 16 kHz ; **aucune source ne publie l'équivalent téléphonique**.
3. ⚠️ **RTF et RAM à l'exécution de Piper** sur le VPS cible. Aucun benchmark officiel dans `piper1-gpl` ; le serveur HTTP expose le temps de synthèse via `/info`.

### 8.5 Signaux de fragilité à surveiller

- 🔶 L'écosystème TTS CPU s'est **fragilisé en 2026** : Supertonic archivé (2026-09-09), Piper en recherche de mainteneurs (Open Home Foundation), Kokoro figé depuis avril 2025. Piper reste le meilleur choix, mais ce n'est pas un socle sans risque.
- 🔶 **Durcissement de licence généralisé** : jambonz (commercial v11+), LiveKit (modèles propriétaires), TEN (non-concurrence Agora), mod_audio_stream (bidirectionnel payant). La tendance 2026 est au repli sur des licences non-OSI. **Pipecat (BSD-2) + Silero (MIT) + Smart Turn (BSD-2) + Asterisk (GPL-2.0) est le seul chemin resté franchement libre de bout en bout.**
- 🔶 `faster-whisper` stagne (10 mois, 322 issues) alors que son socle CTranslate2 reste actif — ⚠️ un fork de reprise est probable mais **n'a pas été identifié** dans cette recherche.

---

## 9. Sources

Toutes consultées le **2026-09-13**.

### Vérifications d'activité (API GitHub + flux Atom + `git ls-remote`)
`api.github.com/repos/{livekit/agents, livekit/livekit, pipecat-ai/pipecat, vocodedev/vocode-core, jambonz/jambonz-api-server, jambonz/jambonz-feature-server}` · flux `releases.atom` / `commits.atom` de : livekit/agents-js, fixie-ai/ultravox, RasaHQ/rasa, drachtio/drachtio-server, TEN-framework/ten-framework, bolna-ai/bolna, kyutai-labs/unmute, OpenVoiceOS/ovos-core, pipecat-ai/pipecat-flows, pipecat-ai/smart-turn, snakers4/silero-vad, OHF-Voice/piper1-gpl, rhasspy/piper · fichiers `LICENSE` bruts via `raw.githubusercontent.com` pour : kyutai-labs/unmute, OpenVoiceOS/ovos-core, fixie-ai/ultravox, RasaHQ/rasa, TEN-framework/ten-framework, jambonz/jambonz-feature-server, bolna-ai/bolna, OHF-Voice/piper1-gpl, signalwire/freeswitch, TEN-framework/ten-vad, OpenSIPS/opensips

### Frameworks — docs officielles
- https://docs.livekit.io/agents/ops/deployment/custom/ (4 cœurs / 8 Go, 10-25 jobs, test 30 agents)
- https://docs.livekit.io/agents/build/turns/turn-detector/ · https://docs.livekit.io/agents/models/ · https://docs.livekit.io/agents/integrations/
- https://docs.pipecat.ai/server/services/supported-services · .../stt/whisper · .../tts/piper · .../tts/kokoro
- https://raw.githubusercontent.com/pipecat-ai/pipecat/main/CHANGELOG.md (v1.10.0, 2026-09-11)
- https://raw.githubusercontent.com/RasaHQ/rasa/main/README.md (« maintenance mode »)
- https://raw.githubusercontent.com/kyutai-labs/unmute/main/README.md (GPU ≥ 16 Go VRAM)
- https://docs.jambonz.org/self-hosting/bare-metal-vps/debian-package (4 vCPU / 8 Go / 100 Go) · https://docs.jambonz.org/self-hosting/overview · https://blog.jambonz.org/why-were-introducing-a-commercial-license

### Téléphonie
- https://www.asterisk.org/asterisk-news/asterisk-23-0-0-now-available/ · https://www.asterisk.org/downloads/
- https://raw.githubusercontent.com/signalwire/freeswitch/master/LICENSE (MPL-1.1) · https://github.com/signalwire/freeswitch/releases/tag/v1.11.1
- https://www.kamailio.org/w/2026/02/kamailio-v6-1-0-released/ · https://www.kamailio.org/w/2026/05/kamailio-v6-1-3-released/
- https://github.com/{OpenSIPS/opensips, baresip/baresip, drachtio/drachtio-server, amigniter/mod_audio_stream, livekit/sip}
- https://phonesstillexist.com/index.php/2026/05/20/building-a-voice-ai-agent-with-freeswitch-part-2-streaming-call-audio-out-of-freeswitch/ (source tierce)
- Tarifs : https://zadarma.com/en/tariffs/numbers/france/ · https://www.ovhcloud.com/fr/phone/ · https://www.ovhcloud.com/fr/phone/sip-trunk/ · https://www.ovhcloud.com/fr/phone/voip/ · https://www.twilio.com/en-us/sip-trunking/pricing/fr · https://telnyx.com/pricing/numbers

### STT — papiers et model cards
- **Open ASR Leaderboard** : https://arxiv.org/html/2510.06961v4 (Table 4) · https://arxiv.org/abs/2510.06961
- Kyutai DSM : https://arxiv.org/html/2509.08753v1 · Parakeet v3 : https://arxiv.org/abs/2509.14128 · Moshi/Mimi : https://arxiv.org/abs/2410.00037 · Moonshine : https://arxiv.org/abs/2410.15608 et https://arxiv.org/abs/2509.02523 · SimulStreaming : https://arxiv.org/abs/2506.17077 · Voxtral : https://arxiv.org/abs/2507.13264
- https://huggingface.co/nvidia/nemotron-3.5-asr-streaming-0.6b · .../parakeet-tdt-0.6b-v3 · .../canary-1b-v2 · .../canary-qwen-2.5b
- https://huggingface.co/kyutai/stt-1b-en_fr · https://huggingface.co/mistralai/Voxtral-Mini-3B-2507 · https://huggingface.co/Qwen/Qwen3-ASR-0.6B · https://huggingface.co/ibm-granite/granite-4.0-1b-speech-GGUF
- https://huggingface.co/bofenghuang/whisper-large-v3-french · .../whisper-large-v3-french-distil-dec16 · https://huggingface.co/openai/whisper-large-v3-turbo · https://huggingface.co/distil-whisper/distil-large-v3.5
- https://github.com/NVIDIA/NeMo-Speech.cpp · https://github.com/ggml-org/whisper.cpp (section *Memory usage*) · https://github.com/SYSTRAN/faster-whisper · https://github.com/OpenNMT/CTranslate2 · https://github.com/collabora/WhisperLive · https://github.com/QuentinFuxa/WhisperLiveKit · https://github.com/ufal/whisper_streaming · https://github.com/moonshine-ai/moonshine (docs/moonshine-vs-whisper.md) · https://github.com/k2-fsa/sherpa-onnx · https://github.com/alphacep/vosk-api · https://alphacephei.com/vosk/models · https://github.com/snakers4/silero-models
- Licence OpenMDW-1.1 : https://openmdw.ai/license/1-1/

### TTS et speech-to-speech
- https://huggingface.co/rhasspy/piper-voices (+ MODEL_CARD de `fr/fr_FR/{siwis,upmc,tom,mls,mls_1840,gilles}`) · https://raw.githubusercontent.com/OHF-Voice/piper1-gpl/main/{README.md,docs/VOICES.md,docs/API_HTTP.md} · https://pypi.org/pypi/piper-tts/json
- https://huggingface.co/hexgrad/Kokoro-82M (+ VOICES.md) · https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX · https://pypi.org/pypi/kokoro/json
- **https://huggingface.co/coqui/XTTS-v2/raw/main/LICENSE.txt (CPML 1.0 — non commercial ; https://coqui.ai/cpml renvoie 404)** · https://pypi.org/pypi/coqui-tts/json
- https://huggingface.co/SWivid/F5-TTS · https://huggingface.co/canopylabs/3b-fr-ft-research_release · https://huggingface.co/ResembleAI/chatterbox · https://huggingface.co/kyutai/tts-1.6b-en_fr · https://huggingface.co/kyutai/pocket-tts · https://huggingface.co/nari-labs/Dia-1.6B · https://huggingface.co/sesame/csm-1b · https://huggingface.co/fishaudio/s1-mini · https://huggingface.co/supertone-oss-archive/supertonic-3 · https://huggingface.co/neuphonic/neutts-nano-french · https://huggingface.co/KittenML/kitten-tts-nano-0.1 · https://huggingface.co/bosonai/higgs-audio-v2-generation-3B-base/raw/main/LICENSE
- https://huggingface.co/kyutai/moshiko-pytorch-bf16 · https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct/raw/main/README.md · https://huggingface.co/openbmb/MiniCPM-o-2_6 · https://huggingface.co/Zyphra/Zonos-v0.1-transformer
- https://github.com/{fishaudio/fish-speech, microsoft/VibeVoice, canopyai/Orpheus-TTS, myshell-ai/MeloTTS, neuphonic/neutts-air, FunAudioLLM/CosyVoice, supertone-inc/supertonic, stepfun-ai/Step-Audio2, zai-org/GLM-4-Voice}

### VAD / turn detection
- https://www.daily.co/blog/announcing-smart-turn-v3-with-cpu-inference-in-just-12ms/ · https://www.daily.co/blog/improved-accuracy-in-smart-turn-v3-1/
- https://livekit.com/blog/solving-end-of-turn-detection · https://livekit.com/blog/improved-end-of-turn-model-cuts-voice-ai-interruptions-39 · https://livekit.com/blog/turn-detection-voice-agents-vad-endpointing-model-based-detection
- **https://huggingface.co/livekit/turn-detector/raw/main/LICENSE (LiveKit Model License)** · https://huggingface.co/livekit/turn-detector
- https://github.com/snakers4/silero-vad · https://github.com/pipecat-ai/smart-turn · https://github.com/TEN-framework/ten-vad · https://github.com/wiseman/py-webrtcvad · https://krisp.ai/blog/krisp-turn-taking/

### AI receptionist OSS
- https://github.com/hkjarral/AVA-AI-Voice-Agent-for-Asterisk · https://github.com/agentvoiceresponse/avr-infra · https://github.com/kirklandsig/AIReceptionist · https://github.com/ictinnovations/asterisk-ai-voice-agent · https://github.com/BB-AI-Arena/helix-ai-virtual-receptionist · https://github.com/redwoodmeridian/cicero · https://github.com/edwinux/didww-voice-agent · https://github.com/vocodedev/vocode-core · https://github.com/pipecat-ai/pipecat-examples

### Sources non consultées / non vérifiées (déclarées)
⚠️ TTS Arena v2 HuggingFace (classement ELO non exposé en HTML statique) · ⚠️ Artificial Analysis (budget de recherche épuisé) · ⚠️ voip.ms/en/rates (HTTP 403) · ⚠️ developer.signalwire.com (bloqué par la politique réseau) · ⚠️ tarifs Telnyx France (non ventilés sur la page publique) · ⚠️ licence des poids Cohere Labs Transcribe · ⚠️ licence des poids Meta Omnilingual ASR distribués sur `dl.fbaipublicfiles.com`. **Aucun chiffre de ces sources n'apparaît dans ce rapport.**
