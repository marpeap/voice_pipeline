# voice-pipeline (refonte) — reprise de session

**Quoi** : standard téléphonique IA en français, conçu comme **greffon** réutilisable (Crenolo, Inkra, Kompagnon, tiers).
**Où en est-on** : deux vagues de recherche bouclées (15 rapports), **13 documents de conception**, et le **lot L0 mesuré à trois sur quatre**. **Aucune ligne de code produit, et c'est voulu** — les bancs de mesure, eux, tournent.

**Mesures faites le 14/09** (`docs/09-L0-MESURES.md`) : Piper RTF 0,096 mais **TTFB 372 ms** (il synthétise la phrase entière avant de livrer → la première réplique doit être courte) · **WER français 8 kHz** : Nemotron 7,8 % (×1,11), Vosk 10,6 % (×1,40), sherpa 23,4 % · **le « zéro » initial des numéros** massacré par Vosk et sherpa, correct chez Nemotron · TTFT Groq 430 ms p50 depuis la France, **la distance mange le budget**.
**Bloqué par Adnan** : une clé d'API pour le TTFT d'un candidat réel · l'arbitrage sur l'extraction de `reservation.py` (lot C0) · le praticien obligatoire ou non.

**Décisions prises le 2026-09-13** : premier livrable = **greffon Crenolo** (vertical beauté) · bord téléphonique **tranché après les mesures du lot L0** · **Kompagnon = M-Campaign renommé** (agent Google Ads, `marpeap/campaign`), greffe de niveau 1 avec le suivi de conversion d'appel comme valeur propre.
**Date de la recherche** : 2026-09-13 (toutes les sources portent cette date de consultation).

## Lire dans cet ordre
1. `docs/00-SYNTHESE.md` — les dix faits qui ferment ou ouvrent des portes, la pile retenue, les décisions ouvertes (D1→D5)
2. `docs/01-CONCEPT-PRODUIT.md` — passe de brainstorming n°1 : produit, onboarding, `memoire.md`, modèle économique, KPI
3. `docs/02-ARCHITECTURE.md` — passe de brainstorming n°2 : contrat de connecteur, paquets, multi-tenant, surfaces, lots L0→L7
3 bis. `docs/03-EXISTANT.md` — audit en lecture seule de l'ancien dépôt `marpeap/voice_pipeline`
4. `docs/04-CONNECTEUR-CRENOLO.md` · `05-QUESTIONNAIRE-ET-PACKS.md` · `06-CONSOLE-ET-CORRECTION.md` · `07-CORPUS-DE-TEST.md` · `08-DEPLOIEMENT.md` — la conception détaillée
5. `docs/recherche2/A1…A8` — la seconde vague, **complète** : LLM et cache de prompt, STT/TTS français, SMS, exploitation et sécurité, conformité, métier salon, hôtes de greffe, console
4. `docs/recherche/R1…R6.md` — les six rapports bruts, sourcés (URL + date), avec leurs dettes de recherche déclarées

## État des accès — résolu le 2026-09-13
- **Le dépôt d'origine est `marpeap/voice_pipeline`, avec un _underscore_.** Retrouvé via le PAT du vault (`11-Secrets/Index-Secrets.md`) ; cloné en lecture dans `/home/marpeap/voice_pipeline`, remote remis en HTTPS sans token, **aucune modification, aucun push**.
- **Audit : `docs/03-EXISTANT.md`.** En résumé : un seul commit (10/02/2026), un dashboard Express de configuration d'un agent **Retell + ElevenLabs**, `node_modules` commité, déploiement cassé (`Cannot find module 'child'`), Basic Auth en dur (`Marpeap` / `Error404`, **à révoquer**). **L'agent lui-même (`/var/www/marpeap.com/retell-agent`) est introuvable** sur les machines joignables et dans les snapshots — probablement perdu avec les VPS supprimés. **Rien à fusionner en code.**
- ⚠️ La clé SSH de la machine est une **deploy key limitée à `marpeap/aurora`** : pour tout autre dépôt, passer par le PAT du vault en HTTPS.
- `~/openclaw-study/extensions/voice-call` est le plugin **upstream OpenClaw** (Twilio/Telnyx/Plivo), utile comme référence de patterns — ce n'est pas notre code.

## Règles propres au projet
- **Aucune décision de pile n'est figée avant le lot L0** : trois mesures manquent au monde entier (RTF NeMo-Speech.cpp sur le VPS, **WER français en 8 kHz**, RTF/RAM Piper).
- **Piper tourne en service HTTP séparé** — obligatoire, son code est GPL-3.0 depuis 2026.
- **Voix Piper autorisées** : `fr_FR-siwis-medium` ou `fr_FR-mls-medium` (CC-BY 4.0). **Interdites** : `tom` (dataset AGPLv3), `gilles` (licence non vérifiée).
- **`read-after-write` avant toute confirmation orale.** Métrique `taux de confirmation orpheline`, cible 0.
- **Annonce « assistant automatique » dans la première phrase**, non désactivable (AI Act art. 50, applicable depuis le 02/08/2026).
- **Jamais de collecte d'e-mail par la voix.** Numéro de mobile + SMS.
- **Le commerçant ne voit jamais un prompt.** Questionnaire → `memoire.md` → agent.
- L'UI **remplace le bloc frontmatter**, jamais le fichier : le corps Markdown n'est jamais reparsé.
- **Branche dédiée, jamais de commit direct sur `main`.** Pas de trailer `Co-Authored-By`.

## Environnement
- Répertoire de travail : `/home/marpeap/voice-pipeline-refonte` (dépôt git local, pas encore de remote).
- Vault : `[[02-Projets-Marpeap/Voice-Pipeline]]` — source de vérité.
- VPS candidats : `petites-claques` 151.241.228.72 · `petites-frappes` 151.241.228.116 (1 Go chacun) · `marpeap-series` (Tailscale). **L'inférence ne tourne sur aucun des trois.**
