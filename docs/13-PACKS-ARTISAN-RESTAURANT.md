# Packs sectoriels — artisan de dépannage et restaurant

> Même format que le pack coiffure (`docs/05-QUESTIONNAIRE-ET-PACKS.md`, cadrage métier dans `docs/recherche2/A6-metier-salon.md` §5).
> Règles communes, rappelées : **jamais plus de 5 options par question**, **toujours un défaut pré-coché (★)**, un salon qui ne répond rien obtient un agent qui fonctionne. Chaque réponse porte son `ecrit` — frontmatter (machine) ou corps (prose).

---

# Pack `depannage`

**Ce qui change tout par rapport au salon** : on n'appelle pas pour réserver, on appelle **parce que quelque chose est cassé maintenant**. Et le droit impose des choses à dire **avant** l'intervention — or c'est l'agent qui parle en premier.

## Les quatre interdits, câblés avant toute question

1. **L'agent n'annonce jamais un prix total.** Taux horaire, frais de déplacement et majorations : oui, à l'oral. Le **devis écrit avant travaux** est obligatoire, et il s'établit sur place.
2. **L'agent ne qualifie jamais l'urgence** au sens juridique — elle conditionne la perte du droit de rétractation de 14 jours. Il **enregistre les faits**, l'artisan tranche.
3. **Sortie immédiate du script** sur odeur de gaz, départ de feu, personne en danger : l'agent donne le numéro des secours et raccroche le scénario. **Câblé en dur, jamais paramétrable.**
4. **La zone est une condition d'éligibilité, pas une préférence.** Le code postal se demande **avant** le créneau : mieux vaut refuser proprement que promettre puis annuler.

## Bloc A — Activité et zone

**A1. Votre métier** ☐ Plomberie ★ ☐ Serrurerie ☐ Électricité ☐ Chauffage / climatisation ☐ Multi-services
**A2. Communes ou codes postaux desservis** — liste. *(condition d'éligibilité, demandée en premier)*
**A3. Hors zone, l'agent :** ☐ Refuse poliment et explique ★ ☐ Prend le message quand même ☐ Propose un confrère
**A4. Horaires d'intervention** ☐ Heures ouvrables ★ ☐ + soirées ☐ 24 h/24
**A5. Urgences la nuit et le week-end** ☐ Oui, avec majoration ★ ☐ Non, message et rappel ☐ Seulement pour les clients existants

## Bloc B — Ce que l'agent doit dire avant tout

**B1. Frais de déplacement** — montant, annoncé à l'oral. *(obligation d'information préalable)*
**B2. Taux horaire de main-d'œuvre** — montant.
**B3. Majorations** ☐ Week-end ☐ Nuit ☐ Jours fériés → pourcentage ou montant.
**B4. Quand on demande un prix total, l'agent :** ☐ « Je ne peux pas vous donner de total, le devis se fait sur place » ★ ☐ Donne une fourchette de dépannage courant ☐ Fait rappeler
**B5. Devis** ☐ Gratuit ★ ☐ Payant, déduit si travaux ☐ Payant

## Bloc C — Qualification de la panne *(le bloc qui remplace le catalogue)*

**C1. Trois questions posées systématiquement** *(non désactivables)* : nature de la panne · **risque immédiat** (eau qui coule, plus d'électricité, porte bloquée, odeur) · **adresse exacte**.
**C2. Pannes les plus fréquentes** — liste cochable, alimente l'amorçage lexical.
**C3. Ce que vous ne faites pas** — texte libre. *(l'agent refuse au lieu de promettre)*
**C4. Les questions en plus, selon la panne** — par métier : *fuite → depuis quand, d'où, eau coupée ?* · *serrure → porte claquée ou verrouillée, vous êtes dehors ?* · *électricité → tout le logement ou une pièce, le disjoncteur a sauté ?*

## Bloc D — Créneaux et engagement

**D1. L'agent propose** ☐ Une **fourchette** (« entre 14 h et 17 h ») ★ ☐ Une heure ferme ☐ « Je vous rappelle sous 15 minutes »
**D2. Délai habituel d'intervention** ☐ Dans la journée ★ ☐ Sous 48 h ☐ Sur rendez-vous
**D3. Sur urgence déclarée, l'agent** ☐ **Transfère immédiatement** ★ ☐ Prend les coordonnées et fait rappeler ☐ Propose le premier créneau
**D4. Ce que l'agent ne promet jamais** — texte libre. *(pré-rempli : un délai ferme, un prix total, la disponibilité d'une pièce)*

---

# Pack `restaurant`

**Ce qui change tout** : l'unité réservée n'est pas une durée de praticien mais **un nombre de couverts sur une table**, avec un temps de rotation implicite. Le service est découpé en **shifts**, pas en agenda continu.

## Bloc A — Établissement et service

**A1. Type** ☐ Restaurant traditionnel ★ ☐ Bistrot / brasserie ☐ Gastronomique ☐ Pizzeria / rapide ☐ Bar à vin
**A2. Shifts** — déjeuner et dîner, avec heures de **première et dernière arrivée**. Défaut ★ : 12 h 00–13 h 30 et 19 h 30–21 h 30.
**A3. Jours de fermeture** — grille 7 jours. Défaut ★ : dimanche soir et lundi.
**A4. Durée de table (rotation)** ☐ 1 h 30 ★ ☐ 2 h ☐ 2 h 30 ☐ Pas de limite
**A5. Terrasse** ☐ Non ★ ☐ Oui, réservable ☐ Oui, non réservable *(« on ne garantit pas la terrasse »)*

## Bloc B — Couverts et groupes

**B1. Nombre de couverts** — **première question de tout appel**, avant même la date.
**B2. Capacité maximale d'une table sans arrangement** ☐ 4 ☐ 6 ★ ☐ 8 ☐ 10
**B3. À partir de combien de personnes parle-t-on d'un groupe ?** ☐ 6 ☐ 8 ★ ☐ 10 ☐ 12
⚠️ *Le seuil est **demandé, jamais supposé** — aucune source ne le fixe.*
**B4. Pour un groupe, l'agent** ☐ Prend les coordonnées et fait rappeler ★ ☐ Réserve si la place existe ☐ Transfère tout de suite
**B5. Menu de groupe imposé ?** ☐ Non ★ ☐ Oui au-delà de B3 ☐ Oui, à partir de ___

## Bloc C — Allergies, régimes, contraintes

**C1. L'agent demande-t-il les allergies à la réservation ?** ☐ Oui, systématiquement ★ ☐ Seulement si le client en parle ☐ Non
*(A6 : elles se collectent **au moment de la réservation**, pas à l'arrivée — la cuisine doit les recevoir avec la réservation.)*
**C2. Ce que la maison sait faire** ☐ Végétarien ☐ Végan ☐ Sans gluten ☐ Sans porc / halal ☐ Menu enfant — cochable.
**C3. L'agent répond-il « oui » sur un régime ?** ☐ Seulement si coché en C2 ★ ☐ Il transmet la demande sans promettre
**C4. Équipements** ☐ Chaise haute ☐ Accès PMR ☐ Chiens acceptés ☐ Parking ☐ Poussette — alimentent la FAQ.

## Bloc D — No-show et paiement

**D1. Empreinte bancaire ou prépaiement** ☐ Jamais ★ ☐ Pour les groupes ☐ Le week-end ☐ Systématiquement
**D2. Annulation sans frais jusqu'à** ☐ Le dernier moment ★ ☐ 4 h avant ☐ 24 h avant
**D3. Retard toléré avant de libérer la table** ☐ 15 min ★ ☐ 20 min ☐ 30 min
**D4. Quand c'est complet, l'agent** ☐ Propose un autre créneau ★ ☐ Propose la liste d'attente ☐ Propose d'être rappelé en cas de désistement

## Amorçage lexical — restaurant

`couverts · personnes · table · terrasse · en salle · midi · ce soir · réserver · annuler · décaler · anniversaire · menu enfant · chaise haute · poussette · PMR · parking · chien`
**Allergies et régimes** : `allergie · intolérance · gluten · arachide · fruits à coque · lactose · crustacés · œuf · végétarien · végan · sans porc · halal · casher`

---

## Ce que ces deux packs ont en commun, et que le pack coiffure n'avait pas

1. **Une information est éliminatoire et se demande en premier** — la zone chez l'artisan, le nombre de couverts au restaurant. Dans les deux cas, la poser après le créneau produit une promesse qu'il faudra retirer.
2. **Une obligation légale contraint le script** — information préalable sur les prix chez l'artisan, allergies transmises en cuisine au restaurant. Ce ne sont pas des options de confort.
3. **Un cas de sortie immédiate existe** — danger chez l'artisan, groupe hors capacité au restaurant. Ils se câblent, ils ne se paramètrent pas.

**Ce qui reste à vérifier avant de livrer ces packs** : les durées et seuils proposés ici sont des **défauts plausibles**, pas des mesures — contrairement au pack coiffure, bâti sur 12 547 lignes de prestation réelles. Il faudra les confronter à deux ou trois professionnels de chaque métier.
