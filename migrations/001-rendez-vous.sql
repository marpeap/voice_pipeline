-- Rendez-vous multi-locataire — PostgreSQL.
--
-- Trois regles, et chacune existe parce que son absence coute cher.
--
-- 1. `ENABLE` **et** `FORCE`. Sans `FORCE`, la politique ne s'applique pas au
--    proprietaire de la table — c'est-a-dire souvent au role qui fait tourner
--    l'API. On croit alors etre cloisonne, et on ne l'est pas.
-- 2. Le locataire vient d'un reglage de session pose DANS la transaction
--    (`set_config('app.tenant_id', ..., true)`), jamais d'un parametre de requete
--    qu'on peut oublier.
-- 3. Le chevauchement est interdit PAR LA BASE. Une verification applicative
--    s'oublie, se contourne, et perd la course entre deux appels simultanes.

CREATE TABLE IF NOT EXISTS rendez_vous (
    reference        text PRIMARY KEY,
    tenant_id        text NOT NULL,
    cle_idempotence  text NOT NULL,
    debut            timestamptz NOT NULL,
    fin              timestamptz NOT NULL,
    annule           boolean NOT NULL DEFAULT false,
    donnees          jsonb NOT NULL,
    cree_le          timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT rendez_vous_duree CHECK (fin > debut)
);

-- Une cle d'idempotence appartient a un locataire.
CREATE UNIQUE INDEX IF NOT EXISTS rendez_vous_cle
    ON rendez_vous (tenant_id, cle_idempotence);

-- Aucun chevauchement chez un meme locataire, les annules ne comptant pas.
CREATE EXTENSION IF NOT EXISTS btree_gist;
ALTER TABLE rendez_vous DROP CONSTRAINT IF EXISTS rendez_vous_sans_chevauchement;
ALTER TABLE rendez_vous ADD CONSTRAINT rendez_vous_sans_chevauchement
    EXCLUDE USING gist (
        tenant_id WITH =,
        tstzrange(debut, fin) WITH &&
    ) WHERE (NOT annule);

-- Cloisonnement sous l'application.
ALTER TABLE rendez_vous ENABLE ROW LEVEL SECURITY;
ALTER TABLE rendez_vous FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS rendez_vous_par_locataire ON rendez_vous;
CREATE POLICY rendez_vous_par_locataire ON rendez_vous
    USING (tenant_id = current_setting('app.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true));
