-- Migration: 012_billing.sql
-- Description: Billing tables for subscriptions, invoices, and payment methods

-- =============================================================================
-- 1. SUBSCRIPTIONS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    plan_id TEXT NOT NULL CHECK (plan_id IN ('free', 'starter', 'professional', 'enterprise')),
    status TEXT NOT NULL CHECK (status IN ('active', 'past_due', 'cancelled', 'trialing')) DEFAULT 'active',
    billing_cycle TEXT NOT NULL CHECK (billing_cycle IN ('monthly', 'annual')) DEFAULT 'monthly',
    amount_per_period DECIMAL(10,2) NOT NULL DEFAULT 0,
    currency TEXT NOT NULL DEFAULT 'USD',
    current_period_start TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    current_period_end TIMESTAMPTZ NOT NULL,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    stripe_subscription_id TEXT UNIQUE,
    stripe_customer_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(org_id)
);

CREATE INDEX idx_subscriptions_org ON subscriptions(org_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_period_end ON subscriptions(current_period_end);
CREATE INDEX idx_subscriptions_stripe ON subscriptions(stripe_subscription_id);

COMMENT ON TABLE subscriptions IS 'Org-level subscription tracking. One subscription per org.';
COMMENT ON COLUMN subscriptions.cancel_at_period_end IS 'If TRUE, subscription will not renew.';

-- =============================================================================
-- 2. INVOICES TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    invoice_number TEXT NOT NULL UNIQUE,
    amount DECIMAL(10,2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    status TEXT NOT NULL CHECK (status IN ('draft', 'open', 'paid', 'void', 'uncollectible')) DEFAULT 'draft',
    due_date DATE NOT NULL,
    paid_at TIMESTAMPTZ,
    pdf_url TEXT,
    stripe_invoice_id TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_invoices_subscription ON invoices(subscription_id);
CREATE INDEX idx_invoices_org ON invoices(org_id);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_due ON invoices(due_date);
CREATE INDEX idx_invoices_stripe ON invoices(stripe_invoice_id);

COMMENT ON TABLE invoices IS 'Billing history for organizations. Invoices downloadable as PDF.';
COMMENT ON COLUMN invoices.invoice_number IS 'Sequential format: INV-YYYY-NNNN';
COMMENT ON COLUMN invoices.pdf_url IS 'URL to downloadable PDF invoice from Stripe.';

-- Sequence for invoice numbers
CREATE SEQUENCE IF NOT EXISTS invoice_number_seq START 1;

-- Function to generate invoice number
CREATE OR REPLACE FUNCTION generate_invoice_number()
RETURNS TEXT AS $$
BEGIN
    RETURN 'INV-' || TO_CHAR(NOW(), 'YYYY') || '-' || LPAD(nextval('invoice_number_seq')::TEXT, 4, '0');
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-generate invoice number
CREATE OR REPLACE FUNCTION set_invoice_number()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.invoice_number IS NULL THEN
        NEW.invoice_number := generate_invoice_number();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_set_invoice_number ON invoices;
CREATE TRIGGER trigger_set_invoice_number
    BEFORE INSERT ON invoices
    FOR EACH ROW
    EXECUTE FUNCTION set_invoice_number();

-- =============================================================================
-- 3. PAYMENT METHODS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS payment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('card', 'bank_account')),
    brand TEXT,  -- visa, mastercard, amex, etc.
    last_four TEXT NOT NULL,
    exp_month INTEGER CHECK (exp_month >= 1 AND exp_month <= 12),
    exp_year INTEGER CHECK (exp_year >= 2024),
    is_default BOOLEAN DEFAULT FALSE,
    stripe_payment_method_id TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_payment_methods_org ON payment_methods(org_id);
CREATE INDEX idx_payment_methods_default ON payment_methods(org_id, is_default) WHERE is_default = TRUE;

COMMENT ON TABLE payment_methods IS 'Cards on file for organizations.';
COMMENT ON COLUMN payment_methods.last_four IS 'Last 4 digits of card number for display.';

-- Ensure only one default payment method per org
CREATE OR REPLACE FUNCTION ensure_single_default_payment_method()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_default = TRUE THEN
        UPDATE payment_methods
        SET is_default = FALSE
        WHERE org_id = NEW.org_id AND id != NEW.id AND is_default = TRUE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_single_default_payment ON payment_methods;
CREATE TRIGGER trigger_single_default_payment
    BEFORE INSERT OR UPDATE ON payment_methods
    FOR EACH ROW
    WHEN (NEW.is_default = TRUE)
    EXECUTE FUNCTION ensure_single_default_payment_method();

-- =============================================================================
-- 4. BILLING CONTACT ON ORGANIZATIONS
-- =============================================================================

ALTER TABLE organizations ADD COLUMN IF NOT EXISTS billing_email TEXT;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS billing_name TEXT;

COMMENT ON COLUMN organizations.billing_email IS 'Email for billing notifications and invoices.';

-- =============================================================================
-- 5. RLS POLICIES
-- =============================================================================

-- Subscriptions: Own org can read, FA/SA can manage all
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "subscriptions_org_read" ON subscriptions
    FOR SELECT USING (
        org_id = current_user_org_id()
        OR is_privileged_user()
    );

CREATE POLICY "subscriptions_privileged_write" ON subscriptions
    FOR ALL USING (is_privileged_user());

CREATE POLICY "subscriptions_admin_update_own" ON subscriptions
    FOR UPDATE USING (
        org_id = current_user_org_id()
        AND get_user_org_role() = 'admin'
    );

-- Invoices: Own org can read, FA/SA can manage all
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;

CREATE POLICY "invoices_org_read" ON invoices
    FOR SELECT USING (
        org_id = current_user_org_id()
        OR is_privileged_user()
    );

CREATE POLICY "invoices_privileged_write" ON invoices
    FOR ALL USING (is_privileged_user());

-- Payment methods: Own org admins can manage, FA/SA can read
ALTER TABLE payment_methods ENABLE ROW LEVEL SECURITY;

CREATE POLICY "payment_methods_org_admin" ON payment_methods
    FOR ALL USING (
        org_id = current_user_org_id()
        AND get_user_org_role() = 'admin'
    );

CREATE POLICY "payment_methods_privileged_read" ON payment_methods
    FOR SELECT USING (is_privileged_user());

-- =============================================================================
-- 6. UPDATED_AT TRIGGERS
-- =============================================================================

-- Reuse existing updated_at function if exists, otherwise create
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_subscriptions_updated ON subscriptions;
CREATE TRIGGER trigger_subscriptions_updated
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_invoices_updated ON invoices;
CREATE TRIGGER trigger_invoices_updated
    BEFORE UPDATE ON invoices
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_payment_methods_updated ON payment_methods;
CREATE TRIGGER trigger_payment_methods_updated
    BEFORE UPDATE ON payment_methods
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- 7. SUBSCRIPTION STATUS TRACKING
-- =============================================================================

-- Function to check for past due subscriptions
CREATE OR REPLACE FUNCTION check_subscription_status()
RETURNS void AS $$
BEGIN
    -- Mark subscriptions as past_due if period_end has passed and not paid
    UPDATE subscriptions
    SET status = 'past_due'
    WHERE status = 'active'
    AND current_period_end < NOW();

    -- Mark subscriptions as cancelled if cancel_at_period_end and period has ended
    UPDATE subscriptions
    SET status = 'cancelled'
    WHERE cancel_at_period_end = TRUE
    AND current_period_end < NOW()
    AND status != 'cancelled';
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 8. PLAN FEATURES VIEW
-- =============================================================================

CREATE OR REPLACE VIEW subscription_plans AS
SELECT
    plan_id,
    monthly_price,
    annual_price,
    max_funds,
    max_matches_per_fund,
    features
FROM (VALUES
    ('free', 0, 0, 0, 0, ARRAY['LP search (limited)', 'Basic profile']),
    ('starter', 99, 990, 1, 50, ARRAY['LP search', 'AI matching', 'Basic pitch generation']),
    ('professional', 299, 2990, 3, -1, ARRAY['Unlimited matches', 'Full pitch generation', 'Priority support']),
    ('enterprise', 499, 4990, -1, -1, ARRAY['Unlimited everything', 'API access', 'Dedicated support', 'Custom integrations'])
) AS plans(plan_id, monthly_price, annual_price, max_funds, max_matches_per_fund, features);

COMMENT ON VIEW subscription_plans IS 'Read-only view of available subscription plans and their features.';

-- =============================================================================
-- GRANTS
-- =============================================================================

GRANT SELECT ON subscriptions TO authenticated;
GRANT SELECT ON invoices TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON payment_methods TO authenticated;
GRANT SELECT ON subscription_plans TO authenticated;

-- Service role has full access
GRANT ALL ON subscriptions TO service_role;
GRANT ALL ON invoices TO service_role;
GRANT ALL ON payment_methods TO service_role;
