# A3 — SMS transactionnel en France (état septembre 2026)

**Objet** : le SMS comme **mécanisme de vérification de bout en bout** de l'agent vocal. Il prouve que le numéro capté est joignable, que le rendez-vous est écrit en base, et il laisse une trace au client. S'il ne part pas, le rendez-vous est marqué « à vérifier ».

**Date de rédaction** : 2026-09-14. Toutes les consultations : **2026-09-13 / 2026-09-14**.

**Méthode et son trou** : le budget **WebSearch de la session était épuisé (200/200) avant le premier appel**. Tout ce qui suit vient de **WebFetch et de `curl` sur des URL officielles construites à la main**. Conséquence assumée : on ne cite ici que des pages **réellement récupérées**, mais on n'a pas pu *découvrir* de sources — d'où plusieurs `[NV]` sur des fournisseurs dont les grilles sont rendues en JavaScript (Brevo, Vonage, Spot-Hit API) ou dont les domaines refusent la connexion (Sinch). Un des trois sous-agents est mort en cours de route (ECONNRESET) ; son lot a été repris à la main, en partie seulement.

**Marquage** : **[F]** fait sourcé (URL + date) · **[H]** hypothèse · **[R]** recommandation · **[NV]** non vérifié / source inaccessible.

---

## 0. Ce qu'il faut retenir avant de lire le reste

1. **[F] La passerelle SIM maison est illicite.** Un envoi automatisé depuis une carte SIM grand public présente un **06/07** comme identifiant d'émetteur, ce que la décision Arcep n° 2018-0881 modifiée interdit **sans aucune exception** pour les numéros mobiles, depuis le 1er août 2019. Ce n'est pas une zone grise : les trois exceptions du texte sont **expressément écartées** pour les mobiles, et l'Arcep recommande aux opérateurs d'**interrompre l'acheminement**. → §3.
2. **[F] Même sans cette interdiction, la passerelle SIM ne peut pas faire le travail demandé** : elle ne produit **aucun accusé de réception opérateur**. Le `envoye_le` de Crenolo signifie « le modem a accepté », jamais « l'opérateur a remis ». Un produit dont le SMS *est* la preuve ne peut pas s'appuyer sur une preuve que le canal ne fournit pas. → §7.
3. **[F] Le SMS transactionnel est confortable juridiquement** : pas de consentement préalable (base légale = exécution du contrat), **pas d'obligation de mention STOP**, **aucune restriction horaire**. La réforme du démarchage du 11/08/2026 **ne concerne pas le SMS** — elle vise les appels vocaux. → §2.
4. **[F] Le coût réel est faible** : ~**17 à 18 € HT par mois** pour un salon à 150 RDV avec confirmation + rappel. Ce n'est pas le prix du SMS qui décide l'architecture. → §6.
5. **[R] Recommandation** : **abandonner la passerelle SIM, garder toute la couche logicielle** (file `sms_sortants`, liste `sms_stop`, normalisateur E.164, texte GSM-7) et brancher un fournisseur A2P français derrière l'interface interne existante. → §7.

---

## 1. Fournisseurs

### 1.1 Prix par SMS vers la France — uniquement ce qui est sourcé

| Fournisseur | Prix unitaire France | Palier | Devise | Source | Marque |
|---|---|---|---|---|---|
| **Octopush** abo « Basique » | **0,045 €** + 9 €/mois | 1 000–9 999 /mois | € HT | `octopush.com/tarifs-sms-france/` | [F] |
| **OVHcloud SMS Pro** | **0,054 €** | pack 10 000 | € HT | `ovhcloud.com/fr/sms/` | [F] |
| OVHcloud SMS Pro | **0,058 €** | pack 1 000 | € HT | idem | [F] |
| OVHcloud SMS Pro | 0,060 € | pack 100 | € HT | idem | [F] |
| **Spot-Hit** premium | **0,059 €** | **100 → 10 000** | € HT | `spot-hit.fr/tarifs` (curl) | [F] |
| Spot-Hit premium | 0,054 € / 0,049 € | 10 k–100 k / >100 k | € HT | idem | [F] |
| **Octopush** prépayé | **0,061 €** | pack 1 000 | € HT | `octopush.com/tarifs-sms-france/` | [F] |
| Octopush prépayé | 0,058 / 0,056 / 0,055 € | 2 500 / 5 000 / 10 000 | € HT | idem | [F] |
| **SMSFactor** prépayé | **0,066 €** | pack 1 000 | € HT | `smsfactor.com/tarifs/` | [F] |
| SMSFactor | 0,062 / 0,060 / 0,056 € | 2 500 / 5 000 / 10 000 | € HT | idem | [F] |
| **Twilio** | **0,0798 $** / **segment** | pas de palier public | **USD** | `twilio.com/en-us/sms/pricing/fr` | [F] |
| Twilio entrant | 0,0075 $ / segment | — | USD | idem | [F] |
| Telnyx | page tarifs **US uniquement** | — | — | `telnyx.com/pricing/messaging` | [NV] |
| Vonage | grille injectée en JS | — | — | `vonage.fr/communications-apis/sms/pricing/` | [NV] |
| Brevo | grille injectée en JS | — | — | `brevo.com/fr/tarifs/` | [NV] |
| LinkMobility FR | **aucun tarif public** — devis | — | — | `linkmobility.fr` | [F] (absence constatée) |
| Sinch | HTTP 000, connexion impossible | — | — | `sinch.com/pricing/` | [NV] |

Toutes consultations **2026-09-13**.

**Pièges de lecture** :
- [F] **Twilio est le seul facturé en USD**, et sa page ajoute : « *Prices may change from time to time without notice and **additional carrier fees may apply*** » → le prix affiché n'est pas le prix final.
- [F] **Spot-Hit** met « à partir de 0,039 € HT/SMS » en tête de page : c'est le **palier au million**, pas un prix d'entrée. Le prix réel d'un salon est **0,059 €**.
- [F] **Vonage** : « *Les tarifs sont mis à jour régulièrement. Consultez votre tableau de bord client au moment de l'achat* » → le prix n'est connu **qu'après ouverture de compte**. Rédhibitoire pour un budget prévisionnel [R].
- ⚠️ **Incohérence Octopush non levée** : `octopush.com/tarifs-sms/` affirme l'existence de « versions low cost et premium » pour la France, alors que la grille `/tarifs-sms-france/` n'en distingue aucune. [H] forte : les prix ci-dessus sont ceux du **premium** (seule route acceptable en transactionnel). **À faire confirmer par écrit** [R].

### 1.2 Frais fixes et conditions

| Fournisseur | Abonnement | Frais numéro | Sender ID alpha | Minimum d'achat | Expiration des crédits |
|---|---|---|---|---|---|
| OVHcloud | aucun (packs prépayés) [F] | [NV] | [NV] | **100 SMS** [F] | [NV] |
| Octopush | 0 € prépayé ; 9 / 39 / 159 €/mois en abo [F] | [NV] | [NV] | **1 000 SMS** [F] | [NV] |
| SMSFactor | 0 € prépayé ; abo dès 3 000 SMS/mois, caution convertible, sans engagement [F] | [NV] | API « Senders » existe [F] ; coût [NV] | **1 000 SMS** [F] | **crédits valables 1 an** [F] |
| Spot-Hit | « sans engagement ni abonnement » [F] | [NV] | [NV] | **100 SMS** [F] | [NV] |
| Twilio | aucun | numéro international **dès 1,15 $/mois** [F] | **gratuit** [F] | aucun | s.o. (post-payé) |

[F] **SMSFactor est le seul à documenter une expiration** (« crédits valables 1 an »). Les autres n'en disent rien — ce qui ne veut pas dire qu'il n'y en a pas. **[NV] à lever par écrit avant achat** [R].

[F] **OVHcloud offre 20 crédits SMS à l'inscription** — de quoi tester la chaîne complète sans engagement.

### 1.3 API, accusés de réception, réception entrante

**Twilio** — le mieux documenté (`twilio.com/docs/messaging/api/message-resource`, consulté 2026-09-14) :
- [F] REST. Envoi : `POST /2010-04-01/Accounts/{AccountSid}/Messages.json`. Lecture : `GET …/Messages/{Sid}.json`.
- [F] **SDK Python officiel** (`twilio.rest`, `twilio.com/docs/python/install`).
- [F] **DLR par webhook** : paramètre `StatusCallback`. Statuts : `queued`, `scheduled`, `accepted`, `sending`, `sent`, `delivered`, `undelivered`, `failed`, `canceled`.
- [F] **Inbound : « Fully supported »** (`twilio.com/en-us/guidelines/fr/sms`).
- [H] Auth : HTTP Basic (AccountSid / AuthToken) — non extrait verbatim.

**SMSFactor** (`dev.smsfactor.com`, consulté 2026-09-13/14) :
- [F] Base URL `https://api.smsfactor.com`, auth `Authorization: Bearer <JWT>`, XML par défaut, **JSON via `Accept: application/json`**.
- [F] Exemples de code en **Python** (parmi 9 langages). Ce sont des **exemples**, pas un SDK packagé.
- [F] **Webhooks documentés** : *Delivery reports*, *Replies*, *Stops*, *Clickers*, *Balance Alert*, avec API de gestion (create/retrieve/update/delete).
- [F] API **Senders** (create / retrieve) : l'enregistrement d'un expéditeur est **piloté par API**. Coût et délai **[NV]**.
- [F] **Anti-flood** : filtre sur les SMS vers un même numéro dans une fenêtre d'**1 heure**, seuil non chiffré. → **[R] attention si confirmation et rappel peuvent partir à moins d'une heure d'écart** (cas d'un RDV pris la veille pour le lendemain).
- [F] **Arbitrage marque / réponse** : l'inbound n'est possible qu'avec **expéditeur non personnalisé** (numéro court à 5 chiffres). Avec un nom de marque, pas de réponse. **Nom OU conversation, pas les deux.**

**OVHcloud, Octopush, Spot-Hit** : [NV] sur l'API, les DLR, l'inbound et le débit — `spot-hit.fr/documentation-api` renvoie **HTTP 522**, la doc Octopush n'a pas été atteinte, `api.ovh.com/console/` redirige (301) hors du périmètre suivi. [H] L'API OVHcloud est REST/JSON à triple clé (application key / secret / consumer key) avec un SDK Python `ovh` — **à vérifier avant engagement**.

### 1.4 Débit et latence — le grand trou

- [F] **Aucun fournisseur ne publie de débit msg/s pour la France, ni de SLA de latence de remise.** Ni Twilio, ni SMSFactor (« *No rate limit information is provided* »), ni les acteurs français.
- [F] Notion générale chez Twilio (`twilio.com/docs/messaging/guides/market-throughput-overview`, consulté 2026-09-14) : « *Throughput is the rate at which you can send messages at a given time. It is measured **per phone number** (also known as a sender), **per second***. » Et : « *Twilio short code numbers have an available throughput of **100 messages per second (MPS)*** ». Avertissement utile : « *purchasing more phone numbers won't necessarily increase the customer's total throughput during congested sending times* ».
- [F] Levier de conception trouvé dans `twilio.com/docs/messaging/guides/scaling-queueing-latency` (2026-09-14) : le **Validity Period** par Messaging Service, pensé pour les messages qui doivent arriver tout de suite (« *This message has to arrive immediately* ») et **expirer plutôt qu'arriver en retard**.
- [R] **À reprendre dans Crenolo** : une confirmation de RDV qui n'est pas partie dans les N minutes ne doit pas partir du tout — elle doit basculer le rendez-vous en « à vérifier ». Une confirmation reçue trois heures après l'appel n'est plus une vérification, c'est une nuisance. La file actuelle n'a **aucune notion de péremption** (§7.2).

---

## 2. Réglementation française du SMS A2P

Sources : décision **Arcep n° 2018-0881 modifiée, version consolidée au 1er janvier 2026** (`arcep.fr/uploads/tx_gsavis/18-0881.pdf`) · **Charte af2m Business Messaging en vigueur au 01/03/2026** (`af2m.org/charte-business-messaging/`) · **CNIL**, fiches du 10 juin 2026 · **Légifrance** (L34-5 CPCE, L223-1 c. conso, loi n° 2025-594). Toutes consultées **2026-09-14**.

> ⚠️ **Note d'accès** : `af2m.fr` **n'est plus** le site de l'Association Française du Multimédia Mobile — c'est aujourd'hui un organisme de formation médicale sans rapport. Le site institutionnel est **`af2m.org`**. L'af2m édite aussi **33700.fr**.

### 2.1 Transactionnel vs marketing — la distinction est écrite

[F] **CNIL** (`cnil.fr/fr/communication-electronique-quelles-regles`, 10/06/2026) pose trois catégories :
- **prospection commerciale** : messages destinés à « *promouvoir, directement ou indirectement, des produits, des services ou l'image d'une entreprise* » ;
- **communications transactionnelles** : « *nécessaires à la gestion ou l'exécution d'un contrat ou d'un service demandé par la personne* » — exemples cités : « *notifications liées à des évènements […], **confirmations de commandes**, […] rappels* » ;
- **communications relationnelles** : suivi client « *sans finalité promotionnelle* ».

[F] Bases légales, littéralement : « *Contrairement à la prospection commerciale, ces communications ne reposent généralement pas sur le consentement préalable. Elles sont en principe fondées sur : **l'exécution du contrat** conclu avec le client (notamment les messages transactionnels) ; **l'intérêt légitime** […] (messages relationnels)* ».

[F] Confirmation côté profession — la Charte af2m définit le **« Message Fonctionnel »** comme « *Message A2P transactionnel […] : notifications de livraison, confirmation des validations de paiement, **des réservations, des rappels de rendez-vous**, authentification, recouvrement* ». Le cas d'usage est **nommé mot pour mot**.

→ [F] **Un SMS de confirmation de RDV pris par le client n'est pas de la prospection. Aucun consentement préalable n'est requis**, ni au titre de L34-5 CPCE, ni au titre du RGPD (art. 6.1.b, exécution du contrat).

[F] **Le garde-fou** : « *La qualification de prospection commerciale ne dépend pas uniquement du contenu du message, mais avant tout de son **objectif*** » ; « *Si un message comporte une part de contenu commercial […], il peut être **requalifié en prospection commerciale*** ».
→ [R] **Un SMS de confirmation qui glisse une offre (« et -20 % sur votre prochaine couleur ») bascule en prospection et redevient soumis au consentement.** Tenir la tentation marketing hors de ce canal.

[F] Obligation qui subsiste : information de la personne dès la collecte (identité, finalité, droits). Mais : « *Les personnes doivent pouvoir accepter ou refuser facilement de recevoir des communications **sauf lorsqu'elles sont nécessaires au contrat*** ».

### 2.2 Émetteur alphanumérique (Sender ID / « Champ Émetteur » / OADC)

[F] **Il n'existe aucun registre d'État ni obligation légale d'enregistrement en France.** Rien dans le CPCE, rien dans le plan de numérotation. L'encadrement est **professionnel**, par la Charte af2m.

[F] Règles de la Charte (§C.1.3.1) — le champ émetteur doit être :
- « *exclusivement alphanumérique[…], **limitée à onze (11) caractères*** » ;
- **pas ressemblant à un numéro** (jamais exclusivement numérique) ;
- permettre « *l'identification claire et immédiate de l'Editeur, d'une de ses marques ou de l'un de ses produits* », sans confusion avec une marque tierce ;
- **pas de mot générique** (« notif », « amendes »…) sauf nom de société/marque justifié ;
- **caractères latins uniquement** — accents, espaces, ponctuation interdits.

[F] Deux listes tenues par l'af2m (§C.1.3.2) :
- **ISA (« Interdits sauf autorisation »)** — champs émetteurs légitimes protégés contre l'usurpation : « *L'obtention de cette autorisation […] est **obligatoire ainsi que sa déclaration auprès de l'af2m*** ». Justificatif à fournir **sous 2 mois** sur demande, sous peine de manquement.
- **SI (« Strictement interdits »)** — « *Ils devront faire l'objet d'un **blocage en sortie du Réseau*** ».

[F] **Auprès de qui** : de l'**agrégateur** (« Partenaire de l'Opérateur »), qui déclare à l'af2m et aux opérateurs. La Charte impose un **KYC sur toute la chaîne** jusqu'à l'éditeur.

[F] **Coût et délai d'un enregistrement de Sender ID : non publiés → [NV]**, dépendent du contrat agrégateur. Twilio, de son côté, annonce pour la France un pré-enregistrement « **Not Required** » et un Sender ID **gratuit** (`twilio.com/en-us/guidelines/fr/sms`, 2026-09-13).

[F] **Risque d'un Sender ID non conforme** : pas une illégalité en soi, mais une **interruption d'acheminement** décidée contractuellement. Charte §B.1 : « *Chacun des Acteurs […] s'engage […] à faire cesser tout acheminement d'un contenu contrevenant aux présentes* ». Twilio ajoute que les IDs génériques (`SMS`, `Info`, `Verify`) sont **massivement bloqués par les opérateurs français** [F].

### 2.3 La mention STOP s'applique-t-elle au transactionnel ?

**[F] NON.** C'est net, et c'est écrit.

[F] **Charte af2m §C.1.2**, phrase décisive : « ***Le dispositif d'opposition ne concerne pas les Messages de type Fonctionnels.*** »

[F] **Fondement légal cohérent** : l'art. **L34-5 CPCE** (obligation de coordonnées valables pour demander l'arrêt, interdiction de dissimuler l'identité) ne vise que la **prospection directe**. Le transactionnel est hors de son champ.

[F] **Ce qui reste obligatoire quand on envoie un STOP** (§B.3) : gratuité et immédiateté. « *conditionner le droit d'opposition à un **appel ou SMS payant**, ou à l'envoi d'un **formulaire à compléter** […] constitue des manquements* ».

[F] **Format réel** (33700.fr, af2m) : « *Lorsque l'expéditeur affiché est une **marque** : envoyer par SMS le mot-clé STOP **au numéro court affiché dans le message** (sms gratuit)* ». → **Le « STOP au 36111 » n'est pas une norme** : c'est le **short code de la campagne** qui doit être cité. **36xxx** = promotionnel, **38xxx** = fonctionnel.

[F] **Le 33700 n'est pas un canal STOP** : c'est la plateforme de **signalement** des SMS indésirables, gérée par l'af2m.

[F] **En revanche, deux obligations de charte s'appliquent à TOUS les messages A2P, fonctionnels inclus** :
- **§B.1.1** : « *préciser **en début de Message le nom commercial de l'Editeur lors de l'envoi du premier Message A2P*** » ;
- **§C.1.2 / §C.2.2** : le mot-clé **CONTACT** doit renvoyer nom commercial + moyen de contact + site de l'éditeur.

→ [R] **Conséquence directe pour Crenolo** : le code actuel colle « *STOP pour ne plus recevoir.* » à la fin de chaque rappel (`services/sms.py:78`). Ce n'est **pas obligatoire**, cela consomme ~28 caractères sur 160, et cela suggère au client qu'il est démarché. **Le remplacer par le nom du salon en tête** (déjà le cas) **et un mot-clé CONTACT** serait à la fois plus conforme à la charte et plus court. Garder la liste `sms_stop` et le traitement du STOP entrant : **honorer un STOP reste obligatoire même s'il n'est pas sollicité** [R].

### 2.4 Plages horaires

[F] **Aucun texte de loi n'encadre les horaires d'envoi de SMS.** L'encadrement horaire légal vise le **démarchage téléphonique vocal**.

[F] **Charte af2m §B.3** : « *Pour les **Messages Promotionnels** […] s'engagent à ne les acheminer qu'**entre 08h et 21h30***. Il est recommandé […] de ne pas exercer une pression commerciale […] les **dimanches et jours fériés**, et de privilégier les envois du **lundi au samedi**.* »

[F] Et, sans ambiguïté : « *Pour les **Messages Fonctionnels** générés à la suite d'une sollicitation en amont de l'Utilisateur Final […], **aucune restriction horaire ne sera applicable.*** »

→ [F] **Un rappel de RDV peut légalement partir à 7 h ou à 22 h.** [R] Ne pas le faire quand même : le vrai risque n'est plus juridique mais le critère CNIL de l'intérêt légitime « *raisonnable* » et non intrusif — et le client qui répond STOP. **L'heure actuelle de Crenolo (18 h la veille, `HEURE_RAPPEL`) est un bon choix et n'a aucune raison de changer.**

[F] Pour mémoire, deux sources fournisseurs divergent sur l'heure de fin du créneau promotionnel : Twilio dit **08:00–21:30 lun.→sam.**, SMSFactor dit **08:00–20:00 lun.→sam., interdit dimanche et fériés**. La Charte af2m (21h30) fait foi ; SMSFactor applique une règle **plus stricte que la charte**. Sans effet ici, le transactionnel étant exempté.

### 2.5 Mentions obligatoires dans le corps du message

[F] **Loi** (L34-5) : coordonnées valables pour demander l'arrêt, interdiction de dissimuler l'identité — **pour la prospection uniquement**.
[F] **Charte af2m §B.1.1**, applicable à **tous** les A2P : nom commercial de l'éditeur en début du premier message · possibilité de répondre ou de contacter l'éditeur · mentions CNIL accès/modification/opposition · coordonnées de réclamation.
[F] **Interdit de contenu** notable : pas d'incitation à appeler un **numéro surtaxé** dans un message non sollicité ; pas de demande de coordonnées bancaires.
[F] **En RCS, les URL courtes sont interdites** (§C.3.3). → [R] par prudence, éviter aussi les raccourcisseurs en SMS : c'est un marqueur anti-smishing côté opérateurs (§4).

### 2.6 Effet de la réforme du démarchage du 11/08/2026

[F] **Texte** : **LOI n° 2025-594 du 30 juin 2025** contre toutes les fraudes aux aides publiques, **article 13**. Réécrit L223-1, L223-2, L223-5, L223-8 du code de la consommation et **abroge L223-3 et L223-4** (dispositif Bloctel). Entrée en vigueur au **11 août 2026**.

[F] **Contenu** (L223-1, version en vigueur au 11/08/2026) : « ***Il est interdit de démarcher par téléphone*** *[…] un consommateur qui n'a pas exprimé préalablement son consentement* » — consentement libre, spécifique, éclairé, univoque, révocable ; **charge de la preuve sur le professionnel** ; exception pour les sollicitations portant sur un **contrat en cours** ; contrats issus d'un démarchage illicite : **nuls**.

[F] **Périmètre : appels téléphoniques vocaux uniquement.** L'article vise « *démarcher **par téléphone*** » ; ni les SMS ni les messages n'y figurent. La CNIL traite le SMS dans une fiche distincte fondée sur **L34-5 CPCE**, et sa fiche « prospection par téléphone » est explicitement « *hors automate d'appel* ».

[F] Horaires du démarchage vocal depuis le 11/08/2026 : **lun.→ven. 10h-13h et 14h-20h**, interdit samedis, dimanches et jours fériés. **Décret n° 2026-662 du 23 juillet 2026** pour le recueil du consentement (validité **limitée à un an**, preuve conservée **au moins 3 ans**).

→ [F] **Conclusion : la réforme du 11/08/2026 ne change rien au SMS transactionnel.** Elle ne s'applique pas au SMS, et l'exception « contrat en cours » écarterait de toute façon un rappel de RDV.

⚠️ [R] **Mais elle change tout pour l'agent vocal lui-même s'il devait un jour appeler en sortant.** Un agent qui *reçoit* des appels n'est pas concerné ; un agent qui *émet* un appel de relance commerciale tomberait en plein dedans. À garder en tête pour la feuille de route produit.

### 2.7 Le point noir à lever

[NV] **Décision du Conseil constitutionnel du 25 juin 2026** déclarant certaines dispositions de l'art. **L34-5 CPCE** non conformes, avec **effet différé au 31 octobre 2027**. Mention trouvée dans le rendu Légifrance de l'article ; **la décision elle-même n'a pas pu être lue**, et les dispositions censurées sont inconnues. C'est le seul élément susceptible de modifier le socle légal du SMS. **À lever avant toute décision produit structurante.**

---

## 3. Le numéro d'envoi — la question qui décide de l'architecture

Source : **décision Arcep n° 2018-0881 modifiée, annexe 1, version consolidée en vigueur au 1er janvier 2026**. Le PDF servi par l'Arcep porte en pied de page « *Plan national de numérotation – Version du 1er janvier 2026* » → **c'est du droit positif, pas un projet.**

### 3.1 La règle

[F] **§2.3.2 f**, texte exact : « *Les **numéros territorialisés**, à l'exception de ceux pour lesquels une dérogation est prévue dans les conditions spécifiques, **ne peuvent être utilisés comme identifiant de l'appelant présenté à l'appelé pour des appels ou des messages émis par des systèmes automatisés d'appels et d'envois de messages**, au sens de l'article L. 32 du CPCE.* »

[F] Les « numéros territorialisés » couvrent « *les numéros **géographiques, non géographiques et mobiles à 10 chiffres*** » → **01–05, 09 et 06/07**. En vigueur depuis le **1er août 2019**.

[F] Trois exceptions au 2ᵉ alinéa : systèmes adressant **≤ 5 numéros différents sur 30 jours** ; systèmes dont les **messages émis ≤ messages reçus (±20 %)** sur 30 jours ; systèmes dont les appels émis ≤ 20 % des appels reçus. (Motivations citées : TPE de paiement, télésurveillance, chatbots.)

[F] **Les opérateurs sont invités à filtrer** : l'Arcep « *recommande aux opérateurs […] d'**interrompre l'acheminement** des appels et des messages […] qui présentent l'un des numéros territorialisés susmentionnés comme identifiant d'appelant dès lors qu'il apparaît […] qu'ils sont émis par un ou plusieurs systèmes automatisés* ».

### 3.2 Peut-on émettre depuis le numéro 09 de l'agent ?

[F] **Un 09 « ordinaire » (polyvalent standard, VoIP grand public) : NON.** C'est un numéro territorialisé, couvert par l'interdiction.

[F] **Certaines sous-catégories de 09 : OUI**, par dérogation expresse :

| Catégorie | Racines | Statut |
|---|---|---|
| **NPUEPT** — polyvalents pour échanges avec plateforme technique | **0937, 0938, 09390 → 09394** | ✅ conçus pour l'A2P/P2A : des systèmes automatisés peuvent les afficher « *même si […] le nombre de messages reçus est significativement inférieur au nombre de messages émis* » |
| Polyvalents **vérifiés** | 0162, 0163, 0270, 0271, 0377, 0378, 0424, 0425, 0568, 0569, **0948–0949** | ✅ dérogation expresse |
| Polyvalents de **longueur étendue** | **09010 → 09014** | ✅ dérogation expresse |
| Mobiles de **longueur étendue** | **07000 → 07004** | ✅ dérogation expresse |
| Polyvalents **d'intérêt général** | 01510, 02810, 03410, 04410, 05410, **09410** | ✅ (catégorie réservée, liste par arrêté) |

[F] Les **NPUEPT** ont été créés par la **décision Arcep n° 2022-1583 du 1er septembre 2022**. C'est le support du « **SMS conversationnel** » de la Charte af2m, qui parle explicitement de « **Numéro 09** ».

→ [F] **Réponse précise à la question posée** : on ne peut **pas** émettre depuis « le numéro 09 de l'agent » si c'est un 09 ordinaire. On peut émettre depuis un **09 de la tranche NPUEPT (0937/0938/09390-4)**, qui est exactement l'objet réglementaire créé pour ce cas — un numéro long, français, qui envoie **et reçoit**.

### 3.3 Les 06/07 : la porte est fermée à double tour

[F] **Conditions spécifiques aux numéros mobiles, §f** : « ***Par dérogation aux conditions particulières du paragraphe 2.3.2f), les exceptions introduites au 2ᵉ alinéa dudit paragraphe 2.3.2f) ne s'appliquent pas aux numéros mobiles.*** »

→ **Même l'exception « ≤ 5 destinataires sur 30 jours » ne sauve pas un 06/07.** L'interdiction est **absolue**.

[F] **§g** : « *les numéros mobiles ne peuvent être présentés comme identifiant d'appelant et d'émetteur de messages que pour les appels et messages émis **depuis l'accès mobile qu'ils identifient*** ».

[F] **Position de l'af2m** (`af2m.org/sms-marketing/`) : « *l'acheminement de SMS […] via des numéros classiques commençant par **06 ou 07 est interdit** depuis la décision 18-0881 rendue par l'ARCEP et entrée en vigueur le 1er août 2019* » ; « *Ces SMS, acheminés par des circuits souvent flous, n'offrent aucune garantie de livraison des messages, ni de respect des règles de confidentialité […]. Cela est encore plus inquiétant pour les **SMS dits transactionnels**, s'ils contiennent des informations sensibles au sens du RGPD.* »

[F] **« SIM box » / SIM farming** : le terme **n'apparaît dans aucun document Arcep récupéré** (0 occurrence sur le plan de numérotation consolidé et sur la consultation 2025). Le régulateur **ne nomme pas la pratique — il la rend inopérante par le droit de la numérotation**. [H] C'est le fondement réglementaire des blocages massifs de « SMS gris ».

[F] Renfort en préparation ([NV] sur l'adoption finale) — consultation Arcep de juillet 2025 : obligation faite aux opérateurs de « *définir la liste des numéros que chaque utilisateur final peut présenter* » et de « *restreindre techniquement* » la présentation ; et « *les opérateurs n'autorisent pas la **délégation d'affichage pour des numéros mobiles** […] compte tenu des risques d'usurpation particulièrement élevés* ».

[F] Socle législatif : **IV de l'art. L. 44 CPCE** (loi n° 2020-901), en vigueur depuis le **25 juillet 2023** — les opérateurs doivent vérifier que l'émetteur est bien affectataire du numéro présenté et **interrompre** les messages non authentifiables.

### 3.4 Numéros courts (la voie normale du A2P français)

[F] Depuis 2016, les opérateurs ont confié à l'af2m la gestion du plan des **numéros courts SMS**. Deux familles :
- **36xxx** : « *messages promotionnels ou informations clients* » ;
- **38xxx** : « *messages **transactionnels**, communément utilisés pour de l'authentification ou pour **confirmer une réservation, un rendez-vous** ou un achat* ». ← **notre cas, nommé explicitement**.

[F] **Réservation** (`af2m.org/comment-reserver-un-numero-sms-marketing/`) : passer par un **agrégateur**. Dossier : formulaire + contrat, PV de recette de raccordement au **GIE EGP**, KBIS < 3 mois, RIB.
[F] **Tarifs af2m publiés : 400 € HT de réservation · 100 € HT/an par numéro court · 300 € HT de cession.** Délai d'obtention **[NV]**.

[F] **Exclusion** : les systèmes automatisés ne peuvent pas utiliser « *des numéros spéciaux à tarification majorée et des numéros courts à tarification banalisée ou majorée* ».

### 3.5 Et si le client répond ?

| Émetteur | Le client peut-il répondre ? | Base |
|---|---|---|
| **Sender ID alphanumérique** | ❌ **Non** — il n'y a pas de numéro derrière | 33700/af2m : face à une marque, il faut « *envoyer STOP **au numéro court affiché dans le message*** » |
| **Short code 36xxx / 38xxx** | ✅ Oui — la charte impose la gestion de **STOP** et **CONTACT** sur le short code | Charte §C.1.2 |
| **Numéro long 09 NPUEPT** | ✅ Oui, c'est sa raison d'être — « *canal interactif autorisant le dialogue […] initié par un Message A2P […] ou par un Message P2A* » | Charte §C.2 |

[F] Contraintes du 09 NPUEPT : « *la **mutualisation des Numéros 09 est strictement interdite** par la décision ARCEP* » · n'utiliser que les 09 affectés à l'éditeur · **pas plus d'un intermédiaire** technique · **déclaration mensuelle** à l'af2m des affectations et résiliations.

→ [F] **Arbitrage produit fondamental** : un **Sender ID alphanumérique seul rend la conversation impossible**. Si l'on veut qu'un client puisse répondre « OUI » ou « ANNULER » à une confirmation, il faut un **NPUEPT 09** ou un **short code avec mots-clés**. SMSFactor confirme cet arbitrage côté commercial : nom de marque **ou** réception, pas les deux.

→ [R] **Pour Crenolo, l'arbitrage penche vers le Sender ID.** Le pipeline vocal a déjà un canal de retour bien meilleur que le SMS : **le téléphone**. Le client rappelle l'agent. Le SMS n'a pas besoin d'être conversationnel — il a besoin d'être **remis et prouvé**. Le seul entrant à traiter reste le **STOP**, que l'agrégateur gère sur son propre short code et restitue par webhook.

---

## 4. Liens courts

### 4.1 Services auto-hébergeables

| Outil | Licence | Stack | API | Domaine propre | Stats |
|---|---|---|---|---|---|
| **YOURLS** | **MIT** [F] | PHP + MySQL [F] | API développeur [F] | oui [F] | « *historical click reports, referrers tracking and visitors geo-location* » [F] |
| **Shlink** | **MIT** [F] | PHP, **image Docker officielle** [F] | **API REST** documentée + CLI + client web [F] | « *serve shortened URLs **under your own domain*** » [F] | oui [F] |
| Kutt, Polr | [NV] | [NV] | [NV] | [NV] | [NV] |

[F] YOURLS : « *YOURLS is a set of PHP scripts that will allow you to run Your Own URL Shortener, on your server* » (`github.com/YOURLS/YOURLS`, 2026-09-14).
[F] Shlink : « *A PHP-based self-hosted URL shortener that can be used to serve shortened URLs under your own domain* » (`github.com/shlinkio/shlink`, 2026-09-14).
[NV] `shlink.io/documentation/` : domaine bloqué par le filtre de sécurité du fetcher — la doc complète n'a pas été lue.

### 4.2 Impact des liens sur le filtrage anti-spam — honnêtement

[F] **Ce qui est établi** : Twilio ne commercialise le raccourcissement **que sur domaine de marque**. « *Link Shortening is a Messaging Services feature that allows you to send messages with shortened links using **your own company-branded domain*** » (`twilio.com/docs/messaging/features/link-shortening`, 2026-09-14). C'est une option payante : **0,015 $/message, les 1 000 premiers gratuits chaque mois**.

[F] **La Charte af2m interdit les URL courtes en RCS** (§C.3.3).

[NV] ⚠️ **Je n'ai PAS trouvé de document officiel affirmant explicitement que bit.ly ou tinyurl sont bloqués par les opérateurs.** `help.twilio.com` ne rend son contenu qu'en JavaScript (coquille HTML de 4 144 octets, corps vide) ; `twilio.com/en-us/legal/messaging-policy` a bien été récupéré mais **ne parle ni de raccourcisseurs ni de filtrage de liens** ; l'article Telnyx visé renvoie 404.

→ [H] **forte, mais à présenter comme une hypothèse** : l'industrie traite le domaine dédié comme la pratique de référence. Le fait qu'un opérateur A2P majeur ne propose **que** cela, en option payante, et que la charte française l'interdise en RCS, sont les deux indices les plus nets. **Ne pas l'affirmer comme un fait sourcé.**

### 4.3 Bonnes pratiques

[R] Pour Crenolo, dans l'ordre d'importance :
1. **Domaine court dédié à la marque** (`crnl.fr` ou un sous-domaine court), jamais un raccourcisseur public partagé.
2. **HTTPS obligatoire**.
3. **Shlink** plutôt que YOURLS si le lien doit être posé par API depuis la file : REST documentée, Docker, multi-domaines — utile en multi-salons. [H]
4. **Compter les caractères** : un lien mange 20 à 25 caractères sur 160. Le texte actuel de Crenolo est déjà à la limite (§7.2).
5. [F] **GSM-7 vs UCS-2** : un texte accentué bascule en UCS-2 et tombe à **70 caractères**, donc deux segments facturés. Crenolo translittère déjà les accents (`services/sms.py:71`) — **c'est la bonne décision, à conserver**.

---

## 5. WhatsApp Business et RCS

### 5.1 WhatsApp Business Platform

[F] **Modèle par message** depuis le **1er juillet 2025**, toujours en vigueur : « *Effective July 1, 2025, Meta charges on a **per-message basis***» (`developers.facebook.com/docs/whatsapp/pricing`, 2026-09-13). Le modèle « conversation de 24 h » est mort.

[F] **Tarifs FRANCE**, relevés dans le sélecteur de pays de la page tarifaire Twilio (`twilio.com/en-us/whatsapp/pricing`, consulté **2026-09-14**, page portant « *Pricing current as of August 2026* ») :

| Catégorie | Tarif Meta / message |
|---|---|
| **Utility** (confirmation, rappel de RDV) | **0,030 $** |
| **Authentication** | **0,030 $** |
| Marketing | 0,0859 $ |
| Service | **0 $** |
| + frais Twilio fixe | **0,005 $** |

→ [F] **Un template *utility* vers la France chez Twilio = 0,035 $/message**, soit ~0,030 € [H] au taux courant (**taux non sourcé → [NV]**).

[F] **Gratuités** : « *All non-template messages are free* » dans une fenêtre de service client (CSW) ouverte ; « ***Utility templates delivered within an open customer service window are free*** » ; « *Service conversations are now free for all businesses* » (depuis le 01/11/2024). La CSW s'ouvre **24 h** quand l'utilisateur écrit à l'entreprise.

[F] Autres frais Twilio : « *A failed message processing fee of **$0.001 per message*** » sur les messages en statut « Failed ».

[NV] **Business Verification, délai de validation d'un template, paliers de messaging limits (250 / 1 k / 10 k)** : pages Meta correspondantes non récupérées dans cette session.

**[R] Pertinence pour une TPE française : faible, et pour trois raisons.**
1. **Le coût n'est pas l'argument** : 0,030 $ contre 0,058 € le SMS — c'est moins cher, mais l'écart (~2 c€/message, soit ~6 €/mois pour notre salon) ne justifie pas la complexité.
2. **L'onboarding est disproportionné** : Meta Business Manager, vérification d'entreprise, et surtout un **numéro dédié qui ne peut plus servir dans l'application WhatsApp normale**. Un salon qui utilise déjà WhatsApp pour discuter avec ses clientes devrait **renoncer à cet usage** ou prendre une seconde ligne. [H] sur le détail du mécanisme, [F] sur le principe du numéro dédié.
3. **La couverture n'est pas garantie** : tout client n'a pas WhatsApp. Le SMS, si.

[R] **WhatsApp devient pertinent le jour où le client écrit le premier** (CSW ouverte → utility gratuit). C'est une piste pour une v2 « conversation », pas pour la vérification de bout en bout.

### 5.2 RCS

[F] Le programme Google s'appelle désormais « **RCS for Business** » (`developers.google.com/business-communications/rcs-business-messaging`, 2026-09-14). « *Engage with customers seamlessly on **Android and iOS*** » → **iOS est couvert**.

[F] **Accès par partenaire uniquement** : « *To apply to become an RCS for Business partner, fill out the partner registration interest form* ». Une TPE ne s'inscrit pas en direct — elle passe par un agrégateur partenaire [H].

[F] La Charte af2m couvre explicitement le **RCS for Business** : opposition par mot-clé STOP, bouton CTA ou URL ; **opt-in commun SMS/RCS** ; agents RBM enregistrés et validés par l'opérateur ; le **nom de l'agent doit contenir la raison sociale** de l'éditeur ; **URL courtes interdites**.

[F] **Prix constaté chez un agrégateur français** (Spot-Hit, `spot-hit.fr/tarifs`, 2026-09-13) : **RCS interactif 0,150 → 0,110 €** · **RCS basic 0,079 → 0,069 €**.
→ [F] **Le RCS est 2 à 2,5 fois plus cher que le SMS en France.**

[NV] **Liste des opérateurs français supportant le RCS A2P** : la page « Carriers » de Google est une console d'administration pour opérateurs et **ne publie aucune liste de pays** — le mot « France » n'y figure pas. Non vérifié.
[NV] Pages RCS de Twilio (`twilio.com/en-us/rcs`, `/docs/rcs`) : 404 / connexion refusée au moment du test. La navigation des docs Twilio mentionne bien « *Get started with RCS messaging* » — le produit existe [F], sans tarif France vérifié.
[NV] Fallback SMS automatique : non vérifié dans une source officielle.

**[R] Pertinence pour une TPE française : nulle aujourd'hui.** Plus cher, accès par partenaire, couverture opérateur non vérifiable, et aucun bénéfice pour la fonction visée — un accusé de lecture ne remplace pas un accusé de remise, et un logo de marque ne vérifie pas un numéro. À revoir dans 18 mois.

---

## 6. Coût réel — un salon, 150 RDV/mois

### Hypothèses, écrites

| # | Hypothèse | Valeur | Marque |
|---|---|---|---|
| H1 | Rendez-vous par mois | **150** | donnée de l'énoncé |
| H2 | Messages par RDV : 1 confirmation + 1 rappel la veille | **2** | donnée de l'énoncé |
| H3 | Part des RDV avec un mobile FR exploitable | **100 %** — hypothèse **haute et volontairement pessimiste sur le coût** ; le normalisateur rejette les fixes et les étrangers (`sms.py:49`), donc le volume réel sera **inférieur** | [H] |
| H4 | Longueur du message | **≤ 160 caractères GSM-7 → 1 segment** | [F] garanti par `texte_rappel()` |
| H5 | Volume mensuel | **300 SMS** | H1 × H2 |
| H6 | Volume annuel | **3 600 SMS** | H5 × 12 |
| H7 | Prix au palier réellement atteignable à ce volume | voir ci-dessous | [F] |
| H8 | Hors taxes, hors frais de numéro court | — | — |

⚠️ **H7 est le point qui fait la différence et que l'on rate facilement** : à 300 SMS/mois, l'abonnement **Octopush « Basique » (0,045 €) n'est PAS accessible** — sa grille exige **1 000 à 9 999 SMS/mois** [F]. Un salon seul reste au **prix prépayé**. L'abonnement ne devient éligible qu'en **mutualisant le volume de plusieurs salons sur un compte Crenolo** (≥ 4 salons).

### Les trois fournisseurs

| | **OVHcloud SMS Pro** | **Spot-Hit** | **Twilio** |
|---|---|---|---|
| Prix unitaire retenu | **0,058 € HT** (pack 1 000) | **0,059 € HT** (palier 100–10 000) | **0,0798 $** / segment |
| Palier atteignable à 300/mois | ✅ pack 1 000 (≈ 3,3 mois) | ✅ **dès 100 SMS** | ✅ post-payé, sans palier |
| **Coût mensuel** | **17,40 € HT** | **17,70 € HT** | **23,94 $** |
| **Coût annuel (3 600 SMS)** | **208,80 € HT** | **212,40 € HT** | **287,28 $** |
| Frais fixes | aucun ; **20 SMS offerts** à l'inscription [F] | aucun, « sans engagement » [F] | aucun ; numéro dès 1,15 $/mois [F] |
| Expiration des crédits | [NV] | [NV] | s.o. (post-payé) |
| Devise | € | € | **$ — risque de change non couvert** [F] |

**Pour comparaison, aux mêmes hypothèses** : Octopush prépayé **18,30 €/mois** (219,60 €/an) · SMSFactor **19,80 €/mois** (237,60 €/an, **crédits expirant à 1 an** [F]) · WhatsApp utility **10,50 $/mois** [F] mais avec l'onboarding décrit en §5.1.

### Ce que ce chiffre veut dire

1. **[F] Le SMS coûte ~17 € HT par mois et par salon.** C'est **moins cher que ce que le code de Crenolo suppose** : le docstring de `services/sms.py` avance « *quatre à sept centimes le SMS* […] *cela dépasserait le prix de l'abonnement* ». Le prix est exact (5,8 c€), la conclusion ne l'est pas à ce volume. **Le calcul qui a justifié la passerelle SIM reposait sur « quelques centaines par mois et par salon » — soit le double du volume réel d'un salon à 150 RDV.**
2. **[F] Le short code coûte plus cher que les SMS** : 400 € HT + 100 € HT/an. Pour **un** salon, c'est disqualifiant. Mutualisé sur la plateforme Crenolo, c'est **100 € HT/an** répartis — négligeable. [H] sur la licéité de la mutualisation d'un **short code** entre salons : la charte interdit explicitement la mutualisation des **numéros 09**, mais ne dit rien d'équivalent pour les short codes. **[NV] à faire trancher par l'agrégateur.**
3. **[R] L'économie d'échelle est dans le regroupement, pas dans la SIM.** 10 salons × 300 SMS = 3 000 SMS/mois → palier Octopush « Basique » (0,045 € + 9 €/mois) → **~13,80 €/mois par salon**, soit **20 % moins cher** que le prépayé, avec des DLR et sans illégalité.

---

## 7. Recommandation : garder la passerelle SIM, ou passer en A2P ?

### 7.1 La réponse

**[R] Passer à un fournisseur A2P. Retirer la passerelle SIM du chemin de production.** Trois raisons, dans l'ordre où elles tombent.

**1. [F] C'est illicite.** La passerelle présente un **06/07** comme identifiant d'émetteur pour des messages émis par un système automatisé. L'interdiction est **absolue pour les mobiles** — les trois exceptions du §2.3.2 f sont expressément écartées par les conditions spécifiques aux numéros mobiles, et le §g ajoute qu'un numéro mobile ne peut être présenté que « *pour les appels et messages émis depuis l'accès mobile qu'il identifie* ». L'af2m vise nommément le transactionnel : « *Cela est encore plus inquiétant pour les SMS dits transactionnels, s'ils contiennent des informations sensibles au sens du RGPD.* » Le code de Crenolo anticipe d'ailleurs le problème sans le nommer : « *Une SIM grand public qui débite vingt messages en dix secondes se fait remarquer de l'opérateur — et c'est la ligne d'Adnan.* » Ce n'est pas un risque de débit. C'est un risque de **résiliation de la ligne** et, en cas de contrôle, de manquement réglementaire.

**2. [F] Elle ne peut pas fournir la preuve que le produit vend.** Le cahier des charges dit : le SMS **prouve** que le numéro est joignable. Or un modem confirme qu'il a **accepté** le message, jamais que l'opérateur l'a **remis**. Le code est lucide sur ce point (`envoye_le` n'est écrit qu'après confirmation modem) mais la lucidité ne crée pas l'information manquante. **Aucun DLR, donc aucune vérification de bout en bout.** Un fournisseur A2P livre `delivered` / `undelivered` / `failed` par webhook — c'est **exactement** le signal qui permet de marquer un rendez-vous « à vérifier » à bon escient. Aujourd'hui, un numéro saisi de travers par l'agent vocal serait marqué « envoyé ».

**3. [F] L'argument économique qui l'a justifiée ne tient plus.** ~17 € HT par mois et par salon (§6), contre un portable qui doit rester allumé, un routeur SIM, un forfait, et une panne qui arrête silencieusement toutes les vérifications de tous les salons.

### 7.2 Ce qu'on garde — et c'est l'essentiel

La couche logicielle de Crenolo est **bien conçue et entièrement réutilisable**. Le problème est le dernier kilomètre, pas l'architecture.

| Composant | Verdict | Motif |
|---|---|---|
| File `sms_sortants` (`023_sms.sql:8`) | ✅ **garder** | Découplage envoi/écriture correct ; l'index partiel `idx_sms_a_envoyer` reste pertinent |
| `envoye_le` écrit après coup | ✅ **garder, et enfin le mériter** | Avec un DLR, ce champ devient vrai |
| Liste `sms_stop` (`023_sms.sql:33`) | ✅ **garder** | Honorer un STOP reste obligatoire même quand la mention n'est pas requise |
| `est_un_stop()` tolérant (`sms.py:105`) | ✅ **garder** | Conforme à l'esprit de la charte (opposition simple, immédiate, gratuite) |
| `numero_normalise()` — mobiles FR seuls (`sms.py:49`) | ✅ **garder tel quel** | La restriction porte sur le **destinataire**, pas sur l'émetteur : elle est **correcte et sans rapport** avec l'interdiction Arcep, qui vise l'identifiant d'émetteur |
| Translittération GSM-7 (`sms.py:71`) | ✅ **garder** | Évite le basculement UCS-2 à 70 car. et le doublement de la facture [F] |
| `HEURE_RAPPEL = 18 h` (`sms.py:37`) | ✅ **garder** | Aucune restriction horaire ne s'applique au fonctionnel [F], mais 18 h reste le bon choix d'usage |
| Routes internes `/internal/sms/*` | ✅ **garder** — elles deviennent l'adaptateur | Il suffit de remplacer le consommateur |
| **Passerelle SIM** (`passerelle_sms.py`) | ❌ **retirer du chemin de production** | §7.1. [R] La **conserver en mode `--a-blanc`** comme harnais de test hors ligne : c'est un atout, pas un déchet |
| Suffixe « STOP pour ne plus recevoir. » (`sms.py:78`) | ⚠️ **à revoir** | **Non obligatoire** en fonctionnel [F] ; mange ~28 car. sur 160 ; suggère un démarchage. Le remplacer par un **mot-clé CONTACT**, lui bien exigé par la charte pour tout A2P [F] |
| Unicité `booking_id` (`023_sms.sql:28`) | ❌ **bloquant, à corriger** | Elle interdit d'écrire **à la fois** une confirmation et un rappel pour un même RDV — or le produit demande les deux. Passer à une clé `(booking_id, type)` |
| Absence de péremption dans la file | ❌ **à ajouter** | Une confirmation partie 3 h après l'appel ne vérifie plus rien. Cf. le *Validity Period* de Twilio [F]. Ajouter un `expire_le` et basculer en « à vérifier » plutôt qu'envoyer tard |
| `TENTATIVES_MAX = 5` puis abandon silencieux | ⚠️ **à revoir** | Aujourd'hui le message sort de la file sans que personne ne soit prévenu. Doit marquer le RDV « à vérifier » |
| Lot 20 + 4 s entre envois + tour de 30 s | ❌ **caduc** | Contraintes de la SIM. Chez un agrégateur, la confirmation part en quelques secondes |
| `X-Internal-Secret` non scopé par salon | ⚠️ **dette connue** | Déjà relevé dans `docs/recherche2/A7-hotes-de-greffe.md:51` |

### 7.3 Choix du fournisseur et de l'émetteur

[R] **Fournisseur** — court-lister **OVHcloud SMS Pro** et **Spot-Hit**, dans cet ordre :
- **OVHcloud** : opérateur français, 0,058 €, packs **dès 100 SMS**, **20 crédits offerts** pour valider la chaîne de bout en bout avant tout engagement. Réserve : API et DLR **[NV]** — **c'est le point à vérifier en premier**, et c'est éliminatoire si les DLR par webhook n'existent pas.
- **Spot-Hit** : 0,059 €, ticket d'entrée à 100 SMS, sans engagement, société française. Même réserve **[NV]** sur l'API (doc en 522 / rendue en JS).
- **SMSFactor** : le plus cher des trois (0,066 €) mais **de loin le mieux documenté** — webhooks *Delivery reports* / *Replies* / *Stops* explicitement listés, API Senders, règles françaises écrites noir sur blanc. [R] **À retenir si l'intégration doit être faite vite et sûrement** : +2,40 €/mois par salon pour une doc qui existe, c'est bon marché. Réserve : **crédits expirant à 1 an** [F] et **anti-flood horaire** [F].
- [R] **Écarter Twilio** ici : 35 % plus cher, facturé en USD, surcoûts opérateurs annoncés. Le garder en second choix si l'inbound devient une exigence dure — c'est le seul à documenter « *Inbound fully supported* ».
- [R] **Écarter** LinkMobility et Sinch (pas de tarif public), Telnyx / Vonage / Brevo (non comparables sans compte ouvert).

[R] **Émetteur** — **Sender ID alphanumérique au nom du salon** (≤ 11 caractères latins, sans accent), pas de numéro long, pas de short code dédié au départ :
- c'est ce que la charte veut (identification claire de l'éditeur) [F] ;
- l'enregistrement est gratuit et non préalable chez Twilio pour la France [F], et [NV] ailleurs — **à chiffrer avec l'agrégateur retenu** ;
- le canal de retour du client, c'est **le téléphone de l'agent vocal**, pas le SMS ;
- le STOP entrant est géré par l'agrégateur sur son propre short code et restitué par webhook sur la route `/internal/sms/entrant` **déjà écrite**.
- ⚠️ [F] Éviter absolument un Sender ID générique type « RDV », « Info », « SMS » : Twilio documente qu'ils sont **massivement bloqués par les opérateurs français**.

### 7.4 Les cinq choses à faire confirmer par écrit avant de signer

Toutes en **[NV]** aujourd'hui :
1. **DLR par webhook** chez OVHcloud et Spot-Hit : existence, statuts, format. **Éliminatoire.**
2. **Expiration des crédits** chez OVHcloud, Octopush et Spot-Hit.
3. **Coût et délai d'enregistrement d'un Sender ID** alphanumérique.
4. **Classement explicite du « rappel de rendez-vous » en message fonctionnel** (exemption horaire, dispense de STOP) — le faire écrire par le fournisseur.
5. **Anti-flood** : seuil exact, si confirmation et rappel peuvent partir à moins d'une heure d'écart (RDV pris la veille pour le lendemain — cas fréquent chez un agent vocal).

Et un point de droit, indépendant des fournisseurs :

6. **[NV] Décision du Conseil constitutionnel du 25 juin 2026** sur l'art. L34-5 CPCE, effet différé au **31 octobre 2027**. Dispositions censurées inconnues. **À lever.**

---

## 8. Ce que cette recherche n'a pas pu établir

| # | Trou | Impact |
|---|---|---|
| 1 | **Débit msg/s et SLA de latence** pour la France : **aucun fournisseur n'en publie** | Moyen — empêche de promettre un délai de confirmation |
| 2 | **API, DLR et inbound d'OVHcloud, Octopush et Spot-Hit** (docs en JS, 522, ou redirections non suivies) | **Fort** — c'est le critère de choix n° 1 |
| 3 | Prix France de **Telnyx, Vonage, Brevo, Sinch, LinkMobility** | Faible — les acteurs retenus suffisent |
| 4 | **Décision CC du 25/06/2026** sur L34-5 CPCE | **Fort** — seul élément pouvant bouger le socle légal |
| 5 | Adoption finale de la **consultation Arcep de juillet 2025** | Faible — renforcerait l'interdiction, ne l'inverserait pas |
| 6 | **Listes af2m SI / ISA** et délais de mise en conformité (non publiques, réservées aux membres) | Moyen — à obtenir via l'agrégateur |
| 7 | **Délai d'obtention d'un short code** 36xxx/38xxx (procédure publiée, délai non) | Faible |
| 8 | **DGCCRF** : fiche démarchage en 403 / Cloudflare | Faible — la CNIL et Légifrance couvrent le sujet |
| 9 | **Preuve documentaire officielle** du filtrage des raccourcisseurs publics | Moyen — recommandation maintenue en [H], pas en [F] |
| 10 | WhatsApp : **Business Verification, délais de template, messaging limits** | Faible — WhatsApp est écarté |
| 11 | **Opérateurs français supportant le RCS A2P** | Faible — RCS écarté |
| 12 | Licéité de la **mutualisation d'un short code** entre salons d'une même plateforme | Moyen — conditionne l'économie d'échelle du §6 |

**Cause commune des trous 1, 2, 3 et 9** : le budget WebSearch était épuisé avant le début. Sans recherche, on ne peut atteindre que les URL que l'on devine — et les pages tarifaires modernes sont rendues en JavaScript. **Une reprise avec WebSearch disponible lèverait probablement les trous 2, 3 et 9 en une heure.**

---

## Annexe — journal des sources

**Réglementation** (toutes consultées 2026-09-14, toutes récupérées avec succès)
- `https://www.arcep.fr/uploads/tx_gsavis/18-0881.pdf` — plan national de numérotation, **version consolidée au 1er janvier 2026**
- `https://www.arcep.fr/uploads/tx_gsavis/22-1583.pdf` — décision du 01/09/2022 créant les NPUEPT
- `https://www.arcep.fr/uploads/tx_gspublication/consultation-plan-de-numerotation-2025_juil2025.pdf` — consultation 07/2025 (**statut : proposé**)
- `https://af2m.org/charte-business-messaging/` → PDF Charte Business Messaging **en vigueur au 01/03/2026**
- `https://af2m.org/charte-business-messaging-2026-laf2m-renforce-les-regles-du-jeu/` (13/02/2026)
- `https://af2m.org/sms-marketing/` · `https://af2m.org/comment-reserver-un-numero-sms-marketing/`
- `https://www.33700.fr/informations-pratiques/stop/`
- `https://www.cnil.fr/fr/la-prospection-commerciale-par-courrier-electronique` (10/06/2026)
- `https://www.cnil.fr/fr/communication-electronique-quelles-regles` (10/06/2026)
- `https://www.cnil.fr/fr/prospection-commerciale-par-telephone-hors-automate-dappel-quelles-sont-les-regles` (10/06/2026)
- `https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000042155961` (L34-5 CPCE)
- `https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000042155931` (L223-1 c. conso, version au 11/08/2026)
- `https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000051824277` (LOI n° 2025-594 du 30/06/2025)

**Fournisseurs** (2026-09-13) — succès : `twilio.com/en-us/sms/pricing/fr` · `twilio.com/en-us/guidelines/fr/sms` · `twilio.com/docs/messaging/api/message-resource` · `ovhcloud.com/fr/sms/` · `octopush.com/tarifs-sms-france/` · `smsfactor.com/tarifs/` · `dev.smsfactor.com/api/sms/about-sms` · `dev.smsfactor.com/api/sms/getting-started` · `spot-hit.fr/tarifs` (curl) · `linkmobility.fr`
Échecs : `ovhcloud.com/fr/sms/tarifs/` (404) · `telnyx.com/resources/international-sms-pricing` (404) · `vonage.com/…/sms/pricing/` (403) · `brevo.com/fr/produits/sms-marketing/` (404) · `help.brevo.com/…` (403) · `spot-hit.fr/documentation-api` (522) · `sinch.com/pricing/` (000) · grilles Vonage et Brevo rendues en JS

**WhatsApp / RCS / liens** (2026-09-13 et 14) — succès : `developers.facebook.com/docs/whatsapp/pricing` · `twilio.com/en-us/whatsapp/pricing` (tarifs France dans les attributs `data-*` de l'option `value="FR"`) · `twilio.com/docs/messaging/features/link-shortening` · `twilio.com/docs/messaging/guides/market-throughput-overview` · `twilio.com/docs/messaging/guides/scaling-queueing-latency` · `developers.google.com/business-communications/rcs-business-messaging` (+ `/carriers`) · `yourls.org` · `github.com/YOURLS/YOURLS` · `github.com/shlinkio/shlink`
Échecs : `help.twilio.com/articles/*` (coquille JS vide) · `twilio.com/en-us/rcs` et `/docs/rcs` (404/000) · `shlink.io/documentation/` (domaine bloqué) · `gsma.com/…/rcs/` (403) · `support.telnyx.com/…` (404)

**Code interne** (lu intégralement) — `api/services/sms.py` · `api/models/sms.py` · `api/migrations/023_sms.sql` · `api/routers/internal/sms.py` · `api/scripts/passerelle_sms.py`, dans `/home/marpeap/Bureau/Marpeap Digitals/rdv.marpeap.com`
