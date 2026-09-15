# Spécification du questionnaire et des packs sectoriels

> Fondé sur `docs/recherche2/A6-metier-salon.md` (pack coiffure mesuré sur 12 547 lignes de prestation réelles), `docs/recherche2/A1-llm-et-dialogue.md` (contrainte de cache) et `R5 §4-5` (round-trip Markdown, paliers, sauvegarde).
> Rappel du parti pris : **le commerçant ne voit jamais un prompt.** Il répond à des questions, le système écrit le fichier.

---

## 1. Une correction à apporter au pack livré par A6

La question **E3 — « Dit-il qu'il est un assistant automatique ? »** propose « ☐ Seulement si on le lui demande ». **Cette option est retirée.** L'annonce est une obligation de l'AI Act art. 50 applicable depuis le 02/08/2026, et c'est aussi le premier levier de satisfaction mesuré (`R4 §C.2`). E3 devient un choix de **formulation**, jamais d'existence :

> **E3. Comment l'agent annonce qu'il est automatique** (obligatoire, non désactivable)
> ☐ « Je suis l'assistant automatique du salon » ★ ☐ « Je suis l'assistant virtuel de [nom] » ☐ Formulation personnalisée : ___

C'est le seul endroit du questionnaire où le produit **refuse** un réglage au commerçant. Il doit être écrit dans l'interface, avec la raison — un commerçant à qui l'on explique qu'il est protégé accepte une contrainte qu'il refuserait si elle était muette.

---

## 2. Format d'un pack sectoriel

Un pack = **un fichier JSON versionné**, livré avec le produit, jamais édité par le commerçant.

```jsonc
{
  "pack": "coiffure", "version": "2026.09.1", "langue": "fr-FR",
  "blocs": [
    { "id": "A", "titre": "Identité et horaires", "palier": 0,
      "questions": [
        { "id": "A3", "type": "choix_unique", "critique": true,
          "libelle": "Fermez-vous entre midi et deux ?",
          "aide": "Si l'agent l'ignore, il proposera un créneau qui n'existe pas.",
          "options": [
            { "valeur": "continu",  "libelle": "Pas de coupure, service continu" },
            { "valeur": "commune",  "libelle": "Coupure commune au salon", "defaut": true,
              "champs": [ { "id": "debut", "type": "heure", "defaut": "12:30" },
                          { "id": "fin",   "type": "heure", "defaut": "13:30" } ] },
            { "valeur": "par_personne", "libelle": "Chaque coiffeur a sa pause",
              "ouvre": "B" }
          ],
          "ecrit": { "cible": "frontmatter", "chemin": "horaires.coupure" } } ] } ],
  "keyterms": { "groupe1": ["rendez-vous", "décaler", "…"],
                "groupe3": { "balayage": ["balayage", "ombré", "tie and dye"] } },
  "collisions": [ { "termes": ["permanente", "semi-permanent", "maquillage permanent"],
                    "desambiguisation": "demander la prestation, jamais deviner" } ]
}
```

**Cinq règles de format, toutes issues de la recherche :**
1. **Jamais plus de 5 options** par question, **toujours un défaut** (`defaut: true`). Un salon qui ne répond rien doit obtenir un agent qui fonctionne. ⚠️ **Précision du 15/09**, trouvée en écrivant les trois packs : un **choix multiple** peut légitimement n'avoir rien de coché — mais il doit le **dire** (`"defaut_vide": true`), sinon on ne distingue pas l'intention de l'oubli. C'est le validateur qui a attrapé le cas, sur mon propre pack.
2. **`ecrit`** dit où va la réponse : `frontmatter` (machine) ou `corps` (prose lue par le modèle). Aucune réponse ne va nulle part — une question sans `ecrit` est un bug de pack.
3. **`ouvre`** est le seul mécanisme de branchement, et il ne descend **que d'un niveau** (NN/g : jamais plus de deux niveaux de divulgation).
4. **`critique: true`** marque les questions dont l'absence produit une erreur *audible par le client* — aujourd'hui A3 (pause), C1 (catalogue), D3 (mot employé pour les arrhes). Elles ne peuvent pas être sautées.
5. **`keyterms.groupe3` est indexé par prestation** : le vocabulaire n'est injecté que si la prestation est cochée en C1. C'est ce qui tient la limite des 20–50 termes recommandée par Deepgram, au lieu de déverser tout le lexique du métier.

---

## 3. Du questionnaire au fichier `memoire.md`

```
pack.json ──► questionnaire (JSONForms)
                  │ réponse par réponse, sauvegarde serveur
                  ▼
          tenant_config (JSONB, append-only, versionné)
                  │
        ┌─────────┴──────────┐
        ▼                    ▼
  frontmatter YAML      corps Markdown
  (régénéré à chaque    (écrit par le commerçant,
   sauvegarde)           JAMAIS reparsé ni réécrit)
                  ▼
             memoire.md ──► dépôt git (Dulwich, auteur = l'utilisateur réel)
                  ▼
        prompt système, mis en cache
```

**La règle qui protège la prose du commerçant** : on remplace le bloc frontmatter délimité, on **reconcatène le corps octet pour octet**. Toute bibliothèque qui reparse et réémet le Markdown complet normalise le style et détruit les annotations — `mdast-util-to-markdown` le dit lui-même, `mdformat` le fait délibérément.

**Et la règle qui vient d'A1, contre-intuitive** : le prompt système est **calibré au-dessus de 4 096 tokens** pour rester cachable. Conséquence concrète pour ce document : **on n'élague pas `memoire.md` pour économiser des tokens.** Un fichier riche coûte 0,1× ; un fichier maigre coûte plein tarif à chaque tour. Les sections vides restent présentes avec leur valeur par défaut explicite — c'est à la fois moins cher et plus lisible pour le modèle.

**Ordre du prompt assemblé** (stable = cachable) :
1. identité et règles générales · 2. schémas d'outils · 3. pack sectoriel (vocabulaire, désambiguïsations) · 4. `memoire.md` du tenant · **— rupture de cache —** · 5. date et heure courantes, fuseau · 6. ce que l'on sait de l'appel en cours.
Tout ce qui varie d'un appel à l'autre est **après** la rupture. Mettre la date en tête d'un prompt invalide le cache à chaque appel et multiplie la facture par dix.

---

## 4. Parcours de remplissage

| Palier | Blocs A6 | Ce que l'agent sait faire à la fin | Questions |
|---|---|---|---|
| 0 | A1, A2, **A3**, E1–E4 | **Il décroche, se présente, annonce qu'il est automatique, donne horaires et adresse** | ~7 |
| 1 | B1–B3 | Il sait qui travaille quand, et quoi faire si le coiffeur demandé est pris | ~4 |
| 2 | **C1**, C2–C5 | Il propose un vrai créneau, avec la bonne durée | ~6 |
| 3 | D1–D9 | Il respecte les règles de la maison et sait quand passer la main | ~10 |
| 4 | C6–C9, D10 | Il gère les enchaînements, la consultation préalable, les interdits | ~6 |

**Le palier 0 seul produit un agent qui décroche** — c'est la seule chose qui rend la suite désirable. Et le parcours est **interrompable à tout moment** : sauvegarde serveur après chaque réponse (pas `localStorage` : le gérant commence au comptoir sur son téléphone et finit au bureau le soir), reprise par lien.

**Score de complétude** — jamais un pourcentage abstrait, toujours une conséquence :
> « Il manque la pause déjeuner. **Tant qu'elle n'est pas renseignée, l'agent peut proposer un rendez-vous pendant votre pause.** » — 30 secondes pour corriger.

---

## 5. Ce que l'import remplit avant même la première question

Le connecteur (`docs/04-CONNECTEUR-CRENOLO.md`) pré-remplit, et le commerçant **valide** au lieu de saisir :

| Question | Source dans Crenolo | Reste à demander |
|---|---|---|
| A2 horaires | `businesses.hours` | rien |
| A3 **pause** | ⚠️ **inexprimable** — `hours` n'a qu'une plage par jour | **tout** : c'est la question critique n°1 |
| B équipe | `practitioners` (prénom, jours, absences) | B1–B3 (les règles, pas les faits) |
| C1 catalogue | `services` (nom, `duration_minutes`, prix) | C2–C9 |
| C6 enchaînements | `bookings.extra_service_ids` — **mesurable sur l'historique** | confirmation seulement |
| D1, D2 délais | `settings.min_booking_hours`, `max_booking_days` | confirmation |
| keyterms | noms de `services`, prénoms de `practitioners`, noms de `fiches_clients` | rien |

**Deux enseignements** : l'import couvre l'essentiel du bloc C, ce qui rend le questionnaire court sans l'appauvrir ; mais **la pause déjeuner n'existe nulle part dans le modèle de données** — le seul défaut audible par le client est précisément celui qu'aucun import ne peut deviner.

---

## 6. Un pack, trois usages

Le même fichier alimente trois consommateurs, et c'est ce qui justifie son format :

1. **Le questionnaire** — libellés, options, branchements, défauts.
2. **L'amorçage lexical du STT** — `keyterms`, filtré par les prestations réellement cochées, plafonné à 50 termes.
3. **Le corpus de test** — chaque `collision` engendre au moins deux scénarios d'appel opposés (« je voudrais une permanente » contre « je voudrais du semi-permanent »), rejoués `k = 5` fois. Un pack qui déclare une collision sans scénario de test associé est incomplet.

---

## 7. Packs prévus, et ce qu'il leur manque

| Pack | État | Manque |
|---|---|---|
| **coiffure / beauté** | Écrit et mesuré (A6) | Rien pour démarrer |
| **artisan dépannage** | Cadré (A6 §5.1) : devis avant travaux, déplacement annoncé, **l'agent ne qualifie jamais l'urgence lui-même** (effet juridique), sortie de secours câblée en dur sur gaz, feu, danger | Le détail des questions |
| **restaurant** | Cadré (A6 §5.2) : couverts d'abord, shifts et non agenda continu | Le seuil « groupe » **à demander, jamais à supposer** |
| santé, auto | Non traités | Tout — et le pack santé demandera un examen RGPD à part |


---

## 6. Les trois packs livrés, et le validateur qui les tient — 15/09

Les packs sont écrits : `packs/coiffure.json` (10 questions, 6 critiques), `packs/artisan-depannage.json` (14 questions, 8 critiques, **quatre interdits câblés**), `packs/restaurant.json` (10 questions, 6 critiques, **deux interdits câblés**).

**`bancs/valide_pack.py` vérifie les cinq règles de format**, et il tourne avant même que le produit existe :

| Règle vérifiée | Ce qu'elle empêche |
|---|---|
| ≤ 5 options, toujours un défaut (ou `defaut_vide` déclaré) | Un commerçant qui ne répond rien obtient quand même un agent qui fonctionne |
| Toute question porte une cible `ecrit` | Une réponse qui n'irait nulle part — et personne ne s'en apercevrait |
| Un seul niveau de branchement | La divulgation en cascade, que la recherche interdit |
| **E3 présente et non désactivable** | L'annonce AI Act supprimée par erreur dans un pack |
| `keyterms.groupe3` indexé par prestation | Le déversement de tout le lexique du métier dans le prompt |

**Un pack est de la donnée, mais une donnée fausse produit un agent faux, en silence.** Le validateur a d'ailleurs attrapé une faute dans le pack artisan dès sa première exécution — d'où la précision ajoutée au §2.
