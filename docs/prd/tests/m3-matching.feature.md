# Milestone 3: Fund Profile + Matching Tests
## "See matching LPs for my fund"

---

## F-GP-01: Fund Profile Creation [P0]

```gherkin
Feature: Fund Profile Creation
  As a GP
  I want to create detailed fund profiles
  So that the system can find matching LPs

  # Sub-feature: Basic Information
  Scenario: Enter fund basics
    Given I am creating a new fund
    When I enter:
      | Field | Value |
      | Fund Name | Growth Fund III |
      | Fund Number | 3 |
      | Vintage Year | 2024 |
      | Target Size | $200M |
      | Hard Cap | $250M |
    Then the basic information is saved

  # Sub-feature: Strategy Details
  Scenario: Define investment strategy
    When I select strategy details:
      | Field | Value |
      | Strategy | Private Equity |
      | Sub-strategy | Growth |
      | Geographic Focus | North America, Europe |
      | Sector Focus | Technology, Healthcare |
    Then the strategy is defined

  # Sub-feature: Investment Parameters
  Scenario: Set investment parameters
    When I enter investment parameters:
      | Field | Value |
      | Check Size Min | $10M |
      | Check Size Max | $30M |
      | Target Companies | 15-20 |
      | Holding Period | 5-7 years |
    Then parameters are saved

  # Sub-feature: Track Record
  Scenario: Add track record
    When I add track record entries:
      | Fund | Vintage | Size | Net IRR | TVPI |
      | Fund II | 2020 | $150M | 25% | 1.8x |
      | Fund I | 2016 | $75M | 32% | 2.5x |
    Then track record is stored
    And summary metrics are calculated

  # Sub-feature: Terms
  Scenario: Enter fund terms
    When I enter fund terms:
      | Field | Value |
      | Management Fee | 2.0% |
      | Carried Interest | 20% |
      | Hurdle Rate | 8% |
      | GP Commitment | 2% |
      | Fund Term | 10 years |
    Then terms are saved

  # Sub-feature: Investment Thesis
  Scenario: Write investment thesis
    When I write my investment thesis:
      """
      We invest in growth-stage technology companies
      in North America and Europe. We focus on B2B SaaS,
      fintech, and healthcare technology. Our sweet spot
      is $10-30M checks in companies with $5-20M ARR.
      """
    Then the thesis is saved
    And it will be used for semantic matching

  # Sub-feature: Draft vs Published
  Scenario: Save as draft
    Given I am creating a fund
    When I click "Save Draft"
    Then the fund is saved with status "draft"
    And I can continue editing later

  Scenario: Publish fund
    Given I have a complete fund profile
    When I click "Publish"
    Then fund status changes to "active"
    And I can generate matches
```

---

## F-GP-02: Pitch Deck Upload [P0]

```gherkin
Feature: Pitch Deck Upload
  As a GP
  I want to upload my pitch deck
  So that I can quickly populate my fund profile

  # Sub-feature: File Upload
  Scenario: Upload PDF deck
    Given I am on fund creation page
    When I click "Upload Deck"
    And I select "growth_fund_iii.pdf" (15MB)
    Then the file uploads successfully
    And I see "Processing deck..."

  Scenario: Upload PPTX deck
    When I upload "pitch_deck.pptx"
    Then the file is accepted
    And processing begins

  Scenario: File size validation
    When I try to upload a 150MB file
    Then I see "File exceeds 100MB limit"
    And upload is rejected

  Scenario: File type validation
    When I try to upload "document.docx"
    Then I see "Only PDF and PPTX are supported"

  # Sub-feature: Secure Storage
  Scenario: Deck stored securely
    When my deck is uploaded
    Then it is stored in Supabase Storage
    And only my company can access it
    And URL is signed and expires
```

---

## F-GP-03: AI Profile Extraction [P0]

```gherkin
Feature: AI Profile Extraction
  As a GP
  I want AI to extract fund info from my deck
  So that I don't manually enter everything

  # Sub-feature: Field Extraction
  Scenario: Extract fund name
    Given I uploaded a deck with "Growth Fund III" on title slide
    When AI processes the deck
    Then it extracts fund_name = "Growth Fund III"
    And shows confidence 95%

  Scenario: Extract target size
    Given my deck mentions "Targeting $200 million"
    When AI processes the deck
    Then it extracts target_size = 200
    And correctly interprets "million" as MM

  Scenario: Extract strategy
    Given my deck describes growth equity investing
    When AI processes the deck
    Then it extracts strategy = "Private Equity - Growth"
    And maps to our taxonomy

  Scenario: Extract team information
    Given my deck has a team slide with bios
    When AI processes the deck
    Then it extracts:
      | Name | Title |
      | John Smith | Managing Partner |
      | Jane Doe | Partner |

  Scenario: Extract track record
    Given my deck has a track record slide
    When AI processes the deck
    Then it extracts historical fund performance
    And structures it properly

  # Sub-feature: Confidence Scoring
  Scenario: High confidence extraction
    Given the deck clearly states "Target: $200M"
    When AI extracts target_size
    Then confidence is > 90%
    And field is highlighted green

  Scenario: Low confidence extraction
    Given the deck vaguely mentions "substantial fund"
    When AI tries to extract target_size
    Then confidence is < 50%
    And field is highlighted yellow
    And I am prompted to confirm/correct

  # Sub-feature: Missing Fields
  Scenario: Identify missing required fields
    Given my deck is missing management fee info
    When AI completes extraction
    Then it reports missing fields:
      | Field | Status |
      | Management Fee | Missing |
      | Hurdle Rate | Missing |
    And questionnaire prompts for these

  # Sub-feature: Human Confirmation
  Scenario: Review extracted fields
    Given AI extracted fund information
    When I view the confirmation screen
    Then I see all extracted fields
    And I can edit any value
    And I must click "Confirm" to proceed

  Scenario: Edit extracted value
    Given AI extracted fund_name = "Growth Equity Fund"
    When I edit it to "Growth Fund III"
    And I click "Confirm"
    Then the corrected value is saved

  Scenario: Reject extraction
    Given AI extracted incorrect information
    When I click "Start Over"
    Then extraction is discarded
    And I can upload a different deck
```

---

## F-GP-04: Fund Profile Editing [P0]

```gherkin
Feature: Fund Profile Editing
  As a GP
  I want to edit and update fund profiles
  So that information stays accurate

  # Sub-feature: Form Editing
  Scenario: Edit fund field
    Given I have an existing fund
    When I click "Edit"
    And I change target_size from $200M to $250M
    And I click "Save"
    Then the fund is updated

  Scenario: Form validation
    When I edit and enter invalid data
    Then I see inline validation errors
    And I cannot save until fixed

  # Sub-feature: Auto-save
  Scenario: Changes auto-save as draft
    When I am editing a fund
    And I make changes
    Then changes auto-save every 30 seconds
    And I see "Draft saved" indicator

  # Sub-feature: Version History
  Scenario: Track version history
    Given I edited the fund 3 times
    When I view version history
    Then I see 3 versions with:
      | Version | Date | Changed By |
      | v3 | Today | me |
      | v2 | Yesterday | colleague |
      | v1 | Last week | me |

  Scenario: View version diff
    When I compare v2 and v3
    Then I see what changed:
      | Field | v2 | v3 |
      | Target Size | $200M | $250M |
```

---

## F-MATCH-01: Hard Filter Matching [P0]

```gherkin
Feature: Hard Filter Matching
  As a matching engine
  I want to eliminate incompatible LPs
  So that only relevant LPs are scored

  # Sub-feature: Strategy Alignment
  Scenario: Strategy must align
    Given my fund strategy is "Private Equity - Growth"
    And LP A invests in "Private Equity, Private Equity - Growth"
    And LP B invests only in "Venture Capital"
    When hard filters run
    Then LP A passes
    And LP B is filtered out

  Scenario: Partial strategy match passes
    Given my fund is "Private Equity - Buyout"
    And LP invests in "Private Equity" (parent category)
    When hard filters run
    Then LP passes (parent includes buyout)

  # Sub-feature: Geography Alignment
  Scenario: Geography must overlap
    Given my fund focuses on "North America"
    And LP A prefers "North America, Europe"
    And LP B prefers only "Asia"
    When hard filters run
    Then LP A passes
    And LP B is filtered out

  # Sub-feature: Fund Size Range
  Scenario: Fund size must be in LP range
    Given my fund target is $200M
    And LP A accepts funds $100M - $500M
    And LP B accepts funds $500M - $2B
    When hard filters run
    Then LP A passes
    And LP B is filtered out (too small)

  # Sub-feature: Track Record Requirements
  Scenario: Meet track record minimums
    Given LP requires minimum 10 years track record
    And my team has 15 years experience
    When hard filters run
    Then LP passes

  Scenario: Fail track record requirement
    Given LP requires Fund III or later
    And this is my Fund II
    When hard filters run
    Then LP is filtered out

  # Sub-feature: Performance
  Scenario: Fast elimination
    Given there are 10,000 LPs
    When hard filters run
    Then filtering completes in < 100ms
    And only compatible LPs remain
```

---

## F-MATCH-02: Soft Scoring [P0]

```gherkin
Feature: Soft Scoring
  As a matching engine
  I want to rank LPs by fit quality
  So that best matches appear first

  # Sub-feature: Multi-factor Scoring
  Scenario: Calculate total score
    Given an LP passed hard filters
    When soft scoring runs
    Then total score is calculated from:
      | Factor | Weight |
      | Sector Overlap | 20% |
      | Size Fit | 20% |
      | Track Record Match | 20% |
      | ESG Alignment | 10% |
      | Semantic Similarity | 30% |

  # Sub-feature: Score Range
  Scenario: Score is 0-100
    When scoring any LP
    Then score is between 0 and 100

  # Sub-feature: Score Breakdown
  Scenario: Show score breakdown
    Given LP has total score 75
    When I view score breakdown
    Then I see:
      | Factor | Score | Contribution |
      | Sector Overlap | 80 | 16 |
      | Size Fit | 90 | 18 |
      | Track Record | 70 | 14 |
      | ESG | 50 | 5 |
      | Semantic | 73 | 22 |
      | Total | - | 75 |

  # Sub-feature: Configurable Weights
  Scenario: Adjust factor weights
    Given I am an admin
    When I change Semantic weight to 40%
    And I reduce others proportionally
    Then scores recalculate with new weights

  # Sub-feature: Minimum Threshold
  Scenario: Filter by minimum score
    Given minimum threshold is 50
    When scoring completes
    Then only LPs scoring 50+ appear in results
    And I can adjust threshold if needed
```

---

## F-MATCH-03: Semantic Matching [P0]

```gherkin
Feature: Semantic Matching
  As a matching engine
  I want to match fund thesis with LP mandate
  So that philosophically aligned LPs score higher

  # Sub-feature: Embedding Generation
  Scenario: Generate fund thesis embedding
    Given my fund has investment thesis:
      "Growth-stage B2B SaaS in fintech and healthcare"
    When I publish the fund
    Then a Voyage AI embedding is generated
    And stored with the fund profile

  Scenario: LP mandate embeddings exist
    Given LPs have mandate descriptions
    Then each LP has a pre-computed embedding
    And embeddings are indexed for fast search

  # Sub-feature: Similarity Calculation
  Scenario: Calculate semantic similarity
    Given my fund thesis embedding
    And an LP mandate embedding
    When similarity is calculated
    Then cosine similarity is computed
    And converted to 0-100 score

  Scenario: Similar theses score high
    Given my thesis: "AI-enabled healthcare companies"
    And LP mandate: "Technology investments in digital health"
    When semantic score is calculated
    Then score is > 80

  Scenario: Different theses score low
    Given my thesis: "AI-enabled healthcare companies"
    And LP mandate: "Core real estate in urban markets"
    When semantic score is calculated
    Then score is < 30

  # Sub-feature: Missing Mandate
  Scenario: Handle LP without mandate text
    Given an LP has no mandate_description
    When semantic matching runs
    Then semantic score defaults to 50
    And a note indicates "No mandate text available"
```

---

## F-MATCH-04: Match Explanations [P0]

```gherkin
Feature: Match Explanations
  As a GP
  I want to understand why an LP matched
  So that I can tailor my outreach

  # Sub-feature: Explanation Generation
  Scenario: Generate explanation
    Given an LP matched with score 85
    When I click "Why this match?"
    Then AI generates 2-3 paragraph explanation

  Scenario: Explanation content
    When I view an explanation
    Then it includes:
      - Key alignment points
      - Relevant LP history
      - Potential concerns or gaps
      - Suggested talking points

  # Sub-feature: Talking Points
  Scenario: Generate talking points
    Given a match explanation
    Then I see 3-5 bullet points like:
      - "Highlight your healthcare portfolio"
      - "Mention your ESG certification"
      - "Discuss your European expansion"

  # Sub-feature: Concerns
  Scenario: Identify potential concerns
    Given my fund is Fund II (less track record)
    And LP typically requires Fund III+
    When explanation is generated
    Then concerns include:
      "LP typically invests in Fund III+.
       Consider highlighting team's prior experience
       and strong Fund I performance."

  # Sub-feature: Caching
  Scenario: Cache explanations
    Given I generated an explanation for LP A
    When I view it again later
    Then the cached explanation loads instantly
    And I see "Generated on [date]"

  Scenario: Refresh explanation
    Given a cached explanation exists
    When I click "Refresh"
    Then a new explanation is generated
    And cache is updated
```

---

## F-MATCH-05: Match Feedback [P1]

```gherkin
Feature: Match Feedback
  As a GP
  I want to provide feedback on matches
  So that the system can improve

  # Sub-feature: Basic Feedback
  Scenario: Thumbs up/down
    Given I am viewing a match
    When I click thumbs up
    Then the match is marked as "positive feedback"

    When I click thumbs down
    Then the match is marked as "negative feedback"

  # Sub-feature: Detailed Feedback
  Scenario: Explain why not relevant
    When I click thumbs down
    Then I can select a reason:
      | "Already in contact" |
      | "Strategy mismatch" |
      | "Check size too small" |
      | "Geographic mismatch" |
      | "Other" |

  Scenario: Already in contact
    When I select "Already in contact"
    Then the match is marked appropriately
    And it won't appear in future suggestions

  # Sub-feature: Algorithm Improvement
  Scenario: Feedback improves future matches
    Given I provided feedback on 50 matches
    When the algorithm is retrained
    Then future matches incorporate my preferences
```

---

## F-HITL-02: Match Selection [P0]

```gherkin
Feature: Match Selection (Human-in-the-Loop)
  As a GP
  I want to explicitly approve matches
  So that I control my outreach

  # Sub-feature: Matches as Recommendations
  Scenario: View matches as suggestions
    When I generate matches
    Then I see a list of recommended LPs
    And they are not automatically added to outreach

  # Sub-feature: Shortlist
  Scenario: Add to shortlist
    Given I am viewing matches
    When I click "Add to Shortlist" on an LP
    Then the LP moves to my shortlist
    And I see "Added to shortlist" confirmation

  Scenario: Bulk add to shortlist
    Given I selected 5 LPs
    When I click "Add Selected to Shortlist"
    Then all 5 are added to shortlist

  # Sub-feature: Shortlist Management
  Scenario: View shortlist
    Given I have 10 LPs in my shortlist
    When I go to Shortlist
    Then I see all 10 LPs
    And I can remove LPs
    And I can generate pitches for them

  Scenario: Clear distinction
    When viewing LPs
    Then I clearly see which are:
      | "Matched" - AI recommended |
      | "Shortlisted" - I approved |
      | "Contacted" - I reached out |
```

---

## F-HITL-03: Fund Profile Confirmation [P0]

```gherkin
Feature: Fund Profile Confirmation (Human-in-the-Loop)
  As a GP
  I want to confirm AI-extracted data
  So that my profile is accurate

  # Sub-feature: Extraction Review
  Scenario: Review each field
    Given AI extracted 15 fields from my deck
    When I view the confirmation screen
    Then I see each field with:
      | Field | Extracted Value | Confidence | Action |
      | Fund Name | Growth III | 95% | ✓ Edit |
      | Target | $200M | 88% | ✓ Edit |
      | Strategy | PE Growth | 72% | ⚠ Review |

  Scenario: Low confidence highlighted
    Given a field has < 70% confidence
    Then it is highlighted yellow
    And marked "Please review"

  # Sub-feature: Required Fields
  Scenario: Show missing required fields
    Given AI could not extract management_fee
    Then that field shows as "Required - Please enter"
    And I cannot proceed until I fill it

  # Sub-feature: Explicit Approval
  Scenario: Must confirm before saving
    Given I reviewed all extracted fields
    When I click "Confirm and Save"
    Then the profile is created
    And audit trail shows AI vs manual fields

  Scenario: Cannot skip confirmation
    Given AI extracted data
    When I try to navigate away
    Then I see "Please confirm or discard extracted data"
```

---

## E2E: Fund Creation to Matching

```gherkin
Feature: Complete Fund to Match Journey
  As a GP
  I want to create a fund and find matches
  So that I can start fundraising

  Scenario: Upload deck, create fund, find matches
    Given I am logged in as a GP

    # Upload deck
    When I click "New Fund"
    And I upload "growth_fund_iii.pdf"
    Then I see processing indicator

    # Review extraction
    When extraction completes
    Then I see extracted fields:
      | Fund Name | Growth Fund III |
      | Target | $200M |
      | Strategy | PE Growth |
    And 2 fields need manual entry

    # Confirm and complete
    When I confirm extracted fields
    And I fill in missing fields
    And I write my investment thesis
    And I click "Publish"
    Then the fund is created and active

    # Generate matches
    When I click "Find Matching LPs"
    Then matching engine runs
    And I see "Analyzing 500 LPs..."

    When matching completes
    Then I see 45 matched LPs
    And they are ranked by score

    # Review matches
    When I view top match (score 92)
    Then I see:
      | LP Name | Score | Key Reasons |
      | CalPERS | 92 | Strategy, Size, ESG |
    And I can see full explanation

    # Shortlist
    When I add top 10 to shortlist
    Then my shortlist has 10 LPs
    And I can generate pitches for them
```
