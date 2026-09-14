# A15 — Multi-tenant, secrets par tenant, outils de support

**Consulté le 2026-09-14.** [F] · [H] · [R] · [NV].

## 1. Le modèle d'isolation : pool, jamais une base par TPE

**[F] PostgreSQL `max_connections`** : défaut **100**, réglable **uniquement au démarrage**, et « PostgreSQL sizes certain resources based directly on the value of max_connections ». **[R] C'est l'argument qui tue le « une base par tenant »** : 500 TPE = 500 pools se disputant un plafond commun. Avec `tenant_id` partagé, un seul pool sert tout le monde.

**[F] Azure** : le mono-tenant multiplie le coût par le nombre de clients (« 100 tenants probably require 100 times that cost ») ; la base partagée « tends to come at the **lowest financial cost** of any approach ». Et l'isolation **par table** est classée **antipattern** : « Instead, consider using a single set of multitenant tables with a tenant identifier column ».
**[F] AWS SaaS Lens** : silo / pool / **bridge**. Le franchissement d'une frontière de tenant est « a **significant and potentially unrecoverable event** ».

**[R] Modèle retenu : bridge.** Données et application en **pool** ; en **silo logique** ce qui est réglementé ou explosif — secrets par tenant, enregistrements et transcriptions, numérotation.

**[F] RLS, les pièges documentés** : `BYPASSRLS` et superuser passent **toujours** outre · le propriétaire de table aussi, sauf `FORCE ROW LEVEL SECURITY` · **les contraintes d'intégrité référentielle contournent toujours RLS** → canal caché (un INSERT rejeté pour doublon révèle l'existence d'une ligne d'un autre tenant) · les fonctions `leakproof` peuvent être évaluées **avant** le contrôle · une sauvegarde peut **omettre des lignes en silence** → utiliser `row_security = off` pour qu'elle **échoue** plutôt qu'elle filtre.
**[F] Azure prévient** : « **Many multitenant solutions don't use row-level security because of those complexities.** »

**[R] Discipline qui rend RLS utile sans être un piège** : filtre `tenant_id` **explicite dans le code** (RLS est le filet, pas la première barrière) · rôle applicatif **non propriétaire et sans `BYPASSRLS`**, `FORCE` sur chaque table · `SET LOCAL` dans la transaction (une variable de session qui survit à la transaction est une fuite inter-tenant en pooling) · **toutes les clés uniques et étrangères préfixées par `tenant_id`** — parade directe au canal caché · tests d'isolation automatisés qui **doivent** échouer.

**[F] La faiblesse assumée du pool** : restaurer un seul tenant « might require you to restore the database to a separate resource and selectively recover that tenant's data ». **[R]** À traiter par conception : PITR + procédure de restauration **écrite et testée**, suppression logique et export par tenant en libre-service (couvre 90 % des demandes réelles), offboarding automatisé.

**[R] À trancher maintenant** : le tenant est-il **l'entreprise** ou **l'établissement** ? Une TPE à deux salons, un gérant, deux numéros — le choix conditionne la facturation et rend la migration ultérieure très coûteuse.

## 2. Secrets par tenant : une clé KMS, pas cinq cents

**[F] Prix AWS KMS** : **1 $/mois par clé gérée par le client** · rotation **+1 $ pour la 1re, +1 $ pour la 2e**, plafonné (**3 $/mois max**) · requêtes symétriques **0,03 $ / 10 000** · **palier gratuit 20 000 requêtes/mois**.

**[H] Calcul à 500 tenants** (2 secrets/tenant, ~20 déchiffrements/tenant/jour) :

| Option | 1re année | Régime établi |
|---|---|---|
| **Clé unique + contexte de chiffrement** | ~**1,84 $/mois** | ~**3,84 $/mois** (≈ 3 $ avec cache des data keys) |
| Une clé par tenant | **500,84 $/mois** | **1 500,84 $/mois** |

**Écart ×130 à ×390.** Sur un an en régime établi : 46 $ contre 18 010 $.

**[R] Architecture** : **enveloppe** — une clé KMS par environnement, une *data key* par tenant stockée chiffrée, le secret chiffré localement en AES-GCM. Le chemin chaud ne rappelle KMS qu'en cas d'absence de cache, ce qui garde la latence **hors du chemin de l'appel téléphonique**. **Contexte de chiffrement `{tenant_id, purpose}` sur chaque opération** : un ciphertext volé au tenant A ne se déchiffre pas au nom du tenant B, et un bug de requête produit une **erreur**, pas une fuite silencieuse.
⚠️ **[NV]** La citation exacte de la doc KMS sur l'*encryption context* n'a pas pu être lue (section non rendue). **Mécanisme à revérifier avant implémentation — tout l'édifice repose dessus.**

**[F] Ce que la rotation KMS ne fait pas** : « Key rotation has no effect on the data that the KMS key protects… **Key rotation will not mitigate the effect of a compromised data key.** » **[R]** La rotation qui compte est celle des **data keys par tenant**, avec rechiffrement — et immédiatement en cas d'incident.

**[F] Vault Transit**, supérieur sur deux points : **dérivation de clé par contexte** et surtout **`rewrap`** (« Re-encrypts data with current key version **without exposing plaintext** ») — l'opération que KMS ne sait pas faire. Prix : un Vault de plus à exploiter. **[R] KMS par défaut ; Transit si la souveraineté ou le multi-cloud entre en jeu.**

**[R] À prévoir dès le schéma** : une colonne `kms_key_arn` **nullable** par tenant — `NULL` = clé partagée. Coût nul aujourd'hui, migration évitée le jour où un client exigera sa propre clé (et **la paiera**).

## 3. Outils de support

**[F] Chatwoot, licence duale — le README est trompeur** : il annonce « MIT » tout court, mais le fichier `LICENSE` renvoie le répertoire `enterprise/` à `enterprise/LICENSE`, qui est une **licence commerciale propriétaire** (« it is forbidden to copy, merge, publish, distribute, sublicense, and/or sell the Software », production autorisée uniquement avec « a valid Chatwoot Enterprise License for the correct number of user seats »).
**[R] Auto-héberger Chatwoot est légal et gratuit si et seulement si le répertoire `enterprise/` est supprimé ou inactif.**

**[F] Prix** : Crisp **au workspace** (45 $ Mini / 95 $ Essentials / 295 $ Plus, sièges additionnels 10 $) — le seul du panel · Chatwoot cloud **19–99 $/agent/mois** · Intercom **29–132 $/siège** + **Fin à « from 0,99 $ par outcome »** · Plain 35 $/siège.
**[R]** À 2–4 opérateurs, **Crisp au workspace bat structurellement le prix au siège**. Son vrai plafond n'est pas le siège mais les **profils clients** (5 000 en Mini). Alternative à coût de licence nul : **Chatwoot sans `enterprise/`**, au prix de l'exploitation.

**[NV] Volume de tickets par client** : aucun benchmark trouvé (zendesk.com/benchmark ne contient pas la donnée, intercom.com/customer-service-trends en 404). **[R] Ne pas dimensionner sur une hypothèse : instrumenter les 30 premiers clients pendant 60 jours.**
