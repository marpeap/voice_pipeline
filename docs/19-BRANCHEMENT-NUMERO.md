# Brancher un numéro en cinq minutes — conception du parcours

> **Ce document transforme la recherche `recherche/R3-telephonie-fr.md` en parcours produit.** R3 dit ce que les opérateurs publient ; ici on décide ce que l'utilisateur voit, dans quel ordre, et ce que le serveur vérifie derrière lui.
>
> C'est l'une des deux exigences fondatrices du service (« répondre aux appels » et « brancher un numéro rapidement, nouveau ou existant »). Elle ne dépend ni de Crenolo, ni d'un hôte de greffe, ni d'une mesure du banc : **elle est écrivable et testable seule**.

---

## 1. Le choix qui structure tout le reste

Trois chemins mènent un appel jusqu'à l'agent. Ils ne se valent pas.

| Chemin | Délai réel | Réversible | Risque pour le commerçant |
|---|---|---|---|
| **A. Un numéro neuf, fourni par nous** | minutes | oui | nul — son numéro historique ne bouge pas |
| **B. Renvoi de son numéro existant vers le nôtre** | 5 min | **5 secondes** (`#002#`) | faible, et local à sa ligne |
| **C. Portabilité de son numéro chez notre opérateur** | 8 jours à 4 semaines | non, pas à court terme | **injoignable si ça casse** |

**Décision — le chemin par défaut est B, et A en est le préalable technique.** On provisionne toujours un **09** (non géographique, autorisé comme destination de renvoi partout, n'induit personne en erreur sur une localité), puis on fait poser le renvoi. C est retiré du parcours d'onboarding : on ne le propose qu'à un client qui veut *de toute façon* quitter son opérateur, et jamais comme moyen de brancher un agent. La raison est écrite en une phrase dans R3 : la portabilité coupe le lien avec l'opérateur historique pour obtenir un résultat que le renvoi donne en cinq minutes et défait en cinq secondes.

**Conséquence de conception, non négociable** : l'agent ne connaît pas le numéro de l'appelant. L'Arcep recommande aux opérateurs de **masquer l'identifiant d'appelant** quand un renvoi complexe empêche de relayer les données d'authentification. Aucune identification client ne doit donc dépendre du CLI — l'agent demande le nom et le numéro à l'oral, toujours. Ce n'est pas une dégradation : c'est l'hypothèse de base.

---

## 2. Le parcours, écran par écran

Cinq écrans. Aucun ne demande d'écrire quoi que ce soit de technique.

**Écran 1 — « Quel numéro vos clients composent-ils ? »**
Un seul champ. On normalise (`+33`), on détecte fixe (01-05, 09) ou mobile (06, 07). Rien d'autre n'est demandé à ce stade.

**Écran 2 — « Chez quel opérateur ? »**
Quatre logos plus « je ne sais pas ». Ce choix est indispensable : **les codes ne sont pas les mêmes d'un opérateur à l'autre**, et deux d'entre eux n'en publient aucun. « Je ne sais pas » bascule sur le parcours de secours (§4).

**Écran 3 — « Quand l'agent doit-il décrocher ? »**
Trois cartes, une seule cochée par défaut :
- **Quand vous ne répondez pas** (recommandé) — le commerçant reste maître de sa ligne, l'agent ramasse ce qui tombe.
- **Quand vous êtes déjà en ligne** — utile en salon, où le poste est souvent occupé.
- **Tout le temps** — pour une ligne dédiée, ou une fermeture.

C'est le seul endroit du parcours où le produit absorbe une complexité réelle : ces trois cartes se traduisent en trois familles de codes (`61`, `67`/`69`, `21`) dont l'orthographe change selon l'opérateur.

**Écran 4 — le code, prêt à composer.**
Un bloc unique, en gros, avec le numéro d'arrivée déjà incrusté, un bouton **copier** et un bouton **composer**. Sous le bloc, une ligne de conséquence écrite en clair : ce que ça coûte au commerçant (§3) et comment on défait.

**Écran 5 — la vérification, faite par nous.**
L'écran ne se valide pas sur un « j'ai fait ». Le serveur attend un appel réel (§5). Tant qu'il n'est pas arrivé, l'état reste **« en attente de vérification »** — jamais « actif ».

---

## 3. Ce qu'on affiche sur le coût, et pourquoi on l'affiche

La deuxième jambe de l'appel est **toujours payée par le commerçant qui pose le renvoi**, jamais par l'appelant. Trois modèles coexistent, et un produit honnête les dit avant, pas après :

| Opérateur du commerçant | Ce qu'on affiche |
|---|---|
| Bouygues **Bbox** → notre 09 | « Gratuit chez votre opérateur. » |
| Orange, SFR, Bouygues **mobile** | « Décompté de votre forfait comme un appel que vous passeriez. » |
| Free fixe et Free mobile | « 0,05 €/min facturés par Free, en plus de votre forfait. » |

Cette dernière ligne a une conséquence commerciale qu'il vaut mieux connaître d'avance : **chez Free, chaque appel capté par l'agent a un coût opérateur pour le client**, faible mais non nul. Sur 60 appels de 2 minutes, environ 6 €. À mettre en regard de l'abonnement, pas à cacher.

---

## 4. Ce qu'on fait là où l'opérateur ne publie rien

Deux trous documentaires sont confirmés, et ils ne se comblent pas à coups d'astuce : **SFR mobile** ne publie aucun code MMI (vérifié sur son sitemap officiel, 2 994 lignes, aucune page de renvoi mobile), et **Free mobile** n'en publie pas non plus hors offre Pro. Les codes qui circulent sur les comparateurs ne sont pas des sources et **n'entrent pas dans le produit**.

Le parcours de secours ne devine pas : il **change de moyen**.
1. On renvoie vers l'espace client de l'opérateur, avec le chemin exact quand il est documenté.
2. À défaut, on propose le chemin **A seul** : l'agent répond sur notre 09, que le commerçant affiche où il veut (fiche Google, site, carte de visite) sans toucher à sa ligne. C'est moins bien, mais c'est vrai, immédiat et sans support.

Même logique pour Orange fixe : le combiné ne sait poser qu'un renvoi **vers la messagerie** ; le renvoi conditionnel vers un numéro tiers passe **obligatoirement par l'Espace client**. Un écran qui afficherait `*61*` pour une Livebox ferait perdre une heure à chaque client. L'écran 4 doit donc pouvoir livrer, selon l'opérateur, **soit un code, soit un chemin de clics**.

**Le bouton « composer » n'est pas fiable partout** : un lien `tel:` doit porter le `#` en `%23`, et les systèmes mobiles restreignent l'exécution des codes MMI depuis un lien. **[NV]** — à tester sur Android et iOS avant de promettre ce bouton. Le bouton **copier**, lui, marche partout : c'est donc lui le chemin principal, et « composer » un bonus.

---

## 5. La vérification : on ne croit pas le client sur parole

Un renvoi peut échouer **en silence**. Trois causes connues, toutes rencontrées ailleurs :

1. **La protection anti-renvoi côté ligne d'arrivée** (Free : `*93#` / `#93#`) fait échouer tous les renvois entrants sans message. À vérifier **côté plateforme**, une fois pour toutes, sur nos propres numéros.
2. **Le répondeur de l'opérateur** reprend la main. Orange l'écrase tout seul, Free exige `*75*…`, Bouygues demande parfois une réinitialisation par le **610** (choix 0, 1, 2) — c'est la panne n°1 attendue au support, elle est déjà scriptée.
3. **Une option de blocage** chez Bouygues mobile rend le renvoi inopérant.

D'où la règle : **l'état d'un numéro est « vérifié le … », pas « configuré »**. Le serveur exige un appel réel arrivé sur le 09 via le renvoi, et l'écran affiche la preuve : l'heure, la durée de sonnerie observée, et si le CLI était présent ou masqué — cette dernière information vaut de l'or au support, parce qu'elle dit tout de suite que l'agent ne pourra pas s'appuyer sur le numéro affiché chez ce client-là.

**Et la surveillance ne s'arrête pas à l'installation.** Un renvoi se défait — un forfait bloqué, une réinitialisation de box, un client qui compose `#002#` sans le dire. Le signal est net : **le trafic tombe à zéro alors que le commerçant est ouvert**. Règle retenue : si un numéro vérifié ne reçoit **aucun appel pendant deux jours d'ouverture consécutifs** alors qu'il en recevait, l'état repasse en **« à revérifier »** et un message part. C'est le seul moyen d'éviter le pire scénario du produit — un commerçant qui paie un agent qui ne reçoit plus rien depuis trois semaines.

---

## 6. Ce qu'on garde en base

Un numéro branché, c'est six informations, pas une chaîne de caractères :

`numero_affiche` (celui des clients) · `numero_arrivee` (notre 09) · `operateur` · `type_renvoi` (`non_reponse` | `occupation` | `inconditionnel`) · `etat` (`en_attente` | `verifie` | `a_reverifier`) · `verifie_le` + `cli_present_a_la_verification`.

Deux règles qui découlent du reste de l'architecture : le numéro d'arrivée est **propre à un locataire** (jamais partagé, sinon on ne sait plus à qui appartient l'appel), et tout cela vit dans les tables partagées avec `tenant_id` et RLS, comme le reste.

---

## 7. Ce qui reste à vérifier sur le terrain, et qu'aucune recherche ne donnera

Une heure de tests réels évite un mois de support. Trois choses, aucune n'est documentée par un opérateur :

- **Ce qui arrive à notre 09 après renvoi, sur les quatre réseaux** : CLI présent, masqué, ou remplacé par le numéro du commerçant. **[NV] pour les quatre.**
- **Le délai réel avant bascule** en renvoi sur non-réponse. Un seul opérateur publie une plage chiffrée (Freebox, 5 à 20 s, passée dans le code) ; Orange mobile est **fixe à 20 s, non réglable** ; les autres parlent de « nombre de sonneries » sans valeur.
- **Le comportement du bouton `composer`** sur Android et iOS.

Tant que ces trois-là ne sont pas mesurées, **aucune promesse commerciale chiffrée sur le délai de décroché**. On dit « l'agent prend le relais quand vous ne répondez pas », on ne dit pas « au bout de 15 secondes ».

---

## 8. Découpage

- **Lot L1** — provisionnement d'un 09, écran 1 à 5 pour **un seul opérateur de test**, vérification par appel réel. Rien de plus : c'est le chemin qui rend le premier appel possible.
- **Lot L2** — les quatre opérateurs, le parcours de secours, l'affichage du coût, la surveillance du trafic à zéro.
- **Plus tard, si un client le demande** — la portabilité, par API, chez un opérateur qui la fait par API. Jamais dans l'onboarding.
