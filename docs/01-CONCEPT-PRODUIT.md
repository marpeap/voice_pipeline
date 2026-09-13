# Passe de brainstorming n°1 — Concept produit

> Aucune ligne de code. Ce document fixe **quoi**, pour **qui**, et **ce que le produit refuse de faire**.
> Tout ce qui est chiffré ici vient de `docs/00-SYNTHESE.md` et des six rapports.

---

## 1. La phrase

**Un standard téléphonique IA en français, qui ne se configure pas : il lit déjà le logiciel métier, et le commerçant ne fait que répondre à des questions.**

Et sa contrepartie technique : **un greffon**, pas un produit monolithique — le même cœur se branche sur Crenolo, Inkra, Kompagnon ou un logiciel tiers via un connecteur de quelques centaines de lignes.

---

## 2. Les trois utilisateurs, et ce qu'ils veulent réellement

| Utilisateur | Ce qu'il veut | Ce qu'il ne fera jamais |
|---|---|---|
| **L'appelant** (client du salon) | Être compris, obtenir son créneau, **ou parler à un humain tout de suite** | Tolérer un robot qui se fait passer pour une humaine, ou qui discute sa demande de transfert |
| **Le commerçant** (gérant du salon) | Ne plus rater d'appels, une facture prévisible, savoir ce que le robot a raté hier | Écrire un prompt. Ni un paragraphe, ni une phrase |
| **L'éditeur hôte** (Crenolo, Inkra, un tiers) | Ajouter « réponse téléphonique IA » à son produit sans devenir éditeur de téléphonie | Maintenir un fork de notre code |

Le troisième utilisateur est celui qui rend le projet réutilisable. Il n'existe chez aucun concurrent étudié : tous vendent en direct au commerçant.

---

## 3. Le parcours du commerçant, en quatre écrans

Ordre imposé par la convergence Vapi / Retell / ElevenLabs (`R5 §5.3`) : **identité → contenu → configuration → provisionnement coûteux en dernier, et test avant provisionnement.**

### Écran 1 — Rien à saisir (import)
Le connecteur de l'hôte remonte : prestations, durées réelles, tarifs, équipe, horaires, règles d'annulation, **et l'historique des rendez-vous**. L'écran est une **validation**, pas une saisie : « voici ce qu'on a compris de votre activité, corrigez ce qui cloche ».

> C'est le patron 3 de `R4 §B.1` (« le logiciel métier sait déjà », Fresha : *« There is no separate configuration »*) **poussé au-delà de Fresha**, qui lit le catalogue en temps réel mais **pas l'historique**. Personne ne le fait. [R4 §B.2 n°1]

**Ce que l'historique donne et qu'un questionnaire ne donnera jamais** : la durée réelle d'une prestation (pas la durée théorique du catalogue), les associations fréquentes (« couleur + coupe »), les créneaux réellement vendus, les prestations mortes, le taux d'annulation par type, les noms de famille des clients existants — qui alimentent directement le **keyterm set** du STT (20–50 termes, `R6 §3.4a`), c'est-à-dire la précision de reconnaissance.

### Écran 2 — Le questionnaire sectoriel pré-rempli
Les 15 à 20 questions qu'un client pose réellement, **déjà répondues par défaut** à partir de l'import. Le gérant corrige ce qui cloche. Questions à choix (issues d'un pack JSON sectoriel) + texte libre là où c'est nécessaire.

C'est le patron 2 de `R4 §B.1` **sans l'humain du patron 5** : Slang vend un onboarding téléphonique de 30 minutes à 399-599 $/site/mois, Dialzara vend un formulaire à 29 $. **Le créneau vide est au milieu** : un questionnaire assez fin pour se passer d'un humain, assez guidé pour qu'un coiffeur le finisse seul. Notre différenciation ne peut pas être « on fait mieux l'appel d'onboarding » — elle doit être **« il n'y a pas d'appel d'onboarding »** (à 94,95 €/mois, prix Fresha, 30 minutes de téléphone mangent plusieurs mois de marge).

### Écran 3 — Les règles de la maison, en cases à cocher
Délai minimum de report, acompte, prestations à praticien imposé, créneaux interdits, **seuils d'escalade**, horaires de transfert, mots qui déclenchent une urgence.

> `R4 §B.2 n°4` : partout ailleurs, les politiques métier sont traitées comme **du texte libre**, jamais comme des règles. Fresha dit « following your business's cancellation policies » sans décrire l'objet de configuration. Ces règles méritent **des champs**, pas un paragraphe — parce qu'un champ est vérifiable, testable, et affichable dans une transcription.

### Écran 4 — « Appelez votre agent »
Un bouton, un numéro d'essai, l'agent décroche. Transcription immédiate. **Correction en un clic depuis la transcription.** Et seulement après : le numéro définitif et le renvoi d'appel.

> Deux trous du marché comblés d'un coup (`R4 §C.15` n°2 et `§B.2` n°3) : presque personne ne fait tester avant la bascule, et **personne** ne documente de boucle de correction — alors que les exploitants la réclament mot pour mot : *« a voice agent still needs maintenance after it goes live. We need to analyze the calls and adjust as it goes »*. Ils ne veulent pas écrire un prompt : ils veulent **corriger un appel raté**.

**Cible : agent qui décroche en 5 à 7 questions**, puis paliers d'enrichissement facultatifs. Le commerçant doit entendre son agent parler avant d'avoir tout rempli — c'est le seul argument qui résiste à la fatigue de formulaire (`R5 §5.4`).

---

## 4. Les paliers du questionnaire

Calqués sur les cinq sections que Retell documente pour ses prompts (`R5 §4.1`), pour que **chaque palier remplisse une section du fichier `.md`** et qu'une section vide reste un fichier valide.

| Palier | Contenu | Effet audible immédiat | Section `.md` |
|---|---|---|---|
| 0 — Identité | Nom, métier, ville, langue, voix, formule d'accueil | **L'agent décroche et se présente** | `Identity` |
| 1 — Disponibilité | Horaires, fermetures, délai de RDV | L'agent sait *quand* proposer | `Availability` |
| 2 — Prestations | Liste, durées, tarifs (pré-remplis par l'import) | L'agent sait *quoi* proposer | `Services` |
| 3 — Ton et garde-fous | Vouvoiement, formules, interdits | L'agent parle comme la maison | `Style Guardrails` |
| 4 — Cas limites | FAQ, annulations, urgences, escalade | L'agent ne se bloque plus | `Objection Handling` |

Règles de conception du questionnaire, toutes sourcées dans `R5 §5` :
- **Une question par écran**, avec branchements — un restaurant et un salon ne répondent pas aux mêmes questions.
- **Jamais plus de deux niveaux** de divulgation progressive (NN/g).
- **Sauvegarde serveur après chaque réponse**, pas à la fin. `localStorage` ne suffit pas : le gérant commence au comptoir sur son téléphone et finit au bureau le soir — c'est le cas nominal, pas l'exception.
- **Aucun champ optionnel dans un palier** : c'est le **palier entier** qui est optionnel. On remplace un long formulaire majoritairement facultatif par une suite de courts formulaires entièrement obligatoires.
- **Pas de mot de passe au milieu du parcours** : c'est statistiquement le champ le plus coûteux (Zuko, 1 362 formulaires : **10,50 %** d'abandon moyen, 7,2 s de saisie, contre 6,41 % pour l'e-mail). Lien magique ou code à usage unique.
- **Score de complétude affiché en permanence**, qui dit *ce que l'agent ne saura pas faire* tant que ce n'est pas rempli — pas un pourcentage abstrait.

**Packs sectoriels** (un JSON par métier) : coiffure/beauté, restaurant, artisan-dépannage, santé, auto. Chaque pack porte questions, valeurs par défaut, vocabulaire (keyterms), FAQ type, règles d'escalade recommandées. Dialzara en a fait un actif marketing en les publiant **avant achat** (`R4 §B.1` patron 6) : le prospect voit le travail déjà fait. À copier.

---

## 5. Le fichier de configuration : `memoire.md`

Ce que le commerçant ne verra jamais, et que le système produit pour lui.

```markdown
---
# Ce que la machine lit — régénéré par le questionnaire, jamais à la main
tenant: salon-nguyen
langue: fr-FR
voix: fr_FR-siwis-medium
annonce_ia: true          # non désactivable (AI Act art. 50)
horaires: { mar-ven: "09:00-19:00", sam: "09:00-18:00" }
escalade: { mots_urgence: ["brûlure", "allergie"], transfert: "+336…", hors_horaires: "message+sms" }
keyterms: ["balayage", "Karim", "Nguyen", …]   # 20–50 max
---

## Ton
On vouvoie. On ne promet jamais un créneau avant de l'avoir vérifié.

## Cas particuliers
Pas de balayage sur cheveux décolorés le samedi.
La coloriste ne travaille pas le lundi.
Une permanente bloque deux heures.
```

**Le savoir qui compte n'est écrit nulle part sur le site du salon** — c'est pour ça que le scraping de site web, que pratiquent Rosie et RingCentral, est un **accélérateur d'amorçage et pas une base de connaissance** (`R4 §B.1`, limite documentée : quand l'appelant sort du site, Rosie « approximates from site content or defaults to taking a message »).

**Trois règles dures**, tirées de `R5 §4.2` :
1. **Le frontmatter est régénéré, le corps Markdown n'est jamais reparsé.** On extrait le bloc par délimiteurs, on le remplace, on reconcatène le corps **octet pour octet**. `mdast-util-to-markdown` l'écrit lui-même : « there are several cases where that is impossible », et ses défauts normalisent activement le style (`-` → `*`, `~~~` → backticks…). Côté Python, `mdformat` réécrit délibérément.
2. **MDX est exclu**, sur la foi de sa propre documentation : *« Do not let random people from the internet write MDX »*. Un commerçant qui décrit sa politique d'annulation est exactement la personne visée.
3. **Un fichier reste valide même vide** (convention AGENTS.md, 60 000+ projets : aucun champ obligatoire).

**Pas de RAG au départ.** Une base de connaissance de commerçant pèse quelques dizaines de milliers de caractères ; l'industrie place le seuil du passage obligatoire au RAG vers **300 000 caractères** (ElevenLabs) et recommande des fichiers **sous 300 Ko** (Vapi). Le fichier entier va dans le prompt système, **avec prompt caching** — parce que la latence de récupération n'est pas un terme séparé dans la formule de latence : elle est absorbée dans le TTFT, donc **chaque milliseconde de RAG est une milliseconde de silence**.

---

## 6. Ce que l'agent fait, par niveau

**Table-stakes — sans ça le produit n'existe pas** (`R4 §A`) : décrocher 24/7 · mise en service **par renvoi d'appel, sans migration de numéro** · FAQ · **prendre un RDV dans l'agenda réel** · transférer à un humain · prendre un message notifié · transcription · résumé lisible en dix secondes · appels simultanés · accueil personnalisable · **annonce « vous parlez à une IA »**.

**Différenciants choisis** : annuler/déplacer pendant l'appel · politiques du salon comme **objets configurés** · SMS avec lien de réservation · transfert **chaud avec résumé** · filtrage spam **non facturé** · alertes par sujet (réclamation, urgence, VIP) · exposition du **taux de résolution et du taux de passage à l'humain**.

**Nos paris, peu coûteux et absents du marché** : apprentissage sur l'historique · **correction en un clic depuis une transcription ratée** · essai avant bascule · **publication du taux d'impasse** · conformité AI Act vendue comme fonctionnalité.

**Ce que le produit refuse de faire, explicitement :**
- **Pas de voix déguisée en humaine**, pas de prénom humain sans mention, **pas de bruit de call-center factice** (un utilisateur note lui-même que cette pratique tombe désormais sous le coup de l'AI Act).
- **Pas de prospection sortante.** Sortant borné au contrat en cours : confirmation, rappel d'un RDV existant, report après annulation (modèle Zenoti).
- **Pas de collecte d'e-mail par la voix.**
- **Pas de commande / paiement dans l'appel** au premier lot. Le seul retour d'exploitant positif et nommé de toute la collecte utilisait l'agent **pour la réservation uniquement, jamais pour les commandes**.
- **Pas d'enregistrement audio par défaut** — transcription seule (modèle Fresha : transcription par défaut, enregistrement en option).

---

## 7. Modèle économique

**Ne pas facturer à la minute.** C'est la plainte n°1 des exploitants, documentée sur Trustpilot chez Ruby (*« they charge by the minute »*, *« the company charges you for the dropped calls »*) et aggravée par le spam qui consomme le quota. Goodcall a démontré l'alternative : **minutes illimitées, facturation au client unique** (100/250/500 par mois puis 0,50 $ par client supplémentaire).

Notre grille de travail (à valider) :
- **Forfait par établissement**, minutes non comptées, avec un plafond d'appels uniques par mois.
- **Le spam ne compte pas** — filtré et non facturé. C'est une fonction de facturation autant que de confort.
- **Côté éditeur hôte** (Crenolo, tiers) : revente en marque blanche, part de revenu, ou licence par site.
- Repère de coût : hybride à **0,0306 $/min** ⇒ un salon à 1 000 min/mois coûte ~**31 $** d'inférence + téléphonie. Repère de marché : Fresha **94,95 €/site**, Tala 29 €, Sylen 49 €, Elio 79 €, Vokai 299 € + 0,29 €/min.

---

## 8. Les KPI que le produit affiche (et ceux qu'il refuse d'afficher)

| Affiché | Pourquoi |
|---|---|
| **Taux de confirmation orpheline** (cible **0**) | L'échec silencieux — « c'est noté, à mardi ! » et rien en base — est le pire mode de défaillance : personne ne le détecte avant le jour J |
| **Taux d'impasse** (le client a demandé un humain et ne l'a pas eu) | Personne ne le publie ; c'est le chiffre que le gérant veut vraiment |
| Taux de passage à l'humain, par motif | Le *handover rate* de Zenoti est l'indicateur le plus mûr vu dans le panel |
| Silence perçu p50 / p95 | En percentiles, jamais en moyenne |
| RDV pris sans intervention humaine | La valeur, en une ligne |
| Appels de spam filtrés (et non facturés) | Preuve visible que la facture est protégée |

**Refusé** : le seul taux de containment sans son inverse, et toute latence annoncée en moyenne. Un benchmark ouvert de 499 appels réels donne des **p50 de 1,3 à 1,7 s** chez Bland, Vapi, Retell, Telnyx, ElevenLabs — pendant que des éditeurs annoncent « < 420 ms ». Les deux chiffres ne mesurent pas la même chose ; nous publierons la définition avec le chiffre.

---

## 9. Les trois greffes maison

| Hôte | Ce que le connecteur expose | Ce que l'agent apporte |
|---|---|---|
| **Crenolo** (réservation, concurrent de Planity) | Catalogue, équipe, créneaux, RDV, politiques, historique | Le cas nominal : réception d'appels d'un salon. **Planity n'a rien** [F] |
| **Inkra** (notes) | Recherche dans les notes, création de note | Dictée téléphonique, prise de message structurée, rappel de contenu par téléphone |
| **Kompagnon** (nouveau nom de **M-Campaign**, agent Google Ads — FastAPI + Next.js, `marpeap/campaign`) | Campagnes actives, mots-clés, budgets, numéro de suivi par campagne ; import de conversion d'appel vers Google Ads | **Le chaînon manquant de la publicité au téléphone** : l'annonce Google génère un appel, l'agent décroche, **qualifie**, et **renvoie l'appel comme conversion** dans Google Ads — l'enchère apprend enfin sur les appels, pas seulement sur les formulaires. C'est ce que fait uh!ive (ex-Allo-Media) pour les grands comptes, jamais pour une TPE |

**Le connecteur est le contrat.** Un hôte fournit : un *profil d'établissement*, des *outils* (chercher un créneau, réserver, annuler, transférer, laisser un message), un *flux d'import*, et reçoit des *webhooks*. Tout le reste — téléphonie, pipeline audio, questionnaire, mémoire, observabilité — est à nous et ne se duplique pas. Détail dans `docs/02-ARCHITECTURE.md`.

---

## 10. Ce que cette passe laisse ouvert

- ~~**D1 positionnement**~~ → **tranché le 13/09/2026 : greffon Crenolo d'abord.**
- ~~**Kompagnon**~~ → **c'est M-Campaign renommé** (agent Google Ads). Greffe de niveau 1 au lot L6, avec la conversion d'appel comme valeur propre.
- **Nom du produit** et voix de marque — non traités ici volontairement.
- Une question ouverte née de la réponse Kompagnon : **le suivi d'appel publicitaire** (un numéro par campagne, attribution, conversion renvoyée à Google Ads) est-il une fonctionnalité du greffon vocal, ou un produit à part qui le consomme ? Il change la façon dont on alloue les numéros — un par établissement, ou un par campagne.
- La grille tarifaire précise, une fois le coût réel mesuré sur 100 appels et non calculé.
