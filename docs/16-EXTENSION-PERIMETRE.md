# Extension navigateur — périmètre

> ⚠️ **Statut révisé le 14/09 au soir : lot reporté.** Adnan demande un **site de configuration** et une **application mobile** ; le site responsive et sa TWA deviennent la surface principale. L'extension n'apporterait plus que « corriger sans changer d'onglet », ce qui ne justifie pas une seconde surface à maintenir dès maintenant. **Ce document reste valable tel quel** : il dit ce que coûtera le lot le jour où on le rouvrira — et il a déjà servi en établissant la contrainte d'authentification par jeton d'appairage.

> Demandée par Adnan le 14/09 : **Chrome, Firefox et Firefox pour Android**, pour « configurer rapidement son agent ».
> ⚠️ Ce document fixe **ce que l'extension fait**, pas **comment**. Les faits d'API attendent la recherche A10 ; tout ce qui en dépend est marqué **[à confirmer]**.

---

## 1. Ce qui change tout : elle ne porte pas l'audio

L'architecture (`02` §7.2) reportait l'extension en dernier lot et écartait Firefox, faute d'équivalent à `chrome.offscreen` pour l'audio en arrière-plan.

**Ce raisonnement ne s'applique pas ici**, et A10 l'a confirmé pour **deux raisons indépendantes** : l'audio ne traverse jamais le navigateur, et même la relecture d'un appel se fait dans une page visible, avec DOM. **`offscreen` est donc hors sujet, et l'obstacle qui écartait Firefox tombe avec lui.**

**Fait connexe utile** : `background.service_worker` est `false` **sur Firefox partout**, pas seulement sur Android — c'est une divergence Firefox globale, pas une limitation mobile. Et bonne surprise : **les cinq règles que Mozilla impose à une event page Android sont exactement celles qu'exige le service worker de Chrome** (listeners synchrones au niveau supérieur, état dans `storage`, `alarms` plutôt que minuteurs). **Un seul arrière-plan sert les trois cibles.**

---

## 2. Ce qu'elle fait — par ordre de valeur

| # | Fonction | Pourquoi elle vaut une extension plutôt qu'un onglet |
|---|---|---|
| 1 | **Corriger un appel raté en trois appuis** (`06`) | C'est le geste qu'on veut rendre **immédiat**. Sur téléphone, entre deux clients, ouvrir un onglet et se reconnecter suffit à ne jamais le faire |
| 2 | **Voir le dernier appel** : issue, transcription, ce que l'agent a écrit | Consultation de dix secondes, plusieurs fois par jour |
| 3 | **Répondre au questionnaire** et modifier une règle | La configuration initiale se fait très bien en onglet ; **c'est la modification ultérieure** qui doit être à portée |
| 4 | **Alerter** : rendez-vous pris, échec d'écriture, quota | Quatre canaux, pas plus (`06` §5). ⚠️ **Mais pas « appel en cours » sur Android** — voir §4 |
| 5 | Déclencher un appel de test (« appelez votre agent ») | Le geste de confiance avant bascule (`01` §3) |

---

## 3. Ce qu'elle ne fait pas, et pourquoi

- **Aucun audio, aucun micro, aucun WebRTC.** C'est ce qui rend les trois cibles atteignables.
- **Aucun prompt exposé**, sous aucune forme « avancée » — la règle vaut partout, l'extension n'y échappe pas.
- **Aucune logique métier propre.** Elle appelle la même API que la console. Une extension qui décide quelque chose est une deuxième implémentation à maintenir.
- **Aucun code distant** : MV3 l'interdit, et c'est déjà la raison pour laquelle la logique vit dans un **paquet npm bundlable** (`02` §1). La décision était prise avant la demande ; elle se trouve validée.

---

## 4. Ordre de construction proposé

1. **Chrome et Edge** — base Chromium commune, revue rapide, 5 USD une fois.
2. **Firefox desktop** — même code, cycle de vie d'arrière-plan différent [à confirmer].
3. **Firefox Android** — **la cible qui compte le plus pour un commerçant** (il est debout, les mains occupées) et **la moins documentée**. À traiter comme un lot à part, avec sa propre vérification de faisabilité.

**Et une question de conception à trancher tôt** : si Firefox Android se révèle trop limité, **la PWA est le repli** — installable, notifiable, sans store ni revue. Ce serait moins pratique qu'une extension, mais **une PWA qui marche vaut mieux qu'une extension qui n'existe pas**. La recherche A10 doit permettre de choisir sur des faits, pas sur une préférence.

---

## 5. Ce qui est écrit ailleurs et qui s'applique ici

- **Temps réel** : SSE, **jamais d'interrogation périodique** — le cas Pandora (0,2 % des octets, **46 % de l'énergie**), et fermeture du flux dès que l'écran est masqué (`06` §5).
- **Accessibilité** : WCAG 2.2 §2.4.11 « Focus Not Obscured » mord sur toute feuille qui monte du bas (`06` §5).
- **Notifications** : médiane mesurée de **63,5 par jour** chez un utilisateur ordinaire — la bonne réponse n'est pas de mieux notifier, c'est de **notifier moins** (`06` §5).
- **Barthez** : le gate s'applique à l'extension comme au reste. Le mauvais exemple s'affiche **en gris, jamais en rouge**.

---

## 6. Les faits, établis le 2026-09-14 (A10)

**Firefox Android est ouvert** — annonce du 10/08/2023 : « users can install **any add-on on AMO** that has been marked as being compatible with Android ». ⚠️ **Mais aucun sideload** : « It will not be possible to install unsigned .xpi files ». Tout passe par AMO signé.

⚠️ **Découverte de méthode** : la page Mozilla qui synthétisait les limitations d'API Android **répond 404**. Il n'existe plus de page listant ce qui marche. La seule source exhaustive est **`mdn/browser-compat-data`, colonne `firefox_android`**, lue API par API. C'est précisément ce qui rend ce sujet opaque : **Mozilla a retiré la synthèse et laissé la donnée brute.**

| Disponible sur Android | **Absent sur Android** |
|---|---|
| `storage` (y compris `sync`), `alarms`, `notifications`, `runtime`, `cookies`, `tabs`, `permissions`, `action`, `scripting`, `options_ui` | **`identity` — API *et* permission** · `sidebarAction` · `menus` / `contextMenus` · `commands` · `windows` · `devtools` · `storage.managed` · `downloads` (retiré en 79) |

**Trois surfaces d'interface, et trois seulement** : popup, page d'options, onglet dédié. Avec un fait qui change le dessin : **sur Android il n'y a pas d'icône dans une barre d'outils** — « Browser actions are presented as **menu items** ». L'extension est **une entrée du menu ⋮, à deux appuis**.

### Les trois conséquences qui engagent la conception

1. **L'authentification est le point dur.** `identity.launchWebAuthFlow` fonctionne sur Chrome et Firefox desktop, **pas sur Android** — l'API n'y est pas implémentée. Le seul schéma couvrant les trois cibles est un **jeton d'appairage** (code d'appareil) ouvert par `tabs.create` vers notre site. **À écrire en premier** : concevoir autour de `launchWebAuthFlow` puis découvrir Android, c'est un mois perdu.
2. **« Rendez-vous pris » oui, « appel en cours » non.** Les notifications existent sur les trois, mais l'arrière-plan dort, le réveil passe par `alarms` (granularité : la minute), et **rien ne tourne si Firefox est fermé**. Promettre une alerte d'appel en cours sur Android serait un mensonge.
3. **Pas de framework.** Vérifié sur leurs documentations officielles : **aucun de WXT, Plasmo ou CRXJS ne déclare Firefox Android** — WXT produit **MV2 par défaut pour Firefox**, Plasmo marque `firefox-mv3` **expérimental**, CRXJS revendique « cross-browser » sans le documenter. Retenu : **Vite + un script générant deux manifestes**.

**Périmètre retenu** : **une seule page applicative responsive, trois portes d'entrée**. Pas de side panel — c'est la seule surface qui exigerait trois implémentations, et elle **n'existe pas sur Android**.

**Effort estimé** : socle commun **70 %** · Chrome +1 j · Firefox desktop +1 j · **Firefox Android +3 à 5 j** (aucun code neuf, mais passe mobile, authentification par appairage, test sur appareil réel) · publication +2 à 3 j.

**Deux points d'administration à ne pas rater** : l'adresse e-mail développeur du Chrome Web Store est **définitive** (prendre une adresse de rôle, jamais personnelle), et Firefox impose depuis la version 140 une clé **`data_collection_permissions`** dans le manifeste — **à faire cohérer avec le dossier RGPD** (`A5`), puisque nous manipulons des transcriptions d'appelants.

**Le risque n°1 n'est pas technique** : c'est de vendre un **récepteur d'alerte** alors qu'on livre un **poste de pilotage**. Sur Android, l'extension se consulte ; elle ne prévient pas en temps réel.
