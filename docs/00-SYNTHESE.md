# Synthèse transversale des six recherches — 2026-09-13

> Six rapports sourcés (URL + date de consultation) dans `docs/recherche/`.
> Convention conservée : **[F]** fait vérifié · **[H]** hypothèse · **[R]** recommandation · **[NV]** non vérifié.
> Toutes les consultations : **2026-09-13**.

| Rapport | Sujet | Taille |
|---|---|---|
| `R1-oss-voice-stack.md` | Briques open source (orchestration, téléphonie, STT, TTS, VAD/turn, S2S, receptionists OSS) | 51 Ko |
| `R2-plateformes-commerciales.md` | Plateformes propriétaires, essais gratuits, coût réel à la minute | 52 Ko |
| `R3-telephonie-fr.md` | Numéros FR, renvoi d'appel, portabilité, SIP trunk, conformité, latence | 87 Ko |
| `R4-benchmark-fonctionnel.md` | Concurrents pro (US + FR/EU), taxonomie fonctionnelle, patrons de configuration, plaintes | 126 Ko |
| `R5-architecture-greffon.md` | Greffon embarquable, multi-tenant, extension MV3, config `.md`, questionnaire, mémoire, observabilité | 98 Ko |
| `R6-qualite-conversationnelle.md` | Budget de latence, tours de parole, robustesse FR, fiabilité d'action, sécurité, évaluation | 85 Ko |

---

## 1. Les dix faits qui ferment ou ouvrent des portes

1. **Le tout-local est impossible sur nos VPS.** Plancher speech-to-speech open source documenté : **16 Go de VRAM** (Unmute, README officiel) ; seul S2S francophone en sortie audio : Qwen3-Omni, **79 Go**. La seule solution OSS clé en main crédible (AVA, MIT, 1 212★) annonce **8–16 Go en tout-local CPU**. [F, R1 §5, §7]
2. ~~**Mais l'orchestration tient largement** (~90 Mo/session).~~ ⚠️ **CORRIGÉ le 14/09 par A4 — ce chiffre était trompeur.** Le test LiveKit qui le produit « ran the Silero VAD plugin » sur « a simple looping sine wave » : **ni STT, ni LLM, ni TTS**. Les chiffres réels : **Pipecat Cloud dimensionne 1 Go pour UNE session vocale** (`agent-1x`, « one bot per instance ») et LiveKit recommande 4 cœurs / 8 Go pour 10–25 jobs, soit **≈ 320 Mo/session**. **Donc : 1 Go = un appel simultané, 2 Go = deux à trois.** La RAM est le mur, pas le CPU. Le principe « l'inférence sort de la machine » reste vrai ; ce qui change, c'est la **capacité** : un VPS ne porte pas un standard, il porte un salon. [F, A4]
3. **Le tout-OSS coûte plus cher que l'hybride avant 17 100 min/mois.** Coût calculé par minute d'appel : tout-commercial **0,0894 $**, hybride auto-hébergé **0,0306 $**, tout-OSS sur GPU loué **0,3628 $** à 1 000 min/mois mais **0,0276 $** à 20 000 min/mois. On paie un GPU allumé, pas des minutes. [F, R2]
4. **La contrainte française n'est pas le prix, c'est le numéro.** Un agent IA **sortant** exige un numéro « Polyvalent Vérifié » (`0162 29`, `09 48 35`, `09 48 19`) avec adresse FR et K-bis ; aucun essai gratuit ne le couvre. Pour l'entrant, seuls **Telnyx** (09 à 0,50 $/mois, KYC ~72 h, portage par API) et **OVHcloud** (1 € HT, API de commande complète) ont API + grille publique. Plivo est disqualifié (entrants FR « Not Supported »). [F, R2, R3 §1]
5. **L'onboarding téléphonique tient en moins de 2 minutes** — renvoi d'appel **sur non-réponse** avec codes MMI pré-remplis par opérateur, à condition de **pré-acheter les numéros 09 par lots** pour sortir le KYC du parcours client. Total d'onboarding chronométré : **8 à 15 minutes**. [R, R3 §7]
6. **L'agent doit fonctionner sans connaître le numéro de l'appelant.** L'ARCEP recommande explicitement le masquage du CLI quand l'authentification MAN ne suit pas un renvoi. Contrainte de conception, pas cas limite — et elle entre en tension avec le cloisonnement par numéro appelant (§4 ci-dessous). [F, R3 §2]
7. **Annoncer l'IA est obligatoire et rentable.** AI Act art. 50 §1 **applicable depuis le 02/08/2026** (non repoussé par l'omnibus numérique). Et le verbatim le plus net de toute la collecte d'avis dit la même chose : *« Complaints basically stopped once we made it announce it was automated in the first breath. People forgive a robot for being a robot, they don't forgive it for pretending. »* [F + V-Reddit, R3 §5, R4 §C.2]
8. **Le démarchage est en opt-in depuis le 11/08/2026**, Bloctel supprimé. ⚠️ **Référence corrigée par A5** : c'est la **loi n° 2025-594 du 30 juin 2025, art. 13** (et non un décret du 25/07/2026). Toute fonction d'appel **sortant** doit être bornée au contrat en cours. **Et A5 resserre encore** : **relancer un client dormant est de la prospection**, parce qu'un contrat *exécuté* n'est plus « en cours » — opt-in R223-1, consentement ≤ 1 an, preuve 3 ans, créneaux 10h-13h/14h-20h du lundi au vendredi, 4 tentatives max sur 30 jours. [F, A5]
9. **Planity n'a aucune offre de réception d'appels IA** — ni page produit, ni prix publiés. Fresha (94,95 €/site/mois), Boulevard (125 $/200 min) et Zenoti l'ont industrialisée. **Aucun produit clé en main anglo-saxon ne parle français** ; les startups FR (Tala 29 €, Sylen 49 €, Elio 79 €, Kronos 249 €, Vokai 299 €) parlent français mais **ne sont greffées sur aucun logiciel de réservation**. [F, R4 §1, §2, §3.1]
10. **2026 est l'année du durcissement des licences.** Piper est passé MIT → **GPL-3.0** ; le turn-detector LiveKit est sous licence propriétaire **utilisable uniquement dans LiveKit Agents** ; TEN VAD/Framework portent une clause de non-concurrence Agora ; **jambonz v11+ exige une clé commerciale** en auto-hébergement ; `mod_audio_stream` bidirectionnel est payant ; XTTS-v2 (CPML) est **juridiquement mort** pour un produit facturé. [F, R1 §4.3, §8.5]

---

## 2. La position produit qui en découle

**L'intersection est vide et c'est la nôtre : le français, *dans* le logiciel de réservation.**

- Les startups FR servent le français **depuis l'extérieur**, sur un agenda générique : elles ne connaissent ni la durée réelle d'un balayage, ni le temps de pose bloquant, ni le praticien imposé.
- Les logiciels de réservation qui savent tout cela (Fresha, Boulevard, Zenoti) **ne servent pas le français** de manière documentée.
- Et l'exploitant lui-même formule la thèse : *« Unless they have a complete API integration that is official with whatever scheduling software you use, the ai agent is guaranteed to cause more pain for you as it will make mistakes all the time »*. [R4 §C.5]

**Cinq trous de marché confirmés par absence dans les sources officielles** [R4 §C.15] :

| # | Trou | Notre réponse |
|---|---|---|
| 1 | Personne n'entraîne l'agent sur **l'historique de rendez-vous** (tous partent du site web, de la fiche Google ou d'un questionnaire) | La greffe lit l'historique : prestations réellement vendues, durées réelles, associations, taux d'annulation |
| 2 | **Aucune boucle de correction** depuis une transcription ratée, alors que les exploitants la réclament (*« needs constant feedback »*) | Correction en un clic depuis l'appel raté, sans jamais toucher un prompt |
| 3 | **Presque personne ne fait tester l'agent avant la bascule** du numéro (exceptions : Dialzara, Vokai) | « Appelez votre agent » avant tout provisionnement |
| 4 | **Aucune détection d'urgence paramétrable** (exceptions FR : OSTIA, Sylen) | Règles d'escalade en cases à cocher, pas en paragraphe |
| 5 | **Le taux d'impasse n'est publié par personne** (seul son inverse flatteur l'est) | Publier le taux d'impasse : appels où le client a demandé un humain et ne l'a pas eu |

**Et deux règles commerciales tirées des plaintes** : ne **pas** facturer à la minute (modèle Goodcall : minutes illimitées, facturation au client unique — la facture imprévisible est la plainte n°1 des exploitants), et **ne rien facturer sur le spam** (chez Ruby, l'agent décroche les robocalls et l'exploitant les paie). [F, R4 §C.7]

---

## 3. La pile technique retenue (recommandation, à arbitrer §5)

| Couche | Choix | Licence | Raison |
|---|---|---|---|
| Téléphonie | **Asterisk 22 LTS + AudioSocket** | GPL-2.0 | La plus frugale ; AudioSocket = TCP, header 3 octets. FreeSWITCH écarté : voie bidirectionnelle libre morte (`mod_audio_fork` → 404) ou payante |
| Numéro / trunk | **Telnyx** principal. ⚠️ **OVHcloud écarté** : A5 a lu ses conditions — l'offre de téléphonie de détail **interdit contractuellement** les robots d'appels, les automates, le partage SIP, plus d'un utilisateur par compte SIP et la revente. **Zadarma** (2 €/mois, entrants gratuits) reste pour les essais, sous réserve de la même vérification contractuelle | — | Le droit d'usage prime sur la grille tarifaire |
| Orchestration | **Pipecat** | BSD-2 | Plus permissif qu'Apache-2.0, le mieux outillé pour les modèles locaux, v1.10.0 du 12/09/2026 |
| VAD | **Silero VAD v6** (1,2 Mo, < 1 ms/chunk) | MIT | Aucun concurrent sérieux |
| Endpointing | **Smart Turn v3.1** (8 Mo, 12–60 ms CPU, FR couvert) | BSD-2 | Le seul endpointing sémantique réellement libre (poids + données + entraînement) |
| STT | **API** en phase 1. Local plus tard : `nemotron-3.5-asr-streaming-0.6b` GGUF q8_0 (742 Mo) via NeMo-Speech.cpp | Apache-2.0 / OpenMDW-1.1 | Seul modèle streaming cache-aware avec licence commerciale. **Whisper est périmé** : fenêtre 30 s, aucun cache inter-appels |
| TTS | **Piper `fr_FR-siwis-medium`** (63 Mo) **en service HTTP séparé** | code GPL-3.0 / voix CC-BY 4.0 | Le process séparé est **obligatoire** pour rester hors du copyleft. Voix `tom` interdite (dataset AGPLv3), `gilles` à éviter (licence non vérifiée) |
| LLM | **API externe** | — | Rien de local sous 2 Go |

**Ordre de rapatriement plus tard : LLM → STT → TTS en dernier.** Le TTS français libre est le maillon faible (Kokoro annonce lui-même un support non-anglais « absent or thin »), pas le STT ni le LLM. [R2]

**Trois mesures à faire avant tout engagement client** — aucune source ne les publie : RTF de NeMo-Speech.cpp sur le VPS cible ; **WER français en bande téléphonique 8 kHz** (tous les WER publics sont en 16 kHz propre) ; RTF et RAM réels de Piper. [R1 §8.4]

---

## 4. Les règles de conception non négociables

Extraites des 43 règles de `R6 §7`, celles qui changent l'architecture :

**Latence** — SLO **p50 ≤ 700 ms, p95 ≤ 1 100 ms** de silence perçu (Roberts & Francis 2013 : bascule de jugement entre 600 et 800 ms ; 170 ms seulement sont du transport incompressible). Mesurer en **percentiles**, jamais en moyenne. **eager EOT + preemptive LLM oui, preemptive TTS non** (double le coût audio pour ~100 ms et risque de laisser fuir une demi-syllabe).

**Tours de parole** — endpointing sémantique obligatoire ; **seuils contextuels** (0,25 s sur un oui/non, 1,2 s sur une dictée) : c'est la règle la plus rentable du document. `min_interruption_words ≥ 2`. Débruitage sur le chemin VAD, **jamais** sur le chemin STT (Krisp : +18 % de WER en BVC-VAD, **×2** en BVC-VAD-STT).

**Capture** — keyterm set dynamique par établissement (**20–50 termes**, pas 500 : recommandation Deepgram) ; relecture du numéro par groupes de deux ; **DTMF de secours après 2 échecs** ; **ne jamais collecter d'e-mail par la voix** (numéro de mobile + SMS, ou lien SMS vers un formulaire) ; dates en **ISO 8601 absolu** dans le function call, jamais de relatif, avec confirmation « jour de la semaine + date + heure » qui sert de bit de parité.

**Action — la règle qui tient tout le produit** : **read-after-write avant toute confirmation orale.** L'agent n'a pas le droit de dire « c'est noté » sans avoir relu l'écriture. Trois barrières contre l'échec silencieux : read-after-write, SMS déclenché **par l'écriture** (pas par la fin de l'appel), réconciliation nocturne. Métrique **`taux de confirmation orpheline`, cible 0** — toute valeur > 0 est un incident, pas une statistique. Contrainte d'unicité en base sur `(établissement, praticien, créneau)` : seule garantie réelle contre le double-booking.

**Escalade** — transfert **immédiat et inconditionnel** sur demande explicite ; transfert chaud avec résumé par défaut ; **timer de secours** (les transferts échouent silencieusement si le destinataire ne répond pas, limite documentée LiveKit) ; hors horaires **pas de transfert** (sonnerie dans le vide = pire que rien) mais message + SMS au commerçant.

**Sécurité** — le LLM n'accède **jamais** à la base, seulement à des outils typés et validés côté serveur ; **aucune fonction de listage global** (elle n'est pas restreinte : elle n'existe pas) ; cloisonnement **côté serveur, pas côté prompt**. ⚠️ **Tension à résoudre** : le cloisonnement « par numéro appelant » (R6 §5.5) suppose un CLI que l'ARCEP recommande de masquer après renvoi (R3 §2). → toute action sur un RDV existant doit s'appuyer sur une **vérification indépendante** (SMS avec code, DTMF), jamais sur le seul CLI.

**Fiabilité, le chiffre à retenir** — τ-bench : GPT-4o passe de **~60 % en pass^1 à ~25 % en pass^8**. *La démonstration mesure pass^1, le commerce mesure pass^k.* Corpus de régression de 60–100 appels réels français **rééchantillonnés 8 kHz / G.711**, rejoués **k = 5 fois**, succès intégraux comptés.

---

## 5. Les décisions qui restent à trancher

| # | Décision | Statut | Enjeu |
|---|---|---|---|
| D1 | **Positionnement** | ✅ **Tranché le 13/09/2026 : greffon Crenolo d'abord**, vertical beauté | On hérite du catalogue, des durées réelles et de l'historique — le seul avantage qu'un concurrent générique ne peut pas copier |
| D2 | **Bord téléphonique phase 1** | ⏸ **Tranché après les mesures L0** (Asterisk auto-hébergé vs media streams Telnyx) | Les trois chiffres manquants changent le choix ; les mesurer coûte quelques jours, se tromper coûte une réécriture |
| D3 | **Budget d'inférence** | hybride ~0,031 $/min | À 1 000 min/mois ≈ 31 $ ; le tout-OSS ne devient rentable qu'au-delà de ~17 100 min/mois |
| D4 | **Enregistrement audio** | off par défaut (transcription seule) | Recommandé : rétention CNIL 6 mois max, et l'audio est un risque sans usage prouvé |
| D5 | **Appels sortants** | bornés au contrat en cours | Hors contrat = démarchage, opt-in obligatoire depuis le 11/08/2026 |

---

## 5 bis. Deuxième vague de recherches — ce qui est rentré

> Rapports dans `docs/recherche2/`. Vague lancée le 13/09/2026 au soir ; les axes A3, A4, A5, A8 restaient à relancer au moment de l'écriture.

### A7 — Hôtes de greffe (audit interne, lecture seule)
Détail : `docs/recherche2/A7-hotes-de-greffe.md`, spécification qui en découle : `docs/04-CONNECTEUR-CRENOLO.md`.
**Inkra et Kompagnon sont greffables tels quels** (token machine, routes déjà orientées agent, `GET /agent/capabilities` chez Kompagnon). **Crenolo est le seul chantier** : pas de clé d'API par établissement, pas de recherche client par téléphone, `client_email` obligatoire, rate-limit 10/h, **aucune contrainte d'unicité SQL sur `bookings`** — la non-superposition ne tient que par un verrou applicatif. Et **les durées réelles n'existent pas** en base : la promesse « l'agent apprend sur l'historique » se limite aux associations de prestations et aux noms de clients tant que `arrivee_le` / `fin_reelle_le` ne sont pas ajoutées.

### A1 — LLM et dialogue
Détail : `docs/recherche2/A1-llm-et-dialogue.md`.

1. **Le fait le plus contre-intuitif de tout le chantier : un prompt système plus long peut coûter moins cher.** Le cache de prompt a un **préfixe minimum** — **4 096 tokens** sur Claude Haiku 4.5 et sur Gemini Flash. Un prompt de 3 000 tokens n'est donc **pas cachable** et se paie plein tarif à chaque tour, douze fois par appel ; un prompt de 4 200 tokens passe à **0,1×**. **Conséquence de conception : le prompt système est délibérément calibré au-dessus du seuil**, et la doctrine « prompt court » des acteurs du vocal ne s'applique pas telle quelle.
2. **Aucun fournisseur ne publie de TTFT p50/p95.** Groq et Cerebras publient du débit (tokens/s), pas de la latence. La cible 250/500 ms **devra être mesurée au banc** — c'est un ajout au lot L0.
3. **Résidence UE** : OpenAI la documente (`eu.api.openai.com`, ZDR éligible sur chat/responses/realtime, cache retenu 24 h) ; **Anthropic n'en a aucune** (`inference_geo` ne connaît que `us` et `global`). Scaleway confirme la région Paris.
4. **Coût d'un appel de 3 minutes** (12 tours, système 4 200 tokens caché, hypothèses écrites dans le rapport) : gpt-5-mini **0,57 ¢** · Gemini Flash-Lite **0,69 ¢** · **Scaleway Mistral Small, sans aucun cache, 0,91 ¢€** · gpt-5.4-mini 1,60 ¢ · Haiku 4.5 2,18 ¢. **Le LLM n'est pas le poste dominant** face à la téléphonie, au STT et au TTS — et l'argument « il faut de l'américain pour le prix » ne tient pas.
5. **Ajouter un outil coûte des tokens** : la seule présence d'outils ajoute 496 à 588 tokens de prompt caché chez Anthropic. À compter dans le préfixe.
6. **Recommandation** : prompt long et figé (4 200–5 000 tokens, ordre Vapi), outils immuables, **toute variable placée après la rupture de cache** ; deux pistes à départager par mesure — UE stricte (Scaleway Mistral Small, OVHcloud) ou qualité d'outillage (gpt-5-mini via `eu.api.openai.com`). **Groq écarté** pour cette charge (remise de 50 % seulement, cache limité à trois modèles).

### A2 — STT et TTS français en API
Détail : `docs/recherche2/A2-stt-tts-francais.md`.

1. **Le piège de facturation est confirmé noir sur blanc.** AssemblyAI : « billed on the total duration that your WebSocket connection stays open, **not on the amount of audio you send** ». Idem pour la Voice Agent API de Deepgram. Les silences se paient. Le STT Deepgram seul, lui, reste facturé à la minute d'audio.
2. **Azure est le seul fournisseur à documenter `say-as` comme valide en français**, avec `number_digit` et surtout `alphanumeric format="spell"` **où le tiret force la pause** (`AB-CD-EF` → « A B ⟨pause⟩ C D ⟨pause⟩ E F »). C'est exactement le groupement par deux exigé pour relire un numéro de téléphone. **Argument décisif en faveur d'Azure côté TTS.**
3. **Google Chirp 3 HD est disqualifié pour notre usage** : « SSML tags are not currently supported for streaming requests ». On ne peut pas avoir `say-as` **et** le streaming — or nous avons besoin des deux dans la même phrase.
4. **Deepgram ne détecte aucune entité PII en français** (« English only, even when you request `true` ») ; seule la rédaction de nombres fonctionne. L'anonymisation des noms devra être faite chez nous.
5. **Le piège des nombres français n'est documenté par personne.** Aucun fournisseur ne dit un mot sur « quatre-vingt-dix-huit », ni sur septante/nonante. **Décision : ne pas déléguer la normalisation au STT** pour les numéros, dates et heures — récupérer le texte en lettres et le parser avec une grammaire française déterministe. Le mode d'échec attendu est un **bug de post-traitement** (`4 20 12`), pas une erreur acoustique.
6. **Deux éliminations sur les chiffres du fournisseur lui-même** : Speechmatics (plancher `max_delay` à 0,7 s, soit 3,5× notre cible) et Deepgram Aura-2 (616 ms de TTFB en exemple, sans garantie) — malgré ses deux voix françaises nommées.
7. **Coût des assemblages** (hypothèses écrites : 14 car./s, 35 % de parole agent, socket ouverte pendant tout l'appel) : qualité maximale Azure + Azure HD **0,0233 $/min** · équilibre Deepgram Nova-3 + Rime Mist v3 **0,0148 $/min** · coût minimal AssemblyAI EU + Azure Neural **0,0070 $/min**, ⚠️ **conditionné** à la confirmation du support du français par Universal-Streaming (pages 404) ; repli Deepgram + Azure à 0,0103 $/min.
8. **Trois cibles du cahier des charges restent non tranchables sur documentation** : aucune latence de finalisation p95 publiée, aucun WER français 8 kHz, et seuls Rime (« bien sous 100 ms ») et ElevenLabs Flash (« ~75 ms ») publient un TTFB.

### A6 — Métier salon (et pack sectoriel coiffure)
Détail : `docs/recherche2/A6-metier-salon.md`. Particularité : l'agent a **mesuré lui-même** plutôt que de citer des tiers — 176 fiches d'établissements français réels, **12 547 lignes de prestation avec nom et durée réels**. Biais assumé : Treatwell FR sur-représente ongles, épilation et massage.

1. **Le temps de pose existe chez les trois éditeurs, sous trois noms** : Planity « **forfait** » (temps d'application, de pause, brushing, rinçage), Fresha « **processing time** » — *« the client is still present while the team member is available to take another appointment »* — opposé à « blocked time », Phorest « **gap time** ». C'est la double occupation, écrite noir sur blanc. Détail révélateur : **chez Planity, le gérant ne peut pas créer un forfait lui-même**, il doit appeler le service client.
2. **Mais l'ordre de priorité proposé n'est pas celui attendu** : ① **la pause déjeuner** — son absence est le seul défaut *visible du client*, l'agent promettant un créneau qui n'existe pas ; ② **surdimensionner plutôt que sous-dimensionner** ; ③ le temps de pose — optimisation de revenu, pas de justesse, la V1 peut vivre sans **en l'assumant** ; ④ la cabine (bloquant en esthétique, secondaire en coiffure). Coût chiffré du renoncement ③ : ~30 min de praticien gelées par coloration (médiane 60 min, n=240 ; balayage 120 min, n=25).
3. **Grille au pas de 5 minutes, pas 15** : **100 %** des durées mesurées sont multiples de 5, **68,6 % seulement** de 15. Une grille au quart d'heure jette 31 % du catalogue.
4. **L'intention dominante n'est pas « je veux une coupe »**, c'est **« comme la dernière fois »** — Planity a un bouton « Reprendre RDV » conçu explicitement pour l'appel téléphonique. Et **le report ou l'annulation tardive est structurellement téléphonique**, parce que les logiciels ont volontairement fermé ce cas en ligne. Ce sont donc les deux parcours à soigner en premier, pas la prise de RDV nue.
5. **Six collisions lexicales produisent un mauvais rendez-vous**, pas seulement une mauvaise transcription : `permanente` (cheveux) ↔ `semi-permanent` (vernis) ↔ `maquillage permanent` · `mèches` (couleur) ↔ `mèche` (rajout) · `extension` cils/cheveux · `patine` ↔ `platine` · `soin` capillaire/visage/corps · `remplissage` ongles/cils. Plus le sigle **`SIF`** (sillon interfessier), prononcé tel quel. Le lexique couvre aussi la **coiffure afro** (tressage, vanilles, closure, tissage), absente des lexiques génériques.
6. ⚠️ **Point juridique sensible** : Code de la consommation L214-1 à L214-3 — « en l'absence de précision, les sommes versées sont **présumées être des arrhes** », et arrhes ≠ acompte : le professionnel qui n'exécute pas rembourse **le double**. **Le mot que l'agent prononce engage le salon** : le script doit dire exactement ce que le gérant a paramétré, jamais « acompte » par confort de langage. Par ailleurs, chez Planity comme chez Fresha **l'application d'une pénalité reste une décision humaine** — l'agent ne la déclenche jamais. Et **le retard n'est modélisé par aucun logiciel** : règle de maison en texte libre, pas objet de données.
7. **Volume d'appels et taux d'appels manqués : aucune source sérieuse.** Le « 40+ appels/jour » qui circule est un cas composite UK/IE, **non citable**. Conséquence assumée : **ce chiffre sera notre donnée propriétaire**, mesurée par l'agent lui-même en V1, et non un préalable.
8. **Pack sectoriel coiffure livré** : 5 blocs, ~35 questions, **toutes cochables, jamais plus de 5 options, toujours un défaut pré-coché** — un salon qui ne répond rien doit obtenir un agent qui fonctionne. Durées proposées = les médianes mesurées.

### A8 — Console et boucle de correction
Détail : `docs/recherche2/A8-console-ux.md` · conception qui en découle : `docs/06-CONSOLE-ET-CORRECTION.md`.

1. **Le trou est confirmé, et par l'aveu des éditeurs eux-mêmes.** Intercom écrit : « **No option to fast-track or manually flag individual conversations for recommendations** ». Fin et Zendesk corrigent **par agrégat statistique** (seuils de volume, 90 jours de tickets) — inatteignable pour un salon à 30 appels/jour. Retell est le plus proche (débogage d'un tour, « Regenerate 10 answers ») mais ses correctifs « link to a guide you follow to make the change yourself », et son assistant demande une phrase en anglais : **c'est un prompt déguisé**. Vapi a une section « Turn production issues into regression tests » — une consigne écrite à un développeur, aucun bouton.
2. **Le geste à copier ne vient pas de l'IA.** Gmail « Filter messages like these » (critères pré-remplis depuis **un** message) et la correction iOS 17 (« tap the underlined word and choose an option »). Une correction n'est pas un texte : **c'est une faute choisie dans une liste courte, appliquée à un empan de transcription**, qui écrit un objet typé.
3. **Limite structurelle à connaître** : Intercom admet qu'une règle écrite en langue naturelle **peut ne pas être retenue** par le modèle sur un tour donné, et que ce n'est *« not a configuration error »*. **Conséquence : les règles d'agenda et de maison ne sont pas des phrases dans un prompt, ce sont des contraintes évaluées côté serveur**, hors du modèle.
4. **Ne jamais afficher un score de confiance** : Google avertit de ne pas traiter `confidence` comme fiable. Soulignement discret, pas de chiffre.
5. **Le temps réel se paie en batterie** : le cas Pandora (0,2 % des octets, **46 % de l'énergie**) disqualifie l'interrogation périodique ; un WebSocket échappe au bridage d'arrière-plan là où un `setTimeout` non. **SSE retenu**, fermé dès que l'écran est masqué.
6. **Notifications** : Pielot & Rello (30 volontaires, médiane **63,5 notifications/jour**, 73,3 % ont voulu changer leurs réglages) — l'anxiété vient de la peur de rater ce qu'on attend de soi. D'où quatre canaux seulement et **un fil quotidien à 19 h**.
7. **Gate Barthez passé** (14 points), pic et fin nommés par écrit. Six tentations écartées, dont **le rouge sur les appels ratés** : le mauvais exemple s'affiche en gris, jamais en rouge — un gérant ne doit pas avoir peur d'ouvrir sa console.

### A3 — SMS transactionnel France
Détail : `docs/recherche2/A3-sms-france.md`.

1. ⚠️ **La passerelle SIM de Crenolo est illicite, et ce n'est pas une zone grise.** Décision Arcep n° 2018-0881 modifiée, **version consolidée au 1er janvier 2026**, annexe 1 §2.3.2 f : les numéros territorialisés « ne peuvent être utilisés comme identifiant de l'appelant présenté à l'appelé pour des appels ou des **messages émis par des systèmes automatisés** ». Pour un **06/07, les trois exceptions du texte sont expressément écartées** : l'interdiction est **absolue depuis le 1er août 2019**, et l'Arcep recommande aux opérateurs d'interrompre l'acheminement. Le terme « SIM box » n'apparaît nulle part : la pratique n'est pas nommée, elle est rendue **inopérante par le droit de la numérotation**. → **Concerne le produit Crenolo aujourd'hui, pas seulement le vocal.**
2. **Deuxième raison, indépendante du droit : aucun accusé de remise.** `envoye_le` signifie « le modem a accepté », jamais « l'opérateur a remis ». Un produit dont le SMS **est** la preuve de bout en bout ne peut pas reposer sur un canal qui ne la fournit pas — un numéro mal capté par l'agent serait aujourd'hui marqué « envoyé ».
3. **L'argument économique qui justifiait la SIM ne tient pas** : 150 RDV × 2 messages = 300 SMS/mois ≈ **17 € HT** (OVHcloud 17,40 · Spot-Hit 17,70 · Twilio 23,94 $). Piège relevé : l'abonnement Octopush à 0,045 € **n'est pas éligible** à ce volume (plancher 1 000/mois) — il ne le devient qu'en mutualisant au moins quatre salons.
4. **Régime juridique tranché** : un SMS de confirmation de rendez-vous est **transactionnel** — la charte af2m nomme littéralement « rappels de rendez-vous ». Donc **pas de consentement** (exécution du contrat), **pas d'obligation de STOP** (« Le dispositif d'opposition ne concerne pas les Messages de type Fonctionnels »), **aucune restriction horaire**. La réforme du 11/08/2026 vise « démarcher **par téléphone** » : **le SMS n'est pas concerné**. Restent obligatoires : nom commercial en tête du premier message, et mot-clé **CONTACT**.
5. **Numéro d'envoi** : le 09 ordinaire de l'agent ne peut pas émettre ; un **09 NPUEPT** (0937/0938/09390-4) le peut, c'est l'objet créé pour cela. Short code **38xxx** = transactionnel (400 € HT + 100 €/an). Un Sender ID alphanumérique seul rend toute **réponse impossible** — le canal de retour reste le numéro vocal de l'agent.
6. **Trois corrections bloquantes trouvées dans le code existant** : l'index unique sur `booking_id` (`023_sms.sql:28`) **interdit d'avoir une confirmation ET un rappel** sur un même rendez-vous ; la file n'a **aucune péremption** (une confirmation partie trois heures après l'appel ne vérifie plus rien) ; l'abandon après cinq tentatives est **silencieux** au lieu de marquer le rendez-vous « à vérifier ».
7. **Ce qu'on garde** : toute la couche logicielle (file, liste STOP, normalisateur E.164, translittération GSM-7, routes internes qui deviennent l'adaptateur) — seule la sortie change. ⚠️ **À lever avant de signer** : les accusés de remise par webhook d'OVHcloud et Spot-Hit sont non vérifiés (docs en JS ou 522) ; **SMSFactor est le seul à les documenter** (+2,40 €/mois par salon). Et une **décision du Conseil constitutionnel du 25/06/2026** censure des dispositions de L34-5 CPCE, effet différé au 31/10/2027, **contenu inconnu**.

### A4 — Exploitation et sécurité
Détail : `docs/recherche2/A4-exploitation-securite.md` (configuration de référence commentée, section « ce qui ne tient pas dans 1 Go », 11 dettes déclarées).

1. **Le dimensionnement réel** : voir la correction du §1.2 ci-dessus. **1 Go = un appel simultané.** Conséquence directe sur l'offre : soit un VPS par poignée de salons, soit une machine plus grosse dès les premiers clients. À chiffrer avant d'annoncer un prix.
2. **Le point aveugle du renvoi d'appel a une parade, et elle est d'onboarding, pas de SIP.** Slang.ai l'écrit : « Secondary/transfer lines **must NOT have call forwarding enabled** […] it will create a call loop and prevent transfers from connecting », et exige un numéro direct distinct. Et **notre choix du renvoi *sur non-réponse* supprime la boucle par construction** — un poste décroché n'active pas le renvoi.
3. **Les deux vérifications négatives valent plus que les citations** : dans RFC 5806 (`Diversion`, statut **Historic**) le paramètre `limit` n'existe **qu'en ABNF, sans prose normative** ; dans RFC 7044 (`History-Info`, Standards Track) le mot « loop » **n'apparaît jamais**. **Aucun des deux ne définit d'algorithme anti-boucle** — il faut compter soi-même ses propres occurrences. Et Twilio **supprime le `Diversion`** s'il ne correspond pas à un numéro du compte. Le critère juste vient de RFC 3261 §6 : rappeler un numéro *différent* est une **spirale** (normal), rappeler le numéro renvoyé est une **boucle**. Piège Asterisk : `Transfer()` **avant décroché** renvoie un 302 → boucle garantie.
4. **`autoload=no` n'est pas de l'hygiène, c'est chiffré** : **13 des 20 CVE Asterisk du 25/06/2026 sont dans des modules qui n'ont aucune raison d'être chargés** (ooh323, unistim, xmpp, ldap, codec2, app_sms…). Cible **22 LTS ≥ 22.10.1**. Deux CVE **ARI** frappent notre architecture de plein fouet → loopback seul, `password_format=crypt`, ACL par utilisateur. **AMI : ne pas l'activer du tout** (`write=originate` suffit à réécrire `/etc/asterisk/`). Et piège fail2ban : sans `auth_username` dans `endpoint_identifier_order` **et** sans `res_security_log.so` chargé, **aucun SecurityEvent n'est produit** — fail2ban est aveugle sans le savoir.
5. **Quatre durcissements systemd cassent précisément ce produit** : `MemoryDenyWriteExecute=` « is incompatible with JIT execution engines » → tue ONNX et PyTorch (donc Silero et Smart Turn) ; `RestrictRealtime=yes` refuse `SCHED_RR` → gigue audio silencieuse ; `CPUQuota` travaille sur une fenêtre de 100 ms contre des trames RTP de 20 ms ; et le rate limit par défaut (**5 démarrages / 10 s**) bloque le service après une rafale d'OOM. À savoir aussi : `MemoryHigh` **n'invoque jamais** l'OOM killer là où `MemoryMax` le fait, et systemd-oomd est **inopérant sans swap**.
6. **Deux corrections à reporter ailleurs** : `pg_dump` seul **perd les rôles et les GRANT** (`pg_dumpall --globals-only` obligatoire), et **Alembic autogenerate ne détecte ni les contraintes `EXCLUDE` ni les renommages de colonne** — la contrainte d'exclusion sur `bookings` (`docs/04-CONNECTEUR-CRENOLO.md` §4.3) devra donc être **écrite à la main**.

---

### A5 — Conformité opérationnelle
Détail : `docs/recherche2/A5-conformite-operationnelle.md` — **41 livrables** (13 documents, 7 mentions et scripts, 16 réglages produit, 5 arbitrages) et **8 points à faire trancher par un avocat**, par ordre d'urgence.

1. ⚠️ **Cinq références que je lui avais données étaient fausses**, corrigées preuve à l'appui : la loi démarchage est la **n° 2025-594 du 30 juin 2025, art. 13** · **la déclaration Arcep L33-1 n'existe plus** depuis l'ordonnance n° 2021-650 du 26 mai 2021 · le MAN est au **IV de l'art. L44**, en vigueur **depuis le 25 juillet 2023** · les mentions légales relèvent de l'**art. 1-1 de la LCEN** (loi SREN) · et **le « référentiel CNIL du 2 avril 2026 sur les enregistrements d'appels » n'existe pas**.
2. **Le Digital Omnibus IA est adopté** — règlement (UE) **2026/1744 du 8 juillet 2026**, en vigueur le 27 juillet. Il **ne reporte pas** l'article 50, applicable **depuis le 2 août 2026**. Seule transitoire : le **marquage lisible par machine (§2) dû au 2 décembre 2026** pour les systèmes déjà sur le marché.
3. **L'annonce IA pèse sur l'éditeur, pas sur le client.** C'est une obligation **de conception**, non transférable par CGV — donc `annonce_ia: true # non désactivable` est juridiquement juste, et notre refus de le rendre optionnel est fondé. Sanction : 15 M€ / 3 %, **mais plafonnée au plus faible pour une PME** (art. 99 §6) : 3 % du chiffre d'affaires, pas 15 M€.
4. **Le marquage lisible par machine s'applique à une voix TTS temps réel**, et le considérant 133 **ne prévoit aucune exonération pour « impraticable »** : il exige un **dossier technique** documentant l'état de la technique. À ouvrir dès maintenant, pas au 2 décembre.
5. **L'enregistrement systématique est interdit** : la CNIL écrit « ni permanent ni systématique » et « ne peut être déclenché par défaut pour tous les appels ». Notre arbitrage « transcription seule » est validé — et la CNIL érige en **bonne pratique la suppression de l'audio après transcription**.
6. **Deux angles morts plus dangereux que ce que j'avais demandé** : **CPCE L34-5**, dont le champ « système automatisé d'appels » (L32, 32°) est **plus large que L223-1** et touche la prospection B2B **de l'éditeur lui-même** (autorité compétente : la CNIL) ; et **l'offre de téléphonie de détail OVHcloud, contractuellement incompatible** avec le produit — elle interdit robots d'appels, automates, partage SIP, plus d'un utilisateur par compte SIP, et la revente.
7. **Le mot prononcé par l'agent EST la stipulation contraire de L214-1.** Dire « acompte », ou ne rien dire, crée **deux régimes juridiques différents à chaque appel**. La qualification doit donc être verrouillée en réglage commerçant, et le script la répéter mot pour mot.

---

### A9 — Marquage lisible par machine (AI Act art. 50 §2)
Détail : `docs/recherche2/A9-marquage-ai-act.md`. Source centrale : les **lignes directrices officielles C(2026) 5054 final du 20.07.2026**, téléchargées et lues intégralement.

1. ⛔ **L'argument « pas de fichier, donc pas de contenu » est mort.** Le §2 vise « les sorties des systèmes d'IA », sans condition de fichier, et les lignes directrices définissent l'audio comme « a **time-varying signal** » (point 60) et visent **nommément les agents IA** produisant de l'audio perceptible (point 63).
2. **Mais une porte de sortie existe, et elle est conditionnelle** — point (88) : le contenu temps réel éphémère « *without being recorded, stored or disseminated further* » **peut être exempté** si **(a)** le marquage est techniquement infaisable **et (b)** la personne exposée est informée. **Deux conditions cumulatives.** Les exemples cités sont le jeu vidéo et la réalité virtuelle, **pas la téléphonie** : ce n'est pas un blanc-seing, c'est un dossier à constituer.
3. **Le régime de preuve est nommé** — point (148) : qui ne signe pas le Code de bonnes pratiques « *should carry out a **gap analysis*** » comparant ses mesures à celles du Code. **C'est exactement le livrable attendu en cas de contrôle.**
4. ⚠️ **Calendrier, et c'est la mauvaise nouvelle** : le sursis de l'omnibus au 2 décembre 2026 ne vaut **que** pour les systèmes **déjà sur le marché avant le 2 août 2026**, et **jamais** pour l'annonce du §1. **Un agent lancé maintenant n'a aucune transition.**
5. **Aucune publication de 2023 à 2026 ne teste un tatouage neuronal sous codec téléphonique.** Le point le plus proche est Opus à 16 kbit/s en 16 kHz. **AudioSeal** est MIT (code **et** poids), détection en 3,3 ms — mais son **mode streaming est cassé** (issue #105 du 12/09/2026, sans réponse), or notre unité est le chunk de 20 ms.
6. **L'annonce vocale ne satisfait pas le §2** (point 71 : l'extraction doit se faire « *without human intervention* ») — **mais elle devient la seconde condition du point (88)**. Elle change donc de rôle : de solution, elle devient pièce du dossier d'exemption.
7. **Aucun standard IETF de divulgation d'appelant IA n'existe** (Datatracker vérifié). RFC 9795 (*Rich Call Data*) authentifie **l'appelant, pas le contenu**. La **méthode par journalisation** est nommée au considérant 133 et au point (73) : **c'est la seule technique réalisable sans conteneur de fichier.**
8. **Et l'argument « notre fournisseur marque en amont » est factuellement indisponible** : Azure ne tatoue que *personal voice* et *avatar*, pas les voix standard ; SynthID audio est borné à Lyria et NotebookLM, **rien dans Cloud TTS** ; ElevenLabs n'a aucun tatouage et **n'est pas signataire** du Code (Cartesia non plus). **Aucun fournisseur ne documente un marquage sur sortie streaming téléphonique.**
9. **Risque réel** : 15 M€ ou 3 % du CA mondial, **le plus faible pour une PME**. L'exposition financière brute est dérisoire ; **le vrai risque est l'injonction de mise en conformité et le retrait du marché**, et l'entrée la plus probable est **la plainte d'un appelant** (art. 85). **[NV]** L'autorité française compétente n'est pas confirmée (la DGCCRF est *pressentie*, source secondaire).

**Ce qu'on met en place** : annonce vocale **versionnée et journalisée** · journal de provenance au vocabulaire `c2pa.ai-disclosure` · **non-rétention de l'audio comme décision d'architecture écrite** · voix génériques sans clonage · **gap analysis écrite** · question écrite au fournisseur TTS · et un **banc d'essai « canal téléphonique » mesuré** (AudioSeal MIT + ffmpeg, budget zéro) — **la seule pièce qui transforme une opinion en preuve**.
**Ce qu'on assume de ne pas faire** : tatouage en production, manifeste C2PA sur le flux, signature du Code, attente d'une norme harmonisée — chaque renoncement justifié par une citation officielle.

---

### A10 — Extension navigateur
Détail : `docs/recherche2/A10-extension-navigateur.md` · périmètre : `docs/16-EXTENSION-PERIMETRE.md`.

1. ⚠️ **Découverte de méthode** : la page Mozilla qui synthétisait les limitations d'API sur Android **répond 404**. **Il n'existe plus de page listant ce qui marche** — la seule source est `mdn/browser-compat-data`, lue API par API. Mozilla a retiré la synthèse et laissé la donnée brute.
2. **Firefox Android est ouvert** depuis fin 2023 à **toute extension d'AMO marquée compatible** — mais **aucun sideload** : « It will not be possible to install unsigned .xpi files ».
3. **`identity` est absent d'Android, API et permission comprises.** Donc `launchWebAuthFlow` est hors jeu : le seul schéma valable sur les trois cibles est un **jeton d'appairage**. **À écrire en premier.**
4. **Pas d'icône en barre d'outils sur Android** : l'extension est **une entrée du menu ⋮**, à deux appuis. Trois surfaces seulement — popup, options, onglet.
5. **« Appel en cours » est impossible sur Android** : l'arrière-plan dort et **rien ne tourne si Firefox est fermé**. « Rendez-vous pris » reste possible.
6. **`offscreen` est confirmé hors sujet** (l'audio ne traverse jamais le navigateur), et les contraintes d'event page Firefox **coïncident avec celles du service worker Chrome** : **un seul arrière-plan sert les trois**.
7. **Aucun des trois frameworks (WXT, Plasmo, CRXJS) ne déclare Firefox Android** — WXT sort du **MV2 par défaut** pour Firefox. Retenu : **Vite plus un script de manifestes**.
8. **Effort** : socle 70 %, Chrome +1 j, Firefox desktop +1 j, **Firefox Android +3 à 5 j**, publication +2 à 3 j.

---

### A11 — Adaptateurs universels : **aucun agenda tiers ne garantit la non-superposition**
Détail : `docs/recherche2/A11-adaptateurs-universels.md` (27 sources officielles).

1. **Google `events.insert` n'empêche rien** : aucune détection de conflit, **aucune clé d'idempotence**, rien sur le chevauchement. **Deux insertions concurrentes sur le même créneau réussissent toutes les deux.** L'ETag tient dans **une seule phrase** de toute la documentation : le contrôle optimiste y est un **comportement de fait, non contractualisé**.
2. **Microsoft Graph** : rien sur le conflit non plus, **mais `transactionId` existe** — une vraie clé d'idempotence. Elle règle **le rejeu, pas la concurrence**. `getSchedule` est une photographie sans durée de validité.
3. **CalDAV** est le seul à traiter la concurrence sérieusement — **et à dire que le chevauchement n'est pas son sujet** : `If-None-Match: *` protège d'une collision de **nom de fichier**, `no-uid-conflict` porte sur **l'UID**, et le free-busy §7.10 indique **« Preconditions: None. »** La RFC **autorise** des périodes occupées qui se recouvrent.
4. **L'explication tient en une ligne** : **aucune ressource serveur ne représente « le créneau ». On ne verrouille que ce qui existe.** Cal.com peut réserver un créneau (`POST /v2/slots/reservations`, 5 min) **parce qu'il possède sa base**.
5. **Calendly** écrit sans interface, mais ses réponses documentées **n'incluent aucun `409`** alors que la spécification en définit ailleurs : **créneau pris et erreur de payload deviennent indistinguables**.
6. **Les passerelles sont hors jeu** dans le temps d'un appel : Zapier **15 min à 1 min** selon le plan, Make 15 min. **Seul n8n auto-hébergé** peut tenir un tour de parole — à mesurer.
7. **Sur sept logiciels verticaux, un seul publie une API d'écriture** : **Phorest**. Fresha, Booksy, Treatwell, Planity, Zenchef, Doctolib : aucune porte publique.
8. **Conséquence produit** : la phrase autorisée à l'appelant devient **une donnée de configuration du connecteur, appliquée dans le code** — « c'est réservé » en N0/N1, « **c'est enregistré** » en N2, « je transmets » en N3, « j'ai noté » en N4. **Jamais confiée au prompt.**

---

## 6. Dette de recherche (à ne pas présenter comme acquis)

- ~~Tout le volet juridique est en source secondaire~~ → **levé par A5**, qui a atteint Légifrance et EUR-Lex par navigateur réel. ⚠️ Et qui a corrigé cinq références fausses, dont **le « référentiel CNIL du 2 avril 2026 sur les enregistrements d'appels », qui n'existe pas** : c'est le référentiel *durées de conservation RH*, dont une rubrique traite l'écoute et l'enregistrement (audio 6 mois, documents d'analyse 1 an). Restent inaccessibles : DGCCRF, Judilibre, CanLII — 23 points listés comme trous dans A5 §11.
- **Aucun WER français en bande téléphonique 8 kHz n'est publié** par qui que ce soit. Première mesure à faire nous-mêmes.
- **Aucun RTF CPU officiel pour NeMo-Speech.cpp ni pour Piper.**
- G2 et Capterra bloqués (HTTP 403) ; **aucune plainte francophone sourcée** sur la qualité d'un callbot (trou de données, pas absence de problème).
- Divergence non résolue sur le prix du numéro Twilio FR (1,35 $ vs 1,15 $ selon la page officielle consultée).
- Équivalent Firefox à `chrome.offscreen` (audio/WebRTC en arrière-plan) : **introuvable** — risque non levé pour une extension cross-browser.
- Jurisprudence Air Canada (responsabilité du donneur d'ordre pour les réponses de son bot) : citée par un utilisateur, **non vérifiée**.
