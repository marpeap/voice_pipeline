# Lot L2 — le service autonome, en tâches exécutables

> **Ce que L2 livre** : un commerçant qui n'a rien à voir avec Crenolo s'inscrit seul, répond à un questionnaire, branche son numéro, et son agent répond. Sans nous au téléphone, sans intervention manuelle en base.
>
> L1 (`docs/17-LOT-L1.md`) prouve qu'un appel tient. **L2 prouve qu'un client peut arriver seul.** C'est le lot qui fait exister « service à part entière » au lieu de « démonstration ».

---

## 1. Ce que L2 ne fait pas

À écrire d'abord, parce que c'est ce qui rend le lot faisable :

- **Pas de connexion à un agenda tiers.** Agenda interne + export iCal. Google est plafonné à 100 utilisateurs tant que l'application n'est pas vérifiée — à vie, sans réinitialisation — et iCloud n'a aucune API. Un export iCal est gratuit, immédiat, et marche avec les deux.
- **Pas d'extension de navigateur.** Reportée (`docs/16-EXTENSION-PERIMETRE.md`) : elle ne porte pas l'audio, l'identité est absente sur Firefox Android, et le site fait le même travail.
- **Pas de paiement en ligne.** Les premiers clients sont facturés à la main. Un tunnel de paiement coûte plus cher à écrire qu'à remplacer par un virement, tant qu'on compte les clients sur une main.
- **Pas de multi-langue.** Français seulement — c'est aussi ce qui est mesuré.

---

## 2. Les tâches

### T1 — Le compte et le locataire
- [ ] Inscription par e-mail + mot de passe, vérification de l'adresse. Pas d'OAuth (voir le plafond Google).
- [ ] À la création du compte, **un locataire** et rien d'autre : `tenant_id`, raison sociale, fuseau, langue.
- [ ] RLS `ENABLE` **et** `FORCE` sur toutes les tables portant `tenant_id`, `set_config(..., true)` en transaction. À écrire dès la première table : le rajouter après coup, c'est réécrire chaque requête.
- [ ] Test qui échoue si une requête sans `tenant_id` posé rend une ligne.

### T2 — Le questionnaire, et le fichier qu'il produit
- [ ] Rendu d'un pack (JSON) en formulaire : questions à cocher issues du pack, champs libres, ordre imposé par le pack.
- [ ] Écriture du `memoire.md` du locataire : **l'UI remplace le bloc frontmatter, jamais le corps**. Le corps Markdown n'est jamais reparsé.
- [ ] Reprise : on peut sortir du questionnaire et y revenir ; ce qui est répondu est gardé.
- [ ] Trois paliers d'exigence — ce qui est nécessaire pour décrocher, ce qui améliore, ce qui est facultatif — et l'agent ne peut pas être activé tant que le premier palier n'est pas complet.
- [ ] Deux packs livrés : coiffure (`docs/05`) et l'un des deux de `docs/13`.

### T3 — Le numéro
- [ ] Provisionnement d'un **09** à la demande, par API, rattaché au locataire.
- [ ] Le parcours en cinq écrans de `docs/19-BRANCHEMENT-NUMERO.md`, pour **un opérateur** d'abord.
- [ ] **Vérification par appel réel** : l'état reste « en attente » tant qu'un appel n'est pas arrivé par le renvoi. Stocker l'heure, la sonnerie observée, et si le CLI était présent.
- [ ] Surveillance : deux jours d'ouverture sans aucun appel sur un numéro vérifié → bascule en « à revérifier » + message.

### T4 — L'agent, multi-locataire
- [ ] Le pipeline de L1, mais chargeant le `memoire.md` **du locataire appelé**, déterminé par le numéro d'arrivée.
- [ ] **Réserve de connexions ouvertes au démarrage** vers STT, LLM, TTS et SMS, noms résolus au démarrage, sonde de maintien. Mesuré : une connexion rouverte coûte 2 040 ms contre 378 ms gardée (`docs/09`, mesure 4). Ce point n'est pas une optimisation tardive, c'est la différence entre tenir le budget et ne pas le tenir.
- [ ] Le nom du modèle vit **en configuration** : deux modèles ont disparu d'un catalogue en deux jours.
- [ ] Rééchantillonnage **dans le processus**, jamais par un `ffmpeg` lancé par fragment (45 ms de démarrage contre 11 ms de travail).
- [ ] Machine à états de `docs/15-RIGUEUR-EXECUTION.md` : le modèle propose, la machine dispose ; conditions de sortie vérifiées côté serveur.
- [ ] `read-after-write` avant toute confirmation orale. Métrique **confirmation orpheline**, cible 0.

### T5 — La console du commerçant
- [ ] Liste des appels : heure, durée, intention, issue, et **ce que l'agent a écrit en base**.
- [ ] La boucle de correction en trois gestes de `docs/06` : une correction ne modifie pas un prompt, elle ajoute une ligne au `memoire.md` et une entrée au corpus.
- [ ] États en gris, jamais en rouge (une erreur d'agent n'est pas une panne du commerçant).
- [ ] Bouton **couper l'agent**, visible, immédiat, sans confirmation.

### T6 — Conformité, non désactivable
- [ ] Annonce « assistant automatique » dans la première phrase, non désactivable, testée par le corpus.
- [ ] Registre des traitements et modèle d'accord de sous-traitance (art. 28) — les pièces sont déjà écrites dans `docs/18-SALON-PILOTE.md`.
- [ ] Audio supprimé après transcription ; durée de conservation affichée au commerçant.
- [ ] **Jamais d'e-mail collecté à l'oral.** Mobile + SMS.

### T7 — La porte de non-régression
- [ ] Rejouer le corpus (`bancs/corpus.py`) à chaque changement de modèle, de prompt ou de pack.
- [ ] `pass^5`, pas `pass^1` : un scénario réussi 4 fois sur 5 est un scénario échoué.
- [ ] Le lot n'est fini que si la porte passe **deux fois d'affilée** sur un corpus qui a grossi des corrections réelles du pilote.

---

## 3. L'ordre, et pourquoi

T1 avant tout (le cloisonnement ne se rajoute pas), puis **T3 avant T2** : un numéro qui sonne dans le vide est un problème visible et réparable, un questionnaire sans numéro ne prouve rien. T4 ensuite, T5 quand un vrai appel a produit une vraie ligne à corriger. T6 est transverse et se code en même temps que T4, jamais après. T7 ferme.

## 4. Ce qui bloquerait L2, et qui ne dépend pas de nous

| Blocage | Qui le lève |
|---|---|
| Un fournisseur de numéro avec achat par API et KYC français | Adnan — c'est le premier vrai poste de dépense du projet |
| Une clé d'API LLM payante | Adnan — et c'est aussi la seule mesure encore impossible : le gain du cache de prompt |
| Un premier commerçant qui accepte de brancher son numéro | Adnan — `docs/18` contient l'argumentaire et l'accord |

Tout le reste de L2 s'écrit sans rien attendre.
