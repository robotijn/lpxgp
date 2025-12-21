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
    # Team members are stored as people records with fund_team links
    Given my deck has a team slide with bios
    When AI processes the deck
    Then it extracts team members:
      | Name | Title | Is Key Person |
      | John Smith | Managing Partner | Yes |
      | Jane Doe | Partner | Yes |
    And creates person records in global people table
    And creates fund_team links with roles

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

---

## Negative Tests: Additional Edge Cases

```gherkin
Feature: Additional Negative Test Scenarios
  As a system
  I want to handle edge cases and failures gracefully
  So that data integrity is maintained and users receive clear feedback

  # ============================================
  # @negative - Fund Profile Invalid State Transitions
  # ============================================

  @negative
  Scenario: Cannot transition from archived to active directly
    Given I have an archived fund
    When I try to publish the fund directly
    Then I see error "Archived funds must be restored to draft before publishing"
    And fund remains in archived state

  @negative
  Scenario: Cannot transition from draft to archived without explicit action
    Given I have a draft fund
    When I try to archive without saving
    Then I see warning "Unsaved changes will be lost. Continue?"
    And I must confirm before archiving

  @negative
  Scenario: Cannot unpublish a fund with active matches
    Given I have a published fund
    And the fund has 50 active matches
    When I try to change status to draft
    Then I see error "Cannot unpublish fund with active matches. Archive matches first."
    And fund remains published

  @negative
  Scenario: Invalid status value rejected
    Given I have a fund
    When API receives status = "invalid_status"
    Then API returns 400 Bad Request
    And error message is "Invalid status. Must be: draft, active, archived"

  @negative
  Scenario: Concurrent status changes cause conflict
    Given user A is changing fund status to archived
    And user B is changing fund status to active
    When both submit simultaneously
    Then one succeeds
    And the other sees "Fund status was changed by another user. Please refresh."
    And database maintains consistent state

  @negative
  Scenario: Cannot publish deleted fund
    Given a fund was soft-deleted
    When I try to publish via direct API call
    Then API returns 404 Not Found
    And error message is "Fund not found"

  @negative
  Scenario: Status transition with missing required fields fails
    Given I have a draft fund
    And investment_thesis is empty
    When I try to change status to active
    Then I see error "Cannot publish: investment_thesis is required"
    And fund remains in draft

  # ============================================
  # @negative - Match Calculation with Missing LP Data
  # ============================================

  @negative
  Scenario: LP missing all preference fields
    Given LP has no strategy, geography, or size preferences set
    When hard filters run
    Then LP is excluded from matching
    And LP is logged as "Insufficient data for matching"

  @negative
  Scenario: LP with null strategy array
    Given LP has strategy_preferences = null
    When hard filters run
    Then LP is excluded
    And matching continues for other LPs

  @negative
  Scenario: LP with empty strategy array
    Given LP has strategy_preferences = []
    When hard filters run
    Then LP is excluded
    And reason is logged "No strategy preferences defined"

  @negative
  Scenario: LP with corrupted size range data
    Given LP has min_fund_size = "not_a_number"
    When hard filters attempt to parse
    Then LP is excluded from matching
    And data quality error is logged
    And matching continues for valid LPs

  @negative
  Scenario: LP with inverted size range
    Given LP has min_fund_size = $500M and max_fund_size = $100M
    When hard filters run
    Then LP is excluded
    And data quality warning is logged "Invalid size range: min > max"

  @negative
  Scenario: LP with null geographic preferences
    Given LP has geographic_preferences = null
    When hard filters run for geography
    Then LP is excluded from geography filter
    And reason is "No geographic preferences set"

  @negative
  Scenario: LP deleted mid-matching
    Given matching is running for 1000 LPs
    And LP X is deleted during matching
    When matching reaches LP X
    Then LP X is skipped gracefully
    And matching continues
    And final results exclude LP X

  @negative
  Scenario: LP with missing mandate blocks semantic matching
    Given LP has no mandate_description
    And no mandate_embedding
    When semantic matching runs
    Then LP gets default semantic score of 50
    And explanation notes "Semantic matching unavailable - no mandate text"

  @negative
  Scenario: Partial LP data allows partial scoring
    Given LP has:
      | Field | Value |
      | strategy_preferences | ["Private Equity"] |
      | geographic_preferences | null |
      | size_range | valid |
    When matching runs
    Then LP passes strategy filter
    And LP is excluded by geography (null = no preference data)
    Or system uses "global" as default if configured

  # ============================================
  # @negative - Concurrent Fund Edits
  # ============================================

  @negative
  Scenario: Optimistic locking prevents lost updates
    Given user A loaded fund at version 5
    And user B loaded fund at version 5
    When user A saves changes (becomes version 6)
    And user B tries to save changes
    Then user B sees "Fund was modified. Your version: 5, Current: 6"
    And user B must reload before saving

  @negative
  Scenario: Concurrent edits to same field
    Given user A changes target_size to $200M
    And user B changes target_size to $300M
    When both submit within milliseconds
    Then database uses optimistic locking
    And second user sees merge conflict
    And audit log shows both attempts

  @negative
  Scenario: Concurrent edits to different fields
    Given user A changes target_size
    And user B changes fund_name
    When both submit
    Then first save succeeds
    And second save shows conflict warning
    And user B can choose to merge or overwrite

  @negative
  Scenario: Auto-save conflicts with manual save
    Given auto-save runs every 30 seconds
    And user manually clicks save at same moment
    When both requests arrive
    Then manual save takes precedence
    And auto-save is discarded
    And user sees "Saved successfully"

  @negative
  Scenario: Session A times out during long edit
    Given user A has unsaved changes for 45 minutes
    When session expires at 30 minutes
    And user A tries to save
    Then user sees "Session expired. Please log in."
    And changes are preserved in local storage
    And user can recover after login

  @negative
  Scenario: Multiple browser tabs editing same fund
    Given I have fund open in tabs A and B
    When I save in tab A
    Then tab B shows "Fund updated in another tab"
    And tab B offers to reload or continue editing

  @negative
  Scenario: Database deadlock during concurrent edits
    Given high contention on fund row
    When deadlock occurs
    Then one transaction retries automatically
    And user sees brief delay
    And save eventually succeeds
    And no data is lost

  # ============================================
  # @negative - AI Extraction Failures (Timeout, Parsing)
  # ============================================

  @negative
  Scenario: OpenRouter timeout during extraction
    Given I uploaded a deck for extraction
    When OpenRouter takes longer than 60 seconds
    Then extraction is cancelled
    And I see "Extraction timed out. The service may be busy."
    And options are:
      | Retry extraction |
      | Enter fields manually |
    And my uploaded deck is preserved

  @negative
  Scenario: OpenRouter returns malformed JSON
    Given AI extraction is processing
    When OpenRouter returns invalid JSON response
    Then parsing fails gracefully
    And I see "Could not parse extraction results"
    And raw response is logged for debugging
    And I can retry or enter manually

  @negative
  Scenario: OpenRouter returns empty response
    Given AI extraction is processing
    When OpenRouter returns 200 OK with empty body
    Then I see error "Extraction returned no data"
    And retry is available
    And fallback to manual entry is offered

  @negative
  Scenario: OpenRouter returns partial extraction
    Given deck has 10 extractable fields
    When OpenRouter returns only 3 fields
    Then I see partial results
    And missing fields show "Not extracted - please enter"
    And I can proceed with partial data

  @negative
  Scenario: OpenRouter rate limit (429) during extraction
    Given I submit extraction request
    When OpenRouter returns 429 Too Many Requests
    Then I see "AI service is busy. Queued for processing."
    And extraction retries after backoff
    And I receive notification when complete

  @negative
  Scenario: OpenRouter server error (500) during extraction
    Given I submit extraction request
    When OpenRouter returns 500 Internal Server Error
    Then I see "AI service temporarily unavailable"
    And automatic retry happens after 30 seconds
    And maximum 3 retries before giving up

  @negative
  Scenario: OpenRouter authentication failure
    Given OPENROUTER_API_KEY is invalid or expired
    When extraction is attempted
    Then I see "AI service configuration error"
    And admin is notified
    And manual entry is only option

  @negative
  Scenario: Extraction response validation fails
    Given OpenRouter returns:
      | Field | Value |
      | target_size | "banana" |
      | vintage_year | 9999 |
    When response is validated
    Then invalid fields are marked as "Could not validate - please enter"
    And valid fields are preserved
    And validation errors are shown inline

  @negative
  Scenario: Extraction response contains injection attempt
    Given OpenRouter returns field value containing "<script>alert('xss')</script>"
    When response is processed
    Then content is sanitized
    And script tags are removed
    And cleaned value is shown for review

  @negative
  Scenario: Network error during extraction
    Given extraction request is in flight
    When network connection drops
    Then I see "Network error. Please check connection and retry."
    And extraction state is preserved for retry
    And uploaded deck is not lost

  @negative
  Scenario: Extraction memory limit exceeded
    Given deck is extremely complex with many tables
    When parsing exceeds memory limit
    Then extraction fails gracefully
    And I see "Document too complex for automatic extraction"
    And simplified extraction is attempted
    Or manual entry is suggested

  # ============================================
  # @negative - Score Calculation Edge Cases
  # ============================================

  @negative
  Scenario: All scoring factors return zero
    Given LP has minimal overlap with fund:
      | Factor | Raw Score |
      | Sector Overlap | 0 |
      | Size Fit | 0 |
      | Track Record | 0 |
      | ESG | 0 |
      | Semantic | 0 |
    When total score is calculated
    Then total score is 0
    And LP appears at bottom of results
    And explanation notes "Very low compatibility"

  @negative
  Scenario: NaN in sector overlap calculation
    Given sector data causes division by zero
    When sector overlap score is calculated
    Then NaN is caught
    And sector score defaults to 0
    And error is logged "NaN in sector calculation for LP X"
    And total score calculation continues

  @negative
  Scenario: NaN in size fit calculation
    Given LP has max_fund_size = 0
    And calculation involves division by max
    When size fit is calculated
    Then NaN is prevented
    And size fit score is 0
    And warning is logged

  @negative
  Scenario: Infinity in score calculation
    Given calculation produces Infinity
    When score is processed
    Then Infinity is clamped to 100
    And warning is logged "Infinity in score calculation"
    And results remain valid

  @negative
  Scenario: Negative intermediate score
    Given weighted calculation produces -10
    When final score is computed
    Then negative is clamped to 0
    And score is valid
    And calculation method is reviewed

  @negative
  Scenario: Score exceeds 100 due to floating point
    Given weighted sum produces 100.0000001
    When final score is computed
    Then score is rounded to 100
    And display shows 100

  @negative
  Scenario: All factors have null data
    Given LP passed hard filters
    But has null for all soft scoring fields
    When soft scoring runs
    Then all factors default to 50
    And total score is 50
    And LP is flagged "Insufficient data for detailed scoring"

  @negative
  Scenario: Mixed null and valid factor data
    Given LP has:
      | Factor | Data |
      | Sector | valid |
      | Size | null |
      | Track Record | valid |
      | ESG | null |
      | Semantic | valid |
    When soft scoring runs
    Then valid factors score normally
    And null factors default to 50
    And explanation notes which factors used defaults

  @negative
  Scenario: Extremely small numbers in calculation
    Given sector overlap is 0.0000001
    When score is calculated and displayed
    Then score shows as 0
    And precision is maintained internally
    And no underflow occurs

  @negative
  Scenario: Score calculation timeout
    Given semantic similarity calculation is slow
    When calculation exceeds 5 second timeout
    Then semantic factor uses default 50
    And I see "Some scores used default values due to timeout"
    And other factors complete normally

  # ============================================
  # @negative - Orphaned Match Data After LP Deletion
  # ============================================

  @negative
  Scenario: LP deleted leaves orphaned matches
    Given fund A has matches with LP X, LP Y, LP Z
    When LP X is deleted from database
    Then fund A's match with LP X becomes orphaned
    And match record remains with lp_id pointing to deleted LP
    And orphan cleanup job runs nightly

  @negative
  Scenario: View matches with deleted LP
    Given I have a match with LP X
    And LP X was deleted
    When I view my matches
    Then I see "LP X (No longer available)"
    And score and explanation are still visible
    And I can remove the orphaned match

  @negative
  Scenario: Generate pitch for deleted LP
    Given I shortlisted LP X
    And LP X was deleted
    When I try to generate pitch for LP X
    Then I see error "LP no longer exists. Cannot generate pitch."
    And I am prompted to remove from shortlist

  @negative
  Scenario: Bulk operations with mixed valid/orphaned matches
    Given I have 10 shortlisted LPs
    And 2 have been deleted
    When I click "Generate all pitches"
    Then 8 pitches are generated successfully
    And I see "2 LPs could not be processed (no longer available)"
    And orphaned entries are highlighted

  @negative
  Scenario: Match explanation for deleted LP
    Given I have cached explanation for LP X
    And LP X was deleted
    When I view the explanation
    Then cached explanation is shown
    And I see warning "This LP is no longer in our database"
    And refresh is disabled

  @negative
  Scenario: Foreign key constraint on LP deletion
    Given database has foreign key from matches to LPs
    When LP X is deleted
    Then either:
      | CASCADE deletes related matches |
      | SET NULL marks matches as orphaned |
    And data integrity is maintained

  @negative
  Scenario: Orphan cleanup job handles large volumes
    Given 10,000 matches reference deleted LPs
    When nightly orphan cleanup runs
    Then orphans are cleaned in batches
    And database load is managed
    And cleanup completes within maintenance window

  @negative
  Scenario: LP restored after deletion
    Given LP X was soft-deleted
    And matches with LP X exist
    When LP X is restored
    Then matches become valid again
    And no data loss occurred
    And match scores may need recalculation

  @negative
  Scenario: Concurrent LP deletion and match creation
    Given GP is adding LP X to shortlist
    And admin is deleting LP X
    When both operations execute
    Then either:
      | Shortlist add fails with "LP not found" |
      | Shortlist add succeeds then becomes orphaned |
    And no database errors occur
    And state is consistent

  @negative
  Scenario: Reporting with orphaned data
    Given analytics include orphaned matches
    When I view matching statistics
    Then orphaned matches are excluded from active counts
    And historical data is preserved
    And report notes "X matches excluded (LP no longer available)"
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

---

## Batch Operations and Load Testing

```gherkin
Feature: Batch Matching Operations at Scale
  As a platform
  I want matching to perform well with large LP databases
  So that GPs get results quickly even with 100,000+ LPs

  # ==========================================================================
  # Match Generation for Large LP Databases
  # ==========================================================================

  Scenario: Match generation with 100,000 LPs
    Given the database contains 100,000 LPs
    And my fund is published with complete profile
    When I click "Find Matching LPs"
    Then matching completes within 30 seconds
    And I see progress updates:
      | Phase | Progress | Time |
      | Hard filtering | 100,000 LPs evaluated | ~5s |
      | Soft scoring | 2,500 candidates scored | ~15s |
      | Ranking | Top 500 selected | ~2s |
      | Complete | Results ready | ~25s total |

  Scenario: Hard filter performance with 100,000 LPs
    Given the database contains 100,000 LPs
    When hard filters run for:
      | Criterion | Filter Type |
      | Strategy | Must match |
      | Geography | Must overlap |
      | Fund size | Must be in range |
    Then filtering completes in under 5 seconds
    And database indexes are utilized efficiently
    And memory usage remains stable

  Scenario: Soft scoring performance with 5,000 candidates
    Given hard filters returned 5,000 candidate LPs
    When soft scoring runs
    Then all 5,000 LPs are scored in under 20 seconds
    And scores are calculated in parallel batches
    And progress is reported every 500 LPs

  Scenario: Semantic similarity calculation at scale
    Given 5,000 LPs need semantic scoring
    And each LP has a mandate embedding
    When semantic similarity is calculated
    Then vector comparisons complete in under 10 seconds
    And pgvector is used for efficient batch comparison
    And results are accurate to 4 decimal places

  Scenario: Match generation with minimal filtering
    Given a fund with very broad criteria
    When matching runs and hard filters return 50,000 LPs
    Then system handles large candidate set:
      | Approach | Action |
      | Sampling | Top 10,000 by pre-score |
      | Tiered scoring | Quick score first, detailed for top 1,000 |
    And user is warned "Very broad criteria - results may be less precise"
    And matching still completes in under 60 seconds

  Scenario: Match generation caching and invalidation
    Given I previously generated matches for my fund
    And no fund or LP data has changed
    When I view matches again
    Then cached results are shown instantly
    And I see "Results from [timestamp]. Refresh?"

  Scenario: Match result caching with LP updates
    Given I generated matches yesterday
    And 100 LPs have been updated since
    When I view matches
    Then I see "100 LP profiles updated since last match"
    And I can refresh matches for updated LPs only

  # ==========================================================================
  # Bulk Match Feedback Operations
  # ==========================================================================

  Scenario: Bulk thumbs up on 50 matches
    Given I have 100 matches displayed
    When I select 50 matches
    And I click "Mark all as relevant"
    Then all 50 receive thumbs up feedback
    And operation completes in under 2 seconds
    And UI shows "50 matches marked as relevant"

  Scenario: Bulk thumbs down with reason
    Given I have 100 matches displayed
    When I select 30 matches
    And I click "Mark as not relevant"
    And I select reason "Already in contact"
    Then all 30 receive thumbs down with same reason
    And operation completes in under 2 seconds

  Scenario: Bulk add to shortlist
    Given I have 100 matches displayed
    When I select 25 matches
    And I click "Add to Shortlist"
    Then all 25 are added to my shortlist
    And operation completes in under 2 seconds
    And duplicates are handled (not added twice)

  Scenario: Bulk remove from shortlist
    Given my shortlist has 50 LPs
    When I select 20 LPs
    And I click "Remove from Shortlist"
    Then all 20 are removed
    And operation completes in under 1 second
    And remaining 30 are still in shortlist

  Scenario: Bulk feedback with partial failures
    Given I select 50 matches for feedback
    And 3 matches reference deleted LPs
    When I submit bulk feedback
    Then 47 feedbacks succeed
    And I see "47 of 50 feedbacks saved. 3 LPs no longer available."
    And failed LPs are listed for removal

  Scenario: Bulk operations transaction safety
    Given I am adding 50 LPs to shortlist
    When database error occurs at LP 30
    Then either:
      | All 50 succeed (transaction committed) |
      | All 50 fail (transaction rolled back) |
    And no partial state exists (0-29 added, 30-49 not)

  Scenario: Bulk export of matched LPs
    Given I have 200 matches
    When I click "Export all matches"
    Then CSV export includes all 200 LPs
    And export includes:
      | Column |
      | LP Name |
      | Score |
      | Key Reasons |
      | Contact Info |
    And export completes in under 5 seconds

  # ==========================================================================
  # Concurrent Match Generation Requests
  # ==========================================================================

  Scenario: Same user requests matching twice rapidly
    Given I clicked "Find Matching LPs"
    And matching is in progress
    When I click "Find Matching LPs" again
    Then I see "Matching already in progress"
    And second request is ignored
    And original matching continues

  Scenario: Multiple users run matching simultaneously
    Given 10 GPs each have a published fund
    When all 10 click "Find Matching LPs" within 30 seconds
    Then all 10 matching jobs run in parallel
    And each job completes within 60 seconds
    And results are isolated per user/fund

  Scenario: Matching request queue under high load
    Given 50 matching requests arrive within 10 seconds
    When system processes requests
    Then requests are queued fairly
    And each user sees "Your request is #X in queue"
    And priority users (premium) may jump queue
    And no requests are dropped

  Scenario: Matching resource allocation
    Given matching is CPU and memory intensive
    When 20 concurrent matching jobs run
    Then system limits concurrent jobs to 10
    And remaining 10 are queued
    And system resources are not exhausted
    And other features remain responsive

  Scenario: Matching timeout handling
    Given matching normally takes 30 seconds
    When a matching job takes longer than 2 minutes
    Then job is terminated
    And user sees "Matching timed out. Please try again."
    And partial results are not saved
    And job ID is logged for investigation

  Scenario: Matching job recovery after crash
    Given matching job crashed at 50% completion
    When system recovers
    Then job status shows "Failed - Server error"
    And user can retry matching
    And no corrupt match data exists

  Scenario: Rate limiting for matching requests
    Given user has run matching 5 times in last hour
    When user tries to run matching again
    Then user sees "Rate limit reached. Please wait 30 minutes."
    And rate limit is per-user, not global

  Scenario: Concurrent matching and LP update
    Given matching is running for Fund A
    And LP X is being updated by admin
    When matching reads LP X during update
    Then matching reads consistent LP data:
      | Either old version (pre-update) |
      | Or new version (post-update) |
    And no inconsistent data is used
    And database isolation level ensures consistency

  Scenario: Matching with database maintenance
    Given database vacuum is running
    When matching job executes
    Then matching completes successfully
    And performance may be slightly degraded
    And no errors occur

  # ==========================================================================
  # Load Testing Scenarios
  # ==========================================================================

  Scenario: Sustained matching load for 1 hour
    Given 20 GPs run matching every 5 minutes for 1 hour
    When load test executes
    Then system handles all requests:
      | Metric | Target |
      | Success rate | > 99% |
      | p50 latency | < 30s |
      | p99 latency | < 90s |
      | Error rate | < 1% |
    And no memory leaks occur
    And database connections are managed properly

  Scenario: Spike load test
    Given normal load is 5 matching requests/minute
    When spike of 50 requests arrives in 30 seconds
    Then system handles spike gracefully
    And queue mechanism activates
    And no requests fail with 5xx errors
    And system recovers to normal within 5 minutes

  Scenario: Match generation with degraded external services
    Given Voyage AI is responding slowly (5s latency)
    When matching runs
    Then semantic scoring uses longer timeout
    And overall matching still completes within 90 seconds
    And user is warned "Some features slower than usual"

  Scenario: Graceful degradation under extreme load
    Given system is at 95% capacity
    When additional matching requests arrive
    Then new requests see "System busy. Estimated wait: X minutes"
    And existing jobs complete
    And system does not crash
    And degradation is logged for capacity planning
```

---

## F-AGENT-01: Research Agent (Data Enrichment) [P1]

```gherkin
Feature: Research Agent Data Enrichment
  As the Research Agent
  I want to enrich sparse LP/GP profiles with external data
  So that matching quality improves with better data

  # ==========================================================================
  # Research Agent Triggering
  # ==========================================================================

  Scenario: Trigger enrichment for low data quality score
    Given an LP has data_quality_score = 30 (below threshold of 50)
    When the Research Agent job scheduler runs
    Then a research job is created for this LP
    And job status is "pending"
    And job is queued for processing

  Scenario: Trigger enrichment for stale data
    Given an LP has last_verified = 8 months ago
    And threshold is 6 months
    When the Research Agent job scheduler runs
    Then a research job is created for this LP
    And job reason is "stale_data"

  Scenario: Manual enrichment request by GP
    Given I am viewing an LP profile
    And the LP has sparse data
    When I click "Request Data Enrichment"
    Then a research job is created with source = "user_request"
    And I see "Enrichment requested. Results typically available within 24 hours."
    And I can track job status

  Scenario: Skip enrichment for recently verified LP
    Given an LP has last_verified = 2 months ago
    And data_quality_score = 75
    When the Research Agent job scheduler runs
    Then no research job is created for this LP

  # ==========================================================================
  # Perplexity Search Integration
  # ==========================================================================

  Scenario: Enrich LP with Perplexity search
    Given a research job is running for LP "Nordic Pension Fund"
    When the Research Agent calls perplexity_search("Nordic Pension Fund investment mandate")
    Then search returns relevant results about the LP
    And results include recent news and commitment announcements
    And results are stored in research_job.raw_results

  Scenario: Extract AUM from Perplexity results
    Given Perplexity search returned "Nordic Pension manages approximately EUR 180 billion"
    When the Research Agent parses results
    Then it extracts aum_mm = 180000
    And extraction confidence = 85%
    And source is recorded for audit

  Scenario: Extract mandate details from search
    Given Perplexity search returned mandate information
    When the Research Agent parses results
    Then it extracts:
      | Field | Value | Confidence |
      | strategy_preferences | ["Private Equity", "Infrastructure"] | 80% |
      | geographic_preferences | ["Europe", "Nordics"] | 90% |
      | esg_required | true | 95% |

  Scenario: Handle Perplexity API timeout
    Given a research job is running
    When Perplexity API does not respond within 30 seconds
    Then the request is retried up to 3 times
    And if all retries fail, job status = "failed"
    And error is logged "Perplexity API timeout after 3 retries"

  Scenario: Handle Perplexity rate limiting
    Given many research jobs are running
    When Perplexity returns 429 Too Many Requests
    Then job is requeued with exponential backoff
    And initial wait is 60 seconds
    And subsequent jobs wait longer

  Scenario: Handle no Perplexity results
    Given a research job for obscure LP "Unknown Family Office"
    When Perplexity search returns no relevant results
    Then job status = "completed"
    And enriched_fields = []
    And notes = "No external data found"

  # ==========================================================================
  # Web Fetch Integration
  # ==========================================================================

  Scenario: Scrape LP website for mandate details
    Given LP has website = "https://nordic-pension.fi"
    When Research Agent calls web_fetch(url)
    Then website content is retrieved
    And mandate page is identified and parsed
    And extracted data is added to raw_results

  Scenario: Handle website not accessible
    Given LP has website = "https://private-lp.com"
    When web_fetch returns 403 Forbidden
    Then agent continues with other data sources
    And notes "Website not publicly accessible"

  Scenario: Handle website with no useful content
    Given LP website is purely marketing with no investment details
    When web_fetch parses the content
    Then no mandate information is extracted
    And job continues with other sources

  # ==========================================================================
  # LLM Summary Generation
  # ==========================================================================

  Scenario: Generate LLM summary for sparse LP data
    Given LP "Nordic Pension Fund" has only name and type
    When Research Agent generates LLM summary
    Then summary includes inferred characteristics:
      """
      Nordic Pension Fund is likely a Scandinavian public pension.
      Nordic pensions typically have: AUM EUR 50-200B, strong ESG requirements,
      preference for Nordic/EU managers, long investment horizons.
      """
    And summary is stored in llm_summary field
    And summary_generated_at is set to now

  Scenario: Generate summary embedding
    Given an LLM summary was generated
    When summary embedding is created
    Then summary_embedding vector is stored (1024 dimensions)
    And embedding can be used for semantic matching

  Scenario: Record summary sources
    Given summary was generated from multiple sources
    When job completes
    Then summary_sources contains:
      | Source | URL | Confidence |
      | Perplexity | query result | 85% |
      | Website | https://nordic-pension.fi | 70% |

  Scenario: Handle LLM generation failure
    Given research job is generating summary
    When OpenRouter API fails
    Then summary generation is retried
    And if retries fail, job continues without summary
    And other enriched fields are still saved

  # ==========================================================================
  # Human Review Queue
  # ==========================================================================

  Scenario: Submit enriched data for human review
    Given Research Agent extracted new data for LP
    When extraction completes
    Then all proposed changes go to review queue
    And status = "pending_review"
    And reviewer can see:
      | Field | Current Value | Proposed Value | Source | Confidence |
      | aum_mm | NULL | 180000 | Perplexity | 85% |
      | esg_required | NULL | true | Website | 90% |

  Scenario: Approve enrichment changes
    Given I am an admin reviewing enrichment proposals
    When I click "Approve All"
    Then proposed changes are committed to LP profile
    And last_verified is updated to now
    And data_quality_score is recalculated

  Scenario: Partially approve enrichment
    Given review queue has 5 proposed field changes
    When I approve 3 and reject 2
    Then only approved changes are committed
    And rejected changes are logged with reason

  Scenario: Reject all enrichment changes
    Given review queue has proposed changes
    When I click "Reject All" with reason "Inaccurate data"
    Then no changes are committed
    And job status = "rejected"
    And feedback is logged for agent improvement

  # ==========================================================================
  # NEGATIVE TESTS: Research Agent Failures
  # ==========================================================================

  @negative
  Scenario: All data sources fail
    Given a research job is running
    When Perplexity fails AND web_fetch fails AND news_api fails
    Then job status = "failed"
    And error = "All data sources unavailable"
    And job is requeued for later retry

  @negative
  Scenario: LLM generates hallucinated data
    Given Research Agent generated summary for LP
    And summary claims AUM = $500B
    But no source corroborates this
    When human reviewer checks sources
    Then reviewer rejects the claim
    And feedback is logged "Unsupported claim"
    And model learns from rejection

  @negative
  Scenario: Conflicting data from multiple sources
    Given Perplexity says AUM = EUR 180B
    And website says AUM = EUR 150B
    When Research Agent processes results
    Then both values are presented to reviewer
    And confidence is reduced for conflicting data
    And reviewer decides which to use

  @negative
  Scenario: Research job timeout
    Given a research job is running
    When job exceeds 10 minute timeout
    Then job is terminated
    And status = "timeout"
    And partial results are saved if available

  @negative
  Scenario: Invalid LP reference in job
    Given a research job references LP ID that was deleted
    When job starts processing
    Then job fails immediately
    And status = "invalid_reference"
    And job is not retried

  @negative
  Scenario: Enrichment creates duplicate organization
    Given Research Agent finds LP under different name
    When attempting to create new organization
    Then duplicate detection runs
    And if match found, data is merged to existing LP
    And no duplicate is created

  @negative
  Scenario: API key expired for external service
    Given PERPLEXITY_API_KEY is expired
    When Research Agent tries to call Perplexity
    Then authentication error is caught
    And admin is notified "Perplexity API key needs renewal"
    And jobs are paused until resolved

  @negative
  Scenario: Rate limit exceeded across all agents
    Given 100 research jobs are running concurrently
    When aggregate rate limits are hit
    Then jobs are automatically throttled
    And queue uses fair scheduling
    And older jobs get priority
```

---

## F-AGENT-02: LLM-Interpreted Constraints [P1]

```gherkin
Feature: LLM-Interpreted Constraints
  As the matching engine
  I want to interpret LP mandate text to derive hard/soft filters
  So that implicit constraints are properly applied

  # ==========================================================================
  # Constraint Interpretation from Mandate Text
  # ==========================================================================

  Scenario: Interpret exclusion from biodiversity mandate
    Given LP has mandate_text = "Invests in biodiversity and climate solutions"
    When LLM interprets constraints
    Then interpreted constraints include:
      | Type | Constraint | Confidence |
      | exclude_sector | weapons | 95% |
      | exclude_sector | fossil_fuels | 95% |
      | exclude_sector | mining | 80% |
      | exclude_sector | pharma_animal_testing | 70% |
      | require | esg_policy = true | 90% |

  Scenario: Interpret geographic constraints
    Given LP has mandate_text = "EU-focused growth equity investments"
    When LLM interprets constraints
    Then interpreted constraints include:
      | Type | Constraint | Confidence |
      | require_geography | Europe | 95% |
      | exclude_geography | Asia | 80% |
      | exclude_geography | Americas | 80% |
      | require_strategy | Growth Equity | 90% |

  Scenario: Interpret fund maturity requirements
    Given LP has mandate_text = "We only invest in Fund III or later managers"
    When LLM interprets constraints
    Then interpreted constraints include:
      | Type | Constraint | Confidence |
      | require | fund_number >= 3 | 95% |
      | exclude | first_time_managers | 95% |

  Scenario: Interpret ESG requirements
    Given LP has mandate_text = "ESG-integrated approach with SFDR Article 8+ funds"
    When LLM interprets constraints
    Then interpreted constraints include:
      | Type | Constraint | Confidence |
      | require | esg_policy = true | 98% |
      | require | sfdr_classification IN ['article_8', 'article_9'] | 90% |

  Scenario: Store interpreted constraints
    Given constraints have been interpreted
    When interpretation completes
    Then constraints are stored in lp_interpreted_constraints table
    And each constraint has:
      | id | lp_org_id | constraint_type | constraint_value | confidence | source_text | created_at |
    And constraints are indexed for matching

  # ==========================================================================
  # Constraint Application in Hard Filters
  # ==========================================================================

  Scenario: Apply exclusion constraint in hard filter
    Given LP has interpreted constraint "exclude_sector = fossil_fuels"
    And my fund has sector_focus = ["Energy", "Oil & Gas"]
    When hard filters run
    Then my fund is excluded from this LP's matches
    And exclusion reason = "LP excludes fossil fuel investments"

  Scenario: Apply requirement constraint in hard filter
    Given LP has interpreted constraint "require fund_number >= 3"
    And my fund is Fund II
    When hard filters run
    Then my fund is excluded
    And exclusion reason = "LP requires Fund III or later"

  Scenario: Apply geographic constraint
    Given LP has interpreted constraint "require_geography = Europe"
    And my fund has geographic_focus = ["North America"]
    When hard filters run
    Then my fund is excluded
    And exclusion reason = "LP requires European focus"

  Scenario: Pass all interpreted constraints
    Given LP has multiple interpreted constraints
    And my fund meets all constraints
    When hard filters run
    Then my fund passes to soft scoring stage
    And no constraint exclusions apply

  # ==========================================================================
  # Confidence-Based Constraint Handling
  # ==========================================================================

  Scenario: High confidence constraint is hard filter
    Given LP has constraint "exclude_sector = weapons" with confidence = 95%
    When constraint is applied
    Then constraint is treated as hard filter
    And matching funds with weapons exposure are excluded

  Scenario: Low confidence constraint is soft factor
    Given LP has constraint "prefer ESG focus" with confidence = 60%
    When constraint is applied
    Then constraint is treated as soft scoring factor
    And funds without ESG get score penalty, not exclusion

  Scenario: Configurable confidence threshold
    Given admin sets hard_filter_confidence_threshold = 80%
    When constraints are applied
    Then constraints with confidence >= 80% are hard filters
    And constraints with confidence < 80% are soft factors

  # ==========================================================================
  # Constraint Updates and Versioning
  # ==========================================================================

  Scenario: Re-interpret constraints when mandate changes
    Given LP's mandate_text was updated
    When constraint interpretation runs
    Then new constraints replace old ones
    And old constraints are archived (not deleted)
    And matches are recalculated with new constraints

  Scenario: Track constraint interpretation history
    Given constraints were interpreted 3 times for LP
    When I view constraint history
    Then I see all versions with timestamps
    And I can see what changed between versions

  # ==========================================================================
  # NEGATIVE TESTS: Constraint Interpretation Failures
  # ==========================================================================

  @negative
  Scenario: Empty mandate text
    Given LP has mandate_text = "" or NULL
    When constraint interpretation runs
    Then no constraints are generated
    And LP uses only explicit preferences for matching

  @negative
  Scenario: Ambiguous mandate text
    Given LP has mandate_text = "We invest broadly across markets"
    When LLM interprets constraints
    Then few or no constraints are generated
    And confidence scores are low (< 50%)
    And note is added "Mandate too vague for constraint extraction"

  @negative
  Scenario: Contradictory mandate statements
    Given LP has mandate_text = "We focus on ESG but also invest in energy transition including natural gas"
    When LLM interprets constraints
    Then conflicting constraints are flagged
    And human review is triggered
    And both interpretations are presented

  @negative
  Scenario: Non-English mandate text
    Given LP has mandate_text in German
    When constraint interpretation runs
    Then text is translated first (if supported)
    Or interpretation fails gracefully with "Unsupported language"

  @negative
  Scenario: LLM interpretation timeout
    Given mandate_text is very long (10000+ characters)
    When LLM interpretation takes > 60 seconds
    Then interpretation is cancelled
    And job is retried with truncated text
    And warning is logged

  @negative
  Scenario: LLM returns invalid constraint format
    Given LLM interpretation runs
    When LLM returns malformed JSON or invalid constraint types
    Then parsing error is caught
    And interpretation is retried with modified prompt
    And if retries fail, manual review is requested

  @negative
  Scenario: Constraint conflicts with explicit LP preferences
    Given LP has explicit strategy_preferences = ["Venture Capital"]
    And LLM interprets constraint "require_strategy = Private Equity"
    When conflict is detected
    Then explicit preference takes precedence
    And interpreted constraint is flagged for review
```

---

## F-AGENT-03: Learning Agent (Cross-Company Intelligence) [P1]

```gherkin
Feature: Learning Agent Cross-Company Intelligence
  As the Learning Agent
  I want to aggregate learnings across all companies
  So that recommendations improve for everyone while preserving privacy

  # ==========================================================================
  # Outcome Observation (Privacy-Safe Aggregation)
  # ==========================================================================

  Scenario: Calculate LP response rate
    Given LP "CalPERS" was contacted by 10 different GPs (across companies)
    And CalPERS responded to 6 of them
    When Learning Agent aggregates signals
    Then LP response_rate = 60% is calculated
    And stored in global_learned_signals table
    And no company-specific data is exposed

  Scenario: Detect LP engagement trend
    Given LP "CalPERS" response rate history:
      | Quarter | Response Rate |
      | Q1 2024 | 70% |
      | Q2 2024 | 55% |
      | Q3 2024 | 40% |
    When Learning Agent analyzes trend
    Then signal is generated: "CalPERS engagement declining"
    And alert is available to all GPs

  Scenario: Identify strategy trends
    Given across all companies:
      | Strategy | Match → Response Rate |
      | Climate Tech | 45% |
      | Traditional PE | 28% |
      | Healthcare | 35% |
    When Learning Agent aggregates
    Then signal is generated: "Climate Tech seeing 2x engagement"
    And market prior is updated

  Scenario: Detect timing patterns
    Given commitment data across companies shows:
      | Quarter | Commitment Count |
      | Q1 | 15 |
      | Q2 | 8 |
      | Q3 | 10 |
      | Q4 | 35 |
    When Learning Agent analyzes
    Then signal is generated: "Q4 allocation windows confirmed"
    And timing factor weights are adjusted

  # ==========================================================================
  # Privacy Boundaries
  # ==========================================================================

  Scenario: Aggregated signals are privacy-safe
    Given Company A contacted LP X
    When Learning Agent stores signals
    Then only aggregated stats are stored:
      | Can Store | Cannot Store |
      | "LP X has 60% response rate" | "Company A contacted LP X" |
      | "Strategy Y is trending" | Specific pitch content |
      | Commitment patterns | Negotiation details |

  Scenario: Minimum aggregation threshold
    Given only 2 companies contacted LP "Small Family Office"
    When Learning Agent aggregates
    Then no response rate is published (below threshold of 5)
    And privacy is maintained for rare LPs

  Scenario: Anonymous outcome data
    Given a commitment was made
    When Learning Agent records outcome
    Then it records:
      | Field | Value |
      | strategy | Private Equity |
      | size_bucket | $50-100M |
      | region | North America |
    And it does NOT record:
      | Field |
      | gp_company_id |
      | lp_company_id |
      | exact_amount |

  # ==========================================================================
  # Model Training and Updates
  # ==========================================================================

  Scenario: Update ensemble weights from outcomes
    Given 100 commitments with outcome data are available
    When Learning Agent retrains model
    Then ensemble weights are updated
    And new weights are A/B tested before full deployment
    And old weights are retained for rollback

  Scenario: Market prior updates
    Given Learning Agent detected market shifts
    When priors are updated
    Then matching scores incorporate new priors
    And update is logged with effective date

  Scenario: Share learnings to all companies
    Given new signal "Pensions prioritizing climate in 2024"
    When signal is published
    Then all GPs can see this insight
    And insight appears in dashboard/reports

  # ==========================================================================
  # NEGATIVE TESTS: Learning Agent Failures
  # ==========================================================================

  @negative
  Scenario: Insufficient data for reliable signal
    Given only 3 data points for a pattern
    When Learning Agent attempts to generate signal
    Then signal is not published (below threshold)
    And data is accumulated for future analysis

  @negative
  Scenario: Bias in aggregated data
    Given most platform users are US-based GPs
    When Learning Agent aggregates
    Then regional bias is detected
    And signals are adjusted for sample bias
    And bias warning is included with signals

  @negative
  Scenario: Stale signals not refreshed
    Given signal "LP X is highly responsive" is 6 months old
    When signal staleness check runs
    Then signal is marked as stale
    And confidence is reduced
    And refresh is triggered

  @negative
  Scenario: Model retraining fails
    Given retraining job is running
    When training fails due to data quality issues
    Then current model remains in production
    And alert is sent to admin
    And training is retried with cleaned data

  @negative
  Scenario: Privacy violation detected
    Given a signal inadvertently reveals company identity
    When privacy check runs
    Then signal is blocked from publication
    And incident is logged
    And affected data is reviewed

  @negative
  Scenario: Outcome data is incomplete
    Given commitment was made but amount not known
    When Learning Agent processes outcome
    Then available data is used
    And missing fields are handled gracefully
    And signal confidence is adjusted accordingly
```

---

## F-MATCH-06: LP-Side Matching (Bidirectional) [P1]

```gherkin
Feature: LP-Side Matching (Bidirectional)
  As an LP
  I want to see which funds match my mandate
  So that I can discover relevant investment opportunities

  # ==========================================================================
  # LP Match Preferences Setup
  # ==========================================================================

  Scenario: LP sets active search preferences
    Given I am logged in as an LP user
    When I navigate to match preferences
    And I set:
      | Field | Value |
      | actively_looking | true |
      | allocation_available_mm | 50 |
      | target_close_date | 2024-Q4 |
    Then preferences are saved
    And I will receive fund recommendations

  Scenario: LP sets notification preferences
    Given I have active search preferences
    When I configure notifications:
      | notify_on_new_funds | true |
      | min_match_score | 75 |
    Then I will be notified when funds score 75+ match my mandate

  Scenario: LP disables active search
    Given I was actively looking
    When I set actively_looking = false
    Then I stop receiving new fund notifications
    And existing matches remain visible

  # ==========================================================================
  # Reverse Match Generation (LP → Fund)
  # ==========================================================================

  Scenario: Generate fund matches for LP
    Given LP has mandate and preferences set
    When a new fund is published
    Then matching runs from LP perspective
    And matching funds are stored in lp_fund_matches table
    And LP can view matched funds

  Scenario: Rank funds by LP perspective
    Given matching found 20 funds for LP
    When LP views matches
    Then funds are ranked by total_score
    And each match shows:
      | Fund Name | Score | Key Alignment Points |

  Scenario: Show score breakdown to LP
    Given LP is viewing a fund match
    When LP clicks on score
    Then LP sees breakdown:
      | Factor | Score |
      | Strategy Alignment | 90 |
      | Size Fit | 85 |
      | Geographic Overlap | 80 |
      | Semantic Similarity | 88 |

  # ==========================================================================
  # LP Interest Actions
  # ==========================================================================

  Scenario: LP marks fund as interesting
    Given I am viewing a matched fund
    When I click "Interested"
    Then lp_interest = "interested"
    And GP sees this in their match view (if enabled)
    And match is moved to "Interested" list

  Scenario: LP marks fund as not interested
    Given I am viewing a matched fund
    When I click "Not Interested"
    Then lp_interest = "not_interested"
    And fund is hidden from my active matches
    And feedback is recorded for algorithm improvement

  Scenario: LP adds notes to match
    Given I am reviewing a matched fund
    When I add notes "Already in contact with this GP"
    Then lp_notes is saved
    And notes are private to my organization

  Scenario: LP requests more information
    Given I am viewing a matched fund
    When I click "Request Info"
    Then a request is sent to the GP
    And GP is notified of LP interest
    And interaction is logged

  # ==========================================================================
  # Notifications
  # ==========================================================================

  Scenario: Notify LP of new matching fund
    Given LP has notify_on_new_funds = true
    And min_match_score = 70
    When a new fund is published with match score = 85
    Then LP receives notification
    And notification includes fund summary and score

  Scenario: Do not notify below threshold
    Given LP has min_match_score = 80
    When a new fund matches with score = 72
    Then LP is NOT notified
    And match is still visible in dashboard

  Scenario: Batch notification for multiple funds
    Given 5 new funds matched in the last 24 hours
    When daily digest runs
    Then LP receives one digest email
    And email lists all 5 funds with scores

  # ==========================================================================
  # Privacy and Visibility
  # ==========================================================================

  Scenario: LP interest visible to GP
    Given LP marked fund as "interested"
    And GP has enabled LP interest visibility
    When GP views their match list
    Then GP sees "1 LP expressed interest"
    And GP can see LP name (with LP's consent)

  Scenario: LP interest hidden if LP chooses
    Given LP settings have share_interest_with_gps = false
    When LP marks fund as interested
    Then GP does NOT see LP's interest
    And LP's privacy is maintained

  # ==========================================================================
  # NEGATIVE TESTS: LP-Side Matching Failures
  # ==========================================================================

  @negative
  Scenario: LP with no mandate cannot receive matches
    Given LP has no mandate_text and no preferences
    When matching runs
    Then no matches are generated for this LP
    And LP sees "Complete your mandate to receive fund recommendations"

  @negative
  Scenario: LP matches expire after fund closes
    Given LP has matches with Fund A
    And Fund A status changes to "closed"
    When LP views matches
    Then Fund A match is marked "Fund Closed"
    And match is moved to archive

  @negative
  Scenario: Notification delivery fails
    Given LP notification is triggered
    When email delivery fails
    Then notification is retried
    And if retries fail, notification is queued for web display
    And delivery failure is logged

  @negative
  Scenario: LP preferences validation
    Given LP tries to set allocation_available_mm = -100
    When saving preferences
    Then validation error "Allocation must be positive"
    And preferences are not saved

  @negative
  Scenario: Concurrent preference updates
    Given LP user A is editing preferences
    And LP user B (same org) is also editing
    When both save
    Then second save warns of conflict
    And user can merge or overwrite

  @negative
  Scenario: No matching funds found
    Given LP has very specific mandate
    When matching runs
    And no funds match
    Then LP sees "No matching funds currently available"
    And suggestions to broaden mandate are shown

  @negative
  Scenario: LP organization deleted
    Given LP had active matches
    When LP organization is deleted
    Then matches are cleaned up
    And GPs no longer see this LP in their matches
    And data is properly cascaded
```
