# Lot L0 — mesures

> Les quatre chiffres dont dépend le choix de la pile, et qu'**aucune source publique ne donne**.
> Ce document ne contient que du mesuré. Chaque entrée porte sa machine, ses versions et sa commande.

| # | Mesure | État |
|---|---|---|
| 1 | **RTF et RAM de Piper** (TTS français) | ✅ **fait le 2026-09-14** |
| 2 | **RTF de NeMo-Speech.cpp** | ✅ **fait le 2026-09-14** — et le logiciel **ne compile pas tel qu'il est publié** (voir ci-dessous) |
| 3 | **WER français en bande téléphonique 8 kHz** | ✅ **fait le 2026-09-14** sur corpus synthétique (un corpus d'appels réels reste nécessaire) |
| 4 | **TTFT réel des LLM** | ⚠️ **partiel le 2026-09-14** : mesuré sur Groq (seule clé disponible). Les candidats retenus demandent des clés — **différé, budget à zéro** |
| 5 | **Survie d'un tatouage audio au canal téléphonique** (AudioSeal MIT + ffmpeg, budget zéro) | **à faire** — ajoutée le 14/09. **Aucune publication de 2023 à 2026 ne teste un tatouage neuronal sous codec téléphonique** : cette mesure est la pièce qui transforme notre dossier d'exemption AI Act d'une opinion en une preuve |

---

## Mesure 1 — Piper, voix `fr_FR-siwis-medium`

**Banc** : `marpeap-series`, **Intel Core i5-4210U @ 1,70 GHz**, 4 fils, 5,8 Go de RAM (3,4 Go libres), Debian 13.
⚠️ **Ce processeur est un mobile Haswell de 2014** — il est plus faible qu'un cœur de VPS récent. Les chiffres ci-dessous sont donc un **plancher**, pas un optimum.

**Versions** : `piper-tts` **1.8.0** (GPL-3.0, lancé en processus séparé) · `onnxruntime` **1.30.0** · Python 3.12.14 · voix `fr_FR-siwis-medium` (63,2 Mo, dataset SIWIS **CC-BY 4.0**).
**Méthode** : six phrases réelles d'agent (accueil, acquittement court, proposition de créneau, **relecture d'un numéro**, explication de prestation, récapitulatif long), trois passes, médiane retenue. Script : `bench_piper.py`, résultats bruts dans `resultats_piper.json` sur le banc.

### Résultats

| Phrase | Audio produit | RTF médian | TTFB médian |
|---|---|---|---|
| Accueil | 5,35 s | 0,095 | 404 ms |
| Acquittement (« Très bien. ») | 0,70 s | 0,103 | **67 ms** |
| Proposition de créneau | 3,73 s | 0,096 | 365 ms |
| **Relecture d'un numéro** | 7,61 s | 0,094 | **628 ms** |
| Explication de prestation | 4,09 s | 0,093 | 390 ms |
| Récapitulatif long | 12,25 s | 0,096 | 155 ms |

**Globaux** : RTF médian **0,096** · TTFB médian **372 ms** · TTFB maximal observé **1 001 ms** (premier appel, à froid) · RAM **136 Mo** après chargement, **362 Mo** au pic · sortie **22 050 Hz**.

### Ce que ces chiffres disent

1. **Le RTF est excellent et stable : 0,096**, soit dix fois plus rapide que le temps réel, **sur un processeur de 2014**. Le calcul n'est pas le problème. Un cœur de VPS fera au moins aussi bien.
2. ⚠️ **Mais le TTFB médian est de 372 ms, alors que la cible du cahier des charges est de 150 ms p50.** La cause n'est pas la lenteur du moteur : **Piper synthétise la phrase entière avant de livrer le premier morceau**. Le TTFB est donc proportionnel à la **longueur de la phrase**, pas à la charge — 67 ms pour « Très bien. », 628 ms pour la relecture d'un numéro.
3. **Règle de conception qui en découle, et elle est gratuite : la première chose que dit l'agent doit être courte.** Un acquittement de deux mots part en 67 ms et couvre la synthèse de la suite. Découper la réponse en propositions courtes et les enchaîner en flux ramène le silence perçu sous la cible **sans changer de moteur**. C'est un gain d'architecture, pas de fournisseur.
4. **Prévoir un préchauffage** : le tout premier appel a coûté 1 001 ms. Une synthèse à vide au démarrage du service l'élimine.
5. **La mémoire est confortable** : 136 Mo au repos, 362 Mo au pic — à retrancher du budget d'un appel (rappel : 1 Go ≈ un appel simultané).
6. **Reste à mesurer** : la conversion 22 050 → 8 kHz (négligeable *a priori*, mais non mesurée), et le même banc **sur la machine de production**, une fois choisie.

### Rejouer la mesure

```bash
ssh marpeap-series
cd ~/bancs/l0-piper
PYTHONPATH=~/bancs/l0-piper/lib ~/miniforge3/bin/python bench_piper.py
```


---

## Mesure 3 — WER français, large bande contre bande téléphonique

**Le chiffre qu'aucune source publique ne donne.** Tous les WER publiés (FLEURS, MLS, CommonVoice, Open ASR Leaderboard) sont mesurés en **16 kHz propre** ; notre canal est du **8 kHz G.711**.

### Méthode

**Banc** : `marpeap-series` (i5-4210U @ 1,70 GHz, 2 fils alloués au décodage).
**Corpus** : **47 énoncés d'appelant** générés par Piper — prise de rendez-vous, report, annulation, **cinq numéros de téléphone dictés en toutes lettres**, dates et heures, **les six collisions lexicales du pack coiffure**, noms propres, questions pratiques.
**Dégradation téléphonique reproduite fidèlement** : 22 050 Hz → **8 kHz + encodage μ-law** → retour en 16 kHz. Ce n'est pas un simple rééchantillonnage : l'information perdue par le codec l'est pour de bon.
**Moteurs** : `sherpa-onnx` 1.13.8 avec `streaming-zipformer-fr-2023-04-14` (int8, 249 Mo) · `vosk` 0.3.45 avec `vosk-model-small-fr-0.22` (66 Mo). Installés **par pip en `--target`, sans compilateur ni `sudo`**.

⚠️ **Limite à énoncer avant les chiffres** : un corpus de **parole de synthèse est plus propre que la parole réelle** — pas d'accent, pas de bruit, pas d'hésitation, débit régulier. **Les valeurs absolues sont donc optimistes et ne sont comparables à aucun leaderboard.** Ce qui est exploitable, c'est **l'écart entre les deux conditions**, mesuré sur exactement le même audio.

### Résultats

| Moteur | WER 16 kHz | WER 8 kHz G.711 | Écart | RTF |
|---|---|---|---|---|
| **Vosk small-fr 0.22** (66 Mo) | **7,6 %** | **10,6 %** | **× 1,40** | 0,51 · 0,58 |
| sherpa-onnx zipformer-fr int8 (249 Mo) | 23,4 % | 23,4 % | × 1,00 | 0,10 |

### Ce que ces chiffres disent

1. **La bande téléphonique coûte environ 40 % de WER en plus** sur le moteur qui entend correctement. C'est le premier chiffre du genre dont nous disposons, et il est du même ordre que l'estimation prudente de R1 (+10 à +25 % relatif) — **en pire**.
2. **Le classement est inverse de celui des leaderboards** : le petit modèle de 66 Mo bat le gros de 249 Mo. Explication la plus probable : le zipformer français date de 2023 et n'a vu que CommonVoice, tandis que notre corpus est de la parole de synthèse très régulière. **Ne pas généraliser** — cela dit surtout que *notre* corpus n'est pas *leur* corpus, et que le choix du moteur devra se refaire sur des appels réels.
3. **L'écart nul de sherpa-onnx est une coïncidence globale**, pas une insensibilité : les transcriptions diffèrent bien énoncé par énoncé (0,357 contre 0,286 sur le même numéro dicté). Vérifié à la main.
4. ⚠️ **La découverte utile n'est pas le WER, c'est où il tombe.** Le **« zéro » initial d'un numéro de téléphone est systématiquement massacré**, par les deux moteurs et dans les deux bandes :
   - « Mon numéro c'est **zéro** six douze… » → « mon numéro **ses héros fit** douze… » (Vosk) · « MON NUMÉRO **SES EUROS** SIX DOUZE… » (sherpa)
   - « …au **zéro** sept… » → « …**véro** sept… »
   - « C'est le **zéro** six… » → « c'est le **verrou si**… »
   **Le premier chiffre est le plus fragile de tout l'appel** — précisément celui qui décide si le SMS de confirmation partira.
5. **Règle de conception qui en découle** : ne jamais faire confiance au « zéro » initial. Le protocole de capture (relecture par groupes de deux, puis DTMF après deux échecs) devient **obligatoire dès le premier essai**, et la validation applicative doit **préfixer** le numéro plutôt que de le lire — un mobile français commence par 06 ou 07, l'information est structurellement redondante.
6. **Les deux moteurs tiennent le temps réel sur un processeur de 2014** : RTF 0,10 pour sherpa-onnx, 0,51 pour Vosk. Le calcul n'est pas le mur — ni pour le TTS (mesure 1), ni pour le STT.

### Rejouer

```bash
ssh marpeap-series
cd ~/bancs && PYTHONPATH=$HOME/bancs/l0-piper/lib:$HOME/bancs/l0-stt/lib \
  ~/miniforge3/bin/python bench_wer.py     # résultats détaillés dans resultats_wer.json
```

### Ce qui reste ouvert sur cette mesure

- **Le corpus d'appels réels** (60 à 100, annotés) reste indispensable : il donnera les valeurs absolues, celles-ci ne donnent que l'écart.
- **NeMo-Speech.cpp** (le candidat n°1 de R1) n'a pas pu être mesuré : il demande `cmake` et `gcc`, donc `sudo` sur le banc. **C'est la seule chose qui bloque, et elle tient à un mot de passe.**
- Les **API commerciales** (Deepgram, AssemblyAI, Azure) ne sont pas dans la comparaison faute de clés.


---

## Mesure 2 — NeMo-Speech.cpp + Nemotron 3.5 ASR streaming 0.6B

### D'abord : le logiciel de référence ne compile pas tel qu'il est publié

Constat vérifié, et il explique pourquoi **aucun chiffre de RTF CPU n'existe nulle part** : le symbole **`GGML_TENSOR_FLAG_Q8_PLANAR` est utilisé trois fois** (`src/runtime/ggml/nn.cpp:32`, `src/asr/encoder/fastconformer.cpp:1069`, `src/asr/encoder/rel_pos_attention.cpp:385`) **et défini nulle part** — ni dans les en-têtes du projet, ni dans le `llama.cpp` qu'il épingle. Vérifié au **commit exact** du sous-module (`560445bf3`, 2026-05-10), pas seulement à la pointe. Échec identique sur `v0.1.0` et sur `HEAD` (`a5b6953`), avec gcc 14 / Debian 13.

**Contournement retenu pour mesurer** : leur propre commentaire (`fastconformer.h:311`) indique que ce drapeau ne sert qu'aux « planar-aware **CUDA** kernels ». Sur CPU il est donc sans effet, et il suffit de le définir sur un bit libre :
```bash
cmake -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="-DGGML_TENSOR_FLAG_Q8_PLANAR=16"
```
⚠️ **C'est un contournement de banc, pas une base de production.** Un projet dont la version publiée ne compile pas est un risque d'exploitation à part entière, à porter au dossier de décision de la pile.

### Résultats — même corpus, même métrique que la mesure 3

| Condition | WER | Écart |
|---|---|---|
| 16 kHz large bande | **7,0 %** | — |
| **8 kHz G.711** | **7,8 %** | **× 1,11** |

**Vitesse**, dérivée de deux mesures (un fichier de 5,6 s → 5,77 s ; le corpus entier de 111,5 s en mode répertoire, un seul chargement → 61,7 s) :
- **chargement du modèle ≈ 2,8 s**, une fois par processus — donc **un service résident, jamais un processus par appel** ;
- **RTF d'inférence ≈ 0,53** sur le i5-4210U de 2014. Temps réel tenu, avec ~47 % de marge.
- (Le RTF de 2,3–2,5 observé en lançant un processus par fichier ne mesurait que le rechargement du modèle 47 fois.)

### Comparaison des trois moteurs, sur exactement le même audio

| Moteur | WER 16 kHz | WER 8 kHz | Écart | Poids |
|---|---|---|---|---|
| **Nemotron 3.5 ASR streaming 0.6B (q8_0)** | **7,0 %** | **7,8 %** | **× 1,11** | 742 Mo |
| Vosk small-fr 0.22 | 7,6 % | 10,6 % | × 1,40 | 66 Mo |
| sherpa-onnx zipformer-fr int8 | 23,4 % | 23,4 % | × 1,00 | 249 Mo |

**Et le point qui décide** : le « zéro » initial des numéros, massacré par les deux autres moteurs, **passe chez Nemotron**, y compris en bande téléphonique — trois des cinq numéros dictés sont transcrits **sans aucune erreur**, les deux autres à 5,9 % (« zéro si » pour « zéro six », « quatre-vingt ans » pour « quatre-vingt-onze »). C'est exactement le mode d'échec qui décidait si le SMS de confirmation partait.

**Conclusion provisoire** : la recommandation de R1 (Nemotron comme candidat n°1) est **confirmée par la mesure**, et pour une raison plus forte que le WER global — c'est le seul des trois à tenir sur les entités qui comptent. Réserve inchangée : corpus de synthèse, donc valeurs absolues optimistes.

---

## Mesure 4 — TTFT réel d'un LLM (partielle)

**Aucun fournisseur ne publie de percentiles de TTFT.** Mesure faite depuis la France, en flux, avec un prompt système réaliste d'agent vocal (identité, règles, catalogue, horaires — 6 647 caractères, ~1 660 tokens), 10 requêtes, `max_tokens=60`.

**Seule clé disponible dans le vault : Groq** (celle d'Hermes). La clé Moonshot/Kimi existe aussi mais son solde (~5 $) est le budget d'Hermes — je n'y touche pas.

| Modèle (Groq) | TTFT p50 | TTFT p95 | Réponse complète p50 |
|---|---|---|---|
| `openai/gpt-oss-20b` | **430 ms** | 529 ms | 646 ms |
| `qwen/qwen3.8-27b` | **507 ms** | 634 ms | 824 ms |

**Lecture** :
1. **La cible de 250 ms p50 n'est pas tenue**, et l'écart ne vient pas du modèle : Groq est aux États-Unis. Le trajet France → États-Unis → France mange l'essentiel du budget. **C'est la démonstration chiffrée de la règle « héberger en UE »** — et elle vaut plus que n'importe quel comparatif de débit.
2. Le p95 reste sous les 500 ms visés pour `gpt-oss-20b`, ce qui laisse penser que la variance du fournisseur est faible et que **le problème est bien la distance**.
3. **Le palier gratuit de Groq rend 429 après six requêtes** : utilisable comme repère, pas comme fournisseur.
4. Deux pièges de méthode rencontrés, à garder pour les mesures suivantes : l'agent utilisateur par défaut de `urllib` reçoit un **403** là où `curl` passe (filtrage en amont), et `llama-3.3-70b-versatile` n'existe plus au catalogue.

**Ce qui manque** : une clé pour au moins un candidat réel — **`gpt-5-mini` via `eu.api.openai.com`**, **Gemini Flash-Lite**, ou **Mistral Small chez Scaleway (région Paris)**. La même mesure prend cinq minutes une fois la clé disponible : `bench_ttft.py` est écrit et paramétrable par variables d'environnement (`CLE_LLM`, `BASE_LLM`, `MODELE_LLM`).
