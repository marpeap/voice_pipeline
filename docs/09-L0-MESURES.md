# Lot L0 — mesures

> Les quatre chiffres dont dépend le choix de la pile, et qu'**aucune source publique ne donne**.
> Ce document ne contient que du mesuré. Chaque entrée porte sa machine, ses versions et sa commande.

| # | Mesure | État |
|---|---|---|
| 1 | **RTF et RAM de Piper** (TTS français) | ✅ **fait le 2026-09-14** |
| 2 | RTF de NeMo-Speech.cpp sur la machine cible | à faire — demande des outils de compilation |
| 3 | **WER français en bande téléphonique 8 kHz** | à faire — demande un corpus et un STT |
| 4 | **TTFT réel des LLM candidats** (aucun fournisseur ne publie de percentiles) | à faire — demande des clés d'API |

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
