# A10 — Extension de navigateur pour configurer un assistant téléphonique IA

**État : septembre 2026.** Recherche menée seule (aucun sous-agent), sources officielles uniquement.

**Convention de marquage**
- `[F]` **Fait** : vérifié sur source officielle, URL + date de consultation donnée.
- `[H]` **Hypothèse** : déduction logique de faits vérifiés, non attestée telle quelle par une source.
- `[R]` **Risque** : point qui peut casser le projet, ou dépendre d'une décision d'un tiers (Mozilla, Google).
- `[NV]` **Non vérifié / non documenté** : la source n'existe pas, ou n'a pas pu être atteinte.

**Cadrage produit rappelé.** L'extension **ne porte pas l'audio de l'appel**. L'appel arrive par le
réseau téléphonique (PSTN/SIP), l'audio vit sur le serveur. L'extension sert à **configurer**
(questionnaire, règles métier, voix, numéro), **revoir** (transcription, résumé d'un appel passé) et
**corriger** en quelques appuis. Conséquence majeure, vérifiée plus bas : les limites d'audio en
arrière-plan (absence d'équivalent Firefox à `chrome.offscreen`) sont **hors sujet** pour ce produit.

---

## 0. Méthode et sources

Deux familles de sources ont été utilisées :

1. **La documentation narrative** : `extensionworkshop.com` (Mozilla), `developer.chrome.com`,
   `developer.mozilla.org`, blogs officiels.
2. **`mdn/browser-compat-data` (BCD), branche `main`** — le jeu de données que MDN utilise pour
   *générer* ses tableaux « Browser compatibility ». C'est la même donnée que la page MDN, lue à la
   source plutôt qu'à travers le rendu HTML. Chemin :
   `https://github.com/mdn/browser-compat-data/tree/main/webextensions`
   (consulté le **14 septembre 2026**). La colonne `firefox_android` de BCD est la réponse
   officielle à « est-ce que cette API marche sur Firefox pour Android ». C'est la seule source
   exhaustive et machine-lisible sur ce sujet.

Note de lecture BCD : `"mirror"` dans la colonne `firefox_android` signifie **« même support que
Firefox desktop »**. `false` signifie **non supporté**. Un numéro signifie la version de Firefox
pour Android à partir de laquelle c'est supporté.

---

## 1. Firefox pour Android — l'état réel (priorité 1)

### 1.1 La liste fermée a-t-elle été ouverte ?

**Oui.** `[F]`

`extensionworkshop.com/documentation/develop/developing-extensions-for-firefox-for-android/`
(consulté le 14/09/2026) documente le développement et la publication d'extensions arbitraires pour
Firefox pour Android, sans restriction à une liste blanche : la page décrit le chargement via
`web-ext run -t firefox-android`, le lint de compatibilité, et un parcours de publication AMO
standard. Il n'y subsiste **aucune mention d'une liste d'extensions recommandées fermée** comme
préalable à la distribution.

Preuve indirecte, mais forte et datable, dans les données de compatibilité `[F]` :
la clé de manifeste `browser_specific_settings.gecko_android` — qui permet à un développeur de
déclarer `strict_min_version` / `strict_max_version` **spécifiquement pour Android** — existe
depuis **Firefox pour Android 113**. Cette clé n'a de sens que dans un monde où n'importe quel
développeur publie pour Android et doit borner ses versions Android indépendamment du desktop.
Firefox 113 date de mai 2023 ; l'ouverture générale a suivi dans la foulée (fin 2023).

**Le billet d'annonce, retrouvé.** `[F]`
`blog.mozilla.org/addons/2023/08/10/prepare-your-firefox-desktop-extension-for-the-upcoming-android-release/`
(consulté le 14/09/2026), daté du **10 août 2023**, annonce l'ouverture et dit, sur la nature exacte
de celle-ci :
> *« [users] can install any add-on on AMO that has been marked as being compatible with Android »*

et sur le calendrier :
> *« We'll announce a definite launch date in early September, but it's safe to expect a roll-out
> before the year's end »*

`[F]` Donc la bascule est bien **« n'importe quelle extension d'AMO déclarée compatible Android »**,
et non plus une liste fermée d'extensions recommandées. Le déploiement a suivi fin 2023.
**Nuance importante** `[F]` : l'ouverture ne signifie **pas** le chargement latéral libre. Mozilla
précise dans les commentaires du même billet : *« It will not be possible to install unsigned .xpi
files. »* → **toute extension doit passer par AMO et être signée**, y compris pour Android.

`[R]` La **date précise du déploiement** (le billet de septembre 2023 annonçant la date ferme) n'a pas
pu être atteinte : les URL du blog Add-ons de décembre 2023 testées répondent 404, et les notes de
version MDN de Firefox 120 ne mentionnent rien sur le sujet (vérifié : leur section
« Changes for add-on developers » ne parle que de `PointerEvent.getCoalescedEvents()`). Ce qui est
établi sans ambiguïté : annonce **10 août 2023**, déploiement **fin 2023**, et **état ouvert en
septembre 2026**.

`[NV]` Point de méthode honnête, demandé explicitement : **il n'existe pas de page unique et à jour,
côté Mozilla, qui liste « les API disponibles sur Firefox Android ».** La page dédiée aux limitations
d'API Android que l'on cite souvent (`.../firefox-android-extension-api-limitations/`) **répond 404**
au 14/09/2026. La seule source exhaustive est BCD, colonne `firefox_android`, lue API par API. C'est
ce que fait la section suivante. C'est bien le point le moins documenté du marché, et la raison en
est structurelle : Mozilla a supprimé la page de synthèse et n'a laissé que la donnée brute.

### 1.2 Ce qui marche et ce qui ne marche pas sur Android

Source : BCD `webextensions/api/*` et `webextensions/manifest/*`, branche `main`, 14/09/2026. `[F]`

**Disponible sur Firefox pour Android :**

| API | Depuis (Firefox Android) | Remarque |
|---|---|---|
| `storage` | 48 | `storage.local`, `storage.session`, **et `storage.sync`** |
| `alarms` | 48 | |
| `notifications` | 48 | voir §4 pour la nuance |
| `runtime` | 48 | messagerie, `onInstalled`, `getURL`… |
| `cookies` | 48 | |
| `webRequest` | 48 | |
| `tabs` | 54 | mais un lot de méthodes est absent (voir plus bas) |
| `permissions` (API) | 79 | |
| `action` (MV3) | mirror desktop (109) | voir la nuance d'UI plus bas |
| `browserAction` (MV2) | 55 | `default_popup` depuis 57 |
| `scripting` | mirror desktop (102) | |
| `declarativeNetRequest` | mirror desktop (113) | |
| `options_ui` (clé de manifeste) | **57** | `options_ui.page` et `options_ui.open_in_tab` |

**Absent sur Firefox pour Android** (`false` dans BCD) :

| API / clé | Statut Android | Impact pour notre produit |
|---|---|---|
| **`sidebarAction`** + clé `sidebar_action` | **false** (tout : `open`, `close`, `toggle`, `setPanel`…) | Aucune barre latérale sur mobile. Sans objet de toute façon. |
| **`identity`** (API **et** permission) | **false** — `identity.launchWebAuthFlow` et `identity.getRedirectURL` explicitement `false` | **Bloquant pour l'auth. Voir §3.** |
| **`menus`** (+ permission `menus` et alias `contextMenus`) | **false** | Pas de menu contextuel sur Android. |
| **`commands`** (raccourcis clavier) | **false**, y compris `_execute_action` | Sans objet sur mobile. |
| **`windows`** (API entière) | **false** | Il n'y a pas de fenêtres sur Android : une seule. |
| `devtools.*` | false | |
| `omnibox` | false | |
| `downloads` | **48, puis retiré en 79** | On ne peut pas proposer d'export de fichier via `downloads` sur Android. |
| `storage.managed` | false | déploiement d'entreprise impossible sur Android |
| `runtime.connectNative` / `sendNativeMessage` | false | messagerie native hors sujet |
| permissions `bookmarks`, `history`, `sessions`, `find`, `theme`, `tabHide`, `search`, `pkcs11`, `nativeMessaging`, `devtools` | false | sans objet |
| `action.default_area`, `action.theme_icons` | false | |
| `browser_action.browser_style`, `.default_area`, `.theme_icons` | false | |

**Nuances `tabs` sur Android** `[F]` : l'API existe (depuis 54) mais sont absents
`tabs.move`, `tabs.duplicate`, `tabs.hide`/`show`, `tabs.discard`, `tabs.highlight`,
`tabs.print`/`printPreview`/`saveAsPDF`, tout le zoom (`getZoom`, `setZoom`, `getZoomSettings`,
`onZoomChange`), `tabs.group`/`ungroup` (139 sur desktop), `tabs.onMoved`, `tabs.toggleReaderMode`,
`tabs.warmup`. Ce qui reste — `create`, `query`, `update`, `sendMessage`, `onUpdated` — est
exactement ce dont une extension de configuration a besoin.

### 1.3 Les surfaces d'interface réellement affichables sur Android

`[F]` Trois surfaces, et trois seulement :

1. **Le popup d'action.** Il existe. `browser_action.default_popup` depuis Firefox Android 57 ;
   `action.default_popup` en MV3 mirrore le desktop. **Mais** BCD porte une note décisive sur
   `action.default_title` / `browser_action.default_title` côté Android :
   > *« Browser actions are presented as menu items, and the title is the menu item's label. »*

   Autrement dit `[F]` : sur Android **il n'y a pas de barre d'outils avec une icône d'extension**.
   L'extension apparaît comme **une entrée dans le menu ⋮ du navigateur**, libellée par
   `default_title`, et l'appui ouvre le popup. Conséquence de design `[H]` : le titre de l'action
   est un vrai libellé de menu lu par l'utilisateur, pas un tooltip — il faut l'écrire comme un
   label ; et l'accès est à **deux appuis** (menu, puis entrée), jamais à un.

2. **La page d'options.** `options_ui` supporté depuis Firefox Android **57**, avec
   `options_ui.open_in_tab`. C'est la surface **large** sur mobile. `[F]`

3. **Un onglet dédié.** `tabs.create({url: runtime.getURL('app.html')})` fonctionne (API `tabs`
   présente depuis 54). C'est une page d'extension plein écran, dans un onglet normal. `[H]`
   C'est la surface la plus confortable sur Android pour un questionnaire de configuration : pleine
   hauteur, scroll natif, clavier virtuel géré par le navigateur, pas de contrainte de taille de
   popup.

`[F]` Ce qui **n'existe pas** comme surface sur Android : barre latérale (`sidebarAction` false),
menu contextuel (`menus` false), fenêtre détachée (`windows` false), raccourci clavier
(`commands` false), icône persistante en barre d'outils.

### 1.4 MV2 ou MV3 sur Android ?

`[F]` La page Extension Workshop consacrée à Android énonce trois limitations MV3 sur Android, avec
leurs numéros de bug Bugzilla, et conclut :
> *« Background service workers aren't supported on Firefox for Android »* (Bug 1573659)
> — les demandes de permissions hôte n'ont pas d'indicateur visuel (Bug 1820867)
> — l'utilisateur ne peut pas modifier les permissions hôte depuis le gestionnaire (Bug 1812125)
> *« it's recommended you use Manifest V2 for extensions targeting Firefox for Android. »*

`[F]` Précision essentielle qui recadre le premier point : BCD donne
`manifest.background.service_worker` → **`firefox: false`**. Firefox **ne supporte pas
`service_worker` du tout**, ni sur desktop ni sur Android. Ce n'est donc pas une limitation Android,
c'est une divergence Firefox/Chrome globale. Firefox MV3 utilise `background.scripts` en **event
page** (non persistante). MV3 est supporté par Firefox depuis 109 et `manifest_version.v3` mirrore
sur Android.

`[R]` La recommandation « utilisez MV2 sur Android » de Mozilla est en tension avec la fin de vie de
MV2 côté Chrome. **Elle ne doit pas nous conduire à écrire une extension MV2**, ce qui nous
couperait de Chrome. La lecture à retenir : écrire **MV3**, avec un background en `background.scripts`
(event page) pour Firefox et `service_worker` pour Chrome — les deux clés peuvent coexister dans un
même manifeste, chaque navigateur ignorant celle qu'il ne connaît pas. `[H]` Firefox 136 a même
ajouté `background.preferred_environment` pour arbitrer explicitement quand les deux sont présentes.

### 1.5 Développer, tester, publier sur Android

`[F]` (Extension Workshop, page Android, 14/09/2026)
- Outillage : **`web-ext` ≥ 7.12.0**, Android Platform Tools (`adb`), et « Remote debugging via USB »
  activé dans les réglages de Firefox sur l'appareil.
- Lancement : `web-ext run -t firefox-android --adb-device XXX --firefox-apk org.mozilla.fenix`.
  Note : *« The add-on is loaded in the main browser profile instead of a new temporary profile
  directory. »*
- Vérification préalable : `web-ext lint` signale permissions, clés de manifeste et API
  incompatibles. Le manifeste doit porter `browser_specific_settings` avec un bloc
  **`gecko_android`** distinct (Android 113+, `strict_min_version` / `strict_max_version`).
- Débogage via `about:debugging` une fois l'appareil connecté en USB. Limite documentée :
  *« You cannot inspect the markup of Fenix's browserAction popups using the Firefox Developer Tools
  Inspector »* — contournement officiel : ouvrir temporairement le popup dans un onglet.
- Publication : **revue AMO**, et la page pose des exigences spécifiquement mobiles :
  balise `viewport` correcte, design responsive, test sur plusieurs tailles d'appareil, et
  **fonctionnement vérifié sans connectivité réseau**.

`[R]` Ce dernier point mérite attention pour notre produit : une extension qui ne sait que parler à
un serveur doit **dégrader proprement hors ligne** (message explicite, pas d'écran blanc, pas de
spinner infini), sous peine de friction en revue.

`[NV]` Je n'ai pas trouvé de **file de revue AMO distincte pour Android** : c'est la même soumission
AMO, le même `.xpi`, avec la compatibilité Android déclarée dans le manifeste. Il n'y a pas de
« store Android » séparé.

---

## 2. Le socle commun aux trois cibles

### 2.1 Ce qui est partagé

`[H]`, appuyé sur les faits du §1 : **la quasi-totalité du code produit est partageable.**
Les pages d'UI (popup, options, onglet dédié) sont du HTML/CSS/JS ordinaire, identiques partout.
Les appels réseau vers notre serveur sont du `fetch` ordinaire. Le stockage (`storage.local`) a la
même API. La messagerie `runtime.sendMessage` est identique. La couche qui diverge est mince et
localisable : **cycle de vie de l'arrière-plan, surfaces d'UI, auth**.

### 2.2 Ce qui diverge vraiment

**a) Arrière-plan** `[F]`
- Chrome MV3 : `background.service_worker` (Chrome 88+). Service worker, **pas de DOM**, se termine
  quand il est inactif, tout état en mémoire est volatile.
- Firefox (desktop et Android) : `background.service_worker` = **false**. On utilise
  `background.scripts` (event page non persistante). `background.persistent` n'est valide qu'en MV2
  et, depuis Firefox 106, les pages persistantes **et** non persistantes sont supportées en MV2.
- Conséquence pratique `[H]` : écrire le background comme **sans état**, tout ce qui doit survivre
  va dans `storage.local`, et tout réveil différé passe par `alarms` (disponible partout, y compris
  Android 48+) — jamais par `setTimeout` long.

`[F]` **Mozilla donne exactement cette liste de règles**, dans le billet du 10/08/2023, comme
préparation obligatoire d'une extension desktop à l'arrivée sur Android :
> — passer le script d'arrière-plan en **event page non persistante** (`"persistent": false`) ;
> — *« Ensure listeners are registered synchronously at the top-level »* ;
> — stocker l'état global via l'**API storage** ;
> — **remplacer les timers par des alarms** ;
> — abandonner `extension.getBackgroundPage` au profit de la messagerie d'extension ou de
> `runtime.getBackgroundPage`.

`[H]` Ces cinq règles sont **aussi** celles qui rendent un background compatible avec le service
worker MV3 de Chrome. C'est la bonne nouvelle du dossier : **le style d'écriture imposé par Firefox
Android est exactement celui qu'exige Chrome MV3.** Un seul background, écrit sans état, listeners
au niveau racine, `alarms` partout, sert les trois cibles.

**b) `sidePanel` contre `sidebarAction`** `[F]`
- Chrome : API `sidePanel`, permission `sidePanel` depuis **Chrome 114**. Côté Firefox : `false`.
- Firefox desktop : `sidebarAction` + clé `sidebar_action` depuis **Firefox 54**. Côté Chrome :
  `false`. MDN le dit explicitement : Chrome fournit les barres latérales via `sidePanel`, *« but
  this is not compatible with `sidebarAction` »*.
- Firefox Android : **ni l'un ni l'autre**.
- `[H]` Recommandation : **ne pas bâtir le produit sur une barre latérale.** C'est la seule surface
  qui exige trois implémentations et qui n'en a aucune sur Android. Si on en veut une sur desktop,
  qu'elle soit un habillage optionnel autour de la même page HTML que l'onglet dédié.

**c) Stockage** `[F]`
- `storage.local` : partout, sans divergence notable.
- `storage.sync` : disponible sur Chrome, Firefox desktop **et Firefox Android** (BCD ne marque
  aucune exclusion Android sur `storage.sync` ; seul `storage.managed` est `false` sur Android).
- `[R]` `storage.sync` a des quotas serrés et une sémantique de synchronisation liée au compte
  navigateur. Pour un produit dont la source de vérité est notre serveur, **`storage.sync` n'a pas
  d'usage légitime** : il introduirait une deuxième source de vérité. À proscrire pour la config
  métier ; `storage.local` sert de cache et de porteur du jeton.

**d) Permissions** `[F]`
- MV3 sépare `permissions` et `host_permissions` (Chrome 88, Firefox 109, mirroré sur Android).
- `[R]` Sur Android, deux bugs ouverts changent l'expérience : pas d'indicateur visuel des demandes
  de permissions hôte (Bug 1820867) et impossibilité pour l'utilisateur d'éditer ces permissions
  (Bug 1812125). Conséquence `[H]` : **demander le strict minimum**. Pour notre produit, une
  permission hôte sur notre seul domaine API (`https://api.notre-domaine/*`) suffit, et encore —
  voir §2.3.

**e) Code distant : l'interdiction** `[F]`
- La CSP des pages d'extension en MV3 interdit `script-src` externe. BCD note que Firefox
  **n'accepte pas** `http://127.0.0.1` ni `http://localhost` comme sources de script (doivent être
  en HTTPS), et que depuis Firefox 147 seules les extensions **chargées temporairement** peuvent
  relâcher la CSP pour autoriser des scripts depuis localhost (équivalent Chrome depuis la 110 pour
  les extensions décompressées).
- `[H]` **Ce que cela interdit concrètement pour nous** : pas de `<script src="https://notre-cdn/…">`,
  pas d'`eval`, pas de rendu d'un formulaire de configuration livré par le serveur sous forme de
  code. Ce que cela **n'interdit pas** : télécharger des **données** (JSON) depuis notre serveur et
  les rendre avec du code embarqué dans l'extension. C'est la conception à adopter : le serveur
  envoie un **schéma de questionnaire en JSON**, l'extension embarque le moteur de rendu.
- `[R]` C'est un point de revue AMO classique : une extension qui charge du code distant est
  rejetée. Notre architecture « schéma JSON + moteur local » y répond nativement.

### 2.3 Faut-il seulement une permission hôte ?

`[H]` Si l'extension ne fait que parler à **notre** API et n'injecte rien dans les pages de
l'utilisateur, il n'y a **aucune permission hôte à demander** : depuis ses propres pages
(popup, options, onglet), une extension fait des `fetch` cross-origin selon la CSP
`connect-src`, et notre serveur répond en CORS. Pas de `content_scripts`, pas de
`host_permissions` → manifeste quasi vide de permissions, revue plus rapide, meilleure confiance
utilisateur. `[R]` À valider en implémentation : si un `fetch` vers notre API est bloqué,
la retombée est d'ajouter `host_permissions: ["https://api.notre-domaine/*"]`, ce qui reste une
permission unique et facile à justifier.

---

## 3. Authentification — et le trou Android

### 3.1 Le fait qui décide de tout

`[F]` **`identity` n'existe pas sur Firefox pour Android.** BCD, deux entrées concordantes :
- `webextensions/api/identity` → `firefox_android: false`, avec `identity.launchWebAuthFlow: false`
  et `identity.getRedirectURL: false` (tous deux supportés sur Firefox desktop depuis 53) ;
- `webextensions/manifest/permissions/identity` → `firefox: 53`, **`firefox_android: false`**,
  `chrome: 29`.

Donc : `identity.launchWebAuthFlow` marche sur **Chrome** et **Firefox desktop**, et **pas** sur
**Firefox Android**. `[R]` C'est le point dur du projet côté auth, et il est structurel : ce n'est
pas un bug à contourner, l'API n'est simplement pas implémentée.

### 3.2 Le seul schéma qui couvre les trois cibles

`[H]` **Le jeton d'appairage, avec le navigateur comme intermédiaire.** Il ne dépend d'aucune API
absente sur une cible :

1. L'extension ouvre `tabs.create({url: 'https://notre-app/lier?code=XXXX'})` — `tabs.create` est
   disponible sur les trois cibles.
2. L'utilisateur s'authentifie **sur notre site**, dans un onglet normal, avec son compte existant
   (cookie de session, OAuth, magic link — c'est notre problème de serveur, pas celui de
   l'extension).
3. Notre page affiche un **code d'appairage court** ; l'utilisateur le recopie dans l'extension.
   Variante sans recopie : l'extension **interroge notre serveur en boucle** (`alarms` + `fetch`)
   sur l'état du code qu'elle a elle-même généré, et récupère le jeton dès que le serveur marque le
   code comme approuvé. C'est le modèle **device-code**, celui des téléviseurs connectés.
4. Le jeton atterrit dans `storage.local`, chiffré côté serveur par rotation courte.

`[H]` Avantages : identique sur Chrome, Firefox desktop, Firefox Android ; aucune permission hôte ;
aucun cookie partagé ; rien à expliquer en revue AMO ou CWS ; et l'étape 2 réutilise l'auth de notre
console web existante.

### 3.3 Les deux alternatives, et pourquoi elles perdent

- **`identity.launchWebAuthFlow`** `[F]` : marche sur Chrome (29+) et Firefox desktop (53+),
  **pas Android**. `[H]` L'adopter impose d'écrire de toute façon le chemin de repli pour Android —
  donc deux chemins d'auth à maintenir au lieu d'un. Ne se justifie que si l'UX desktop en un clic
  est un argument commercial.
- **Cookie partagé** `[H]` : l'extension lit le cookie de session de notre domaine via l'API
  `cookies` (disponible sur les trois cibles : Android depuis 48). Techniquement faisable, mais
  exige une permission hôte sur notre domaine **et** la permission `cookies`, deux demandes qui
  alourdissent la revue, et casse si l'utilisateur n'est pas déjà connecté dans ce navigateur-là.
  `[R]` Un jeton porteur volé depuis un cookie lisible par extension est un mauvais modèle de
  sécurité. À écarter.

---

## 4. Notifications

`[F]` L'API `notifications` est disponible sur Firefox pour Android **depuis la version 48**, et la
permission `notifications` mirrore le desktop côté Android. Sur Chrome, depuis la 28. Donc
**oui, techniquement, une extension peut afficher une notification sur les trois cibles.**

`[R]` Mais trois réserves sérieuses avant d'en faire une promesse produit :

1. **Il faut que l'extension tourne pour notifier.** Le background est une event page (Firefox) ou
   un service worker (Chrome) : il dort. Le réveil régulier passe par `alarms`
   (disponible partout, Android 48+), avec une granularité de l'ordre de la minute, jamais de la
   seconde. `[H]` **Une notification « appel en cours »**, qui n'a de valeur qu'en temps réel,
   **n'est pas tenable par ce chemin.** Une notification « un rendez-vous a été pris », qui tolère
   quelques minutes de retard, l'est.
2. **Le navigateur doit être ouvert.** `[H]` Sur Android, si Firefox n'est pas en cours d'exécution,
   il n'y a personne pour exécuter l'alarme. Une extension de navigateur n'est pas un service
   Android en arrière-plan et ne peut pas le devenir.
3. `[NV]` Je n'ai pas trouvé de documentation officielle Mozilla décrivant le rendu exact d'une
   `notifications.create` sur Fenix (canal Android, persistance, comportement en Doze mode). Le
   support est attesté par BCD ; **le comportement fin sur Android n'est pas documenté**. À valider
   sur appareil réel avant toute promesse.

`[H]` **Conclusion produit** : la notification d'appel en temps réel doit venir d'ailleurs — SMS,
push de l'application mobile si elle existe, ou e-mail. L'extension notifie des **événements
différés et résumés**, et c'est tout ce qu'on doit lui demander.

### 4.1 Le point `offscreen` : vérifié, et effectivement hors sujet

`[F]` `chrome.offscreen` existe pour donner au service worker MV3 de Chrome un accès au DOM et aux
API média (lecture audio, `getUserMedia`, canvas…) que le service worker n'a pas. Firefox n'en a
pas d'équivalent — et n'en a pas besoin de la même manière, puisque son background MV3 est une
**event page** avec DOM, pas un service worker (§2.2a).

`[H]` **Vérification explicite pour notre produit, comme demandé** : l'absence d'équivalent Firefox à
`offscreen` est **sans aucun impact ici**, pour deux raisons cumulatives et indépendantes.
(a) L'extension ne traite pas d'audio : l'audio de l'appel vit sur le serveur et n'entre jamais dans
le navigateur. (b) Même pour relire l'enregistrement d'un appel passé, la lecture se fait dans une
**page visible** (popup, options ou onglet), qui a un DOM complet et une balise `<audio>` sur les
trois cibles — pas dans le background. `offscreen` ne sert qu'au besoin très particulier de jouer ou
capturer du son **depuis un contexte invisible**, que nous n'avons pas. Le sujet est clos.

---

## 5. Publication

### 5.1 Firefox / AMO

`[F]` Soumission sur addons.mozilla.org, revue AMO, exigences mobiles spécifiques listées au §1.5
(viewport, responsive, test multi-appareils, comportement hors ligne). Un seul paquet couvre desktop
et Android ; la compatibilité Android se déclare dans `browser_specific_settings.gecko_android`.
`[F]` Complément vérifié sur
`extensionworkshop.com/documentation/publish/submitting-an-add-on/` (14/09/2026) :
- **Aucun frais de soumission n'est mentionné.** La page décrit tout le parcours sans jamais évoquer
  de paiement. `[H]` AMO est gratuit ; je le marque `[H]` parce que c'est une absence de mention, pas
  une affirmation positive.
- Deux modes de distribution : **listée sur AMO**, ou **auto-distribuée**. En auto-distribution, il
  faut `browser_specific_settings` avec `update_url` pointant vers un manifeste de mise à jour ;
  **AMO signe automatiquement les extensions listées**. Rappel `[F]` du §1.1 : sur Android, le
  chargement d'un `.xpi` non signé est impossible — l'auto-distribution suppose donc quand même une
  signature AMO.
- Format : archive ZIP (`.zip`, `.xpi`, `.crx`), **200 Mo maximum**.
- Le formulaire demande de **« select the add-on's compatible platform(s) »**, desktop et/ou Android.
  C'est là que se joue la visibilité Android, en plus de `gecko_android` dans le manifeste.
- Délais : la page dit seulement que l'extension *« may be subject to further review »* avec
  notification ultérieure. `[NV]` **Aucun SLA de revue n'est publié.**

### 5.2 Chrome Web Store

`[F]` `developer.chrome.com/docs/webstore/register` (14/09/2026) : l'inscription exige d'accepter
l'accord développeur puis de **payer « a one-time registration fee »** — frais **uniques**.
`[NV]` **Le montant n'est pas indiqué sur cette page** et je ne l'invente pas. Autres exigences
vérifiées : une **adresse e-mail développeur dédiée et non modifiable ultérieurement**, à surveiller
car elle reçoit les alertes de conformité.
`[R]` Point d'organisation concret : cette adresse étant définitive, elle doit être une **adresse de
rôle de l'entreprise** (type `extensions@…`), jamais l'adresse personnelle d'un développeur.
`[NV]` Délais de revue CWS : non publiés sur cette page.

### 5.3 Ce qui bloque réellement une extension qui parle à un serveur tiers

`[H]`, déduit des règles vérifiées :
- **Code distant** : rédhibitoire (§2.3). Notre architecture « schéma JSON + moteur embarqué » est
  conforme. À écrire noir sur blanc dans les notes de soumission.
- **Justification de chaque permission** : les deux stores exigent une justification par permission.
  Un manifeste sans `host_permissions` et sans `content_scripts` supprime la difficulté.
- **Politique de confidentialité** obligatoire dès qu'on transmet des données utilisateur à un
  serveur — et nous en transmettons (configuration métier, et par ricochet des données d'appel).
- `[R]` **Firefox 140+ introduit `browser_specific_settings.gecko.data_collection_permissions`**
  (`firefox: 140`, `firefox_android: 142`) `[F]` : une déclaration **dans le manifeste** de ce que
  l'extension collecte. `[H]` Sur un produit qui manipule des transcriptions d'appels — donc de la
  donnée personnelle de tiers, les appelants — c'est à remplir sérieusement et à cohérer avec la
  politique de confidentialité et le dossier RGPD du projet (cf. A5).

---

## 6. Outillage

Vérifié sur la **documentation officielle de chaque projet**, et non sur des billets de blog, comme
demandé. Consultation du 14/09/2026.

**Réponse courte : aucun des trois ne déclare Firefox pour Android comme cible.** `[F]`

| Outil | Cibles officiellement déclarées | Firefox Android | Source |
|---|---|---|---|
| **WXT** | `chrome` (défaut), `firefox`, `safari`, `custom` — via `-b` | **Non mentionné** | `wxt.dev/guide/essentials/target-different-browsers.html` |
| **Plasmo** | `chrome-mv3` (défaut), `firefox-mv2`, `firefox-mv3` (**expérimental**), + chromium divers (`edge-mv3`, `brave-mv3`, `opera-mv3`), `safari-mv3` avec contournements | **Non listé** | `docs.plasmo.com/framework/workflows/faq` |
| **CRXJS** | se présente comme *« cross-browser extensions with native HMR, zero-config setup, and Vite 8 support »* ; **aucune déclaration de navigateurs ni de versions de manifeste** sur la page d'accueil | **Non documenté** | `crxjs.dev` |

Détails et pièges relevés :

- `[R]` **WXT** : *« By default, WXT will target MV2 for Safari and Firefox and MV3 for all other
  browsers. »* Le défaut de WXT pour Firefox est donc **MV2**. C'est cohérent avec la recommandation
  de Mozilla (§1.4) mais **contraire à notre choix** (MV3 partout) ; il faudrait forcer `--mv3`.
  WXT permet par ailleurs des options par navigateur (patterns de correspondance, moment
  d'exécution), ce qui est le mécanisme qu'on utiliserait pour les divergences.
- `[R]` **Plasmo** : `firefox-mv3` est explicitement marqué **expérimental**. Bâtir une cible de
  production dessus est un pari.
- `[NV]` **CRXJS** : la page d'accueil revendique le « cross-browser » sans le documenter. Deux URL
  de sous-pages testées (`/vite-plugin/concepts/manifest`,
  `/vite-plugin/getting-started/vanilla-js/create-project`) répondent **404**, et `/vite-plugin/`
  n'est qu'une redirection méta vers la racine — la documentation a été réorganisée. **Support
  Firefox non établi.** Le projet paraît maintenu (release `vite-plugin-v2.6.1`, support Vite 8).

`[H]` **Conclusion et recommandation.** Sur la cible qui nous intéresse le plus — Firefox Android —
**aucun framework n'apporte quoi que ce soit**, puisqu'aucun ne la connaît. Ce qu'ils apportent
(génération de manifeste par navigateur, HMR) est réel mais marginal pour ce projet, qui demande
(a) un manifeste avec deux clés de background coexistantes, (b) trois pages HTML, (c) `fetch` +
`storage.local`.

**Recommandation : commencer sans framework d'extension.** Une build minimale — Vite, plus un petit
script qui génère `manifest.chrome.json` et `manifest.firefox.json` depuis une base commune — couvre
tout le besoin, en une journée, sans dépendre de la feuille de route d'un tiers.
`[H]` Si l'on en veut un quand même, **WXT est le moins mauvais** : cibles Firefox non
expérimentales, options par navigateur, documentation explicite — à condition de forcer MV3.

---

## 7. Recommandation de périmètre

### 7.1 Le principe directeur

`[H]` **Une seule page applicative, trois portes d'entrée.** Tout le produit vit dans une page HTML
d'extension (`app.html`) responsive, conçue mobile-first. Le popup, la page d'options et l'onglet
dédié ouvrent **la même page**, avec des largeurs différentes. C'est la seule conception qui produise
un code unique sur trois cibles dont l'une n'a ni barre latérale, ni menu contextuel, ni raccourci
clavier, ni barre d'outils.

### 7.2 Par plateforme

**Chrome (MV3, service worker)**
- Fait : popup d'action (accès en un clic depuis la barre d'outils), page d'options, onglet dédié,
  notifications d'événements différés, auth par jeton d'appairage (`launchWebAuthFlow` possible en
  option de confort).
- Ne fait pas : audio, capture d'appel, side panel (non retenu par choix d'unicité du code).

**Firefox desktop (MV3, `background.scripts` en event page)**
- Fait : strictement les mêmes choses que Chrome. `sidebarAction` **disponible** mais **non retenu** :
  il n'apporte rien qu'un onglet n'apporte, et coûte une troisième implémentation.
- Ne fait pas : idem Chrome.

**Firefox pour Android**
- Fait : **entrée dans le menu ⋮** ouvrant le popup (rappel `[F]` : pas d'icône en barre d'outils,
  l'action est un item de menu libellé par `default_title`), page d'options, et surtout **l'onglet
  dédié plein écran** comme surface principale. Configuration, revue d'un appel, correction en
  quelques appuis : tout est faisable. Auth par jeton d'appairage — **seul chemin possible**,
  `identity` étant absent.
- **Ne fait pas** : notification temps réel d'un appel en cours `[R]` ; barre latérale ; menu
  contextuel ; raccourcis ; export de fichier via `downloads` (retiré en 79) ; aucune action quand
  Firefox n'est pas ouvert.

### 7.3 Effort estimé `[H]`

| Cible | Effort | Ce qui le porte |
|---|---|---|
| **Socle commun** (pages, état, client API, moteur de questionnaire JSON) | **~70 % du total** | tout le produit est là |
| **Chrome** | **+1 j** | manifeste MV3 + `service_worker` ; rien d'autre ne diffère |
| **Firefox desktop** | **+1 j** | `background.scripts`, `browser_specific_settings.gecko`, polyfill `browser`/`chrome` |
| **Firefox Android** | **+3 à 5 j** | pas de code neuf, mais : `gecko_android`, passe responsive mobile-first, **chemin d'auth par appairage**, dégradation hors ligne exigée en revue, et surtout **test sur appareil réel via adb** — la seule manière de lever les `[NV]` du §4 |
| **Publication (2 stores)** | **+2 à 3 j** | captures, politique de confidentialité, `data_collection_permissions`, justifications, allers-retours de revue |

`[R]` **Le risque n°1 n'est pas technique, il est de cadrage** : si quelqu'un promet « l'extension
vous prévient quand un appel arrive », la promesse est intenable sur Android et fragile sur desktop.
Le produit doit être vendu comme **un poste de pilotage**, pas comme un **récepteur d'alerte**.

`[R]` **Le risque n°2 est l'auth** : concevoir l'auth autour de `launchWebAuthFlow` puis découvrir
Android est un mois de retard. Le jeton d'appairage doit être écrit **en premier**, et servir les
trois cibles dès le premier jour.

---

## 8. Ce qui reste ouvert

- `[NV]` **Date ferme du déploiement** Android fin 2023 (annonce du 10/08/2023 retrouvée, billet de
  lancement 404, notes MDN de Firefox 120 muettes). Sans impact décisionnel.
- `[NV]` **Montant** des frais uniques du Chrome Web Store (la page officielle dit « a one-time
  registration fee » sans chiffrer). Gratuité d'AMO déduite d'une absence de mention `[H]`.
- `[NV]` **Délais de revue** AMO et CWS : aucun SLA publié sur les pages officielles consultées.
  Prévoir des allers-retours sans les chiffrer.
- `[NV]` **Comportement fin des `notifications` sur Fenix** (canal Android, persistance, Doze mode).
  Le support est attesté par BCD depuis Android 48 ; le rendu réel n'est documenté nulle part.
  **À tester sur appareil — c'est le seul `[NV]` qui peut changer une décision produit.**
- `[NV]` **Support Firefox de CRXJS** : documentation réorganisée, sous-pages en 404.
- `[NV]` La page Mozilla de synthèse des limitations d'API Android répond 404 ; **BCD est désormais
  la seule source exhaustive**, ce qui est en soi un résultat de cette recherche.

---

*Sources principales consultées le 14 septembre 2026 :*
- `https://extensionworkshop.com/documentation/develop/developing-extensions-for-firefox-for-android/`
- `https://github.com/mdn/browser-compat-data` — `webextensions/api/*.json` et
  `webextensions/manifest/*.json`, branche `main`
  (`sidebarAction`, `identity`, `menus`, `notifications`, `alarms`, `storage`, `tabs`, `commands`,
  `windows`, `downloads`, `runtime`, `permissions`, `scripting`, `declarativeNetRequest`,
  `action`, `background`, `options_ui`, `browser_specific_settings`, `content_security_policy`)
- `https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/sidebarAction`
- `https://blog.mozilla.org/addons/2023/08/10/prepare-your-firefox-desktop-extension-for-the-upcoming-android-release/`
- `https://extensionworkshop.com/documentation/publish/submitting-an-add-on/`
- `https://developer.chrome.com/docs/webstore/register`
- `https://wxt.dev/guide/essentials/target-different-browsers.html`
- `https://docs.plasmo.com/framework/workflows/faq` et `/framework/workflows/build`
- `https://crxjs.dev/`
- `https://developer.mozilla.org/en-US/docs/Mozilla/Firefox/Releases/120`

*URL consultées et retournant 404 au 14/09/2026 (signalées comme telles, non contournées) :*
- `https://extensionworkshop.com/documentation/develop/firefox-android-extension-api-limitations/`
- `https://crxjs.dev/vite-plugin/concepts/manifest`, `https://crxjs.dev/vite-plugin/getting-started/vanilla-js/create-project`
- billets du blog Mozilla Add-ons de décembre 2023
