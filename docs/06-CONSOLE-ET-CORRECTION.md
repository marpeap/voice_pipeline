# Console et boucle de correction — conception

> Distillé de `docs/recherche2/A8-console-ux.md` (spécification détaillée, états, YAML, gate Barthez) et de `R4 §C.12` (les exploitants réclament la correction, sans vouloir toucher à un prompt).
> Règle qui domine tout ce document : **le commerçant ne voit jamais un prompt, sous aucune forme « avancée ».**

---

## 1. Ce que le marché ne fait pas, et pourquoi

| Acteur | Ce qu'il propose | Pourquoi ça ne marche pas pour un salon |
|---|---|---|
| Intercom Fin | Recommandations issues d'agrégats, et l'aveu écrit : *« No option to fast-track or manually flag individual conversations »* | Il faut du **volume**. Un salon fait 30 appels/jour |
| Zendesk | Correction sur 90 jours de tickets | Même problème, en pire |
| Retell | Débogage d'un tour, « Regenerate 10 answers » | Le correctif *« links to a guide you follow to make the change yourself »* — et son assistant demande une phrase en anglais : **prompt déguisé** |
| Vapi | « Turn production issues into regression tests » | Une consigne écrite à un développeur, **aucun bouton** |

**Le geste juste existe ailleurs** : Gmail « Filter messages like these » — des critères **pré-remplis depuis un seul message** — et la correction iOS 17, « tap the underlined word and choose an option ». Dans les deux cas, l'utilisateur **choisit**, il ne rédige pas.

---

## 2. La correction, en trois appuis

**Une correction n'est jamais du texte. C'est une faute choisie dans une liste courte, appliquée à un empan de transcription, qui produit un objet typé.**

1. **Ouvrir l'appel raté** depuis le fil (ou depuis la notification d'échec).
2. **Toucher le passage fautif** dans la transcription — l'empan est l'ancrage, comme le mot souligné d'iOS.
3. **Choisir la faute** dans une liste de sept. Aucun clavier, sauf pour la seule entrée libre, qui accepte la dictée.

Chaque choix écrit une **contrainte typée**, pas une phrase :

| La faute choisie | Ce qui est écrit | Où |
|---|---|---|
| « Ce n'est pas la bonne prestation » | correspondance terme → prestation, et désambiguïsation | pack du tenant + keyterms |
| « La durée est fausse » | `duree_minutes` sur la prestation | `frontmatter` |
| « Ce créneau n'existe pas » | contrainte d'agenda (pause, fermeture, praticien) | **règle serveur**, pas prompt |
| « Il n'aurait pas dû promettre ça » | interdit explicite | `corps` + garde serveur si l'action est écrivante |
| « Il fallait passer la main » | règle d'escalade (motif, seuil) | `frontmatter` |
| « Mauvaise information » | correction de la fiche (horaire, tarif, accès) | `frontmatter` ou `corps` |
| « Autre » (dictée acceptée) | note datée, **mise en file pour arbitrage**, jamais appliquée seule | `corps`, section *à revoir* |

**Pourquoi les trois contraintes d'agenda sortent du prompt** : Intercom documente qu'une règle rédigée en langue naturelle **peut ne pas être retenue** par le modèle sur un tour donné, et que ce n'est *« not a configuration error »*. Une règle qui s'applique « la plupart du temps » n'est pas une règle. Donc : **ce qui doit être vrai à 100 % est évalué côté serveur**, et le modèle ne peut proposer qu'un créneau que le serveur a déjà validé.

---

## 3. Cycle de vie d'une correction

```
proposée ──► en essai ──► active ──► suspendue
   │            │            │            │
   │            └──► révoquée (le gérant annule)
   │                         │
   └──► expirée              └──► en conflit (contredit une autre correction)
```

- **Écriture serveur à chaque appui.** Fin perd ses modifications au changement de page : inacceptable pour un gérant interrompu toutes les deux minutes.
- **« En essai »** : la correction s'applique, et son effet est visible dans le fil (« depuis cette correction, 4 appels concernés, 0 rechute »).
- **« En conflit »** : deux corrections qui se contredisent ne sont jamais fusionnées en silence — on montre les deux et on demande laquelle vaut.
- **Toute correction alimente automatiquement le corpus de régression.** Personne ne le fait sur le marché. C'est pourtant ce qui transforme un correctif ponctuel en garantie durable : l'appel raté devient un scénario rejoué à chaque changement, `k = 5` fois.

---

## 4. L'écran d'appel

**Contenu, dans cet ordre** : issue en un mot · ce que l'agent a fait (RDV créé, message pris, transfert) · transcription alignée sur l'audio · entités mises en évidence (numéro, date, prestation) · durée et coût · bouton de correction.

**Deux règles contre-intuitives :**
- **Aucun score de confiance affiché.** Google avertit explicitement de ne pas traiter `confidence` comme une mesure fiable. Un passage douteux est **discrètement souligné**, jamais noté.
- **Le mauvais exemple s'affiche en gris, jamais en rouge.** Un gérant qui a peur d'ouvrir sa console ne la corrige pas. Le rouge est réservé à ce qui exige une action immédiate — un échec d'écriture, pas une maladresse de l'agent.

---

## 5. Temps réel, notifications, accessibilité

- **SSE, jamais d'interrogation périodique.** Le cas Pandora est sans appel : 0,2 % des octets pour **46 % de l'énergie**. Et un `setTimeout` est bridé en arrière-plan là où une connexion persistante ne l'est pas. Le flux se ferme dès que l'écran est masqué.
- **Quatre canaux, pas plus** — RDV pris, escalade, **échec d'écriture**, quota — plus **un fil quotidien à 19 h**. Repère : Pielot & Rello mesurent une médiane de **63,5 notifications par jour** et 73,3 % de participants qui ont voulu changer leurs réglages. Le bon geste n'est pas de notifier mieux, c'est de notifier moins.
- **WCAG 2.2 §2.4.11 « Focus Not Obscured »** mord directement sur la feuille de correction qui monte du bas : elle ne doit jamais masquer l'élément qui a le focus.

---

## 6. Les KPI affichés

Exactement ceux qu'on a décidé d'exposer, et pas d'autres : **taux de confirmation orpheline** (cible 0, toute valeur > 0 est un incident) · **taux d'impasse** · taux de passage à l'humain par motif · silence perçu p50/p95 · RDV pris sans intervention · **spams filtrés et non facturés**.

---

## 7. Ce qui reste ouvert

- **Les libellés des sept fautes** doivent être testés à l'oral sur trois gérants avant d'être figés. Ce sont eux qui décident si la boucle fonctionne — la mécanique est triviale, la formulation ne l'est pas.
- Volet iOS « Time Sensitive » : non vérifiable dans la recherche (pages Apple en SPA).
- Centres d'aide Fresha, Zenoti, Boulevard, RingCentral : restés inaccessibles, donc aucune affirmation à leur sujet.
