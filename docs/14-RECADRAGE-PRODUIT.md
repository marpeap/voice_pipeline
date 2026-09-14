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

## 2. Un cœur, quatre surfaces — **mis à jour le 14/09 au soir**

**Précision d'Adnan, transmise par la session Crenolo** : le produit est « **un service à part entière, indépendant** », et Crenolo devient « **un module**, afin que les utilisateurs de Crenolo puissent aussi avoir un agent téléphonique. **Mais ce n'est pas le but premier.** » Le recadrage de ce document allait dans ce sens ; il est désormais **durci** : le mode **autonome est le produit**, le greffon en est une déclinaison.

Et une quatrième surface s'ajoute : **une application mobile et un site de configuration**.

### La question qui commande le coût de l'application mobile

**Touche-t-elle au téléphone, ou seulement aux données ?**

| Réponse | Ce que ça implique | Verdict |
|---|---|---|
| **Seulement les données** — configurer, consulter les appels, recevoir des notifications | Le natif **n'apporte rien** qu'une TWA ne fasse. Et Marpeap a déjà tout l'outillage : une TWA existe pour Crenolo (`com.marpeap.rdv.twa`), avec keystore, `assetlinks.json` en production, build documenté, **et ses trois pièges déjà payés** (JDK 17 obligatoire, `preferIPv4Stack` sans quoi le DNS échoue, AGP 8.9.1 minimum). Sortie : un AAB de 3,6 Mo | ✅ **Retenu. Une seconde TWA se compte en heures.** |
| **Intercepter ou filtrer les appels** sur le mobile du commerçant | `READ_CALL_LOG`, déclaration de permissions, **revue manuelle de Google**, politique qui se durcit au 15/07/2026 [T, à vérifier]. Le refus tomberait **après** le développement | ⛔ **Écarté, et pas seulement pour le risque** |

**La raison de fond du refus** : **le renvoi d'appel est précisément ce qui nous affranchit de tout terminal.** L'audio arrive chez nous par le réseau, jamais sur le mobile du commerçant. Intercepter sur l'appareil ajouterait une dépendance là où l'architecture en supprime une — et l'ARCEP, dont nous citons la recommandation sur le masquage du CLI, **suppose déjà ce modèle**.

## 2 bis. Les surfaces, et le doublon qu'il faut trancher

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

| | **Autonome** (le produit) | Greffon (module) | Site + app mobile | Extension |
|---|---|---|---|---|
| Qui porte le compte | nous | l'app hôte | nous | s'authentifie auprès de l'un des deux |
| Qui porte l'agenda | un adaptateur (§3) ou notre agenda interne | l'app hôte | — | — |
| Qui porte la facturation | nous | l'hôte en marque blanche, ou nous | — | — |
| Ce qu'elle apporte | **l'autonomie commerciale** | l'intégration native, donc la fiabilité | **la configuration et la consultation, partout** | ~~la vitesse de configuration~~ — **voir ci-dessous** |

⚠️ **Le doublon, et il faut le trancher maintenant plutôt que de le payer deux fois.** J'avais donné à l'extension comme apport propre « la vitesse de configuration ». **Si un site de configuration rapide existe — et Adnan le demande —, cet argument tombe.** Ce qui resterait à l'extension : corriger un appel **sans changer d'onglet**, depuis n'importe quelle page. C'est réel, mais mince.

**Décision : le site responsive (et sa TWA) est la surface principale ; l'extension passe en lot ultérieur, et seulement si l'usage montre que le changement d'onglet freine réellement la correction.** Construire les deux en même temps, c'est deux surfaces à maintenir pour un même geste. Le travail déjà fait (`16-EXTENSION-PERIMETRE.md`, recherche A10) n'est pas perdu : il dit exactement ce que coûterait ce lot le jour où on le décidera — et il a **déjà** servi, en établissant que l'authentification devra passer par un **jeton d'appairage** puisque `identity` n'existe pas sur Firefox Android.

---

## 3. Le contrat d'adaptateur, généralisé

Le connecteur Crenolo (`docs/04-CONNECTEUR-CRENOLO.md`) devient **une implémentation d'un contrat**, pas le contrat lui-même. Quatre niveaux, et **ce que l'agent a le droit de promettre change à chaque niveau** :

| Niveau | Ce qu'il y a en face | **La phrase exacte que l'agent a le droit de dire** |
|---|---|---|
| **N0 — notre base** | agenda interne, verrou et contrainte à nous | « **c'est réservé** » |
| **N1 — réservation de créneau chez l'éditeur** | `POST /v2/slots/reservations` de Cal.com — « *Make a slot not available for others to book* », 5 min | « **c'est réservé** », dans le périmètre de cet éditeur |
| **N2 — agenda standard** | Google Calendar, Microsoft Graph, CalDAV | « **c'est enregistré** » — ⛔ **jamais « c'est bloqué »** |
| **N3 — passerelle** | Zapier, Make | « **je transmets votre demande** » |
| **N4 — aucune API** | rien en face | « **j'ai noté votre demande** » |

### Pourquoi N2 ne peut pas dire « c'est bloqué » — la réponse d'A11, et elle est nette

**Aucun des trois grands n'empêche le chevauchement**, et ce n'est pas une lacune de documentation : c'est une absence de mécanisme.

- **Google `events.insert`** : six paramètres optionnels, **aucune détection de conflit, aucun `requestId`, aucune clé d'idempotence**, rien sur le comportement en cas de chevauchement. **Deux insertions concurrentes sur le même créneau réussissent toutes les deux.** L'ETag n'apparaît que dans **une seule phrase** de toute la documentation, jamais spécifiée : le contrôle optimiste y est un **comportement de fait, non contractualisé**.
- **Microsoft Graph** : rien non plus sur le conflit — la seule erreur de chevauchement documentée concerne les exceptions d'une série récurrente. ⚠️ **Mais une vraie exception existe** : **`transactionId`**, clé d'idempotence fournie par le client, « *to avoid redundant POST operations in case of client retries* ». **Elle règle le rejeu après timeout, pas la concurrence.** Et `getSchedule` est une **photographie sans durée de validité**, qui échoue au-delà de 1 000 entrées.
- **CalDAV (RFC 4791)** est le seul à parler sérieusement de concurrence — **et à dire que le chevauchement n'est pas son sujet**. ETags forts **MUST** ; `If-None-Match: *` protège contre une **collision de nom de fichier**, la RFC le dit elle-même ; `CALDAV:no-uid-conflict` porte sur **l'UID, pas sur l'intervalle** ; et le rapport free-busy §7.10 précise : **« Preconditions: None. »** La RFC **autorise explicitement** des périodes occupées qui se recouvrent.

**La ligne qui explique tout le reste : dans les trois cas, aucune ressource serveur ne représente « le créneau ». On ne verrouille que ce qui existe.** Cal.com peut offrir une réservation de créneau **parce qu'il possède sa propre base** — pas parce qu'il serait plus malin.

**Et les autres voies sont pires qu'on ne le pensait** : Calendly a une API d'écriture, mais ses réponses documentées **ne comportent aucun `409`** alors que la même spécification en définit ailleurs — **un créneau déjà pris devient indistinguable d'une erreur de payload**. Les passerelles sont hors jeu dans le temps d'un appel : **Zapier va de 15 minutes à 1 minute selon le plan**, Make 15 minutes par défaut ; **seul n8n auto-hébergé** peut tenir le budget d'un tour de parole, et cela reste à mesurer. Enfin, sur **sept logiciels verticaux** examinés, **un seul — Phorest — publie une API d'écriture de rendez-vous**.

**La règle qui tient l'ensemble : l'agent ne promet jamais plus que ce que son adaptateur garantit.** C'est ce qui évite la plainte n°1 relevée dans la recherche — *« unless they have a complete API integration, the ai agent is guaranteed to cause more pain »*. Un N1 honnête vaut mieux qu'un N3 menteur.

**Conséquence de conception** : le niveau est une **propriété déclarée par l'adaptateur**, et le cœur adapte son vocabulaire automatiquement. Ce n'est pas au rédacteur du pack sectoriel d'y penser.

### 3 bis. Le mur des 100 utilisateurs, et pourquoi le N0 passe devant le N2 (A17)

**[F] Google plafonne une application non vérifiée à 100 nouveaux utilisateurs — « over the entire lifetime of the project », « cannot be reset or changed ».** Le plafond vaut **aussi pour les scopes sensibles**. Chaque test et chaque démo consomme une place **définitivement**, et au 100ᵉ commerçant connecté, la connexion Google **s'éteint**.

**Cela inverse l'ordre de construction** que ce document laissait supposer :

1. **Agenda interne par défaut** — zéro OAuth, zéro plafond, et **nous sommes la source de vérité**, donc le verrou anti-double-booking nous appartient.
2. **Export iCal en lecture seule** — le commerçant retrouve ses rendez-vous dans **son** agenda. Google, Outlook **et Apple** l'acceptent nativement par simple abonnement à une URL : aucune vérification, aucun coût, et **c'est la seule chose qui fonctionne avec iCloud, qui n'a aucune API** [NV].
3. **Connexion Google bidirectionnelle plus tard**, sur un projet dédié dont les 100 places sont **intactes** — et la vérification (10 jours annoncés, **3 à 6 semaines réelles**) se lance **dès maintenant**, puisqu'elle ne coûte rien à démarrer et que seule l'attente est perdue.
4. **Nylas en soupape** : **83,50 $/mois à 50 clients, 448 $/mois à 500** — le seul intermédiaire qui publie un prix à l'agenda connecté. Cronofy démarre à **819 $/mois**, et **Cal.com Platform est fermé aux nouveaux depuis le 15/12/2025**.

**La question du niveau N2 est tranchée** (A11, 14/09) : **non, aucune de ces API ne garantit la non-superposition** — voir §3. La session Crenolo n'avait pas pu y répondre depuis son code, et pour une bonne raison : **Crenolo n'écrit pas dans Google Calendar**, il implémente Actions Center en variante *Appointments Redirect*.

⚠️ **La question à dix minutes qui commande tout ce paragraphe** : la Console Google affiche-t-elle les scopes Calendar en *Sensitive* ou en *Restricted* ? La doc publique ne le dit **nulle part**. *Sensitive* = 10 jours de revue, zéro euro. *Restricted* = 6 semaines **et** un audit de sécurité annuel au prix non publié.

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

## 5 bis. Les briques du mode autonome, chiffrées (A13 à A16)

Quatre recherches rentrées malgré les coupures. Détail dans `docs/recherche2/A13` à `A16`.

| Question | Décision | Ce qui la fonde |
|---|---|---|
| Isolation | **Pool** : une base, `tenant_id`, RLS en **second** filet | `max_connections` vaut 100 par défaut et dimensionne la mémoire partagée — une base par TPE est intenable. Azure classe l'isolation par table en **antipattern** |
| Secrets | **Une clé KMS + contexte de chiffrement `{tenant_id, purpose}`**, jamais une clé par tenant | **3,84 $/mois contre 1 500 $/mois** à 500 tenants. Prévoir `kms_key_arn` **nullable** dès le schéma pour le jour où un client exigera la sienne — et la paiera |
| Authentification | **ZITADEL auto-hébergé**, repli **Logto OSS** | Seuls à offrir des **organisations illimitées gratuites** sans coupler le prix au nombre de tenants. Auth0 demanderait **700 $/mois à 500 tenants** ; Ory plafonne à **3 organisations** sous 9 350 $/an |
| Facturation | **Notre base est la source de vérité**, `call_id` comme clé d'idempotence, **un appel = un événement en secondes** | Stripe ne garantit l'unicité que sur **24 h glissantes** et le backfill sur **35 jours**. Cette discipline rend le prestataire remplaçable |
| Encaissement | **Prélèvement SEPA** plutôt que carte | 0,35 € fixe contre 1,5 % + 0,25 € : **~1 075 €/mois d'économie à 500 clients**, davantage que le coût total d'un Lago auto-hébergé |
| Support | **Crisp** (facturé au *workspace*) ou **Chatwoot sans `enterprise/`** | Chatwoot est MIT **sauf** son répertoire `enterprise/`, sous licence propriétaire — le README ne le dit pas |

⚠️ **Et le risque propre au mode autonome, qui n'existe pas en greffon** : **l'inscription est la porte d'entrée du fraudeur**. Un compte créé en quelques minutes obtient un numéro et une capacité d'émission — soit exactement la primitive recherchée pour la fraude à la terminaison. **10 appels simultanés pendant une nuit coûtent 769 $** au tarif mobile France standard. Or **`UsageTrigger` de Twilio notifie mais ne coupe pas**, et `UsageRecord` ne garantit aucune fraîcheur : **le plafond dur est notre code**, alimenté par les webhooks d'appel, refusant l'appel **avant** émission. Par défaut à l'inscription : France métropolitaine seule, plafond bas, aucune destination internationale.

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
