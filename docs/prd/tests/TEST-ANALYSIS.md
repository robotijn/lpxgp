# Test Specification Analysis

**Date:** 2025-12-21
**Purpose:** Verify test coverage against PRD features and identify gaps

---

## Summary

| Metric | Value |
|--------|-------|
| Total test files | 7 |
| Total scenarios | ~1,651 |
| Total lines | ~15,000 |
| PRD features covered | 35/35 (100%) |

---

## Coverage Matrix: PRD Features → Test Files

### Priority A: LP Search & Database

| Feature ID | Feature Name | Status | Test File | Notes |
|------------|--------------|--------|-----------|-------|
| F-LP-01 | LP Profile Storage | ✅ | m0-foundation | Core data validation |
| F-LP-02 | LP Search & Filter | ✅ | m1-auth-search | Full-text search |
| F-LP-03 | Semantic Search | ✅ | m2-semantic | Voyage AI embeddings |
| F-LP-04 | LP Data Import | ✅ | m0-foundation | CSV import, validation |
| F-LP-05 | LP Data Cleaning | ✅ | m0-foundation | Normalization, dedup |
| F-LP-06 | LP Data Enrichment | ✅ | m2-semantic | Research agent |

### Priority B: Matching Engine

| Feature ID | Feature Name | Status | Test File | Notes |
|------------|--------------|--------|-----------|-------|
| F-MATCH-01 | Hard Filter Matching | ✅ | m3-matching | Strategy, geography |
| F-MATCH-02 | Soft Scoring | ✅ | m3-matching | Score calculation |
| F-MATCH-03 | Semantic Matching | ✅ | m3-matching | Thesis similarity |
| F-MATCH-04 | Match Explanations | ✅ | m3-matching | AI-generated |
| F-MATCH-05 | Match Feedback | ✅ | m3-matching | User ratings [P1] |
| F-MATCH-06 | LP-Side Matching | ✅ | m3-matching | Bidirectional |
| F-MATCH-07 | Enhanced Explanations | ✅ | m4-pitch | With learning |

### Priority C: Pitch Generation

| Feature ID | Feature Name | Status | Test File | Notes |
|------------|--------------|--------|-----------|-------|
| F-PITCH-01 | Executive Summary | ✅ | m4-pitch | LP-specific |
| F-PITCH-02 | Outreach Email | ✅ | m4-pitch | Draft generation |

### Priority D: Authentication

| Feature ID | Feature Name | Status | Test File | Notes |
|------------|--------------|--------|-----------|-------|
| F-AUTH-01 | User Login | ✅ | m1-auth-search | Session, JWT |
| F-AUTH-02 | Multi-tenancy | ✅ | m1-auth-search | RLS policies |
| F-AUTH-03 | Role-Based Access | ✅ | m1-auth-search | Admin/Member/Viewer |
| F-AUTH-04 | Invitation System | ✅ | m1-auth-search | No public registration |

### Priority E: Multi-Agent Architecture

| Feature ID | Feature Name | Status | Test File | Notes |
|------------|--------------|--------|-----------|-------|
| F-AGENT-01 | Research Agent | ✅ | m3-matching | Data enrichment |
| F-AGENT-02 | LLM Constraints | ✅ | m3-matching | Mandate interpretation |
| F-AGENT-03 | Learning Agent | ✅ | m3-matching | Cross-company signals |
| F-AGENT-04 | Explanation Agent | ✅ | m4-pitch | Interaction learning |

### Priority F: User Interface

| Feature ID | Feature Name | Status | Test File | Notes |
|------------|--------------|--------|-----------|-------|
| F-UI-01 | Dashboard | ✅ | m1-auth-search | Home screen |
| F-UI-02 | Fund Profile Form | ✅ | m3-matching | Wizard flow |
| F-UI-03 | LP Search Interface | ✅ | m1-auth-search | Filters, results |
| F-UI-04 | Match Results View | ✅ | m4-pitch | Score breakdown |
| F-UI-05 | Admin Interface | ✅ | m5-production | Data management |

### Priority G: Human-in-the-Loop

| Feature ID | Feature Name | Status | Test File | Notes |
|------------|--------------|--------|-----------|-------|
| F-HITL-01 | Email Review | ✅ | m4-pitch | No auto-send |
| F-HITL-02 | Match Selection | ✅ | m3-matching | Shortlist approval |
| F-HITL-03 | Fund Confirmation | ✅ | m3-matching | AI extraction review |
| F-HITL-04 | Data Import Preview | ✅ | m5-production | Before commit |
| F-HITL-05 | LP Data Corrections | ✅ | m5-production | Flag outdated [P1] |

### Agent Debate System

| Feature ID | Feature Name | Status | Test File | Notes |
|------------|--------------|--------|-----------|-------|
| F-DEBATE | Multi-Agent Debates | ✅ | m3-matching | Bull/Bear/Synthesizer |
| F-PITCH-CRITIC | Pitch Quality | ✅ | m4-pitch | Generator/Critic pattern |

---

## Gaps Identified

### Missing Tests (Should Add)

| Gap | Priority | Recommendation | Est. Scenarios |
|-----|----------|----------------|----------------|
| **Langfuse Observability** | HIGH | Add tests for trace capture, metrics recording | 10-15 |
| **Prompt Versioning** | MEDIUM | Test version switching, rollback | 8-10 |
| **A/B Testing for Prompts** | MEDIUM | Test traffic splitting, metrics comparison | 6-8 |
| **Real-Time vs Batch Mode** | MEDIUM | Test mode switching, user experience | 10-12 |
| **Agent Token Usage** | LOW | Cost tracking, budget limits | 5-6 |

### Detailed Gap Descriptions

#### 1. Langfuse Observability Tests (HIGH)

The architecture specifies Langfuse for monitoring, but no tests verify:
- Traces are created for each debate
- Span hierarchy is correct
- Metrics are recorded (latency, tokens, cost)
- Failed traces are handled

**Suggested scenarios:**
```gherkin
Feature: Agent Observability with Langfuse

  Scenario: Debate creates complete trace
    Given a match debate is initiated
    When the debate completes successfully
    Then a trace is recorded in Langfuse with:
      | field | expected |
      | name | match_debate_{fund_id}_{lp_id} |
      | spans | >= 3 (bull, bear, synthesizer) |
      | status | success |

  Scenario: Failed debate records error trace
    Given a match debate is initiated
    When Bull Agent fails with API error
    Then trace is recorded with status "error"
    And error details are captured

  Scenario: Token usage is tracked
    Given a match debate completes
    Then token usage is recorded:
      | metric | type |
      | input_tokens | number |
      | output_tokens | number |
      | total_cost | currency |
```

#### 2. Prompt Versioning Tests (MEDIUM)

Architecture documents prompt versioning but no tests verify:
- Prompts can be retrieved by version
- Active version is used by default
- Version history is maintained

**Suggested scenarios:**
```gherkin
Feature: Prompt Version Management

  Scenario: Use active prompt version
    Given prompt "match_bull_agent" has versions [1, 2, 3]
    And version 2 is marked as active
    When Bull Agent runs
    Then prompt version 2 is used
    And trace records prompt_version = 2

  Scenario: Rollback to previous version
    Given prompt "match_bull_agent" active version is 3
    When admin rolls back to version 2
    Then new debates use version 2
```

#### 3. Real-Time vs Batch Mode Tests (MEDIUM)

PRD specifies different modes but tests don't clearly verify:
- New fund gets immediate simplified scoring
- Refresh requests are queued for batch
- Cached results are served appropriately

**Suggested scenarios:**
```gherkin
Feature: Real-Time vs Batch Processing

  Scenario: New fund gets immediate matches
    Given I create a new fund profile
    When I request matches
    Then I see results within 30 seconds
    And scores are from simplified single-pass
    And status shows "preliminary - full analysis tonight"

  Scenario: Refresh queues for batch
    Given I have existing matches (cached)
    When I click "Refresh Matches"
    Then I see message "Queued for overnight analysis"
    And current cached results remain visible
```

---

## Tests That Could Be Reduced

| Area | Current | Issue | Recommendation |
|------|---------|-------|----------------|
| E2E Error Paths | ~100 scenarios | Overlap with unit tests | Consolidate to 50 key paths |
| Negative Scenarios | ~200 scenarios | Many similar patterns | Template-based reduction |
| Boundary Conditions | ~80 scenarios | Some redundant | Focus on critical boundaries |

**Estimated reduction:** ~100 scenarios could be consolidated without losing coverage.

---

## Recommendations

### Immediate Actions (Before M3)

1. **Add Langfuse observability tests** to m3-matching.feature.md
   - 15 scenarios covering trace capture, metrics, errors
   - Critical for debugging agent issues in production

2. **Add prompt versioning tests** to m3-matching.feature.md
   - 10 scenarios for version management
   - Required for prompt improvement workflow

### Future Actions (M4+)

3. **Add A/B testing tests** to m4-pitch.feature.md
   - 8 scenarios for traffic splitting
   - Enables data-driven prompt optimization

4. **Consolidate E2E error paths**
   - Review e2e-journeys.feature.md for overlaps
   - Reduce to essential user-facing scenarios

---

## Test Metrics Summary

| Milestone | Scenarios | Features | Coverage |
|-----------|-----------|----------|----------|
| M0 | 183 | 12 | 100% |
| M1 | 249 | 16 | 100% |
| M2 | 157 | 5 | 100% |
| M3 | 385 | 20 | 95% (missing observability) |
| M4 | 271 | 12 | 95% (missing A/B tests) |
| M5 | 230 | 12 | 100% |
| E2E | 174 | 21 | 100% |

**Overall: 1,649 scenarios covering 35 features with 2 identified gaps.**
