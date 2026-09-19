# Livraison — ce qui est fait, ce qui est prouvé, ce qui ne l'est pas

> Document d'honnêteté. Il sépare trois choses qu'on confond d'habitude : ce qui
> est **écrit**, ce qui est **vérifié**, et ce qui est **encore une promesse**.

## 1. Ce qui est vérifié, et par quelle commande

| Affirmation | Commande qui la prouve |
|---|---|
| La suite de tests passe | `.venv/bin/python -m pytest tests/ -q` |
| Les fautes déjà mesurées ne reviennent pas | `.venv/bin/python bancs/porte.py --passages 2` — `pass^5`, deux passages |
| **Un rendez-vous se prend à travers une socket TCP** | `tests/test_bout_en_bout.py` — de la connexion à la ligne écrite en base |
| L'agent se tait quand on lui coupe la parole | `tests/test_serveur.py` — mesuré à travers le serveur réel, pas sur le composant |
| Un appel laisse une trace, avec la preuve d'annonce | `tests/test_bout_en_bout.py::test_l_appel_laisse_une_trace_au_journal` |
| Un créneau déjà pris n'est plus proposé | même fichier |
| Le service dit ce qui lui manque avant de décrocher | `python -m standard verifier` |
| Un appel se rejoue sans téléphone ni clé | `python demonstration.py` |

## 2. Ce qui est écrit et branché

Vingt et un modules. Les pièces qui portent une garantie :

- **`ecriture`** — la seule à pouvoir dire qu'un rendez-vous existe, et seulement après relecture ;
- **`decision`** — toutes les phrases que l'appelant entend ; cinq seuils mesurés ;
- **`comprehension`** — le seul endroit où vit le modèle, et rien de ce qu'il rend n'est cru sur parole ;
- **`session` / `serveur` / `audiosocket`** — le bord téléphonique, émission dans son propre fil ;
- **`depot` / `journal` / `audit`** — cloisonnés par locataire, écritures sérialisées ;
- **`sms`** — transactionnel par construction, et qui refuse de basculer en commercial ;
- **`console`** — trois gestes, aucun clavier, aucun prompt ;
- **`acces`** — clés par locataire, rotation à recouvrement, débit borné.

## 3. Ce qui n'est pas prouvé, et ne peut pas l'être ici

1. **Aucun appel réel n'a jamais été passé.** Tout est mesuré sur corpus synthétique et sur des sockets locales. C'est la limite principale du dossier depuis le premier jour, elle est écrite partout, et **elle ne se lève qu'avec un numéro et un commerçant**.
2. **Les valeurs absolues de reconnaissance** viennent d'un corpus synthétique à une voix. Ce qui est solide, ce sont les **écarts** entre conditions.
3. **Le gain du cache de prompt** n'est pas mesuré : le palier gratuit plafonne à 8 000 jetons par minute. Seule mesure du dossier qui attende une dépense.
4. **Le comportement des quatre opérateurs après renvoi** (identifiant d'appelant présent ou masqué) n'est documenté par aucun d'eux. Une heure de tests terrain, impossible sans ligne.
5. **Le multilingue** est une limitation assumée : détection prudente, puis transfert.

## 4. Ce qu'il faut pour un premier pilote

| Quoi | Pourquoi | Qui |
|---|---|---|
| Un numéro **09** et un renvoi d'appel | cinq minutes, réversible en cinq secondes (`docs/19`) | Adnan |
| Un commerçant volontaire | la seule source possible du volume d'appels réel (`docs/18`) | Adnan |
| Une clé d'API pour le STT distant | mesuré comme le meilleur choix sous bruit (mesure 12) | Adnan |
| Un expéditeur SMS déclaré au nom du salon | charte AF2M, onze caractères | Adnan |

**Le reste tourne déjà** : la machine, la base, la console, le mode hors ligne.

## 5. Comment ce document a été tenu honnête

Deux revues de code indépendantes ont été demandées pendant la construction, avec
pour consigne de chercher les promesses que le code ne tient pas. **La première a
trouvé que le produit ne pouvait prendre aucun rendez-vous** — 372 tests étaient
verts, et le chemin du téléphone à la base n'existait pas. Les cinq défauts
critiques et les onze importants ont été corrigés, chacun avec le test qui manquait.

C'est la raison d'être de la règle posée par Adnan le 18/09 : *ne pas se faire
confiance pour juger si le produit est fini.* Elle a payé quatre fois.
