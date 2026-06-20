-- Migration: Add workflow engine enhancements
-- Execute inside PostgreSQL container: docker exec -i <db_container> psql -U postgres -d qms < migrations/versions/add_workflow_enhancements.sql

-- 1. WorkflowEtape: add SLA column
ALTER TABLE workflow_etape ADD COLUMN IF NOT EXISTS delai_jours INTEGER;

-- 2. WorkflowInstance: add demandeur, deadline, commentaire, indexes
ALTER TABLE workflow_instance ADD COLUMN IF NOT EXISTS demandeur_id INTEGER REFERENCES utilisateur(id);
ALTER TABLE workflow_instance ADD COLUMN IF NOT EXISTS date_deadline TIMESTAMP;
ALTER TABLE workflow_instance ADD COLUMN IF NOT EXISTS commentaire TEXT;

-- 3. Indexes for performance
CREATE INDEX IF NOT EXISTS idx_wf_entity ON workflow_instance(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_wf_statut ON workflow_instance(entreprise_id, statut);
