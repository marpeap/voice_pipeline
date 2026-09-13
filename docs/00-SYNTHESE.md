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
2. **Mais l'orchestration tient largement.** LiveKit mesure **2,8 Go pour 30 sessions simultanées** (~90 Mo/session) quand l'inférence est déportée. **Le VPS porte la téléphonie et l'agent ; l'inférence sort de la machine.** C'est l'arbitrage central. [F+H, R1 §1.2]
3. **Le tout-OSS coûte plus cher que l'hybride avant 17 100 min/mois.** Coût calculé par minute d'appel : tout-commercial **0,0894 $**, hybride auto-hébergé **0,0306 $**, tout-OSS sur GPU loué **0,3628 $** à 1 000 min/mois mais **0,0276 $** à 20 000 min/mois. On paie un GPU allumé, pas des minutes. [F, R2]
4. **La contrainte française n'est pas le prix, c'est le numéro.** Un agent IA **sortant** exige un numéro « Polyvalent Vérifié » (`0162 29`, `09 48 35`, `09 48 19`) avec adresse FR et K-bis ; aucun essai gratuit ne le couvre. Pour l'entrant, seuls **Telnyx** (09 à 0,50 $/mois, KYC ~72 h, portage par API) et **OVHcloud** (1 € HT, API de commande complète) ont API + grille publique. Plivo est disqualifié (entrants FR « Not Supported »). [F, R2, R3 §1]
5. **L'onboarding téléphonique tient en moins de 2 minutes** — renvoi d'appel **sur non-réponse** avec codes MMI pré-remplis par opérateur, à condition de **pré-acheter les numéros 09 par lots** pour sortir le KYC du parcours client. Total d'onboarding chronométré : **8 à 15 minutes**. [R, R3 §7]
6. **L'agent doit fonctionner sans connaître le numéro de l'appelant.** L'ARCEP recommande explicitement le masquage du CLI quand l'authentification MAN ne suit pas un renvoi. Contrainte de conception, pas cas limite — et elle entre en tension avec le cloisonnement par numéro appelant (§4 ci-dessous). [F, R3 §2]
7. **Annoncer l'IA est obligatoire et rentable.** AI Act art. 50 §1 **applicable depuis le 02/08/2026** (non repoussé par l'omnibus numérique). Et le verbatim le plus net de toute la collecte d'avis dit la même chose : *« Complaints basically stopped once we made it announce it was automated in the first breath. People forgive a robot for being a robot, they don't forgive it for pretending. »* [F + V-Reddit, R3 §5, R4 §C.2]
8. **Le démarchage est en opt-in depuis le 11/08/2026**, Bloctel supprimé. Toute fonction d'appel **sortant** doit être bornée au contrat en cours (confirmation, rappel de RDV existant, report après annulation). Vendre « l'IA rappelle vos anciens clients » à un commerçant français, c'est lui vendre un risque juridique. [T→à valider juridiquement, R3 §5, R4 §3.3]
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
| Numéro / trunk | **Telnyx** principal, **OVHcloud** second, **Zadarma** (2 €/mois, entrants gratuits, 3 canaux) pour les essais | — | Seuls avec API d'achat FR + grille publique |
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

| # | Décision | Options | Enjeu |
|---|---|---|---|
| D1 | **Positionnement** | (a) greffon Crenolo d'abord, vertical beauté ; (b) produit autonome horizontal ; (c) les deux via le même cœur | Détermine l'ordre de construction, pas l'architecture (le cœur est le même) |
| D2 | **Bord téléphonique phase 1** | (a) Asterisk auto-hébergé ; (b) media streams d'un fournisseur (Telnyx/Twilio) | (a) = moins cher, plus d'exploitation ; (b) = démarrage en jours, dépendance et coût/min |
| D3 | **Budget d'inférence** | hybride ~0,031 $/min | À 1 000 min/mois ≈ 31 $ ; le tout-OSS ne devient rentable qu'au-delà de ~17 100 min/mois |
| D4 | **Enregistrement audio** | off par défaut (transcription seule) | Recommandé : rétention CNIL 6 mois max, et l'audio est un risque sans usage prouvé |
| D5 | **Appels sortants** | bornés au contrat en cours | Hors contrat = démarchage, opt-in obligatoire depuis le 11/08/2026 |

---

## 6. Dette de recherche (à ne pas présenter comme acquis)

- **Tout le volet juridique est en source secondaire** : Légifrance, CNIL et EUR-Lex étaient inaccessibles depuis l'environnement de recherche. AI Act art. 50, décret démarchage du 25/07/2026, référentiel CNIL du 02/04/2026 : **à relire à la source avant tout engagement client**.
- **Aucun WER français en bande téléphonique 8 kHz n'est publié** par qui que ce soit. Première mesure à faire nous-mêmes.
- **Aucun RTF CPU officiel pour NeMo-Speech.cpp ni pour Piper.**
- G2 et Capterra bloqués (HTTP 403) ; **aucune plainte francophone sourcée** sur la qualité d'un callbot (trou de données, pas absence de problème).
- Divergence non résolue sur le prix du numéro Twilio FR (1,35 $ vs 1,15 $ selon la page officielle consultée).
- Équivalent Firefox à `chrome.offscreen` (audio/WebRTC en arrière-plan) : **introuvable** — risque non levé pour une extension cross-browser.
- Jurisprudence Air Canada (responsabilité du donneur d'ordre pour les réponses de son bot) : citée par un utilisateur, **non vérifiée**.
