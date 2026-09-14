# A9 — Marquage lisible par machine (AI Act art. 50 §2) sur de la parole synthétique diffusée en temps réel sur le réseau téléphonique

> Recherche menée le **14 septembre 2026**. Toutes les dates de consultation ci-dessous sont le **2026-09-14** sauf mention contraire.
> Convention de marquage : **[F]** fait vérifié à la source · **[H]** hypothèse raisonnée · **[R]** recommandation · **[NV]** non vérifié / introuvable dans le temps imparti.
>
> **Cas d'usage tenu pour acquis d'un bout à l'autre** : agent vocal IA qui parle à un appelant sur le réseau téléphonique commuté, **8 kHz, G.711 μ-law**, en flux (paquets de 20 ms), **sans jamais produire ni stocker de fichier**, audio **détruit après transmission** (pas d'enregistrement par défaut).

---

## 0. Réponse en une page

**[F]** L'article 50 §2 est **applicable depuis le 2 août 2026** (art. 113, phrase liminaire — le chapitre IV n'est visé par aucune des dérogations a/b/c). Il vise les **fournisseurs** de systèmes d'IA générant des « contenus de synthèse de type audio », sans exception pour l'éphémère : le texte dit « les **sorties** du système d'IA », pas « les fichiers ».

**[F]** Aucune publication scientifique 2023-2026 ne teste un tatouage audio neuronal sous **codec téléphonique** (G.711, G.722, G.729, AMR-NB). Le point le plus proche jamais publié est **Opus 16 kbps à 16 kHz**. Le triplet « décimation 8 kHz + bande 300-3400 Hz + quantification μ-law » n'a **jamais** été mesuré sur aucun watermark neuronal. C'est un angle mort documenté de l'état de l'art.

**[F]** Le texte lui-même borne l'obligation à ce que « **la technologie le permet** » (FR) / « **as far as this is technically feasible** » (EN), « compte tenu des spécificités et des limites des différents types de contenus, des **coûts de mise en œuvre** et de l'**état de la technique généralement reconnu**, comme cela peut ressortir des normes techniques pertinentes ». Le considérant 133 énumère explicitement, à côté des filigranes, « les **identifications de métadonnées** », « les méthodes cryptographiques », « les **méthodes d'enregistrement** » (*logging methods*), « les empreintes digitales ou d'autres techniques, selon qu'il convient ».

**[F] La pièce décisive est le point (88) des lignes directrices de la Commission C(2026) 5054 final du 20.7.2026** : le contenu temps réel éphémère « *without being recorded, stored or disseminated further* » **peut être exempté** — mais à **deux conditions cumulatives** : que le marquage soit techniquement infaisable **et** que la personne exposée soit informée. Ce n'est pas une exclusion de champ : c'est une exemption à mériter, et à documenter.

**[F] Le régime de preuve qui nous est applicable a un nom** : point (148) — un non-signataire du Code de bonnes pratiques « *should carry out a **gap analysis** that compares the measures they have implemented with the measures set out by a code of practice that is assessed as adequate* ».

**[F] Calendrier** : art. 50 applicable depuis le **2 août 2026** ; le sursis de l'« AI Omnibus » (jusqu'au **2 décembre 2026**) ne vaut **que** pour les systèmes mis sur le marché **avant** le 2 août 2026, et **jamais** pour l'annonce du §1 sur un système interactif (point 153). Un agent vocal lancé maintenant n'a **aucune** période transitoire.

**[R]** Conclusion opérationnelle : le marquage exigible se satisfait ici par une **combinaison journal de provenance + annonce vocale + non-rétention de l'audio**, complétée par la signalisation d'appel, et non par un tatouage du signal — à condition de **mesurer** l'infaisabilité (banc d'essai canal téléphonique) plutôt que de l'affirmer, et de produire la gap analysis écrite. Détail en §8.

---

## 1. Le texte exact et son champ

### 1.1 Article 50 §2 — verbatim (FR, JO L 2024/1689 du 12.7.2024)

> « **2.**   Les fournisseurs de systèmes d'IA, y compris de systèmes d'IA à usage général, qui génèrent des contenus de synthèse de type audio, image, vidéo ou texte, veillent à ce que les sorties des systèmes d'IA soient marquées dans un format lisible par machine et identifiables comme ayant été générées ou manipulées par une IA. Les fournisseurs veillent à ce que leurs solutions techniques soient aussi efficaces, interopérables, solides et fiables que la technologie le permet, compte tenu des spécificités et des limites des différents types de contenus, des coûts de mise en œuvre et de l'état de la technique généralement reconnu, comme cela peut ressortir des normes techniques pertinentes. Cette obligation ne s'applique pas dans la mesure où les systèmes d'IA remplissent une fonction d'assistance pour la mise en forme standard ou ne modifient pas de manière substantielle les données d'entrée fournies par le déployeur ou leur sémantique, ou lorsque leur utilisation est autorisée par la loi à des fins de prévention ou de détection des infractions pénales, d'enquêtes ou de poursuites en la matière. »

Version anglaise, même paragraphe — c'est elle qui porte la formule « techniquement faisable » :

> « **2.**   Providers of AI systems, including general-purpose AI systems, generating synthetic audio, image, video or text content, shall ensure that the outputs of the AI system are marked in a machine-readable format and detectable as artificially generated or manipulated. Providers shall ensure their technical solutions are effective, interoperable, robust and reliable **as far as this is technically feasible**, taking into account the specificities and limitations of various types of content, the costs of implementation and the generally acknowledged state of the art, as may be reflected in relevant technical standards. […] »

**[F] Réponse à la question « la formulation *techniquement faisable* figure-t-elle dans le texte ? »** : **oui, dans le corps même de l'article 50 §2** (version anglaise : *as far as this is technically feasible*), et non seulement dans un considérant. La version française rend la même idée par « **aussi efficaces, interopérables, solides et fiables que la technologie le permet** ». Les deux versions font également foi (art. 55 TUE). **[F]** Cette réserve est assortie de trois facteurs cumulatifs de modulation, tous favorables à notre cas : *spécificités et limites du type de contenu*, *coûts de mise en œuvre*, *état de la technique généralement reconnu tel qu'il ressort des normes techniques pertinentes*.

*Source : Règlement (UE) 2024/1689, versions FR et EN obtenues via l'Office des publications (négociation de contenu XHTML sur `https://publications.europa.eu/resource/celex/32024R1689`, cellar `dc8116a1-3fe6-11ef-865a-01aa75ed71a1`), consulté le 2026-09-14. NB : `eur-lex.europa.eu` renvoie actuellement un challenge WAF CloudFront (HTTP 202, `x-amzn-waf-action: challenge`) — le texte a donc été récupéré par l'endpoint cellar, qui sert le même document officiel.*

### 1.2 Qui est tenu, et à quelle date

**[F]** « **fournisseur** » (art. 3, point 3) : « une personne physique ou morale, une autorité publique, une agence ou tout autre organisme qui développe ou fait développer un système d'IA ou un modèle d'IA à usage général et le met sur le marché ou met le système d'IA en service sous son propre nom ou sa propre marque, à titre onéreux ou gratuit ».

**[F]** « **déployeur** » (art. 3, point 4) : « une personne physique ou morale […] utilisant sous sa propre autorité un système d'IA sauf lorsque ce système est utilisé dans le cadre d'une activité personnelle à caractère non professionnel ».

**[H]** Dans notre montage : nous (éditeur de l'agent vocal, mis en service sous notre nom auprès du salon) sommes **fournisseur** ; le salon est **déployeur**. Le §2 pèse donc **sur nous**, pas sur le client. Le §1 (annonce) pèse aussi sur le fournisseur (conception du système). Le §4 (hypertrucage) pèse sur le déployeur — voir §1.4.

**[F] Dates (art. 113)** :
- « Il est applicable à partir du **2 août 2026**. » — c'est la date qui gouverne le **chapitre IV**, donc l'article 50 : aucune des trois dérogations ne le mentionne.
- a) chapitres I et II → 2 février 2025 ; b) chap. III section 4, chap. V, VII, **XII** (sanctions) et art. 78 → 2 août 2025, sauf art. 101 ; c) art. 6 §1 → 2 août 2027.

→ **[F] L'obligation est en vigueur depuis six semaines à la date de cette recherche.** (Voir §7.2 pour l'éventuel décalage « omnibus numérique ».)

### 1.3 Considérant 133 — verbatim et ce qu'il autorise

> « (133) Divers systèmes d'IA peuvent générer de grandes quantités de contenu de synthèse qu'il devient de plus en plus difficile pour les êtres humains de distinguer du contenu authentique généré par des humains. […] il convient d'exiger que les fournisseurs de ces systèmes intègrent des solutions techniques permettant le marquage dans un format lisible par machine et la détection du fait que les sorties ont été générées ou manipulées par un système d'IA, et non par un être humain. De telles techniques et méthodes devraient être **aussi fiables, interopérables, efficaces et solides que la technologie le permet**, et tenir compte des **techniques disponibles ou d'une combinaison de ces techniques, telles que les filigranes, les identifications de métadonnées, les méthodes cryptographiques permettant de prouver la provenance et l'authenticité du contenu, les méthodes d'enregistrement, les empreintes digitales ou d'autres techniques, selon qu'il convient**. Lorsqu'ils mettent en œuvre cette obligation, les fournisseurs devraient également tenir compte des **spécificités et des limites des différents types de contenu**, ainsi que des évolutions technologiques et du marché pertinentes dans le domaine, **tels qu'elles ressortent de l'état de la technique généralement reconnu**. Ces techniques et méthodes peuvent être mises en œuvre **au niveau du système d'IA ou au niveau du modèle d'IA**, y compris pour les modèles d'IA à usage général qui génèrent du contenu, ce qui facilitera l'accomplissement de cette obligation par le fournisseur en aval du système d'IA. […] »

**[F] Trois enseignements décisifs, tirés du texte et non d'une interprétation :**
1. Le **filigrane n'est qu'une option parmi six** explicitement nommées. « Identifications de métadonnées » et « méthodes d'enregistrement » (*logging methods*) sont mises sur le même plan.
2. Une **combinaison** de techniques est expressément envisagée (« ou d'une combinaison de ces techniques »).
3. La mise en œuvre **au niveau du modèle** vaut pour le fournisseur en aval — c'est la base juridique de l'argument « notre fournisseur TTS marque en amont » (cf. §6), quand il le fait réellement.

**[F]** Le considérant 133 ne mentionne **ni le streaming, ni l'audio éphémère, ni la téléphonie**. Aucun passage du règlement ne distingue le contenu persistant du contenu transitoire pour l'article 50 §2.

### 1.4 LA question : le §2 s'applique-t-il à un flux audio téléphonique éphémère ?

**[F] Ce que dit le texte** : l'obligation porte sur « **les sorties des systèmes d'IA** » (*the outputs of the AI system*). Le règlement ne conditionne le §2 ni à l'existence d'un fichier, ni à un stockage, ni à une diffusion publique, ni à une mise en ligne. Par comparaison, le §4 alinéa 2 vise expressément des « textes **publiés** dans le but d'informer le public » — le législateur sait restreindre à la publication **quand il le veut**, et ne l'a pas fait au §2.

**[F] Ce que dit la définition de « système d'IA » (art. 3, point 1)** : « un système automatisé […] qui, pour des objectifs explicites ou implicites, déduit, à partir des entrées qu'il reçoit, la manière de générer des **sorties telles que des prédictions, du contenu**, des recommandations ou des décisions qui peuvent influencer les environnements physiques ou virtuels ». Rien n'exige la persistance.

**[F] Ce que dit le considérant 133 sur la finalité** : le risque visé est « l'intégrité de l'écosystème informationnel », « la désinformation et la manipulation à grande échelle, la fraude, l'usurpation d'identité et la tromperie des consommateurs ». Une conversation téléphonique éphémère relève typiquement de l'usurpation d'identité et de la tromperie du consommateur — **pas** de l'intégrité de l'écosystème informationnel.

**[H] Analyse** : *de lege lata*, un flux audio téléphonique synthétique **entre dans le champ littéral du §2** ; l'éphémérité n'est pas une exemption. Aucune des trois exclusions du §2 ne joue : notre système ne remplit pas « une fonction d'assistance pour la mise en forme standard », il **modifie substantiellement** (il génère de la parole à partir de texte), et il n'est pas au service de la répression pénale.

**[H] Mais** : la réserve de faisabilité technique, elle, joue à plein, et le considérant 133 impose de tenir compte des « spécificités et des **limites** des différents types de contenu ». Un flux 8 kHz μ-law non stocké est précisément le cas où *les limites du type de contenu* mordent le plus. C'est le cœur du dossier à constituer (§7.3, §8).

**[NV]** Aucune position officielle (Commission, Bureau de l'IA, autorité nationale) traitant explicitement du cas « audio conversationnel temps réel non enregistré » n'a été identifiée à la date du 2026-09-14. **Ne pas présenter l'exemption comme acquise.**

### 1.5 Ce que le §1 et le §4 ajoutent (et n'ajoutent pas)

**[F] §1, verbatim** : « Les fournisseurs veillent à ce que les systèmes d'IA destinés à interagir directement avec des personnes physiques soient conçus et développés de manière que les personnes physiques concernées soient informées qu'elles interagissent avec un système d'IA, sauf si cela ressort clairement du point de vue d'une personne physique normalement informée et raisonnablement attentive et avisée, compte tenu des circonstances et du contexte d'utilisation. […] »

**[F] §5, verbatim** : « Les informations visées aux paragraphes 1 à 4 sont fournies aux personnes physiques concernées de manière claire et reconnaissable **au plus tard au moment de la première interaction ou de la première exposition**. Les informations sont conformes aux exigences applicables en matière d'accessibilité. »

**[F]** Le §1 et le §2 sont **deux obligations distinctes et cumulatives** : le §1 vise l'information de l'humain, le §2 le marquage **lisible par machine**. Le §5 ne renvoie qu'à l'information des personnes physiques. **[F] L'annonce vocale ne peut donc pas, à elle seule, satisfaire le §2** : elle n'est pas « lisible par machine » au sens du §2. (Nuance en §5.2.)

**[F] §4 et hypertrucage (art. 3, point 60)** : « une image ou un contenu audio ou vidéo généré ou manipulé par l'IA, **présentant une ressemblance avec des personnes, des objets, des lieux, des entités ou événements existants** et pouvant être perçu à tort par une personne comme authentiques ou véridiques ». **[H]** Une voix de synthèse **générique** (non clonée sur une personne réelle) ne constitue pas un hypertrucage : elle ne « présente pas une ressemblance avec des personnes existantes ». → **[R] Ne jamais cloner la voix du gérant ou d'une employée** : cela ferait basculer le dispositif dans le §4, avec une obligation d'étiquetage supplémentaire pesant sur le **client** (déployeur), qui n'y est pas préparé.

**[F] §7, verbatim** : « Le Bureau de l'IA encourage et facilite l'élaboration de codes de bonne pratique au niveau de l'Union afin de faciliter la mise en œuvre effective des obligations relatives à la détection et à l'étiquetage des contenus générés ou manipulés par une IA. La Commission peut adopter des actes d'exécution pour approuver ces codes de bonne pratique conformément à la procédure prévue à l'article 56, paragraphe 6. Si elle estime que le code n'est pas approprié, la Commission peut adopter un acte d'exécution précisant des règles communes pour la mise en œuvre de ces obligations conformément à la procédure d'examen prévue à l'article 98, paragraphe 2. »

**[F]** L'article 50 **n'impose aucune documentation technique**. L'obligation de documentation technique (art. 11 + annexe IV) ne vise que « un système d'IA **à haut risque** ». Le « dossier technique » évoqué en §7.3 est donc une **pièce de défense volontaire**, pas une obligation réglementaire — ce qui ne la rend pas moins nécessaire.

---

## 2. Normes, code de bonnes pratiques et lignes directrices

### 2.1 Ce qui a changé depuis la rédaction du règlement — et qui décide de tout

**[F] Deux textes de niveau Commission, publiés à l'été 2026, gouvernent désormais l'application concrète de l'article 50 :**

| Texte | Référence | Date | Portée |
|---|---|---|---|
| **Code of Practice on Transparency of AI-generated Content** | PDF 38 p., `https://ec.europa.eu/newsroom/dae/redirection/document/129555` | **final le 10 juin 2026** ; avis d'adéquation de la Commission **8 juillet 2026** ; *Adequacy Assessment* de l'AI Board **9 juillet 2026** | art. 50 §2, §4, §5 — **~190 signataires** fin juillet 2026 |
| **Lignes directrices de la Commission sur l'article 50** | **C(2026) 5054 final**, ANNEXE, 51 p., `https://ec.europa.eu/newsroom/dae/redirection/document/131215` | **20 juillet 2026** | interprétation officielle de l'ensemble de l'article 50 |

*Pages de référence : `https://digital-strategy.ec.europa.eu/en/policies/code-practice-ai-generated-content` et `https://digital-strategy.ec.europa.eu/en/policies/guidelines-transparency-ai-generated-content` — consultées le 2026-09-14. Le PDF C(2026) 5054 a été téléchargé et lu intégralement pour la présente note.*

**[F] Le point (88) des lignes directrices est la pièce maîtresse de notre dossier.** Verbatim, page 27 :

> « **(88) Real-time content generation that is ephemeral and consumed immediately, without being recorded, stored or disseminated further (e.g. in video games, virtual reality applications), may also be exempted when marking is not technically feasible and the persons exposed to the content are made aware that the content is AI-generated or manipulated (e.g. in-experience disclosure, session-level notifications).** »

**[F]** Les deux conditions sont **cumulatives** (« *when marking is not technically feasible **and** the persons exposed … are made aware* »). **[H]** Notre cas remplit la définition d'entrée (temps réel, éphémère, consommé immédiatement, ni enregistré, ni stocké, ni diffusé plus loin) ; il reste à établir (a) l'infaisabilité technique et (b) l'information de l'appelant. Les exemples cités sont le jeu vidéo et la VR, **pas la téléphonie** : ce n'est donc pas un blanc-seing, mais une application nommée du principe de proportionnalité, qu'il faut documenter pour son propre cas.

**[F]** Deux exemptions voisines, pour bien situer la nôtre :
- **Point (86)** : métadonnées moins robustes suffisantes pour un système embarqué « *in physical products generating outputs in a technically controlled and closed environment that is mainly instructive in nature (e.g., an AI system embedded in navigation systems in vehicles)* ». Ne nous concerne pas.
- **Point (87)** : applications industrielles / B2B, « **excluding public and consumer-facing AI systems** », sous trois conditions cumulatives. **Un agent vocal qui répond à un appelant grand public en est explicitement exclu.**

### 2.2 Ce que disent les lignes directrices sur « techniquement faisable » et « état de la technique »

**[F] Point (81), verbatim** :
> « ‘Technically feasible’ solutions within the meaning of Article 50(2) AI Act are solutions that are capable of being implemented for the modalities covered in the scope of the provision, using currently available technology, methods, and engineering practices, within the specific technical architecture and operational environment concerned. The provider is not obliged to make use of a technical solution that is not yet developed or available on the market, or that is technically unfeasible for implementation. **Technical feasibility is an objective notion that is not dependent on the specific resources and capabilities of individual providers.** »

**[F] Point (83), verbatim (extraits)** :
> « The ‘state of the art’ is to be understood as a developed stage of technical capability at a given time as regards products, processes and services, based on the relevant consolidated findings of science, technology and experience and which is accepted as good practice in technology. **The state of the art does not necessarily imply the latest scientific research still in an experimental stage or with insufficient technological maturity.** Providers must continuously adapt their marking and detection solutions in a timely and proportionate manner as the technology and state of the art evolves. »

**[H] Lecture directe pour nous** : « *within the specific technical architecture and operational environment concerned* » légitime l'analyse au niveau de **notre** environnement (RTC, 8 kHz, μ-law, flux). Et « *does not necessarily imply the latest scientific research still in an experimental stage* » écarte l'exigence d'un fine-tuning d'AudioSeal sur canal téléphonique (§4.3), qui serait précisément de la recherche expérimentale. **Mais** « *not dependent on the specific resources and capabilities of individual providers* » interdit l'argument « on est une petite structure » : l'infaisabilité doit être **objective**, pas budgétaire.

**[F] Point (72)** : « providers may rely on **a single marking technique or a combination of techniques**, so long as their overall technical solution is machine-readable and meets the requirements ». **Point (73)** reprend la liste du considérant 133 et ajoute : « While methods for proving provenance and authenticity are mentioned in Recital 133 AI Act, **providers are not required to record or keep a full provenance chain** ». **Point (74)** : la solution peut être mise en œuvre « *at the level of the underlying AI model or integrated in the AI system's inference process* », et le fournisseur « *may rely on the marking solution implemented by an upstream model provider* » — **mais** « *Such reliance is without prejudice to the responsibility of the provider of the AI system to demonstrate compliance* ». **[R] Donc : s'appuyer sur le marquage d'un fournisseur TTS ne transfère pas la responsabilité ; il faut le vérifier soi-même.**

**[F] Point (75)-(76), obligation de détection** : le fournisseur doit rendre « *the means of detection … available to the persons potentially exposed to the content* », et « *must rely on publicly-available industry standard detection solutions* » ; à défaut de norme, « *in particular at the initial stage of the implementation of Article 50(2) AI Act for watermarking technologies* », il peut recourir à sa propre solution ou à une solution tierce, à titre transitoire. **[F] Il y a donc une obligation de détection et pas seulement de marquage** — point souvent oublié, et qui rend un tatouage propriétaire non détectable par un tiers insuffisant à lui seul.

### 2.3 Le Code de bonnes pratiques — ce qu'il exige concrètement pour l'audio

**[F] Mesure 1.1 — marquage multicouche** : « *So long as no single marking technique can, under the state of the art, ensure by itself compliance with the four requirements in Article 50(2) AI Act… for audio, images, video, and containerised text, in particular for content that can be disseminated online, Signatories will implement a multi-layered marking approach to ensure that the outputs of their generative AI systems are marked with **at least two layers** of machine-readable marking.* »
- **1.1.1 métadonnées signées** — **conditionnelle** : « *If content is generated, manipulated or exported **in a data format that supports attaching metadata**…* » → **[H] un flux RTP/G.711 n'est pas un tel format : la sous-mesure ne mord pas.**
- **1.1.2 watermark imperceptible** — « *with the exception of very short text* ».
- **1.1.3 fingerprinting / logging** — optionnel, et « *relying on fingerprinting or logging alone is not considered sufficient* ».
- **Dérogation à une seule couche** : réservée au système « *embedded in physical products … in a technically controlled and closed environment mainly instructive in nature* ».

**[F] Mesure 3.3 robustesse** : les altérations à encaisser incluent explicitement `voice enhancement`, `pitch shifting`, `time stretching`, `(re)compression`, `change of file format`, et « *survival of the analogue hole, e.g. … audio playback and recording* ». **[H] Une recompression μ-law 8 kHz relève de cette catégorie — le Code place donc la barre au-dessus de ce que l'état de l'art sait faire (§4).**

**[F] Mesure 3.4 interopérabilité, échéance dure** : « *At the time of publication of this Code, relevant interoperability standards and/or best practices are yet to be developed, except for digitally signed metadata.* » Les signataires doivent implémenter une solution d'interopérabilité de détection **au plus tard le 2 février 2027**.

**[F] Fait notable : le Code ne cite jamais C2PA ni « Content Credentials »** — zéro occurrence dans les 38 pages ; il parle génériquement de « digitally signed metadata ».

**[F] Portée juridique** : « *Even though adherence to the code is voluntary, the transparency requirements under article 50 of the AI Act are legal obligations* » ; « *providers and deployers that decide to comply through other means will have to demonstrate that those measures are adequate* » ; avis de la Commission : « *Adherence to the code does not constitute conclusive evidence of compliance.* »

### 2.4 C2PA / Content Credentials — et pourquoi ça ne s'applique pas à notre flux

**[F] Version courante : C2PA Technical Specification 2.4, avril 2026** (précédente : 2.3, décembre 2025). *Source : `https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html`, consultée le 2026-09-14.*

**[F] Audio couvert, mais toujours comme fichier conteneur** (Annexe A) : MP3/FLAC via objet `GEOB` ID3v2 ; WAV/BWF via un chunk RIFF d'identifiant `C2PA` ; AAC/ALAC/MP4/M4A via une boîte `uuid` BMFF ; OGG Vorbis via un flux logique dédié (ajouté en 2.3). **Aucune entrée pour G.711, μ-law, RTP ou flux brut sans conteneur** — vérifié par extraction du texte intégral de la spec (zéro occurrence de RTP, telephony, G.711).

**[F] Le « streaming » C2PA existe (§19 Live Video, introduit en 2.3, étendu en 2.4) mais présuppose un conteneur segmenté** :
> « This version of the specification applies to content packaged using the **ISO BMFF** standard, while being agnostic of manifest and delivery protocols. It also applies to **CMAF** content… **It does not support MPEG Transport Streams.** »
Validation segment par segment via `c2pa.livevideo.segment` ou *Verifiable Segment Info* (COSE_Sign1 dans une boîte `emsg`), les deux exigeant un `bmff-hash-map` et une boîte `uuid`.
→ **[F] Un flux RTP/G.711 μ-law 8 kHz n'a ni boîte `uuid`, ni `emsg`, ni segment fMP4 : il n'existe aucune voie C2PA de liaison forte (*hard binding*) applicable.**

**[F] La seule voie C2PA résiduelle est le *soft binding*** (§18.10, assertion `c2pa.soft-binding`, action `c2pa.watermarked.bound`) adossé à un *manifest repository* — notion formalisée en 2.4 sous le nom de **Durable Content Credential** : « *A Durable Content Credential is a Content Credential for which there exists one or more soft bindings that enable its discovery in a manifest repository.* » **[H] Cela suppose un manifeste publié et interrogeable, ce qui contredit frontalement « audio détruit après transmission ».**

**[F]** La **Soft Binding Algorithm List** officielle (`https://spec.c2pa.org/softbinding-alg-list/softbinding-algorithm-list.json`) compte **28 entrées, dont 10 déclarant `audio`** : `com.digimarc.validate.1`, `org.atsc.a336`, `io.iscc.v0` (ISO 24138), `com.nagra.nexguard.watermark.1`, `com.mentaport.watermark.1`, `com.sonicorigin.watermark.1`, `com.microsoft.wavmark.1`, `ai.contentlens.audio.mono`/`.stereo`, `com.markany.watermark.1`. **[H] Aucune fiche ne documente un mode temps réel à 8 kHz ; le registre ne porte ni débit, ni latence, ni bande minimale. Leur aptitude au G.711 n'est pas établie par le registre.**

**[F] Nouveauté 2.4 directement pertinente** : assertion **`c2pa.ai-disclosure`** (§18.28), « *for machine-readable AI transparency info* », avec `modelType`, `modelName`, `modelIdentifier`, `contentProfile` (dont `humanOversightLevel` : `fully_autonomous` / `prompt_guided` / `human_validated`). **[R] C'est le vocabulaire à réutiliser dans notre journal de provenance, même hors conteneur C2PA.**

**[F] Programme de conformance C2PA** : lancé mi-2025 avec la C2PA Trust List officielle ; l'*Interim Trust List* a été gelée le 1er janvier 2026. Gouvernance JDF, « more than 500 members and over 6,000 affiliates » (juillet 2026). *Source : `https://c2pa.org/conformance/`, `https://c2pa.org/news/`.*

### 2.5 ISO, JPEG Trust, normes harmonisées

- **[F] JPEG Trust = ISO/IEC 21617.** Partie 1 *Core Foundation* **publiée en janvier 2025** (2ᵉ édition en cours) ; parties 2 (*Trust profiles catalogue*), **3 (*Media asset watermarking*)** et 4 (*Reference software*) en développement. Périmètre : « *due to its generic nature, many aspects of the framework can also be applied to other image file formats or other media modalities such as video or **audio*** » — mais l'intégration native visée est la famille JPEG. *Source : `https://jpeg.org/jpegtrust/`, consultée le 2026-09-14.* **[H] Rien d'exploitable pour un flux téléphonique aujourd'hui.**
- **[NV] Reprise de C2PA en norme ISO (« ISO 22144 » ou autre numéro) : NON VÉRIFIÉE.** `iso.org` renvoie 403 (Cloudflare) sur toutes les URL testées ; le texte intégral de la spec C2PA 2.4 ne contient **aucune** occurrence de « 22144 » ni de mention d'une reprise ISO ; le site c2pa.org ne mentionne ISO nulle part hors référence indirecte à ISO 24138 (ISCC). **Ne pas affirmer que cette norme existe.**
- **[F] Normes harmonisées CEN-CENELEC JTC 21 : aucun item marquage/watermarking/provenance.** La demande de normalisation de la Commission porte sur dix domaines, **tous rattachés au chapitre III (haut risque)** : risk management, datasets, record keeping, **transparency (art. 13, pas art. 50)**, human oversight, accuracy, robustness, cybersecurity, quality management, conformity assessment. Première norme harmonisée entrée en enquête publique : **prEN 18286** (système de management de la qualité, art. 17), le 30 octobre 2025. *Sources : `https://digital-strategy.ec.europa.eu/en/policies/ai-act-standardisation` et `https://www.cencenelec.eu/areas-of-work/cen-cenelec-topics/artificial-intelligence/`.* **[NV]** Le programme de travail complet de `jtc21.eu` renvoie HTTP 406 : l'absence d'item watermarking est une **[H] fondée sur trois sources concordantes**, dont le Code lui-même (« *relevant interoperability standards … are yet to be developed* »), et non sur un listing exhaustif.

→ **[F] Conséquence : il n'existe aucune présomption de conformité par norme harmonisée pour l'article 50 §2. Le Code de bonnes pratiques est aujourd'hui le seul instrument reconnu à l'échelle de l'Union.**

---

## 3. Les techniques de tatouage audio utilisables

> **Note de méthode [F]** : le budget WebSearch de la session était **épuisé (200/200)** dès le premier appel de recherche. Toute la partie technique a été établie par **WebFetch direct** sur arXiv, GitHub, HuggingFace, deepmind.google et l'API Crossref. Signalé comme demandé.

### 3.1 Tableau comparatif

| Méthode | Licence code / poids | Sample rate | Robustesse publiée (chiffres) | Codec **voix** testé ? | Temps réel |
|---|---|---|---|---|---|
| **AudioSeal** (Meta, ICML 2024) | **MIT / MIT** [F] | 16 kHz (24/48 « ok » selon README) | acc. moy. **0,96**, AUC 0,97 ; MP3 32k **1,00** ; AAC 64k **1,00** ; EnCodec **0,98** ; resample 32 kHz **1,00** ; **highpass 1500 Hz → 0,61** ; lowpass 500 Hz **0,99** | **NON** [F] | Oui : détection **3,30 ± 2,03 ms**/segment (Quadro GP100), génération 7,41 ms ; mode streaming ≥ 0.2 **mais bug ouvert** [F] |
| **WavMark** (2023) | **MIT / MIT** [F] | **16 kHz strict** | BER moy. **0,48 %** sur 10 attaques ; s'effondre sous EnCodec (FNR ≈ 1,0 selon AudioMarkBench) | **NON** [F] | **Non** — détection **≈ 1710 ± 1314 ms** [F] |
| **Timbre Watermarking** (NDSS 2024) | **[NV]** | 22,05 kHz (amplitude STFT) | resample 16 kHz **100 %**, **resample 8 kHz 99,4 %** ; MP3 64k **99,92 %** / 8k **75,65 %** ; passe-haut / passe-bas **65,5 % / 70,8 %** | **NON** (resample 8 kHz nu ≠ codec) [F] | **[NV]** |
| **SilentCipher** (Sony, 2024) | **MIT / MIT** [F] | 44,1 kHz **et** 16 kHz | chiffres par attaque **[NV]** | **NON** [F] | **[NV]** |
| **XAttnMark** (ICML 2025) | **[NV]** | 16 kHz | détection **99,19 %** (TPR 98,56 / FPR 0,19) ; vitesse **99,5 %** ; bandpass 300-8000 Hz, MP3/AAC 128k, EnCodec, HSJA | **NON** — le papier écrit « Telephone/Narrowband Codecs: Not tested » [F] | **[NV]** |
| **Perth** (Resemble AI) | **MIT** [F] | **non documenté** [NV] | **aucun chiffre publié**, revendication générique seule [F] | **NON** [F] | **[NV]** |
| **SynthID audio** (Google DeepMind) | **fermé, indisponible hors produits Google** [F] | non publié [NV] | **aucun chiffre publié** ; revendications qualitatives (bruit, MP3, changement de vitesse) [F] | **NON** [F] | non publié [NV] |
| **Juvela & Wang** (ICASSP 2025, augmentation par codecs) | code public [F] | **22,05 kHz** | EER : Opus 64k **0,45 %**, MP3 64k **0,79 %**, DAC 8k **0,00 %**, Vorbis q3 **5,75 %** | **NON** — codecs de parole explicitement hors périmètre [F] | non discuté [F] |

### 3.2 AudioSeal — le seul candidat sérieux, et ses deux réserves

**[F]** *Proactive Detection of Voice Cloning with Localized Watermarking*, San Roman, Fernandez, Défossez, Furon, Tran, Elsahar — **ICML 2024**, [arXiv:2401.17264](https://arxiv.org/abs/2401.17264) (consulté 2026-09-14).

- **[F] Licence** : **MIT pour le code ET pour les poids** depuis la version 0.1.2 (02/04/2024) — le dépôt annonce explicitement « updated license to full MIT license (including the license for the model weights)! Now you can use AudioSeal in commercial application too! ». Model card HuggingFace `facebook/audioseal` : MIT. **C'est le seul des candidats à offrir cette clarté commerciale.**
- **[F] Taille** : `generator_base.pth` **58,8 Mo**, `detector_base.pth` **34,7 Mo**. Nombre de paramètres non publié [NV].
- **[F] Latence** : détection **3,30 ± 2,03 ms** par segment de 1-10 s sur une Quadro GP100 ; génération 7,41 ± 4,52 ms. Soit ×485 plus rapide que WavMark en détection.
- **[F] Réserve n° 1 — le streaming est cassé à date.** Issue GitHub **#105**, ouverte le **12/09/2026** (soit deux jours avant cette recherche), PR #106 liée, sans réponse de mainteneur : « Streaming watermark generator does not retain history between chunks ». Le mode streaming ne s'active qu'au niveau du conteneur ; 37 modules encodeur/décodeur internes conservent un `_NullState` vide. Vérifié par l'auteur de l'issue sur des chunks de 0,5 s : la sortie est identique avec ou sans historique. **Notre mode d'usage est précisément le chunk de 20 ms.**
- **[F] Réserve n° 2 — aucun codec téléphonique dans la table de robustesse.** Le texte du papier ne contient ni « telephone », ni « narrowband », ni « 8 kHz ». Le seul rééchantillonnage testé va **vers le haut** (32 kHz).

### 3.3 SynthID — hors de portée

**[F]** SynthID audio « embeds a watermark into any audio generated or published through our AI music generation model **Lyria** or the podcast generation feature of **NotebookLM** » (deepmind.google/science/synthid, consulté 2026-09-14). Méthode publiée le 16/11/2023 : tatouage dans une représentation spectrogramme.
**[F]** Seul **SynthID-Text** a été ouvert (`google-deepmind/synthid-text`, code Apache-2.0). **Le volet audio n'est ni open source, ni disponible via API hors produits Google.** Le **SynthID Detector** est en accès restreint (« currently collaborating with journalists and media professionals », liste d'attente).
**[F] Aucun chiffre de robustesse publié** pour SynthID audio, aucune publication évaluée par les pairs.
→ **[F] Écarté : inaccessible.**

---

## 4. Le point décisif — la survie à la bande téléphonique

### 4.1 Le canal, en chiffres officiels

- **[F]** ITU-T **G.711**, *Pulse code modulation (PCM) of voice frequencies* (Genève 1972, texte en vigueur approuvé le **25/11/1988**) : « The nominal value recommended for the sampling rate is **8000 samples per second** » (§2) ; « **Eight binary digits per sample** should be used for international circuits » (§3.1) ; deux lois de compression, **A-law et μ-law** (§3.2). → 64 kbit/s. *Source : PDF officiel ITU, `https://www.itu.int/rec/T-REC-G.711-198811-I/en`, consulté 2026-09-14.*
- **[F]** ITU-T **G.712** (11/2001), *Transmission performance characteristics of pulse code modulation channels* : le gabarit d'affaiblissement est spécifié « over the frequency range **300 Hz to 3400 Hz** ». *Source : PDF officiel ITU, `https://www.itu.int/rec/T-REC-G.712/en`, consulté 2026-09-14.*
- **[F] Conséquence arithmétique** : 8 kHz d'échantillonnage ⇒ **Nyquist à 4 kHz**. Toute la bande 4-8 kHz, dans laquelle opèrent AudioSeal, WavMark et XAttnMark (modèles 16 kHz), est **supprimée, pas dégradée**. S'y ajoutent le filtrage sous 300 Hz et la quantification logarithmique 8 bits.

### 4.2 Ce que la littérature teste réellement — et ce qu'elle ne teste pas

**[F] Résultat central de cette recherche : aucune publication de tatouage audio neuronal (2023-2026) n'évalue un codec téléphonique.** Vérifié de deux manières :

1. **Recherches arXiv (titre + résumé), toutes nulles, 2026-09-14** : `audio watermarking telephone codec` → « produced no results » ; `audio watermarking G.711` → aucun résultat ; `speech watermarking AMR codec` → aucun résultat ; `watermarking VoIP speech` → aucun résultat. `watermarking streaming real-time speech generation detection` → un seul résultat, *Seamless* (arXiv:2312.05187), qui **intègre** AudioSeal en traduction streaming sans tester aucun codec téléphonique.
2. **Lecture des tables de robustesse elles-mêmes** (AudioSeal Table 3 + Annexe D.2 ; Timbre Table III ; XAttnMark ; AudioMarkBench ; Juvela & Wang) : **aucune ne contient G.711, G.722, G.729, AMR, GSM, ni condition 8 kHz bout-en-bout.**

**[F] Le point le plus proche jamais publié** : **AudioMarkBench** (NeurIPS D&B 2024, arXiv:2406.06979) teste **Opus 16-256 kbps** et **MP3 8-40 kbps** — mais à **16 kHz**, jamais à 8 kHz, jamais en μ-law. **Timbre** publie **99,4 % après un rééchantillonnage 8 kHz** — mais c'est un aller-retour **nu**, sans μ-law, sans filtre 300-3400 Hz, sans perte de codec ; ce n'est pas un canal téléphonique. **Juvela & Wang (ICASSP 2025)**, le seul papier dont le sujet *est* la robustesse aux codecs, travaille **à 22,05 kHz** et écrit explicitement que les codecs de parole en bande étroite sont hors périmètre.

**[F] Littérature ancienne, pré-neuronale, qui existe mais n'est reprise par personne** (identifiée via l'API Crossref, DOI vérifiés, contenu non lisible — IEEE Xplore inaccessible, donc **[NV]** sur les chiffres) : *Quality-aware GSM speech watermarking* (ISCAS 2008, 10.1109/iscas.2008.4542080) ; *Audio Watermarking for Covert Communication through Telephone System* (ISSPIT 2006, 10.1109/isspit.2006.270935) ; *Comparison of digital audio watermarking techniques for the security of VOIP communications* (IAS 2011, 10.1109/isias.2011.6122787). Aucune n'est neuronale, aucune ne fournit de poids réutilisables, aucun travail 2024-2026 ne les reprend pour du TTS.

**[F] Nuance honnête** : la recherche arXiv ne porte que sur titre et résumé ; un test de codec enfoui dans une table pourrait échapper à cette requête. C'est pourquoi les tables ont été lues directement — mais l'exhaustivité n'est pas garantie sur l'ensemble de la littérature.

### 4.3 Ce qu'on peut raisonnablement en déduire (et ce qu'on ne peut pas)

- **[H, argument d'espoir]** Le profil fréquentiel d'AudioSeal — détection **intacte en lowpass 500 Hz (0,99)**, **détruite en highpass 1500 Hz (0,61, soit le hasard)**, entraînement en bandpass **300-8000 Hz**, évaluation en bandpass 500-5000 Hz à **1,00** — indique que l'énergie utile du tatouage vit **majoritairement sous 1500 Hz et largement sous 500 Hz**. Le filtrage téléphonique ne coupe que **sous 300 Hz**. La **bande passante seule n'est donc probablement pas le facteur limitant.**
- **[H, argument de risque]** Le danger se déplace sur ce que personne n'a mesuré : la **décimation 24 → 8 kHz**, la **quantification μ-law** (bruit *multiplicatif*, proportionnel à l'amplitude locale, très différent du bruit blanc additif σ = 0,05 testé), et le fait que la détection exige de **suréchantillonner 8 → 16 kHz**, produisant un signal dont la moitié haute du spectre est identiquement nulle — condition jamais présentée à aucun détecteur publié.
- **[H]** Ce n'est pas un problème de capacité de Shannon (3,1 kHz de bande utile et ~38 dB de SNR laissent largement de la place) mais un **décalage de domaine** : les décodeurs n'ont jamais vu cette dégradation.
- **[H]** Le remède techniquement correct existerait : **fine-tuner le détecteur AudioSeal avec une couche de distorsion « canal téléphonique » différentiable** (décimation → bande 300-3400 → μ-law → retour 16 kHz), en reprenant l'estimateur straight-through de Juvela & Wang pour la partie non différentiable. Licences MIT compatibles. **[R]** C'est un projet de R&D de plusieurs semaines, pas une case à cocher — voir §8 sur ce qu'on assume de ne pas faire.
- **[F] Rappel de sécurité** (AudioMarkBench) : **100 % de faux négatifs sous attaque en boîte blanche** pour les trois méthodes évaluées, à SNR 20. Un tatouage est une **trace de provenance coopérative**, pas un mécanisme anti-adversaire. Aucun tatouage n'empêchera un fraudeur de faire passer sa voix pour humaine.

> **[F] Verdict de la section** : pour un flux 8 kHz / G.711 μ-law en chunks de 20 ms, **il n'existe aujourd'hui aucun chiffre publié sur lequel fonder une obligation de résultat**. Ni « ça marche », ni « ça casse ». Le croisement « watermark neuronal de parole synthétique » × « codec téléphonique bande étroite » est un **angle mort complet de l'état de l'art** — c'est exactement le terrain où joue la réserve de faisabilité technique de l'article 50 §2.

---

## 5. Les alternatives au tatouage du signal

> Toutes les citations de cette section proviennent des **lignes directrices C(2026) 5054 final du 20.7.2026** (PDF officiel `https://ec.europa.eu/newsroom/dae/redirection/document/131215`, **téléchargé et extrait intégralement le 2026-09-14**) et du **Code of Practice on Transparency of AI-generated Content** (PDF officiel `https://ec.europa.eu/newsroom/dae/redirection/document/129555`), sauf mention contraire.

### 5.1 Le cadre que les lignes directrices posent avant toute alternative

**[F] Point (70)** : marquage **et** détection sont indissociables — « *Fulfilling only one element (e.g. for machine-readable marking of outputs without the means for their detection being available) will not suffice to comply with that provision.* »

**[F] Point (71) — définition officielle de « lisible par machine »** :
> « A machine-readable format means that marks are structured in a way that allows **software applications to easily identify, recognise and extract them without human intervention**. Perceptible marks and labels are not excluded as a complementary measure, where appropriate, with a view to facilitating the compliance of deployers with their obligation to label deep fakes pursuant to Article 50(4) AI Act. »

**[F] Point (72)** : « providers may rely on **a single marking technique or a combination of techniques** ».
**[F] Point (73)** : la liste du considérant 133 est reprise telle quelle — *watermarks, metadata identifications, cryptographic methods, **logging methods**, fingerprints or other techniques* — et le texte précise : « **providers are not required to record or keep a full provenance chain** containing information on content origin and modifications ».

**[F] Point (63) — l'agent vocal est nommément visé** :
> « Article 50(2) AI Act may also apply to **AI agents** if the AI agent takes an action, the output of which is AI-generated or manipulated content **perceptible by natural persons in the form of audio**, image, video or text. Those outputs must therefore be marked and detectable as described below. »

**[F] Point (60) — définition de l'« audio »** : « a **time-varying signal** encoding sound that is capable of being perceived through hearing by humans. This may cover **speech**, instrumental music or other audio signals. » → **[F] Rien, dans la définition officielle de l'audio, ne suppose un fichier. Un flux RTP est un signal variant dans le temps. L'argument « ce n'est pas un contenu parce qu'il n'y a pas de fichier » est mort.**

### 5.2 L'annonce vocale — ce qu'elle couvre et ce qu'elle ne couvre pas

**[F]** Le §1 est une obligation d'**information de l'humain**, le §2 une obligation de **marquage lisible par machine**. Les lignes directrices les traitent dans deux sections distinctes (3. et 4.) et le point (71) exige explicitement l'extraction « *without human intervention* ». **Une phrase prononcée à l'oreille de l'appelant n'est pas lisible par machine.**

**[F] Point (37) — la forme attendue de l'annonce dans notre contexte, verbatim** :
> « **Auditory disclosure: In voice-based or telephony contexts, explicit spoken statements at the beginning of the interaction** (e.g. “This is an AI-powered assistant”) combined, as appropriate, **with periodic reminders in longer interactions**, in particular in case of interruptions or a change of the role of the AI system during a user journey. **Distinct audio cues (e.g. tones or earcons) may support recognition, particularly for visually impaired users, but are not considered sufficient by themselves.** »

**[F] Point (36)** cite aussi, parmi les modes d'information admis, « *disclosure of AI identifiers, and credentials (e.g. AI agents that disclose their AI identity **to the extent feasible in a verifiable manner**)* », la note de bas de page 21 renvoyant aux attestations électroniques d'attributs eIDAS / portefeuille d'identité numérique européen. **[H] C'est la seule piste « identité vérifiable d'agent » citée par la Commission ; elle n'a aucune implémentation téléphonique aujourd'hui — [NV].**

**[R] Conclusion** : l'annonce vocale **ne satisfait pas le §2 à elle seule** — **mais** elle est la **seconde condition cumulative** de l'exemption du point (88) (§2.1). Elle passe donc du statut de « simple obligation §1 » à celui de **pièce constitutive de la défense sur le §2**. Elle doit être : prononcée en **premier**, avant toute autre parole ; **répétée** sur les appels longs ou après une interruption ; **journalisée** (texte exact, horodatage, position dans le flux) pour être démontrable.

### 5.3 Métadonnées de signalisation SIP — l'état réel du dossier

**[F] Il n'existe aucun standard IETF de signalisation d'un appelant synthétique ou généré par IA.** Vérifié sur le Datatracker le **2026-09-14** :
- `https://datatracker.ietf.org/doc/search?name=synthetic&rfcs=on&activedrafts=on&olddrafts=on` → aucun document sur les médias synthétiques ; les seuls RFC « synthetic » sont **RFC 4149** (2005, MIB de sources synthétiques) et **RFC 5297** (2008, AES-SIV).
- `https://datatracker.ietf.org/doc/search?name=artificial+intelligence&…` → 8 drafts actifs (gouvernance, gestion de réseau, datacenters, MIB, Colorado AI Act) ; **aucun ne touche SIP, la téléphonie, les appels, ni la divulgation d'un agent IA**.

**[F] Le seul véhicule normalisé qui pourrait porter une mention lisible par machine dans la signalisation est RFC 9795, *PASSporT Extension for Rich Call Data* (Proposed Standard, juillet 2025)** — `https://datatracker.ietf.org/doc/draft-ietf-stir-passport-rcd/`, consulté le 2026-09-14. Il définit :
- la revendication `rcd` (`nam` nom d'affichage obligatoire, `apn`, `icn` icône, `jcd`/`jcl` jCard),
- la revendication `rcdi` (empreintes d'intégrité des contenus référencés par URI),
- **la revendication `crn` — *call reason* / intention de l'appel**.

**[F]** Le document **ne mentionne ni l'IA, ni les appelants synthétiques** (une seule occurrence d'« automaton », dans un contexte sans rapport).

**[H] Ce qu'on peut en tirer et ce qu'on ne peut pas** :
- `crn` et `nam` sont **techniquement** des champs texte signés cryptographiquement (PASSporT/JWT, chaîne STIR), donc **extractibles par un logiciel sans intervention humaine** → ils cochent la définition du point (71).
- **Mais** : (a) STIR/SHAKEN est un dispositif d'**authentification de l'appelant**, pas de marquage du **contenu** ; le §2 porte sur « les sorties du système d'IA », pas sur l'en-tête d'appel ; (b) en France, le mécanisme d'authentification des numéros (**MAN**, décret n° 2023-1093 du 24/11/2023, obligation opérateurs) **[NV sur le détail — non revérifié dans cette session, cf. note A3 du dossier]** ne transporte pas de champ libre destiné au terminal de l'appelé ; (c) **aucun terminal grand public n'affiche `crn`** ; (d) l'exemption du point (86) réservée aux métadonnées « moins robustes » est cantonnée aux produits physiques en environnement fermé, **pas à nous**.
- **[F] Le Code de bonnes pratiques verrouille par ailleurs la sous-mesure métadonnées** : 1.1.1 ne s'applique que « *If content is generated, manipulated or exported **in a data format that supports attaching metadata*** ». **Un flux RTP/G.711 n'est pas un tel format.**

→ **[H] Verdict : la signalisation SIP est un *complément* documentable, pas une solution de marquage au sens du §2.** La mettre en place coûte peu (champ `nam`/`crn` côté trunk si l'opérateur l'accepte), n'engage rien, et se raconte bien en cas de contrôle. Elle ne doit jamais être présentée comme « le marquage ».

### 5.4 Journal de provenance (*logging method*) — la piste explicitement nommée par le texte

**[F]** *Logging methods* figure dans la liste du considérant 133 **et** du point (73). C'est la seule technique de la liste qui soit réalisable sans toucher au signal ni au conteneur.

**[F] Limite dure, posée par le Code de bonnes pratiques, mesure 1.1.3** : « *relying on fingerprinting or **logging alone** is not considered sufficient* » — dans le cadre de l'approche multicouche exigée pour les contenus « *that can be disseminated online* ».
**[H]** Notre flux n'est précisément **pas** diffusable en ligne (ni fichier, ni export), ce qui affaiblit l'applicabilité de la mesure 1.1 à notre cas ; mais nous ne sommes **pas signataires** du Code (§6.3), donc ce n'est pas cette mesure qui nous lie — c'est l'article 50 §2 lui-même, lu à travers le point (148) (§7.3).

**[R] Contenu minimal d'un journal de provenance défendable** (aucune de ces données n'est de l'audio ; la rétention reste soumise au RGPD) :

| Champ | Valeur | Justification |
|---|---|---|
| `call_id` | identifiant d'appel SIP | jointure avec la signalisation |
| `started_at` / `ended_at` | horodatage UTC | fenêtre d'exposition |
| `ai_generated` | `true` | l'assertion elle-même |
| `modelType` / `modelName` / `modelIdentifier` | moteur TTS + version | vocabulaire **C2PA 2.4 `c2pa.ai-disclosure`** (§2.4) |
| `humanOversightLevel` | `fully_autonomous` \| `prompt_guided` \| `human_validated` | idem |
| `disclosure_played` | `true` + texte exact + offset | preuve de la 2ᵉ condition du point (88) |
| `codec` / `sample_rate` | `PCMU` / `8000` | preuve du canal invoqué à l'appui de l'infaisabilité |
| `watermark_attempted` | `true`/`false` + méthode + raison d'échec | preuve de la 1ʳᵉ condition du point (88) |
| `audio_retained` | `false` | preuve du caractère éphémère |

**[R]** Réutiliser le **vocabulaire `c2pa.ai-disclosure` de la spec 2.4** même hors conteneur C2PA : cela rend le journal interopérable *par vocabulaire* à défaut de l'être *par format*, et c'est un argument gratuit en cas de contrôle.

### 5.5 Marquer le seul enregistrement, quand il existe

**[F] Point (88)** ne protège que le contenu « *without being **recorded**, stored or disseminated further* ». **Dès qu'un enregistrement est activé, l'exemption tombe pour ce contenu-là.**

**[R] Conséquence opérationnelle nette** :
1. **L'enregistrement d'appel est désactivé par défaut**, et c'est une décision de conformité, pas un choix produit.
2. S'il est activé (à la demande d'un client, ou pour une transcription), le fichier produit **est** un conteneur : il redevient marquable. On produit alors du **WAV/BWF avec chunk RIFF `C2PA`** (§2.4, Annexe A de la spec C2PA 2.4) **ou**, a minima, un manifeste latéral signé portant les mêmes champs qu'en §5.4.
3. **Ne jamais** laisser le client activer l'enregistrement sans que le pipeline de marquage du fichier soit en place : c'est le seul scénario où l'infaisabilité technique disparaît, et donc le seul où le §2 devient exigible **sans réserve**.

---

## 6. Ce que font réellement les acteurs du vocal

> Vérifications faites le **2026-09-14** par lecture directe des pages éditeurs. **Aucun** des fournisseurs examinés ne documente un marquage lisible par machine sur sa **sortie en streaming à 8 kHz μ-law**.

### 6.1 Tableau

| Fournisseur | Marquage documenté | Sur le streaming ? | Désactivable ? | Détection ouverte ? | Signataire du Code ? |
|---|---|---|---|---|---|
| **Microsoft / Azure AI Speech** | **Oui, mais uniquement sur *personal voice* et *avatar*** [F] | non précisé [NV] | non documenté [NV] | **Non — sur demande par e-mail** [F] | **Oui** [F] |
| **OpenAI** | **[NV]** — page de référence inaccessible (403) | [NV] | [NV] | [NV] | **Oui** [F] |
| **Google / DeepMind** | SynthID audio, **limité à Lyria et NotebookLM** [F] | non applicable à Cloud TTS [F] | n/a | **Non — liste d'attente** [F] | **Oui** [F] |
| **Meta** | AudioSeal, **MIT, ouvert** [F] (§3.2) | mode streaming **bogué** [F] | n/a (on l'intègre soi-même) | **Oui, librement** [F] | **Oui** [F] |
| **ElevenLabs** | **Aucun watermark documenté** ; classifieur propriétaire seulement [F] | n/a | n/a | classifieur maison, non standard [F] | **Non listé** [F] |
| **Cartesia** | **[NV]** — documentation derrière authentification (307 vers `play.cartesia.ai/docs-auth-login`) [F] | [NV] | [NV] | [NV] | **Non listé** [F] |
| **Rime** | **Aucune mention de watermark** dans la doc publique [F] | n/a | n/a | n/a | **Non listé** [F] |
| **Resemble AI** | *Perth*, MIT, **aucun chiffre publié** [F] (§3.1) | [NV] | n/a | code ouvert [F] | **Oui** [F] |

### 6.2 Les constats qui comptent

**[F] Microsoft** — *Transparency note* Azure TTS (`https://learn.microsoft.com/en-us/azure/ai-foundry/responsible-ai/speech-service/text-to-speech/transparency-note`, page datée du 31.3.2026, mise à jour 20.6.2026, consultée 2026-09-14), verbatim :
> « **Watermarks are added to custom neural voices created with the personal voice feature.** Watermarks allow users to identify whether speech is synthesized using Azure Speech, and specifically, which voice was used. **Eligible customers** can use Azure Speech watermark detection capabilities. **To request to add watermark detection to your applications please contact `mstts[at]microsoft.com`.** »
et, pour l'avatar : « *avatar outputs are automatically watermarked … To request watermark detection, please contact avatarvoice[at]microsoft.com* ».
→ **[F] Les voix *standard* (neural, HD, prebuilt) — celles qu'on utiliserait — ne sont pas couvertes par cette phrase.** Et la détection est **fermée** : elle ne satisfait pas le point (76) (« *publicly-available industry standard detection solutions* »).
**[F]** La même page impose au client la divulgation : « *Microsoft requires its customers to disclose the synthetic nature of text to speech avatars to its users.* »

**[F] Google** — SynthID audio est explicitement borné à **Lyria** et à la génération de podcasts de **NotebookLM** (`deepmind.google/science/synthid`, §3.3). La documentation **Chirp 3: HD** de Cloud Text-to-Speech (`https://docs.cloud.google.com/text-to-speech/docs/chirp3-hd`, consultée 2026-09-14) **ne contient aucune mention de watermark ni de SynthID**. → **[F] Un flux Cloud TTS n'est pas tatoué, ou du moins ce n'est pas documenté.**

**[F] ElevenLabs** — `https://elevenlabs.io/safety` (consulté 2026-09-14) : aucune occurrence de « watermark ». La page revendique une traçabilité **côté serveur**, pas dans le signal : « *Our systems are designed to trace generated content back to the user who generated it, allowing us to detect and respond to abuse* », et propose un **AI Speech Classifier** (« *lets you detect whether an audio clip was created using ElevenLabs* »). C2PA y est cité comme standard de référence, sans revendication d'implémentation audio. **Aucune mention de l'article 50.**
**[H]** Un classifieur propriétaire, non téléchargeable, sans API de détection publique et documentée, ne remplit pas le point (75)-(76).

**[F] Signataires du Code de bonnes pratiques** (`https://digital-strategy.ec.europa.eu/en/news/strong-backing-code-practice-transparency-ai-generated-content`, publié le 31.7.2026, mis à jour le 20.8.2026, consulté 2026-09-14) : ~190 organisations, dont **~82 en section 1 (fournisseurs)** et **~152 en section 2 (déployeurs)**. Section 1 : « *Aleph Alpha, Anthropic, Black Forest Labs, Cohere, **Google**, **Meta**, **Microsoft**, Mistral, **Open AI**, Synthesia* », plus **Resemble.ai**. **[F] ElevenLabs et Cartesia n'y figurent pas.**

### 6.3 Ce que ça change pour nous

**[H] Le point (74) permet de s'appuyer sur le marquage d'un fournisseur amont — mais il n'y a, à date, aucun fournisseur TTS commercialement disponible qui documente un marquage lisible par machine sur une sortie streaming téléphonique.** L'argument « notre fournisseur marque en amont » est donc **factuellement indisponible**, quel que soit le fournisseur retenu. Et il resterait de toute façon sans effet sur la charge de la preuve : point (74), « *Such reliance is without prejudice to the responsibility of the provider of the AI system to demonstrate compliance* ».

**[R]** Conséquence de sélection fournisseur : **exiger par écrit, dans l'appel d'offres TTS, une réponse à la question « marquez-vous la sortie streaming, avec quelle méthode, et la détection est-elle publiquement disponible ? »**. La réponse — y compris « non » — est une pièce du dossier §7.3. C'est gratuit.

---

## 7. Le risque réel

### 7.1 Qui contrôle, et combien ça coûte

**[F] Sanction, lignes directrices point (152), verbatim** :
> « Provider and deployers that do not comply with the applicable transparency obligations laid down in Article 50 AI Act may be **fined up to EUR 15 000 000 or, if the offender is an undertaking, up to 3 % of its total worldwide annual turnover** for the preceding financial year, whichever is higher. […] **In the case of small and medium-sized enterprises (SMEs), including start-ups, each fine shall be up to the above percentages or amount, whichever is lower.** »

**[F]** Base : **article 99 §4, point g)** — « *transparency obligations for providers and deployers pursuant to Article 50* » — et **article 99 §6** pour le plafond PME. *Source : `https://artificialintelligenceact.eu/article/99/`, consulté 2026-09-14 ; texte concordant avec le point (152) des lignes directrices officielles.*
→ **[F] Pour une PME française, le plafond effectif est donc le plus **faible** des deux : 3 % du CA mondial.** Sur un chiffre d'affaires de quelques dizaines de milliers d'euros, l'exposition financière brute est de l'ordre de **quelques centaines d'euros**. **[H] Le risque réel n'est pas la sanction pécuniaire : c'est l'injonction de mise en conformité, le retrait du marché (règlement (UE) 2019/1020), et la perte de crédibilité commerciale auprès de clients professionnels.**

**[F] Qui contrôle, point (151), verbatim** :
> « **Market surveillance authorities designated by the Member States**, the AI Office, and the European Data Protection Supervisor are responsible for supervising and enforcing the rules for AI systems falling within their competence, including the transparency obligations laid down in Article 50 AI Act. Such enforcement takes place within the system of market surveillance and compliance of products established by **Regulation (EU) 2019/1020** and the AI Act. […] Those authorities can take enforcement actions in relation to the obligations listed in Article 50 AI Act **on their own initiative or following a complaint, which every affected person or any other natural or legal person having grounds to consider such violations has the right to lodge** (Article 85). »

**[H] La voie d'entrée la plus probable d'un contrôle n'est donc pas un audit spontané, mais la plainte d'un appelant** — article 85. C'est cohérent avec ce qui déclenche les contentieux dans notre secteur.

**[F]** Le point (151) ajoute que ces compétences « *do not affect the powers and tasks of other supervisory authorities … (e.g. data protection, consumer protection)* ». **[H] En France, la CNIL reste donc compétente sur le volet données de l'appel, indépendamment du §2.**

**[H] Autorité française compétente — état non consolidé au 2026-09-14.** La seule source obtenue indique que « *The Directorate-General for Competition, Consumer Affairs and Fraud Control* » (**DGCCRF**) « *will act as the coordinating market surveillance authority and single point of contact* », dans le cadre d'un **modèle décentralisé** élargissant les autorités existantes — mais présenté comme **proposition législative**, sans date de désignation définitive. *Source : `https://artificialintelligenceact.eu/national-implementation-plans/`, consultée 2026-09-14 (source secondaire).*
**[NV]** Confirmation par une source officielle française **impossible dans cette session** : `economie.gouv.fr` renvoie **403 Forbidden sur deux tentatives** (page DGCCRF dédiée, puis racine DGCCRF) ; `senat.fr` 404 sur le dossier testé ; `cnil.fr/fr/intelligence-artificielle` ne contient aucune mention de désignation. **Ne pas affirmer que la DGCCRF est l'autorité désignée : dire qu'elle est pressentie comme point de contact unique, et vérifier avant tout usage contractuel.**

### 7.2 Les dates — et la découverte qui change le calendrier

**[F] Point (153), verbatim** :
> « According to Article 113 AI Act, **Article 50 AI Act will apply as from 2 August 2026**. This requires all in scope AI systems placed on the market or put into service in the Union to be compliant with that provision on that date, regardless of their date of placement on the market or putting into service. **Regulation amending the AI Act (the AI Omnibus), which has been recently adopted by the Union legislature, envisages a targeted grandfathering rule only with regard to the marking and detection obligations under Article 50(2) AI Act for generative AI systems placed on the market or put into service before 2 August 2026. It gives providers of those existing systems a transitional period to bring their systems in conformity by 2 December 2026. Systems that are partly interactive and partly generative may benefit from this transitional period only with regard to the marking obligation under Article 50(2) AI Act, while compliance with the disclosure obligation for AI systems directly interacting with natural persons must be ensured as of 2 August 2026.** »

**[F] Trois conséquences directes, et elles sont désagréables :**
1. **Le sursis existe — « AI Omnibus », jusqu'au 2 décembre 2026 — mais il est réservé aux systèmes déjà mis sur le marché ou en service *avant le 2 août 2026*.** Un agent vocal lancé après cette date **ne bénéficie d'aucune période transitoire** : il doit être conforme **dès sa mise en service**.
2. Un agent vocal est exactement le « *system partly interactive and partly generative* » visé par la dernière phrase. **Même si le sursis s'appliquait, il ne couvrirait que le §2** ; l'**annonce vocale du §1 est due sans délai depuis le 2 août 2026**.
3. **[F] Point (154)** : pas de rétroactivité — rien de généré avant le 2 août 2026 n'est à marquer.

**[H]** Le texte des lignes directrices qualifie l'« AI Omnibus » de « *recently adopted by the Union legislature* » au 20 juillet 2026. **[NV]** Sa référence exacte au JO n'a **pas** pu être vérifiée : `digital-strategy.ec.europa.eu/…/digital-omnibus` renvoie 404, la salle de presse de la Commission renvoie une page vide, et `artificialintelligenceact.eu/developments/` s'arrête au 12 juillet 2024. **Citer le point (153) comme source, jamais le règlement modificatif directement.**

### 7.3 Ce qu'un éditeur doit pouvoir présenter — la pièce maîtresse

**[F] Point (147)** : l'adhésion à un code de bonnes pratiques jugé adéquat est « *a straightforward, predictable, and legally certain way of demonstrating compliance* », et les autorités « *will focus their supervisory activities on assessing whether those signatories have adhered to the code* ».

**[F] Point (148), verbatim — c'est le régime qui nous est applicable, puisque nous ne sommes pas signataires** :
> « Providers and deployers that are **not signatories** to a code of practice that is deemed adequate pursuant to Article 50(7) AI Act **are expected to demonstrate how they have complied** with their obligations under Article 50(2), (4) and (5) AI Act **through other adequate means**. Furthermore, such providers and deployers **are expected to explain how the measures they implement ensure compliance** with their obligations under the AI Act. For instance, **they should carry out a gap analysis that compares the measures they have implemented with the measures set out by a code of practice that is assessed as adequate.** »

→ **[F] L'attendu officiel, pour un non-signataire, porte un nom : une *gap analysis* écrite, mesure par mesure, en regard du Code de bonnes pratiques.** Ce n'est pas une obligation réglementaire au sens de l'article 11 (qui ne vise que le haut risque, §1.5) — c'est la forme de preuve que la Commission annonce attendre. **C'est le livrable à produire.**

**[R] Le dossier à tenir, pièce par pièce** (rien de payant) :

| # | Pièce | Ce qu'elle établit | Source de l'exigence |
|---|---|---|---|
| 1 | **Gap analysis** écrite vs. Code de bonnes pratiques, mesure par mesure (1.1.1 / 1.1.2 / 1.1.3 / 3.3 / 3.4), avec pour chacune : applicable / non applicable / non faisable, et pourquoi | le régime du non-signataire | point (148) [F] |
| 2 | **Note d'infaisabilité technique** : canal G.711 μ-law 8 kHz, Nyquist 4 kHz, bande 300-3400 Hz, chunks 20 ms ; absence totale de littérature (§4.2) ; bug streaming AudioSeal #105 (§3.2) | 1ʳᵉ condition du point (88) | points (81), (83), (88) [F] |
| 3 | **Mesures de banc d'essai** : taux de détection AudioSeal avant / après passage par le canal simulé, sur N échantillons, avec le script et les données | transforme l'argument en **fait mesuré** | point (83) « *state of the art* » [F] |
| 4 | **Preuve de l'annonce** : texte exact, position en tête d'appel, rappels périodiques, journal par appel | 2ᵈᵉ condition du point (88) + §1 + §5 | points (36), (37), (88) [F] |
| 5 | **Journal de provenance** (§5.4) + preuve de non-rétention de l'audio | qualification « *ephemeral, not recorded, stored or disseminated* » | point (88) [F] |
| 6 | **Réponses écrites des fournisseurs TTS** sur leur marquage streaming | diligence au titre du point (74) | point (74) [F] |
| 7 | **Note de veille datée**, révisée au moins deux fois par an | « *Providers must continuously adapt their marking and detection solutions in a timely and proportionate manner as the technology and state of the art evolves* » | point (83) [F] |

**[R]** Pièce 3 : c'est la seule qui demande du travail, et c'est la seule qui vaut vraiment quelque chose. Un dossier qui **affirme** l'infaisabilité est une opinion ; un dossier qui la **mesure** est une preuve. Coût : AudioSeal (MIT), `sox`/`ffmpeg` (G.711 μ-law intégré), quelques heures de CPU. **Budget zéro respecté.**

---

## 8. Recommandation opérationnelle

### 8.1 Ce qu'on met en place

**[R] 1. L'annonce vocale, traitée comme une pièce de conformité et non comme un détail d'écriture.**
Première phrase de chaque appel, avant toute autre parole, formulation explicite du type « Bonjour, vous parlez à un assistant vocal automatique du salon X. » Rappel si l'appel dépasse un seuil (à fixer) ou après une interruption/transfert, conformément au point (37). Texte **versionné dans le code**, jamais laissé à la main du client sans garde-fou. Journalisé à chaque appel.
*Pourquoi* : due depuis le 2 août 2026 sans période transitoire (point 153), et 2ᵉ condition cumulative de l'exemption du point (88).

**[R] 2. Le journal de provenance (§5.4), avec le vocabulaire `c2pa.ai-disclosure` de la spec C2PA 2.4.**
Une ligne par appel, sans audio, incluant `watermark_attempted` et `audio_retained: false`. C'est une *logging method* nommée au considérant 133 et au point (73).
*Pourquoi* : c'est la seule technique de la liste officielle réalisable sur un flux sans conteneur, et elle transforme « on n'a rien fait » en « on a fait ce qui était faisable ».

**[R] 3. L'audio n'est jamais conservé, et c'est une décision architecturale écrite.**
Pas de fichier temporaire, pas de buffer persistant, pas de transcription audio archivée. Si un client demande l'enregistrement, le marquage du **fichier** (WAV/BWF + chunk RIFF `C2PA`, ou manifeste latéral signé) devient un prérequis de l'activation de la fonction, pas une option (§5.5).
*Pourquoi* : le point (88) tombe dès qu'il y a enregistrement. C'est la ligne à ne pas franchir sans compensation.

**[R] 4. Le banc d'essai « canal téléphonique » (pièce 3 du §7.3), une fois, mesuré et daté.**
Chaîne : TTS 24 kHz → AudioSeal `generator_base` → resample 8 kHz → filtre 300-3400 Hz → encodage μ-law → décodage → upsample 16 kHz → `detector_base`. N échantillons français, taux de détection publié en interne avec le script.
*Pourquoi* : c'est ce qui distingue un dossier crédible d'une pétition de principe. Et si le résultat est bon — ce que le profil fréquentiel d'AudioSeal rend non absurde (§4.3) — la question change de nature.

**[R] 5. La gap analysis écrite vs. le Code de bonnes pratiques, avant la première mise en service commerciale.**
Deux à trois pages, mesure par mesure. Datée, signée, révisée deux fois par an.
*Pourquoi* : point (148). C'est nommément ce que la Commission annonce attendre d'un non-signataire.

**[R] 6. Question écrite au fournisseur TTS retenu, et archivage de la réponse.**
*Pourquoi* : point (74), gratuit, et cela documente une diligence.

**[R] 7. Voix génériques uniquement — jamais de clonage de la voix du gérant ou d'une employée.**
*Pourquoi* : §1.5. Le clonage ferait basculer le dispositif dans le §4 (hypertrucage), avec une obligation d'étiquetage pesant sur le **client**, qui n'y est pas préparé et ne la respectera pas.

### 8.2 Ce qu'on assume de ne pas faire — et pourquoi

**[R] a. Pas de tatouage audio en production, à ce stade.**
*Justification* : (i) aucune publication 2023-2026 ne mesure un tatouage neuronal sous codec téléphonique — c'est un angle mort complet de l'état de l'art (§4.2), et le point (83) précise que l'état de la technique « *does not necessarily imply the latest scientific research still in an experimental stage* » ; (ii) le mode streaming d'AudioSeal est **cassé** au 2026-09-14 (issue #105, PR #106 sans réponse), or notre unité de travail est le chunk de 20 ms ; (iii) le point (70) exige marquage **et** détection accessible : un tatouage qu'aucun tiers ne peut vérifier ne satisfait pas le §2 de toute façon.
**Ce qu'on ne dit pas** : qu'un tatouage est impossible. On dit qu'il n'est **pas mesurable comme fiable** aujourd'hui sur ce canal, et on le documente. **Le renoncement est révisable** — c'est l'objet de la pièce 7.

**[R] b. Pas de manifeste C2PA sur le flux.**
*Justification* : la spec 2.4 ne prévoit aucune liaison forte hors conteneur (Annexe A : MP3/FLAC/WAV/AAC/MP4/OGG ; §19 live video : BMFF/CMAF, « *It does not support MPEG Transport Streams* »). Un flux RTP/G.711 n'a ni boîte `uuid`, ni `emsg` (§2.4). La seule voie résiduelle — *Durable Content Credential* par soft binding sur dépôt de manifestes — suppose un manifeste publié et interrogeable, ce qui contredit frontalement la destruction de l'audio.
**Ce qu'on garde quand même** : le **vocabulaire** `c2pa.ai-disclosure`, gratuit et interopérable par convention (§5.4).

**[R] c. Pas de signature du Code de bonnes pratiques.**
*Justification* : la mesure 3.3 impose une robustesse (« *survival of the analogue hole* », recompression, pitch shifting) que l'état de l'art ne sait pas tenir sur un canal 8 kHz μ-law (§2.3) ; la mesure 3.4 impose une solution d'interopérabilité de détection **au plus tard le 2 février 2027**. Signer, c'est s'engager sur des mesures qu'on ne pourra pas honorer, et « *Any opt-out from sections by signatories … will result in those providers and deployers losing the benefit* » (point 147). La voie du point (148) — démontrer par d'autres moyens adéquats, gap analysis à l'appui — est **plus honnête et plus tenable**.
**Ce qu'on perd** : la présomption de sérieux du point (147). **[H] Compensation : produire une gap analysis de meilleure qualité que la moyenne.**

**[R] d. Pas de marquage par la signalisation SIP présenté comme « le » marquage.**
*Justification* : aucun standard IETF de divulgation d'appelant IA n'existe (§5.3) ; RFC 9795 authentifie l'**appelant**, pas le **contenu** ; aucun terminal n'affiche `crn` ; le Code borne la sous-mesure métadonnées aux formats « *that support attaching metadata* ».
**Ce qu'on fait quand même** : renseigner `nam`/`crn` si l'opérateur l'accepte, et le noter dans la gap analysis comme couche complémentaire. Coût nul.

**[R] e. Pas d'attente d'une norme harmonisée.**
*Justification* : CEN-CENELEC JTC 21 n'a aucun item marquage/provenance ; les dix domaines de la demande de normalisation relèvent tous du chapitre III (haut risque) ; le Code lui-même écrit que « *relevant interoperability standards and/or best practices are yet to be developed, except for digitally signed metadata* » (§2.5). **Il n'existe aucune présomption de conformité par norme pour l'article 50 §2.** Attendre serait attendre indéfiniment.

### 8.3 Les trois choses à ne pas se raconter

1. **[F] L'éphémérité n'est pas une exemption.** Le point (88) est une exemption **conditionnelle et cumulative** (infaisabilité **et** information), pas une exclusion de champ. Et ses exemples sont le jeu vidéo et la VR — pas la téléphonie. Le point (63) vise nommément les agents IA produisant de l'audio ; le point (60) définit l'audio comme un signal variant dans le temps, sans exigence de fichier.
2. **[F] L'annonce vocale ne satisfait pas le §2.** Elle est nécessaire, elle n'est pas suffisante. Ceux qui répondent « on prévient l'appelant, donc c'est bon » confondent le §1 et le §2.
3. **[F] « On est une petite structure » n'est pas un argument.** Point (81) : « *Technical feasibility is an objective notion that is **not dependent on the specific resources and capabilities of individual providers**.* » L'infaisabilité doit être démontrée comme **objective** — d'où le banc d'essai, qui est la seule pièce qui parle ce langage. Le statut de PME ne joue que sur le **plafond de l'amende** (art. 99 §6), pas sur l'obligation.

### 8.4 Séquence

| Ordre | Action | Bloquant pour la mise en service ? |
|---|---|---|
| 1 | Annonce vocale + journalisation de l'annonce | **Oui** — due depuis le 2 août 2026, sans transitoire |
| 2 | Journal de provenance (§5.4) | **Oui** |
| 3 | Décision écrite « audio non conservé » + garde-fou sur l'enregistrement | **Oui** |
| 4 | Voix génériques, interdiction de clonage | **Oui** |
| 5 | Gap analysis vs. Code de bonnes pratiques | **Oui** (point 148) |
| 6 | Question écrite au fournisseur TTS | Non, mais avant le premier client |
| 7 | Banc d'essai canal téléphonique | Non — mais c'est la pièce qui vaut le plus |
| 8 | Note de veille semestrielle | Non |

---

## 9. Ce qui reste non vérifié

- **[NV]** Référence au JO du règlement modificatif « **AI Omnibus** » et son texte exact : connue seulement par la citation qu'en font les lignes directrices (point 153). Trois domaines testés en échec (`digital-strategy.ec.europa.eu` 404, salle de presse vide, `artificialintelligenceact.eu/developments` obsolète).
- **[NV]** **Désignation définitive de l'autorité française** : `economie.gouv.fr` 403 sur deux tentatives, `senat.fr` 404, `cnil.fr` muet. DGCCRF **pressentie**, non confirmée par source officielle.
- **[NV]** **OpenAI** : page de référence sur les voix de synthèse en 403. Marquage de la sortie audio non établi.
- **[NV]** **Cartesia** : documentation API derrière authentification (307 vers `play.cartesia.ai/docs-auth-login`).
- **[NV]** Chiffres de robustesse de **SilentCipher**, latence de **Timbre**, **XAttnMark**, **Perth** ; contenu des trois publications pré-neuronales de tatouage sur canal téléphonique (IEEE Xplore inaccessible).
- **[NV]** Reprise de C2PA en norme ISO (§2.5) — `iso.org` en 403.
- **[NV]** Programme de travail complet de **CEN-CENELEC JTC 21** (`jtc21.eu` en HTTP 406) : l'absence d'item « watermarking » est une déduction de trois sources concordantes, pas un listing exhaustif.
- **[NV]** Mécanisme d'authentification des numéros (MAN) français et sa capacité éventuelle à transporter un champ libre : non revérifié dans cette session.

**Budget** : WebSearch épuisé (200/200) avant le premier appel ; **toute cette note a été établie par WebFetch direct et téléchargement des PDF officiels**, plus lecture intégrale hors ligne du PDF C(2026) 5054 final (51 pages, extraction `pdftotext -layout`). Chaque domaine en échec a été réessayé au moins une fois avant d'être déclaré inaccessible.
