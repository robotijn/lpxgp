# Test Specifications

**Format:** Gherkin/BDD (natural language)
**Purpose:** Communicate requirements with product owner, generate tests later

## Test Files by Milestone

| Milestone | File | Coverage |
|-----------|------|----------|
| [M0: Foundation](m0-foundation.feature.md) | Data import, cleaning, quality | LP database setup |
| [M1: Auth + Search](m1-auth-search.feature.md) | Authentication, LP search, RLS | Core platform security |
| [M1b: IR Core](m1b-ir-core.feature.md) | Investor Relations features | IR team workflows |
| [M2: Semantic](m2-semantic.feature.md) | Embeddings, semantic search | AI-powered search |
| [M3: Matching](m3-matching.feature.md) | GP profiles, agent debates, scoring | Match generation |
| [M4: Pitch](m4-pitch.feature.md) | Pitch generation, learning agents | Content creation |
| [M5: Production](m5-production.feature.md) | Admin, monitoring, performance | Operations |
| [M9: IR Advanced](m9-ir-advanced.feature.md) | Events, advanced IR | IR expansion |
| [E2E Journeys](e2e-journeys.feature.md) | Complete user flows | Integration tests |
| [Security](security.feature.md) | Auth, RLS, input validation | Security tests |

## Feature Coverage by Area

| Area | Features | Milestone |
|------|----------|-----------|
| Authentication | F-AUTH-01 to F-AUTH-04 | M1, M5 |
| GP Profile | F-GP-01 to F-GP-04 | M3 |
| LP Database | F-LP-01 to F-LP-06 | M0, M1, M2 |
| Matching | F-MATCH-01 to F-MATCH-07 | M3, M4 |
| Pitch Generation | F-PITCH-01 to F-PITCH-05 | M4 |
| User Interface | F-UI-01 to F-UI-05 | M1, M4, M5 |
| Human-in-the-Loop | F-HITL-01 to F-HITL-05 | M3, M4, M5 |
| Agentic Architecture | F-AGENT-01 to F-AGENT-04 | M3, M4 |

## Priority Coverage

| Priority | Count | Status |
|----------|-------|--------|
| P0 (MVP) | 29 | All tested |
| P1 | 11 | All tested |
| P2 | 1 | All tested |

## How to Read These Specs

```gherkin
Feature: Feature Name
  As a [role]
  I want [capability]
  So that [benefit]

  Background:
    Given [common preconditions]

  Scenario: Scenario Name
    Given [initial context]
    When [action taken]
    Then [expected outcome]
    And [additional outcomes]

  Scenario: Another Scenario
    Given [context]
    When [action]
    Then [outcome]
```

## Running Tests (Future)

Once implemented, tests will run with:
```bash
uv run pytest tests/                    # All tests
uv run pytest tests/ -k "auth"          # By feature area
uv run pytest tests/e2e/                # E2E only
```
