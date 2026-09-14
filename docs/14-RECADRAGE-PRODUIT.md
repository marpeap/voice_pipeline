# Recadrage — un assistant téléphonique configurable, branchable partout

> Écrit le 2026-09-14 après recadrage d'Adnan. Il corrige une dérive réelle de ce dossier : à force de spécifier le connecteur Crenolo, j'ai fini par traiter Crenolo comme **le** produit alors qu'il n'en est qu'un **adaptateur**.
> ⚠️ Les faits marqués **[à confirmer]** attendent les recherches A9 à A12, interrompues par des coupures réseau. Ils sont écrits comme hypothèses de conception, pas comme acquis.

---

## 1. Ce qu'on construit, en une phrase

**Un agent qui répond au téléphone, qu'un utilisateur configure lui-même en quelques minutes, et qui fait le travail d'un assistant téléphonique dédié — pour son métier à lui.**

Trois exigences en découlent, et elles priment sur tout le reste :
1. **Configuration rapide** — l'utilisateur répond à des questions, jamais à un prompt.
2. **Branchable partout** — sur un logiciel métier, sur un agenda générique, ou sur rien.
3. **Rigueur d'exécution** — l'agent suit sa tâche jusqu'au bout, sans dériver ni oublier une étape.

---

## 2. Un cœur, trois modes de distribution

```
                    ┌──────────────────────────────┐
                    │   CŒUR — identique partout   │
                    │  téléphonie · pipeline audio │
                    │  mémoire · questionnaire     │
                    │  machine à états de tâche    │
                    │  observabilité · facturation │
                    └───────────┬──────────────────┘
        ┌───────────────────────┼───────────────────────┐
   ┌────▼──────┐         ┌──────▼──────┐         ┌──────▼──────┐
   │ GREFFON   │         │  AUTONOME   │         │  EXTENSION  │
   │ dans une  │         │  vendu seul │         │ navigateur  │
   │ app hôte  │         │             │         │ (config)    │
   └───────────┘         └─────────────┘         └─────────────┘
```

**Le cœur ne sait pas dans quel mode il tourne.** C'est la frontière à tenir dès maintenant : chaque fois qu'une décision dépend du mode, elle appartient à l'enveloppe, pas au cœur.

| | Greffon | Autonome | Extension |
|---|---|---|---|
| Qui porte le compte | l'app hôte | nous | ni l'un ni l'autre (elle s'authentifie auprès de l'un des deux) |
| Qui porte l'agenda | l'app hôte | un adaptateur (§3) ou notre agenda minimal | — |
| Qui porte la facturation | l'hôte (marque blanche) ou nous | nous | — |
| Ce qu'elle apporte | l'intégration native, donc la fiabilité | l'autonomie commerciale | **la vitesse de configuration** |

---

## 3. Le contrat d'adaptateur, généralisé

Le connecteur Crenolo (`docs/04-CONNECTEUR-CRENOLO.md`) devient **une implémentation d'un contrat**, pas le contrat lui-même. Quatre niveaux, et **ce que l'agent a le droit de promettre change à chaque niveau** :

| Niveau | Ce qu'il y a en face | Ce que l'agent peut dire | Risque |
|---|---|---|---|
| **N3 — natif** | API du logiciel métier, avec verrou d'occupation et idempotence | « **C'est noté, jeudi 10 h 30** » | faible : `read-after-write` possible |
| **N2 — agenda standard** | Google Calendar, Microsoft Graph, CalDAV, Cal.com | « C'est noté » — **seulement si** l'écriture est relue et le conflit détecté **[à confirmer : ces API garantissent-elles la non-superposition ?]** | moyen |
| **N1 — passerelle** | Zapier, Make, webhook maison | « **Je transmets votre demande, vous recevrez une confirmation** » — jamais « c'est réservé » | élevé : latence et asynchronisme **[à confirmer]** |
| **N0 — rien** | aucune intégration | « Je prends votre message, le salon vous rappelle » + SMS au gérant + export iCal | nul, mais valeur réduite |

**La règle qui tient l'ensemble : l'agent ne promet jamais plus que ce que son adaptateur garantit.** C'est ce qui évite la plainte n°1 relevée dans la recherche — *« unless they have a complete API integration, the ai agent is guaranteed to cause more pain »*. Un N1 honnête vaut mieux qu'un N3 menteur.

**Conséquence de conception** : le niveau est une **propriété déclarée par l'adaptateur**, et le cœur adapte son vocabulaire automatiquement. Ce n'est pas au rédacteur du pack sectoriel d'y penser.

---

## 4. La rigueur d'exécution — ce qui manque au dossier

Jusqu'ici j'ai spécifié la fiabilité **de l'écriture** (idempotence, `read-after-write`, réconciliation) et la fiabilité **de la compréhension** (grammaire française, relecture, DTMF). Il manque la fiabilité **de la tâche** : l'agent suit-il sa mission jusqu'au bout ?

**Le problème est documenté** : τ-bench montre une chute de ~60 % à ~25 % entre un essai et huit sur la même tâche. Et l'aveu d'Intercom, relevé en A8, dit qu'une règle en langue naturelle **peut ne pas être retenue** sur un tour donné, sans que ce soit une erreur de configuration.

**Donc la tâche ne vit pas dans le prompt.** Conception retenue, à confirmer par la recherche A12 :
- **Une machine à états par mission** (prendre un rendez-vous, prendre un message, qualifier une panne), avec ses étapes obligatoires et ses sorties.
- **Chaque étape a une condition de sortie vérifiable côté serveur** — pas « l'agent pense avoir le numéro », mais « le numéro passe la grammaire ».
- **Reprise après interruption** : si l'appelant part sur autre chose, l'agent revient à l'étape non close.
- **Aucune étape ne se saute**, et la dernière est toujours la confirmation de ce qui a été écrit.
- Ce que les acteurs appellent *Conversation Flow* (Retell) ou *Workflows* (Vapi) **[à confirmer, A12]**.

C'est le même principe que partout ailleurs dans ce dossier : **ce qui doit être vrai à 100 % ne se confie pas à un système probabiliste.**

---

## 5. L'extension navigateur — et pourquoi elle est moins coûteuse que je ne l'ai écrit

`docs/02-ARCHITECTURE.md` §7.2 reportait l'extension en dernier lot, avec Firefox écarté faute d'équivalent à `chrome.offscreen` pour l'audio en arrière-plan.

**Ce raisonnement tombe si l'extension ne porte pas d'audio** — et elle n'en porte pas : l'appel arrive par le réseau téléphonique, l'audio vit sur le serveur. L'extension sert à **configurer vite** : questionnaire, règles, voix, numéro, revue d'un appel, correction en trois appuis.

Si c'est confirmé **[A10 en attente]**, alors :
- **Chrome, Firefox desktop et Firefox Android** deviennent atteignables avec un socle commun ;
- ce qui reste à vérifier n'est plus l'audio mais **les API disponibles sur Firefox Android** et la surface d'affichage qu'on y a ;
- l'interdiction de code distant (MV3) garde sa conséquence : la logique vit dans un **paquet npm bundlable**, jamais dans un script hébergé. C'était déjà la décision.

---

## 6. Les frontières à tenir dès maintenant

Pour que le mode autonome ne soit pas une réécriture, cinq règles à ne pas violer :

1. **Le cœur n'appelle jamais un hôte directement** — il passe par le contrat d'adaptateur, même quand l'hôte est chez nous.
2. **L'identité de l'établissement est une donnée du cœur**, pas un identifiant emprunté à l'hôte.
3. **Le questionnaire et le pack sectoriel ne connaissent pas l'hôte** : ils décrivent un métier, pas un logiciel.
4. **La facturation est un module remplaçable** : chez l'hôte en marque blanche, chez nous en autonome.
5. **Toute promesse faite à l'appelant dérive du niveau d'adaptateur**, jamais d'un texte écrit à la main.

---

## 7. Ce qui change dans les documents existants

| Document | Ce qui reste | Ce qui est requalifié |
|---|---|---|
| `04-CONNECTEUR-CRENOLO.md` | tout, y compris les invariants et les lots C0–C7 | devient **l'exemple de référence d'un adaptateur N3**, pas la spécification du produit |
| `02-ARCHITECTURE.md` | les trois frontières, les paquets, le multi-tenant | §7.2 sur l'extension : **à réécrire** après A10 |
| `05-QUESTIONNAIRE-ET-PACKS.md` | tout | les packs sont **indépendants de l'hôte** — c'était déjà vrai, c'est maintenant explicite |
| `11-CHIFFRAGE.md` | mutualisation, coût variable, SMS en tête | il manque **le coût du mode autonome** (numéro, facturation, support) |
| `12-LOTS-CRENOLO.md` | tout | c'est le plan d'**un** adaptateur, pas le plan du produit |

---

## 8. Ce qu'il reste à établir, et par quoi

- **A10** — extension : ce que Firefox Android permet réellement en 2026.
- **A11** — adaptateurs : ce que CalDAV, Google et Microsoft garantissent sur la non-superposition, et si une passerelle tient dans le temps d'un appel.
- **A12** — autonome : ce que le mode seul exige de plus, et comment les acteurs rendent un agent rigoureux.
- **A9** — marquage lisible par machine de l'AI Act sur un flux téléphonique.

Les quatre sont lancées et interrompues par des coupures réseau (`ECONNRESET`, erreurs de certificat). **Rien de ce document ne dépend de leur résultat pour être vrai — mais quatre points y sont marqués [à confirmer], et ils le resteront jusqu'à ce que les rapports arrivent.**
