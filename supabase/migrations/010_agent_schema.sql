-- ============================================================================
-- Migration 010: Agent Schema (M3 Preparation)
-- Purpose: Tables for multi-agent debate system and batch processing
-- ============================================================================

-- ============================================================================
-- 1. Agent Debates
-- ============================================================================

-- Store agent debate sessions and their outcomes
CREATE TABLE IF NOT EXISTS agent_debates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Context
    debate_type TEXT NOT NULL CHECK (debate_type IN (
        'lp_match',           -- Match LP to fund
        'pitch_generation',   -- Generate pitch content
        'profile_extraction', -- Extract profile from deck
        'data_enrichment'     -- Enrich entity data
    )),

    -- Input references
    fund_id UUID REFERENCES funds(id) ON DELETE SET NULL,
    lp_org_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    target_entity_id UUID,  -- Generic entity reference
    target_entity_type TEXT,

    -- Status
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'in_progress', 'completed', 'failed', 'cancelled'
    )),

    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,

    -- Results
    consensus_reached BOOLEAN,
    final_recommendation TEXT,
    confidence_score DECIMAL(5,2),

    -- Metadata
    model_used TEXT,  -- e.g., 'claude-3-opus'
    prompt_version TEXT,  -- e.g., 'lp-match-v2.1'
    total_tokens INTEGER,
    total_cost_usd DECIMAL(10,4),

    -- Langfuse trace
    langfuse_trace_id TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_debates_org ON agent_debates(org_id);
CREATE INDEX idx_agent_debates_status ON agent_debates(status) WHERE status IN ('pending', 'in_progress');
CREATE INDEX idx_agent_debates_type ON agent_debates(debate_type, created_at DESC);

COMMENT ON TABLE agent_debates IS 'Multi-agent debate sessions for LP matching, pitch generation, etc.';


-- ============================================================================
-- 2. Agent Outputs (Individual Agent Responses)
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_outputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    debate_id UUID NOT NULL REFERENCES agent_debates(id) ON DELETE CASCADE,

    -- Agent identification
    agent_type TEXT NOT NULL CHECK (agent_type IN (
        'bull',           -- Optimistic analyst
        'bear',           -- Skeptical analyst
        'synthesizer',    -- Consensus builder
        'fact_checker',   -- Verifies claims
        'risk_assessor',  -- Evaluates risks
        'strategist'      -- Tactical recommendations
    )),
    agent_version TEXT,

    -- Execution
    sequence_number INTEGER NOT NULL,  -- Order in debate
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Output
    reasoning TEXT,  -- Agent's reasoning/thought process
    conclusion TEXT,  -- Agent's conclusion
    confidence DECIMAL(3,2),
    supporting_evidence JSONB,  -- Structured evidence
    concerns JSONB,  -- Structured concerns

    -- Tokens
    input_tokens INTEGER,
    output_tokens INTEGER,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_outputs_debate ON agent_outputs(debate_id, sequence_number);

COMMENT ON TABLE agent_outputs IS 'Individual agent responses within a debate';


-- ============================================================================
-- 3. Agent Disagreements
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_disagreements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    debate_id UUID NOT NULL REFERENCES agent_debates(id) ON DELETE CASCADE,

    -- Disagreeing agents
    agent_a_type TEXT NOT NULL,
    agent_a_output_id UUID REFERENCES agent_outputs(id),
    agent_b_type TEXT NOT NULL,
    agent_b_output_id UUID REFERENCES agent_outputs(id),

    -- Disagreement details
    topic TEXT NOT NULL,  -- What they disagree about
    agent_a_position TEXT,
    agent_b_position TEXT,

    -- Resolution
    resolution_method TEXT CHECK (resolution_method IN (
        'synthesizer', 'human_override', 'majority_vote', 'escalated', 'unresolved'
    )),
    resolved_position TEXT,
    resolution_rationale TEXT,

    -- Severity
    severity TEXT CHECK (severity IN ('minor', 'moderate', 'major', 'critical')),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_disagreements_debate ON agent_disagreements(debate_id);
CREATE INDEX idx_agent_disagreements_unresolved ON agent_disagreements(resolution_method)
    WHERE resolution_method IS NULL OR resolution_method = 'unresolved';

COMMENT ON TABLE agent_disagreements IS 'Track disagreements between agents for quality analysis';


-- ============================================================================
-- 4. Agent Escalations
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_escalations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    debate_id UUID NOT NULL REFERENCES agent_debates(id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Escalation reason
    reason TEXT NOT NULL CHECK (reason IN (
        'low_confidence',      -- Agents not confident in result
        'major_disagreement',  -- Agents strongly disagree
        'missing_data',        -- Required data not available
        'policy_violation',    -- Result may violate policy
        'user_requested',      -- User asked for human review
        'anomaly_detected'     -- Unexpected pattern in data
    )),
    description TEXT,

    -- Status
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'assigned', 'in_review', 'resolved', 'dismissed'
    )),

    -- Assignment
    assigned_to UUID REFERENCES people(id),
    assigned_at TIMESTAMPTZ,

    -- Resolution
    resolution TEXT,
    resolved_by UUID REFERENCES people(id),
    resolved_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_escalations_pending ON agent_escalations(org_id, status)
    WHERE status IN ('pending', 'assigned', 'in_review');

COMMENT ON TABLE agent_escalations IS 'Human escalations from agent debates';


-- ============================================================================
-- 5. Batch Jobs
-- ============================================================================

CREATE TABLE IF NOT EXISTS batch_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id) ON DELETE SET NULL,  -- NULL for system jobs

    -- Job definition
    job_type TEXT NOT NULL CHECK (job_type IN (
        'match_generation',    -- Generate matches for fund
        'profile_enrichment',  -- Enrich LP/GP profiles
        'data_import',         -- Import data from source
        'embedding_update',    -- Update embeddings
        'cache_refresh',       -- Refresh cached data
        'report_generation'    -- Generate reports
    )),

    -- Scope
    target_count INTEGER,  -- Expected items to process
    processed_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,

    -- Status
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'queued', 'running', 'paused', 'completed', 'failed', 'cancelled'
    )),
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),

    -- Timing
    scheduled_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Configuration
    config JSONB DEFAULT '{}',

    -- Results
    result_summary JSONB,
    error_details JSONB,

    -- Metadata
    created_by UUID REFERENCES people(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_batch_jobs_status ON batch_jobs(status, priority DESC)
    WHERE status IN ('pending', 'queued', 'running');
CREATE INDEX idx_batch_jobs_org ON batch_jobs(org_id, created_at DESC);
CREATE INDEX idx_batch_jobs_scheduled ON batch_jobs(scheduled_at)
    WHERE status = 'pending' AND scheduled_at IS NOT NULL;

COMMENT ON TABLE batch_jobs IS 'Async batch processing jobs (matching, enrichment, etc.)';


-- ============================================================================
-- 6. Entity Cache
-- ============================================================================

CREATE TABLE IF NOT EXISTS entity_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Entity reference
    entity_type TEXT NOT NULL CHECK (entity_type IN (
        'lp_profile', 'gp_profile', 'fund', 'person', 'organization'
    )),
    entity_id UUID NOT NULL,

    -- Cache type
    cache_type TEXT NOT NULL CHECK (cache_type IN (
        'embedding',        -- Vector embedding
        'enrichment',       -- Enriched data
        'analysis',         -- AI analysis result
        'match_scores',     -- Pre-computed match scores
        'summary'           -- Generated summary
    )),

    -- Cached data
    data JSONB NOT NULL,
    embedding VECTOR(1024),  -- For embedding cache type

    -- Validity
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    is_stale BOOLEAN DEFAULT FALSE,

    -- Source tracking
    source_version TEXT,  -- Version of source data when computed
    model_version TEXT,   -- Version of model used

    CONSTRAINT unique_entity_cache UNIQUE (entity_type, entity_id, cache_type)
);

CREATE INDEX idx_entity_cache_entity ON entity_cache(entity_type, entity_id);
CREATE INDEX idx_entity_cache_stale ON entity_cache(is_stale, expires_at)
    WHERE is_stale = FALSE;
CREATE INDEX idx_entity_cache_embedding ON entity_cache USING ivfflat (embedding vector_cosine_ops)
    WHERE cache_type = 'embedding';

COMMENT ON TABLE entity_cache IS 'Cache for embeddings, enrichments, and computed data';


-- ============================================================================
-- 7. RLS Policies
-- ============================================================================

-- Agent debates: org-scoped with privileged access
ALTER TABLE agent_debates ENABLE ROW LEVEL SECURITY;

CREATE POLICY "agent_debates_org_scoped" ON agent_debates
    FOR ALL USING (
        org_id = current_user_org_id()
        OR is_privileged_user()
    );

-- Agent outputs: access through debate
ALTER TABLE agent_outputs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "agent_outputs_via_debate" ON agent_outputs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM agent_debates d
            WHERE d.id = agent_outputs.debate_id
            AND (d.org_id = current_user_org_id() OR is_privileged_user())
        )
    );

-- Agent disagreements: access through debate
ALTER TABLE agent_disagreements ENABLE ROW LEVEL SECURITY;

CREATE POLICY "agent_disagreements_via_debate" ON agent_disagreements
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM agent_debates d
            WHERE d.id = agent_disagreements.debate_id
            AND (d.org_id = current_user_org_id() OR is_privileged_user())
        )
    );

-- Agent escalations: org-scoped
ALTER TABLE agent_escalations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "agent_escalations_org_scoped" ON agent_escalations
    FOR ALL USING (
        org_id = current_user_org_id()
        OR is_privileged_user()
    );

-- Batch jobs: org-scoped (NULL org = system job, FA+ only)
ALTER TABLE batch_jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "batch_jobs_org_or_system" ON batch_jobs
    FOR SELECT USING (
        org_id = current_user_org_id()
        OR (org_id IS NULL AND is_privileged_user())
        OR is_privileged_user()
    );

CREATE POLICY "batch_jobs_create_own_org" ON batch_jobs
    FOR INSERT WITH CHECK (
        org_id = current_user_org_id()
        OR (org_id IS NULL AND is_privileged_user())
    );

-- Entity cache: based on entity ownership
ALTER TABLE entity_cache ENABLE ROW LEVEL SECURITY;

CREATE POLICY "entity_cache_privileged_only" ON entity_cache
    FOR ALL USING (is_privileged_user());

-- Note: For production, entity_cache should have more granular policies
-- based on the entity_type and entity_id ownership


-- ============================================================================
-- 8. Helpful Views
-- ============================================================================

-- View: Active debates requiring attention
CREATE OR REPLACE VIEW v_active_debates AS
SELECT
    d.*,
    f.name as fund_name,
    lo.name as lp_org_name,
    COUNT(e.id) as escalation_count
FROM agent_debates d
LEFT JOIN funds f ON d.fund_id = f.id
LEFT JOIN organizations lo ON d.lp_org_id = lo.id
LEFT JOIN agent_escalations e ON e.debate_id = d.id AND e.status = 'pending'
WHERE d.status IN ('pending', 'in_progress')
GROUP BY d.id, f.name, lo.name;

-- View: Pending batch jobs
CREATE OR REPLACE VIEW v_pending_batch_jobs AS
SELECT
    b.*,
    o.name as org_name,
    p.full_name as created_by_name
FROM batch_jobs b
LEFT JOIN organizations o ON b.org_id = o.id
LEFT JOIN people p ON b.created_by = p.id
WHERE b.status IN ('pending', 'queued')
ORDER BY b.priority DESC, b.scheduled_at NULLS LAST, b.created_at;


-- ============================================================================
-- Done
-- ============================================================================

COMMENT ON SCHEMA public IS 'Migration 010: Agent schema for M3 multi-agent debates';
