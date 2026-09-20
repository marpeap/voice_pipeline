-- Les réponses du commerçant au questionnaire (docs/05).
--
-- Une ligne par locataire, et la mise à jour est une **fusion** : un écran qui
-- ne porte qu'un bloc de questions ne doit pas effacer les réponses des autres.
-- C'est la même règle que pour la mémoire — on ne réécrit jamais ce que le
-- commerçant a déjà dit.

CREATE TABLE IF NOT EXISTS reponses (
    tenant_id  text PRIMARY KEY,
    donnees    jsonb NOT NULL,
    modifie_le timestamptz NOT NULL DEFAULT now()
);

-- Cloisonnement sous l'application.
ALTER TABLE reponses ENABLE ROW LEVEL SECURITY;
ALTER TABLE reponses FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS reponses_par_locataire ON reponses;
CREATE POLICY reponses_par_locataire ON reponses
    USING (tenant_id = current_setting('app.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true));
