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
.venv/bin/python -m pytest tests/ -q          # la suite complète
.venv/bin/python bancs/porte.py --passages 2  # la porte de non-régression
```

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

## Configurer un salon

Les packs sectoriels (`packs/*.json`) sont de la **donnée** : coiffure, artisan de
dépannage, restaurant. Le commerçant répond à des questions, le système écrit le
fichier — **il ne voit jamais un prompt**.

```bash
python3 bancs/valide_pack.py packs/*.json   # cinq règles de format, dont l'annonce non désactivable
```

## Ce qui n'est pas encore là

- **Le bord téléphonique** (Asterisk, AudioSocket, un numéro) : `docs/19` décrit le
  parcours de branchement, il n'est pas codé.
- **Le gain réel du cache de prompt** : seule mesure encore impossible sans clé
  payante (`docs/09`, mesure 23).
- **Les valeurs absolues de reconnaissance** : le corpus est synthétique, une seule
  voix. Ce qui est solide, ce sont les **écarts** entre conditions.

## Pour reprendre le travail

`CLAUDE.md` à la racine dit où en est le chantier. `docs/21-BILAN-L0-ET-FEU-VERT.md`
résume les vingt-trois mesures et l'ordre de construction ; `docs/22-SPEC-MODULES.md`
donne le contrat de chaque module et le test qui le prouve.
