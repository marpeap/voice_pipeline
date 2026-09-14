# Extension navigateur — périmètre

> Demandée par Adnan le 14/09 : **Chrome, Firefox et Firefox pour Android**, pour « configurer rapidement son agent ».
> ⚠️ Ce document fixe **ce que l'extension fait**, pas **comment**. Les faits d'API attendent la recherche A10 ; tout ce qui en dépend est marqué **[à confirmer]**.

---

## 1. Ce qui change tout : elle ne porte pas l'audio

L'architecture (`02` §7.2) reportait l'extension en dernier lot et écartait Firefox, faute d'équivalent à `chrome.offscreen` pour l'audio en arrière-plan.

**Ce raisonnement ne s'applique pas ici.** L'appel arrive par le **réseau téléphonique**, l'audio vit **sur le serveur**, et l'extension ne fait que **lire et écrire de la configuration**. Elle n'a besoin ni de micro, ni de WebRTC, ni de traitement audio en arrière-plan — **donc l'obstacle qui écartait Firefox tombe avec lui** [à confirmer, A10].

Ce qui reste à vérifier n'est plus l'audio, mais **quelles API existent réellement sur Firefox Android** et **quelles surfaces d'affichage** y sont disponibles.

---

## 2. Ce qu'elle fait — par ordre de valeur

| # | Fonction | Pourquoi elle vaut une extension plutôt qu'un onglet |
|---|---|---|
| 1 | **Corriger un appel raté en trois appuis** (`06`) | C'est le geste qu'on veut rendre **immédiat**. Sur téléphone, entre deux clients, ouvrir un onglet et se reconnecter suffit à ne jamais le faire |
| 2 | **Voir le dernier appel** : issue, transcription, ce que l'agent a écrit | Consultation de dix secondes, plusieurs fois par jour |
| 3 | **Répondre au questionnaire** et modifier une règle | La configuration initiale se fait très bien en onglet ; **c'est la modification ultérieure** qui doit être à portée |
| 4 | **Alerter** : échec d'écriture, escalade, quota | Quatre canaux, pas plus (`06` §5) |
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

## 6. Ce qu'il faut savoir avant d'écrire une ligne

1. **Quelles API WebExtensions existent sur Firefox Android en 2026**, et quelles surfaces d'affichage (popup, options, onglet) — **[NV]**.
2. **Comment une extension s'authentifie** auprès de notre service sur Android — **[NV]**.
3. **Si les notifications fonctionnent** sur Firefox Android — **[NV]**.
4. **Quel outil** (WXT, Plasmo, CRXJS) couvre réellement les trois cibles, d'après sa documentation officielle — **[NV]**.

Recherche A10 relancée le 14/09 à 17 h. **Tant qu'elle n'a pas abouti, ce document ne fixe que le périmètre — aucune promesse de faisabilité n'est faite sur Firefox Android.**
