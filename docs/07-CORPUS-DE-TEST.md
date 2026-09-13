# Corpus de test et porte de non-régression

> Fondé sur `R6 §6.6` (méthodologie, `pass^k`, rééchantillonnage 8 kHz), `docs/recherche2/A6-metier-salon.md` (collisions lexicales, intentions réelles) et `docs/recherche2/A8-console-ux.md` (toute correction alimente le corpus).
> Principe directeur, tiré de τ-bench : **la démonstration mesure `pass^1`, le commerce mesure `pass^k`.** Un agent qui prend correctement un rendez-vous en démonstration a une probabilité sensiblement inférieure de le faire correctement huit fois d'affilée — GPT-4o passe de ~60 % à **~25 % entre pass^1 et pass^8**.

---

## 1. Ce que le corpus doit attraper

Quatre familles d'échec, par ordre de gravité **pour le commerçant**, pas par ordre de fréquence :

| # | Échec | Pourquoi il est en tête |
|---|---|---|
| 1 | **Confirmation orpheline** — l'agent dit « c'est noté », rien en base | Personne ne le détecte avant le jour J. Cible **0**, toute occurrence est un incident |
| 2 | **Créneau promis inexistant** (pause déjeuner, fermeture, praticien indisponible) | Le seul défaut que le **client** entend. C'est aussi la donnée qu'aucun import ne devine |
| 3 | **Mauvaise prestation réservée** (collision lexicale) | Produit un rendez-vous faux, pas une transcription approximative — le salon perd une heure de fauteuil |
| 4 | **Impasse** — le client demande un humain et ne l'obtient pas | Le vrai mode d'échec décrit par les exploitants : *« the customer got trapped when the call stopped being routine »* |

---

## 2. Composition

**60 à 100 appels réels français**, enregistrés avec consentement, transcrits et annotés à la main : intention, entités attendues (nom, numéro, date, prestation), issue attendue.

**Axes de variation, au moins cinq appels chacun** :
- accents régionaux et francophones (Nord, Sud, Belgique, Maghreb, Afrique de l'Ouest) ;
- bruit réel : **sèche-cheveux**, musique de salon, perceuse, rue, salle de restaurant ;
- **haut-parleur** — le cas qui révèle l'écho ;
- locuteurs âgés, débit lent, hésitations marquées ;
- chevauchements et interruptions volontaires ;
- changement d'avis en cours d'appel (« finalement plutôt jeudi ») ;
- **auto-correction** (« zéro six douze… non, quatorze ») — identifié par Full-Duplex-Bench v3 comme **le mode d'échec le plus constant** ;
- injection de prompt par l'appelant.

**Scénarios métier obligatoires, issus d'A6** — et l'ordre compte, parce que l'intention dominante n'est pas celle qu'on croit :
1. **« Comme la dernière fois »** — l'intention la plus fréquente, que Planity a outillée d'un bouton conçu *pour le téléphone*.
2. **Report ou annulation tardive** — structurellement téléphonique, les logiciels ayant fermé ce cas en ligne.
3. Prise de rendez-vous nue, avec et sans praticien nommé.
4. Demande de prix (l'agent doit dire ce que le gérant a paramétré, pas inventer une fourchette).
5. **Appel pendant la pause déjeuner** — l'agent doit refuser le créneau.
6. **Les six collisions lexicales**, chacune en deux scénarios opposés : `permanente` ↔ `semi-permanent` ↔ `maquillage permanent` · `mèches` ↔ `mèche` · `extension` cils/cheveux · `patine` ↔ `platine` · `soin` capillaire/visage/corps · `remplissage` ongles/cils. Plus le sigle **`SIF`**, prononcé tel quel.
7. Demande explicite d'un humain → **transfert immédiat, sans négociation**.
8. Arrhes : l'agent doit prononcer **exactement** le mot paramétré (le Code de la consommation présume des arrhes, remboursables au double).

---

## 3. Trois règles de fabrication qui décident de la validité

1. **Rééchantillonner tout le corpus en 8 kHz / G.711.** Tester en 16 kHz donne des résultats qui ne veulent rien dire pour nous : tous les WER publics sont en large bande propre, et **aucune source au monde ne publie de WER français téléphonique**.
2. **Rejouer chaque scénario `k = 5` fois et compter les succès *intégraux*.** Un scénario réussi 4 fois sur 5 est un scénario **échoué**.
3. **Injecter du bruit de façon contrôlée** : rejouer le corpus propre à 20, 15, 10 et 5 dB de rapport signal/bruit pour tracer **notre propre courbe de dégradation** — elle est absente de la littérature.

---

## 4. Ce qu'on mesure, et ce qu'on refuse de mesurer

| Métrique | Cible | Remarque |
|---|---|---|
| **Taux de confirmation orpheline** | **0** | Incident, pas statistique |
| Taux d'erreur **par entité** (numéro, nom, date, prestation) | à établir | **Séparé du WER** : un WER de 5 % réparti sur des mots vides est sans conséquence, le même concentré sur le dernier chiffre d'un numéro fait perdre le client |
| Créneaux promis inexistants | **0** | Vérifié contre l'agenda réel, pas contre la réponse du modèle |
| Taux d'impasse | à établir | Le chiffre que le gérant veut vraiment |
| Silence perçu p50 / p95 | **≤ 700 / 1 100 ms** | En percentiles, jamais en moyenne |
| Nombre de tours pour capter un numéro | ≤ 2 | Au-delà, bascule DTMF |

**Refusé** : le WER global comme indicateur de qualité, et tout **juge LLM pour valider une entité**. Un numéro se compare par égalité de chaîne. Le juge LLM ne sert qu'à noter la pertinence conversationnelle.

---

## 5. La boucle qui rend le corpus vivant

**Toute correction faite dans la console engendre automatiquement un scénario de régression** (`docs/06-CONSOLE-ET-CORRECTION.md`). C'est ce que personne ne fait sur le marché : Vapi documente « Turn production issues into regression tests » comme une consigne écrite à un développeur, sans aucun bouton.

Le cycle : appel raté → correction en trois appuis → scénario ajouté → rejoué `k = 5` fois à chaque changement. L'appel raté cesse d'être un incident pour devenir une **garantie**.

---

## 6. La porte de non-régression

Avant tout déploiement, **trois conditions cumulatives** :
1. **aucun scénario du corpus ne régresse** (succès intégraux, `pass^5`) ;
2. les SLO de latence tiennent (p50 ≤ 700 ms, p95 ≤ 1 100 ms) ;
3. **taux de confirmation orpheline = 0** sur la campagne de test.

Une seule des trois qui tombe bloque la mise en ligne. Et la porte s'applique **aussi à un changement de configuration d'un seul tenant** : c'est ce qui empêche qu'une correction faite pour un salon casse silencieusement le comportement d'un autre.

---

## 7. Coût et outillage

- **Exécution en intégration continue**, sur le modèle du cadre de test LiveKit (pytest + juge LLM) ou de promptfoo (MIT, exécution 100 % locale). **Coût d'infrastructure : nul.**
- Le coût réel est **l'annotation humaine** des 60 à 100 appels — quelques heures, une fois. C'est le seul investissement du lot, et il est réutilisé à chaque changement pendant toute la vie du produit.
- **Détection d'échec par règles avant tout LLM** : raccroché sous 10 secondes, plus de trois reformulations consécutives, silence de l'agent au-delà du seuil, demande explicite d'un humain. Quelques dizaines de lignes attrapent la majorité des échecs réels.

---

## 8. Ce qui manque encore

- Les **enregistrements eux-mêmes** : il faut 60 à 100 appels réels, donc un premier salon volontaire et un consentement écrit. À prévoir dès le lot L1, avant même que l'agent soit bon.
- La **courbe de dégradation par rapport signal/bruit** n'existe nulle part : c'est une mesure à faire, pas une donnée à chercher.
- Les libellés des sept fautes de correction, à tester à l'oral sur trois gérants — ce sont eux qui décident si la boucle fonctionne.
