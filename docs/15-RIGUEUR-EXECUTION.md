# La rigueur d'exécution — comment l'agent suit sa tâche jusqu'au bout

> Exigence posée par Adnan le 14/09 : « cet agent doit aussi suivre sa tâche de façon rigoureuse ».
> Ce document traite le seul volet de fiabilité que le dossier n'avait pas encore : ni la fiabilité de **l'écriture** (`04`), ni celle de **la compréhension** (`10`), mais celle de **la mission**.

---

## 1. Le problème, chiffré

**τ-bench** : un agent qui résout une tâche à ~60 % au premier essai tombe à **~25 % sur huit essais de la même tâche**. *La démonstration mesure `pass^1`, le commerce mesure `pass^k`.*

**Et l'aveu d'Intercom** (relevé en A8) : une règle écrite en langue naturelle **peut ne pas être retenue** par le modèle sur un tour donné, et ce n'est *« not a configuration error »*.

**Conclusion qui commande tout ce document : une consigne écrite dans un prompt est suivie *en moyenne*.** Pour un rendez-vous, la moyenne ne suffit pas — le client dont l'appel tombe dans les 25 % n'est pas une statistique, c'est un client perdu et un créneau vide.

---

## 2. La mission est un objet, pas une consigne

Chaque type d'appel est une **mission** déclarée : prendre un rendez-vous · le déplacer · l'annuler · prendre un message · qualifier une panne · répondre à une question.

Une mission porte :
- des **étapes** ordonnées, chacune avec une **condition de sortie vérifiable côté serveur** ;
- des **sorties** possibles (accomplie, transférée, message pris, abandon) ;
- un **plafond de promesse**, hérité du niveau d'adaptateur (`14` §3) ;
- une **dernière étape non sautable** : la confirmation de ce qui a été **réellement écrit**.

**La différence avec un prompt** tient en une phrase : le modèle **propose**, la machine à états **dispose**. Le modèle choisit les mots ; il ne choisit pas si l'étape est franchie.

---

## 3. Les conditions de sortie sont des faits, jamais des impressions

| Étape | ❌ Ce qu'on n'accepte pas | ✅ La condition réelle |
|---|---|---|
| Identifier la demande | « l'agent pense avoir compris » | une **prestation du catalogue** est sélectionnée, ou la mission bascule en « prise de message » |
| Capter le numéro | « le numéro semble correct » | il **passe la grammaire** (`10` §3) : 10 chiffres, préfixe valide, relu à voix haute |
| Choisir un créneau | « l'agent a proposé jeudi 10 h » | le créneau **existe dans la réponse de l'adaptateur**, obtenue pendant cet appel |
| Écrire | « l'outil a répondu » | **`201` relu** (`read-after-write`), sinon l'écriture n'a pas eu lieu |
| Confirmer | « l'agent a dit que c'était noté » | la confirmation **cite les champs relus**, pas ceux demandés |

**Le principe est le même que partout dans ce dossier** : ce qui doit être vrai à 100 % est vérifié **côté serveur**, hors du modèle. Le modèle n'a pas le droit de déclarer une étape franchie.

---

## 4. Les quatre mécanismes anti-dérive

**4.1 La reprise après digression.** Un appelant part sur autre chose — « au fait, vous êtes ouverts lundi ? ». L'agent répond, puis **revient à l'étape non close**. L'état de la mission survit à la digression : c'est lui qui décide de la suite, pas le dernier tour de parole.

**4.2 Aucune étape sautée, et aucune re-demandée.** Ce qui est acquis est acquis : redemander un numéro déjà validé est perçu comme une panne. Ce qui manque est redemandé **une fois**, puis escalade.

**4.3 Le plafond de promesse.** L'agent ne peut pas prononcer une formule que son adaptateur ne garantit pas. En N1 ou N0, « c'est réservé » est **indisponible** — pas déconseillé, indisponible. La formulation est choisie par la machine, pas par le modèle.

**4.4 Le compteur d'échecs.** Trois échecs sur la même information → escalade. Une demande explicite d'humain → **transfert immédiat, sans négociation**. Un échec d'écriture après reprises → **jamais de confirmation**, prise de message et rappel programmé.

---

## 5. Ce qui vit dans le prompt, et ce qui n'y vit pas

| Dans le prompt (le modèle décide) | Hors du prompt (la machine décide) |
|---|---|
| Le ton, les formules, le vouvoiement | Les horaires, fermetures, **pauses** |
| La reformulation d'une question | La disponibilité d'un créneau |
| L'ordre des questions dans un même tour | Le franchissement d'une étape |
| La gestion d'une digression | Le droit de dire « c'est noté » |
| Les réponses aux questions hors mission | Le plafond de promesse et l'escalade |

**Règle de tri** : si une erreur sur ce point produit un rendez-vous faux, une promesse intenable ou une donnée perdue, **ça sort du prompt**. Sinon, ça y reste — et c'est très bien : le modèle est excellent pour le reste.

---

## 6. Comment on le mesure

Trois métriques, toutes déjà prévues ailleurs dans le dossier, mais qui prennent ici leur sens :

- **`pass^5` par mission** — chaque scénario du corpus rejoué cinq fois, **succès intégraux** comptés (`07`). Réussir quatre fois sur cinq, c'est échouer.
- **Taux d'étapes non closes** — appels terminés avec une étape ouverte. C'est la mesure directe de la dérive, et elle n'existe que si la mission est un objet.
- **Taux de confirmation orpheline**, cible **0** — la sanction ultime : l'agent a dit « c'est noté » sans que rien ne soit écrit.

---

## 7. Ce qui reste à confirmer

La recherche **A12** (ce que Retell appelle *Conversation Flow* et Vapi *Workflows*, et ce qu'ils documentent sur l'exécution rigoureuse) n'a jamais abouti — quatre lancements, quatre coupures réseau. **Ce document est donc une conception, pas une synthèse de l'état de l'art.** Ce qui le fonde est en revanche mesuré ou cité : τ-bench, l'aveu d'Intercom, et les règles de fiabilité déjà établies dans `04`, `06`, `07` et `10`.

Ce que A12 pourrait encore apporter : les patrons de reprise après interruption, la façon dont les acteurs exposent une machine à états à un non-technicien, et si l'un d'eux publie un taux d'étapes non closes.


---

## Une valeur retenue doit pouvoir être oubliée — mesuré le 15/09

La mesure 16 de `docs/09` a produit, au premier essai, **une boucle infinie polie** : la machine avait retenu une heure (`18:15`) avec une confiance maximale, l'appelant changeait de jour à chaque tour, et la machine répétait **mot pour mot** le même refus jusqu'à l'abandon. Le modèle n'y était pour rien ; c'est l'état qui était figé.

**Deux règles en découlent, et elles sont aussi importantes que « le modèle propose, la machine dispose » :**

1. **Deux refus consécutifs portant sur la même entité l'invalident.** La machine la vide et la redemande explicitement, en proposant les valeurs possibles : « à quelle heure, parmi 9 h, 9 h 45, 10 h 30 ? »
2. **Aucune réponse de l'agent ne doit être identique à la précédente.** Si la machine s'apprête à redire exactement ce qu'elle vient de dire, c'est qu'elle boucle : elle change de stratégie, ou elle passe la main à un humain. Cette vérification coûte une comparaison de chaînes et supprime le pire mode d'échec téléphonique, celui où l'appelant ne peut pas comprendre d'où vient le blocage.
