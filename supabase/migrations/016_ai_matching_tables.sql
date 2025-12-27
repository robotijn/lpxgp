-- ============================================================================
-- Migration 016: Separate AI Matching Tables
--
-- Keeps original data intact for client display.
-- Creates derived tables with normalized data for AI matching only.
-- ============================================================================

--------------------------------------------------------------------------------
-- Fund AI Profile (derived from funds table)
-- Used by matching algorithm - NOT for client display
--------------------------------------------------------------------------------
CREATE TABLE fund_ai_profiles (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fund_id             UUID NOT NULL REFERENCES funds(id) ON DELETE CASCADE,

    -- Normalized strategies (canonical values for matching)
    -- Original: "Development / Minority", "Seed / early stage"
    -- Normalized: ["growth", "venture_seed"]
    strategy_tags       TEXT[] DEFAULT '{}',

    -- Normalized geography (regional buckets)
    -- Original: "france", "germany", "western_europe"
    -- Normalized: ["europe_west"]
    geography_tags      TEXT[] DEFAULT '{}',

    -- Normalized sectors
    -- Original: "Technology and software", "Healthcare"
    -- Normalized: ["tech", "healthcare"]
    sector_tags         TEXT[] DEFAULT '{}',

    -- Normalized fund size bucket
    -- Original: "Small (€100m-€500m)"
    -- Normalized: "small"
    size_bucket         TEXT CHECK (size_bucket IN ('micro', 'small', 'mid', 'large', 'mega')),

    -- Numeric size for range matching (midpoint in millions)
    size_mm             DECIMAL(12,2),

    -- Geographic scope
    -- Original: "Global", "Pan-European"
    -- Normalized: "global", "regional"
    geographic_scope    TEXT CHECK (geographic_scope IN ('global', 'regional', 'national', 'local')),

    -- Boolean flags for filtering
    has_esg             BOOLEAN DEFAULT FALSE,
    accepts_emerging    BOOLEAN DEFAULT FALSE,  -- emerging manager friendly

    -- Embeddings for semantic matching
    thesis_embedding    VECTOR(1024),

    -- Data quality
    completeness_score  DECIMAL(3,2),  -- 0.0 to 1.0
    last_synced_at      TIMESTAMPTZ DEFAULT NOW(),

    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(fund_id)
);

-- Indexes for matching queries
CREATE INDEX idx_fund_ai_strategies ON fund_ai_profiles USING GIN(strategy_tags);
CREATE INDEX idx_fund_ai_geography ON fund_ai_profiles USING GIN(geography_tags);
CREATE INDEX idx_fund_ai_sectors ON fund_ai_profiles USING GIN(sector_tags);
CREATE INDEX idx_fund_ai_size ON fund_ai_profiles(size_bucket);
CREATE INDEX idx_fund_ai_embedding ON fund_ai_profiles USING ivfflat (thesis_embedding vector_cosine_ops);

--------------------------------------------------------------------------------
-- LP AI Profile (derived from lp_profiles + behavioral data)
-- Used by matching algorithm - NOT for client display
--------------------------------------------------------------------------------
CREATE TABLE lp_ai_profiles (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lp_profile_id       UUID NOT NULL REFERENCES lp_profiles(id) ON DELETE CASCADE,
    org_id              UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Normalized strategy interests
    -- Derived from: explicit preferences OR inferred from behavior
    strategy_interests  TEXT[] DEFAULT '{}',

    -- Normalized geography interests
    -- Derived from: explicit preferences OR LP country OR behavior
    geography_interests TEXT[] DEFAULT '{}',

    -- Normalized sector interests
    sector_interests    TEXT[] DEFAULT '{}',

    -- Fund size preferences (normalized buckets)
    size_preferences    TEXT[] DEFAULT '{}',  -- ["small", "mid"]

    -- Check size range (in millions)
    check_size_min_mm   DECIMAL(12,2),
    check_size_max_mm   DECIMAL(12,2),

    -- Boolean preferences
    requires_esg        BOOLEAN DEFAULT FALSE,
    accepts_emerging    BOOLEAN DEFAULT FALSE,

    -- Behavioral signals (from solicitation data)
    acceptance_rate     DECIMAL(5,4),  -- 0.0000 to 1.0000
    engagement_score    DECIMAL(3,2),  -- 0.00 to 1.00 (composite)
    total_interactions  INTEGER DEFAULT 0,

    -- Inferred preferences (from accepted/declined patterns)
    -- JSON: {"buyout": 0.8, "venture": 0.3} = probability of interest
    inferred_strategy_probs   JSONB DEFAULT '{}',
    inferred_geography_probs  JSONB DEFAULT '{}',
    inferred_sector_probs     JSONB DEFAULT '{}',

    -- Embeddings for semantic matching
    mandate_embedding   VECTOR(1024),

    -- Data source tracking
    data_sources        TEXT[] DEFAULT '{}',  -- ["explicit", "behavioral", "inferred"]
    confidence_score    DECIMAL(3,2),  -- 0.0 to 1.0
    last_synced_at      TIMESTAMPTZ DEFAULT NOW(),

    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(lp_profile_id)
);

-- Indexes for matching queries
CREATE INDEX idx_lp_ai_strategies ON lp_ai_profiles USING GIN(strategy_interests);
CREATE INDEX idx_lp_ai_geography ON lp_ai_profiles USING GIN(geography_interests);
CREATE INDEX idx_lp_ai_sectors ON lp_ai_profiles USING GIN(sector_interests);
CREATE INDEX idx_lp_ai_sizes ON lp_ai_profiles USING GIN(size_preferences);
CREATE INDEX idx_lp_ai_engagement ON lp_ai_profiles(engagement_score DESC);
CREATE INDEX idx_lp_ai_embedding ON lp_ai_profiles USING ivfflat (mandate_embedding vector_cosine_ops);

--------------------------------------------------------------------------------
-- Match Cache (pre-computed matches for performance)
--------------------------------------------------------------------------------
CREATE TABLE match_cache (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fund_ai_id          UUID NOT NULL REFERENCES fund_ai_profiles(id) ON DELETE CASCADE,
    lp_ai_id            UUID NOT NULL REFERENCES lp_ai_profiles(id) ON DELETE CASCADE,

    -- Match scores (0.0 to 1.0)
    overall_score       DECIMAL(5,4) NOT NULL,
    strategy_score      DECIMAL(5,4),
    geography_score     DECIMAL(5,4),
    sector_score        DECIMAL(5,4),
    size_score          DECIMAL(5,4),
    semantic_score      DECIMAL(5,4),  -- embedding similarity
    behavioral_score    DECIMAL(5,4),  -- based on LP acceptance patterns

    -- Explanation for humans
    match_reasons       JSONB DEFAULT '[]',  -- ["strategy overlap: buyout", "same region"]
    concerns            JSONB DEFAULT '[]',  -- ["LP prefers larger funds"]

    -- Cache management
    computed_at         TIMESTAMPTZ DEFAULT NOW(),
    expires_at          TIMESTAMPTZ DEFAULT NOW() + INTERVAL '7 days',

    UNIQUE(fund_ai_id, lp_ai_id)
);

CREATE INDEX idx_match_cache_fund ON match_cache(fund_ai_id);
CREATE INDEX idx_match_cache_lp ON match_cache(lp_ai_id);
CREATE INDEX idx_match_cache_score ON match_cache(overall_score DESC);
CREATE INDEX idx_match_cache_expiry ON match_cache(expires_at);

--------------------------------------------------------------------------------
-- Triggers: Keep updated_at current
--------------------------------------------------------------------------------
CREATE TRIGGER update_fund_ai_profiles_updated_at
    BEFORE UPDATE ON fund_ai_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_lp_ai_profiles_updated_at
    BEFORE UPDATE ON lp_ai_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

--------------------------------------------------------------------------------
-- Comments
--------------------------------------------------------------------------------
COMMENT ON TABLE fund_ai_profiles IS 'Normalized fund data for AI matching - NOT for display';
COMMENT ON TABLE lp_ai_profiles IS 'Normalized LP data for AI matching - NOT for display';
COMMENT ON TABLE match_cache IS 'Pre-computed match scores for performance';

COMMENT ON COLUMN fund_ai_profiles.strategy_tags IS 'Canonical strategy values: buyout, growth, venture_seed, venture_growth, debt_direct, debt_mezz, infra, real_estate, etc.';
COMMENT ON COLUMN fund_ai_profiles.geography_tags IS 'Regional buckets: europe_west, europe_east, europe_north, north_america, asia_pac, latam, mena, africa, global';
COMMENT ON COLUMN fund_ai_profiles.size_bucket IS 'Normalized: micro (<100M), small (100-500M), mid (500M-2B), large (2-10B), mega (>10B)';

COMMENT ON COLUMN lp_ai_profiles.inferred_strategy_probs IS 'ML-inferred probabilities from behavioral patterns: {"buyout": 0.8, "venture": 0.3}';
COMMENT ON COLUMN lp_ai_profiles.engagement_score IS 'Composite score from acceptance_rate, recency, activity level';
COMMENT ON COLUMN lp_ai_profiles.data_sources IS 'Where preferences came from: explicit (form), behavioral (actions), inferred (ML)';
