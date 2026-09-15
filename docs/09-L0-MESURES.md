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
