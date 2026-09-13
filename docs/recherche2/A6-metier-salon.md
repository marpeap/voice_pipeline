# A6 — Recherche métier : ce qui se passe au téléphone dans un salon de coiffure / d'esthétique en France

**État : septembre 2026.** Toutes les URL ont été consultées le **13 septembre 2026**.
Destinataire : conception d'un agent vocal qui décroche à la place du gérant et pose le rendez-vous.

## Convention de marquage

| Marque | Sens |
|---|---|
| **[F]** | Fait documenté, source citée avec URL |
| **[H]** | Hypothèse de travail, dérivée d'un fait mais non mesurée telle quelle |
| **[NV]** | Non vérifié — aucune source sérieuse trouvée pendant cette recherche |

## Note de méthode (à lire avant d'exploiter les chiffres)

1. Le budget `WebSearch` de la session était **épuisé (200/200)** au démarrage. Toute la collecte s'est faite en **accès direct aux sources** (WebFetch + `curl`), sans moteur de recherche : les moteurs accessibles (DuckDuckGo, Mojeek, Brave, Startpage, SearXNG publics) renvoyaient tous un CAPTCHA ou un 403/429. Conséquence : la couverture est **excellente sur les documentations produit et les données de catalogue**, et **faible sur la presse professionnelle et les études sectorielles**, qui ne sont pas atteignables sans moteur.
2. **Corpus mesuré de première main** : j'ai aspiré les fiches de **176 établissements français réels** sur la marketplace Treatwell (`treatwell.fr/salon/<slug>`), répartis sur Paris, Lyon, Marseille, Lille, Toulouse, Bordeaux, Nantes et les pages nationales coiffure / visage / épilation / ongles. J'en tire **12 547 lignes de prestation** portant chacune un **nom réel** et une **durée réelle en minutes** (champ `durationRange.minDurationMinutes/maxDurationMinutes` du payload de la page). Toutes les statistiques de durée et de vocabulaire marquées « corpus Treatwell 176 » viennent de là. **Biais connu** : la composition de la marketplace Treatwell France sur-représente l'esthétique, l'onglerie et le massage, et sous-représente la coiffure féminine technique (couleur/balayage). Les effectifs sont donnés à chaque ligne ; ne pas citer un chiffre dont `n` est petit.
3. Aucune statistique de ce rapport n'est inventée. Là où je n'ai pas trouvé, c'est écrit **[NV]**.

---

# 1. Les intentions d'appel

## 1.1 Ce qui est établi

**[F] Les clients continuent d'appeler, même quand le salon a la réservation en ligne.** C'est écrit noir sur blanc par l'éditeur n°1 du marché français, dans un article dont l'objet même est d'aider le gérant à absorber ce flux :

> « Beaucoup de clients continuent d'appeler les établissements de beauté sur leur ligne directe pour prendre rendez-vous. »
> — Planity, *Quel message mettre sur votre répondeur téléphonique ?*, mis à jour le 2026-09-01
> https://support.planity.com/hc/fr/articles/27935760768274-Quel-message-mettre-sur-votre-r%C3%A9pondeur-t%C3%A9l%C3%A9phonique

Le même article recommande un **message pré-décroché** dont la fonction déclarée est de « **filtrer un certain nombre d'appels et de pouvoir mieux [se] concentrer sur [ses] prestations** ». **[F]** C'est l'aveu explicite, par l'éditeur, que l'appel entrant est vécu comme une **interruption de la prestation en cours** — ce qui est exactement le problème que l'agent vocal adresse.

**[F] La prise de rendez-vous par téléphone est un flux de premier plan dans le produit.** L'article Planity « Comment poser un rendez-vous ? » s'ouvre sur : « Pour ajouter un rendez-vous à la main, **comme par exemple quand un client souhaite prendre rendez-vous par téléphone** ». https://support.planity.com/hc/fr/articles/27769907712786-Comment-poser-un-rendez-vous (2026-09-10)

**[F] Le bouton « Reprendre RDV » de Planity est conçu pour l'appel téléphonique**, et il nous dit ce que le gérant fait réellement pendant l'appel :

> « Il permet de gagner du temps **lorsqu'un client vous appelle et que vous n'avez pas forcément en tête les dernières prestations dont il a bénéficié**. […] l'onglet "Reprendre RDV" vous proposera les **5 dernières prestations** prises par votre client, avec la date et l'heure du dernier rendez-vous correspondant. »
> https://support.planity.com/hc/fr/articles/27961206255378-À-quoi-sert-le-bouton-Reprendre-RDV (2026-08-29)

**Conséquence produit directe :** l'intention la plus fréquente n'est pas « je veux une coupe », c'est **« la même chose que la dernière fois »**. L'agent doit savoir résoudre *« comme d'habitude »* → dernière prestation connue du client, et le confirmer à l'oral. Sans historique client, l'agent rate la formulation la plus naturelle du métier.

**[F] Le renvoi vers le téléphone est utilisé comme sanction.** Quand un gérant bloque un client de la réservation en ligne (typiquement après des no-shows répétés), Planity affiche au client : « *Vous n'avez plus l'autorisation de prendre RDV en ligne dans ce salon. **Merci d'appeler le …*** ». https://support.planity.com/hc/fr/articles/28146055745170-Comment-empêcher-un-client-de-prendre-rendez-vous (2026-09-03)
→ **[H]** Une part non nulle des appels entrants provient de clients *volontairement exclus du canal en ligne*. L'agent vocal doit pouvoir reconnaître ce cas et **escalader au gérant** plutôt que confirmer.

**[F] L'annulation et le déplacement en ligne sont bornés par un délai paramétrable ; passé ce délai, le client n'a plus que le téléphone.**
- Planity : délais de prise et d'annulation en ligne réglables (exemple documenté : prise jusqu'à **15 minutes** avant, ouverture du calendrier **1 mois** à l'avance, annulation jusqu'à **2 jours** avant). https://support.planity.com/hc/fr/articles/27812419351698-Comment-modifier-les-délais-de-prise-et-d-annulation-de-rendez-vous (2026-09-03)
- Fresha : « Set a deadline for when clients can cancel or reschedule online. **After this time, they'll need to contact your business directly** ». https://www.fresha.com/help-center/knowledge-base/calendar/101218-manage-online-bookings-settings

→ **[H] forte :** le **report/annulation tardif est structurellement téléphonique**. Les logiciels ont volontairement fermé ce cas en ligne. C'est une intention d'appel que l'agent rencontrera beaucoup, et dont la conséquence métier (pénalité ? créneau reperdu ?) est la plus sensible.

**[F] Le choix d'un praticien précis est un objet de première classe dans l'agenda.** Planity a un bouton « **Choisi** » et une **icône cadenas** sur le rendez-vous pour marquer que « le client a spécifiquement choisi ce collaborateur » — posé à la main quand la demande arrive hors ligne. https://support.planity.com/hc/fr/articles/27961623283602-Comment-indiquer-qu-un-client-a-choisi-un-collaborateur-pour-une-prestation

**[F] La recherche de disponibilité immédiate est outillée côté comptoir.** Planity : « Comment afficher le prochain RDV de libre pour un collaborateur ? », avec cette précision capitale pour nous : « **Les disponibilités que vous visualisez sont identiques et suivent les mêmes règles que celles affichées pour vos clients** ». https://support.planity.com/hc/fr/articles/31031362423058-Comment-afficher-le-prochain-RDV-de-libre-pour-un-collaborateur (2026-09-09)
→ **[H]** L'agent vocal doit interroger **le même moteur de disponibilité** que la réservation en ligne, pas une approximation.

**[F] La liste d'attente existe et est adossée à l'e-mail, pas au téléphone.** Planity : le client coche « Me prévenir si un RDV se libère avant » et reçoit un **e-mail**. https://support.planity.com/hc/fr/articles/27978508818578-Comment-fonctionne-la-liste-d-attente (2026-09-10). Fresha propose trois politiques d'attribution : *First in line*, *Highest value*, *Offer to all*. https://www.fresha.com/help-center/knowledge-base/calendar/259-set-up-and-manage-your-waitlist
→ **[H]** Quand l'agent n'a rien à proposer, la bonne sortie n'est pas « rappelez plus tard » mais « **je vous mets en liste d'attente** » — c'est le geste que le métier a déjà.

## 1.2 Volume d'appels et taux d'appels manqués

**Je n'ai trouvé aucune statistique publiée, sérieuse et française, sur le volume d'appels ou le taux d'appels manqués d'un salon. [NV]**

Ce qui existe et qu'il ne faut **pas** citer comme une mesure :
- Phorest décrit une journée type dans « un cabinet esthétique **composite** de taille moyenne : trois praticiens, deux cabines, une salle laser, et un accueil qui **encaissait 40+ appels téléphoniques par jour** » — c'est un **cas composite illustratif**, marché UK/IE, pas une mesure. **[H] au mieux.** https://www.phorest.com/blog/the-perfectly-packed-calendar-a-day-inside-aesthetic-clinic-scheduling-software/ (2026-08-14)
- Phorest annonce « **up to 49% fewer no-shows** » avec acompte à la réservation, sans méthodologie publiée sur la page. **[NV]** en tant que chiffre opposable.

**Repères sectoriels solides, à utiliser pour dimensionner et non pour affirmer** — UNEC (organisation professionnelle de la coiffure), page « Chiffres clés de la coiffure », https://unec.fr/chiffres-cles-de-la-coiffure/ :
- **[F]** 111 200 établissements
- **[F]** 177 964 actifs, dont ~108 900 salariés et ~21 600 apprentis
- **[F]** 23 198 apprentis
- **[F]** 6,3 Md€ de chiffre d'affaires ; **2ᵉ secteur de l'artisanat**

**Recommandation :** ne pas mettre de taux d'appels manqués dans un argumentaire client tant qu'il n'est pas mesuré **sur le parc réel** (l'agent vocal est lui-même l'instrument de mesure : nombre d'appels décrochés hors horaires, pendant prestation, en double appel). C'est un livrable de la V1, pas un préalable.

## 1.3 Taxonomie d'intentions proposée (à implémenter)

Pondération **[H]** — dérivée des affordances produit listées ci-dessus (ce que les éditeurs ont jugé utile d'outiller), **pas** d'un comptage d'appels. À recalibrer sur les 500 premiers appels réels.

| # | Intention | Signaux lexicaux typiques | Ce que l'agent doit savoir faire | Poids [H] |
|---|---|---|---|---|
| 1 | **Prise de RDV** (nouveau) | « je voudrais un rendez-vous », « vous auriez de la place », « c'est possible pour… » | prestation → praticien → créneau → confirmation nom + téléphone | ●●●●● |
| 2 | **Prise de RDV « comme d'habitude »** | « la même chose que d'habitude », « comme la dernière fois », « mon rendez-vous habituel » | résoudre via l'historique client ; **reformuler la prestation à voix haute** avant de confirmer | ●●●● |
| 3 | **Report / déplacement** | « je peux décaler », « je voudrais changer l'heure », « j'ai un empêchement » | retrouver le RDV, vérifier le délai d'annulation, proposer 2-3 créneaux | ●●●● |
| 4 | **Annulation** | « je ne pourrai pas venir », « il faut que j'annule » | annuler + **appliquer ou non la politique** ; libérer le créneau ; déclencher la liste d'attente | ●●● |
| 5 | **Disponibilité immédiate** | « vous avez quelque chose là tout de suite », « aujourd'hui », « ce soir » | prochain créneau libre, **mêmes règles que la réservation en ligne** | ●●● |
| 6 | **Demande d'un praticien précis** | « avec Sophie », « c'est Karim qui me fait d'habitude » | filtrer sur compétence + contrainte horaire ; marquer « choisi » | ●●● |
| 7 | **Prix** | « c'est combien un balayage », « ça coûte combien » | annoncer le tarif **et sa variabilité** (voir §2.5 : « à partir de », longueur) | ●●● |
| 8 | **Horaires / adresse / accès** | « vous êtes ouverts le lundi », « vous êtes où » | réponse factuelle depuis la fiche établissement | ●●● |
| 9 | **Conseil / faisabilité technique** | « est-ce que c'est possible sur cheveux décolorés », « combien de temps ça prend » | **ne pas trancher** ; proposer un RDV de **consultation** (voir §2.4) ou rappel du gérant | ●● |
| 10 | **Réclamation / SAV** | « la couleur a dégorgé », « je ne suis pas contente » | **ne jamais arbitrer** ; prendre le message, escalader au gérant | ● |
| 11 | **Démarchage entrant** | fournisseur, référencement, « responsable des achats » | détecter et couper court proprement, sans rendez-vous | ● |
| 12 | **Appel pour un proche** | « c'est pour ma fille », « je réserve pour mon mari » | Planity a un parcours dédié « prendre rendez-vous pour un proche » — traiter comme un cas nominal, pas une exception. https://support.planity.com/hc/fr/articles/28218449672210-Comment-prendre-rendez-vous-pour-un-proche | ●● |

---

# 2. Le catalogue réel et les contraintes d'agenda

> **C'est le cœur du rapport.** Le logiciel hôte ne modélise aujourd'hui ni pause ni temps de pose. Cette section dit exactement ce que ça coûte.

## 2.1 Le modèle de données que le marché considère comme normal

### 2.1.1 Fresha — le modèle le plus explicite, et le plus proche de ce qu'il nous faut

Fresha distingue **deux natures de temps additionnel** attachées à une prestation, et la différence est *exactement* notre problème :

> **Blocked time** : « The client is not present, and **the team member is unavailable for new bookings**. » (ex. nettoyage/remise en état après prestation)
> **Processing time** : « **The client is still present while the team member is available to take another appointment.** » — exemple donné : la **coloration**, « where treatment needs time to develop ».
> Un **extra servicing time** optionnel peut suivre le processing time si le praticien doit revenir sur le client.
> — https://www.fresha.com/help-center/knowledge-base/catalog/101630-add-extra-time-to-services-and-appointments-1 **[F]**

C'est la **double occupation** en une phrase : pendant le temps de pose, **le fauteuil est occupé mais le praticien est libre**. Ce sont deux ressources distinctes, et un modèle qui n'a qu'une durée unique les confond.

Autres briques Fresha **[F]** :
- **Service variants** : « different versions of the same service, each with its own price and duration, such as **Short hair** or **Long hair** » — https://www.fresha.com/help-center/knowledge-base/catalog/75-create-service-variants
- **Resources** : « the rooms, equipment, or spaces […] used during appointments » (exemples : *massage couch 1/2*, sun bed, sauna) ; « When a resource is assigned to a service, it becomes unavailable for the duration of the appointment **to prevent double bookings** ». Le personnel en salon peut forcer un chevauchement, avec alerte. — https://www.fresha.com/help-center/knowledge-base/calendar/101215-create-and-manage-resources
- **Book in sequence** : « When a client books multiple services online, the services in your sequence will **always be scheduled in the order you've set**, no matter what order the client selects them in. » — https://www.fresha.com/help-center/knowledge-base/catalog/74-set-services-to-book-in-sequence
- **Service bundles**, **add-ons**, **advanced pricing and durations** (prix/durée différents selon le praticien et selon l'établissement) — https://www.fresha.com/help-center/knowledge-base/catalog/284-create-services-1

### 2.1.2 Planity — « prestation » vs « forfait », et pourquoi ça compte

Planity nomme la chose autrement, mais décrit la même réalité **[F]** :

> « Une **prestation** est un service "simple" qui est effectué par un collaborateur : coupe de cheveux, manucure, massage, etc.
> Un **forfait** est un type de prestation **nécessitant plusieurs étapes**, par exemple : un **temps d'application**, un **temps de pause**, **brushing**, **temps de rinçage** ou autre. »
> — https://support.planity.com/hc/fr/articles/28229486052370-Quelles-sont-les-différences-entre-une-prestation-et-un-forfait (2026-08-07)

Détail qui en dit long sur la complexité réelle : **le gérant ne peut pas créer un forfait lui-même.** Les deux articles concernés renvoient au service client : « *Si vous souhaitez ajouter des forfaits, **par exemple pour les colorations**, merci de bien vouloir contacter le service client au 01 86 26 44 44.* » (https://support.planity.com/hc/fr/articles/27741125976978-Comment-ajouter-une-prestation, 2026-09-10). **[H]** Le multi-étapes est jugé trop délicat pour être laissé en libre-service — c'est le signe qu'il est structurant, pas cosmétique.

Autres contraintes d'agenda Planity **[F]** :

| Mécanisme | Ce qu'il fait | Source |
|---|---|---|
| **Plusieurs collaborateurs en même temps** | case à cocher sur la prestation + **nombre de personnes requises** + **nombre de ressources** ; à l'agenda, les champs « **Avec** » (collaborateurs) et « **En** » (ressources) | [art. 28225488590226](https://support.planity.com/hc/fr/articles/28225488590226-Comment-créer-une-prestation-nécessitant-plusieurs-collaborateurs-ou-ressources-en-même-temps) |
| **Contrainte horaire** | rend une prestation réservable **seulement** pour tel collaborateur sur telle plage ; « les prestations non cochées n'auront pas de créneau horaire en ligne pour ce collaborateur uniquement » | [art. 27824504969362](https://support.planity.com/hc/fr/articles/27824504969362-Comment-mettre-une-contrainte-horaire) |
| **Limiter des plages à certaines prestations** | ex. documenté : « tous les jeudis, un collaborateur ne fait que des prestations hommes, de 10h à 19h » | [art. 27790769901586](https://support.planity.com/hc/fr/articles/27790769901586-Comment-limiter-certaines-plages-horaires-à-certaines-prestations) |
| **Limite de prestation par collaborateur et par jour** | quota journalier ; alerte à l'agenda, **franchissable en salon**, **bloquant en ligne** | [art. 33884833656978](https://support.planity.com/hc/fr/articles/33884833656978-Comment-ajouter-une-limite-de-prestation-par-collaborateur) (2026-09-10) |
| **Pause déjeuner** | posée à l'agenda, **répétable** (« tous les jours ») | [art. 27839474353170](https://support.planity.com/hc/fr/articles/27839474353170-Comment-gérer-les-pauses-déjeuner-d-une-collaborateur) |
| **Blocage d'un créneau / indisponibilité / absences / vacances / jours fériés** | quatre mécanismes distincts | art. 27820158994578, 27795117679634, 28119358175506, 28410720193810 |
| **Fréquence des créneaux en ligne** | pas de grille réglable ; « la fréquence des créneaux doit se terminer par **0 ou 5 minutes** » | [art. 29426586301714](https://support.planity.com/hc/fr/articles/29426586301714-Comment-changer-la-fréquence-des-créneaux-de-prise-de-rendez-vous-en-ligne) (2026-08-06) |
| **Délais de prise/annulation, y compris par prestation** | global **et** personnalisable prestation par prestation | art. 27812419351698 et [29425921401874](https://support.planity.com/hc/fr/articles/29425921401874-Comment-personnaliser-les-délais-de-prise-de-RDV-pour-chaque-prestation) |
| **Prestations à la suite** | le client empile plusieurs prestations ; « Les créneaux proposés s'adaptent automatiquement en fonction de vos disponibilités **et de la durée totale des prestations choisies** » | [art. 34616500952210](https://support.planity.com/hc/fr/articles/34616500952210-Ajouter-des-prestations-à-la-suite-en-ligne) (2026-09-09) |
| **Compétences** | « Seuls les agendas **ayant les compétences requises** pour la prestation apparaissent » | art. 31031362423058 |

### 2.1.3 Phorest — même mécanique, vocabulaire « gap time »

> « Built-in **gap or processing time** splits an appointment into **active treatment blocks with a bookable window in between**, so numbing or cooling periods don't sit unused. »
> « the system **blocks a slot the moment any one resource is unavailable**, not just when a provider's calendar happens to be full. »
> — https://www.phorest.com/blog/the-perfectly-packed-calendar-a-day-inside-aesthetic-clinic-scheduling-software/ (2026-08-14) **[F]**

**Synthèse [F] :** les trois éditeurs majeurs modélisent tous, avec trois noms différents (*forfait* / *processing time* / *gap time*), **le même objet** : un rendez-vous **discontinu** pour le praticien et **continu** pour le client.

## 2.2 Ce que coûte l'absence de temps de pose et de pause — chiffré

Le logiciel hôte ne sait modéliser **ni pause ni temps de pose**. Traduction opérationnelle, avec les durées mesurées (§2.3) :

| Cas | Modèle « durée unique » | Réalité métier | Coût |
|---|---|---|---|
| **Coloration racines** (médiane 60 min sur corpus, n=240) | 60 min de praticien bloqué | ~15-20 min d'application, **~25-35 min de pose praticien libre**, ~10 min rinçage + coiffage **[H]** | **~30 min de praticien gelées par coloration.** Sur un salon 2 praticiens × 3 colorations/jour, ~3 h/jour de capacité invisible. |
| **Balayage** (médiane **120 min**, n=25) | 120 min bloquées | 2 à 3 fenêtres libres dans l'intervalle **[H]** | Le créneau le plus cher du salon est aussi celui qui coûte le plus en capacité perdue. |
| **Permanente** (médiane 105 min, n=22), **lissage/défrisage** (médiane 60 min, n=222) | idem | temps de pose long | idem |
| **Pause déjeuner** non modélisée | l'agent propose 12h30 | le praticien n'est pas là | **Faux créneau proposé au téléphone.** Le pire défaut possible pour un agent vocal : il engage la parole du salon. |
| **Cabine / ressource** non modélisée (esthétique) | deux soins visage en parallèle | une seule cabine | **Double booking physique.** |
| **Enchaînement** (« coupe + couleur ») non ordonné | ordre libre | couleur **avant** coupe/brushing dans la quasi-totalité des cas **[H]** | Durée totale et ordre faux. |

**Arbitrage recommandé [H], à faire valider par Adnan :**

1. **Priorité 1 — la pause.** Ne rien modéliser d'autre tant que l'agent peut proposer un créneau pendant une pause déjeuner. C'est un défaut **visible du client** et **destructeur de confiance**. Coût d'implémentation minimal (une indisponibilité récurrente par praticien).
2. **Priorité 2 — la marge de sécurité.** En l'absence de temps de pose, **surdimensionner** la durée annoncée plutôt que la sous-dimensionner : l'agent réserve la durée totale *client présent*. On perd de la capacité, on ne crée pas de conflit. **Ne jamais faire l'inverse.**
3. **Priorité 3 — le temps de pose (double occupation).** C'est une optimisation de revenu, pas une condition de justesse. À condition d'avoir posé 1 et 2, la V1 peut vivre sans, en l'assumant explicitement auprès du salon : « *l'agenda est tenu au plus large ; vous récupérerez la capacité quand on modélisera la pose.* »
4. **Priorité 4 — la ressource/cabine.** Indispensable en **esthétique** (cabine, table de massage, appareil), secondaire en **coiffure classique**. À trancher par segment, pas globalement.

## 2.3 Durées réelles mesurées — corpus Treatwell 176 établissements FR

Durées en minutes, sur 12 547 lignes de prestation. Les colonnes p10/p90 incluent les variantes et forfaits ; **la médiane est la valeur à retenir** pour un défaut d'agenda.

### Coiffure

| Prestation | n | p10 | **médiane** | p90 | min | max |
|---|---:|---:|---:|---:|---:|---:|
| Coupe homme | 135 | 30 | **35** | 120 | 15 | 180 |
| Coupe femme | 20 | 30 | **60** | 120 | 15 | 390 |
| Coupe enfant | 29 | 15 | **30** | 30 | 5 | 195 |
| Coupe + brushing | 52 | 30 | **45** | 110 | 30 | 195 |
| Brushing | 195 | 30 | **90** | 180 | 15 | 300 |
| Coloration / couleur | 240 | 30 | **60** | 120 | 5 | 180 |
| Balayage | 25 | 10 | **120** | 165 | 5 | 195 |
| Mèches | 24 | 10 | **120** | 165 | 10 | 180 |
| Patine | 11 | 30 | **75** | 185 | 30 | 190 |
| Permanente | 22 | 35 | **105** | 150 | 10 | 180 |
| Lissage / défrisage / kératine | 222 | 30 | **60** | 105 | 5 | 240 |
| Soin capillaire (Olaplex, Tokio…) | 53 | 10 | **15** | 90 | 5 | 180 |
| Barbe | 225 | 15 | **30** | 75 | 10 | 180 |
| Chignon | 14 | 45 | **60** | 180 | 10 | 225 |
| Extensions capillaires | 20 | 15 | **30** | 150 | 15 | 150 |
| Head spa | 26 | 45 | **105** | 150 | 10 | 150 |

⚠️ **[F] mais à lire avec méfiance :** la médiane « Brushing » à 90 min est gonflée par les lignes *coloration + shampoing + brushing* qui contiennent le mot. Un brushing seul, dans le corpus, descend à p10 = 30 min. **Ne pas amorcer un défaut d'agenda sur une correspondance de sous-chaîne.**

### Esthétique / épilation / ongles

| Prestation | n | p10 | **médiane** | p90 |
|---|---:|---:|---:|---:|
| Épilation sourcils | 406 | 10 | **15** | 60 |
| Épilation lèvre supérieure | 38 | 10 | **10** | 15 |
| Épilation aisselles | 358 | 10 | **30** | 60 |
| Épilation maillot | 618 | 15 | **30** | 60 |
| Épilation jambes | 566 | 20 | **35** | 60 |
| Soin du visage | 331 | 30 | **60** | 85 |
| Massage | 898 | 30 | **60** | 95 |
| Manucure | 340 | 20 | **40** | 90 |
| Pose vernis semi-permanent | 956 | 20 | **40** | 80 |
| Pose gel / capsules / gainage | 218 | 30 | **60** | 95 |
| Remplissage | 181 | 35 | **60** | 95 |
| Dépose | 643 | 15 | **30** | 70 |
| Beauté des pieds / pédicure | 223 | 30 | **45** | 85 |
| Extension de cils | 99 | 45 | **75** | 120 |
| Rehaussement de cils | 76 | 45 | **60** | 75 |
| Teinture cils / sourcils | 198 | 15 | **30** | 75 |
| Maquillage | 82 | 30 | **60** | 90 |

### Granularité des durées — décision de grille

Sur les 12 547 durées **[F]** :

- **100,0 %** sont des multiples de **5 min**
- **68,6 %** sont des multiples de **15 min**
- **67,1 %** sont des multiples de **10 min**
- **44,4 %** sont des multiples de **30 min**
- Durées les plus fréquentes : **30 min (16,6 %)**, 60 (13,9 %), **15 (10,7 %)**, 45 (7,6 %), 20 (7,1 %), 90 (6,0 %), 10 (5,8 %), 120 (4,0 %)
- Seulement **1,3 %** des prestations ont une durée affichée **variable** (min ≠ max)

**Conclusion [F]+[H] :** la grille interne doit être **au pas de 5 minutes** — une grille au quart d'heure jetterait ~31 % du catalogue réel. Cela recoupe la règle Planity : « la fréquence des créneaux doit se terminer par 0 ou 5 minutes ». En revanche, **les créneaux proposés à l'oral** peuvent être arrondis à un pas plus large (15 ou 30 min) sans perdre en justesse : c'est la **durée** qui doit être au pas de 5, pas nécessairement **l'heure de début**.

## 2.4 Le rendez-vous de consultation — un objet à part entière

**[F]** Dans le corpus, un salon (Woody Saeie) publie **19 lignes « Consultation (uniquement) pour … »**, de **5 à 10 minutes**, une par technique sensible : *Balayage, Coloration, Décoloration, Mèches, Permanente Classique ou Digitale, Coupe Transformation, Coupe à Sec, Chignon et Coiffure de Soirée, Coiffure de Mariage, Head Spa, Soin Capillaire Anti-Chute, Soin Tokio Inkarami (+ Olaplex), Coupe Fille, Coupe Garçon…*
Le corpus contient aussi : *Consultation capillaire*, *Diagnostic Capillaire*, *Consultation préalable*, *Diagnostic du visage*, *Consultation Maquillage permanent*, *Diagnostic Epilation Définitive*. Et, en clair sur une fiche : *« Avant votre 1er rendez-vous **un entretien téléphonique est préférable** pour optimiser la prestation »*.

**Conséquence produit [H] — c'est une bonne nouvelle pour nous :** l'intention n°9 (conseil / faisabilité) a une **sortie légitime et déjà normée par le métier** : *« Je vous propose une consultation de 10 minutes avec [praticien] avant, c'est offert/rapide. »* L'agent n'a pas à trancher une question technique ; il a un objet d'agenda pour ça.

## 2.5 Le supplément cheveux longs et la variabilité du prix

**[F]** Le corpus contient **47 lignes dont le nom contient « supplément »**, dont, mot pour mot :
`Femme - Supplément cheveux longs ou épais` · `Homme - Supplément cheveux longs` · `Supplément longueur` · `Supplément coupe` · `Supplément Wavy` · `Supplément French` · `Supplément Baby Boomer` · `Supplément Nail Art` · `Supplément Extensions` · `French sur faux ongles ou ongles longs (en supplément)` · `Pose complète (gel ou capsules) supplément si longueur L XL` · `Les suppléments ajout d'une capsule`

**[F]** Et **174 lignes** portent une déclinaison de longueur explicite. Les **cinq paliers réellement employés** sont :
1. `Cheveux courts`
2. `Cheveux mi-longs` (aussi « mi-long », « Cheveux Courts & Mi longs »)
3. `Cheveux longs`
4. `Cheveux très longs` (« Cheveux très longs dépassant le milieu du dos »)
5. `Cheveux volumineux ou très denses` — **un axe distinct de la longueur**, souvent facturé et minuté comme elle

Formulations descriptives observées : « *Cheveux courts pas plus que les épaules* », « *Cheveux longs sur l'épaule jusqu'au milieu du dos* », « *Cheveux très longs dépassant le milieu du dos* ».

**[F]** Le prix est très souvent **non ferme** : le corpus est rempli de `Prix à partir de`, et Fresha modélise nativement un price type *« "From" a minimum price »* (https://www.fresha.com/help-center/knowledge-base/catalog/284-create-services-1).

→ **Règle de conception [H] :** l'agent **ne doit jamais annoncer un prix ferme** sur une prestation à longueur variable. Formulation sûre : *« C'est à partir de X €, le tarif exact dépend de la longueur — on vous le confirme au salon. »* Et il doit **demander la longueur** dès que la prestation touche à la couleur, au balayage, au brushing ou au lissage : c'est ce qui détermine la durée, donc le créneau.

## 2.6 Récapitulatif — les 12 dimensions d'agenda à couvrir

| # | Dimension | Couverte par le marché | Criticité pour l'agent vocal |
|---|---|---|---|
| 1 | Durée de base | tous | **bloquante** |
| 2 | Variante de longueur / densité | Fresha (*variants*), usage massif en FR | **bloquante** (prix + durée) |
| 3 | Compétence praticien ↔ prestation | tous | **bloquante** |
| 4 | Horaires d'ouverture + **pause déjeuner** | tous | **bloquante** |
| 5 | Absences / congés / fériés / blocages ponctuels | tous | **bloquante** |
| 6 | Délai minimum de prise (lead time) | Planity, Fresha | **bloquante** |
| 7 | Horizon max de réservation | Planity (ex. 1 mois), Fresha (jusqu'à 12 mois) | haute |
| 8 | **Temps de pose / double occupation** | Planity (*forfait*), Fresha (*processing time*), Phorest (*gap time*) | haute — **absente du logiciel hôte** |
| 9 | Ressource / cabine / appareil | Fresha, Planity, Phorest | haute en esthétique |
| 10 | Prestations enchaînées + **ordre imposé** | Fresha (*book in sequence*), Planity (*à la suite*) | haute |
| 11 | Multi-praticiens simultanés | Planity, Fresha | moyenne |
| 12 | Quota journalier par praticien | Planity | moyenne |

---

# 3. Vocabulaire réellement employé — amorçage lexical du moteur de reconnaissance

Trois sources croisées, toutes **[F]** :
- **A.** Taxonomie officielle **Planity FR** (pages de catégorie du sitemap `planity.com/sitemap-0.xml`) — c'est le vocabulaire que l'éditeur n°1 juge canonique pour le marché français.
- **B.** **12 547 noms de prestation réels** issus des 176 fiches Treatwell (corpus décrit en note de méthode).
- **C.** **Glossaire Treatwell FR** — https://www.treatwell.fr/inspiration/glossary/

## 3.1 Fréquence mesurée des termes (corpus B, nombre d'établissements sur 176 employant le terme)

```
 98 soin            76 vernis          72 épilation      68 cure          63 aisselle
 91 visage          75 semi-permanent  71 massage        67 dépose        61 manucure
 74 cils            70 sourcil         64 french         59 lissage       58 maillot
 56 gel             56 coupe           48 remplissage    47 teinture      37 extension
 37 uv              36 barbe           35 shampoing      33 gommage       33 rehaussement
 32 forfait         31 fil             29 gainage        28 capsule       26 brushing
 25 coloration      24 couleur         22 nail art       22 maquillage    12 peeling
 10 dégradé          9 botox            9 balayage        9 mèche          9 chignon
  8 tresse           8 défrisage        7 décoloration    7 ombré          7 henné
  7 patine           6 pédicure         6 permanente      6 locks          6 perruque
  6 head spa         6 nattes           6 hydrafacial     5 racines        5 tissage
  5 kératine         5 vanille          5 microblading    4 sucre          2 cryolipolyse
  2 closure          2 laser            1 lumière pulsée  1 détatouage
```
*(Rappel du biais : Treatwell FR sur-représente ongles/épilation/massage. Sur un parc coiffure pur, `coupe`, `couleur`, `balayage`, `brushing`, `mèches` remonteraient nettement.)*

## 3.2 Lexique coiffure — liste d'amorçage

**Coupe & coiffage**
`coupe` · `coupe femme` · `coupe homme` · `coupe enfant` · `coupe fille` · `coupe garçon` · `coupe étudiant` / `coupe étudiante` · `coupe à sec` · `coupe transformation` · `coupe entretien` · `coupe des pointes` · `rafraîchir les pointes` · `pointes` · `frange` · `création de frange` · `dégradé` · `fondu dégradé` · `undercut` · `blunt cut` · `bob` · `lob` · `wob` · `carré` · `carré plongeant` · `pixie` · `calligraphy cut` · `shampoing` · `brushing` · `brushing souple` · `brushing bouclé` · `séchage naturel` · `coiffage` · `boucles au fer` · `wavy` · `chignon` · `chignon de mariage` · `chignon invitée` · `coiffure de mariage` · `coiffure de soirée`

**Couleur & technique** *(le terrain de jeu principal des fautes)*
`coloration` · `couleur` · `coloration racines` · `retouche racines` · `racines` · `coloration végétale` · `coloration sans ammoniaque` · `coloration semi-permanente` · `henné` · `INOA` · `gloss` · `décoloration` · `blond polaire` · `balayage` · `french balayage` · `baby lights` · `babylights` · `mèches` · `mèches à l'aluminium` · `feuilles d'aluminium` · `papillotes` · `ombré` / `ombré hair` · `sombré` · `tie and dye` / `tie & dye` / `tie-dye` · `patine` · `reflet` · `nuancier` · `shatush` · `contouring`

**Transformation & soin**
`permanente` · `permanente digitale` · `lissage` · `lissage brésilien` · `lissage à la kératine` · `kératine` · `botox capillaire` · `défrisage` · `défrisage contour` · `soin capillaire` · `Olaplex` · `Tokio Inkarami` · `masque` · `head spa` · `rituel japonais` · `soin anti-chute` · `diagnostic capillaire` · `consultation capillaire`

**Cheveux texturés / afro** *(présent dans le corpus, souvent oublié des lexiques génériques)*
`coiffure afro` · `tressage` · `tresses` · `nattes` · `nattes collées` · `vanilles` · `twists` · `barrel twist` · `coils` · `locks` · `entretien locks` · `crochet` · `tissage` · `closure` · `perruque` · `pose de perruque` · `extensions` · `extensions à la kératine` · `mèche` (au sens *rajout*, homonyme piégeux de `mèches` coloration) · `défrisage`

**Barbier**
`barbe` · `taille de barbe` · `taille de barbe au rasoir` · `taille de barbe à la tondeuse` · `entretien barbe` · `soin barbe` · `coloration barbe` · `rasage` · `rasage traditionnel` · `moustache` · `taille de moustache` · `contours` · `dégradé américain`

**Longueur & supplément** (obligatoire, voir §2.5)
`cheveux courts` · `cheveux mi-longs` · `cheveux longs` · `cheveux très longs` · `cheveux épais` · `cheveux volumineux` · `cheveux denses` · `supplément cheveux longs` · `supplément longueur` · `prix à partir de`

## 3.3 Lexique esthétique — liste d'amorçage

**Épilation** — le domaine le plus riche et le plus normé du corpus
`épilation` · `épilation à la cire` · `cire chaude` · `cire tiède` · `cire roll-on` · `épilation orientale` · `sucre` / `sugaring` · `épilation au fil` · `épilation à la lumière pulsée` · `épilation au laser` · `épilation définitive`
Zones : `sourcils` · `lèvre supérieure` · `menton` · `visage` · `aisselles` · `bras` · `demi-bras` · `bras entiers` · `demi-jambes` · `jambes complètes` · `jambes entières` · `cuisses` · `maillot` · `maillot classique` · `maillot échancré` · `maillot semi-intégral` · `maillot brésilien` · `maillot intégral` · `SIF` (*sillon interfessier* — sigle prononcé « sif », **piège de reconnaissance majeur**) · `sillon interfessier` · `fesses` · `dos` · `torse` · `ventre` · `épaules` · `nez` · `oreilles` · `corps entier`

**Soins du visage & corps**
`soin du visage` · `soin visage` · `nettoyage de peau` · `gommage` · `gommage corps` · `masque` · `peeling` · `microneedling` · `microdermabrasion` · `dermaplaning` · `hydrafacial` · `BB glow` · `radiofréquence` · `LPG` · `soin anti-âge` · `soin minceur` · `drainage lymphatique` · `madérothérapie` · `cryolipolyse` · `cryothérapie` · `modelage` · `massage` (`californien`, `suédois`, `thaïlandais`, `ayurvédique`, `kobido`, `shiatsu`, `aux pierres chaudes`, `aux huiles chaudes`, `des pieds`, `Renata`) · `réflexologie` · `hammam` · `sauna` · `UV` · `bronzage` · `blanchiment dentaire`

**Regard**
`extension de cils` · `cil à cil` · `volume russe` · `2D` `3D` `4-6D` `7-12D` · `effet mascara` · `remplissage` · `dépose` · `rehaussement de cils` · `lamination` · `teinture des cils` · `teinture des sourcils` · `brow lift` · `épilation des sourcils` · `restructuration des sourcils` · `ligne de sourcils` · `microblading` · `microshading` · `powder brow` · `maquillage permanent` · `maquillage semi-permanent` · `candy lips` · `lip blush`

**Ongles**
`manucure` · `manucure russe` · `manucure japonaise` · `beauté des mains` · `beauté des pieds` · `pédicure` · `pose de vernis` · `vernis semi-permanent` · `semi-permanent` (souvent abrégé « **le semi** ») · `vernis classique` · `vernis en poudre` · `ongles en gel` · `pose de gel` · `capsules` · `faux ongles` · `résine` · `acrylique` · `gainage` · `remplissage` · `dépose` · `french` · `french manucure` · `baby boomer` / `babyboomer` · `nail art` · `chrome` · `œil de chat` / `cat eye` · `nacré` · `paillettes` · `strass` · `ongles ballerine` · `limage` · `cuticules`

## 3.4 Variantes orthographiques et pièges de reconnaissance — à injecter tels quels

Toutes ces formes ont été **observées dans le corpus réel** ou sont des homophones directs à couvrir **[F] / [H]** :

| Forme canonique | Variantes et fautes à mapper |
|---|---|
| balayage | *balayage*, « balliage », « ballayage », « ba-layage » ; **homophone piège : `balayage` vs `nettoyage`** |
| ombré hair | *ombré*, *ombre hair*, « hombré », *sombré*, *tie and dye*, *tie & dye*, *tie-dye*, « taille and daï » |
| patine | *patine*, « patinne » ; **piège : `patine` vs `platine` (blond platine)** — deux prestations différentes |
| mèches | *mèche*, *meche*, *mèches*, *mech* ; **collision sémantique** : `mèches` (coloration) vs `mèche` (rajout capillaire afro) — désambiguïser par le contexte |
| brushing | *brushing*, « broching », « brossing », *brushing souple/bouclé* |
| permanente | *permanente*, *permanente digitale* ; **collision majeure : `permanente` (cheveux) vs `semi-permanent` (vernis) vs `maquillage permanent`** |
| lissage | *lissage*, *lissage brésilien*, *lissage kératine*, *kératine*, « keratine », *botox capillaire*, *défrisage*, « defrisage » |
| extensions | *extension*, *extensions*, *rajouts*, *extensions à la kératine*, *extension de cils* — **désambiguïser cheveux / cils** |
| épilation | *épilation*, *epilation*, « epillation », *cire*, *wax*, *sugaring*, *au fil* |
| SIF | *sif*, *S.I.F.*, *sillon interfessier* — **sigle prononcé, très mal transcrit** |
| semi-permanent | *semi permanent*, *semi-permanent*, « **le semi** », *SP*, *vernis SP* |
| dépose | *dépose*, *depose*, « dépause », *enlever le semi*, *retirer le gel* |
| baby boomer | *baby boomer*, *babyboomer*, *baby-boomer*, « babibumer » |
| french | *french*, *french manucure*, *french blanc*, *french relevé* |
| gainage | *gainage*, « guinage », *gainage gel* |
| rehaussement | *rehaussement*, *réhaussement*, *rehaussement de cils*, *lash lift* |
| head spa | *head spa*, « hed spa », *rituel japonais* |
| Olaplex | *Olaplex*, « olapleks », « holaplex » |
| forfait | *forfait*, *formule*, *pack*, *cure*, *abonnement* |
| entretien | *entretien*, *entretient* (**faute présente telle quelle dans le corpus**), *retouche*, *reprise*, *remplissage* |

**Règles de désambiguïsation à coder [H] :**
- `permanente` + contexte ongles/vernis → **semi-permanent**, jamais la permanente capillaire.
- `mèche` au singulier + contexte tresses/nattes/tissage → **rajout**, pas coloration.
- `extension` seul → **demander** « des cils ou des cheveux ? ». Ne jamais deviner.
- `remplissage` → ongles par défaut (n=181 dans le corpus) **sauf** contexte cils (« remplissage volume russe »).
- `soin` seul → ambigu entre capillaire, visage et corps → **demander**.

---

# 4. Les règles de maison usuelles

## 4.1 Acompte / arrhes — le cadre légal français

**[F]** Service-Public, *Acompte, avance, arrhes et avoir : quelles différences ?* — https://www.service-public.gouv.fr/particuliers/vosdroits/F31187

- **Acompte** : « un **1er versement** sur l'achat d'une marchandise ou d'une prestation de services ». **Engage les deux parties.** Si le client annule, il perd l'acompte et le professionnel peut exiger l'exécution forcée ou des dommages-intérêts.
- **Arrhes** : « une **partie de la somme** versée d'avance ». **Chacune des parties peut se dédire.** Le client qui annule perd les arrhes ; **le professionnel qui n'exécute pas rembourse le double.**
- **Avance** : juridiquement traitée comme des arrhes.
- **Présomption par défaut — décisive : « En l'absence de précision, les sommes versées sont présumées être des arrhes. »**
- Base : **Code de la consommation, articles L214-1 à L214-3**.

→ **Conséquence directe pour l'agent vocal [H] :** lorsqu'il annonce un prépaiement à l'oral, **le terme employé engage juridiquement le salon**. Le script doit dire **exactement** ce que le salon a paramétré, et par défaut le plus prudent est de dire « **des arrhes** » ou d'employer le mot que le salon utilise dans ses CGV — jamais « acompte » par confort de langage.

## 4.2 Ce que les logiciels permettent de paramétrer

### Planity **[F]**
Source : https://support.planity.com/hc/fr/articles/28251675841298-Comment-activer-et-gérer-le-prépaiement-des-réservations-en-ligne (2026-09-12) et https://support.planity.com/hc/fr/articles/28168892345874-À-quoi-sert-l-avance-et-comment-l-utilise-t-on (2026-09-11)

- **Prépaiement** : **avance** (pourcentage) ou **paiement total**, au moment de la réservation en ligne. Objectif annoncé : « garantir une avance ou un paiement total […] peu importe si le client honore ou non son rendez-vous » et « **réduire le taux d'annulation tardive ou de "non venu"** ».
- Le client a deux options : « régler une partie maintenant (avance) et le reste sur place » ou « régler l'intégralité tout de suite ».
- **Délai à partir duquel l'annulation devient payante** — exemple documenté : « si l'annulation se déroule **24h avant** le RDV, elle est gratuite, sinon elle sera payante ».
- **Montant de la pénalité d'annulation tardive** et **montant de la pénalité de non-venue**, réglés séparément, en % du montant de la prestation.
- **Activable/désactivable prestation par prestation**, ou par catégorie.
- Côté agenda : boutons **« Pas venu »** et **« Supprimer »** ; dans les deux cas une fenêtre demande **si l'on applique la pénalité** → **[F] la pénalité reste une décision humaine, prestation par prestation**. L'agent vocal ne doit jamais l'appliquer de lui-même.
- Les frais de transaction peuvent être supportés par l'établissement **ou** refacturés au client (« frais bancaires côté utilisateur »).

### Fresha **[F]**
- Frais de no-show et d'annulation : « Enter the amount to charge the client, **up to the limit agreed in your payment policy** » ; les pourcentages sont définis dans la *payment policy*, en amont. **« A no-show fee cannot be reversed once it has been charged. »** L'option de marquer un no-show n'est disponible **qu'après l'heure de début et jusqu'à la fin de la même journée**. https://www.fresha.com/help-center/knowledge-base/payments/617-charge-no-show-and-cancellation-fees
- Réservation en ligne : **délai minimum** (« from Immediately up to 2 weeks before start time »), **horizon maximum** (« up to 12 months in the future »), **deadline d'annulation/report** au-delà de laquelle il faut appeler. https://www.fresha.com/help-center/knowledge-base/calendar/101218-manage-online-bookings-settings
- **Blocage d'un client** de la réservation en ligne : https://www.fresha.com/help-center/knowledge-base/clients/346-block-clients-from-booking
- **Motifs d'annulation** normalisés : https://www.fresha.com/help-center/knowledge-base/calendar/545-manage-cancellation-reasons
- **Allergies** et **patch tests** enregistrés sur la fiche client (https://www.fresha.com/help-center/knowledge-base/clients/53-record-an-allergy, .../55-record-client-patch-tests) → **[H]** en coloration, le **test d'allergie préalable** est un prérequis métier dont l'agent doit savoir parler pour un nouveau client.
- **Alertes équipe** sur la fiche client : https://www.fresha.com/help-center/knowledge-base/clients/54-add-staff-alerts-to-client-profiles

### Rappels et no-show **[F]**
Planity : SMS de rappel **24 h avant** si le RDV est à plus de 24 h ; **dans les 10 minutes suivant la prise** si le RDV est à moins de 24 h. Avertissement documenté : si le gérant déplace ou supprime un RDV à moins de 24 h, **le SMS de rappel est déjà parti et le client ne le sait pas**. https://support.planity.com/hc/fr/articles/27847088525586-Comment-fonctionnent-les-SMS-de-rappel (2026-09-11)
→ **[H]** Si l'agent vocal déplace un RDV à moins de 24 h, il doit **le dire explicitement au client à l'oral** : « vous allez peut-être recevoir un SMS avec l'ancien horaire, ne le prenez pas en compte ».

### Prestations réservées à un praticien **[F]**
Voir §2.1.2 : « contrainte horaire », « limiter certaines plages horaires à certaines prestations », « compétences », « limite de prestation par collaborateur ». La réservation à un praticien précis n'est pas une préférence, c'est une **règle d'agenda** que le moteur applique.

### Retard **[NV]**
Aucune source produit ou professionnelle trouvée décrivant une **politique de retard** paramétrable (tolérance en minutes, requalification en no-show). Les logiciels consultés gèrent l'annulation et la non-venue, **pas le retard**. À traiter comme une **règle de maison en texte libre**, posée à l'onboarding et lue par l'agent, pas comme un objet de données.

## 4.3 Ce que l'agent vocal ne doit jamais faire

1. **Annoncer un prix ferme** sur une prestation à longueur/densité variable (§2.5).
2. **Appliquer ou annuler une pénalité** — c'est une décision humaine dans tous les logiciels consultés.
3. **Trancher une question technique** (« est-ce que ma décoloration va tenir ? ») — proposer une **consultation** (§2.4).
4. **Traiter une réclamation.**
5. **Confirmer un créneau** sans avoir vérifié pause, absence, compétence et délai minimum.
6. **Employer « acompte » pour « arrhes »**, ou l'inverse (§4.1).

---

# 5. Deux autres métiers, plus brièvement

## 5.1 Artisan de dépannage — urgence, qualification, zone

Le déclencheur n'est pas le même : on n'appelle pas pour réserver, on appelle **parce que quelque chose est cassé maintenant**. Le cadre légal français impose des choses à dire **avant** l'intervention, et l'agent est le premier à parler.

**[F]** Service-Public, *Dépannage à domicile* — https://www.service-public.gouv.fr/particuliers/vosdroits/F38350
- Secteurs couverts : plomberie, électricité, serrurerie, chauffage/climatisation, couverture, maçonnerie, réparation d'appareils.
- **Devis écrit détaillé avant le début des travaux.** Facture obligatoire **dès que la prestation dépasse 25 € TTC**.
- Doivent être communiqués **avant intervention** : **taux horaire de main-d'œuvre**, **frais de déplacement**, **majorations** week-end / jours fériés / nuit, et une **estimation chiffrée**.
- **Délai de rétractation de 14 jours** pour les contrats conclus à distance ou à domicile, **qui ne s'applique pas en cas d'urgence réelle** (fuite d'eau, panne électrique).

**Conséquences de conception [H] :**
- **Qualifier avant de promettre.** Trois questions non négociables : *quelle est la panne ?* · *est-ce qu'il y a un risque immédiat (eau qui coule, plus d'électricité, porte bloquée, odeur de gaz) ?* · *quelle adresse exacte ?*
- **La zone est une condition d'éligibilité, pas une préférence.** Poser le code postal **avant** le créneau ; refuser proprement hors zone plutôt que promettre.
- **L'agent doit énoncer le déplacement et le taux horaire à l'oral**, et **ne jamais annoncer un prix total** — le devis est établi sur place.
- **Il ne doit pas qualifier lui-même l'urgence** au sens juridique (elle conditionne la perte du droit de rétractation) : il enregistre les faits, l'artisan tranche.
- **Odeur de gaz / départ de feu / personne en danger → sortie immédiate du script** vers les secours. À câbler en dur.
- Créneaux typiques : **fourchettes** (« entre 14 h et 17 h »), pas des heures fermes. **[H]**

## 5.2 Restaurant — couverts, créneaux, allergies, groupes

**[F]** Zenchef (éditeur français de réservation restaurant) — https://www.zenchef.com/fr : **plan de salle** (« Gérez chaque réservation, de la première prise en ligne au service en salle »), **prévention des no-shows** (« Réduisez les no-shows grâce à des outils de paiement intelligents », **prépaiements**), **liste d'attente**, **fichier clients** (« des expériences culinaires plus personnalisées »), **widget de réservation**, et — mention explicite dans un témoignage client — **assistant téléphonique**. Le marché restaurant français a donc **déjà** la catégorie « agent au téléphone ».

**Différences structurelles avec le salon [H] :**
- L'unité réservée n'est **pas une durée de praticien** mais **un nombre de couverts sur une table**, avec un **temps de rotation** implicite. Le nombre de couverts est la **première** information à obtenir, avant même la date.
- Le service est **découpé en shifts** (déjeuner / dîner) avec des **créneaux d'arrivée**, pas un agenda continu.
- **Groupes** : au-delà d'un seuil (souvent 6 à 8 personnes **[NV]**), le traitement change — menu de groupe, empreinte bancaire, validation humaine. **Seuil à demander à l'onboarding, jamais à supposer.**
- **Allergies et régimes** : à collecter **au moment de la réservation**, pas à l'arrivée. Fresha montre qu'un champ allergie structuré existe déjà côté beauté ; côté restaurant c'est une **note de réservation** transmise en cuisine. Vocabulaire minimal à amorcer : `allergie`, `intolérance`, `gluten`, `arachide`, `fruits à coque`, `lactose`, `crustacés`, `œuf`, `végétarien`, `végan`, `sans porc`, `halal`, `casher`, `poussette`, `chaise haute`, `PMR`, `terrasse`, `anniversaire`.
- **Intentions d'appel supplémentaires** : « vous avez de la place ce soir ? », « est-ce que vous avez une terrasse », « on peut venir avec un chien », « jusqu'à quelle heure vous servez », « vous faites un menu enfant ».

---

# 6. Proposition de pack sectoriel coiffure

## 6.1 Questionnaire d'onboarding

Conçu pour être rempli **en une fois, par le gérant, à l'oral ou en 15 clics**. Réponses cochables par défaut ; texte libre seulement où c'est inévitable. Chaque réponse alimente directement soit le moteur de créneaux, soit le script de l'agent.

> **Règle de conception appliquée (Miller / Hick) :** aucune question n'offre plus de 5 options, et chaque question a **un défaut recommandé** pré-coché, marqué **★**. Un salon qui ne répond rien doit obtenir un agent qui fonctionne.

### Bloc A — Identité et horaires

**A1. Type d'établissement**
☐ Salon de coiffure mixte ★ ☐ Coiffure femme ☐ Barbier / coiffure homme ☐ Coiffure afro / cheveux texturés ☐ Salon + institut

**A2. Jours et horaires d'ouverture** — grille 7 jours × (ouverture, fermeture)
Défaut ★ : mardi–samedi, 9 h 00 – 19 h 00, fermé dimanche et lundi.

**A3. Coupure / pause déjeuner** *(question critique — §2.2)*
☐ Pas de coupure, service continu ☐ Coupure commune à tout le salon, de ___ à ___ ★ *(défaut 12 h 30 – 13 h 30)* ☐ Chaque coiffeur a sa propre pause (préciser au bloc B)

**A4. Fermetures annuelles connues** — texte libre, dates.

**A5. Que dit l'agent s'il ne sait pas répondre ?**
☐ « Je note votre demande, [prénom du gérant] vous rappelle » ★ ☐ Transférer l'appel maintenant ☐ Proposer d'envoyer un SMS

### Bloc B — L'équipe

Pour chaque coiffeur : **prénom** (tel qu'un client le prononce au téléphone), **jours travaillés**, **pause si différente de A3**.

**B1. Un client peut-il demander un coiffeur précis ?**
☐ Oui, tous ★ ☐ Oui, sauf les apprentis ☐ Non, on attribue nous-mêmes

**B2. Y a-t-il des prestations qu'un seul coiffeur sait faire ?**
☐ Non ★ ☐ Oui → lesquelles, et par qui *(→ alimente la table de compétences)*

**B3. Si le coiffeur demandé n'est pas libre, l'agent doit :**
☐ Proposer le premier créneau de **ce** coiffeur, même plus tard ★ ☐ Proposer un autre coiffeur à l'horaire souhaité ☐ Proposer les deux et laisser choisir

### Bloc C — Le catalogue *(le bloc qui fait la justesse des créneaux)*

**C1. Cochez vos prestations** — liste pré-remplie avec **durée par défaut = médiane mesurée (§2.3)**, modifiable :

| ☐ | Prestation | Durée proposée |
|---|---|---|
| ★ | Coupe homme | 35 min |
| ★ | Coupe femme (sans brushing) | 60 min |
| ★ | Coupe + brushing | 45 min |
| ★ | Coupe enfant | 30 min |
| ★ | Brushing seul | 30 min |
| ★ | Shampoing + coupe + coiffage | 60 min |
| ☐ | Coloration racines | 60 min |
| ☐ | Coloration complète | 90 min |
| ☐ | Balayage | 120 min |
| ☐ | Mèches | 120 min |
| ☐ | Patine / gloss | 45 min |
| ☐ | Décoloration | 120 min |
| ☐ | Permanente | 105 min |
| ☐ | Lissage / défrisage | 60 min |
| ☐ | Soin capillaire (Olaplex, Tokio…) | 15 min |
| ☐ | Head spa | 105 min |
| ☐ | Chignon / coiffure de soirée | 60 min |
| ☐ | Coiffure de mariage (+ essai) | 120 min |
| ☐ | Barbe / taille de barbe | 30 min |
| ☐ | Extensions / tresses / tissage | à préciser |
| ☐ | Consultation avant technique | 10 min |

**C2. Le prix change-t-il selon la longueur des cheveux ?**
☐ Oui, sur toutes les prestations techniques ★ ☐ Oui, seulement sur ___ ☐ Non, prix unique

**C3. Quels paliers de longueur employez-vous ?** *(vocabulaire mesuré, §2.5)*
☐ Courts / Longs ☐ Courts / Mi-longs / Longs ★ ☐ Courts / Mi-longs / Longs / Très longs ☐ + un palier « cheveux épais ou très denses »

**C4. Combien de temps en plus sur cheveux longs ?**
☐ +15 min ☐ +30 min ★ ☐ +45 min ☐ On double la durée ☐ Variable, l'agent doit demander au salon

**C5. Que dit l'agent quand on demande un prix ?**
☐ Le prix exact ☐ « À partir de X € » ★ ☐ Une fourchette ☐ « Je préfère que le salon vous le confirme »

**C6. Quelles prestations le client enchaîne-t-il le plus souvent ?**
☐ Coupe + couleur ★ ☐ Coupe + brushing ★ ☐ Couleur + balayage ☐ Coupe + barbe ☐ Autre : ___
→ *et dans quel ordre ?* ☐ Toujours la technique avant la coupe ★ ☐ Toujours la coupe avant ☐ Ça dépend

**C7. Pendant le temps de pose d'une couleur, le coiffeur :** *(pour préparer le modèle, même si la V1 ne l'exploite pas)*
☐ Reste avec la cliente ☐ Prend un autre client ★ ☐ Ça dépend du coiffeur
→ *Combien de temps est-il réellement libre ?* ___ min

**C8. Faites-vous un rendez-vous de consultation avant les grosses techniques ?**
☐ Non ★ ☐ Oui, obligatoire pour balayage/décoloration ☐ Oui, proposé si le client hésite

**C9. Test d'allergie (coloration, nouvelle cliente) :**
☐ On le fait le jour même ★ ☐ RDV séparé 48 h avant, obligatoire ☐ On ne le pratique pas

### Bloc D — Règles de maison

**D1. Délai minimum pour prendre un RDV par téléphone :**
☐ Tout de suite, même dans 15 min ☐ 1 h avant ★ ☐ La veille ☐ 24 h avant

**D2. Jusqu'à quand peut-on réserver à l'avance :**
☐ 1 mois ☐ 2 mois ★ ☐ 3 mois ☐ 6 mois

**D3. Demandez-vous des arrhes ou un acompte ?** *(§4.1 — l'agent répétera exactement ce mot)*
☐ Jamais ★ ☐ Oui, pour les prestations longues (balayage, extensions, mariage) ☐ Oui, pour les nouveaux clients ☐ Oui, systématiquement
→ *Montant :* ___ % · → *Vous le nommez :* ☐ **arrhes** ★ ☐ **acompte** ☐ « réservation »

**D4. Délai d'annulation sans frais :**
☐ Jusqu'au dernier moment ★ ☐ 24 h avant ☐ 48 h avant ☐ 72 h avant

**D5. En cas d'annulation tardive ou de client qui ne vient pas, l'agent doit :**
☐ Rappeler la règle à l'oral, sans rien facturer ★ ☐ Rappeler la règle et prévenir que des frais s'appliquent ☐ Ne rien dire, le salon gère
*(Dans tous les cas, l'agent n'applique jamais la pénalité lui-même — §4.2.)*

**D6. Retard toléré avant d'écourter ou d'annuler :**
☐ 5 min ☐ 10 min ★ ☐ 15 min ☐ Ça dépend, on rappelle le client
→ *Au-delà, l'agent dit :* ___ (texte libre, une phrase)

**D7. Liste d'attente quand il n'y a plus de place :**
☐ Oui, l'agent propose de rappeler si ça se libère ★ ☐ Non, l'agent propose juste une autre date

**D8. Clients qu'on ne prend plus / à signaler :**
☐ Aucun ★ ☐ Oui → l'agent doit alors **passer la main au gérant** sans confirmer de RDV

**D9. L'agent peut-il déplacer un RDV existant ?**
☐ Oui, librement ★ ☐ Oui, mais pas à moins de 24 h ☐ Non, il note et le salon rappelle

**D10. Trois choses à ne surtout pas dire au téléphone :** texte libre.

### Bloc E — Voix et ton

**E1. Comment l'agent se présente :**
☐ « [Nom du salon], bonjour » ★ ☐ « Bonjour, [Nom du salon], je vous écoute » ☐ Phrase personnalisée : ___

**E2. Vouvoiement :** ☐ Toujours ★ ☐ Tutoiement (salon jeune / barbier)

**E3. Dit-il qu'il est un assistant automatique ?**
☐ Oui, dès le début ★ ☐ Seulement si on le lui demande

**E4. Langues :** ☐ Français seulement ★ ☐ Français + anglais ☐ + autre : ___

## 6.2 Liste d'amorçage lexical — coiffure

À injecter telle quelle dans le biasing du moteur de reconnaissance. **Groupe 1** = poids fort (toujours actif). **Groupe 2** = poids moyen. **Groupe 3** = activé seulement si le salon a coché la prestation correspondante en C1 (réduit les faux positifs).

### Groupe 1 — noyau, toujours actif

```
rendez-vous · prendre rendez-vous · déplacer · décaler · reporter · annuler · changer l'heure
aujourd'hui · demain · après-demain · cette semaine · la semaine prochaine · ce matin · cet après-midi
ce soir · en fin de journée · samedi · lundi · mardi · mercredi · jeudi · vendredi
le plus tôt possible · dès que possible · quand vous voulez · ça m'est égal · comme d'habitude
la même chose que la dernière fois · avec [prénom] · c'est pour moi · c'est pour ma fille
c'est pour mon fils · c'est pour mon mari · c'est combien · vous êtes ouverts · vous fermez à quelle heure
coupe · coupe femme · coupe homme · coupe enfant · shampoing · brushing · couleur · coloration
balayage · mèches · racines · soin · barbe · cheveux courts · cheveux mi-longs · cheveux longs
```

### Groupe 2 — technique courante

```
coupe + brushing · coupe et brushing · rafraîchir les pointes · pointes · frange · dégradé
coiffage · séchage · wavy · boucles · chignon · coiffure de mariage · coiffure de soirée
coloration racines · retouche racines · couleur complète · coloration végétale
coloration sans ammoniaque · henné · gloss · patine · reflet · décoloration · blond polaire
baby lights · babylights · french balayage · ombré · ombré hair · sombré
tie and dye · tie & dye · tie-dye · shatush · contouring
permanente · permanente digitale · lissage · lissage brésilien · kératine · lissage à la kératine
botox capillaire · défrisage · soin capillaire · Olaplex · Tokio · Tokio Inkarami · masque
head spa · rituel japonais · diagnostic capillaire · consultation · consultation capillaire
extensions · rajouts · extensions à la kératine · taille de barbe · rasage · moustache · contours
cheveux très longs · cheveux épais · cheveux volumineux · cheveux denses
supplément cheveux longs · supplément longueur · à partir de · forfait · formule
```

### Groupe 3 — conditionnel (activer selon C1)

```
[si afro/texturé]  coiffure afro · tressage · tresses · nattes · nattes collées · vanilles
                   twists · barrel twist · coils · locks · entretien locks · crochet
                   tissage · closure · perruque · pose de perruque · mèche (rajout)
                   défrisage contour · départ en twist
[si barbier]       dégradé américain · fade · undercut · taille au rasoir · taille à la tondeuse
                   soin barbe · coloration barbe · serviette chaude
[si institut]      épilation · cire · cire chaude · cire tiède · sucre · au fil · maillot
                   maillot classique · maillot échancré · maillot semi-intégral · maillot brésilien
                   maillot intégral · SIF · sillon interfessier · aisselles · demi-jambes
                   jambes complètes · sourcils · lèvre supérieure · soin du visage · gommage
                   peeling · massage · modelage
[si onglerie]      manucure · beauté des mains · beauté des pieds · pédicure · vernis
                   vernis semi-permanent · le semi · pose de gel · ongles en gel · capsules
                   faux ongles · résine · gainage · remplissage · dépose · french
                   french manucure · baby boomer · nail art · chrome · œil de chat
[si cils/sourcils] extension de cils · cil à cil · volume russe · rehaussement · lash lift
                   teinture · brow lift · microblading · microshading · maquillage permanent
```

### Formes fautives et homophones à mapper explicitement

Toutes les entrées du tableau §3.4 sont à charger comme **alias** vers la forme canonique, avec en priorité absolue les six collisions qui produisent un **mauvais rendez-vous** et pas seulement une mauvaise transcription :

| Collision | Résolution |
|---|---|
| `permanente` (cheveux) ↔ `semi-permanent` (vernis) ↔ `maquillage permanent` | trancher sur le contexte ongles/cils, sinon **demander** |
| `mèches` (coloration) ↔ `mèche` (rajout afro) | contexte tresses/tissage → rajout |
| `extension` cils ↔ cheveux | **toujours demander** |
| `patine` ↔ `platine` | deux prestations réelles, **demander** |
| `soin` capillaire ↔ visage ↔ corps | **demander** |
| `remplissage` ongles ↔ cils | défaut ongles, sauf contexte cils |

---

# 7. Annexe — inventaire des sources

Toutes consultées le **13 septembre 2026**.

**Éditeurs de logiciels de réservation**
- Planity, centre d'aide FR (Zendesk), ~200 articles inventoriés : https://support.planity.com/hc/fr — articles cités : 27741125976978, 28229486052370, 28225488590226, 34616500952210, 27978508818578, 27812419351698, 29425921401874, 29426586301714, 27935760768274, 28251675841298, 27824504969362, 27790769901586, 33884833656978, 27839474353170, 28146055745170, 27961623283602, 31031362423058, 27961206255378, 27847088525586, 27796320734738, 28168892345874, 27769907712786, 28218449672210
- Planity, taxonomie officielle des prestations FR : https://www.planity.com/sitemap-0.xml (pages `coiffeur/*`, `barbier/*`, `institut-de-beaute/*`, `manucure-et-pedicure/*`, `spa/*`)
- Fresha, help center : https://www.fresha.com/help-center/knowledge-base — articles 101630 (extra time), 284 (create services), 75 (variants), 101215 (resources), 74 (book in sequence), 101218 (online booking settings), 617 (no-show/cancellation fees), 259 (waitlist), 545 (cancellation reasons), 346 (block clients), 53/54/55 (allergies, alertes, patch tests)
- Phorest : https://www.phorest.com/blog/the-perfectly-packed-calendar-a-day-inside-aesthetic-clinic-scheduling-software/
- Zenchef (restaurant) : https://www.zenchef.com/fr
- Treatwell : glossaire https://www.treatwell.fr/inspiration/glossary/ ; corpus de 176 fiches `https://www.treatwell.fr/salon/<slug>/`
- **Non exploitables cette session** : Treatwell Pro (`pro.treatwell.fr`, SPA sans rendu serveur), Booksy (`help.booksy.com` → 403), Kitry (`kitry.com`, site vitrine sans documentation fonctionnelle publique), Merlin (aucun domaine officiel identifié sans moteur de recherche). **[NV]**

**Organisations professionnelles et sources officielles**
- UNEC, Chiffres clés de la coiffure : https://unec.fr/chiffres-cles-de-la-coiffure/
- Service-Public, *Acompte, avance, arrhes et avoir* : https://www.service-public.gouv.fr/particuliers/vosdroits/F31187
- Service-Public, *Dépannage à domicile* : https://www.service-public.gouv.fr/particuliers/vosdroits/F38350
- **Non consultés** : CNEC (`cnec.fr` joignable mais non exploré faute de budget), DGCCRF et Legifrance (403 sur les pages ciblées). **[NV]**

**Artefacts de travail** (dans le scratchpad de session, non versionnés) : `rows.json` (12 547 lignes prestation/durée), `slugs.txt` (176 établissements), `planity_arts.json` (200 articles Planity).

## Ce qui manque et comment le combler

| Manque | Marque | Comment le combler |
|---|---|---|
| Volume d'appels et taux d'appels manqués en salon FR | **[NV]** | Instrumenter l'agent en V1 : appels hors horaires, pendant prestation, doubles appels. C'est notre donnée propriétaire. |
| Répartition réelle des intentions | **[H]** | Étiqueter les 500 premiers appels réels et recalibrer le §1.3. |
| Durée réelle du temps de pose par technique | **[NV]** | Question C7 de l'onboarding + mesure sur les RDV réels. |
| Politique de retard | **[NV]** | Aucun logiciel ne la modélise : question D6, texte libre. |
| Seuil « groupe » en restaurant | **[NV]** | Question d'onboarding restaurant. |
| Presse professionnelle FR (Les Nouvelles Esthétiques, Coiffure de Paris) | **[NV]** | Domaines injoignables + pas de moteur. À reprendre avec du budget WebSearch. |
