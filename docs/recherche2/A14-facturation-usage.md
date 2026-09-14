# A14 — Facturation à l'usage pour un SaaS vocal français

**Consulté le 2026-09-14.** [F] · [H] · [R] · [NV].

## 1. Le fait qui change la donne : Stripe a absorbé Metronome

**[F]** `docs.stripe.com/billing/subscriptions/usage-based` : « Metronome est la plateforme principale de facturation à l'usage de Stripe, **recommandée pour toutes les nouvelles intégrations**. La facturation à l'usage classique, reposant sur l'API Billing Meters, est une brique de bas niveau qui **reste entièrement prise en charge pour les intégrations existantes**. » Bandeau `metronome.com` : « Metronome is now part of Stripe. »

⚠️ **[F] Contre-indication documentée par Stripe lui-même** : prendre Billing Meters plutôt que Metronome si l'on a besoin d'une « compatibilité complète avec **Connect, Checkout, Adaptive Pricing ou Workflows** (Metronome ne prend en charge que partiellement certaines de ces fonctionnalités) ».
**[R]** Un parcours d'inscription en libre-service repose typiquement sur **Stripe Checkout** — précisément dans la liste des prises en charge partielles. On est donc poussé vers un produit recommandé qui peut casser le tunnel d'achat, ou vers une brique rétrogradée au rang de « maintenu pour l'existant ». **[NV]** prix de Metronome : page inaccessible.

## 2. Mécanique Stripe, vérifiée

**[F]** `POST /v1/billing/meter_events` — champs `event_name` (requis), `payload` (requis), `identifier` (optionnel), `timestamp` (optionnel).
**[F] Idempotence, citation littérale** : « **Stripe enforces uniqueness within a rolling period of at least 24 hours.** The enforcement of uniqueness primarily addresses issues arising from accidental retries. »
**[R]** C'est un **garde-fou anti-retry, pas une dédup métier**. Au-delà de 24 h, rejouer le même identifiant peut refacturer. **La table de vérité reste chez nous.**
**[F] Backfill** : « Must be within the past **35 calendar days** or up to 5 minutes in the future. »
**[R]** 35 jours couvrent un cycle mensuel, **mais seulement avant l'émission de la facture**. Une minute retrouvée après facturation exige un avoir ou un report.
**[F]** Traitement **asynchrone** : l'usage compilé « peut ne pas refléter immédiatement les derniers événements ».

**Tarifs France** [F, `stripe.com/fr/pricing`] : cartes EEE standard **1,5 % + 0,25 €** · premium 2,8 % + 0,25 € · **prélèvement SEPA 0,35 € fixe** · Stripe Billing **0,7 % du volume** · Stripe Tax 0,5 %/transaction ou 0,45 €/transaction en API.

## 3. Lago — et la question qui bloque

**[F]** Licence vérifiée à la source : **AGPL v3**, texte intégral et nu dans `lago-api/main/LICENSE`.
**[F] Idempotence** : « Lago **deduplicates usage events by `transaction_id`**, so retrying an event does not bill it twice » + « Atomic batch processing — rejected batches persist no events ».
**[H]** Modèle **plus fort que Stripe** : dédup sans fenêtre de 24 h annoncée, et lot atomique. Pour un agent vocal, `call_id → transaction_id` est un mapping direct et sûr.
**[F] Prix** : `getlago.com/pricing` **n'affiche aucun montant** — « Contact us ».
⚠️ **[NV] BLOQUANT** : `lago-api/main/ee/LICENSE` renvoie **404**. Le statut juridique du code entreprise **n'est pas établi**. L'AGPL étant virale sur l'usage réseau, **faire trancher par un juriste avant d'écrire une ligne d'intégration**, pas après.

## 4. Les autres

**Paddle** [F, `paddle.com/pricing`] : **5 % + 0,50 $ par transaction**, *merchant of record*, TVA UE collectée et reversée à notre place, aucun palier gratuit. **[F] Facturation à l'usage : non documentée** — ni sur la page tarifs, ni sur `/billing`.
**[R] Disqualifiant** : on paierait ~3,5 points de marge pour résoudre un problème de TVA multi-pays **qu'on n'a pas** avec une clientèle de TPE françaises.

**Chargebee** [F] : plan Flow **160 $/mois** (100 M d'événements inclus) ; « 0 $ + 0,80 % du volume facturé jusqu'à 20 000 $ ; 99 $ + 0,65 % au-delà ». **[NV]** articulation exacte entre l'abonnement et le pourcentage. **[R]** 160 $/mois de plancher avant le premier client : choix de phase 2.

**Orb** : **[NV] intégralement** — trois URL en échec. Rien n'est affirmé.

## 5. Coût mensuel, calculs montrés

Hypothèses [H] : panier 150 € HT/mois/client (abonnement + minutes), une facture et une transaction par mois, cartes EEE **standard**, Stripe Tax en API. MRR : 50 clients = 7 500 € · 500 clients = 75 000 €.

| Scénario | Par facture | 50 clients | 500 clients |
|---|---|---|---|
| **A — Stripe complet, carte** | 2,50 € (PSP) + 1,05 € (Billing) + 0,45 € (Tax) = **4,00 €** (2,67 % du CA) | 200 €/mois | **2 000 €/mois** |
| **B — Stripe, SEPA** | 0,35 + 1,05 + 0,45 = **1,85 €** (1,23 %) | 92,50 € | **925 €/mois** |
| **C — Lago auto-hébergé + Stripe PSP (SEPA)** | **0,35 €** + infra | 47,50 € | **235 €/mois** |
| D — Paddle (théorique) | **7,93 €** (5,29 %) | 396 € | 3 965 €/mois |
| E — Chargebee Flow | — | ~220 $ | ~747 $ + PSP |

**[R] Le levier le plus rentable du dossier est le prélèvement SEPA** : 0,35 € fixe contre 1,5 % + 0,25 € en carte, soit **~1 075 €/mois d'économie à 500 clients** — davantage que le coût total du scénario Lago. Contrepartie : SEPA est **asynchrone** (échec constaté plusieurs jours après), donc pas de coupure instantanée sur impayé, et un risque de fraude supérieur à l'inscription en libre-service.
**[R]** Le scénario C n'est pas « 235 € contre 925 € » : c'est **235 € plus notre temps d'exploitation** contre 925 € clé en main.

## 6. Le minimum viable, et la règle qui rend le choix réversible

**[H]** **La vérité de l'usage reste chez nous.** Le CDR de l'opérateur est la source ; notre base porte `calls(call_id PK, customer_id, started_at, billable_seconds, metered_at NULL)`. `call_id` sert de clé d'idempotence de bout en bout : un worker prend les lignes non facturées, émet l'événement avec `identifier = call_id`, et n'écrit `metered_at` **que** sur réponse 2xx.
**[H]** **Un appel = un événement**, émis à la fin de l'appel, **valeur en secondes et non en minutes** — arrondir à la facturation, jamais à l'ingestion, sous peine de ne plus pouvoir changer la règle d'arrondi sans réémettre l'historique.
**[R]** Cette discipline rend le prestataire **remplaçable**. C'est sa vraie valeur, avant l'économie.
