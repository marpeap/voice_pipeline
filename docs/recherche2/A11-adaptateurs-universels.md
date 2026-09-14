# A11 — Adaptateurs universels d'agenda : qu'est-ce qui empêche deux rendez-vous de se superposer ?

> État : **septembre 2026** (consultations du 2026-09-14).
> Méthode : sources officielles (docs éditeurs, RFC), WebFetch direct, URL + date de consultation.
> Marquage : **[F]** fait vérifié à la source · **[H]** hypothèse raisonnée · **[R]** risque · **[NV]** non vérifié / source inaccessible.
>
> **Question centrale** : quand notre agent téléphonique écrit un événement dans un agenda tiers,
> qu'est-ce qui, techniquement, empêche deux rendez-vous de se superposer ?
> Chez nous : verrou en base + contrainte SQL. Ailleurs : voir ci-dessous.

**Résultat central** : ni Google Calendar, ni Microsoft Graph, ni CalDAV n'empêchent deux rendez-vous de se superposer. Aucun des trois n'expose d'objet serveur représentant « le créneau », donc rien à verrouiller. La garantie de non-superposition n'est pas une propriété des agendas : c'est une propriété de celui qui détient la source de vérité.

---

## 1. Google Calendar API — la non-superposition

### 1.1 `events.insert` n'empêche rien. C'est le résultat majeur.

**[F]** La page de référence de `events.insert` liste exactement six paramètres de requête optionnels :
`conferenceDataVersion`, `eventLabelVersion`, `maxAttendees`, `sendNotifications` (déprécié),
`sendUpdates`, `supportsAttachments`.
Il n'y a **aucun** paramètre, aucun en-tête, aucune clause de corps liés à la détection de conflit,
à la prévention de chevauchement, à une clé d'idempotence ou à un `requestId`.
Le document ne décrit **aucun comportement** de l'API en cas de chevauchement avec un événement existant.
→ Source : https://developers.google.com/workspace/calendar/api/v3/reference/events/insert — consulté le **2026-09-14**.

> **Conclusion nette, à énoncer telle quelle : rien, dans l'API Google Calendar, n'empêche
> deux événements de se superposer.** Un agenda Google est une **liste d'événements**, pas une
> ressource à exclusion mutuelle. Deux `events.insert` concurrents sur le même créneau
> réussissent tous les deux, renvoient deux `id` distincts, et l'agenda affiche deux
> rendez-vous empilés. Aucune erreur, aucun avertissement, aucun code 409.

**[F]** Corollaire : il n'existe **pas de clé d'idempotence** sur `events.insert`. Un
`POST` rejoué après un timeout réseau crée un **deuxième événement**. (Contre-mesure côté appelant :
générer soi-même l'`id` de l'événement — Google accepte un `id` fourni par le client, ce qui rend
la création idempotente par collision d'identifiant. **[H]** Non confirmé dans la page insert
consultée ; à vérifier dans la ressource Events avant de s'en servir comme garantie.)

### 1.2 ETag / If-Match : mentionnés, jamais spécifiés

**[F]** La page `events.update` contient une seule phrase sur le sujet, dans sa description :
« *To do a partial update, perform a `get` followed by an `update` using etags to ensure atomicity.* »
Le reste de la page — paramètres, corps de requête, réponses — ne mentionne **ni** en-tête `If-Match`,
**ni** code `412 Precondition Failed`, **ni** aucune sémantique de concurrence.
→ https://developers.google.com/workspace/calendar/api/v3/reference/events/update — consulté le **2026-09-14**.

**[F]** Le guide *Performance* de l'API Calendar ne parle d'ETag que dans un exemple **générique**
d'API fictive (« *If you use the `If-Match: "ETagString"` HTTP header* … »), sans jamais affirmer
que Calendar l'implémente.
→ https://developers.google.com/workspace/calendar/api/guides/performance — consulté le **2026-09-14**.

**[R]** Autrement dit : le contrôle de concurrence optimiste sur Google Calendar est un
**comportement de fait**, hérité de l'infrastructure Google API, **non contractualisé dans la
documentation du produit**. Construire une promesse client dessus, c'est construire sur du
non-documenté.

**[F] Et surtout — point décisif, souvent mal compris :** même si `If-Match` fonctionnait
parfaitement, il ne résout **pas** le problème. `If-Match` protège **un événement contre sa propre
modification concurrente**. Il ne dit rien du chevauchement entre **deux événements différents**.
L'ETag de l'événement A n'a aucune relation avec la création de l'événement B sur le même créneau.
**Il n'existe, dans Google Calendar, aucun objet sur lequel poser un verrou représentant « le créneau ».**

---

## 2. Microsoft Graph — même question, réponse presque identique, avec une exception

### 2.1 `POST /events` n'empêche pas non plus le chevauchement

**[F]** La page *Create event* (v1.0, `ms.date` 2026-07-29, mise à jour 2026-08-03) ne documente
**aucune** détection de conflit, **aucun** contrôle de chevauchement, **aucun** code d'erreur de
type « créneau déjà pris ». La ressource `event` n'a **aucune propriété** `hasConflict` /
`conflictingEvents` en v1.0 : la liste complète des propriétés (allowNewTimeProposals … webLink)
n'en contient pas.
→ https://learn.microsoft.com/en-us/graph/api/user-post-events?view=graph-rest-1.0
et https://learn.microsoft.com/en-us/graph/api/resources/event?view=graph-rest-1.0 — consultés le **2026-09-14**.

> **Deuxième résultat majeur : Microsoft Graph non plus n'empêche pas deux rendez-vous de se
> superposer.** Outlook *affiche* un avertissement de conflit dans son interface ; l'API, elle,
> accepte l'écriture sans broncher. L'unique erreur de chevauchement documentée est
> `ErrorOccurrenceCrossingBoundary` sur `PATCH`, et elle concerne **uniquement** les exceptions
> d'une série récurrente vis-à-vis de **leurs propres occurrences voisines** — jamais deux
> rendez-vous distincts :
> « *Modified occurrence is crossing or overlapping adjacent occurrence.* »
> → https://learn.microsoft.com/en-us/graph/api/event-update?view=graph-rest-1.0 — consulté le **2026-09-14**.

### 2.2 L'exception qui compte : `transactionId`, une vraie clé d'idempotence [F]

Graph a ce que Google n'a pas. Définition exacte, ressource `event` :

> « **transactionId** | String | *A custom identifier specified by a client app for the server to
> avoid redundant POST operations in case of client retries to create the same event. It's useful
> when low network connectivity causes the client to time out before receiving a response from the
> server for the client's prior create-event request. After you set transactionId when creating an
> event, you can't change transactionId in a subsequent update. This property is only returned in a
> response payload if an app has set it. Optional.* »
> → https://learn.microsoft.com/en-us/graph/api/resources/event?view=graph-rest-1.0 — consulté le **2026-09-14**.

**Pourquoi c'est important pour un agent téléphonique** : le rejeu est le mode de défaillance le
plus probable d'une écriture pendant un appel (timeout réseau, l'agent réessaie, l'appelant
raccroche). `transactionId` élimine le doublon **par rejeu**. Il n'élimine **pas** le doublon
**par concurrence** (deux appelants différents, même créneau) : ce sont deux `transactionId`
distincts, donc deux événements créés.
**[R]** La durée de rétention de la clé n'est pas documentée sur la page consultée. **[NV]**

### 2.3 ETag / If-Match sur Graph

**[F]** La table *Request headers* de `PATCH /events/{id}` ne liste **que** `Authorization`.
Aucun `If-Match` documenté sur cette page.
→ https://learn.microsoft.com/en-us/graph/api/event-update?view=graph-rest-1.0 — consulté le **2026-09-14**.

**[F]** Les réponses portent bien `@odata.etag` (ex. `W/"ZlnW4RIAV06KYYwlrfNZvQAALfZeRQ=="`) et la
propriété `changeKey`, définie ainsi : « *Identifies the version of the event object. Every time the
event is changed, ChangeKey changes as well. It allows Exchange to apply changes to the correct
version of the object.* » — même source.
**[H]** Le support d'`If-Match` sur les entités Outlook de Graph est un comportement connu de
l'infrastructure OData/Exchange mais **n'est pas documenté sur la page de l'opération**.
Même remarque qu'au §1.2 : cela protège **un** événement contre l'écrasement, pas **un créneau**
contre la double réservation.

### 2.4 `getSchedule` : une photographie, pas une réservation [F]

Description officielle : « *Get the free/busy availability information for a collection of users,
distribution lists, or resources (rooms or equipment) for a specified time period.* »
Réponse : `availabilityView` (chaîne de chiffres, un par tranche de `availabilityViewInterval`,
défaut 30 min, min 5, max 1440) + `scheduleItems` + `workingHours`.
→ https://learn.microsoft.com/en-us/graph/api/calendar-getschedule?view=graph-rest-1.0 — consulté le **2026-09-14**.

**Ce que le document ne dit nulle part** : que le résultat engage l'avenir. Il n'y a **aucune**
notion de *hold*, de *tentative reservation*, de TTL, de jeton à repasser à l'écriture.
`getSchedule` est un **état à l'instant t**, et il ne verrouille rien.
**[F]** Il a même une limite dure qui le rend faillible : « *When the user's calendar has a time slot
that contains more than 1000 entries, a `5006` response code with the message "The result set
contains too many calendar entries..." will be returned.* » — un salon très chargé peut donc voir
sa lecture de disponibilité **échouer** alors que l'écriture, elle, réussirait.

**[F] Nuance réelle, et la seule du dossier** : Exchange sait refuser une double réservation
**pour les salles** (`resource mailbox` en mode *AutoAccept* avec `AllowConflicts $false`), car une
salle est un objet dont l'agenda est arbitré par un agent serveur. Mais ce refus n'est **pas**
synchrone : la création de l'événement réussit, et c'est le *Resource Booking Attendant* qui
**décline ensuite** l'invitation par message. **[R]** Pour un agent téléphonique, un refus qui
arrive après le raccroché est inutilisable comme garantie. **[NV]** Non re-vérifié à la source
Exchange dans cette passe.

---

## 3. CalDAV (RFC 4791, mars 2007) — le seul des trois qui parle vraiment de concurrence,
## et qui dit quand même que le chevauchement n'est pas son problème

Source unique de ce chapitre : **RFC 4791**, https://www.rfc-editor.org/rfc/rfc4791.txt — consultée le **2026-09-14**.

### 3.1 ETags : obligatoires, et forts [F]

§2 (Requirements Overview) : « *MUST support ETags [RFC2616] with additional requirements specified
in Section 5.3.4 of this document* ».
§5.3.4 : « *The DAV:getetag property MUST be defined and set to a **strong** entity tag on all
calendar object resources.* » … « *A response to a GET request targeted at a calendar object
resource MUST contain an ETag response header field indicating the current value of the strong
entity tag* ».

C'est **beaucoup plus fort que Google et Microsoft** : chez CalDAV, l'ETag est **normatif et
obligatoire**, pas un comportement de fait non documenté.

**[R]** Piège documenté : « *In the case where the data stored by a server as a result of a PUT
request is not equivalent by octet equality to the submitted calendar object resource, the behavior
of the ETag response header is not specified here, with the exception that a strong entity tag
MUST NOT be returned in the response.* » — un serveur qui normalise l'iCalendar (beaucoup le font)
**ne rend pas d'ETag** sur le PUT ; le client doit refaire un GET. Une étape réseau de plus, pendant
un appel téléphonique.

### 3.2 `If-None-Match: *` à la création : une vraie exclusion mutuelle, mais sur l'URI [F]

§5.3.2 — le texte est explicite sur son intention et sur sa portée :

> « *a client might not want to examine all resources in the collection and might not want to lock
> the entire collection to ensure that a new resource isn't created with a name collision. However,
> there is an HTTP feature to mitigate this. […] the client SHOULD use the HTTP request header
> "If-None-Match: \*" on the PUT request. […] The "If-None-Match: \*" request header ensures that the
> client will not inadvertently overwrite an existing resource if the last path segment turned out
> to already be used.* »

Et pour la modification : « *The request to change an existing event is the same, but with a
specific ETag in the "If-Match" header* ».

**Lecture critique** : `If-None-Match: *` garantit l'unicité **d'un nom de fichier**, pas d'un
créneau. C'est exactement la même limite que chez Google et Microsoft, énoncée ici en toutes lettres
par la RFC elle-même : la garantie porte sur **la collision de nom**, jamais sur le temps.

### 3.3 `CALDAV:no-uid-conflict` : la seule contrainte d'unicité normative du dossier [F]

§5.3.2.1, préconditions additionnelles de PUT/COPY/MOVE :

> « *(CALDAV:no-uid-conflict): The resource submitted in the PUT request, or targeted by a COPY or
> MOVE request, MUST NOT specify an iCalendar UID property value already in use in the targeted
> calendar collection or overwrite an existing calendar object resource with one that has a
> different UID property value.* »

**C'est l'équivalent le plus proche d'une contrainte SQL `UNIQUE` dans tout ce dossier.** Elle est
**MUST**, donc opposable. Mais elle porte sur le **UID iCalendar**, c'est-à-dire sur *l'identité du
rendez-vous*, pas sur son *intervalle*. Elle donne donc une **idempotence de création** gratuite
(rejouer le même PUT avec le même UID échoue au lieu de dupliquer) — ce que Google n'a pas et ce que
Graph obtient via `transactionId`. Elle ne donne **aucune** exclusion temporelle.

### 3.4 Le verrouillage WebDAV : possible, et explicitement déconseillé pour réserver [F]

§8.3 *Use of Locking* — le seul endroit du dossier où un verrou existe vraiment :

> « *WebDAV locks can be used to prevent two clients that are modifying the same resource from
> either overwriting each others' changes (though that problem can also be solved by using ETags)…* »
> « *Clients are responsible for requesting a lock timeout period that is appropriate to the use case.
> When the user explicitly decides to reserve a resource and prevent other changes, a long timeout
> might be appropriate, but in cases where the client automatically decides to lock the resource,
> the timeout should be short…* »

Là encore : le verrou porte sur **une ressource existante** (un événement, une collection). On ne
peut pas verrouiller « mardi 14 h », qui n'est pas une ressource. **[H]** On *pourrait* verrouiller
la collection entière le temps d'un lire-puis-écrire — la RFC le mentionne comme la chose que le
client « ne veut pas » faire — ce qui sérialiserait toutes les écritures de l'agenda. Coût :
latence et fragilité ; sur un agenda partagé multi-clients, le verrou est refusé (`423 Locked`) dès
qu'un autre client le détient. **[R]** Support réel très inégal : de nombreux serveurs CalDAV
n'implémentent pas LOCK/UNLOCK, qui n'est pas dans la liste des MUST du §2.

### 3.5 `CALDAV:free-busy-query` (§7.10) : une photographie, et la RFC le dit [F]

Support **REQUIRED**. Description : « *generates a VFREEBUSY component containing free busy
information for all the calendar object resources targeted by the request…* » ; « *This report only
returns busy time information. Free time information can be inferred from the returned busy time
information.* »

Et, décisif : **« Preconditions: None. »** La seule postcondition est
`DAV:number-of-matches-within-limits`, c'est-à-dire une limite de volume côté serveur.

> **Le rapport free-busy n'est ni une réservation, ni une option, ni un engagement. C'est une
> photographie, et la RFC ne prétend rien d'autre.** Le mot « conflict » n'apparaît dans la RFC 4791
> qu'au sens HTTP `409` et dans `no-uid-conflict` ; **le mot « overlap » n'y apparaît jamais au sens
> de deux rendez-vous qui se chevauchent** — uniquement au sens « composants qui recouvrent
> l'intervalle interrogé » (filtres `time-range`) et « périodes busy à fusionner »
> (« *Servers SHOULD coalesce consecutive or overlapping busy time periods of the same type. Busy time
> periods with different FBTYPE parameter values MAY overlap.* »).

Noter la dernière phrase : la RFC **autorise explicitement** des périodes occupées qui se
chevauchent dans la réponse. Le chevauchement n'est pas une anomalie dans le modèle CalDAV ; c'est
un état normal.

### 3.6 Et RFC 6638 (scheduling) ? [H] [NV]

Le *CalDAV Scheduling Extensions* (RFC 6638) ajoute la négociation organisateur/participants
(boîtes `schedule-inbox`/`schedule-outbox`, `Attendee` `PARTSTAT`). Il déplace le problème vers
l'**acceptation asynchrone d'une invitation** — utile pour une salle de réunion, inutile pour un
agent qui doit dire « c'est réservé » avant que l'appelant ne raccroche. **Non vérifié à la source
dans cette passe.**

---

## Bilan intermédiaire des trois protocoles

| | Empêche le chevauchement ? | Idempotence de création | Concurrence optimiste | Verrou sur le créneau |
|---|---|---|---|---|
| **Google Calendar API** | **Non** [F] — rien de documenté | **Non** documentée sur `insert` [F] ; `id` client **[H]** | ETag évoqué en une phrase, jamais spécifié [F][R] | **Aucun objet à verrouiller** [F] |
| **Microsoft Graph** | **Non** [F] | **Oui** — `transactionId` [F] (rejeu seulement) | `@odata.etag` / `changeKey` présents ; `If-Match` non documenté sur l'opération [F][H] | **Aucun** [F] |
| **CalDAV / RFC 4791** | **Non** [F] — la RFC n'en parle même pas | **Oui** — `CALDAV:no-uid-conflict`, **MUST** [F] | **ETag fort, MUST** [F] ; `If-Match` / `If-None-Match: *` normatifs | LOCK WebDAV sur une **ressource**, jamais sur un intervalle [F][R] |

**La ligne qui décide de tout** : dans les trois cas, **il n'existe aucune ressource serveur qui
représente « le créneau ».** Or on ne peut verrouiller que ce qui existe. C'est pourquoi aucun des
trois n'offre — et ne peut offrir — la garantie que notre contrainte SQL donne chez nous.

---

## 4. La conséquence pratique : l'intervalle entre lire et écrire, et ce que les acteurs en font

Entre `freebusy.query` / `getSchedule` / `free-busy-query` et l'écriture, il y a un **intervalle**.
Pendant un appel téléphonique, cet intervalle n'est pas de quelques millisecondes : c'est le temps
que l'agent énonce les créneaux, que l'appelant hésite, choisisse, épelle son nom.
**Dix à soixante secondes**, réalistement. C'est une éternité en terme de course.

### 4.1 Cal.com — la réponse de référence : **réserver le créneau avant de le proposer** [F]

Cal.com expose un endpoint dédié, `POST /v2/slots/reservations` (*Reserve a slot*), dont la
description officielle est :

> « *Make a slot not available for others to book for a certain period of time.* »

- Durée par défaut : **5 minutes**.
- `reservationDuration` : durée personnalisée, **réservée aux requêtes authentifiées** (clé API,
  jeton d'accès ou OAuth).
- Pendant la réservation, **personne d'autre ne peut réserver** ce type d'événement à cet horaire.
→ https://cal.com/docs/api-reference/v2/slots/reserve-a-slot — consulté le **2026-09-14**.

**C'est exactement le mécanisme qui manque à Google, Microsoft et CalDAV** : un objet serveur qui
représente « ce créneau, pris, provisoirement ». Cal.com peut l'offrir **parce que Cal.com possède
sa propre base** et n'est pas un simple miroir de l'agenda tiers.

**[F]** Cal.com documente aussi, sur la création de réservation, un paramètre `allowConflicts` :
« *When true, availability conflict checks are bypassed for an authenticated user who has access
through the existing event owner, host, assigned user, team admin or organization admin checks.* »
→ https://cal.com/docs/api-reference/v2/bookings/create-a-booking — consulté le **2026-09-14**.
Donc **Cal.com fait bien un contrôle de conflit côté serveur à l'écriture** (sinon il n'y aurait
rien à contourner). **[R]** En revanche le code d'erreur exact retourné en cas de conflit n'est
**pas documenté** sur cette page, ni aucune clé d'idempotence. **[NV]**

### 4.2 Cronofy — idempotence oui, non-superposition non [F]

*Upsert Event* : « *The first request made for a `calendar_id` and `event_id` combination will
create an entry in the calendar and all subsequent requests will update the details of the event.* »
→ https://docs.cronofy.com/developers/api/events/upsert-event/ — consulté le **2026-09-14**.

C'est une **clé d'idempotence fournie par le client**, de même nature que le UID CalDAV : elle règle
le rejeu, pas la concurrence. La documentation **ne mentionne aucune** détection de conflit ni
refus fondé sur la disponibilité du créneau.

*Availability API* : la documentation **ne traite ni** de la double réservation, **ni** de la course
entre la requête de disponibilité et la création de l'événement. Le seul mécanisme voisin documenté
est le `buffer` (`before` / `after`), configurable globalement ou par membre
(`participants.members.buffer`) — **une préférence d'ordonnancement, pas un verrou**.
→ https://docs.cronofy.com/developers/api/scheduling/availability/ — consulté le **2026-09-14**.

### 4.3 Nylas — rien de documenté sur le sujet [F]

La documentation Scheduler v3 mentionne les types de réunion (one-on-one, collective, round-robin,
group) et le fait qu'« *When a booking is confirmed, Scheduler displays a booking confirmation
message and sends a confirmation email to all participants* », **sans aucune** discussion de la
prévention de double réservation, de la péremption des disponibilités, ni d'une garantie de
confirmation.
→ https://developer.nylas.com/docs/v3/scheduler/ — consulté le **2026-09-14**.

### 4.4 Calendly — écriture directe désormais possible, garantie toujours pas documentée [F]

**Nouveauté à retenir (état septembre 2026)** : Calendly expose maintenant une *Scheduling API* qui
permet de réserver **sans** passer par sa page de réservation.
`POST /invitees` — *Create Event Invitee (Scheduling API)* :

> « *Creates a new booking for an event invitee. Use this endpoint to book an invitee directly from
> your app without redirects, iframes, or Calendly-hosted UI.* »
> « *Standard notifications, calendar invites, reschedules, and workflows run as if booked via the
> Calendly UI.* »
> « *Access to this endpoint is limited to Calendly users on paid plans (Standard and above). Users
> on the Free plan will receive a 403 Forbidden response.* »

Corps requis : `event_type`, `start_time`, `invitee`. Scope OAuth : `scheduled_events:write`.
→ Spécification OpenAPI officielle, https://developer.calendly.com/openapi/calendly-api.yaml
(chemin `/invitees`) — téléchargée et lue le **2026-09-14**.

**[F] Le point qui compte** : les réponses documentées de `POST /invitees` sont
`201, 400, 401, 403, 404, 500`. **Il n'y a pas de `409 Conflict`.** Et ce n'est pas un oubli
d'écriture de la spec : le même fichier **définit** des schémas `409` ailleurs
(`Create-contactRequestConflictError`, `Patch-contacts-uuidRequestConflictError`,
`CreatewebhooksRequestConflictError`). Calendly sait écrire un 409 quand il en veut un ; il n'en a
pas mis sur la réservation.
**[H]** Le refus d'un créneau déjà pris arrive donc probablement en `400 Bad Request` générique —
non documenté, donc non contractuel, donc **impossible à distinguer de manière fiable** d'une
erreur de payload par un agent automatisé. **[R]** Sérieux : un agent téléphonique doit savoir
distinguer « créneau pris, propose autre chose » de « ma requête est mal formée ».

**[F]** Lecture des disponibilités : `GET /event_type_available_times` (plage ≤ **31 jours**) et
`GET /user_busy_times` (plage ≤ **7 jours**). Aucune notion de réservation temporaire, aucun jeton
de créneau. Et une note qui détruit toute idée de garantie côté agendas externes :

> « *External events will only be returned for calendars that have "Check for conflicts" configured.* »

Autrement dit, la vue de Calendly sur l'agenda réel du professionnel **dépend d'une case cochée par
l'utilisateur final**. Aucun tiers ne peut la garantir à distance.

**[F]** `POST /scheduling_links` (lien à usage unique, `max_event_count`) est la voie historique :
elle plafonne le nombre de réservations par lien, ce qui est un garde-fou de volume, **pas** une
exclusion temporelle.

### 4.5 Ce que « réservation garantie » veut dire en pratique

Synthèse des quatre acteurs :

| Acteur | Écriture directe par un tiers | Contrôle de conflit à l'écriture | Idempotence | Verrou de créneau |
|---|---|---|---|---|
| **Cal.com** | Oui | **Oui** (implicite via `allowConflicts`) [F], code d'erreur **non documenté** [R] | non documentée [NV] | **Oui — `POST /v2/slots/reservations`, 5 min par défaut** [F] |
| **Calendly** | Oui depuis la *Scheduling API* (**plan payant**) [F] | non documenté ; **pas de 409** sur `/invitees` [F] | non documentée [NV] | Non — seulement `max_event_count` sur lien à usage unique [F] |
| **Cronofy** | Oui (`Upsert Event`) | **Non** documenté [F] | **Oui** — `calendar_id` + `event_id` [F] | Non ; seulement `buffer` [F] |
| **Nylas** | Oui | **Non** documenté [F] | non documentée [NV] | non documenté [NV] |

**Le seul mécanisme du marché qui ferme réellement l'intervalle est le *hold* / *slot reservation*
de Cal.com** — et il ne fonctionne que parce que Cal.com est **lui-même la source de vérité** du
planning. Dès qu'on écrit directement dans Google/Microsoft/CalDAV, ce mécanisme n'existe plus,
parce qu'il n'y a **rien à réserver**.

> **Conséquence directe pour notre produit** : la garantie de non-superposition n'est pas une
> propriété des agendas. C'est une propriété de **celui qui détient la source de vérité**.
> Notre verrou en base + contrainte SQL **est** la garantie ; l'agenda tiers n'en est que le
> **reflet**, publié en aval, en *best effort*.

---

## 5. MCP (Model Context Protocol) comme contrat de connecteur

Source : spécification officielle, révision **2026-07-28** (schéma de référence
`schema/2026-07-28/schema.ts`), https://modelcontextprotocol.io/specification/latest
et https://modelcontextprotocol.io/specification/2026-07-28/server/tools — consultées le **2026-09-14**.

### 5.1 Ce que MCP apporte réellement par rapport à du REST [F]

1. **Typage machine, dans les deux sens.** `inputSchema` est **obligatoire** et **MUST** être un
   objet JSON Schema valide (par défaut 2020-12). `outputSchema` est optionnel mais, dès qu'il est
   présent : « *Servers **MUST** provide structured results that conform to this schema.
   Clients **SHOULD** validate structured results against this schema.* » Les résultats structurés
   arrivent dans `structuredContent`.
   → C'est le vrai gain : **un éditeur tiers décrit son outil « prendre_rdv » une fois, et notre
   agent sait l'appeler sans intégration écrite à la main.** Une API REST ordinaire a bien OpenAPI,
   mais rien n'oblige l'éditeur à le publier ni à le tenir à jour ; en MCP, le schéma **est** le
   protocole.
2. **Découverte dynamique et versionnable.** `tools/list` est paginé, cacheable (`ttlMs`,
   `cacheScope`), et l'ensemble d'outils **MUST NOT** varier par connexion mais **MAY** varier selon
   l'autorisation présentée (« *returning only the tools the caller's granted scopes permit — since
   credentials are per-request input, not connection state* »). Notifications
   `notifications/tools/list_changed` quand le catalogue bouge.
3. **Versionnage explicite** de la révision du protocole (`io.modelcontextprotocol/protocolVersion`
   dans `_meta`, **obligatoire** sur chaque requête) et négociation de capacités par requête.
4. **Erreurs à deux étages**, distinction très utile pour un agent vocal :
   - *Protocol Errors* (JSON-RPC, ex. `-32602` outil inconnu) — « *models are less likely to be able
     to fix* » ;
   - *Tool Execution Errors* (`isError: true` dans le résultat) — « *contain actionable feedback that
     language models can use to self-correct and retry with adjusted parameters* », avec les erreurs
     métier explicitement dans cette catégorie.
   **C'est exactement le canal par lequel un éditeur devrait nous dire « créneau pris, en voici
   trois autres ».** Aucune API REST d'agenda grand public ne le fait aujourd'hui.
5. **Extension *Tasks*** (opt-in) : « *Asynchronous execution of long-running operations, with
   polling, mid-flight input, and durable handles* ». Pertinent pour une écriture qui dépasse le
   budget de latence d'un appel.

### 5.2 Ce que MCP n'apporte **pas**, et il le dit lui-même [F]

La section *Stateful Tools* est sans ambiguïté :

> « *The protocol has no concept of a state handle; from the wire's perspective a handle is an
> ordinary string in a tool result and an ordinary argument to subsequent tool calls.* »
> « *MCP has no protocol-level session, so a server cannot rely on implicit per-connection state to
> relate one tool call to the next. Servers that need to maintain state across calls — a shopping
> cart, an open browser context, **a database transaction** — should do so by returning an explicit
> handle from a creation tool and accepting that handle as an argument on subsequent calls.* »

> **Résultat : MCP n'offre ni transaction, ni verrou, ni idempotence au niveau du protocole.**
> Il offre la *place* où mettre un jeton de réservation — le « handle » — mais c'est au serveur
> de l'implémenter. MCP ne change **rien** à la question centrale de ce rapport ; il change la
> **facilité d'intégration**, pas la **garantie**.

**[F]** La spec donne d'ailleurs les bonnes propriétés d'un tel handle, qui sont exactement celles
d'un *hold* de créneau : autorisation revalidée à chaque appel, opacité, **durée de vie bornée
annoncée dans la description de l'outil** (« *baskets expire after 24 hours of inactivity* »), et
erreur explicite à l'expiration.

**[R] Sécurité** : « *clients **MUST** consider tool annotations to be untrusted unless they come
from trusted servers* » et « *Tools represent arbitrary code execution* ». Un connecteur MCP d'un
éditeur tiers qui écrit dans l'agenda d'un salon est une surface d'attaque à traiter comme telle.

### 5.3 Adoption en 2026 — ce qu'on peut affirmer et ce qu'on ne peut pas

**[F]** Le protocole est en révisions datées et publiques, la dernière étant **2026-07-28**, avec
un écosystème d'extensions formalisées (Tasks, MCP Apps, Skills over MCP) et des groupes de travail.
C'est le signe d'une spécification mûre et gouvernée, plus d'un prototype.
**[NV]** Nous n'avons **pas** de chiffre d'adoption sourcé (nombre de serveurs, d'éditeurs métier
français exposant un MCP de prise de rendez-vous). **Aucun éditeur vertical de la §7 n'est connu de
nous pour exposer un serveur MCP public.** Ne rien affirmer là-dessus.

---

## 6. Les passerelles (Zapier, Make, n8n) : utilisables pendant un appel ?

Le budget est connu : dans une conversation téléphonique, une réponse au-delà d'**environ une
seconde** produit un silence que l'appelant interprète comme une panne. La question n'est donc pas
« est-ce que ça marche », mais « est-ce que ça répond à temps ».

### 6.1 Zapier — **non**, en mode déclencheur [F]

Temps de rafraîchissement (« polling time ») publié sur la grille tarifaire officielle :

| Plan | Intervalle de scrutation |
|---|---|
| Free | **15 min** |
| Professional | **2 min** |
| Team | **1 min** |
| Enterprise | **1 min** |

→ https://zapier.com/pricing — consulté le **2026-09-14**.

**[F]** Zapier précise par ailleurs : « *The polling interval is the frequency that Zapier will check
your trigger apps for new data. The available intervals depend on your Zapier pricing plan and the
app your trigger uses.* » et « *Triggers labeled Instant will always trigger Zap workflows
immediately (regardless of pricing plan).* »
→ https://help.zapier.com/hc/en-us/articles/8496181725453 — consulté le **2026-09-14**.

> **Verdict : une minute au mieux, quinze au pire. C'est deux à trente fois le budget d'un tour de
> parole.** Un Zap en scrutation est **inutilisable en synchrone** pendant un appel. Les
> déclencheurs *Instant* (webhook) échappent au polling, mais restent une chaîne d'exécution
> hébergée dont **aucune latence de bout en bout n'est contractuelle**. **[R]**

### 6.2 Make — **non** en scénario planifié, **peut-être** en webhook [F]

L'intervalle par défaut est de **15 minutes** ; « *the minimum length of the interval depends on your
plan* » — le minimum n'est pas chiffré universellement dans la documentation. Options : intervalles
réguliers, une fois par jour, jours ouvrés, hebdomadaire, mensuel, dates spécifiées, à la demande.
L'option « *immediately* » « *is available only for some triggers* », et le mode « *as data
arrives* » existe pour les déclencheurs webhook, avec une limite de débit par défaut de
**100 exécutions par minute**.
→ https://help.make.com/schedule-a-scenario — consulté le **2026-09-14** (après redirection 301
depuis `www.make.com/en/help/scenarios/scheduling-a-scenario`).
**[R]** Aucune garantie de latence publiée. Le plafond de 100/min est un plafond de **débit**, pas
un engagement de **délai**.

### 6.3 n8n — le seul des trois qui peut techniquement répondre en synchrone [F]

Le nœud Webhook documente trois modes de réponse :
- *Immediately* — « *The Webhook node returns the response code and the message **Workflow got
  started***. »
- *When Last Node Finishes* — « *returns the response code and the data output from the last node
  executed in the workflow.* »
- *Using 'Respond to Webhook' Node* — la réponse est définie par un nœud dédié.
Plus un mode *Streaming response* (« *Enables real-time data streaming back to the user* »).
Aucune limite de délai documentée ; la seule limite chiffrée est la taille : « *The webhook maximum
payload size is 16MB.* »
→ https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/ — consulté le **2026-09-14**.

**Ce qui le distingue** : n8n est **auto-hébergeable**. On maîtrise donc la machine, la co-localisation
avec notre pipeline vocal, et l'absence de file d'attente mutualisée. C'est la seule des trois
passerelles dont la latence puisse être **mesurée et tenue** par nous.
**[R]** Mais « pas de timeout documenté » n'est pas « rapide » : le mode *When Last Node Finishes*
fait attendre l'appelant pendant **tout** le workflow, y compris les appels sortants vers l'API
d'agenda. Un workflow n8n dans la boucle d'un appel doit être traité comme du code de production
(budget de latence explicite, timeout dur, repli).

### 6.4 Conclusion sur les passerelles

| | Dans la boucle de l'appel (< 1 s) | En différé (après l'appel) |
|---|---|---|
| **Zapier** | **Non** [F] | Oui |
| **Make** | **Non** en planifié [F] ; webhook **[NV]**, latence non publiée | Oui |
| **n8n auto-hébergé** | **Possible** [F], sous notre responsabilité et notre mesure | Oui |

**Règle d'architecture qui en découle** : une passerelle est un **organe de publication**, jamais un
organe de **décision**. La décision « ce créneau est à vous » doit être prise par notre base pendant
l'appel ; la propagation vers l'agenda du professionnel peut, elle, passer par une passerelle, en
asynchrone, avec réconciliation. C'est d'ailleurs cohérent avec la conclusion du §4.5.

---

## 7. Les logiciels métier verticaux : y a-t-il une porte d'entrée ?

Méthode : recherche de portail développeur public, de documentation d'API, ou d'une page partenaire
décrivant un accès programmatique en écriture. Toutes consultations le **2026-09-14**.

### 7.1 Phorest — **oui**, sur demande [F]

Portail développeur public : https://developer.phorest.com/
- API publique existante et « live » : les écritures se répercutent immédiatement dans Phorest.
- Capacité d'écriture confirmée : « *Whether it's retrieving client information, **booking
  appointments**, or managing services, the changes happen instantly.* »
- Conditions : demande d'accès via le support, **depuis une adresse e-mail rattachée à l'entreprise
  cliente dans Phorest** ; pour construire une intégration, contact `developer@phorest.com`.
- **Aucun tarif d'accès n'est indiqué** dans la documentation.
- Des intégrations tierces vérifiées existent déjà (JoinMya, Vish, LoopHR cités).

> **C'est le meilleur cas du panel : API documentée, écriture de rendez-vous, accès conditionné au
> consentement du salon.** Le point important : l'autorisation est **donnée par le salon**, pas par
> nous — ce qui est exactement le modèle qu'il nous faut (le professionnel active son connecteur).
> **[R]** Le comportement en cas de créneau déjà pris n'a pas été vérifié à la source. **[NV]**

### 7.2 Booksy — pas de portail développeur accessible [F]

`https://developers.booksy.com/` **redirige (302) vers `https://booksy.com/`** : il n'y a pas de
portail développeur public à cette adresse.
**[H]** Un programme partenaire existe probablement en marque blanche / API privée, mais rien n'est
sourçable publiquement. **[NV]**

### 7.3 Fresha — rien de public [F]

- `developers.fresha.com` : **le domaine n'existe pas** (`ENOTFOUND`).
- La page *Integrations* et le centre d'aide (recherche « API ») ne renvoient **aucun** article sur
  un accès API ou un portail développeur.
→ https://www.fresha.com/for-business/integrations et https://www.fresha.com/help-center?query=API

### 7.4 Treatwell — rien de public [F]

- `partner.treatwell.com` : **domaine inexistant** (`ENOTFOUND`).
- `treatwell.co.uk/partners/connect/` : **404**.
- `treatwell.co.uk/partners/` : page commerciale (gestion de RDV, paiements, acquisition de
  clients), **aucune** mention d'API, d'intégration Connect ou d'accès développeur.

### 7.5 Planity — rien de public [F]

- `planity.com/pro` : **404**.
- `planity.com` : contenu entièrement orienté logiciel de gestion et réservation via l'interface
  Planity. **Aucune** mention d'API, de portail développeur, ni de création de rendez-vous par un
  système externe.

### 7.6 Zenchef — intégrations oui, API publique non [F]

La page officielle FR parle d'écosystème et d'intégrations — « *Connectez Zenchef aux outils que vous
utilisez déjà* », avec des caisses nommées (« *Lightspeed, Trivec and others* ») — mais **aucune**
documentation d'API, **aucun** portail développeur.
→ https://www.zenchef.com/fr/
**[H]** Les intégrations existantes sont donc des **partenariats négociés au cas par cas**, pas une
API ouverte.

### 7.7 Doctolib — rien de public [F]

`doctolib.fr/partenaires` ne mentionne ni API publique, ni programme partenaire d'intégration
technique ; seule est présentée la suite « Doctolib Pro », logiciel pour les praticiens.
**[R]** Contexte à ne pas oublier : données de santé. Toute écriture dans un agenda de praticien en
France relève de l'**hébergement de données de santé (HDS)** et du secret médical, ce qui rend
l'ouverture d'une API tierce d'écriture structurellement improbable. **[H]**

### 7.8 Ce que cela veut dire

**Sur sept éditeurs verticaux examinés, un seul (Phorest) publie une documentation d'API
permettant à un tiers d'écrire un rendez-vous.** Les six autres n'exposent, publiquement, **aucune
porte d'entrée programmatique**.

> **Conclusion opérationnelle : on ne peut pas bâtir un produit sur l'hypothèse « l'agenda métier du
> client a une API ». Dans la grande majorité des cas, il n'en a pas.**
> Les chemins restants, par ordre de robustesse décroissante :
> 1. le professionnel **synchronise déjà** son logiciel métier vers Google/Outlook/CalDAV
>    (très courant) → on écrit dans l'agenda synchronisé, en acceptant ses garanties, c'est-à-dire
>    aucune (§1-3) ;
> 2. on devient **nous-mêmes la source de vérité** du planning et le logiciel métier lit chez nous ;
> 3. partenariat négocié au cas par cas (le modèle Zenchef, et probablement Booksy) ;
> 4. **[R]** automatisation d'interface (navigateur piloté) — fragile, souvent contraire aux CGU,
>    à ne pas promettre.

---

# 8. Hiérarchie des adaptateurs — et ce que l'agent peut dire sans mentir

Le principe qui structure tout ce qui suit : **la garantie n'est pas une propriété du connecteur,
c'est une propriété de qui détient la source de vérité.** Chaque niveau descend d'un cran dans la
force de ce que l'agent a le droit de promettre. La phrase prononcée doit descendre avec lui.

---

## Niveau 0 — Source de vérité chez nous (verrou en base + contrainte SQL d'exclusion)

**Mécanisme** : la réservation est écrite dans **notre** base, sous transaction, avec une contrainte
d'exclusion sur l'intervalle. Deux appels concurrents sur le même créneau : le second **échoue**, de
manière déterministe, avant la fin de la phrase.

**Ce qui est garanti** : la non-superposition, réellement. C'est le seul niveau du dossier où le
mot « garantie » est exact.

**Ce que l'agent peut dire** :
> « C'est noté, votre rendez-vous est réservé mardi à 14 h. »

**Ce qu'il doit ajouter si l'agenda du professionnel est alimenté par ailleurs** : rien pendant
l'appel — mais notre système doit réconcilier, et prévenir en cas de collision détectée après coup.

---

## Niveau 1 — Éditeur qui expose une écriture avec contrôle de conflit côté serveur
### (Cal.com avec `POST /v2/slots/reservations` ; Phorest ; tout éditeur qui refuse un créneau pris)

**Mécanisme** : on pose un **hold** avant de proposer le créneau à voix haute (Cal.com : 5 min par
défaut, `reservationDuration` réglable en authentifié), puis on confirme. Ou bien l'éditeur rejette
explicitement l'écriture conflictuelle.

**Ce qui est garanti** : la non-superposition **à l'intérieur du périmètre de cet éditeur**. Si le
professionnel a aussi un agenda Google que l'éditeur ne voit pas, la garantie s'arrête à la
frontière de l'éditeur.

**[R]** Chez Cal.com, le **code d'erreur du conflit n'est pas documenté** ; chez Phorest, le
comportement n'est pas vérifié. Il faut donc, en intégration, **provoquer le conflit une fois** et
constater la réponse réelle avant de s'appuyer dessus.

**Ce que l'agent peut dire** :
> « C'est réservé, mardi à 14 h. Vous recevrez la confirmation. »

---

## Niveau 2 — Écriture directe dans Google Calendar / Microsoft Graph / CalDAV

**Mécanisme réel** : lire les disponibilités (photographie), écrire l'événement. **Rien** n'empêche
la superposition (§1, §2, §3). On peut au mieux :
- rendre l'écriture **idempotente** : `transactionId` sur Graph [F], `event_id` sur Cronofy [F],
  `UID` + `If-None-Match: *` en CalDAV [F], `id` fourni par le client sur Google **[H]** ;
- **relire juste après l'écriture** pour détecter un chevauchement — détection *a posteriori*, pas
  prévention ;
- réduire l'intervalle : n'énoncer un créneau qu'après l'avoir verrouillé chez nous (retour au
  niveau 0, l'agenda tiers devenant un simple miroir).

**Ce qui est garanti** : **rien, au niveau de l'agenda**. L'événement sera créé ; il pourra se
superposer à un autre.

**Ce que l'agent peut dire** :
> « C'est enregistré pour mardi 14 h. »

**Ce qu'il ne doit jamais dire à ce niveau** : « le créneau est bloqué », « personne d'autre ne peut
le prendre », « c'est garanti ». Aucune de ces phrases n'est vraie.

**[R]** Si le professionnel prend aussi des rendez-vous au comptoir ou par un autre canal, le
chevauchement est **probable**, pas théorique. Ce niveau exige un mécanisme de détection et une
procédure humaine de rattrapage — et il faut le dire au professionnel à la vente, pas après.

---

## Niveau 3 — Passerelle (Zapier / Make / n8n hébergé ailleurs) dans la boucle de l'appel

**Mécanisme** : l'agent délègue l'écriture à une automatisation. Latences documentées : Zapier
**15 / 2 / 1 min** selon le plan [F] ; Make **15 min par défaut**, minimum dépendant du plan [F] ;
n8n auto-hébergé, synchrone possible mais non garanti [F].

**Ce qui est garanti** : ni la non-superposition, **ni même que l'écriture ait eu lieu avant la fin
de l'appel**.

**Ce que l'agent peut dire** :
> « Je transmets votre demande pour mardi 14 h. Vous recevrez une confirmation par SMS. »

**Ce qu'il ne doit pas dire** : « c'est fait », « c'est réservé », « c'est dans l'agenda ».
Au moment où il parle, ce n'est probablement pas encore vrai.

**Règle** : une passerelle publie, elle ne décide pas. Si elle est dans la boucle, l'agent parle
au futur.

---

## Niveau 4 — Aucune écriture possible (Planity, Treatwell, Fresha, Booksy, Zenchef, Doctolib)

**Mécanisme** : pas de porte d'entrée programmatique publique (§7). On note la demande et on la
transmet — SMS au professionnel, e-mail, fiche dans une console.

**Ce qui est garanti** : la **transmission**. Rien d'autre.

**Ce que l'agent peut dire** :
> « J'ai bien noté votre demande pour mardi vers 14 h. Le salon vous confirme le créneau
> par SMS. »

**Ce qu'il ne doit pas dire** : toute forme de « c'est réservé ». Il n'y a pas de rendez-vous ;
il y a une demande.

---

## Le tableau que l'on peut afficher en face d'un client

| Niveau | Garantie de non-superposition | Formulation autorisée à l'appelant | Formulation interdite |
|---|---|---|---|
| **0 — notre base** | **Oui, réelle** (verrou + contrainte) | « C'est réservé. » | — |
| **1 — hold éditeur** | Oui, **dans le périmètre de l'éditeur** | « C'est réservé. » | « Garanti sur tous vos agendas. » |
| **2 — Google / Graph / CalDAV** | **Non** | « C'est enregistré. » | « C'est bloqué / garanti / réservé pour vous seul. » |
| **3 — passerelle** | Non, et écriture non encore effectuée | « Je transmets, vous recevrez une confirmation. » | « C'est fait. » |
| **4 — pas d'API** | Non | « J'ai noté votre demande, le salon confirme. » | « Vous avez rendez-vous. » |

---

## Les trois décisions que ce rapport impose

1. **Ne jamais laisser l'agenda tiers être la source de vérité.** Aucun des trois protocoles
   universels n'offre d'objet « créneau » à verrouiller (§3, bilan intermédiaire). Notre base reste
   l'arbitre ; l'agenda tiers est un **miroir publié**, et doit être présenté comme tel au
   professionnel.
2. **Faire descendre la phrase avec le niveau.** La formulation prononcée par l'agent est une
   donnée de configuration du connecteur, au même titre que l'URL et le jeton. Un connecteur de
   niveau 2 ne doit pas pouvoir émettre la phrase du niveau 0 — à garantir dans le code, pas dans
   le prompt.
3. **Rendre toute écriture idempotente, systématiquement.** `transactionId` (Graph),
   `event_id` (Cronofy), `UID` + `If-None-Match: *` (CalDAV), `id` client (Google, **[H]** à
   vérifier). C'est gratuit, c'est documenté, et cela supprime le mode de défaillance le plus
   fréquent d'une écriture pendant un appel : le rejeu après timeout.

---

## Annexe — inventaire des sources (toutes consultées le 2026-09-14)

| # | Source | Ce qu'elle établit |
|---|---|---|
| 1 | https://developers.google.com/workspace/calendar/api/v3/reference/events/insert | Aucun paramètre de conflit, d'idempotence ou de `requestId` |
| 2 | https://developers.google.com/workspace/calendar/api/v3/reference/events/update | « *…using etags to ensure atomicity* » ; rien d'autre |
| 3 | https://developers.google.com/workspace/calendar/api/guides/performance | ETag mentionné en exemple générique seulement |
| 4 | https://learn.microsoft.com/en-us/graph/api/user-post-events?view=graph-rest-1.0 | Aucun contrôle de conflit ; `transactionId` en exemple |
| 5 | https://learn.microsoft.com/en-us/graph/api/resources/event?view=graph-rest-1.0 | Définition de `transactionId` et `changeKey` ; pas de propriété de conflit |
| 6 | https://learn.microsoft.com/en-us/graph/api/event-update?view=graph-rest-1.0 | En-têtes : `Authorization` seul ; `ErrorOccurrenceCrossingBoundary` |
| 7 | https://learn.microsoft.com/en-us/graph/api/calendar-getschedule?view=graph-rest-1.0 | free/busy = photographie ; limite 1000 entrées (erreur 5006) |
| 8 | https://www.rfc-editor.org/rfc/rfc4791.txt | ETags MUST ; `If-None-Match: *` ; `no-uid-conflict` ; §7.10 « Preconditions: None » ; §8.3 locking |
| 9 | https://cal.com/docs/api-reference/v2/slots/reserve-a-slot | *Hold* de créneau, 5 min par défaut |
| 10 | https://cal.com/docs/api-reference/v2/bookings/create-a-booking | `allowConflicts` ; code d'erreur de conflit non documenté |
| 11 | https://docs.cronofy.com/developers/api/events/upsert-event/ | Idempotence par `calendar_id` + `event_id` |
| 12 | https://docs.cronofy.com/developers/api/scheduling/availability/ | `buffer` ; rien sur la double réservation |
| 13 | https://developer.nylas.com/docs/v3/scheduler/ | Rien de documenté sur le conflit |
| 14 | https://developer.calendly.com/openapi/calendly-api.yaml | `POST /invitees` (Scheduling API, plan payant) ; **pas de 409** ; `user_busy_times` ≤ 7 j ; `event_type_available_times` ≤ 31 j |
| 15 | https://modelcontextprotocol.io/specification/latest | Révision **2026-07-28** ; extensions Tasks / Apps / Skills |
| 16 | https://modelcontextprotocol.io/specification/2026-07-28/server/tools | `inputSchema` MUST, `outputSchema`, `structuredContent`, erreurs à deux étages, « *no protocol-level session* » |
| 17 | https://zapier.com/pricing | Polling : 15 / 2 / 1 / 1 min |
| 18 | https://help.zapier.com/hc/en-us/articles/8496181725453 | Intervalle dépendant du plan ; déclencheurs *Instant* |
| 19 | https://help.make.com/schedule-a-scenario | 15 min par défaut ; minimum selon le plan ; 100 exécutions/min |
| 20 | https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/ | 3 modes de réponse ; pas de timeout documenté ; 16 Mo |
| 21 | https://developer.phorest.com/ | API publique, écriture de rendez-vous, accès sur demande |
| 22 | https://www.fresha.com/for-business/integrations · /help-center?query=API · `developers.fresha.com` (ENOTFOUND) | Aucune API publique |
| 23 | `https://developers.booksy.com/` (302 → booksy.com) | Pas de portail développeur public |
| 24 | https://www.treatwell.co.uk/partners/ · `/partners/connect/` (404) · `partner.treatwell.com` (ENOTFOUND) | Aucune API publique |
| 25 | https://www.planity.com/ · `/pro` (404) | Aucune API publique |
| 26 | https://www.zenchef.com/fr/ | Intégrations partenaires nommées, pas d'API publique |
| 27 | https://www.doctolib.fr/partenaires | Aucune API ni programme d'intégration technique public |

### Points restés non vérifiés [NV] — à traiter dans une passe ultérieure
- Google : `id` fourni par le client sur `events.insert` comme clé d'idempotence (probable, non
  confirmé à la source).
- Microsoft : durée de rétention de `transactionId` ; `If-Match` réellement honoré sur `PATCH /events`.
- Exchange : refus de conflit sur boîte aux lettres de ressource (`AllowConflicts $false`) et son
  caractère asynchrone.
- RFC 6638 (CalDAV Scheduling) non lue.
- Cal.com : code d'erreur exact en cas de conflit ; idempotence.
- Calendly : code d'erreur exact en cas de créneau pris (probablement `400`).
- Booksy / Zenchef / Treatwell : existence d'un programme partenaire privé.
- MCP : chiffres d'adoption ; existence de serveurs MCP chez les éditeurs verticaux.
