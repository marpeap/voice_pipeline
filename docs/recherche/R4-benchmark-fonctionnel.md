# R4 — Benchmark fonctionnel : réception d'appels par IA / standard téléphonique IA

**État au 13 septembre 2026.** Toutes les dates de consultation ci-dessous sont le **13/09/2026** sauf mention contraire.

## Convention de fiabilité

Chaque affirmation porte un marqueur :

- **[V]** — **fait vérifié** sur une source officielle (page produit, doc, centre d'aide, page tarifs de l'éditeur) avec URL.
- **[T]** — **fait rapporté par un tiers** (comparateur, blog concurrent, presse). À traiter comme indice, pas comme preuve : une grande partie du contenu « best AI receptionist 2026 » en ligne est du marketing de concurrents.
- **[H]** — **hypothèse / lecture d'analyste** de ma part. Jamais présenté comme un fait.
- **[NV]** — **non vérifié** : cherché, pas trouvé de source officielle.

Rien dans ce document n'est inventé. Quand un tarif ou une fonctionnalité n'a pas pu être confirmé sur une page officielle, c'est écrit.

**Limite de la collecte :** le budget de recherche web de la session a été atteint avant d'avoir pu épuiser certains fils (notamment les avis primaires G2/Capterra, protégés par Cloudflare — HTTP 403 sur `g2.com` en accès direct, constaté le 13/09/2026). Les manques sont signalés à leur place.

---

## Sommaire

1. Produits spécialisés en réception d'appels par IA (US/international)
2. Marché français et européen
3. Voisins fonctionnels : logiciels de réservation, standards cloud, cadre réglementaire
- **A.** Taxonomie des fonctionnalités en trois niveaux
- **B.** La configuration par le commerçant (cœur de la différenciation)
- **C.** Trous du marché et plaintes récurrentes
- **D.** Implications produit
- **E.** Dette de recherche

## Les dix faits qui comptent

1. **Planity n'a aucune offre de réception d'appels par IA** — ni sur sa page produit, ni sur sa page tarifs, où aucun prix n'est d'ailleurs affiché. **[V]**
2. **Les logiciels de réservation anglo-saxons l'ont déjà industrialisée** : Fresha AI Concierge **94,95 €/site/mois**, Boulevard Beau **125 $/site/mois (200 min, puis 0,60 $/min)**, Zenoti AIR (tarif non public, avec appels sortants et frais d'annulation automatiques). **[V]**
3. **Aucun produit clé en main anglo-saxon ne parle français** : Slang, Rosie, Dialzara, Smith.ai plafonnent à l'anglais + espagnol. **[V]**
4. **Les startups françaises parlent français mais ne sont dans aucun logiciel de réservation** : Tala 29 €, Sylen 49 €, Elio 79 €, Kronos 249 €, Vokai 299 € — toutes branchées sur un agenda générique par renvoi d'appel. Une seule nomme Planity (AirAgent, tarif non public). **[V]**
5. **Le prompt libre a déjà disparu chez les meilleurs.** Six patrons de configuration coexistent ; les plus aboutis sont « zéro configuration parce que le logiciel métier sait déjà » (Fresha, Boulevard, Zenoti) et « questionnaire sectoriel pré-rempli » (Slang, Dialzara, Vokai). **[V]**
6. **Personne n'entraîne l'agent sur l'historique de rendez-vous.** Tout le monde part du site web, de la fiche Google ou d'un questionnaire. C'est le seul avantage qu'une greffe sur logiciel de réservation peut prendre et que personne ne peut copier sans les données. **[NV → opportunité]**
7. **La plainte n°1 des appelants n'est pas l'IA, c'est le déguisement.** Verbatim r/smallbusiness : « **Complaints basically stopped once we made it announce it was automated in the first breath. People forgive a robot for being a robot, they don't forgive it for pretending.** » L'obligation légale et la satisfaction client pointent dans le même sens. **[V, Reddit primaire]**
8. **La plainte n°1 des exploitants est la facture**, aggravée par le spam qui consomme le quota (« they tell you to move your call plan up… meanwhile your getting lots of robo calls », Trustpilot Ruby). Goodcall prouve l'alternative : minutes illimitées, 0,50 $ par client unique au-delà du quota. **[V]**
9. **La prise de RDV sans intégration API officielle est dénoncée comme trompeuse par les exploitants eux-mêmes** : « **the ai agent is guaranteed to cause more pain for you as it will make mistakes all the time** ». C'est la validation directe de la thèse de la greffe native. **[V, Reddit primaire]**
10. **Deux échéances légales de 2026 changent le cahier des charges** : annonce obligatoire « vous parlez à une IA » (AI Act art. 50, depuis le 02/08/2026) et consentement préalable au démarchage téléphonique (depuis le 11/08/2026, Bloctel supprimé) — ce qui borne sévèrement toute fonction d'appel sortant. **[T, à faire valider juridiquement]**

---

## 1. Produits spécialisés en réception d'appels par IA

Sauf mention contraire, tout ce qui suit est **[V]** (lu sur une page officielle de l'éditeur, consultée le 13/09/2026) et ce qui n'a pas pu l'être est écrit **non vérifié [NV]**.

### 1.1 Slang.ai — restaurants

- **Agent** : réponse 24/7 et gestion automatique des réservations — « instantly responds to guest inquiries, and automatically manages reservations – 24/7 ». FAQ : « From hours and directions to reservations, promos and allergy information ». Transfert : « If Slang AI cannot address a query, it automatically forwards the call to a human staff member ». SMS : « Send real-time SMS messages to guests, including reservation confirmations, ordering links, wine lists » ; texting IA bidirectionnel (« AI-Powered Texting », plan Premium). **Appels sortants : [NV]**. — https://www.slang.ai/ , https://www.slang.ai/product
- **Intégrations** : OpenTable, SevenRooms, Tripleseat, Yelp, Fishbowl. Agenda Google/Outlook, CRM, POS, Zapier/API : **[NV]**.
- **Configuration** : pas de prompt libre exposé — « User-Friendly Restaurant Prompts » pré-construits par des experts en design conversationnel à partir de « 17 million+ guest calls », et « Pre-Trained AI » ; « Flexible Call Handling » (renvoi d'appel, routage VIP différencié pendant/hors horaires). Import du site, scraping Google Business, onboarding par appel : **[NV]** côté page officielle (l'onboarding humain de 30 min est **[T]**, cf. §B.1).
- **Multilingue** : **anglais / espagnol uniquement** — « Bilingual Support (Spanish) » en Premium ou à la carte, « Spanish Concierge support... developed and tested by native Spanish speakers ».
- **Garde-fous** : escalade automatique en cas d'échec ; « Real Time Alerts » sur incidents (objet perdu, réclamation) en Premium. Détection d'urgence par mots-clés : **[NV]**.
- **Analytique** : enregistrements, résumés, insights réservations, « call volume, answer rate, reservations, covers, peak call times, common customer inquiries, and guest satisfaction », classement des sites entre eux. Le mot « sentiment » n'apparaît pas ; la satisfaction est mesurée (CSAT).
- **Tarifs** (https://www.slang.ai/pricing) : **Core 399 $/site/mois** · **Premium 599 $/site/mois** · **Enterprise** sur devis. CAD : 379 / 539. À la carte : Private Events (Tripleseat), support bilingue. **Aucun tarif à la minute ni à l'appel.**

### 1.2 Numa — concessions automobiles (hors cible, mais instructif)

⚠️ Produit **verticalisé concession auto**, pas un réceptionniste générique pour commerce de proximité.

- « The AI Operating System » pour concessionnaires, « 1,300+ rooftops », « 1B+ calls & texts handled ». — https://www.numa.com/
- **Agent** : voix **et** SMS ; prise de RDV avec « 80%+ appointment booking rate » annoncé ; « AI with telepathic context. Full history, real-time sentiment, the right response » ; **écriture en retour dans le DMS** — « Numa resolves the request and writes it back to the DMS ». Modules : Voice AI, Smart Inbox, **LiveCSI™** (satisfaction temps réel), Service Advisor Agent, **Heat Case Agent** (récupération des clients insatisfaits), Opportunity Agent, app mobile. — https://www.numa.com/pricing
- **Intégrations** : DMS (couverture annoncée 90 % du secteur), CRM, scheduler. Noms précis, Zapier/API : **[NV]**.
- **Configuration, multilingue, transfert, transcription, résumé, containment : [NV]**.
- **Tarifs : aucune grille publique** (page /pricing sans prix, demande de démo).

> **[H]** Le *Heat Case Agent* est la seule mécanique du panel qui traite explicitement le client mécontent comme un objet produit. Transposable en salon : le client dont le rendez-vous a mal tourné.

### 1.3 Goodcall

- **Agent** : transfert vers la ligne de l'entreprise ; partage instantané de chaque appel « via SMS, email » ; prise de RDV via synchro agenda — « Sync with your CRM and calendar to cut booking time by 5X » ; capture de leads vers Google Sheets ou CRM ; « Tune agent logic, workflows, and skills ». Qualification, rappel, sortant, warm vs cold : **[NV]**. — https://goodcall.com/
- **Configuration** (le plus explicite du panel) : 5 étapes — connecter l'entreprise (CRM, agenda, base de connaissance) → définir les **AI Skills** (RDV, FAQ, routage, capture de leads) → régler la **logique de conversation** (routage, repli) → choisir le numéro (nouveau ou renvoi) → publier. Escalade configurable : « transfer to a specific person, department, take a message, send a self-service link, or schedule a callback ». Contrôle total du texte « from the greeting... to the goodbye ». Création à partir du **site web, de la fiche Google, ou de détails métier saisis**. — https://www.goodcall.com/how-it-works
- **Intégrations** : **Zapier (10 000+ outils)**, CRM générique, Google Sheets, agenda générique. Pages /integrations et /features en 404 → liste exhaustive **[NV]**.
- **Multilingue : [NV]** — aucune langue mentionnée.
- **Analytique** : « Track **automation rates**, call duration, and caller behavior », analyse de « intent and outcomes of every interaction ». Transcription/résumé non nommés sur les pages lues (rétention « call details » 7 j / 30 j / illimitée).
- **Tarifs** (https://goodcall.com/pricing) — **au client unique, pas à la minute** :

| Plan | Mensuel | Annuel (−15 %) | Inclus |
|---|---|---|---|
| Starter | 79 $ | 66 $ | minutes/tokens illimités, **1 logic flow**, 3 membres, 3 contacts, détails 7 j, **100 clients uniques/mois** puis **0,50 $/client** |
| Growth | 129 $ | 108 $ | **3 logic flows**, 9 membres, 25 contacts, détails 30 j, **250 clients uniques** |
| Scale | 249 $ | 208 $ | **25 logic flows**, 50 membres, 500 contacts, détails illimités, **500 clients uniques** |
| Enterprise | devis | — | workflows custom, équipe illimitée, gestionnaire dédié, intégrations API, sécurité entreprise |

### 1.4 Rosie (heyrosie.com) — le plus proche du besoin « commerce de proximité »

- **Agent** : prise de RDV — « Book appointments directly into your calendar or texts a scheduling link » (écriture directe à partir du plan Scale ; lien SMS dès Professional) ; **prise de message par scénarios** (2 / 5 / illimités selon plan) ; **transferts « warm or cold »**, « Warm transfers – Rosie briefs your team before connecting », « Live call transfers » (Scale), **« Waterfall transfers – Rosie tries multiple numbers until someone answers »** (Growth) ; SMS pendant l'appel (Scale) ; FAQ personnalisées ; **détection automatique du spam** ; widget de chat sur le site inclus. Qualification, appels sortants : **[NV]**. — https://heyrosie.com/ , https://heyrosie.com/pricing
- **Configuration** (point fort) : **« Auto-trained from your website and Google Business Profile »** — c'est **le seul produit du panel où le scraping de la fiche Google Business est confirmé en page officielle**. Plus : FAQ personnalisées, message d'accueil, choix parmi « 10+ voices » ; en plan Growth, « Custom agent training – upload your training docs, policies, and more » et « White-glove onboarding – dedicated specialist ».
- **Intégrations** : agenda (générique), **Zapier — « connect to 1,000+ apps »**. Marques d'agenda, CRM, POS, API : **[NV]**.
- **Multilingue** : **« Speaks fluent English and Spanish on every call »** — **français non supporté** selon les pages lues.
- **Analytique** : « Every call logged with an AI-generated summary and full transcript and recording » ; notifications e-mail et SMS pour chaque appel. Sentiment, taux de résolution : **[NV]**.
- **Tarifs** : **Professional 49 $/mois (250 min)** · **Scale 149 $/mois (1 000 min)** · **Growth 299 $/mois (2 000 min)**. **Surcoût par minute au-delà : non affiché [NV]**. Add-on *Website Texting* **50 $/mois** (25 conversations incluses, **1 $** par conversation supplémentaire).

### 1.5 Dialzara

- **Agent** : réponse 24/7, prise de RDV (« Books appointments directly to your calendar »), **qualification et filtrage spam** (« Screens spam and qualifies leads »), résumés d'appels par e-mail, transcription de messagerie, routage, **appels simultanés illimités** ; agents **SMS bidirectionnels** et chatbot de site. Appels sortants : **[NV]** (la grille lue est intitulée « Voix entrante »). — https://dialzara.com/ , https://dialzara.com/pricing/
- **Configuration** : parcours en 4 étapes, **≈ 15 minutes** — création de compte et **import du site web** → choix parmi « 50+ different voices » et du numéro → **téléversement de documents de formation** → activation du renvoi d'appel. Scraping Google Business, flows visuels : **[NV]**.
- **Intégrations** : « CRM/calendar integration » dès le premier palier, renvoi depuis le système existant. **Aucune marque nommée [NV]**.
- **Multilingue** : **anglais + espagnol** (dès le plan Lite). Autres langues : **[NV]**.
- **Transfert** : « You can specify transfer numbers and conditions. Multiple transfer extensions are supported. » Warm vs cold, détection d'urgence : **[NV]**.
- **Tarifs** — seul acteur du panel publiant un **surcoût minute dégressif** :

| Plan | Prix | Minutes incluses | Surcoût/min |
|---|---|---|---|
| Business Lite | 29 $/mois | 60 | **0,48 $** |
| Business Pro | 99 $/mois | 220 | **0,45 $** |
| Business Plus | 199 $/mois | 500 | **0,40 $** |
| Business Elite | 349 $/mois | 1 000 | **0,35 $** |

Essai 7 jours, pas de frais de setup.

### 1.6 Smith.ai — hybride IA + humains

**AI Receptionist** — « Answer, qualify, book, and convert », 24/7, filtrage des prospects par type de dossier, réservation de consultations, suivi ; enregistrement et **transcription intégrale** ; routage avec contexte ; scoring qualité via « Quality Studio ». Intégrations natives **Salesforce, HubSpot, Clio** et « 5,000+ apps either natively, or through Zapier and Make ». **Anglais et espagnol**, « 12+ voices ». Escalade vers les **500+ réceptionnistes humains nord-américains**, **facturée à l'appel en supplément** — c'est le garde-fou différenciant du produit. — https://smith.ai/ai-receptionist

- **Tarifs AI** : **gratuit** 25 appels/mois puis **3,00 $/appel** · **Pro 150 $/mois** (**2,00 $/appel**) · **Enterprise 500 $/mois** (**1,67 $/appel**). Sans contrat ni frais de setup.
- **Tarifs Virtual Receptionist (humains)**, facturation **à l'appel** — « Billing per client call saves you money » : Starter 30 appels **300 $/mois** (surcoût 11,50 $) · Basic 90 appels **810 $** (10,50 $) · Pro 300 appels **2 100 $** (8,50 $) · Enterprise sur devis ; −10 % à 12 mois. — https://smith.ai/pricing

> ⚠️ Contradiction à noter : des blogs tiers annoncent un **frais de setup de 95 $** et un engagement minimum payé d'avance chez Smith.ai **[T]**, alors que la page officielle dit « no contracts or setup fees » pour l'offre AI **[V]**. Les plaintes Trustpilot (§C.2) portent sur l'engagement long. **À vérifier au contrat avant toute comparaison publique.**

### 1.7 Ruby — réceptionnistes humains + couche IA

- Service de réceptionnistes **humains**, avec des « optional AI enhancements available in all our plans, at no extra cost! ». — https://www.ruby.com/pricing/
- **Fonctions IA nommées** (https://www.ruby.com/ai/) : **Call Nav** — « LLM-powered assistant pulls relevant information from a database built for the business that receptionist is representing » (assistance au réceptionniste humain, pas un agent autonome) ; **transcription** verbatim de chaque appel et des messages vocaux ; **analyse de sentiment** — « AI-quantified insights around your callers' sentiments » ; **filtrage spam/robocalls** par filtres IA.
- **Tarifs**, à la minute : 50 min **250 $/mois** · 100 min **395 $** · 200 min **720 $** · 500 min **1 725 $**. Live Chat 10/30/50 chats : 143 / 335 / 520 $. Bundle −20 % sur le chat. « No additional or hidden fees for activation, onboarding, setup, customization ». Surcoût minute : **[NV]**.

> Repère de coût : Ruby 200 min = **720 $/mois** contre Rosie 1 000 min = **149 $/mois**. **Facteur ≈ 24× à la minute** — c'est l'écart humain / IA du marché, et l'argument économique central de la catégorie.

### 1.8 Curious Thing — **non vérifiable**

Le site est intégralement rendu côté client : `curiousthing.io/`, `/features`, `/features/customise` et la page produit « Alex » renvoient un contenu **vide** au fetch, et le HTML brut ne contient aucun texte. **Aucune information n'est affirmée.** Les seules indications disponibles (produit australien, agents « Lucy » et « Alex », paiement / demandes / RDV / FAQ / qualification, entrant et sortant, conformité ISO 27001, SOC 2, GDPR, HIPAA) proviennent d'**extraits de moteur de recherche** et sont **[NV]**. Tarifs, langues, intégrations : **[NV]**.

### 1.9 Parloa — grands comptes

- « AI Agent Management Platform » (AMP), cycle « Design, Test, Scale, Optimize », « millions of conversations in any language » ; secteurs finance, utilities, e-commerce, santé, médias, IT. — https://www.parloa.com/ , https://www.parloa.com/platform/
- **Configuration** : **Parloa Studio**, builder « intuitive UI » ; briques « Pre-built Skills, Custom Skills, Integrations, Subtask Agents, MCP Skills » ; déploiement Chat, Messaging, Voice.
- **Intégrations** : Salesforce, SAP, ServiceNow, Zendesk, et plus largement « CCaaS, CRM, and data systems » ; **SAP Endorsed App Premium Certification** — « the only customer-facing voice AI and contact center platform to earn » cette certification.
- **Multilingue** : « any language », section « Languages and Voices », précision de traduction temps réel de 97 % citée pour TUI. **Liste exacte non publiée [NV]**.
- **Conformité** : ISO 27001:2022, ISO 17442:2020, SOC 2 Type 1 et 2, PCI DSS, HIPAA, DORA, **GDPR**. Escalade humaine, détection d'urgence : **[NV]**.
- **Analytique** : « Parloa Lens, Data Hub and Sharing, Conversation Store » ; résultats clients affichés −90 % de charge au standard (Barmenia), NPS +179 %, −60 % de durée d'appel (ATU). Transcription/résumé/sentiment/containment nommés : **[NV]**.
- **Tarifs : aucune information publiée.**

### 1.10 PolyAI — grands comptes

- « Not a chatbot. Not voice bolted onto chat. A full-stack dialog agent », motorisé par **Raven**, « our proprietary model trained on 1B+ enterprise conversations ». — https://poly.ai/
- **Cas d'usage listés** : gestion de compte, **authentification**, **routage d'appel**, facturation & paiements, **réservation**, **FAQ**, gestion de commandes, dépannage ; conversations difficiles « including fraud, outage, triage, multilingual disputes ». Qualification, prise de message, SMS, sortant : **[NV]**.
- **Multilingue — liste exacte publiée, 75+ langues**, dont le **français** : afrikaans, arabe, bengali, cantonais, mandarin, croate, tchèque, danois, néerlandais, anglais, filipino, finnois, **français**, allemand, gujarati, hébreu, hindi, indonésien, italien, japonais, kannada, coréen, malais, malayalam, marathi, norvégien bokmål, persan, polonais, portugais, roumain, russe, serbe, espagnol, suédois, tamoul, télougou, thaï, turc, ukrainien, ourdou, vietnamien, zoulou. — https://poly.ai/languages/
- **Intégrations** : un **ADK** (Agent Development Kit) documenté ; **aucune intégration tierce nommée [NV]**.
- **Analytique** : « Analytics & insights » en fonction cœur ; « PolyAI's Analyst Agents » — poser des questions en langage naturel. Détail : **[NV]**.
- **Tarifs** : pas de grille publique, modèle déclaré — « Ongoing use of the voice agent is priced on a **per-minute basis**, which includes proactive performance improvements, maintenance and 24/7 support ». — https://poly.ai/pricing/

### 1.11 Regal.ai

- Trois familles d'agents : **Phone AI Agents, SMS AI Agents, Chat AI Agents** ; **entrant et sortant** — support et qualification en entrant, recouvrement de créances et prise de rendez-vous en sortant. — https://www.regal.ai/
- **Garde-fous** : **« Safety Layer »** avec « intelligent escalation when needed ». Détection d'urgence, mots-clés, warm vs cold : **[NV]**.
- **Intégrations** : **40+**, « Integrates with all major contact center software » (CCaaS, CRM). Noms précis : **[NV]** (page /platform/ai-agents en 404).
- **Configuration** : **AI Agent Builder no-code**, orchestration **drag-and-drop**. Import de site, knowledge base, scraping GBP : **[NV]**.
- **Multilingue** : **« speak over 30 languages fluently in hundreds of accents »** — nombre annoncé, **liste non publiée [NV]**.
- **Analytique** : « Conversation Intelligence with automated QA », dashboards en direct.
- **Tarifs : aucune grille publique** — « pricing model depends on a few factors specific to your team » ; remise selon engagement et volume. — https://www.regal.ai/pricing

### 1.12 Plateformes d'infrastructure vocale (à distinguer des produits clés en main)

Ce ne sont pas des concurrents directs : ce sont les **briques sur lesquelles nous construirions**. Leur lecture donne le plancher technique et le coût réel à la minute.

**Bland.ai** — builder d'agents **Norm**, « Build production-ready agents with no experience » ; routage et résolution « route, resolve, or book it in one conversation » ; escalade avec contexte ; **omnicanal à mémoire partagée** (Voice, SMS, iMessage, Web Chat, « unified memory ») ; **appels sortants** qualifiant les leads, confirmant les RDV et relançant. Intégrations les plus complètes du panel : **Twilio, Genesys, Five9, NICE CXone, Talkdesk, Amazon Connect, Salesforce, HubSpot, Calendly, Cal.com, Zapier, Make, Pipedream, Slack**. **« 40+ languages natively, with real-time translation available in 23 of them »** (liste exacte **[NV]**). Analytique : « Every call transcribed, scored, and searchable ». Tarifs (https://www.bland.ai/pricing) : Start **0 $** de plateforme + **0,14 $/min** (transferts 0,05 $/min, 100 appels/jour, 10 simultanés, 1 voix, 10 bases de connaissance) · Build **299 $/mois** + **0,12 $/min** (0,04 $/min, 2 000 appels/jour, 50 simultanés, 5 voix, 50 bases) · Enterprise sur devis. LLM + STT + TTS **inclus** — « No token charges. No model-provider pass-throughs. » ⚠️ **Warm transfers, live transfers et guardrails réservés au plan Enterprise.**

**Retell AI** — deux architectures : **Conversation Flow Agent** (« Build a node-by-node call flow with explicit transitions. Best for structured, multi-step, or high-stakes calls ») et **Single Prompt Agent**. **Base de connaissance** : « Attach a knowledge base of **URLs, documents, or text** so the agent retrieves accurate answers instead of relying only on the prompt » — import du site web confirmé. Fonctions natives documentées : transfert d'appel et **transfert vers un autre agent**, **SMS**, prise de RDV via **Calendly et Cal.com**, **post-call analysis** (extraction, catégories, re-run), voix clonées, détection de répondeur/IVR, capture DTMF. Intégrations : **HubSpot, Salesforce, Zendesk, Google Drive, Notion, Calendly, Cal.com**. **Multilingue — liste exacte la plus complète du panel** (55 langues dont le **français**), avec la contrainte officielle : « Every language your agent uses must be supported by **both** a voice (text-to-speech) provider and a speech recognition (ASR) provider ». Agent multilingue : détection automatique parmi les langues sélectionnées, repli sur la première si échec, **mise en garde officielle** — les langues proches sont difficiles à distinguer (cantonais/mandarin), d'où une recommandation d'agents monolingues avec routage. Tarifs : **« True pay as you go »**, 0 $ de plateforme, 10 $ de crédits offerts, **0,07–0,31 $/min** (infra Retell 0,055 $/min ; LLM 0,08–0,16 $/min ; TTS 0,015 $/min ; téléphonie ~0,015 $/min US). — https://docs.retellai.com/build/overview , /build/language-support , /agent/multilingual , https://www.retellai.com/pricing

**Vapi** — orchestration multi-assistants (**« Squads »**, transferts préservant le contexte), base de connaissance, outils connectés aux APIs. **Transfert le plus finement documenté du panel** (https://docs.vapi.ai/call-forwarding) : *blind transfer*, *warm transfer avec message fixe*, *warm transfer avec résumé généré de la conversation*, *warm transfer TwiML*, variantes attendant la parole de l'opérateur, et un mode expérimental de mise en attente avec repli. Multilingue, analyse post-appel, agenda, SMS : **[NV]** sur les pages lues. Tarifs : **0,05 $/min** de plateforme, **0,005 $/msg**, coûts STT/LLM/TTS refacturés **au coût réel** ou gratuits avec vos propres clés ; 10 lignes incluses puis 10 $/ligne/mois ; **HIPAA 2 000 $/mois, Zero Data Retention 1 000 $/mois**.

**Synthflow** — « Automate, manage, and scale thousands of calls from one unified Voice AI Operating System » ; « contextual routing, appointment booking, voicemail detection, and **SMS follow-ups** » ; actions temps réel sur les enregistrements. **200+ intégrations** dont Salesforce, HubSpot, Zapier, Cal.com, GoHighLevel, Cisco, Avaya, Genesys, RingCentral. Configuration : **« visual Flow Designer »** + modèles sectoriels. Garde-fous les plus explicites du panel : « human handoff when needed », **« escalation rules to keep calls on message »**, **« handoff triggers based on failed attempts or sentiment »**. Analytique : « Real-Time Monitoring », **« Auto-QA and monitoring analyze every conversation in real-time »**. Multilingue : annoncé, avec mention explicite d'anglais et espagnol ; liste complète **[NV]**. **Tarifs : la page publique ne présente plus qu'une offre Enterprise — « Enterprise contracts start at $30,000 annually »**, aucun palier libre-service, aucune minute incluse publiée. — https://synthflow.ai/ , https://synthflow.ai/pricing

### 1.13 Produits demandés et **non couverts**

**Air.ai, Voiceflow, Sameday AI, « Belle », Convoso** : **aucune vérification effectuée**, budget de recherche épuisé. Rien n'est affirmé à leur sujet. « Belle » n'a pas pu être identifié comme produit existant — le point d'interrogation reste entier.

### 1.14 Trois faits de synthèse à retenir du volet spécialisé

1. **Trois modèles de facturation incompatibles cohabitent** : à la minute (Rosie, Dialzara, Ruby, PolyAI, plateformes infra), **à l'appel** (Smith.ai), **au client unique** (Goodcall, minutes illimitées), **forfait par site sans compteur** (Slang.ai). Comparer des prix entre eux sans dire lequel est en face n'a aucun sens.
2. **Le français est absent des produits clés en main.** Aucun de Slang, Rosie, Dialzara, Smith.ai, Goodcall ne dépasse le couple **anglais / espagnol** **[V]**. Le français n'est explicitement supporté que sur les **plateformes d'infrastructure** (Retell, PolyAI, listes officielles) et, sans liste publiée, chez Bland (40+), Regal (30+), Parloa (« any language »).
3. **L'import automatique de la fiche Google Business n'est confirmé en page officielle que chez Rosie.** Goodcall le mentionne via des sources tierces **[T]**, tous les autres partent du site web ou d'un questionnaire.


## 2. Marché français et européen

Tout ce qui suit est daté du **13/09/2026**, prix **HT sauf mention contraire**. Deux niveaux de vérification sont distingués à l'intérieur du **[V]** : **[V+]** = page officielle ouverte et lue en texte brut ; **[V]** = page officielle lue et résumée. **[NV]** = absent de la page ou non vérifié.

### 2.1 Grands comptes et centres de contact

#### Zaion (FR) — zaion.ai **[V+]**
- **Produits** : `AI Agents`, `Agent Assist`, `Conversational Insights` ; vocabulaire maison « IA agentique pour l'expérience client ».
- **Agent** : appels entrants et sortants, escalade vers conseiller humain, multicanal natif. **Prise de RDV, SMS, rappel : absents des pages produit [NV]** — ne pas les supposer.
- **Intégrations** : mention générique « CCaaS, CRM, APIs ». **Aucun connecteur nommé.**
- **Configuration** : pas de self-service ; le site vend un dispositif humain — « Chefs de projet, CSM et experts qualité ». Modèle **projet**, pas produit.
- **Langues de l'agent : [NV]** (site en FR/EN/ES).
- **Analytique** : dashboards temps réel, résumés automatiques (« 95 % conformes »), « 100 % des interactions analysées ».
- **Tarif : non public.** **Cible** : assurance, mutuelles, banque (MNH, La Banque Postale, Butagaz). **Hors cible commerce de proximité.**
— https://zaion.ai/ , https://zaion.ai/produit/

#### Diabolocom (FR) — diabolocom.com **[V+]**
- **Produit** : `Intelligent Virtual Agent`, dans une suite IA propriétaire (Transcription, Summary, Voice Analytics, Agent Assist, AQM).
- **Agent** : automatisation des appels entrants, SVI intelligent, routage dynamique via API, scénarios adaptatifs, TTS personnalisé, appels simultanés illimités. Sur question non résolue : redirection humain, ou recherche puis rappel, ou consignation pour analyse. **RDV, SMS sortant : [NV]**.
- **Intégrations** : Salesforce (dont Service Cloud Voice BYOT), Microsoft/Teams, HubSpot, Oracle, Zendesk (Sell + Support), SAP, ServiceNow. **Opérateur télécom certifié**, portabilité de numéro.
- **Configuration** : parcours d'intégration en 5 étapes (analyse du besoin → choix de plateforme → développement et personnalisation, y compris scripts de dialogue et entraînement au vocabulaire de l'entreprise → connexion SI/CRM → tests). La FAQ parle de « low code no code AI » mais **l'entrée reste commerciale**.
- **Langues** : « peut être disponible dans n'importe quelle langue », **aucune liste publiée** — formulation prudente à ne pas surinterpréter.
- **Analytique** : transcription, résumé, Voice Analytics, Automated Quality Monitoring sur 100 % des interactions.
- **Tarif — publié et décisif** : `Voice` **à partir de 60 $/licence nommée/mois**, `Omnichannel` **99 $**, `Ultimate` sur devis. **L'Intelligent Virtual Agent est un add-on payant** sur Voice et Omnichannel, inclus seulement dans Ultimate. Astérisque capitale : *« prix basés sur un engagement de 3 ans pour un minimum de 150 licences nommées »*, facturation à l'usage en sus (minutes, transcription, stockage, SMS). Tarifs « effective as of August 1, 2026 ».
- **Cible** : grands centres de contact. **Le plancher de 150 licences exclut mécaniquement la PME de proximité.**
— https://www.diabolocom.com/pricing/ , https://www.diabolocom.com/artificial-intelligence/virtual-agent/

#### Odigo (FR) — odigo.com **[V+ partiel]**
- Offres segmentées : `Essential : CCaaS pour PME/ETI` · `Enterprise` · `CXaaS : sur mesure`. **Seul CCaaS historique du panel à afficher une ligne PME/ETI en propre.**
- Produits IA affichés : `IA Agentique`, `Automatisation & IA`, `AI Orchestrator` (orchestration de plusieurs bots), voicebots, routage intelligent, résumés automatiques, suggestions de réponse.
- ⚠️ **Plusieurs URL produit IA renvoient un 404** (`/fr-fr/produits-et-services/solution/agents-virtuels-ia/` n'existe pas) ; l'arborescence a bougé. Les descriptions de voicebot lisibles viennent de pages éditoriales, **pas de fiches produit** → capacités **[NV]**.
- **Tarif : non public.** Entrée par démo malgré la ligne PME/ETI.
— https://www.odigo.com/fr-fr/

#### Cognigy (DE, filiale NiCE) — cognigy.com **[V]**
- `Voice AI Agents` : entrants et sortants, NLU, routage vers humain, authentification.
- **Intégrations** : Avaya, AWS Amazon Connect, Genesys, NiCE CXOne, Microsoft, 8x8 ; plus de 1 000 voix (ElevenLabs, Deepgram, Microsoft, AWS).
- **Configuration** : **flow builder low-code** (nœuds Say, Question, Lookup/Case, Hang Up), nécessitant des identifiants de fournisseur vocal (Azure Speech, Google Speech, Amazon Polly), un Voice Gateway Endpoint et un SIP Trunk en production. **Plateforme pour intégrateur, pas formulaire de commerçant.**
- **Langues : plus de 100**, traduction temps réel. **Analytique** : transcription, sentiment, satisfaction, résolution au premier contact. **Tarif : non public.**
— https://www.cognigy.com/solutions/voice-ai-agents , https://docs.cognigy.com/ai/agents/develop/voice

#### VIER (DE) — vier.ai **[V]**
- `VIER Cognitive Voice Gateway`, remplacement de SVI par du dialogue naturel ; chiffres affichés : 65 % des demandes résolues sans humain, 35 % transférées pré-qualifiées, jusqu'à 2 000 requêtes/heure.
- **Configuration** : `VIER AI Studio`, éditeur **low-code** avec simulation d'agents ou d'étapes de process.
- **Intégrations** : boost.ai, ChatGPT, Cognigy, Google Dialogflow, Rasa, Jovo, ubitec, Neohelden ; centres de contact VIER et Genesys ; services vocaux Azure, Google, IBM Watson, Polly, Nuance.
- **Hébergement cloud allemand, RGPD.** Langues de conversation : **[NV]**. **Tarif : non public.**
— https://www.vier.ai/en/intelligence/vier-cognitive-voice-gateway/ , /vier-ai-studio/

#### DialOnce (FR) — dialonce.ai **[V+ partiel]**
- Domaine réel **dialonce.ai** (dial-once.com redirige). Produits : `Agent IA vocal`, `Agent conversationnel`, `SVI Visuel`, `Call back & web call back`, `Suite IA Conseiller`.
- **Agent** : point d'entrée unique multicanal (voix, site, **fiche Google**, SMS, RCS, WhatsApp, QR code, borne), compréhension du motif, qualification, résolution autonome ou transmission au conseiller **avec le contexte**, reprise en livechat « en un geste ». Côté conseiller : réponses recommandées, classification d'e-mails, compte rendu post-appel.
- **Intégrations** : « systèmes CCaaS et CRM », **non nommés [NV]**. Langues, analytique chiffrée, tarif : **[NV] / non public**.
- **Cible** : banques, assurances, habitat social, transports, énergie, services publics, retail, télécom, tourisme ; « plus de 150 entreprises depuis 10 ans ». **Grands comptes.**

#### Yelda (FR) — yelda.ai **[V]**
- **Agent** : RDV et rappels, routage d'intention, FAQ, authentification vocale, « plus de 50 % des appels entrants » traités en autonomie ; omnicanal téléphone, chat, WhatsApp, Messenger, Instagram.
- **Configuration** : plateforme **no-code**, personnalisation de voix, gestion des flux d'appel sans IT, base de connaissance.
- **Langues : 45+ langues et accents régionaux** revendiqués. **Analytique** : transcription temps réel, résumés. **Tarif : non public.**
- **Cible** : banque, hôtellerie, assurance, santé, retail, télécom, public (BNP, Carrefour, Best Western). ⚠️ Yelda est souvent présenté comme « solution PME » dans les comparatifs — **son propre site dit le contraire**.

#### Vocalcom, Kiamo, Easiware — trois nuances importantes **[V]**
- **Vocalcom** (plateforme Hermes, 47 pays) : chatbots et voicebots self-service 24/7, escalade humaine, « Smart Pairing » (routage ML), Salesforce natif. **RDV, SMS, rappel, sortants IA, langues, analytique, tarif : [NV].** — https://www.vocalcom.com/fr/ia-centre-contact/
- **Kiamo** (groupe Foliateam) : **n'édite pas d'agent vocal IA propriétaire**. C'est un **orchestrateur de bots tiers** — connecteurs natifs Dydu, DialOnce, Illuin Technology, Dots, plus API/SDK ; transfert bot→humain avec historique complet. — https://kiamo.com/solution/overview-2/omnichannel/bots.html
- **Easiware** : IA = **easiAI** (basé Mistral AI), **texte uniquement** — classification, résumé multicanal, suggestions de réponse, reformulation, sentiment, traduction temps réel. **Aucun callbot.** Offres segmentées <10 / 11-50 / >50 agents, tarif non public. — https://www.easiware.com/intelligence-artificielle/

#### Fonvirtual (ES) — fonvirtual.com **[V]**
Le seul « établi » du panel dont la fiche produit décrit explicitement la prise de RDV.
- **Agent** : prise de RDV (« connectez votre logiciel de gestion de rendez-vous »), FAQ en langage naturel, prise de message, **transfert humain sur détection d'insatisfaction** + routage par intention, suivi de commande, biométrie vocale. Canaux : téléphone, webchat, WhatsApp, Messenger, appel vidéo avec avatar. **SMS et sortants : [NV]**.
- **Intégrations** : HubSpot, Salesforce, Dynamics, Zoho, Zendesk, logiciels de RDV, bases internes.
- **Configuration** : flux prédéfinis, personnalisation messages/voix/ton, entraînement de la base de connaissance sur les données de l'entreprise, « aucune programmation pour les fonctions de base ». **Import automatique du site web : [NV]**.
- **Langues (page traduction d'appels)** : allemand, arabe, catalan, chinois, espagnol, basque, **français**, galicien, anglais, italien, polonais, portugais, russe, turc, ukrainien.
- **Analytique** : transcription temps réel avec détection de langue, sentiment, intention. `Supervisor`, `Transcription and summary`, `Speech Analytics` **facturés séparément**.
- **Tarif : non public** — « prix déterminé selon les caractéristiques de chaque projet ».
— https://www.fonvirtual.com/en/virtual-agent/ , /en/prices/ , /en/real-time-call-translation/

### 2.2 Téléphonie cloud avec brique agent vocal — le segment qui bouge

#### Ringover — AIRO Voice **[V+]**, le comparable le plus direct avec prix publics

- **Agent** : réponse 24/7, qualification d'intention dès les premières secondes, **prise de RDV avec vérification de disponibilité et réservation du créneau pendant l'appel**, **SMS de confirmation automatique en fin d'appel**, e-mail de suivi (résumé + transcription, conditionnable à des mots-clés), mise à jour de fiche client, création de tickets et workflows, transfert vers le bon agent **avec conservation du contexte**.
- ⚠️ **Contradiction sur leur propre page** : le bloc fonctionnalités donne la prise de RDV pour acquise, mais la FAQ de la **même page** écrit « la **pré**-prise de rendez-vous (**bientôt disponible**) ». À faire trancher en démo avant toute promesse comparative.
- **Sortants : explicitement non** — « Airo se concentre sur les appels entrants. Les cas d'usage sortants (relances, rappels, campagnes) sont prévus sur la feuille de route. »
- **Intégrations** : Salesforce, HubSpot, Zoho, Zendesk, Odoo, Pipedrive, « +100 intégrations ».
- **Configuration** : « activée en quelques clics, très peu de ressources techniques » ; personnalisation voix/ton/accueil, import de sa propre voix.
- **Langues** : « anglais, français, espagnol, italien, portugais et bien d'autres ».
- **Garde-fous** : sur question sans réponse, transfert automatique à l'agent humain approprié avec le contexte capturé.
- **Tarif AIRO, entièrement public sur ringover.fr** : **60 minutes offertes/mois** ; à la consommation **0,39 €/min sans engagement** ; forfaits `Starter` 300 min **99 €/mois** (0,33 €/min) · `Growth` 1 000 min **290 €** (0,29) · `Scale` 2 000 min **500 €** (0,25) · `Business` 5 000 min **1 100 €** (0,22) · `Enterprise` 10 000 min **1 900 €** (0,19). Au-delà du forfait, retour au tarif à la consommation. Aucun frais d'activation.
- **Socle téléphonie** : `TALK` **20 €/utilisateur/mois** (annuel) ou 29 € (mensuel), **3 utilisateurs minimum, engagement 12 mois** — TALK inclut déjà transcription, résumé et un « Réceptionniste virtuel AI ». `BUSINESS` 47 € (annuel) / 57 €. `ADVANCED` sur mesure. Add-ons IA : Empower, Assistant IA Target First **99 €/site/mois**, CRM Autofill **5 €/licence/mois**.
- **Cible** : équipes ventes/support/service, 14 000 entreprises. **Le minimum de 3 utilisateurs place l'entrée au-dessus du commerçant seul.**
— https://www.ringover.fr/agent-vocal-ia , https://www.ringover.fr/tarifs

> ⚠️ **Écart de devise constaté** : la page `ringover.com/pricing` consultée le 13/09/2026 affiche **TALK $15 / BUSINESS $47 par utilisateur/mois, Empower $39/licence/mois, AI Voice Agent (AIRO) « From $0.19 / minute »** — tandis que `ringover.fr/tarifs` affiche des euros et un plancher AIRO à 0,39 €/min à la consommation. **Ne jamais citer un tarif Ringover sans préciser le site, la devise et la date.**

#### Aircall — AI Voice Agents / AIVA **[V+]**, le plus agressif en prix d'entrée

- **Gamme nommée** : `AI Receptionist`, `AI Sales Agent`, `AI Support Agent`, `AI Order Agent`, plus des `AI Messaging Agents`.
- **Agent** : entrants (résolution de bout en bout, transfert avec contexte complet) ; **appels sortants** (relances prospects, alerte d'échéance de paiement, rappel de RDV, 24/7) ; **SMS et WhatsApp** ; mise à jour CRM ; création de tickets ; **planification de rendez-vous pendant et après l'appel** ; vérification de commande. Gestion des interruptions et des changements de ton.
- **Intégrations** : HubSpot, Salesforce, Zendesk, Shopify, Stripe, **Calendly**, « 250+ intégrations natives » (Zoho, Pipedrive, Monday, Intercom, Gorgias, Help Scout, Bullhorn, Klaviyo, Slack, Zapier).
- **Configuration** : **déploiement en libre-service en quelques minutes**, ou accompagnement par les ingénieurs terrain d'Aircall. Numéros provisionnables dans 100+ pays « en deux clics ». Argument explicite : « pas de trunk SIP, pas de renvoi d'appel, pas de fournisseurs séparés ».
- **Langues : 23**, voix expressives et sélection d'accents, ou voix personnalisée.
- **Analytique** : taux de résolution, score CX, taux de transfert, temps gagné par conversation, sentiments et sujets, **détection automatique des lacunes de contenu et des questions non résolues**. Statistiques unifiées IA + humain.
- **Tarif public en euros pour la France** : **50 minutes offertes par mois sur chaque compte, plus 100 minutes à l'inscription** ; à l'usage **0,49 €/min jusqu'à 2 500 min, puis 0,39 €/min** ; forfaits prépayés **175 € / 500 min par mois** et **725 € / 2 500 min par mois** ; au-delà de 10 000 min, contact. « Pas de contrat, pas de minimum d'usage, annulable à tout moment ».
- **Cible** : segmentation affichée **1-50 / 50-500 / 500+ salariés**, secteurs santé, immobilier, recrutement, services à domicile, retail, voyage ; 23 000 entreprises. **Le seul acteur établi qui descend structurellement jusqu'à la TPE.**
- Chiffres clients affichés : 90 % des appels hors horaires traités automatiquement (SJWD), 87 % résolus sans transfert (TripCity).
— https://aircall.io/fr/products/ai/voice-agent/

> Les montants en dollars relevés ailleurs (500 min pour 175 $, 2 500 pour 725 $, 5 000 pour 1 450 $, 0,015 $ par tentative sortante) proviennent du **blog** Aircall et de comparateurs **[T]** ; la page produit FR donne les mêmes ordres de grandeur **en euros [V+]**. Utiliser la page FR.

#### Callr (FR, Paris) **[V+]**
- `Agents vocaux IA` dans une plateforme CPaaS (Voice API, SMS API, call tracking, trunk SIP).
- **Agent** : qualification et scoring de lead (exemple affiché 88/100), classification d'intention, FAQ depuis la base de connaissance, **prise / déplacement / annulation de RDV dans l'agenda**, création de ticket, mise à jour CRM, webhooks, résumé + transcription + enregistrement envoyés par mail. **Latence annoncée < 1 s (0,7 s moyen)**, gestion du barge-in.
- **Langues : plus de 30**, nativement, « le même agent » sans agent distinct par marché.
- **Différenciant réel** : **modèle au choix du client** — GPT, Claude, Mistral, Llama, Gemini ou stack auto-hébergée. Réseau opérateur en propre, numéros dans 220+ pays.
- **Configuration** : `Callr Actions` = **scénarios d'appel écrits en YAML**, plus API REST. **Orienté développeur / agence.**
- **Tarif public** : `Professional` **599 €/mois** (Voice API, SMS API, numéros, Callr Actions, agent vocal IA, agent SMS IA, messagerie vocale IA, extraction de données d'appel par IA) ; `Enterprise` sur mesure ; sans frais d'installation.
- 2,5 M d'appels/jour, 300+ entreprises ; verticales marketplaces, immobilier, automobile, agences (**offre marque blanche**).
- **Cible** : éditeurs, agences, marketplaces. 599 €/mois **hors de portée du commerce de proximité en direct**, mais pertinent **en marque blanche**.
— https://www.callr.com/fr/solutions/ai-voice-agents/ , https://www.callr.com/fr/pricing/

#### Yeastar — AI Receptionist (P-Series) **[V+]**
- ⚠️ **Correction de périmètre** : Yeastar n'est **pas européen** — copyright officiel *Xiamen Yeastar Digital Technology Co., Ltd.* (Chine), avec numéro ICP chinois. À écarter si la souveraineté compte.
- **Produits** : `AI Assistance` (résumé d'appel et points clés, transcription des messages vocaux et des appels, lecteur neuronal) et `AI Receptionist` (l'agent vocal).
- **Agent** : accueil en langage naturel, **FAQ depuis une base de connaissance personnalisée**, routage intelligent, présence multi-sites, disponibilité hors horaires, **automatisation cross-plateforme** (CRM, planification, gestion de commandes). **Prise de RDV explicite, SMS, sortants : [NV]**.
- **Langues — la liste la plus précise du panel, 34** : arabe, bulgare, chinois, croate, tchèque, danois, néerlandais, anglais, filipino, finnois, **français**, allemand, grec, hindi, hongrois, indonésien, italien, japonais, coréen, malais, norvégien, polonais, portugais (Brésil), roumain, russe, slovaque, espagnol, suédois, tamoul, turc, ukrainien, vietnamien.
- **Analytique** : CDR enrichis d'insights IA par extension, rapports d'appels IA avec **taux de résolution** et engagement, notes et listes d'actions automatiques.
- **Ouverture** : WebSocket et Open API pour brancher ses propres modèles, traduction ou analyse de sentiment tierce.
- Positionnement revendiqué : « AI for SMB support », natif dans le PBX, « zéro plugin, zéro setup complexe ».
- **Tarif : non public** — distribution par **distributeurs et partenaires certifiés**. La page `/ai-receptionist/` renvoie « Page Not Found » ; la fiche vivante est `/solution/ai/`.
- **Cible** : PME **via canal indirect** (intégrateur télécom), pas en vente directe.
— https://www.yeastar.com/solution/ai/

### 2.3 Startups françaises dédiées PME et commerce de proximité

Segment le plus actif, et **le seul où les prix sont systématiquement publics**. Les tarifs ci-dessous ont été relus en texte brut **[V+]** ; les capacités viennent des pages officielles **[V]**.

| Acteur | Entrée | Détail tarifaire |
|---|---|---|
| **Tala** (Lyon) | **29 € HT/mois** | essai 7 j pour 1 € ; Découverte 29 € (50 min, 1 ligne) · Essentiel 99 € (800 min, 3 lignes) · Pro 249 € (2 500 min, 5 lignes) · Temps plein 499 € (9 000 min, 5 lignes) |
| **Sylen** | **49 €/mois** | Start 49 € (100 min) · Pro 129 € (350 min) · Scale 329 € (1 000 min) ; essai 14 j |
| **Elio / Eliocall** | **79 € HT/mois** | 150 min incluses, sans engagement ; installation offerte (valeur annoncée 879 € HT) |
| **Kronos** | **249 €/mois** | offre unique PRO : 1 000 min (**0,15 €/min** au-delà), **100 SMS inclus** (0,15 €/SMS au-delà), 1 numéro dédié, configuration offerte (valeur annoncée 490 €) |
| **Vokai** | **299 € HT/mois** | Starter 299 € (TPE 1-5 sal.) · Pro 499 € (PME 5-30 sal.) · Enterprise sur devis ; **+ 0,29 € HT/minute sur tous les plans** ; « des frais de mise en service peuvent s'appliquer » |
| **AirAgent, Voxibot, OSTIA, Secretar.IA** | — | **tarif non public** |

- **Sylen** — décroché < 2 s 24/7, RDV synchronisé à l'agenda, qualification objet + priorité, **transfert d'urgence vers le personnel humain**, filtrage anti-spam, notifications SMS, résumés, tableau de bord temps réel. **19+ outils de planning** dont Google Calendar, Outlook, Calendly, **Zenchef** (restaurants), Mindbody (bien-être), Cloudbeds (hôtellerie). Activation annoncée en < 10 minutes, hébergement France, RGPD. Langues précises **[NV]**. — https://sylen.ai
- **Tala** — décroché immédiat hors horaires, qualification (besoin, urgence, coordonnées), prise de RDV, message structuré transmis, transfert humain **selon règles de priorité**, rappel avec contexte, **campagnes d'appels sortants**. Google Calendar, Outlook, Calendly ; métier : Immofacile. App mobile avec transcriptions. Configuration : règles d'accueil, scénarios, transferts, base de connaissance. Stack propriétaire (Tala Mind / Voice / Whisper) hébergée en France. Langues **[NV]**. — https://www.tala-assistant.com
- **Vokai** — 24/7/365, RDV, qualification, SAV, relances la veille, **transfert live vers humain avec fiche prospect pré-remplie**, enregistrement et transcription, audit des appels manqués. **50+ connecteurs** : HubSpot, Salesforce, Pipedrive, Google Calendar, Calendly, **Doctolib**, Gmail, WhatsApp Business, Slack, Teams, Shopify, Zapier, Zoom, Mailchimp, Intercom. **Langues : 9** — français (natif), anglais, arabe, espagnol, allemand, italien, portugais, néerlandais, polonais, avec **détection automatique en cours d'appel**. Configuration : déploiement en 24 h après un **appel de configuration**, **agents pré-entraînés par secteur** (vocabulaire auto-école ≠ dentaire ≠ BTP), choix de voix, **test d'appel avant lancement**, portabilité de numéro en 3-10 jours ouvrés. Hébergement UE, RGPD + DPA, « HDS-ready », rétention 90-365 jours. Latence annoncée < 420 ms, uptime 99,97 %. — https://vokai.fr
- **Kronos** — RDV dans l'agenda, qualification du motif, voix personnalisée, **confirmation SMS au prospect**, compte rendu par mail, appels simultanés. **Transfert humain / escalade d'urgence : non mentionné sur la page** — point faible notable pour une cible dépannage. Google Agenda natif puis via **Cal.com** : Outlook, Apple Calendar, Calendly, Notion, HubSpot. Téléphonie par **simple renvoi d'appel opérateur**. Configuration : **appel de 30 minutes avec l'équipe**, mise en service en 24 h, base de connaissance (tarifs, zones d'intervention, horaires), accès aux transcriptions. « Développé par des Artisans, pour des Artisans ». — https://www.allokronos.com
- **Elio / Eliocall** — 24/7, RDV lié à l'agenda, qualification (urgence, type de demande, localisation), transfert humain **avec résumé de contexte**, envoi du résumé par **SMS / WhatsApp / e-mail**. **Langues : français, anglais, espagnol, avec changement de langue en cours d'appel.** Google Calendar, Outlook. ⚠️ **Signal qualité [V+]** : la page publiée contient des **variables de template non rendues** (`{{ fomoDeadline }}`, `{{ lostPerMonth }}`, `{{ calcSecretaryFmt }}`) visibles en clair ; les « +239 pros équipés » et « 4,9/5 » sont **auto-déclarés et non auditables**. — https://eliocall.com
- **AirAgent** — RDV, qualification, transfert intelligent, relances, **appels sortants de prospection**, enregistrement/transcription/analyse. « 3 000+ apps » via Zapier/Make, Google Calendar, Salesforce, HubSpot, Zoho, API/webhooks, **et Planity cité explicitement — le seul du panel à nommer Planity**. Configuration : onboarding guidé, personnalisation nom/mission, scripts, base de connaissance, **configuration par prompt**. Tarif **non public** ; l'argument « −80 % de coûts de secrétariat » est **non vérifiable**. — https://airagent.fr
- **Voxibot** — entrants **et sortants**, transfert conseiller, préqualification (notamment RH), filtrage, **SMS/MMS**, RDV, enregistrement ; NLU propriétaire. Configuration par **logigrammes d'appels** + base de connaissance métier, accompagnée par des « Bot managers » — **pas de self-service**. Tarif **non public** (un « prix par appel » est annoncé sans chiffre). — https://www.voxibot.ai
- **OSTIA** — accueil, collecte motif / urgence / coordonnées / contexte, RDV selon règles configurées, **transfert humain automatique pour les cas sensibles, urgents ou hors scénario** — **le garde-fou le plus explicitement formulé de tout le panel FR** — résumés structurés avec priorité, gestion de messages. Intégrations non nommées, langues et analytique **[NV]**. — https://ostia.fr/secretaire-virtuelle-ia.html
- **Secretar.IA** — verticale **restaurants** ; prise, modification et annulation de réservations 24/7. **Tout le reste est absent de la page** : qualification, transfert, FAQ, SMS, sortants, langues, escalade, analytique, tarif. Intégrations en générique, **sans nommer Zenchef ni TheFork**. **Très early stage.** — https://secretar-ia.fr

### 2.4 Vérifications négatives — à ne pas citer comme concurrents

| Nom | Verdict au 13/09/2026 |
|---|---|
| **Allo-Media** | **N'existe plus sous ce nom.** `allo-media.net` renvoie un **301 permanent vers uh.live**. Le produit est désormais **uh!ive** : Speech-to-Text temps réel (< 250 ms), PRX™, Vocal Cookie™, reconnaissance de 25 types d'entités, anonymisation RGPD, opérateur télécom agréé depuis 2018. **C'est de l'analyse et de la transcription d'appels, pas un agent qui répond au téléphone.** Intégrations SIPREC, MRCP, WebSocket, SFTP, CCaaS, CRM. Clients TotalEnergies, LVMH, Orange, Bouygues, EDF. Tarif non public. — https://uh.live/en/ |
| **Ubicall** | **Mort.** Le site répond mais affiche un copyright **2016**, décrit un routage visuel multicanal sans aucune IA vocale, et son pied de page est **truffé de spam SEO injecté** — signe classique d'un domaine abandonné et compromis. **À écarter.** — https://www.ubicall.com/ |
| **Dring / dring.ai** | **Existe, mais n'est ni français ni européen** : « Founded in Istanbul » (Turquie, hors UE). Agents vocaux santé, hôtellerie, finance, e-commerce, RH ; 32+ langues revendiquées ; onboarding par **formulaire Q&R** puis développement et tests alpha/beta par l'éditeur (modèle de service) ; transfert live vers un autre agent IA ou un humain ; PBX virtuel intégré ou raccordement à l'opérateur existant ; paiement dans l'appel. Tarif **non public**, site en anglais uniquement. — https://dring.ai/ , https://dring.ai/about |
| **Leexi** | **Hors sujet.** Intelligence conversationnelle **post-appel** (transcription, résumés, extraction d'actions). **Ne décroche pas le téléphone** ; intègre au contraire Aircall, Ringover et 3CX. À partir de 20 €/mois, siège Bruxelles. — https://leexi.ai |
| **Kiamo** | N'édite **pas** d'agent vocal propriétaire — orchestrateur de bots tiers. |
| **Easiware** | IA **texte** uniquement, **aucun callbot**. |
| **Mindsay** | **[NV]** — statut (actif / racheté) non confirmé, budget de recherche épuisé. Ne rien affirmer. |

### 2.5 Ce qui ressort du volet FR/EU

1. **Une frontière de prix nette et structurelle.** Diabolocom impose 150 licences nommées sur 3 ans ; Callr démarre à 599 €/mois ; Zaion, Odigo, Yelda, DialOnce, Cognigy, VIER ne publient aucun prix et vendent un projet avec chefs de projet. Face à eux, la nouvelle génération FR publie tout : Tala 29 €, Sylen 49 €, Elio 79 €, Kronos 249 €, Vokai 299 €. **Il n'y a rien entre les deux** — et c'est exactement là que Ringover (99 €) et surtout **Aircall** (175 € / 500 min, 50 min gratuites par mois, sans contrat) sont en train de descendre. **[H]**
2. **Le différenciateur n'est pas la techno, c'est le mode de configuration.** Quatre modèles cohabitent : **formulaire + appel de 30 minutes** (Kronos, Vokai, Dring), **scénarios/logigrammes accompagnés** par un bot manager (Voxibot, Zaion, Diabolocom), **flow builder low-code pour intégrateur** (Cognigy, VIER), **YAML/API pour développeur** (Callr). Le **self-service pur** n'est revendiqué que par Aircall, Sylen et Ringover. **Aucun acteur FR/EU du panel ne propose l'import automatique du site web** pour bâtir la base de connaissance — c'est un manque généralisé, donc un espace. **[V pour les constats, H pour la conclusion]**
3. **Trois angles morts récurrents.** (a) Les **garde-fous d'urgence** ne sont explicitement décrits que par **OSTIA** et **Sylen** ; Kronos, qui vise pourtant le dépannage, n'en mentionne aucun. (b) Les **logiciels métier français** sont quasi absents des listes d'intégration : seuls **Planity (AirAgent)**, **Doctolib (Vokai)**, **Zenchef (Sylen)** et **Immofacile (Tala)** sont nommés — personne ne cite TheFork. (c) Les **listes de langues** sont rarement publiées : seuls Yeastar (34), Callr (30+), Aircall (23), Fonvirtual (15), Vokai (9) et Cognigy (100+) s'engagent par écrit.
4. **Deux points à trancher avant tout comparatif publié.** La page AIRO de Ringover **se contredit** sur la prise de RDV (« disponible » dans les fonctionnalités, « bientôt disponible » dans la FAQ). Et **Ringover ne fait pas d'appels sortants** là où Aircall en fait : sur ce critère les deux ne sont pas comparables.


## 3. Voisins fonctionnels

### 3.1 Logiciels de réservation beauté/bien-être — le terrain direct

C'est le volet décisif : notre produit doit se greffer sur un logiciel de réservation concurrent de Planity. La question n'est pas « les IA vocales existent-elles ? » mais « le logiciel de réservation en a-t-il déjà une, et à quel niveau de finition ? ».

#### Planity — **pas d'offre IA téléphonique** (au 13/09/2026)

- La page produit Planity Pro liste : réservation 24h/7j, agenda synchronisé, liste d'attente automatique, caisse certifiée NF525, TPE WiFi, prépaiement, campagnes SMS, cartes cadeaux, boutique en ligne, Tap to Pay, gestion du temps de travail, site web personnalisé, « SMS de rappel automatiques ». **[V]** — https://info.planity.com/ (13/09/2026)
- **Aucune mention** d'intelligence artificielle, d'agent vocal, de standard téléphonique automatisé ni de traitement des appels manqués sur cette page. **[V]** (même URL)
- La page tarifs officielle affiche trois formules — *Agenda*, *Agenda + Caisse*, *Agenda + Caisse + TPE* (« Le plus populaire »), toutes « sans engagement » — **sans aucun montant en euros**, avec renvoi vers « Échanger avec un conseiller ». Aucune option IA ni téléphonie n'y figure. **[V]** — https://info.planity.com/tarifs (13/09/2026)
- Les montants qui circulent (74 / 94 / 114 € HT par mois ; TPE 20 €/mois + 0,17 € + 0,59 % par paiement ; paiement en ligne 0,17 € + 1,29 %) proviennent de **comparateurs tiers**, pas de Planity. **[T]** — https://clientbase.fr/combien-coute-planity et https://www.lacaisseideale.fr/articles/planity-avis/ (13/09/2026). **À ne pas citer comme tarif officiel.**

> **Lecture [H] :** le leader français du créneau ne vend pas de réponse téléphonique IA et ne publie même pas ses prix. Le canal téléphone reste un angle mort chez lui, alors que les équivalents anglo-saxons (Fresha, Boulevard, Zenoti) l'ont déjà industrialisé. C'est exactement la fenêtre décrite dans le brief.

#### Fresha — **AI Concierge**, le benchmark le plus proche de notre cible

Source unique : https://www.fresha.com/for-business/features/ai-concierge (13/09/2026) **[V]**

- Répond aux **appels entrants** « on behalf of your salon, spa, barbershop, or clinic », décroche « in under two seconds », gère **plusieurs appels simultanés**.
- Répond aussi aux **SMS** : « replies to messages in seconds, handling FAQs, booking queries, and follow-ups ».
- **Réserve et replanifie automatiquement dans l'agenda Fresha**, connecté « to your live Fresha calendar in real time » : il voit services, prix, plannings du personnel, créneaux libres.
- **Annule / déplace** un rendez-vous existant pendant l'appel, « following your business's cancellation and rescheduling policies ».
- **Multilingue** : « can understand and respond in multiple languages », avec **détection automatique de la langue de l'appelant**. (Liste exacte des langues : **[NV]**.)
- **Personnalisation vocale** : choix de la voix, de l'accent, du ton, du nom de l'agent, message d'accueil rédigé par le commerçant.
- **Configuration** : base de connaissance de Q/R à compléter ; « Setup takes minutes, not days » car l'IA lit les données Fresha existantes, « no manual data entry » ; « There is no separate configuration » pour le catalogue de services.
- **Escalade** : transfert en direct vers un membre de l'équipe, ou prise de message détaillé transmis au gérant.
- **Analytique** : chaque appel journalisé avec **transcription complète** ; enregistrement audio **optionnel**, activable dans les réglages.
- **Tarif** : « Only €94.95 per location, per month », en option additionnelle.
- Non mentionné sur la page : tableau de bord analytique au-delà des transcriptions, formulaires d'accueil/consultation, règles d'escalade fines, mesure de satisfaction ou de taux de résolution. **[V]**

#### Boulevard — **Beau**, l'agent intégré nativement

Source : https://www.joinblvd.com/features/ai-receptionist (13/09/2026) **[V]**

- Répond 24/7 pour salons, spas, medspas, barbershops ; **filtre robocalls et spam** ; traite les FAQ (horaires, politique d'annulation) ; capte les informations de prospect pour les medspas.
- **Mise en route** : « To set up AI receptionist, just forward your calls, complete a few simple steps, and you're ready to go. » Les étapes ne sont pas détaillées. **[V]**
- **Base de connaissance implicite** : « built into Boulevard, not bolted on », Beau « already knows your service menu, hours, location info, and policies » — **zéro entraînement initial**.
- **Transfert humain** : formule explicite citée, « Let me transfer you to a member of the team to help with that » ; hors horaires, prise de message.
- **Analytique** : tableau de bord « showing total calls, time saved, and bookings captured », sans détail.
- **Tarif** : « $125/mo per location for 200 minutes, and just $0.60 per minute over that », avec alerte quand le solde de minutes baisse.
- **Multilingue : non mentionné. SMS : non mentionné.** **[V]**
- Par ailleurs Boulevard commercialise **Precision Scheduling™**, un moteur d'optimisation de créneaux (rentabilité, disponibilité du praticien, contrainte de cabine) qui évite les trous d'agenda. **[T]** — https://www.joinblvd.com/guides/ai-appointment-booking (13/09/2026, page éditeur mais de type guide marketing).

#### Zenoti — **AI Receptionist (AIR)**, l'approche « entreprise multi-sites »

Source : https://www.zenoti.com/ai-workforce/ai-receptionist (13/09/2026) **[V]**

- Décroche « during rush hour, lunch, evenings, weekends, and public holidays » ; réserve de bout en bout, y compris **prestations multiples**, en respectant préférences de praticien et plannings.
- **Vente additionnelle** : « Suggests complementary services and active offers on every call answered ».
- **Sortant** : rappelle automatiquement les clients dont le rendez-vous n'est pas confirmé ; propose un report quand le client appelle pour annuler ; **applique automatiquement les frais d'annulation**.
- **Escalade** : « Transfers to a human instantly when a guest requests it or the situation calls for it ».
- **Mise en route** : « You forward calls from your current phone provider to a Zenoti-provisioned AIR number — no migration required. » Pas d'autre détail de configuration.
- **Analytique** : tableau de bord « Revenue booked, calls handled, number of appointments managed, handover rate », enregistrement systématique + résumés, métriques par site.
- **Langues : non indiquées. Tarif : non publié** (demande de démo). **SMS : non mentionné.** **[V]**

> Le **handover rate** (taux de passage à l'humain) affiché comme KPI de premier plan est l'indicateur le plus mûr vu dans tout ce panel. **[H]** C'est la métrique qui rassure vraiment un gérant : « combien de fois ton robot m'a-t-il refilé le bébé ».

#### Phorest — IA oui, **mais pas sur la voix**

Source : https://www.phorest.com/features/ai-features/ (13/09/2026) **[V]**

- Trois produits IA : **Cheat Sheet AI** (résumé de l'historique client avant le rendez-vous, sur mobile), **Front Desk AI** (traite les **SMS et WhatsApp entrants** : réservation, report, rebooking, FAQ parking/horaires/prestations), **Insights AI** (analyse de données en langage naturel, co-développé avec Google, avec « pre-built prompts »).
- **Aucune gestion d'appel téléphonique, aucun agent vocal, rien sur les appels manqués.** **[V]** Aucun tarif affiché pour ces fonctions.
- Conséquence : un écosystème de tiers se branche sur Phorest pour la voix (BookingBee, SalonAgent…). **[T]** — https://bookingbee.ai/phorest-integration-made-simple-with-ai-voice-agent/ (13/09/2026, source éditeur tiers, donc juge et partie).

#### Mangomint — **pas d'agent vocal IA** au catalogue tarifaire

Source : https://www.mangomint.com/pricing/ (13/09/2026) **[V]**

- Base **$120/mo** + **$10 par utilisateur** ; site additionnel **$120/mo**.
- Options : **Phone $70/mo par ligne** (appels et SMS depuis un numéro unique, multi-appareils), Marketing « starting at $30/mo », Payroll « $50/mo + $8 per worker ». Encaissement 2,45 % + 15 ¢ en présentiel, 2,90 % + 30 ¢ à distance.
- **Aucune fonctionnalité de réceptionniste IA téléphonique mentionnée** sur la page tarifs. **[V]** L'option *Phone* est une ligne téléphonique intégrée, pas un agent autonome.

#### Booksy — **pas de réceptionniste IA**, mais une porte d'entrée agentique

- Booksy a annoncé son intégration au **Google AI Mode** de la recherche : l'utilisateur formule « Find me a hair salon for a highlight this Saturday afternoon » et l'IA de Google « automatically match their request to real-time availability and book the appointment directly into the provider's calendar ». Annonce datée du **20 novembre 2025**. **[V]** — https://biz.booksy.com/blog/booksy-google-ai-mode-integration (13/09/2026)
- Aucune page officielle trouvée décrivant un agent téléphonique vocal Booksy. **[NV]** Un tiers l'affirme explicitement (« Booksy doesn't sell an AI receptionist ») mais c'est un blog concurrent. **[T]** — https://www.usecarly.com/blog/booksy-ai/ (13/09/2026)
- Un marché d'agents tiers « intégration Booksy » existe (AgentZap annonce des offres « from $109/month »). **[T]** — https://agentzap.ai/integrations/booksy (13/09/2026, éditeur juge et partie).

#### Treatwell Connect — **pas d'IA vocale**

- La page produit liste : agenda intelligent, remplissage automatique, report/annulation, multi-salons, rappels illimités, réservation 24/7 multicanale, offres heures creuses / dernière minute, demandes d'avis automatiques, formulaires personnalisés, liste d'attente, Tap to Pay, stock, comptabilité de base, plannings d'équipe. **[V]** — https://www.treatwell.fr/partenaires/solutions/logiciel-de-gestion/ (13/09/2026)
- **Aucune mention d'IA, d'agent vocal ni de réponse automatique aux appels ou SMS. Aucun tarif affiché.** **[V]**

**Synthèse du volet réservation [V sauf mention] :**

| Logiciel | Agent vocal IA natif | Écrit dans l'agenda | Multilingue | Tarif public de l'option |
|---|---|---|---|---|
| Fresha | **Oui** (AI Concierge, voix + SMS) | Oui, temps réel | Oui, détection auto | **94,95 €/site/mois** |
| Boulevard | **Oui** (Beau) | Oui | Non mentionné | **$125/site/mois, 200 min, $0,60/min au-delà** |
| Zenoti | **Oui** (AIR, + sortant) | Oui | Non indiqué | Non publié |
| Phorest | Non (SMS/WhatsApp seulement) | Oui (via Front Desk AI) | Non indiqué | Non publié |
| Mangomint | Non (ligne tél. à $70/mois) | — | — | — |
| Booksy | Non ; canal Google AI Mode | Oui (via Google) | Non indiqué | — |
| Treatwell | Non | — | — | Non publié |
| **Planity** | **Non** | — | — | **Non publié** |

### 3.2 Standards téléphoniques cloud avec IA

#### RingCentral AI Receptionist (AIR) — le plus documenté publiquement

Sources : https://www.ringcentral.com/ai-receptionist.html et https://www.ringcentral.com/pricing/ai-receptionist.html (13/09/2026) **[V]**

- **Appels 24/7**, routage « by names, locations, and keywords », remise à l'humain avec « caller details and a call summary ».
- **SMS** : réponses automatisées 24/7 aux questions courantes et « frictionless appointment booking directly through text ».
- **Prise de RDV** : « book and reschedule appointments by connecting to your calendar system », présentiel et visio, synchronisation **Google et Outlook**.
- **Multilingue explicite** : « Support multiple languages, including English, Spanish, French, Italian, German, Portuguese », avec **changement de langue en cours de conversation**. — c'est la liste la plus précise et la plus européenne du panel.
- **Configuration** : « No IT support needed. Quickly train AI Receptionist using your **website, FAQs, or uploaded documents** » ; parcours en trois étapes — ajouter le site web, personnaliser l'IA, mettre en ligne.
- **Analytique** : « call volumes, **resolution rates**, routing outcomes, conversational insights, and conversation summaries ».
- **Tarif** : autonome **à partir de 49 $/mois, 100 minutes incluses** ; en option de RingEX **à partir de 39 $/mois, 100 minutes** ; dépassement **0,50 $/minute**, « Call time is rounded up and billed in **30-second increments** » ; essai gratuit 14 jours.

#### Aircall

- Aircall commercialise un **AI Voice Agent** traitant les appels de routine en autonomie (FAQ, planification, journalisation CRM) avant passage à l'humain. **[T]** — https://aircall.io/blog/best-practices/ai-voice-agent-cost/ (13/09/2026 ; page éditeur mais de blog, pas page produit).
- Tarification rapportée : 50 minutes gratuites/mois, puis bundles (500 min pour 175 $, 2 500 min pour 725 $, 5 000 min pour 1 450 $) ou 0,49 $/min jusqu'à 2 500 min et 0,39 $/min au-delà, plus 0,015 $ par tentative d'appel sortant hors bundle. **[T]** (même source, reprise par des comparateurs) — **non confirmé sur une page tarifs officielle : à revérifier avant toute citation client.**

#### Ringover et Aircall

Traités en détail au **§2.2** (pages officielles françaises, tarifs publics en euros). Rappel des deux faits structurants : **Ringover AIRO** annonce la prise de RDV mais **se contredit** dans sa propre FAQ (« bientôt disponible ») et **ne fait pas d'appels sortants** ; **Aircall** offre **50 minutes par mois** et facture **0,49 €/min** sans contrat, ce qui en fait l'acteur établi le plus bas en prix d'entrée. **[V+]**

#### 3CX

- **V20 Update 8** (billet daté du 9 février 2026) introduit une **AI Receptionist** traitant les appels entrants sans humain et des **AI Agents** configurables par cas d'usage, capables de parler aux appelants ou de répondre aux chats, de répondre aux questions et de router vers un humain au besoin. **[T]** — https://www.3cx.com/blog/releases/agentic-ai/ (13/09/2026 ; la lecture complète de la page a échoué, contenu tronqué — **détails de configuration, fournisseurs de LLM et coûts : [NV]**).
- **AI Transcription** : résumé automatique de chaque appel significatif et **analyse de sentiment** ; transcription **on-premise / cloud privé** pour les organisations ne pouvant pas confier la voix à un cloud public. **[T]** — https://www.3cx.com/phone-system/ai-transcription/ (13/09/2026).

> **[H]** L'argument 3CX (traitement local des enregistrements) est le seul du panel qui réponde frontalement à l'objection RGPD d'un gérant français. À retenir comme axe défensif.

### 3.3 Cadre réglementaire français et européen — contrainte produit, pas détail juridique

Deux échéances **de 2026** changent le cahier des charges d'un agent vocal en France :

1. **AI Act, article 50 — applicable depuis le 2 août 2026.** L'éditeur d'un agent conversationnel doit avertir explicitement l'utilisateur qu'il interagit avec une IA et non un humain ; pour un agent vocal cela se traduit par une annonce dès les premiers mots (« Bonjour, je suis l'assistant virtuel de [entreprise] »). Les contenus audio générés doivent porter un marquage lisible par machine ; report au 2 décembre 2026 pour les systèmes mis sur le marché avant le 2 août 2026. Sanctions annoncées jusqu'à 15 M€ ou 3 % du CA mondial. **[T]** — https://artificialintelligenceact.eu/transparency-rules-article-50/ et https://itsocial.fr/contenus/actualites/intelligence-artificielle-actualites-contenus/ai-act-les-obligations-de-transparence-de-larticle-50-sont-entrees-en-application/ (13/09/2026). **Le texte officiel de l'article 50 n'a pas été relu ligne à ligne dans cette session : à faire valider juridiquement avant mise en avant commerciale.**
2. **Démarchage téléphonique : consentement préalable obligatoire depuis le 11 août 2026.** Décret publié au Journal officiel le 25 juillet, pris en application de la loi contre les fraudes aux aides publiques : consentement libre, spécifique, éclairé, univoque et révocable, qui ne peut résulter d'une mention pré-rédigée ni d'une reconduction tacite. La prospection téléphonique n'est possible que sur consentement préalable ou dans le cadre d'un contrat en cours. **Bloctel est supprimé.** **[T]** — https://reunion.deets.gouv.fr/Demarchage-telephonique-a-partir-du-11-aout-2026-le-consentement-devient-la (source administration française) et https://www.economie.gouv.fr/entreprises/developper-son-entreprise/innover-et-numeriser-son-entreprise/professionnels-comment-respecter-la-reglementation-sur-le-demarchage (13/09/2026).

**Conséquences produit directes [H] :**
- L'**annonce « je suis un assistant virtuel »** n'est pas une option de style : c'est une obligation. Elle doit être non désactivable, et la formulation doit rester paramétrable (nom du salon).
- Toute fonction d'**appel sortant** (relance de no-show, rappel de liste d'attente, réactivation de clients dormants) doit distinguer **relation contractuelle en cours** (légitime) de **prospection** (interdite sans consentement). Un produit qui vend « l'IA rappelle vos anciens clients » vend un risque juridique à un commerçant français.
- L'enregistrement audio doit être **optionnel et désactivable** (le modèle Fresha — transcription par défaut, enregistrement en option — est le bon défaut).



---

# A. Taxonomie des fonctionnalités en trois niveaux

Classement établi par **fréquence d'occurrence dans les sources officielles lues**. Un item est « table-stakes » s'il apparaît chez la quasi-totalité des produits examinés ; « différenciant » s'il n'apparaît que chez une partie ; « avancé/rare » s'il n'apparaît que chez un ou deux. La classification elle-même est une **lecture d'analyste [H]** ; les occurrences qui la fondent sont **[V]**.

## Niveau 1 — Table-stakes (sans ça, le produit n'existe pas)

| Fonction | Présent chez (vérifié) |
|---|---|
| Décrocher 24/7, y compris heures de pointe, soirs, week-ends, jours fériés | Fresha, Boulevard, Zenoti, RingCentral, Rosie, Goodcall **[V]** |
| Mise en service par **renvoi d'appel**, sans migration de numéro | Zenoti, Boulevard, Goodcall, Rosie, RingCentral **[V]** |
| Répondre aux **FAQ** (horaires, adresse, parking, tarifs, prestations) | Fresha, Boulevard, Zenoti, RingCentral, Rosie, Goodcall **[V]** |
| **Prendre un rendez-vous** dans un agenda réel | Fresha, Boulevard, Zenoti, RingCentral (Google/Outlook), Rosie **[V]** |
| **Transférer à un humain** sur demande ou en cas de blocage | Fresha, Boulevard, Zenoti, RingCentral, Rosie, Goodcall **[V]** |
| **Prendre un message** et le notifier (mail/SMS) | Fresha, Boulevard, Rosie, Goodcall **[V]** |
| **Transcription** de chaque appel | Fresha, Rosie, RingCentral, Zenoti, 3CX **[V/T]** |
| **Résumé** d'appel lisible en dix secondes | Zenoti, RingCentral, Rosie, Slang, 3CX **[V/T]** |
| Traiter **plusieurs appels simultanés** | Fresha **[V]** ; implicite ailleurs **[H]** |
| Message d'accueil et nom d'agent personnalisables | Fresha, Rosie, Goodcall **[V]** |
| **Annonce « vous parlez à une IA »** | Obligation légale UE depuis le 02/08/2026 **[T]** |

## Niveau 2 — Différenciant (présent chez une partie, arbitrage réel)

| Fonction | Qui l'a (vérifié) | Commentaire |
|---|---|---|
| **Annuler / déplacer** un RDV existant pendant l'appel | Fresha, RingCentral, Zenoti **[V]** | Beaucoup savent créer, moins savent modifier |
| Respect des **politiques d'annulation** du commerçant | Fresha **[V]**, Zenoti (frais appliqués automatiquement) **[V]** | Rarement décrit comme objet configurable |
| **SMS pendant ou après l'appel** (lien de réservation, confirmation, suivi) | Fresha, RingCentral, Rosie (liens SMS), Slang (« text links and confirmations ») **[V]** | Souvent la vraie porte de sortie de l'agent |
| **Multilingue avec détection de langue** | Fresha (détection auto) **[V]**, RingCentral (EN/ES/FR/IT/DE/PT, bascule en cours d'appel) **[V]** | Rosie : anglais + espagnol seulement **[V]** ; Slang : espagnol en plan Premium **[V]** |
| **Filtrage du spam et des robocalls** | Rosie **[V]**, Boulevard **[V]** | Sous-estimé : c'est aussi ce qui protège la facture |
| **Transfert chaud** (briefing de l'humain avant passation) | Rosie (« warm transfers », « waterfall transfers » en plan Growth) **[V]**, RingCentral (résumé + détails appelant remis au transfert) **[V]** | Marqueur de sérieux |
| **Vente additionnelle** pendant l'appel | Zenoti **[V]**, Slang (« reservation cross-selling », plan Premium) **[V]** | Argument de revenu, pas de confort |
| **Routage** par nom, service, lieu, mot-clé | RingCentral **[V]**, Goodcall (logic flows) **[V]** | Utile en multi-sites |
| **Alertes par sujet** en temps réel (réclamation, objet perdu, VIP) | Slang **[V]** | Meilleure idée de garde-fou du panel |
| **Taux de résolution** exposé au client | RingCentral (« resolution rates ») **[V]**, Zenoti (« handover rate ») **[V]** | Presque personne ne l'affiche |
| **Écriture en temps réel dans le logiciel métier** (pas via API générique) | Fresha, Boulevard, Zenoti **[V]** | Frontière entre « agent » et « agent intégré » |
| Personnalisation **voix, accent, ton** | Fresha **[V]**, Rosie (10+ voix) **[V]** | Attente de base côté commerçant |
| Tarification **non indexée sur la minute** | Goodcall (« unlimited minutes and tokens », facturation au client unique) **[V]** | Exception notable |
| **Traitement local / cloud privé** de la voix | 3CX **[T]** | Seul argument RGPD frontal trouvé |

## Niveau 3 — Avancé / rare (un ou deux acteurs)

| Fonction | Qui |
|---|---|
| **Appels sortants** de confirmation avant rendez-vous | Zenoti **[V]** |
| **Rétention à l'annulation** : proposer un report quand le client appelle pour annuler | Zenoti **[V]** |
| Application automatique des **frais d'annulation** | Zenoti **[V]** |
| **Mesure de CSAT** directement sur l'appel | Slang (« CSAT measurement » au plan Core ; « only voice platform that directly measures CSAT » — revendication éditeur) **[V/T]** |
| **Optimisation du remplissage d'agenda** (rentabilité, cabine, praticien) | Boulevard, Precision Scheduling™ **[T]** |
| Suggestion d'un **autre établissement du groupe** quand le premier est complet | Slang **[V]** |
| **Analyse de sentiment** sur l'appel | 3CX **[T]** |
| **Canal agentique externe** (réservation depuis l'IA de Google) | Booksy **[V]** |
| Prise de RDV **multi-prestations** avec contraintes de praticien | Zenoti **[V]** |
| **Essai de l'agent avant bascule** du numéro | Dialzara **[T]** |
| **Alertes de consommation** de minutes | Boulevard **[V]** |

**Rares mais existants, à ne pas compter comme inédits** : **escalade d'urgence** — décrite explicitement par **OSTIA** (« transfert humain automatique pour les cas sensibles, urgents ou hors scénario ») et **Sylen** (« transfert d'urgence vers le personnel humain »), et par **Tala** (transfert « selon règles de priorité») **[V]** ; **essai de l'agent avant bascule** — **Vokai** (« test d'appel avant lancement ») et **Dialzara** **[V/T]** ; **agents pré-entraînés par secteur** — **Vokai** (vocabulaire auto-école ≠ dentaire ≠ BTP) et **Slang.ai** (prompts restaurant) **[V]**.

**Absents du panel entier [NV — cherché, non trouvé sur source officielle] :** correction de l'agent en un clic depuis une transcription ratée, apprentissage sur l'historique de rendez-vous, gestion explicite de liste d'attente par l'agent vocal, import automatique du site web chez les acteurs FR/EU, marquage explicite de la conformité AI Act art. 50 comme fonctionnalité.

---

# B. La configuration par le commerçant — analyse de fond

C'est le cœur du sujet. Un gérant de salon n'écrira jamais un prompt. La question est : **par quel artefact le produit remplace-t-il le prompt ?** Le panel étudié fait apparaître **six patrons distincts**, du plus artisanal au plus abouti.

## B.1 Les six patrons observés

### Patron 1 — « Aspire une source publique et pré-remplis » (site web / fiche Google Business)

Le plus répandu chez les acteurs SMB.

- **Rosie** : étape 1 de l'onboarding = « **Add your site or Google Business Profile to train Rosie** » ; le système apprend seul horaires, prestations et informations de base. Étape 2 : relire et corriger (FAQ, message d'accueil, filtrage du spam). Étape 3 : rediriger les appels. « No developer skills », « takes minutes ». **[V]** — https://heyrosie.com/ (13/09/2026)
- **RingCentral AIR** : « Quickly train AI Receptionist using your **website, FAQs, or uploaded documents** », parcours en trois écrans (ajouter le site → personnaliser → publier). **[V]** — https://www.ringcentral.com/ai-receptionist.html (13/09/2026)
- **Goodcall** : « You connect your Google Business Profile or website, the AI learns your business info, you customize greetings and logic flows, and you're live », ~15-20 minutes, sans code. **[T]** — https://www.goodcall.com/how-it-works tel que restitué par la recherche ; la lecture directe de la page mentionne « connect your CRM, calendar, and knowledge base » mais **ne cite pas explicitement Google Business Profile** : la mention GBP reste **[T]**, pas **[V]** (13/09/2026).

**Limite documentée du patron 1**, et c'est une critique importante : quand un appelant pose une question sur un tarif ou une disponibilité que le site ne couvre pas, Rosie « either approximates from site content or defaults to taking a message » ; les entreprises dont le savoir vit dans la tête du patron « will need to update their website content to effectively train Rosie ». **[T]** — https://serviceagent.ai/blogs/rosie-ai-pricing/ (13/09/2026, blog concurrent : à considérer comme un signal, pas une preuve).

> **[H]** Le scraping du site est un **accélérateur d'amorçage**, pas une base de connaissance. Le savoir qui compte dans un salon — « on ne fait pas de balayage sur cheveux décolorés le samedi », « la coloriste ne travaille pas le lundi », « une permanente ça bloque deux heures » — n'est écrit nulle part sur le site.

### Patron 2 — « Le questionnaire guidé, pré-rempli par métier »

C'est le patron le plus intéressant pour nous.

- **Slang.ai** : le tableau de bord livré contient **des questions pré-programmées selon le type de restaurant**, que le commerçant parcourt **avec un onboarding manager pendant un appel de 30 minutes** pour valider le traitement de chacune. Mise en service « less than 30 minutes », en ligne le jour même. **[T]** — https://backofhouse.io/resources/ai-phone-answering-software-slang-restaurants (13/09/2026, média sectoriel) ; la page produit officielle confirme seulement « Setting up Slang AI typically requires less than 30 minutes » **[V]** — https://www.slang.ai/ (13/09/2026).
- **Dialzara** : « Most businesses are live in about 15 minutes by **answering onboarding questions**, importing website content or docs for knowledge, testing via chat or phone, then forwarding your number. » Chaque page sectorielle du site embarque un **prompt de départ**, une liste de « common questions callers ask », des règles de routage recommandées et un plan de base de connaissance (prestations, horaires, moyens de paiement, FAQ) — soit **88+ modèles sectoriels** que l'utilisateur adapte. **[T]** — https://dialzara.com/ et https://dialzara.com/faqs tels que restitués par la recherche ; le décompte « 88+ » vient d'une synthèse tierce et **n'a pas été vérifié en page officielle [NV]** (13/09/2026).

> **[H]** Slang et Dialzara illustrent les deux extrêmes du même patron : **questionnaire + humain au téléphone** (Slang, haut de gamme, 399-599 $/site/mois) contre **questionnaire + gabarit sectoriel en libre-service** (Dialzara, bas de gamme). Le premier vend du temps humain, le second vend un formulaire. **Le créneau vide est au milieu : un questionnaire sectoriel assez fin pour ne pas nécessiter d'humain, mais assez guidé pour qu'un coiffeur le finisse seul.**

### Patron 3 — « Zéro configuration : le logiciel métier sait déjà »

Le patron le plus fort structurellement, et celui qui nous concerne directement puisque nous nous greffons sur un logiciel de réservation.

- **Fresha** : « Setup takes minutes, not days » parce que l'IA lit les données Fresha existantes, « **no manual data entry** » ; pour le catalogue de prestations, « **There is no separate configuration** ». L'agent voit en temps réel services, prix, plannings et créneaux. Le commerçant n'ajoute que la **base de Q/R** et l'habillage vocal (voix, accent, ton, nom, message d'accueil). **[V]** — https://www.fresha.com/for-business/features/ai-concierge (13/09/2026)
- **Boulevard / Beau** : « built into Boulevard, not bolted on », Beau « already knows your service menu, hours, location info, and policies ». Mise en route = rediriger les appels + « a few simple steps ». **[V]** — https://www.joinblvd.com/features/ai-receptionist (13/09/2026)
- **Zenoti / AIR** : « You forward calls from your current phone provider to a Zenoti-provisioned AIR number — **no migration required** ». **[V]** — https://www.zenoti.com/ai-workforce/ai-receptionist (13/09/2026)

> **[H] C'est notre position naturelle.** Greffés sur un logiciel de réservation, nous héritons gratuitement de ce que les acteurs génériques (Rosie, Goodcall, Dialzara) doivent arracher au commerçant : catalogue de prestations, durées, tarifs, plannings d'équipe, historique client. La surface de configuration résiduelle se réduit à trois choses : **les règles du salon** (qui fait quoi, quelles contraintes), **les Q/R hors agenda** (parking, accès, moyens de paiement), **la politique d'escalade**. Tout le reste est du vol de données à l'utilisateur.

### Patron 4 — « Les compétences et les flux logiques » (semi-technique)

- **Goodcall** structure la configuration en cinq étapes explicites : 1) *Connect Your Business* (CRM, agenda, base de connaissance) ; 2) *Define AI Skills* — « Tell it how to schedule appointments, answer FAQs, route complex support tickets, or capture new leads » ; 3) *Set Conversation Logic* — règles de routage et options de repli ; 4) *Choose Your Phone Setup* (nouveau numéro ou renvoi) ; 5) *Go Live*. L'escalade est un objet de configuration à part entière : « transfer to a specific person, department, take a message, send a self-service link, or schedule a callback ». Contrôle total du texte, « from the greeting when a call is answered to the goodbye ». Connecteurs via **Zapier, 10 000+ outils**. **[V]** — https://www.goodcall.com/how-it-works (13/09/2026)
- Le **nombre de « logic flows » est le levier de segmentation tarifaire** de Goodcall : 1 flow en Starter (79 $/agent/mois), 3 en Growth (129 $), 25 en Scale (249 $) ; « unlimited minutes and tokens » dans les trois, facturation au **client unique** (100 / 250 / 500 par mois, puis 0,50 $ par client supplémentaire). Remise annuelle de 15 % (66 / 108 / 208 $). **[V]** — https://www.goodcall.com/pricing (13/09/2026)

> **[H]** Goodcall a fait un choix de tarification remarquable : **pas de facturation à la minute**. Le commerçant ne paie pas le temps de parole, il paie le nombre de clients distincts. C'est la réponse la plus directe à la plainte n°1 du marché (facture imprévisible, cf. section C). À copier sérieusement.

### Patron 5 — « L'onboarding fait par un humain de l'éditeur » (white glove)

- **Slang.ai** : équipe d'onboarding qui fait la recherche préalable sur le restaurant, pré-configure, puis anime un appel de 30 minutes. **[T]** (source média sectorielle citée plus haut). Le plan Core inclut « White glove support » et « User-friendly restaurant prompts ». **[V]** — https://www.slang.ai/pricing (13/09/2026)
- **Rosie** : l'onboarding « white-glove » est réservé au plan **Growth à 299 $/mois**. **[V]** — https://heyrosie.com/ (13/09/2026)
- **Smith.ai** : **frais de mise en service de 95 $** pour configurer les « call instructions ». **[T]** — https://contractortoolstack.com/software/smith-ai/ (13/09/2026, blog tiers ; **non confirmé sur la page tarifs officielle [NV]**).

> **[H]** L'onboarding humain est vendu comme un service premium **parce que c'est un coût**. Tout produit qui en dépend plafonne son échelle : à 94,95 €/mois (prix Fresha), un onboarding téléphonique de 30 minutes mange plusieurs mois de marge. Notre différenciation ne peut pas être « on fait mieux l'appel d'onboarding », elle doit être « **il n'y a pas d'appel d'onboarding** ».

### Patron 6 — « Le gabarit sectoriel comme contenu marketing »

Dialzara publie ses modèles de prompt **sur ses pages sectorielles publiques**, donc lisibles avant achat : gabarit de prompt + questions fréquentes des appelants + règles de routage recommandées + squelette de base de connaissance. **[T]** — https://dialzara.com/ (13/09/2026, tel que restitué ; **pages sectorielles non ouvertes une à une [NV]**).

> **[H]** Double effet : SEO sectoriel massif, et **réduction de l'angoisse d'achat** (le prospect voit le travail déjà fait). Transposable : une page « agent IA pour salon de coiffure » qui montre le questionnaire réel, pas une promesse.

## B.2 Ce que personne ne fait bien (et qui est notre angle)

Constats **[H]**, appuyés sur les vides relevés ci-dessus :

1. **Personne ne construit l'agent à partir de l'historique de rendez-vous.** Tous partent du site web, de la fiche Google ou d'un questionnaire. Or un logiciel de réservation contient la vérité : quelles prestations sont réellement vendues, à quelle durée réelle, par qui, avec quel taux d'annulation, quelles associations de prestations. **Un agent entraîné sur six mois d'agenda sait davantage que n'importe quel questionnaire.** Aucune source officielle du panel ne revendique cela — Fresha revendique la lecture du **catalogue en temps réel**, pas l'apprentissage sur l'**historique**. **[V/NV]**
2. **Personne ne documente une boucle de correction par le commerçant.** Aucune des pages officielles lues ne décrit un mécanisme du type « écoute l'appel raté, corrige la réponse en un clic, l'agent apprend ». Rosie et Fresha exposent des transcriptions ; Boulevard et Zenoti des tableaux de bord. La correction reste un aller-retour manuel dans les réglages. **[NV — cherché, non trouvé]**
3. **Presque personne ne fait tester l'agent avant la mise en ligne.** Deux exceptions : **Dialzara** (« testing via chat or phone » avant le renvoi d'appel, **[T]**) et **Vokai** (« test d'appel avant lancement », **[V]**). Partout ailleurs le gérant met son numéro en jeu sans avoir entendu son agent. **[H]** Un « appelez votre agent pour l'essayer » est une brique de confiance triviale et quasi absente.
4. **Le paramétrage des politiques métier est traité comme du texte libre, pas comme des règles.** Fresha dit « following your business's cancellation and rescheduling policies » **[V]** sans décrire l'objet de configuration. Zenoti va plus loin en appliquant automatiquement les frais d'annulation **[V]**. **[H]** Les règles de salon (délai minimum de report, acompte, prestations réservées à un praticien, temps de pose bloquant) méritent des champs, pas un paragraphe.
5. **L'escalade reste largement binaire** — transfert ou message. Deux exceptions françaises seulement : **OSTIA** (« cas sensibles, urgents ou hors scénario ») et **Sylen** (« transfert d'urgence »), plus **Synthflow** dont les déclencheurs de passation reposent sur « failed attempts **or sentiment** » **[V]**. Chez tous les autres, y compris les logiciels de réservation (Fresha, Boulevard, Zenoti), **aucune détection d'urgence paramétrable n'est documentée [NV]** — seulement le filtrage de spam.

## B.3 Recommandation de conception (recommandation, pas fait)

**[Recommandation]** Un onboarding en quatre écrans, sans une ligne de prompt :

1. **Rien à saisir** — import depuis le logiciel de réservation : prestations, durées, prix, équipe, horaires, historique. Écran de **validation**, pas de saisie (patron 3, poussé au-delà de Fresha par l'usage de l'historique).
2. **Questionnaire sectoriel pré-rempli** — les 15 à 20 questions qu'un client pose réellement à un salon, déjà répondues par défaut à partir des données importées, le gérant ne corrigeant que ce qui cloche (patron 2, sans l'humain du patron 5).
3. **Règles du salon en cases à cocher** — délai de report, acompte, prestations à praticien imposé, créneaux interdits, seuil d'escalade, horaires de transfert (réponse au trou n°4).
4. **Essai avant bascule** — un bouton « appelez votre agent », transcription immédiate, correction en un clic depuis la transcription (réponses aux trous n°2 et n°3).

Plus : annonce IA obligatoire non désactivable (AI Act art. 50), enregistrement audio désactivable, et **tarification non indexée sur la minute** (modèle Goodcall) pour désamorcer la plainte dominante.


---

# C. Trous du marché et plaintes récurrentes

## C.0 Avertissement méthodologique, important

Le corpus d'avis sur ce marché est **pauvre et pollué**. Constats de collecte, tous du 13/09/2026 :

- **G2 et Capterra sont inaccessibles** : HTTP 403 systématique (constaté sur `g2.com/products/slang-ai/reviews` et sur les fiches produit Capterra). **Aucune note G2 ou Capterra n'est rapportée dans ce document.** La valeur « Slang AI 4,4/5, 57 avis sur G2 » qui circule provient d'un blog concurrent (bitebuddy.ai) : **non retenue**.
- **Capterra est de toute façon quasi vide** : la fiche Rosie affiche **0 avis**, « 0.0 » sur tous les critères. **[V]** — https://www.capterra.com/p/10034390/Rosie/
- **Le profil Trustpilot de Rosie est vide et non revendiqué** : « This company hasn't received any reviews yet ». **[V]** — https://www.trustpilot.com/review/heyrosie.com
- **La première page de résultats est saturée de blogs concurrents** (loman.ai, retellai.com, cloudtalk.io, agentzap.ai, serviceagent.ai, usecarly.com, bitebuddy.ai, perfectvenue.com) qui publient des « reviews » de leurs rivaux. Marqué **[T]**, hostile à la cible.
- **Subreddits astroturfés à éviter** : `r/AI_Agent_Reviews`, `r/Best_Ai_Agents`, `r/CloudTalk_Official`, `r/XBert`, `r/XBertAI`, `r/AISEOInsider` publient des comparatifs qui concluent systématiquement en faveur d'un produit. **Ce sont des subreddits de marque, pas des communautés.**
- Même dans les fils authentiques (r/smallbusiness, r/Plumbing), une part notable des réponses vient de **vendeurs qui construisent l'outil**.
- **Fiabilité des verbatim** : 🟢 = texte lu directement (Reddit, extraction HTML), citation fidèle · 🟡 = page Trustpilot lue via un fetcher qui résume — la citation est réelle mais **à revérifier sur la page avant toute publication externe**.

> **[H] C'est en soi un trou de marché** : un acheteur commerçant ne trouve aujourd'hui aucune évaluation indépendante de ces produits. La preuve sociale vérifiable (avis réels, appels témoins écoutables) est un actif marketing rare.

## C.1 Le rejet frontal du bot par l'appelant — plainte n°1, et elle vient des clients finaux

C'est de très loin le thème le mieux documenté, et il traverse tous les secteurs. 🟢

- r/smallbusiness, « Home service owners: Are you guys actually using AI voice receptionists, or do they just piss off older customers? » : « I'm an "older" electrician at 45yo. **100% of my customers in a 2 week period told me they would hang up and call someone else** if I tried it. » · « As a "customer" in my 30s, I can confirm that I would also immediately hang up. » · « I'm 30 and the second I hear a robot on the line I immediately ask to be transferred to a real person - every single time. » — https://www.reddit.com/r/smallbusiness/comments/1ulegrs/home_service_owners_are_you_guys_actually_using/
- r/msp : « My clients would rather shit in their hands and clap, over dealing with an AI receptionist. » · « **We are winning new customers because our competitors have moved to bots.** Customers and users want real people. » — https://www.reddit.com/r/msp/comments/1ida9lo/how_are_ai_receptionists_working_out_for_msps/
- r/restaurantowners : « As a customer, I would immediately hang up and never visit that restaurant. » · « we provide hospitality, why would I put a machine between me and my guests. » — https://www.reddit.com/r/restaurantowners/comments/1w4r5nh/have_anyone_used_ai_phone_answering_system_any/
- r/Barber, seule réponse substantielle du fil : « Its like having a receptionist thats terrible at their job and barely understands english. » — https://www.reddit.com/r/Barber/comments/1vbxrp3/ai_receptionist_stories/

**Contre-point, dans le même fil r/restaurantowners** 🟢 : « We've (regional chain) been using it for over a year now. […] **The average guest simply does not care and the AI hate you see on Reddit is not a reflection of reality.** »

> **[H]** Ces fils sont auto-sélectionnés — les mécontents s'expriment. Mais leur volume et leur constance sur cinq subsections de métier interdisent de les balayer. La conclusion opérationnelle n'est pas « ne pas faire d'IA vocale », c'est **rendre la sortie vers l'humain instantanée et évidente**.

## C.2 Le bot qui se fait passer pour un humain — le vrai déclencheur de colère

Plainte distincte de la précédente, et bien plus actionnable : **ce n'est pas l'IA qui fâche, c'est le déguisement.** 🟢

- r/smallbusiness : « the people it actually pissed off weren't the older customers, it was the 35 year olds who realized mid sentence they'd been talking to a machine with a human name. […] **Complaints basically stopped once we made it announce it was automated in the first breath. People forgive a robot for being a robot, they don't forgive it for pretending.** » — même URL qu'en C.1
- Bruit de call-center factice : « At least then I wouldn't be as annoyed as I am right now about **the fake call center backing track** they played while she didn't answer a single question I needed asked. » — https://www.reddit.com/r/smallbusiness/comments/1vkue0d/a_guy_trolled_my_ai_receptionist_for_90_seconds/
- Dommage commercial réel, plomberie : « I called Pattan plumbing and I am so very angry […] **They said they were contacting dispatch never told me it was an AI** » — le client avait annulé sa journée pour un rendez-vous qui n'existait pas. — C.1, même URL
- Et le rappel juridique, formulé par un utilisateur : « that backing track would put them on **the wrong side of the eu ai act** now, you have to be told you're talking to a machine. »

> **[H] C'est le point le plus important de toute la section C.** L'annonce « je suis un assistant virtuel » est à la fois une obligation légale (§3.3) **et le premier levier de satisfaction**. Les deux vont dans le même sens — rare, et à exploiter comme argument commercial, pas comme contrainte subie.

## C.3 Latence — des chiffres mesurés

🟢 Benchmark ouvert publié sur r/voiceagents : **499 appels réels, 1 883 tours de parole**, même appelant, même opérateur (Plivo), même script. Temps jusqu'au premier octet audio, en ms :

| Plateforme | p50 | p90 | p95 | p99 | tours |
|---|---|---|---|---|---|
| Telnyx | 1302 | 1724 | 1839 | 2164 | 379 |
| ElevenLabs | 1430 | 1686 | 1772 | 2269 | 389 |
| **Bland AI** | 1528 | 2010 | 2273 | 2860 | 389 |
| Vapi | 1562 | 1854 | 2014 | 2677 | 345 |
| **Retell AI** | 1738 | 2096 | 2224 | 2764 | 381 |

Code et configurations publiés : https://github.com/openbenchmarks-labs/voice-agent-latency — https://www.reddit.com/r/voiceagents/comments/1vjdwxj/independent_open_source_benchmark_of_voice_agent/

⚠️ **Biais à signaler** : l'auteur est openbenchmarks-labs, qui écrit lui-même « Our customers are AI agents ». Ce n'est pas un tiers neutre, mais méthodologie et données sont publiques et reproductibles — bien supérieur aux démos vendeurs. **Aucun chiffre pour PolyAI, Parloa, Synthflow, Slang.ai.**

> À mettre en regard des promesses éditeurs : **Callr annonce « < 1 s, 0,7 s moyen »**, **Vokai « < 420 ms »**, **Fresha « picks up in under two seconds »** **[V]**. Le benchmark mesure des p50 de 1,3 à 1,7 s sur les plateformes d'infra. **[H]** Les chiffres annoncés par les éditeurs ne mesurent probablement pas la même chose ; ne jamais les comparer directement.

Confirmation qualitative côté intégrateur 🟢, r/msp : « The biggest issue is going to be **latency** and time to parse the Speech to Text (pray the STT is accurate) » · « I had 2 AI receptionists […] They both sucked and people hated them. But I believe this is **due to latency and understanding** » — https://www.reddit.com/r/msp/comments/1o6i96u/which_voip_vendor_has_the_best_ai_receptionist/

## C.4 Échec hors-script, boucles, transfert raté — « le client s'est retrouvé piégé »

🟢 r/smallbusiness : « The calls that trip bots up are the vague ones, "my furnace is making a noise, is that bad," where a human would ask a couple quick questions and **the bot just flails**. […] What annoys people usually isn't that it's AI, it's when **the AI is a dead end**. » · « The failure mode isn't "AI answered the phone." It's **"the customer got trapped when the call stopped being routine."** »

- Concession Ford : « There i get AI and it cannot help me. **I ask for a representative and it argues with me.** I hang up. 2 hours later I get a text asking to help. I call 13 mile dealer and a receptionist answers […] I am done in under 2 minutes. » — https://www.reddit.com/r/smallbusiness/comments/1pqlni4/who_has_actually_replaced_frontdesk_tasks_with_an/
- Restaurant : « I asked if I could order and it said it couldn't do that. **Then it also wouldn't let me talk to the employees** to let them know their system was down » — C.1, r/restaurantowners

> **[H]** Le KPI à exposer n'est donc pas le taux de containment (que les éditeurs mettent en avant) mais son inverse : **le taux d'impasse** — appels où le client a demandé un humain et ne l'a pas eu. Aucun produit du panel ne le publie.

## C.5 Échec de prise de RDV — « prendre un message ≠ réserver »

🟢 Exploitant d'un service de permanence téléphonique construisant son propre agent, r/smallbusiness : « One of the biggest things I'm seeing with these "ai receptionist" companies is **how misleading they are with scheduling appointments**. Unless they have a complete API integration that is official with whatever scheduling software you use, **the ai agent is guaranteed to cause more pain for you as it will make mistakes all the time and infuriate clients**. The other thing I'm seeing a lot of is the "set it and forget" mentality […] an ai agent needs constant feedback » — https://www.reddit.com/r/smallbusiness/comments/1pqlni4/

🟢 Critère de bascule formulé par plusieurs exploitants : « if it just takes a message its literally no better than a standard answering machine » · « If it just says "someone will call you back," that's when people feel like they got a machine instead of service »

🟢 Seul chiffre de réussite trouvé, **déclaratif et non vérifiable** : « The booking accuracy is like 95% which beats my old receptionist who would double-book me constantly »

**Double réservation** : 🟡 **aucun avis sourcé trouvé mettant en cause un produit d'IA vocale nommé.** Les plaintes de double réservation trouvées concernent les plateformes de booking (§C.9), pas les callbots.

> **[H] C'est la validation directe de notre thèse.** La plainte est mot pour mot : « sans intégration API officielle avec le logiciel de planification, l'agent fera des erreurs en permanence ». C'est exactement ce qu'une greffe native supprime.

## C.6 Accents, noms propres, adresses

Plainte réelle mais **moins bien documentée** — aucun verbatim détaillé avec produit nommé. 🟢

- r/smallbusiness : « man getting the address right when a dog is barking in the background is such a good point. half these bots probably spell the street name wrong anyway and **mess up the whole dispatch** »
- r/Barber : « barely understands english » (C.1)
- r/restaurantowners, sur la précision de commande : « Even at 97% accurate - **if we had an employee who was 97% accurate at taking orders, they would be promoted to cook.** » — https://www.reddit.com/r/restaurantowners/comments/1kmyjyj/as_an_outsider_why_do_most_restaurants_not_use_ai/

Sur **Slang.ai** en particulier (accents régionaux, redirection vers la commande en ligne au lieu de prendre la commande) : les seules sources sont **des blogs concurrents** — **écartées**. Aucun avis primaire sourcé sur ces points.

## C.7 Facturation imprévisible, contrats et résiliation — le thème le plus chargé

### Smith.ai — 🟡 TrustScore **4,4/5**, **371 avis**, **7 % de 1 étoile** — https://www.trustpilot.com/review/smith.ai
- « **the AI receptionist was faulty and would repeatedly ask questions that were already answered** » — Sean Mahbobian, 17/08/2026
- « they charged my account for another month and refused to refund me » — Sean Mahbobian, 17/08/2026
- « **They make it virtually impossible to cancel** » — Sadie Vineyard, 26/06/2026
- « We never set up the system. We never used it for one day... they will tell you it is a long-term contract » — Dean Roberts, 01-02/09/2026
- « customer support is terrible » — Jennifer Gramuglia, 15/02/2026

### Ruby — 🟡 TrustScore **4,5/5**, **850 avis**, **4 % de 1 étoile** — https://www.trustpilot.com/review/www.ruby.com
- « **the company charges you for the dropped calls** to add insult to injury » — Josh Crowfoot, 22/10/2025
- « **They charge by the minute** […] they went ahead and canceled my phone service w/o my knowledge » — Lance, 02/11/2023
- « 30-40% of calls were being dropped or not connecting…up to 5 minutes charges » — mrjazzitup, 07/12/2022
- « they tell you to move your call plan up when you reach your threshold of time. meanwhile **your getting lots of robo calls** » — Tara Melling, 31/07/2026
- « whenever my service with Ruby was active, my business saw a massive spike in spam calls » — Brad Vali, septembre 2026
- « they kept billing me…eventually had to cancel my credit card to stop the recurring payments » — Torie, 03/07/2024

⚠️ **Angle non anticipé et récurrent : la facturation à la minute des spams et robocalls.** L'agent décroche les robocalls, et l'exploitant les paie. **Le filtrage anti-spam est donc une fonction de facturation autant que de confort.**

### RingCentral — 🟡 TrustScore **1,7/5**, **1 987 avis**, **64 % de 1 étoile** — https://www.trustpilot.com/review/ringcentral.com
- « automatically renewed another 2 years…They never mentioned that in the proposal. » — Renee Xu, 09/09/2026
- « It is impossible to cancel…in violation of the FTC 'click to cancel' laws. » — Bradley Gillie, 10/09/2026

### Aircall — 🟡 TrustScore **3,0/5**, **1 084 avis**, **29 % de 1 étoile** — https://www.trustpilot.com/review/aircall.io
- « Absolutely no customer support after the sale. Have logged tickets, started chats & **received no actual response except AI**. » — Melissa Gowen, 30/08/2026
- « The contract feels built to trap and upsell, not to let you leave cleanly. » — Peter Walde, 23/07/2026

### Coût des offres « IA » des opérateurs VoIP 🟢
- r/msp : « We use Zoom for our phone system […] It took almost a full month just to get a basic meeting, and when we finally did, **the quoted price was $2,000 per month. We only have five people in the office.** » — https://www.reddit.com/r/msp/comments/1o6i96u/
- r/restaurantowners, sur RingCentral : « Was looking for a service or different solution that's **not as grifty with the per call fees that are debited daily ALONG with monthly fees**. » — https://www.reddit.com/r/restaurantowners/comments/1t3qe6q/need_help_selecting_ai_answering_service/
- La hausse tarifaire comme levier de migration : « Current company we are using have been **raising prices regularly in part in effort to move people to their AI answering system** »

**Rappel des structures tarifaires qui produisent ces plaintes** : Boulevard 200 min puis **0,60 $/min** · RingCentral 100 min puis **0,50 $/min**, arrondi aux **30 secondes supérieures** · Dialzara 0,35 à 0,48 $/min · Vokai **+0,29 € HT/min sur tous les plans** · Ringover AIRO 0,19 à 0,39 €/min · Aircall 0,39 à 0,49 €/min **[V]**. Seul **Goodcall** échappe au compteur (minutes illimitées, 0,50 $ par client unique au-delà du quota) **[V]**, et **Slang.ai** vend un forfait par établissement sans compteur **[V]**.

## C.8 Verrouillage du numéro, portabilité, intégration téléphonique cassée

🟡 **Ringover** — TrustScore **4,0/5**, **1 081 avis**, **17 % de 1 étoile** — https://www.trustpilot.com/review/ringover.com
- « **They fail to meet their legal obligations and withhold documentation to block number portability.** » — Asier Hernández, 28/05/2026
- « Constant errors and needing customer support. Such as **calls showing as missed but never rang**. » — Jessie, 04/09/2026

🟡 **RingCentral** : « **Can't even port a number correctly.** Terrible. » — Angie McCreight, 27/08/2026 · « I am left with SOS/no normal cellular service…filed a formal complaint with the FCC. » — Sofiia Karabasheva, 01/09/2026

🟢 **Cas Slang.ai documenté — transfert cassé et renvoi de balle entre fournisseurs**, r/3CX : « 3CX is blocking calls returning from Slang.AI. My customer's main line is forwarded to Slang.AI. Call comes in on the main line, **client asks for a rep / hostess / person, then the call is blocked upon return to the 3CX system**. […] **Both companies are pointing fingers at each other and not helping me out.** » Résolution dans le fil : forwarder l'appel via **le numéro émis par Slang** — soit une **dépendance structurelle au numéro du fournisseur**. — https://www.reddit.com/r/3CX/comments/1jm68l7/3cx_slangai/

C'est **le seul retour d'exploitation primaire, technique et daté trouvé sur Slang.ai**.

> **[H]** Le renvoi d'appel est vendu partout comme « aucune migration nécessaire » — mais **le retour de l'appel vers le standard du commerçant est le maillon fragile**, et personne ne le documente. À traiter en priorité côté produit et côté support.

## C.9 Plateformes de réservation métier — notes Trustpilot

⚠️ Ces notes portent sur la **plateforme**, pas sur son module IA, et les avis Fresha/Planity sont massivement **consommateurs**, pas professionnels. Toutes consultées le 13/09/2026.

| Produit | TrustScore | Avis | % 1★ |
|---|---|---|---|
| [Booksy](https://www.trustpilot.com/review/booksy.com) | **3,1/5** | 16 549 | n/d |
| [Fresha](https://www.trustpilot.com/review/fresha.com) | 4,8/5 | 6 980 | 8 % |
| [Planity](https://www.trustpilot.com/review/www.planity.com) | 4,5/5 | 3 550 | n/d |
| [Zenoti](https://www.trustpilot.com/review/zenoti.com) | 4,4/5 | 264 | n/d |
| [Phorest](https://www.trustpilot.com/review/phorest.com) | 4,0/5 | 86 | 22 % |

🟡 **Booksy** — rendez-vous qui bougent seuls, notifications qui ne partent pas : « It doesn't show my scheduled appt, it doesn't text the appt, or alert me about an upcoming appt. » (Sameer Salem, 28/08/2026) · « **A client's appointment date changed unexpectedly**…Booksy repeatedly relied on their audit information and **dismissed the possibility of a technical issue**. » (Sophie, 10/07/2026) · « I cancelled my appointment within the required cancellation period, yet I was still charged the FULL €60 fee. » (JMC, 02/09/2026)

🟡 **Planity** — échec d'authentification bloquant la réservation : « So difficult to make a booking. **Doesn't send me the verification code to my phone number so I can't book.** » (Dan Baronetti, 30/08/2026)

🟡 **Phorest** : « The software does not work well. Many times, **I am unable to login, to make a booking** » (Anna Potter, 08/11/2025)

## C.10 RGPD, confidentialité, responsabilité juridique

Peu de matière, mais trois signaux nets. 🟢

- r/msp, le plus sévère, et il vise le médical : « I've seen quite a few **medical ai receptionist systems, you can't seem to teach these systems to follow privacy regulations. One of these companies openly demonstrated their system violating privacy regulations in their own demos**, so the people producing them don't even care. » — https://www.reddit.com/r/msp/comments/1o6i96u/
- Obligation d'information : « you have to be told you're talking to a machine » (cité en C.2).
- **Responsabilité du donneur d'ordre sur les réponses du bot** : « look up the **Air Canada chatbot court case**. Basically the bot gave a wrong answer, cost the customer money […] The court found that AC was liable for the chatbot's advice and they had to pay. » — jurisprudence **citée par un utilisateur, non vérifiée dans cette session [NV]**. — https://www.reddit.com/r/smallbusiness/comments/1pqlni4/

🟡 **Enregistrement des appels / consentement : aucun avis sourcé trouvé** mettant en cause un produit nommé.

> **[H]** Si la jurisprudence Air Canada se confirme, **le commerçant est responsable de ce que dit son agent** — ce qui fait de la maîtrise des réponses (et de la traçabilité) une exigence contractuelle, pas un confort. À faire vérifier juridiquement.

## C.11 Absence de français — trou de données, pas absence de problème

**Aucun avis sourcé trouvé.** Recherches sur r/france (« agent vocal », « standardiste IA ») et en requêtes françaises sur Reddit : **zéro résultat pertinent**. Les forums pros FR (coiffure, restauration) n'ont pas été atteignables sans moteur de recherche.

Seul signal francophone indirect : Ringover et Planity sont critiqués sur des sujets **non-IA** (portabilité, support, code de vérification SMS). **Il n'existe, dans ce qui a pu être sourcé, aucune plainte documentée sur la qualité du français d'un callbot.** C'est un **trou de données**, à ne pas lire comme une absence de problème.

## C.12 Configuration et maintenance continue — « set it and forget it » ne marche pas

🟢 r/Plumbing : « It works very well **EXCEPT when there is a situation it hasnt been trained on**. […] I've had a couple customers communicate frustration with it after ive shown up. I know its **pretty pricey** » · « a voice agent it still needs maintenance after it goes live. We need to analyze the calls and AI data, and adjust and twitch the prompts as it goes! » — https://www.reddit.com/r/Plumbing/comments/1rxeyf4/has_anyone_tried_an_ai_voice_receptionist/

🟢 r/smallbusiness : « it is IMPERATIVE you find someone who is knowledgeable enough […] because they will break […] **If you are paying a service who has tons of customers, you are NOT going to be able to get a hold of them when you have an issue.** » · « I've spent about a year training an AI chatbot in my CRM […] **it has yet to respond helpfully, so I've given up.** »

🟢 r/restaurantowners, test réel abandonné : « I was a little surprised at the conversational tone the AI was able to achieve, but **it had stumbling points on the most basic stuff**. We would have had to subject customers to many mistakes over time til we got it to learn enough to hopefully be acceptable. **I'm not willing to put my customers through that.** » — https://www.reddit.com/r/restaurantowners/comments/1w4r5nh/

🟢 r/msp, verdict sur les offres IA des opérateurs : « They've all added "AI" but **it's mostly just a nicer auto attendant**. As soon as you try to do anything real like Autotask, ticket creation, or proper triage, you hit limits pretty fast. »

> **[H]** Ceci valide directement le trou identifié en §B.2 n°2 : **la boucle de correction post-lancement n'existe nulle part**, alors que les exploitants la réclament explicitement (« needs constant feedback », « adjust and twitch the prompts as it goes »). Et ils ne veulent pas écrire de prompt : ils veulent corriger un appel raté.

## C.13 Le seul retour d'exploitant positif et nommé

🟢 r/restaurantowners, sur Slang.ai : « We utilized Slang and while **we had a few negative pieces of feedback from some guests**, we saw a significant increase in reservation bookings (**we didn't utilize it for orders of any sort**). It also hugely benefited our private dining team as rather than a host taking a message and then often forgetting to send it » — https://www.reddit.com/r/restaurantowners/comments/1w4r5nh/

Usage **réservation uniquement, jamais commande** — cohérent avec les critiques (non primaires) reprochant à Slang.ai de rediriger vers la commande en ligne.

## C.14 Produits sans aucun avis sourcé

| Produit | Statut |
|---|---|
| **Rosie** | **profil Trustpilot vérifié vide** (« This company hasn't received any reviews yet », non revendiqué) + **0 avis Capterra** |
| **Numa, Goodcall, Dialzara, PolyAI, Parloa, Synthflow, Boulevard, Mangomint** | aucun avis sourcé trouvé |
| **Bland.ai, Retell** | uniquement les chiffres de latence du benchmark (C.3) |
| **Slang.ai** | 2 retours primaires seulement (C.8 r/3CX, C.13 r/restaurantowners), aucune note vérifiable |
| **Smith.ai, Ruby, Aircall, Ringover, RingCentral, Booksy, Fresha, Planity, Phorest, Zenoti** | sourcés ci-dessus (Trustpilot) |

## C.15 Synthèse — les trous du marché

Établis par absence dans les sources officielles lues, confirmés ou nuancés par les avis primaires :

1. **Aucune détection d'urgence paramétrable**, sauf OSTIA et Sylen côté FR et Synthflow (sentiment) **[V]**. Ailleurs, seul le filtrage de spam existe.
2. **Aucune boucle de correction depuis une transcription ratée** — et les exploitants la réclament explicitement (C.12). **[NV]**
3. **Aucun apprentissage sur l'historique de rendez-vous.** Tout le monde part du site web, de la fiche Google ou d'un questionnaire. **[NV]**
4. **Le français est absent des produits intégrés aux logiciels de réservation** ; il existe chez les startups FR, mais aucune n'est greffée sur un logiciel métier beauté. **[V]**
5. **Planity, leader français du créneau, n'a aucune offre** — ni page produit, ni ligne tarifaire. **[V]**
6. **La conformité 2026 n'est traitée comme fonctionnalité par personne** (annonce IA obligatoire, consentement au démarchage), alors que les appelants eux-mêmes en font leur premier grief (C.2). **[NV/T]**
7. **Le maillon « retour de l'appel vers le standard du commerçant » n'est documenté nulle part** et casse en production (cas Slang/3CX). **[V]**
8. **Preuve produit inexistante** : pas d'enregistrement de démonstration écoutable, pas d'essai avant bascule sauf Dialzara et Vokai, pas d'avis indépendants, et deux des plus gros vendeurs SMB (Rosie, Goodcall) n'ont **aucun avis public**.
9. **Le taux d'impasse n'est publié par personne** — seul son inverse flatteur (containment, résolution) l'est.

---

# D. Implications produit (recommandations, pas faits)

Toute cette section est **[Recommandation]**, dérivée des faits ci-dessus.

1. **Notre avantage structurel est le patron 3 (zéro configuration) poussé plus loin que Fresha.** Fresha lit le catalogue en temps réel ; personne ne lit **l'historique**. C'est le seul endroit du marché où une greffe sur un logiciel de réservation peut faire ce qu'un agent générique ne fera jamais.
2. **Ne pas facturer à la minute.** C'est la plainte n°1 des exploitants (§C.7) et Goodcall a démontré qu'on peut vendre autrement. Corollaire : **le filtrage du spam ne doit rien coûter**, sinon le commerçant paie les robocalls — grief récurrent et documenté chez Ruby.
2 bis. **Annoncer l'IA à la première seconde, et le vendre.** Le verbatim le plus net de toute la collecte dit que les plaintes cessent quand le bot se présente comme bot (§C.2). Aucune voix « humaine » déguisée, aucun bruit de call-center factice, aucun prénom humain sans mention. Obligation légale **et** levier de satisfaction.
2 ter. **Rendre la sortie vers l'humain instantanée et inconditionnelle.** La formule « the customer got trapped when the call stopped being routine » (§C.4) décrit le vrai mode d'échec. Un agent qui discute la demande de transfert détruit la relation client.
3. **Le fossé n'est pas « le français », c'est « le français **dans** le logiciel de réservation ».** Les startups FR (Tala 29 €, Sylen 49 €, Elio 79 €, Vokai 299 €) servent déjà le français, mais depuis l'extérieur, sur un agenda générique — elles ne connaissent ni la durée réelle d'un balayage, ni la contrainte de temps de pose, ni le praticien imposé. Les logiciels de réservation qui savent tout cela (Fresha, Boulevard, Zenoti) ne servent pas le français de manière documentée. **Notre position est l'intersection.**
4. **Table-stakes à livrer sans discussion** : décrocher 24/7, renvoi d'appel sans migration de numéro, FAQ, prise de RDV réelle, transfert humain, message notifié, transcription, résumé, appels simultanés, annonce IA obligatoire.
5. **Différenciants à choisir tôt** : annulation/report pendant l'appel, respect des politiques du salon comme **objet configuré** et non comme texte, SMS avec lien de réservation, transfert chaud avec briefing, alertes par sujet, exposition du **taux de résolution** et du **taux de passage à l'humain**.
6. **Deux avancés à fort levier, peu coûteux** : l'**essai de l'agent avant bascule** du numéro, et la **correction en un clic depuis la transcription d'un appel raté** — les exploitants la réclament explicitement (« needs constant feedback », « adjust and twitch the prompts as it goes », §C.12) sans vouloir toucher à un prompt.
6 bis. **Tester le retour d'appel, pas seulement l'aller.** Le cas Slang/3CX (§C.8) montre que le maillon fragile est le renvoi de l'appel **vers** le standard du commerçant, et que les deux fournisseurs se renvoient la balle. À industrialiser et à documenter.
6 ter. **Publier le taux d'impasse**, pas seulement le taux de résolution. Personne ne le fait ; c'est le chiffre que le gérant veut vraiment.
7. **Prudence juridique sur le sortant.** Depuis le 11/08/2026, relancer un ancien client « pour lui proposer un créneau » sans consentement est de la prospection. Les fonctions sortantes doivent être bornées au **contrat en cours** (confirmation, rappel de RDV existant, report après annulation — modèle Zenoti).

---

# E. Ce qui reste à vérifier (dette de recherche)

- **Avis primaires G2 et Capterra** — bloqués (HTTP 403 systématique). Nécessite un relevé manuel en navigateur. **Google Play / App Store : non consultés. Forums pros FR : inatteignables.**
- **Verbatim Trustpilot marqués 🟡** — obtenus via lecture assistée ; à revérifier sur la page avant toute publication externe.
- **Jurisprudence Air Canada** (responsabilité du donneur d'ordre pour les réponses de son chatbot) — citée par un utilisateur, **non vérifiée**.
- **Aircall AI Voice Agent** — tarifs et périmètre lus uniquement via restitution de recherche, **pas via la page tarifs officielle**. À reconfirmer avant toute citation. (Ringover a été reconfirmé en page officielle le 13/09/2026, en USD.)
- **3CX V20 Update 8** — page tronquée au fetch ; configuration, fournisseurs de LLM et coûts inconnus.
- **Curious Thing** — site non lisible par fetch ; rien n'est établi.
- **Air.ai, Voiceflow, Sameday AI, Convoso** — non traités.
- **Textes juridiques** (AI Act art. 50, décret démarchage du 25/07/2026) — lus via sources secondaires, dont une source d'administration française ; à faire valider juridiquement avant usage commercial.
- **Slang.ai** — l'onboarding humain de 30 minutes vient d'un média sectoriel, pas d'une page officielle.
- **Frais de setup Smith.ai (95 $)** — contredit la page officielle « no setup fees » ; à trancher.
