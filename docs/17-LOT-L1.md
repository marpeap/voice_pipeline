# Lot L1 — le premier appel qui tient une conversation

> Écrit pendant que le banc dort, pour que L1 puisse démarrer le jour où les mesures L0 sont closes.
> **Objectif du lot, en une phrase** : un appelant compose un numéro français, un agent décroche, comprend une demande simple, et raccroche sans avoir menti.

---

## 1. Ce que L1 prouve, et ce qu'il ne prouve pas

**Il prouve** : que la chaîne tient debout de bout en bout, et que **le SLO de latence est mesuré et non estimé**.
**Il ne prouve pas** : qu'un rendez-vous s'écrit (c'est L2), que la configuration est utilisable par un commerçant (L3), ni que l'agent résiste à des appels réels (L5).

**Critère de sortie, unique et mesurable** : **p50 du silence perçu ≤ 700 ms, p95 ≤ 1 100 ms**, sur **20 appels d'essai**, avec la décomposition par étage journalisée.

---

## 2. Ce qui est déjà tranché et n'a pas à être rediscuté

| Décision | Prise dans |
|---|---|
| Pipecat comme orchestrateur (BSD-2), Silero VAD, Smart Turn v3.1 | `00-SYNTHESE` §3 |
| Piper `fr_FR-siwis-medium` **en service HTTP séparé** (GPL-3.0) | `00-SYNTHESE` §3, mesure 1 |
| **Nemotron 3.5 ASR** en service **résident** — jamais un processus par appel (chargement 2,8 s) | mesure 2 |
| **La première réplique de l'agent est courte** (67 ms contre 628 ms de TTFB) | mesure 1 |
| Annonce « assistant automatique » **dans la première phrase**, non désactivable | `00-SYNTHESE` §1.7, A9 |
| Numéro **Telnyx** ; OVHcloud écarté (interdit contractuellement les automates) | A5 |
| Renvoi d'appel **sur non-réponse**, et **la ligne de transfert ne doit pas avoir de renvoi actif** | A4 |

**La seule décision qui attend L0** : **Asterisk auto-hébergé ou media streams d'un fournisseur** (D2). Les tâches ci-dessous sont écrites pour que **seule la tâche 2 change** selon la réponse.

---

## 3. Les tâches, dans l'ordre d'exécution

### T1 — La machine
- [ ] Machine dédiée (~4 Go), **pas `petites-claques`** qui porte déjà Crenolo, **pas `petites-frappes`** qui ne tiendrait qu'un appel.
- [ ] Durcissement d'A4 : `autoload=no` (13 CVE sur 20 visent des modules inutiles), **AMI désactivé**, ARI en loopback, `password_format=crypt`.
- [ ] systemd : **ne pas copier** `MemoryDenyWriteExecute` (tue ONNX, donc Silero et Smart Turn) ni `RestrictRealtime` (gigue audio) ; `MemoryMax` plutôt que `MemoryHigh` ; relever la limite de 5 démarrages / 10 s.
- [ ] fail2ban **avec** `auth_username` dans `endpoint_identifier_order` et `res_security_log.so` chargé — sinon il tourne à vide sans le dire.
- [ ] `TMPDIR` hors tmpfs, et **veille désactivée** (leçon du banc).

### T2 — Le bord téléphonique *(dépend de D2)*
- [ ] **Voie A, Asterisk** : trunk Telnyx en TLS/SRTP, ACL par IP, préfixes FR entrants seulement, AudioSocket vers le worker.
- [ ] **Voie B, fournisseur** : media stream WebSocket, et **on accepte de payer la minute** pendant L1.
- [ ] Dans les deux cas : **anti-boucle maison** (compter ses propres occurrences dans `History-Info` — aucune RFC ne le fait), et `Transfer()` **jamais avant décroché** (302 → boucle garantie).

### T3 — Les services résidents
- [ ] Piper en **service HTTP**, préchauffé au démarrage (le premier appel coûtait 1 001 ms).
- [ ] Nemotron en **service résident**, modèle chargé une fois.
- [ ] Rééchantillonnage **en mémoire**, jamais un processus ffmpeg par énoncé (134 ms de lancement mesurés).

### T4 — Le pipeline
- [ ] Pipecat : VAD Silero → Smart Turn v3.1 → STT → LLM → TTS, **seuils d'endpointing contextuels** (0,25 s sur un oui/non, 1,2 s sur une dictée).
- [ ] **eager EOT + preemptive LLM activés, preemptive TTS non.**
- [ ] `min_interruption_words ≥ 2`, `resume_false_interruption` activé.
- [ ] Débruitage **sur le chemin VAD uniquement**, jamais sur le chemin STT (×2 de dégradation mesurée par Krisp).
- [ ] **Pré-roll du VAD, et flux STT ouvert avant la parole.** Mesuré le 15/09 (`docs/09`, mesure 9) : un moteur streaming perd le premier mot d'**un énoncé sur quatre** (24 %, contre 5 % pour un décodage de fichier entier) — « Mon numéro c'est le zéro six » devient « NUMÉRO C'EST LE ZÉRO SIX ». Le flux doit donc être ouvert et alimenté **avant** que l'appelant ne parle, et le détecteur d'activité vocale doit conserver l'audio d'**avant** son seuil de déclenchement. **Recette** : sur dix appels, le premier mot de la première phrase est transcrit dix fois.

### T5 — Le dialogue minimal
- [ ] Mission unique pour L1 : **répondre à une question simple et prendre un message**. Pas de réservation — c'est L2.
- [ ] Machine à états de `15-RIGUEUR-EXECUTION` : conditions de sortie **vérifiées côté serveur**.
- [ ] Prompt **calibré au-dessus de 4 096 tokens** pour être cachable, variables **après** la rupture de cache.
- [ ] Grammaire française de `10-GRAMMAIRE-FRANCAISE` sur le numéro : relecture par groupes de deux, **le « zéro » initial reconstruit par contrainte**, DTMF après deux échecs.

### T6 — L'instrumentation, dès le premier appel
- [ ] Une ligne par tour : `end_of_utterance_delay`, `llm_ttft`, `tts_ttfb`, `total_latency`, tokens dont **cachés**, `speech_id`, `tenant_id`.
- [ ] Les quatre règles de détection d'échec (raccroché < 10 s, trois reformulations, silence, demande d'humain).
- [ ] **Transcription oui, audio non** (position CNIL : « ni permanent ni systématique »).

### T7 — La conformité, avant le premier appel réel
- [ ] Annonce d'IA **dans la première phrase**, versionnée et journalisée.
- [ ] Journal de provenance (`c2pa.ai-disclosure`), non-rétention de l'audio **écrite comme décision d'architecture**.
- [ ] **Gap analysis** commencée (point 148 des lignes directrices) — le marquage étant **possible mais coûteux**, c'est l'infaisabilité *temps réel* qu'il faut documenter.

---

## 4. Ce qui peut faire échouer ce lot

| Risque | Signal précoce | Parade |
|---|---|---|
| Le SLO ne tient pas | p50 > 900 ms sur les premiers essais | Décomposer par étage — la mesure 1 dit que **le TTS n'est pas le coupable si la première réplique est courte** |
| Le WER s'effondre sur voix réelle | erreurs sur les numéros dès les premiers appels | Le corpus L0 est **synthétique** : c'est le risque n°1 de ce lot, et il ne se lève qu'avec de vrais appels |
| La boucle de renvoi | le transfert revient sur l'agent | Vérifier **avant** que la ligne de transfert n'a pas de renvoi actif |
| Le fournisseur LLM est trop loin | TTFT > 500 ms p95 | **Basculer en UE** — 430 ms mesurés vers les États-Unis |

---

## 5. Ce que L1 ne demande à personne

Ni l'arbitrage sur `reservation.py` (c'est L2), ni la clé d'API si l'on reste sur ce qui est gratuit pour les essais, ni aucun développement côté Crenolo. **L1 est entièrement dans notre périmètre** — c'est précisément ce que le recadrage en service indépendant permet.
