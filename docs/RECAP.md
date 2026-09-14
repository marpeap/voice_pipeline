# Voice-Pipeline — où en est le chantier (15/09/2026, 2 h)

## En une phrase

**Un assistant téléphonique configurable, branchable sur n'importe quelle application** — Crenolo n'en est qu'un adaptateur. Et surtout : **un service à part entière, vendu seul**, configurable depuis un site. L'extension de navigateur est reportée — elle ne portait pas l'audio, et le site fait le même travail.

**21 documents de conception · 16 rapports de recherche sourcés · 7 mesures faites · toujours zéro ligne de code produit** (les bancs de mesure, eux, tournent). Dépôt : `marpeap/voice_pipeline`, branche **`refonte`**.

---

## Les mesures faites (personne d'autre ne les publie)

| Mesure | Résultat |
|---|---|
| **TTS Piper** (voix FR, 63 Mo) | RTF **0,096**, RAM 136 Mo — mais **TTFB 372 ms** contre 150 visés, parce qu'il synthétise la phrase **entière** avant de livrer. **D'où la règle : la première réplique de l'agent doit être courte** (67 ms pour deux mots), la suite s'enchaîne en flux |
| **WER français, bande téléphonique** | Nemotron **7,8 %** (×1,11) · Vosk 10,6 % (×1,40) · sherpa 23,4 %. Aucune source au monde ne publiait ce chiffre |
| **Les numéros de téléphone** | **4 sur 10 perdus**, et *exactement les mêmes* en 16 kHz et en 8 kHz : le moteur coupe « quarante-trois » en « 40 3 ». Ce n'est donc pas le canal, **c'est la grammaire des nombres français** — donc le parsing, pas le micro |
| **Le « zéro » des numéros** | Massacré par Vosk et sherpa (« ses héros fit », « le verrou si »), **correct chez Nemotron**. C'est le maillon qui décide si le SMS de confirmation part |
| **TTFT LLM** | **2 040 ms** p50 en rouvrant une connexion à chaque appel, **378 ms** en la gardant ouverte, **85 ms** au mieux — vers un fournisseur américain. Ce n'est donc pas la distance : ce sont le DNS et les deux poignées de main, repayés à chaque tour de parole. Le premier levier de latence est le client, et il est gratuit |
| **Conversion 8 kHz G.711** | 11 ms de travail pour 3 s d'audio — mais **45 ms rien que pour démarrer `ffmpeg`**. Aucun processus externe par fragment audio |

---

## Les découvertes qui ont changé le projet

1. **La latence ne venait pas d'où on croyait.** Une connexion HTTPS rouverte à chaque appel coûte **2 040 ms** ; gardée ouverte, **378 ms**, et 85 ms au mieux — vers un fournisseur américain. Ce sont le DNS et les poignées de main, pas la distance. **Le premier levier de latence est gratuit.**
2. **Le SMS coûte plus cher que l'intelligence artificielle** — 17,40 €/salon/mois contre 4 à 10 $ pour le STT, le TTS, le LLM et la téléphonie réunis. Et comme Crenolo envoie déjà le rappel, notre coût incrémental tombe à **~13 €**.
3. **Un prompt plus long coûte moins cher** — le cache exige un préfixe de 4 096 tokens ; en dessous, **rien n'est caché**. On n'élague donc pas le fichier de connaissance, on le calibre au-dessus du seuil.
4. **1 Go = un appel simultané**, pas trente (mon estimation initiale venait d'un test sans STT ni LLM ni TTS). Mais **les lignes se mutualisent** : 20 salons tiennent sur 4 lignes.
5. **Google plafonne une application non vérifiée à 100 utilisateurs — à vie, sans réinitialisation.** D'où : agenda interne et **export iCal** d'abord (gratuit, sans OAuth, marche même avec iCloud qui n'a aucune API), connexion Google ensuite.
6. **La passerelle SMS par SIM est illicite** (décision Arcep consolidée au 01/01/2026) **et** ne produit aucun accusé de remise. Ça concerne **Crenolo aujourd'hui**, pas seulement ce chantier.
7. **NeMo-Speech.cpp ne compile pas tel qu'il est publié** — un symbole utilisé trois fois et défini nulle part. Ça explique qu'aucun chiffre de performance CPU n'existe : personne ne l'a compilé.

---

## Ce qui attend une décision de toi

1. **L'extraction de `reservation.py`** côté Crenolo — le pair a écrit 14 tests de caractérisation et attend ton feu vert. Argument décisif trouvé depuis : **le verrou y est déjà dupliqué**, donc l'extraction en **supprime** un au lieu d'en ajouter un.
2. **Rien d'autre.** La clé d'API est différée (tu as dit : pas de dépense), et j'ai retiré de ta pile l'arbitrage sur le praticien, qui était une affaire interne à Crenolo.

## Ce qui attend une machine

**`marpeap-series` est hors ligne depuis la mi-journée du 14** — c'est le banc de mesure, et aussi la machine d'AGENT-OS. Il ne reste qu'**une** mesure à y faire : la **tenue en charge** — combien d'appels simultanés une machine soutient, donc combien de salons par machine, donc la marge. Le reste a été mesuré depuis le poste cette nuit.

---

## La suite

**Lot L1** : une machine dédiée, Asterisk durci, un numéro, le pipeline complet — et un premier appel qui tient une conversation, avec le SLO mesuré et non estimé.
