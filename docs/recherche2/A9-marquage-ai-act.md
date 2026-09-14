# A9 — Marquage lisible par machine (AI Act art. 50 §2) sur de la parole synthétique diffusée en temps réel sur le réseau téléphonique

> Recherche menée le **14 septembre 2026**. Toutes les dates de consultation ci-dessous sont le **2026-09-14** sauf mention contraire.
> Convention de marquage : **[F]** fait vérifié à la source · **[H]** hypothèse raisonnée · **[R]** recommandation · **[NV]** non vérifié / introuvable dans le temps imparti.
>
> **Cas d'usage tenu pour acquis d'un bout à l'autre** : agent vocal IA qui parle à un appelant sur le réseau téléphonique commuté, **8 kHz, G.711 μ-law**, en flux (paquets de 20 ms), **sans jamais produire ni stocker de fichier**, audio **détruit après transmission** (pas d'enregistrement par défaut).

---

*(rédaction en cours — sections assemblées ci-dessous)*

## 0. Réponse en une page

**[F]** L'article 50 §2 est **applicable depuis le 2 août 2026** (art. 113, phrase liminaire — le chapitre IV n'est visé par aucune des dérogations a/b/c). Il vise les **fournisseurs** de systèmes d'IA générant des « contenus de synthèse de type audio », sans exception pour l'éphémère : le texte dit « les **sorties** du système d'IA », pas « les fichiers ».

**[F]** Aucune publication scientifique 2023-2026 ne teste un tatouage audio neuronal sous **codec téléphonique** (G.711, G.722, G.729, AMR-NB). Le point le plus proche jamais publié est **Opus 16 kbps à 16 kHz**. Le triplet « décimation 8 kHz + bande 300-3400 Hz + quantification μ-law » n'a **jamais** été mesuré sur aucun watermark neuronal. C'est un angle mort documenté de l'état de l'art.

**[F]** Le texte lui-même borne l'obligation à ce que « **la technologie le permet** » (FR) / « **as far as this is technically feasible** » (EN), « compte tenu des spécificités et des limites des différents types de contenus, des **coûts de mise en œuvre** et de l'**état de la technique généralement reconnu**, comme cela peut ressortir des normes techniques pertinentes ». Le considérant 133 énumère explicitement, à côté des filigranes, « les **identifications de métadonnées** », « les méthodes cryptographiques », « les **méthodes d'enregistrement** » (*logging methods*), « les empreintes digitales ou d'autres techniques, selon qu'il convient ».

**[R]** Conclusion opérationnelle : le marquage exigible se satisfait ici par une **combinaison métadonnées de signalisation + journal de provenance + annonce vocale**, et non par un tatouage du signal, à condition de **documenter par écrit** l'état de l'art et l'impossibilité mesurée. Détail en §8.

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
- **[F] Taille** : `generator_base.pth` **58,8 Mo**, `detector_base.pth` **34,7 Mo`. Nombre de paramètres non publié [NV].
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
