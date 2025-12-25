-- LPxGP Seed Data for Development
-- Run with: npx supabase db reset (includes seed) or psql directly

-- =============================================================================
-- 1. ORGANIZATIONS (GPs and LPs)
-- =============================================================================

-- GP Organizations
INSERT INTO organizations (id, name, website, hq_city, hq_country, description, is_gp, is_lp) VALUES
('11111111-1111-1111-1111-111111111111', 'Summit Ventures', 'https://summitvc.com', 'San Francisco', 'USA', 'Early-stage tech investor focused on B2B SaaS', true, false),
('22222222-2222-2222-2222-222222222222', 'Alpine Growth Partners', 'https://alpinegrowth.com', 'New York', 'USA', 'Growth equity firm specializing in fintech', true, false),
('33333333-3333-3333-3333-333333333333', 'Nordic Capital Partners', 'https://nordiccap.eu', 'Stockholm', 'Sweden', 'Pan-European buyout fund', true, false);

-- LP Organizations
INSERT INTO organizations (id, name, website, hq_city, hq_country, description, is_gp, is_lp) VALUES
('aaaa1111-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'CalPERS', 'https://calpers.ca.gov', 'Sacramento', 'USA', 'California Public Employees Retirement System', false, true),
('aaaa2222-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Harvard Management Company', 'https://hmc.harvard.edu', 'Boston', 'USA', 'Manages Harvard University endowment', false, true),
('aaaa3333-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Ontario Teachers Pension Plan', 'https://otpp.com', 'Toronto', 'Canada', 'Canadian pension fund', false, true),
('aaaa4444-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Abu Dhabi Investment Authority', 'https://adia.ae', 'Abu Dhabi', 'UAE', 'Sovereign wealth fund', false, true),
('aaaa5555-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Sequoia Heritage', 'https://sequoiaheritage.com', 'Menlo Park', 'USA', 'Family office and wealth management', false, true),
('aaaa6666-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Future Fund', 'https://futurefund.gov.au', 'Melbourne', 'Australia', 'Australian sovereign wealth fund', false, true),
('aaaa7777-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'GIC Private Limited', 'https://gic.com.sg', 'Singapore', 'Singapore', 'Singapore sovereign wealth fund', false, true),
('aaaa8888-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Wellcome Trust', 'https://wellcome.org', 'London', 'UK', 'Global charitable foundation', false, true);

-- Dual GP/LP (fund of funds style)
INSERT INTO organizations (id, name, website, hq_city, hq_country, description, is_gp, is_lp) VALUES
('bbbb1111-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'Pantheon Ventures', 'https://pantheon.com', 'London', 'UK', 'Private equity fund of funds', true, true);

-- =============================================================================
-- 2. GP PROFILES
-- =============================================================================

INSERT INTO gp_profiles (org_id, investment_philosophy, team_size, years_investing, notable_exits) VALUES
('11111111-1111-1111-1111-111111111111', 'We partner with technical founders building category-defining B2B software companies. Our sweet spot is $2-10M Series A rounds.', 12, 15, '[{"company": "DataDog", "return": "45x"}, {"company": "Snowflake", "return": "32x"}]'),
('22222222-2222-2222-2222-222222222222', 'Growth equity investing in proven fintech business models. We lead $20-50M rounds in companies with $10M+ ARR.', 25, 12, '[{"company": "Stripe", "return": "28x"}, {"company": "Plaid", "return": "18x"}]'),
('33333333-3333-3333-3333-333333333333', 'European buyout specialist focusing on industrial technology and healthcare services.', 45, 22, '[{"company": "Assa Abloy", "return": "8x"}, {"company": "Mölnlycke", "return": "5x"}]');

-- =============================================================================
-- 3. LP PROFILES
-- =============================================================================

INSERT INTO lp_profiles (org_id, lp_type, total_aum_bn, pe_allocation_pct, strategies, geographic_preferences, sector_preferences, check_size_min_mm, check_size_max_mm, fund_size_min_mm, fund_size_max_mm, esg_required, emerging_manager_ok, mandate_description) VALUES
('aaaa1111-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'pension', 450.0, 12.0, ARRAY['buyout', 'growth', 'venture'], ARRAY['North America', 'Europe'], ARRAY['technology', 'healthcare'], 50, 500, 500, 10000, true, false, 'Seeking diversified PE exposure with focus on top-quartile managers. Minimum 3 fund track record required.'),
('aaaa2222-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'endowment', 50.0, 18.0, ARRAY['venture', 'growth'], ARRAY['North America', 'Asia'], ARRAY['technology', 'life_sciences'], 25, 200, 250, 5000, true, true, 'Innovation-focused portfolio. Willing to back emerging managers with differentiated strategies.'),
('aaaa3333-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'pension', 250.0, 15.0, ARRAY['buyout', 'infrastructure'], ARRAY['North America', 'Europe'], ARRAY['infrastructure', 'real_assets'], 100, 750, 1000, 15000, true, false, 'Long-duration assets preferred. Strong ESG requirements.'),
('aaaa4444-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'sovereign_wealth', 900.0, 8.0, ARRAY['buyout', 'growth', 'venture'], ARRAY['Global'], ARRAY['technology', 'financial_services', 'consumer'], 200, 2000, 2000, 25000, false, false, 'Global mandate seeking co-investment opportunities alongside fund commitments.'),
('aaaa5555-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'family_office', 15.0, 35.0, ARRAY['venture', 'growth'], ARRAY['North America'], ARRAY['technology', 'fintech'], 10, 50, 100, 1000, false, true, 'Tech-focused family office. Strong network in Silicon Valley. Prefer funds with co-invest rights.'),
('aaaa6666-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'sovereign_wealth', 200.0, 10.0, ARRAY['buyout', 'growth'], ARRAY['Asia Pacific', 'North America'], ARRAY['technology', 'healthcare'], 75, 400, 500, 8000, true, false, 'Asia-Pacific focus with selective global exposure.'),
('aaaa7777-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'sovereign_wealth', 750.0, 11.0, ARRAY['buyout', 'growth', 'venture', 'infrastructure'], ARRAY['Global'], ARRAY['technology', 'real_estate', 'infrastructure'], 150, 1500, 1000, 20000, false, false, 'Diversified global portfolio. Significant direct and co-investment capability.'),
('aaaa8888-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'foundation', 35.0, 20.0, ARRAY['venture', 'growth'], ARRAY['North America', 'Europe', 'Asia'], ARRAY['life_sciences', 'healthcare'], 20, 100, 200, 2000, true, true, 'Healthcare and life sciences focus aligned with charitable mission.');

-- =============================================================================
-- 4. PEOPLE
-- =============================================================================

-- GP Team Members
INSERT INTO people (id, full_name, email, linkedin_url, bio, is_decision_maker, role) VALUES
('c0111111-1111-1111-1111-111111111111', 'Sarah Chen', 'sarah@summitvc.com', 'https://linkedin.com/in/sarahchen', 'Founding Partner at Summit Ventures. Former Product at Google.', true, 'admin'),
('c0222222-2222-2222-2222-222222222222', 'Michael Torres', 'michael@summitvc.com', 'https://linkedin.com/in/michaeltorres', 'Partner focusing on enterprise software.', true, 'member'),
('c0333333-3333-3333-3333-333333333333', 'James Morrison', 'james@alpinegrowth.com', 'https://linkedin.com/in/jamesmorrison', 'Managing Partner at Alpine Growth. 20 years in fintech investing.', true, 'admin'),
('c0444444-4444-4444-4444-444444444444', 'Emma Lindqvist', 'emma@nordiccap.eu', 'https://linkedin.com/in/emmalindqvist', 'Partner leading healthcare investments at Nordic Capital.', true, 'admin');

-- LP Contacts
INSERT INTO people (id, full_name, email, linkedin_url, bio, is_decision_maker, role) VALUES
('c0555555-5555-5555-5555-555555555555', 'David Kim', 'dkim@calpers.ca.gov', 'https://linkedin.com/in/davidkim', 'Senior Portfolio Manager, Private Equity at CalPERS.', true, 'member'),
('c0666666-6666-6666-6666-666666666666', 'Jennifer Walsh', 'jwalsh@hmc.harvard.edu', 'https://linkedin.com/in/jenniferwalsh', 'Managing Director, Private Investments at HMC.', true, 'member'),
('c0777777-7777-7777-7777-777777777777', 'Robert Chang', 'rchang@otpp.com', 'https://linkedin.com/in/robertchang', 'VP Private Equity at Ontario Teachers.', true, 'member'),
('c0888888-8888-8888-8888-888888888888', 'Ahmed Al-Rashid', 'alrashid@adia.ae', 'https://linkedin.com/in/ahmedalrashid', 'Director, Private Equity at ADIA.', true, 'member');

-- =============================================================================
-- 5. EMPLOYMENT
-- =============================================================================

INSERT INTO employment (person_id, org_id, title, is_current) VALUES
('c0111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', 'Founding Partner', true),
('c0222222-2222-2222-2222-222222222222', '11111111-1111-1111-1111-111111111111', 'Partner', true),
('c0333333-3333-3333-3333-333333333333', '22222222-2222-2222-2222-222222222222', 'Managing Partner', true),
('c0444444-4444-4444-4444-444444444444', '33333333-3333-3333-3333-333333333333', 'Partner', true),
('c0555555-5555-5555-5555-555555555555', 'aaaa1111-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Senior Portfolio Manager', true),
('c0666666-6666-6666-6666-666666666666', 'aaaa2222-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Managing Director', true),
('c0777777-7777-7777-7777-777777777777', 'aaaa3333-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'VP Private Equity', true),
('c0888888-8888-8888-8888-888888888888', 'aaaa4444-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Director', true);

-- =============================================================================
-- 6. FUNDS
-- =============================================================================

INSERT INTO funds (id, org_id, created_by, name, fund_number, status, vintage_year, target_size_mm, current_size_mm, hard_cap_mm, strategy, sub_strategy, geographic_focus, sector_focus, check_size_min_mm, check_size_max_mm, investment_thesis) VALUES
('0f111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', 'c0111111-1111-1111-1111-111111111111', 'Summit Ventures Fund IV', 4, 'raising', 2024, 350, 175, 400, 'venture', 'Series A', ARRAY['North America'], ARRAY['enterprise_software', 'developer_tools'], 5, 15, 'We invest in technical founders building the next generation of enterprise infrastructure. Our focus is on companies with strong product-market fit and $1-5M ARR seeking Series A funding.'),
('0f222222-2222-2222-2222-222222222222', '11111111-1111-1111-1111-111111111111', 'c0111111-1111-1111-1111-111111111111', 'Summit Ventures Fund III', 3, 'invested', 2021, 250, 250, 275, 'venture', 'Series A', ARRAY['North America'], ARRAY['enterprise_software', 'fintech'], 3, 12, 'Enterprise software focus with proven track record.'),
('0f333333-3333-3333-3333-333333333333', '22222222-2222-2222-2222-222222222222', 'c0333333-3333-3333-3333-333333333333', 'Alpine Growth Fund II', 2, 'raising', 2024, 800, 450, 1000, 'growth', 'Growth Equity', ARRAY['North America', 'Europe'], ARRAY['fintech', 'payments'], 25, 75, 'Growth equity investments in fintech companies with $10M+ ARR and clear path to profitability.'),
('0f444444-4444-4444-4444-444444444444', '33333333-3333-3333-3333-333333333333', 'c0444444-4444-4444-4444-444444444444', 'Nordic Capital Fund XI', 11, 'raising', 2024, 5000, 3200, 6000, 'buyout', 'Mid-Market Buyout', ARRAY['Europe'], ARRAY['healthcare', 'technology', 'financial_services'], 200, 750, 'European mid-market buyouts with focus on healthcare services, technology-enabled businesses, and financial services.');

-- =============================================================================
-- 7. FUND TEAM
-- =============================================================================

INSERT INTO fund_team (fund_id, person_id, role, is_key_person, allocation_pct) VALUES
('0f111111-1111-1111-1111-111111111111', 'c0111111-1111-1111-1111-111111111111', 'Lead Partner', true, 60),
('0f111111-1111-1111-1111-111111111111', 'c0222222-2222-2222-2222-222222222222', 'Partner', true, 40),
('0f333333-3333-3333-3333-333333333333', 'c0333333-3333-3333-3333-333333333333', 'Managing Partner', true, 100),
('0f444444-4444-4444-4444-444444444444', 'c0444444-4444-4444-4444-444444444444', 'Partner', true, 50);

-- =============================================================================
-- 8. FUND-LP MATCHES (AI-generated recommendations)
-- =============================================================================

INSERT INTO fund_lp_matches (id, fund_id, lp_org_id, score, score_breakdown, explanation, talking_points, concerns) VALUES
('0a111111-1111-1111-1111-111111111111', '0f111111-1111-1111-1111-111111111111', 'aaaa2222-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 92.5, '{"strategy": 95, "size": 88, "geography": 95, "track_record": 90}', 'Excellent fit: HMC actively backs emerging venture managers and has strong appetite for enterprise software. Fund size within their sweet spot.', ARRAY['Harvard has backed 3 similar funds in past 2 years', 'Strong overlap with their tech thesis', 'Co-invest appetite aligns with our model'], ARRAY['May want to see more diversity in portfolio', 'Fund IV larger than Fund III - justify scaling']),
('0a222222-2222-2222-2222-222222222222', '0f111111-1111-1111-1111-111111111111', 'aaaa5555-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 88.0, '{"strategy": 92, "size": 95, "geography": 90, "track_record": 85}', 'Strong fit: Sequoia Heritage actively deploys to top-tier venture funds. Our size and strategy align well with their mandate.', ARRAY['Family office with strong Valley network', 'Values co-investment rights we offer', 'Quick decision-making process'], ARRAY['Smaller check size may not move the needle for them', 'Competitive - likely seeing many funds']),
('0a333333-3333-3333-3333-333333333333', '0f111111-1111-1111-1111-111111111111', 'aaaa1111-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 65.0, '{"strategy": 80, "size": 45, "geography": 90, "track_record": 70}', 'Moderate fit: CalPERS invests in venture but typically larger funds. May be below their minimum check size threshold.', ARRAY['Large allocation to PE overall', 'Recently increased venture exposure', 'ESG focus aligns with our practices'], ARRAY['Fund likely too small for their program', 'Prefer established managers with 5+ funds', 'Long due diligence process']),
('0a444444-4444-4444-4444-444444444444', '0f333333-3333-3333-3333-333333333333', 'aaaa1111-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 95.0, '{"strategy": 95, "size": 98, "geography": 95, "track_record": 92}', 'Excellent fit: CalPERS actively commits to growth equity and our fund size is ideal for their program.', ARRAY['Growth equity is core strategy for CalPERS PE', 'Fintech exposure complements their portfolio', 'Strong ESG alignment'], ARRAY['Competitive process with many funds', 'Will want governance rights']),
('0a555555-5555-5555-5555-555555555555', '0f444444-4444-4444-4444-444444444444', 'aaaa3333-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 91.0, '{"strategy": 90, "size": 95, "geography": 88, "track_record": 92}', 'Strong fit: Ontario Teachers has significant European buyout exposure and values healthcare investments.', ARRAY['Existing relationship from Fund X', 'Healthcare focus aligns with their thesis', 'Long-term partnership approach'], ARRAY['May have capacity constraints in European buyout', 'Will benchmark against peer funds']),
('0a666666-6666-6666-6666-666666666666', '0f444444-4444-4444-4444-444444444444', 'aaaa4444-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 89.5, '{"strategy": 88, "size": 92, "geography": 85, "track_record": 93}', 'Strong fit: ADIA has significant buyout allocation and appetite for European exposure.', ARRAY['Co-investment capability is attractive', 'Fund size matches their preferred range', 'Strong track record appeals to their standards'], ARRAY['May prefer direct deals over fund commitments', 'Long approval process']);

-- =============================================================================
-- 9. FUND-LP STATUS (Pipeline tracking)
-- =============================================================================

INSERT INTO fund_lp_status (fund_id, lp_org_id, gp_interest, gp_interest_reason, pipeline_stage, notes) VALUES
('0f111111-1111-1111-1111-111111111111', 'aaaa2222-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'pursuing', 'Top target - strong fit and existing relationship', 'lp_reviewing', 'Had intro call 12/15. Jennifer reviewing materials. Follow-up scheduled for Jan.'),
('0f111111-1111-1111-1111-111111111111', 'aaaa5555-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'interested', 'Good fit for emerging manager mandate', 'gp_interested', 'Need to get warm intro through portfolio company CEO.'),
('0f111111-1111-1111-1111-111111111111', 'aaaa1111-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'not_interested', 'Fund too small for their program', 'gp_passed', 'Decided not to pursue - below their minimum.'),
('0f333333-3333-3333-3333-333333333333', 'aaaa1111-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'pursuing', 'Excellent fit - priority target', 'mutual_interest', 'David Kim confirmed interest. Scheduling on-site visit.'),
('0f444444-4444-4444-4444-444444444444', 'aaaa3333-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'pursuing', 'Re-up from Fund X', 'in_diligence', 'DD process started. Reference calls next week.');

-- =============================================================================
-- 10. INVESTMENTS (Historical)
-- =============================================================================

INSERT INTO investments (lp_org_id, fund_id, commitment_mm, commitment_date, source, confidence) VALUES
('aaaa2222-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '0f222222-2222-2222-2222-222222222222', 25.0, '2021-06-15', 'disclosed', 'confirmed'),
('aaaa5555-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '0f222222-2222-2222-2222-222222222222', 15.0, '2021-07-01', 'disclosed', 'confirmed'),
('aaaa3333-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '0f444444-4444-4444-4444-444444444444', 200.0, '2020-03-15', 'public', 'confirmed'),
('aaaa4444-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '0f444444-4444-4444-4444-444444444444', 350.0, '2020-04-01', 'public', 'confirmed');

-- =============================================================================
-- 11. RELATIONSHIPS
-- =============================================================================

INSERT INTO relationships (gp_org_id, lp_org_id, relationship_type, prior_commitments, total_committed_mm, relationship_strength, notes) VALUES
('11111111-1111-1111-1111-111111111111', 'aaaa2222-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'existing_investor', 1, 25.0, 4, 'Strong relationship from Fund III. Jennifer is champion internally.'),
('11111111-1111-1111-1111-111111111111', 'aaaa5555-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'existing_investor', 1, 15.0, 3, 'Good relationship but smaller commitment.'),
('33333333-3333-3333-3333-333333333333', 'aaaa3333-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'existing_investor', 2, 350.0, 5, 'Long-standing partnership. Key LP for the franchise.'),
('33333333-3333-3333-3333-333333333333', 'aaaa4444-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'existing_investor', 1, 350.0, 4, 'Strong first fund relationship. Potential for increase.');

-- =============================================================================
-- Done!
-- =============================================================================
