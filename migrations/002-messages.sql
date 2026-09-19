-- Les messages pris quand le salon a choisi « rappeler » plutôt que
-- « transférer » (question D4 des packs).
--
-- Trois choix, et leur raison :
-- 1. Mêmes `ENABLE` **et** `FORCE` que `rendez_vous` : sans `FORCE`, la
--    politique ne s'applique pas au propriétaire de la table, et c'est
--    justement sous ce rôle que tourne une application mal configurée.
-- 2. Aucune contrainte d'unicité : deux appelants peuvent laisser le même
--    message, et les deux comptent. Dédupliquer ici perdrait un appel.
-- 3. `recu_le` porte la date d'arrivée, pas la date de traitement : le fil de
--    la console se lit du plus récent au plus ancien, et rien n'efface.

CREATE TABLE IF NOT EXISTS messages (
    reference  text PRIMARY KEY,
    tenant_id  text NOT NULL,
    recu_le    timestamptz NOT NULL DEFAULT now(),
    donnees    jsonb NOT NULL
);

CREATE INDEX IF NOT EXISTS messages_locataire ON messages (tenant_id, recu_le DESC);

-- Cloisonnement sous l'application.
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS messages_par_locataire ON messages;
CREATE POLICY messages_par_locataire ON messages
    USING (tenant_id = current_setting('app.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true));
