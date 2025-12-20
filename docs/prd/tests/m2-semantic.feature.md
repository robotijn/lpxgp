# Milestone 2: Semantic Search Tests
## "Natural language search works"

---

## F-LP-03: Semantic Search [P0]

```gherkin
Feature: Semantic Search
  As a GP
  I want to search LPs using natural language
  So that I can find investors by meaning, not just keywords

  # Sub-feature: Natural Language Queries
  Scenario: Search with natural language
    Given LPs have mandate descriptions
    When I search "family offices interested in climate tech"
    Then I see LPs whose mandates match semantically
    And results are ranked by relevance

  Scenario: Understand synonyms
    When I search "growth equity technology"
    Then I also find LPs with "growth stage tech investing"
    And "expansion capital software" matches too

  Scenario: Handle complex queries
    When I search "European pensions looking for first-time managers in healthcare"
    Then results match on:
      | Criteria | Matched |
      | Geography | Europe |
      | LP Type | Pension |
      | Emerging Manager | Yes |
      | Sector | Healthcare |

  # Sub-feature: Similarity Scores
  Scenario: Show similarity scores
    When I perform a semantic search
    Then each result has a similarity score
    And scores range from 0 to 100
    And higher scores appear first

  Scenario: Minimum score threshold
    Given the system has a minimum score threshold of 50
    When I search "very specific niche strategy"
    Then results below 50 score are hidden
    And I see "Showing 10 of 25 results above threshold"

  # Sub-feature: Combine with Filters
  Scenario: Semantic search with type filter
    When I search "technology investors"
    And I filter by type "Endowment"
    Then I only see Endowments
    And they are ranked by semantic relevance to "technology"

  Scenario: Semantic search with geography filter
    When I search "climate infrastructure"
    And I filter by geography "Europe"
    Then I only see LPs focused on Europe
    And they match "climate infrastructure" semantically

  Scenario: Semantic search with check size filter
    When I search "growth equity"
    And I filter by check size $25M - $75M
    Then results match "growth equity"
    And LP check sizes overlap with my range

  # Sub-feature: Performance
  Scenario: Semantic search performance
    Given 10,000 LPs with embeddings
    When I perform a semantic search
    Then results return in under 2 seconds

  # Sub-feature: UI Experience
  Scenario: Search input with HTMX
    When I type in the semantic search box
    And I press Enter
    Then loading indicator appears
    And results update via HTMX
    And page does not reload

  Scenario: Clear search
    Given I performed a semantic search
    When I click "Clear"
    Then search is cleared
    And I see all LPs again
    And filters remain applied

  # Sub-feature: Empty Results
  Scenario: No matching results
    When I search for something with no matches
    Then I see "No LPs match your search"
    And I see suggestions:
      | Try different keywords |
      | Remove some filters |
      | Browse all LPs |

  # Sub-feature: Embedding Quality
  Scenario: Similar concepts cluster together
    Given LP A mandate: "We invest in renewable energy startups"
    And LP B mandate: "Focus on clean tech and sustainability"
    And LP C mandate: "Buyout opportunities in manufacturing"
    When I search "green energy companies"
    Then LP A and LP B score higher than LP C

  Scenario: Different concepts are distant
    Given LP A focuses on "biotech and life sciences"
    And LP B focuses on "real estate development"
    When I search "pharmaceutical research"
    Then LP A scores much higher than LP B
```

---

## F-LP-06: LP Data Enrichment [P1]

```gherkin
Feature: LP Data Enrichment
  As a platform
  I want to enhance LP data from external sources
  So that profiles are more complete

  # Sub-feature: Future API Integrations
  Scenario: Design for external data sources
    Given the system is designed for extensibility
    When we add a new data source (e.g., Preqin API)
    Then we can map external fields to LP fields
    And we can schedule regular updates

  Scenario: Bulk update from external provider
    Given we have an API connection to data provider
    When we run a bulk update job
    Then LP records are matched by name/domain
    And new data is flagged for review
    And admin can approve updates

  # Sub-feature: Human Review
  Scenario: Enriched data requires approval
    Given an LP was enriched from external source
    When the job completes
    Then enriched fields show as "pending review"
    And admin can see old vs new values
    And admin must approve before data is live

  Scenario: Reject enrichment
    Given an LP has pending enriched data
    When admin reviews and finds it incorrect
    And admin clicks "Reject"
    Then original data is kept
    And enrichment is logged as rejected

  # Sub-feature: Confidence Scoring
  Scenario: Show confidence for enriched fields
    Given LP data was enriched
    Then each enriched field has a confidence score
    And low-confidence fields are highlighted
    And admin can prioritize review by confidence

  # Sub-feature: Enrichment Log
  Scenario: Track enrichment history
    Given an LP has been enriched multiple times
    When I view the LP's enrichment log
    Then I see:
      | Date | Source | Field | Old Value | New Value | Status |
      | 2024-01-15 | Preqin | AUM | $10B | $12B | Approved |
      | 2024-01-10 | Manual | Type | - | Pension | Approved |

  # Sub-feature: Data Quality Improvement
  Scenario: Enrichment improves data quality score
    Given an LP has data quality score of 40%
    When enrichment adds missing fields
    And admin approves the enrichment
    Then data quality score increases to 70%
```

---

## E2E: Semantic Search Journey

```gherkin
Feature: Natural Language LP Discovery
  As a GP with a new fund
  I want to find LPs using natural language
  So that I can discover investors I might have missed

  Scenario: Use semantic search to find niche investors
    Given I am logged in as a GP
    And I have a fund focused on "AI infrastructure for healthcare"

    # Initial search
    When I go to LP Search
    And I enter "investors interested in AI and healthcare technology"
    Then I see results ranked by semantic similarity
    And top results mention AI, healthtech, or digital health

    # View similarity scores
    When I look at the results
    Then I see scores like:
      | LP Name | Score | Why |
      | Tech Health Fund | 92 | Direct AI + healthcare focus |
      | Digital Ventures | 78 | Technology focus |
      | General Pension | 45 | Broad mandate |

    # Refine with filters
    When I add filter "Check Size: $25M+"
    Then results update
    And I only see LPs with larger check sizes
    And semantic ranking is preserved

    # Combine search modes
    When I also search for "emerging manager friendly"
    Then results prioritize LPs that:
      - Match "AI healthcare" semantically
      - Have emerging manager programs
      - Meet check size criteria

    # Save promising LPs
    When I find 5 great matches
    And I add them to my shortlist
    Then they appear in my saved list
    And I can generate matches for my fund later
```
