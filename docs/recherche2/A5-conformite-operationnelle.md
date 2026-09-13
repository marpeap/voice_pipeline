# A5 — Conformité opérationnelle d'un agent vocal IA vendu en SaaS

> **Périmètre** : éditeur français (SASU) qui vend à des commerçants (salons, restaurants) un agent vocal IA répondant au téléphone à leur place. STT et LLM fournis par des prestataires américains. Numéros achetés chez Telnyx / OVHcloud et affectés aux clients.
> **État du droit arrêté au 13–14 septembre 2026.** Toutes les URL ont été consultées les 13 et 14/09/2026.
> **Ce document n'est pas un cours de droit** : il liste ce qu'il faut faire, écrire et paramétrer. Il se termine (§10) par la liste des livrables, chacun rattaché au texte qui le fonde.

## Barème de fiabilité

| Marque | Sens |
|---|---|
| **[F]** | Source primaire officielle lue directement (EUR-Lex, Légifrance, CNIL, EDPB, Arcep, service-public.gouv.fr) |
| **[F2]** | Source secondaire fiable ou documentation contractuelle d'un fournisseur (Telnyx, OVHcloud) |
| **[H]** | Hypothèse raisonnée, adossée à des [F], à faire valider par un avocat |
| **[NV]** | Non vérifié — recherche tentée et échouée, déclarée comme telle |

## Aveu de méthode — lire avant d'exploiter ce document

**Le budget `WebSearch` de la session était épuisé (200/200) dès la première requête, pour les trois volets de la recherche.** Toute la recherche a donc été conduite en **`WebFetch` / accès direct**, comme la consigne l'autorisait. Conséquences :

- Impossible de « chercher » : il a fallu **naviguer** (tables des matières Légifrance, moteur GET `legifrance.gouv.fr/search/code?...`, `sitemap.xml` d'Arcep et de la CNIL, fiches « Document information » d'EUR-Lex).
- **Légifrance et economie.gouv.fr sont derrière Cloudflare** : 403 en `curl`. Contourné par navigateur réel (MCP chrome-devtools) pour Légifrance. **`economie.gouv.fr` / DGCCRF est resté inaccessible sur toutes les URL essayées — [NV]**.
- `courdecassation.fr` (Judilibre) est rendu en JavaScript : contenu vide côté fetch. **Aucune recherche de jurisprudence française n'a pu aboutir — [NV]** (voir §6).
- `canlii.org` et `decisions.civilresolutionbc.ca` : 403. La décision canadienne Air Canada n'a pas pu être vérifiée à la source (voir §6).
- Pour les articles du Code du travail, Légifrance ayant refusé l'accès sur ce volet, le texte vient de **`code.travail.gouv.fr` (Code du travail numérique, service public du ministère du Travail)** — source officielle, mais **pas Légifrance** : réserve explicite.

**Aucune source n'a été remplacée par un blog ou un cabinet d'avocats.** Ce qui n'a pas été trouvé est marqué [NV] avec la recherche exacte qui a échoué.

---

## 0. Trois prémisses de la commande étaient inexactes — corrigées ici

| Prémisse de la commande | Réalité vérifiée | Marque |
|---|---|---|
| « Loi du 30 juin **2024** contre les fraudes aux aides à la rénovation énergétique, **art. 5** » | **LOI n° 2025-594 du 30 juin 2025 contre toutes les fraudes aux aides publiques, article 13** | [F] |
| « Déclaration Arcep au titre de l'article L. 33-1 CPCE » | **La déclaration préalable n'existe plus** depuis l'ordonnance n° 2021-650 du 26 mai 2021 | [F] |
| « MAN prévu à l'art. **L. 44-4** CPCE, en vigueur le **1er octobre 2024** » | Le mécanisme est au **IV de l'article L. 44**, en vigueur **depuis le 25 juillet 2023** | [F] |
| (bonus) « Mentions légales art. 6 III LCEN » | Déplacées à l'**article 1-1 de la LCEN** par la loi SREN n° 2024-449 du 21 mai 2024, art. 48 | [F] |
| (bonus) « Référentiel CNIL du 2 avril 2026 sur les enregistrements d'appels » | Ce qui a été publié le 2 avril 2026 est le **référentiel « durées de conservation — gestion des ressources humaines »**, sans numéro de délibération (droit souple), qui **contient** une rubrique « écoute et enregistrement des conversations téléphoniques ». Aucun référentiel autonome « enregistrements d'appels » à cette date | [F] |

**Un fait majeur non anticipé par la commande : le « Digital Omnibus » IA n'est plus une proposition, c'est du droit positif.** Voir §1.7.

---

## 1. AI Act — article 50

Texte de base : **règlement (UE) 2024/1689 du 13 juin 2024**, JO L du 12.7.2024.
https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=OJ:L_202401689 — 13/09/2026. **[F]**
Modifié par le **règlement (UE) 2026/1744 du 8 juillet 2026** (omnibus numérique sur l'IA), JO L du 24.7.2026.
https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=CELEX:32026R1744 — 14/09/2026. **[F]**

### 1.1 Texte exact — §1, §2, §5

**§1 — interaction directe avec des personnes physiques** [F] :
> « Les fournisseurs veillent à ce que les systèmes d'IA destinés à interagir directement avec des personnes physiques soient conçus et développés de manière que les personnes physiques concernées soient informées qu'elles interagissent avec un système d'IA, sauf si cela ressort clairement du point de vue d'une personne physique normalement informée et raisonnablement attentive et avisée, compte tenu des circonstances et du contexte d'utilisation. […] »

**§2 — marquage lisible par machine** [F] :
> « Les fournisseurs de systèmes d'IA, y compris de systèmes d'IA à usage général, qui génèrent des contenus de synthèse de type audio, image, vidéo ou texte, veillent à ce que les sorties des systèmes d'IA soient marquées dans un format lisible par machine et identifiables comme ayant été générées ou manipulées par une IA. Les fournisseurs veillent à ce que leurs solutions techniques soient aussi efficaces, interopérables, solides et fiables que la technologie le permet, compte tenu des spécificités et des limites des différents types de contenus, des coûts de mise en œuvre et de l'état de la technique généralement reconnu […] Cette obligation ne s'applique pas dans la mesure où les systèmes d'IA remplissent une fonction d'assistance pour la mise en forme standard ou ne modifient pas de manière substantielle les données d'entrée fournies par le déployeur ou leur sémantique […] »

**§5 — forme et moment** [F] :
> « Les informations visées aux paragraphes 1 à 4 sont fournies aux personnes physiques concernées de manière claire et reconnaissable au plus tard au moment de la première interaction ou de la première exposition. Les informations sont conformes aux exigences applicables en matière d'accessibilité. »

**§3 — reconnaissance des émotions** [F] : obligation portée par **le déployeur** (le commerçant). ⚠️ **S'active si le produit fait de l'analyse de sentiment / détection d'émotion sur la voix.** La définition art. 3, 39) n'a pas été extraite — **[NV]**, à vérifier avant toute fonctionnalité de ce type.

**§4 — hypertrucages** [F] : obligation du **déployeur**. Sans objet ici en principe (l'agent ne fabrique pas de deepfake d'une personne réelle), **sauf si la voix de l'agent clone celle du gérant** — cas à écarter par conception. [H]

**§7 — codes de bonne pratique : REMPLACÉ au 27/07/2026** par l'art. 1er, 20) du règlement 2026/1744 [F]. C'est désormais **la Commission** (et non le Bureau de l'IA) qui pilote ; l'habilitation à **approuver** un code par acte d'exécution est supprimée. **Aucun code de bonne pratique adopté sous l'art. 50 §7 n'a été trouvé — [NV]**.

### 1.2 Date d'application — l'article 50 est en vigueur

**Article 113** [F] : « Il est applicable à partir du **2 août 2026**. Toutefois : a) les chapitres I et II […] 2 février 2025 ; b) le chapitre III, section 4, le chapitre V, le chapitre VII, le chapitre XII et l'article 78 […] 2 août 2025 […] ; c) l'article 6, paragraphe 1 […] 2 août 2027. »

L'article 50 est au **chapitre IV**, qui ne figure dans **aucune** dérogation.
→ **L'article 50 s'applique depuis le 2 août 2026. Au 14 septembre 2026, il est en vigueur depuis six semaines.** [F]

**L'omnibus n'a pas reporté cette date** : le règlement 2026/1744 modifie l'art. 113 aux points a), c) et ajoute un d), **sans toucher au chapitre IV**. [F]

**Une seule transitoire concerne l'art. 50** — nouvel **art. 111 §4**, inséré par l'art. 1er, 39) b) du règlement 2026/1744 [F] :
> « Les fournisseurs de systèmes d'IA […] qui génèrent des contenus de synthèse de type audio, image, vidéo ou texte, qui ont été mis sur le marché **avant le 2 août 2026** prennent les mesures nécessaires pour se conformer à **l'article 50, paragraphe 2**, d'ici au **2 décembre 2026**. »

> 🔴 **Échéancier produit** :
> - **Annonce vocale (§1) : due MAINTENANT, sans transition, dans tous les cas.**
> - **Marquage machine-readable (§2)** : due **immédiatement** si le produit est mis sur le marché après le 2 août 2026 ; due au **2 décembre 2026** s'il l'était avant. [F] / [H] sur la date de mise sur le marché du produit, qui dépend de faits internes.

### 1.3 Qui porte l'obligation

**Art. 3** [F] :
> « 3) "fournisseur", une personne physique ou morale […] qui développe ou fait développer un système d'IA […] et le met sur le marché ou met le système d'IA en service sous son propre nom ou sa propre marque, à titre onéreux ou gratuit ;
> 4) "déployeur", une personne physique ou morale […] utilisant sous sa propre autorité un système d'IA sauf lorsque ce système est utilisé dans le cadre d'une activité personnelle à caractère non professionnel ; »

| § | Texte | Ici |
|---|---|---|
| §1 annonce IA | « **Les fournisseurs** veillent à ce que les systèmes […] soient **conçus et développés** de manière que… » | **L'éditeur SASU** [H] |
| §2 marquage | « **Les fournisseurs** […] veillent à ce que les sorties soient marquées » | **L'éditeur SASU** [H] |
| §3 émotions | « Les **déployeurs** » | Le commerçant |
| §4 hypertrucages | « Les **déployeurs** » | Le commerçant |

> 🔴 **La charge de l'article 50 pèse quasi intégralement sur l'éditeur, et elle n'est pas transférable par contrat** : le §1 est une obligation **de conception et de développement**. Une clause CGV « le client est responsable de l'annonce » ne décharge de rien. [H]

⚠️ **Piège marque blanche — article 25.** Un déployeur **devient fournisseur** s'il appose son nom ou sa marque sur le système ou en modifie la destination. Le modèle « éditeur hôte » (Crenolo, Inkra, un tiers qui intègre le greffon sous sa marque) **fait basculer la qualification**. Le texte de l'art. 25 n'a pas été extrait — **[NV], à traiter en priorité 1 avant toute offre white-label.** Noter que le règlement 2026/1744 a **ajouté l'art. 25 §§2 et 4 à la liste des manquements sanctionnés à 15 M€ / 3 %** (nouveau point d bis) de l'art. 99 §4) [F].

### 1.4 Forme acceptable de l'annonce vocale

Le texte **n'impose aucune formule, aucun script, aucune durée**. Il impose trois qualités cumulatives (§5) [F], dont la lecture opérationnelle est [H] :

1. **« claire »** → intelligible, sans jargon ;
2. **« reconnaissable »** → perceptible comme telle, **pas noyée** dans un flux commercial ni débitée à toute vitesse ;
3. **« au plus tard au moment de la première interaction »** → **dans les premières secondes du décroché, avant tout échange de fond**. Une annonce placée après la collecte d'une information auprès de l'appelant est **hors délai**.

**Accessibilité** : renvoi sans texte nommé. Sur un canal vocal : débit, articulation, volume. Le texte de référence exact (directive (UE) 2019/882) n'a pas été vérifié — **[NV]**.

#### L'exception « évident pour une personne raisonnablement avisée » — ne pas s'y fier

**Considérant 132** [F] :
> « […] les personnes physiques devraient être avisées qu'elles interagissent avec un système d'IA, sauf si cela ressort clairement du point de vue d'une personne physique normalement informée et raisonnablement attentive et avisée […] Lors de la mise en œuvre de cette obligation, **les caractéristiques des personnes physiques appartenant à des groupes vulnérables en raison de leur âge ou d'un handicap devraient être prises en compte** dans la mesure où le système d'IA est destiné à interagir également avec ces groupes. »

> 🔴 **Verdict [H], solidement étayé : ne PAS se reposer sur cette exception.** Trois raisons tirées du texte :
> 1. Le standard est celui d'une personne « normalement informée », pas d'un early adopter. Qui appelle un salon n'a aucune raison de supposer qu'une IA décroche.
> 2. **La qualité du produit joue contre lui** : plus la voix TTS est naturelle, moins « cela ressort clairement ». L'exception s'éteint à mesure que le produit s'améliore.
> 3. Le considérant 132 impose de tenir compte des personnes vulnérables « en raison de leur âge » — or la clientèle téléphonique d'un salon ou d'un restaurant en comprend structurellement.
>
> **Conséquence produit : annonce systématique, dès le décroché, sur tous les appels (entrants ET sortants), NON DÉSACTIVABLE par le commerçant.** Le réglage `annonce_ia: true # non désactivable` déjà présent dans `01-CONCEPT-PRODUIT.md` est juridiquement correct — le garder tel quel.

### 1.5 Marquage des contenus audio générés (§2) — s'applique, et le considérant 133 n'exonère pas

**Analyse [H]** : une voix TTS est **un contenu de synthèse de type audio**. Le §2 ne comporte **aucune exclusion pour le temps réel, la téléphonie ou la conversation**. Les deux seules exclusions (mise en forme standard / absence de modification substantielle de la sémantique) ne jouent pas : l'agent **génère de la parole nouvelle**. → **le §2 s'applique.**

**Considérant 133** — ce qu'il dit réellement [F] :
> « […] De telles techniques et méthodes devraient être **aussi fiables, interopérables, efficaces et solides que la technologie le permet**, et tenir compte des techniques disponibles ou d'une combinaison de ces techniques, telles que **les filigranes, les identifications de métadonnées, les méthodes cryptographiques permettant de prouver la provenance et l'authenticité du contenu, les méthodes d'enregistrement, les empreintes digitales** ou d'autres techniques, selon qu'il convient. Lorsqu'ils mettent en œuvre cette obligation, les fournisseurs devraient également tenir compte **des spécificités et des limites des différents types de contenu**, ainsi que des évolutions technologiques […] tels qu'elles ressortent de l'état de la technique généralement reconnu. […] Dans un souci de proportionnalité, il convient d'envisager que cette obligation de marquage ne s'applique pas aux systèmes d'IA qui remplissent une fonction d'assistance pour la mise en forme standard ou […] qui ne modifient pas de manière substantielle les données d'entrée […] »

> ❌ **Le considérant 133 ne contient AUCUNE clause générale d'exonération pour « marquage impraticable ». Cette clause n'existe pas.** [F]
> ✅ Ce qu'il contient est un **standard de moyens modulé**, glissant avec l'état de la technique.
>
> 🔴 **Traduction** : la ligne de défense n'est pas « c'est impossible en temps réel sur du G.711 8 kHz », c'est **« voici ce que l'état de la technique permet pour de l'audio téléphonique temps réel, voici ce que nous avons implémenté, et voici pourquoi »**. Cela suppose :
> - un **dossier technique écrit** : options évaluées (watermarking audio type AudioSeal/Perth, métadonnées C2PA, marqueurs dans la signalisation SIP, journalisation d'origine), choix retenu, justification des rejets ;
> - une **réévaluation périodique** (le standard évolue) ;
> - un **suivi des codes de bonne pratique** de l'art. 50 §7.
>
> **Un éditeur qui n'implémente rien et n'a rien documenté ne peut invoquer ni le §2 ni le considérant 133.** Le dossier technique est la mesure de conformité la plus urgente après l'annonce vocale.

### 1.6 Sanctions — et le plafond PME qui change tout

**Article 99 §4** [F] :
> « La non-conformité avec l'une quelconque des dispositions suivantes […] fait l'objet d'une amende administrative pouvant aller jusqu'à **15 000 000 EUR** ou, si l'auteur de l'infraction est une entreprise, jusqu'à **3 % de son chiffre d'affaires annuel mondial total** réalisé au cours de l'exercice précédent, **le montant le plus élevé étant retenu** : […] **g) les obligations de transparence pour les fournisseurs et les déployeurs conformément à l'article 50.** »

**Article 99 §6 — le plafond PME** [F] :
> « Dans le cas des **PME**, y compris les jeunes pousses, chaque amende visée au présent article s'élève au maximum aux pourcentages ou montants visés aux paragraphes 3, 4 et 5, **le chiffre le plus FAIBLE étant retenu**. »

> 🔴 **Pour une SASU qualifiée PME, l'exposition maximale n'est PAS 15 M€ : c'est le plus FAIBLE de 15 M€ et 3 % du CA mondial — donc 3 % du CA.** Sur un CA de 500 k€, le plafond théorique est de **15 000 €**. [F]
> C'est l'élément déterminant pour **dimensionner l'effort de conformité** : le risque AI Act est réel mais borné ; le risque RGPD et le risque DGCCRF (§4) sont, en montant, bien supérieurs.
> Le règlement 2026/1744 ajoute un §6 bis étendant la même logique aux *small mid-caps* [F].
> **Réserve [H]** : la définition « PME » retenue par le règlement IA n'a pas été vérifiée — **[NV]**.

**Article 99 §7** : critères de modulation, dont « le degré de responsabilité compte tenu des **mesures techniques et organisationnelles mises en œuvre** ». → **le dossier technique du §1.5 est directement un facteur atténuant.** [F]

**Date d'application des sanctions** : l'article 99 est au **chapitre XII**, applicable depuis le **2 août 2025** (art. 113, b)) [F]. Mais on ne peut être sanctionné que pour la violation d'une obligation applicable : **l'exposition au titre de l'art. 99 §4 g) court depuis le 2 août 2026** [H].

### 1.7 Autorité française de surveillance de marché — [NV] assumé

Quatre recherches Légifrance distinctes (texte intégral « 2024/1689 » tous fonds ; « surveillance du marché intelligence artificielle » ; titres « intelligence artificielle » — 115 résultats ; titres « adaptation au droit de l'Union européenne » — 90 résultats), **toutes négatives** : aucune loi, aucun décret, aucun arrêté français désignant une autorité de surveillance du marché au titre de l'AI Act. [F sur les recherches]
`economie.gouv.fr` : 403 Cloudflare puis 404 sur les deux chemins de recherche du site. `digital-strategy.ec.europa.eu` : échec réseau.

> **[NV] — Conclusion honnête : non trouvé, pas « inexistant ».**
> **[H]** L'hypothèse DGCCRF est plausible (autorité de surveillance du marché de droit commun au titre du règlement (UE) 2019/1020, auquel l'AI Act renvoie) **mais n'est pas vérifiée et ne doit pas être présentée comme acquise.**
> À reprendre dès que WebSearch est disponible, sous trois angles : (1) liste des autorités notifiées publiée par la Commission au titre de l'art. 70 §2 ; (2) loi DDADUE 2026 ; (3) communiqués DGCCRF.

### 1.8 Effet de l'omnibus numérique 2026 — ADOPTÉ, et sans répit sur l'article 50

**Chaîne de vérification** [F] :
- Proposition **COM(2025) 836 final** — https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:52025PC0836
- Fiche de procédure **2025/0359/COD** : « **Adopted act: 32026R1744 — Adopted on: 08/07/2026** »
- Acte : **RÈGLEMENT (UE) 2026/1744 du 8 juillet 2026**, JO L du **24.7.2026**, **entrée en vigueur le 27 juillet 2026** (art. 4 : troisième jour suivant la publication ; confirmé par le nouveau point d) de l'art. 113).
- ⚠️ À ne pas confondre avec **COM(2025) 837** (omnibus « général » — RGPD, ePrivacy, NIS2, Data Act) ni **COM(2025) 838**.
- ⚠️ Écart de périmètre avec la proposition : l'acte adopté modifie **aussi le règlement (UE) 2023/1230** (machines).

| Point | Statut | Détail |
|---|---|---|
| Date d'application de l'art. 50 | ✅ **INCHANGÉE — 2 août 2026** | Chapitre IV non touché [F] |
| Art. 50 §1 (annonce IA) | ✅ **INCHANGÉ** | [F] |
| Art. 50 §2 (marquage) | ✅ texte inchangé, **transitoire ajoutée** | Art. 111 §4 : 2 décembre 2026 pour les systèmes mis sur le marché avant le 2 août 2026 [F] |
| Art. 50 §§3-6 | ✅ **INCHANGÉS** | [F] |
| Art. 50 §7 | 🔄 **REMPLACÉ** | Commission au lieu du Bureau de l'IA [F] |
| Art. 99 §4 g) (sanction art. 50) | ✅ **INCHANGÉ** | [F] |
| Haut risque (ch. III, sect. 1-3) | 🔄 **REPORTÉ** | 2 déc. 2027 (annexe III) / 2 août 2028 (annexe I) [F] — sans objet ici sauf requalification |
| Art. 4 (maîtrise de l'IA) | 🔄 **ASSOUPLI** | Devient « prendre des mesures pour soutenir le développement de la maîtrise de l'IA » du personnel (cons. 67) [F] — concerne fournisseur **et** déployeur |
| Bacs à sable réglementaires | 🔄 | Opérationnels au plus tard le 2 août 2027 (art. 57 §1 modifié) [F] |

> 🔴 **L'omnibus n'offre aucun répit sur l'article 50.** Le seul allègement calendaire est la transitoire de 4 mois sur le marquage §2.

**Reste [NV] sur l'omnibus** : le détail des **nouvelles pratiques interdites** art. 5 §1 b bis) et b ter) et §§1 bis/1 ter, **applicables au 2 décembre 2026**, sanctionnées à **35 M€ / 7 %**. **À dépouiller en priorité 1** : il faut vérifier qu'aucune ne vise l'usurpation de voix humaine ou la manipulation par agent conversationnel.

---

## 2. RGPD — l'éditeur, le commerçant, l'appelant

### 2.1 Qualification : sous-traitant par principe, responsable dès qu'il réutilise

**Art. 4(8) RGPD** [F] : « "sous-traitant", la personne physique ou morale […] qui traite des données à caractère personnel **pour le compte du responsable du traitement** ».
**Art. 28.10** — la clause de bascule [F] : « si, en violation du présent règlement, **un sous-traitant détermine les finalités et les moyens du traitement, il est considéré comme un responsable du traitement** pour ce qui concerne ce traitement. »
https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=CELEX:32016R0679 — 13/09/2026.

**Lignes directrices EDPB 07/2020**, v2.1 (PDF FR) : https://www.edpb.europa.eu/system/files/documents/2023-10/edpb_guidelines_202007_controllerprocessor_final_fr.pdf — 13/09/2026. [F]
- **§36** : « Le responsable du traitement doit décider **à la fois** des finalités et des moyens […] **À l'inverse, la partie qui agit comme sous-traitant ne peut jamais déterminer la finalité du traitement.** »
- **§40 — moyens essentiels / non essentiels** : les moyens essentiels (« quelles données », « pendant combien de temps », « qui aura accès », « quelles catégories de personnes ») « **doivent être décidés par le responsable du traitement** » ; les moyens non essentiels (choix d'un matériel, d'un logiciel, mesures de sécurité concrètes) « **peuvent être laissées à la discrétion du sous-traitant** ».
- **§30** : un service « **précisément défini au préalable** », « à prendre ou à laisser », **reste de la sous-traitance** tant que le fournisseur ne traite pas à ses propres fins.
- **§65 — le piège de la plateforme** : « **L'utilisation d'un système technique existant n'exclut pas une responsabilité conjointe** du traitement lorsque les utilisateurs du système peuvent décider du traitement de données à caractère personnel à effectuer dans ce contexte. » → **directement pertinent pour le modèle « greffon + éditeur hôte »** de `01-CONCEPT-PRODUIT.md`.
- **§152 — sous-traitants ultérieurs** : « une **liste des sous-traitants ultérieurs envisagés (comprenant pour chacun : la localisation, ce qu'ils feront et la preuve des garanties qui ont été mises en œuvre)** devra être fournie au responsable du traitement par le sous-traitant. »

#### La doctrine CNIL la plus utile : « Quelles qualifications pour les acteurs de l'informatique en nuage (cloud) ? », **28 mai 2026**
https://www.cnil.fr/fr/quelles-qualifications-pour-les-acteurs-de-linformatique-en-nuage-cloud — 13/09/2026. [F]
La CNIL y découpe la qualification **par finalité**, ce qui est exactement la méthode à appliquer :

**(a) Fourniture du service** [F] : « En principe, **le client est responsable des traitements** […] **Le fournisseur intervient alors généralement comme sous-traitant** […] À noter : **le fait que le fournisseur décide de la plupart des moyens essentiels du traitement ne suffit pas à le qualifier de responsable du traitement.** »

**(b) Amélioration du service — trois cas** [F] :
- **Cas 1, fournisseur = responsable** : « L'amélioration du service est faite **à l'initiative du fournisseur pour ses propres besoins** […] **Le fournisseur détermine seul les données dont il a besoin** […] »
- **Cas 2, fournisseur = sous-traitant** : « L'amélioration […] est **spécifiquement recherchée pour le service fourni à un client en particulier** […] fondée sur les données générées par ce seul client. »
- **Cas 3, responsabilité conjointe** : objectifs « **décidés conjointement** […] car ce traitement présente un intérêt pour chacune des parties ».

**Application** [H, fondée sur les [F] ci-dessus] :

| Traitement | Qualification |
|---|---|
| Décrocher, dialoguer, transcrire, prendre RDV pour le compte du commerçant | Commerçant **RT** / Éditeur **ST** |
| Enregistrement audio décidé et paramétré par le commerçant | Commerçant **RT** / Éditeur **ST** |
| Journaux techniques, supervision d'infrastructure | Éditeur **ST** (voire RT pour ses obligations propres de sécurité) |
| Fine-tuning d'un modèle **dédié à un client**, sur ses seules données, à sa demande | Éditeur **ST** (cas 2 CNIL) |
| **Entraînement d'un modèle global mutualisé** décidé par l'éditeur | **Éditeur RT autonome** (cas 1 CNIL) |
| Co-conception d'un modèle sectoriel avec un éditeur hôte, bénéfice partagé | **Responsables conjoints** (art. 26) |

#### La règle qui condamne la clause CGU standard
CNIL, « **Sous-traitants : la réutilisation de données confiées par un responsable de traitement** » — https://www.cnil.fr/fr/sous-traitants-la-reutilisation-de-donnees-confiees-par-un-responsable-de-traitement — 13/09/2026. [F]
> « […] il ne peut pas réutiliser ces données pour son propre compte, de sa propre initiative, sauf si un texte national ou européen le lui impose. »
> « **Le sous-traitant qui réutiliserait les données de sa propre initiative serait qualifié de responsable de ce traitement et passible de sanctions** […] »

Conditions cumulatives de licéité [F] : (1) **test de compatibilité art. 6.4 réalisé par le responsable initial** — le commerçant, pas l'éditeur ; (2) **pas d'autorisation générale** — « Ce "test de compatibilité" doit être réalisé **pour un traitement déterminé** […] **une autorisation préalable et générale de réutilisation des données n'est pas légale** » ; (3) autorisation écrite ; (4) information des personnes ; (5) l'ex-sous-traitant devenu responsable assume finalité, base légale, art. 14, durée, minimisation, droits, sécurité.

> 🔴 **Une clause de CGU du type « le Client autorise l'Éditeur à utiliser les Données pour améliorer ses services » est illicite en l'état.** Il faut un **opt-in par finalité nommée, désactivé par défaut**. La CNIL cite elle-même l'**anonymisation** comme la garantie qui fait passer le test de compatibilité pour une finalité d'amélioration de service. [F + H]

Autres fiches CNIL utiles [F] :
- « IA et RGPD : nouvelles recommandations », **07/02/2025** — https://www.cnil.fr/fr/ia-et-rgpd-la-cnil-publie-ses-nouvelles-recommandations-pour-accompagner-une-innovation-responsable : « Lorsque des données personnelles servent à l'entraînement d'un modèle d'IA et sont potentiellement mémorisées par celui-ci, **les personnes concernées doivent être informées**. »
- « Comment déployer une IA générative ? », **18/07/2024** — https://www.cnil.fr/fr/comment-deployer-une-ia-generative-la-cnil-apporte-de-premieres-precisions : « privilégiant le recours à des systèmes **locaux, sécurisés et spécialisés** […] **À défaut, il faut déterminer dans quelle mesure le prestataire opérant le système est susceptible de réutiliser les données fournies au système d'IA, et adapter l'usage en conséquence.** » → **critère de sélection du fournisseur STT/LLM.**
- « Chatbots : les conseils de la CNIL », **19/02/2021** — https://www.cnil.fr/fr/chatbots-les-conseils-de-la-cnil-pour-respecter-les-droits-des-personnes : « Une conversation avec un chatbot **sans intervention humaine ne peut conduire à elle seule à des décisions importantes pour la personne concernée** […] » → prendre un RDV n'est probablement pas une décision au sens de l'art. 22 [H] ; **refuser, blacklister ou tarifer différemment le serait** [H].

**[NV] non lus dans cette recherche, à dépouiller** : note exploratoire CNIL / Conseil de l'IA et du Numérique sur **l'IA agentique, 20 juillet 2026** ; **lignes directrices CEPD du 7 juillet 2026 sur l'anonymisation et sur le moissonnage en IA générative** (relayées par la CNIL le 09/07/2026, https://www.cnil.fr/fr/cepd-ia-generative-chaines-blocs) — directement pertinentes pour la clause de réutilisation ci-dessus ; référentiels CNIL « gestion des activités commerciales » et « gestion des impayés », numéros de délibération non relevés.

### 2.2 Contrat article 28 — contenu obligatoire exhaustif

**Chapeau du 28.3** — les quatre mentions que les DPA du marché oublient le plus souvent [F] :
> « Le traitement par un sous-traitant est régi par **un contrat ou un autre acte juridique** […] qui lie le sous-traitant à l'égard du responsable du traitement, **définit l'objet et la durée du traitement, la nature et la finalité du traitement, le type de données à caractère personnel et les catégories de personnes concernées, et les obligations et les droits du responsable du traitement.** »

**Les huit obligations a) à h)** [F], verbatim résumé :
| | Obligation |
|---|---|
| **a)** | traiter **uniquement sur instruction documentée** du RT, **y compris pour les transferts vers un pays tiers** ; informer le RT de toute obligation légale contraire avant le traitement |
| **b)** | veiller à ce que les personnes autorisées **s'engagent à respecter la confidentialité** |
| **c)** | prendre **toutes les mesures requises en vertu de l'article 32** |
| **d)** | respecter les **paragraphes 2 et 4** pour recruter un autre sous-traitant |
| **e)** | **aider le RT** à donner suite aux demandes d'exercice des **droits du chapitre III** |
| **f)** | **aider le RT à garantir le respect des obligations des articles 32 à 36** (sécurité, violations, AIPD, consultation préalable) |
| **g)** | **supprimer ou renvoyer** toutes les données au terme de la prestation, **au choix du RT**, et détruire les copies |
| **h)** | **mettre à disposition toutes les informations nécessaires** pour démontrer la conformité et **permettre des audits, y compris des inspections**, et y contribuer |

**Alinéa final du 28.3 — obligation d'alerte, presque toujours omise** [F] :
> « […] **le sous-traitant informe immédiatement le responsable du traitement si, selon lui, une instruction constitue une violation du présent règlement** […] »

**28.9** : forme écrite, y compris électronique. [F]

**Sous-traitants ultérieurs — 28.2 et 28.4** [F] :
> **28.2** « **Le sous-traitant ne recrute pas un autre sous-traitant sans l'autorisation écrite préalable, spécifique ou générale, du responsable du traitement.** Dans le cas d'une autorisation écrite générale, le sous-traitant informe le responsable du traitement de tout changement prévu […] **donnant ainsi au responsable du traitement la possibilité d'émettre des objections** […] »
> **28.4** « […] **les mêmes obligations en matière de protection de données** que celles fixées dans le contrat […] sont imposées à cet autre sous-traitant […] **Lorsque cet autre sous-traitant ne remplit pas ses obligations […], le sous-traitant initial demeure pleinement responsable devant le responsable du traitement** […] »

> 🔴 **L'éditeur répond intégralement, devant chaque salon de coiffure, des manquements du fournisseur STT et du fournisseur LLM américains.** [F]

**Clauses contractuelles types RT↔ST : décision d'exécution (UE) 2021/915 du 4 juin 2021** (C/2021/3701, JO L 199 du 7.6.2021, p. 18-30) [F].
Statut vérifié sur la fiche « Document information » d'EUR-Lex le 13/09/2026 : **« In force », « No end date »**, modifiée seulement par le rectificatif 32021D0915R(01) — **aucune modification de fond**.
https://eur-lex.europa.eu/legal-content/FR/HIS/?uri=CELEX:32021D0915

> ⚠️ **Piège majeur, énoncé par la CNIL elle-même** (« Clauses contractuelles types entre responsable de traitement et sous-traitant », 30/06/2021, https://www.cnil.fr/fr/clauses-contractuelles-types-entre-responsable-de-traitement-et-sous-traitant) [F] :
> « **Ces clauses contractuelles types permettent-elles de transférer des données en dehors de l'Union européenne ? — Non**, la Commission européenne précise que ses clauses contractuelles types **ne peuvent servir aux fins du chapitre V du RGPD**. En cas de transfert, il convient d'utiliser les clauses contractuelles types dédiées. »
> **Deux instruments contractuels distincts sont nécessaires** : 2021/915 pour l'art. 28, **2021/914 pour le chapitre V** (voir §2.6).

Autres précisions CNIL [F] : les CCT 2021/915 « **n'ont pas obligatoirement à être utilisées** » si le contrat contient tous les éléments de l'art. 28 ; « les parties s'engagent à **ne pas modifier les clauses**, sauf ajout ou mise à jour des annexes ». La CNIL n'a pas adopté ses propres CCT mais publie un **« Exemple de clauses »** (https://www.cnil.fr/fr/sous-traitance-exemple-de-clauses).

**Guide CNIL du sous-traitant** (page du 29/09/2017 ; PDF https://www.cnil.fr/sites/default/files/atoms/files/rgpd-guide_sous-traitant-cnil.pdf) — ce qu'il ajoute [F] : **obligation de conseil** (« aider dans la mise en œuvre de certaines obligations : étude d'impact, notification de violation, sécurité, contribution aux audits ») ; **privacy by design et by default** ; **registre** ; **DPO** dans certains cas.

**Check-list contractuelle minimale** [H, adossée aux [F]] :
1. Les 4 mentions de chapeau, **en annexe remplie par commerçant**.
2. Les 8 obligations a)→h), verbatim ou équivalent démontrable.
3. La clause d'alerte sur instruction illicite (dernier alinéa 28.3).
4. **Autorisation générale de sous-traitance ultérieure** + **liste nominative avec localisation, rôle, garanties** (§152 EDPB) + **préavis d'objection chiffré**.
5. **Clause de réutilisation séparée, opt-in, par finalité nommée** — jamais générale (§2.1).
6. Chapitre V traité par un **instrument distinct**.
7. Sort des données en fin de contrat : choix explicite suppression / restitution, **format et délai**.

### 2.3 Registre des traitements — obligatoire, l'exemption ne joue pas

**Art. 30.2 — registre du sous-traitant (l'éditeur)** [F] : a) **nom et coordonnées de chaque responsable du traitement pour le compte duquel il agit** ; b) catégories de traitements effectués **pour chaque responsable** ; c) transferts hors UE avec identification du pays et documents attestant les garanties ; d) description générale des mesures de sécurité (art. 32.1).
**Art. 30.1 — registre du responsable (le commerçant)** [F] : a) identité/DPO ; b) finalités ; c) catégories de personnes et de données ; d) catégories de destinataires ; e) transferts hors UE ; f) délais d'effacement ; g) mesures de sécurité.

**Art. 30.5 — l'exemption < 250 salariés** [F] :
> « Les obligations […] ne s'appliquent pas à une entreprise […] comptant moins de 250 employés, **sauf si** le traitement […] **est susceptible de comporter un risque** […], **s'il n'est pas occasionnel** ou **s'il porte notamment sur les catégories particulières de données visées à l'article 9, paragraphe 1** […] »

Les trois branches du « sauf si » sont **alternatives**. Le traitement de l'éditeur **n'est pas occasionnel** (c'est son objet social) → la deuxième branche suffit seule. Il est en outre **susceptible de comporter un risque**, et peut porter incidemment sur des données de l'art. 9.
→ **Registre obligatoire pour l'éditeur (30.2) ET pour chaque commerçant (30.1), quelle que soit la taille. L'exemption est inapplicable.** [F pour le texte, [H] pour la subsomption]

> **Note pratique** : le 30.2 a) impose de **nommer chaque commerçant client**. Pour un SaaS à des centaines de salons, le registre doit être **généré depuis la base clients**, pas tenu dans un tableur figé. [H]

### 2.4 AIPD — oui, elle est obligatoire

**Art. 35.1** [F] : « Lorsqu'un type de traitement, **en particulier par le recours à de nouvelles technologies** […] est susceptible d'engendrer un risque élevé […], **le responsable du traitement effectue, avant le traitement**, une analyse d'impact […] **Une seule et même analyse peut porter sur un ensemble d'opérations de traitement similaires** […] »

#### La voix est-elle une donnée biométrique ? Réponse nuancée mais ferme
**Art. 4(14)** [F] : données biométriques = « données […] **résultant d'un traitement technique spécifique** […] **qui permettent ou confirment son identification unique** ».
**Art. 9.1** [F] : l'interdiction ne vise que « le traitement des **données biométriques aux fins d'identifier une personne physique de manière unique** ».
**Considérant 51** [F] : « Le traitement des photographies ne devrait pas systématiquement être considéré comme constituant un traitement de catégories particulières […], étant donné que celles-ci ne relèvent de la définition de données biométriques que lorsqu'elles sont traitées selon **un mode technique spécifique permettant l'identification ou l'authentification unique** d'une personne physique. »

**Conclusion [H, fondée sur ces trois [F]]** :
- **Enregistrer, transcrire et comprendre** la voix pour prendre un RDV → **pas de donnée biométrique** au sens de l'art. 9. La voix est ici un **véhicule du contenu**, pas un identifiant.
- **Dès qu'une fonction de reconnaissance du locuteur / voiceprint / authentification vocale / reconnaissance d'un appelant récurrent par empreinte vocale est activée → bascule en article 9.1**, interdiction de principe, exception nécessaire (en pratique le **consentement explicite** du 9.2 a)), entrée automatique dans la liste des 14 de la CNIL, AIPD de plein droit.
- 🔴 **Recommandation produit : proscrire par conception toute fonction de *speaker identification*.** L'impact sur la qualification est massif et disproportionné par rapport au gain fonctionnel.

**Point distinct et sous-estimé** : le **contenu** des conversations peut révéler des données de l'art. 9 sans aucune biométrie — un client qui annule pour cause de chimiothérapie, un régime religieux, une allergie. La CNIL le pointe pour les chatbots : « une attention particulière doit être portée aux données sensibles […] dont le traitement est en principe interdit » [F]. → **filtrage/expurgation à la transcription + rétention courte.** [H]

#### Délibération n° 2018-327 du 11 octobre 2018 — la liste des 14
Référence exacte vérifiée [F], accompagnée de la **délibération n° 2018-326** (lignes directrices AIPD).
Page : https://www.cnil.fr/fr/analyse-dimpact-relative-la-protection-des-donnees-publication-dune-liste-des-traitements-pour
PDF : https://www.cnil.fr/sites/default/files/atoms/files/liste-traitements-aipd-requise.pdf — 13/09/2026.

Les types qui peuvent s'appliquer ici [F pour les libellés, [H] pour la subsomption] :
- **n° 4 — « Traitements ayant pour finalité de surveiller de manière constante l'activité des employés concernés »** → **OUI si enregistrement permanent/systématique des appels traités par des salariés**. C'est le point de contact le plus net.
- **n° 3** — profils de personnes à des fins de gestion des RH → si l'agent produit des scores sur les salariés.
- **n° 8** — profilage pouvant aboutir à l'exclusion du bénéfice d'un contrat → si l'agent refuse/blackliste des appelants (no-show).
- **n° 9** — traitements **mutualisés** de manquements contractuels → **oui si liste noire partagée entre commerçants : architecture à proscrire.**
- **n° 11** — données biométriques d'identification unique → seulement si reconnaissance du locuteur (cf. supra).

#### Les 9 critères WP248 rev.01 repris par la CNIL — seuil de 2
CNIL, « Ce qu'il faut savoir sur l'AIPD » — https://www.cnil.fr/fr/ce-quil-faut-savoir-sur-lanalyse-dimpact-relative-la-protection-des-donnees-aipd — 13/09/2026 [F] :
> « Soit le traitement remplit **au moins deux des neuf critères** issus des lignes directrices du G29 : évaluation/scoring […] ; décision automatique avec effet légal ou similaire ; **surveillance systématique** ; collecte de données sensibles ou **données à caractère hautement personnel** ; **collecte de données personnelles à large échelle** ; croisement de données ; personnes vulnérables […] ; **usage innovant (utilisation d'une nouvelle technologie)** ; exclusion du bénéfice d'un droit/contrat. »

| Critère | Rempli ? | Motif |
|---|---|---|
| 3. **Surveillance systématique** | **OUI** | Le dispositif capte **tous** les appels entrants, en continu, y compris ceux traités par des salariés |
| 4. **Données sensibles ou hautement personnelles** | **OUI** | La voix et le **contenu intégral d'une conversation privée** sont des données hautement personnelles ; l'art. 9 peut être atteint incidemment |
| 8. **Usage innovant** | **OUI, sans discussion** | STT + LLM génératif décrochant le téléphone ; l'art. 35.1 vise expressément « le recours à de nouvelles technologies » |
| 1. Scoring / profilage | Partiel | Si scoring qualité d'appel, grilles salariés, profilage client |
| 5. Large échelle | **OUI au niveau éditeur** | Voir la nuance ci-dessous |
| 6. Croisement | Possible | Transcriptions × fichier client × historique RDV × agenda |
| 7. Personnes vulnérables | Partiel | Les **salariés** sont qualifiés de vulnérables par la CNIL elle-même (lien de subordination) ; appelants mineurs possibles |
| 2. Décision automatisée art. 22 | Non en principe | **Oui** si refus/blacklist automatisé |
| 9. Exclusion d'un droit/contrat | Possible | Idem |

**Décompte : 3 critères certains au minimum (3, 4, 8), le plus souvent 5 à 6. Le seuil de 2 est franchi largement.**

**La nuance « grande échelle » pour un petit salon** — **considérant 91, dernière phrase** [F] :
> « **Le traitement […] ne devrait pas être considéré comme étant à grande échelle si le traitement concerne les données […] de patients ou de clients par un médecin, un autre professionnel de la santé ou un avocat exerçant à titre individuel.** Dans de tels cas, une analyse d'impact […] ne devrait pas être obligatoire. »

Et, en sens inverse, la première phrase du même considérant [F] : « […] en particulier aux opérations de traitement à grande échelle […] lorsque […] **une nouvelle technique est appliquée à grande échelle** ».
→ [H] Pris isolément, un salon indépendant est proche du praticien individuel : le critère n° 5 lui est difficilement opposable **seul**. Mais (i) les critères 3, 4 et 8 suffisent à atteindre le seuil ; (ii) **au niveau de l'éditeur**, qui applique une technologie nouvelle à des centaines de commerçants, la première phrase du considérant 91 s'applique frontalement.

> ### 🔴 **CONCLUSION : OUI, l'analyse d'appels par IA rend l'AIPD obligatoire.** [H — conclusion de raisonnement, chaque prémisse étant [F]]
> 1. Seuil des 9 critères franchi sans ambiguïté (3 certains, seuil à 2).
> 2. L'art. 35.1 vise textuellement « le recours à de nouvelles technologies ».
> 3. **Si le dispositif enregistre systématiquement les appels traités par des salariés**, on entre en outre dans le **type n° 4 de la délibération 2018-327** → AIPD obligatoire **de plein droit**, sans décompte.
> 4. **Le débiteur est le responsable du traitement, donc le commerçant** (art. 35.1 : « le responsable du traitement effectue »). **L'éditeur y est tenu d'aider au titre de l'art. 28.3 f).**

**Ce que l'éditeur doit produire — et c'est la CNIL qui l'écrit** [F] :
> « En tant que bonne pratique, **une AIPD peut également être menée par le fournisseur d'un produit** […] Les différents responsables de traitement qui utilisent ensuite ce produit doivent mener leurs propres AIPD mais, le cas échéant, **ceux-ci peuvent être alimentés par l'AIPD du fournisseur.** »
→ **Livrable : une AIPD « produit », réalisée avec le logiciel PIA de la CNIL, livrée pré-remplie à chaque commerçant.** Obligation d'assistance **et** argument de vente.

### 2.5 Information de l'appelant au téléphone — quelles mentions, à quel moment

**Art. 13.1** [F] : a) identité et coordonnées du RT (et du représentant) ; b) coordonnées du DPO ; c) **finalités et base juridique** ; d) **intérêts légitimes poursuivis** si base 6.1 f) ; e) **destinataires ou catégories de destinataires** ; f) **le cas échéant, le fait que le RT a l'intention d'effectuer un transfert vers un pays tiers**, et l'existence ou l'absence d'une décision d'adéquation, ou la référence aux garanties appropriées et les moyens d'en obtenir une copie.
**Art. 13.2** [F] : a) **durée de conservation** (ou critères) ; b) **existence des droits** d'accès, rectification, effacement, limitation, opposition, portabilité ; c) droit de retirer le consentement ; d) **droit d'introduire une réclamation auprès d'une autorité de contrôle** ; e) caractère réglementaire/contractuel de la fourniture des données ; f) existence d'une **décision automatisée** au sens de l'art. 22.

**Art. 21.4 — la mention qui doit être détachée** [F] :
> « **Au plus tard au moment de la première communication avec la personne concernée, le droit [d'opposition] est explicitement porté à l'attention de la personne concernée et est présenté clairement et séparément de toute autre information.** »

**Information en deux temps — expressément admise par la CNIL** [F, fiches enregistrement d'appels citées §3] : mention orale essentielle en début d'appel + renvoi vers une information exhaustive accessible. Le **droit d'opposition doit être porté à connaissance et exerçable avant la fin de la conversation.**

#### Script d'annonce recommandé [H, construit sur les [F] ci-dessus + AI Act §1 + CPCE L34-5 §4.6]

> **Temps 1 — dès le décrochage, avant toute capture conservée :**
> « Bonjour, vous êtes en relation avec l'assistant téléphonique de **[RAISON SOCIALE DU COMMERÇANT]**. Cet appel **est traité par un système automatisé**[, et **est enregistré** afin de …]. **Vous pouvez vous y opposer** en tapant [1] ou en le disant à tout moment ; vous serez alors [mis en relation avec une personne / rappelé]. Information complète sur **[site.fr/confidentialite]** ou en tapant [9]. »

Ce script couvre simultanément :
| Élément | Fondement |
|---|---|
| « assistant de [raison sociale] » | RGPD art. 13.1 a) **+ C. conso. L. 121-2, 3°** (« la personne pour le compte de laquelle la pratique est mise en œuvre n'est pas clairement identifiable » = trompeuse) **+ CPCE L. 34-5** (interdiction de dissimuler l'identité du donneur d'ordre) |
| « traité par un système automatisé » | **AI Act art. 50 §1 et §5** |
| « est enregistré afin de… » | RGPD art. 13.1 c) |
| « vous pouvez vous y opposer » | **RGPD art. 21.4** (porté à l'attention **séparément**) |
| URL + touche 9 | RGPD art. 13 complet, information en deux temps |

> **Trois exigences non négociables** [F] :
> 1. L'opposition doit être exerçable **jusqu'à la fin de l'appel** → touche active pendant tout l'appel, pas seulement au début.
> 2. L'annonce précède **toute** capture conservée : la mention ne peut arriver après la première seconde d'audio stocké.
> 3. **Temps 2** : information exhaustive 13.1 a)→f) et 13.2 a)→f), avec **mention expresse des transferts hors UE et de leur fondement** (13.1 f)).

### 2.6 Sous-traitants ultérieurs hors UE (STT et LLM américains) et base de transfert

#### Le principe
**Art. 44** [F] : « […] les conditions définies dans le présent chapitre **sont respectées par le responsable du traitement ET le sous-traitant**, y compris pour les **transferts ultérieurs** […] »
**Art. 45.1** [F] : décision d'adéquation → « **Un tel transfert ne nécessite pas d'autorisation spécifique.** »
**Art. 46.1/46.2** [F] : à défaut, **garanties appropriées** — dont c) « **clauses types de protection des données adoptées par la Commission** ».
**Art. 49.1** : dérogations de stricte interprétation.
→ **L'article 49 est inutilisable ici** : les appels d'un agent vocal sont par nature **répétitifs** et touchent un **nombre illimité** de personnes. [H fondée sur [F]]

#### Le Data Privacy Framework est-il toujours en vigueur ? **OUI, vérifié**
**Décision d'exécution (UE) 2023/1795 de la Commission du 10 juillet 2023** [notifiée C(2023) 4745], JO L 231 du 20.9.2023, p. 118-229.
Métadonnées EUR-Lex relevées le 13/09/2026 : **« In force »**, *Date of end of validity* : **« No end date »**, **aucune version consolidée postérieure, aucun acte modificatif**.
https://eur-lex.europa.eu/legal-content/FR/HIS/?uri=CELEX:32023D1795 **[F]**

**L'affaire Latombe — résultat exact** [F] :
> **Arrêt du Tribunal (dixième chambre élargie) du 3 septembre 2025, Philippe Latombe / Commission européenne, affaire T-553/23**, CELEX 62023TJ0553. Intervenants au soutien de la Commission : **l'Irlande** et **les États-Unis d'Amérique**.
> Dispositif : « **1) Le recours est rejeté.** » (et point 204 : « il y a lieu de rejeter le cinquième moyen et, partant, **le recours dans son intégralité** »).
> https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=CELEX:62023TJ0553 — 13/09/2026.
> (Le sursis à exécution avait déjà été rejeté pour défaut d'urgence par ordonnance du 12 octobre 2023, T-553/23 R.)

> ⚠️ **IL Y A UN POURVOI, ET IL EST PENDANT** [F] :
> **Affaire C-703/25 P — pourvoi formé le 31 octobre 2025** par Philippe Latombe contre l'arrêt T-553/23. CELEX 62025CN0703, **JO C, C/2025/6610, 22.12.2025**.
> Au 13/09/2026, l'inventaire complet des documents EUR-Lex relatifs à « Latombe » (8 documents) **ne comporte aucun arrêt ni ordonnance dans l'affaire C-703/25 P**. **La Cour ne s'est pas prononcée.**

> 🔴 **Conclusion opérationnelle** [H fondée sur [F]] :
> 1. **Le DPF est une base de transfert valide au 14 septembre 2026.** Mais il ne couvre que **les organisations effectivement inscrites sur la liste CPD** tenue par le ministère américain du Commerce — **pas « les États-Unis » en bloc**. → **vérifier nominativement chaque fournisseur STT et LLM, et vérifier que la certification couvre la catégorie de données concernée.**
> 2. **Un pourvoi est pendant.** Le précédent Schrems II (invalidation du Privacy Shield le 16 juillet 2020, **sans période de grâce**) commande de prévoir **dès maintenant un dispositif de repli** : CCT 2021/914 module 3 **déjà signées et dormantes**, AITD déjà rédigée, et idéalement une **option d'hébergement européen** du STT et du LLM.
> 3. Le DPF figure dans l'information des personnes (art. 13.1 f)) : **si son statut change, les mentions légales de tous les commerçants clients deviennent fausses simultanément.**

#### Clauses contractuelles types de transfert — décision (UE) 2021/914
**Décision d'exécution (UE) 2021/914 de la Commission du 4 juin 2021** (C/2021/3972, JO L 199 du 7.6.2021, p. 31-61).
Statut au 13/09/2026 : **« In force »**, *No end date*, modifiée uniquement par **quatre rectificatifs** (R(01) à R(04)) — **aucune modification de fond**. Base juridique : art. 28.7 **et art. 46.2 c)** RGPD.
https://eur-lex.europa.eu/legal-content/FR/HIS/?uri=CELEX:32021D0914 **[F]**

**Modules vérifiés dans le texte de l'annexe** [F] : Module 1 (RT→RT), **Module 2 (RT→ST)**, **Module 3 (ST→ST)**, Module 4 (ST→RT).

> ### 🔴 **Module applicable ici : MODULE 3 (sous-traitant → sous-traitant ultérieur).** [F]
> L'éditeur français est **sous-traitant** du commerçant, **exportateur** ; le fournisseur STT/LLM américain est **sous-traitant ultérieur**, **importateur**. **Le module 2 serait une erreur de qualification.**

**Nouvelles CCT en 2025/2026 ?** Les deux décisions 2021/914 et 2021/915 sont toujours en vigueur et non modifiées au fond [F]. Mais les recherches plein texte sur EUR-Lex pour un éventuel **nouveau jeu de CCT** (notamment celui annoncé pour les importateurs déjà directement soumis au RGPD au titre de l'art. 3.2) **n'ont pas abouti** — **[NV] sur ce point précis** : je peux affirmer que 2021/914 et 2021/915 sont en vigueur, **pas** qu'aucune nouvelle CCT n'a été adoptée.

#### Analyse d'impact des transferts (AITD / TIA)
**Recommandations CEPD 01/2020** v2.0 (PDF FR) : https://www.edpb.europa.eu/system/files/documents/2022-04/edpb_recommendations_202001vo.2.0_supplementarymeasurestransferstools_fr.pdf — 13/09/2026 [F]. Six étapes, intitulés exacts :
1. **connaître les transferts** ; 2. **recenser les instruments de transfert** ; 3. **évaluer si l'instrument est efficace compte tenu de toutes les circonstances du transfert** ; 4. **adoption de mesures supplémentaires** ; 5. **étapes de la procédure** ; 6. **réévaluation à intervalles appropriés**.
> Étape 3, §28-30 [F] : « […] la protection accordée aux données […] doit être **essentiellement équivalente** à celle garantie dans l'EEE […] Tel n'est pas le cas si l'importateur de données n'est pas en mesure de se conformer aux obligations qui lui incombent […] **en raison du droit du pays tiers et des pratiques applicables au transfert, y compris pendant le transit** […] »
Complément : **Recommandations 02/2020** du CEPD sur les **garanties essentielles européennes** en matière de surveillance [F].

**Guide AITD de la CNIL, version finale du 09/07/2025** — https://www.cnil.fr/fr/analyse-dimpact-des-transferts-des-donnees-la-cnil-publie-la-version-finale-de-son-guide-aitd ; PDF https://www.cnil.fr/sites/cnil/files/2025-02/guide_aitd_pdf.pdf — 13/09/2026 [F] :
> « Une AITD doit être réalisée par **l'exportateur soumis au RGPD, qu'il soit responsable de traitement ou sous-traitant**, avec **l'assistance de l'importateur**, avant de transférer les données […] **lorsque ce transfert s'appuie sur un outil de l'article 46** […] Il existe **deux dérogations** […] : si le pays de destination est couvert par une **décision d'adéquation** ; si le transfert est effectué sur la base d'une des dérogations [art. 49]. »
> « Les exportateurs ont également la responsabilité de **suspendre le transfert et/ou de résilier le contrat si l'importateur n'est pas, ou n'est plus, en mesure de respecter ses engagements** […] (cf. arrêt "Schrems II"). »

> **Conséquence directe** [F] :
> - Fournisseur **certifié DPF** → transfert fondé sur l'art. 45 → **pas d'AITD obligatoire**.
> - Fournisseur **non certifié DPF** (ou certification ne couvrant pas la catégorie) → CCT 2021/914 module 3 → **AITD obligatoire, réalisée par l'éditeur exportateur**, avec l'assistance de l'importateur.
> - Si le pourvoi C-703/25 P aboutit → **AITD obligatoire pour tous.** [H]

#### Les obligations sont cumulatives, pas alternatives
| Obligation | Fondement | Contenu |
|---|---|---|
| **Autoriser** le sous-traitant ultérieur | **Art. 28.2** | Autorisation écrite du commerçant ; si générale, information des changements + **droit d'objection** |
| **Répercuter** les obligations | **Art. 28.4** | Mêmes obligations imposées au fournisseur US ; **l'éditeur reste pleinement responsable** |
| **Documenter** | **§152 EDPB 07/2020** | Liste avec **localisation, rôle, preuve des garanties** |
| **Légitimer le transfert** | **Chapitre V** | DPF (art. 45) **ou** CCT 2021/914 module 3 (art. 46.2 c)) + AITD |
| **Instruire le transfert** | **Art. 28.3 a)** | L'instruction documentée doit couvrir explicitement « **les transferts […] vers un pays tiers** » |
| **Informer l'appelant** | **Art. 13.1 f)** | Existence du transfert + adéquation **ou** garanties et moyen d'en obtenir copie |
| **Consigner** | **Art. 30.2 c) + 49.6** | Pays tiers identifié, documents attestant des garanties |

---

## 3. Enregistrement et transcription

### 3.1 Base légale, par finalité

| Finalité | Base légale | Source |
|---|---|---|
| **Prise de RDV** (STT, extraction de la demande, écriture dans l'agenda) | **6.1 b)** — mesures précontractuelles à la demande de la personne | [H] fondée sur le texte |
| **Formation, évaluation des salariés, amélioration de la qualité du service** | **6.1 f) — intérêt légitime de l'employeur**, expressément visé par la CNIL : « la base légale du dispositif (obligation issue d'un texte légal par exemple, **ou intérêt légitime de l'employeur**) » | **[F]** — fiche CNIL « L'écoute et l'enregistrement des appels sur le lieu de travail » |
| **Preuve de la formation d'un contrat conclu à l'oral** | **6.1 b)** — « Lorsque les personnes acceptent de contractualiser par téléphone, les enregistrements […] peuvent être traités sur le fondement de la base légale du contrat (article 6.1.b du RGPD) », **à la condition** que « L'information sur la possibilité, lorsqu'elle existe, de conclure le contrat par d'autres moyens […] est donc **indispensable** pour que l'enregistrement puisse être considéré comme nécessaire au contrat » | **[F]** — fiche CNIL « preuve de la formation d'un contrat » |
| **Entraînement / amélioration des modèles de l'éditeur** | **Traitement ultérieur distinct** : autorisation écrite spécifique après test de compatibilité (art. 6.4) + base légale propre de l'éditeur devenu RT ; **l'anonymisation est la garantie citée en exemple par la CNIL** | **[F]** — fiche « réutilisation », §2.1 |

> **Le consentement (6.1 a)) n'est PAS la base de principe de l'enregistrement.** C'est l'intérêt légitime ou le contrat, selon la finalité. Le **consentement explicite (art. 9.2 a))** ne redevient obligatoire que si une fonction d'identification vocale unique est activée (§2.4). [H fondée sur [F]]

### 3.2 🔴 L'enregistrement systématique de TOUS les appels est INTERDIT

**C'est le point le plus tranché du dossier, et il valide l'arbitrage déjà pris dans `01-CONCEPT-PRODUIT.md` (« Pas d'enregistrement audio par défaut — transcription seule »).**

**CNIL, « L'écoute et l'enregistrement des appels sur le lieu de travail »** — https://www.cnil.fr/fr/lecoute-et-lenregistrement-des-appels-sur-le-lieu-de-travail — 13/09/2026 [F] :
> « L'écoute en temps réel et l'enregistrement sonore des appels sur le lieu de travail peuvent être réalisés **en cas de nécessité reconnue** et doivent être **proportionnés** aux objectifs poursuivis. »
> « […] l'employeur peut installer un dispositif d'écoute et/ou **d'enregistrement ponctuel** des conversations téléphoniques pour : former ses salariés […] ; les évaluer ; améliorer la qualité du service […] »
> « **L'employeur ne peut pas mettre en place un dispositif d'écoute ou d'enregistrement permanent ou systématique, sauf texte légal** (par exemple pour les services d'urgence). »
> « **L'employeur ne peut pas non plus enregistrer tous les appels pour lutter contre les incivilités. Il doit choisir un moyen moins intrusif** (par exemple : opter pour un système permettant au salarié de déclencher l'enregistrement en cas de problème). »
> « **L'enregistrement des appels ne peut être couplé à un système de captures d'écran du poste informatique des salariés.** »
> « **L'employeur doit mettre à disposition des salariés des lignes téléphoniques non reliées au système d'enregistrement, ou un dispositif technique leur permettant de couper l'enregistrement, pour les appels personnels.** »

**CNIL, « L'enregistrement des conversations téléphoniques afin d'établir la preuve de la formation d'un contrat »** — https://www.cnil.fr/fr/lenregistrement-des-conversations-telephoniques-afin-detablir-la-preuve-de-la-formation-dun-contrat — 13/09/2026 [F] — la même règle, énoncée plus durement :
> « À cet égard, sauf dispositions légales le permettant, **les enregistrements ne peuvent être ni permanents ni systématiques.** »
> « **L'enregistrement d'une conversation téléphonique ne peut être déclenché par défaut, de manière automatisée, pour tous les appels téléphoniques et pour l'intégralité des conversations.** Concrètement, le téléopérateur pourrait notamment déclencher manuellement l'enregistrement, uniquement dans le cas où la conversation a pour objet de conclure un contrat ne pouvant être prouvé par un autre moyen. »
> « Le professionnel devra ainsi prévoir des mécanismes afin de **n'enregistrer la conversation […] qu'à partir du moment où son objet porte clairement sur la conclusion d'un contrat**. »
> **Données bancaires** : « La CNIL recommande […] la mise en place d'un dispositif permettant **d'interrompre ou de supprimer rapidement l'enregistrement de la conversation téléphonique au moment où le consommateur prononce ces données**. »

#### Conséquence d'architecture produit [H, fondée sur les [F] ci-dessus]
> **L'enregistrement audio ne doit PAS être activé par défaut.** Il doit être :
> - **déclenché** sur événement métier identifié, ou par échantillonnage ponctuel documenté — **jamais continu** ;
> - **interruptible en cours d'appel** (opposition, ou détection de données bancaires/sensibles) ;
> - **dissocié de la transcription fonctionnelle** nécessaire à la prise de RDV, qui relève d'une autre finalité et d'une autre base légale.

> **La distinction sur laquelle repose toute la conformité du produit** [H] : un agent vocal **doit** techniquement convertir la voix en texte pour fonctionner. Il y a donc un traitement audio **transitoire** inévitable (6.1 b)), qu'il faut **distinguer nettement** de la **conservation d'un fichier audio** (6.1 f), finalité qualité/preuve).
> **La doctrine CNIL « pas d'enregistrement systématique » vise la CONSERVATION, non le traitement transitoire.** Cette distinction doit être **écrite et motivée dans l'AIPD** — c'est la ligne de défense centrale du produit.

### 3.3 Différence de régime AUDIO vs TRANSCRIPTION — et le référentiel du 2 avril 2026

#### Ce qui a réellement été publié le 2 avril 2026
> **« Référentiel — Les durées de conservation des données à caractère personnel — Gestion des ressources humaines »**
> Page : https://www.cnil.fr/fr/referentiel-durees-conservation-donnees-rh
> PDF : https://www.cnil.fr/sites/default/files/2026-04/referentiel_durees_de_conservation_gestion_des_ressources_humaines.pdf
> En-tête du PDF, verbatim : « **Publié le 2 avril 2026 — Mis à jour le 20 mai 2026** ». **Aucun numéro de délibération** : c'est un instrument de **droit souple**. — consulté le 13/09/2026. **[F]**

> **Il n'existe pas de « référentiel CNIL du 2 avril 2026 sur les enregistrements d'appels » autonome.** Ce qui existe est ce référentiel **RH**, qui **contient** une rubrique « écoute et enregistrement des conversations téléphoniques sur le lieu de travail ». **La différence de périmètre est décisive** : il traite des **durées de conservation en contexte RH**, pas de la base légale de manière autonome, ni de l'information, ni du droit d'opposition. [F + H]

Portée déclarée [F] : « Ce référentiel s'adresse à **tous les organismes-employeurs privés ou publics** […] dont les personnels sont soumis au droit du travail français. » ; « **le respect du référentiel n'est pas obligatoire** […] En revanche, certaines durées recensées sont obligatoires car prévues par des textes législatifs ou réglementaires ».

#### Le tableau, transcrit verbatim du PDF (p. 9) [F]

| Finalité | Base active | Archivage intermédiaire | Fondement | MAJ |
|---|---|---|---|---|
| « Les enregistrements des appels **à des fins de formation et d'amélioration de la qualité de service ou à des fins d'évaluation** » | « **6 mois maximum à compter de l'enregistrement**. L'employeur ou la personne habilitée peut écouter les enregistrements dans les jours suivants leur réalisation et rédiger le(s) document(s) d'analyse(s) nécessaire(s). **Les enregistrements sont ensuite supprimés à bref délai, l'employeur ne conservant que les documents d'analyse** » | « Seuls les **documents d'analyse** peuvent être conservés en archivage intermédiaire pendant **1 an maximum** » | Fiche CNIL « L'écoute et l'enregistrement des appels sur le lieu de travail » (recommandation) | 29/01/2026 |
| « Les enregistrements de **certains appels à des fins probatoires (formation d'un contrat)** » — « L'enregistrement doit être nécessaire pour prouver la formation du contrat souscrit à l'oral et **ne peut être ni systématique ni permanent** » | N/A | « Par exemple, dans le cadre de la vente d'un bien ou d'un service : **5 ans à compter de la connaissance de l'existence du contrat** » | **Article 2224 du code civil** (obligation) ; fiche CNIL « preuve de la formation d'un contrat » (recommandation) | 29/01/2026 |

Confirmation par la fiche thématique [F] : « Sauf texte imposant une durée spécifique ou justification particulière, **les enregistrements peuvent être conservés jusqu'à six mois au maximum. Les documents d'analyse peuvent quant à eux être conservés jusqu'à un an.** »

#### La pratique des « enregistrements tampon » — la réponse directe à la question audio/transcription
**CNIL**, présenté explicitement comme **« une bonne pratique »** [F] :
> « Cette pratique consiste pour l'employeur, ou la personne habilitée, **à écouter les enregistrements dans les jours suivant leur réalisation et à rédiger le(s) document(s) d'analyse nécessaire(s). Les enregistrements sont ensuite supprimés à bref délai, l'employeur ne conservant que les documents d'analyse.** »

> ### ✅ **OUI : la transcription permet de supprimer l'audio plus vite — et la CNIL l'érige en bonne pratique.** [F]

#### Modèle de rétention recommandé [H, calqué sur le mécanisme « tampon » validé par la CNIL]

| Artefact | Durée | Justification |
|---|---|---|
| **Audio brut** | **quelques jours** (« à bref délai » après exploitation), **6 mois maximum absolu** | Référentiel 02/04/2026 + fiche CNIL. L'audio est le plus intrusif : voix, ton, émotion, bruits de fond, tiers présents |
| **Transcription complète non expurgée** | Assimilable au « document d'analyse » → **1 an maximum**, **mais à réduire drastiquement** | [H] — la transcription intégrale reste très intrusive ; quelques jours est plus défendable |
| **Données métier extraites** (nom, téléphone, créneau, prestation) | Durée du fichier client du commerçant | Finalité distincte, base 6.1 b) |
| **Enregistrement probatoire d'un contrat oral** | **5 ans** à compter de la connaissance de l'existence du contrat, **archivage intermédiaire uniquement** | Art. 2224 C. civ., via référentiel CNIL |
| **Données transmises au LLM/STT US** | **Zéro rétention** côté fournisseur, **exigée contractuellement** | [H] — cf. CNIL « déployer une IA générative » |

**Minimisation appliquée à la transcription** [H] : la transcription conservée doit être **expurgée** des données bancaires, de santé et des propos hors objet.

### 3.4 Droit d'opposition

**Art. 21.1** [F] : « La personne concernée a le droit de s'opposer **à tout moment, pour des raisons tenant à sa situation particulière**, à un traitement […] **fondé sur l'article 6, paragraphe 1, point e) ou f)** […] Le responsable du traitement **ne traite plus les données à caractère personnel, à moins qu'il ne démontre qu'il existe des motifs légitimes et impérieux** […] »
**Art. 21.4** [F] : droit « explicitement porté à l'attention […] **clairement et séparément de toute autre information** », au plus tard à la première communication.
**Art. 21.5** [F] : « la personne concernée peut exercer son droit d'opposition **à l'aide de procédés automatisés utilisant des spécifications techniques**. »

**Applicabilité** [H fondée sur [F]] :
- **Applicable** dès que la base est **6.1 f)** (enregistrement pour qualité, formation, évaluation) — le cas principal.
- **Non applicable** sur le fondement du 6.1 b) (prise de RDV, preuve du contrat) — **mais** la CNIL exige alors d'informer de « la possibilité éventuelle de conclure le contrat par d'autres moyens n'impliquant pas l'enregistrement » [F], ce qui produit un effet fonctionnellement équivalent.

**Mise en œuvre concrète au téléphone** [H] :
1. **Touche DTMF dédiée**, annoncée à l'ouverture et **active pendant tout l'appel** (satisfait 21.5).
2. **Détection vocale d'intention** (« je ne veux pas être enregistré », « arrêtez l'enregistrement ») → arrêt immédiat de la capture.
3. **Effet réel et vérifiable** : **suppression de l'audio déjà capté sur cet appel**, pas seulement arrêt prospectif — sinon l'opposition est cosmétique.
4. **Voie de repli non dégradée** : transfert vers une personne physique, ou rappel. Un droit d'opposition dont l'exercice fait perdre le service n'est pas libre.
5. **Journalisation** de chaque opposition (art. 5.2, accountability).

### 3.5 Information du personnel du commerçant

> ⚠️ **Réserve de source** : Légifrance a renvoyé HTTP 403 sur ce volet. Les textes viennent de **`code.travail.gouv.fr` (Code du travail numérique, ministère du Travail)** — source publique officielle, **pas Légifrance**. [F sous cette réserve], consultés le 13/09/2026.

| Article | Texte | URL |
|---|---|---|
| **L1121-1** | « Nul ne peut apporter aux droits des personnes et aux libertés individuelles et collectives de restrictions qui ne seraient pas justifiées par la nature de la tâche à accomplir ni proportionnées au but recherché. » | https://code.travail.gouv.fr/code-du-travail/l1121-1 |
| **L1222-4** | « **Aucune information concernant personnellement un salarié ne peut être collectée par un dispositif qui n'a pas été porté préalablement à sa connaissance.** » | https://code.travail.gouv.fr/code-du-travail/l1222-4 |
| **L1222-3** | « Le salarié est expressément informé, préalablement à leur mise en oeuvre, des méthodes et techniques d'évaluation professionnelles mises en oeuvre à son égard. Les résultats obtenus sont confidentiels. Les méthodes et techniques d'évaluation des salariés doivent être pertinentes au regard de la finalité poursuivie. » | https://code.travail.gouv.fr/code-du-travail/l1222-3 |
| **L2312-38** | « […] Il est aussi **informé, préalablement à leur introduction dans l'entreprise, sur les traitements automatisés de gestion du personnel** […] **Le comité est informé et consulté, préalablement à la décision de mise en œuvre dans l'entreprise, sur les moyens ou les techniques permettant un contrôle de l'activité des salariés.** » | https://code.travail.gouv.fr/code-du-travail/l2312-38 |
| **L2312-8, II, 4°** | « Le comité est informé et consulté sur les questions intéressant l'organisation, la gestion et la marche générale de l'entreprise, notamment sur : […] **4° L'introduction de nouvelles technologies** […] » | https://code.travail.gouv.fr/code-du-travail/l2312-8 |

**Point de rédaction** : le 3e alinéa de L2312-38 impose **information ET consultation**, **préalablement à la décision de mise en œuvre**. [F]

**CNIL, « Le contrôle de l'activité des personnes employées », page du 09/07/2026** — https://www.cnil.fr/fr/controle-de-lactivite-des-personnes-employees — 13/09/2026 [F] :
> « Pour être licite […] un dispositif de contrôle de l'activité du personnel doit **cumulativement** : satisfaire aux tests de **justification et de proportionnalité** ; être soumis aux **instances représentatives du personnel** selon les règles en vigueur ; être **porté à la connaissance** des salariés/agents. »
> « **Une surveillance constante est excessive** […] »
> « […] l'employeur doit consulter : **le conseil social et économique (CSE) dans les entreprises privées de 50 salariés et plus** […] »
> « **L'employeur doit pouvoir prouver le respect de ces conditions.** »

**Application au cas d'espèce** [H fondée sur [F]] :
- **La quasi-totalité des salons et restaurants clients ont moins de 50 salariés** → **pas de CSE** → l'obligation de consultation de L2312-38 **ne s'applique pas en pratique** à la majorité de la clientèle. **Restent applicables sans seuil d'effectif : L1222-4 (information individuelle préalable) et L1121-1 (proportionnalité).**
- **L'éditeur doit livrer le kit employeur** : modèle de note d'information individuelle (L1222-4) ; modèle de note d'information/consultation CSE pour les clients de 50+ salariés (chaînes, franchises) ; mention des **périodes** d'écoute possible exigée par la CNIL ; documentation de la **ligne non enregistrée** ou du dispositif de coupure pour les appels personnels. Obligation d'assistance (art. 28.3 f)) autant qu'argument de vente.

**[NV]** — Une source secondaire mentionne une sanction CNIL de 250 000 € contre un centre d'appels le 16/10/2025. **Aucune page correspondante n'a été trouvée sur cnil.fr** ; la même source mêle CNIL et CNPD luxembourgeoise. **L'information n'est pas reprise.**

---

## 4. Démarchage téléphonique — la réforme du 11 août 2026

### 4.1 Le texte fondateur

> **LOI n° 2025-594 du 30 juin 2025 contre toutes les fraudes aux aides publiques (1)** — **article 13** [F]
> https://www.legifrance.gouv.fr/loda/id/JORFTEXT000051824277 — 14/09/2026
> **Article 13, III** : « **Les a à f et le h du 1° du B du II entrent en vigueur le 11 août 2026.** »

Ce que l'article 13 fait au code de la consommation [F] : **modifie** L121-11, L221-16, la **dénomination du chapitre III**, **L223-1**, **L223-2**, **L223-5**, L224-27-1, L511-5 ; **crée** L132-14-1, L521-28, **chapitre III bis et L223-8**, L224-114, L224-115, **section 3 bis et L242-16-1**, L521-3-2, L242-51 ; **abroge L223-3 et L223-4**.

**Le basculement est inscrit jusque dans le titre du chapitre** [F] :
> ancien : « Chapitre III : **Opposition** au démarchage téléphonique » → nouveau : « **Chapitre III : Consentement au démarchage téléphonique** (Articles L223-1 à L223-7) »

### 4.2 Article L223-1 — texte en vigueur au 14/09/2026

https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006069565/LEGISCTA000032221441 — 14/09/2026.
**Version en vigueur depuis le 11 août 2026 — Modifié par LOI n°2025-594 du 30 juin 2025 - art. 13 (V)** [F] :

> « **Il est interdit de démarcher par téléphone, directement ou par l'intermédiaire d'un tiers agissant pour son compte, un consommateur qui n'a pas exprimé préalablement son consentement à faire l'objet de prospections commerciales par ce moyen.**
>
> **Pour l'application du présent article, on entend par consentement toute manifestation de volonté libre, spécifique, éclairée, univoque et révocable par laquelle une personne accepte, par un acte positif clair, que des données à caractère personnel la concernant soient utilisées à des fins de prospection commerciale par voie téléphonique.**
>
> **Il appartient au professionnel d'apporter la preuve que le consentement du consommateur a été recueilli dans les conditions prévues au deuxième alinéa.**
>
> **L'interdiction prévue au premier alinéa n'est pas applicable lorsque la sollicitation intervient dans le cadre de l'exécution d'un contrat en cours et a un rapport avec l'objet de ce contrat, y compris lorsqu'il s'agit de proposer au consommateur des produits ou des services afférents ou complémentaires à l'objet du contrat en cours ou de nature à améliorer ses performances ou sa qualité.**
>
> [5e alinéa — interdiction sectorielle : rénovation énergétique, adaptation du logement au vieillissement ou au handicap, énergies renouvelables — sauf contrat en cours au sens du 4e alinéa]
>
> **Un décret […] détermine les jours et horaires ainsi que la fréquence auxquels la prospection commerciale par voie téléphonique peut avoir lieu […] Toutefois, le professionnel peut solliciter le consommateur en dehors des jours et horaires prévus par le décret si le consommateur consent explicitement à être appelé à une date et à un horaire précisément spécifiés et que le professionnel peut en attester.**
>
> **Les professionnels respectent un code de bonnes pratiques** […]
>
> **Tout professionnel ayant tiré profit de sollicitations commerciales de consommateurs réalisées par voie téléphonique en violation des dispositions du présent article est présumé responsable du non-respect de ces dispositions, sauf s'il démontre qu'il n'est pas à l'origine de leur violation.**
>
> **Tout contrat conclu avec un consommateur à la suite d'un démarchage téléphonique réalisé en violation des dispositions du présent article est nul.**
>
> **Les modalités d'application du présent article sont précisées par décret en Conseil d'Etat.** »

> 🔴 **Deux dispositions redoutables** [F] :
> - **al. 8 — présomption de responsabilité** : « **Tout professionnel ayant tiré profit** de sollicitations […] en violation […] **est présumé responsable** ». Renversement de la charge de la preuve, y compris pour le donneur d'ordre qui a sous-traité. **Le commerçant tire profit des appels : c'est lui qui est présumé responsable.**
> - **al. 9 — nullité** : tout contrat conclu à la suite d'un démarchage illicite **est nul**.

### 4.3 Le consentement : recueil, durée, preuve, retrait

**Décret n° 2026-662 du 23 juillet 2026**, articles **R223-1 à R223-4** et **D223-9**, en vigueur depuis le 11 août 2026.
https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006069565/LEGISCTA000032807254 — 14/09/2026 [F]

**R223-1, I — les 5 mentions obligatoires de la demande de consentement** [F] :
1. identité du professionnel et, le cas échéant, du tiers agissant pour son compte, **ainsi que la nature des biens ou services** concernés ;
2. la proposition de consentir ou non, **pour la personne et l'objet du 1°** ;
3. **« La période pendant laquelle le consommateur consent à être démarché, qui ne peut excéder un an à compter de la date de recueil du consentement »** ;
4. l'indication du **droit de retrait à tout moment** et ses modalités (R223-3) ;
5. l'indication que le consommateur **pourra accéder au support durable** comportant la preuve de son consentement (R223-2).
> « **Le consentement recueilli ne peut faire l'objet d'un renouvellement tacite ni être considéré comme tacitement reconduit à l'expiration du délai mentionné au 3°.** »

**R223-1, II — ce qui n'est PAS un consentement** [F] : information incomplète ; appel hors période ou hors créneaux ; et
> « **3° Le consentement ne résulte pas d'un acte positif clair. Ne constituent notamment pas un acte positif clair une mention prérédigée sur un document par laquelle le consommateur reconnaît, sans qu'aucun accord exprès de sa part ne soit nécessaire, consentir à être appelé, ou le simple fait qu'il poursuive sa navigation sur un site internet.** »

**R223-2 — conservation et preuve** [F] : archivage numérique des informations du I, **date et heure du consentement**, et le cas échéant date/horaire dérogatoire accepté. « Ces éléments sont conservés pendant une période de **trois ans** à compter de la date de recueil du consentement. » Fourniture **gratuite sur support durable**, dans un délai raisonnable et de manière individualisée, au consommateur qui en fait la demande. Le support durable peut être une **interface en ligne dédiée** avec authentification sécurisée, qui **ne peut consister en la création d'un compte client**.

> ⚠️ **Asymétrie à retenir : consentement valable 1 an, preuve à conserver 3 ans.** [F]

**R223-3 — retrait** [F] :
> « Le professionnel permet au consommateur de retirer à tout moment son consentement au démarchage téléphonique selon des modalités qui ne peuvent pas être plus complexes que celles de son recueil. **Ce retrait peut être exprimé oralement.** »

> 🔴 **Exigence fonctionnelle, pas clause de CGV** : si l'agent vocal passe des appels sortants, il **doit comprendre et enregistrer un retrait de consentement prononcé oralement pendant l'appel**, et le propager immédiatement. [F pour le texte, [H] pour l'implication produit]

**R223-4 — rappel après demande d'information** (secteurs interdits du 5e alinéa) [F] : n'est pas de la prospection l'appel « en vue de répondre à une demande d'information émanant de ce consommateur », sous trois conditions : justifier de la réalité de la demande ; appeler **dans les cinq jours ouvrables** ; **objet limité** aux biens ou services demandés. Justifications archivées **3 ans**.

### 4.4 Ce qui reste permis : l'exception « contrat en cours »

**Texte, L223-1 al. 4** [F] : deux conditions cumulatives — (1) **dans le cadre de l'exécution d'un contrat en cours** ; (2) **rapport avec l'objet** de ce contrat.

**Un appel de confirmation ou de rappel de RDV entre-t-il dedans ?** Raisonnement en deux temps [H] :

**Premier temps — l'exception n'a probablement même pas besoin d'être invoquée.** L'interdiction du 1er alinéa vise « **démarcher** […] un consommateur qui n'a pas exprimé préalablement son consentement à faire l'objet de **prospections commerciales** ». Le champ est la **prospection commerciale**. Un appel de confirmation ou de rappel d'un RDV déjà pris **ne promeut rien** : il exécute une prestation convenue. → **hors du champ dès l'alinéa 1.** C'est l'argument principal et le plus solide.

**Second temps — l'alinéa 4 comme filet.** À supposer la qualification de prospection retenue, la prise de RDV est un engagement en cours d'exécution et l'appel de confirmation a un rapport direct avec son objet.

| Appel sortant | Qualification [H] | Consentement requis ? |
|---|---|---|
| « Je confirme votre RDV de jeudi 14 h » | Exécution, hors prospection | **Non** |
| « Rappel : vous avez RDV demain » | Exécution, hors prospection | **Non** |
| « Votre RDV est déplacé, est-ce OK ? » | Exécution, hors prospection | **Non** |
| « Votre coupe date de 6 semaines, on vous reprend RDV ? » | **Prospection** — le contrat précédent est **exécuté, donc terminé**, il n'est plus « en cours » | **OUI** ⚠️ |
| Offre commerciale greffée sur un appel de confirmation licite | **Prospection** | **OUI** ⚠️ |

> 🔴 **La ligne rouge produit : la relance / réactivation de clients dormants.** C'est la fonctionnalité la plus demandée par un salon, et c'est **de la prospection commerciale au sens de L223-1**, parce qu'un contrat **exécuté** n'est plus un contrat **en cours**. Elle exige un opt-in R223-1 conforme (≤ 1 an, preuve archivée 3 ans, créneaux, compteur de fréquence).
> Le seul angle défendable sans opt-in serait un **abonnement / forfait en cours d'exécution** (formule d'entretien mensuelle), où la relance a bien « rapport avec l'objet du contrat en cours ». **[H] — c'est le point qui mérite l'avis d'un avocat en premier.**

### 4.5 Suppression de Bloctel — confirmée, base légale et décrets compris

| Article | Statut au 14/09/2026 |
|---|---|
| **L223-3** (interdiction de louer/vendre des fichiers contenant des inscrits) | « VERSION EN VIGUEUR DU 01 JUILLET 2016 AU 11 AOÛT 2026 — **Abrogé par LOI n°2025-594 du 30 juin 2025 - art. 13 (V)** » [F] |
| **L223-4** (désignation par arrêté de l'organisme gestionnaire) | « VERSION EN VIGUEUR DU 26 JUILLET 2020 AU 11 AOÛT 2026 — **Abrogé** » [F] |
| **R223-4-1, R223-5, R223-6, R223-7, R223-8** | **Abrogés par décret 2026-662 art. 3**, effet 11 août 2026 [F] |
| Intitulé du chapitre III | « Opposition » → « **Consentement** » [F] |

> **Le mécanisme d'opposition (liste Bloctel) a disparu du code de la consommation le 11 août 2026. Il n'est remplacé par aucun dispositif équivalent : le régime est désormais purement consentement-préalable, sans liste centralisée.** [F]
> **[NV]** — le sort pratique de l'organisme gestionnaire (Opposetel) et de sa base n'a pas été recherché : fait de gestion, non couvert par une source primaire.

**Articles du chapitre III qui subsistent** [F] :
- **L223-2** (modifié, en vigueur depuis le 11 août 2026) :
> « **Lorsqu'un professionnel recueille les données téléphoniques d'un consommateur, il informe celui-ci que toute sollicitation téléphonique effectuée à des fins commerciales, sauf si elle intervient dans le cadre de l'exécution d'un contrat en cours au sens du quatrième alinéa de l'article L. 223-1, suppose son consentement préalable. Lorsque ce recueil de données téléphoniques se fait à l'occasion de la conclusion d'un contrat, le contrat mentionne, de manière claire et compréhensible, qu'il est interdit de démarcher par téléphone un consommateur sans son consentement préalable.** »
> 🔴 **Obligation directe sur tout formulaire de collecte de numéro — y compris la prise de RDV en ligne** : mention d'information obligatoire ; **et clause obligatoire dans le contrat** si un contrat est conclu.
- **L223-5** : l'interdiction ne s'applique pas à la prospection en vue de la fourniture de journaux, périodiques ou magazines (avec décret sur les jours/horaires).
- **L223-7** : « Les conditions de la prospection directe au moyen d'un **automate d'appel** […] sont prévues à l'**article L. 34-5 du code des postes et des communications électroniques**. » → **voir §4.6, l'angle mort le plus grave.**
- **L223-8** (chapitre III bis, en vigueur depuis le 02/07/2025) : interdiction de la prospection **par message / e-mail / réseaux sociaux** dans les mêmes secteurs (rénovation énergétique, adaptation du logement). **Sans objet pour salons et restaurants.** L'article **L242-16-1** (sanction) n'a pas été extrait — **[NV]**.

### 4.6 ⚠️ ANGLE MORT CRITIQUE — CPCE L34-5, « système automatisé d'appels »

**Ce point n'était pas dans la commande. Pour un agent vocal IA, il est potentiellement plus contraignant que L223-1 — et il n'est pas limité aux consommateurs.**

**Article L34-5 CPCE** — version en vigueur depuis le 26 juillet 2020 (LOI n° 2020-901 du 24 juillet 2020, art. 8).
https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006070987/LEGISCTA000006165910 — 14/09/2026 [F] :
> « **Est interdite la prospection directe au moyen de système automatisé de communications électroniques au sens du 6° de l'article L. 32, d'un télécopieur ou de courriers électroniques utilisant les coordonnées d'une personne physique, abonné ou utilisateur, qui n'a pas exprimé préalablement son consentement à recevoir des prospections directes par ce moyen.**
> […]
> **Constitue une prospection directe l'envoi de tout message destiné à promouvoir, directement ou indirectement, des biens, des services ou l'image d'une personne vendant des biens ou fournissant des services.** […]
> **Dans tous les cas, il est interdit d'émettre, à des fins de prospection directe, des messages au moyen de système automatisé de communications électroniques […] sans indiquer de coordonnées valables auxquelles le destinataire puisse utilement transmettre une demande tendant à obtenir que ces communications cessent sans frais autres que ceux liés à la transmission de celle-ci. Il est également interdit de dissimuler l'identité de la personne pour le compte de laquelle la communication est émise et de mentionner un objet sans rapport avec la prestation ou le service proposé.**
> **La Commission nationale de l'informatique et des libertés veille** […] au respect des dispositions du présent article […] »

**La définition — article L32, 32° CPCE** [F] :
> « **32° Système automatisé d'appels et d'envois de messages.** On entend par système automatisé d'appels et d'envois de messages **les systèmes émettant des appels ou des messages de manière automatique vers plusieurs utilisateurs finals conformément aux instructions établies pour ce système.** »

⚠️ **Note de rigueur [F]** : L34-5 renvoie au « 6° de l'article L. 32 », mais le 6° de L32 en vigueur définit les « Services de communications électroniques ». **La définition du système automatisé est au 32°.** Le renvoi interne de L34-5 est **périmé**, vraisemblablement non actualisé après la renumérotation de L32 [H, texte renumérotant non vérifié]. Cela n'affaiblit pas l'analyse : la définition existe et est claire.

> 🔴 **CONSÉQUENCES [H] — l'angle le plus dangereux du dossier, à faire arbitrer par un avocat :**
> 1. **Un agent vocal IA qui passe des appels sortants automatiquement vers plusieurs destinataires, selon des instructions préétablies, correspond littéralement à la définition du L32, 32°** — chaque terme colle.
> 2. Si la qualification est retenue, **L34-5 impose un consentement préalable à toute prospection directe par ce moyen, EN PLUS de L223-1.**
> 3. **Le champ de L34-5 est PLUS LARGE que celui de L223-1** : il vise « **une personne physique, abonné ou utilisateur** », **pas seulement un consommateur**. → **la prospection B2B de l'éditeur vers des commerçants personnes physiques (coiffeur en nom propre, restaurateur en EI) pourrait y tomber**, là où L223-1 ne s'applique pas. **C'est exactement le cas d'usage de l'éditeur pour son propre développement commercial.**
> 4. **Obligations de forme cumulatives, applicables « dans tous les cas »** : coordonnées valables pour demander l'arrêt ; **ne pas dissimuler l'identité de la personne pour le compte de laquelle l'appel est émis** ; ne pas mentionner un objet sans rapport.
> 5. **L'autorité ici est la CNIL**, pas la DGCCRF — avec le régime de sanctions du RGPD.
>
> **Le point 4 converge avec l'AI Act** : un agent vocal sortant doit **annoncer pour le compte de qui il appelle** (CPCE L34-5 + C. conso. L121-2, 3°) **et** qu'il est une IA (AI Act art. 50 §1). **Deux mentions distinctes, toutes deux obligatoires.**

**[NV]** : aucune position officielle (CNIL, Arcep, DGCCRF) sur la qualification d'un agent conversationnel IA comme « système automatisé d'appels » n'a été trouvée. Recherche impossible sans WebSearch. **C'est la première question à poser à un avocat.**

### 4.7 Jours, horaires, fréquence — le décret 2022-1313 n'est plus le texte applicable

**Réponse directe : non.** Le décret n° 2022-1313 du 13 octobre 2022 avait créé D223-9, mais cet article a été **réécrit par le décret n° 2026-662 du 23 juillet 2026 (art. 4), avec effet au 11 août 2026** [F, vérifié par comparaison ChronoLégi].

**Article D223-9 — version en vigueur depuis le 11 août 2026** [F] :
> « La sollicitation d'un consommateur par voie téléphonique à des fins de prospection commerciale, y compris celle visée à l'article L. 223-5, n'est autorisée d'une part que **du lundi au vendredi, sauf lorsque ces jours sont fériés** en application de l'article L. 3133-1 du code du travail, et d'autre part seulement **de 10 heures à 13 heures et de 14 heures à 20 heures, ces heures correspondant à celles du fuseau horaire du consommateur**.
>
> Il est interdit à un même professionnel, directement ou par l'intermédiaire d'un tiers agissant pour son compte, **de démarcher ou de tenter de démarcher téléphoniquement un même consommateur plus de quatre fois au cours d'une période de trente jours calendaires.** »

**Créneaux exacts en vigueur au 14/09/2026** [F] :
- **Jours** : lundi → vendredi, **hors jours fériés** (L3133-1 C. trav.)
- **Horaires** : **10 h–13 h** et **14 h–20 h**, **dans le fuseau horaire du consommateur**
- **Exclus** : samedi, dimanche, jours fériés, et la **pause 13 h–14 h**
- **Fréquence** : **4 sollicitations ou tentatives max par consommateur et par professionnel sur 30 jours calendaires** — « démarcher **ou tenter de démarcher** » : **les appels non décrochés comptent**

**Les deux changements du 11 août 2026** [F] :
1. **La dérogation horaire a changé de support et s'est durcie** : elle est remontée au **6e alinéa de L223-1**. Ancienne formulation (D223-9) : « consentement exprès et préalable ». Nouvelle : « **si le consommateur consent explicitement à être appelé à une date et à un horaire précisément spécifiés et que le professionnel peut en attester** ». → un accord général ne suffit plus : **date et heure précises, attestables**, archivées au titre de R223-2.
2. **La règle des 60 jours après refus oral a disparu** de D223-9 [F] — [H] : devenue redondante avec le droit de retrait oral de R223-3, plus radical.

### 4.8 Sanctions — article L242-16

https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006069565/LEGISCTA000032221841 — 14/09/2026.
**Version en vigueur depuis le 26 juillet 2020 — NON modifié par la loi 2025-594** [F] :
> « **Tout manquement aux dispositions des articles L. 223-1 à L. 223-5 est passible d'une amende administrative dont le montant ne peut excéder 75 000 € pour une personne physique et 375 000 € pour une personne morale.**
> […]
> **Par dérogation au premier alinéa de l'article L. 522-6, la décision prononcée en application du présent article par l'autorité administrative chargée de la concurrence et de la consommation est publiée aux frais de la personne sanctionnée.** »
> (Le report, l'anonymisation ou la non-publication ne sont possibles que si la publication causerait « un préjudice grave et disproportionné » ou perturberait gravement une enquête en cours.)

> 🔴 **Le *name and shame* est le PRINCIPE, pas l'exception.** Publication de plein droit, aux frais du sanctionné, par dérogation au droit commun de L522-6. **Pour un éditeur SaaS qui vend à des commerçants, c'est plus dangereux que le montant.** [F]

**Autorité compétente** : « l'autorité administrative chargée de la concurrence et de la consommation » — **c'est la DGCCRF** [H] (périphrase consacrée du code de la consommation ; le texte de désignation n'a pas été vérifié — **[NV]**).

**Coopération entre autorités — article 17, I de la loi n° 2025-594** [F] :
> « L'article 11 du code de procédure pénale ou les dispositions relatives au secret professionnel ne font pas obstacle à la communication entre **les agents de la concurrence, de la consommation et de la répression des fraudes, l'Autorité de régulation des communications électroniques, des postes et de la distribution de la presse et la Commission nationale de l'informatique et des libertés** d'informations et de documents […] nécessaires à la recherche et à la constatation des infractions et des manquements définis : 1° A la section 5 du chapitre Ier et au chapitre III du titre II du livre II ainsi qu'aux articles L. 242-12, L. 242-14 et **L. 242-16** du code de la consommation ; 2° Aux articles **L. 34-5** et **L. 44** du code des postes et des communications électroniques. »

> 🔴 **DGCCRF + Arcep + CNIL échangent désormais librement leurs dossiers sur le démarchage. Un signalement chez l'une remonte chez les autres.** [F] Les §§1, 2, 4 et 5 de ce rapport ne sont donc pas des silos : **un même appel mal conçu déclenche les trois.**

### 4.9 Synthèse par cas d'usage

| Cas d'usage | Qualification | Consentement L223-1 ? | Créneaux D223-9 ? | Annonce IA (art. 50 §1) ? | Marquage (§2) ? |
|---|---|---|---|---|---|
| **① Appel ENTRANT** : le client appelle, l'agent décroche | **Hors champ de L223-1** — le professionnel ne « démarche » pas, il reçoit [H] | **Non** | **Non** | **OUI, dès le décroché** [F] | **OUI** [F/H] |
| **② Sortant de service** : confirmation / rappel / report de RDV | Hors prospection (al. 1) ; à défaut, exception « contrat en cours » (al. 4) [H] | **Non** [H] | **Non** si hors prospection [H] — **prudence : appliquer les créneaux par défaut** | **OUI** [F] | **OUI** [F/H] |
| **③ Sortant de relance** : « ça fait 6 semaines, on reprend RDV ? » | **Prospection** [H] | **OUI**, opt-in R223-1 complet | **OUI** | **OUI** [F] | **OUI** [F/H] |
| **④ Sortant de prospection pure** vers des consommateurs | Prospection [F] | **OUI** | **OUI** | **OUI** | **OUI** |
| **⑤ Prospection B2B de l'éditeur** vers salons/restaurants | L223-1 ne s'applique pas (« consommateur ») [H] — ⚠️ **mais CPCE L34-5 peut s'appliquer** si personne physique [H] | L223-1 : non — **L34-5 : probablement oui** ⚠️ | L223-1 : non | **OUI si c'est l'agent IA qui appelle** [F] | **OUI** |

**Fondement du « hors champ » de l'appel entrant** [H] : L223-1 al. 1 interdit de « **démarcher** par téléphone […] un consommateur ». *Démarcher* suppose une démarche **active du professionnel vers le consommateur**. Quand le consommateur compose lui-même le numéro, il n'y a ni démarchage ni prospection. **Aucun texte primaire ne l'énonce expressément** — c'est une lecture du verbe employé, pas une exception écrite. Lecture robuste, mais [H].

---

## 5. Statut télécom — devient-on opérateur ?

### 5.1 Les définitions (art. L32 CPCE)

https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049571421 — 13/09/2026. Version en vigueur depuis le 23/05/2024 (LOI n° 2024-449, art. 34). [F]
- **2° Réseau de communications électroniques** : « toute installation ou tout ensemble d'installations de transport ou de diffusion ainsi que, le cas échéant, les autres moyens assurant l'acheminement de communications électroniques »
- **6° Services de communications électroniques** : « les services fournis via des réseaux de communications électroniques qui comprennent au moins l'un des types de services suivants : un service d'accès à Internet ; **un service de communications interpersonnelles** ; un service consistant entièrement ou principalement en la transmission de signaux »
- **15° Opérateur** : « **toute personne physique ou morale exploitant un réseau de communications électroniques ouvert au public OU fournissant au public un service de communications électroniques** »

« Exploitant de réseau » et « fournisseur de service de communications électroniques » : pas de définition autonome confirmée dans l'énumération de L32 (extraction partielle) — **[NV]**. Ce sont **les deux branches de la définition du 15°**, employées comme catégories distinctes au III de L32-1. [F]

> **Lecture opérationnelle** [H, adossé à L32 6° et 15°] : la qualification d'opérateur ne dépend **ni** de la possession d'un réseau, **ni** d'une immatriculation, **ni** d'un seuil de chiffre d'affaires. Elle dépend d'un seul fait : **fournir au public un service de communications électroniques**.

### 5.2 ⚠️ LA RÉPONSE CENTRALE : la déclaration L33-1 n'existe plus

**Article L33-1 I** — version en vigueur depuis le 11 mars 2023, https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000047293234 — 13/09/2026 [F] :
> « I. – L'établissement et l'exploitation des réseaux ouverts au public et la fourniture au public de services de communications électroniques **sont libres sous réserve du respect de règles portant sur** : »

**Le I ne contient plus aucune obligation de déclaration.** Le **II** n'est pas la déclaration, c'est la **séparation comptable** au-delà d'un seuil de CA fixé par arrêté. [F]

**Arcep, extranet, « Questions fréquentes »** — https://extranet.arcep.fr/communications-electroniques/questions-frequentes — 13/09/2026 [F] :
> « **L'ordonnance n° 2021-650 du 26 mai 2021 a supprimé l'obligation de déclaration préalable à l'établissement ou l'exploitation d'un réseau de communications électroniques ouvert au public** »
> « **Seule la nature de l'activité effective de la structure détermine si celle-ci doit être considérée comme celle d'un opérateur de communications électroniques** » — les activités de conseil ou d'assistance en télécommunications ne constituent pas une activité d'opérateur.

L'Arcep précise que **l'extranet ne propose plus de formulaire de déclaration** et que **l'Autorité n'a plus compétence pour délivrer un récépissé**. [F]

⚠️ **Il n'existe donc plus, dans le L33-1 en vigueur, ni « seuil », ni exemption pour « réseaux internes » ou « établissements ouverts au public ».** Ces notions appartenaient au régime antérieur, abrogé. Les seules exclusions subsistantes sont celles de l'**article L33** (installations de l'État pour la défense/sécurité publique ; installations utilisant des fréquences assignées par l'Arcom). [F]

#### Ce qui a remplacé le récépissé : l'« identifiant CE »
https://extranet.arcep.fr/communications-electroniques/identifiant-ce — 13/09/2026 [F]
Identifiant de **4 caractères** (« identifiant de communications électroniques »), successeur du code opérateur, utilisé dans les **échanges informatiques entre opérateurs**. L'Arcep l'attribue à trois catégories :
1. structures demandant **des ressources en numérotation ou des fréquences** ;
2. **structures qui reçoivent des ressources de numérotation mises à disposition par un opérateur attributaire** ← **c'est le cas de l'éditeur** ;
3. structures sans ressources propres adhérant aux instances centrales (portabilité, plans d'acheminement d'urgence, renseignements téléphoniques…).
L'Arcep souligne que **l'identifiant CE n'est pas requis pour exercer une activité d'opérateur**. [F]
Référentiel public : https://extranet.arcep.fr/uploads/identifiants_CE.csv — Demande : https://extranet.arcep.fr/communications-electroniques/identifiant-ce/demande-identifiant-ce

> ### 🔴 **RÉPONSE À LA QUESTION POSÉE**
> **L'éditeur devient très probablement opérateur au sens de l'article L32, 15° CPCE — mais il n'a AUCUNE déclaration à faire, car la formalité a été supprimée en 2021.** [H sur la qualification, **[F]** sur l'absence de formalité]
>
> Raisonnement : l'éditeur « fournit au public un service de communications électroniques » (communications interpersonnelles **fondées sur la numérotation**) dès lors qu'il met à disposition de ses clients une ligne sous un numéro du plan national. Le critère Arcep est « la nature de l'activité effective ». Revendre de la voix sous un numéro affecté au client **est** une activité d'opérateur ; conseiller ou intégrer ne l'est pas.
>
> **Contre-lecture, à documenter si l'on veut rester hors du statut** [H] : si le contrat de téléphonie est conclu **directement entre le commerçant et l'opérateur**, l'éditeur n'étant que **mandataire technique** — sans facturer la communication, sans être affectataire du numéro — alors il ne fournit pas le service au public et n'est pas opérateur. **Le montage décrit (« l'éditeur achète les numéros et les affecte à ses clients ») ne relève PAS de cette contre-lecture.**
> **C'est un arbitrage de modèle économique, pas seulement juridique : il détermine si l'éditeur porte ou non les obligations du §5.4.**

**La clause d'allègement qui ne s'applique pas ici** — L33-1 I, dernier alinéa [F] :
> « Les fournisseurs de services de communications interpersonnelles **non-fondés sur la numérotation** ne sont concernés que par les règles énoncées aux a, b, c, e, f bis, g, k, l, n, n bis, n ter et o du présent I. »
→ Le régime allégé (sans urgences au f, sans annuaire au h, sans interconnexion au i) ne bénéficie **qu'aux services non fondés sur la numérotation**. **Dès que l'éditeur affecte des numéros du plan national, il en est exclu.** [H, lecture directe]

### 5.3 Attribution des numéros — article L44 CPCE

https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000051830329 — 13/09/2026. Version en vigueur du 02/07/2025 au 01/01/2027 (LOI n° 2025-594, art. 16). [F]

**I bis** [F] : « L'autorité attribue […] **aux opérateurs qui le demandent**, des ressources de numérotation. » Et : « **En vue de fournir des services innovants, l'autorité peut aussi attribuer des ressources de numérotation […] à des personnes morales autres que les opérateurs** à condition que […] L'autorité s'assure que ces personnes morales sont en mesure de gérer les ressources de numérotation et de respecter les obligations prévues au présent article. »

→ **Un non-opérateur peut-il attribuer un numéro à un tiers ?** L'attribution **primaire** par l'Arcep est réservée aux opérateurs, **sauf** le canal « services innovants » ouvert aux personnes morales non-opérateurs. [F]
En pratique, l'éditeur ne passe pas par l'attribution primaire : il reçoit des numéros par **mise à disposition** d'un opérateur attributaire (Telnyx, OVHcloud) — ce qui déclenche la **catégorie 2 de l'identifiant CE**. [H]

**I ter** [F] : la décision d'attribution fixe type de service, prescriptions de bonne utilisation, portabilité, durée (≤ 20 ans), modalités de cession ; les ressources « **ne peuvent faire l'objet d'une cession qu'après accord de l'Arcep** ».
**II** : taxe annuelle de numérotation, unité de base « a » ≤ 0,023 €, **par numéro à dix chiffres attribué**. [F]

**Éligibilité géographique** — Arcep, fiche « Le plan de numérotation pour les professionnels », https://www.arcep.fr/mes-demarches-et-services/entreprises/fiches-pratiques/plan-numerotation-professionnels.html — 13/09/2026 [F] :
- l'affectation donne à l'utilisateur final **l'usage exclusif** d'un numéro ;
- le numéro doit permettre, pendant la durée de l'affectation, de **rappeler l'utilisateur à l'origine de l'appel, ou l'organisme qu'il représente** ;
- les numéros **01-05, 06-07 et 09** ne peuvent être affectés « qu'à un utilisateur final **résidant habituellement ou temporairement, ou justifiant de liens stables impliquant une présence fréquente et significative, sur le territoire correspondant à ce numéro** ».

→ Structurant [H] : **le numéro affecté doit rester joignable et rattaché au commerçant**, pas à une plateforme anonyme. Et le KYC géographique n'est pas une lubie du fournisseur : c'est une règle du plan de numérotation.

**Plan de numérotation en vigueur** : **décision Arcep n° 2018-0881 modifiée du 24 juillet 2018** (numéro et mention « modifiée » confirmés), PDF 37 p. : https://www.arcep.fr/uploads/tx_gsavis/18-0881.pdf — 13/09/2026 [F]. Dernière modification identifiée : **décision n° 2025-2215 du 27 novembre 2025**. Fichier des tranches : https://extranet.arcep.fr/uploads/MAJNUM.csv. Consultation publique sur de nouvelles évolutions ouverte du 23 juillet au 26 septembre 2025. [F]

### 5.4 🔴 LE POINT CRITIQUE : authentification des numéros (MAN) et appels sortants

⚠️ **Il n'existe pas d'article « L44-4 » portant le MAN. Le mécanisme est au IV de l'article L44.** [F]
(L'article L44-3 existe et prévoit que l'Arcep « participe à la lutte contre les services frauduleux ou abusifs et les numéros qui permettent d'y accéder ».)

**Texte du IV de l'article L44** [F] :
> « **Les opérateurs sont tenus de s'assurer que, lorsque leurs clients utilisateurs finals utilisent un numéro issu du plan de numérotation établi par l'autorité comme identifiant d'appelant pour les appels et messages qu'ils émettent, ces utilisateurs finals sont bien affectataires dudit numéro ou que l'affectataire dudit numéro a préalablement donné son accord pour cette utilisation.**
>
> Les opérateurs sont tenus de veiller à l'authenticité des numéros […] Les opérateurs utilisent un dispositif d'authentification […] Les opérateurs veillent à l'interopérabilité des dispositifs d'authentification […]
>
> **Lorsque le dispositif d'authentification n'est pas utilisé ou qu'il ne permet pas de confirmer l'authenticité d'un appel ou message destiné à l'un de ses clients utilisateurs finals ou transitant par son réseau, l'opérateur interrompt l'acheminement de l'appel ou du message.** […] »

**Le VI, qui vise explicitement les automates** [F] :
> « **L'autorité peut préciser les catégories de numéros du plan national de numérotation téléphonique qu'il est interdit d'utiliser comme identifiant de l'appelant présenté à l'appelé […] pour des appels ou des messages émis par des systèmes automatisés d'appels et d'envois de messages**, ainsi que les conditions dans lesquelles cette interdiction s'applique.
> L'autorité peut préciser les mesures que les opérateurs mettent en œuvre pour **interrompre l'acheminement des appels et des messages** […] qui ne respectent pas cette interdiction. […] »

#### ⚠️ Date d'entrée en vigueur : 25 juillet 2023, pas 1er octobre 2024
**Décision Arcep n° 2025-2215 du 27 novembre 2025**, publiée au JO — https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000054122929 — 14/09/2026 [F] :
> « Cette obligation est entrée en vigueur le **25 juillet 2023**. »
Cohérent avec la **LOI n° 2020-901 du 24 juillet 2020** (promulguée le 24 juillet 2020, + 3 ans = 25 juillet 2023) [F].
**La date du « 1er octobre 2024 » n'a été confirmée par aucune source primaire — [NV].** Elle correspond vraisemblablement à un jalon de déploiement opérationnel. **Ne pas l'écrire dans un document contractuel ou commercial sans l'avoir revérifiée.**

#### Ce que la décision n° 2025-2215 ajoute — décisif
Obligations nouvelles pesant sur les opérateurs [F] :
- **« définir la liste des numéros que chaque utilisateur final peut présenter comme identifiant d'appelant ou d'émetteur de messages »** ;
- **restreindre techniquement** la présentation d'identifiant d'appelant à cette seule liste ;
- disposer des **moyens contractuels et techniques de vérifier que l'autorisation de l'affectataire perdure** ;
- **masquer l'identifiant d'appelant** non authentifié (numéros mobiles, interconnexions internationales) **à compter du 1er janvier 2026** ;
- **usage effectif** : au moins un numéro affecté à un utilisateur final **dans l'année** suivant l'attribution du bloc.

#### Conséquence pour l'agent vocal qui appelle sous le numéro du commerçant
**Ce n'est PAS du spoofing illicite — à condition que la chaîne d'autorisation soit documentée et vérifiable.** Le IV pose exactement **deux hypothèses licites** : l'utilisateur final **est affectataire**, **ou** l'affectataire **a préalablement donné son accord**. [F]

Traduction [H, adossée à L44 IV et à la décision 2025-2215] :
1. Si l'éditeur est **affectataire** du numéro et l'« affecte » au commerçant : il faut que **le commerçant soit l'affectataire déclaré dans les systèmes de l'opérateur**, ou que l'éditeur autorise expressément l'usage — **accord préalable et traçable**.
2. Si le commerçant utilise **son propre numéro historique** comme identifiant d'appelant des appels émis par l'agent : il faut un **accord écrit de l'affectataire transmis à l'opérateur**, et **l'opérateur doit pouvoir vérifier que cet accord perdure**. **Hypothèse la plus risquée** : un accord non répercuté dans la « liste des numéros présentables » se traduira par un **blocage ou un masquage de l'appel** — la sanction est **technique et immédiate**, pas une amende.
3. **Le VI est une épée de Damoclès spécifique** : un agent vocal est, sans discussion possible, un « système automatisé d'appels ». **L'Arcep PEUT interdire certaines catégories de numéros comme identifiant d'appelant pour ces systèmes.** → **surveiller chaque révision du plan de numérotation.** [F sur le texte, [H] sur la qualification]

> **Livrable qui en découle : un mandat d'usage de numéro**, distinct des CGV (objet, numéros visés, durée, révocabilité, transmission à l'opérateur), **répercuté à l'opérateur** pour alimenter sa liste des numéros présentables. Sans cela, le montage est techniquement fragile **et** contractuellement en infraction (§5.6). [H]

### 5.5 Autres obligations résiduelles d'un opérateur

**Appels d'urgence** — L33-1 I f) [F] :
> « **L'acheminement gratuit des communications d'urgence.** A ce titre, les opérateurs mettent en œuvre toute mesure permettant de garantir la continuité de l'acheminement de ces communications. Ils sont chargés de mettre en place une supervision technique permettant d'assurer, dans les meilleurs délais, une remontée d'alerte […] **Ils fournissent également gratuitement aux services d'urgence l'information relative à la localisation de l'appelant** ; »
Article **D98-8 CPCE** (LEGIARTI000044164666, en vigueur depuis le 03/10/2021) : règles d'acheminement et de localisation, liste des numéros d'urgence déterminée par l'Arcep. [F]
> 🔴 **Point d'attention majeur** [H] : **un agent vocal ne peut pas traiter un appel d'urgence.** Si l'éditeur fournit la ligne, l'acheminement du 15/17/18/112 doit rester possible et **gratuit**, avec remontée de localisation. **À traiter explicitement dans l'architecture d'appel** — et ce n'est pas dans les table-stakes actuelles du concept produit.

**Annuaire universel** — **article L34 CPCE** (en vigueur depuis le 02/07/2025, LOI n° 2025-594 art. 15), https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000051830311 — 13/09/2026 [F] :
> « Sur toute demande présentée en vue d'éditer un annuaire universel ou de fournir un service universel de renseignements […] **les opérateurs sont tenus de communiquer** […] **la liste de tous les abonnés ou utilisateurs auxquels ils ont affecté, directement ou par l'intermédiaire d'un distributeur, un ou plusieurs numéros du plan national de numérotation téléphonique prévu à l'article L. 44.** »
→ ⚠️ Noter « **ou par l'intermédiaire d'un distributeur** » : **le CPCE envisage explicitement la chaîne opérateur → distributeur → utilisateur final. L'éditeur, dans le montage décrit, EST ce distributeur.** [F]
Le même article impose le **consentement préalable** de l'abonné à toute inscription annuaire et le droit de s'opposer à l'utilisation commerciale des informations nominatives. [F]

**Portabilité / mandat** — L44 I ter, 4° prévoit « les prescriptions relatives à la portabilité du numéro » dans la décision d'attribution [F]. Mécanique du mandat décrite côté fournisseur (OVHcloud, CP Téléphonie §3.6) [F2].
⚠️ **Ne pas confondre : « MAN » = Mécanisme d'Authentification des Numéros (L44 IV), PAS le mandat de portabilité.**

### 5.6 Ce que Telnyx et OVHcloud imposent à un revendeur [F2]

#### Telnyx
- **Acceptable Use Policy** — https://telnyx.com/acceptable-use-policy — 13/09/2026 : interdiction d'utiliser « **Telnyx numbering resources […] as the Calling Line Identification (CLI) in any manner which Telnyx, in its sole discretion, constitutes as fraud, deceptive or spam** » ; interdiction d'acquérir des numéros « with the intent or having the effect of **hoarding, warehousing, squatting, or parking** such TNs without active use ».
- **Terms and Conditions of Service** — https://telnyx.com/terms-and-conditions — 13/09/2026 :
  - **§11.19** : « Customer shall not use, and shall not permit any third party to use, the Services to **hand off, relay, route, transit, intermediate, gateway, or terminate voice traffic that was already originated by any other carrier** » → **la revente en transit/terminaison de gros exige une autorisation écrite distincte.**
  - **§11.2** : « Customer is **solely responsible** for (a) content of information and communications transmitted using the Services […] » — le client doit **faire respecter les policies et lois par ses propres utilisateurs finaux**.
  - **§11.11** : obligation de « **transmitting accurate caller identification information and complying with all applicable caller ID rules** ».
  - **§11.12** : mandat (« attorney-in-fact ») donné à Telnyx pour signer les **letters of authorization** de portabilité.
  - **§12.1** : le client est responsable du **maintien à jour de l'adresse d'urgence pour chaque numéro**.
- **KYC France** : servi par API dynamique (`GET /requirements`, https://developers.telnyx.com/docs/numbers/phone-numbers/regulatory-requirements), **pas publié en clair — [NV]**, à récupérer sur le compte de l'éditeur.
- Les URL `telnyx.com/legal`, `/legal-center`, `/legal/msa`, `/service-terms` renvoient **404** : la documentation vit sous `telnyx.com/<slug>` sans préfixe `/legal`.

#### OVHcloud — ⚠️ point bloquant pour le modèle décrit
**Conditions particulières des Services de Téléphonie, version du 8 juillet 2025** (PDF 11 p.) : https://contract.eu.ovhapis.com/1.0/pdf/contrat_genTelephony-fr.pdf — 13/09/2026 [F2]
- **§2.2** : « Les numéros de téléphone français sont **exclusivement réservés aux utilisateurs résidant en France métropolitaine sur présentation de pièces justificatives**. Conformément à la réglementation, ce numéro **ne peut être ni cédé, ni vendu** […] »
- **§3.2** : « le Client doit adresser **par voie postale** à OVHcloud une liste de documents justificatifs de son **identité**, de son **lieu de résidence** et de sa **domiciliation bancaire** […] À défaut […] le Service de Téléphonie sera **strictement limité à la seule réception d'appels** […] »
- **§3.4 — restrictions d'usage** — le Client s'engage à ne pas utiliser le Service :
  > « e) avec l'utilisation des **robots d'appels** et/ou des opérations de "**spoofing**" […] ;
  > f) avec l'utilisation des systèmes du type **automate**, *soft switch*, PABX ou IP PBX, ou n'importe quel autre type de système **permettant des appels automatisés** ou de partage du compte SIP et/ou des identifiants ;
  > g) avec **plus d'un utilisateur par compte SIP** […] ;
  > h) **pour les revendre** ;
  > j) par l'entremise d'**utilisateurs domiciliés géographiquement dans un pays différent de celui de l'adresse du Client** ; »
  Le même § renvoie aux « bonnes pratiques et interdictions édictées par la **décision n° 2018-0881 de l'ARCEP dans sa version en vigueur** ».
- **§3.5** : OVHcloud met à disposition des éditeurs d'annuaire les informations relatives aux utilisateurs ; le Client les tient à jour via son Espace Client.
- **§2.1** : accès aux **appels d'urgence** avec transmission de **l'adresse de facturation** pour la géolocalisation — « **La localisation exacte réelle du Client n'est pas prise en considération à cet effet.** »
- **§5.1** : reconduction automatique pour des périodes de même durée que la durée initiale.

**Conditions Particulières du Service SIP Trunk, v. 02/11/2015** : https://www.ovh.com/fr/support/documents_legaux/Conditions_particulieres_SIP_trunk.pdf — 13/09/2026 [F2]
- **Art. 3** : « Le Client est le responsable entier et exclusif des identifiants d'enregistrement fournis par OVH. … **Sans l'autorisation écrite d'OVH, le Client s'interdit toute revente de communications.** »
- **Art. 6** : durée indéterminée, tacite reconduction mensuelle, résiliable à tout moment.

> ### 🔴 **Verdict fournisseur** [H, adossé aux clauses citées]
> - **L'offre de téléphonie de DÉTAIL d'OVHcloud est juridiquement incompatible avec le produit décrit.** Elle interdit **cumulativement** les robots d'appels (e), les automates et le partage de compte SIP (f), plus d'un utilisateur par compte SIP (g), la revente (h) et le spoofing (e). **Un agent vocal multi-commerçants viole au moins quatre de ces cinq interdictions.**
> - **Le SIP Trunk OVH est envisageable, mais la revente exige une autorisation écrite préalable d'OVH** (art. 3). **Sans cet écrit au dossier, le montage est en infraction contractuelle dès le premier client.**
> - **Telnyx est structurellement plus adapté** (CPaaS assumant sous-comptes et cas d'usage automatisés), mais impose : **CLI exacte** (§11.11), **responsabilité pleine de l'éditeur pour ses utilisateurs finaux** (§11.2), **adresse d'urgence à jour par numéro** (§12.1), et **autorisation écrite distincte** pour toute activité de transit/terminaison de gros (§11.19).

### 5.7 Conclusion du volet télécom

**Statut le plus probable : opérateur de communications électroniques au sens de l'article L32, 15° CPCE — sans aucune formalité déclarative à accomplir.** [H sur la qualification, [F] sur chacune de ses conséquences]

**Ce que l'éditeur n'a PAS à faire** : aucune déclaration Arcep (supprimée en 2021) ; aucun récépissé (l'Arcep n'en délivre plus) ; pas de séparation comptable sous le seuil de l'arrêté (L33-1 II). [F]

**Ce que l'éditeur DOIT faire** : identifiant CE · acheminement gratuit des urgences avec localisation · dossier KYC par commerçant (identité, établissement dans la zone du numéro, domiciliation bancaire) · mandat d'usage de numéro répercuté à l'opérateur · jamais de CLI sans accord de l'affectataire · réponse aux demandes d'annuaire universel · autorisation écrite de revente si SIP Trunk OVH · veille sur les décisions de numérotation (L44 VI). [F + F2]

---

## 6. Responsabilité des propos de l'agent

### 6.1 Y a-t-il une décision ? — réponse honnête

> **Aucune décision de la Cour de cassation ni de la CJUE jugeant qu'un professionnel est engagé par les déclarations de son système automatisé n'a été trouvée. [NV]**
>
> **C'est un échec d'accès, pas une preuve d'absence** : la recherche sur `courdecassation.fr` (interface Judilibre) a échoué techniquement — page rendue côté client, document vide sur deux requêtes distinctes (« chatbot », « intelligence artificielle chatbot »).

**Moffatt v. Air Canada** : les deux dépôts officiels (`canlii.org` et `decisions.civilresolutionbc.ca`) ont renvoyé **403 Forbidden**. La référence **2024 BCCRT 149, 14 février 2024, British Columbia Civil Resolution Tribunal** **n'a pas pu être vérifiée à la source — [NV]**.
Ce qui peut être affirmé sans vérification : **il s'agit d'une décision d'un tribunal administratif de résolution des litiges de la Colombie-Britannique (Canada). Elle n'a strictement aucune valeur en droit français** — ni comme précédent, ni comme autorité persuasive devant une juridiction française. **Elle ne peut servir qu'à illustrer un risque commercial dans une note interne, jamais à fonder une analyse juridique.** [H]

> **En droit français, la question se règle exclusivement par le droit commun. Ce qui suit n'est pas un pis-aller — c'est la vraie réponse, et elle est ferme.**

### 6.2 Le fondement décisif : l'offre est engageante

**Code civil, article 1114** — https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000032040891 — 13/09/2026 [F] :
> « **L'offre, faite à personne déterminée ou indéterminée, comprend les éléments essentiels du contrat envisagé et exprime la volonté de son auteur d'être lié en cas d'acceptation. À défaut, il y a seulement invitation à entrer en négociation.** »

⚠️ **La seconde phrase ne figurait pas dans la commande. Elle est pourtant la clé défensive** : ce qui ne comprend pas les éléments essentiels n'est pas une offre.

| Article | Texte | LEGIARTI |
|---|---|---|
| **1100** | « Les obligations naissent d'actes juridiques, de faits juridiques ou de l'autorité seule de la loi. […] » | LEGIARTI000032006706 |
| **1100-1** | « **Les actes juridiques sont des manifestations de volonté destinées à produire des effets de droit.** Ils peuvent être conventionnels ou unilatéraux. Ils obéissent, en tant que de raison […] aux règles qui gouvernent les contrats. » | LEGIARTI000032006708 |
| **1113** | « Le contrat est formé par la rencontre d'une offre et d'une acceptation par lesquelles les parties manifestent leur volonté de s'engager. » | LEGIARTI000032040896 |
| **1119** | « **Les conditions générales invoquées par une partie n'ont effet à l'égard de l'autre que si elles ont été portées à la connaissance de celle-ci et si elle les a acceptées.** » | LEGIARTI000032040866 |
| **1188** | « Le contrat s'interprète d'après la commune intention des parties plutôt qu'en s'arrêtant au sens littéral de ses termes. » | LEGIARTI000032041270 |

**Le raisonnement, en trois pas** [H, entièrement adossé aux textes ci-dessus] :
1. **L'agent vocal n'a pas de volonté propre.** L'article 1100-1 rattache l'acte juridique à une « manifestation de volonté ». La volonté manifestée par l'agent est **celle du commerçant qui l'a paramétré et mis en ligne**, exactement comme un distributeur automatique ou un formulaire en ligne. **Il n'existe aucun véhicule juridique permettant de dire « la machine a parlé, pas moi ».**
2. **Si l'agent énonce les éléments essentiels (prestation, date, prix, arrhes) et exprime la volonté d'être lié, c'est une offre au sens de l'article 1114.** L'acceptation du client la transforme en contrat (1113). **Le rendez-vous est pris, le prix annoncé est dû.**
3. **L'interprétation se fera contre le professionnel.** L'article 1188 impose de rechercher la commune intention des parties : un client qui a entendu « 45 euros, jeudi 14 h » a formé son intention sur cette base. Le commerçant **ne pourra pas opposer utilement une grille tarifaire interne que le client n'a jamais vue** — l'article 1119 verrouille ce point pour les CGV.

> 🔴 **Portée : le professionnel est engagé MÊME SI l'agent s'est trompé. L'erreur de l'agent est une erreur du professionnel, pas un vice du consentement du client.** [H]

### 6.3 Les fondements complémentaires

**Responsabilité délictuelle** [F] :
- **Art. 1240** : « Tout fait quelconque de l'homme, qui cause à autrui un dommage, oblige celui par la faute duquel il est arrivé à le réparer. »
- **Art. 1241** : « Chacun est responsable du dommage qu'il a causé non seulement par son fait, mais encore par sa négligence ou par son imprudence. »
- **Art. 1242 al. 1** : « On est responsable non seulement du dommage que l'on cause par son propre fait, mais encore de celui qui est causé par le fait des personnes dont on doit répondre, **ou des choses que l'on a sous sa garde**. »

**Sur 1242 al. 1 appliqué à un logiciel** [H] : la jurisprudence classique exige une **chose** et un **gardien** (usage, direction, contrôle). Un service logiciel purement immatériel s'y prête mal, et le fondement est de toute façon **inutile** ici : la faute personnelle (paramétrage, absence de garde-fous, absence de supervision) est directement caractérisable sur 1240. **Ne pas bâtir la défense sur 1242 al. 1** — mais **le citer dans l'analyse de risque**, car un demandeur pourra tenter de l'invoquer **contre l'éditeur**, gardien de la structure du modèle.

**Pratiques commerciales trompeuses — art. L121-2 C. conso.** (en vigueur depuis le 28/05/2022) [F] :
> « Une pratique commerciale est trompeuse si elle est commise dans l'une des circonstances suivantes : […] 2° Lorsqu'elle repose sur des allégations, indications ou présentations **fausses ou de nature à induire en erreur** et portant sur […] a) L'existence, la **disponibilité** ou la nature du bien ou du service ; b) Les caractéristiques essentielles […] ; **c) Le prix ou le mode de calcul du prix, le caractère promotionnel du prix, […] et les conditions de vente, de paiement et de livraison** […] ; e) La portée des engagements de l'annonceur […] ; f) L'identité, les qualités, les aptitudes et les droits du professionnel ; g) Le traitement des réclamations et les droits du consommateur ; **3° Lorsque la personne pour le compte de laquelle elle est mise en œuvre n'est pas clairement identifiable** ; »

> ⚠️ **Le 3° est directement mortel pour un agent vocal mal conçu** : si l'appelant ne peut pas identifier clairement **pour le compte de qui** l'agent parle, la pratique est trompeuse **par elle-même**, sans qu'il faille démontrer une fausse allégation. **L'agent doit se présenter au nom du commerçant, sans ambiguïté, dès les premières secondes.** [H, adossé au 3°] — c'est la même exigence que celle du CPCE L34-5 (§4.6) et elle se loge dans la même phrase d'ouverture que l'annonce AI Act.

**Art. L121-4 C. conso.** — 28 pratiques **réputées trompeuses en toutes circonstances** [F]. Les plus pertinentes :
> « 5° De proposer l'achat de produits ou la fourniture de services à un prix indiqué **sans révéler les raisons plausibles que pourrait avoir le professionnel de penser qu'il ne pourra fournir […] au prix indiqué** […] ;
> 7° De **déclarer faussement qu'un produit ou un service ne sera disponible que pendant une période très limitée** […] afin d'obtenir une décision immédiate […] ;
> 9° De déclarer ou de donner l'impression que la vente d'un produit ou la fourniture d'un service est licite alors qu'elle ne l'est pas ;
> 10° De présenter les droits conférés au consommateur par la loi comme constituant une caractéristique propre à la proposition faite par le professionnel ;
> 17° De communiquer des informations matériellement inexactes sur les conditions de marché ou sur les possibilités de trouver un produit ou un service […] »

> 🔴 **Un agent vocal qui « hallucine » une disponibilité, une promotion ou une urgence artificielle (« il ne reste qu'un créneau ») tombe mécaniquement dans le 5° ou le 7°. Il n'y a AUCUN élément intentionnel à démontrer : ce sont des pratiques réputées trompeuses.** [H]

### 6.4 État du droit européen

**Directive sur la responsabilité en matière d'IA (AILD, COM(2022) 496) — RETIRÉE** ✅ [F]
- Fiche de procédure EUR-Lex **2022/0303(COD)** : https://eur-lex.europa.eu/procedure/FR/2022_303 — 13/09/2026. Statut : « **Proposal withdrawn** », retrait du **06/10/2025**.
- Avis de retrait : **C/2025/5423** — https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=celex:52025XC05423 — JOUE du 6.10.2025.
- Retrait approuvé par la Commission lors de sa **2533e réunion du 16 juillet 2025** ; motifs au **COM(2025) 45 final du 11 février 2025, annexe IV**.

> **Au 14 septembre 2026, il n'existe AUCUN régime européen spécifique de responsabilité civile du fait de l'IA.** [F]

**Directive (UE) 2024/2853 du 23 octobre 2024 — responsabilité du fait des produits défectueux : le logiciel EST un produit** ✅
https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=OJ:L_202402853 — 13/09/2026 [F]
- **Article 4, point 1** : « tout meuble […] ; le terme comprend l'électricité, les fichiers de fabrication numériques, les matières premières et **les logiciels** ».
- Le considérant précise que le logiciel est couvert **quel que soit son mode de fourniture** — installé, accessible via un réseau, en nuage, **ou fourni en software-as-a-service**. [F]
- **Exclusion** : logiciels libres/open source développés ou fournis hors activité commerciale — sans effet ici.
- **Article 2 §1** : « La présente directive s'applique aux produits **mis sur le marché ou mis en service après le 9 décembre 2026**. »
- **Article 22 §1** : transposition au plus tard le **9 décembre 2026**.

> **Conséquence** [H] : le SaaS d'agent vocal **sera un « produit »**. Mis sur le marché après le 9 décembre 2026, il expose l'éditeur à une **responsabilité sans faute** du fait du défaut. Mais le dommage indemnisable sous ce régime est le **dommage corporel, matériel, ou la destruction/corruption de données** — **pas** le préjudice purement économique né d'un rendez-vous mal pris. **Le risque « l'agent a dit une bêtise » reste principalement contractuel (1114/1113) et consumériste (L121-2), pas produit.**
> **Mais la directive impose dès maintenant de documenter les tests, les garde-fous et les mises à jour de sécurité : une IA laissée sans correctif devient un produit défectueux.**

### 6.5 Mesures de réduction du risque, par ordre d'efficacité [H]

1. **Cantonner l'agent aux éléments non essentiels.** L'article 1114 n'est déclenché que si l'offre « comprend les éléments essentiels ». Un agent qui **ne chiffre jamais un prix et ne qualifie jamais une somme**, et qui renvoie explicitement à une confirmation écrite, produit une « **invitation à entrer en négociation** », pas une offre. **C'est la digue la plus efficace, et elle est purement produit.**
2. **Confirmation écrite systématique** (SMS/e-mail) reprenant prestation, date, prix et **nature exacte de la somme** — elle fixe le contenu contractuel et neutralise les dérives orales.
3. **Faire dire à l'agent, à l'ouverture, qui il est et pour qui il parle** (L121-2, 3° + CPCE L34-5 + AI Act art. 50 §1).
4. **Interdire par conception** l'annonce de disponibilités, promotions ou urgences **non vérifiées contre le système de réservation** (L121-4, 5° et 7°).
5. **Répartir contractuellement la responsabilité éditeur/commerçant** — mais **sans illusion** : à l'égard du consommateur, c'est **le commerçant** qui est engagé ; l'éditeur ne peut être recherché **qu'en garantie** par le commerçant.
6. **Journaliser et conserver les transcriptions** : en cas de litige, la preuve de ce que l'agent a réellement dit **protège autant qu'elle accuse**. (À arbitrer avec la politique de rétention du §3.3.)

---

## 7. Arrhes et acompte — le mot qui change le régime

### 7.1 Les textes, vérifiés

⚠️ **Vérification de numérotation faite** : la présomption d'arrhes est bien à l'article **L214-1** dans la codification issue de l'**ordonnance n° 2016-301 du 14 mars 2016** (ancien L114-1). [F]

**Article L214-1** — https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000032226990 — en vigueur depuis le 01/07/2016 — 13/09/2026 [F] :
> « **Sauf stipulation contraire, pour tout contrat de vente ou de prestation de services conclu entre un professionnel et un consommateur, les sommes versées d'avance sont des arrhes, au sens de l'article 1590 du code civil. Dans ce cas, chacun des contractants peut revenir sur son engagement, le consommateur en perdant les arrhes, le professionnel en les restituant au double.** »

**Article L214-2** — LEGIARTI000032226988, en vigueur depuis le 01/07/2016 [F] : pour une **vente de meubles**, tout versement d'avance sur le prix — « **quelles que soient la nature de ce versement et la dénomination qui lui est donnée dans l'acte** » — porte **intérêt au taux légal en matière civile** à l'expiration d'un délai de **trois mois** à compter du versement et jusqu'à la livraison, **sans préjudice de l'obligation de livrer** ; **même règle pour une prestation de services** (intérêts à compter de trois mois après le versement et jusqu'à l'exécution, sans préjudice de l'obligation d'exécuter) ; ces intérêts sont **déduits du solde**.

**Article L214-3** — LEGIARTI000032226986 [F] :
> « **Les dispositions du présent chapitre ne sont pas applicables aux commandes spéciales sur devis ni aux ventes de produits dont la fabrication est entreprise sur commande spéciale de l'acheteur.** »

**Code civil, article 1590** — LEGIARTI000006441327 [F] :
> « **Si la promesse de vendre a été faite avec des arrhes, chacun des contractants est maître de s'en départir, celui qui les a données, en les perdant, et celui qui les a reçues, en restituant le double.** »

⚠️ **L214-2 est le grand oublié des analyses courantes.** Un salon qui encaisse 20 € trois mois avant la prestation doit, en théorie, des intérêts au taux légal — déduits du solde. Marginal en montant, mais c'est du texte, et **cela interdit de présenter la somme comme définitivement acquise avant exécution.** [F + H]

### 7.2 Arrhes / acompte / dédit

**Fiche officielle** : « **Acompte, avance, arrhes et avoir : quelles différences ?** », https://www.service-public.gouv.fr/particuliers/vosdroits/F31187 — 13/09/2026 [F]
(⚠️ `service-public.fr` redirige en 301 vers `service-public.gouv.fr`. Et la fiche **F2050**, parfois citée pour les arrhes, porte en réalité sur le **classement des hôtels de tourisme** — vérifié.)

| Notion | Formulation officielle | Effet |
|---|---|---|
| **Acompte** | « Un 1er versement sur l'achat d'une marchandise ou d'une prestation de services. » | **Les deux parties sont définitivement engagées** ; la rupture ouvre droit à **dommages-intérêts** |
| **Arrhes** | « Une partie de la somme que vous versez d'avance […] » | **Chacun peut se dédire** ; le client perd les arrhes, le professionnel **rembourse le double** |
| **Avance** | « Une somme versée avant que la vente […] soit réalisée. » | **Juridiquement traitée comme des arrhes** |
| **Avoir** | valeur d'une marchandise rendue | accordé seulement si le vendeur l'accepte ; généralement valable un an |

Textes cités par la fiche : **C. civ. art. 1590 ; C. conso. art. L214-1 à L214-3.** [F]
**Dédit** [H] : clause organisant conventionnellement une faculté de se délier moyennant une somme convenue. **Les arrhes sont, en substance, un dédit légal à double détente. L'acompte n'ouvre aucune faculté de dédit.**

**[NV]** — La fiche DGCCRF sur `economie.gouv.fr` n'a pas pu être consultée : toutes les URL essayées renvoient **403 Forbidden**.

### 7.3 Le cas concret : le salon qui encaisse 20 € à la réservation

[H, entièrement déduit de L214-1 et 1590]

| Ce que l'agent vocal dit | Qualification | Le client annule | **Le salon annule** |
|---|---|---|---|
| **rien** (« vous versez 20 € ») | **Arrhes** (présomption L214-1) | Le salon **garde 20 €** | Le salon **rend 40 €** |
| « **arrhes** » | Arrhes | Le salon garde 20 € | Le salon **rend 40 €** |
| « **acompte** » | **Acompte** (stipulation contraire) | Le salon garde 20 € **et peut réclamer le solde + dommages-intérêts** | Le salon rend 20 € **et doit des dommages-intérêts** ; le client peut exiger l'exécution |

**Trois conséquences opérationnelles :**
1. **Le silence coûte le double.** Si l'agent ne qualifie rien, la présomption légale joue : arrhes. Un salon qui doit annuler (maladie du coiffeur, panne) rembourse **40 €**, pas 20 €. Sur un volume de réservations, ce n'est pas anecdotique.
2. **Dire « acompte » n'est pas « plus protecteur » — c'est un autre risque.** L'acompte verrouille le client, mais il verrouille **aussi le salon** : il ne peut plus annuler librement. Beaucoup de commerçants demandent « acompte » en croyant sécuriser l'encaissement et s'exposent en réalité à une **action en exécution forcée**.
3. 🔴 **Le mot prononcé par l'agent EST la stipulation contraire.** L'article L214-1 ne dit pas « sauf stipulation **écrite** » : il dit « **sauf stipulation contraire** ». **Une qualification orale claire, prononcée par l'agent au nom du commerçant et acceptée par le client, suffit à écarter la présomption légale.** C'est précisément pour cela qu'un agent vocal qui emploie les deux mots indifféremment est **dangereux** : **chaque appel crée un régime juridique différent, et le commerçant ne sait plus quel régime s'applique à quelle réservation.**

> **Recommandation forte** [H] : imposer dans le produit une **qualification unique, verrouillée au niveau du commerçant** — **un réglage, pas une formulation libre du modèle** — reprise **à l'identique** dans la confirmation écrite. **Interdire au modèle de générer librement les mots « arrhes », « acompte », « caution », « dépôt », « réservation payante ».**
> En pratique : **arrhes par défaut**, car c'est le régime légal supplétif et celui qui laisse au commerçant la liberté d'annuler — au prix du double.

### 7.4 ⚠️ Le mot « caution » est à proscrire
[H] Ni le code de la consommation ni la fiche Service-Public n'emploient « caution » pour désigner une somme versée d'avance ; en droit, la **caution est une sûreté personnelle** (une personne qui garantit la dette d'autrui). Un agent qui dit « une caution de 20 € » emploie un terme **juridiquement faux**, qui sera **interprété contre son auteur** au titre de l'article 1188.

### 7.5 Obligation d'information précontractuelle — art. L111-1 C. conso.

https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000044142438 — 13/09/2026 [F] :
> « **Avant que le consommateur ne soit lié par un contrat à titre onéreux, le professionnel communique au consommateur, de manière lisible et compréhensible, les informations suivantes :**
> 1° Les caractéristiques essentielles du bien ou du service […] ;
> 2° **Le prix ou tout autre avantage procuré au lieu ou en complément du paiement d'un prix** […] ;
> 3° **En l'absence d'exécution immédiate du contrat, la date ou le délai auquel le professionnel s'engage à délivrer le bien ou à exécuter le service** ;
> 4° Les informations relatives à l'**identité du professionnel**, à ses coordonnées postales, téléphoniques et électroniques et à ses activités […] ;
> 5° L'existence et les modalités de mise en œuvre des garanties légales […] **et les informations afférentes aux autres conditions contractuelles** ;
> 6° La possibilité de recourir à un **médiateur de la consommation** […] »

**La nature de la somme doit-elle être annoncée ? OUI.** [H, adossé au texte] Trois rattachements, le plus solide étant le **5°** — « les informations afférentes aux **autres conditions contractuelles** » : **la faculté de dédit, ou son absence, est une condition contractuelle majeure.** Subsidiairement le 2° (prix et modalités) et le 3° (date d'exécution, indissociable du régime d'annulation).
Et le tout « **de manière lisible et compréhensible** » : sur un canal **vocal**, cela signifie **énoncé clairement, pas noyé dans un débit rapide**, et **confirmé par écrit**. [H]

**Cohérence avec le §6** : une somme présentée comme « arrhes » puis traitée comme un acompte relève en outre de la **pratique commerciale trompeuse** au sens de L121-2, 2°, c) (« conditions de vente, de paiement »). [F + H]

---

## 8. CGV SaaS B2B

### 8.1 Le socle unique — art. L441-1 C. com.

https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000038414469 — en vigueur depuis le 26 avril 2019 — 13/09/2026 [F] :
> « **I. - Les conditions générales de vente comprennent notamment les conditions de règlement, ainsi que les éléments de détermination du prix tels que le barème des prix unitaires et les éventuelles réductions de prix.**
> **II. -** Toute personne […] qui établit des conditions générales de vente est tenue de les communiquer à tout acheteur qui en fait la demande pour une activité professionnelle. Cette communication s'effectue **par tout moyen constituant un support durable**. Ces conditions générales de vente **peuvent être différenciées selon les catégories d'acheteurs** […]
> **III. - Dès lors que les conditions générales de vente sont établies, elles constituent le socle unique de la négociation commerciale.** Dans le cadre de cette négociation, les parties peuvent convenir de **conditions particulières de vente** qui ne sont pas soumises à l'obligation de communication prescrite au II. **Lorsque le prix d'un service ne peut être déterminé a priori ou indiqué avec exactitude, le prestataire de services est tenu de communiquer au destinataire qui en fait la demande la méthode de calcul du prix permettant de vérifier ce dernier, ou un devis suffisamment détaillé.**
> **IV. - Tout manquement au II est passible d'une amende administrative dont le montant ne peut excéder 15 000 € pour une personne physique et 75 000 € pour une personne morale.** »

**Trois enseignements pour ce SaaS** :
1. Le III permet des **conditions particulières négociées** pour les gros comptes, sans obligation de les communiquer aux autres. [F]
2. Le II permet des **CGV différenciées par catégorie d'acheteurs** (indépendant / franchise / chaîne — et possiblement **éditeur hôte**). [F]
3. 🔴 Le dernier alinéa du III s'applique directement à une **tarification à l'usage** : **un SaaS vocal facturé à la minute ou à l'appel DOIT publier sa méthode de calcul sur demande.** [H, adossé au texte]

### 8.2 Délais de paiement et pénalités — art. L441-10 C. com.

https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000038414392 — **en vigueur du 26 avril 2019 au 1er janvier 2027** — 13/09/2026 [F]

| Élément | Valeur vérifiée | Source |
|---|---|---|
| Délai supplétif (à défaut de stipulation) | **30 jours** après réception / exécution | L441-10 I [F] |
| Délai conventionnel maximal | **60 jours** après émission de la facture | L441-10 I [F] |
| Dérogation | **45 jours fin de mois** après émission, **expressément stipulée par contrat** et sans abus manifeste | L441-10 I [F] |
| Facture périodique (art. 289, I, 3 CGI) | **45 jours** après émission | L441-10 I [F] |
| Taux des pénalités de retard | **taux BCE refi le plus récent + 10 points de pourcentage** | L441-10 II [F] |
| Plancher si taux contractuel différent | **3 × taux d'intérêt légal** | L441-10 II [F] |
| Exigibilité | **sans qu'un rappel soit nécessaire** | L441-10 II [F] |
| Indemnité forfaitaire de recouvrement | **40 €** | **art. D441-5** (LEGIARTI000043197457, en vigueur depuis le 27/02/2021) [F] |
| Indemnisation complémentaire | possible **sur justification** | L441-10 II [F] |

**Article D441-5** [F] : « **Le montant de l'indemnité forfaitaire pour frais de recouvrement prévue au II de l'article L. 441-10 est fixé à 40 euros.** »

⚠️ **Note de veille** : la version lue de L441-10 porte « en vigueur du 26 avril 2019 **au 1er janvier 2027** ». **Une modification est programmée au 1er janvier 2027** — à revérifier avant toute mise à jour des CGV fin 2026. [F]

⚠️ **Piège fréquent** [H] : un SaaS en **prélèvement d'avance** n'est pas concerné par les délais maximaux, **mais doit tout de même** faire figurer dans ses CGV les conditions d'application, le taux des pénalités de retard et le montant de l'indemnité forfaitaire — le II renvoie aux « conditions de règlement mentionnées au I de l'article L441-1 », qui sont une **mention obligatoire** des CGV.

### 8.3 Reconduction tacite — L215-1 ne s'applique PAS en B2B

**Article L215-1 C. conso.** (en vigueur depuis le 18 août 2022) [F] : information écrite du consommateur, **au plus tôt trois mois et au plus tard un mois avant le terme** de la période autorisant le rejet de la reconduction, avec **la date limite de non-reconduction dans un encadré apparent** ; à défaut, « **le consommateur peut mettre gratuitement un terme au contrat, à tout moment à compter de la date de reconduction** », et les avances postérieures sont **remboursées dans un délai de trente jours**.

**Article L215-3** [F] : « **Les dispositions du présent chapitre sont également applicables aux contrats conclus entre des professionnels et des non-professionnels.** »

> **Réponse : non.** Le champ du chapitre est double — **consommateurs** et **non-professionnels** (personne morale n'agissant pas à des fins professionnelles : syndicat de copropriété, association, CE). **Un salon de coiffure qui souscrit un outil de prise de rendez-vous agit à des fins professionnelles** : il est un **professionnel**, ni consommateur ni non-professionnel. **Le chapitre lui est inapplicable.** [H, adossé à L215-3]
>
> **Mais l'absence d'obligation légale n'est pas une immunité — voir §8.4.**

### 8.4 Déséquilibre significatif — art. L442-1 C. com.

https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000054716237 — **version en vigueur depuis le 20 août 2026** — 13/09/2026 [F]
(⚠️ Version très récente : **toute analyse antérieure à août 2026 est à revérifier.**)
> « I. - Engage la responsabilité de son auteur et l'oblige à réparer le préjudice causé le fait […] par toute personne exerçant des activités de production, de distribution ou de services : 1° D'obtenir ou de tenter d'obtenir de l'autre partie **un avantage ne correspondant à aucune contrepartie ou manifestement disproportionné** […] ; **2° De soumettre ou de tenter de soumettre l'autre partie à des obligations créant un déséquilibre significatif dans les droits et obligations des parties** ; 3° […] pénalités logistiques […] ; 4° De pratiquer […] des prix, des délais de paiement, des conditions de vente ou des modalités de vente ou d'achat **discriminatoires et non justifiés par des contreparties réelles** […] ; 5° De ne pas avoir mené de bonne foi les négociations commerciales […] ; 6° […] mises en concurrence ou appels d'offres répétés […] »

> **Réponse : OUI, une clause de durée ou de reconduction peut être sanctionnée en B2B.** [H, adossé au 2°]
> Deux éléments constituent le grief du 2° : la **soumission** (ou tentative) et le **déséquilibre significatif**. Le premier se déduit de **l'absence de négociation réelle** — soit exactement la situation d'un **contrat d'adhésion SaaS imposé à un salon indépendant**.

**Clauses à risque dans un SaaS vendu à des TPE** [H] :
- engagement initial long (24/36 mois) **sans faculté de sortie**, alors que l'éditeur peut résilier librement ou modifier unilatéralement le service ;
- reconduction tacite **sans information préalable** et préavis de résiliation long ;
- **asymétrie des préavis** entre les parties — **le marqueur le plus classiquement retenu** ;
- révision unilatérale du prix **sans droit de résiliation corrélatif** ;
- plafond de responsabilité de l'éditeur dérisoire **combiné** à des pénalités lourdes à la charge du client.

> **Le remède est simple et peu coûteux : la symétrie contractuelle.** Mêmes préavis des deux côtés ; **information de reconduction envoyée volontairement en s'alignant sur la fenêtre 3 mois / 1 mois de L215-1** (qui devient un standard de bonne pratique, non une obligation) ; droit de résiliation ouvert au client en cas de modification unilatérale du prix ou du service. [H]

### 8.5 Droit de rétractation — art. L221-3 C. conso.

https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000032226882 — 13/09/2026 [F] :
> « **Les dispositions des sections 2, 3, 6 du présent chapitre applicables aux relations entre consommateurs et professionnels, sont étendues aux contrats conclus HORS ÉTABLISSEMENT entre deux professionnels dès lors que l'objet de ces contrats n'entre pas dans le champ de l'activité principale du professionnel sollicité et que le nombre de salariés employés par celui-ci est inférieur ou égal à cinq.** »

**Trois conditions cumulatives — et la première est presque toujours oubliée** [F] :
1. ⚠️ **Contrat conclu HORS ÉTABLISSEMENT.** Le texte ne vise **que** les contrats hors établissement, **pas** les contrats à distance. **Un SaaS vendu par téléphone, par e-mail ou en ligne est un contrat À DISTANCE : L221-3 ne s'applique pas, quel que soit l'effectif.** C'est la condition qui écarte, en pratique, la majorité des ventes SaaS.
2. L'objet **n'entre pas dans le champ de l'activité principale** du professionnel sollicité.
3. Effectif **≤ 5 salariés**.

**Le salon est-il DANS ou HORS du champ ?** **Très probablement hors du champ — mais pas pour la raison qu'on croit.** [H]
- **Contrat à distance** (cas normal : appel sortant, démo visio, signature électronique) → **L221-3 ne s'applique pas du tout**, la condition n° 1 n'étant pas remplie. **Pas de 14 jours.**
- **Contrat hors établissement** (commercial qui se déplace au salon, signature sur place) → il faut trancher la condition n° 2, **réellement incertaine** :
  - *« hors du champ »* (→ 14 jours dus) : l'activité principale d'un salon est la coiffure, pas l'informatique ni la téléphonie ; un logiciel de prise de RDV est un outil de gestion, étranger au métier.
  - *« dans le champ »* (→ pas de rétractation) : la jurisprudence apprécie le **rapport direct** avec l'activité ; or **prendre des rendez-vous est le cœur opérationnel d'un salon**, et répondre au téléphone fait partie de l'exploitation quotidienne.
  - **Je ne peux pas trancher avec une source primaire : aucune décision consultable (Judilibre inaccessible). [NV]**

> **Recommandation** [H] : **accorder contractuellement 14 jours de rétractation à tout client professionnel de 5 salariés ou moins, quel que soit le mode de conclusion.** Le coût est faible (une TPE qui se rétracte n'aurait pas été un bon client), et cela supprime trois risques d'un coup : requalification sous L221-3 ; argument du déséquilibre significatif (L442-1 I 2°) ; et le risque de **L121-4, 10°** (« présenter les droits conférés au consommateur par la loi comme constituant une caractéristique propre à la proposition faite par le professionnel »).

### 8.6 ⚠️ Mentions légales : article 1-1 de la LCEN, et non plus article 6 III

**Correction.** Les mentions d'identification des éditeurs de services de communication au public en ligne figurent désormais à l'**article 1-1 de la LCEN** (LEGIARTI000049568614), **inséré par la LOI n° 2024-449 du 21 mai 2024 (loi SREN), article 48**. L'article 6 existe toujours mais **son III porte sur d'autres obligations** (FAI, moyens techniques de filtrage). [F]
https://www.legifrance.gouv.fr/loda/id/JORFTEXT000000801164 — 13/09/2026

**Article 1-1, I — la liste** [F] : pour une **personne morale** : **dénomination ou raison sociale**, **siège social**, **numéro de téléphone**, **numéro d'inscription au RCS ou au RNE**, **capital social**, **adresse du siège social** ; **nom du directeur ou codirecteur de la publication** (art. 93-2 de la loi n° 82-652 du 29 juillet 1982) et, le cas échéant, du responsable de la rédaction ; **nom, dénomination, adresse et numéro de téléphone du fournisseur d'hébergement** ; le cas échéant, identité et adresse des personnes assurant **le stockage de données**. Le tout **« dans un standard ouvert »**.
(Les III à V organisent le **droit de réponse** en ligne : demande dans les 3 mois, insertion dans les 3 jours, **amende de 3 750 €** en cas de refus.) [F]

**Sanction** : fiche officielle « Mentions obligatoires sur un site internet » (https://entreprendre.service-public.gouv.fr/vosdroits/F31228 — 13/09/2026) : maximum **1 an d'emprisonnement et 75 000 € d'amende**, et obligation, **depuis le 1er juin 2023**, d'une **fonctionnalité de résiliation en ligne**. [F]
(⚠️ `service-public.gouv.fr/professionnels-entreprises/vosdroits/F31228` redirige en 301 vers `entreprendre.service-public.gouv.fr/vosdroits/F31228`.)

### 8.7 Checklist CGV [H, chaque ligne adossée à un texte vérifié]

| # | Mention | Fondement |
|---|---|---|
| 1 | Conditions de règlement | L441-1 I [F] |
| 2 | Barème des prix unitaires, réductions de prix | L441-1 I [F] |
| 3 | **Méthode de calcul du prix** si facturation à l'usage | L441-1 III [F] |
| 4 | Délai de paiement ≤ 60 j (ou 45 j fin de mois, **expressément stipulé**) | L441-10 I [F] |
| 5 | Taux des pénalités de retard = BCE refi + 10 pts (≥ 3 × taux légal) | L441-10 II [F] |
| 6 | Indemnité forfaitaire de recouvrement **40 €** + complémentaire sur justificatif | D441-5 / L441-10 II [F] |
| 7 | Exigibilité des pénalités **sans rappel** | L441-10 II [F] |
| 8 | Durée, reconduction, **préavis symétriques** | L442-1 I 2° [F] |
| 9 | 14 jours de rétractation offerts aux pros ≤ 5 salariés | L221-3 [F] + prudence [H] |
| 10 | Mentions légales complètes du site | LCEN art. 1-1 [F] |
| 11 | Fonctionnalité de résiliation en ligne | fiche Service-Public [F] |
| 12 | Mandat d'usage de numéro, annexé et révocable | CPCE L44 IV [F] |
| 13 | Répartition de responsabilité sur les propos de l'agent + obligation de confirmation écrite | C. civ. 1114 / C. conso. L121-2 [F] |
| 14 | Qualification verrouillée arrhes/acompte, paramètre commerçant | C. conso. L214-1 [F] |
| 15 | Traitement des appels d'urgence : exclusion explicite + acheminement garanti | CPCE L33-1 I f) / D98-8 [F] |
| 16 | Répartition **fournisseur / déployeur** au sens de l'AI Act + **interdiction du rebranding** | AI Act art. 3 et 25 [F] / [NV] sur le détail de l'art. 25 |
| 17 | DPA art. 28 en annexe, avec liste des sous-traitants ultérieurs et préavis d'objection | RGPD art. 28.3, 28.2 [F] |
| 18 | Clause de réutilisation **séparée, opt-in, par finalité nommée** | CNIL, fiche réutilisation [F] |

---

## 9. Le calendrier : obligatoire aujourd'hui / obligatoire à une date future / bonne pratique

### 9.1 Obligatoire AUJOURD'HUI (14 septembre 2026)

| Obligation | Depuis | Fondement |
|---|---|---|
| **Annonce « vous parlez à un système d'IA »**, claire, reconnaissable, au plus tard à la première interaction, sur **tous** les appels | **2 août 2026** | AI Act art. 50 §1 et §5 [F] |
| **Identification du commerçant pour le compte duquel l'agent parle** | en vigueur | C. conso. L121-2, 3° ; CPCE L34-5 [F] |
| **Consentement préalable** (opt-in R223-1) pour toute prospection téléphonique de consommateurs, **relance de clients dormants incluse** | **11 août 2026** | C. conso. L223-1, R223-1 [F] |
| **Capacité d'enregistrer un retrait de consentement exprimé ORALEMENT** pendant l'appel | **11 août 2026** | C. conso. R223-3 [F] |
| **Créneaux** lun-ven hors fériés, 10h-13h / 14h-20h (fuseau du consommateur) + **max 4 sollicitations ou tentatives / 30 j** | **11 août 2026** | C. conso. D223-9 [F] |
| **Preuve du consentement archivée 3 ans**, consentement valable ≤ 1 an sans reconduction tacite | **11 août 2026** | C. conso. R223-1 3°, R223-2 [F] |
| **Mention L223-2 sur tout formulaire de collecte de numéro** + clause dans le contrat | **11 août 2026** | C. conso. L223-2 [F] |
| **Pas d'enregistrement audio permanent ou systématique** ; enregistrement ponctuel / déclenché seulement | doctrine en vigueur | CNIL, fiches écoute et preuve [F] |
| **Information de l'appelant en deux temps** + droit d'opposition annoncé **séparément** et exerçable jusqu'à la fin de l'appel | en vigueur | RGPD art. 13, 21.4, 21.5 [F] |
| **Contrat art. 28 écrit** avec chaque commerçant (chapeau + a→h + alerte + sous-traitants ultérieurs) | en vigueur | RGPD art. 28.3, 28.9 [F] |
| **Registre art. 30.2** nommant chaque commerçant (exemption < 250 salariés inapplicable) | en vigueur | RGPD art. 30.2, 30.5 [F] |
| **AIPD** (portée par le commerçant, assistée par l'éditeur) | avant le traitement | RGPD art. 35, 28.3 f) ; délib. CNIL 2018-327 [F] |
| **Base de transfert** pour STT/LLM US : DPF vérifié nominativement, **ou** CCT 2021/914 **module 3** + **AITD** | en vigueur | RGPD ch. V ; déc. 2023/1795 ; déc. 2021/914 ; guide AITD CNIL 09/07/2025 [F] |
| **Information individuelle préalable des salariés** du commerçant (kit à fournir) | en vigueur | C. trav. L1222-4, L1121-1 [F] |
| **Information/consultation du CSE** pour les clients de 50+ salariés | en vigueur | C. trav. L2312-38, L2312-8 II 4° [F] |
| **Acheminement gratuit des appels d'urgence** + localisation | en vigueur | CPCE L33-1 I f), D98-8 [F] |
| **Accord préalable et traçable de l'affectataire** pour toute CLI présentée | **25 juillet 2023** | CPCE L44 IV ; déc. Arcep 2025-2215 [F] |
| **Identifiant CE** dès mise à disposition de numéros | en vigueur | Arcep, page identifiant CE [F] |
| **Mentions légales** LCEN art. 1-1 + **fonctionnalité de résiliation en ligne** (depuis le 1er juin 2023) | en vigueur | LCEN art. 1-1 ; fiche Service-Public [F] |
| **CGV** : conditions de règlement, barème, méthode de calcul si usage, délais, pénalités, 40 € | en vigueur | C. com. L441-1, L441-10, D441-5 [F] |
| **Qualification de la somme (arrhes/acompte) annoncée** au client | en vigueur | C. conso. L111-1 5°, L214-1 [F] |

### 9.2 Obligatoire à une DATE FUTURE

| Échéance | Obligation | Fondement |
|---|---|---|
| **2 décembre 2026** | **Marquage machine-readable des sorties audio générées** — pour les systèmes **mis sur le marché avant le 2 août 2026**. **Immédiat** pour ceux mis sur le marché après. | AI Act art. 50 §2 + art. 111 §4 inséré par le règl. (UE) 2026/1744 [F] |
| **2 décembre 2026** | **Nouvelles pratiques interdites** art. 5 §1 b bis) / b ter) et §§1 bis / 1 ter, sanctionnées **35 M€ / 7 %**. **Contenu non dépouillé — [NV], priorité 1** | AI Act modifié par le règl. 2026/1744, art. 113 a) [F] |
| **9 décembre 2026** | **Directive (UE) 2024/2853** : transposition, et application aux produits **mis sur le marché ou mis en service après** cette date. Le **SaaS est un « produit »** → responsabilité sans faute du fait du défaut (dommages corporels/matériels/données). | Dir. 2024/2853 art. 2 §1, 4 pt 1, 22 §1 [F] |
| **1er janvier 2027** | **Modification programmée de C. com. L441-10** (délais de paiement) — à revérifier avant toute mise à jour des CGV fin 2026 | mention ChronoLégi sur L441-10 [F] |
| **2 août 2027 / 2 décembre 2027 / 2 août 2028** | Régime **haut risque** (ch. III sect. 1-3) — **sans objet pour ce produit sauf requalification**, mais à surveiller | AI Act art. 113 modifié [F] |
| **Indéterminée** | **Pourvoi C-703/25 P** (Latombe) pendant devant la CJUE : si le DPF tombe, **tous les transferts basculent sur l'art. 46** → CCT module 3 + AITD obligatoires pour tous, **sans période de grâce** (précédent Schrems II) | CELEX 62025CN0703 [F] + [H] |

### 9.3 BONNE PRATIQUE (non obligatoire, mais recommandé)

| Mesure | Pourquoi |
|---|---|
| **AIPD « produit »** livrée pré-remplie à chaque commerçant | La CNIL la qualifie expressément de **bonne pratique** ; en pratique, obligation d'assistance (art. 28.3 f)) **et** argument de vente [F] |
| **Signer les CCT 2021/914 module 3 même si le fournisseur est certifié DPF** (dormantes) | Filet de sécurité face au pourvoi C-703/25 P [H] |
| **Option d'hébergement européen** du STT et du LLM | CNIL : « privilégier le recours à des systèmes **locaux, sécurisés et spécialisés** » [F] |
| **Cantonner l'agent aux éléments non essentiels** (jamais de prix chiffré seul, renvoi à confirmation écrite) | Transforme l'offre (art. 1114) en **invitation à entrer en négociation** — la digue la plus efficace [H] |
| **Anonymisation des données réutilisées pour entraînement** | La CNIL cite l'anonymisation comme la garantie qui fait passer le test de compatibilité de l'art. 6.4 [F] |
| **Symétrie contractuelle** des préavis + information volontaire de reconduction (fenêtre 3 mois / 1 mois de L215-1) | Neutralise l'argument du déséquilibre significatif en B2B (L442-1 I 2°) [H] |
| **14 jours de rétractation offerts** aux pros ≤ 5 salariés, quel que soit le mode de conclusion | Supprime trois risques : requalification L221-3, déséquilibre significatif, L121-4 10° [H] |
| **Appliquer les créneaux D223-9 par défaut même aux appels sortants de service** | Le coût est nul, la zone grise « prospection ou pas » disparaît [H] |
| **Journalisation de chaque opposition et de chaque retrait**, avec effet vérifiable (suppression de l'audio déjà capté) | Accountability (art. 5.2) ; une opposition sans effet est cosmétique [H] |
| **Proscrire par conception toute fonction de reconnaissance du locuteur** | Éviterait la bascule en art. 9 RGPD (biométrie), consentement explicite, AIPD de plein droit [H] |
| **Proscrire toute liste noire mutualisée entre commerçants** | Type n° 9 de la délibération CNIL 2018-327 (« traitements mutualisés de manquements contractuels ») [F] |

---

## 10. 🔴 LES LIVRABLES À PRODUIRE

Chaque ligne : ce qu'il faut produire, et **l'obligation qui le fonde**.

### 10.1 Documents juridiques (13)

| # | Livrable | Obligation qui le fonde |
|---|---|---|
| **D1** | **DPA / contrat de sous-traitance art. 28**, annexé aux CGV : chapeau (objet, durée, nature, finalité, types de données, catégories de personnes, droits du RT) + obligations a) à h) + **clause d'alerte sur instruction illicite** + sort des données en fin de contrat (choix suppression/restitution, format, délai) | **RGPD art. 28.3 et 28.9** [F] |
| **D2** | **Liste nominative des sous-traitants ultérieurs** (STT, LLM, hébergeur, opérateur télécom, SMS) avec, **pour chacun : localisation, ce qu'il fait, preuve des garanties**, + **préavis d'objection chiffré** | **RGPD art. 28.2 et 28.4 ; EDPB 07/2020 §152** [F] |
| **D3** | **CCT de transfert, décision (UE) 2021/914, MODULE 3** (ST → ST ultérieur) signées avec chaque fournisseur US — **même si DPF**, en dormance | **RGPD art. 46.2 c)** ; déc. 2021/914 [F] ; pourvoi C-703/25 P [H] |
| **D4** | **AITD (analyse d'impact des transferts)** suivant les 6 étapes CEPD 01/2020 et le guide CNIL du 09/07/2025 — **obligatoire pour tout fournisseur non certifié DPF** | **Rec. CEPD 01/2020 ; guide AITD CNIL** [F] |
| **D5** | **Vérification nominative de la certification DPF** de chaque fournisseur STT et LLM sur la liste CPD du ministère américain du Commerce, **catégorie de données incluse**, avec date et capture | **RGPD art. 45 ; déc. (UE) 2023/1795** [F] |
| **D6** | **Registre des traitements art. 30.2**, **généré depuis la base clients** (nomme chaque commerçant), pas un tableur figé | **RGPD art. 30.2 ; art. 30.5 inapplicable** [F] |
| **D7** | **AIPD « produit »** (logiciel PIA de la CNIL), livrée pré-remplie à chaque commerçant. **Doit documenter explicitement la distinction traitement audio TRANSITOIRE / CONSERVATION d'un fichier audio** — c'est la ligne de défense centrale | **RGPD art. 35 ; art. 28.3 f) ; délib. CNIL 2018-327 ; bonne pratique CNIL** [F] |
| **D8** | **Dossier technique de marquage** des sorties audio : options évaluées (watermarking audio, C2PA, marqueurs SIP, journalisation d'origine), choix retenu, justification des rejets au regard de « l'état de la technique généralement reconnu », **date de réévaluation** | **AI Act art. 50 §2 + considérant 133 ; facteur atténuant art. 99 §7** [F] |
| **D9** | **Mandat d'usage de numéro**, distinct des CGV : objet, numéros visés, durée, **révocabilité**, **transmission à l'opérateur** pour alimenter la « liste des numéros présentables » | **CPCE L44 IV ; décision Arcep n° 2025-2215** [F] |
| **D10** | **Dossier KYC par commerçant** : identité, **justificatif d'établissement dans la zone géographique du numéro**, domiciliation bancaire, **adresse d'urgence à jour par numéro** | **Règles d'affectation du plan de numérotation (Arcep)** [F] ; **OVHcloud §3.2, Telnyx §12.1** [F2] |
| **D11** | **Autorisation écrite de revente** obtenue d'OVH si le transport passe par SIP Trunk — **ou** bascule sur Telnyx. **L'offre de téléphonie de détail OVHcloud est incompatible avec le produit** | **OVH SIP Trunk art. 3 ; OVHcloud CP Téléphonie §3.4 e) f) g) h)** [F2] |
| **D12** | **CGV SaaS B2B** conformes à la checklist §8.7 (18 points), avec **préavis symétriques** et **14 jours de rétractation offerts** aux pros ≤ 5 salariés | **C. com. L441-1, L441-10, D441-5, L442-1 I 2° ; C. conso. L221-3** [F] |
| **D13** | **Mentions légales du site** : dénomination, siège, téléphone, RCS/RNE, capital social, directeur de la publication, hébergeur (nom/adresse/téléphone), prestataire de stockage — **dans un standard ouvert** — **+ fonctionnalité de résiliation en ligne** | **LCEN art. 1-1 (loi SREN 2024-449 art. 48)** ; fiche Service-Public [F] |

### 10.2 Mentions et scripts (7)

| # | Livrable | Obligation qui le fonde |
|---|---|---|
| **M1** | **Annonce d'ouverture d'appel, verrouillée et non désactivable**, portant dans la même phrase : (a) **« assistant de [raison sociale du commerçant] »**, (b) **« traité par un système automatisé »**, (c) le cas échéant **« et est enregistré afin de … »**, (d) **le droit d'opposition, énoncé séparément**, (e) le renvoi vers l'information complète (URL + touche DTMF) | (a) **RGPD art. 13.1 a) + C. conso. L121-2, 3° + CPCE L34-5** ; (b) **AI Act art. 50 §1 et §5** ; (c) **RGPD art. 13.1 c)** ; (d) **RGPD art. 21.4** ; (e) **RGPD art. 13** [F] |
| **M2** | **Politique de confidentialité appelant** (temps 2), couvrant **intégralement** 13.1 a)→f) et 13.2 a)→f), **avec mention expresse des transferts hors UE et de leur fondement** | **RGPD art. 13.1 f), 13.2** [F] |
| **M3** | **Note d'information individuelle aux salariés** du commerçant, modèle fourni, mentionnant les **périodes** d'écoute possible | **C. trav. L1222-4, L1121-1 ; CNIL contrôle de l'activité** [F] |
| **M4** | **Note d'information / consultation CSE**, modèle fourni, pour les clients de **50+ salariés** (chaînes, franchises) | **C. trav. L2312-38 al. 3 ; L2312-8 II 4°** [F] |
| **M5** | **Mention sur tout formulaire de collecte de numéro** (prise de RDV en ligne comprise) : la sollicitation commerciale suppose le consentement préalable ; **+ clause obligatoire dans le contrat** si un contrat est conclu | **C. conso. L223-2** [F] |
| **M6** | **Script de recueil du consentement** au démarchage, portant les **5 mentions de R223-1 I** (identité + nature des biens/services ; proposition ; **période ≤ 1 an** ; droit de retrait et ses modalités ; accès au support durable de preuve) | **C. conso. R223-1 I** [F] |
| **M7** | **Confirmation écrite systématique** (SMS/e-mail) de chaque rendez-vous : prestation, date, prix, **et nature exacte de la somme** — reprise **à l'identique** de la qualification annoncée à l'oral | **C. civ. 1114, 1119, 1188 ; C. conso. L111-1 5°, L214-1** [F] |

### 10.3 Réglages et contraintes produit (16)

| # | Réglage / contrainte | Obligation qui le fonde |
|---|---|---|
| **P1** | **`annonce_ia: true`, non désactivable par le commerçant**, sur appels entrants **et** sortants | **AI Act art. 50 §1 (obligation de CONCEPTION, non transférable par contrat)** [F] |
| **P2** | **Enregistrement audio DÉSACTIVÉ par défaut** ; jamais continu ; **déclenché** sur événement métier identifié ou échantillonnage ponctuel documenté | **CNIL : « ni permanent ni systématique », « ne peut être déclenché par défaut, de manière automatisée, pour tous les appels »** [F] |
| **P3** | **Interruption de l'enregistrement en cours d'appel** : sur opposition, et **sur détection de données bancaires** | **CNIL, fiche preuve de la formation d'un contrat** [F] |
| **P4** | **Touche DTMF d'opposition active pendant tout l'appel** + **détection vocale d'intention** (« arrêtez l'enregistrement ») | **RGPD art. 21.1 (« à tout moment »), 21.5 (procédés automatisés)** [F] |
| **P5** | **Effet réel de l'opposition** : suppression de l'audio **déjà capté sur cet appel**, pas seulement arrêt prospectif ; **voie de repli non dégradée** (transfert humain ou rappel) | **RGPD art. 21.1** ; [H] — une opposition sans effet est cosmétique |
| **P6** | **Politique de rétention implémentée techniquement** : audio « à bref délai » (plafond **6 mois**) · documents d'analyse **1 an** · probatoire **5 ans** en archivage intermédiaire · données métier = durée du fichier client · **zéro rétention côté fournisseur US, exigée contractuellement** | **Référentiel CNIL du 02/04/2026 (durées RH) ; C. civ. art. 2224** [F] |
| **P7** | **Expurgation à la transcription** des données bancaires, de santé et des propos hors objet | **RGPD art. 5.1 c) minimisation ; CNIL, fiche Chatbots** [F] |
| **P8** | **Compréhension et propagation immédiate d'un retrait de consentement exprimé ORALEMENT** pendant un appel sortant | **C. conso. R223-3 (« Ce retrait peut être exprimé oralement »)** [F] |
| **P9** | **Plages horaires en dur** pour tout appel sortant de prospection : lun-ven hors fériés, 10h-13h / 14h-20h, **fuseau du consommateur** | **C. conso. D223-9** [F] |
| **P10** | **Compteur de fréquence** : max **4 sollicitations ou tentatives** par consommateur et par professionnel sur **30 jours calendaires** — **les appels non décrochés comptent** | **C. conso. D223-9** [F] |
| **P11** | **Purge des consentements à 12 mois glissants**, **sans reconduction tacite** ; preuve conservée **3 ans** et restituable **gratuitement sur support durable** (interface dédiée, **sans création de compte client**) | **C. conso. R223-1 I 3°, R223-2** [F] |
| **P12** | **Qualification arrhes/acompte VERROUILLÉE au niveau du commerçant** (un réglage, pas une formulation libre du modèle). **Interdire au modèle de générer librement « arrhes », « acompte », « caution », « dépôt », « réservation payante »** | **C. conso. L214-1 (« sauf stipulation contraire » — le mot prononcé EST la stipulation)** [F] |
| **P13** | **Interdiction par conception** d'annoncer disponibilité, promotion ou urgence **non vérifiée contre le système de réservation** | **C. conso. L121-4, 5° et 7° (pratiques réputées trompeuses, sans élément intentionnel à démontrer)** [F] |
| **P14** | **Cantonnement de l'agent aux éléments non essentiels** : ne jamais chiffrer un prix sans renvoi à une confirmation écrite, afin de rester dans « l'invitation à entrer en négociation » | **C. civ. art. 1114, seconde phrase** [F] |
| **P15** | **Traitement explicite des appels d'urgence** : l'acheminement du 15/17/18/112 doit rester possible et **gratuit**, avec remontée de localisation ; **l'agent ne doit jamais se mettre en travers du 112** | **CPCE L33-1 I f) ; D98-8** [F] |
| **P16** | **Interdictions d'architecture** : pas de reconnaissance du locuteur / voiceprint · pas de liste noire mutualisée entre commerçants · pas de couplage enregistrement + captures d'écran des salariés · **ligne non enregistrée ou dispositif de coupure pour les appels personnels des salariés** | **RGPD art. 9.1 + 4(14)** ; **délib. CNIL 2018-327 type n° 9** ; **CNIL, fiche écoute au travail** [F] |

### 10.4 Décisions et arbitrages à prendre (5)

| # | Décision | Enjeu |
|---|---|---|
| **A1** | **Statut télécom : opérateur ou mandataire technique ?** Si l'éditeur achète les numéros et les affecte, il est **opérateur** (L32 15°) et porte urgences, annuaire, MAN. La contre-lecture (contrat téléphonie **directement** commerçant ↔ opérateur, éditeur simple mandataire non affectataire, ne facturant pas la communication) évite le statut — **mais c'est un arbitrage de modèle économique**, à trancher avant de construire le provisionnement | §5.2 [H] |
| **A2** | **Offre marque blanche / éditeur hôte** : le rebranding par l'éditeur hôte le fait **basculer en fournisseur au sens de l'AI Act art. 25**, et peut créer une **responsabilité conjointe RGPD** (EDPB 07/2020 §65). **Le texte de l'art. 25 n'a pas été vérifié — [NV], priorité 1** avant toute offre white-label | §1.3, §2.1 |
| **A3** | **Relance / réactivation de clients dormants** : c'est **de la prospection commerciale**, donc opt-in R223-1 complet. Décider si la fonctionnalité est livrée, et à quel prix de conformité. **Premier point à soumettre à un avocat** | §4.4 [H] |
| **A4** | **Fournisseur télécom** : OVHcloud téléphonie de détail est **contractuellement incompatible** ; SIP Trunk exige une **autorisation écrite de revente** ; Telnyx est structurellement plus adapté mais impose CLI exacte, responsabilité pleine et adresse d'urgence par numéro | §5.6 [F2] |
| **A5** | **Réutilisation des données pour entraînement** : la rendre **opt-in par finalité nommée, désactivée par défaut, avec anonymisation**. Une clause générale de CGU est **illicite** | §2.1 [F] |

### 10.5 Les huit points à faire trancher par un avocat, par ordre d'urgence

1. **CPCE L34-5** — un agent vocal IA est-il un « système automatisé d'appels » au sens du L32, 32° ? Champ **plus large que L223-1** (toute personne physique, pas seulement les consommateurs) → **touche la prospection B2B de l'éditeur lui-même**. Aucune position officielle trouvée [NV]. §4.6
2. **AI Act art. 25** — bascule déployeur → fournisseur en marque blanche. Texte non extrait [NV]. §1.3
3. **AI Act art. 5 §1 b bis) / b ter)** — nouvelles pratiques interdites applicables au **2 décembre 2026**, sanction **35 M€ / 7 %** : vérifier qu'aucune ne vise l'usurpation de voix humaine ou la manipulation par agent conversationnel [NV]. §1.8
4. **Relance de clients dormants** — prospection ou exécution d'un contrat en cours ? §4.4
5. **Statut opérateur** — qualification et montage contractuel avec l'opérateur. §5.2
6. **L221-3** — « champ de l'activité principale » pour un salon achetant un outil de prise de RDV : aucune décision consultable [NV]. §8.5
7. **Autorité française de surveillance de l'AI Act** — aucun texte français trouvé sur Légifrance [NV] ; l'hypothèse DGCCRF n'est pas vérifiée. §1.7
8. **Art. 22 RGPD** — le seuil à partir duquel une décision de l'agent (refus, blacklist, tarification différenciée) devient une « décision automatisée produisant des effets juridiques ou l'affectant de manière significative ». §2.1

---

## 11. Récapitulatif des [NV] — ce qui n'a pas pu être vérifié

| # | Point | Recherche tentée et échec |
|---|---|---|
| 1 | **Autorité française de surveillance de marché de l'AI Act** | 4 recherches Légifrance distinctes, toutes négatives ; `economie.gouv.fr` 403 puis 404 ; `digital-strategy.ec.europa.eu` échec réseau. **Hypothèse DGCCRF non vérifiée.** |
| 2 | **AI Act art. 25** (bascule déployeur → fournisseur) | Texte non extrait |
| 3 | **AI Act art. 3, 39)** (définition « système de reconnaissance des émotions ») | Texte non extrait |
| 4 | **AI Act art. 5 §1 b bis) / b ter) et §§1 bis / 1 ter** nouveaux (2 déc. 2026, 35 M€ / 7 %) | Non dépouillés |
| 5 | **Définition « PME »** retenue par le règlement IA pour l'art. 99 §6 | Non vérifiée |
| 6 | **Code de bonne pratique adopté sous l'art. 50 §7** | Recherche impossible sans WebSearch |
| 7 | **Directive (UE) 2019/882** (accessibilité), renvoi implicite de l'art. 50 §5 | Non vérifiée |
| 8 | **Nouvelles CCT adoptées en 2025/2026** | Recherche plein texte EUR-Lex sans résultat exploitable hors navigateur. **2021/914 et 2021/915 sont en vigueur et non modifiées au fond — c'est tout ce qui peut être affirmé.** |
| 9 | **Lignes directrices CEPD du 7 juillet 2026** (anonymisation, moissonnage en IA générative) | Non lues — directement pertinentes pour la clause de réutilisation |
| 10 | **Note exploratoire CNIL / Conseil de l'IA et du Numérique sur l'IA agentique, 20 juillet 2026** | Non lue |
| 11 | **Référentiels CNIL « gestion des activités commerciales » et « gestion des impayés »** | Pages non ouvertes, numéros de délibération non relevés |
| 12 | **Sanction CNIL de 250 000 € contre un centre d'appels (16/10/2025)** | Aucune page correspondante sur cnil.fr ; source secondaire confondant CNIL et CNPD. **Information non reprise.** |
| 13 | **Décisions françaises / CJUE sur l'engagement par un système automatisé** | Judilibre rendu en JS, contenu vide sur deux requêtes. **Échec d'accès, pas preuve d'absence.** |
| 14 | **Moffatt v. Air Canada, 2024 BCCRT 149** | CanLII et CRT en 403. Référence non vérifiée à la source. **Aucune valeur en droit français en tout état de cause.** |
| 15 | **Fiche DGCCRF arrhes/acompte** | `economie.gouv.fr` 403 sur toutes les URL |
| 16 | **Définitions autonomes « exploitant de réseau » / « fournisseur de service »** dans L32 | Extraction partielle des ~30 alinéas définitionnels |
| 17 | **Date du « 1er octobre 2024 » pour le MAN** | Aucune source primaire ne la confirme. Seule date attestée : **25 juillet 2023**. **Ne pas l'écrire dans un document contractuel.** |
| 18 | **Exigences KYC Telnyx spécifiques à la France** | Servies par API (`GET /requirements`), non publiées en clair |
| 19 | **Jurisprudence sur « champ de l'activité principale » (L221-3)** appliqué à un logiciel de gestion acheté par un salon | Judilibre inaccessible |
| 20 | **C. conso. L242-16-1** (sanction du L223-8) et **article liminaire** (définition du « consommateur ») | Non extraits |
| 21 | **Version de C. com. L441-10 applicable après le 1er janvier 2027** | Modification programmée, texte futur non consulté |
| 22 | **Texte désignant « l'autorité administrative chargée de la concurrence et de la consommation »** | Non vérifié (hypothèse DGCCRF) |
| 23 | **LOI n° 2025-391 du 30 avril 2025 (DDADUE)** | Contenu non dépouillé |

---

## Annexe — table des sources primaires

Toutes consultées les **13 ou 14 septembre 2026**.

### Droit de l'Union — EUR-Lex
| Source | URL |
|---|---|
| **Règlement (UE) 2024/1689 (AI Act)**, texte JO FR | https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=OJ:L_202401689 |
| **Règlement (UE) 2026/1744 du 8 juillet 2026** (omnibus numérique IA), JO L 24.7.2026 | https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=CELEX:32026R1744 |
| Proposition COM(2025) 836 final | https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:52025PC0836 |
| Fiche procédure 2025/0359/COD (« Adopted act: 32026R1744 ») | https://eur-lex.europa.eu/legal-content/FR/ALL/?uri=CELEX:52025PC0836 |
| **RGPD**, règlement (UE) 2016/679, texte intégral FR | https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=CELEX:32016R0679 |
| Décision d'exécution (UE) **2021/914** — CCT transferts (texte) | https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=CELEX:32021D0914 |
| Décision (UE) 2021/914 — statut « In force », historique | https://eur-lex.europa.eu/legal-content/FR/HIS/?uri=CELEX:32021D0914 |
| Décision d'exécution (UE) **2021/915** — CCT RT↔ST (texte) | https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=CELEX:32021D0915 |
| Décision (UE) 2021/915 — statut, historique | https://eur-lex.europa.eu/legal-content/FR/HIS/?uri=CELEX:32021D0915 |
| Décision d'exécution (UE) **2023/1795** — adéquation DPF, « In force », « No end date » | https://eur-lex.europa.eu/legal-content/FR/HIS/?uri=CELEX:32023D1795 |
| **Arrêt T-553/23, Latombe / Commission, 3 septembre 2025** | https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=CELEX:62023TJ0553 |
| Ordonnance T-553/23 R, 12 octobre 2023 | https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=CELEX:62023TO0553 |
| **Pourvoi C-703/25 P** (CELEX 62025CN0703, JO C/2025/6610, 22.12.2025) | http://data.europa.eu/eli/C/2025/6610/oj |
| **Directive (UE) 2024/2853** du 23 octobre 2024 (produits défectueux) | https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=OJ:L_202402853 |
| Procédure 2022/0303(COD) (AILD) — « Proposal withdrawn », 06/10/2025 | https://eur-lex.europa.eu/procedure/FR/2022_303 |
| Retrait de propositions de la Commission, C/2025/5423, JOUE 6.10.2025 | https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=celex:52025XC05423 |

### CEPD / EDPB
| Source | URL |
|---|---|
| Lignes directrices **07/2020** — responsable / sous-traitant (FR) | https://www.edpb.europa.eu/system/files/documents/2023-10/edpb_guidelines_202007_controllerprocessor_final_fr.pdf |
| Recommandations **01/2020** — mesures supplémentaires, v2.0 (FR) | https://www.edpb.europa.eu/system/files/documents/2022-04/edpb_recommendations_202001vo.2.0_supplementarymeasurestransferstools_fr.pdf |
| Recommandations **02/2020** — garanties essentielles européennes | https://edpb.europa.eu/sites/default/files/files/file1/edpb_recommendations_202002_europeanessentialguaranteessurveillance_fr.pdf |

### CNIL
| Source | Date | URL |
|---|---|---|
| **Référentiel durées de conservation — Gestion des RH** (page) | 02/04/2026 | https://www.cnil.fr/fr/referentiel-durees-conservation-donnees-rh |
| Référentiel durées RH (**PDF**, « Publié le 2 avril 2026 — Mis à jour le 20 mai 2026 », sans n° de délibération) | 02/04/2026 | https://www.cnil.fr/sites/default/files/2026-04/referentiel_durees_de_conservation_gestion_des_ressources_humaines.pdf |
| Quelles qualifications pour les acteurs du cloud ? | 28/05/2026 | https://www.cnil.fr/fr/quelles-qualifications-pour-les-acteurs-de-linformatique-en-nuage-cloud |
| Le contrôle de l'activité des personnes employées | 09/07/2026 | https://www.cnil.fr/fr/controle-de-lactivite-des-personnes-employees |
| Sous-traitants : la réutilisation de données confiées par un RT | — | https://www.cnil.fr/fr/sous-traitants-la-reutilisation-de-donnees-confiees-par-un-responsable-de-traitement |
| L'écoute et l'enregistrement des appels sur le lieu de travail | — | https://www.cnil.fr/fr/lecoute-et-lenregistrement-des-appels-sur-le-lieu-de-travail |
| L'enregistrement des conversations téléphoniques afin d'établir la preuve de la formation d'un contrat | — | https://www.cnil.fr/fr/lenregistrement-des-conversations-telephoniques-afin-detablir-la-preuve-de-la-formation-dun-contrat |
| AIPD : publication de la liste (délib. **2018-326** et **2018-327** du 11/10/2018) | — | https://www.cnil.fr/fr/analyse-dimpact-relative-la-protection-des-donnees-publication-dune-liste-des-traitements-pour |
| Liste des 14 types nécessitant une AIPD (PDF, délib. 2018-327) | 11/10/2018 | https://www.cnil.fr/sites/default/files/atoms/files/liste-traitements-aipd-requise.pdf |
| Ce qu'il faut savoir sur l'AIPD (9 critères, seuil de 2) | — | https://www.cnil.fr/fr/ce-quil-faut-savoir-sur-lanalyse-dimpact-relative-la-protection-des-donnees-aipd |
| Clauses contractuelles types RT ↔ ST (« ne peuvent servir aux fins du chapitre V ») | 30/06/2021 | https://www.cnil.fr/fr/clauses-contractuelles-types-entre-responsable-de-traitement-et-sous-traitant |
| Sous-traitance : exemple de clauses | — | https://www.cnil.fr/fr/sous-traitance-exemple-de-clauses |
| Guide du sous-traitant (PDF) | — | https://www.cnil.fr/sites/default/files/atoms/files/rgpd-guide_sous-traitant-cnil.pdf |
| Guide AITD — version finale (page) | 09/07/2025 | https://www.cnil.fr/fr/analyse-dimpact-des-transferts-des-donnees-la-cnil-publie-la-version-finale-de-son-guide-aitd |
| Guide AITD (PDF) | — | https://www.cnil.fr/sites/cnil/files/2025-02/guide_aitd_pdf.pdf |
| IA et RGPD : nouvelles recommandations | 07/02/2025 | https://www.cnil.fr/fr/ia-et-rgpd-la-cnil-publie-ses-nouvelles-recommandations-pour-accompagner-une-innovation-responsable |
| Comment déployer une IA générative | 18/07/2024 | https://www.cnil.fr/fr/comment-deployer-une-ia-generative-la-cnil-apporte-de-premieres-precisions |
| Chatbots : les conseils de la CNIL | 19/02/2021 | https://www.cnil.fr/fr/chatbots-les-conseils-de-la-cnil-pour-respecter-les-droits-des-personnes |
| Norme simplifiée n° 57 (historique, abrogée depuis le RGPD) | — | https://www.cnil.fr/sites/cnil/files/atoms/files/ns57.pdf |

### Légifrance — codes
**Code de la consommation** : chapitre III (L223-1 à L223-7) https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006069565/LEGISCTA000032221441 · partie réglementaire (R223-1 à D223-9) https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006069565/LEGISCTA000032807254 · L242-16 https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006069565/LEGISCTA000032221841 · chapitre III bis (L223-8) https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006069565/LEGISCTA000051828333 · L111-1 (LEGIARTI000044142438) · L121-2 (LEGIARTI000044563114) · L121-4 (LEGIARTI000044563107) · L214-1 (LEGIARTI000032226990) · L214-2 (LEGIARTI000032226988) · L214-3 (LEGIARTI000032226986) · L215-1 (LEGIARTI000046194176) · L215-3 (LEGIARTI000032226976) · L221-3 (LEGIARTI000032226882)

**CPCE** : L32 (LEGIARTI000049571421) · L33 (LEGIARTI000044259890) · L33-1 (LEGIARTI000047293234) · L34 (LEGIARTI000051830311) · L34-5 https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006070987/LEGISCTA000006165910 · L44 (LEGIARTI000051830329) · D98-8 (LEGIARTI000044164666)

**Code civil** : 1100 (LEGIARTI000032006706) · 1100-1 (LEGIARTI000032006708) · 1113 (LEGIARTI000032040896) · 1114 (LEGIARTI000032040891) · 1119 (LEGIARTI000032040866) · 1188 (LEGIARTI000032041270) · 1240 (LEGIARTI000032041571) · 1241 · 1242 al. 1 (LEGIARTI000051786000) · 1590 (LEGIARTI000006441327)

**Code de commerce** : L441-1 (LEGIARTI000038414469) · L441-10 (LEGIARTI000038414392) · D441-5 (LEGIARTI000043197457) · L442-1 (LEGIARTI000054716237, v. 20/08/2026)

**Code du travail** — ⚠️ via `code.travail.gouv.fr` (Légifrance en 403 sur ce volet) : L1121-1 · L1222-3 · L1222-4 · L2312-8 · L2312-38 — `https://code.travail.gouv.fr/code-du-travail/<article>`

### Légifrance — textes non codifiés
- **LOI n° 2025-594 du 30 juin 2025** contre toutes les fraudes aux aides publiques (art. 13, art. 17) — https://www.legifrance.gouv.fr/loda/id/JORFTEXT000051824277
- **LOI n° 2020-901 du 24 juillet 2020** (démarchage téléphonique et appels frauduleux) — https://www.legifrance.gouv.fr/loda/id/JORFTEXT000042148119
- **LOI n° 2004-575 du 21 juin 2004 (LCEN)**, art. 1-1 (LEGIARTI000049568614) — https://www.legifrance.gouv.fr/loda/id/JORFTEXT000000801164
- **Décret n° 2026-662 du 23 juillet 2026** (R223-1 à R223-4, D223-9) — via la section réglementaire ci-dessus
- **Décision Arcep n° 2025-2215 du 27 novembre 2025** — https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000054122929

### Arcep
Décision n° 2018-0881 modifiée du 24 juillet 2018 (plan national de numérotation, PDF 37 p.) https://www.arcep.fr/uploads/tx_gsavis/18-0881.pdf · FAQ opérateurs (suppression de la déclaration) https://extranet.arcep.fr/communications-electroniques/questions-frequentes · Identifiant CE https://extranet.arcep.fr/communications-electroniques/identifiant-ce · Demande d'identifiant CE https://extranet.arcep.fr/communications-electroniques/identifiant-ce/demande-identifiant-ce · Référentiel identifiants CE https://extranet.arcep.fr/uploads/identifiants_CE.csv · MAJNUM https://extranet.arcep.fr/uploads/MAJNUM.csv · Fiche « Plan de numérotation pour les professionnels » https://www.arcep.fr/mes-demarches-et-services/entreprises/fiches-pratiques/plan-numerotation-professionnels.html · Consultation publique numérotation 07/2025 https://www.arcep.fr/actualites/les-consultations-publiques/p/gp/detail/evolutions-plan-national-de-numerotation-regles-de-gestion-juillet2025.html

### Service-Public
« Acompte, avance, arrhes et avoir : quelles différences ? » https://www.service-public.gouv.fr/particuliers/vosdroits/F31187 · « Mentions obligatoires sur un site internet » https://entreprendre.service-public.gouv.fr/vosdroits/F31228

### Documentation contractuelle fournisseurs [F2]
Telnyx AUP https://telnyx.com/acceptable-use-policy · Telnyx Terms and Conditions of Service https://telnyx.com/terms-and-conditions · Telnyx Regulatory requirements https://developers.telnyx.com/docs/numbers/phone-numbers/regulatory-requirements · OVHcloud contrats https://www.ovhcloud.com/fr/terms-and-conditions/contracts/ · OVHcloud CP Services de Téléphonie v. 08/07/2025 https://contract.eu.ovhapis.com/1.0/pdf/contrat_genTelephony-fr.pdf · OVH CP SIP Trunk v. 02/11/2015 https://www.ovh.com/fr/support/documents_legaux/Conditions_particulieres_SIP_trunk.pdf

---

*Rapport établi les 13-14 septembre 2026. `WebSearch` indisponible (budget de session épuisé sur les trois volets) — recherche conduite intégralement par accès direct aux sources officielles, avec navigateur réel pour Légifrance. Aucune source secondaire non officielle n'a été utilisée. Les 23 points non vérifiés sont listés au §11 : ce sont des trous, pas des réponses.*
