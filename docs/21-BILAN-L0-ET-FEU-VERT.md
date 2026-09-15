# Bilan du lot L0 — ce qui est prouvé, ce qui est décidé, et ce qu'il reste à accepter

> **C'est le document d'arrêt avant la première ligne de code produit.** Vingt mesures, vingt et un documents de conception, seize rapports de recherche. Ce qui suit dit ce qui est établi, ce qui est tranché, ce qu'on assume de ne pas savoir, et dans quel ordre on construit.

---

## 1. Ce que les mesures ont prouvé

**Sur la chaîne technique**

| Fait | Conséquence |
|---|---|
| **Un tour de parole complet tient en 624 ms** (STT 168 + LLM 165 + TTS 249) | Le budget est atteignable **dès la première version**, sans optimisation exotique |
| **Toute la variance vient du LLM** (935 ms p90, 8 751 ms au pire) — les étages locaux sont stables à ±30 ms | Délai de garde, connexions maintenues, second fournisseur en repli |
| **Une connexion rouverte coûte 2 040 ms, gardée 378 ms** | Réserve de connexions ouverte au démarrage. Le premier levier de latence est gratuit |
| **Le TTS fixe la capacité, en latence** : 162 ms à 1 flux, 614 ms à 6 | ~10 appels simultanés par machine, soit **~60 salons**. Une machine pleine a l'air inactive |
| **Le STT ne limite rien** : 11 Mo par flux, RTF 0,27 à 8 flux | Le poste mémoire, c'est le TTS (~150 Mo par synthèse) |

**Sur la qualité d'écoute**

| Fait | Conséquence |
|---|---|
| **La bande téléphonique coûte ×1,03 à un gros modèle distant, ×1,30 à un petit modèle local** | La sensibilité se mesure par candidat, elle ne se déduit pas |
| **Au point de fonctionnement réel (10-15 dB), le classement des moteurs s'inverse** | Un moteur ne se choisit jamais sur de l'audio propre |
| **Le bruit est du côté de l'appelant** (rue, voiture, haut-parleur) | Le WER à attendre est **20-27 %**, pas 9-11 % |
| **4 numéros sur 10 perdus, identiquement en 16 et 8 kHz** | La perte vient de **la grammaire française**, pas du canal |
| **Les moteurs locaux rendent des mots, le distant rend des chiffres** | Auto-héberger le STT, c'est s'engager à écrire toute la grammaire des nombres |
| **Un moteur streaming perd un premier mot sur quatre** | Flux ouvert et VAD à pré-roll **avant** que l'appelant parle |

**Sur le comportement de l'agent**

| Fait | Conséquence |
|---|---|
| **Un agent « prompt seul » faute sur 6 tours sur 12** : créneaux inventés, faits inventés, **2 confirmations orphelines** | L'architecture à machine à états n'est pas un luxe |
| **Avec garde-fous : 0 faute — et 0 réservation** | La rigueur ne remplace pas l'écoute, elle la révèle |
| **La boucle de clarification ferme en 2,2 tours** | La rigueur coûte **un tour**, moins d'une seconde |
| **Un appelant têtu déjoue les règles locales par alternance** | Compteur de progrès : **il compte des valeurs neuves**, pas des tours |
| **L'annonce légale et la relecture du numéro survivent au canal** | Conformité art. 50 §1 vérifiée **sur l'audio**, pas sur le prompt |
| **Le quantième est le mot le plus fragile que l'agent prononce** | Date énoncée jour + quantième + mois ; jamais deux horaires proches dans une phrase |

---

## 2. La pile retenue, et pourquoi

| Brique | Choix | Raison, mesurée |
|---|---|---|
| **STT** | **API distante**, durablement | ×1,03 sous bruit contre ×1,30, sortie en chiffres, numéros conservés (mesures 9, 10, 12) |
| **TTS** | **Piper local**, voix `fr_FR-siwis-medium`, **en flux** | 162 ms au premier fragment, service HTTP séparé (GPL-3.0) |
| **LLM** | **API, nom et paramètres en configuration**, second fournisseur en repli | Catalogue modifié 3 fois en 48 h (mesures 9, 17) |
| **Téléphonie** | Numéro **09**, **renvoi d'appel** plutôt que portabilité | 5 minutes contre 8 à 30 jours, réversible en 5 secondes (`docs/19`) |
| **Orchestration** | Machine à états, le modèle ne rédige jamais au client | 6 fautes sur 12 sans elle, 0 avec (mesures 14, 15) |
| **Données** | Tables partagées, `tenant_id`, RLS `ENABLE`+`FORCE` | `docs/02` |

---

## 3. Ce qu'on assume de ne pas savoir

1. **Le volume d'appels réel d'un salon.** Aucune source, et la base de Crenolo ne peut pas répondre — les appels n'y laissent aucune trace. **Se mesure avec une feuille de papier chez un salon volontaire** (`docs/18`).
2. **Le gain du cache de prompt.** Seule mesure qui attend une dépense : le palier gratuit plafonne à 8 000 jetons/minute. **Impact : le coût par appel, pas l'architecture.**
3. **Les taux absolus de reconnaissance.** Corpus synthétique, une voix. Ce qui est solide, ce sont les **écarts** entre conditions. Se lève avec les premiers appels réels.
4. **Le comportement des quatre opérateurs après renvoi** (identifiant d'appelant présent ou masqué). Une heure de tests terrain, impossible sans ligne.

**Aucune de ces quatre inconnues ne change ce qu'il faut coder.** Elles changent le prix affiché et la promesse commerciale, pas l'architecture.

---

## 4. Ce que je propose de construire, dans l'ordre

**Étape 1 — le squelette qui prouve la chaîne** (rien d'externe, tout mesurable en local)
1. Le **pipeline** STT → machine à états → LLM → TTS, en flux, avec réserve de connexions, pré-roll VAD et délai de garde.
2. La **machine à états** avec ses cinq seuils mesurés (`docs/15`) : transfert immédiat sur demande d'humain, oubli d'une entité refusée deux fois, reformulation puis transfert sur répétition, transfert à deux tours sans valeur neuve.
3. La **grammaire française** des nombres, dates et heures (`docs/10`), avec son jeu de tests — y compris les quatre échecs réels mesurés.
4. Le **corpus de non-régression** rejouable en une commande, déjà écrit (`bancs/corpus.py`).

**Étape 2 — le tenant et la mémoire**
5. `tenant_id` + RLS dès la première table.
6. Le **questionnaire** et le `memoire.md` (`docs/05`), l'UI ne remplaçant que le frontmatter.

**Étape 3 — le téléphone**
7. Asterisk + AudioSocket, numéro 09, parcours de branchement en cinq écrans (`docs/19`) et **vérification par appel réel**.

**Étape 4 — la console et la boucle de correction** (`docs/06`), puis la conformité de bout en bout (`docs/17` T6).

**Ce que je code en premier si tu dis oui** : le pipeline et la machine à états, parce que ce sont les deux seules pièces dont les mesures disent qu'elles décident de tout le reste — et parce qu'elles se testent sans numéro, sans client et sans dépense.

---

## 5. Ce qu'il me faut de toi

| Quoi | Pourquoi | Bloquant ? |
|---|---|---|
| **Le feu vert pour écrire du code produit** | C'est l'arrêt que tu as demandé | **Oui** |
| Un **salon volontaire**, étape A (feuille de comptage) | Seule source possible du volume d'appels | Non — L1 se construit sans |
| Une **clé d'API payante** | Cache de prompt, et un vrai candidat LLM | Non — le repli gratuit suffit pour construire |
| L'arbitrage sur **`reservation.py`** (Crenolo) | Le pair attend depuis le 14 | Non — c'est l'adaptateur, pas le produit |

---

## 6. Ce qui se passe si tu dis oui

Je commence par l'étape 1, en tests d'abord : le corpus et les seuils existent déjà, donc **chaque brique naît avec sa mesure**. Branche dédiée, commits en français, push à chaque tâche verte, et le point de contrôle habituel — fait, découvert, bloqué, suite — à chaque jalon.
