-- LPxGP Business Logic Constraints
-- Addresses Blue Team findings: data integrity, self-match prevention

--------------------------------------------------------------------------------
-- Self-Match Prevention
-- A GP organization cannot match their own LP (if they are both GP and LP)
--------------------------------------------------------------------------------

-- Add constraint to fund_lp_matches
ALTER TABLE fund_lp_matches
DROP CONSTRAINT IF EXISTS no_self_match;

ALTER TABLE fund_lp_matches
ADD CONSTRAINT no_self_match
CHECK (
    -- Fund's org_id must not equal the LP's org_id
    fund_id IS NULL OR lp_org_id IS NULL OR
    (SELECT org_id FROM funds WHERE id = fund_id) != lp_org_id
);

-- Alternative: Use a trigger for more complex validation
CREATE OR REPLACE FUNCTION check_no_self_match()
RETURNS TRIGGER AS $$
DECLARE
    fund_org_id UUID;
BEGIN
    SELECT org_id INTO fund_org_id FROM funds WHERE id = NEW.fund_id;

    IF fund_org_id = NEW.lp_org_id THEN
        RAISE EXCEPTION 'Cannot match fund to own LP organization (self-match prevention)';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_no_self_match ON fund_lp_matches;
CREATE TRIGGER trg_no_self_match
    BEFORE INSERT OR UPDATE ON fund_lp_matches
    FOR EACH ROW
    EXECUTE FUNCTION check_no_self_match();

--------------------------------------------------------------------------------
-- Fund Name Uniqueness Per Organization
--------------------------------------------------------------------------------

ALTER TABLE funds
DROP CONSTRAINT IF EXISTS unique_fund_name_per_org;

ALTER TABLE funds
ADD CONSTRAINT unique_fund_name_per_org
UNIQUE (org_id, name);

--------------------------------------------------------------------------------
-- Non-Negative Financial Amounts
--------------------------------------------------------------------------------

ALTER TABLE funds
DROP CONSTRAINT IF EXISTS non_negative_target_size;
ALTER TABLE funds
ADD CONSTRAINT non_negative_target_size
CHECK (target_size_mm IS NULL OR target_size_mm >= 0);

ALTER TABLE funds
DROP CONSTRAINT IF EXISTS non_negative_hard_cap;
ALTER TABLE funds
ADD CONSTRAINT non_negative_hard_cap
CHECK (hard_cap_mm IS NULL OR hard_cap_mm >= 0);

-- Add comments for units
COMMENT ON COLUMN funds.target_size_mm IS 'Target fund size in millions USD';
COMMENT ON COLUMN funds.hard_cap_mm IS 'Hard cap in millions USD';

--------------------------------------------------------------------------------
-- LP Profile Financial Constraints
--------------------------------------------------------------------------------

-- Check size constraints
ALTER TABLE lp_profiles
DROP CONSTRAINT IF EXISTS non_negative_total_aum;
ALTER TABLE lp_profiles
ADD CONSTRAINT non_negative_total_aum
CHECK (total_aum_bn IS NULL OR total_aum_bn >= 0);

ALTER TABLE lp_profiles
DROP CONSTRAINT IF EXISTS non_negative_pe_allocation;
ALTER TABLE lp_profiles
ADD CONSTRAINT non_negative_pe_allocation
CHECK (pe_allocation_bn IS NULL OR pe_allocation_bn >= 0);

-- Percentage constraints (0-100)
ALTER TABLE lp_profiles
DROP CONSTRAINT IF EXISTS valid_pe_target_pct;
ALTER TABLE lp_profiles
ADD CONSTRAINT valid_pe_target_pct
CHECK (pe_target_pct IS NULL OR (pe_target_pct >= 0 AND pe_target_pct <= 100));

--------------------------------------------------------------------------------
-- Investment Amount Constraints
--------------------------------------------------------------------------------

ALTER TABLE investments
DROP CONSTRAINT IF EXISTS non_negative_amount;
ALTER TABLE investments
ADD CONSTRAINT non_negative_amount
CHECK (amount_mm IS NULL OR amount_mm >= 0);

--------------------------------------------------------------------------------
-- Valid Check Size Range
--------------------------------------------------------------------------------

-- Ensure min <= max for check sizes
ALTER TABLE lp_profiles
DROP CONSTRAINT IF EXISTS valid_check_size_range;
ALTER TABLE lp_profiles
ADD CONSTRAINT valid_check_size_range
CHECK (
    check_size_min_mm IS NULL OR
    check_size_max_mm IS NULL OR
    check_size_min_mm <= check_size_max_mm
);

--------------------------------------------------------------------------------
-- Pipeline Stage State Machine
-- Document valid state transitions
--------------------------------------------------------------------------------

COMMENT ON COLUMN fund_lp_status.pipeline_stage IS '
Valid states and transitions:
- recommended: Initial AI recommendation
  -> gp_interested, gp_passed
- gp_interested: GP wants to pursue
  -> gp_pursuing, gp_passed
- gp_pursuing: Active outreach
  -> lp_reviewing, gp_passed
- lp_reviewing: LP is evaluating
  -> mutual_interest, lp_passed
- mutual_interest: Both parties engaged
  -> in_diligence, lp_passed, gp_passed
- in_diligence: Due diligence phase
  -> invested, lp_passed, gp_passed
- invested: Commitment made (terminal)
- gp_passed: GP declined (terminal)
- lp_passed: LP declined (terminal)
';

-- Add constraint for valid stages
ALTER TABLE fund_lp_status
DROP CONSTRAINT IF EXISTS valid_pipeline_stage;
ALTER TABLE fund_lp_status
ADD CONSTRAINT valid_pipeline_stage
CHECK (pipeline_stage IN (
    'recommended',
    'gp_interested',
    'gp_pursuing',
    'lp_reviewing',
    'mutual_interest',
    'in_diligence',
    'invested',
    'gp_passed',
    'lp_passed'
));

--------------------------------------------------------------------------------
-- Score Range Constraints
--------------------------------------------------------------------------------

-- Match scores should be 0-100
ALTER TABLE fund_lp_matches
DROP CONSTRAINT IF EXISTS valid_overall_score;
ALTER TABLE fund_lp_matches
ADD CONSTRAINT valid_overall_score
CHECK (overall_score IS NULL OR (overall_score >= 0 AND overall_score <= 100));

ALTER TABLE fund_lp_matches
DROP CONSTRAINT IF EXISTS valid_strategy_score;
ALTER TABLE fund_lp_matches
ADD CONSTRAINT valid_strategy_score
CHECK (strategy_score IS NULL OR (strategy_score >= 0 AND strategy_score <= 100));

ALTER TABLE fund_lp_matches
DROP CONSTRAINT IF EXISTS valid_geography_score;
ALTER TABLE fund_lp_matches
ADD CONSTRAINT valid_geography_score
CHECK (geography_score IS NULL OR (geography_score >= 0 AND geography_score <= 100));

ALTER TABLE fund_lp_matches
DROP CONSTRAINT IF EXISTS valid_size_score;
ALTER TABLE fund_lp_matches
ADD CONSTRAINT valid_size_score
CHECK (size_score IS NULL OR (size_score >= 0 AND size_score <= 100));

--------------------------------------------------------------------------------
-- Email Format Validation (basic)
--------------------------------------------------------------------------------

-- People email must contain @
ALTER TABLE people
DROP CONSTRAINT IF EXISTS valid_email_format;
ALTER TABLE people
ADD CONSTRAINT valid_email_format
CHECK (email IS NULL OR email LIKE '%@%.%');

-- Invitations email must contain @
ALTER TABLE invitations
DROP CONSTRAINT IF EXISTS valid_invitation_email;
ALTER TABLE invitations
ADD CONSTRAINT valid_invitation_email
CHECK (email LIKE '%@%.%');

--------------------------------------------------------------------------------
-- Prevent Duplicate Pending Invitations
--------------------------------------------------------------------------------

CREATE UNIQUE INDEX IF NOT EXISTS idx_one_pending_invitation_per_email
ON invitations (email)
WHERE status = 'pending';

--------------------------------------------------------------------------------
-- Fund Team Allocation Percentage
--------------------------------------------------------------------------------

COMMENT ON COLUMN fund_team.allocation_pct IS 'Team member allocation percentage (0-100)';

ALTER TABLE fund_team
DROP CONSTRAINT IF EXISTS valid_allocation_pct;
ALTER TABLE fund_team
ADD CONSTRAINT valid_allocation_pct
CHECK (allocation_pct IS NULL OR (allocation_pct >= 0 AND allocation_pct <= 100));

--------------------------------------------------------------------------------
-- Summary of Constraints Added
--------------------------------------------------------------------------------

/*
Business Rules Enforced:
1. no_self_match - GP cannot match their own LP org
2. unique_fund_name_per_org - No duplicate fund names within org
3. non_negative_* - Financial amounts must be >= 0
4. valid_*_pct - Percentages must be 0-100
5. valid_check_size_range - Min <= Max for check sizes
6. valid_pipeline_stage - Only allowed stage values
7. valid_*_score - Match scores must be 0-100
8. valid_email_format - Basic email validation
9. idx_one_pending_invitation_per_email - One pending invite per email
*/
