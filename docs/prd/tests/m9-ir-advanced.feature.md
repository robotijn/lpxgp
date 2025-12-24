# M9: IR Advanced - Test Specifications

**Milestone:** M9 - IR Advanced (Entity Resolution & Intelligence)
**Focus:** Entity Resolution, AI briefing books, relationship scoring, data imports

> **Note:** Basic IR tests (contact lookup, events, touchpoints, tasks) are in [M1b tests](m1b-ir-core.feature.md).

---

## Feature: Entity Resolution

### F-ER-01: Data Import

```gherkin
Feature: Data Import with Entity Resolution
  As a data admin
  I want to import contacts from external sources
  So that I can consolidate relationship data

  Background:
    Given I am logged in as a data admin
    And the system has existing contacts

  Scenario: Import CSV file
    When I click "Import Data"
    And I upload a CSV file with 500 contacts
    And I map columns to fields (name, email, company, title)
    And I click "Start Import"
    Then I see import progress
    And import completes within 2 minutes
    And I see summary: "500 records processed"

  Scenario: Import detects duplicates
    Given the database has "John Smith" at "CalPERS"
    When I import a CSV containing "John Smith" at "CalPERS"
    Then the ER pipeline detects a potential duplicate
    And the record is flagged for review
    And I see match confidence score (e.g., 87%)

  Scenario: Auto-merge high-confidence matches
    Given import finds a match with 95% confidence
    When auto-merge threshold is set to 90%
    Then the records are automatically merged
    And golden record is created
    And field provenance is tracked

  Scenario: Flag uncertain matches for review
    Given import finds a match with 75% confidence
    When auto-merge threshold is set to 90%
    Then the match is NOT auto-merged
    And it appears in the human review queue
    And both records remain separate until reviewed

  Scenario: Handle import errors gracefully
    When I upload a CSV with malformed rows
    Then valid rows are imported
    And invalid rows are logged with error details
    And I can download error report
```

### F-ER-02: Human Review Queue

```gherkin
Feature: Human Review Queue for Entity Resolution
  As a data admin
  I want to review uncertain matches
  So that I can ensure data quality

  Background:
    Given I am logged in as a data admin
    And there are matches in the review queue

  Scenario: View match comparison
    When I open a match in the review queue
    Then I see side-by-side comparison
    And differences are highlighted
    And I see match confidence score
    And I see which fields match/differ

  Scenario: Approve match (merge records)
    When I click "Merge" on a match
    Then the records are merged into a golden record
    And field values are selected from best source
    And provenance is tracked for each field
    And the match is removed from queue

  Scenario: Reject match (keep separate)
    When I click "Keep Separate" on a match
    Then both records remain in database
    And they are marked as "reviewed - not duplicates"
    And the match is removed from queue
    And future imports won't re-flag this pair

  Scenario: Edit before merge
    When I click "Edit & Merge"
    Then I can modify field values before merging
    And I can select which source to use per field
    And I can add notes explaining the merge

  Scenario: Queue prioritization
    Given the queue has 100 matches
    When I view the queue
    Then matches are sorted by confidence (uncertain first)
    And I can filter by source (CSV, Salesforce, etc.)
    And I can filter by entity type (person, company)
```

### F-ER-03: Golden Record Management

```gherkin
Feature: Golden Record Management
  As a data admin
  I want to manage golden records
  So that I maintain a single source of truth

  Background:
    Given I am logged in as a data admin

  Scenario: View golden record with provenance
    Given a contact has data from 3 sources
    When I view the contact profile
    Then I see the golden record values
    And I can expand to see field provenance
    And each field shows its source and last update

  Scenario: Override golden record field
    When I edit a field on a golden record
    And I save the change
    Then the field value is updated
    And provenance shows "Manual override by [user]"
    And previous value is preserved in history

  Scenario: View merge history
    Given a golden record was created from 3 source records
    When I click "View History"
    Then I see all source records
    And I see merge dates and who approved
    And I can see original values from each source
```

---

## Feature: AI Briefing Books

### F-BB-01: Briefing Book Generation

```gherkin
Feature: AI-Powered Briefing Books
  As an IR team member
  I want AI-generated briefing books before events
  So that I know who to prioritize meeting

  Background:
    Given I am logged in as an IR team member
    And I have an event "SuperReturn 2025" with 50 attendees

  Scenario: Generate briefing book
    When I open "SuperReturn 2025"
    And I click "Generate Briefing Book"
    Then AI generates the briefing book
    And generation completes within 30 seconds
    And I see "Briefing book ready"

  Scenario: View briefing book
    Given a briefing book has been generated
    When I open the briefing book
    Then I see attendees ranked by priority
    And each attendee has a profile card
    And cards show talking points and topics to avoid

  Scenario: Briefing book content
    When I view an attendee's briefing card
    Then I see:
      | Section | Content |
      | Quick Facts | Title, company, tenure |
      | Relationship Score | 1-5 scale with explanation |
      | Recent Activity | Last 3 touchpoints |
      | Talking Points | AI-generated based on history |
      | Topics to Avoid | Extracted from notes |
      | Suggested Priority | Must meet / Should meet / Optional |

  Scenario: Refresh briefing book
    Given a briefing book was generated 7 days ago
    And new touchpoints have been logged since
    When I click "Refresh Briefing Book"
    Then AI regenerates with new data
    And I see what changed since last version

  Scenario: Export briefing book
    When I click "Export PDF"
    Then I download a formatted PDF
    And it's optimized for mobile viewing
    And it works offline
```

### F-BB-02: Talking Points Generation

```gherkin
Feature: AI Talking Points
  As an IR team member
  I want AI-generated talking points
  So that I have relevant conversation starters

  Background:
    Given I am logged in as an IR team member
    And contact "John Smith" has 10 touchpoints logged

  Scenario: Generate talking points from history
    When AI generates talking points for John Smith
    Then points reference specific past conversations
    And points are relevant to current context
    And points avoid topics marked as sensitive

  Scenario: Talking points consider recency
    Given last touchpoint was 90 days ago
    When AI generates talking points
    Then points include "reconnection" framing
    And reference the last meaningful interaction
    And suggest updates to share

  Scenario: Topics to avoid extracted from notes
    Given a touchpoint note says "John dislikes discussing competitor XYZ"
    When AI generates the briefing card
    Then "Topics to Avoid" includes "Competitor XYZ"
    And explanation shows source note
```

---

## Feature: Relationship Intelligence

### F-RI-01: Relationship Scoring

```gherkin
Feature: Relationship Scoring
  As an IR team member
  I want to see relationship strength scores
  So that I can prioritize outreach

  Background:
    Given I am logged in as an IR team member

  Scenario: View relationship score
    Given contact "John Smith" has 15 touchpoints over 2 years
    When I view John's profile
    Then I see relationship score (e.g., 4/5)
    And I see score breakdown:
      | Factor | Weight | Score |
      | Touchpoint frequency | 30% | 5/5 |
      | Recency | 25% | 3/5 |
      | Sentiment trend | 25% | 4/5 |
      | Engagement depth | 20% | 4/5 |

  Scenario: Score reflects activity decay
    Given contact "Jane Doe" hasn't been contacted in 60 days
    When I view Jane's profile
    Then relationship score shows decay
    And "Stale relationship" warning appears
    And suggested action: "Schedule follow-up"

  Scenario: Score updates after touchpoint
    Given contact has score 3/5
    When I log a positive touchpoint
    Then score recalculates
    And new score reflects the interaction
    And score history shows the change

  Scenario: Compare relationship scores
    When I view the relationship dashboard
    Then I see all contacts with scores
    And I can sort by score (high to low)
    And I can filter by score range
```

### F-RI-02: Priority Queue

```gherkin
Feature: Priority Queue
  As an IR team manager
  I want a priority queue of relationships
  So that I can assign follow-ups strategically

  Background:
    Given I am logged in as an IR team manager
    And the system has 500 contacts with relationship data

  Scenario: View priority queue
    When I open the priority queue
    Then I see contacts ranked by:
      | Priority Factor | Description |
      | Staleness | Days since last contact |
      | Score decay | Recent score decline |
      | Importance | LP size, allocation fit |
      | Urgency | Upcoming events, deadlines |

  Scenario: Filter priority queue
    When I filter by "Stale > 30 days"
    Then I see only contacts not touched in 30+ days
    And queue re-ranks within filter

  Scenario: Assign from priority queue
    When I select 5 contacts from the queue
    And I click "Assign to Team Member"
    And I select "Sarah Johnson"
    Then tasks are created for Sarah
    And contacts are marked as "Assigned"

  Scenario: Priority queue alerts
    Given contact "John Smith" score dropped from 4 to 2
    When I view the priority queue
    Then John appears with "Score Alert" badge
    And alert explains the score drop
```

---

## Feature: Advanced Analytics

### F-AA-01: Event ROI Tracking

```gherkin
Feature: Event ROI Analytics
  As an IR team manager
  I want to track event ROI
  So that I know which events drive outcomes

  Background:
    Given I am logged in as an IR team manager
    And we attended "SuperReturn 2024" 6 months ago

  Scenario: View event ROI dashboard
    When I open event analytics for "SuperReturn 2024"
    Then I see:
      | Metric | Value |
      | Attendees Met | 45 |
      | Follow-up Meetings | 12 |
      | Entered Pipeline | 5 |
      | Commitments | 1 |
      | ROI Score | 4.2/5 |

  Scenario: Track progression over time
    When I view the progression funnel
    Then I see conversion rates:
      | Stage | Count | Conversion |
      | Met at Event | 45 | - |
      | Follow-up Meeting | 12 | 27% |
      | Active Pipeline | 5 | 42% |
      | Commitment | 1 | 20% |

  Scenario: Compare events
    When I select multiple events
    And I click "Compare"
    Then I see side-by-side ROI metrics
    And I can identify highest-performing events
```

### F-AA-02: Data Quality Dashboard

```gherkin
Feature: Data Quality Dashboard
  As a data admin
  I want to monitor data quality
  So that I can maintain clean data

  Background:
    Given I am logged in as a data admin

  Scenario: View data quality metrics
    When I open the data quality dashboard
    Then I see:
      | Metric | Value |
      | Total Records | 50,000 |
      | Golden Records | 45,000 |
      | Pending Review | 250 |
      | Duplicate Rate | 2.3% |
      | Completeness | 87% |

  Scenario: View field completeness
    When I click on "Completeness"
    Then I see per-field stats:
      | Field | Completeness |
      | Name | 100% |
      | Email | 92% |
      | Phone | 67% |
      | Title | 89% |
      | Company | 98% |

  Scenario: ER pipeline health
    When I view ER metrics
    Then I see:
      | Metric | Value |
      | Auto-merged (high confidence) | 3,500 |
      | Human-reviewed | 1,200 |
      | Rejected matches | 150 |
      | Average confidence | 78% |
```

---

## Non-Functional Requirements

### Performance

```gherkin
Scenario: Import performance
  Given a CSV file with 10,000 contacts
  When I run the import
  Then import completes within 10 minutes
  And ER pipeline processes all records
  And no timeout errors occur

Scenario: Briefing book generation time
  Given an event with 100 attendees
  When I generate a briefing book
  Then generation completes within 60 seconds
  And all attendee cards are populated

Scenario: Priority queue load time
  Given 50,000 contacts with relationship scores
  When I open the priority queue
  Then the queue loads within 3 seconds
  And I can scroll smoothly
```

### Data Quality

```gherkin
Scenario: ER accuracy
  Given test dataset with known duplicates
  When ER pipeline processes the data
  Then precision is > 95%
  And recall is > 90%
  And F1 score is > 92%

Scenario: Golden record integrity
  When a golden record is created
  Then all source data is preserved
  And field provenance is complete
  And audit trail is maintained
```

---

## Exit Criteria Verification

```gherkin
Feature: M9 Exit Criteria

  Scenario: All exit criteria met
    Then CSV import creates data_imports batch
    And ER pipeline detects potential duplicates
    And confidence scores show match quality
    And human review queue handles uncertain matches
    And golden record merger creates clean master records
    And briefing book auto-generates before events
    And per-attendee cards show talking points
    And relationship scores are computed (1-5 scale)
    And priority queue ranks by score and staleness
    And event ROI dashboard shows funnel metrics
    And data quality dashboard shows ER health
    And all features are live on lpxgp.com
```
