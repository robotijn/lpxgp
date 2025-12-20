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

  # ============================================
  # NEGATIVE TESTS: Missing Required Fields
  # ============================================

  Scenario: Attempt to publish without fund name
    Given I am creating a new fund
    And I have not entered a fund name
    When I click "Publish"
    Then I see error "Fund Name is required"
    And the fund remains in draft status

  Scenario: Attempt to publish without target size
    Given I am creating a new fund
    And I entered fund name "Growth Fund III"
    But I have not entered target size
    When I click "Publish"
    Then I see error "Target Size is required"
    And a list of missing required fields is shown

  Scenario: Attempt to publish without strategy
    Given I am creating a new fund
    And I entered basic information
    But I have not selected a strategy
    When I click "Publish"
    Then I see error "Strategy is required for matching"
    And the strategy section is highlighted

  Scenario: Attempt to publish without geographic focus
    Given I am creating a new fund
    And I have not selected any geographic focus
    When I click "Publish"
    Then I see error "At least one geographic focus is required"

  Scenario: Show all missing required fields at once
    Given I am creating a new fund
    And I have not filled any required fields
    When I click "Publish"
    Then I see a summary of all missing required fields:
      | Field | Status |
      | Fund Name | Missing |
      | Target Size | Missing |
      | Strategy | Missing |
      | Geographic Focus | Missing |
    And I can click each field to navigate to it

  # ============================================
  # NEGATIVE TESTS: Invalid Fund Data
  # ============================================

  Scenario: Negative target size rejected
    Given I am creating a new fund
    When I enter target size "-$100M"
    Then I see error "Target size must be a positive number"
    And the field is highlighted red

  Scenario: Zero target size rejected
    Given I am creating a new fund
    When I enter target size "$0"
    Then I see error "Target size must be greater than zero"

  Scenario: Target size exceeds hard cap
    Given I am creating a new fund
    When I enter:
      | Field | Value |
      | Target Size | $300M |
      | Hard Cap | $250M |
    Then I see error "Target size cannot exceed hard cap"

  Scenario: Negative check size rejected
    When I enter investment parameters:
      | Check Size Min | -$5M |
    Then I see error "Check size must be a positive number"

  Scenario: Check size min exceeds max
    When I enter investment parameters:
      | Check Size Min | $50M |
      | Check Size Max | $30M |
    Then I see error "Minimum check size cannot exceed maximum"

  Scenario: Invalid vintage year
    When I enter vintage year "1850"
    Then I see error "Vintage year must be between 1950 and 2030"

  Scenario: Future vintage year too far ahead
    When I enter vintage year "2099"
    Then I see error "Vintage year cannot be more than 5 years in the future"

  Scenario: Invalid strategy selection
    When I select strategy "Unknown Strategy"
    Then I see error "Please select a valid strategy from the list"

  Scenario: Management fee out of range
    When I enter management fee "15%"
    Then I see warning "Management fee of 15% is unusually high. Please confirm."

  Scenario: Carried interest exceeds 100%
    When I enter carried interest "150%"
    Then I see error "Carried interest must be between 0% and 100%"

  Scenario: Negative IRR in track record
    When I add track record entries:
      | Fund | Vintage | Size | Net IRR | TVPI |
      | Fund I | 2016 | $75M | -50% | 0.5x |
    Then the entry is saved (negative IRR is valid for underperforming funds)
    And a warning is shown "Negative IRR will impact matching scores"

  Scenario: Invalid TVPI in track record
    When I add track record entries:
      | Fund | Vintage | Size | Net IRR | TVPI |
      | Fund I | 2016 | $75M | 25% | -1.0x |
    Then I see error "TVPI must be a positive number"

  Scenario: Investment thesis too short
    When I write my investment thesis:
      """
      We invest.
      """
    Then I see warning "Investment thesis is very short. Consider adding more detail for better matching."

  Scenario: Investment thesis too long
    When I write an investment thesis longer than 10,000 characters
    Then I see error "Investment thesis must be under 10,000 characters"
    And character count is displayed
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

  # ============================================
  # NEGATIVE TESTS: Deck Upload Failures
  # ============================================

  Scenario: Upload corrupt PDF file
    Given I am on fund creation page
    When I upload "corrupt_deck.pdf" that is malformed
    Then I see error "File appears to be corrupted or invalid"
    And I am prompted to upload a different file
    And the corrupt file is not stored

  Scenario: Upload corrupt PPTX file
    When I upload "broken_presentation.pptx" with invalid structure
    Then I see error "Unable to read PPTX file. The file may be corrupted."
    And processing does not begin

  Scenario: Upload password-protected PDF
    When I upload a password-protected PDF
    Then I see error "Password-protected files are not supported"
    And I am prompted to upload an unprotected version

  Scenario: Upload encrypted PPTX
    When I upload an encrypted PPTX file
    Then I see error "Encrypted files cannot be processed"

  Scenario: Upload empty PDF
    When I upload an empty PDF (0 pages)
    Then I see error "The uploaded file contains no pages"

  Scenario: Upload PDF with no extractable text
    When I upload a PDF that is entirely scanned images
    Then I see warning "Limited text found. Extraction results may be incomplete."
    And OCR processing is attempted

  Scenario: Upload file exactly at size limit
    When I upload a 100MB file
    Then the file uploads successfully
    And processing begins normally

  Scenario: Upload file just over size limit
    When I upload a 100.1MB file
    Then I see "File exceeds 100MB limit"
    And upload is rejected

  Scenario: Network interruption during upload
    Given I am uploading a large file
    When the network connection is interrupted
    Then I see error "Upload failed. Please check your connection and try again."
    And I can retry the upload
    And partial uploads are cleaned up

  Scenario: Upload timeout
    Given I am uploading a file
    When the upload takes longer than 5 minutes
    Then I see error "Upload timed out. Please try again."
    And I can retry with smaller file recommendation

  Scenario: Simultaneous deck uploads
    Given I am uploading "deck1.pdf"
    When I try to upload "deck2.pdf" before the first completes
    Then I see "Please wait for current upload to complete"

  Scenario: Storage quota exceeded
    Given my company has used all storage allocation
    When I try to upload a new deck
    Then I see error "Storage quota exceeded. Please delete old decks or contact support."

  Scenario: Supabase Storage unavailable
    Given Supabase Storage is temporarily unavailable
    When I try to upload a deck
    Then I see error "Storage service temporarily unavailable. Please try again in a few minutes."
    And the error is logged for monitoring

  Scenario: Unsupported PDF version
    When I upload a PDF using version 2.0 features not supported
    Then I see error "PDF version not supported. Please save as PDF 1.7 or earlier."

  Scenario: Upload file with wrong extension
    When I upload "fake_pdf.pdf" that is actually a renamed JPEG
    Then I see error "File content does not match file type"
    And upload is rejected

  Scenario: Upload extremely large page count
    When I upload a PDF with 500 pages
    Then I see warning "Large document detected. Processing may take several minutes."
    And only first 100 pages are processed
    And I am notified of the truncation
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

  # ============================================
  # NEGATIVE TESTS: AI Extraction Failures
  # ============================================

  Scenario: Unreadable deck content
    Given I uploaded a deck with poor quality scanned images
    When AI processes the deck
    Then I see warning "Unable to extract readable text from document"
    And I am prompted to enter fields manually
    And extraction result shows "Manual entry required"

  Scenario: Deck in unsupported language
    Given I uploaded a deck entirely in Japanese
    When AI processes the deck
    Then I see "Document language not supported for extraction"
    And I am offered manual entry option

  Scenario: Mixed language deck partial extraction
    Given I uploaded a deck with English and German content
    When AI processes the deck
    Then English sections are extracted
    And German sections show "Could not extract - non-English content"

  Scenario: AI service unavailable
    Given OpenRouter API is temporarily unavailable
    When AI tries to process my deck
    Then I see error "AI extraction service temporarily unavailable"
    And I can retry later or enter fields manually
    And my uploaded deck is preserved

  Scenario: AI service timeout
    Given I uploaded a complex 50-page deck
    When AI processing takes longer than 2 minutes
    Then I see "Processing is taking longer than expected"
    And I can choose to wait or switch to manual entry
    And processing continues in background

  Scenario: AI extraction returns invalid data
    Given AI extracts target_size as "approximately two hundred"
    When validation runs on extracted data
    Then target_size is marked as "Could not parse - please enter manually"
    And confidence is set to 0%

  Scenario: AI extracts conflicting information
    Given my deck mentions "$200M" on page 1 and "$250M" on page 5
    When AI processes the deck
    Then it shows both values with locations:
      | Field | Value 1 | Location 1 | Value 2 | Location 2 |
      | Target Size | $200M | Page 1 | $250M | Page 5 |
    And I must select which value is correct

  Scenario: All fields low confidence
    Given I uploaded a very minimal deck
    When AI completes extraction
    And all fields have confidence < 50%
    Then I see warning "Extraction confidence is low. Manual review strongly recommended."
    And all fields are highlighted yellow

  Scenario: AI hallucinates non-existent information
    Given my deck does not mention ESG
    When AI extracts esg_policy = "Strong ESG commitment"
    But the deck text is analyzed and contains no ESG references
    Then esg_policy is flagged as "Possible extraction error"
    And confidence is reduced to 0%

  Scenario: Extraction partially fails
    Given AI successfully extracts 5 of 10 fields
    When extraction completes with errors for remaining fields
    Then I see partial results with:
      | Field | Status |
      | Fund Name | Extracted |
      | Target Size | Extracted |
      | Strategy | Error - retry available |
      | Track Record | Error - manual entry needed |
    And I can retry failed fields individually

  Scenario: Rate limiting from AI provider
    Given my company has made many extraction requests
    When AI processing is rate limited
    Then I see "Processing queued. Estimated wait: 5 minutes"
    And extraction runs when quota resets
    And I receive notification when complete

  Scenario: Deck content extraction succeeds but parsing fails
    Given AI extracts raw text successfully
    When structured parsing fails
    Then I see extracted raw text
    And fields show "Could not structure - please enter manually"
    And I can copy text from extraction to help fill forms

  Scenario: Very old deck format
    Given I uploaded a deck from 2005 with outdated formatting
    When AI processes the deck
    Then extraction attempts proceed
    And I see warning "Older document format - extraction may be less accurate"

  Scenario: Deck with no fund information
    Given I uploaded a marketing brochure instead of pitch deck
    When AI processes the deck
    Then I see "No fund information detected in document"
    And I am prompted to upload actual pitch deck
    And no fields are populated
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

  # ============================================
  # NEGATIVE TESTS: Editing Edge Cases
  # ============================================

  Scenario: Edit published fund requires confirmation
    Given I have a published fund
    When I try to edit target_size
    Then I see warning "Editing a published fund will notify LPs who have viewed it"
    And I must confirm before changes are saved

  Scenario: Concurrent edit conflict
    Given colleague A is editing the fund
    When colleague B also opens the fund for editing
    And both save changes
    Then the second save shows "Fund was modified by colleague A"
    And B must review changes before saving

  Scenario: Auto-save fails silently
    Given I am editing a fund
    When network becomes unavailable
    And auto-save triggers
    Then I see warning "Unable to save draft. Your changes are preserved locally."
    And changes are stored locally
    And I can manually save when network returns

  Scenario: Navigate away with unsaved changes
    Given I have unsaved changes
    When I try to navigate away
    Then I see "You have unsaved changes. Discard?"
    And I can choose to stay, save, or discard

  Scenario: Edit fund that was deleted
    Given my colleague deleted the fund
    When I try to save my edits
    Then I see error "This fund no longer exists"
    And I am offered to create a new fund with my data

  Scenario: Validation error during edit
    Given I am editing a published fund
    When I change target_size to "-$50M"
    Then I see inline error "Target size must be positive"
    And the Save button is disabled
    And other valid changes are preserved
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

  # ============================================
  # NEGATIVE TESTS: No Matching Results
  # ============================================

  Scenario: No LPs match any criteria
    Given my fund strategy is "Crypto Venture"
    And no LPs in database invest in Crypto
    When hard filters run
    Then I see "No matching LPs found"
    And I am shown suggestions:
      | Suggestion |
      | "Consider broadening your strategy selection" |
      | "Check if your fund size is too small/large" |

  Scenario: No LPs match geographic focus
    Given my fund focuses exclusively on "Antarctica"
    When hard filters run
    Then I see "No LPs found for your geographic focus"
    And I am shown LP distribution by geography

  Scenario: Fund size outside all LP ranges
    Given my fund target is $5M (very small)
    And all LPs require minimum $50M
    When hard filters run
    Then I see "No LPs accept funds of this size"
    And I see "Smallest LP minimum: $50M"

  Scenario: Very restrictive criteria yields no matches
    Given I have multiple restrictive criteria:
      | Criterion | Value |
      | Strategy | Rare Strategy |
      | Geography | Small Country |
      | Size | Unusual Range |
    When hard filters run
    Then I see "Your criteria combination has no matches"
    And I see which criterion is most restrictive
    And I can relax criteria one by one

  # ============================================
  # NEGATIVE TESTS: Matching Timeout
  # ============================================

  Scenario: Hard filter timeout
    Given there are 1,000,000 LPs to filter
    And system is under heavy load
    When hard filters run for more than 10 seconds
    Then I see "Matching is taking longer than expected"
    And I can wait or cancel
    And partial results are not shown

  Scenario: Database connection timeout during matching
    Given database is slow to respond
    When hard filters query times out
    Then I see error "Unable to complete matching. Please try again."
    And I can retry matching

  Scenario: Matching cancelled by user
    Given matching is in progress
    When I click "Cancel"
    Then matching stops
    And I see "Matching cancelled"
    And no partial results are saved

  # ============================================
  # NEGATIVE TESTS: Invalid Fund Data for Matching
  # ============================================

  Scenario: Attempt matching with draft fund
    Given my fund is in draft status
    When I try to generate matches
    Then I see error "Please publish your fund before generating matches"
    And matching does not run

  Scenario: Attempt matching with incomplete required fields
    Given my fund is missing strategy
    When I try to generate matches
    Then I see error "Cannot match without strategy defined"
    And I am directed to complete fund profile

  Scenario: Fund with invalid size cannot match
    Given my fund somehow has target_size = 0
    When I try to generate matches
    Then I see error "Invalid fund size. Please update your fund profile."
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

  # ============================================
  # NEGATIVE TESTS: Invalid Score Ranges
  # ============================================

  Scenario: Score cannot exceed 100
    Given all scoring factors return maximum values
    When total score is calculated
    Then total score is exactly 100
    And score is not 105 or higher

  Scenario: Score cannot be negative
    Given scoring factors return minimum or zero values
    When total score is calculated
    Then total score is at least 0
    And score is not -5 or lower

  Scenario: Handle missing scoring factor data
    Given an LP has no sector information
    When soft scoring runs
    Then sector overlap score defaults to 50
    And a note indicates "LP sector data unavailable"
    And other factors score normally

  Scenario: Handle all factors missing
    Given an LP passed hard filters but has minimal data
    When soft scoring runs
    Then all factors default to 50
    And total score is 50
    And LP is flagged as "Limited data available"

  Scenario: Weight configuration sums to more than 100%
    Given an admin sets weights:
      | Factor | Weight |
      | Sector | 30% |
      | Size | 30% |
      | Track Record | 30% |
      | ESG | 30% |
      | Semantic | 30% |
    When trying to save
    Then I see error "Weights must sum to 100%"
    And configuration is not saved

  Scenario: Weight configuration sums to less than 100%
    Given an admin sets total weights to 80%
    When trying to save
    Then I see error "Weights must sum to 100%"

  Scenario: Negative weight rejected
    Given an admin tries to set Sector weight to -10%
    Then I see error "Weights must be positive numbers"

  Scenario: Invalid minimum threshold
    Given I set minimum threshold to 150
    Then I see error "Threshold must be between 0 and 100"

  Scenario: Threshold set to 100 yields no results
    Given minimum threshold is 100
    And no LP has a perfect score
    When scoring completes
    Then I see "No LPs meet your threshold of 100"
    And I am suggested to lower threshold

  # ============================================
  # NEGATIVE TESTS: Scoring Calculation Edge Cases
  # ============================================

  Scenario: Division by zero in size fit calculation
    Given LP has size range $0 - $0
    When size fit is calculated
    Then calculation handles edge case gracefully
    And size fit score defaults to 0
    And error is logged for data quality review

  Scenario: Very large numbers in calculations
    Given fund target is $999,999,999,999
    When scoring calculations run
    Then calculations complete without overflow
    And scores remain in 0-100 range

  Scenario: Floating point precision in score calculation
    Given calculated score is 74.999999999
    When score is displayed
    Then score shows as 75
    And ranking uses full precision internally
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

  # ============================================
  # NEGATIVE TESTS: Embedding Service Failures
  # ============================================

  Scenario: Voyage AI unavailable during fund publish
    Given I am publishing a fund
    When Voyage AI service is unavailable
    Then fund is still published
    And I see warning "Semantic matching temporarily unavailable"
    And embedding generation is queued for retry
    And matching can proceed with other factors only

  Scenario: Voyage AI timeout
    Given thesis is being embedded
    When Voyage AI takes longer than 30 seconds
    Then timeout occurs
    And embedding is queued for retry
    And user is notified when complete

  Scenario: Voyage AI rate limit exceeded
    Given many embeddings are being generated
    When rate limit is hit
    Then requests are queued
    And I see "Processing queued. Please check back in a few minutes."

  Scenario: Embedding generation fails completely
    Given thesis: "..." (very short text)
    When Voyage AI fails to generate embedding
    Then I see warning "Could not generate semantic embedding"
    And semantic score is excluded from matching
    And other scores are weighted higher

  Scenario: Corrupt or invalid embedding stored
    Given an LP has a malformed embedding in database
    When similarity calculation is attempted
    Then error is caught gracefully
    And LP gets default semantic score of 50
    And error is logged for data quality review

  Scenario: Embedding dimension mismatch
    Given fund embedding has 1024 dimensions
    And LP embedding has 768 dimensions (old format)
    When similarity is calculated
    Then incompatibility is detected
    And LP embedding is regenerated
    Or default score is used

  # ============================================
  # NEGATIVE TESTS: Semantic Calculation Edge Cases
  # ============================================

  Scenario: Empty thesis text
    Given fund thesis is empty string
    When I try to generate embedding
    Then I see error "Investment thesis is required for semantic matching"
    And embedding is not generated

  Scenario: Thesis with only special characters
    Given fund thesis is "$$$ ### @@@"
    When embedding is generated
    Then low-quality embedding warning is shown
    And semantic matching may be unreliable

  Scenario: Very long thesis text
    Given thesis exceeds Voyage AI token limit
    When embedding is generated
    Then thesis is truncated to limit
    And I see "Thesis truncated for embedding - consider shortening"

  Scenario: Non-English thesis
    Given thesis is in French
    When embedding is generated
    Then embedding is generated (Voyage supports multilingual)
    But matching may be less accurate with English LP mandates
    And warning is shown about language mismatch

  Scenario: All cosine similarities are identical
    Given fund thesis is very generic
    When compared to all LP mandates
    And all return similarity of ~0.5
    Then semantic scores are all 50
    And I see "Thesis may be too generic for meaningful semantic matching"
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

  # ============================================
  # NEGATIVE TESTS: Explanation Generation Failures
  # ============================================

  Scenario: AI unavailable for explanation
    Given I click "Why this match?"
    When OpenRouter is unavailable
    Then I see error "Unable to generate explanation at this time"
    And I can view score breakdown instead
    And I can retry later

  Scenario: Explanation generation timeout
    Given explanation is being generated
    When it takes longer than 30 seconds
    Then I see "Generation is taking longer than expected"
    And I can wait or cancel

  Scenario: Insufficient data for meaningful explanation
    Given LP has minimal profile information
    When I request explanation
    Then I see "Limited LP data available for explanation"
    And explanation is basic/generic
    And score breakdown is emphasized

  Scenario: Explanation cache expired
    Given cached explanation is 30 days old
    When I view the explanation
    Then I see "Explanation may be outdated"
    And "Refresh" button is highlighted

  Scenario: AI generates inappropriate content
    Given AI explanation contains errors or inappropriate content
    When content moderation catches it
    Then explanation is blocked
    And generic fallback is shown
    And incident is logged

  Scenario: Explanation generation rate limited
    Given I requested many explanations quickly
    When I request another
    Then I see "Please wait before requesting more explanations"
    And cooldown time is shown
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

  # ============================================
  # NEGATIVE TESTS: Feedback Edge Cases
  # ============================================

  Scenario: Cannot submit empty feedback reason
    Given I click thumbs down
    When I try to submit without selecting a reason
    Then I see "Please select a reason"
    And feedback is not saved

  Scenario: Duplicate feedback ignored
    Given I already gave thumbs up to LP A
    When I click thumbs up again
    Then no duplicate is created
    And feedback count remains the same

  Scenario: Change feedback from positive to negative
    Given I previously gave thumbs up
    When I click thumbs down
    Then feedback is updated to negative
    And I am asked for a reason
    And old positive feedback is replaced

  Scenario: Feedback storage fails
    Given I submit feedback
    When database write fails
    Then I see error "Could not save feedback. Please try again."
    And my feedback is preserved for retry
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

  # ============================================
  # NEGATIVE TESTS: Selection Edge Cases
  # ============================================

  Scenario: Add already shortlisted LP
    Given LP A is already in my shortlist
    When I try to add LP A again from matches
    Then I see "LP A is already in your shortlist"
    And duplicate is not created

  Scenario: Shortlist limit reached
    Given I have 100 LPs in shortlist (maximum)
    When I try to add another LP
    Then I see "Shortlist limit reached. Please remove LPs before adding more."

  Scenario: Bulk add exceeds limit
    Given I have 95 LPs in shortlist
    When I try to bulk add 10 LPs
    Then I see "Can only add 5 more LPs. Please select fewer or remove from shortlist."

  Scenario: Remove last LP from shortlist
    Given I have 1 LP in shortlist
    When I remove that LP
    Then shortlist is empty
    And I see "Your shortlist is empty. Add matches to get started."

  Scenario: LP removed from system after shortlisting
    Given I shortlisted LP A
    And LP A is later removed from database
    When I view my shortlist
    Then I see "LP A (No longer available)"
    And I can remove the stale entry
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

  # ============================================
  # NEGATIVE TESTS: Confirmation Edge Cases
  # ============================================

  Scenario: Confirm with required fields still missing
    Given AI extracted data
    But management_fee is still missing
    When I click "Confirm and Save"
    Then I see "Please fill in all required fields"
    And missing fields are highlighted
    And save is blocked

  Scenario: Session timeout during confirmation
    Given I am on confirmation screen
    When my session expires (30 minutes inactive)
    Then I see "Session expired. Please log in again."
    And my extracted data is preserved for 1 hour
    And I can continue after logging in

  Scenario: Browser crash during confirmation
    Given I was reviewing extracted fields
    When browser crashes and I return
    Then my extraction is recoverable
    And I see "Recover unsaved extraction?"

  Scenario: Edit creates invalid data
    Given I am editing extracted fund_name
    When I change it to empty string
    Then I see "Fund name is required"
    And I cannot proceed

  Scenario: Confirm extraction for already-confirmed fund
    Given I already confirmed this extraction
    When I try to confirm again (duplicate request)
    Then I see "Fund already created from this extraction"
    And I am redirected to the fund profile
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

  # ============================================
  # E2E NEGATIVE TESTS
  # ============================================

  Scenario: Complete journey with upload failure recovery
    Given I am logged in as a GP
    When I click "New Fund"
    And I upload a corrupt file
    Then I see error about corrupt file
    When I upload a valid deck
    Then processing begins normally
    And journey continues

  Scenario: Complete journey with extraction failure recovery
    Given I uploaded a valid deck
    When AI extraction fails
    Then I can enter fields manually
    When I complete manual entry
    And I publish the fund
    Then matching works normally

  Scenario: Complete journey with no matches
    Given I created and published a fund
    With very restrictive criteria
    When matching completes
    And no LPs match
    Then I see suggestions to broaden criteria
    When I edit fund to broaden criteria
    And run matching again
    Then matches are found

  Scenario: Complete journey with service degradation
    Given AI services are slow
    When I proceed through the journey
    Then I see appropriate loading indicators
    And timeouts are handled gracefully
    And I can complete the journey despite delays

  Scenario: Unauthorized access attempt during journey
    Given I am on the matching page
    When my session is invalidated
    And I try to add to shortlist
    Then I am redirected to login
    And my work is preserved where possible
```

---

## Error Handling Summary

```gherkin
Feature: Error Handling Across M3
  As a system
  I want to handle errors gracefully
  So that users have a good experience even when things go wrong

  # Database Errors
  Scenario: Database connection lost during fund save
    When database becomes unavailable
    Then user sees "Unable to save. Please try again."
    And data is preserved locally
    And retry is possible

  Scenario: Database constraint violation
    When unique constraint is violated
    Then user sees meaningful error "A fund with this name already exists"

  # API/External Service Errors
  Scenario: All external services unavailable
    When OpenRouter, Voyage AI, and Supabase are down
    Then user sees "Services temporarily unavailable"
    And monitoring is alerted
    And status page shows degradation

  # Rate Limiting
  Scenario: User rate limited
    When user makes too many requests
    Then they see "Please slow down. Try again in X seconds."
    And legitimate usage is not impacted

  # Data Validation
  Scenario: Malicious input attempt
    When user inputs script tags or SQL injection
    Then input is sanitized
    And validation error is shown
    And no security breach occurs

  # Concurrent Operations
  Scenario: Race condition in matching
    When two users run matching simultaneously
    Then both complete successfully
    And results are consistent
    And no data corruption occurs
```
