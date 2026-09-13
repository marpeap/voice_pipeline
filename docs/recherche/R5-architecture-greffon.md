# R5 — Architecture d'un module vocal IA en greffon réutilisable + configuration par questionnaire générant des .md

**État de l'art : septembre 2026. Toutes les consultations de sources : 2026-09-13.**

Contrainte cible rappelée en tête, parce qu'elle tranche la moitié des débats : **un petit VPS (1–2 Go de RAM), stack existante Next.js + FastAPI + PostgreSQL, budget nul, et le besoin de brancher le même module sur trois produits maison hétérogènes** (deux Next.js, un FastAPI/Jinja).

Convention de lecture :

- **[F]** fait vérifié sur source officielle, avec URL.
- **[H]** hypothèse ou déduction de ma part à partir de faits vérifiés — pas une citation.
- **[NV]** non vérifié : je n'ai pas trouvé de source officielle, et je le dis plutôt que d'inventer.
- **[R]** recommandation argumentée pour le contexte cible.

Deux limites méthodologiques honnêtes : (1) certains domaines (`docs.stripe.com`, `opentelemetry.io`) ont été bloqués au fetch direct par le filtrage réseau de cette session — les faits les concernant proviennent de recherche indexée ou de pages miroir, et sont marqués comme tels ; (2) je n'ai pas fait tourner de benchmark : aucun chiffre de performance ci-dessous n'est une mesure maison.

---

## Axe 1 — Patterns de greffon embarquable

### 1.1 Le pattern « loader + queue + iframe » : ce que font réellement les produits

**[F] Intercom.** Le snippet officiel pose `window.intercomSettings = { app_id: APP_ID }` puis charge un script async qui monte le widget. Pour un visiteur non identifié, seul `app_id` doit être présent (pas de `user_id`, `email`, `user_hash`). Un package npm officiel existe en parallèle, `@intercom/messenger-js-sdk`.
[Installation | Intercom Developer Platform](https://developers.intercom.com/installing-intercom/web/installation) · [npm @intercom/messenger-js-sdk](https://www.npmjs.com/package/@intercom/messenger-js-sdk) — consulté 2026-09-13.

**[F] Crisp.** Snippet en `<head>`, configuré par `window.CRISP_WEBSITE_ID`. Pour une SPA : `Crisp.configure("WEBSITE_ID")`. Cas iframe documenté explicitement, avec les options `lock_maximized`, `lock_full_view`, `cross_origin_cookies`.
[Crisp — installer le widget](https://help.crisp.chat/en/article/how-to-install-a-chat-widget-software-on-my-website-10wcj3l/) · [Crisp — embed in iFrame](https://help.crisp.chat/en/article/how-can-i-embed-the-crisp-chatbox-in-an-iframe-bkfh98/) — consulté 2026-09-13.

**[F] Chatwoot.** IIFE classique : création d'un `<script>` vers `<baseUrl>/packs/js/sdk.js`, insertion avant le premier `<script>` existant, puis au `onload` appel de `window.chatwootSDK.run({ websiteToken, baseUrl })`. La configuration (bulle masquée, position, locale, type `standard` / `expanded_bubble`) passe par `window.chatwootSettings` défini **avant** le chargement du SDK.
[Chatwoot Developer Docs](https://developers.chatwoot.com/introduction) — consulté 2026-09-13.

**[F] Cal.com.** Deux SDK distincts publiés sous le scope officiel `calcom` : `@calcom/embed-snippet` (vanilla JS, charge dynamiquement `@calcom/embed-core`, affiche un Cal Link en iframe) et `@calcom/embed-react` (wrapper React du même mécanisme).
[npm @calcom/embed-snippet](https://www.npmjs.com/package/@calcom/embed-snippet) · [npm @calcom/embed-react](https://www.npmjs.com/package/@calcom/embed-react) · [Cal.com Docs — Set up your embed](https://calcom.gitbook.io/docs/core-features/embed/set-up-your-embed) — consulté 2026-09-13.

**[F] Stripe Elements.** `element.mount()` insère une `<iframe>` servie depuis un domaine Stripe, donc cross-origin : la page parente ne peut pas accéder au contenu. C'est la frontière d'isolation qui porte la conformité PCI.
[docs.stripe.com/js/element/mount](https://docs.stripe.com/js/element/mount.md) — consulté 2026-09-13 (page atteinte via recherche indexée, fetch direct du domaine bloqué).

**[H] Le dénominateur commun** des quatre produits est un bootstrap minuscule qui (1) pose une variable de config globale lue avant chargement, (2) empile éventuellement les appels dans une file (`window.X.q = window.X.q || []`), (3) injecte un `<script async>` vers le CDN du vendeur, (4) laisse la vraie bibliothèque vider la file à son chargement. Aucun de ces loaders ne porte de version explicite dans son URL : le vendeur assume la rétrocompatibilité côté client. C'est un choix, pas une fatalité — et il a un coût, voir 1.5.

### 1.2 Le point qui décide tout pour un module **vocal** : le micro en iframe cross-origin

C'est là que le cas vocal diverge du cas chat, et c'est la contrainte la plus structurante de tout ce rapport.

**[F]** Une iframe cross-origin n'hérite pas de l'accès micro/caméra. La délégation est explicite, via l'attribut `allow` de la balise :

```html
<iframe src="https://widget.exemple.com/embed" allow="microphone"></iframe>
```

La valeur par défaut de la plupart des features de Permissions Policy est `src` : la feature n'est autorisée dans l'iframe que si le document chargé vient de la même origine que l'URL du `src`. Sans `allow="microphone"` explicite, `getUserMedia()` échoue dans l'iframe cross-origin.
[MDN — Permissions Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Permissions_Policy) · [MDN — `<iframe>` (attribut allow)](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/iframe) · [W3C — Permissions Policy](https://www.w3.org/TR/permissions-policy/) — consulté 2026-09-13.

**[F]** Si la page parente envoie un header `Permissions-Policy` **et** que l'iframe porte un `allow`, les deux politiques se combinent en prenant le sous-ensemble le plus restrictif : il faut que les deux autorisent la feature.
[MDN — header Permissions-Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Permissions-Policy) — consulté 2026-09-13.

**[F]** Chromium a délibérément déprécié l'accès aux permissions dites « puissantes » (caméra, micro, géolocalisation) dans les iframes cross-origin par défaut, précisément pour forcer cette déclaration explicite.
[Chromium — Deprecating Permissions in Cross-Origin Iframes](https://www.chromium.org/Home/chromium-security/deprecating-permissions-in-cross-origin-iframes/) — consulté 2026-09-13.

**[H] Conséquence opérationnelle.** Le pattern « je colle un script, ça marche » de Crisp ou Intercom **ne transpose pas tel quel** à un widget vocal servi depuis un domaine tiers. Chaque page hôte devra porter un `allow="microphone"` sur l'iframe, et ne pas envoyer un header qui l'annule. Cela veut dire : soit le loader du greffon crée lui-même l'iframe avec le bon `allow` (faisable — le loader s'exécute dans la page hôte, donc il maîtrise l'attribut), soit l'intégrateur doit le faire à la main. La première voie est la bonne, et c'est un argument fort pour livrer un **loader** plutôt qu'un bout de HTML à copier.

### 1.3 CSP : ce qui casse un widget, et comment les vendeurs le documentent

**[F] Stripe** publie une allowlist CSP explicite : `connect-src` doit inclure `https://api.stripe.com` ; `frame-src` doit inclure `https://js.stripe.com`, `https://*.js.stripe.com`, `https://hooks.stripe.com` ; `script-src` doit inclure `https://js.stripe.com`, `https://*.js.stripe.com`.
[docs.stripe.com/security/guide](https://docs.stripe.com/security/guide.md) — consulté 2026-09-13 (via recherche indexée). Un cas de casse réel remonté publiquement : sans `connect-src` élargi à `https://errors.stripe.com` / `https://q.stripe.com`, la télémétrie interne de Stripe.js est bloquée. [GitHub stripe/stripe-js#127](https://github.com/stripe/stripe-js/issues/127) — consulté 2026-09-13.

**[NV]** Je n'ai pas trouvé de page CSP dédiée et officielle équivalente chez Intercom.

**[H] Cartographie des directives qui cassent un greffon**, déduite des mécanismes CSP standard et cohérente avec le cas Stripe :

| Directive | Ce qui casse si elle est trop étroite | Symptôme |
|---|---|---|
| `script-src` | Le loader ne se charge pas | Rien ne se passe, erreur console CSP |
| `frame-src` (fallback `child-src`) | L'iframe est bloquée | Cadre vide, **pas d'erreur JS** |
| `connect-src` | API, WebSocket, signalisation WebRTC | Widget monté mais muet |
| `media-src` | Fichiers audio statiques (sonneries, prompts pré-enregistrés) | Sons absents |
| `worker-src` | AudioWorklet, VAD côté client, Web Worker de traitement | Pipeline audio dégradé |

À noter : le flux issu de `getUserMedia` n'est **pas** soumis à `media-src` — c'est Permissions Policy qui le gouverne (1.2).

**[R]** Publier dès le jour 1 une page « CSP & Permissions Policy » qui donne la ligne à copier, exactement comme Stripe. C'est trois lignes de doc qui économisent des heures de support, et c'est l'un des rares endroits où un petit éditeur peut paraître aussi sérieux qu'un gros.

### 1.4 Web Components : l'option qui traverse les trois apps

**[F]** Les custom elements sont dans le Living Standard WHATWG, §4.13. [HTML Standard — Custom elements](https://html.spec.whatwg.org/multipage/custom-elements.html) — consulté 2026-09-13.

**[F] Declarative Shadow DOM** est passé « widely available » le **2026-08-20**. Support : Chrome 111+, Edge 111+, Firefox 123+, Safari 16.4+. Fait partie d'Interop 2024.
[web-features-explorer — declarative shadow DOM](https://web-platform-dx.github.io/web-features-explorer/features/declarative-shadow-dom/) · [caniuse](https://caniuse.com/declarative-shadow-dom) — consulté 2026-09-13.

**[F] Scoped Custom Element Registries** : la proposition, révisée pour ne plus dépendre uniquement des shadow roots, a été intégrée au HTML Living Standard (mise à jour datée 2026-09-08) ; WebKit a activé le support en implémentation.
[WICG/webcomponents#716](https://github.com/WICG/webcomponents/issues/716) · [whatwg/html#10854](https://github.com/whatwg/html/issues/10854) · [Bugzilla 1874414](https://bugzilla.mozilla.org/show_bug.cgi?id=1874414) — consulté 2026-09-13.
**[NV]** Le statut « shippé stable partout » en septembre 2026 n'est pas confirmé : spec intégrée et implémentations en cours ≠ couverture navigateur complète. Ne pas en dépendre.

**[F] Next.js et hydratation.** Le Shadow DOM doit être hydraté côté client ; exécuter `customElements.define` pendant l'hydratation provoque un FOUC. Solutions documentées : `dynamic(..., { ssr: false })`, shim des API navigateur absentes sous Node, logique DOM déplacée dans `useEffect`.
[CSS-Tricks — Using Web Components With Next](https://css-tricks.com/using-web-components-with-next-or-any-ssr-framework/) · [vercel/next.js discussion #49537](https://github.com/vercel/next.js/discussions/49537) — consulté 2026-09-13.

**[H]** Un custom element autonome fonctionne à l'identique sur une page Jinja servie par FastAPI (aucun framework ne « possède » le DOM, donc aucun problème d'hydratation) et sur Next.js (à condition de le monter client-only). C'est la seule couche de livraison de cette liste dont le contrat est du DOM standard plutôt qu'un runtime de framework.

### 1.5 Micro-frontends, SDK npm, headless + UI

**[F] Module Federation 2.0** tourne désormais sur Webpack, Vite (`@module-federation/vite`, v1.21.5 au moment de la recherche), Rspack (`@module-federation/enhanced`) et Rollup, avec runtime unifié, partage de types TypeScript entre remotes et découverte dynamique par manifest.
[module-federation.io — Vite](https://module-federation.io/integrations/build-tool/vite.html) · [npm @module-federation/vite](https://www.npmjs.com/package/@module-federation/vite) — consulté 2026-09-13.

**[H]** Module Federation présuppose un pipeline de build JS synchronisé des deux côtés, host et remote. Une page Jinja servie par FastAPI n'a pas de bundler runtime. Pour trois apps dont une est dans ce cas, c'est structurellement inapplicable — indépendamment de la question du coût.

**[F] Cal.com Platform Atoms** (`@calcom/atoms`) fournit `CalProvider`, `Booker`, `AvailabilitySettings`, `EventTypeSettings` comme composants React natifs rendus **dans le DOM de l'app hôte** (pas en iframe), stylables, adossés à l'API Platform v2 (`api.cal.com/v2`). C'est le pattern « headless API + UI React optionnelle », maintenu **en parallèle** du SDK iframe.
[npm @calcom/atoms](https://www.npmjs.com/package/@calcom/atoms) · [packages/platform/atoms — README](https://github.com/calcom/cal.com/blob/main/packages/platform/atoms/README.md) · [Cal.com Platform Quickstart](https://cal.com/docs/platform/quickstart) — consulté 2026-09-13.

C'est le précédent le plus directement transposable : un même éditeur, deux voies de livraison au-dessus d'un même cœur d'API.

**[F] Versionnage d'API chez Stripe** : deux niveaux. Des *major releases* nommées (`acacia`, `basil`, `dahlia`…) qui peuvent casser la compatibilité, et des *monthly releases* portant le même nom de major, garanties rétrocompatibles. Version constatée : `2026-08-26.dahlia`. Chaque compte est épinglé à une version, changeable depuis Workbench.
[docs.stripe.com/api/versioning](https://docs.stripe.com/api/versioning) — consulté 2026-09-13 (via recherche indexée).

**[H]** Le découplage est la leçon : le **loader JS** n'est pas versionné dans son URL (`js.stripe.com/v3/` est figé mais son contenu évolue), alors que le **contrat de données** est versionné par date et épinglé par client. Un petit éditeur qui inverse ces deux choix — loader épinglé, API non versionnée — se condamne à ne jamais pouvoir corriger un bug côté client et à casser ses intégrations à chaque changement de schéma.

### 1.6 [R] Recommandation Axe 1

**Trois couches, un seul cœur.**

1. **Cœur headless en TypeScript** — machine à états de l'appel, transport (WebRTC ou WebSocket), signalisation, événements. Aucune dépendance de framework. C'est le seul artefact où vit la logique ; tout le reste est une enveloppe.
2. **Custom element** (`<votre-widget-vocal>`) qui embarque ce cœur et rend son UI en Shadow DOM. C'est la livraison universelle : `<script src>` + une balise, valable pour Next.js (monté client-only) comme pour la page Jinja. Le custom element **crée lui-même** son iframe interne avec `allow="microphone"` si une isolation cross-origin est requise — l'intégrateur n'a pas à y penser.
3. **Wrapper React mince** publié sur npm pour les deux apps Next.js, qui n'est qu'un `useRef` + `useEffect` autour du custom element. Exactement le rapport `embed-react` → `embed-core` de Cal.com.

**Écarté : Module Federation** (incompatible avec la page FastAPI/Jinja, et disproportionné). **Écarté : package React seul** (n'adresse pas le troisième produit sans y injecter React pour un seul composant). **Nuancé : iframe cross-origin pure** — excellente pour l'isolation CSS et la sécurité, mais elle transforme le micro en négociation de permissions à chaque intégration. Si le module vocal peut tourner en **same-origin** (servi depuis le domaine de l'app hôte via un reverse proxy), tout le problème 1.2 disparaît ; c'est l'option à privilégier pour les produits maison, en gardant l'iframe pour d'éventuels clients externes.

**Versionnage** : loader non versionné (`/v1/widget.js`, contenu évolutif, rétrocompatibilité assumée), API versionnée par date et épinglée par tenant. Et une page CSP dès le départ.

---

## Axe 2 — Multi-tenant sur une petite infra

### 2.1 Isolation des données : RLS PostgreSQL, et ses pièges réels

**[F]** `ENABLE ROW LEVEL SECURITY` active les policies, mais **le propriétaire de la table les contourne** par défaut. `FORCE ROW LEVEL SECURITY` soumet aussi le propriétaire. Une table avec RLS activé et aucune policy est en deny-par-défaut : aucune ligne visible.
[PostgreSQL — Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) — consulté 2026-09-13.

**[F] Les superusers et les rôles portant l'attribut `BYPASSRLS` contournent toujours** le système de sécurité par ligne. [même source]

**[F] Trois avertissements explicites de la documentation**, souvent ignorés :

- Les fonctions marquées `leakproof` peuvent être évaluées **avant** le contrôle RLS par l'optimiseur : « the optimizer may choose to apply such functions ahead of the row-security check ».
- Les contrôles d'intégrité référentielle (unicité, clés primaires, clés étrangères) **contournent toujours** RLS. Donc une violation de contrainte peut révéler l'existence d'une ligne d'un autre tenant.
- Une policy contenant un sous-`SELECT` sans `FOR SHARE` / `FOR UPDATE` est sujette à une condition de course entre transactions concurrentes.

[même source] — consulté 2026-09-13.

**[F] Le piège du pooling.** Une valeur posée par `SET app.tenant_id` persiste pour la durée de vie de la connexion. Avec un pool (PgBouncer, SQLAlchemy), la requête suivante qui récupère cette connexion hérite du contexte du tenant précédent. La forme correcte est `SET LOCAL` ou `set_config(name, value, true)` — le troisième argument `true` limitant la portée à la transaction courante — à l'intérieur d'une transaction explicite. PgBouncer en mode transaction ne préserve pas les variables de session entre transactions, ce qui **force** la bonne discipline.
Synthèse concordante de plusieurs sources techniques ; le mécanisme `set_config(..., is_local => true)` est documenté dans [PostgreSQL — System Administration Functions](https://www.postgresql.org/docs/current/functions-admin.html). Consulté 2026-09-13. **[H]** — je n'ai pas trouvé de page PostgreSQL officielle qui énonce ce piège comme tel ; le mécanisme est officiel, l'avertissement est une déduction bien établie dans la pratique.

**[H] Choix entre les trois patterns** :

| Pattern | Isolation | Coût migrations | Coût opérationnel | Verdict VPS 1–2 Go |
|---|---|---|---|---|
| Base par tenant | Maximale | N migrations | Élevé (N connexions, N sauvegardes) | Non |
| Schéma par tenant | Forte | N × Alembic, à séquencer | Moyen, dégrade au-delà de quelques centaines de schémas | Non au départ |
| Table partagée + `tenant_id` + RLS | Correcte si discipline | Une seule | Faible | **Oui** |

**[R]** Table partagée, colonne `tenant_id NOT NULL` sur **toutes** les tables métier, `ENABLE` + `FORCE ROW LEVEL SECURITY`, policies sur `tenant_id = current_setting('app.tenant_id')::uuid`, un rôle applicatif **non-propriétaire et sans `BYPASSRLS`**, et une dépendance FastAPI unique qui ouvre la transaction et pose `set_config('app.tenant_id', …, true)` avant toute requête. Index composite préfixé par `tenant_id` sur chaque table. RLS est un filet, pas la sécurité primaire : le filtre applicatif reste là, RLS rattrape l'oubli.

Un test d'intégration qui tente une lecture croisée entre deux tenants et **doit** échouer vaut plus que toute la doc ci-dessus.

### 2.2 Configuration par tenant

**[H]** Trois besoins qui ne se stockent pas pareil : (a) les réglages structurés et validés (voix, horaires, numéros) → colonnes ou JSONB validé applicativement ; (b) la connaissance libre du commerçant → fichiers `.md` (axe 4) ; (c) les secrets → 2.3.

**[R]** Une table `tenant_config(tenant_id, version, data JSONB, created_at, created_by)` en **append-only** : chaque sauvegarde insère une nouvelle version au lieu d'écraser. Sur un VPS, le coût est nul et on gagne l'historique, le rollback, et la réponse à « qui a changé quoi » sans machinerie. La validation reste dans Pydantic côté FastAPI (axe 4), pas dans une contrainte SQL — une contrainte `CHECK` avec un schéma JSON figé en base devient vite un obstacle aux migrations.

### 2.3 Secrets par tenant

**[F] OWASP** recommande des solutions dédiées de gestion de secrets plutôt qu'un stockage en base, et décrit l'**envelope encryption** : le secret est chiffré par une clé de données, elle-même chiffrée par une clé maître stockée séparément. Principe insistant : ne jamais stocker les clés à côté des secrets qu'elles protègent. Rotation automatisée plutôt que manuelle, et moindre privilège — « engineers should not have access to all secrets ».
[OWASP — Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html) — consulté 2026-09-13.

**[F] pgcrypto** fournit `pgp_sym_encrypt` / `pgp_sym_decrypt`, `pgp_pub_encrypt` / `pgp_pub_decrypt`, et les fonctions brutes `encrypt` / `decrypt` / `encrypt_iv` / `decrypt_iv`. **Avertissement explicite de la documentation** : « All pgcrypto functions run inside the database server. That means that all the data and passwords move between pgcrypto and client applications in clear text. » D'où l'obligation de se connecter localement ou en SSL, et de faire confiance à l'administrateur système et base. La documentation conclut : « If you cannot, then better do crypto inside client application. » Elle précise également que l'implémentation ne résiste pas aux attaques par canal auxiliaire.
[PostgreSQL — pgcrypto](https://www.postgresql.org/docs/current/pgcrypto.html) — consulté 2026-09-13.

**[R]** Chiffrement **applicatif**, pas pgcrypto. Concrètement : une clé maître dans une variable d'environnement du service systemd (mode 0600, hors du dépôt), une clé de données par tenant chiffrée par la clé maître et stockée en base, les secrets du tenant chiffrés par sa clé de données. C'est de l'envelope encryption à budget nul, et cela respecte l'avertissement pgcrypto : la clé ne transite jamais vers le serveur de base. Vault est écarté — sur 1 Go de RAM, son empreinte et son coût opérationnel ne se justifient pas pour quelques dizaines de tenants. La rotation se fait par re-chiffrement des clés de données, sans toucher aux secrets.

### 2.4 Quotas et limitation de débit

**[F] slowapi** est « a rate limiting library for Starlette and FastAPI adapted from flask-limiter », licence MIT, backends mémoire / Redis / memcached, limites partageables entre routes et décorateurs cumulables. Contrainte d'usage : l'argument `request` doit être passé explicitement à la fonction d'endpoint ; les endpoints WebSocket ne sont pas supportés.
[GitHub laurentS/slowapi](https://github.com/laurentS/slowapi) — consulté 2026-09-13.

**[H]** L'absence de support WebSocket est notable pour un produit vocal, dont la session d'appel passe souvent par WebSocket : la limitation de débit devra alors se faire à l'ouverture de session (HTTP) et non sur les frames.

**[R]** Deux niveaux distincts, à ne pas confondre. **Anti-abus** : slowapi avec le backend mémoire tant qu'il n'y a qu'un process ; dès qu'il y a deux workers uvicorn, le backend mémoire compte faux, et il faut Redis. **Quota métier** (minutes d'appel du mois) : ce n'est pas du rate limiting, c'est de la comptabilité — un compteur transactionnel en base, incrémenté à la fin de chaque appel dans la même transaction que l'écriture de l'appel, avec un seuil qui refuse le démarrage du suivant. Le faire en base et non en cache, parce qu'un quota perdu au redémarrage est un quota offert.

### 2.5 Facturation à l'usage

**[F] Stripe** : depuis la version d'API **2025-03-31.basil**, l'ancienne API `usage records` a disparu et tout prix *metered* requiert un **Meter** associé. L'API v2 des meter events offre deux voies : validation **synchrone** (jusqu'à 1 000 événements/s en livemode) et validation **asynchrone** via meter event streams (jusqu'à 10 000 requêtes/s).
[Stripe API — Meters](https://docs.stripe.com/api/billing/meter) · [Create a Meter Event (v2)](https://docs.stripe.com/api/v2/billing/meter-events/create) · [Meter event stream (v2)](https://docs.stripe.com/api/v2/billing/meter-event-stream/create) — consulté 2026-09-13 (via recherche indexée, fetch du domaine bloqué).

**[F] Lago** : moteur de facturation open source sous **AGPLv3**, édition Community auto-hébergeable gratuitement via Docker ou Kubernetes, sans limite d'usage ni frais par événement.
[getlago.com](https://getlago.com/) · dépôt GitHub Lago — consulté 2026-09-13. **[NV]** Je n'ai pas mesuré son empreinte mémoire.

**[H]** Lago embarque Postgres, Redis, un worker Sidekiq et une API Rails. Sur un VPS de 1 Go déjà occupé par FastAPI, Next.js et PostgreSQL, cela n'entre pas.

**[R]** Stripe Billing avec meters, et rien d'autre. Deux règles à tenir dès le premier événement : **idempotence** — un identifiant d'événement déterministe dérivé de l'identifiant d'appel, pour qu'un rejeu après timeout ne facture pas deux fois ; et **réconciliation** — la table locale des appels reste la source de vérité, Stripe n'est qu'un miroir, et un job quotidien compare les deux. Lago est le plan B du jour où la facturation deviendra un produit en soi, pas avant.

---

## Axe 3 — Extension navigateur, Manifest V3

### 3.1 État par navigateur

**[F] Chrome.** MV2 a été désactivé pour tous les utilisateurs le **24 juillet 2025** (Chrome 138). La policy entreprise `ExtensionManifestV2Availability`, dernière exemption, a été retirée avec **Chrome 139**. Après le **28 juillet 2026**, plus aucun mécanisme ne permet d'exécuter une extension MV2 sur Chrome stable. Le **31 août 2026**, Google supprime les extensions MV2 restantes du Chrome Web Store.
[Manifest V2 support timeline — Chrome for Developers](https://developer.chrome.com/docs/extensions/develop/migrate/mv2-deprecation-timeline) · [Chrome Enterprise — ExtensionManifestV2Availability](https://chromeenterprise.google/policies/extension-manifest-v2-availability/) — consulté 2026-09-13.
Autrement dit : à la date de ce rapport, **MV2 est mort, y compris en entreprise**. La question « MV2 ou MV3 » ne se pose plus.

**[F] Firefox** supporte MV3 mais avec une différence structurante : la clé `background.scripts` charge une **event page** non persistante, pas un service worker DOM-less séparé comme Chrome. Les listeners survivent au déchargement, les valeurs en mémoire non — d'où l'usage de l'API `storage` pour la persistance.
[MDN — Background scripts](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Background_scripts) · [Firefox Extension Workshop — MV3 migration](https://extensionworkshop.com/documentation/develop/manifest-v3-migration-guide/) — consulté 2026-09-13.

**[F] Safari.** Conversion depuis une extension Chrome via `xcrun safari-web-extension-converter` (Xcode 13+), qui génère un projet Xcode avec app macOS et/ou iOS. Distribution obligatoire par l'App Store.
[Apple Developer — Safari Extensions](https://developer.apple.com/safari/extensions/) — consulté 2026-09-13.

### 3.2 Le service worker ne sait pas faire d'audio — et la réponse officielle

**[F] Cycle de vie du service worker MV3.** Chrome le termine après **30 secondes d'inactivité** (tout événement ou appel d'API réinitialise le compteur), ou si un événement dépasse **5 minutes**, ou si une réponse `fetch()` met plus de **30 secondes** à arriver. Depuis Chrome 110, `chrome.alarms` descend à 30 s, et **une connexion WebSocket active prolonge la durée de vie** : chaque message envoyé ou reçu réinitialise le compteur d'inactivité.
[The extension service worker lifecycle](https://developer.chrome.com/docs/extensions/develop/concepts/service-workers/lifecycle) · [Longer extension service worker lifetimes](https://developer.chrome.com/blog/longer-esw-lifetimes) — consulté 2026-09-13.

Un service worker n'a pas de DOM : ni `AudioContext`, ni `getUserMedia`.

**[F] Offscreen documents.** `chrome.offscreen` définit des raisons dont `USER_MEDIA` (interaction avec des flux média via `getUserMedia()`), `AUDIO_PLAYBACK` et `WEB_RTC`. Détail important : la raison `AUDIO_PLAYBACK` ferme le document après **30 secondes sans audio en cours de lecture** ; les autres raisons n'imposent pas cette limite de durée de vie. Le document offscreen a un cycle de vie et des permissions distincts du service worker.
[chrome.offscreen API](https://developer.chrome.com/docs/extensions/reference/api/offscreen) · [Offscreen Documents in Manifest V3](https://developer.chrome.com/blog/Offscreen-Documents-in-Manifest-v3) — consulté 2026-09-13.

**[F] chrome.tabCapture** capture un `MediaStream` de l'onglet courant, mais uniquement à la suite d'une action utilisateur explicite ; le `streamId` retourné est à usage unique et expire en quelques secondes. Avant Chrome 116, on ne pouvait ni l'appeler depuis un service worker, ni consommer son `streamId` dans un document offscreen — ces deux limitations sont levées.
[chrome.tabCapture API](https://developer.chrome.com/docs/extensions/reference/api/tabCapture) · [Audio recording and screen capture](https://developer.chrome.com/docs/extensions/how-to/web-platform/screen-capture) — consulté 2026-09-13.

**[NV] Équivalent Firefox à `chrome.offscreen` : introuvable dans la documentation Mozilla.** C'est un risque réel et non levé pour toute extension cross-browser ayant besoin d'audio ou de WebRTC en arrière-plan. À traiter comme un POC séparé, jamais comme un acquis.

### 3.3 UI, permissions, déclenchement d'appel

**[F] Side panel.** Chrome expose `chrome.sidePanel` (clé manifest `side_panel`), **délibérément distincte** de l'API `sidebarAction` / clé `sidebar_action` de Firefox et Opera — l'équipe Chrome a évité de réutiliser l'API existante pour ne pas laisser croire à un comportement identique. Les deux ne sont pas interchangeables.
[chrome.sidePanel](https://developer.chrome.com/docs/extensions/reference/api/sidePanel) · [MDN — sidebarAction](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/sidebarAction) · [MDN — Chrome incompatibilities](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Chrome_incompatibilities) — consulté 2026-09-13.

**[F] Déclencher un appel.** `navigator.registerProtocolHandler()` permet d'enregistrer un gestionnaire pour un schéma de la liste blanche, qui inclut `tel:` (avec `mailto`, `sms`, `geo`, `bitcoin`…). L'URL du handler doit être en `https` et de même origine que la page appelante ; le navigateur demande confirmation à l'utilisateur.
[MDN — registerProtocolHandler()](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/registerProtocolHandler) — consulté 2026-09-13.

### 3.4 Publication : coûts et délais réels

| Store | Frais | Délais / contraintes |
|---|---|---|
| **Chrome Web Store** | **5 USD, une seule fois**, couvre toutes les extensions [F] | 90 % des soumissions revues sous 3 jours ; permissions étroites → parfois quelques minutes ; `<all_urls>` ou compte neuf → revue humaine, jusqu'à plusieurs semaines [F] |
| **Edge Add-ons** | Gratuit (compte Microsoft) [F] | Revue standard ; programme de revue accélérée depuis 2025, sélection automatique sur l'usage et la qualité [F] |
| **Firefox AMO** | Aucun frais trouvé [NV] | Signature Mozilla **obligatoire** même hors AMO ; revue humaine obligatoire pour les extensions listées [F] |
| **Safari** | **99 USD/an** (Apple Developer Program) [F] | Distribution App Store, revue Apple complète |

[Chrome — Register your developer account](https://developer.chrome.com/docs/webstore/register) · [Chrome Web Store review process](https://developer.chrome.com/docs/webstore/review-process) · [Edge — Register as developer](https://learn.microsoft.com/en-us/microsoft-edge/extensions/publish/create-dev-account) · [Edge — Curation and review](https://learn.microsoft.com/en-us/microsoft-edge/extensions/publish/add-ons-curation) · [Mozilla — Add-on signing](https://support.mozilla.org/en-US/kb/add-on-signing-in-firefox) · [Apple Developer — Safari Extensions](https://developer.apple.com/safari/extensions/) — consulté 2026-09-13.

**[F] Interdiction du code distant en MV3.** Toute la logique doit être empaquetée : pas de `<script src>` hors du package, pas d'`eval()` sur du code distant, pas d'interpréteur exécutant des commandes distantes même présentées comme des données.
[Additional Requirements for MV3](https://developer.chrome.com/docs/webstore/program-policies/mv3-requirements) · [Remote hosted code violations](https://developer.chrome.com/docs/extensions/develop/migrate/remote-hosted-code) — consulté 2026-09-13.

### 3.5 Partage de code entre extension et app web

**[F]** Trois outils dominent en 2026 : **CRXJS** (plugin Vite, v2.0 en juin 2025, compatible Vite 3→8 y compris Rolldown), **WXT** (wxt.dev), **Plasmo**. La comparaison qualitative entre eux provient de sources secondaires, pas de documentation officielle — je ne la tiens pas pour un fait vendeur.

**[H] La divergence structurelle.** L'interdiction de code distant fait que le greffon **ne peut pas être livré à l'extension sous la forme d'un script CDN**, contrairement aux trois apps web. Le même custom element doit être **bundlé au build** dans le package de l'extension. C'est précisément pour cela que la recommandation de l'axe 1 place la logique dans un **package npm partagé** : ce package est consommable à la fois par le loader CDN (pour le web) et par le build de l'extension (pour le store). Un greffon conçu uniquement comme « un script hébergé chez nous » ne sera jamais publiable en extension.

### 3.6 [R] Recommandation Axe 3

**Reporter l'extension, et concevoir dès maintenant pour qu'elle reste possible.**

Le cas d'usage décrit — appels en cours, fiche appelant, déclencher un appel, éditer la config — est parfaitement faisable sur Chrome et Edge avec le triptyque documenté service worker (orchestration) + offscreen document (`USER_MEDIA` + `WEB_RTC`) + side panel (UI). Ce n'est pas de la recherche, c'est de l'assemblage de patterns officiels. Mais c'est **une deuxième application à maintenir** : deux cycles de revue, deux surfaces de bug, et une API side panel non portable vers Firefox.

Or les trois quarts de ce cas d'usage — voir les appels, la fiche appelant, éditer la config — ne demandent aucune capacité propre à une extension : une **application web dans un onglet, ou une PWA**, les couvre. Seul « déclencher un appel depuis n'importe quelle page » et « voir l'appel sans changer d'onglet » justifient vraiment l'extension.

Donc : lot 1 sur Chrome + Edge uniquement (5 USD, revue rapide, base Chromium commune), **et seulement une fois le produit web validé**. Firefox est un chantier distinct tant que l'absence d'équivalent à `chrome.offscreen` n'est pas levée. Safari ne se justifie pas à 99 USD/an avant d'avoir des clients qui le réclament. Et dès aujourd'hui : la logique vit dans un package npm bundlable, jamais dans un script hébergé.

---

## Axe 4 — Config-as-code en Markdown



### 4.1 La convention `.md` + frontmatter est devenue un standard de fait

**[F] AGENTS.md** est « a simple, open format for guiding coding agents », qui fournit « a dedicated, predictable place to provide the context and instructions ». **Plus de 60 000 projets open source** l'utilisent ; parmi les adoptants : OpenAI, Google (Jules), Cognition (Devin, Windsurf), GitHub Copilot, Cursor, Zed, Aider, VS Code. Format : Markdown standard, **aucun champ obligatoire**, titres de sections libres. Emplacement : racine du dépôt. En monorepo, plusieurs fichiers imbriqués, « the closest one takes precedence ». Le prompt explicite de l'utilisateur prime sur tout.
[agents.md](https://agents.md/) — consulté 2026-09-13.

C'est le point le plus important de cet axe : **l'idée de configurer un agent par un fichier Markdown n'est plus une originalité à défendre, c'est une convention établie et massivement adoptée.** Trois enseignements directement transposables : pas de champs obligatoires (le fichier reste lisible même vide), résolution par proximité, et priorité explicite de l'instruction directe sur le fichier.

**[F] Cursor Rules.** Les fichiers `.cursor/rules/*.mdc` portent trois champs de frontmatter : `alwaysApply` (booléen ; si `true`, ignore `globs` et `description`), `description` (utilisée quand `alwaysApply` est `false` et qu'aucun glob n'est défini — l'agent lit la description et charge la règle quand elle est pertinente), et `globs` (motif de chemin ; la règle s'attache automatiquement si un fichier correspondant est en contexte). Point notable : **un `.md` simple déposé dans `.cursor/rules` est ignoré** — le frontmatter y est obligatoire pour activer la règle.
[cursor.com/docs/context/rules](https://cursor.com/docs/context/rules) — consulté 2026-09-13.

**[F] GitHub Copilot** distingue les deux cas explicitement : `.github/copilot-instructions.md` est du **Markdown pur, sans frontmatter** — « Add natural language instructions to the file, in Markdown format » — tandis que `.github/instructions/*.instructions.md`, spécifiques à un chemin, exigent un **frontmatter YAML** avec `applyTo` (glob) et `excludeAgent` optionnel.
[GitHub Docs — Add repository instructions](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions) — consulté 2026-09-13.

**[H] La convention réelle de 2026 n'est donc pas « toujours du frontmatter ».** Les deux plus gros outils de développement assisté convergent sur la même règle : **Markdown pur pour le contenu narratif global, frontmatter YAML uniquement pour le ciblage conditionnel** — quel fichier, quel contexte, quel agent. Transposé à notre cas : le `.md` du commerçant n'a besoin de frontmatter que si plusieurs prompts coexistent (par canal, par établissement, par plage horaire). Sinon, du Markdown nu suffit et se relit mieux.

**[F] Vapi.** Une Knowledge Base est « a collection of custom files that contain information on specific topics or domains », intégrable via l'API ou le dashboard. Trois modes : bases standard, **bases personnalisées** (« implement your own document retrieval server, giving you complete control over how your assistant searches and retrieves information »), et Query Tool adossé à des identifiants de fichiers. Recommandation officielle : garder les fichiers individuels **sous 300 Ko** et bien structurés. Le prompt système doit explicitement instruire l'assistant d'utiliser la base de connaissances.
[Vapi — Introduction to Knowledge Bases](https://docs.vapi.ai/knowledge-base) · [Custom Knowledge Base](https://docs.vapi.ai/knowledge-base/custom-knowledge-base) · [Using the Query Tool](https://docs.vapi.ai/knowledge-base/using-query-tool) — consulté 2026-09-13.

Le mode « custom knowledge base » est structurant : il signifie qu'un serveur de récupération maison est un citoyen de première classe chez Vapi, pas un contournement.

**[F] ElevenLabs Agents.** Sources acceptées : fichiers, URL, texte. Formats : PDF, Word, Text, **Markdown**, HTML, EPUB. Limite de **20 Mo par fichier**. Deux modes d'usage : *full context* (le document entier entre dans le prompt système, plafonné à environ **300 000 caractères**) ou **RAG** (indexation préalable, récupération des seuls passages pertinents) ; les documents plus gros doivent passer en RAG. Le mode se règle sur `auto` (défaut), `prompt`, ou dépendant du RAG ; « the agent always accesses folders through RAG ».
[ElevenLabs — Knowledge base](https://elevenlabs.io/docs/agents-platform/customization/knowledge-base) — consulté 2026-09-13.

**[F] Retell AI** recommande des **prompts sectionnés** : « Break large prompts into focused sections for better organization and LLM comprehension. » Les sections proposées sont **Identity** (rôle et expertise de l'agent), **Style Guardrails** (ton et approche), **Response Guidelines** (formatage et règles d'interaction), **Task Instructions** (étapes opérationnelles), **Objection Handling** (réponses préparées aux objections courantes). Les exemples de la documentation sont rédigés en Markdown. Aucune limite de taille n'est donnée ; en revanche, au-delà de « more than 3-4 conditional paths » ou « 5+ different functions/tools », Retell recommande de basculer vers des agents de type Conversation Flow plutôt que d'étendre un prompt unique. Principe affiché : réutilisabilité, maintenabilité, clarté — l'organisation prime sur la taille brute.
[Retell AI — Prompt engineering guide](https://docs.retellai.com/build/prompt-engineering-guide) — consulté 2026-09-13.

**[H]** Cette liste de cinq sections est directement réutilisable comme **squelette du `.md` de tenant**, et elle a l'avantage de venir d'un acteur du vocal plutôt que d'une intuition. Elle donne aussi la structure des paliers du questionnaire de l'axe 5 : chaque palier remplit une section, et une section vide reste un fichier valide. Le seuil « 3-4 chemins conditionnels » est un signal d'alerte utile : au-delà, le problème n'est plus la connaissance de l'agent mais sa logique, et aucune quantité de Markdown ne le résoudra.

**[H]** Le seuil de ~300 000 caractères est une information de calibrage précieuse : en dessous, l'industrie considère qu'injecter tout le contexte est préférable au RAG. Pour un commerçant, une base de connaissance complète (horaires, services, tarifs, FAQ, politique d'annulation) tient très largement sous cette barre. Voir axe 6.

### 4.2 Le round-trip : la seule difficulté technique réelle de cet axe

Écrire un `.md` depuis une UI est trivial. Le **réécrire** sans détruire ce qu'un humain y a mis entre-temps ne l'est pas. Trois niveaux de perte à traiter séparément.

**[F] Préalable : le frontmatter n'a pas de spécification.** Ni YAML (1.1/1.2) ni CommonMark ne définissent la notion. C'est un motif adopté indépendamment par des dizaines d'outils, chacun avec ses délimiteurs et ses règles. Preuve directe : `remark-frontmatter` est une **extension à activer explicitement** dans une chaîne remark, et il **ne parse pas** le contenu du bloc — « Doesn't parse the data inside them: create your own plugin to do that ». Le nœud mdast produit est `{type: 'yaml', value: '<chaîne brute>'}`.
[remark-frontmatter README](https://github.com/remarkjs/remark-frontmatter) — consulté 2026-09-13.

**[F] gray-matter** (JS) accepte YAML (défaut), JSON et JavaScript, TOML via `options.engines`. **C'est un outil d'extraction, pas de préservation** : il ne conserve ni commentaires ni formatage d'origine lors d'un `stringify()` après modification.
[gray-matter README](https://github.com/jonschlinkert/gray-matter) — consulté 2026-09-13.

**[F] python-frontmatter** supporte YAML (défaut), JSON, TOML, avec `load()`/`dumps()` et `post.metadata`. Le README ne revendique aucune fidélité de round-trip. **[H]** Il s'appuie sur PyYAML par défaut, donc hérite de ses pertes sauf handler branché sur ruamel.yaml.
[python-frontmatter README](https://github.com/eyeseast/python-frontmatter) — consulté 2026-09-13.

**[F] YAML du frontmatter — Python : `ruamel.yaml`** est « a YAML parser/emitter that supports roundtrip preservation of comments, seq/map flow style, and map key order », implémente **YAML 1.2**, licence **MIT**. Les fonctions de module dépréciées (`load()`, `dump()`) ont été retirées au profit des méthodes d'instance `YAML()`. Extension C optionnelle via `ruamel.yaml[libyaml]`, la version pure Python conservant toutes les capacités de round-trip.
[PyPI — ruamel.yaml](https://pypi.org/project/ruamel.yaml/) — consulté 2026-09-13.

Le mode round-trip `YAML(typ='rt')` est **le mode par défaut**, pas une option secondaire. Cas limites documentés dans le changelog officiel, à connaître avant de promettre une fidélité parfaite : impossibilité d'avoir à la fois un commentaire avant et après un tag devant un nœud (corrigé en v0.18.4) ; saut de ligne parasite sur le premier élément après un commentaire suivi d'une séquence bloc imbriquée (v0.18.3) ; changement d'indentation des scalaires bloc de premier niveau (v0.18.16). Sécurité : `max_depth` limite la récursion, et `typ='unsafe'` est déprécié au profit de `typ='full'`.
[ruamel.yaml — documentation](https://yaml.dev/doc/ruamel.yaml/) — consulté 2026-09-13.

**[F] PyYAML ne préserve rien.** Aucune mention de conservation des commentaires dans l'intégralité du changelog du projet, et l'issue #90 confirme que les commentaires sont écartés au parsing et inaccessibles ensuite — classée comme demande de fonctionnalité jamais implémentée, pas comme bug.
[PyYAML CHANGES](https://github.com/yaml/pyyaml/blob/master/CHANGES) · [yaml/pyyaml#90](https://github.com/yaml/pyyaml/issues/90) — consulté 2026-09-13.

Pour un fichier qu'un humain relit, c'est disqualifiant : une sauvegarde depuis l'UI effacerait les annotations du commerçant sans aucun signal.

**[F] YAML — JavaScript : la bibliothèque `yaml` (eemeli/yaml)** supporte « parsing, modifying, and writing YAML comments and blank lines », donc l'édition aller-retour sans perte, sur **YAML 1.1 et 1.2**, licence **ISC**. Trois couches d'API : `parse()`/`stringify()` ; la classe `Document` avec ses nœuds (`Scalar`, `YAMLMap`, `YAMLSeq`, `Pair`, `Alias`) et les utilitaires `visit()`/`visitAsync()` qui modifient l'AST **en préservant formatage et commentaires** ; et un accès bas niveau lexer/parser/composer au CST.
[github.com/eemeli/yaml](https://github.com/eemeli/yaml) — consulté 2026-09-13.

Attention : les fonctions simples `parse()`/`stringify()` de cette bibliothèque **n'exposent pas** commentaires et formatage — seule la couche `parseDocument()` préserve. [même source]

**[R]** `ruamel.yaml` côté FastAPI, `yaml` (eemeli) côté Next.js si le front doit aussi écrire. Dans les deux cas, passer par la couche **Document/AST** et non par `parse` → objet → `stringify` : c'est cette dernière forme, apparemment innocente, qui détruit les commentaires.

**[F] Le corps Markdown, lui, n'a aucune garantie — et c'est assumé.** `mdast-util-to-markdown`, le sérialiseur de la chaîne remark, l'écrit noir sur blanc : « mdast-util-to-markdown will do its best to serialize markdown to match the syntax tree, but there are several cases where that is impossible. » Les valeurs par défaut normalisent activement le style : `bullet` à `*` (écrase `-` et `+`), `emphasis`/`strong` à `*` (écrase `_` et `__`), `fence` en backticks (écrase `~~~`), `rule` en `***`, `closeAtx: false` (supprime les `# titre #`), `setext: false` (convertit tout titre souligné en style ATX).
[mdast-util-to-markdown README](https://github.com/syntax-tree/mdast-util-to-markdown) — consulté 2026-09-13.

**[F]** Côté Python, aucune alternative ne comble ce trou. **mdformat** est « an opinionated Markdown formatter » qui vise l'équivalence de rendu HTML et **réécrit délibérément le style** — l'inverse exact du besoin. **mistletoe** et **marko** ne revendiquent aucune fidélité de round-trip.
[mdformat](https://github.com/executablebooks/mdformat) · [mistletoe](https://github.com/miyuchina/mistletoe) · [marko](https://github.com/frostming/marko) — consulté 2026-09-13.

**[R] La règle qui en découle, et c'est la plus importante de cet axe.** Traiter le fichier comme **deux zones de nature différente** : le frontmatter est reconstruit via la couche Document (ruamel.yaml ou eemeli/yaml), le **corps Markdown est une chaîne opaque que l'on ne reparse jamais**. On extrait le bloc frontmatter par délimiteurs, on le remplace, on reconcatène le corps octet pour octet. Faire passer le corps par un cycle parse → stringify remark, même « juste pour valider », réécrit silencieusement la prose du commerçant.

**[F] MDX** combine Markdown, JSX et JavaScript : composants importables, expressions JavaScript entre accolades, déclarations `import`/`export`.
[mdxjs.com — What is MDX](https://mdxjs.com/docs/what-is-mdx/) — consulté 2026-09-13.

**[F] Et la documentation MDX elle-même tranche la question**, dans sa section Sécurité :

> « MDX is a programming language. If you trust your authors, that's fine. If you don't, it's unsafe. Do not let random people from the internet write MDX. If you do, you might want to look into using `<iframe>`s with `sandbox`, but security is hard, and that doesn't seem to be 100%… you should probably also sandbox the whole OS using Docker or similar, perform rate limiting, and make sure processes can be killed when taking too long. »

[mdxjs.com — Getting started, section Security](https://mdxjs.com/docs/getting-started/) — consulté 2026-09-13. La politique de sécurité du dépôt confirme que l'exécution de code arbitraire est un comportement voulu et non une faille : la charge du bac à sable incombe à l'intégrateur. [mdx-js/mdx — security](https://github.com/mdx-js/mdx/security) — consulté 2026-09-13.

**[H] MDX est donc écarté sans hésitation.** Un commerçant qui décrit sa politique d'annulation est exactement le « random people from the internet » visé par cet avertissement. Le prix à payer serait iframe sandboxée, isolation de processus, Docker, limitation de débit et kill sur dépassement — pour configurer des horaires d'ouverture. Markdown + frontmatter YAML donne lisibilité, structure et diff sans aucune de ces surfaces.

### 4.3 Schéma comme source des questions

**[F] JSON Schema** : la version courante reste **2020-12** ; « The current version is 2020-12! The previous version was 2019-09. » Aucun draft plus récent n'est annoncé sur la page de spécification.
[json-schema.org/specification](https://json-schema.org/specification) — consulté 2026-09-13.

**[F] react-jsonschema-form (rjsf)** : licence **Apache 2.0**, version courante **v6.10.0**. Fournit `uiSchema` et des props de formulaire pour personnaliser le rendu.
[rjsf docs](https://rjsf-team.github.io/react-jsonschema-form/docs/) — consulté 2026-09-13.

**[F] Limites de rjsf sur les branchements conditionnels, à connaître avant de le choisir.** Le mot-clé `dependencies` est supporté mais **documenté comme obsolète par rjsf lui-même** : « react-jsonschema-form supports the `dependencies` keyword from an earlier draft of JSON Schema (note that this is not part of the latest JSON Schema spec, though) ». Il n'existe **aucune page dédiée à `if`/`then`/`else`**, absent de la table des matières JSON Schema de la documentation. `oneOf`, `anyOf` et `allOf` sont supportés, ce dernier fusionné via `@x0k/json-schema-merge`. L'internationalisation passe par la prop `translateString`, qui ne traduit que les **chaînes internes de rjsf** (boutons, messages d'erreur), pas les libellés métier — ceux-ci relèvent des `title`/`description` du schéma.
[rjsf — dependencies](https://rjsf-team.github.io/react-jsonschema-form/docs/json-schema/dependencies) — consulté 2026-09-13.

**[H] C'est une contrainte dirimante pour un questionnaire à branchements.** Un onboarding qui demande des questions différentes à un restaurant et à un salon de coiffure repose entièrement sur du conditionnel. Si le mécanisme officiel de JSON Schema 2020-12 (`if`/`then`/`else`) n'est pas documenté comme supporté et que l'alternative est marquée obsolète, rjsf oblige à porter la logique de branchement **hors du schéma**, dans du code applicatif — ce qui annule une bonne part de l'intérêt d'un formulaire piloté par schéma.

**[F] SurveyJS** : la **Form Library est gratuite et sous licence MIT** — elle parse un JSON de formulaire et rend des formulaires interactifs. Sont **payants** : Survey Creator (le constructeur visuel), PDF Generator, Dashboard. Tarifs par développeur : Basic 589 USD (renouvellement 239 USD/an), PRO 1 059 USD (419 USD/an), Enterprise à partir de 2 359 USD (939 USD/an). Accès perpétuel aux versions reçues, redistribution sans royalties.
[surveyjs.io/licensing](https://surveyjs.io/licensing) — consulté 2026-09-13.

**[H]** Distinction à retenir : on peut **rendre** des formulaires SurveyJS gratuitement et commercialement ; c'est **construire** les formulaires visuellement qui est payant. Pour un questionnaire dont le schéma est écrit par l'éditeur et non par le client, la partie payante ne sert à rien.

**[F] JSONForms** est « a declarative framework for efficiently building form-based web UIs », qui interprète JSON et JSON Schema **à l'exécution**. Architecture à **deux schémas** : le schéma de données, et un **UI schema** distinct qui gouverne ordre, visibilité et disposition. Une section « Rules » dédiée permet la visibilité conditionnelle. Intégrations React, Angular et Vue. Renderers par défaut pour tous les types, surchargeables.
Licence **MIT** (EclipseSource GmbH). Version 3.8.0 stable, support Angular 22 récent — projet actif.
[jsonforms.io/docs](https://jsonforms.io/docs/) · [LICENSE](https://github.com/eclipsesource/jsonforms/blob/master/LICENSE) — consulté 2026-09-13. **[NV]** Drafts JSON Schema exactement supportés : non précisés sur la page consultée.

**[F] Formily** (Alibaba) : licence **MIT**, cible React, React Native, Vue 2 et Vue 3. **[H]** La documentation détaillée et la communauté sont majoritairement sinophones, ce qui est un risque de support réel pour une équipe qui ne lit pas le chinois.
[github.com/alibaba/formily](https://github.com/alibaba/formily) — consulté 2026-09-13.

**[H]** La séparation schéma de données / schéma d'UI de JSONForms est exactement ce dont un questionnaire d'onboarding a besoin : l'ordre des questions, les branchements et le libellé évoluent constamment, alors que la forme de la config change rarement. Les mêler dans un seul document — ce que fait rjsf par défaut avec `uiSchema` en option — mène à modifier le contrat de données chaque fois qu'on veut déplacer une question.

**[F] Zod** dispose d'une conversion native vers JSON Schema, introduite en **3.23**, ciblant **Draft 2020-12** par défaut (Draft 7, Draft 4 et OpenAPI 3.0 disponibles en cible). Types non représentables et donc rejetés par défaut : `z.bigint()`, `z.symbol()`, `z.undefined()`, `z.void()`, `z.date()`, `z.map()`, `z.set()`, `z.transform()`, `z.nan()`, `z.custom()` — le paramètre `unrepresentable` permet de substituer `{}` ou de gérer soi-même.
[zod.dev/json-schema](https://zod.dev/json-schema) — consulté 2026-09-13.

**[F] Formbricks** : plateforme open source d'enquêtes, cœur sous **AGPLv3** (usage personnel et commercial libre, versions modifiées distribuables à condition de documenter les changements et leur date), plus une **édition entreprise** dans `/apps/web/modules/ee` nécessitant une clé de licence en auto-hébergement. Nuance importante : les **SDK clients** (`packages/js/`, `packages/android/`, `packages/ios/`, `packages/api/`) sont sous **MIT** — seul le serveur est AGPL. Prérequis : Node.js 18+, pnpm, Docker pour PostgreSQL et MailHog.
[github.com/formbricks/formbricks](https://github.com/formbricks/formbricks) — consulté 2026-09-13.

**[H] L'AGPLv3 est un point de vigilance réel pour un SaaS**, pas un détail de licence : sa clause réseau étend l'obligation de partage du code aux utilisateurs qui accèdent au logiciel à distance. Intégrer du code AGPL dans le produit — par opposition à le faire tourner comme service séparé — demande un examen juridique. rjsf (Apache 2.0) et SurveyJS Form Library (MIT) n'ont pas ce problème.

**[F] Pydantic v2** génère du JSON Schema conforme à **Draft 2020-12** et à **OpenAPI 3.1.0**, via `BaseModel.model_json_schema()` ou `TypeAdapter.json_schema()`. Le paramètre `mode` distingue `'validation'` (défaut, ce que le modèle accepte en entrée) de `'serialization'` (ce qu'il produit en sortie) — la différence est réelle, illustrée par `Decimal`, qui accepte plusieurs formats en validation mais sérialise uniformément en chaîne. Limites documentées : les namedtuples perdent leur type ; seules les clés de type chaîne sont valides en JSON ; `Callable` n'a pas de représentation ; les types personnalisés complexes exigent `__get_pydantic_core_schema__` ou `__get_pydantic_json_schema__`.
[Pydantic — JSON Schema](https://pydantic.dev/docs/validation/latest/concepts/json_schema/) — consulté 2026-09-13.

**[F] Chaîne de génération de types partagés.** FastAPI expose `/openapi.json` ; sa documentation officielle « Generate Clients » recommande désormais **Hey API** (`npx @hey-api/openapi-ts`) comme solution dédiée TypeScript, avec OpenAPI Generator en option multi-langage. [FastAPI — Generate Clients](https://fastapi.tiangolo.com/advanced/generate-clients/) — consulté 2026-09-13. Les autres outils restent actifs et valides : **openapi-typescript** (OpenAPI → types TS), **datamodel-code-generator** (JSON Schema/OpenAPI → Pydantic v2, gère `$ref`, `allOf`, `oneOf`, `anyOf`), **json-schema-to-typescript** (CLI `json2ts`), et **Ajv** pour la validation à l'exécution côté Node (drafts 04 → 2020-12 et JTD ; utilisé par ESLint, Webpack et Fastify).
[openapi-typescript](https://github.com/openapi-ts/openapi-typescript) · [datamodel-code-generator](https://github.com/koxudaxi/datamodel-code-generator) · [json-schema-to-typescript](https://github.com/bcherny/json-schema-to-typescript) · [ajv.js.org](https://ajv.js.org/) — consulté 2026-09-13.

**[H]** Pydantic et Zod ciblent **le même draft, 2020-12**. C'est ce qui rend le pattern « un seul schéma » réellement praticable : le JSON Schema produit par Pydantic est directement consommable par un générateur de formulaire côté front, et validable par Ajv ou Zod côté client si l'on veut un retour immédiat avant l'appel réseau. Le piège est le `mode` : c'est le schéma de **validation** qu'il faut exporter pour piloter un questionnaire, pas celui de sérialisation.

**[H] Le piège à connaître d'avance** : `z.date()` et `z.transform()` ne traversent pas la frontière JSON Schema. Un questionnaire qui contient des dates (horaires d'ouverture, périodes de fermeture) doit les modéliser en `z.string()` avec un format, pas en `z.date()`, sous peine de casser la génération de formulaire.

### 4.4 [R] Recommandation Axe 4

**Un schéma, deux artefacts, un round-trip discipliné.**

Source de vérité unique : **Pydantic côté FastAPI**, d'où sort un JSON Schema (`model_json_schema()`) exporté en build vers le front, qui pilote le rendu des questions. On évite ainsi de maintenir deux définitions divergentes du même questionnaire — la faute la plus courante et la plus coûteuse dans ce genre de produit.

Le fichier `.md` par tenant suit la convention AGENTS.md : **frontmatter YAML pour ce que la machine lit** (identité, voix, horaires structurés, drapeaux), **corps Markdown pour ce que l'humain écrit** (ton, FAQ, cas particuliers, interdits). Cette séparation n'est pas cosmétique : elle permet de régénérer le frontmatter depuis le questionnaire **sans jamais toucher au corps**, ce qui est la seule façon de laisser un commerçant écrire librement sans qu'une sauvegarde d'UI n'efface sa prose.

Règle dure qui en découle : **l'UI ne réécrit jamais le fichier entier.** Elle remplace le bloc frontmatter et laisse le reste intact, octet pour octet. Toute bibliothèque qui reparse et réémet le Markdown complet est un risque de perte.

---

## Axe 5 — Questionnaire d'onboarding



### 5.1 Ce que disent les données sur le nombre de questions

**[F] Baymard Institute.** Le parcours de commande américain moyen contient **23,48 éléments de formulaire** affichés par défaut, ou **14,88** si l'on ne compte que les champs. Le nombre idéal est de **12 à 14** champs, et la plupart des parcours peuvent réduire de **20 à 60 %** le nombre d'éléments affichés. **Les taux de complétion chutent de 4 à 6 % pour chaque champ au-delà du huitième.** Près d'un acheteur sur cinq a déjà abandonné un panier pour cause de parcours « trop long ou trop compliqué ». Le taux d'abandon moyen de 70,22 % est calculé à partir de 50 études distinctes.
[Baymard — Cart abandonment rate statistics](https://baymard.com/lists/cart-abandonment-rate) — consulté 2026-09-13.

**Réserve méthodologique importante [H]** : ces chiffres viennent d'un contexte **e-commerce transactionnel**, où l'utilisateur veut acheter et perçoit le formulaire comme un péage. Un onboarding de configuration d'agent vocal est un contexte **différent** : le commerçant a déjà signé, il construit son propre outil, et chaque question a une contrepartie visible. Transposer directement le seuil des « 8 champs » serait une erreur de raisonnement. Ce que le chiffre établit solidement, c'est la **forme** de la courbe — la friction croît avec le nombre de champs, de façon à peu près linéaire — pas le seuil absolu.

**[F] Zuko — la source la plus proche de notre cas.** Analyse de **1 362 formulaires sur 12 mois**, taux d'abandon **par champ** (n par champ indiqué) :

| Champ | Abandon moyen | Abandon médian | n |
|---|---|---|---|
| **Mot de passe** | **10,50 %** | 5,95 % | 238 |
| E-mail | 6,41 % | — | 1 003 |
| Téléphone | 6,28 % | — | 1 028 |
| Code postal | 4,82 % | — | 505 |
| Adresse | 4,32 % | — | 301 |

Le champ mot de passe cumule les pires indicateurs : 7,2 s de temps moyen et 0,65 retour au champ, les plus élevés de tous. Zuko signale lui-même que « the median abandonment rate is much lower than the mean » — la moyenne est tirée par une longue traîne de formulaires mal conçus.
[Zuko — Which form fields cause the biggest UX problems](https://www.zuko.io/blog/which-form-fields-cause-the-biggest-ux-problems) — consulté 2026-09-13.

Sur des millions de sessions (n exact non public), les formulaires de type **« Application »** — les plus proches d'un onboarding marchand — atteignent environ **75 %** de complétion depuis le démarrage ; les formulaires **« Registration »** comptent 14 champs en moyenne pour 1 min 35 de remplissage, avec un abandon survenant près du temps de complétion, ce qui suggère des **échecs de validation** plutôt que de la lassitude.
[Zuko — Benchmarking data comparing form types](https://www.zuko.io/blog/zuko-benchmarking-data-comparing-form-types) — consulté 2026-09-13. **[NV]** Aucune courbe « abandon en fonction du nombre de champs » n'est publiée, malgré une section qui pose la question.

**[H] Deux conséquences directes.** Le mot de passe étant statistiquement le point de friction le plus coûteux, il doit être isolé, simplifié (lien magique ou code à usage unique) ou repoussé — pas placé au milieu du questionnaire. Et le profil d'abandon des formulaires d'inscription pointe vers la **validation** plutôt que la longueur : soigner les messages d'erreur rapporte peut-être davantage que supprimer des questions.

**[F] Nielsen Norman Group — divulgation progressive.** Montrer d'abord les options importantes, les spécialisées à la demande, avec une mise en garde explicite : **jamais plus de deux niveaux de divulgation**, au-delà desquels les utilisateurs se perdent.
[NN/g — Progressive Disclosure](https://www.nngroup.com/articles/progressive-disclosure/) — consulté 2026-09-13.

**[H]** Plafond concret pour la conception du questionnaire : une question peut ouvrir une sous-question, cette sous-question ne doit pas en ouvrir une troisième.

**[F] Nielsen Norman Group — conception de formulaires.** Priorité à la réduction de la longueur : « Eliminating unnecessary fields requires more time, but the reduced user effort and increased completion rates make it worthwhile » — supprimer ce qui peut être déduit, collecté plus tard, ou omis. **Colonne unique** : « Multiple columns interrupt the vertical momentum of moving down the form », une ligne par champ, exception faite de champs courts logiquement liés (ville, code postal). **Libellés** immédiatement au-dessus du champ sur mobile et formulaires courts, à côté sur les très longs formulaires desktop, avec l'attribut `label` pour l'accessibilité. **Champs optionnels** : en limiter le nombre à un ou deux, clairement étiquetés comme tels — mais d'abord chercher à les supprimer. **Erreurs** : signalées sur plusieurs canaux simultanés (contour du champ **et** texte rouge **et** graisse), message spécifique, saisie erronée préservée pour correction.
[NN/g — Website Form Design](https://www.nngroup.com/articles/web-form-design/) — consulté 2026-09-13.

**[H]** La recommandation « un ou deux champs optionnels au maximum » entre en tension frontale avec un questionnaire d'onboarding où l'essentiel est optionnel par nature — un commerçant peut très bien ne pas vouloir décrire sa politique d'annulation. La résolution n'est pas d'ignorer NN/g mais de **changer de granularité** : chaque palier du questionnaire (voir 5.2) ne comporte que des champs requis, et c'est le **palier entier** qui est optionnel. On passe d'un long formulaire majoritairement facultatif à une suite de courts formulaires entièrement obligatoires, ce qui satisfait la règle sans amputer la config.

**[F] Nielsen Norman Group — indicateurs de progression.** Un retour visuel immédiat est nécessaire pour toute action dépassant environ **1 seconde**. Animation en boucle pour 2 à 10 secondes (à éviter sous 1 s : distrayant ; au-delà de 10 s : l'utilisateur s'impatiente) ; indicateur de pourcentage au-delà de **10 secondes**. Une étude de l'université du Nebraska-Lincoln citée par NN/g montre que les utilisateurs voyant une barre de progression animée ont exprimé une satisfaction supérieure et **ont accepté d'attendre en moyenne trois fois plus longtemps**. Recommandations complémentaires : accompagner d'un texte explicatif, démarrer l'animation lentement puis l'accélérer, estimer le temps restant généreusement.
[NN/g — Progress Indicators](https://www.nngroup.com/articles/progress-indicators/) — consulté 2026-09-13.

**[H]** Ce résultat porte sur l'attente machine, pas sur la progression dans un formulaire — mais le mécanisme sous-jacent (rendre l'effort restant visible et fini) est le même, et il justifie d'afficher une progression explicite dans un questionnaire long.

**[NV] Sur l'effet de gradient de but**, souvent invoqué pour justifier les barres de progression : la référence bibliographique est confirmée — Kivetz, Urminsky & Zheng (2006), « The Goal-Gradient Hypothesis Resurrected », *Journal of Marketing Research* 43(1), 39-58, DOI [10.1509/jmkr.43.1.39](https://doi.org/10.1509/jmkr.43.1.39) — mais l'article est derrière un péage et son texte intégral n'a pas pu être consulté. **Aucun des chiffres qui circulent sur le web à son sujet ne doit être présenté comme établi.** L'application à l'onboarding reste une extrapolation produit plausible, pas une citation.

### 5.2 Le wizard : le bon patron, avec ses défauts documentés

**[F] NN/g sur les assistants pas-à-pas.** Recommandés « for novice users or infrequent processes (e.g., configuration or setup) » — exactement le cas d'un commerçant qui configure son agent une fois. Présenter une étape à la fois pour réduire la charge cognitive. Navigation : boutons précédent/suivant avec des **libellés descriptifs** plutôt que « Suivant » générique, ordre séquentiel clair sans saut en avant, et une liste ou un diagramme visible de toutes les étapes avec la position courante mise en évidence. **Sauvegarde** : « Allow users to exit the wizard midway and save state. Allow them to resume the process at a later time. »
Problèmes d'utilisabilité connus, que NN/g énumère sans détour : coût d'interaction supérieur (plus de clics), difficulté à comparer des informations entre étapes, mauvaise récupérabilité en cas d'interruption, accès bloqué à des informations de contexte nécessaires, contrôle et créativité limités, caractère fastidieux en usage répété.
[NN/g — Wizards](https://www.nngroup.com/articles/wizards/) — consulté 2026-09-13.

**[H]** Deux de ces défauts frappent directement notre cas et appellent une réponse explicite. **« Tedious for repetitive tasks »** : le wizard convient à la configuration initiale, **jamais** à la modification ultérieure — il faut donc prévoir dès le départ un second mode d'édition, direct et non séquentiel, pour le commerçant qui veut juste changer un horaire six mois plus tard. **« Poor recoverability if interrupted »** : c'est précisément ce que la sauvegarde après chaque réponse annule, et c'est la raison pour laquelle cette sauvegarde n'est pas une commodité mais une nécessité.

### 5.3 Reprise : le seul modèle nommé et documenté est celui de Stripe

**[F] Stripe Connect** distingue explicitement deux régimes : l'**upfront onboarding** (`eventually_due`, tout demander d'emblée) et l'**incremental onboarding** (`currently_due`, le strict minimum à l'inscription, complété progressivement à mesure que le compte génère du revenu). Le flux repose sur un Account Link avec `refresh_url` et `return_url` ; l'utilisateur peut **enregistrer pour plus tard à tout moment**, sans garantie de complétion — la plateforme re-vérifie l'état via `GET /accounts` ou le webhook `account.updated`. Stripe recommande par ailleurs de ne demander que les `capabilities` réellement nécessaires, et permet le pré-remplissage avant génération du lien.
[Stripe — Connect onboarding](https://docs.stripe.com/connect/onboarding) — consulté 2026-09-13 (via recherche indexée, fetch du domaine bloqué).

**[H]** C'est le seul patron **nommé** de sauvegarde progressive multi-étapes trouvé dans une documentation officielle. Côté front, il n'existe pas d'équivalent : ni React Hook Form ni Formik ne documentent d'autosave. Le débounce de 300 à 1 000 ms suivi d'un `PATCH` serveur est une convention d'ingénierie, pas une doctrine de framework — **[NV]**.

**[F] Et le brouillon local ne suffit pas.** `localStorage` est strictement cloisonné par origine, effacé à la fermeture en navigation privée, et **ne se synchronise jamais entre appareils**.
[MDN — Window.localStorage](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage) — consulté 2026-09-13.

**[H]** Un commerçant qui commence sur son téléphone au comptoir et reprend sur l'ordinateur du bureau le soir est le cas nominal, pas l'exception. L'état doit vivre en base, pas dans le navigateur.

**[F] Ordre des questions : les trois produits du secteur convergent.** Vapi (« moins de 5 minutes » annoncées) : nom et modèle → premier message et prompt système → numéro de téléphone → test. Retell : compte → type d'agent (prompt unique ou flux conversationnel) → configuration → **test web gratuit** → achat du numéro → test réel. ElevenLabs : compte → assistant → premier message et prompt → base de connaissances → voix → test → critères d'analyse.
[Vapi — Dashboard quickstart](https://docs.vapi.ai/quickstart/dashboard) · [Retell — Quickstart](https://docs.retellai.com/general/quickstart) · [ElevenLabs — Agents quickstart](https://elevenlabs.io/docs/agents-platform/quickstart) — consulté 2026-09-13.

**[H] La règle commune est nette : identité → contenu → configuration → provisionnement coûteux ou irréversible en dernier, et test avant provisionnement.** Vapi et Retell font tous deux essayer l'agent **avant** l'achat du numéro. Transposé : ne jamais demander le numéro de téléphone, les coordonnées bancaires ou quoi que ce soit d'engageant avant que le commerçant ait entendu son agent parler.

### 5.4 [R] Recommandation Axe 5

**Découper en paliers qui produisent chacun un résultat utilisable.**

Plutôt que de viser « le moins de questions possible » — objectif contre-productif quand chaque réponse améliore réellement l'agent — viser **un agent fonctionnel au bout de 5 à 7 questions**, puis proposer des paliers d'enrichissement facultatifs. Le commerçant doit pouvoir entendre son agent parler avant d'avoir tout rempli. C'est le seul argument qui résiste à la fatigue de formulaire : la contrepartie est immédiate et audible.

Structure des paliers, calquée sur les sections que Retell documente (4.1) pour que chaque palier remplisse une section du `.md` :

| Palier | Contenu | Effet visible |
|---|---|---|
| 0 — Identité | Nom, métier, ville, langue, voix | L'agent décroche et se présente |
| 1 — Disponibilité | Horaires, jours de fermeture, délai de rendez-vous | L'agent sait quand proposer |
| 2 — Prestations | Liste, durées, tarifs | L'agent sait quoi proposer |
| 3 — Ton et garde-fous | Vouvoiement, formules, interdits | L'agent parle comme la maison |
| 4 — Objections et cas limites | FAQ, annulations, urgences, escalade humaine | L'agent ne se bloque plus |

Le palier 0 seul doit produire un agent qui décroche. C'est la seule chose qui rend la suite désirable.

Corollaires : une question par écran avec branchements (un restaurant et un salon de coiffure ne répondent pas aux mêmes questions), **sauvegarde serveur après chaque réponse** et non à la fin, reprise par lien, et un **score de complétude** affiché en permanence qui rend visible ce qui manque encore et ce que cela coûterait à l'agent de ne pas le savoir.

---

## Axe 6 — Mémoire de l'agent

### 6.1 Le budget de latence commande l'architecture

**[F] LiveKit** publie la formule de latence de bout en bout d'un agent vocal :

```
total_latency = eou.end_of_utterance_delay + llm.ttft + tts.ttfb
```

et expose les métriques correspondantes : `LLMMetrics` (`ttft`, `duration`, `prompt_tokens`, `completion_tokens`, `prompt_cached_tokens`, `tokens_per_second`, `speech_id`), `STTMetrics` (`audio_duration`, `duration`, `streamed`), `TTSMetrics` (`ttfb`, `audio_duration`, `characters_count`, `duration`, `speech_id`), `EOUMetrics` (`end_of_utterance_delay`, `transcription_delay`, `on_user_turn_completed_delay`), `VADMetrics` (`idle_time`, `inference_duration_total`, `inference_count`). Collecte par l'événement `metrics_collected`, corrélation entre étapes par `speech_id`.
[LiveKit — Capturing metrics](https://docs.livekit.io/agents/ops/logging/) — consulté 2026-09-13.

**[H] Lecture décisive de cette formule** : le temps de récupération de connaissance n'y figure pas comme terme séparé. Il est **absorbé dans `llm.ttft`** — c'est-à-dire qu'il retarde le premier token, donc la première syllabe. Chaque milliseconde de RAG est une milliseconde de silence perçu. C'est pour cela qu'un budget de 300 ms pour la récupération est en réalité très généreux : il consomme l'essentiel de la marge disponible avant que la conversation ne paraisse lente.

**[F]** La contrainte est confirmée par la littérature : un article d'arXiv de mars 2026 (arXiv:2603.02206, *VoiceAgentRAG*) pose explicitement la latence RAG comme goulot d'étranglement des agents vocaux temps réel, et propose une architecture à deux agents : un « Slow Thinker » qui analyse le dialogue en continu, anticipe les sujets à venir et pré-charge les extraits pertinents dans un cache sémantique FAISS, et un « Fast Talker » qui ne lit que ce cache, éliminant toute requête vectorielle sur un succès de cache — avec des temps de réponse annoncés « sub-millisecond ».
[arXiv:2603.02206](https://arxiv.org/abs/2603.02206) — consulté 2026-09-13. **[H]** L'abstract ne fournit pas de métriques de bout en bout ; je ne présente donc pas ce travail comme une validation empirique, mais comme la confirmation que le problème est réel et reconnu.

### 6.2 Fichiers .md, base vectorielle, ou graphe ?

**[F] pgvector v0.8.6** : deux types d'index. **HNSW** — « better query performance than IVFFlat (in terms of speed-recall tradeoff), but has slower build times and uses more memory ». **IVFFlat** — construction plus rapide, moins de mémoire, performance de requête inférieure. La construction HNSW est nettement plus rapide quand le graphe tient dans `maintenance_work_mem`, que la documentation suggère de porter autour de **8 Go**. Dimensions maximales : 2 000 (`vector`), 4 000 (`halfvec`), 64 000 (`bit`), 1 000 éléments non nuls (`sparsevec`). Opérateurs : `<->` (L2), `<#>` (produit scalaire négatif), `<=>` (cosinus), `<+>` (L1), `<~>` (Hamming), `<%>` (Jaccard).
[github.com/pgvector/pgvector](https://github.com/pgvector/pgvector) — consulté 2026-09-13.

**[H]** La recommandation de 8 Go de `maintenance_work_mem` pour HNSW est **hors d'atteinte sur un VPS de 1 Go**. Sur de très petits volumes (quelques centaines de chunks par tenant), l'index n'est de toute façon pas nécessaire : une recherche séquentielle sur quelques centaines de vecteurs est instantanée. Le problème ne se pose qu'à partir de quelques dizaines de milliers de chunks — un horizon qu'un commerçant individuel n'atteint jamais.

**[F] Calibrage industriel.** ElevenLabs place le seuil du passage obligatoire au RAG autour de **300 000 caractères** de contexte complet ; Vapi recommande des fichiers sous **300 Ko** (voir 4.1).

**[H] Conséquence directe et contre-intuitive.** Une base de connaissance de commerçant — horaires, prestations, tarifs, FAQ, politique d'annulation, ton de voix, interdits — pèse typiquement quelques dizaines de milliers de caractères. **Elle tient entièrement dans le contexte.** Construire un pipeline RAG pour cela, c'est ajouter une latence de récupération, une dépendance d'embedding, un index et une source d'erreur (le mauvais chunk récupéré) pour résoudre un problème qu'on n'a pas.

**[F] Le levier qui remplace le RAG ici : le prompt caching.** Le mécanisme stocke le traitement du préfixe d'un prompt — prompt système, définitions d'outils, documents — pour que les requêtes ultérieures partageant ce préfixe ne le retraitent pas. Le bénéfice est une réduction directe du **TTFT**, donc du terme dominant de la formule LiveKit. Les agents de support client sont décrits comme un cas d'usage quasi idéal : long prompt système partagé, mêmes définitions d'outils à chaque tour, référence constante à une base de connaissance stable.
Synthèse de sources secondaires convergentes ([Redis — prompt vs semantic caching](https://redis.io/blog/prompt-caching-vs-semantic-caching/), [Parloa](https://www.parloa.com/knowledge-hub/prompt-caching/)) — consulté 2026-09-13. **[NV]** Je n'ai pas vérifié les conditions exactes de mise en cache chez un fournisseur donné (taille minimale de préfixe, durée de vie) ; elles varient et doivent être lues dans la documentation du fournisseur retenu avant de dimensionner le prompt.

### 6.3 Versions et « qui a changé quoi »

**[H]** Deux besoins distincts, souvent confondus. **L'historique métier** — qui a modifié quoi, quand, et pouvoir revenir en arrière — est un besoin produit, visible par le commerçant. **Le versionnage git** est un mécanisme, utile surtout pour le diff et la réconciliation. Les deux se recouvrent mais ne se substituent pas : un commerçant ne lira jamais un `git log`.

**[F] Piège de bibliothèque à connaître avant d'écrire la première ligne.** GitPython avertit explicitement qu'il « is not suited for long-running processes (like daemons) as it tends to leak system resources » — conséquence de destructeurs qui ne s'exécutent plus de façon déterministe en Python moderne. Les contournements proposés sont l'appel manuel des méthodes de nettoyage, ou l'exécution de GitPython dans un processus séparé tué périodiquement. Licence New BSD.
[GitPython — Introduction](https://gitpython.readthedocs.io/en/stable/intro.html) — consulté 2026-09-13.

**[H]** Un serveur FastAPI *est* un processus long. Utiliser GitPython dans le handler d'une route qui sauvegarde un `.md` tombe exactement dans le cas déconseillé par ses propres auteurs.

**[F] Les deux alternatives Python.** **pygit2** s'appuie sur libgit2, donc sur une dépendance système à compiler et maintenir (Python 3.11–3.14 et PyPy). **Dulwich** est **pur Python sans aucune dépendance externe** — pas de binaire `git` à garantir, pas de libgit2 à construire — avec des extensions Rust optionnelles activées si présentes, une API porcelaine complète (clone, pull, push, commit, diff) et un accès bas niveau. Python 3.10+.
[pygit2.org](https://www.pygit2.org/) · [dulwich.io](https://www.dulwich.io/) — consulté 2026-09-13. **[NV]** Aucune comparaison de performance chiffrée entre les trois n'a été trouvée.

**[R]** **Dulwich** sur un petit VPS : c'est le seul des trois qui n'ajoute ni dépendance système, ni binaire à provisionner, ni fuite de ressources documentée dans un démon.

**[F] L'attribution se règle nativement côté git.** `git commit --author="A U Thor <author@example.com>"` remplace l'auteur, et les variables d'environnement `GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`, `GIT_AUTHOR_DATE` sont prioritaires sur la configuration — mécanisme prévu pour les scripts et processus automatisés qui doivent fixer l'auteur par programme.
[git-commit — documentation](https://git-scm.com/docs/git-commit) — consulté 2026-09-13.

**[H]** C'est exactement ce qu'il faut : **committer technique fixe, auteur = l'utilisateur réel** de l'interface (par exemple `commercant-42@votreapp.internal`). Toutes les bibliothèques exposent l'équivalent via un paramètre `author` ou une `Signature`.

**[R]** Le `.md` par tenant vit dans un dépôt git sur le VPS, un commit par sauvegarde, message et auteur portant l'identité réelle de l'utilisateur qui a validé le questionnaire (pas « système »). Le diff git alimente une vue produit lisible — « Horaires du samedi modifiés par Karim, hier à 14h » — et le rollback est un `git checkout` d'une version antérieure du fichier. La table `tenant_config` append-only (2.2) porte le même historique pour la partie structurée. Le point d'attention réel est le **conflit** : si le commerçant édite le corps Markdown pendant qu'un job régénère le frontmatter, il faut que la seconde opération ne touche pas au corps — ce qui ramène exactement à la règle de l'axe 4 : **on remplace le bloc frontmatter, jamais le fichier.**

### 6.4 [R] Recommandation Axe 6

**Pas de base vectorielle au départ. Le fichier .md, entier, dans le prompt, mis en cache.**

Ordre d'escalade, et chaque palier n'est franchi que lorsque le précédent a démontré sa limite par la mesure :

1. **Fichier `.md` complet injecté dans le prompt système, avec prompt caching.** Latence de récupération : zéro. Qualité : maximale, l'agent voit tout. Tient jusqu'à plusieurs dizaines de milliers de caractères — c'est-à-dire jusqu'au-delà du besoin réel d'un commerçant.
2. **Découpage par section avec sélection déterministe** (par exemple : n'injecter la section « livraison » que si le commerçant l'a activée). Toujours zéro appel vectoriel, simplement moins de tokens.
3. **pgvector dans le PostgreSQL déjà présent**, sans index au départ puis IVFFlat, uniquement si un tenant dépasse réellement le contexte utile. Aucune base vectorielle séparée : elle ajouterait un service à faire tenir dans 1 Go pour un gain que l'étape 1 rend invisible.
4. **Pré-chargement anticipé** façon *VoiceAgentRAG* : à réserver au cas où l'étape 3 serait atteinte et mesurée trop lente. C'est de la recherche appliquée, pas un point de départ.

Le graphe de connaissances est écarté à tous les paliers : il résout des questions de relations multi-sauts qu'un agent de prise de rendez-vous ne pose jamais.

---

## Axe 7 — Observabilité et évaluation

### 7.1 OpenTelemetry GenAI : utile, mais pas encore stable

**[F]** Les conventions sémantiques GenAI ont été **sorties du dépôt principal** des semantic conventions OpenTelemetry vers un dépôt dédié, `open-telemetry/semantic-conventions-genai`, qui couvre « spans, metrics, and events for GenAI clients, MCP (Model Context Protocol), and provider-specific conventions (OpenAI, etc.) ». La section « Schema URL » du dépôt est encore marquée TODO.
[github.com/open-telemetry/semantic-conventions-genai](https://github.com/open-telemetry/semantic-conventions-genai) — consulté 2026-09-13.

**[F, via recherche indexée]** À la mi-2026, **aucun attribut, span, métrique ou événement `gen_ai.*` n'est marqué Stable** : tous portent le badge « Development ». La séparation en dépôt dédié (release v1.42.0, 12 juin 2026) est un changement d'organisation destiné à donner un rythme de publication propre à ce travail rapide, **pas une graduation vers la stabilité**. L'énumération `gen_ai.operation.name` couvre notamment `chat`, `create_agent`, `invoke_agent`, `invoke_workflow`, `plan`, `execute_tool`, `embeddings`, `retrieval`.
Le domaine `opentelemetry.io` était bloqué au fetch dans cette session ; ces éléments proviennent de sources de synthèse concordantes et du dépôt officiel ci-dessus. **[NV]** à revérifier directement sur `opentelemetry.io/docs/specs/semconv/gen-ai/` avant toute décision d'architecture.

**[NV] Conventions spécifiques à l'audio, la parole ou les modèles temps réel : rien trouvé.** Le dépôt officiel n'en mentionne pas. C'est une lacune réelle : les métriques qui comptent pour un agent vocal — délai de fin de parole, TTFB du TTS, interruptions — n'ont pas de convention normalisée.

**[H]** La conséquence pratique est rassurante plutôt qu'inquiétante : puisqu'il n'existe pas de norme pour le vocal, personne n'est en retard. Adopter les attributs `gen_ai.*` existants pour la partie LLM et **nommer soi-même** les attributs vocaux, en calquant le vocabulaire LiveKit (`end_of_utterance_delay`, `ttft`, `ttfb`), est la stratégie la moins risquée : on suit une convention documentée par un acteur du domaine plutôt que d'inventer.

### 7.2 Outils auto-hébergeables : le mur des 1 Go

**[F] Langfuse** dépend de **quatre** systèmes de stockage : PostgreSQL (transactionnel), **ClickHouse** (OLAP, stocke traces, observations et scores), Redis/Valkey (file et cache), et un stockage objet S3 (événements entrants, entrées multimodales, exports). Docker Compose est présenté comme « single VM without high availability, scaling, or backups », adapté aux tests locaux ; Kubernetes/Helm est recommandé pour la production. Certaines fonctionnalités additionnelles requièrent une clé de licence.
[langfuse.com/self-hosting](https://langfuse.com/self-hosting) — consulté 2026-09-13.

**[F, via recherche indexée]** Langfuse recommande au minimum 2 CPU et 4 Go de RAM pour l'ensemble des conteneurs ; les guides de déploiement évoquent 4 vCPU et 8 Go, voire 4 cœurs et 16 Go pour la production. ClickHouse consomme à lui seul plus de 2 Go, et en dessous de 4 Go de RAM totale le démarrage échoue silencieusement. Les besoins ont approximativement doublé entre la v2 et la v3.
[Langfuse — ClickHouse (self-hosted)](https://langfuse.com/self-hosting/deployment/infrastructure/clickhouse) · [langfuse discussion #5785](https://github.com/orgs/langfuse/discussions/5785) — consulté 2026-09-13.

**Verdict sans ambiguïté : Langfuse est hors de portée d'un VPS de 1 à 2 Go.** Ce n'est pas une question de réglage, c'est ClickHouse.

**[F] Phoenix (Arize)** est « completely free to self-host » sans frais de licence, limite d'usage ni restriction de fonctionnalité, avec possibilité d'air-gap complet. Neuf modes de déploiement : terminal/CLI local, Docker, Docker Compose, Kubernetes, Helm, AWS CloudFormation, Railway, Render, Google Cloud Run, Azure ARM. Authentification (OAuth2, LDAP, comptes locaux), RBAC, politiques de rétention. Recommandation : épingler une version plutôt que `latest`.
[arize.com/docs/phoenix/self-hosting](https://arize.com/docs/phoenix/self-hosting) — consulté 2026-09-13. **[NV]** La page ne documente ni les backends de stockage (SQLite vs PostgreSQL), ni les besoins en ressources.

**[H]** Le mode « terminal/CLI local » et l'absence de dépendance OLAP annoncée font de Phoenix un candidat nettement plus plausible que Langfuse sur une petite machine — mais sans chiffre officiel, cela reste à mesurer avant de s'engager. À traiter comme un test d'une heure, pas comme un acquis.

### 7.3 Évaluation automatique

**[F] LiveKit Agents** fournit un cadre de test intégré à **pytest** (Python) et **Vitest** (Node), avec évaluation par **LLM-as-judge**. Exemple officiel :

```python
result = await session.run(user_input="Hello")
await result.expect.next_event().is_message(role="assistant").judge(
    llm, intent="Makes a friendly introduction and offers assistance."
)
```

Dimensions couvertes : contenu et intention des messages, invocation d'outils avec les bons arguments, gestion d'erreur, ancrage factuel (absence d'hallucination), résistance aux usages détournés. Assertions tour par tour et sur des conversations multi-tours.
[LiveKit — Testing and evaluation](https://docs.livekit.io/agents/build/testing/) — consulté 2026-09-13.

C'est le point le plus directement actionnable de tout cet axe : un cadre d'évaluation d'agent vocal qui s'exécute en CI comme des tests unitaires, sans infrastructure.

**[F] promptfoo** : CLI et bibliothèque d'évaluation et de red-teaming d'applications LLM, **licence MIT**, open source (le projet indique être resté open source après son rachat par OpenAI). Exécution **100 % locale** — « your prompts never leave your machine ». Intégration CI/CD et scan de code pour les problèmes de sécurité et de conformité liés aux LLM. Prérequis Node.js ≥ 22.22.0, Node 24 LTS recommandé.
[github.com/promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) — consulté 2026-09-13.

**[F] Pipecat** expose un motif d'observateurs non intrusifs sur le flux de frames, avec des observateurs intégrés : `LLMLogObserver`, `TranscriptionLogObserver`, `ServiceMetricsObserver` (« reports service latency and usage metrics as structured records »), `StartupTimingObserver`, `UserBotLatencyObserver`, `TurnTrackingObserver`. Méthodes `on_push_frame()` et `on_process_frame()`.
[Pipecat — Observer pattern](https://docs.pipecat.ai/server/utilities/observers/observer-pattern) — consulté 2026-09-13.

### 7.4 Enregistrement des appels : la contrainte juridique

**[F] CNIL** — l'enregistrement de conversations téléphoniques peut reposer sur la base légale du **contrat** (article 6.1.b du RGPD) lorsqu'il s'agit d'établir la preuve de la formation d'un contrat ne pouvant être prouvé autrement ; l'enregistrement doit alors être déclenché ponctuellement et non systématiquement.
[CNIL — L'enregistrement des conversations téléphoniques afin d'établir la preuve de la formation d'un contrat](https://www.cnil.fr/fr/lenregistrement-des-conversations-telephoniques-afin-detablir-la-preuve-de-la-formation-dun-contrat) — consulté 2026-09-13.

**[F, via recherche indexée]** Un référentiel CNIL publié le **2 avril 2026** encadre les durées de conservation des enregistrements d'appels sur le lieu de travail : de l'ordre de **12 mois**, réduits à **6 mois** pour les finalités d'évaluation, sauf obligation légale contraire. Finalité, base légale et information des personnes doivent être définies **avant** la mise en service.
**[NV]** Je n'ai pas pu ouvrir directement le référentiel du 2 avril 2026 ; cette date et ces durées proviennent de sources secondaires concordantes. **À faire vérifier avant toute mise en production, idéalement par un juriste** — ce n'est pas un point où une approximation est acceptable.

**[H]** Distinction qui change tout sur le plan technique : la **transcription** et l'**audio brut** n'ont pas le même statut ni le même risque. Une transcription texte, purgée des données non nécessaires, suffit à l'immense majorité des besoins d'exploitation (évaluation, débogage, statistiques). Conserver l'audio est un choix coûteux en stockage et en risque, qui doit être justifié finalité par finalité.

### 7.5 [R] Recommandation Axe 7

**Instrumenter tout de suite, outiller le plus tard possible.**

1. **Dès le premier appel**, écrire dans PostgreSQL une ligne par tour de parole avec les champs empruntés au vocabulaire LiveKit : `end_of_utterance_delay`, `llm_ttft`, `tts_ttfb`, `total_latency`, tokens entrée/sortie/cachés, `speech_id`, `tenant_id`. Une table, un index sur `(tenant_id, created_at)`. Ces cinq colonnes répondent déjà à « pourquoi cet agent est lent » et à « combien cet appel a coûté », ce qui couvre l'essentiel des questions qu'on se pose les six premiers mois.
2. **Tracing OpenTelemetry** avec les attributs `gen_ai.*` pour la partie LLM, en sachant qu'ils sont en *Development* et bougeront — donc en les isolant derrière une petite couche d'émission maison plutôt qu'en les câblant partout. Les attributs vocaux sont nommés d'après LiveKit, faute de convention.
3. **Évaluation par LLM-as-judge en CI**, sur le modèle du cadre de test LiveKit ou de promptfoo : un jeu d'une vingtaine de scénarios par type de commerce, exécuté à chaque modification du prompt. C'est ce qui empêche qu'une amélioration de la config d'un tenant casse silencieusement un autre. Coût d'infrastructure : nul.
4. **Détection d'échec par règles avant tout LLM** : appel raccroché sous 10 secondes, plus de trois reformulations consécutives, silence de l'agent au-delà d'un seuil, demande explicite d'un humain. Ces quatre règles attrapent la majorité des échecs réels pour quelques dizaines de lignes.
5. **Langfuse : non**, tant que l'infrastructure est un VPS de 1 à 2 Go — ClickHouse à lui seul dépasse le budget. **Phoenix : à tester**, sans s'y engager avant mesure. Une vue produit maison sur la table de l'étape 1 rend 80 % du service pour 0 % de la RAM.
6. **Audio : par défaut, ne pas conserver.** Transcription oui, audio uniquement sur finalité explicite, consentement documenté et rétention bornée. Le référentiel CNIL doit être lu en entier avant la mise en service.

---

## Synthèse transversale : les cinq décisions qui tiennent l'ensemble

1. **La logique vit dans un package npm, jamais dans un script hébergé.** C'est ce qui rend possible à la fois le loader web, le custom element, le wrapper React et — plus tard — l'extension MV3 qui interdit le code distant.
2. **Le micro décide de la frontière d'origine.** Servir le module en same-origin quand on le peut ; sinon, faire créer l'iframe avec `allow="microphone"` par le loader lui-même, et documenter CSP et Permissions Policy comme Stripe le fait.
3. **Un schéma Pydantic, deux artefacts.** Le questionnaire, la validation et le frontmatter du `.md` descendent tous de la même définition. Et l'UI remplace le bloc frontmatter, jamais le fichier.
4. **Pas de base vectorielle, pas de ClickHouse, pas de Vault.** Trois services que le VPS ne peut pas porter, pour trois problèmes que le volume réel ne pose pas encore. PostgreSQL avec RLS, chiffrement applicatif, et le `.md` entier dans un prompt mis en cache.
5. **Mesurer avant d'outiller.** Cinq colonnes de latence en base répondent aux questions des six premiers mois. Chaque palier d'escalade — RAG, Phoenix, extension, Lago — se franchit sur une mesure, pas sur une intuition.

---

## Points explicitement non vérifiés

- Page CSP officielle dédiée chez Intercom : introuvable.
- Statut d'implémentation cross-browser stable des Scoped Custom Element Registries en septembre 2026.
- Équivalent Firefox à `chrome.offscreen` pour l'audio et WebRTC en arrière-plan — **risque non levé** pour toute ambition cross-browser.
- Frais de signature et de revue chez Firefox AMO (gratuité probable, jamais écrite noir sur blanc dans les sources consultées).
- Empreinte mémoire réelle de Lago et de Phoenix auto-hébergés.
- Backends de stockage et besoins en ressources de Phoenix (non documentés sur la page de self-hosting).
- Contenu exact du référentiel CNIL du 2 avril 2026 sur les durées de conservation des enregistrements d'appels.
- Conventions sémantiques OpenTelemetry pour l'audio, la parole et les modèles temps réel : **inexistantes à ma connaissance**.
- Drafts JSON Schema exactement supportés par JSONForms : non précisés.
- Limites de taille des prompts et bases de connaissance chez Retell AI : non documentées.
- Format exact du prompt système de Vapi (Markdown ou structuré) : non documenté.
- Comparaison de performance chiffrée entre GitPython, pygit2 et Dulwich : introuvable.
- Chiffres de l'article Kivetz, Urminsky & Zheng 2006 sur le gradient de but : article sous péage, **aucun chiffre ne doit être cité**.
- Courbe « taux d'abandon en fonction du nombre de champs » chez Zuko : posée comme question, jamais publiée.
- Statistique fréquemment citée sur les formulaires en colonne unique (« 15,4 s plus rapide, 42 % d'erreurs en moins ») : source primaire introuvable, **à ne pas reprendre**.
- Chiffres Formstack, HubSpot, Unbounce, Venture Harbour, WPForms sur l'abandon : non consultés (budget de recherche épuisé).
- Taux de récupération d'une relance par e-mail sur formulaire abandonné : aucun chiffre trouvé.
- Ordre exact du paramétrage d'Intercom Fin, et parcours d'onboarding de Cal.com : pages inaccessibles.
- Attribution des commits chez Decap CMS : absente de la documentation officielle.
- Motif d'autosave par question côté React Hook Form ou Formik : aucune documentation officielle, convention d'ingénierie seulement.
- Conditions exactes de prompt caching (taille minimale de préfixe, durée de vie du cache) chez un fournisseur donné.
- Aucun chiffre de performance de ce rapport n'est une mesure faite sur l'infrastructure cible.
