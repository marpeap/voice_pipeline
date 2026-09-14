# A11 — Adaptateurs universels d'agenda : qu'est-ce qui empêche deux rendez-vous de se superposer ?

> État : **septembre 2026** (consultations du 2026-09-14).
> Méthode : sources officielles (docs éditeurs, RFC), WebFetch direct, URL + date de consultation.
> Marquage : **[F]** fait vérifié à la source · **[H]** hypothèse raisonnée · **[R]** risque · **[NV]** non vérifié / source inaccessible.
>
> **Question centrale** : quand notre agent téléphonique écrit un événement dans un agenda tiers,
> qu'est-ce qui, techniquement, empêche deux rendez-vous de se superposer ?
> Chez nous : verrou en base + contrainte SQL. Ailleurs : voir ci-dessous.

_(document en cours de rédaction — complété au fil des consultations)_

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

