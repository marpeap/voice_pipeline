# A16 — Authentification et identité, prix 2026

**Consulté le 2026-09-14.** [F] · [H] · [R] · [NV]. Hypothèse de dimensionnement [H] : **3 utilisateurs actifs par tenant et par mois** → 50 tenants = 150 MAU, 500 tenants = 1 500 MAU. Pas de SSO d'entreprise (une TPE n'a pas d'annuaire).

## Le critère qui trie tout : le prix est-il couplé au nombre de tenants ?

| Éditeur | Gratuit | Organisations natives | Au-delà | Self-host et licence |
|---|---|---|---|---|
| **ZITADEL** | **100 DAU** + **organisations illimitées, sans surcoût** | **oui, illimitées, gratuites** | Pro **100 $/mois** (25 000 DAU) | oui — **AGPL-3.0** (+ exceptions Apache/MIT) |
| **Logto** | 50 000 MAU | **add-on 48 $/mois** en cloud, **incluses en self-host** | Pro 24 $/mois | oui — **MPL-2.0**, OSS gratuit |
| **Stytch** | **10 000 MAU** + **organisations illimitées gratuites** | oui, sans frais par organisation | prix par MAU **[NV]** | [NV] |
| **WorkOS** | **1 000 000 MAU** | [NV] | 2 500 $/mois par million | [NV] |
| Clerk | 50 000 MRU + **100 organisations** | 100 incluses, ≤ 20 membres | **prix par organisation au-delà : [NV]** | [NV] |
| Supabase | 50 000 MAU | **aucune primitive** — à coder | 0,00325 $/MAU | oui, gratuit — auth **MIT** |
| SuperTokens | self-host illimité | **multi-tenancy : prix sur demande [NV]** | 0,02 $/MAU en cloud | oui — Apache 2.0 (+ `ee/` propriétaire) |
| **Auth0** | 25 000 MAU, **5 organisations** | **illimitées uniquement en ligne B2B** | **B2B 150 $/mois à 500 MAU, 700 $/mois à 2 500** | [NV] |
| Ory | 0 environnement de production | **maximum 3 organisations** sous 9 350 $/an | 0,14 $/aDAU/mois | Enterprise, tarif custom |
| Keycloak | — (pas de cloud) | realms [NV] | — | oui — **Apache 2.0** |
| authentik | OSS complet | [NV] | 5 $/utilisateur interne, **0,02 $/externe** | self-host **seul** — MIT + EE |

## Les trois pièges du panel

1. **Ory plafonne à 3 organisations** sous 9 350 $/an — disqualifiant pour « beaucoup de très petits tenants ».
2. **Auth0 réserve les organisations illimitées à sa ligne B2B** : 150 $/mois dès 500 MAU, **700 $/mois à 1 500 MAU** — soit ~23× le coût d'une solution auto-hébergée.
3. **Trois éditeurs ne publient pas le prix de la fonction dont nous avons précisément besoin** : Clerk (au-delà de 100 organisations), Stytch (au-delà de 10 000 MAU), SuperTokens (multi-tenancy). Le prix manquant est toujours celui de la fonctionnalité critique.

## Recommandation

**[R] ZITADEL auto-hébergé**, repli **Logto OSS**. Motifs : organisations **natives, illimitées et gratuites** (seul avec Stytch à ne facturer ni l'organisation ni le tenant), self-host réel, et surtout **aucun couplage du prix au nombre de tenants** — le risque central de ce modèle d'affaires.
⚠️ **Réserve** : ZITADEL est en **AGPL-3.0**. Si l'AGPL est refusée pour un SaaS, **Logto OSS (MPL-2.0, organisations incluses en self-host)** est le repli direct, et **Keycloak (Apache 2.0)** le plus permissif juridiquement, au prix d'un multi-tenant à bâtir sur les realms.

**[H] Coût** : ~0 $ de licence, le coût est l'infrastructure (~20–30 €/mois de VPS, à vérifier). Comparatifs : ZITADEL Cloud **0 $ à 50 tenants, 100 $/mois à 500** · Logto Cloud **72 $/mois** (Pro + add-on organisations) · **Auth0 B2B 700 $/mois à 500 tenants**.

**[R] Seuil de bascule honnête** : sous **10 000 MAU** (~3 300 tenants), **Stytch et WorkOS sont gratuits**. Le self-host ne se justifie donc pas par l'économie immédiate — **il se justifie par la souveraineté des données et par l'absence de dépendance à un tarif non publié.**
