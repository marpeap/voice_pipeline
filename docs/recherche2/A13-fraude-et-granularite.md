# A13 — Fraude télécom et granularité de facturation

**Consulté le 2026-09-14.** [F] fait sourcé · [H] hypothèse · [R] raisonnement · [NV] non vérifié.
⚠️ **Sources inaccessibles** : `twilio.com/docs/voice/tutorials/how-to-prevent-toll-fraud` (**404**, page morte), `support.telnyx.com` (bloqué), `cfca.org` (bloqué, 3 tentatives). **Aucun montant de fraude mondiale n'est cité dans ce rapport** — la seule source de chiffres prévue était le CFCA.

## 1. Toll fraud et IRSF

**[F]** Twilio distingue **deux catégories qui ne se confondent pas** (`docs/voice/api/dialingpermissions-country-resource`) :
- `high_risk_special_numbers_enabled` — plages allouées par le pays : « premium numbers, special services, shared cost ».
- `high_risk_tollfraud_numbers_enabled` — « **narrow number ranges that have a high-risk of international revenue sharing fraud (IRSF) attacks** ».

**[R]** Conséquence directe : **bloquer les seuls numéros surtaxés officiels ne suffit pas**. L'IRSF passe par des plages d'apparence banale dans des destinations à terminaison chère — d'où le drapeau séparé.

**[F]** Les préfixes sont consultables : `GET /v1/DialingPermissions/Countries/{IsoCode}/HighRiskSpecialPrefixes`. Exemple documenté, Lettonie : `+37181`, `+3719000`. **Ressource informationnelle** : elle liste, elle n'applique pas. L'application passe par les drapeaux booléens par pays.

**[F]** Héritage : `https://voice.twilio.com/v1/Settings` expose `dialing_permissions_inheritance` — « `true` if the sub-account will inherit voice dialing permissions from the Master Project ».
**[R]** C'est **la brique d'architecture du mode autonome** : un sous-compte par client, héritage forcé, liste blanche non contournable par le client.

**[NV]** Mécanisme détaillé de l'IRSF : la page Twilio qui le décrivait est morte. Rien n'est affirmé ici au-delà du vocabulaire employé par la doc (« revenue sharing »).

## 2. Pourquoi le mode autonome est structurellement plus exposé que le greffon — [R]

1. **Le fraudeur s'attribue lui-même un numéro et une capacité d'émission en quelques minutes**, sans intervention humaine. En greffon, il devrait d'abord compromettre un client réel ; en autonome, **l'inscription est la porte d'entrée**.
2. **Le coût est prépayé par nous.** Les minutes sont facturées à notre compte fournisseur dans la seconde ; l'encaissement client est différé, et irrécouvrable en cas de rejet de paiement.
3. **Un agent vocal est un générateur d'appels programmable** — exactement la primitive que cherche un fraudeur.
4. **La scalabilité de l'attaque est celle du produit** : un service qui accepte 200 inscriptions par jour accepte 200 comptes d'attaque par jour.
5. **La détection est asymétrique** : un pic anormal se voit sur un compte créé il y a quarante minutes, sous identité fausse. La coupure doit être automatique ou elle n'aura pas lieu.

**[R] Exposition chiffrée** : un seul compte émettant **10 appels simultanés pendant 8 h** vers du mobile France au tarif standard ($0,1603/min) coûte **769 $ en une nuit**. Avec 100 canaux et des destinations IRSF classiques (tarifs supérieurs, [NV] faute de table accessible), l'ordre de grandeur passe à cinq chiffres.

## 3. Granularité de facturation — la question reste ouverte

**[F — absence constatée]** **Ni Twilio ni Telnyx ne documentent leur incrément de facturation** sur les pages consultées (`twilio.com/en-us/voice/pricing/fr`, `/voice/pricing`, `telnyx.com/pricing/call-control`, `developers.telnyx.com/pricing.md`). Tarifs en $/min, **aucune mention d'arrondi ni de durée minimale**.
**[H]** La croyance de marché (Telnyx à la seconde, Twilio à la minute entamée) **n'est confirmée par aucune source consultée**. À trancher par les CGU et par un **test empirique** : un appel de 12 s, puis lecture du champ `price` de l'UsageRecord.

**Tarifs France vérifiés** [F] : sortant fixe **$0,0187/min** · sortant mobile depuis EEE **$0,0404** · **sortant mobile standard $0,1603** · entrant local **$0,0100** · numéro local **$1,35/mois**.
⚠️ Le rapport EEE/standard sur le mobile français est de **×3,97**. Ce n'est pas du pricing, c'est un paramètre de risque.

**[R] Si nous facturons à la minute entamée** : sur des appels courts (30–90 s, typiques d'un agent vocal), l'arrondi représente **+30 à +80 % de marge** sur le poste télécom. Maximal là où le produit est le plus utilisé, donc structurel. **À écrire noir sur blanc dans la grille**, ou à remplacer par une facturation à la seconde vendue en forfaits — sinon c'est un motif de litige et de résiliation.

## 4. Garde-fous : ce qui est natif, ce qui est à construire

**Natif** [F] : liste blanche géographique par pays, avec séparation premium/IRSF · héritage des permissions vers les sous-comptes · **alertes** de dépense (`UsageTrigger`, déclenchement sur `price`, évalué ~1×/min, **plafond de 1 000 par compte**) · comptabilité d'usage (`UsageRecord`, champ `as_of`, **aucune garantie de fraîcheur**).

⚠️ **Le trou central** : **`UsageTrigger` notifie, il ne coupe pas.** Aucun plafond dur natif n'a été trouvé. Et `UsageRecord` est un système **de comptabilité, pas de contrôle** — bâtir la coupure sur son interrogation périodique, c'est accepter une fenêtre d'exposition non bornée.

**À construire** [R] : la coupure automatique · le plafond **par tenant** (les déclencheurs portent sur un compte, et 1 000 déclencheurs = une limite d'échelle réelle) · un **compteur temps réel alimenté par les webhooks d'appel**, qui refuse l'appel **avant** émission · les limites de **concurrence** par tenant (le facteur d'amplification d'une attaque) · un **profil de risque à l'inscription** (par défaut : France métropolitaine seule, plafond bas, aucune destination internationale ; élargissement après vérification de paiement) · la **détection comportementale** (rafales nocturnes, concentration sur un préfixe) · le lien **solvabilité ↔ droit d'émettre**, en minutes et non en jours.

**Stripe, limites qui contraignent la conception** [F, `docs.stripe.com/rate-limits`] : **10 factures par abonnement et par minute, 20 par jour** · quota de lecture **500 GET par transaction**, plancher 10 000/mois → **l'état de solvabilité doit être mis en cache localement, jamais interrogé à chaque appel** · `429` avec en-tête `Stripe-Rate-Limited-Reason` ; un `429` **sans** cet en-tête est un verrou d'objet, à retenter.

## 5. Dette de recherche
Montants chiffrés de la fraude mondiale [NV] · mécanisme détaillé de l'IRSF [NV] · **granularité de facturation des deux fournisseurs** [NV, bloquant pour la marge] · protections anti-fraude Telnyx [NV] · comportement par défaut réel d'un compte Twilio neuf (lu dans un **exemple de réponse**, pas dans une phrase normative) · table de prix par destination IRSF.
