# Grammaire française — nombres, numéros, dates et heures

> **Spécification, pas implémentation.** Décision prise en A2 : on **ne délègue pas** la normalisation au moteur de reconnaissance. Aucun fournisseur ne documente le cas français, et le mode d'échec attendu est un **bug de post-traitement** (`4 20 12`), pas une erreur acoustique. Un bug se teste ; une hallucination acoustique, non.
> Les cas de test ci-dessous ne sont pas inventés : ce sont les **sorties réelles** des moteurs mesurés le 14/09 (`docs/09-L0-MESURES.md`).

---

> **Mise à jour du 15/09** — la mesure 7 (`docs/09`) a montré que **quatre numéros sur dix se perdent, et exactement de la même façon en 16 kHz et en 8 kHz**. La bande téléphonique n'y est pour rien : ce qui casse, c'est la grammaire française des nombres. Cette page cesse donc d'être une précaution : **c'est elle qui décide si le rendez-vous existe.** Trois règles nouvelles en sont tirées (T8, T9, T10).

## 1. Ce que le moteur nous donne réellement

Mesuré sur Nemotron 3.5, en bande téléphonique :

```
« Mon numéro c'est zéro six douze trente-quatre cinquante-six soixante-dix-huit »
```

Les chiffres arrivent **en toutes lettres**, groupés **par deux**, avec la composition française des dizaines 70–99. Trois conséquences :
1. La segmentation n'est pas triviale : `quatre-vingt-dix-huit` est **un** nombre, pas `4 20 10 8`.
2. Le groupement par deux est une **information**, pas du bruit : il structure le numéro.
3. Les erreurs observées sont **lexicales et locales** — `zéro si` pour `zéro six`, `quatre-vingt ans` pour `quatre-vingt-onze` —, donc rattrapables par contrainte de format.

---

## 2. Nombres — règles

**N1.** Unités et dizaines simples : `zéro`…`seize`, puis `dix-sept`…`dix-neuf`, `vingt`…`soixante`.
**N2.** Composition 70–99 : `soixante-dix` = 70, `soixante et onze` = 71, `quatre-vingts` = 80, `quatre-vingt-un` = 81, `quatre-vingt-dix` = 90, `quatre-vingt-onze` = 91, `quatre-vingt-dix-neuf` = 99. **La conjonction `et` n'apparaît qu'à 21, 31, 41, 51, 61 et 71** — jamais à 81 ni 91.
**N3.** Variantes régionales à accepter en entrée, jamais à produire : `septante` (70), `huitante`/`octante` (80), `nonante` (90). Un appelant belge ou suisse existe ; l'agent, lui, parle français de France.
**N4.** Liaisons et élisions transcrites de façon variable : `vingt-et-un` / `vingt et un`, `quatre-vingt` / `quatre-vingts`. **Normaliser avant analyse** : minuscules, accents retirés, tirets et espaces unifiés.
**N5.** Chiffres déjà en chiffres : le moteur peut rendre `06` ou `6`. Les deux formes doivent entrer dans la même grammaire.

---

## 3. Numéros de téléphone — la contrainte sauve la lecture

**Le format français est redondant, et cette redondance est notre filet.**

**T1.** Un numéro national est **exactement 10 chiffres**, commençant par `01`–`05` (fixes), `06`/`07` (mobiles), `08` (spéciaux, **à refuser**), `09` (non géographiques).
**T2.** **Ne jamais faire confiance au premier mot.** Mesuré : `zéro` devient `ses héros`, `véro`, `verrou`, `si`. Règle : si la suite donne 9 chiffres et que le premier mot est inintelligible, **le premier chiffre est un `0`** — c'est le seul début possible. La contrainte reconstruit ce que l'acoustique a perdu.
**T3.** Le second chiffre est lui aussi contraint : `1`–`9`, jamais `0`. Un `zéro zéro` en tête est une erreur de transcription, pas un numéro.
**T4.** Après reconstruction, **vérifier la longueur avant tout**. 10 chiffres → accepter et relire. 9 ou 11 → **ne pas deviner**, relire à voix haute ce qui a été compris et demander confirmation.
**T5.** Les formats internationaux (`+33 6 …`) sont acceptés en entrée : `+33` suivi de 9 chiffres ≡ `0` suivi des mêmes 9.
**T6.** **Relecture obligatoire par groupes de deux**, avec le `say-as` d'Azure (`alphanumeric format="spell"`, le tiret force la pause) — c'est le seul TTS du panel à le documenter en français.
**T8. Onze chiffres est un cas aussi fréquent que neuf — et il ne se traite pas pareil.** Mesuré le 15/09 sur `whisper-large-v3-turbo` : « zéro un **quarante-trois** vingt-deux onze zéro neuf » ressort en `01 40 3 22 11 09`, soit **onze chiffres**, parce que le moteur a coupé un nombre composé en deux. Règle : si la suite donne 11 chiffres **et** qu'il existe **une seule** façon de refusionner deux jetons adjacents en un nombre français valide (`40` + `3` → `43`) qui ramène à 10 chiffres avec un préfixe licite, **proposer cette lecture — et la faire confirmer à voix haute**. S'il y en a plusieurs, ou aucune, on relit sans deviner (T4).

**T9. Un marqueur de correction annule le groupe précédent, pas le numéro.** Mesuré : « zéro six, douze, quatorze… **non**, quinze, quarante, soixante » est **parfaitement transcrit** par le moteur — l'échec est à l'interprétation, pas à l'écoute. Les marqueurs à traiter : `non`, `pardon`, `plutôt`, `excusez-moi`, `je me trompe`. Chacun **invalide le dernier groupe de chiffres énoncé** et rien d'autre. Ici : `06 12 ~~14~~ 15 40 60` → `0612154060`.

**T10. Certaines ambiguïtés sont dans la langue, pas dans le micro.** « quatre-vingts douze » peut valoir `92` ou `80 12` ; un humain hésiterait aussi. Une ambiguïté structurelle **ne se tranche jamais en silence** : les deux lectures donnent dix chiffres, donc T4 ne la rattrape pas. Relecture obligatoire, et c'est le seul cas où l'agent propose explicitement deux lectures.

**T7.** Après **deux** échecs, bascule **DTMF** (`numDigits=10`, `finishOnKey=#`). Après un échec DTMF, **escalade humaine**.

---

## 4. Dates et heures

**D1.** Le function call reçoit une **date absolue ISO 8601 avec fuseau**, jamais une expression relative. Le prompt porte la date et l'heure courantes, **après la rupture de cache**.
**D2.** Relatifs à résoudre : `demain`, `après-demain`, `lundi prochain`, `en huit` (= dans 8 jours), `en quinze`, `dans la semaine`, `ce week-end`, `le 3` (mois courant si futur, sinon mois suivant).
**D3.** ⚠️ **`jeudi prochain` est ambigu en français** — ce jeudi-ci ou celui de la semaine suivante ? **Ne jamais trancher silencieusement** : reformuler avec la date (« jeudi 17, donc dans trois jours ? »).
**D4.** Heures : `quatorze heures`, `deux heures de l'après-midi`, `neuf heures moins le quart` (08:45), `midi et demi` (12:30), `minuit`. **`midi et demi` s'écrit sans `e`, `demie` s'emploie après une heure** — sans importance à l'oral, mais le TTS doit le rendre correctement.
**D5.** **Confirmation obligatoire avec jour de la semaine + date + heure** : « donc **jeudi 17 septembre à 10 h 30** ». Le jour de la semaine sert de **bit de parité** — si l'appelant avait une autre date en tête, la discordance apparaît immédiatement.
**D6.** Garde-fous : refuser toute date passée, ou au-delà de `max_booking_days` du salon. Une date hors bornes est une erreur de compréhension, pas une demande.

---

## 5. Jeu de tests attendu

Chaque ligne est un test. Les entrées marquées **[mesuré]** sont des sorties réelles des moteurs le 14/09.

### 5.1 Nombres

| Entrée | Attendu |
|---|---|
| `quatre-vingt-dix-huit` | `98` |
| `quatre-vingt dix huit` **[mesuré]** | `98` |
| `soixante et onze` | `71` |
| `soixante-dix-sept` | `77` |
| `quatre-vingts` / `quatre-vingt` | `80` |
| `nonante-deux` | `92` |
| `septante` | `70` |
| `vingt et un` | `21` |
| `quatre vingt un` | `81` |

### 5.2 Numéros — dont les échecs réels

| Entrée | Attendu | Pourquoi |
|---|---|---|
| `zéro six douze trente-quatre cinquante-six soixante-dix-huit` | `0612345678` | cas nominal |
| `mon numéro ses héros fit douze trente-quatre cinquante-six soixante-dix-huit` **[mesuré, Vosk]** | **`0612345678`** | T2 + T4 : 8 chiffres lisibles + longueur → reconstruire `06` |
| `MON NUMÉRO SES EUROS SIX DOUZE…` **[mesuré, sherpa]** | `0612345678` | idem |
| `c'est le zéro si quatre-vingt-dix-huit soixante-seize…` **[mesuré, Nemotron]** | `0698764821` | `si` → `six` par contrainte de position |
| `zéro sept quatre-vingt-deux quatre-vingt ans soixante-treize zéro cinq` **[mesuré]** | **échec contrôlé** | `ans` ≠ chiffre → 8 chiffres seulement → **relire, ne pas deviner** |
| `zéro huit douze trente-quatre cinquante-six` | **refus** | T1 : `08` interdit |
| `plus trente-trois six douze trente-quatre cinquante-six soixante-dix-huit` | `0612345678` | T5 |
| `zéro six douze trente-quatre cinquante-six` | **relecture** | 8 chiffres → T4, jamais compléter |
| `zéro un quarante-trois vingt-deux onze zéro neuf` → transcrit `01 40 3 22 11 09` **[mesuré 15/09, whisper-turbo]** | `0143221109` **puis confirmation orale** | T8 : 11 chiffres, une seule refusion valide (`40`+`3`→`43`) |
| `zéro six, douze, quatorze… non, quinze, quarante, soixante` **[mesuré 15/09 — transcription correcte, interprétation fausse]** | `0612154060` | T9 : `non` annule `14`, et lui seul |
| `zéro six quatre-vingts douze zéro trois quarante-quatre` **[mesuré 15/09]** | **deux lectures proposées** | T10 : ambiguïté de la langue ; `92` et `80 12` donnent tous deux dix chiffres |
| `zéro neuf soixante-dix zéro zéro quatre-vingt-un douze` → transcrit `09-7100-92` **[mesuré 15/09]** | **relecture** | chiffres perdus à l'écoute : 8 chiffres, aucune refusion ne sauve — T4 |

### 5.3 Dates et heures

| Entrée (le mardi 15/09/2026 à 14:00) | Attendu |
|---|---|
| `demain à dix heures` | `2026-09-16T10:00+02:00` |
| `jeudi à dix heures et demie` | `2026-09-17T10:30+02:00` |
| `jeudi prochain` | **question de levée d'ambiguïté**, jamais une date |
| `en huit` | `2026-09-23` |
| `le 3 à quatorze heures` | `2026-10-03T14:00+02:00` (le 3 courant est passé) |
| `neuf heures moins le quart` | `08:45` |
| `midi et demi` | `12:30` |
| `hier` | **refus** : date passée |
| `dans six mois` | **refus** si au-delà de `max_booking_days` |

---

## 6. Où cette grammaire s'exécute

**Côté serveur, jamais dans le modèle.** C'est la même leçon qu'en A8 : ce qui doit être vrai à 100 % ne se confie pas à un système probabiliste. Le LLM rapporte ce qu'il a entendu ; **la grammaire décide**, et c'est elle qui déclenche la relecture, la bascule DTMF ou l'escalade.

Corollaire pour le corpus de régression : ces tests sont **déterministes et gratuits**, ils tournent à chaque changement sans appeler aucun fournisseur. Ce sont les seuls tests du produit qui ne coûtent rien à rejouer.
