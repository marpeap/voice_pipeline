# Voice-Pipeline — récap de session (13/09/2026)

## Ce qui est fait
Recherche terminée (6 rapports parallèles, ~500 Ko, chaque affirmation sourcée URL + date) et **deux passes de conception**. **Aucune ligne de code**, volontairement.

Travail : `/home/marpeap/voice-pipeline-refonte`, branche `recherche-et-conception`, 2 commits.
Vault : `02-Projets-Marpeap/Voice-Pipeline` (+ INDEX + mémoire).

| Document | Contenu |
|---|---|
| `docs/00-SYNTHESE.md` | Les 10 faits décisifs, la pile retenue, les décisions D1→D5, la dette de recherche |
| `docs/01-CONCEPT-PRODUIT.md` | Parcours en 4 écrans, paliers du questionnaire, `memoire.md`, prix, KPI |
| `docs/02-ARCHITECTURE.md` | Contrat de connecteur, 12 paquets, multi-tenant, widget, extension, lots L0→L7 |
| `docs/recherche/R1…R6.md` | Les rapports bruts avec leurs sources et leurs trous déclarés |

## Les 7 faits qui ont changé le projet

1. **Le tout-local est fermé** : plancher speech-to-speech open source **16 Go de VRAM**, seul S2S francophone 79 Go. Mais l'orchestration coûte **~90 Mo par session** : le VPS porte la téléphonie et l'agent, jamais les modèles.
2. **Le tout-OSS coûte 12× plus cher que l'hybride** à 1 000 min/mois (0,3628 $ contre **0,0306 $/min**). On paie un GPU allumé, pas des minutes. Bascule vers 17 100 min/mois.
3. **Le verrou français est le numéro**, pas le prix : Telnyx et OVHcloud sont les seuls avec API d'achat FR et grille publique. Onboarding par renvoi d'appel : **moins de 2 minutes**, si on pré-achète les 09 par lots.
4. **L'agent doit fonctionner sans numéro d'appelant** (masquage CLI recommandé par l'ARCEP après renvoi) → identification par SMS ou DTMF, jamais par le CLI.
5. **Annoncer l'IA est obligatoire depuis le 02/08/2026** (AI Act art. 50) **et** c'est le premier levier de satisfaction : les plaintes cessent quand le bot se présente comme bot.
6. **Planity n'a aucune offre IA téléphonique**, aucun produit anglo-saxon ne parle français, aucune startup FR n'est greffée sur un logiciel de réservation. **L'intersection est vide, c'est notre place.**
7. **Durcissement des licences 2026** : Piper → GPL-3.0 (service HTTP séparé obligatoire, voix `tom` interdite), turn-detector LiveKit inutilisable hors LiveKit, jambonz v11+ payant, XTTS mort pour un produit facturé, Whisper périmé en temps réel.

## Tes arbitrages enregistrés
- Premier livrable : **greffon Crenolo** (vertical beauté).
- Bord téléphonique : **tranché après les mesures du lot L0**.
- **Kompagnon = M-Campaign** → greffe de niveau 1, avec le **suivi de conversion d'appel vers Google Ads** comme valeur propre.

## Ce que j'attends de toi
Le nom exact du dépôt d'origine : `<owner>/voice-pipeline`. Ma clé SSH est une deploy key limitée à `marpeap/aurora`, donc le plus rapide reste que tu lances toi-même :

```
git clone https://github.com/<owner>/voice-pipeline /home/marpeap/voice-pipeline
```

## Ensuite — lot L0
Trois chiffres qu'aucune source au monde ne publie, et qui décident de la pile :
1. RTF de NeMo-Speech.cpp sur le VPS cible ;
2. **WER français en bande téléphonique 8 kHz** (tous les WER publics sont en 16 kHz propre) ;
3. RTF et RAM réels de Piper.

Rien n'est figé avant.
