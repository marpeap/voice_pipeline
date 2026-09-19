# Standard téléphonique — un assistant qui répond, et qui ne ment pas

Un agent qui décroche le téléphone d'un commerçant, comprend une demande, et
**n'annonce jamais un rendez-vous qui n'existe pas**.

Ce dépôt contient trois choses : **le produit** (`standard/`), **les mesures qui
l'ont dicté** (`docs/09-L0-MESURES.md`, vingt-trois mesures), et **les bancs qui
les rejouent** (`bancs/`). Aucune règle du code n'est là par principe : chacune
vient d'un tour de parole réellement joué, et le commentaire la cite.

## Essayer en une commande, sans rien dépenser

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python demonstration.py
```

Un appel entier se rejoue : ni téléphone, ni clé d'API, ni dépense. Trois autres
scénarios montrent ce qui compte vraiment :

```bash
.venv/bin/python demonstration.py --scenario tetu     # l'appelant qui insiste : transfert, jamais de boucle
.venv/bin/python demonstration.py --scenario humain   # « passez-moi quelqu'un » : transfert immédiat
.venv/bin/python demonstration.py --scenario faute    # la base perd l'écriture : l'agent ne promet rien
```

## Vérifier

```bash
.venv/bin/python -m pytest tests/ -q          # la suite complète (583 tests)
.venv/bin/python bancs/porte.py --passages 2  # la porte de non-régression
.venv/bin/python bancs/appel_reel.py          # douze appels joués avec les vrais moteurs
```

**`bancs/appel_reel.py` est le banc qui a trouvé ce qu'aucun test ne voyait.**
Rien n'y est simulé sauf la ligne : la voix de l'appelant est synthétisée puis
dégradée en 8 kHz comme le ferait le réseau, envoyée en trames AudioSocket sur
une vraie socket, transcrite par le moteur local, et le rendez-vous est relu en
base. Douze scénarios : créneau explicite, jour fermé, heure hors créneaux,
refus puis accord, « oui » trop court pour le moteur, créneau pris par un autre
pendant l'appel, question d'horaires, prise de message, correction du nom,
numéro dicté puis composé au clavier avec SMS. **Douze sur douze au 20/09** —
deux sur cinq avant les correctifs du 19.

**La porte rejoue les fautes mesurées contre le produit**, en `pass^5` : un
scénario réussi quatre fois sur cinq est un scénario **échoué**. Le lot n'est fini
que si elle passe deux fois d'affilée.

## Ce que le produit garantit, et pourquoi

| Garantie | D'où elle vient |
|---|---|
| **Aucune confirmation sans écriture relue** | Mesure 14 : deux confirmations orphelines en douze tours, dont « votre rendez-vous de demain matin est annulé » — rien en base |
| **Aucune date ne vient du modèle** | Même mesure : « le premier du mois prochain est un dimanche », inventé |
| **Hors horizon ≠ fermé ≠ incompris** | Mesure 15 : confondre les trois fait mentir la machine, et c'est invérifiable par le client |
| **Deux tours sans valeur neuve → transfert** | Mesure 18 : un compteur d'anti-boucle compte des **valeurs neuves**, pas des tours |
| **« Passez-moi quelqu'un » n'est jamais interprété** | Mesure 17 : détecté sur la transcription, avant tout appel au modèle |
| **Le flux d'écoute est ouvert avant que l'appelant parle** | Mesure 9 : un moteur streaming perd le premier mot d'un énoncé sur quatre |
| **Les connexions s'ouvrent au démarrage** | Mesure 4 : 2 040 ms pour une connexion neuve, 378 ms pour une connexion gardée |
| **Quatre synthèses simultanées au plus** | Mesure 13 : au-delà, le premier son dépasse 400 ms |
| **L'annonce « assistant automatique » est non désactivable** | AI Act art. 50 §1 — et mesure 19 : elle survit au canal téléphonique |

## Ce qui tourne, en trois commandes

```bash
python -m standard verifier   # dit si le service peut décrocher, et ce qui manque sinon
python -m standard servir     # écoute les appels d'Asterisk (AudioSocket)
python -m standard console    # la console du commerçant, sur la boucle locale
python -m standard registre   # le registre des traitements (RGPD art. 30)
```

En service, `GET http://127.0.0.1:8092/sante` rend les chiffres qui disent si ça
va : appels, part bruitée, **confirmations orphelines** (cible zéro), délai avant
premier fragment — c'est lui qui signale une machine pleine, bien avant la charge
processeur —, appels en cours, paroles perdues, pannes, état du ménage. Il est
joignable sans jeton, donc il ne porte que des compteurs : jamais un nom, un
numéro ou une transcription.

## Les pièces

| Module | Ce qu'il fait | Ce qu'il n'a pas le droit de faire |
|---|---|---|
| `ecoute` | audio → texte, pré-roll, rapport signal/bruit | perdre le premier mot |
| `comprehension` | texte → proposition structurée | inventer une entité, rédiger une phrase |
| `decision` | proposition → **la phrase que l'agent dit** | dire qu'un rendez-vous existe |
| `ecriture` | écrit, **relit**, et confirme | confirmer sans relecture |
| `parole` | phrase → audio, en flux | laisser un silence au-delà du délai de garde |
| `grammaire` | les nombres français | deviner un numéro incomplet |
| `locataire` | questionnaire → `memoire.md` | reparser le corps écrit par le commerçant |
| `hors_ligne` | comprendre sans modèle | combler ce qu'il n'a pas lu |
| `service` | configuration, démarrage, supervision | activer un agent dont une question critique est vide |
| `serveur` | écoute AudioSocket, un appel = une session | laisser un appel raté en emporter d'autres |
| `session` | trames, interruption, clavier DTMF | continuer à parler quand l'appelant reprend la parole |
| `audiosocket` | le protocole d'Asterisk | supposer qu'un paquet reçu est une trame complète |
| `connecteur` | l'agenda interne ou un logiciel tiers | confondre un « non » et un « je ne sais pas » |
| `journal` | ce qui reste de l'appel | conserver l'audio |
| `console` | le fil, le détail, la correction en trois gestes | montrer un prompt, sous quelque forme que ce soit |
| `correction` | sept fautes, cycle de vie, corpus | appliquer une dictée sans arbitrage |
| `conformite` | annonce, audio, e-mail, registre | promettre ce qui n'est pas vérifié |
| `acces` | clés par locataire, rotation, débit | garder un secret en clair |
| `audit` | qui a changé quoi | permettre de corriger un événement |
| `depot` | rendez-vous cloisonnés | rendre des lignes sans locataire |
| `langue` | détection prudente | servir à moitié un appelant qu'on ne comprend pas |
| `identite` | le nom de l'appelant, et sa correction | écrire un nom deviné, ou une formule de politesse |
| `fiche` | répondre aux horaires depuis le frontmatter | inventer une information absente de la fiche |
| `entretien` | purge à la durée annoncée | laisser une durée de conservation devenir fausse |
| `registre` | le registre RGPD, dérivé de la configuration | publier une clé de fournisseur |
| `sante` | le point d'état, lisible par une machine | publier une donnée d'appelant |
| `sms` | la confirmation écrite, transactionnelle | promettre un SMS qui ne peut pas partir |

## Configurer un salon

Les packs sectoriels (`packs/*.json`) sont de la **donnée** : coiffure, artisan de
dépannage, restaurant. Le commerçant répond à des questions, le système écrit le
fichier — **il ne voit jamais un prompt**.

```bash
python3 bancs/valide_pack.py packs/*.json   # cinq règles de format, dont l'annonce non désactivable
```

## Ce qui n'est pas encore là

- **Un vrai numéro.** Le bord téléphonique est codé et joué de bout en bout
  (`standard/audiosocket.py`, `serveur.py`, `session.py`, et douze appels réels
  par `bancs/appel_reel.py`), mais **il n'a jamais reçu d'appel d'un opérateur** :
  il manque un numéro 09 avec renvoi, et la configuration Asterisk de
  `deploiement/` n'a tourné sur aucune machine. `docs/19` décrit le parcours.
- **Le gain réel du cache de prompt** : seule mesure encore impossible sans clé
  payante (`docs/09`, mesure 23).
- **Les valeurs absolues de reconnaissance** : le corpus est synthétique, une seule
  voix. Ce qui est solide, ce sont les **écarts** entre conditions. Le moteur
  local échoue encore de temps en temps sur une première phrase — c'est ce qui
  fonde la mesure 20 : **le moteur distant reste le défaut** en production.
- **Un commerçant.** Aucune des règles n'a été confrontée à un vrai salon.

## Pour reprendre le travail

`CLAUDE.md` à la racine dit où en est le chantier. `docs/21-BILAN-L0-ET-FEU-VERT.md`
résume les vingt-trois mesures et l'ordre de construction ; `docs/22-SPEC-MODULES.md`
donne le contrat de chaque module et le test qui le prouve.
