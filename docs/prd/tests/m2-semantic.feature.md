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

  # ==========================================================================
  # NEGATIVE TESTS: Empty Search Queries
  # ==========================================================================

  Scenario: Empty search query
    When I submit a search with an empty query ""
    Then I see validation message "Please enter a search term"
    And no API call is made to Voyage AI
    And the current results remain unchanged

  Scenario: Whitespace-only search query
    When I submit a search with only spaces "   "
    Then I see validation message "Please enter a search term"
    And no API call is made to Voyage AI

  Scenario: Empty query after clearing
    Given I previously searched for "technology investors"
    When I clear the search box and press Enter
    Then I see all LPs unfiltered by search
    And other filters remain applied

  # ==========================================================================
  # NEGATIVE TESTS: Very Long Search Queries
  # ==========================================================================

  Scenario: Search query at maximum length
    Given the maximum query length is 1000 characters
    When I search with a query of exactly 1000 characters
    Then the search executes successfully
    And results are returned

  Scenario: Search query exceeds maximum length
    Given the maximum query length is 1000 characters
    When I search with a query of 1500 characters
    Then I see validation message "Search query is too long (max 1000 characters)"
    And the query is not sent to Voyage AI

  Scenario: Very long query is truncated gracefully in UI
    Given a valid but long query of 800 characters
    When I perform the search
    Then the search box shows the full query
    And results are displayed correctly
    And the query preview in results shows truncated version with "..."

  # ==========================================================================
  # NEGATIVE TESTS: Special Characters in Search
  # ==========================================================================

  Scenario: Search with special characters - quotes
    When I search "investors looking for "deep tech" opportunities"
    Then the search handles embedded quotes correctly
    And results match "deep tech" semantically

  Scenario: Search with special characters - SQL injection attempt
    When I search "technology'; DROP TABLE lps;--"
    Then the query is sanitized
    And the search executes safely
    And results match "technology" if any exist

  Scenario: Search with special characters - HTML/script tags
    When I search "<script>alert('xss')</script> investors"
    Then the HTML tags are escaped or stripped
    And no script executes
    And search matches "investors" semantically if possible

  Scenario: Search with unicode characters
    When I search "投资者 interested in 技术"
    Then the search handles unicode correctly
    And results are returned (may be empty if no matches)
    And no error occurs

  Scenario: Search with emoji characters
    When I search "🌱 sustainable investing 🌍"
    Then emojis are handled gracefully
    And search focuses on text "sustainable investing"
    And results are returned

  Scenario: Search with newlines and tabs
    When I search "technology\ninvestors\twith experience"
    Then whitespace is normalized
    And search matches "technology investors with experience"

  Scenario: Search with only special characters
    When I search "!@#$%^&*()"
    Then I see message "No meaningful search terms found"
    Or results are empty with appropriate message

  # ==========================================================================
  # NEGATIVE TESTS: No Matching Results
  # ==========================================================================

  Scenario: No matching results for valid query
    When I search "quantum computing in underwater basket weaving"
    Then I see "No LPs match your search"
    And I see suggestions:
      | Try different keywords |
      | Remove some filters |
      | Browse all LPs |

  Scenario: No results due to overly specific filters
    When I search "technology investors"
    And I filter by type "Sovereign Wealth Fund"
    And I filter by geography "Antarctica"
    And I filter by check size "$1B+"
    Then I see "No LPs match your search and filters"
    And I see which filters can be relaxed

  Scenario: No results with high similarity threshold
    Given the minimum similarity threshold is set to 95
    When I search "moderately related concept"
    Then I see "No results above 95% similarity"
    And I see option to "Show results with lower similarity"

  Scenario: Empty database returns appropriate message
    Given the LP database is empty
    When I perform any search
    Then I see "No LP data available"
    And I see option to "Import LP data"

  # ==========================================================================
  # NEGATIVE TESTS: API Failures (Voyage AI Down)
  # ==========================================================================

  Scenario: Voyage AI API returns 500 error
    Given Voyage AI API is returning 500 errors
    When I perform a semantic search
    Then I see "Semantic search is temporarily unavailable"
    And I see option to "Use keyword search instead"
    And the error is logged for monitoring

  Scenario: Voyage AI API returns 401 unauthorized
    Given Voyage AI API key is invalid or expired
    When I perform a semantic search
    Then I see "Semantic search is temporarily unavailable"
    And admin is alerted about API key issue
    And users can still use keyword search

  Scenario: Voyage AI API returns 429 rate limit
    Given Voyage AI API rate limit is exceeded
    When I perform a semantic search
    Then I see "Search is busy, please try again in a moment"
    And retry is attempted after backoff
    And rate limit headers are respected

  Scenario: Voyage AI API returns malformed response
    Given Voyage AI API returns invalid JSON
    When I perform a semantic search
    Then the error is handled gracefully
    And I see "Semantic search encountered an error"
    And fallback to keyword search is offered

  Scenario: Voyage AI API returns empty embeddings
    Given Voyage AI API returns empty embedding array
    When I perform a semantic search
    Then the error is handled gracefully
    And I see appropriate error message
    And the issue is logged for investigation

  Scenario: Network error connecting to Voyage AI
    Given network connectivity to Voyage AI is lost
    When I perform a semantic search
    Then I see "Unable to connect to search service"
    And I see option to "Retry" or "Use keyword search"

  Scenario: Graceful degradation when embedding service unavailable
    Given Voyage AI has been down for 5 minutes
    When I try to search
    Then the system offers keyword-based search as fallback
    And a banner shows "Semantic search temporarily unavailable"
    And cached embeddings are still usable for comparisons

  # ==========================================================================
  # NEGATIVE TESTS: Timeout Handling
  # ==========================================================================

  Scenario: Voyage AI API timeout
    Given Voyage AI API takes longer than 10 seconds to respond
    When I perform a semantic search
    Then the request is cancelled after timeout
    And I see "Search timed out, please try again"
    And I see option to retry

  Scenario: Database query timeout
    Given the vector similarity search takes too long
    When I perform a semantic search
    Then the query is cancelled after 5 seconds
    And I see "Search is taking too long"
    And simplified search is offered

  Scenario: Slow search shows loading state
    Given the search takes 3 seconds (within timeout)
    When I perform a semantic search
    Then loading spinner is shown immediately
    And "Searching..." text appears
    And UI remains responsive
    And results appear when ready

  Scenario: User cancels slow search
    Given a search is taking longer than expected
    When I click "Cancel" or navigate away
    Then the pending request is cancelled
    And no results are displayed
    And system resources are freed

  Scenario: Multiple rapid searches handle correctly
    When I quickly type and search "tech"
    And before results return I search "healthcare"
    Then only the most recent search results are shown
    And previous pending requests are cancelled
    And no race condition occurs

  # ==========================================================================
  # NEGATIVE TESTS: Invalid Filter Combinations
  # ==========================================================================

  Scenario: Contradictory filters
    When I filter by geography "North America only"
    And I also filter by geography "Europe only"
    Then I see "These filters have no overlap"
    And I see option to "Clear geography filters"

  Scenario: Check size range invalid - min greater than max
    When I set check size filter min "$100M"
    And I set check size filter max "$50M"
    Then I see "Minimum cannot be greater than maximum"
    And the filter is not applied until corrected

  Scenario: Invalid filter values
    When I try to filter by check size "not a number"
    Then I see validation error "Please enter a valid amount"
    And the filter is not applied

  Scenario: Filter with no matching LPs in database
    When I filter by type "Cryptocurrency Exchange"
    And this type does not exist in the database
    Then I see "No LPs match this filter"
    And the filter type is shown as yielding 0 results

  Scenario: Too many filters applied
    When I apply more than 10 filters simultaneously
    Then I see "Too many filters may limit results"
    And search still executes
    And results are shown (may be empty)

  Scenario: Filter after semantic search preserves relevance
    Given I searched for "climate tech investors"
    When I add filter by type "Family Office"
    Then results are filtered to Family Offices
    And semantic relevance ranking is preserved within filtered set
    And scores are recalculated relative to filtered set

  Scenario: Reset all filters
    Given I have applied multiple filters and a search
    When I click "Reset all filters"
    Then all filters are cleared
    And search query remains
    And results update to show all matches for query

  # ==========================================================================
  # NEGATIVE TESTS: Edge Cases
  # ==========================================================================

  Scenario: Search with single character
    When I search "a"
    Then I see "Please enter at least 3 characters"
    Or search executes but with low-quality results notice

  Scenario: Search with only stop words
    When I search "the and or but"
    Then I see "Please include more specific terms"
    Or results are empty with explanation

  Scenario: Search with numbers only
    When I search "12345"
    Then the search executes
    And results may match LPs with that number in profile
    Or empty results with appropriate message

  Scenario: Concurrent searches from same user
    Given I have two browser tabs open
    When I perform different searches simultaneously
    Then each tab shows its own results
    And no interference occurs between searches

  Scenario: Search while embeddings are being updated
    Given background job is updating LP embeddings
    When I perform a search
    Then search uses currently available embeddings
    And results are consistent (no partial updates visible)

  Scenario: LP with no mandate description
    Given LP "Silent Investor LLC" has no mandate description
    When I search for any term
    Then "Silent Investor LLC" may appear with low score
    Or is excluded from semantic results
    And no error occurs

  Scenario: LP with very short mandate
    Given LP has mandate "We invest"
    When I search "technology growth equity"
    Then LP scores lower than detailed mandates
    And results are still valid

  Scenario: LP with extremely long mandate
    Given LP has a 10,000 character mandate description
    When I search for related terms
    Then LP is matched correctly
    And embedding was calculated on truncated/summarized text
    And no performance degradation occurs

  Scenario: Search relevance across languages
    Given LP A has English mandate about "renewable energy"
    And LP B has French mandate about "energie renouvelable"
    When I search "renewable energy"
    Then LP A ranks highest
    And LP B may or may not match depending on embedding model

  # ==========================================================================
  # NEGATIVE TESTS: Security Edge Cases
  # ==========================================================================

  Scenario: Search query in URL parameter - XSS prevention
    When I navigate to /search?q=<script>alert(1)</script>
    Then the script is not executed
    And the query is safely displayed/escaped in UI

  Scenario: Extremely nested query structure attempt
    When I submit a malformed JSON query via API
    Then the request is rejected with 400 error
    And no server crash occurs

  Scenario: Search results don't leak unauthorized LP data
    Given LP "Private Investor" is not visible to my user role
    When I search for terms that would match "Private Investor"
    Then "Private Investor" does not appear in my results
    And no information about it is disclosed
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

  # ==========================================================================
  # NEGATIVE TESTS: Enrichment Failures
  # ==========================================================================

  Scenario: External data source API is down
    Given Preqin API is returning 503 errors
    When the bulk update job runs
    Then the job fails gracefully
    And admin is notified of the failure
    And existing LP data remains unchanged
    And job is scheduled for retry

  Scenario: External data source returns invalid data
    Given Preqin API returns malformed JSON
    When the bulk update job runs
    Then the error is logged
    And no LP records are corrupted
    And admin is alerted to investigate

  Scenario: Enrichment data conflicts with existing data
    Given LP "Alpha Fund" has AUM "$10B" (high confidence)
    And external source says AUM "$500M"
    When enrichment is processed
    Then conflict is flagged for manual review
    And both values are shown to admin
    And no automatic override occurs

  Scenario: Enrichment times out
    Given external API takes too long to respond
    When bulk update job runs
    Then timeout is enforced
    And partial results are not applied
    And job status shows "Timed out"

  Scenario: Duplicate LP matching ambiguity
    Given external data mentions "Blackrock"
    And database has "BlackRock Inc" and "Blackrock Capital"
    When enrichment runs
    Then the ambiguous match is flagged
    And admin must manually select correct LP
    And no automatic enrichment occurs

  Scenario: Enrichment with empty or null values
    Given external source returns null for AUM field
    When enrichment is processed
    Then null values do not overwrite existing data
    And the field is skipped in enrichment
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

  # ==========================================================================
  # E2E NEGATIVE SCENARIOS
  # ==========================================================================

  Scenario: Search journey with API failure recovery
    Given I am logged in as a GP
    And Voyage AI API is temporarily down

    When I go to LP Search
    And I enter "technology investors"
    Then I see "Semantic search temporarily unavailable"
    And I see option for "Keyword search"

    When I click "Use keyword search"
    Then I see results matching "technology" in LP names/descriptions
    And results are sorted alphabetically or by relevance heuristic

    When Voyage AI API recovers
    And I refresh the page
    Then semantic search is available again
    And I can perform full semantic queries

  Scenario: Search journey with progressive error handling
    Given I am logged in as a GP

    When I search with an empty query
    Then I see validation message
    And search does not execute

    When I search "!@#$%"
    Then I see "No meaningful search terms"

    When I search "technology investors in healthcare"
    And the request times out
    Then I see timeout message
    And I click "Retry"
    And this time it succeeds
    And I see relevant results

  Scenario: Filter journey with edge cases
    Given I am logged in as a GP
    And I searched for "growth equity"

    When I add filter for check size "$100M - $50M" (invalid range)
    Then I see "Invalid range" error
    And filter is not applied

    When I correct to "$50M - $100M"
    Then filter is applied
    And results are updated

    When I add 15 different filters
    Then I see warning "Many filters applied"
    And results show 0 matches

    When I click "Reset all"
    Then all filters clear
    And search query remains
    And I see full results again
```

---

## Technical Test Cases

```gherkin
Feature: Semantic Search Technical Implementation
  As a developer
  I need to ensure robust error handling
  So that the system is reliable in production

  # ==========================================================================
  # API Client Resilience
  # ==========================================================================

  Scenario: Voyage AI client retries on transient failures
    Given Voyage AI returns 503 on first attempt
    And succeeds on second attempt
    When I perform a semantic search
    Then the retry happens automatically
    And results are returned to user
    And retry is logged for monitoring

  Scenario: Voyage AI client respects rate limits
    Given Voyage AI returns 429 with Retry-After: 60
    When I perform a semantic search
    Then the client waits before retrying
    And the user sees appropriate waiting message
    And rate limit is not violated

  Scenario: Circuit breaker opens after repeated failures
    Given Voyage AI has failed 5 times in the last minute
    When I perform a semantic search
    Then the circuit breaker is open
    And the request fails fast without calling API
    And fallback to keyword search is offered
    And circuit breaker is checked periodically for recovery

  # ==========================================================================
  # Embedding Cache Behavior
  # ==========================================================================

  Scenario: LP embeddings are cached
    Given LP "Tech Ventures" has a cached embedding
    When a search runs
    Then the cached embedding is used for comparison
    And no API call is made for that LP's embedding

  Scenario: LP embedding cache is invalidated on mandate update
    Given LP "Tech Ventures" has a cached embedding
    When the LP's mandate description is updated
    Then the cached embedding is invalidated
    And new embedding is generated on next search or background job

  Scenario: Search query embedding is cached briefly
    Given I searched for "technology investors"
    When I search for "technology investors" again within 5 minutes
    Then the cached query embedding is used
    And no duplicate API call is made

  # ==========================================================================
  # Database Resilience
  # ==========================================================================

  Scenario: Database connection pool exhausted
    Given all database connections are in use
    When I perform a semantic search
    Then I see "System is busy, please try again"
    And no database deadlock occurs
    And connections are eventually freed

  Scenario: Vector index is corrupted
    Given the pgvector index has corruption
    When I perform a semantic search
    Then the error is caught
    And I see "Search temporarily unavailable"
    And admin is alerted to rebuild index

  Scenario: Large result set is paginated
    Given 500 LPs match my search
    When I perform the search
    Then I see first 20 results
    And pagination controls appear
    And I can load more results
    And total count is displayed
```
