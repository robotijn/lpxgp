# Test Specifications

**Format:** Gherkin/BDD (natural language)
**Purpose:** Communicate requirements with product owner, generate tests later

## Feature Coverage

| Area | Features | Tests |
|------|----------|-------|
| [Authentication](auth.feature.md) | F-AUTH-01 to F-AUTH-04 | 4 features |
| [GP Profile](gp-profile.feature.md) | F-GP-01 to F-GP-04 | 4 features |
| [LP Database](lp-database.feature.md) | F-LP-01 to F-LP-06 | 6 features |
| [Matching](matching.feature.md) | F-MATCH-01 to F-MATCH-07 | 7 features |
| [Pitch Generation](pitch.feature.md) | F-PITCH-01 to F-PITCH-05 | 5 features |
| [User Interface](ui.feature.md) | F-UI-01 to F-UI-05 | 5 features |
| [Human-in-the-Loop](human-in-loop.feature.md) | F-HITL-01 to F-HITL-05 | 5 features |
| [Agentic Architecture](agents.feature.md) | F-AGENT-01 to F-AGENT-04 | 4 features |
| [E2E User Journeys](e2e-journeys.feature.md) | Complete flows | 6 journeys |

## Priority Coverage

| Priority | Count | Status |
|----------|-------|--------|
| P0 (MVP) | 29 | All tested |
| P1 | 11 | All tested |
| P2 | 1 | All tested |

## Milestone Mapping

| Milestone | Features Tested |
|-----------|-----------------|
| M0: Foundation | F-LP-01, F-LP-04, F-LP-05 |
| M1: Auth + Search | F-AUTH-01 to 04, F-LP-02, F-UI-01, F-UI-03 |
| M2: Semantic Search | F-LP-03, F-LP-06 |
| M3: Matching + Agents | F-GP-01 to 04, F-MATCH-01 to 06, F-HITL-02, F-HITL-03, F-AGENT-01 to 03 |
| M4: Pitch + Learning | F-PITCH-01 to 05, F-UI-04, F-HITL-01, F-AGENT-04, F-MATCH-07 |
| M5: Production | F-AUTH-04, F-UI-05, F-HITL-04, F-HITL-05 |

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
