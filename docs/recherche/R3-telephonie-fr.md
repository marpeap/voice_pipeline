# R3 — Téléphonie pour un agent vocal IA en France

**État au 13 septembre 2026.** Toutes les dates de consultation sont le **2026-09-13**.

## Comment lire ce document

Chaque affirmation porte une étiquette :

- **[V]** — **fait vérifié** : lu sur la page officielle citée, à la date indiquée.
- **[V-2]** — **vérifié sur source secondaire** : page officielle inaccessible depuis cet environnement, information confirmée par un moteur de recherche citant cette source. À reconfirmer avant décision contractuelle.
- **[H]** — **hypothèse** : déduction raisonnée, non lue telle quelle sur une source.
- **[R]** — **recommandation** de ma part.
- **[NV]** — **non vérifié** : je n'ai pas trouvé la source. Rien n'est inventé pour combler le trou.

**Limite technique de cette recherche, à connaître** : depuis cet environnement, `curl` n'a pas d'accès réseau et l'outil de récupération de page a refusé plusieurs domaines (`eur-lex.europa.eu`, `legifrance.gouv.fr`, `cnil.fr`). Les points de droit concernés sont donc en **[V-2]** et non en **[V]**. Ils doivent être relus sur Légifrance avant tout engagement client. Les pages opérateurs (Twilio, OVHcloud, ARCEP) ont, elles, été ouvertes directement.

---

## 1. Acheter un numéro français par API

### 1.1 Tableau de décision

| Fournisseur | API d'achat FR | Prix numéro / mois | Entrant / min | Délai KYC annoncé | Portage par API |
|---|---|---|---|---|---|
| **Telnyx** | ✅ `POST /v2/number_orders` | **$1,00** local · **$0,50** en 09 · $20,00 mobile | **$0,006** | **~72 h** | ✅ |
| **Twilio** | ✅ `POST .../IncomingPhoneNumbers.json` | $1,35 (CSV officiel : $1,15) | $0,0100 (SIP trunk : $0,0060) | non chiffré officiellement | ❌ US uniquement |
| **OVHcloud** | ✅ `POST /order/telephony/{ba}/numberGeographic` | **1 € HT** | [NV] | [NV] | ✅ (RIO/SIRET en paramètres) |
| **Zadarma** | ✅ `POST /v1/direct_numbers/order/` | **2 € HT** (3 canaux inclus) | **gratuit** | [NV] | [NV] |
| **Plivo** | ✅ `POST .../PhoneNumber/{number}/` | $2,00 — **statut BETA** | $0,0095 | [NV] | [NV] |
| **Vonage** | ✅ `POST rest.nexmo.com/number/buy` | **403 — non consultable** | 403 | [NV] | [NV] |
| **Bandwidth** | ❓ non documenté hors US | non public (devis) | non public | [NV] | ✅ API porting v3 |
| **Sipgate** | ❌ aucun endpoint d'achat | 10,88 €/mois (international, FR non confirmée) | [NV] | — | ❌ lecture seule |
| **Keyyo** | ❌ aucun endpoint | à partir de 5 € HT | [NV] | [NV] | gratuite (payante pour les 08) |
| **Ringover** | ❌ `GET` uniquement | 20 € HT/utilisateur/mois, **3 utilisateurs minimum** | inclus | [NV] | 10-30 j, gratuite |

**Ce que ce tableau dit en une phrase** : sur dix fournisseurs, **quatre seulement** permettent d'acheter un numéro français par API avec une grille tarifaire publiquement vérifiable — Telnyx, Twilio, OVHcloud et Zadarma. Les acteurs français traditionnels (Keyyo, Ringover) vendent des licences par utilisateur et n'ont **aucun endpoint d'approvisionnement de numéro** : leur API pilote les appels, pas le stock.

### 1.2 Les quatre fournisseurs réellement utilisables

**Telnyx** — le meilleur compromis vérifié. **[V]**
- Types FR tarifés : local 01-05, national 09, mobile 06/07, shared-cost 08xx, toll-free 0800. Grille : <https://telnyx.com/pricing.md> (2026-09-13).
- Prix mensuels (USD) : **local $1,00** (frais unique $1) · **national 09 $0,50** (frais unique $1) · **mobile $20,00** · shared-cost $16,89 · toll-free $10,00 · E911 France $0.
- Entrant : local **$0,006**, mobile $0,010, national 09 $0,016, toll-free $0,060 (une seconde ligne du même fichier indique $0,12 — **incohérence interne de la source, signalée telle quelle**).
- **[NV] Aucun tarif sortant France n'est publié.** Un grep exhaustif du fichier canonique donne 52 lignes « France » et aucune terminaison. C'est un trou à faire combler par écrit avant de signer.
- Repères hors France utiles : terminaison Call Control $0,002/min, **Voice AI Assistant $0,05/min**, media streaming $0,0035/min.
- **KYC** : adresse en France obligatoire, **justificatif de domicile de moins de 3 mois**, **présence physique dans le pays exigée**, **usage professionnel requis (usage privé interdit)**, Kbis pour une société. **Délai annoncé : ~72 heures.** Source : <https://support.telnyx.com/en/articles/1311445-france-did-requirements>.
- Chaîne API : `POST /v2/addresses` → `POST /v2/documents` → `POST /v2/requirement_groups` → `submit_for_approval` → `GET /v2/available_phone_numbers?country_code=FR` → `POST /v2/number_orders`. Doc : <https://developers.telnyx.com/docs/numbers/phone-numbers/number-orders>.
- **Le mobile est tarifé mais non documenté côté conformité** — à ne pas utiliser sans confirmation.

**Twilio** — le plus documenté, le plus contraint. **[V]**
- Types FR : local +331→+335 · mobile +336 et +3373-78 · national +339 · plateforme technique +3393903/24/20 · **NPV** +3316229, +33948353, +33948194 · toll-free +33800→+33805 (entreprises uniquement). Source : <https://www.twilio.com/en-us/guidelines/fr/regulatory>.
- **Point décisif, deux fois vérifié** : les **numéros mobiles français sont réservés au P2P**. Les conditions France de Twilio (<https://www.twilio.com/en-us/legal/service-country-specific-terms/france-phone-numbers>) précisent que l'A2P et les appels automatisés y sont **interdits**, et la page voice guidelines recommande « select a geographical number or a France national number type ». La catégorie **NPV** est la seule qui autorise l'appel sortant automatisé.
- Autres conditions France vérifiées : hors numéros mobiles étendus à 14 chiffres et numéros gratuits, les numéros **ne peuvent pas être assignés hors de France** ; la cession/location n'est pas permise ; **période minimale d'utilisation de 72 heures**.
- **Divergence de prix non résolue entre deux sources Twilio** : $1,35/mois sur <https://www.twilio.com/en-us/voice/pricing/fr> contre **$1,15/mois** dans le CSV officiel <https://www.twilio.com/content/dam/twilio-com/pricing-data/en/csv/PMded94a0dae30eaaec0f115f22859bd38_SiteNumbersPricing.csv>. À faire trancher. Le CSV officiel ne contient d'ailleurs **qu'une seule ligne France, de type « Local »** : mobile, 09 et 08 ne sont pas au catalogue public d'achat.
- Minutes (USD) : entrant local **$0,0100** (SIP trunking $0,0060) · sortant fixe FR **$0,0187** · sortant mobile FR **$0,1603**, ou **$0,0404 si l'appel part d'un numéro de l'EEE** — un facteur 4 selon l'origine, qui se joue à la configuration et pas au contrat. · 08xx $0,5513. Source : <https://assets.cdn.prod.twilio.com/pricing-csv/OutboundVoicePricing.csv>.
- **KYC** : adresse locale FR obligatoire, **boîte postale et adresse virtuelle refusées**, justificatif d'adresse de moins de 3 mois, autres pièces de moins d'un an, Kbis ou SIREN/SIRET et représentant habilité. À défaut de pièce d'identité du représentant, une procuration signée est acceptée. Chaîne API : `POST /v2/RegulatoryCompliance/EndUsers` → `SupportingDocuments` → `Bundles` → `ItemAssignments`. Achat : `POST /2010-04-01/Accounts/{Sid}/IncomingPhoneNumbers.json` avec `AddressSid` et `BundleSid`.
- **Délai** : la FAQ officielle annonce « We do our best to verify documents submitted within **24 business hours** », avec escalade au support au-delà de 72 heures (<https://www.twilio.com/docs/phone-numbers/regulatory/faq>). Un numéro **ne peut pas être utilisé avant conformité** : « Regulators and carriers expect phone numbers to be compliant from the time they begin to be in use », et un bundle non conforme expose à la **reprise réglementaire du numéro**.

**OVHcloud Telecom** — le seul acteur français avec une vraie API de commande. **[V]**
- L'API publique expose trois familles : `numberGeographic` (01-05), `numberNogeographic` (09), `numberSpecial` (08xx). Enum pays `['be','ch','fr','gb','uk']`, plages jusqu'à 100 numéros. **Pas de mobile 06/07 au catalogue.** Sources : <https://api.ovh.com/1.0/order.json>, <https://api.ovh.com/1.0/telephony.json>.
- **1 € HT/mois (1,20 € TTC) par numéro**, fixe local, international **ou spécial** (<https://www.ovhcloud.com/fr/phone/numeros/>). Lignes VoIP : Découverte 0,99 € HT, Entreprise 4,99 € HT, Entreprise+ 14,99 € HT (<https://www.ovhcloud.com/fr/phone/voip/>). Confirmé dans le catalogue public `GET https://api.ovh.com/1.0/order/catalog/public/telephony?ovhSubsidiary=FR` (EUR, TVA 20 %), avec **frais de dossier compte téléphonie à 0,00 €**.
- **[NV] Grille à la minute non publiée.** Le modèle est forfaitaire : appels vers les fixes de France et 40 pays inclus, mobiles à la seconde, inclus dans Entreprise+ et dans le trunk illimité. Le prix mobile hors forfait n'est pas publiquement lisible.
- **KYC sans dépôt de pièces** : la conformité passe par les champs déclaratifs de la commande — `legalform`, `siret`, `ape`, `socialNomination`, adresse complète, `retractation`. C'est **le parcours le plus léger du panel**. **[NV]** Délai d'activation non publié.
- Achat : `POST /order/telephony/{billingAccount}/numberGeographic` (le `GET` homonyme renvoie le devis), paramètres requis `country`, `zone`, `offer` (`alias` ou `didsOnly`), `legalform`, `city`, `displayUniversalDirectory`, `retractation`.

**Zadarma** — le moins cher, le plus limité. **[V]**
- Trois types FR : géographique **+33 1** (Paris/Saint-Denis), national **+33 9**, mobile **+33 7**. Pages : <https://zadarma.com/en/tariffs/numbers/france/paris/>, `/national/`, `/mobile/`.
- **2 €/mois HT** pour les trois types, **0 € de frais de connexion**, **3 canaux simultanés inclus**.
- **Entrant gratuit** sur tous les DID (sauf 800). Sortant fixe FR 0,008 € (plan Economy) ou 0,01 € (Standard) ; mobile FR 0,027 € ou 0,033 €. Facturation à la seconde sauf Economy. <https://zadarma.com/en/tariffs/calls/france/>.
- **KYC entièrement pilotable par API** — c'est remarquable : `POST /v1/documents/groups/create/`, `POST /v1/documents/upload/`, `GET /v1/documents/groups/valid/<ID>/`, puis `POST /v1/direct_numbers/order/`. Pièce d'identité recto-verso ou certificat d'immatriculation, plus une adresse courante dans le pays. Alternative : paiement par virement depuis un compte société. <https://zadarma.com/en/support/instructions/api/numbers/>.
- **Limite structurelle** : le numéro est **attribué aléatoirement**, pas de choix du numéro en France. **[NV]** Délai d'activation non chiffré.

### 1.3 Les six autres, et pourquoi les écarter

- **Vonage** : `www.vonage.com` renvoie **HTTP 403** à toute récupération automatisée (trois URL, deux user-agents, 2026-09-13) ; `vonage.fr` répond mais **n'affiche aucun prix**. L'API d'achat existe et est documentée (`POST https://rest.nexmo.com/number/buy`, <https://developer.vonage.com/en/api/numbers>), mais **aucun prix, aucune exigence KYC française et aucune procédure de portabilité FR n'ont pu être vérifiés**. Un fournisseur dont on ne peut pas lire la grille avant de créer un compte est un fournisseur qu'on n'évalue pas.
- **Plivo** : numéros FR en statut **BETA** (local, mobile) et **PREVIEW** (toll-free). $2,00/mois, entrant $0,0095, sortant fixe FR $0,0195 depuis l'EEE contre **$0,0530 en domestique**, mobile $0,0426 depuis l'EEE contre **$0,3030** en domestique — l'écart EEE/domestique est massif et structurant. La Compliance API « currently supports India only » : **[NV]** exigences FR. Données extraites du bundle servi par <https://www.plivo.com/phone-numbers/pricing/fr/> (la table n'est pas rendue côté serveur). **[R]** BETA n'est pas un statut de production pour un service qui répond au téléphone d'un commerçant.
- **Bandwidth (ex-Voxbone)** : la France figure dans la table de couverture (<https://www.bandwidth.com/global-reach/>), mais **aucun prix n'est public** — <https://www.bandwidth.com/pricing/> n'affiche que des tarifs US et renvoie à un devis. L'endpoint d'achat de DID international **n'est pas documenté publiquement** : les seules specs OpenAPI exposées pour Voxbone couvrent le CDR et le porting. Leur page réglementaire mentionne uniquement, pour la France, le programme MAN de l'ARCEP (« As of October 1, 2024, all ARCEP-notified Operators and owners of numbering resources in France will need to comply with the "final phase" of the MAN Program »).
- **Sipgate** : **`sipgate.fr` ne résout pas en DNS**. Il n'y a pas de filiale française. Le schéma OpenAPI officiel (`https://api.sipgate.com/v2/swagger.json`, parsé) n'expose **aucun endpoint d'achat de numéro** — uniquement `GET /numbers` et `PUT /numbers/{numberId}` pour la configuration, et `GET|DELETE /portings` en lecture/annulation. **À écarter.**
- **Keyyo** (groupe Bouygues Telecom) : numéros 01-05 et 09 « à partir de 5 € HT/mois », gamme 08 complète (abonnement gratuit, mise en service 50 €). Mais `keyyo.com/fr/tarifs/` renvoie **404** et aucune page tarifaire publique n'existe dans l'arborescence. L'API (<https://api.keyyo.com/developers>) couvre le click-to-call et les notifications d'appel — **aucun provisioning de numéro**.
- **Ringover** : gamme FR la plus complète du panel (01-05, 09, mobile, 08xx, numéros localisés, mnémotechniques). Mais le modèle est la licence : **TALK 20 € HT/utilisateur/mois avec 3 utilisateurs minimum**, BUSINESS 47 € HT. Le schéma OpenAPI public officiel (`https://developer.ringover.com/web/openapi_public.yml`, 573 ko, parsé) n'expose que **`GET /numbers`** et **`GET /numbers/{number}`** : **aucune méthode POST/PUT/DELETE, aucun endpoint de commande**. Inutilisable pour un provisioning automatisé à l'échelle d'un parc de TPE.

### 1.4 Recommandation

**[R]** **Telnyx en principal, OVHcloud en second.**

Telnyx parce que c'est le seul du panel qui réunit les quatre qualités nécessaires : achat par API, **portage par API**, délai KYC annoncé et chiffré (~72 h), et un numéro **09 à $0,50/mois** — soit le tarif le plus bas du panel sur le type de numéro exactement adapté à notre usage (voir §2.3 : le numéro d'arrivée d'un renvoi doit être un 01-05 ou un 09).

OVHcloud en second parce que c'est un opérateur **français**, hébergé en France, à **1 € HT/mois** et avec **un KYC purement déclaratif** — le parcours d'onboarding le plus court du panel, et un argument commercial réel auprès de TPE qui se méfient des acteurs américains. Le prix des minutes n'étant pas publié, l'engager suppose un devis écrit.

**[R]** Deux règles non négociables issues de cette recherche :
1. **Ne jamais utiliser un numéro mobile français** pour l'agent. Twilio l'interdit contractuellement (P2P uniquement), Telnyx ne le documente pas côté conformité, OVHcloud n'en propose pas, et c'est la cible prioritaire du dispositif anti-fraude ARCEP.
2. **Trois points à faire confirmer par écrit avant tout engagement** : l'écart $1,35 / $1,15 chez Twilio ; l'absence totale de tarif sortant France publié chez Telnyx ; le statut BETA des numéros FR chez Plivo.



## 2. Utiliser le numéro EXISTANT sans le porter — le renvoi d'appel

C'est **le** chemin d'onboarding. Le commerçant garde son numéro, sa carte de visite, sa fiche Google. Aucun risque de coupure. Réversible en cinq secondes. Toutes les pages citées ici ont été ouvertes le **2026-09-13**.

### 2.1 Ce que les opérateurs publient réellement — tableau des codes

⛔ = l'opérateur ne publie pas ce code sur son site d'assistance.

| | Orange mobile | Orange fixe / Livebox | SFR fixe | SFR mobile | Freebox | Free mobile | Bouygues mobile | Bouygues Bbox |
|---|---|---|---|---|---|---|---|---|
| Inconditionnel | `**21*n*11#` | `*21*n#` | `*21*n#` | ⛔ | `*21*n#` | ⛔ (Free Pro : `*21*n#`) | serveur vocal **610** | `*21*n#` |
| Non-réponse | `**61*n*11#` | Espace client uniquement | `*61*n#` | ⛔ | **`*61*n*tempo#`** | ⛔ | `*61*n#` | `*61*n#` |
| Occupation | `**67*n*11#` | Espace client uniquement | `*69*n#` | ⛔ | `*69*n#` | ⛔ | `*67*n#` | `*69*n#` |
| Injoignable | `**62*n*11#` | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | `*62*n#` | annoncé, code ⛔ |
| Tout annuler | `##002#` | `#21#` | `#21#` / `#61#` / `#69#` | ⛔ | `#21#` / `#61#` / `#69#` | ⛔ | `#002#` | `#002#` |
| Délai réglable | **non — 20 s fixes** | nb de sonneries | oui si Fibre, valeurs ⛔ | ⛔ | **5 à 20 s** | ⛔ | ⛔ | nb de sonneries |
| Qui paie la 2ᵉ jambe | ⛔ | décompté du forfait | tarifs de l'offre | ⛔ | **0,05 €/min** | **0,05 €/min (option)** | forfait, ou **0,50 €/min hors forfait** | **gratuit vers fixe/09** |

**Source normative des codes MMI** : 3GPP TS 22.030, qui définit les *Service Codes* 21 (inconditionnel), 61 (non-réponse), 62 (injoignable), 67 (occupation), la structure `*`/`#`/`**`/`##`/`*#` et le paramètre SIC portant la valeur du *No Reply Condition Timer*. Copie consultée : <http://www.arib.or.jp/english/html/overview/doc/STD-T63V12_10/5_Appendix/Rel13/22/22030-d00.pdf> (2026-09-13). **[V-2]**

### 2.2 Opérateur par opérateur — ce qui compte

**Orange mobile** **[V]** — <https://assistance.orange.fr/nid/172736> (MAJ 13/02/2025) et <https://assistancepro.orange.fr/telephone_mobile/la_messagerie_vocale_visuelle/messagerie_vocale/comment_programmer_un_renvoi_dappel_depuis_mon_mobile_-395750>. La page pro et la page grand public sont identiques.
- **Délai fixe, non réglable** : « après 20 secondes de sonneries ».
- **Le conflit avec le répondeur se règle tout seul** — et c'est une excellente nouvelle : « tout renvoi programmé vers un autre numéro **annule les renvois d'appels vers votre Messagerie Vocale 888** », et l'annulation du renvoi « **réactive automatiquement** » le 888. Rien à désactiver, rien à restaurer.
- **Exclusions** : Mobicarte et forfaits bloqués. Le mobile doit être sous couverture Orange France.
- **Les codes MMI sont le seul chemin** : « cette fonctionnalité n'est pas accessible depuis l'Espace Client ou les applications Orange et Moi et My Sosh ».
- Incohérence relevée sur la page Orange : la désactivation du renvoi sur injoignabilité y est notée `*#62#` (qui est un code de consultation). `##62#` n'est pas écrit → **[NV]**.

**Orange fixe / Livebox** **[V]** — <https://assistance.orange.fr/telephone/telephone-par-internet/toutes-les-livebox/installer-et-utiliser/rester-joignable/renvoi-d-appel/telephone-par-internet-activer-ou-desactiver-le-renvoi-d-appel_19032-19121> (MAJ 21/07/2026).
- **Piège sérieux** : depuis le combiné, `*22*` et `*23*` renvoient **uniquement vers la messagerie**, pas vers un numéro tiers. **Le renvoi conditionnel vers un numéro externe passe obligatoirement par l'Espace client** (« Si vous ne répondez pas ou êtes déjà en ligne », puis nombre de sonneries dans un menu déroulant).
- L'Espace client Orange fixe propose aussi un transfert **temporaire** (dates + heures) et **périodique hebdomadaire** (jours + heures). **[R]** C'est exactement ce qu'il faut vendre à un commerçant qui ne veut l'IA qu'en dehors de ses horaires d'ouverture, et c'est un argument commercial en soi.
- Coût : activations/désactivations gratuites, mais avertissement explicite d'Orange que les appels transférés vers mobile sont facturés si l'abonnement n'inclut pas les appels illimités.
- Sur la ligne fixe RTC classique (<https://assistance.orange.fr/telephone/telephone-fixe/installer-et-utiliser/rester-joignable/transfert-d-appels/transfert-d-appels-activer-ou-desactiver-_20309-20699>, MAJ 28/05/2024) : `*21*` + 10 chiffres + `#`, désactivation `#21#`, ou serveur vocal **3000** (choix 2 puis 1). Mention légale « chaque activation est facturée 0€111 TTC, désactivation gratuite » — **[H]** le rattachement exact de cette note (4) à l'activation du transfert n'est pas lisible dans le HTML, à reconfirmer.

**Orange pro** **[V]** — la règle de facturation est écrite quatre fois sur les pages pro : « les appels entrants renvoyés vers un numéro tiers sont **décomptés de votre forfait, de la même façon que lorsque vous émettez un appel** […] susceptibles de vous être facturés hors forfait ». Standard cloud Connect Pro : `*28` + numéro, désactivation `*28*0`. Optimale/Open Pro Office : `*21*` + numéro, retour messagerie `*21*0`, statut `**21`. PABX géré par Orange → 1017 choix 3. Open Pro Partagé → option **RVTI, payante**, via le 3901.
**[NV]** Trunk SIP / Business Talk Orange : aucune page publique trouvée.

**SFR fixe / box** **[V]** — <https://assistance.sfr.fr/internet-tel-fixe/tel-fixe/activer-desactiver-options.html> et <https://assistance.sfr.fr/internet-tel-fixe/tel-fixe/gerer-options-appels-box-thd-sfr.html>. Jeu complet : `*21*n#` / `*61*n#` / `*69*n#`, réactivation du dernier numéro sans le retaper (`*21#`, `*61#`, `*69#`), statuts (`*#21#`…). Le délai avant renvoi « peut être configuré » **si client Fibre** — valeurs non publiées **[NV]**. Coût : « les appels transférés sont alors facturés selon les tarifs en vigueur de votre offre ». Les numéros en **0806 à 0809** sont facturés au tarif d'un appel local (<https://assistance.sfr.fr/internet-tel-fixe/tel-fixe/tarifs-telephoniques-ligne-fixe-sfr.html>).
**Contradiction entre deux pages officielles SFR**, à signaler : l'une dit que le signal d'appel doit être inactif pour que le renvoi sur occupation fonctionne, l'autre dit qu'il fonctionne même si le signal d'appel est activé. **[H]** Probablement une différence THD/Fibre vs ADSL. Non tranché.
**[R] Attention à `*82#`** (rejet des appels anonymes) : à laisser **inactif** sur le numéro d'arrivée, sans quoi un appel renvoyé avec CLI masqué sera rejeté — voir §2.4.

**SFR mobile — trou documentaire confirmé [NV]** : le sitemap officiel `https://assistance.sfr.fr/sitemap.xml` (2 994 lignes, récupéré le 2026-09-13) **ne contient aucune page de renvoi ou transfert d'appel mobile**. SFR ne publie aucun code MMI mobile. Les codes qui circulent sur les sites comparateurs ne sont pas des sources officielles et **ne sont volontairement pas repris ici**. Le répondeur mobile SFR se pilote au **123**.

**Freebox — la documentation la plus utilisable du marché** **[V]** — articles 551 à 574 de <https://assistance.free.fr>.
- **Le seul opérateur qui publie une plage de délai chiffrée** : `*61*<numéro>*<tempo>#`, « entre **5 et 20 secondes** ». Le délai se passe directement dans le code.
- Désactivation du renvoi vers la messagerie Free, indispensable pour libérer la voie : `*75*1#` (inconditionnel), `*75*2#` (occupation), `*75*3#` (non-réponse), `*75*4#`, `*75*5#`.
- Coût : **0,05 €/min pour chaque appel renvoyé**, y compris vers les destinations incluses, plus le tarif de base sur les destinations payantes.
- L'appelant entend « une tonalité spéciale » pendant son appel.

**Free mobile** **[V]** — <https://assistance.free.fr/articles/1755> : les 4 types existent, destinations autorisées « fixes en France métropolitaine (en **01 à 05 et 09**) ou vers les mobiles (06 et 07) ». Renvoi vers la messagerie gratuit et actif par défaut. **Codes MMI non publiés [NV]** (seule exception : Free Pro publie `*21*n#` pour l'inconditionnel, <https://support-pro.free.fr/comment-parametrer-un-renvoi-dappel/>).
**Coût [V]** — brochure tarifaire officielle, version du 21/07/2026, <https://mobile.free.fr/docs/bt/tarifs.pdf> : « **Option Renvoi d'appels métropolitains : 0,05 €/min** », avec exclusion explicite des « numéros courts, spéciaux, surtaxés et autres services à valeur ajoutée ainsi que vers l'étranger et Outre-Mer qui est interdit ». Chez Free le renvoi est donc une **option facturée**, pas un décompte de forfait. Non listée pour le Forfait 2 € → **[H]** probablement indisponible, **[NV]**.

**Bouygues mobile** **[V]** — <https://www.assistance.bouyguestelecom.fr/s/article/activation-desactivation-renvoi-appel> (page entièrement en JavaScript, rendue au navigateur le 2026-09-13).
- **Codes à une seule étoile**, là où Orange documente le double : `*62*n#`, `*67*n#`, `*61*n#`, annulation globale `#002#`. Reproduit tel que Bouygues l'écrit.
- **Le renvoi systématique n'a pas de code** : il passe par le serveur vocal **610** (ou `06 60 61 06 10` depuis un autre téléphone, `+33 660 610 610` gratuitement depuis l'étranger).
- Coût, cité mot pour mot : « **Gratuit** : si les appels sont redirigés vers un numéro mobile, fixe Bouygues Telecom ou vers un fixe d'un autre opérateur. Ils sont décomptés de votre forfait […] **Payant** : si les appels sont renvoyés vers un autre numéro que Bouygues Telecom (hors n° courts et spéciaux) […] facturé en hors forfait au prix d'une communication métropolitaine (**0,50 € par minute**). » Les deux alinéas se recouvrent — **[H]** lecture probable : décompté du forfait quand la destination est couverte, 0,50 €/min sinon.
- « Si vous avez activé **l'option de blocage**, le renvoi d'appel mobile ne peut fonctionner. »
- **Procédure de déblocage quand un renvoi refuse de se désactiver** : composer le **610**, choix 0, puis 1, puis 2 → message « Le répondeur reprend un comportement standard », les renvois sont supprimés. **[R]** À garder dans le script du support : c'est la panne n° 1 qu'un commerçant signalera.

**Bouygues Bbox** **[V]** — <https://www.assistance.bouyguestelecom.fr/s/article/renvoi-appel-telephone-fixe> : `*21*n#`, `*61*n#`, `*69*n#`, `#002#`. **« Numéro fixe : le renvoi d'appel est gratuit. »** Le nombre de sonneries est réglable depuis l'espace client / l'appli (valeurs non publiées **[NV]**).

**[NV]** Offres Trunk SIP / Business des quatre opérateurs : aucune documentation publique exploitable trouvée.

### 2.3 Les quatre conclusions produit

1. **La deuxième jambe est toujours payée par le commerçant qui pose le renvoi**, jamais par l'appelant. Trois modèles coexistent : décompte du forfait (Orange, SFR, Bouygues mobile), **option à 0,05 €/min** (Free fixe et mobile), **gratuit** (Bouygues Bbox vers un fixe).
2. **Le numéro d'arrivée de l'agent doit être un 01-05 ou un 09.** Jamais un numéro court, spécial ou surtaxé : interdit par la brochure Free, exclu par Bouygues, et un 0806-0809 est facturé au tarif local chez SFR. **[R]** Un **09** est le meilleur choix : national, non géographique, autorisé partout, et il n'induit pas le client en erreur sur une localité.
3. **Le répondeur opérateur est l'obstacle récurrent.** Orange l'écrase automatiquement. Free exige `*75*…`. Bouygues exige parfois la réinitialisation par le 610. SFR mobile ne publie rien.
4. **Deux blocages doivent être vérifiés avant toute promesse commerciale** — voir ci-dessous.

### 2.4 Les deux pièges qui feront échouer un déploiement

**Piège 1 — la « protection contre les renvois » côté numéro d'arrivée.** **[V]** <https://assistance.free.fr/articles/892> (mobile) et <https://assistance.free.fr/articles/554> (fixe) : « Ce service vous permet de **refuser les renvois d'appels effectués vers votre numéro**. Il empêche donc l'appel d'un correspondant cherchant à joindre un numéro pour lequel un renvoi vers votre ligne a été activé. » Fixe : `*93#` / `#93#` / statut `*#93#`. Mobile : Espace Abonné.
→ Si cette protection est active sur la ligne d'arrivée, **tous les renvois échouent silencieusement**. À vérifier côté plateforme.

**Piège 2 — le numéro de l'appelant après renvoi n'est pas garanti.** **[V]** Fiche pratique Arcep déjà citée : « Dans certaines situations (équipements anciens, fonctionnalités limitées, **renvois d'appels complexes**), il peut être techniquement impossible de retransmettre correctement les informations d'authentification. Dans ce cas, l'Arcep **recommande aux opérateurs de masquer l'identifiant d'appelant** afin d'éviter une coupure automatique de l'appel tout en évitant les risques d'usurpation ». Le communiqué du 2 décembre 2025 le redit : certains équipements « ne sont pas toujours en mesure de relayer correctement les données d'authentification des numéros **lors de renvois d'appels** ».

C'est le point le plus important de toute la section, et il est structurel, pas anecdotique :

> **L'agent vocal doit fonctionner sans connaître le numéro de l'appelant.**

**[R]** Conséquences de conception, à intégrer dès la première version :
- Ne **jamais** faire dépendre l'identification du client du CLI. L'agent demande le nom et le numéro à l'oral, point.
- Ne pas activer le rejet des appels anonymes sur le numéro d'arrivée (SFR `*82#`, équivalents ailleurs). Un renvoi au CLI masqué serait rejeté.
- **Tester en réel sur les quatre réseaux** avant toute promesse commerciale. Aucun opérateur ne documente ce qu'il présente au numéro de destination après renvoi — **[NV]** pour les quatre. C'est un test terrain d'une heure qui évite un mois de support.



## 3. Portabilité d'un numéro FR vers un opérateur API

**[R] À lire avant tout le reste de cette section : pour une TPE, la portabilité est le mauvais chemin.** Elle coupe le lien avec l'opérateur historique, elle est irréversible à court terme, elle prend des semaines, et le premier incident se traduit par un commerçant injoignable. Le renvoi d'appel (§2) obtient le même résultat fonctionnel en cinq minutes et se défait en cinq secondes. La portabilité ne se justifie que pour un client qui **veut** quitter son opérateur, jamais pour brancher un agent vocal.

### 3.1 Comparatif vérifié

| Opérateur | Types portables | Documents exigés | Délai annoncé | Coût | Portage par API |
|---|---|---|---|---|---|
| **Twilio** | +331→+335 et +339. **Port-in mobile (+336/+337) suspendu** | SIRET, code NAF, **code RIO valide**, nom de l'opérateur actuel, LOA pour les numéros « Cristal » +33 969 | **jusqu'à 4 semaines** | [NV] | ❌ formulaire manuel (API US uniquement) |
| **Telnyx** | [NV] par type | **LOA modèle France**, **code RIO (12 caractères, obtenu au 3179)**, **SIRET 14 chiffres**, dernière facture, justificatif d'adresse < 3 mois | **≥ 8 jours ouvrés**, bascule 10h-13h ou 14h-17h | port-**out** $6/numéro ; port-in [NV] | ✅ `PATCH /v2/porting_orders/:id` |
| **OVHcloud** | `landline` et `special` | RIO (offre individuelle) ou SIRET (société), raison sociale, adresse complète, champ `fiabilisation` propre à la France | [NV] | **« Portabilité offerte — de tous vos numéros »** | ✅ `POST /order/telephony/{ba}/portability` puis `/document`, `/execute`, `/changeDate`, `/relaunch` |
| **Keyyo** | « quel qu'en soit le type » | [NV] | [NV] | **gratuite**, sauf option payante pour les 08 | ❌ |
| **Ringover** | FR complet | mandat de portabilité, dernière facture, justificatif d'identité (le RIO facilite mais n'est pas présenté comme obligatoire) | **10 à 30 jours** | « sans coût additionnel » | ❌ |
| **Bandwidth** | [NV] pour la France | [NV] | [NV] | [NV] | ✅ API v3 (`POST /porting/validator`, `/portInOrders`, `/documents`) |
| Vonage, Plivo, Zadarma, Sipgate | [NV] — procédure FR non trouvée | | | | |

Sources : <https://www.twilio.com/en-us/guidelines/fr/porting>, <https://support.telnyx.com/en/articles/3266956-france-number-porting>, <https://www.ovhcloud.com/fr/phone/numeros/>, <https://www.keyyo.com/fr/telephonie-faq/conservation-numeros>, <https://www.ringover.fr/conserver-vos-numeros> (toutes 2026-09-13).

### 3.2 Le point commun à retenir : le RIO

Le **code RIO** (Relevé d'Identité Opérateur) est la clé de voûte du portage français. Il s'obtient en appelant le **3179** depuis la ligne à porter — c'est gratuit et immédiat, et le code arrive par SMS ou est dicté par le serveur vocal. **[V]** Telnyx précise un format à **12 caractères**.

**[R]** Si un portage est malgré tout décidé, la séquence sûre est :
1. Récupérer le RIO au 3179 depuis la ligne concernée.
2. **Mettre le renvoi d'appel en place d'abord**, et vérifier que l'agent vocal fonctionne dessus pendant plusieurs jours.
3. Seulement ensuite lancer le portage, avec une date de bascule sur un créneau creux.
4. Prévoir le cas de l'échec : un portage refusé (RIO invalide, impayé chez l'opérateur sortant, titulaire ne correspondant pas) est fréquent et le commerçant doit le savoir avant, pas après.

**[NV]** Les coûts de port-in ne sont publiés par aucun des fournisseurs API du panel, à l'exception du port-**out** Telnyx ($6/numéro). À faire chiffrer par écrit.



## 4. SIP trunking — brancher son propre serveur média

### 4.1 Ce que ça change par rapport à une API vocale

Avec une API vocale (Twilio Voice, Telnyx Call Control), l'opérateur héberge le média et vous parlez HTTP/WebSocket. Avec un **trunk SIP**, l'opérateur vous livre de la signalisation SIP et du RTP brut, et **c'est votre serveur qui tient le média**. Vous gagnez le contrôle du codec, du jitter buffer, du barge-in et de la localisation du média ; vous héritez de l'exploitation d'un SBC.

**[R]** Pour Crenolo : **ne pas commencer par là**. L'API vocale permet de livrer un client en jours. Le trunk SIP devient rentable quand le volume de minutes rend la marge de l'API vocale douloureuse, ou quand la latence du média hors de France devient le facteur limitant. C'est une migration de phase 2, pas une décision de départ.

### 4.2 Fournisseurs et prix vérifiés

**[V] OVHcloud — Trunk SIP** (<https://www.ovhcloud.com/fr/phone/sip-trunk/>, 2026-09-13). C'est le seul fournisseur du panel dont la grille française est publiée nettement, en euros, sans login :

| Offre | Prix | Notes |
|---|---|---|
| Trunk SIP à la consommation | **4 € HT/mois soit 4,80 € TTC/mois pour 1 canal**, sans engagement | Appels entrants inclus, sortants à l'usage |
| Trunk SIP appels illimités | **19,99 € HT/mois soit 23,99 € TTC/mois pour 1 canal**, sans engagement | Fixes et mobiles inclus, entrants inclus |
| Frais de mise en service | **9,99 € HT soit 11,99 € TTC** | Les deux offres |
| Capacité | **jusqu'à 100 canaux** | Modulable à la demande |

Compatible « IPBX / UC / SBC », raccordement par connexion Internet standard, portabilité des numéros existants supportée, numéros disponibles en France, Belgique, Suisse et Royaume-Uni. Facturation à la seconde sur l'offre à la consommation.
**[NV]** Le prix unitaire des numéros et les tarifs à la minute détaillés ne figurent pas sur la page produit consultée.

**[V] Twilio — Elastic SIP Trunking, grille France** (<https://www.twilio.com/en-us/sip-trunking/pricing/fr>, 2026-09-13), **en USD** :

| Poste | Prix |
|---|---|
| Origination (entrant), numéro local FR | **$0,0060 / min** |
| Termination vers **fixe FR** | **$0,0147 / min** |
| Termination vers **mobile FR** (Orange, SFR, Bouygues, Free, autres) | **$0,1563 / min** |
| Termination vers **services spéciaux FR** | **$0,5473 / min** |
| Numéro local FR | **$1,3500 / mois** |

À comparer avec la grille **Twilio Voice** (API vocale, <https://www.twilio.com/en-us/voice/pricing/fr>, 2026-09-13) : numéro local **$1,35/mois**, entrant **$0,0100/min**, sortant **$0,0187/min**, mobile FR **$0,1603/min** (ou **$0,0404/min** au départ de l'EEE), ConversationRelay **$0,07/min**, enregistrement **$0,0025/min**.

Deux enseignements chiffrés :
1. **Le trunk SIP est ~40 % moins cher à l'entrant** que l'API vocale chez Twilio ($0,0060 vs $0,0100). Sur un salon qui reçoit 300 minutes/mois, l'écart est de l'ordre du dollar. **Le trunk SIP ne se justifie pas par le prix de la minute à cette échelle.**
2. **Le coût dominant d'un agent vocal n'est pas la téléphonie.** ConversationRelay à $0,07/min est **sept fois** le coût de la minute entrante. Le poste à optimiser est l'IA, pas le transport. C'est contre-intuitif et ça oriente toute l'architecture.

**[V-2] Telnyx** : tarifs Elastic SIP Trunking annoncés « à partir de » **$0,0032/min entrant** et **$0,005/min sortant**, abonnement numéro à partir de **$1,00/mois**, **sans frais de canal** (capacité élastique, tarif par destination). Ces chiffres sont des prix d'appel américains ; **la page tarifaire consultée ne donne pas de grille France** — il faut passer par « rates by country ». <https://telnyx.com/pricing/elastic-sip> (2026-09-13). **[NV]** Prix France Telnyx : non vérifié.

**[NV]** Bandwidth/Voxbone, Keyyo, Ringover, Zadarma, Axialys, Sewan, Alphalink : pas de grille France vérifiée dans cette recherche (budget de requêtes épuisé). Ne rien affirmer sur leurs prix.

### 4.3 Raccordement technique

**Authentification.** Deux modes : `REGISTER` avec identifiants, ou **authentification par adresse IP** (le trunk accepte le trafic venant d'une IP déclarée).
**[R]** Sur un serveur public avec IP fixe, **choisir l'authentification par IP**. Elle supprime le cycle de ré-enregistrement, supprime la classe de pannes « le registre a expiré à 3 h du matin », et rend le NAT non pertinent. Le `REGISTER` n'a de sens que derrière une IP dynamique — ce qui ne devrait jamais être le cas d'un serveur de production.

**Ports.** SIP : 5060 (UDP/TCP), **5061 (TLS)**. **[V-2]** Telnyx expose `sip.telnyx.com:5061` en TLS 1.2/1.3 (TLS 1.0 et 1.1 refusés), autorité de certification Let's Encrypt (migration depuis Sectigo/Digicert au cours de 2026). <https://support.telnyx.com/en/articles/1130711-does-telnyx-encrypt-communication> (2026-09-13).
RTP : une plage UDP à ouvrir en entrée, dimensionnée à **2 ports par appel simultané** (RTP + RTCP). **[H]** — pratique standard, non revérifiée en ligne aujourd'hui.

**Canaux simultanés.** Deux modèles de facturation opposés : OVHcloud facture **au canal** (4 € HT/canal/mois), Telnyx annonce **aucun frais de canal** avec capacité élastique. **[R]** Pour un parc de TPE, le modèle élastique est structurellement meilleur : cent salons qui reçoivent chacun trois appels par jour ne créent presque jamais cent appels simultanés, et payer cent canaux serait absurde. Dimensionner sur le pic réel, pas sur le nombre de clients.

### 4.4 Codecs — le point qui surprend

**[V] Twilio Elastic SIP Trunking** (<https://www.twilio.com/docs/sip-trunking/codecs>, 2026-09-13) supporte **PCMU et PCMA par défaut**, avec accès en **Limited Availability** à **G.729, Opus et AMR-NB**.

Ce qu'il faut en retenir, et qui va à rebours de l'intuition :

> **En téléphonie française, on travaille en G.711 A-law (PCMA), 8 kHz, 64 kbit/s. Opus n'est pas la norme du trunk : c'est une option.**

**Références normatives** (numéros de RFC donnés de mémoire, **non revérifiés en ligne aujourd'hui — [NV] sur la vérification, le contenu est stable**) : **RFC 3551** (profil RTP audio/vidéo, payload type 8 = PCMA, 0 = PCMU) ; **RFC 6716** (codec Opus) ; **RFC 3581** (extension `rport`) ; **RFC 3711** (SRTP) ; **RFC 4733** (événements téléphoniques DTMF, remplace RFC 2833) ; **RFC 3261** (SIP).

**Conséquences réelles pour un agent vocal :**
- **La bande passante audio est plafonnée à ~3,4 kHz** par le réseau téléphonique lui-même. Aucun codec ne récupère ce qui n'a jamais été transmis. Un TTS 24 kHz superbe sera entendu en 8 kHz.
- **Le STT doit être choisi pour le 8 kHz téléphonique**, pas pour de l'audio studio. Les fournisseurs distinguent en général un modèle « phonecall ». **[R]** Vérifier ce point avant de benchmarker : un écart de WER de 5 points vient plus souvent de là que du modèle.
- **Opus ne réduit pas la latence de façon décisive ici.** G.711 n'a quasiment pas de délai algorithmique (pas de look-ahead), là où Opus en a un. Opus gagne sur la robustesse à la perte de paquets et sur la bande passante consommée, pas sur le délai. **[H]**
- **ptime 20 ms** est la valeur de fait. Monter à 40 ms économise des paquets et ajoute 20 ms au budget — mauvais échange quand on se bat pour rester sous 1,1 s. **[H]**

**[R]** Rester en **PCMA/20 ms** de bout en bout, et dépenser l'effort d'optimisation sur l'endpointing et le streaming, pas sur le codec.

### 4.5 NAT

Le symptôme canonique : **l'appel s'établit, la signalisation est parfaite, et personne n'entend personne** — ou une seule des deux parties entend. La cause est presque toujours que le SDP annonce une adresse IP privée que le pair ne peut pas joindre.

Remèdes, par ordre de préférence **[R]** :
1. **Mettre le serveur média sur une IP publique** et faire de l'authentification par IP. Le problème disparaît au lieu d'être contourné. C'est la seule bonne réponse en production.
2. Si le NAT est inévitable : `ext-sip-ip` / `ext-rtp-ip` côté FreeSWITCH, `external_media_address` / `external_signaling_address` et `nat=force_rport,comedia` côté Asterisk (chan_pjsip : `rtp_symmetric`, `force_rport`, `rewrite_contact`). **[NV]** Noms d'options donnés de mémoire, à confirmer dans la documentation courante de chaque projet.
3. `rport` (**RFC 3581**) permet à la réponse de revenir sur le port source observé — indispensable derrière NAT, inutile sans.
4. STUN/ICE relèvent du monde WebRTC ; sur un trunk SIP opérateur, ils ne sont généralement pas la réponse.

### 4.6 Sécurité

**Chiffrement.** **[V-2]** Twilio annonce TLS pour la signalisation et SRTP pour le média, activables sans surcoût sur les trunks élastiques, TLS 1.2 minimum (<https://www.twilio.com/en-us/blog/secure-elastic-sip-trunks>, 2026-09-13). **[V-2]** Telnyx supporte TLS 1.2/1.3 et SRTP, avec `AEAD_AES_256_GCM_8` en cipher préféré par défaut et `AES_CM_128_HMAC_SHA1_80` maintenu pour l'interopérabilité (même source qu'en §4.3).
**[H]** Le coût en latence du chiffrement est négligeable devant les postes STT/LLM/TTS : quelques millisecondes de handshake à l'établissement, un surcoût CPU marginal sur le média. **Il n'y a aucune raison de s'en passer.**

**Fraude au trafic sortant (toll fraud).** C'est le risque financier n° 1 d'un trunk SIP, et il est brutal : un trunk compromis compose des numéros surtaxés à l'international pendant une nuit. Le tarif « services spéciaux FR » vérifié plus haut ($0,5473/min) donne l'échelle, et les destinations internationales exotiques montent bien plus haut.
**[R]** Quatre défenses, toutes obligatoires, aucune suffisante seule :
1. **Authentification par IP + ACL stricte** sur le SBC. Refuser tout SIP venant d'ailleurs, en `DROP` silencieux.
2. **Interdire par défaut l'international et les numéros surtaxés** dans le plan de numérotation. Ouvrir à la demande, destination par destination.
3. **Plafond de dépense et alerte chez le fournisseur** — la plupart en proposent ; les activer au provisionnement, pas après l'incident.
4. **Détection d'anomalie** : alerte sur volume sortant inhabituel, surtout entre 22 h et 6 h.
**[R]** Et une règle produit : un agent de prise de rendez-vous **n'a aucun besoin d'émettre des appels internationaux**. Cadenasser cette capacité dès le jour 1 ferme la quasi-totalité de la surface d'attaque.

### 4.7 Qualité

- **Jitter buffer** : arbitrage direct entre latence ajoutée et robustesse. **[R]** Buffer adaptatif, plafonné bas (de l'ordre de 60 ms), parce que chaque milliseconde ici se paie sur le tour de parole.
- **Perte de paquets** : le PLC de G.711 est rudimentaire. **[H]** Au-delà de quelques pourcents de perte, le STT décroche avant l'oreille humaine — un humain reconstitue, un modèle non. Surveiller la perte comme un indicateur produit, pas seulement réseau.
- **DTMF** : utiliser **RFC 4733** (`telephone-event`), négocié dans le SDP. L'inband passe mal à travers les codecs compressés ; SIP INFO est hors bande mais mal supporté. **[R]** Prévoir le DTMF dès le départ : « tapez 1 pour être rappelé » est le filet de sécurité quand la reconnaissance vocale échoue, et c'est ce qui évite de perdre un client.
- **Écho** : sur un trunk opérateur l'écho est normalement traité en amont, mais un écho résiduel est catastrophique pour un agent vocal — il **se réentend et s'interrompt lui-même**. **[R]** Tester explicitement le barge-in en conditions réelles, depuis un mobile en mains libres, qui est le pire cas.

### 4.8 Jambonz

**[V-2]** jambonz est une plateforme CPaaS open source sous **licence MIT**, conçue par l'auteur du serveur SIP open source drachtio, orientée déploiement d'applications vocales IA, pilotée par **webhooks et API REST**, s'appuyant sur **FreeSWITCH** pour le média, « bring your own everything » (on branche ses propres fournisseurs STT/TTS/LLM et son propre trunk SIP). Auto-hébergeable sur n'importe quelle infrastructure, y compris bare metal et air-gapped. Version hébergée annoncée à **$8,00 par concurrence**, version auto-hébergée gratuite.
Sources : <https://jambonz.org/>, <https://docs.jambonz.org/guides/get-started/jambonz-overview>, <https://github.com/jambonz> (2026-09-13).

**[R] Ce que jambonz apporte réellement par rapport à FreeSWITCH brut** : la couche applicative. FreeSWITCH vous donne un moteur média et vous laisse écrire l'orchestration, la gestion multi-tenant, les webhooks, l'intégration des fournisseurs de parole. jambonz livre tout cela. Pour une équipe qui n'a pas d'ingénieur télécom à temps plein — ce qui est le cas ici — **c'est le bon niveau d'abstraction pour la phase 2** : on garde le média en France et le contrôle du pipeline, sans écrire un softswitch.

**[V-2]** Alternative à connaître : **OpenAI Realtime via SIP** (§6.3) permet de router un appel directement vers le modèle, sans serveur média du tout. C'est plus simple, mais on perd le contrôle de la localisation du média et de l'orchestration.



---

## 5. Réglementation applicable — ce qui est obligatoire, et depuis quand

### 5.1 Tableau de synthèse

| Obligation | Texte | Applicable depuis | Concerne notre cas ? |
|---|---|---|---|
| Informer qu'on parle à une IA | Règlement (UE) 2024/1689, art. 50 §1 | **2 août 2026** [V-2] | **Oui, directement** |
| Marquer les contenus audio synthétiques en format lisible par machine | Règlement (UE) 2024/1689, art. 50 §2 | 2 août 2026, délai de grâce évoqué jusqu'au 2 déc. 2026 pour les systèmes déjà sur le marché [V-2] | Oui (TTS) |
| Règles « haut risque » de l'AI Act | Chapitre III | **Reportées au 2 déc. 2027** (systèmes autonomes) et **2 août 2028** (embarqués) par l'omnibus numérique [V-2] | Probablement non applicable à une prise de RDV [H] |
| Information sur l'enregistrement de l'appel | RGPD art. 12-14 ; doctrine CNIL | RGPD : 25 mai 2018 | Oui |
| Durées de conservation des enregistrements | Référentiel CNIL | Doctrine CNIL, mise à jour 2026 [V-2] | Oui |
| Consentement préalable au démarchage (opt-in) | Art. L. 223-1 c. consom., issu de la loi n° 2025-594 du 30 juin 2025 | **11 août 2026** [V-2] | **Non pour les appels entrants**, oui si rappel commercial |
| Authentification du numéro appelant (MAN) | Loi n° 2020-901 du 24 juillet 2020 (« Naegelen »), art. L. 44 CPCE | 25 juillet 2023 ; durcissement au 1er janvier 2026 [V] | **Oui pour les appels sortants** |
| Acheminement des appels d'urgence | Art. D. 98-8 CPCE | En vigueur | Oui si on devient fournisseur de service [V-2] |
| Déclaration d'opérateur auprès de l'Arcep | Art. L. 33-1 CPCE | **Supprimée** par l'ordonnance n° 2021-650 du 26 mai 2021 [V] | Non — mais le statut d'opérateur reste factuel |

### 5.2 Informer que l'interlocuteur parle à une IA — l'obligation centrale

**[V-2]** L'article 50 §1 du règlement (UE) 2024/1689 impose que « les systèmes d'IA destinés à interagir directement avec des personnes physiques sont conçus et développés de manière à ce que les personnes concernées soient informées qu'elles interagissent avec un système d'IA », sauf si cela est évident pour une personne raisonnablement informée et attentive.
Texte consulté sur le mirror <https://artificialintelligenceact.eu/article/50/> (2026-09-13). **[R]** Relire le texte officiel au JO de l'UE avant rédaction des CGU : le mirror n'est pas la source de droit.

Trois conséquences opérationnelles :

1. **L'exception « c'est évident » ne tient pas ici.** Un agent vocal en voix de synthèse naturelle sur un numéro de salon de coiffure est précisément le cas que l'article vise. **[R]** Considérer l'annonce comme obligatoire, sans discussion.
2. **L'information doit arriver à la première interaction.** **[V-2]** Le §5 prévoit que l'information est fournie de manière claire au plus tard lors de la première interaction. En pratique : la première phrase de l'agent. **[R]** Formulation type, à valider juridiquement : « Bonjour, vous êtes en ligne avec l'assistant vocal automatique du salon X. Cet appel peut être enregistré pour la prise de rendez-vous. »
3. **§2 — marquage machine-readable des contenus audio générés.** **[V-2]** L'obligation vise les *fournisseurs* de systèmes générant du contenu synthétique. **[H]** Pour un intégrateur qui consomme une API TTS tierce, la charge du marquage pèse d'abord sur le fournisseur du modèle ; mais la qualification exacte (fournisseur / déployeur / fournisseur en aval si on rebrande) doit être tranchée par un juriste. **[NV]** Je n'ai pas trouvé de position officielle française tranchant ce point pour les agents vocaux.

**Calendrier AI Act — état réel au 13/09/2026 [V-2]** :
- 2 février 2025 : interdictions (chapitre II) et littératie IA.
- 2 août 2025 : gouvernance, modèles à usage général, sanctions.
- **2 août 2026 : article 50 (transparence) — c'est fait, l'obligation est vivante aujourd'hui.**
- L'omnibus numérique, publié le 19 novembre 2025 et entré en vigueur le 27 juillet 2026, a repoussé les obligations « haut risque » au 2 décembre 2027 (systèmes autonomes) et au 2 août 2028 (systèmes embarqués dans des produits). **Il n'a pas repoussé l'article 50.**
Sources : <https://www.gibsondunn.com/eu-ai-act-omnibus-agreement-postponed-high-risk-deadlines-and-other-key-changes/>, <https://www.pinsentmasons.com/out-law/news/rules-high-risk-ai-delayed-under-eu-omnibus-deal> (2026-09-13). Ce sont des cabinets d'avocats, pas des sources officielles — **[R]** reconfirmer sur EUR-Lex.

**[V-2]** Un délai de grâce pour le seul marquage lisible par machine du §2 courrait jusqu'au **2 décembre 2026** pour les systèmes d'IA générative déjà mis sur le marché avant le 2 août 2026. Source secondaire : <https://www.donneespersonnelles.fr/transparence-ia-article-50-ai-act> (2026-09-13). **[R]** À vérifier impérativement sur le texte de l'omnibus : c'est le seul point du dossier où une source non officielle avance une date qu'aucune source officielle consultée ne confirme.

### 5.3 Voix synthétique et clonage

**[V-2]** L'article 50 §4 traite des contenus de type « deepfake » : obligation de divulguer que le contenu a été généré ou manipulé artificiellement.
**[R]** Deux règles de produit qui découlent du bon sens juridique autant que du texte :
- Ne **jamais** cloner la voix du commerçant sans mandat écrit et sans annonce explicite. Une voix clonée qui ne se déclare pas est exactement le cas visé.
- Préférer une voix de synthèse **neutre et assumée**, annoncée comme telle. C'est aussi ce qui protège commercialement : le client final ne se sent pas trompé.

### 5.4 Enregistrement des appels

**[V-2]** La doctrine CNIL, historiquement portée par la norme simplifiée NS-057 (<https://www.cnil.fr/sites/cnil/files/atoms/files/ns57.pdf>) et par la page « L'écoute et l'enregistrement des appels sur le lieu de travail » (<https://www.cnil.fr/fr/lecoute-et-lenregistrement-des-appels-sur-le-lieu-de-travail>), pose :
- L'enregistrement **ne peut pas être systématique et permanent** lorsqu'il vise à constituer une preuve contractuelle. La CNIL a rappelé le 29 janvier 2026 que l'enregistrement à valeur probatoire est déclenché ponctuellement, pas par défaut, et seulement quand la preuve ne peut être rapportée autrement. Source : <https://www.cnil.fr/fr/lenregistrement-des-conversations-telephoniques-afin-detablir-la-preuve-de-la-formation-dun-contrat> (2026-09-13).
- **Durées de conservation** annoncées par le référentiel CNIL d'avril 2026 : **6 mois** pour un enregistrement à finalité qualité/formation, **5 ans** pour un enregistrement à valeur de preuve, **1 an** pour les documents d'analyse produits à partir des enregistrements. Source : <https://www.cnil.fr/sites/default/files/2026-04/referentiel_durees_de_conservation_gestion_des_ressources_humaines.pdf> (2026-09-13, **[V-2]** — PDF non ouvert directement).
- **Information de l'appelant** en début d'appel : finalité, durée de conservation, droits d'accès et de rectification.

**[R] Architecture qui simplifie la conformité** — c'est le point le plus important de cette section :

> **Ne pas conserver l'audio par défaut.** Transcrire en flux, ne persister que la transcription et les données structurées du rendez-vous, purger l'audio à la fin de l'appel.

Motifs : l'audio est une donnée biométrique potentielle, il porte la voix de l'appelant ; la transcription suffit à toutes les finalités produit (prise de RDV, résumé, qualité) ; et une base sans audio réduit massivement la surface d'une violation de données. Si l'enregistrement audio est activé, il doit l'être **par option explicite du commerçant**, avec annonce renforcée et durée de purge automatique à 6 mois.

**[H]** Le commerçant est responsable de traitement, l'éditeur de l'agent vocal est sous-traitant au sens de l'article 28 RGPD. Un contrat de sous-traitance (DPA) est donc nécessaire dès le premier client. **[NV]** Cette qualification n'est pas confirmée par une source officielle spécifique aux agents vocaux ; elle découle de la structure classique SaaS.

### 5.5 Démarchage téléphonique — ne concerne pas les appels entrants, mais concerne les rappels

**[V-2]** L'article 13 de la **loi n° 2025-594 du 30 juin 2025** réécrit l'**article L. 223-1 du code de la consommation** : depuis le **11 août 2026**, le démarchage téléphonique d'un consommateur est **interdit sans consentement préalable** (bascule opt-out Bloctel → opt-in). Le consentement doit être libre, spécifique, éclairé, univoque et révocable, et la preuve en incombe au professionnel. Amende administrative jusqu'à **375 000 €** pour une personne morale.
Sources : <https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006069565/LEGISCTA000032221441/2026-08-11> (page non ouverte directement), <https://www.donneespersonnelles.fr/demarchage-telephonique> (2026-09-13).
**[V-2]** Un **décret n° 2026-662 du 23 juillet 2026** fixerait les modalités d'archivage du consentement (date et heure du recueil, créneaux d'appel acceptés, conservation **3 ans minimum**). **[R]** Numéro de décret à reconfirmer sur Légifrance avant de le citer à un client.

**Ce que cela change pour Crenolo :**
- **Appels entrants reçus par l'agent : hors champ.** C'est le consommateur qui appelle. **[H]** — le raisonnement est direct mais je n'ai pas de source officielle qui le dise explicitement pour un agent vocal.
- **Rappel automatique, confirmation de RDV, relance de no-show : zone à traiter.** Un rappel de confirmation d'un RDV que le client a lui-même pris n'est pas de la prospection commerciale [H], mais une relance « ça fait 3 mois, vous revenez ? » en est **[H, mais risque élevé]**. **[R]** Interdire par construction toute campagne sortante non sollicitée dans le produit, ou l'assortir d'un recueil de consentement horodaté conforme au décret.

### 5.6 Identification de l'appelant — le MAN, point dur pour les appels sortants

**[V]** Page Arcep « Authentification des numéros de téléphone fixe ou mobile : que dois-je faire en tant qu'opérateur téléphonique ? » (<https://www.arcep.fr/mes-demarches-et-services/acteurs-regules/operateurs-telecoms/fiches-pratiques/authentification-numeros-telephone-fixe-ou-mobile-que-faire-en-tant-que-operateur-telephonique.html>, consultée le 2026-09-13) :

- Fondement : **loi n° 2020-901 du 24 juillet 2020 (« Naegelen »)**, modifiant l'**article L. 44 du CPCE**.
- **Entrée en vigueur des obligations d'authentification : 25 juillet 2023.**
- **Obligation de l'opérateur de départ** : vérifier que son client « est bien affectataire dudit numéro **ou que l'affectataire dudit numéro a préalablement donné son accord** » pour l'utiliser. Vérification systématique, intégrée aux systèmes.
- **Opérateurs de transit et d'arrivée** : « interrompre l'acheminement de l'appel ou du message » quand le dispositif d'authentification n'est pas utilisé ou ne confirme pas l'authenticité.
- **Depuis le 1er janvier 2026** : masquage obligatoire des numéros mobiles français 06/07 non authentifiés provenant de l'étranger ; blocage systématique pour les numéros fixes non authentifiés.

**[V]** Décision Arcep du 2 décembre 2025 sur le plan de numérotation (<https://www.arcep.fr/actualites/actualites-et-communiques/detail/n/plan-de-numerotation-021225.html>, 2026-09-13) : entrée en application au **1er janvier 2026** (sauf Saint-Martin, 1er janvier 2028) ; motivée notamment par **18 000 signalements d'usurpation de numéro depuis janvier 2025** ; création de **numéros spécifiques pour les appels et messages automatisés d'intérêt général**, réservés aux organismes désignés par arrêté.

**[V-2]** Le MAN s'appuie sur les protocoles **STIR/SHAKEN**, déjà déployés aux États-Unis et au Canada — donc pas un mécanisme français ad hoc, mais une déclinaison nationale. Source secondaire : <https://www.sfrbusiness.fr/room/communications-unifiees/appels-frauduleux-loi-naegelen.html> (2026-09-13). **[R]** À reconfirmer sur une décision Arcep si le point devient contractuellement important.

**Conséquence produit, décisive [V + H] :**

> Présenter le numéro du commerçant en CLI lors d'un appel sortant émis par notre plateforme **n'est légal que si le commerçant, affectataire du numéro, a donné son accord préalable, et que cet accord est transmis à l'opérateur de départ**. Ce n'est pas une formalité interne : c'est l'opérateur qui doit pouvoir le justifier.

**[R]** Trois règles :
1. Faire signer un **mandat d'utilisation du numéro** par le commerçant à l'onboarding, et le déposer chez l'opérateur choisi selon sa procédure (chaque fournisseur a la sienne — voir §1).
2. **À défaut de mandat déposé, sortir avec notre propre numéro**, pas avec celui du commerçant. Un appel avec CLI non authentifié sera masqué ou bloqué, et l'échec sera silencieux.
3. Ne jamais présenter un numéro mobile 06/07 non détenu. C'est la cible n° 1 du dispositif anti-fraude.

### 5.7 Numéros d'urgence

**[V-2]** L'**article D. 98-8 du CPCE** (<https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000035813246/>) impose au **fournisseur de service de communications interpersonnelles fondé sur la numérotation** d'acheminer **gratuitement** les communications d'urgence vers le centre compétent, de mettre sans délai les informations de localisation de l'appelant à disposition des services de secours par un procédé sécurisé, de garantir un accès équivalent aux utilisateurs handicapés, et de ne pas facturer ces appels. Modifié notamment par le décret n° 2021-1281 du 30 septembre 2021.

**Notre cas :**
- **[H]** Un agent vocal qui **reçoit** des appels n'émet pas d'appels d'urgence et n'est pas, pour cette fonction, un fournisseur de service d'accès au 112. L'obligation D. 98-8 pèse sur l'opérateur qui fournit le numéro (Twilio, OVHcloud, Telnyx…), pas sur l'applicatif.
- **[V-2]** En revanche, si le service évolue vers la **fourniture d'un numéro sortant au commerçant** utilisé comme sa ligne principale, la question de l'accès au 112 depuis cette ligne se pose réellement.
- **[R] Point de sécurité produit, non réglementaire mais impératif** : l'agent doit détecter une urgence exprimée (« il y a le feu », détresse, malaise) et **dire clairement à l'appelant de raccrocher et de composer le 112/15/18**. Un agent qui gère une urgence comme une demande de rendez-vous est un risque humain et réputationnel majeur. Le prévoir dans le prompt système, et le tester.
- **Le renvoi d'appel ne change rien au 112** [H] : l'appelant compose le 112 depuis son propre terminal, il ne passe pas par le numéro renvoyé.

### 5.8 Faut-il être opérateur déclaré ?

**[V]** Page FAQ de l'extranet Arcep (<https://extranet.arcep.fr/communications-electroniques/questions-frequentes>, 2026-09-13) : l'**ordonnance n° 2021-650 du 26 mai 2021**, transposant la directive (UE) 2018/1972 (code des communications électroniques européen), a **supprimé l'obligation de déclaration préalable** prévue à l'article L. 33-1 du CPCE. Ce qui détermine le statut d'opérateur est désormais **la nature réelle de l'activité** au sens de l'article L. 32, 15° du CPCE — et non un enregistrement administratif. Les activités de conseil, d'assistance à ingénierie ou de prestation de services dans le secteur des télécoms ne sont notamment pas concernées.

**[H] Lecture pour Crenolo** : tant qu'on **achète** des numéros et des minutes à un opérateur déclaré (Twilio, OVHcloud…) et qu'on vend une **application** de prise de rendez-vous, on est prestataire de services, pas opérateur. On bascule vers le statut d'opérateur si on **revend de la connectivité en propre** : attribution de numéros aux clients sous notre nom, acheminement pour compte de tiers, facturation de minutes à la minute. **[R]** Rester délibérément du côté « application » aussi longtemps que possible : le franchissement déclenche les obligations D. 98-x (urgence, interceptions légales, annuaire, conservation des données).

### 5.9 Conservation des données de connexion

**[NV]** Je n'ai pas pu ouvrir l'article L. 34-1 du CPCE ni le décret n° 2021-1362 depuis cet environnement (domaine Légifrance refusé). Les durées exactes de conservation des données de trafic et des données d'identité ne sont donc **pas vérifiées** dans ce rapport. **[H]** Ces obligations pèsent en premier lieu sur l'opérateur qui achemine, pas sur l'application. **[R]** À faire trancher par un conseil avant la première signature d'un client à volume.

---

## 6. Latence — où héberger le média et quel budget viser

### 6.1 Les seuils de référence

**[V-2]** **Recommandation UIT-T G.114** (« One-way transmission time ») fixe les limites générales du délai **de bouche à oreille, en un sens** :
- **0 à 150 ms** : plage préférée, interactivité essentiellement transparente pour la plupart des applications ;
- **150 à 400 ms** : acceptable, avec dégradation croissante, à condition que les administrations soient conscientes de l'impact ;
- **au-delà de 400 ms** : inacceptable pour la planification générale des réseaux.
Le texte précise que les tâches très interactives peuvent être affectées à des délais bien inférieurs à 150 ms.
Source : <https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-G.114-200305-I%21%21PDF-E> et copie PDF <http://www.cs.columbia.edu/~andreaf/new/documents/other/T-REC-G.114-200305.pdf> (2026-09-13).

**Attention au contresens le plus fréquent dans ce domaine** : G.114 mesure le **délai de transmission**, c'est-à-dire le temps qu'un son met à traverser le réseau. Il ne mesure **pas** le temps de réflexion de l'agent. Les 150 ms de G.114 sont un budget **réseau**, pas un budget conversationnel. Les deux s'additionnent.

**[V-2]** **Stivers et al., PNAS 2009**, « Universals and cultural variation in turn-taking in conversation », 106(26):10587-10592 : sur 10 langues, la distribution des temps de réponse est unimodale avec un **pic à moins de 200 ms** après la fin de la question, et les écarts entre langues restent dans une fourchette de **250 ms** autour de la moyenne inter-langues. Source : <https://www.pnas.org/doi/10.1073/pnas.0903616106> (2026-09-13).

C'est **la** donnée qui explique pourquoi un agent vocal « paraît lent » : l'oreille humaine est calibrée sur un silence de 200 ms entre deux tours de parole. Tout ce qui dépasse est perçu comme une hésitation, puis comme une panne.

### 6.2 Le budget réel publié par un acteur du domaine

**[V]** Twilio, « A guide to core latency in AI voice agents » (<https://www.twilio.com/en-us/blog/developers/best-practices/guide-core-latency-ai-voice-agents>, consultée le 2026-09-13), publie des cibles de référence (baseline 2025, architecture en cascade sans optimisation avancée) :

| Poste | Cible | Limite haute |
|---|---|---|
| **Mouth-to-ear turn gap** (bout en bout perçu) | **1 115 ms** | **1 400 ms** |
| **Platform turn gap** (plateforme seule) | **885 ms** | **1 100 ms** |
| Speech-to-Text | 350 ms | 500 ms |
| LLM — time to first token | 375 ms | 750 ms |
| Text-to-Speech — time to first byte | 100 ms | 250 ms |
| Transmission réseau terminal → media edge | ~40 ms | — |
| Orchestration + buffering | ~30-70 ms | — |
| Décodage | ~25 ms | — |
| Détection de fin de tour (seuil de silence fixe) | ~500 ms | — |

**[V]** Twilio annonce pour son produit ConversationRelay « **<0.5 second median latency, <0.725 second at the 95th percentile** », soit **p50 491 ms / p95 713 ms** sur benchmarks internes (même page).

**Lecture honnête de ce tableau** : la cible industrielle réaliste est **environ 1,1 s** de silence perçu, soit **cinq fois** le gap humain naturel de 200 ms. Personne ne tient 200 ms aujourd'hui en cascade STT→LLM→TTS. **[R]** Ne pas promettre « indiscernable d'un humain » à un commerçant. Promettre « répond immédiatement, ne fait jamais sonner dans le vide » — ce qui est vrai et suffit largement à battre un répondeur.

**[V-2]** Autres chiffres constructeurs, utiles pour dimensionner :
- **Deepgram Nova-3** : latence de streaming annoncée **sous 300 ms**, typiquement 200-300 ms en bonnes conditions ; taille de buffer de streaming recommandée **20 à 100 ms** d'audio. <https://developers.deepgram.com/docs/measuring-streaming-latency> (2026-09-13).
- **ElevenLabs Flash v2.5** : **~75 ms** d'inférence modèle, sur entrées courtes et conditions normales — **ce chiffre est le temps d'inférence seul, pas la latence bout en bout**, qui dépend de la localisation de l'appelant et du type d'endpoint. <https://elevenlabs.io/docs/overview/models> et <https://elevenlabs.io/docs/eleven-api/concepts/latency> (2026-09-13).

Le poste qu'on oublie toujours : **la détection de fin de tour, ~500 ms de silence**. C'est souvent le premier contributeur au budget, et c'est le seul qu'on optimise sans changer de fournisseur (VAD sémantique, endpointing prédictif).

### 6.3 Où héberger le média

**[V]** OpenAI propose une **résidence des données dans l'UE** pour les modèles temps réel (`gpt-realtime-2025-08-28`, `gpt-4o-realtime-preview-2025-06-03`), activable au niveau de l'organisation, via l'endpoint **`https://eu.api.openai.com`**, avec un **surcoût de 10 %** pour les modèles sortis à partir du 5 mars 2026 éligibles à la résidence des données. Source : <https://help.openai.com/en/articles/10503543-data-residency-for-the-openai-api> (page renvoyant 403 en accès direct, information relevée via recherche le 2026-09-13 — **[V-2]**).

**[V-2]** OpenAI expose aussi un **connecteur SIP** pour la Realtime API : on appelle `sip:proj_xxxxx@sip.api.openai.com`, un webhook notifie l'appel entrant, puis on pilote la conversation sur `wss://api.openai.com/v1/realtime?call_id=...`. La doc recommande explicitement de passer par un fournisseur de trunk SIP (Twilio cité) pour raccorder un numéro. <https://developers.openai.com/api/docs/guides/realtime-sip> (2026-09-13).

**[NV]** Je n'ai **pas** trouvé de mesure RTT publiée par une source officielle pour Paris↔Paris, Paris↔Francfort ou Paris↔Virginie (us-east-1). AWS documente l'existence d'un outil de mesure inter-régions (<https://aws.amazon.com/blogs/networking-and-content-delivery/monitoring-aws-global-network-performance/>) mais ne publie pas la matrice de valeurs. **Je ne donne donc aucun chiffre de RTT transatlantique dans ce rapport.** Les valeurs qu'on lit partout (« 80-90 ms Paris↔Virginie ») circulent sur des sites de mesure communautaires, pas sur des sources d'opérateur. **[R]** Mesurer soi-même depuis le futur hôte : c'est une heure de travail et ça vaut mieux que n'importe quelle citation.

**[H] Ce que la physique impose quand même** : le média fait l'aller-retour. Un serveur média aux États-Unis pour un appel Paris↔Paris ajoute **deux traversées transatlantiques** au budget, et cet ajout se paie sur chaque tour de parole, pas une fois par appel. Comme la cible totale tient déjà difficilement sous 1,1 s, c'est un poste qu'on ne peut pas se permettre.

**[R] Règle d'hébergement, par ordre de priorité :**
1. **Le média (SBC, FreeSWITCH/Jambonz, RTP) en France.** Régions disponibles : AWS `eu-west-3` (Paris), GCP `europe-west9` (Paris), Azure France Central, Scaleway Paris, OVHcloud (Gravelines/Roubaix/Strasbourg). **[NV]** Je n'ai pas revérifié aujourd'hui l'existence de chacune de ces régions sur les pages fournisseurs — à confirmer avant de choisir.
2. **Le STT en Europe** si le fournisseur le propose ; sinon, accepter le trajet mais le mesurer.
3. **Le LLM en Europe** dès que possible (endpoint `eu.api.openai.com` pour OpenAI), en acceptant le surcoût de 10 % : il achète à la fois de la latence et de la conformité RGPD, c'est le meilleur rapport des deux.
4. **Le TTS au plus près du média** : c'est le dernier maillon avant l'oreille, sa latence est intégralement perçue.

**[R]** Et une règle d'architecture qui vaut tous les choix de région : **commencer à parler avant d'avoir fini de penser.** Le streaming token-par-token du LLM vers le TTS, et le TTS en flux vers le RTP, effacent plusieurs centaines de millisecondes perçues. Un agent qui commence sa phrase à 400 ms et la termine à 2 s est jugé rapide ; un agent qui se tait 1,2 s puis débite tout d'un coup est jugé lent. C'est le même budget.

---

## 7. Le chemin d'onboarding le plus rapide pour un commerçant

**Principe** : le commerçant ne change rien. Il garde son numéro, son opérateur, son abonnement. On lui donne un numéro d'arrivée et un code à taper. C'est tout.

**Prérequis côté plateforme, faits une fois pour toutes, pas par client** : compte opérateur créé, bundle réglementaire validé (Twilio ~24 h ouvrées, Telnyx ~72 h), stock de numéros **09** pré-acheté. **[R] Pré-acheter les numéros par lots** : à $0,50/mois chez Telnyx, garder dix numéros d'avance coûte $5/mois et supprime le seul délai incompressible du parcours. Un commerçant qui attend 72 h de KYC pendant la démo est un commerçant perdu.

### 7.1 Le parcours, chronométré

| # | Étape | Durée | Qui | Notes |
|---|---|---|---|---|
| 1 | Attribuer un numéro **09** du stock au commerçant | **~5 s** | plateforme | `POST /v2/number_orders` si le stock est vide, sinon assignation immédiate |
| 2 | Configurer l'agent : nom du salon, horaires, prestations, voix | **5-10 min** | commerçant, guidé | La vraie durée du parcours est ici, pas dans la téléphonie |
| 3 | **Appel de test entrant** sur le numéro 09 | **~1 min** | commerçant | Valide le pipeline avant de toucher à sa ligne |
| 4 | Vérifier les deux bloqueurs : protection anti-renvoi sur le 09, rejet des anonymes désactivé | **~30 s** | plateforme, automatique | §2.4 |
| 5 | **Composer le code de renvoi** sur la ligne du commerçant | **~15 s** | commerçant | Code affiché à l'écran, prérempli avec le numéro 09, en un tap sur mobile |
| 6 | **Appel de test depuis un autre téléphone** vers le numéro habituel | **~1 min** | commerçant | La seule preuve qui compte |
| 7 | Relever le CLI reçu : numéro transmis ou masqué ? | automatique | plateforme | Conditionne les fonctions qui dépendent du numéro appelant |

**Total réaliste : 8 à 15 minutes**, dont **moins de 2 minutes de téléphonie**. Tout le reste est de la configuration métier.

### 7.2 Les codes à afficher, par opérateur

L'écran doit afficher **un seul code**, prérempli, choisi d'après l'opérateur déclaré par le commerçant. Tous ces codes sont vérifiés en §2.1.

**Recommandation par défaut : le renvoi sur non-réponse**, pas l'inconditionnel. Le commerçant décroche s'il est disponible ; l'IA prend le relais s'il ne répond pas. C'est ce qu'il veut réellement, et c'est ce qui évite le rejet de l'outil dès la première semaine.

| Opérateur du commerçant | Code à taper (non-réponse) | Repli |
|---|---|---|
| Orange mobile | `**61*0XXXXXXXXX*11#` | délai fixe 20 s, non réglable |
| Orange fixe / Livebox | **pas de code** → Espace client, « Si vous ne répondez pas ou êtes déjà en ligne » | proposer l'assistance guidée |
| SFR fixe / box | `*61*0XXXXXXXXX#` | délai réglable si Fibre |
| SFR mobile | **aucun code officiel publié** | passer par le service client SFR, ou proposer l'inconditionnel hors horaires |
| Freebox | `*61*0XXXXXXXXX*15#` | `<tempo>` entre 5 et 20 s ; penser à `*75*3#` pour libérer la messagerie |
| Free mobile | **aucun code officiel publié** | Espace Abonné ; **option facturée 0,05 €/min** |
| Bouygues mobile | `*61*0XXXXXXXXX#` | si blocage : 610 → 0 → 1 → 2 pour réinitialiser |
| Bouygues Bbox | `*61*0XXXXXXXXX#` | **renvoi gratuit vers un fixe** |

**[R]** Afficher aussi, systématiquement, **le code d'annulation** (`##61#` chez Orange, `#61#` ailleurs). Un commerçant qui sait comment revenir en arrière essaie ; un commerçant qui ne le sait pas hésite. C'est un point de conversion, pas un détail de documentation.

### 7.3 Ce qu'il faut dire au commerçant, et ne pas dire

**Dire :**
- « Vous gardez votre numéro. On ne touche à rien chez votre opérateur. »
- « Si ça ne vous plaît pas, vous tapez un code et tout redevient comme avant. »
- « Votre opérateur peut vous facturer les appels transférés » — **c'est vrai chez les quatre**, sauf Bouygues Bbox vers un fixe. Le taire, c'est préparer une réclamation.

**Ne pas dire :**
- « On ne verra pas la différence avec un humain. » Faux : la cible industrielle est ~1,1 s de silence entre les tours (§6.2), cinq fois le gap humain naturel.
- « L'agent saura qui appelle. » Pas garanti : l'ARCEP recommande explicitement aux opérateurs de **masquer le CLI** quand l'authentification ne suit pas un renvoi (§2.4).

### 7.4 Ce qui doit être prêt côté conformité avant le premier client

1. **L'annonce IA dans la première phrase de l'agent** — obligation vivante depuis le 2 août 2026 (§5.2). Non négociable, non désactivable par le commerçant.
2. **Un DPA signé** entre l'éditeur (sous-traitant) et le commerçant (responsable de traitement).
3. **Pas d'enregistrement audio par défaut** (§5.4). Transcription seule, purge de l'audio en fin d'appel.
4. **Aucune campagne d'appels sortants non sollicités** dans le produit — opt-in obligatoire depuis le 11 août 2026 (§5.5).
5. **Un mandat d'utilisation du numéro** signé si on doit un jour présenter le numéro du commerçant en CLI sortant (§5.6).
6. **Une détection d'urgence** dans le prompt système, qui renvoie vers le 112 (§5.7).



## 8. Ce qui n'a PAS pu être vérifié

Liste explicite, pour qu'aucun trou ne passe pour une réponse.

**Prix et conditions commerciales**
- Vonage : **aucun** prix, aucune exigence KYC FR, aucune procédure de portabilité FR — site en HTTP 403.
- Telnyx : **aucun tarif sortant France publié**.
- OVHcloud : grille à la minute non publiée ; délai d'activation d'un numéro non publié.
- Twilio : divergence $1,35 / $1,15 entre deux sources officielles ; coût de port-in non publié.
- Bandwidth, Keyyo : aucun tarif France public.
- Plivo : exigences KYC France ; procédure de portabilité France.
- Zadarma : délai d'activation ; portabilité France.
- Coûts de port-in : non publiés par l'ensemble du panel (sauf port-out Telnyx à $6).

**Téléphonie grand public**
- **Codes MMI mobiles SFR et Free Mobile** : aucun des deux opérateurs ne les publie. Volontairement non repris depuis des sources tierces.
- Délai avant renvoi en secondes : Orange mobile (fixe à 20 s), SFR Fibre, Bouygues (valeurs des menus déroulants).
- **Comportement du CLI après renvoi chez les quatre opérateurs** — le point le plus important, et documenté nulle part. À tester en réel.
- Offres Trunk SIP / Business des quatre opérateurs : aucune documentation publique exploitable.
- Coût du renvoi sur mobile Orange.

**Droit**
- Les textes Légifrance, CNIL et EUR-Lex n'ont **pas pu être ouverts directement** depuis cet environnement. Tout le §5 marqué **[V-2]** repose sur des sources secondaires citant ces textes. **Aucun engagement client ne doit être pris sur cette base sans relecture des textes eux-mêmes.**
- Article L. 34-1 CPCE et décret n° 2021-1362 (conservation des données de connexion) : non vérifiés.
- Numéro du décret n° 2026-662 du 23 juillet 2026 : à reconfirmer.
- Délai de grâce au 2 décembre 2026 pour le marquage machine-readable de l'article 50 §2 : avancé par une seule source secondaire, non confirmé officiellement.
- Qualification exacte fournisseur / déployeur au sens de l'AI Act pour un intégrateur de TTS tiers.

**Latence**
- **Aucune mesure RTT officielle** Paris↔Paris, Paris↔Francfort ou Paris↔us-east-1. Aucun chiffre de RTT transatlantique n'est avancé dans ce rapport.
- Existence des régions cloud françaises citées, non revérifiée aujourd'hui sur les pages fournisseurs.

---

## 9. Sources

Toutes consultées le **2026-09-13**.

**Réglementation**
- ARCEP, fiche pratique authentification des numéros (MAN) — <https://www.arcep.fr/mes-demarches-et-services/acteurs-regules/operateurs-telecoms/fiches-pratiques/authentification-numeros-telephone-fixe-ou-mobile-que-faire-en-tant-que-operateur-telephonique.html>
- ARCEP, plan de numérotation, communiqué du 02/12/2025 — <https://www.arcep.fr/actualites/actualites-et-communiques/detail/n/plan-de-numerotation-021225.html>
- ARCEP, décision n° 2026-0113-RDPI — <https://www.arcep.fr/uploads/tx_gsavis/26-0113-RDPI.pdf>
- ARCEP, plan de numérotation, version du 23/07/2025 — <https://www.arcep.fr/fileadmin/user_upload/56-25-version-francaise.pdf>
- Extranet ARCEP, FAQ opérateurs (suppression de la déclaration préalable) — <https://extranet.arcep.fr/communications-electroniques/questions-frequentes>
- Règlement (UE) 2024/1689, article 50 (mirror consulté, **non officiel**) — <https://artificialintelligenceact.eu/article/50/>
- Report des obligations « haut risque » (analyses de cabinets) — <https://www.gibsondunn.com/eu-ai-act-omnibus-agreement-postponed-high-risk-deadlines-and-other-key-changes/> · <https://www.pinsentmasons.com/out-law/news/rules-high-risk-ai-delayed-under-eu-omnibus-deal>
- Délai de grâce art. 50 §2 (source secondaire, à confirmer) — <https://www.donneespersonnelles.fr/transparence-ia-article-50-ai-act>
- CNIL, norme simplifiée NS-057 — <https://www.cnil.fr/sites/cnil/files/atoms/files/ns57.pdf>
- CNIL, écoute et enregistrement des appels sur le lieu de travail — <https://www.cnil.fr/fr/lecoute-et-lenregistrement-des-appels-sur-le-lieu-de-travail>
- CNIL, enregistrement des conversations pour preuve de formation d'un contrat — <https://www.cnil.fr/fr/lenregistrement-des-conversations-telephoniques-afin-detablir-la-preuve-de-la-formation-dun-contrat>
- CNIL, référentiel durées de conservation (avril 2026) — <https://www.cnil.fr/sites/default/files/2026-04/referentiel_durees_de_conservation_gestion_des_ressources_humaines.pdf>
- Légifrance, art. L223-1 à L223-7 c. consom. au 11/08/2026 — <https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006069565/LEGISCTA000032221441/2026-08-11>
- Légifrance, art. D98-8 CPCE — <https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000035813246/>
- Légifrance, art. L33-1 CPCE — <https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000047293234>
- Légifrance, décret n° 2021-1281 du 30/09/2021 — <https://www.legifrance.gouv.fr/jorf/article_jo/JORFARTI000044154230>

**Opérateurs API**
- Twilio : <https://www.twilio.com/en-us/guidelines/fr/regulatory> · <https://www.twilio.com/en-us/guidelines/fr/voice> · <https://www.twilio.com/en-us/guidelines/fr/porting> · <https://www.twilio.com/en-us/legal/service-country-specific-terms/france-phone-numbers> · <https://www.twilio.com/en-us/voice/pricing/fr> · <https://www.twilio.com/en-us/sip-trunking/pricing/fr> · <https://assets.cdn.prod.twilio.com/pricing-csv/OutboundVoicePricing.csv> · <https://www.twilio.com/content/dam/twilio-com/pricing-data/en/csv/PMded94a0dae30eaaec0f115f22859bd38_SiteNumbersPricing.csv> · <https://www.twilio.com/docs/phone-numbers/regulatory/faq> · <https://www.twilio.com/docs/phone-numbers/api/incomingphonenumber-resource> · <https://www.twilio.com/docs/sip-trunking/codecs> · <https://www.twilio.com/en-us/blog/secure-elastic-sip-trunks>
- Telnyx : <https://telnyx.com/pricing.md> · <https://telnyx.com/pricing/elastic-sip> · <https://support.telnyx.com/en/articles/1311445-france-did-requirements> · <https://support.telnyx.com/en/articles/3266956-france-number-porting> · <https://support.telnyx.com/en/articles/1130711-does-telnyx-encrypt-communication> · <https://developers.telnyx.com/docs/numbers/phone-numbers/number-orders>
- OVHcloud : <https://www.ovhcloud.com/fr/phone/sip-trunk/> · <https://www.ovhcloud.com/fr/phone/numeros/> · <https://www.ovhcloud.com/fr/phone/voip/> · <https://api.ovh.com/1.0/order.json> · <https://api.ovh.com/1.0/telephony.json>
- Zadarma : <https://zadarma.com/en/tariffs/numbers/france/paris/> · <https://zadarma.com/en/tariffs/calls/france/> · <https://zadarma.com/en/support/instructions/api/numbers/>
- Plivo : <https://www.plivo.com/voice/pricing/fr/> · <https://www.plivo.com/docs/numbers/api/phone-number/> · <https://www.plivo.com/docs/numbers/regulatory-compliance/activation>
- Vonage : <https://developer.vonage.com/en/api/numbers> (tarifs en 403)
- Bandwidth : <https://www.bandwidth.com/global-reach/> · <https://www.bandwidth.com/pricing/> · <https://www.bandwidth.com/regulations/> · <https://dev.bandwidth.com/docs/numbers/guides/searchingForNumbers>
- Sipgate : <https://www.sipgate.de/funktionen/internationale-rufnummern> · <https://api.sipgate.com/v2/swagger.json>
- Keyyo : <https://www.keyyo.com/fr/numero-virtuel> · <https://www.keyyo.com/fr/numeros-speciaux-overview> · <https://www.keyyo.com/fr/telephonie-faq/conservation-numeros> · <https://api.keyyo.com/developers>
- Ringover : <https://www.ringover.fr/tarifs> · <https://www.ringover.fr/numeros-virtuels> · <https://www.ringover.fr/conserver-vos-numeros> · <https://developer.ringover.com/web/openapi_public.yml>

**Opérateurs grand public FR**
- Orange : <https://assistance.orange.fr/nid/172736> · <https://assistance.orange.fr/telephone/telephone-par-internet/toutes-les-livebox/installer-et-utiliser/rester-joignable/renvoi-d-appel/telephone-par-internet-activer-ou-desactiver-le-renvoi-d-appel_19032-19121> · <https://assistance.orange.fr/telephone/telephone-fixe/installer-et-utiliser/rester-joignable/transfert-d-appels/transfert-d-appels-activer-ou-desactiver-_20309-20699> · <https://assistancepro.orange.fr/telephone_mobile/la_messagerie_vocale_visuelle/messagerie_vocale/comment_programmer_un_renvoi_dappel_depuis_mon_mobile_-395750> · <https://assistancepro.orange.fr/telephone_fixe/rester_joignable/renvoi_et_transfert_d_appels/renvoi_et_transfert_dappel__mode_demploi_clients_pro-395333>
- SFR : <https://assistance.sfr.fr/internet-tel-fixe/tel-fixe/activer-desactiver-options.html> · <https://assistance.sfr.fr/internet-tel-fixe/tel-fixe/gerer-options-appels-box-thd-sfr.html> · <https://assistance.sfr.fr/internet-tel-fixe/tel-fixe/tarifs-telephoniques-ligne-fixe-sfr.html> · <https://assistance.sfr.fr/sitemap.xml>
- Free : <https://assistance.free.fr/articles/1755> · <https://assistance.free.fr/articles/telephone-fixe-transferer-tous-les-appels-entrants-553> · <https://assistance.free.fr/articles/telephone-fixe-transferer-un-appel-sur-non-reponse-552> · <https://assistance.free.fr/articles/551> · <https://assistance.free.fr/articles/telephonie-fixe-gerer-le-renvoi-dappel-vers-la-messagerie-574> · <https://assistance.free.fr/articles/554> · <https://assistance.free.fr/articles/892> · <https://mobile.free.fr/docs/bt/tarifs.pdf> · <https://support-pro.free.fr/comment-parametrer-un-renvoi-dappel/> · <https://support-pro.free.fr/comment-activer-un-transfert-dappel/>
- Bouygues Telecom : <https://www.assistance.bouyguestelecom.fr/s/article/activation-desactivation-renvoi-appel> · <https://www.assistance.bouyguestelecom.fr/s/article/renvoi-appel-telephone-fixe>

**Technique et latence**
- UIT-T G.114 — <https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-G.114-200305-I%21%21PDF-E> · copie <http://www.cs.columbia.edu/~andreaf/new/documents/other/T-REC-G.114-200305.pdf>
- 3GPP TS 22.030 (codes MMI) — <http://www.arib.or.jp/english/html/overview/doc/STD-T63V12_10/5_Appendix/Rel13/22/22030-d00.pdf>
- Stivers et al., PNAS 2009, 106(26):10587-10592 — <https://www.pnas.org/doi/10.1073/pnas.0903616106>
- Twilio, guide de la latence des agents vocaux IA — <https://www.twilio.com/en-us/blog/developers/best-practices/guide-core-latency-ai-voice-agents>
- Deepgram, mesure de la latence de streaming — <https://developers.deepgram.com/docs/measuring-streaming-latency>
- ElevenLabs, modèles et latence — <https://elevenlabs.io/docs/overview/models> · <https://elevenlabs.io/docs/eleven-api/concepts/latency>
- OpenAI, Realtime via SIP — <https://developers.openai.com/api/docs/guides/realtime-sip>
- OpenAI, résidence des données — <https://help.openai.com/en/articles/10503543-data-residency-for-the-openai-api> (403 en accès direct)
- jambonz — <https://jambonz.org/> · <https://docs.jambonz.org/guides/get-started/jambonz-overview> · <https://github.com/jambonz>
- AWS, mesure des performances réseau inter-régions — <https://aws.amazon.com/blogs/networking-and-content-delivery/monitoring-aws-global-network-performance/>

