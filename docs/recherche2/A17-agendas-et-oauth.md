# A17 — Connecter l'agenda de n'importe quel commerçant : coût et délai réels

**Consulté le 2026-09-14.** [F] · [H] · [R] · [NV].

## 1. Le fait qui découpe la trajectoire commerciale en deux

**[F] Google, verbatim** (`support.google.com/cloud/answer/13463817`) :
> « unverified apps that are accessing **restricted or sensitive** scopes have a **100 new-user cap** restriction »
> « the user cap applies **over the entire lifetime of the project**, and it **cannot be reset or changed** »
> « Failure to get your app verified… will result in your project's 100 new-user cap eventually getting exhausted and **Google sign-in being disabled** »

**[R] Trois conséquences** : le plafond mord **aussi sur les scopes sensibles**, pas seulement les restreints · il est **à vie et non réinitialisable**, donc **chaque test, chaque démo, chaque compte jetable consomme une place définitivement** · à 100 commerçants connectés, **le service s'arrête net**. **50 clients : vivable. 500 : impossible sans vérification.**

⚠️ **La question à 10 minutes qui décide de tout** : la Console affiche-t-elle `calendar` / `calendar.events` en **Sensitive** ou en **Restricted** ? La documentation publique **ne le dit nulle part** [NV] — les deux pages listent les 17 scopes **sans label**, et renvoient la classification à la Console. **[R]** Déduction (à confirmer, pas à croire) : la FAQ ne cite comme exemple de *restricted* que `https://mail.google.com/`, donc Calendar en écriture est **très probablement *sensitive*** → vérification renforcée **oui**, audit CASA **non**.

**[F] Délais annoncés** : brand verification **2–3 jours ouvrés** · **sensitive scope 10 jours ouvrés** · **restricted 6 semaines**. Avec l'avertissement « these estimates are not guaranteed ». **[R]** En réalité **3 à 6 semaines** : il faut d'abord une page d'accueil réelle sur un domaine vérifié dans Search Console, une politique de confidentialité **sur le même domaine**, et une **vidéo de démonstration** montrant l'écran de consentement avec les scopes exacts.

**[R] Risque propre à un agent vocal** : Google exige que les données servent « **user-facing features that are prominent** ». Or l'appelant ne voit aucune interface. Il faut donc que **le commerçant** dispose d'un tableau de bord où les rendez-vous pris sont visiblement exploités — sans quoi le refus est prévisible.

**[F] CASA** (si jamais *restricted*) : « **Google does not charge the developer any fees for security assessment** », mais le prix est « agreed on between the developer and the assessor ». **[NV] Aucun montant n'est publié**, et les pages de l'App Defense Alliance détaillant les paliers renvoient **404**. Renouvellement **annuel**.

## 2. Microsoft : pas de plafond, mais un prérequis administratif

**[F]** « **Microsoft doesn't charge developers for publisher verification. No license is required** », et la vérification prend « **minutes** » — **une fois** l'organisation inscrite et vérifiée au programme partenaire (Partner One ID, tenant associé, domaine d'éditeur distinct de `*.onmicrosoft.com`, MFA). **[R] Le vrai délai est le KYC société, pas la revue.**
**[F] Le piège** : depuis novembre 2020, avec le *risk-based step-up consent*, « **users can't consent to most newly registered multitenant apps that aren't publisher verified** ». Sans badge : avertissement, voire consentement **bloqué**.
**[R]** Nuance pour notre cible : une TPE utilise souvent un compte Outlook **personnel**, pas un tenant d'entreprise — les politiques de consentement d'administrateur ne s'y appliquent pas.

## 3. iCloud : pas d'API

**[NV] Apple ne publie aucune API iCloud Calendar ni documentation CalDAV pour tiers.** En pratique : un endpoint CalDAV non documenté, authentifié par un **mot de passe d'application que le commerçant doit générer lui-même**. **[R]** Pas de contrat, pas de SLA, une expérience de connexion hostile, rupture possible sans préavis. **Le pire des trois pour une vente en libre-service.**

## 4. Quotas, et ce qu'ils imposent au dialogue

**[F] Google Calendar** : 10 000 req/min/projet · **600 req/min/utilisateur** · 1 000 000/jour **non augmentable** · dépassement en 403/429 `usageLimits` · backoff exponentiel tronqué imposé.
**[R]** Le plafond qui mord n'est pas celui du projet mais les **600/min par commerçant** : un agent qui réinterroge les disponibilités à chaque tour de parole doit **mettre le free/busy en cache** pendant l'appel.

**[F] Notifications push** : certificat SSL valide obligatoire · « **there's no automatic way to renew a notification channel** » → un **cron de renouvellement par commerçant, à maintenir à vie** · et surtout « **Notifications are not 100 % reliable. Expect a small percentage of messages to get dropped.** »
**[R]** Donc **le push seul ne suffit pas** : réconciliation périodique par `syncToken` obligatoire. Un événement manqué chez un vrai commerçant, c'est un double-booking.

**[F] Microsoft Graph** : 429 avec `Retry-After` à respecter · le **batching ne protège pas** (« Requests in a batch are evaluated individually ») et **les SDK ne rejouent pas** les requêtes throttlées d'un lot · `delta query` et notifications recommandées contre le polling. Limites chiffrées Outlook : **[NV]**, section non rendue.

## 5. Les intermédiaires

| | Prix | Verdict |
|---|---|---|
| **Nylas** | base **15–49 $/mois** + **1,35–1,70 $ par agenda connecté** | **Le seul à publier un prix à l'unité** — donc le seul budgétable. Absorbe Google + Outlook + iCloud |
| **Cronofy** | **« from 819 $/month »**, paliers [NV] | **Éliminé à 50 clients** (16 $/client rien qu'en agenda) |
| **Cal.com Platform** | — | ⛔ **Fermé aux nouvelles inscriptions depuis le 15/12/2025** [F]. Reste l'auto-hébergement — facilité par un passage en **licence MIT** (⚠️ [R] à reconfirmer), mais qui **nous remet le problème OAuth sur les bras** : ce serait notre client OAuth à faire vérifier |
| **Calendly** | [NV] | Facturé au siège : obligerait **chaque commerçant** à souscrire. Incompatible avec une vente en autonome |

## 6. Recommandation — et elle inverse l'ordre attendu

**[R] 1. Agenda interne par défaut, aucune connexion.** L'agent écrit dans **notre** base : zéro OAuth, zéro vérification, zéro plafond, et **nous sommes la source de vérité**, donc l'anti-double-booking est à nous. À vérifier d'abord : combien de TPE visées ont réellement un agenda numérique à synchroniser ?
**[R] 2. Export iCal en lecture seule** — le commerçant voit ses rendez-vous dans son propre agenda. **Google, Outlook et Apple l'acceptent tous nativement, par simple abonnement à une URL, sans OAuth, sans vérification, sans coût.** **Meilleur rapport valeur/effort du dossier**, et la seule chose qui marche avec iCloud.
**[R] 3. Connexion Google bidirectionnelle en option**, plus tard, **sur un projet GCP dédié dont les 100 places n'ont pas été brûlées en développement** (projet de test séparé, impérativement).
**[R] 4. Nylas en soupape** si « lisez mon agenda existant » devient bloquant commercialement : **83,50 $/mois à 50 clients**, **448 $/mois à 500** (hypothèse : 60 % de clients synchronisés) — marginal face au revenu d'un agent vocal, et sans plafond.

**[R] À lancer en parallèle dès maintenant** : la vérification Google en scope sensible. Elle ne coûte rien à démarrer et prend des semaines — l'attendre pour la commencer est la seule vraie perte.
