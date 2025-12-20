# E2E User Journeys

Complete end-to-end scenarios that span multiple features and milestones.

---

## Journey 1: New GP Onboarding

```gherkin
Feature: New GP Onboarding Journey
  As a new GP user
  I want to set up my account and create my first fund
  So that I can start finding LPs

  Scenario: Complete onboarding from signup to first match
    # Step 1: Registration (M1)
    Given I am a GP at a new fund
    When I visit lpxgp.com
    And I click "Get Started"
    And I register with my email
    Then I receive a verification email

    # Step 2: Email Verification (M1)
    When I click the verification link
    Then my account is verified
    And I am redirected to login

    # Step 3: First Login (M1)
    When I login for the first time
    Then I see a welcome screen
    And I am prompted to create my first fund

    # Step 4: Upload Pitch Deck (M3)
    When I click "Create Fund"
    And I upload my pitch deck
    Then AI extracts fund information
    And I see the extraction results

    # Step 5: Confirm Fund Profile (M3)
    When I review the extracted fields
    And I correct any mistakes
    And I fill in missing required fields
    And I write my investment thesis
    And I click "Confirm and Publish"
    Then my fund profile is created

    # Step 6: Generate Matches (M3)
    When I click "Find Matching LPs"
    Then the matching engine runs
    And I see my matched LPs ranked by score

    # Step 7: Review Top Match (M3)
    When I click on my top match
    Then I see detailed LP information
    And I see why we matched
    And I see talking points

    # Step 8: Generate Pitch (M4)
    When I click "Generate Pitch"
    And I select "Executive Summary"
    Then AI generates a personalized summary
    And I can download as PDF

    # Step 9: Create Outreach Email (M4)
    When I click "Generate Email"
    And I select "Warm" tone
    Then AI generates a personalized email
    And I can edit and copy to clipboard

    # Step 10: Complete Outreach (M4)
    When I copy the email
    And I send it from my Gmail
    And I mark the LP as "Contacted"
    Then my outreach is logged
    And I have completed my first outreach!
```

---

## Journey 2: LP Research and Discovery

```gherkin
Feature: LP Research Journey
  As a GP doing market research
  I want to explore the LP database
  So that I can understand the investor landscape

  Scenario: Research LPs before fund launch
    Given I am a GP planning a new fund
    And I want to understand potential investors

    # Step 1: Browse LP Database (M1)
    When I go to LP Search
    Then I see all available LPs
    And I can browse by type

    # Step 2: Filter by Criteria (M1)
    When I filter by:
      | Type | Endowment |
      | Strategy | Venture Capital |
      | Geography | North America |
    Then I see relevant LPs

    # Step 3: Semantic Search (M2)
    When I search "investors interested in deep tech and AI"
    Then I see LPs matching that description
    And results are ranked by relevance

    # Step 4: Save Search (M1)
    When I click "Save Search"
    And I name it "DeepTech Endowments"
    Then my search is saved
    And I can reload it anytime

    # Step 5: View LP Details (M1)
    When I click on an interesting LP
    Then I see full profile:
      | Organization details |
      | Investment mandate |
      | Check sizes |
      | Contact information |
      | Historical commitments |

    # Step 6: Export for Analysis (M1)
    When I select 20 LPs
    And I click "Export CSV"
    Then I download a spreadsheet
    And I can analyze in Excel

    # Step 7: Create Shortlist (M3)
    When I identify 10 target LPs
    And I add them to a shortlist
    Then I have a saved list
    And I can use it when my fund is ready
```

---

## Journey 3: Fundraising Campaign

```gherkin
Feature: Fundraising Campaign Journey
  As a GP raising a fund
  I want to systematically contact LPs
  So that I can efficiently raise capital

  Scenario: Run a fundraising campaign
    Given I have an active fund profile
    And I have 50 matched LPs

    # Step 1: Review and Prioritize (M3)
    When I view my matches
    Then I see LPs ranked by score
    When I review the top 20
    And I add them to my shortlist
    Then I have a prioritized list

    # Step 2: Tier 1 Outreach (M4)
    When I select my top 5 LPs
    For each LP:
      When I generate executive summary
      And I customize it slightly
      And I download PDF

      When I generate outreach email
      And I select appropriate tone
      And I personalize the opening
      And I copy to clipboard

      When I send from my email client
      And I attach the summary PDF
      Then outreach is complete

    When I mark all 5 as "Contacted"
    Then my dashboard shows 5 contacted

    # Step 3: Track Responses (M3)
    Over the next week:
      When LP responds positively
      Then I update status to "Interested"

      When LP declines
      Then I update status to "Passed"
      And I note the reason

    # Step 4: Tier 2 Outreach (M4)
    When I've contacted Tier 1
    And I start Tier 2 (next 10 LPs)
    Then I repeat the outreach process
    And I adjust approach based on learnings

    # Step 5: Review Campaign (M3)
    After 30 days:
      When I view my campaign stats
      Then I see:
        | Contacted | 15 |
        | Interested | 5 |
        | In Meetings | 3 |
        | Passed | 7 |
      And I can see which messages worked best
```

---

## Journey 4: Data Import and Setup

```gherkin
Feature: Platform Data Setup Journey
  As a platform admin
  I want to import and clean LP data
  So that the database is ready for users

  Scenario: Initial data load
    Given I am a super admin
    And I have an LP spreadsheet with 1,000 records

    # Step 1: Upload Data (M0)
    When I go to Admin > Import
    And I upload "lp_database.xlsx"
    Then file is accepted

    # Step 2: Map Columns (M0)
    When I map columns to LP fields:
      | Investor Name | name |
      | Type | type |
      | AUM ($B) | total_aum_bn |
      | Strategies | strategies |
    Then mapping is saved

    # Step 3: Preview and Validate (M0)
    When I view the preview
    Then I see:
      | Total Rows | 1,000 |
      | Valid | 950 |
      | Errors | 30 |
      | Duplicates | 20 |

    # Step 4: Fix Critical Errors (M0)
    When I view errors
    And I fix the ones I can
    And I skip unfixable rows
    Then error count decreases

    # Step 5: Approve Import (M0)
    When I click "Approve & Import"
    Then import runs
    And 950 LPs are imported

    # Step 6: Cleaning Pipeline (M0)
    When the cleaning pipeline runs:
      Then strategies are normalized
      And geographies are standardized
      And types are cleaned
    And I see "Cleaning complete"

    # Step 7: Generate Embeddings (M2)
    When embedding generation runs:
      Then each LP mandate gets a vector
    And semantic search becomes available

    # Step 8: Quality Review (M0)
    When I view the review queue
    Then I see 45 low-quality LPs
    When I process the queue
    Then data quality improves

    # Step 9: Verify Ready (M1)
    When I check database stats
    Then I see:
      | Total LPs | 950 |
      | Avg Quality | 72% |
      | With Embeddings | 900 |
    And the platform is ready for users
```

---

## Journey 5: Match to Investment

```gherkin
Feature: Full Investment Journey
  As a GP
  I want to track an LP from match to commitment
  So that I can manage my fundraising

  Scenario: From first match to LP commitment
    # Discovery (M3)
    Given I generated matches
    When I find "CalPERS" with score 92
    Then I add to shortlist

    # First Outreach (M4)
    When I generate email for CalPERS
    And I send from my email
    Then status is "Contacted"

    # Response (M3)
    When CalPERS responds with interest
    Then I update status to "Interested"

    # First Meeting
    When I prepare for meeting
    And I generate briefing materials
    Then I have personalized talking points

    # Due Diligence
    When LP starts due diligence
    Then I update status to "Due Diligence"
    And I track their questions

    # Term Sheet
    When LP sends term sheet
    Then I update status to "Term Sheet"

    # Commitment
    When LP commits $50M
    Then I update status to "Committed"
    And I record commitment amount
    And this LP is a success!

    # Analytics (M5)
    When I view my funnel
    Then I see:
      | Stage | Count |
      | Contacted | 30 |
      | Interested | 12 |
      | Due Diligence | 5 |
      | Committed | 2 |
    And I can see my conversion rates
```

---

## Journey 6: Multi-Fund Management

```gherkin
Feature: Multi-Fund Management Journey
  As a GP with multiple funds
  I want to manage all my fundraising
  So that I stay organized

  Scenario: Managing multiple active funds
    Given I am at a firm with 3 funds:
      | Fund | Status | Stage |
      | Fund III | Active | Raising |
      | Fund II | Active | Investing |
      | Fund I | Closed | Divesting |

    # Dashboard Overview (M1)
    When I view my dashboard
    Then I see all 3 funds
    And I see quick stats for each

    # Fund III Fundraising (M3)
    When I select Fund III
    Then I see:
      | Matches | 45 |
      | Shortlisted | 20 |
      | Contacted | 15 |
      | Committed | 3 |
    And I can continue outreach

    # Switch Context (M1)
    When I switch to Fund II
    Then I see its specific matches
    And I see its specific LPs
    And outreach is separate

    # Team Collaboration (M1)
    When my colleague logs in
    Then they see the same funds
    And we can work on different LPs
    And changes sync in real-time

    # Company-Wide View (M5)
    When admin views company dashboard
    Then they see all funds
    And they see all team activity
    And they see aggregate metrics
```
