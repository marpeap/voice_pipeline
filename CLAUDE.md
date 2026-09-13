# voice-pipeline (refonte) — reprise de session

**Quoi** : standard téléphonique IA en français, conçu comme **greffon** réutilisable (Crenolo, Inkra, Kompagnon, tiers).
**Où en est-on** : phase **recherche terminée**, conception en cours. **Aucune ligne de code écrite, et c'est voulu.**
**Date de la recherche** : 2026-09-13 (toutes les sources portent cette date de consultation).

## Lire dans cet ordre
1. `docs/00-SYNTHESE.md` — les dix faits qui ferment ou ouvrent des portes, la pile retenue, les décisions ouvertes (D1→D5)
2. `docs/01-CONCEPT-PRODUIT.md` — passe de brainstorming n°1 : produit, onboarding, `memoire.md`, modèle économique, KPI
3. `docs/02-ARCHITECTURE.md` — passe de brainstorming n°2 : contrat de connecteur, paquets, multi-tenant, surfaces, lots L0→L7
4. `docs/recherche/R1…R6.md` — les six rapports bruts, sourcés (URL + date), avec leurs dettes de recherche déclarées

## État des accès
- **Dépôt d'origine `voice-pipeline` : introuvable.** Ni en local, ni dans le vault. `git@github.com:marpeap/voice-pipeline` → *Repository not found*. La clé SSH de la machine est une **deploy key limitée à `marpeap/aurora`**. `gh` n'est pas installé ; l'appel API avec le PAT du vault a été refusé par le classifieur de sécurité.
  → **À faire par Adnan** : donner le `owner/repo` exact, ou cloner lui-même (`! git clone …`). Le code existant doit être lu et repris, pas réinventé.
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
