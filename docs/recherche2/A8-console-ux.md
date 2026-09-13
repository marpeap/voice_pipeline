# A8 — La console de l'agent vocal : recherche UX et spécification d'interface

> État **septembre 2026**. Toutes les consultations : **2026-09-13 / 2026-09-14**.
> Doctrine appliquée : **Règles Barthez** (`/home/marpeap/_vault/12-Processus/Regles-Barthez.md`, lu en entier le 2026-09-13). Chaque arbitrage d'interface cite la loi qui le tranche.
> Contexte produit imposé : `docs/01-CONCEPT-PRODUIT.md` §3, §4, §8 — **le commerçant ne voit jamais un prompt**, sous aucune forme « avancée ». KPI affichés : taux de confirmation orpheline (cible 0), taux d'impasse, taux de passage à l'humain, silence perçu en percentiles.

## Convention de marquage

| Marque | Sens |
|---|---|
| **[F]** | Fait vérifié dans une documentation officielle ou une source primaire, URL + date données |
| **[H]** | Hypothèse de conception, dérivée de faits marqués, assumée comme telle |
| **[R]** | Source secondaire ou page marketing de l'éditeur — non vérifiée dans un centre d'aide |
| **[NV]** | Non vérifié : page inaccessible ou information non trouvée |

## Note de méthode — ce qui a résisté

Le budget `WebSearch` de la session était **épuisé (200/200)** avant le premier appel, et le récupérateur de pages interne refuse la vérification de domaine sur `nngroup.com`, `intercom.com`, `support.zendesk.com`, `docs.vapi.ai`, `docs.retellai.com`, `docs.langchain.com` (« Unable to verify if domain … is safe to fetch »). Deux voies de contournement ont été ouvertes et sont celles qui ont produit la quasi-totalité du §2 :

1. **`curl` direct depuis le shell** + extracteur HTML→texte maison (`scratchpad/f.py`) — passe partout où le récupérateur interne échoue ;
2. **recherche via `https://html.duckduckgo.com/html/?q=…`** en `curl` — la seule surface de recherche qui réponde (Bing renvoie du bruit géolocalisé, DuckDuckGo et Mojeek en navigateur réel opposent un captcha) ;
3. **API publique des centres d'aide Zendesk** (`/api/v2/help_center/articles/search.json`) — permet de retrouver un article sans moteur de recherche.

Sont restés hors d'atteinte malgré plusieurs tentatives : **toutes les pages Apple Developer / HIG** (SPA React, seul le `<title>` revient), **`dl.acm.org` et ResearchGate**, et le détail visuel des consoles verticales (Fresha, Zenoti, Boulevard, RingCentral) dont seules les pages marketing ont répondu → **[R]** partout où c'est le cas, jamais **[F]**.

---

# 1. Inventaire d'écrans

## 1.1 Le postulat d'usage

Le gérant est **debout, au bac ou à la caisse, une main occupée, entre deux clients**. Deux conséquences dures, et non négociables :

- **Tout ce qui compte doit être atteignable au pouce d'une seule main.** Hoober mesure que **49 %** des gens tiennent leur téléphone à une main et **75 %** agissent au pouce (`Regles-Barthez` §B3, source [alistapart.com](https://alistapart.com/article/how-we-hold-our-gadgets/)) **[F, via doctrine]**.
- **Toute tâche doit survivre à une interruption de trente secondes.** Le concept produit a déjà tranché la conséquence côté questionnaire : *« sauvegarde serveur après chaque réponse, pas à la fin »* (`01-CONCEPT-PRODUIT` §4). La même règle vaut pour la correction : **une correction commencée et abandonnée ne doit jamais être perdue ni appliquée à moitié** **[H]**.

## 1.2 Navigation principale — quatre entrées, pas plus

**B4 (Miller, 4±1 — jamais 7)** plafonne la barre de navigation. Quatre onglets :

| # | Onglet | Ce qu'on y fait | Position sérielle (B7) |
|---|---|---|---|
| 1 | **Aujourd'hui** | Ce qui s'est passé depuis ce matin, et ce qui demande une action | Position 1 — le plus consulté |
| 2 | **Appels** | Le journal complet, filtrable | milieu |
| 3 | **Agent** | Ce que l'agent sait, ce qu'il a appris, ce qu'il ne sait pas encore | milieu |
| 4 | **Réglages** | Horaires, règles de la maison, numéro, notifications, facture | Position n — rare mais structurant |

Pas d'onglet « Analytique » : les KPI vivent dans **Aujourd'hui** (les trois qui comptent) et dans **Agent** (les tendances). Un cinquième onglet violerait B4 sans rien ajouter que ces deux écrans ne portent déjà **[H]**.

## 1.3 Les onze écrans

| Code | Écran | Action primaire (une seule — B2) | État vide (B9) |
|---|---|---|---|
| **E0** | **Aujourd'hui** | Ouvrir le premier appel qui demande quelque chose | « Rien à revoir. L'agent a pris 4 rendez-vous. » + lien vers le journal |
| **E1** | **Journal des appels** | Ouvrir un appel | « Aucun appel aujourd'hui. Voir hier. » |
| **E2** | **Revue d'appel** | **Corriger** | (jamais vide) |
| **E3** | **Feuille de correction** (surcouche de E2) | Appliquer la correction | (jamais vide) |
| **E4** | **Ce que l'agent a appris** (registre des corrections) | Suspendre / rétablir une correction | « L'agent n'a rien appris de particulier. C'est normal au début. » + lien vers le dernier appel |
| **E5** | **Appel en cours** | Prendre la main | « Aucun appel en ce moment. » |
| **E6** | **Règles de la maison** | Enregistrer le bloc modifié | (jamais vide) |
| **E7** | **Questionnaire** (paliers 0→4, déjà spécifié `01-CONCEPT` §4) | Répondre à la question affichée | — |
| **E8** | **Santé de l'agent** (KPI) | Ouvrir la liste d'appels derrière le chiffre | « Pas encore assez d'appels pour un chiffre honnête. » |
| **E9** | **Alertes** (quoi notifier, où) | Enregistrer | — |
| **E10** | **Numéro et renvoi d'appel** | Copier le code de renvoi | — |
| **E11** | **Facture et quota** | — (écran de lecture) | — |

### E0 — Aujourd'hui

Trois zones, dans cet ordre (**B7** : l'essentiel en position 1 et n) :

1. **Une ligne de verdict.** « 7 appels · 4 rendez-vous pris · 1 à revoir ». Le « 1 à revoir » est **la seule emphase forte de l'écran** (**B6** : une par vue), et il est doublé d'un mot, jamais de la seule couleur.
2. **La pile à revoir** — au plus 5 éléments (**B4**), chacun une carte : motif de l'alerte en micro-label, une phrase de contexte, l'heure. Au-delà de 5 : « voir les 12 autres ».
3. **Le bouton primaire, en zone de pouce** : *Revoir le premier*. Un seul aplat `--electric` sur l'écran (**B6**, DA §2.6).

Ce que E0 **n'affiche pas** : aucun pourcentage abstrait, aucun graphique. Le graphique est dans E8, sur décision de l'utilisateur.

### E8 — Santé : les quatre chiffres, et comment ils s'énoncent

Les KPI imposés par le concept sont des chiffres de spécialiste. Ils doivent être **traduits sans être édulcorés** — B8 (Tesler) : c'est le produit qui absorbe la complexité, pas le commerçant.

| KPI interne | Ce que l'écran affiche | Règle d'affichage |
|---|---|---|
| **Taux de confirmation orpheline** (cible 0) | « **Rendez-vous promis et jamais enregistrés : 0** » | Toute valeur > 0 est un **incident**, pas une statistique (`00-SYNTHESE` L84) : bandeau, notification immédiate, et le chiffre passe en tête de E0 |
| **Taux d'impasse** | « Ont demandé quelqu'un et ne l'ont pas eu : **2 appels** » — en **nombre**, pas en pourcentage | Un pourcentage sur 7 appels ne veut rien dire ; le nombre absolu est honnête à tout volume **[H]** |
| **Taux de passage à l'humain** | « Passés à vous : 3 sur 7 » + répartition par motif (≤ 5 motifs, B4) | Le *handover rate* est l'indicateur le plus mûr du panel (`01-CONCEPT` §8) |
| **Silence perçu p50 / p95** | « Temps de réponse : **1,4 s** d'habitude, **2,9 s** au pire » | Jamais de moyenne. Le concept refuse explicitement « toute latence annoncée en moyenne » (§8) |

Chaque chiffre est **cliquable et mène à la liste d'appels qui le compose**. Un KPI qu'on ne peut pas ouvrir est un KPI qu'on ne peut pas corriger — et c'est précisément le patron que Fin applique à sa guidance : *« Drill into the metrics to view a list of conversations where the guidance was used »* (**[F]** [fin.ai/help/en/articles/13975768](https://fin.ai/help/en/articles/13975768-provide-fin-ai-agent-with-specific-guidance), 2026-09-14).

---

# 2. La boucle de correction — le cœur

## 2.1 Ce que le marché fait, et où il s'arrête

### 2.1.1 Intercom Fin — l'état de l'art de la règle explicite

**Fin Guidance** est le mécanisme le plus abouti observé. Faits vérifiés (**[F]**, [fin.ai/help/en/articles/13975768-provide-fin-ai-agent-with-specific-guidance](https://fin.ai/help/en/articles/13975768-provide-fin-ai-agent-with-specific-guidance), consulté 2026-09-14) :

- **Cinq catégories fermées** de guidance : *Communication style*, *Context and clarification*, *Content and sources*, *Spam*, *Other*. « To ensure guidance works effectively, make sure it is assigned to the correct category. »
- **Un titre est obligatoire** : « You must enter a value in the title field before you can save your guidance. The Save button will remain disabled until a title is provided. »
- **Plafonds durs** : « Up to 1,000 pieces of guidance are allowed per workspace. Each guidance can be up to 2500 characters in length. »
- **Un correcteur de règles** (*Optimize*) qui relit la règle écrite et signale quatre défauts : **ambiguïté, redondance, contradiction, clarté** — plus les « system limitations », c'est-à-dire les instructions demandant une action que Fin ne peut pas faire.
- **Portée par audience** : une règle peut être limitée à un segment ; « Audience targeting completely hides non-matching guidance from Fin ».
- **Aperçu avant activation** : « You do not need to click Save or Enable to test your guidance in preview ». Puis **Save** puis **Enable** — deux gestes distincts.
- **Mesure d'impact par règle** : combien de fois elle a été appliquée, et quel pourcentage de ces conversations a été résolu ou routé vers l'équipe.
- **Historique de version avec retour arrière et notes** : « View a previous version », « Roll back », « Add notes ». Limite documentée : « Changes made to paused Guidance are not shown in version history, as only live versions are tracked. »
- **Aveu capital sur la fiabilité** : « Guidance is applied on a per-turn basis. On each turn, Fin evaluates which rules are contextually relevant and selects those to apply — **even a live, correctly configured rule may not be selected if the conversation context doesn't surface it. This is an inherent characteristic of how guidance works, not a configuration error.** »

→ **Conséquence directe pour nous** : une règle exprimée en langue naturelle et sélectionnée par le modèle **n'est pas déterministe**. Intercom le dit lui-même et renvoie vers l'audience (une règle *dure*, hors modèle) quand le comportement doit être garanti. Notre produit, qui promet un taux de confirmation orpheline nul, ne peut donc pas faire reposer ses corrections critiques sur du texte injecté : **les corrections qui touchent l'agenda, l'escalade ou l'écriture doivent être des contraintes évaluées côté serveur, hors du modèle** **[H, dérivé d'un fait]**.

**Les états du cycle de publication chez Fin** (Procedures) sont directement réutilisables (**[F]**, [fin.ai/help/en/articles/14324571-manage-procedure-versions-and-publishing](https://fin.ai/help/en/articles/14324571-manage-procedure-versions-and-publishing), 2026-09-14) :

| État | Sens |
|---|---|
| *Unsaved changes* | « exist only in your browser and will be lost if you navigate away » |
| *Draft* | enregistré, « Fin is not using them yet » |
| *Live* | « active and used by Fin in real customer conversations » |
| *Live with draft* | en vigueur, avec une modification enregistrée non publiée |
| *Paused* / *Paused with draft* | retirée du service, brouillon préservé |

Plus : le retour arrière **ne remet pas en service** (« rolling back creates a new draft. It won't go live until you click Set live ») ; la note de version est **obligatoirement de 50 à 500 caractères** ; « version history only records versions that have been set live ».

### 2.1.2 Intercom Fin — la boucle « cas raté → modification durable »

C'est **Analyze > Optimize** (**[F]**, [fin.ai/help/en/articles/13975989-use-ai-powered-content-recommendations-to-improve-fin](https://fin.ai/help/en/articles/13975989-use-ai-powered-content-recommendations-to-improve-fin), 2026-09-14) :

- Les recommandations sont produites en **comparant les réponses ratées de Fin aux réponses humaines réussies** sur des questions similaires : « Failed Fin responses (e.g. escalations or poor-quality replies) and comparing them to successful human replies to similar questions ».
- Chaque recommandation porte : **score d'impact, résumé explicatif, date, conversations sources, contenu lié, actions à faire**. Un tiroir latéral montre « the conversations that directly informed a recommendation ».
- Actions possibles : **accepter / rejeter / éditer avant d'accepter / marquer comme fait**, avec **diff en rouge (suppressions) et vert (ajouts)**.
- Approbation explicite : « Nothing goes live without your explicit approval first ».
- Quatre types : ajouter du contenu, éditer du contenu, **arbitrer une contradiction**, **arbitrer un doublon**.
- **La limite décisive, écrite noir sur blanc** : « **No option to fast-track or manually flag individual conversations for recommendations.** » Et : « Suggestions are only generated for conversations that have an AI topic assigned » ; « Low-volume customers (with fewer conversations) may receive fewer or no recommendations ».

→ **C'est exactement le trou de marché du produit.** Fin corrige **par agrégat statistique**, sur des seuils de volume (« Regular queries (1+ a day) on the same topic for at least 7 days »). Un salon de coiffure fait **quelques dizaines d'appels par jour** : il n'atteindra jamais ces seuils. Il a un appel raté, hier, qu'il veut corriger **maintenant**. Le geste « depuis **ce** cas » n'existe nulle part — ni chez Intercom, qui le refuse explicitement, ni chez Zendesk, dont toute la machinerie est également agrégée.

### 2.1.3 Zendesk — même architecture, même plafond de volume

**[F]**, [support.zendesk.com/hc/en-us/articles/9877546283930](https://support.zendesk.com/hc/en-us/articles/9877546283930-Viewing-and-using-the-automation-potential-report-to-create-or-enhance-AI-agents) (2026-09-14) : le *rapport de potentiel d'automatisation* classe les sujets en **« Covered by knowledge » / « Knowledge gaps »**, marque chaque catégorie **high / medium / low impact**, montre des tickets d'exemple qu'on peut ouvrir « to confirm that the topic and the conversation in the ticket match », et propose un bouton **« Generate article draft »** qui ouvre l'éditeur avec un brouillon construit sur **90 jours** de données de tickets. Le rapport n'existe pas si « your account … has fewer than 90 days of data, or doesn't have enough relevant ticket data in the last 90 days ».

**Knowledge copilot (EAP)** (**[F]**, [support.zendesk.com/hc/en-us/articles/10799529609498](https://support.zendesk.com/hc/en-us/articles/10799529609498-Using-knowledge-copilot-to-generate-and-maintain-your-knowledge-base-EAP), 2026-09-14) ajoute trois indicateurs de santé, rafraîchis **chaque semaine** : **Coverage** (part des problèmes courants couverts), **Freshness** (articles non mis à jour depuis six mois → score baissé), **AI readability** (formatage exploitable par un modèle). Et la même garantie de contrôle : « Knowledge copilot doesn't automatically create or publish content to your help center; you remain in full control. »

→ **Le patron commun Fin / Zendesk** : *santé du corpus → recommandation classée par impact → cas sources consultables → diff → accepter / éditer / rejeter → publication explicite*. On le reprend intégralement. **Ce qu'on change** : le déclencheur n'est pas un seuil statistique, c'est **un appel, désigné par le commerçant**.

### 2.1.4 LangSmith — la correction qui devient un exemple

C'est le seul mécanisme trouvé où **une correction humaine modifie durablement le comportement sans qu'on écrive de règle** (**[F]**, [docs.langchain.com/langsmith/create-few-shot-evaluators](https://docs.langchain.com/langsmith/create-few-shot-evaluators), 2026-09-14) :

- « Human corrections are automatically inserted into your evaluator prompt using few-shot examples. »
- « Creating an evaluator with few-shot examples will automatically create a dataset for you, which will be auto-populated with few-shot examples **once you start making corrections**. »
- Nombre d'exemples injectés **paramétrable, défaut 5** ; au-delà, tirage aléatoire.
- L'humain doit joindre une **explication** : « make sure to attach explanations — these will get populated into your evaluator prompt in place of the `few_shot_explanation` variable ».
- Le jeu de corrections est **consultable et éditable** comme un jeu de données ordinaire.

Les **files d'annotation** (**[F]**, [docs.langchain.com/langsmith/annotation-queues](https://docs.langchain.com/langsmith/annotation-queues), 2026-09-14) apportent le reste du vocabulaire : une **grille de notation** (feedback keys catégorielles avec description), des **assertions** (« capture acceptance criteria for offline evaluation »), un bouton **Add to Dataset**, des **règles d'automatisation** qui poussent en file « runs or threads that match a filter (for example, errors or low user scores) », et trois états d'avancement : **Needs Review → Needs Others' Review → Completed**.

→ **Deux emprunts** : (a) une correction produit **un exemple**, pas seulement une règle — c'est ce qui permet de corriger une formulation sans écrire une phrase d'instruction ; (b) **la limite du nombre d'exemples injectés est un paramètre du produit**, pas une conséquence subie. Défaut retenu : **5 par catégorie** **[H, calé sur le défaut LangSmith]**.

Réserve importante : chez LangSmith, la correction corrige **le juge**, pas l'agent, et **exige une explication rédigée**. Nous reprenons la mécanique, pas l'exigence de rédaction.

### 2.1.5 Retell — le plus proche du geste voulu, et pourquoi ça ne suffit pas

**Debug sur un tour de parole** (**[F]**, [docs.retellai.com/test/llm-playground-debug](https://docs.retellai.com/test/llm-playground-debug.md), 2026-09-14) : « When your agent answers wrong or takes the wrong path, Debug lets you fix that exact turn instead of guessing at the whole prompt or flow. » Les correctifs proposés sont **une liste fermée de trois** : *Add Fine-tuning Examples* (« to teach the wording you want »), *Split One Node into Two Nodes*, *Adjust LLM Temperature*. Puis **vérification par rejeu** : *Regenerate the answer*, et surtout ***Regenerate 10 answers* « to check how consistent the responses are across runs »**.

**Conductor** (**[F]**, [docs.retellai.com/conductor/test-and-improve](https://docs.retellai.com/conductor/test-and-improve.md) et [/conductor/review-changes](https://docs.retellai.com/conductor/review-changes.md), 2026-09-14) : on lui attache **un appel réel** et on demande « Review my recent calls and suggest fixes » ; il **propose** des changements, jamais ne les applique : « it doesn't edit your agent directly. Instead, it shows you a **proposal** ». La revue d'une proposition est remarquable — **chaque changement s'affiche sur le réglage concerné lui-même**, avec une bascule *View incoming changes / View current*, un compteur **1 / 3** qui fait défiler et surligner brièvement le réglage touché, et un **diff JSON** (supprimé barré, ajouté en vert) pour les valeurs structurées.

**Ce qui manque malgré tout, et c'est décisif** :
- les correctifs de Debug « **each one links to a guide you follow to make the change yourself** » — ce n'est pas un clic, c'est une documentation ;
- Conductor demande **une phrase en anglais**. C'est un prompt, déguisé en conversation. Rédhibitoire au regard de la contrainte produit.

**Vapi** confirme le même plafond, en plus brutal (**[F]**, [docs.vapi.ai/test/run-and-maintain-tests](https://docs.vapi.ai/test/run-and-maintain-tests.md), 2026-09-14) : il existe une section entière *« Turn production issues into regression tests »*, mais ce n'est qu'une **consigne écrite à un développeur** : « After you fix a production issue, add the smallest test that would have caught it before release », avec un tableau *problème de production → couverture de régression*. Le produit fournit les Evals, les Simulations et les Monitors (**[F]**, [docs.vapi.ai/observability/monitoring-quickstart](https://docs.vapi.ai/observability/monitoring-quickstart.md) : *Monitors / Triggers / Issues / Notifiers*, alertes e-mail, Slack, webhook) — mais **aucun bouton ne transforme un appel en test**. Vapi le dit d'ailleurs sans détour : « Monitors only detect the conditions you configure. »

Utile aussi : la distinction explicite de Vapi entre **tests d'amélioration** et **tests de régression** — « Use improvement tests to explore difficult behavior the agent cannot handle reliably yet. These tests show where to improve, so they do not all need to pass before every release » ; les tests de régression, eux, « should remain consistently passing ». Et l'interdit méthodologique qui va avec : « Don't loosen a success criterion or rerun until you get a pass without explaining the failure. »

### 2.1.6 Les correcteurs automatiques — d'où vient le geste

C'est dans les correcteurs, pas dans les plateformes d'IA, qu'on trouve la **forme** du geste à copier (**B1, loi de Jakob** : le commerçant a déjà ce geste dans les doigts).

- **iOS ≥ 17** (**[F]**, [support.apple.com/en-us/104995](https://support.apple.com/en-us/104995), 2026-09-14) : « Auto-Correction **temporarily underlines words that it corrects**. To quickly edit an auto-correction, **tap the underlined word and choose an option from the pop-up menu**. » → *la machine marque ce qu'elle a décidé à ta place, un appui suffit pour le reprendre.* C'est le modèle exact de la correction d'entité dans une transcription (§4.3).
- **Remplacement de texte** (même page) : on enregistre un couple *raccourci → phrase*, consultable et modifiable dans une liste. → *une correction lexicale est une paire, pas une instruction.*
- **Gmail, « Filter messages like these »** (**[F]**, [support.google.com/mail/answer/6579](https://support.google.com/mail/answer/6579), 2026-09-14) : on coche **un message**, on ouvre *Plus*, on clique *Filter messages like these* — **les critères sont pré-remplis depuis le message**, on ne choisit que l'action, et la règle finit dans une liste *Filters and Blocked Addresses* où elle s'édite et se supprime. → **le patron canonique du « d'un cas vers une règle »**, et il a vingt ans. C'est B8 (Tesler) appliqué : le système déduit les critères, l'humain ne décide que de l'intention.

## 2.2 Le principe qui tient toute la spécification

> **Une correction n'est jamais du texte libre. C'est le choix d'une faute dans une liste fermée, appliquée à un passage désigné de la transcription, qui écrit un objet de configuration typé déjà prévu par le schéma.**

Trois raisons, chacune adossée à un fait :

1. **Le texte libre n'est pas déterministe.** Intercom le documente : une règle en langue naturelle peut ne pas être sélectionnée sur un tour donné, « not a configuration error » (§2.1.1). Nos deux promesses les plus dures — confirmation orpheline nulle, impasse mesurée — ne peuvent pas dépendre d'une sélection contextuelle.
2. **Le texte libre est invérifiable.** Le concept l'a déjà tranché pour les politiques : *« Ces règles méritent des champs, pas un paragraphe — parce qu'un champ est vérifiable, testable, et affichable dans une transcription »* (`01-CONCEPT` écran 3).
3. **Le texte libre est un prompt.** Même déguisé en chat, comme Conductor. Le produit l'interdit.

Corollaire d'architecture, hérité de `02-ARCHITECTURE` §5 : **le corps Markdown de `memoire.md` n'est jamais reparsé**. Une correction n'écrit donc **jamais** dans le corps du fichier. Elle écrit dans le **frontmatter régénéré** et dans `tenant_config` (JSONB, append-only, versionné), avec un commit Git par sauvegarde et **l'utilisateur réel comme auteur**.

## 2.3 Les sept fautes — la liste fermée

Dérivées de la taxonomie d'intentions (`A6` §1.3), des modes d'échec détectables par règles (`02-ARCHITECTURE` §8.2) et des blocs du questionnaire coiffure (`A6` §6.1). **Sept, parce que ce n'est pas un menu à parcourir mais une grille de tri** — B2 (Hick) ne s'applique pas à une liste catégorisée et scannable, et sa limite l'écrit explicitement (`Regles-Barthez` §B2). En pratique l'écran n'en montre jamais sept d'un coup : **il en propose deux ou trois, pré-triées par ce que la machine sait déjà de l'appel** (B8).

| # | Libellé affiché | Ce que le gérant a vu | Objet de configuration écrit |
|---|---|---|---|
| **F1** | **« Il a mal entendu »** | Un mot, un prénom, une prestation, un numéro mal transcrits | `keyterms[]` + `lexique_corrections[]` (paire *forme entendue → forme juste*) |
| **F2** | **« Ce n'est pas la bonne information »** | Prix, durée, horaire, adresse faux | Champ du catalogue / de la fiche établissement (`services[]`, `horaires`, `adresse`) |
| **F3** | **« Il aurait dû me passer l'appel »** | Réclamation, urgence, cas sensible traité par l'agent | `escalade.declencheurs[]` (motif + destinataire + fenêtre horaire) |
| **F4** | **« Ce créneau n'existe pas »** | Créneau promis pendant la pause, sans temps de pose, ou avec un praticien indisponible | `contraintes_agenda[]` (pause, temps de pose, praticien imposé, tampon) |
| **F5** | **« Il n'a pas su répondre »** | Question jamais prévue, impasse, « je ne sais pas » | `faq[]` (question type + réponse, choisie ou dictée) |
| **F6** | **« Il ne parle pas comme nous »** | Tutoiement, formule, mot interdit | `style[]` (variable fermée) ou `formulations[]` (exemple : *au lieu de X, dire Y*) |
| **F7** | **« Il n'aurait pas dû faire ça »** | A pris / déplacé / annulé quand la règle l'interdit | Bascule d'une règle **D1–D9** du bloc « Règles de la maison » |

**Règle de composition** : une correction porte **exactement une faute**. Deux fautes sur le même appel = deux corrections, tracées séparément. C'est la leçon explicite de Fin : « Split broad rules into focused ones. A single rule covering multiple style behaviors is less reliably retrieved than separate, single-purpose rules » (**[F]**, §2.1.1).

## 2.4 Le geste, tap par tap

Cible : **trois appuis au maximum, aucun clavier dans le cas nominal.**

```
E2 Revue d'appel
 └─ appui long / bouton « Corriger » sur une ligne de transcription   ← 1er appui (désigne l'empan)
     └─ E3 Feuille de correction, montée du bas (zone de pouce, B3)
         ├─ 2 ou 3 fautes proposées, pré-triées                        ← 2e appui (désigne la faute)
         └─ la valeur juste, pré-remplie et modifiable                 ← 3e appui (confirme)
             └─ « Corrigé. L'agent le saura au prochain appel. »
                + « Écouter comment il répondrait maintenant »  (facultatif, jamais bloquant)
```

**Ce qui est pré-rempli, et pourquoi** — B8 (Tesler), contrôle : *« pour chaque champ, pourquoi est-ce l'humain qui tape ça ? »*

| Ce que la machine sait déjà | Ce qu'elle pré-remplit |
|---|---|
| L'empan sélectionné et son type d'entité | La faute la plus probable (F1 si l'empan est une entité à faible confiance, F4 si c'est une confirmation de créneau, F3 si l'appel a été classé réclamation) |
| Le catalogue | La liste des prestations proches phonétiquement, pour F1 et F2 |
| L'agenda | Le motif exact du conflit, pour F4 (« ce créneau tombe dans la pause de 12 h 30 ») |
| Les motifs d'escalade déjà configurés | Ceux qui **manquaient** pour que cet appel bascule, pour F3 |
| La transcription | La question de l'appelant, mot pour mot, comme intitulé de FAQ pour F5 |

**Le seul cas où un clavier apparaît** : F5, la réponse à une question nouvelle — et encore, **dictée acceptée**, puisque le gérant a les mains occupées. Le texte dicté est une **réponse**, pas une instruction à l'agent : la distinction est ce qui sépare notre produit d'un éditeur de prompt.

## 2.5 Spécification d'états

### 2.5.1 Les états d'une correction

Repris de Fin (Draft / Live / Live with draft / Paused, **[F]** §2.1.1) et complétés par ce que le vocal impose (l'essai audible, la péremption, le conflit).

| État | Sens | L'agent l'applique ? | Transitions sortantes |
|---|---|---|---|
| **`proposee`** | Écrite mais pas confirmée (la feuille a été quittée) | Non | → `en_essai`, `active`, ou suppression après 7 jours |
| **`en_essai`** | Confirmée, appliquée **uniquement au numéro d'essai** | Non (appels réels) | → `active`, → `revoquee` |
| **`active`** | En vigueur sur les appels réels | **Oui** | → `suspendue`, → `revoquee`, → `expiree`, → `en_conflit` |
| **`active_avec_brouillon`** | Active, avec une modification enregistrée non publiée | Oui (l'ancienne version) | → `active` (publication), → `active` (abandon du brouillon) |
| **`suspendue`** | Retirée du service, conservée, réactivable en un appui | Non | → `active`, → `revoquee` |
| **`en_conflit`** | Contredit une autre correction ou une réponse du questionnaire | **Non — la plus récente est suspendue d'office** | → `active` (arbitrage), → `revoquee` |
| **`expiree`** | Avait une date de fin (fermeture, remplacement, promotion) | Non | → `active` (prolongation), archive |
| **`revoquee`** | Annulée. Reste dans l'historique, jamais supprimée | Non | (terminal) |

**Trois décisions qui divergent volontairement de Fin** :

1. **Pas d'état « non enregistré ».** Fin assume que des modifications « exist only in your browser and will be lost if you navigate away ». Inacceptable ici : le gérant est interrompu par un client au milieu du geste. **Chaque appui est écrit serveur**, comme le questionnaire (`01-CONCEPT` §4). L'état `proposee` est le filet.
2. **L'essai est un état, pas un mode.** Fin sépare *Preview* (test) et *Enable* (mise en service). On garde les deux, mais l'essai porte sur le **numéro d'essai** déjà prévu par l'écran 4 du concept — donc le gérant **entend** la correction avant qu'elle touche un client. C'est la seule vérification qui vaille en vocal : Vapi écrit que ses Evals « run at the text and model layer. They don't test speech recognition, audio quality, or turn-taking » (**[F]**, §2.1.5).
3. **Le conflit est un état de première classe.** Fin ne détecte les contradictions que dans le contenu, par un balayage hebdomadaire (**[F]** §2.1.2), et son *Optimize* signale la contradiction **à l'écriture** d'une règle. Nous détectons **à l'écriture et à chaque activation**, parce que nos corrections sont typées : deux valeurs contradictoires sur le même champ se comparent par égalité, pas par jugement d'un modèle. *(Rappel `02-ARCHITECTURE` §8.3 : « jamais de juge LLM pour valider une entité ».)*

### 2.5.2 Les états d'un appel, dans le journal

| État | Comment il est atteint | Conséquence à l'écran |
|---|---|---|
| `traite` | L'agent a fait ce qu'il devait | Ligne ordinaire |
| `a_revoir` | Une règle de détection a levé un drapeau (`02-ARCHITECTURE` §8.2 : raccroché < 10 s, > 3 reformulations, silence au-delà du seuil, demande d'humain non satisfaite) | Remonte dans E0, micro-label du motif |
| `corrige` | Une correction en est issue | Pastille + lien vers la correction |
| `incident` | Confirmation orpheline détectée | Bandeau, notification immédiate, tête de E0 |
| `ignore` | Le gérant a dit « c'est normal » | Sort de la pile, **et le motif de détection est compté** — trois « c'est normal » sur le même motif proposent de désactiver ce drapeau **[H]** |

L'état `ignore` est la soupape sans laquelle la pile à revoir devient un mur. Il est aussi un **signal produit** : un drapeau qu'on ignore trois fois est un mauvais drapeau.

## 2.6 Ce qui est écrit dans la configuration, action par action

Format cible, dérivé de `01-CONCEPT` §5 et `02-ARCHITECTURE` §5. **Tout va dans le frontmatter ou dans `tenant_config` ; rien dans le corps Markdown.** Chaque entrée porte les mêmes métadonnées : `id`, `etat`, `origine` (identifiant de l'appel et empan), `cree_le`, `auteur`, `expire_le?`.

### F1 — « Il a mal entendu »

```yaml
keyterms: ["balayage", "Karim", "Nguyen", "shatush"]   # ajout, plafond 50 (recommandation Deepgram, A6)
lexique_corrections:
  - entendu: "cha toucher"
    juste: "shatush"
    id: c_8f21
    origine: { appel: a_5512, empan: [142.3, 143.1] }
    etat: active
```
**Portée** : tous les appels du tenant. **Effet second** : le terme entre dans la liste d'amorçage du moteur de reconnaissance, **et** dans le corpus de régression (§2.8). **Réversible** : retrait de la paire.
**Ce qui n'est pas écrit** : aucune phrase d'instruction. Une correction phonétique est une **paire**, comme un remplacement de texte iOS (**[F]** §2.1.6).

### F2 — « Ce n'est pas la bonne information »

```yaml
services:
  - id: s_014
    nom: "Balayage"
    duree_min: 120          # était 90
    prix_cents: 9000
    prix_variable: true     # « à partir de », A6 §2.5
```
**Portée** : la fiche. **Ce n'est pas une correction d'agent, c'est une correction de données** — et c'est le point : la moitié des « l'agent a mal répondu » sont des données fausses, pas un comportement fautif. L'écran le dit au gérant en toutes lettres, parce que c'est rassurant et vrai **[H]**.
**Effet second obligatoire** : si la durée change, **tous les rendez-vous futurs déjà pris sur l'ancienne durée sont listés**. On ne les modifie pas d'office — l'agent ne décide jamais à la place du gérant (`01-CONCEPT` §6).

### F3 — « Il aurait dû me passer l'appel »

```yaml
escalade:
  declencheurs:
    - motif: reclamation
      mots: ["dégorgé", "pas contente", "remboursement"]
      action: transfert
      destinataire: "+336…"
      hors_horaires: message_et_sms
      id: c_8f24
      origine: { appel: a_5512 }
      etat: en_essai
```
**Portée** : tous les appels. **Les mots sont extraits de l'appel lui-même**, proposés cochés, décochables — jamais tapés. **Garde-fou hérité de `00-SYNTHESE` L86** : hors horaires, **pas de transfert** (« sonnerie dans le vide = pire que rien ») — l'interface n'offre donc pas cette combinaison, elle bascule automatiquement sur *message + SMS*. Un choix impossible n'est pas grisé : il n'est pas montré (B2).

### F4 — « Ce créneau n'existe pas »

```yaml
contraintes_agenda:
  - type: pause
    jours: [mar, mer, jeu, ven]
    debut: "12:30"
    fin: "13:30"
    id: c_8f26
    origine: { appel: a_5512, empan: [88.0, 95.4] }
    etat: active
```
**La plus importante des sept.** `A6` §2.2 l'établit : l'absence de pause est **le seul défaut que le client entend**, l'agent promettant un créneau qui n'existe pas. C'est aussi la faute qui alimente le taux de confirmation orpheline.
**Portée** : le moteur de créneaux, **côté serveur, hors du modèle**. Une contrainte d'agenda n'est jamais une phrase dans un prompt — c'est un filtre appliqué avant que le modèle ne voie la liste des créneaux. C'est la conséquence directe de l'aveu d'Intercom sur la sélection par tour (§2.1.1).

### F5 — « Il n'a pas su répondre »

```yaml
faq:
  - question: "Vous faites les extensions à chaud ?"    # verbatim de l'appelant
    reponse: "Non, seulement à froid, par bandes."      # choisie ou dictée
    id: c_8f28
    origine: { appel: a_5512, empan: [201.7, 205.2] }
    etat: active
```
**Portée** : base de connaissance. Pas de RAG (`01-CONCEPT` §5 : seuil du passage obligatoire vers **300 000 caractères**, fichiers sous **300 Ko**) — l'entrée va dans le fichier, donc dans le prompt système, avec mise en cache.
**Patron emprunté à Zendesk** (**[F]** §2.1.3) : la question est **le verbatim du ticket**, la réponse est un brouillon qu'on relit. Différence : le brouillon vient de **cet appel-là**, pas de 90 jours d'agrégat.

### F6 — « Il ne parle pas comme nous »

Deux formes, et la première est toujours proposée en premier :

```yaml
style:
  vouvoiement: true        # variable fermée du bloc E (A6 §6.1)
  accueil: "Salon Nguyen, bonjour"
formulations:
  - au_lieu_de: "Je vous mets ça de côté"
    dire: "Je vous le note"
    id: c_8f30
    origine: { appel: a_5512, empan: [33.1, 35.0] }
    etat: active
```
**`formulations[]` est un exemple, pas une consigne.** C'est l'emprunt direct à LangSmith (§2.1.4) et à *Add Fine-tuning Examples* de Retell (§2.1.5) : **on montre la bonne phrase au lieu de décrire la bonne phrase**. Plafond : **5 formulations injectées** par appel, les plus récentes (défaut calé sur LangSmith) **[H]**. Au-delà, l'interface propose d'en archiver.

### F7 — « Il n'aurait pas dû faire ça »

```yaml
regles_maison:
  D9_agent_peut_deplacer: "pas_moins_de_24h"   # était "librement"
```
**Portée** : règle dure, évaluée côté serveur. Une bascule, pas une phrase. **Effet second** : la règle est **citable dans une transcription** — l'écran de revue peut afficher « refusé : règle D9 » sous le tour de parole concerné. C'est ce que le concept appelle un champ « vérifiable, testable, et affichable ».

### 2.6.1 Tableau de synthèse — action → écriture

| Action dans l'UI | Objet écrit | Où | Portée | Déterministe ? | Réversible |
|---|---|---|---|---|---|
| Corriger un mot entendu | paire `lexique_corrections` + `keyterms` | frontmatter | tenant | Oui (amorçage ASR) | retrait de la paire |
| Corriger un prix / une durée | champ de `services[]` | `tenant_config` | tenant | Oui | version précédente |
| Ajouter un motif d'escalade | `escalade.declencheurs[]` | frontmatter | tenant | **Partiellement** — mots-clés déterministes, jugement de contexte non | suspension |
| Ajouter une contrainte d'agenda | `contraintes_agenda[]` | `tenant_config` | moteur de créneaux | **Oui, hors modèle** | suspension |
| Ajouter une réponse | `faq[]` | frontmatter | tenant | Non (sélection par le modèle) | suspension |
| Corriger une formulation | `formulations[]` (exemple) | frontmatter | tenant | Non | suspension |
| Basculer une règle de maison | `regles_maison.*` | `tenant_config` | serveur | **Oui, hors modèle** | version précédente |

La colonne « déterministe » est **affichée au gérant**, en clair et sans jargon : les corrections d'agenda et de règles portent la mention « **appliqué à coup sûr** », les autres « **l'agent en tiendra compte** ». C'est l'honnêteté que Fin ne dit qu'à ses développeurs, enterrée dans une FAQ. **B6** : la distinction est portée par un mot, jamais par une couleur seule.

## 2.7 Les garde-fous

1. **Plafonds.** Fin plafonne à 1 000 règles et 2 500 caractères (**[F]** §2.1.1). Nous plafonnons plus bas, parce qu'un salon n'est pas un service client : **50 keyterms** (recommandation Deepgram reprise dans `A6`), **5 formulations injectées**, **30 entrées de FAQ** avant de proposer un regroupement **[H]**.
2. **Détection de contradiction à l'écriture.** Si la correction contredit une réponse du questionnaire ou une correction active, l'écran montre **les deux, côte à côte**, et demande laquelle vaut. Il ne tranche pas tout seul. C'est *Review contradictory content* de Fin, mais **au moment du geste** plutôt qu'au balayage du dimanche.
3. **Péremption facultative mais proposée.** « Jusqu'à quand ? » avec trois réponses : *toujours* (défaut recommandé, B2), *jusqu'à une date*, *cette semaine*. Une fermeture estivale ou une promotion n'a aucune raison de survivre à l'automne.
4. **Aucune correction ne s'applique rétroactivement.** Les rendez-vous déjà pris ne bougent pas. On liste, on ne modifie pas.
5. **Journal d'audit intégral.** Chaque transition d'état est une ligne, auteur réel, horodatée, avec l'appel d'origine. Le `memoire.md` vit déjà dans un dépôt Git avec `GIT_AUTHOR_NAME` = l'utilisateur (`02-ARCHITECTURE` §5).
6. **Rien ne part en production sans un geste explicite.** Formulation retenue de Fin : « Nothing goes live without your explicit approval first » (**[F]** §2.1.2), et de Retell : « Nothing is applied until you approve » (**[F]** §2.1.5).

## 2.8 La correction devient un test — et c'est là qu'on dépasse le marché

Personne ne le fait en un clic. Vapi écrit la consigne à des développeurs, Retell propose des liens vers des guides (§2.1.5). **Nous le faisons en silence, sans le demander :**

> **Toute correction confirmée ajoute automatiquement l'extrait d'appel correspondant au corpus de régression du tenant.**

Le corpus existe déjà (`02-ARCHITECTURE` §8.4) : 60 à 100 appels réels français, **rééchantillonnés 8 kHz / G.711**, rejoués **k = 5 fois**, succès **intégraux** comptés. Une correction y ajoute : l'audio de l'empan, la transcription attendue (F1), ou le comportement attendu (F3, F4, F7).

Deux emprunts de vocabulaire, à garder tels quels :
- **La distinction amélioration / régression de Vapi** (**[F]** §2.1.5) : les cas issus de corrections récentes sont des **tests d'amélioration** (ils ont le droit d'échouer) ; ils deviennent des **tests de régression** quand ils passent cinq fois de suite. Le gérant ne voit jamais ces mots — il voit « l'agent sait maintenant le faire » **[H]**.
- **Le rejeu multiple de Retell** : *Regenerate 10 answers* « to check how consistent the responses are across runs » (**[F]** §2.1.5). Notre équivalent, offert après une correction de formulation ou de FAQ : « **Écouter trois réponses** » — parce qu'une réponse juste une fois ne prouve rien.

## 2.9 Le pic et la fin — nommés par écrit (B10, contrôle obligatoire)

> **Le pic** : l'instant où le gérant appuie sur « Corriger », choisit une faute, et **entend l'agent redire la chose correctement dans les secondes qui suivent**. Pas un message de succès : sa propre voix de marque, réparée, dans l'écouteur. C'est le seul moment du produit où l'on voit l'agent apprendre.
>
> **La fin** : l'écran qui suit la correction n'est pas un cul-de-sac. Il porte **une phrase de conséquence** — « L'agent proposera désormais 13 h 30 au plus tôt le mardi » — et **une seule action suivante** : *Revoir l'appel suivant*, ou, s'il n'y en a plus, *Voir ce que l'agent a appris* (E4). Jamais un « OK ».

E4 est la fin longue du produit : **la liste de ce que l'agent a appris grâce à lui**. C'est l'écran qui transforme une corvée de supervision en capital. Il se lit comme un registre, position 1 = la correction la plus récente, position n = « tout voir » (B7).

---

# 3. Écran de revue d'appel — ce que fait le marché

> Les lignes de ce chapitre marquées **[R]** proviennent de pages marketing d'éditeurs ; les centres d'aide de Fresha, Zenoti, Boulevard et RingCentral n'ont pas répondu. **Aucun détail d'interface n'a été inventé** : ce qui n'a pas été vu est marqué **[NV]**.

## 3.1 Comparatif

| Produit | Liste d'appels | Transcription | Audio | Issue / résumé | Coût & durée | Latence | Raison de fin | Éditable |
|---|---|---|---|---|---|---|---|---|
| **Vapi** | Call Logs : durée, statut, résultats d'outils, erreurs **[F]** | `messages` horodatés (`time`), diarisation par `role` **[F]** | mono/stéréo, URL signée, `wav;l16` par défaut **[F]** | `analysis.summary`, `successEvaluation` (Numeric / Descriptive / Checklist / Matrix / % / Likert / Rubric / PassFail), `structuredData` **[F]** | oui **[F]** | **[NV]** | `endedReason` codé (`vapifault-*`, `providerfault-*`, `pipeline-error-*`, timeout, transfert…) **[F]** | non, en amont seulement **[F]** |
| **Retell** | heure, coût, id, statut, sentiment, numéros, agent, durée, canal, direction, raison de fin, résultat, **latence** **[F]** | messages + appels d'outils + transitions d'état + SMS + récupérations KB **[F]** | lecteur WAV intégré **[F]** | `call_summary`, `call_successful`, `user_sentiment`, `in_voicemail` + 4 champs custom **[F]** | affichés, **non modifiables** **[F]** | oui, par appel **[F]** | `disconnection_reason`, **31 valeurs** **[F]** | non **[F]** |
| **ElevenLabs Agents** | filtres agent / branche / langue / modèle / outil / erreur **[F]**, colonnes exactes **[NV]** | historique consultable + recherche sémantique **[F]**, rendu **[NV]** | « audio saving » réglable, rétention 0 j → années **[F]** | Success Evaluation `success` / `failure` / `unknown` + justification par critère **[F]** | agrégés **[F]** | agrégée **[F]** | taux d'erreur agrégé **[F]** | non, en amont **[F]** |
| **Fresha (AI Concierge)** | **[NV]** | « transcription complète » **[R]** | « disponible et peut être activé dans vos paramètres » — le plus proche d'un vrai opt-in **[R]** | RDV créés, modifications, escalades **[R]** | 94,95 €/site/mois (tarif) **[R]** | **[NV]** | **[NV]** | **[NV]** |
| **Zenoti (AI Receptionist)** | revenu, appels traités, RDV, **handover rate**, par site **[R]** | transcriptions + résumés **[R]** | « Every call automatically recorded » **[R]** | réservation, upsell, conversion annulation→report, frais d'annulation **[R]** | **[NV]** | **[NV]** | **[NV]** | **[NV]** |
| **Boulevard** | appels totaux, temps gagné, réservations **[R]** | transcript + résumé pour « reprendre où l'IA s'est arrêtée » **[R]** | **[NV]** | FAQ, coordonnées, liens de réservation, transferts **[R]** | **125 $/mois/site, 200 min, puis 0,60 $/min** **[R]** | **[NV]** | **[NV]** | **[NV]** |
| **RingCentral AIR** | volumes, taux de résolution, transferts, **questions sans réponse** **[R]** | transcripts + résumés **[R]** | « can be recorded and transcribed automatically » **[R]** | leads, MAJ CRM, agenda, SMS **[R]** | **[NV]** | **[NV]** | **[NV]** | **[NV]** |
| **Rosie** | **[NV]** | transcription complète **[R]** | enregistrement intégral **[R]** | résumé + notification e-mail/SMS/app à chaque fin d'appel **[R]** | **[NV]** | **[NV]** | **[NV]** | **[NV]** |
| **Slang.ai** | **Priority Queue** avec étiquettes et tri **[R]** | transcripts **[R]** | enregistrements **[R]** | résumés + fiche client ; top topics, heures de pointe, answer rate, satisfaction, couverts réservés **[R]** | **[NV]** | **[NV]** | **[NV]** | **notes + « résolu » sur la file** — seul cas d'édition trouvé **[R]** |
| Goodcall, Dialzara, Sameday, Numa, Voiceflow | **[NV]** — non atteints | | | | | | | |

## 3.2 Les patrons récurrents — donc attendus (B1)

1. **Le triptyque transcription + résumé généré + enregistrement**, partout, sans exception.
2. **Le résumé est toujours une génération, jamais un extrait** (Vapi `summaryPrompt`, Retell `call_summary`, ElevenLabs).
3. **Une note de succès par appel**, sous une forme ou une autre — mais **aucune norme commune de valeurs**.
4. **Deux familles de métriques qui ne se parlent pas** : les verticaux (Fresha, Zenoti, Boulevard, RingCentral, Slang) affichent du **ROI métier** (appels traités, RDV, temps gagné, revenu) et **jamais** de latence ; les plateformes (Vapi, Retell, ElevenLabs) affichent **latence et taux d'erreur** et presque pas de ROI.
5. **L'escalade vers un humain est documentée partout comme une issue légitime** — c'est le *handover rate* de Zenoti, le plus mûr du panel.
6. **Extraction de données structurées définies par le client** : Retell (4 champs typés), ElevenLabs (data collection), Vapi (`structuredDataSchema`) convergent.

**Notre écran de revue doit donc être immédiatement reconnaissable** : même triptyque, même position, mêmes mots. On n'innove pas sur la mécanique (B1, limite de la loi : « on innove sur la valeur, jamais sur la mécanique de base »).

## 3.3 Ce qui manque partout — les six trous

1. **Aucun indicateur de confiance visible** sur l'écran d'un appel, chez aucun des neuf produits documentés.
2. **Aucune mise en évidence d'entités** confirmée dans une transcription.
3. **Le lien transcription ↔ audio n'est confirmé que chez Retell** : « sélectionner un horodatage de transcription pour accéder à ce point de l'enregistrement » **[F]**. C'est pourtant le geste le plus utile pour vérifier une IA.
4. **Aucune édition ni correction depuis l'écran d'appel.** Retell écrit explicitement que coût, durée et sentiment ne sont pas modifiables. Slang est le seul à offrir une action (note + « résolu »), et sur sa file de priorité, pas sur la transcription.
5. **Aucune comparaison « ce que l'IA a fait / ce qu'un humain aurait fait ».**
6. **Le consentement est quasi absent de toute la documentation technique.** Retell recommande une annonce vocale dans le premier message de l'agent mais « il n'existe pas de paramètre dédié » **[F]** ; ElevenLabs ne traite que la rétention et réserve la rédaction des données personnelles à l'offre entreprise **[F]** ; seul Fresha mentionne une annonce vocale en début d'appel **[R]**.

Le sixième trou est **notre argument de vente**, pas un détail : l'annonce « vous parlez à une IA » est non désactivable dans le concept (§5, AI Act art. 50), et **pas d'enregistrement audio par défaut — transcription seule** (§6). Le marché fait l'inverse : Vapi enregistre par défaut, Retell enregistre par défaut avec trois niveaux (*Everything / Everything except PII / Basic Attributes Only*) **[F]**, Zenoti et Rosie annoncent l'enregistrement systématique **[R]**.

---

# 4. Affichage d'une transcription

## 4.1 Lisibilité

Règles retenues, avec la loi qui tranche :

- **Une ligne = un tour de parole**, label de locuteur en tête, jamais en infobulle. La diarisation est structurelle, pas décorative.
- **Mesure ≤ 62 caractères** (DA §2.2). Sur un téléphone tenu à une main, c'est la contrainte qui gouverne la taille de corps, pas l'inverse.
- **Le gérant et l'appelant ne se distinguent pas par la couleur seule** (**B6**, limite) : l'agent est en retrait (`--ink-mute`, label à gauche), l'appelant en pleine encre. Deux bulles opposées façon messagerie sont un contresens ici — on ne lit pas une conversation, on **audite** une conversation, ce qui se fait en colonne unique, du haut vers le bas.
- **Proximité 1:2** (**B5**) : l'interligne à l'intérieur d'un tour est au plus la moitié de l'écart entre deux tours. Aucune bordure, aucun fond n'est nécessaire pour faire comprendre le regroupement — s'il l'est, l'espacement est raté.
- **Position sérielle** (**B7**) : le premier et le dernier tour de parole sont les deux qui comptent — l'accueil (la voix de la maison) et la conclusion (ce qui a été promis). Ils sont épinglés en haut et en bas de l'écran quand on fait défiler le milieu **[H]**.

## 4.2 Alignement audio ↔ texte

La structure canonique est disponible chez tous les moteurs sérieux : AssemblyAI expose un tableau `words[]` avec `text`, `start`, `end` (ms), `confidence`, `speaker` (**[F]**, [assemblyai.com/docs/speech-to-text/speech-recognition](https://www.assemblyai.com/docs/speech-to-text/speech-recognition), 2026-09-14). Otter annonce « synced audio and text, and playback speed control », l'identification des locuteurs, et l'édition en place du texte, des locuteurs **et des codes temporels** (**[F]**, [otter.ai/features](https://otter.ai/features), 2026-09-13/14).

**Décisions** :
- Appuyer sur un tour **place la lecture à cet instant** — c'est le seul geste confirmé chez Retell, et il est attendu (B1).
- **Pas de karaoké mot à mot par défaut.** Le suivi mot à mot est un effet de démonstration ; il est coûteux à lire d'une main et n'apporte rien à l'audit. Il n'est justifié que **pendant** la lecture audio, à la demande **[H]**.
- L'audio n'étant **pas enregistré par défaut** (`01-CONCEPT` §6), l'écran doit être **entièrement utile sans lecteur**. La transcription est la vue de référence, pas une béquille.

## 4.3 Entités et passages à faible confiance

**Ce que disent réellement les fournisseurs**, et c'est plus prudent qu'on ne le croit :

- **Deepgram** : la confiance est « une probabilité calibrée » 0–1 ; un score de 0,93 signifie qu'environ 93 % des mots à ce score sont corrects. Seuil de base recommandé pour détecter des erreurs : **0,65** — « very likely to be genuine errors, high precision ». Approche adaptative proposée : erreurs attendues ≈ `(1 − confiance moyenne) × nombre de mots`, puis signaler ce nombre de mots les moins confiants. **Ne jamais comparer les scores bruts entre fournisseurs** (calibrations différentes). (**[F]**, [developers.deepgram.com/docs/confidence](https://developers.deepgram.com/docs/confidence.md), 2026-09-14)
- **Google Cloud STT** : avertissement explicite — « the model determines the "best", top-ranked result based on more signals than the confidence score alone » et « **Don't include confidence as a required field in your code. It may not be set in any of the results, and it may not be accurate.** » (**[F]**, [docs.cloud.google.com/speech-to-text/docs/basics](https://docs.cloud.google.com/speech-to-text/docs/basics), 2026-09-14)
- **Azure** : non documenté sur la page consultée **[NV]**.

**Conséquence de conception** : la confiance est un **filtre statistique**, pas un verdict. Donc :

| Ce qu'on fait | Ce qu'on ne fait pas |
|---|---|
| **Souligner discrètement** l'entité incertaine, exactement comme iOS souligne un mot auto-corrigé (**[F]** §2.1.6) | Afficher un pourcentage de confiance |
| Un appui sur l'entité soulignée ouvre **les candidats** (« Karim » / « Karine »), pré-classés | Un badge d'alarme, un point d'exclamation, une couleur d'alerte |
| N'appliquer le soulignement qu'aux **entités qui comptent** : numéro, date, heure, prestation, prénom de praticien | Souligner des mots ordinaires — le bruit détruirait le signal |
| Traiter tout numéro et toute date comme suspects **par construction**, indépendamment du score | Faire confiance au score seul |

Le dernier point est une conséquence directe de `00-SYNTHESE` L82 : relecture du numéro par groupes de deux, **DTMF de secours après deux échecs**, dates en **ISO 8601 absolu** dans l'appel de fonction avec confirmation « jour de la semaine + date + heure » qui sert de **bit de parité**. L'écran de revue **affiche ce bit de parité** : si l'agent a dit « mardi 17 » et que le 17 est un mercredi, la contradiction est visible sans qu'aucun modèle n'ait à juger.

**Mise en évidence d'entités** : le patron existe (puces Gmail, détecteurs de données Apple) mais aucune page officielle le documentant n'a pu être récupérée cette session — **[NV]**. Le soulignement + menu contextuel d'iOS, lui, est vérifié (**[F]**).

## 4.4 Édition en place

Otter confirme le patron « la transcription **est** la surface d'édition » (texte, locuteur, code temporel) (**[F]**). Descript et Rev suivent le même modèle **[NV]** cette session.

**Notre contrainte** : corriger la transcription affichée ne sert à rien si ça ne corrige que l'affichage. **Toute édition en place est donc une correction F1** (§2.6) : elle écrit une paire dans `lexique_corrections` et alimente le corpus de régression. **L'édition sans conséquence est interdite** — c'est de la cosmétique qui donne l'illusion du contrôle.

Exception : la transcription **historique** n'est pas réécrite. On corrige le **futur**, pas l'archive. Une archive réécrite n'est plus une preuve, et ces transcriptions peuvent servir en cas de litige sur un rendez-vous.

---

# 5. Temps réel sur mobile

## 5.1 Le coût caché n'est pas la donnée, c'est la radio

Le chapitre mobile de *High Performance Browser Networking* (Ilya Grigorik) donne le chiffre qui tranche tout (**[F]**, [hpbn.co/mobile-networks/](https://hpbn.co/mobile-networks/), 2026-09-14) :

- **L'énergie de traîne** : après un transfert, la radio reste en état de haute puissance (**1 000 à 3 500 mW**) jusqu'à expiration d'un minuteur d'inactivité, **indépendamment de la quantité de données transférées**.
- **Le cas Pandora** : les balises analytiques représentaient **0,2 % des octets transférés et 46 % de la consommation d'énergie totale**.
- Transitions RRC en LTE : repos → connecté **< 100 ms**, dormant → connecté **< 50 ms** ; en 3G, repos → connecté **jusqu'à 2 secondes**.

→ **L'interrogation périodique fréquente est disqualifiée**, non pas par le volume mais par le réveil radio. Un appel de 4 minutes sondé toutes les 2 secondes, c'est 120 réveils pour afficher une barre de progression.

## 5.2 SSE contre WebSocket

| | SSE | WebSocket |
|---|---|---|
| Reconnexion | **automatique par défaut**, `.close()` pour l'arrêter ; le champ `id` alimente le dernier identifiant d'événement **[F]** | **aucune reconnexion automatique documentée** — à écrire soi-même **[F]** |
| Plafond de connexions | **6 par navigateur** hors HTTP/2 — « Won't fix » chez Chrome et Firefox ; sous HTTP/2, limite négociée (défaut 100) **[F]** | non concerné |
| Contre-pression | non concerné | **pas de gestion native** sur l'interface standard ; accumulation mémoire/latence possible ; `WebSocketStream` (non standard) corrige **[F]** |
| Cache retour/avant | — | une connexion ouverte **empêche le bfcache** ; fermer en quittant la page **[F]** |
| Sens | serveur → client | bidirectionnel |

Sources : [MDN — Using server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events) et [MDN — WebSockets API](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API), 2026-09-14 **[F]**.

## 5.3 L'arrière-plan

**[F]**, [MDN — Page Visibility API](https://developer.mozilla.org/en-US/docs/Web/API/Page_Visibility_API), 2026-09-14 :

- `requestAnimationFrame` est **arrêté** dans un onglet en arrière-plan ; `setTimeout` est **bridé** — budget de **30 s (10 s sous Chrome)**, régénéré à **10 ms par seconde**.
- **Exemptions au bridage** : onglets qui jouent de l'audio, onglets avec **WebSocket ou WebRTC actif**, traitements IndexedDB.
- Recommandation explicite : arrêter l'interrogation serveur quand la page est cachée.

→ **Un WebSocket actif échappe au bridage ; une boucle `setTimeout` non.** C'est l'argument technique décisif contre l'interrogation périodique sur mobile — elle ne devient pas seulement coûteuse, elle devient **non fiable**.

## 5.4 Décision

| Écran | Transport | Raison |
|---|---|---|
| **E5 — appel en cours** | **SSE**, un flux, fermé à `visibilitychange` → `hidden` | Le flux est **unidirectionnel** : le serveur pousse les tours de parole, le gérant n'envoie rien. La reconnexion automatique et `Last-Event-ID` sont offerts ; le WebSocket demanderait d'écrire la reprise à la main **[F]** |
| **Prendre la main pendant l'appel** | requête POST ordinaire | Une action rare n'a pas besoin d'un canal permanent |
| **E0, E1 — journal** | pas de temps réel. Rafraîchissement **à la remise au premier plan** (`visibilitychange` → `visible`) + **tirer pour rafraîchir** (B1) | Un journal d'appels n'a aucune raison d'être poussé. C'est exactement le cas Pandora **[F]** |
| **Alertes hors application** | **notification poussée**, jamais un flux maintenu | §7 |

**Deux garde-fous** :
- **Un seul flux SSE ouvert à la fois dans tout le produit** — le plafond de 6 connexions hors HTTP/2 est un piège classique quand plusieurs onglets sont ouverts **[F]**.
- **Le flux se ferme dès que l'écran est caché**, et se rouvre avec `Last-Event-ID` au retour. Le gérant qui range son téléphone dans sa poche ne doit pas payer la traîne radio.
- **Rythme de battement de cœur** : aucune valeur chiffrée officielle n'a été trouvée dans MDN, web.dev ou les spécifications W3C — **[NV]**. Le choix se fera par mesure sur appareil réel, pas par recopie.

## 5.5 Budgets de latence (B9, seuil de Doherty)

| Geste | Budget | Traitement |
|---|---|---|
| Ouvrir la feuille de correction | **< 100 ms** | Purement local, aucune requête. La liste des fautes est déjà chargée avec l'appel |
| Appliquer une correction | **< 400 ms** | Écriture optimiste : l'état passe à `active` à l'écran, réconciliation ensuite. Échec → retour visible et explicite, jamais silencieux |
| Charger un détail d'appel | **< 400 ms**, sinon squelette | Squelette, jamais de rouet nu (DA §2.8) |
| Rejouer l'agent après correction | **> 1 s assumé** | Progression explicite, et **sortie disponible** : le gérant peut partir, le résultat l'attendra dans E4 |

---

# 6. Accessibilité et mobile

## 6.1 WCAG 2.2 AA — ce qui compte réellement ici

Toutes les citations viennent des pages *Understanding* du W3C, consultées le 2026-09-14 **[F]**.

| Critère | Énoncé | Conséquence dans la console |
|---|---|---|
| **2.5.8 Target Size (Minimum), AA** — [w3.org](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html) | « The size of the target for pointer inputs is at least **24 by 24 CSS pixels** », avec cinq exceptions : *Spacing* (un cercle de 24 px centré sur la cible ne doit intersecter aucune autre cible), *Equivalent*, *Inline*, *User Agent Control*, *Essential*. La page note que viser 24×24 reste la bonne pratique même sous exception | **Barthez impose plus dur : 44×44 px** (§B3, Apple HIG / WCAG 2.5.5 AAA), 24 px étant le **plancher absolu**. Les cibles de la transcription (une entité soulignée dans une ligne de texte) relèvent de l'exception **Inline** — d'où l'obligation d'une **seconde voie conforme** : le bouton « Corriger » de la ligne, lui, fait 44 px |
| **1.4.3 Contrast (Minimum), AA** — [w3.org](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) | **4,5:1** corps, **3:1** grand texte (18 pt, ou 14 pt gras) | Ratios Barthez déjà calculés sur `--paper` : `--ink` 17,4:1, `--electric` 8,2:1, `--ink-mute` 4,9:1. **`--rule` à 2,3:1 ne porte jamais de texte** |
| **1.4.11 Non-text Contrast, AA** — [w3.org](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html) | **3:1** contre la couleur adjacente pour l'information visuelle identifiant un composant et son état | Le **soulignement d'incertitude** (§4.3) est de l'information visuelle : il doit tenir 3:1, donc `--ink-mute`, pas `--rule` |
| **2.4.7 Focus Visible, AA** — [w3.org](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html) | « Any keyboard operable user interface has a mode of operation where the keyboard focus indicator is visible » | Anneau 2 px `--electric`, décalé de 2 px (DA §2.9) |
| **2.4.11 Focus Not Obscured (Minimum), AA — nouveau en 2.2** — [w3.org](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html) | « When a user interface component receives keyboard focus, the component is **not entirely hidden** due to author-created content » | **Critique** : la feuille de correction monte du bas et peut masquer la ligne de transcription qui a le focus. La feuille doit donc **pousser le contenu** ou garantir que l'empan sélectionné reste visible au-dessus d'elle |
| **2.5.7 Dragging Movements, AA** — [w3.org](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html) | Toute fonction utilisant un glissement doit être réalisable **par un pointeur unique sans glisser**, sauf si le glissement est essentiel ou géré par le navigateur | Le **balayage latéral sur une ligne d'appel** (« ignorer ») doit avoir un équivalent par appui. Le curseur de lecture audio aussi : boutons ±10 s |
| **3.3.7 Redundant Entry, A** — [w3.org](https://www.w3.org/WAI/WCAG22/Understanding/redundant-entry.html) | Une information déjà saisie dans le même processus doit être auto-remplie ou sélectionnable | C'est **B8 rendu obligatoire par la norme**. Le pré-remplissage de la feuille de correction (§2.4) n'est pas un confort, c'est une conformité |
| **3.2.6 Consistent Help, A** — [w3.org](https://www.w3.org/WAI/WCAG22/Understanding/consistent-help.html) | Les mécanismes d'aide apparaissent **dans le même ordre relatif** sur l'ensemble des pages | Le lien « Nous appeler » occupe la même position dans tous les écrans |

## 6.2 Les contraintes du terrain

- **Gants mouillés, mains pleines, bruit.** Conséquence : **aucune action destructive ne vit dans la zone de pouce chaude** (**B3**), et « Révoquer une correction » est à ≥ 24 px de tout voisin fréquent.
- **Lumière de vitrine.** Le contraste `--ink` sur `--paper` à 17,4:1 est un avantage réel, pas un pédantisme.
- **Écoute impossible en salon.** L'audio n'est de toute façon pas enregistré par défaut : **la transcription doit tout porter**. Corollaire : **toute information disponible seulement à l'écoute est une information perdue**.
- **Ordre de tabulation = ordre visuel**, HTML sémantique avant ARIA (DA §2.9). Une console de supervision finit par être utilisée au clavier depuis le bureau, le soir — c'est le cas nominal du concept, pas une exception.

---

# 7. Notifications

## 7.1 Ce que dit la recherche

**Pielot & Rello, « Productive, Anxious, Lonely — 24 Hours Without Push Notifications », MobileHCI 2017** (**[F]**, PDF [pielot.org/pubs/PielotRello2017-MHCI-DoNotDisturb.pdf](https://pielot.org/pubs/PielotRello2017-MHCI-DoNotDisturb.pdf), consulté 2026-09-14) :

- **30 volontaires** ont désactivé toutes les alertes pendant 24 h, sur tous leurs appareils, comparé à une journée de référence.
- Volume mesuré : **médiane de 63,5 notifications par jour** par participant.
- Le résultat est un **dilemme, pas un verdict** : sans notifications, les participants se sont sentis **moins distraits et plus productifs**, mais aussi **incapables d'être aussi réactifs qu'attendu, ce qui a rendu certains anxieux**, et **moins connectés à leur groupe social**.
- **73,3 %** des participants ont exprimé l'intention de changer leurs réglages ; deux ans plus tard, **la moitié s'y tenait encore**.

→ La leçon n'est pas « notifier moins ». C'est que **l'anxiété vient de la crainte de rater ce qui était attendu de soi**. Pour un gérant, ce qui est attendu de lui, c'est de ne pas laisser un client en plan. **Donc : notifier peu, mais notifier sans faute ce qui engage un client réel.**

**NN/g — Indicators, Validations, and Notifications** (**[F]**, [nngroup.com/articles/indicators-validations-notifications](https://www.nngroup.com/articles/indicators-validations-notifications/), consulté 2026-09-14) donne la grille de tri :

- **Indicateurs** : contextuels, conditionnels, **passifs** — « They do not require that a user take action ».
- **Validations** : liées à l'action immédiate de l'utilisateur.
- **Notifications** : « not triggered by users' immediate actions », deux familles — **à action requise** (« often urgent and should be intrusive ») et **passives** (« typically not urgent and should be less intrusive »).
- Le piège documenté : « Passive notifications can easily be missed, since they require no user action. When the information provided by the notification is key to the understanding of the system, an easy-to-ignore passive notification can be problematic. »
- Et l'exigence de contexte : contrairement à une validation, une notification doit **s'expliquer elle-même**, parce que l'utilisateur pensait à autre chose.

**Android — Notification channels** (**[F]**, [developer.android.com/develop/ui/views/notifications/channels](https://developer.android.com/develop/ui/views/notifications/channels), consulté 2026-09-14) : depuis Android 8.0 (API 26), toute notification appartient à un canal. Cinq niveaux : `IMPORTANCE_HIGH` (son **+ affichage intrusif**), `IMPORTANCE_DEFAULT` (son seul), `IMPORTANCE_LOW`, `IMPORTANCE_MIN`, `IMPORTANCE_NONE`. **L'importance est fixée à la création du canal et ne peut plus être changée par le code** — seul l'utilisateur la modifie dans les réglages ; l'application peut lire `getImportance()` et ouvrir l'écran de réglage du canal.

→ **Conséquence d'architecture** : le découpage en canaux est **irréversible**. Il faut le décider maintenant, correctement, et ne plus y toucher.

**iOS** — les quatre niveaux d'interruption (`passive`, `active`, `timeSensitive`, `critical`) existent dans l'API, mais **aucune page Apple n'a pu être récupérée** (SPA React, seul le titre revient). **[NV]** : rien n'est cité de la documentation Apple.

**Taux d'ouverture comparés SMS / push / e-mail** : aucune source fiable atteinte. **[NV]** — aucun chiffre avancé.

## 7.2 Quoi notifier, et par quel canal

Quatre canaux, pas plus (**B4**), et l'importance de chacun est figée dès la première version (contrainte Android **[F]**) :

| Canal | Ce qui y passe | Importance Android | Canal de transport |
|---|---|---|---|
| **Ce qui engage un client** | RDV pris · RDV déplacé ou annulé · message laissé | `DEFAULT` (son, pas d'intrusion) | Poussée ; **SMS en repli** si l'application n'est pas installée |
| **Ce qui demande le gérant** | Escalade non aboutie (**taux d'impasse**) · urgence détectée · réclamation | `HIGH` (son + intrusion) | Poussée **et** SMS, sans attendre |
| **Ce qui est cassé** | **Confirmation orpheline** · échec d'écriture dans l'agenda · connecteur hors service | `HIGH` | Poussée + SMS + courriel |
| **Ce qui est administratif** | Quota atteint à 80 % · facture · fin d'essai | `LOW` (sans son) | Courriel, et **digest** dans l'application |

**Le fil de la journée, une fois, à heure choisie** : un seul résumé quotidien (défaut : **19 h**, modifiable) — « 7 appels, 4 rendez-vous, 1 à revoir ». C'est la réponse directe au dilemme de Pielot & Rello : le gérant n'a pas besoin de savoir en temps réel, il a besoin de **savoir qu'il n'a rien raté**.

**Ce qu'on ne notifie jamais** :
- chaque appel traité normalement — ce serait 63 notifications quotidiennes, soit exactement la médiane que l'étude mesure comme pathologique **[F]** ;
- un appel de démarchage filtré — il est **non facturé** (`01-CONCEPT` §7), donc invisible ;
- une correction appliquée — l'écran l'a déjà confirmée.

**Deux règles de rédaction**, tirées de NN/g **[F]** :
1. **Une notification s'explique seule.** « Rendez-vous pris » est inutilisable ; « Mme Tran, balayage, mardi 17 à 14 h — pris par l'agent » est une notification.
2. **Une notification à action requise porte l'action.** « Personne n'a pu prendre l'appel de M. Diallo (impasse, 14 h 32) » + **Rappeler** en action directe. Une notification qui ne fait qu'informer d'un problème est une notification qui crée de l'anxiété sans offrir de sortie.

**Quota** : notifié **une seule fois à 80 %**, puis à 100 %. Un rappel quotidien de quota est le prototype de la notification qui apprend à ignorer le canal.

---

# 8. Conformité Barthez

## 8.1 Préséance appliquée

Le projet est un **produit Marpeap** : la règle §0 de `Regles-Barthez` s'applique — si la console adopte les tokens sombres du Design System Marpeap, **on garde ses couleurs mais on applique la structure Barthez** : grille, hiérarchie typographique, densité, échelle de contraste, marginalia, motion, tailles de cibles. La console de supervision relève par ailleurs du **registre produit** au sens §2.7 : la profondeur y sert (ce qui est posé sur quoi, ce qui flotte), contrairement au registre éditorial. **Jamais les deux registres dans une même vue.**

Si un thème clair est retenu, la palette est celle de la DA : `--paper #F2F0EB`, `--ink #0A0A0C`, `--electric #0A0AEA` (**accent unique, ≤ 5 % de surface**), `--ink-mute #6A6765`, `--rule #A19E99`, `--wash #DBDBF7`.

## 8.2 Gate de conformité — §3.3

| | Point | Statut | Preuve dans ce document |
|---|---|---|---|
| **B1** | Chaque pattern non standard a une justification écrite | ✅ | Le geste de correction est calqué sur *Filter messages like these* de Gmail et sur la correction automatique d'iOS, tous deux **[F]** §2.1.6. L'écran de revue reprend le triptyque du marché §3.2. Le seul pattern réellement neuf — la correction depuis un empan de transcription — est justifié par un trou de marché documenté §3.3 n°4 |
| **B2** | Une action primaire par écran ; un défaut recommandé partout où il y a choix | ✅ | Tableau §1.3, colonne « action primaire ». Défauts : « toujours » pour la portée d'une correction §2.7, 19 h pour le fil quotidien §7.2. La liste des fautes n'invoque pas Hick — c'est une grille de tri, cf. limite §B2 |
| **B3** | Cibles ≥ 44 px, écarts ≥ 8 px, CTA mobile en zone de pouce | ✅ | §6.1 ligne 2.5.8 ; feuille de correction montée du bas §2.4 ; action destructive à ≥ 24 px §6.2 |
| **B4** | Aucun groupe non scannable > 5 éléments | ✅ | Navigation à 4 entrées §1.2 ; pile à revoir plafonnée à 5 §1.3 ; 4 canaux de notification §7.2 ; motifs d'escalade ≤ 5 §1.3. Les 7 fautes sont une grille triée, jamais affichée entière — 2 à 3 proposées §2.4 |
| **B5** | Règle 1:2 respectée ; aucun groupe qui ne tient que par une bordure | ✅ | §4.1, interligne intra-tour ≤ moitié de l'écart inter-tours, sans bordure ni fond |
| **B6** | Une seule emphase forte par vue ; jamais la couleur seule | ✅ | E0 : « 1 à revoir » est la seule emphase §1.3. Un seul aplat `--electric`. Locuteurs distingués par le retrait et le label §4.1. La mention « appliqué à coup sûr » est un **mot** §2.6.1 |
| **B7** | Positions 1 et n portent l'essentiel | ✅ | Navigation §1.2 ; E0 §1.3 ; premier et dernier tour épinglés §4.1 ; registre E4 §2.9 |
| **B8** | Aucun champ que le système pourrait déduire ; défauts visibles et modifiables | ✅ | Tableau de pré-remplissage §2.4 ; un seul clavier possible (F5), dictée acceptée. Renforcé par **3.3.7 Redundant Entry** §6.1. Limite respectée : tout défaut reste **visible et modifiable** — c'est l'objet même de E4 |
| **B9** | Tout bouton a `loading`/succès/erreur ; tout écran a un état vide ; budgets tenus | ✅ | Budgets §5.5 ; états vides colonne 4 du §1.3 ; écriture optimiste avec échec **visible**, jamais silencieux |
| **B10** | Le pic et la fin nommés par écrit ; aucune confirmation en cul-de-sac | ✅ | **§2.9**, nommés explicitement. L'écran post-correction porte une phrase de conséquence et une action suivante |
| **DA** | Palette, accent ≤ 5 %, zéro dégradé, zéro glow, zéro lift uniforme | ✅ | §8.1. Le survol d'une ligne d'appel change la **bordure**, jamais la position (§2.8 de la doctrine) |
| **P** | Aucune ombre `rgba(0,0,0,…)` ; ≥ 2 couches ; rehaut ; élévation par rôle ; densité au niveau 1 | ✅ | Registre produit §8.1. **Le journal d'appels et la transcription sont des listes denses → niveau 1, ombre de contact seule** (P4 : « l'ombre portée répétée fait de la bouillie »). La feuille de correction est une superposition → niveau 4 |
| **A11y** | Contrastes, focus visible, `prefers-reduced-motion`, ordre de tabulation | ✅ | §6.1 intégral. **2.4.11** traité explicitement pour la feuille de correction |
| **Anti-LLM** | Score < 3 | ✅ | Aucun lift uniforme, aucune grille de cartes décorative, aucune icône à la place d'une démonstration. Les comparaisons du §2.1 sont des **tableaux de faits sourcés**, pas des pictogrammes |

## 8.3 Les interdits qui ont réellement mordu

| Tentation écartée | Interdit violé |
|---|---|
| Afficher un pourcentage de confiance à côté de chaque entité | **DA §2.5** (icône/chiffre décoratif à la place d'une démonstration) et **B6** — et surtout l'avertissement de Google : « It may not be set … and it may not be accurate » **[F]** §4.3 |
| Deux boutons pleins sur l'écran de revue (« Corriger » et « Écouter ») | **B6** — « Écouter » est un bouton secondaire, bordure 1 px |
| Colorer en rouge les appels ratés dans le journal | **DA §2.5** — le mauvais exemple est **gris et éteint**, jamais rouge. La couleur reste à ce qui est juste. Le motif est porté par un **micro-label** |
| Un onglet « Analytique » | **B2 / B4** — cinquième entrée de navigation sans valeur propre |
| Un assistant conversationnel pour décrire la correction (façon Conductor) | **Contrainte produit** — c'est un prompt, et **B8** est mal servi par une conversation : le système sait déjà ce qui a raté, il n'a pas à le demander |
| Une carte par KPI avec `translateY` au survol | **DA §2.8** — signature LLM. Le survol change la bordure |

---

# 9. Ce que cette passe laisse ouvert

1. **Le nom des sept fautes en langue de comptoir.** Les libellés du §2.3 sont des propositions **[H]** ; ils doivent être testés à l'oral sur trois gérants avant d'être figés. Un libellé de faute mal nommé annule toute la boucle.
2. **Le seuil de soulignement d'incertitude.** Deepgram recommande **0,65** comme point de départ et donne la formule adaptative **[F]** ; la valeur juste pour du français téléphonique 8 kHz se mesure sur le corpus de régression, elle ne se recopie pas.
3. **Le rythme du battement de cœur SSE** — **[NV]**, aucune valeur officielle. À mesurer sur appareil réel.
4. **iOS Time Sensitive** — **[NV]** intégralement. Aucune page Apple n'a répondu ; à revérifier avant d'écrire le code des notifications, car le pendant Android est figé à la création du canal **[F]**.
5. **La mise en évidence d'entités (puces Gmail, détecteurs Apple)** — **[NV]** cette session, patron connu mais non vérifié à la source.
6. **Ce qui se passe quand deux corrections F4 se contredisent sur des jours différents** — le modèle d'arbitrage §2.5.1 les met en `en_conflit`, mais l'écran d'arbitrage n'est pas dessiné.
7. **Le cas multi-établissement** : le registre E4 est pensé pour un site. Slang.ai expose un classement par site **[R]** ; à reprendre si un client en exploite plusieurs.

---

# 10. Sources

**Boucle de correction**
- Intercom Fin — Guidance : https://fin.ai/help/en/articles/13975768-provide-fin-ai-agent-with-specific-guidance (2026-09-14) **[F]**
- Intercom Fin — Content gap recommendations : https://fin.ai/help/en/articles/13975989-use-ai-powered-content-recommendations-to-improve-fin (2026-09-14) **[F]**
- Intercom Fin — Versions et publication : https://fin.ai/help/en/articles/14324571-manage-procedure-versions-and-publishing (2026-09-14) **[F]**
- Intercom Fin — Simulations vs Batch tests vs Previews : https://fin.ai/help/en/articles/14077180-simulations-vs-batch-tests-vs-previews (2026-09-14) **[F]**
- Zendesk — Rapport de potentiel d'automatisation : https://support.zendesk.com/hc/en-us/articles/9877546283930-Viewing-and-using-the-automation-potential-report-to-create-or-enhance-AI-agents (2026-09-14) **[F]**
- Zendesk — Knowledge copilot (EAP) : https://support.zendesk.com/hc/en-us/articles/10799529609498-Using-knowledge-copilot-to-generate-and-maintain-your-knowledge-base-EAP (2026-09-14) **[F]**
- LangSmith — Few-shot evaluators : https://docs.langchain.com/langsmith/create-few-shot-evaluators (2026-09-14) **[F]**
- LangSmith — Annotation queues : https://docs.langchain.com/langsmith/annotation-queues (2026-09-14) **[F]**
- Retell — Debug your agent response : https://docs.retellai.com/test/llm-playground-debug.md (2026-09-14) **[F]**
- Retell — Test & improve with Conductor : https://docs.retellai.com/conductor/test-and-improve.md (2026-09-14) **[F]**
- Retell — Review & apply changes : https://docs.retellai.com/conductor/review-changes.md (2026-09-14) **[F]**
- Vapi — Run and maintain tests : https://docs.vapi.ai/test/run-and-maintain-tests.md (2026-09-14) **[F]**
- Vapi — Evals quickstart : https://docs.vapi.ai/observability/evals-quickstart.md (2026-09-14) **[F]**
- Vapi — Monitoring quickstart : https://docs.vapi.ai/observability/monitoring-quickstart.md (2026-09-14) **[F]**
- Vapi — Versioning avec assistants et outils : https://docs.vapi.ai/assistants/versioning/versioning-with-assistants-and-tools.md (2026-09-14) **[F]**
- Apple — Auto-Correction, texte prédictif, remplacement de texte : https://support.apple.com/en-us/104995 (2026-09-14) **[F]**
- Google — Créer des règles de filtrage Gmail : https://support.google.com/mail/answer/6579 (2026-09-14) **[F]**

**Écrans de revue d'appel** — Vapi (`call-analysis.md`, `call-recording.md`, `calls/call-ended-reason`) **[F]** · Retell (`features/session-history.md`, `post-call-analysis-overview.md`, `reliability/debug-call-disconnect.md`, `reliability/check-actual-latency.md`) **[F]** · ElevenLabs (`elevenlabs.io/docs/eleven-agents/dashboard`, `/agent-analysis`, `/agent-analysis/success-evaluation`, `/customization/privacy`) **[F/NV]** · Fresha (`fresha.com/for-business/features/ai-concierge`) **[R]** · Zenoti (`zenoti.com/ai-receptionist`) **[R]** · Boulevard (`joinblvd.com/features/ai-receptionist`) **[R]** · RingCentral (`ringcentral.com/ai-receptionist.html`) **[R]** · Rosie (`heyrosie.com`) **[R]** · Slang.ai (`slang.ai/product`) **[R]** — toutes 2026-09-13/14.

**Transcription**
- Deepgram — Confidence scores : https://developers.deepgram.com/docs/confidence.md (2026-09-14) **[F]**
- AssemblyAI — Speech recognition (`words[]`, `confidence`, `speaker`) : https://www.assemblyai.com/docs/speech-to-text/speech-recognition (2026-09-14) **[F]**
- Google Cloud STT — Basics (avertissement sur `confidence`) : https://docs.cloud.google.com/speech-to-text/docs/basics (2026-09-14) **[F]**
- Otter.ai — Features : https://otter.ai/features (2026-09-13/14) **[F]**

**Temps réel**
- Grigorik, *High Performance Browser Networking* — Mobile Networks (RRC, énergie de traîne, cas Pandora) : https://hpbn.co/mobile-networks/ (2026-09-14) **[F]**
- MDN — Using server-sent events : https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events (2026-09-14) **[F]**
- MDN — WebSockets API : https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API (2026-09-14) **[F]**
- MDN — Page Visibility API : https://developer.mozilla.org/en-US/docs/Web/API/Page_Visibility_API (2026-09-14) **[F]**

**Accessibilité** — W3C *Understanding WCAG 2.2*, consultées le 2026-09-14 **[F]** : [2.5.8](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html) · [1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) · [1.4.11](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html) · [2.4.7](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html) · [2.4.11](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html) · [2.5.7](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html) · [3.3.7](https://www.w3.org/WAI/WCAG22/Understanding/redundant-entry.html) · [3.2.6](https://www.w3.org/WAI/WCAG22/Understanding/consistent-help.html)

**Notifications**
- Pielot & Rello, *Productive, Anxious, Lonely — 24 Hours Without Push Notifications*, MobileHCI 2017 : https://pielot.org/pubs/PielotRello2017-MHCI-DoNotDisturb.pdf (2026-09-14) **[F]**
- NN/g — Indicators, Validations, and Notifications : https://www.nngroup.com/articles/indicators-validations-notifications/ (2026-09-14) **[F]**
- Android — Create and manage notification channels : https://developer.android.com/develop/ui/views/notifications/channels (2026-09-14) **[F]**
- Apple HIG / UserNotifications — **[NV]**, aucune page récupérable (SPA)

**Doctrine interne** — `/home/marpeap/_vault/12-Processus/Regles-Barthez.md` (lu intégralement le 2026-09-13) · `docs/01-CONCEPT-PRODUIT.md` · `docs/02-ARCHITECTURE.md` · `docs/00-SYNTHESE.md` · `docs/recherche2/A6-metier-salon.md`
