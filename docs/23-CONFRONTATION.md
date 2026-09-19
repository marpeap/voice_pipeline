# Confrontation — ce que le produit n'a pas, et ce qu'on en fait

> **Pourquoi ce document existe.** Adnan a posé la règle le 18/09 : *« tu ne te fais pas confiance pour juger si le produit est fini »*. Donc, plutôt que de décréter la fin, on cherche ce qu'un produit professionnel de cette catégorie comporte, on compare **point par point**, on écrit l'écart, et on corrige.
>
> Recherches faites le **19/09/2026**. Chaque ligne cite ce qui l'a produite.

---

## 1. Les fonctions attendues d'un agent vocal professionnel

| Attendu par le marché | Chez nous | Décision |
|---|---|---|
| **Interruption (barge-in)** — l'agent se tait quand l'appelant reprend la parole | ❌ **absent** | ✅ **corrigé le 19/09** : garde de durée minimale à 240 ms, ce qui reste est jeté, `interruptions` au journal |
| **Latence bout en bout ~600 ms** | ✅ 624 ms p50 mesurés (mesure 14) | conforme, et mesuré plutôt qu'annoncé |
| **Transfert vers un humain** | ⚠️ décidé mais **pas exécuté** : le produit dit « je vous passe quelqu'un » sans signal au bord téléphonique | ✅ **corrigé** : signal de transfert explicite, vérifiable |
| **Preuve de l'annonce** — « documented so it can be proven » | ⚠️ l'annonce est prononcée, mais rien ne l'atteste | ✅ **corrigé** : horodatage + formulation au journal d'appel |
| **Détection de répondeur** (voicemail detection) | ❌ absent | **hors périmètre, assumé** : elle sert aux appels **sortants**. Le produit est entrant. À rouvrir le jour où un rappel automatique existe |
| **Fonctions / webhooks vers un système tiers** | ⚠️ le contrat de connecteur est spécifié (`docs/04`), pas codé | **écart ouvert**, prochaine tâche |
| **Multilingue** | ❌ français seulement | **limitation assumée et écrite** : l'AI Act demande l'annonce « dans la langue de la conversation ». Un appelant qui ne parle pas français doit donc être **transféré**, pas servi à moitié |

## 2. Ce que la conformité européenne exige réellement

Vérifié le 19/09 sur les textes et sur des synthèses à jour :

| Obligation | Ce que ça veut dire pour nous | État |
|---|---|---|
| **AI Act art. 50**, applicable **depuis le 02/08/2026** | annoncer de vive voix qu'il s'agit d'une IA, **à chaque nouvelle interaction**, **dans la langue de la conversation**, et **de façon prouvable** | ✅ annonce non désactivable, vérifiée sur la phrase réelle ; ✅ preuve au journal ; ⚠️ une seule langue |
| Sanction associée | jusqu'à **15 M€ ou 3 % du chiffre d'affaires mondial** | ce n'est pas un détail de confort : c'est pourquoi l'annonce n'est pas un réglage |
| **Enregistrement des appels — opt-in en France depuis août 2026** | il faudrait un consentement préalable pour enregistrer | ✅ **sans objet chez nous : on n'enregistre pas.** L'audio est effacé dès que la transcription existe, et un test le vérifie |
| **ePrivacy art. 13(1)** — consentement préalable pour les **systèmes d'appel automatisés** | concerne les appels **sortants** | **hors périmètre aujourd'hui**, et à rouvrir avant tout rappel automatique. Écrit ici pour que personne ne l'apprenne après |
| RGPD art. 30 — registre des traitements | un registre tenu à part se périme | ✅ **dérivé de la configuration** du service |
| RGPD art. 28 — sous-traitance | un modèle d'accord est nécessaire | ✅ écrit (`docs/18`) |

## 3. Ce qui reste ouvert, et qui ne se règle pas en codant

1. **Aucun appel réel n'a jamais été passé.** Tout est mesuré sur corpus synthétique et sur des simulations. C'est la limite la plus importante du dossier, elle est écrite partout, et elle ne se lève qu'avec un numéro et un salon.
2. **Le multilingue.** Servir un appelant en anglais à moitié serait pire que le transférer.
3. **Le connecteur vers un logiciel tiers** : spécifié, pas codé.

---

**Ce document se relit à chaque fois que le produit semble fini.** La première confrontation a trouvé une fonction majeure absente — l'interruption — dans un produit que je croyais complet à 227 tests verts. C'est exactement ce qu'Adnan avait prévu en écrivant la règle.

---

# Deuxième passe — 19/09, après la construction du bord téléphonique

## 4. Ce que la vérification d'avant-livraison a trouvé

Le point le plus important de tout ce document, et il n'a été trouvé ni par un test ni par une recherche, mais en appliquant la règle « **aucune affirmation sans preuve fraîche** » :

> **Le produit n'avait aucun point d'entrée.** Neuf modules, 260 tests verts, une porte de non-régression ouverte, une démonstration qui tourne — et **rien qui écoute**. Un standard téléphonique qui ne peut pas recevoir de connexion n'est pas livrable, quel que soit le nombre de tests.

C'est l'angle mort classique : chaque pièce était vérifiée, l'assemblage était vérifié, et personne n'avait vérifié qu'on pouvait **brancher le tout**. Corrigé — le serveur existe, et ses tests ouvrent un vrai socket au lieu de simuler le protocole.

## 5. Ce que la recherche sur Asterisk a changé

| Ce qu'on a relevé | Ce qu'on en a fait |
|---|---|
| **Restreindre les codecs** (ulaw, alaw, slin16) évite les problèmes de négociation, **première cause d'appels qui aboutissent muets** | `deploiement/pjsip.conf` : `disallow=all` puis deux codecs, pas plus |
| Le serveur reçoit des trames de **320 octets, 20 ms, 8 kHz** | c'est déjà ce que la session émet — confirmation, pas correction |
| `direct_media` doit être désactivé | sans quoi l'audio contourne Asterisk et AudioSocket ne voit rien |
| Asterisk **18 ou plus récent**, `app_audiosocket` chargé | écrit dans le plan de numérotation |
| Objectif de bout en bout : **moins de deux secondes** entre la fin de la phrase de l'appelant et le début de la réponse | mesuré chez nous à **624 ms p50** (mesure 14) — trois fois mieux que la cible du marché |

## 6. Ce qui reste, honnêtement

1. **Aucun appel réel.** C'est toujours la limite principale. Tout le reste est prêt à la recevoir.
2. **Le moteur de transcription n'est pas branché** au serveur : le service démarre, décroche et répond, mais `transcrire` rend une chaîne vide tant qu'un STT n'est pas configuré. C'est volontaire — cela permet de **vérifier un déploiement avant d'avoir un STT** — et c'est écrit ici pour que personne ne le découvre en production.
3. **Le multilingue** reste une limitation assumée : détection prudente, puis transfert.
