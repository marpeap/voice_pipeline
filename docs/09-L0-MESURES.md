# Lot L0 — mesures

> Les quatre chiffres dont dépend le choix de la pile, et qu'**aucune source publique ne donne**.
> Ce document ne contient que du mesuré. Chaque entrée porte sa machine, ses versions et sa commande.

| # | Mesure | État |
|---|---|---|
| 1 | **RTF et RAM de Piper** (TTS français) | ✅ **fait le 2026-09-14** |
| 2 | **RTF de NeMo-Speech.cpp** | ✅ **fait le 2026-09-14** — et le logiciel **ne compile pas tel qu'il est publié** (voir ci-dessous) |
| 3 | **WER français en bande téléphonique 8 kHz** | ✅ **fait le 2026-09-14** sur corpus synthétique (un corpus d'appels réels reste nécessaire) |
| 4 | **TTFT réel des LLM** | ⚠️ **partiel le 2026-09-14** : mesuré sur Groq (seule clé disponible). Les candidats retenus demandent des clés — **différé, budget à zéro** |
| 5 | **Survie d'un tatouage audio au canal téléphonique** | ✅ **faite le 14/09 — et le résultat est l'inverse de l'attendu** (ci-dessous). **Aucune publication de 2023 à 2026 ne teste un tatouage neuronal sous codec téléphonique** : cette mesure est la pièce qui transforme notre dossier d'exemption AI Act d'une opinion en une preuve |

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

## Piège d'exploitation du banc — à connaître avant toute mesure longue

**`marpeap-series` se met en veille dès qu'il est inactif**, et une session SSH est le seul chose qui le tienne éveillé. Conséquence constatée deux fois le 14/09 : une mesure lancée en arrière-plan puis détachée **est interrompue par la veille**, sans erreur ni trace — la machine disparaît simplement du tailnet.

Deux autres pièges du même banc, payés le même jour :
- **`/tmp` est un tmpfs de 2,9 Go** rempli à 93 %. Une installation qui y décompresse échoue avec un `Errno 28` qui ressemble à un manque de mémoire. **Toujours poser `TMPDIR=$HOME/bancs/tmp`.**
- **torch tire les paquets CUDA par défaut** sur une machine sans GPU (2,5 Go pour rien). **Toujours `--index-url https://download.pytorch.org/whl/cpu`.**

**Règle retenue** : toute mesure de plus d'une minute se lance sous
```bash
systemd-inhibit --what=idle:sleep --why="banc L0" bash mon_banc.sh
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

### Reprise du 2026-09-15 — la lecture « c'est la distance » était incomplète

La mesure a été refaite depuis le poste, avec le même fournisseur et les mêmes modèles, mais en séparant deux régimes : **une connexion neuve à chaque appel** (ce que fait un client HTTP naïf, et ce que faisait le premier banc) contre **une connexion HTTPS maintenue ouverte** d'un appel à l'autre.

| Régime | TTFT p50 | TTFT min | TTFT max |
|---|---|---|---|
| Connexion neuve à chaque appel | **2 040 ms** | 1 704 ms | 8 016 ms |
| **Connexion gardée ouverte** | **378 ms** | **85 ms** | 1 538 ms |

*(`qwen/qwen3.6-27b`, prompt système court, 8 requêtes par régime, poste en France, fournisseur aux États-Unis.)*

**Facteur 5,4, et un minimum à 85 ms vers un fournisseur américain** : la distance ne peut pas expliquer 400 ms, puisque l'aller-retour lui-même en coûte moins de cent. Ce qui coûte, c'est **l'établissement de la connexion** — résolution DNS, poignée TCP, poignée TLS — payé à chaque tour de parole si le client ne réutilise rien.

Deux faits mesurés en marge, qui expliquent le reste de l'écart :

- **Une résolution DNS froide, sur ce poste, coûte de 1,6 à 4,7 s** (`api.mistral.ai` 4,74 s, `api.openai.com` 2,60 s, `api.scaleway.ai` 1,67 s au premier appel ; 1 à 113 ms une fois le cache chaud). Un banc qui ne chauffe pas son DNS mesure son résolveur, pas son fournisseur.
- **Poignée de main complète vers le fournisseur, DNS chaud** : TCP 39 ms, TLS 104 ms. C'est trois allers-retours qu'on ne paie qu'une fois si la connexion vit.

**Règles d'architecture qui en découlent, et qui valent pour les quatre bords du pipeline (STT, LLM, TTS, SMS)** :

1. **Une réserve de connexions ouvertes, établie au démarrage du service**, jamais à l'arrivée de l'appel. Un appel qui commence ne doit ouvrir aucune connexion.
2. **Les noms sont résolus au démarrage et gardés** ; le pipeline ne dépend jamais d'une résolution DNS en cours d'appel.
3. **Une sonde de maintien** (requête minuscule) empêche le fournisseur de fermer une connexion inactive entre deux appels — sinon le premier appel après un creux repaie les 2 s.

**Ce que ça change pour le choix du fournisseur** : la règle « héberger en UE » reste bonne, mais elle n'est plus l'argument principal. **Le premier levier est le client, pas le fournisseur** — et il est gratuit.

### Ce que le catalogue a fait entre-temps

Deux jours après la première mesure, `llama-3.3-70b-versatile` et `llama-3.1-8b-instant` **ont disparu du catalogue** ; `qwen/qwen3.8-27b` mesuré le 13 est remplacé par `qwen/qwen3.6-27b`. Le banc rendait `HTTP 404`, pas un message lisible.

C'est une contrainte de conception, pas une anecdote : **le modèle est une pièce d'usure**. Le pipeline doit tenir un changement de modèle sans redéploiement (nom en configuration), et le corpus de non-régression doit pouvoir être rejoué contre un nouveau modèle en une commande — sinon chaque retrait de catalogue devient une panne.

### Le palier gratuit ne sert pas à mesurer un prompt réaliste

En-têtes lues sur le fournisseur : **8 000 tokens par minute**. Notre prompt calibré au-dessus du seuil de cache (~5 000 tokens) consomme donc un quota par minute et demie, et le banc rend `429` dès la deuxième requête. **Le régime « prompt long mis en cache » n'est pas mesurable sur un palier gratuit** — il faudra une clé payante pour vérifier le gain de cache, et c'est la seule mesure qui restera bloquée sur un budget.

**Ce qui manque** : une clé pour au moins un candidat réel — **`gpt-5-mini` via `eu.api.openai.com`**, **Gemini Flash-Lite**, ou **Mistral Small chez Scaleway (région Paris)**. La même mesure prend cinq minutes une fois la clé disponible : `bancs/ttft.py` est écrit, versionné, et saute tout seul les fournisseurs dont la clé est absente (`GROQ_API_KEY`, `MISTRAL_API_KEY`, `SCW_SECRET_KEY`, `CEREBRAS_API_KEY`, `OPENAI_API_KEY`). Il mesure le premier token **prononçable** séparément du premier token du flux, parce qu'un modèle de raisonnement livre d'abord sa réflexion et qu'un agent téléphonique ne peut pas la dire.


---

## Mesure 5 — le tatouage survit au canal téléphonique, et ça nous enlève un argument

**Banc** : `marpeap-series`, i5-4210U de 2014, ⚠️ **machine chargée à ~4 pendant la mesure** (un processus tiers occupait trois cœurs). **AudioSeal 0.2.0** (MIT, code et poids), torch 2.14 CPU, six phrases réelles d'agent, dégradation **8 kHz + encodage μ-law puis retour en 16 kHz**.

### Résultats

| Condition | Score de détection |
|---|---|
| Audio tatoué, 16 kHz | **1,000** |
| **Audio tatoué, après 8 kHz + G.711 μ-law** | **1,000** |
| **Témoin non tatoué, même canal** | **0,000** |

**Le tatouage survit intégralement au canal téléphonique.** Six phrases sur six, score maximal, et **aucun faux positif** sur le témoin — le détecteur ne voit pas de tatouage là où il n'y en a pas, ce qui rend le premier chiffre crédible.

### Ce que ça change, et ce n'est pas confortable

**J'attendais l'effondrement, et je comptais dessus.** Le raisonnement était : si le tatouage ne survit pas au 8 kHz μ-law, alors le marquage est **techniquement infaisable** sur notre canal — première des deux conditions cumulatives d'exemption du **point (88)** des lignes directrices C(2026) 5054.

**Cette porte est fermée par la mesure.** Le marquage n'est pas infaisable : il fonctionne, et il fonctionne parfaitement. **Nous ne pouvons donc pas invoquer l'infaisabilité de principe.**

**Mais la mesure en ouvre une autre, plus étroite et plus honnête** — le coût :

| | Médiane mesurée |
|---|---|
| Tatouage d'un énoncé | **1 481 ms** |
| Détection | **675 ms** |

⚠️ **Chiffres à prendre avec précaution** : machine de 2014, chargée à ~4 pendant la mesure, et **tatouage de l'énoncé entier** — pas en flux. **À rejouer sur machine au repos.** Mais même divisés par cinq, ces temps restent hors du budget d'un tour de parole (SLO : 700 ms **pour tout le tour**, TTS compris).

**Et le point qui compte vraiment** : **le mode streaming d'AudioSeal est cassé en amont** (issue #105 du 12/09/2026, sans réponse), alors que notre unité de travail est le **chunk de 20 ms**. L'argument d'infaisabilité se déplace donc : il ne porte plus sur le **canal**, il porte sur le **temps réel**.

### Conséquence pour le dossier AI Act

La *gap analysis* (point 148) doit désormais dire, **mesures à l'appui** :
1. le tatouage **survit** au canal téléphonique — mesuré, 1,000 contre 0,000 sur témoin ;
2. mais il coûte **~1,5 s par énoncé** en traitement hors ligne sur notre matériel, et **le mode flux de la seule implémentation libre est non fonctionnel** ;
3. donc l'infaisabilité invoquée est celle du **temps réel**, pas celle du support — et elle devra être **réexaminée** dès qu'AudioSeal réparera son mode flux, ou qu'un fournisseur de synthèse proposera un marquage natif en streaming.

**C'est une position plus faible que celle que j'espérais, mais c'est la vraie.** Et elle est défendable précisément parce qu'elle s'appuie sur une mesure que personne d'autre n'a publiée.

### Rejouer
```bash
ssh marpeap-series
cd ~/bancs && PYTHONPATH=$HOME/bancs/l0-piper/lib:$HOME/bancs/l0-tatouage/lib \
  ~/miniforge3/bin/python bench_tatouage.py    # résultats dans resultats_tatouage.json
```

---

## Mesure 6 — ce que coûte vraiment la bande téléphonique (conversion 8 kHz / G.711)

**Pourquoi la mesurer** : tout le pipeline reçoit du 8 kHz et produit du 22 050 Hz. La conversion est donc payée **deux fois par tour de parole**, et elle avait été jusqu'ici estimée « négligeable » sans chiffre.

### Méthode

79 énoncés français synthétisés par Piper (`fr_FR-siwis-medium`, 22 050 Hz), 235,2 s d'audio au total. Chacun est converti en deux versions : 16 kHz PCM pour la référence large bande, et **8 kHz avec aller-retour µ-law** — c'est-à-dire encodé en G.711 puis redécodé, ce que fait réellement le réseau. Un simple rééchantillonnage à 8 kHz sous-estime la dégradation et ne mesure pas la bonne chose.

### Résultat, et le piège qu'il révèle

| | Mesuré |
|---|---|
| Conversion complète, telle que le banc l'appelle | 7,96 s pour 235,2 s d'audio, **RTF 0,0338** (100,8 ms par énoncé) |
| **Démarrage de `ffmpeg` seul**, sans aucun travail (p50 sur 10 lancements) | **44,9 ms** |
| Travail de conversion réel, une fois les deux démarrages retranchés | **≈ 11 ms par énoncé de 3 s**, soit un **RTF ≈ 0,004** |

**Ce que ça dit** : la conversion ne coûte rien — **c'est le lancement du processus qui coûte tout**. Neuf dixièmes du temps mesuré sont deux `ffmpeg` qui démarrent.

**Conséquence de conception** : le pipeline ne lance **jamais** un processus externe par fragment audio. Le rééchantillonnage se fait dans le processus (bibliothèque liée), une fois pour toutes par flux. Un prototype qui appelle `ffmpeg` par tour de parole ajoute ~90 ms à chaque réplique, soit **plus d'un tiers du budget de 250 ms**, pour un travail qui en vaut onze.

### Rejouer

```bash
python3 bancs/corpus.py --sortie ~/corpus-fr   # génère et chiffre la conversion
```

---

## Mesure 7 — la bande téléphonique ne coûte presque rien à un modèle récent, mais les numéros se perdent quand même

### Méthode

Corpus de `bancs/corpus.py` : **79 énoncés français**, 235 s d'audio, onze familles (numéros dictés, dates, « comme la dernière fois », report/annulation, collisions lexicales du pack coiffure, prix, demande d'humain, cas limites, noms propres, hésitations, prise de rendez-vous nue). Chaque énoncé est transcrit **deux fois** : en 16 kHz, et après **aller-retour µ-law (G.711)** à 8 kHz. Moteur : `whisper-large-v3-turbo` par API, `language=fr`. Même fichier, même moteur, même jour : seul le canal change.

### Résultats

| | WER global | Numéro de téléphone reconstruit exactement |
|---|---|---|
| **16 kHz** | 21,2 % (168 erreurs / 791 mots) | **6 / 10** |
| **8 kHz G.711** | 21,9 % (173 / 791) | **6 / 10** |
| **Écart** | **×1,03** | aucun |

**Le WER global de 21 % n'est pas le vrai taux d'erreur** : il est dominé par une différence d'écriture, pas d'écoute. La référence écrit « zéro six douze trente-quatre », le moteur écrit « 0 612 34 » — mêmes chiffres, sept mots comptés faux. D'où le détail par famille, qui est le chiffre utile :

| Famille | 16 kHz | 8 kHz |
|---|---|---|
| demande d'humain | 0,0 % | 0,0 % |
| « comme la dernière fois » | 1,9 % | 1,9 % |
| cas limites (hors sujet, injection) | 1,9 % | 1,9 % |
| report / annulation | 4,1 % | 4,1 % |
| prise de rendez-vous | 4,1 % | **8,1 %** |
| **collisions lexicales du pack** | **6,6 %** | **6,6 %** |
| hésitations | 9,6 % | 9,6 % |
| prix / horaires | 15,2 % | 15,2 % |
| dates et heures | 21,1 % | **24,2 %** |
| noms propres | 30,9 % | 29,1 % |
| numéros (artefact d'écriture) | 80,5 % | 80,5 % |

### Ce que ces chiffres disent

1. **La bande téléphonique n'est pas une fatalité — c'est une propriété du modèle.** ×1,03 ici, contre ×1,11 pour Nemotron et ×1,40 pour Vosk sur la mesure 3. Un modèle récent et gros encaisse le 8 kHz presque sans perte. **Conséquence : l'écart 16/8 kHz doit être mesuré pour chaque moteur candidat, il ne se déduit pas.**
2. **Les collisions lexicales du pack coiffure passent à 6,6 %**, et identiquement dans les deux bandes. `permanente` / `semi-permanent` / `maquillage permanent`, `patine` / `platine`, `mèches` / `mèche` : ce n'est pas là que ça casse.
3. **Ça casse sur les numéros, et pas à cause de la bande.** Quatre échecs sur dix, **exactement les mêmes en 16 kHz et en 8 kHz** :
   - « zéro un **quarante-trois** vingt-deux onze zéro neuf » → `01 40 3 22 11 09` — le moteur a coupé *quarante-trois* en deux, onze chiffres au lieu de dix ;
   - « zéro neuf soixante-dix zéro zéro quatre-vingt-un douze » → `09-7100-92` — chiffres perdus ;
   - « zéro six **quatre-vingts douze** zéro trois quarante-quatre » → `06 92 03 44` — l'énoncé lui-même est ambigu en français, et le moteur a tranché comme un humain aurait hésité ;
   - l'auto-correction (« douze, quatorze… non, quinze ») est **correctement transcrite** : `06, 12, 14, non, 15, 40, 60`. L'échec n'est pas à l'écoute, il est **à l'interprétation** — c'est le travail de la grammaire de `docs/10-GRAMMAIRE-FRANCAISE.md`, pas celui du STT.

   **Donc : la perte du numéro vient de la grammaire des nombres français, pas du canal.** Les trois parades déjà décidées sont les bonnes, et elles ne sont pas optionnelles : relecture du numéro par groupes de deux, reconstruction sous contrainte (dix chiffres, commence par 0), bascule DTMF après deux échecs.
4. **Les noms propres sont le deuxième point faible** (≈ 30 %), et l'épellation ne les sauve pas toujours. À traiter comme les numéros : relecture, et jamais de décision silencieuse sur un nom.

### Ce que cette mesure ne dit pas

Corpus **synthétique**, **une seule voix**, **aucun bruit**, et un aller-retour µ-law **sans perte de paquets ni gigue**. Les taux absolus sont donc un plancher optimiste. Ce qui est transposable, c'est **l'écart entre les deux bandes** et **la répartition des erreurs par famille** — pas le niveau.

### Rejouer

```bash
python3 bancs/corpus.py --sortie ~/corpus-fr
GROQ_API_KEY=... python3 bancs/wer.py --corpus ~/corpus-fr
```

---

## Mesure 8 — le même corpus sur un petit moteur local, et le WER classe les moteurs à l'envers

### Méthode

Corpus identique à la mesure 7 (79 énoncés, 16 kHz et 8 kHz µ-law), moteur **Vosk `vosk-model-small-fr-0.22`** — 41 Mo, installé **par `pip`, sans compilateur**, exécuté sur le processeur du poste. Même métrique, même normalisation, même code de distance : seules changent la taille du modèle et sa localisation.

### Résultats, côte à côte avec la mesure 7

| | WER 16 kHz | WER 8 kHz | Écart | **Numéro reconstruit** | RTF |
|---|---|---|---|---|---|
| `whisper-large-v3-turbo` (distant, gros) | 21,2 % | 21,9 % | **×1,03** | **6 / 10** | — |
| `vosk-small-fr-0.22` (local, 41 Mo) | **9,0 %** | 11,6 % | **×1,30** | **1 / 10** | 0,37 → 0,41 |

### Trois enseignements, dont un qui change une décision

**1. Le WER classe les deux moteurs à l'envers.** Vosk affiche un WER **deux fois meilleur** (9,0 % contre 21,2 %) et reconstruit **six fois moins de numéros**. La raison est bête et décisive : la référence est écrite en lettres (« zéro six douze »), Vosk aussi, Whisper écrit `06 12`. Le WER récompense donc la forme d'écriture, pas la compréhension. **Un choix de moteur fondé sur le WER publié aurait pris le mauvais.** C'est la démonstration chiffrée de la règle de `docs/07` : le taux d'erreur par entité est la métrique, le WER est un indicateur.

**2. Le format de sortie du moteur décide de la taille du travail de grammaire.** Whisper rend des chiffres : le numéro est presque déjà là. Vosk rend des mots : il faut **toute** la grammaire française des nombres pour en tirer dix chiffres — et le 1/10 de ce tableau mesure d'ailleurs **le convertisseur naïf du banc**, pas Vosk, dont les transcriptions en toutes lettres sont largement correctes. Autrement dit : selon le moteur retenu, `docs/10-GRAMMAIRE-FRANCAISE.md` est **un petit module ou la pièce la plus difficile du produit**. C'est un critère de choix qu'aucun comparatif ne mentionne.

**3. La robustesse au 8 kHz semblait se payer en taille de modèle** — ⚠️ **démenti par la mesure 9**, qui ajoute un troisième moteur : la sensibilité à la bande ne suit aucune propriété affichée et se mesure par candidat. Ce qui reste vrai ici, c'est la forme de la dégradation. ×1,03 pour le gros modèle, **×1,30** pour le petit — et la dégradation n'est pas répartie au hasard :

| Famille | 16 kHz | 8 kHz | |
|---|---|---|---|
| numéros | 4,7 % | **10,2 %** | ×2,2 |
| prix et horaires | 13,0 % | **26,1 %** | ×2,0 |
| collisions lexicales du pack | 9,8 % | 15,6 % | ×1,6 |
| noms propres | 30,9 % | 34,5 % | ×1,1 |
| dates | 5,3 % | 7,4 % | ×1,4 |

**La bande téléphonique frappe exactement là où ça coûte** : les chiffres et les montants, c'est-à-dire ce qui se confirme par SMS et ce qui engage le commerçant. Sur un petit modèle, le 8 kHz n'est donc pas une gêne générale, c'est une attaque ciblée sur les entités.

### Ce que ça pose comme choix

Un petit modèle local tourne à **RTF 0,37** sur un processeur de poste, sans GPU, sans compilateur, sans dépense — c'est utilisable. Mais il exige la grammaire complète **et** encaisse mal le 8 kHz sur les entités. Un gros modèle distant fait l'inverse : entités mieux tenues, bande téléphonique presque gratuite, mais dépendance, coût par minute et données qui sortent.

**Ce banc ne tranche pas le choix — il rend le compromis lisible pour la première fois avec des chiffres du même corpus.** Le trancher demande la mesure qui manque encore : la tenue en charge, qui dira combien d'appels une machine soutient si le STT est local.

### Rejouer

```bash
python3 -m venv ~/bancs-stt && ~/bancs-stt/bin/pip install vosk
# modèle : https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip (41 Mo)
cd bancs && PYTHONPATH=. ~/bancs-stt/bin/python wer_vosk.py
```

---

## Mesure 9 — trois moteurs sur exactement le même corpus, et deux règles de pipeline qui en tombent

### Méthode

Même corpus que les mesures 7 et 8 (79 énoncés, 16 kHz et 8 kHz µ-law), troisième moteur : **`sherpa-onnx-streaming-zipformer-fr-2023-04-14`, int8, 380 Mo**, installé par `pip` sans compilateur, deux fils sur le processeur du poste. C'est un modèle **streaming** — donc le plus proche de ce que le produit fera réellement, puisqu'un agent transcrit au fil de la parole.

### Le tableau complet

| Moteur | Où | WER 16 kHz | WER 8 kHz | Écart | Numéro reconstruit | RTF | Sortie |
|---|---|---|---|---|---|---|---|
| `whisper-large-v3-turbo` | distant | 21,2 % | 21,9 % | ×1,03 | **6 / 10** | — | **chiffres** |
| `vosk-small-fr-0.22` (41 Mo) | local | **9,0 %** | 11,6 % | ×1,30 | 1 / 10 | 0,37 | mots |
| `sherpa zipformer-fr int8` (380 Mo) | local, **streaming** | 18,8 % | 20,0 % | ×1,06 | **0 / 10** | **0,065** | mots, capitales |

### Ce que le troisième point change

**1. Correction de la mesure 8 : la sensibilité au 8 kHz ne suit pas la taille du modèle.** J'avais écrit que la robustesse se payait en taille ; le troisième moteur dit non — 380 Mo pour ×1,06, 41 Mo pour ×1,30, et le plus robuste des trois est le plus gros mais aussi le distant. **La sensibilité à la bande est idiosyncrasique : elle se mesure par candidat, elle ne se déduit d'aucune propriété affichée.** Un moteur qui se trompe déjà beaucoup a d'ailleurs mécaniquement moins à perdre.

**2. Le compromis « chiffres contre mots » est général, et il oppose le local au distant.** Les **deux** moteurs locaux rendent des nombres en toutes lettres ; seul le moteur distant rend des chiffres. Autrement dit : **choisir l'auto-hébergement, c'est s'engager à écrire toute la grammaire française des nombres** (`docs/10`), et choisir le distant, c'est en hériter presque gratuitement. Ce n'est plus une particularité de Vosk, c'est un critère de choix structurant — et il ne figure dans aucun comparatif public.

**3. Un moteur streaming perd le début de l'énoncé, et c'est mesurable.** Premier mot différent de la référence :

| Moteur | Premier mot faux |
|---|---|
| Vosk (hors ligne, fichier entier) | 4 / 79 (**5 %**) |
| Whisper turbo (hors ligne, fichier entier) | 8 / 79 (10 %) |
| **sherpa, streaming** | **19 / 79 (24 %)** |

« Mon numéro c'est le zéro six… » devient « NUMÉRO C'EST LE ZÉRO SIX… ». **Un énoncé sur quatre perd son premier mot** sur le moteur qui travaille comme le fera le produit.

**Règle de pipeline qui en découle, et qu'aucun de nos documents ne portait** : le flux STT doit être **ouvert et alimenté avant que l'appelant ne parle**, et le détecteur d'activité vocale doit **conserver l'audio d'avant le seuil de déclenchement** (pré-roll). Sinon la première syllabe, celle qui porte le « zéro » d'un numéro ou le « non » d'un refus, se perd dans le réchauffement du décodeur. À vérifier explicitement dans le lot L1.

**4. Le calcul n'est pas le mur, et de loin.** RTF **0,065** pour le streaming : une machine soutient, côté STT seul, une quinzaine de flux par cœur. Le poste de coût d'un STT local est donc négligeable — ce qui déplace la question de la charge vers la mémoire et vers le LLM, exactement là où la mesure manquante (tenue en charge) doit regarder.

### Rejouer

```bash
cd bancs && PYTHONPATH=. ~/bancs-stt/bin/python wer_sherpa.py
```

---

## Mesure 10 — la courbe de dégradation au bruit, et le classement des moteurs qui s'inverse

### Méthode

79 énoncés, **en 8 kHz** (la bande réelle), mélangés à un bruit calibré en rapport signal/bruit exact, à **20, 15, 10 et 5 dB**, plus la référence propre. Deux natures de bruit, parce qu'elles ne détruisent pas la même chose :

- **bruit rose** large bande — le sèche-cheveux, la hotte, la rue ;
- **babil** — six voix superposées et décalées, fabriquées **à partir du corpus lui-même**, donc avec le bon spectre et la bonne prosodie : une salle pleine.

Deux moteurs locaux, 18 conditions, 1 422 transcriptions. **C'est la courbe que `docs/07` réclamait et qu'aucune source publique ne donne pour le français téléphonique.**

### Résultats — WER en %

| Condition | `vosk-small-fr` | `sherpa zipformer` |
|---|---|---|
| **propre** | **11,5** | 20,0 |
| rose 20 dB | 15,2 | 19,5 |
| **rose 15 dB** | **24,9** | **20,7** |
| rose 10 dB | 36,4 | 26,3 |
| rose 5 dB | **52,8** | 34,5 |
| babil 20 dB | 12,0 | 19,5 |
| babil 15 dB | 15,8 | 19,0 |
| babil 10 dB | 27,7 | 20,2 |
| babil 5 dB | 51,5 | 28,7 |

### Ce que ça dit, et c'est le résultat le plus dérangeant du lot

**1. Le classement des moteurs s'inverse avec le bruit.** Sur de l'audio propre, Vosk est **deux fois meilleur** que sherpa (11,5 contre 20,0). À partir de **15 dB de bruit rose**, il devient **le pire des deux** (24,9 contre 20,7), et à 5 dB il a perdu la moitié des mots (52,8) quand sherpa en perd un tiers (34,5).

> **Conséquence directe : un moteur ne se choisit pas sur de l'audio propre.** Tout notre classement précédent — et tous les leaderboards publics — décrivent une condition que notre produit ne rencontrera jamais. **Le choix doit se faire au rapport signal/bruit du terrain**, c'est-à-dire autour de 10 à 15 dB.

**2. La pente compte plus que le point de départ.** Sherpa est plat de 20 dB à 10 dB (19,5 → 20,2 en babil) puis se dégrade doucement ; Vosk s'effondre dès 15 dB. Un moteur médiocre mais stable vaut mieux, en exploitation, qu'un bon moteur fragile : le premier rend un service prévisible, le second rend un service qui dépend de la rue où se tient l'appelant.

**3. Le babil est moins destructeur que le bruit rose, à rapport signal/bruit égal** — l'inverse de ce que j'attendais en écrivant le banc. À 10 dB : 27,7 contre 36,4 pour Vosk, 20,2 contre 26,3 pour sherpa. **[H]** Explication probable : notre babil est lui aussi passé en 8 kHz, il est donc confiné à la même bande étroite que la parole utile et il comporte des silences, là où le bruit rose occupe toute la bande en continu. À revérifier avec du babil enregistré en salon — c'est une dette de mesure, pas une conclusion.

**4. Le bruit est du côté de l'appelant, pas du salon.** L'agent n'entend jamais le sèche-cheveux du salon : il entend **l'environnement de celui qui appelle** — la rue, la voiture, le magasin, le haut-parleur. Ce sont précisément des conditions de 10 à 15 dB. **Donc la colonne qui décrit notre exploitation n'est pas la ligne « propre », c'est la ligne 10-15 dB.** Le WER réel à attendre est entre 20 et 27 %, pas entre 9 et 11 %.

### Trois règles de conception qui en tombent

1. **Mesurer le rapport signal/bruit dès les premières secondes de l'appel** — c'est un calcul de deux lignes sur l'énergie pendant et hors parole, et il ne coûte rien. Il est connu avant la première question.
2. **Basculer de stratégie quand il est bas**, au lieu de subir : questions plus courtes, une entité à la fois, **et passage au clavier pour le numéro dès le premier essai** au lieu d'attendre deux échecs (règle T7 de `docs/10`). Le numéro est la seule donnée qu'on ne peut pas se permettre de perdre, et c'est celle que le bruit attaque.
3. **Le journal d'appel enregistre le rapport signal/bruit.** Sans lui, une plainte « l'agent comprend mal » n'est pas diagnosticable ; avec lui, on sait tout de suite si le problème est le moteur, le pack, ou la rue.

### Rejouer

```bash
cd bancs && PYTHONPATH=. ~/bancs-stt/bin/python bruit.py      # ~20 min sur un processeur de poste
```

---

## Mesure 11 — tenue en charge du STT : ce n'est pas lui qui limitera la machine

> **La mesure qui manquait au chiffrage** (`docs/11` §6-2), faite sur le poste plutôt que sur le banc, puisque le banc est hors ligne depuis trois heures. La machine diffère — Intel i5-9300H, 8 fils, bureau chargé en parallèle — mais **la forme du résultat se transpose** : elle dit où est la limite, et surtout où elle n'est pas.

### Protocole

K flux simultanés **partageant un seul modèle en mémoire** — c'est ce que fera le service, et c'est l'hypothèse sur laquelle repose toute l'arithmétique du chiffrage. Chaque flux décode le corpus 8 kHz en boucle pendant 15 s. Un fil par décodeur côté `onnxruntime`, pour que le parallélisme mesuré soit celui **des appels**, pas celui du décodeur.

### Résultats

| Flux simultanés | RTF par flux | Débit agrégé | Mémoire résidente |
|---|---|---|---|
| 1 | 0,082 | 10,2 × temps réel | 229 Mo |
| 2 | 0,093 | 18,2 × | 240 Mo |
| 3 | 0,116 | 22,2 × | 253 Mo |
| 4 | 0,138 | **24,9 ×** | 265 Mo |
| 5 | 0,174 | 24,2 × | 277 Mo |
| 6 | 0,202 | 25,1 × | 285 Mo |
| 7 | 0,234 | 25,5 × | 297 Mo |
| 8 | 0,270 | 25,0 × | 308 Mo |

*(Processus à vide : 201 Mo. Aucune erreur sur les huit paliers.)*

### Trois choses, dont une qui corrige le chiffrage

**1. Un flux STT coûte 11 Mo, pas 150.** La mémoire passe de 229 Mo à un flux à 308 Mo à huit : **+11,3 Mo par flux supplémentaire**, le modèle étant partagé. `docs/11` §2 retenait 150 à 320 Mo « par appel » d'après une source LiveKit — c'est le coût de **toute l'orchestration**, pas du STT. **La part STT de cette ligne est donc négligeable**, et la mémoire par appel doit être réattribuée au reste du pipeline, là où elle sera mesurée.

**2. Le débit sature à 25 × le temps réel dès 4 flux** — le nombre de cœurs physiques de cette machine. Au-delà, les flux supplémentaires se partagent le même gâteau sans le faire grossir : le RTF par flux monte proportionnellement, mais reste **très en dessous de 1**. À 8 flux il est encore à 0,27, soit une marge de facteur 3,7.

**3. Extrapolation prudente : de l'ordre de 25 à 30 appels simultanés avant que le STT ne prenne du retard sur la parole**, sur une machine de ce calibre. Et ce calcul est **pessimiste**, parce qu'un vrai appel laisse le décodeur inactif entre les répliques, là où ce banc le nourrit sans interruption.

> **Conclusion pour le dimensionnement : le STT n'est pas le mur.** Les 4 à 6 appels simultanés que `docs/11` retenait pour une machine à 4 Go n'étaient pas limités par lui. Ce qui reste à mesurer, et qui portera la limite réelle, c'est **l'orchestration par appel, le TTS et surtout le LLM** — à commencer par le nombre de requêtes simultanées qu'un fournisseur accepte.

### Rejouer

```bash
cd bancs && PYTHONPATH=. ~/bancs-stt/bin/python charge_stt.py --max 8 --duree 15
```

---

## Mesure 12 — le moteur distant sous bruit : il ne bouge pas, et il garde les numéros

### Résultats, sur exactement les mêmes fichiers bruités que la mesure 10

| Condition (8 kHz) | `vosk-small-fr` | `sherpa zipformer` | **`whisper-large-v3-turbo`** |
|---|---|---|---|
| propre | **11,5 %** | 20,0 % | 21,9 % |
| rose 15 dB | 24,9 % | 20,7 % | **22,9 %** |
| **rose 10 dB** | 36,4 % | 26,3 % | **23,8 %** |
| babil 10 dB | 27,7 % | 20,2 % | **22,3 %** |
| **Numéro reconstruit, à 10 dB** | — | — | **6 / 10, inchangé** |

### Ce que ça tranche

**1. Le moteur distant est quasi insensible au bruit** : +1,9 point de WER entre le propre et 10 dB de bruit rose, là où le petit modèle local en prend **+25** et le streaming local **+6,3**. Sa courbe est plate.

**2. Et surtout : le taux de numéros reconstruits ne bouge pas d'un pouce** — 6 sur 10 au propre, 6 sur 10 sous bruit. Les quatre échecs sont **les mêmes qu'au calme**, et ils viennent de la grammaire française des nombres (mesure 7), pas de l'acoustique. **Le bruit n'attaque pas l'entité chez ce moteur ; il l'attaque chez les locaux.**

**3. Au point de fonctionnement réel — 10 à 15 dB, l'environnement de l'appelant — le classement est net** : distant 23,8 % · sherpa local 26,3 % · vosk local 36,4 %. Le moteur qui gagnait de loin sur de l'audio propre arrive **dernier**, avec un écart de 12 points.

### La conséquence pour l'arbitrage « local ou distant », qui n'était jusqu'ici qu'une question de coût

L'auto-hébergement coûte, **en plus** de la machine :

- **toute la grammaire française des nombres** (les deux moteurs locaux rendent des mots, le distant rend des chiffres — mesure 9) ;
- **une dégradation qui vise les entités** dès 10 dB (mesure 10), c'est-à-dire exactement les numéros et les montants ;
- et il rapporte, côté calcul, **moins que prévu** : le STT n'était pas le mur (mesure 11).

> **Ce que je retiens, et qui contredit l'ordre de rapatriement écrit dans `docs/00-SYNTHESE` (« LLM → STT → TTS ») : le STT est le dernier poste qu'il faut rapatrier, pas le deuxième.** Il économise 6,50 $ par salon et par mois (`docs/11` §3), et il coûte la fiabilité sur la seule donnée qu'on n'a pas le droit de perdre. **Décision proposée : STT en API, durablement, et non « en phase 1 ».** À rouvrir seulement si un moteur local démontre, sur ce corpus bruité, à la fois une sortie en chiffres et une courbe plate.

⚠️ **Limite** : trois moteurs, un corpus synthétique, une seule voix. Ce qui est solide, c'est **l'écart entre conditions sur le même audio** ; ce qui ne l'est pas, c'est le niveau absolu. La mesure se refait en une commande le jour où un corpus d'appels réels existe.

### Rejouer

```bash
# corpus bruité : bancs/bruit.py ; puis les trois moteurs sur les mêmes fichiers
GROQ_API_KEY=... python3 bancs/wer.py --corpus ~/corpus-bruit/rose-10db
```

---

## Mesure 13 — le TTS est le vrai mur, et il l'est en latence avant de l'être en débit

> Suite directe de la mesure 11 : le STT ne limitait rien, donc le suspect suivant était le TTS. Il l'est, mais pas par où on l'attendait.

### Protocole

K synthèses simultanées **partageant une voix chargée en mémoire**, six phrases d'agent réelles (annonce, confirmation, relance, « d'accord »), 12 s par palier. Cette fois, la mesure se fait **par l'API Python**, qui rend un **flux de fragments** — on mesure donc le délai avant le **premier fragment**, le seul que l'appelant entende.

### Résultats

| Flux | Premier fragment p50 | p90 | RTF/flux | Débit | Mémoire résidente |
|---|---|---|---|---|---|
| 1 | **162 ms** | 226 ms | 0,065 | 15,4 × | 313 Mo |
| 2 | 225 ms | 303 ms | 0,087 | 23,0 × | 465 Mo |
| 3 | 319 ms | 438 ms | 0,126 | 23,7 × | 592 Mo |
| **4** | **394 ms** | 588 ms | 0,167 | 23,9 × | 766 Mo |
| 5 | 486 ms | 690 ms | 0,203 | 24,2 × | 872 Mo |
| 6 | 614 ms | 877 ms | 0,245 | 24,0 × | 873 Mo |

### Quatre enseignements, dont une correction de la mesure 1

**1. Correction : le TTFB de 372 ms n'était pas une propriété du modèle, c'était le binaire.** En passant par l'API en flux, le premier fragment tombe à **162 ms p50** — **sous** les 250 ms visés. La mesure 1 mesurait un exécutable qui synthétise la phrase entière avant d'écrire son fichier. **La règle « la première réplique doit être courte » reste bonne, mais elle cesse d'être une contrainte dure** : ce qu'il faut, c'est appeler le moteur en flux, pas raccourcir les phrases.

**2. Le TTS limite en latence, pas en débit.** Le RTF reste ridicule (0,245 à six flux) et le débit sature à 24 × le temps réel, exactement comme le STT. Mais **le premier fragment, lui, se dégrade linéairement** : 162 ms à un flux, 394 ms à quatre, 614 ms à six. Le STT ne faisait pas ça. **La capacité d'une machine ne se lit donc pas sur son RTF, mais sur le délai avant le premier son.**

**3. La mémoire par appel, c'est le TTS.** +150 Mo par flux jusqu'à quatre (313 → 766 Mo), puis un plateau vers 870 Mo. La ligne « 150 à 320 Mo par appel » du chiffrage, que la mesure 11 avait retirée au STT (11 Mo), **se retrouve ici, presque au chiffre près**. Le compte est bon, mais il change de poste — et donc de levier : c'est le TTS qu'il faudra mutualiser ou borner.

**4. Le dimensionnement réel, en tenant le budget de latence.** Si l'on refuse de dépasser ~400 ms avant le premier son, la machine soutient **quatre synthèses simultanées**, pas plus. Mais un agent ne parle qu'une fraction du temps d'un appel — l'ordre de grandeur usuel est 40 % —, donc **quatre synthèses simultanées correspondent à une dizaine d'appels en cours**. C'est le premier chiffre de capacité du projet qui repose sur une mesure et non sur une estimation.

### Deux règles de conception

1. **Borner le nombre de synthèses simultanées** (file d'attente à parallélisme fixe, de l'ordre de 4 sur une machine à 4 cœurs) plutôt que de laisser tous les appels synthétiser en même temps. Sans borne, le dixième appel dégrade les neuf autres ; avec borne, il attend quelques dizaines de millisecondes et personne ne s'en aperçoit.
2. **Surveiller le délai avant premier fragment comme métrique de production**, au même titre que le taux de confirmation orpheline. C'est lui qui dira qu'une machine est pleine — bien avant la charge processeur, qui restera basse jusqu'au bout.

### Rejouer

```bash
cd bancs && PYTHONPATH=. ~/bancs-stt/bin/python charge_tts.py --max 6 --duree 12
```

---

## Mesure 14 — le tour de parole complet, et ce qu'un agent « prompt seul » raconte à un client

> Les mesures 11 et 13 donnaient les étages séparément. Celle-ci les enchaîne : **STT local streaming → LLM distant sur connexion gardée → TTS en flux**, sur douze énoncés réels du corpus en 8 kHz. Ce que l'appelant perçoit n'est aucun des trois, c'est leur somme.

### Le budget de silence

| Étage | p50 | p90 |
|---|---|---|
| STT (finalisation) | 168 ms | 199 ms |
| **LLM (premier token)** | **165 ms** | **935 ms** |
| TTS (premier fragment) | 249 ms | 378 ms |
| **Total perçu** | **624 ms** | **1 498 ms** |

**Lecture** : le tour médian tient largement dans ce qu'un humain accepte au téléphone (~800 ms). **Toute la variance vient du LLM** — 165 ms en médiane, 935 ms au neuvième décile, jusqu'à 2 401 ms sur un tour. Les deux étages locaux, eux, sont stables à ±30 ms. **Le contrat de service ne se joue donc pas sur la machine mais sur le fournisseur de LLM**, ce qui confirme le déplacement du mur annoncé par la mesure 11, et rend obligatoire ce qui n'était qu'une bonne idée : un **délai de garde** au-delà duquel l'agent dit quelque chose (« je vérifie ») plutôt que de laisser le silence s'installer.

### Et maintenant la partie dérangeante

Le même banc produit les réponses réellement générées. **Douze tours, sans machine à états, sans outil, avec le seul prompt système** — c'est-à-dire exactement l'architecture que tout le monde démontre en vidéo. Classification à la main :

| Énoncé de l'appelant | Ce que le STT a rendu | Ce que l'agent a répondu | Faute |
|---|---|---|---|
| « Samedi **neuf heures moins le quart** » | « SAMEDI NEUF HEURES **MOIS** LE QUART » | « Je vous propose le samedi à **9 h 15** » | **Créneau inventé**, et faux (8 h 45) |
| « Le premier du mois prochain » | correct | « Le premier du mois prochain **est un dimanche**, jour de fermeture » | **Fait inventé** — l'agent n'a aucune date |
| « Mardi dix-sept à dix-huit heures quinze » | correct | « **C'est noté**, souhaitez-vous confirmer ? » | **Confirmation orpheline** — rien n'est écrit nulle part |
| « Je dois annuler mon rendez-vous de demain matin » | correct | « **C'est noté, votre rendez-vous de demain matin est annulé** » | **Confirmation orpheline grave** — le client va s'organiser là-dessus |
| « Jeudi prochain vers quinze heures trente » | « **JE DIS** PROCHAIN » (jour perdu) | « Je vous propose un créneau à 15 h 30 » | Le jour manquant est **comblé en silence** |
| « Plutôt demain **en fin d'après-midi** » | transcription cassée | « Souhaitez-vous un créneau **à 14 h** ? » | Proposition sans rapport, donnée avec aplomb |

**Six tours sur douze portent une faute, dont deux confirmations orphelines et trois inventions.** Et aucune n'est signalée : l'agent ne dit jamais « je n'ai pas compris ». Il comble.

### Ce que ça démontre, et qui n'était jusqu'ici qu'un principe

`docs/15-RIGUEUR-EXECUTION.md` pose que **« le modèle propose, la machine à états dispose »**. Cette mesure en donne la preuve empirique au premier essai, sans avoir cherché à piéger le modèle :

1. **Un modèle comble toujours un trou de transcription**, il ne le signale pas. Donc la **relecture obligatoire** des entités (`docs/10`) n'est pas une politesse, c'est le seul endroit où l'erreur devient visible.
2. **« C'est noté » doit être interdit au modèle.** Cette phrase ne peut être prononcée que par la machine, **après** un `read-after-write` réussi (`docs/04` §C2.3). Un prompt qui l'autorise produit une confirmation orpheline dès le quatrième tour — mesuré.
3. **Aucune date ne doit venir du modèle.** Le jour de la semaine, les fermetures, les créneaux : tout cela se calcule côté machine et s'injecte. Le modèle qui décide qu'un premier du mois « est un dimanche » le fait avec le même aplomb qu'une information vraie.
4. **Le taux de faute d'un agent « prompt seul » est de l'ordre de 50 %** sur des demandes ordinaires. C'est l'écart entre une démonstration et un produit, et il est maintenant chiffré.

⚠️ **Limites** : douze tours, un modèle gratuit de petite taille, aucun outil branché, classification à la main. Le taux exact n'est pas le résultat — **le mode d'échec l'est**, et il est systématique.

### Rejouer

```bash
GROQ_API_KEY=... cd bancs && PYTHONPATH=. ~/bancs-stt/bin/python tour_complet.py
```

---

## Mesure 15 — les mêmes tours avec les garde-fous : le mensonge disparaît, l'utilité aussi

> Suite immédiate de la mesure 14. Mêmes énoncés, même STT, même modèle — mais l'architecture de `docs/15` : le modèle **ne rédige plus rien**, il rend une proposition structurée ; le calendrier est **injecté** et calculé par la machine ; toute entité douteuse devient une **question** ; c'est la machine qui compose la phrase.

### Résultats, sur les dix tours qui ont abouti

| | Prompt seul (mesure 14) | **Avec garde-fous** |
|---|---|---|
| Confirmations orphelines | **2** | **0** |
| Faits calendaires inventés | 1 | **0** |
| Heures inventées **dites au client** | 3 | **0** |
| Heures inventées **par le modèle** | — | 1, **interceptée par la validation d'agenda** |
| Tours aboutissant à une réservation | (aucune n'était réelle) | **0** |
| Questions de clarification | 0 | **7** |
| Refus argumentés | 0 | 3 |

### Trois lectures, dont une qui n'est pas confortable

**1. La partie « ne pas mentir » est réglée, et elle l'est par construction.** Zéro confirmation orpheline, zéro date inventée — non pas parce que le modèle s'est amélioré, mais parce qu'**il n'a plus la parole**. La seule invention qu'il ait tentée (une heure absente de la transcription) a été **arrêtée par la validation contre l'agenda**. C'est exactement ce que la validation est censée faire, et elle l'a fait au premier essai.

**2. Mais l'agent est devenu inutile sur ce corpus : zéro réservation.** Sept tours sur dix finissent en question de clarification. La cause n'est pas l'architecture, elle est en amont : **les transcriptions du moteur local sont trop abîmées** pour porter une date et une heure (mesures 9 et 10). Un agent rigoureux branché sur un STT médiocre ne ment plus — il fait répéter. **C'est un argument de plus, et mesuré, pour le STT distant** (mesure 12).

> **Ce qu'il faut retenir pour la conception** : la rigueur ne remplace pas la qualité d'écoute, elle la révèle. Les deux chantiers sont distincts et tous les deux obligatoires — sans garde-fous l'agent invente, sans bon STT il fait répéter, et un client raccroche dans les deux cas.

**3. Un piège trouvé au premier essai, et qui aurait fait mentir la machine à son tour.** Ma première version confondait **« absent de l'agenda »** et **« fermé »** : « le premier du mois prochain » et « le vingt-quatre décembre » tombaient hors de l'horizon de quatorze jours, et l'agent répondait « nous sommes fermés ce jour-là » — **faux, et invérifiable par le client**. Corrigé : trois réponses distinctes, **hors horizon** (« je ne prends pas encore les rendez-vous aussi loin »), **fermé** (jour non ouvré, vérifié), **incompris** (date non reconnue). La leçon est générale : **dans une machine à états, toute absence de donnée doit avoir sa propre réponse** — sinon elle se fait passer pour une information.

⚠️ **Limite de la mesure** : dix tours sur douze ont abouti à la première exécution ; la seconde, faite pour valider la correction ci-dessus, s'est arrêtée après quatre tours sur le **plafond de jetons par minute du palier gratuit** (déjà rencontré à la mesure 4). Les chiffres du tableau viennent donc de la première exécution, et la correction n'est vérifiée que sur quatre tours.

### Rejouer

```bash
GROQ_API_KEY=... cd bancs && PYTHONPATH=. ~/bancs-stt/bin/python tour_garde.py
```

---

## Mesure 16 — la boucle de clarification ferme, et elle coûte deux tours

> La mesure 15 laissait l'agent honnête mais muet : sept demandes de précision sur dix. Restait la question qui décide de l'utilisabilité — **quand l'agent demande une précision, l'obtient-il ?**

### Protocole

L'appelant est simulé, mais **ses réponses passent par la même chaîne que le reste** : elles sont synthétisées, dégradées en 8 kHz µ-law aller-retour, puis retranscrites par le moteur local. Une réponse de clarification est donc aussi abîmée que la demande initiale — un banc qui rendrait du texte parfait au deuxième tour mesurerait une conversation qui n'existe pas. Quatre tours au maximum, dix scénarios.

### Résultats

| | |
|---|---|
| Scénarios menés | 10 |
| **Aboutis à un créneau valide** | **9** |
| **Tours nécessaires, en moyenne** | **2,2** |
| Abandons après quatre tours | 1 |

**Lecture : la rigueur coûte environ un tour de parole supplémentaire, pas une conversation.** L'agent qui « fait répéter » de la mesure 15 obtient sa réponse au tour suivant dans neuf cas sur dix. Avec un tour médian de 624 ms (mesure 14), **un tour de plus, c'est moins d'une seconde de conversation** — le prix est dérisoire au regard de ce qu'il achète : zéro confirmation orpheline.

### L'échec est plus instructif que les neuf réussites

Le seul abandon révèle **un défaut de conception de la machine à états**, pas du modèle. Déroulé réel :

| Tour | Ce que l'appelant dit | Ce que la machine répond |
|---|---|---|
| 1 | « mardi dix-sept à **dix-huit heures quinze** » | « Ce créneau n'est pas libre. Il reste 09:00, 09:45, 10:30. » |
| 2 | « vendredi, à **la même heure** » | « Ce créneau n'est pas libre. Il reste 09:00, 09:45, 10:30. » |
| 3 | idem | idem |
| 4 | idem | idem |

**La machine avait retenu `18:15` avec une confiance de 1,0 et ne l'a plus jamais remise en cause.** Le jour changeait, l'heure restait, le refus se répétait à l'identique. C'est une boucle infinie polie — le pire mode d'échec possible au téléphone, parce que l'appelant n'a aucun moyen de comprendre d'où vient le blocage.

> **Règle qui manquait à `docs/15-RIGUEUR-EXECUTION.md` : une valeur retenue doit pouvoir être oubliée.** Concrètement : **deux refus consécutifs portant sur la même entité l'invalident**, la machine la vide et la redemande explicitement (« à quelle heure, parmi 9 h, 9 h 45, 10 h 30 ? »). Et **aucune réponse de l'agent ne doit être identique à la précédente** : si la machine s'apprête à redire mot pour mot ce qu'elle vient de dire, c'est qu'elle boucle — il faut changer de stratégie ou passer la main.

### Ce que cette mesure ne dit pas

Les réponses de l'appelant sont **scriptées et coopératives** (« jeudi », « quinze heures trente »). Elle mesure donc **la mécanique de la boucle**, pas la fidélité à l'intention : un vrai appelant qui tient à son samedi 8 h 45 n'accepterait pas le jeudi 15 h 30. Le chiffre à retenir est **« la boucle ferme en 2,2 tours quand l'appelant est souple »**, et la question ouverte reste le client qui ne l'est pas.

### Rejouer

```bash
GROQ_API_KEY=... cd bancs && PYTHONPATH=. ~/bancs-stt/bin/python boucle_clarification.py
```

---

## Mesure 17 — l'appelant qui n'est pas coopératif, et comment il déjoue les deux garde-fous

> La mesure 16 mesurait une boucle avec un appelant souple. Celle-ci fait l'inverse : quelqu'un qui tient à un créneau indisponible (samedi 18 h 30), se répète, s'agace. Les deux règles nées de la mesure 16 sont implémentées dans le banc — oublier une entité refusée deux fois de suite, ne jamais répéter une phrase mot pour mot — plus le transfert immédiat sur demande explicite d'un humain.

### Résultats, trois variantes d'appelant

| Appelant | Issue | Tours |
|---|---|---|
| **A** — insiste deux fois puis cède | **transfert décidé par la machine** | 2 |
| **B** — insiste jusqu'au bout, sans jamais demander d'humain | **boucle, jusqu'au plafond de six tours** | 6 |
| **C** — demande explicitement un humain | **transfert immédiat** | 2 |

### Ce que ça apprend

**1. Le transfert sur demande explicite fonctionne, et il doit rester en amont de tout.** Détecté sur la transcription, avant même d'appeler le modèle : « passez-moi quelqu'un » n'a pas à être interprété, il a à être exécuté. Deux tours, dont un seul de politesse. C'est la garantie que `docs/14` appelle N4 et elle tient.

**2. Les deux garde-fous se laissent déjouer par l'alternance.** Déroulé de l'appelant B :

| Tour | Réponse de la machine |
|---|---|
| 1 | question — « quelle heure préférez-vous ? » |
| 2 | question — « je n'ai pas bien saisi » |
| 3 | **refus** — « ce créneau n'est pas libre » |
| 4 | question — « je n'ai pas bien saisi » |
| 5 | **refus** — « ce créneau n'est pas libre » |
| 6 | question — « quelle heure préférez-vous ? » |

Jamais **deux refus consécutifs** (donc la règle d'oubli ne se déclenche pas), jamais **deux phrases identiques d'affilée** (donc la règle anti-répétition non plus). **Les deux garde-fous sont locaux ; l'échec, lui, est global.** Six tours, aucun progrès, et la machine aurait continué.

> **Troisième règle, qui manquait : un compteur de progrès.** La machine compte les tours **depuis la dernière entité nouvellement validée**. Au-delà de **trois**, elle passe la main, quoi qu'aient dit les règles locales. C'est la seule qui attrape l'alternance, parce qu'elle ne regarde pas les phrases mais **l'avancement**.

**3. Et la règle anti-répétition transfère parfois trop tôt.** L'appelant A allait céder au troisième tour ; la machine l'a transféré au deuxième. Ce n'est pas grave — un transfert coûte moins cher qu'une boucle — mais ça se paie en appels remontés vers le salon, donc en promesse commerciale. **Le réglage juste n'est pas « deux » dans l'absolu** : c'est deux pour une entité refusée, trois pour l'absence de progrès, et immédiat pour une demande d'humain.

### Le catalogue a encore bougé pendant la mesure

Le modèle utilisé depuis hier, `qwen/qwen3.6-27b`, **a disparu du catalogue en cours de nuit** (`model_not_found`) ; `qwen/qwen3.8-27b`, disparu la veille, **est réapparu**. Troisième mouvement en quarante-huit heures. Et le modèle de remplacement **refuse un paramètre que l'autre acceptait** (`reasoning_effort: "none"` → « must be one of low, medium, high »).

> **Conséquence, qui vient s'ajouter à la règle « le nom du modèle vit en configuration » : les paramètres d'appel aussi.** Un pipeline qui code en dur un paramètre propre à un modèle tombe le jour où ce modèle s'en va. Et l'erreur doit être lisible : mon banc avalait un `KeyError: 'choices'` là où le fournisseur disait exactement ce qui n'allait pas — trois quarts d'heure perdus sur un message qui était disponible dès la première requête.

### Rejouer

```bash
GROQ_API_KEY=... cd bancs && PYTHONPATH=. ~/bancs-stt/bin/python appelant_tetu.py
```

---

## Mesure 18 — l'escalade graduée, et trois définitions du mot « progrès » avant la bonne

> La mesure 17 laissait deux défauts : l'appelant têtu bouclait six tours, et celui qui allait céder était transféré trop tôt. Cette mesure corrige les deux et donne les réglages retenus.

### Ce qui a changé dans la machine

1. **Se répéter ne veut pas dire abandonner.** À la première répétition, la machine **change de stratégie** — une seule entité à la fois, avec des choix explicites énoncés (« dites-moi seulement l'heure, par exemple 9 h, 9 h 45 ou 10 h 30 »). Elle ne passe la main qu'à la deuxième.
2. **Le compteur de progrès déclenche à deux tours consécutifs sans progrès**, pas trois : au téléphone, deux tours stériles, c'est déjà long.

### Résultat, mêmes trois appelants

| Appelant | Mesure 17 | **Mesure 18** |
|---|---|---|
| insiste deux fois puis cède | transfert au tour 2 | **rendez-vous pris au tour 3** |
| insiste jusqu'au bout | boucle, 6 tours | **transfert au tour 5** |
| demande un humain | transfert au tour 2 | transfert au tour 2 |

**La reformulation sauve l'appel** : l'appelant A, transféré la veille, obtient son créneau — parce que la machine a cessé de reposer la même question et a énoncé les possibilités.

### Le vrai travail de cette mesure : définir « progrès »

Le compteur n'a fonctionné qu'à la **troisième** définition, et les deux premières échouaient en silence — c'est-à-dire de la pire façon.

| Définition essayée | Pourquoi elle échoue |
|---|---|
| « le couple (date, heure) a changé » | La règle d'oubli **vide** une entité : le couple change, donc c'est compté comme un progrès. **Oublier n'est pas avancer**, et le compteur repartait à zéro à chaque oubli. |
| « une entité est passée de vide à remplie » | L'appelant répète la même phrase, le modèle en ré-extrait la même heure, l'entité repasse de vide à remplie **à chaque tour**. Compteur inopérant. |
| ✅ **« une entité a pris une valeur jamais essayée »** | Seule définition qui résiste : la machine tient la liste des valeurs déjà tentées pour chaque entité, et ne compte comme progrès que ce qui est neuf. |

> **Règle à écrire dans le code du jour où il s'écrira** : un compteur d'anti-boucle ne compte pas des tours, ni des changements — **il compte des valeurs neuves**. Toute autre définition se laisse déjouer par un interlocuteur qui se répète, et l'échec est silencieux : la machine croit avancer.

### Réglages retenus, tous mesurés

| Déclencheur | Seuil | Effet |
|---|---|---|
| Demande explicite d'un humain | **immédiat**, détecté sur la transcription **avant** l'appel au modèle | transfert |
| Même entité refusée | **2 fois de suite** | l'entité est oubliée et redemandée avec ses valeurs possibles |
| Phrase identique à la précédente | **1ʳᵉ fois** | changement de stratégie (choix explicites, une entité à la fois) |
| Phrase identique à la précédente | **2ᵉ fois** | transfert |
| Tours sans valeur neuve | **2** | transfert |

### Rejouer

```bash
GROQ_API_KEY=... cd bancs && PYTHONPATH=. ~/bancs-stt/bin/python appelant_tetu.py
```

---

## Mesure 19 — ce que l'agent dit survit-il au canal ? (et l'annonce légale, elle, passe-t-elle ?)

> Tout le reste du dossier mesure ce que l'agent **entend**. Personne n'avait mesuré ce que l'appelant **reçoit** — alors que deux choses en dépendent : l'annonce « assistant automatique » (AI Act art. 50 §1), qui doit être **comprise** et pas seulement prononcée, et la relecture du numéro par groupes de deux, notre seul filet contre le mauvais SMS.

### Protocole

Dix phrases réelles d'agent, synthétisées, passées par le canal (**8 kHz µ-law aller-retour**), puis retranscrites par deux moteurs indépendants. Le transcripteur joue le rôle de l'oreille de l'appelant : ce n'est pas un humain, mais **un mot que deux moteurs ne retrouvent pas est un mot que le canal a abîmé**.

### Résultat principal : la parole de l'agent tient très bien

| Phrase | Ce que le canal en fait |
|---|---|
| **Annonce légale** | « Je suis un **assistant automatique** » → retrouvé **intact par les deux moteurs** (l'un écrit « assistante », le genre change, le sens non) |
| **Relecture du numéro** | « zéro six, douze, trente-quatre, cinquante-six, soixante-dix-huit » → **les dix chiffres retrouvés**, dans les deux bandes et par les deux moteurs |
| Transfert, prix, refus | intacts |

**L'annonce obligatoire n'est pas menacée par le canal, et le filet de relecture du numéro tient.** C'est la première vérification de conformité faite sur l'audio réel plutôt que sur le texte du prompt.

### Les deux fragilités réelles, et ce qu'elles imposent

**1. Le quantième de la date est le mot le plus fragile de tout ce que l'agent dit.**
« jeudi **dix-sept** à quinze heures trente » devient « jeudi **dix** » sur un moteur et « jeudi d'y séa » sur l'autre — **raté deux fois sur deux**, alors que le jour de la semaine et l'heure passent parfaitement.

> **Règle** : la date s'énonce toujours **jour de la semaine + quantième + mois** (« jeudi dix-sept septembre »), et **aucune confirmation ne repose sur le seul quantième**. La redondance du jour de la semaine est ce qui permet au client de détecter l'erreur.

**2. Deux créneaux proches énoncés d'affilée fusionnent.**
« Il me reste **neuf heures, neuf heures quarante-cinq**, ou dix heures trente » est revenu en « de vers neuf heures quarante-cinq ou dix heures trente » : **la première option a disparu**.

> **Règle** : ne jamais énoncer deux horaires séparés de moins d'une heure dans la même phrase. Deux options **espacées**, et la troisième seulement si le client la demande. Ça contredit l'idée intuitive de « donner le plus de choix possible » — au téléphone, le choix se paie en intelligibilité.

### Un rappel de méthode, pour la troisième fois

Le moteur distant affiche ici des WER de 35 à 85 % sur les phrases qui contiennent des nombres — **et il n'a rien perdu du tout** : il écrit `06 12 34 56 78` là où la référence écrit « zéro six, douze… ». **Le WER continue de mesurer l'orthographe, pas la compréhension.** C'est la troisième mesure du dossier où il faut le rappeler (voir 7, 8, 9) ; la métrique qui décide reste le **taux de retrouvaille des mots-clés**, calculé ici en comparant chiffres à chiffres et mots à mots.

### Rejouer

```bash
GROQ_API_KEY=... cd bancs && PYTHONPATH=. ~/bancs-stt/bin/python agent_audible.py
```

---

## Mesure 20 — dix appels parlent en même temps : le fournisseur tient, mais son temps de réponse ne veut rien dire

### Résultats — K requêtes lancées ensemble, connexion neuve pour chacune

| Simultanées | Servies | Refusées | TTFT p50 | TTFT max |
|---|---|---|---|---|
| 1 | 1 | 0 | **6 200 ms** | 6 200 ms |
| 2 | 2 | 0 | 2 395 ms | 2 489 ms |
| 4 | 4 | 0 | 2 015 ms | 2 189 ms |
| 6 | 6 | 0 | 1 404 ms | 1 422 ms |
| 8 | 8 | 0 | 4 943 ms | **8 751 ms** |
| 10 | 10 | 0 | 1 665 ms | 1 998 ms |

### Trois lectures

**1. La simultanéité n'est pas le problème.** Dix requêtes lancées ensemble, **aucun refus**, et le TTFT à dix (1 665 ms) est meilleur qu'à un (6 200 ms). Le palier gratuit ne bronche pas sur dix appels concurrents — ce qui, rapporté à la capacité machine de la mesure 13 (~10 appels simultanés), veut dire que **le fournisseur n'est pas le goulot de capacité**.

**2. Mais son temps de réponse ne se prédit pas.** De 1 404 ms à 8 751 ms sans rapport avec la charge. Le premier appel à 6 200 ms est la signature du démarrage à froid déjà mesuré (mesure 4 : DNS + TCP + TLS), les autres pics n'ont aucune explication visible de notre côté. **Un fournisseur distant est une variable aléatoire bornée par le haut, pas un service à latence garantie.**

**3. Donc la conception doit absorber, pas espérer.** Trois mécanismes, tous obligatoires et tous déjà nommés ailleurs dans le dossier — cette mesure les rend non négociables :
- **connexions ouvertes d'avance et maintenues** (mesure 4) : elles suppriment le pire cas, celui du démarrage à froid ;
- **délai de garde** : au-delà de ~700 ms sans premier token, l'agent dit « je vérifie » — la mesure 14 donnait 935 ms au p90, celle-ci 8 751 ms au pire, le silence n'est donc pas une hypothèse d'école ;
- **un second fournisseur en repli**, choisi le jour où la latence du premier sort de ses clous, et **dont le nom comme les paramètres vivent en configuration** (mesure 17 : le catalogue a bougé trois fois en 48 h).

⚠️ **Limite** : palier gratuit, un seul fournisseur, requêtes courtes. Ce qui se transpose, c'est **la forme** — aucune corrélation entre concurrence et latence, et une dispersion d'un facteur six. Pas les valeurs.

---

## Mesure 21 — les sept numéros difficiles, vus par les trois moteurs

> Les règles T8, T9 et T10 de `docs/10` sont nées des échecs de la mesure 7. Restait à vérifier qu'elles sont **implémentables** : la transcription contient-elle encore l'information nécessaire pour réparer ? Sept énoncés fabriqués exprès, passés en 8 kHz, transcrits par les trois moteurs.

### Ce que chaque moteur rend

| Cas | Moteur distant (écrit des chiffres) | Moteurs locaux (écrivent des mots) |
|---|---|---|
| **T8** « zéro un **quarante-trois** vingt-deux onze zéro neuf » | `01 40 3 22 11 09` — **11 chiffres**, composé coupé | « quarante-trois » **intact** |
| **T9** « douze, quatorze, **non**, quinze… » | `06 12 14 **non** 15 40 60` | « non » **conservé** par les deux |
| **T9 bis** « zéro six, **pardon**, zéro sept… » | `06, **pardon**, 07, 12, 34…` | « pardon » **conservé** par les deux |
| **T5** « **plus trente-trois** six douze… » | `plus 33 6 12 34 56 78` | « plus trente-trois » puis dégradation |
| **T1** « **zéro huit** douze… » | `0 8 12 34 56` | correct chez les deux |
| **T4** « zéro neuf soixante-dix zéro zéro… » | `0970 0092` — **chiffres perdus** | perdus aussi, autrement |

### Trois enseignements, dont un qui change une règle

**1. La sur-segmentation est un défaut du moteur, pas de la langue.** « quarante-trois » n'est coupé en « 40 3 » **que par le moteur qui écrit des chiffres** ; les deux moteurs qui écrivent des mots le rendent intact. **T8 ne concerne donc que les moteurs à sortie numérique** — c'est-à-dire précisément celui qu'on a retenu. La règle reste, et sa portée est maintenant connue.

**2. Les marqueurs de correction survivent chez les trois.** « non » et « pardon » sont transcrits par tout le monde, dans les deux bandes. **T9 est implémentable sans réserve** : l'information est toujours là, c'est l'interprétation qui manquait.

**3. Et voici ce qui change une règle : le moteur distant tranche les ambiguïtés en silence.** « quatre-vingts douze » — qui peut valoir `92` ou `80 12` — ressort en `06 92 03 44`. Il a **choisi**, sans le dire. Les moteurs à sortie en mots, eux, rendent « quatre-vingt-douze » et laissent la question ouverte.

> **Conséquence** : en choisissant un moteur qui écrit des chiffres, **on lui délègue une part du parsing — donc une part des erreurs de parsing, prises en silence et sans trace.** T10 (« ne jamais trancher une ambiguïté sans le dire ») **ne peut pas être appliquée en aval d'un tel moteur** : l'ambiguïté a déjà disparu de l'entrée.
>
> **La relecture du numéro devient donc inconditionnelle**, et non plus « en cas de doute ». Il n'y a plus de doute observable : c'est précisément le problème. La mesure 19 a déjà montré que cette relecture survit au canal — elle est notre seul filet, et elle doit être systématique.

### Une limite du banc, à dire clairement

Le cas T10 n'est **pas observable sur ce corpus** : la voix de synthèse prononce « quatre-vingts douze » comme un `92`, donc l'ambiguïté disparaît **avant** le moteur. De même, le cas T4 a été rendu ambigu par la synthèse elle-même (« quatre-vingt-un douze » entendu « quatre-vingt-douze » par les trois). **Un corpus synthétique ne peut pas tester une ambiguïté de prononciation** — il faut une voix humaine. Dette de mesure déclarée, à lever avec le premier corpus réel.

---

## Mesure 22 — laquelle des deux voix licenciées embarquer ?

> Tout le dossier a été mesuré avec `fr_FR-siwis-medium` sans jamais la comparer. Or les deux voix françaises utilisables commercialement (CC-BY 4.0) ne se valent pas, et le choix décide de deux choses mesurées ailleurs : le délai avant le premier son (mesure 13) et ce que l'appelant comprend après le canal (mesure 19).

### Résultats — dix phrases d'agent, trois passages, puis passage en 8 kHz µ-law

| Voix | Premier fragment p50 | p90 | RTF | **WER après canal (moteur local)** | Mots-clés perdus |
|---|---|---|---|---|---|
| **`siwis`** | 256 ms | 422 ms | 0,071 | **6,4 %** | 3 |
| `mls` | 280 ms | 415 ms | 0,070 | **20,0 %** | 4 |

*(Les « mots-clés perdus » sur les numéros sont, pour les deux voix, l'artefact chiffres/mots déjà signalé aux mesures 7, 8, 9 et 19 — les dix chiffres sont bien là, écrits en lettres.)*

### Le cas qui tranche : l'annonce légale

Même phrase, même canal, deux voix :

| Voix | Ce que le moteur en comprend |
|---|---|
| `siwis` | « bonjour vous êtes bien au salon élégance **je suis un assistant automatique** » |
| `mls` | « j'en viens au salon élégant **suzanne** assistant automatique » |

**Chez `mls`, « je suis un » devient « suzanne ».** L'annonce reste à moitié reconnaissable, mais la phrase d'ouverture — celle qui porte l'obligation de l'AI Act et la première impression — part en bouillie. **Trois fois plus d'erreurs après le canal, pour une latence identique.**

> **Décision : `fr_FR-siwis-medium` reste la voix embarquée par défaut**, et `mls` n'est qu'un repli licencié si un problème survenait sur la première. Ce qui n'était jusqu'ici qu'un choix par défaut est maintenant un choix mesuré.

### Ce que ça apprend au-delà de ce projet

**Une voix de synthèse se choisit sur ce qu'elle devient après le canal, pas sur son rendu en studio.** Les deux voix ont le même RTF et la même latence ; en large bande, `mls` passe souvent pour la plus naturelle. Après un aller-retour µ-law à 8 kHz, elle perd trois fois plus. **La bande étroite ne dégrade pas toutes les voix de la même façon, et rien dans leur fiche ne le dit.**

### Rejouer

```bash
GROQ_API_KEY=... cd bancs && PYTHONPATH=. ~/bancs-stt/bin/python voix.py
```

---

## Mesure 23 — notre prompt fait 854 jetons, le seuil de cache est à 4 096

> La recherche (A1) avait établi qu'en dessous de **4 096 jetons de préfixe, rien n'est mis en cache** — d'où la doctrine écrite dans `00-SYNTHESE` : « on n'élague pas le fichier de connaissance, on le calibre au-dessus du seuil ». Restait à savoir où se situe le nôtre. Personne ne l'avait compté.

### Méthode

Composer le `memoire.md` **réel** d'un salon à partir du pack coiffure et de données plausibles (horaires, coupure, cinq prestations avec durées et prix, trois praticiens, huit paragraphes de particularités), l'envoyer comme prompt système avec `max_tokens=1`, et lire le `usage.prompt_tokens` renvoyé par le fournisseur. **C'est le seul compte exact.**

### Résultats

| Morceau | Jetons | Caractères | Caractères par jeton |
|---|---|---|---|
| Consignes de l'agent | 147 | 289 | 1,97 |
| **`memoire.md` d'un salon** | **782** | 2 420 | 3,09 |
| **Prompt complet** | **854** | 2 709 | 3,17 |

### Deux résultats, dont un qui corrige une doctrine

**1. La règle de pouce « quatre caractères par jeton » est fausse en français** : on mesure **3,1**, soit **30 % de jetons en plus** que l'estimation courante. Toute prévision de coût faite à la louche sous-estime donc d'un tiers. (Mes propres bancs utilisaient cette approximation pour fabriquer un prompt « long » — ils visaient 5 000 jetons et en produisaient davantage.)

**2. Le seuil de cache n'est pas atteignable par un salon, et il ne doit pas l'être.** Il manque **3 242 jetons**, soit environ **10 000 caractères** — près de **cinq fois** le fichier actuel. Aucun salon n'a dix mille caractères de particularités vraies à raconter. **Calibrer le fichier au-dessus du seuil reviendrait à le rembourrer**, c'est-à-dire à payer plus cher un texte qui n'apprend rien au modèle et qui dilue ce qui compte.

> **Correction de doctrine.** Ce n'est pas le fichier du salon qu'il faut allonger, c'est **l'ordre du prompt** qu'il faut inverser : **du plus partagé au plus spécifique.**
>
> ```
> [ consignes communes, grammaire, protocole, exemples ]  ← identique pour TOUS les salons
> [ memoire.md du salon ]                                 ← ~800 jetons
> [ variables du tour : calendrier, etat, transcription ] ← apres la coupure de cache
> ```
>
> Le préfixe long et stable devient alors **commun à toute la flotte** : il est mis en cache une fois et touché par tous les appels de tous les locataires, au lieu d'être recalculé salon par salon sans jamais franchir le seuil. **Et ce bloc commun, nous avons déjà de quoi l'écrire honnêtement** — la grammaire française des nombres, les règles d'énonciation, les patrons de refus, les exemples tirés des mesures 14 à 21 font largement les 4 096 jetons, et chacun de ces jetons sert à quelque chose.

**Ce qui reste non mesuré** : le **gain réel** du cache, qui exige une clé payante (le palier gratuit plafonne à 8 000 jetons/minute). Mais ce qu'il fallait savoir pour concevoir, on le sait : **l'ordre du prompt est un choix d'architecture, pas un détail de mise en forme.**

### Rejouer

```bash
GROQ_API_KEY=... cd bancs && PYTHONPATH=. ~/bancs-stt/bin/python taille_memoire.py
```

---

## Mesure 24 — la latence réelle d'un tour, moteurs locaux (21/09)

Neuf tours joués contre le serveur complet, voix synthétisée dégradée en 8 kHz,
transcription `sherpa-onnx` locale, synthèse Piper — les mêmes moteurs que le
banc d'appel réel, sur le poste de travail.

| Étape | p50 | p95 |
|---|---|---|
| Transcription | **184 à 270 ms** | 382 à 449 ms |
| Décision de l'agent | **1 à 3 ms** | 3 à 7 ms |
| Premier fragment de synthèse | **227 à 271 ms** | 325 à 353 ms |
| **Total, fin de parole → premier son** | **472 à 532 ms** | **765 à 969 ms** |

> Deux passages, neuf tours chacun : les fourchettes sont l'écart entre les deux.
> Sur une machine de bureau qui fait autre chose en même temps, c'est l'ordre de
> grandeur qui compte, pas la troisième décimale.

**Ce que ces chiffres disent :**

1. **Le modèle n'est pas le coupable ici** : 1 à 3 ms. Toute la latence est dans les
   deux moteurs, à parts presque égales. C'est l'inverse de la mesure 14, où la
   variance venait entièrement du fournisseur distant — parce qu'ici il n'y a pas
   de fournisseur : le repli hors ligne décide seul.
2. **Le seuil de Doherty (400 ms) n'est pas tenu en p50** sur cette machine.
   L'appelant perçoit en plus le silence de fin de tour (700 ms, mesure 8) :
   environ **1,2 s** entre sa dernière syllabe et la première de l'agent.
3. **C'est le deuxième argument pour le moteur distant**, après le taux d'erreur
   (mesure 20) : la transcription locale coûte 184 ms de plus qu'un moteur en
   flux, qui rend son texte pendant que l'appelant parle encore.

### Ce que cette mesure a d'abord révélé

Le compteur `premier_fragment_ms` affichait **zéro sur les neuf tours**. Il
lisait la file d'attente, pas la synthèse : quand des paquets de la phrase
précédente restaient à jouer, `emettre` les rendait sans toucher au moteur et le
chronomètre ne mesurait rien. L'indicateur de la mesure 13 — celui qui dit
qu'une machine est pleine **avant** que la charge processeur ne bouge — était
faux depuis qu'il existait.

### Rejouer

```bash
.venv/bin/python bancs/latence.py
```

---

## Mesure 25 — ce que le standard occupe en mémoire (21/09)

Quatorze appels joués contre le serveur complet, sur le poste de travail, en
lisant la RSS **courante** (`/proc/self/statm`) et non le pic.

| Configuration | Au chargement des moteurs | Pic | Oscille ensuite entre |
|---|---|---|---|
| Moteurs locaux (sherpa + Piper) | 329 Mo | **620 Mo** | 473 et 619 Mo |
| Transcription distante (Piper seul) | 145 Mo | **432 Mo** | 363 et 432 Mo |

**Ce que ces chiffres décident :**

1. **Pas de fuite.** La RSS monte jusqu'au sixième appel, puis **redescend** —
   473 Mo au douzième après 619 au dixième. C'est l'allocateur qui garde ses
   arènes et les rend, pas le produit qui oublie. Trois appels ne suffisaient
   pas à le voir : la courbe montait encore.
2. **Le standard ne tient pas sur `petites-claques` à côté de l'API.** 1 Go au
   total, l'API Marpeap et sa base déjà en place : ajouter 430 à 620 Mo n'est
   pas raisonnable. Il lui faut sa propre machine, ou une machine plus grande.
   C'est la mesure qui décide où poser `wss://agent.marpeap.com`, pas une
   préférence.
3. **La transcription distante paie trois fois** : elle enlève 185 Mo au
   chargement et près de 190 Mo au pic, en plus du taux d'erreur (mesure 20) et
   des 200 ms de latence (mesure 24). Les trois arguments pointent dans la même
   direction.

### Deux pièges rencontrés en mesurant

- **`ru_maxrss` est un pic** : il ne peut que monter, et ne dit donc rien d'une
  fuite. Mesurer avec lui aurait conclu « la mémoire ne redescend jamais », ce
  qui est faux.
- **Trois points ne font pas une courbe.** La première version du banc s'arrêtait
  à trois appels et montrait une montée continue ; elle se stabilise au sixième.

### Rejouer

```bash
.venv/bin/python bancs/empreinte.py                                 # moteurs locaux
VARIANTE_STT=muet APPELS=14 .venv/bin/python bancs/empreinte.py     # Piper seul
```
