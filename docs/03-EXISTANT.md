# Audit de l'existant — `marpeap/voice_pipeline` (lecture seule)

**Dépôt retrouvé le 2026-09-13** via le PAT du vault : le nom porte un **underscore** (`voice_pipeline`), pas un tiret — c'est pour cela que toutes les sondes précédentes échouaient.
Cloné en lecture dans `/home/marpeap/voice_pipeline`. **Aucune modification, aucun push.**

## Ce que le dépôt contient réellement

| | |
|---|---|
| Commits | **un seul** — `7d635ec`, **2026-02-10**, « Dashboard Niveau 2: Configuration Voice Agent » |
| Branches | `main` uniquement |
| Contenu | `server.js` (8 Ko, Express), `public/index.html` (17,5 Ko), `package.json`, `server.log`, `url.txt`, **`node_modules/` commité** (4,8 Mo) |
| Secrets commités | **aucun** — le seul motif suspect est un `placeholder="sk_..."` dans un champ de formulaire |

**Ce n'est pas un agent vocal. C'est un tableau de bord de configuration** : sept routes API qui lisent et réécrivent un fichier `.env`, testent deux fournisseurs et redémarrent un service.

## La pile d'origine, et pourquoi elle est périmée

Le dashboard pilote un agent **Retell AI + ElevenLabs** :

- `POST /api/test/retell` → `https://api.retellai.com/v2/list-agents`
- `POST /api/test/elevenlabs` → `https://api.elevenlabs.io/v1/voices`, avec **filtrage des voix françaises**
- Variables écrites : `RETELL_API_KEY`, `AGENT_ID`, `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `AGENT_NAME` (défaut **« Sarah »**), `AGENT_COMPANY`, **`AGENT_PROMPT`**

Trois constats de la recherche s'appliquent directement :

1. **Retell est une plateforme d'infrastructure, pas notre produit** : 0,07 à 0,31 $/min tout compris, et toute la logique d'agent vit chez eux. C'est exactement le verrou que l'assemblage hybride (0,0306 $/min) supprime. [R2]
2. **ElevenLabs Free interdit l'usage commercial** — et le benchmark ouvert de 499 appels réels place ElevenLabs à **p50 1 430 ms**, loin des promesses affichées. [R2, R4 §C.3]
3. **La configuration passait par un champ « Prompt Système » libre et un nom d'agent humain (« Sarah »)** : c'est précisément ce que le nouveau produit supprime. Le prompt libre a disparu chez les meilleurs acteurs du marché [R4 §B.1], et un prénom humain sans annonce tombe sous l'AI Act art. 50 **et** sous la plainte n°1 des appelants (« ils ne pardonnent pas au robot de faire semblant »). [R4 §C.2]

## L'agent lui-même est introuvable

`server.js` pointe vers des chemins absolus qui ne sont **pas** dans le dépôt :

- `/var/www/marpeap.com/retell-agent/.env` — le vrai agent
- `pm2 reload voice-agent` — le service
- `/opt/marpeap/dashboard` — le dashboard déployé (visible dans `server.log`)

Recherché en lecture seule le 13/09/2026, **rien trouvé** : ni sur `petites-claques` (151.241.228.72), ni sur `marpeap-series`, ni dans les dépôts `nano-marpo-snapshot` / `micro-marpo-snapshot`. `petites-frappes` (151.241.228.116) refuse la clé `nano-marpo`. Les deux VPS d'origine (nano-marpo, micro-marpo) ont été supprimés.

**Conclusion : le code de l'agent Retell n'est probablement plus récupérable.** Ce n'est pas grave — la refonte l'abandonne de toute façon — mais il faut le dire plutôt que de le chercher indéfiniment.

## Ce que le déploiement raconte

- `server.log` : `Error: Cannot find module 'child'` à la ligne 13 → sur le serveur, quelqu'un a édité `require('child_process')` en `require('child')`. **Le dashboard déployé était cassé**, et la version corrigée n'a jamais été recommitée.
- `url.txt` : `https://valuable-roles-trademarks-hint.trycloudflare.com` — exposition par **tunnel Cloudflare éphémère**, donc une URL morte à chaque redémarrage.
- Un seul commit en sept mois : le chantier s'est arrêté là.

## Ce qu'il ne faut pas reprendre

- **Identifiants Basic Auth en dur dans le source** : `Marpeap` / `Error404`, lignes 32-33. À révoquer si ce couple sert ailleurs.
- **`POST /api/restart` qui appelle `exec()`** sur pm2 derrière ce même Basic Auth.
- **Écriture directe dans le `.env` de production** depuis une page web (le backup avant écriture, lui, est une bonne idée — à garder).
- **`node_modules` dans git.**
- **Le prompt libre exposé à l'utilisateur.**

## Ce qui mérite d'être repris dans la console

Trois intentions justes, à refaire proprement :

1. **Tester la connexion d'un fournisseur et afficher la latence mesurée** (`latency_ms` renvoyé par les deux endpoints de test). Bonne idée : elle devient, dans le nouveau produit, la vérification de santé par tenant.
2. **Sauvegarde horodatée avant toute écriture de configuration** — remplacée par la table `tenant_config` append-only et le dépôt git du `memoire.md`.
3. **Masquage des clés à l'affichage** (`maskKey`, 4 premiers + 4 derniers caractères).

## Verdict

**Rien à fusionner en code.** L'ancien dépôt vaut comme **document d'intention** : il dit ce qu'Adnan voulait configurer (identité de l'agent, voix, entreprise, connaissance) et confirme que la voie Retell + prompt libre est celle qu'il faut quitter. Les 4 écrans du questionnaire (`docs/01-CONCEPT-PRODUIT.md` §3) remplacent terme à terme les quatre champs de ce dashboard.
