# Milestone 4: Pitch Generation Tests
## "AI explains matches + generates pitch"

---

## F-PITCH-01: LP-Specific Executive Summary [P0]

```gherkin
Feature: LP-Specific Executive Summary
  As a GP
  I want to generate personalized summaries
  So that each LP gets relevant information

  # Sub-feature: Summary Generation
  Scenario: Generate executive summary
    Given I have a match with LP "CalPERS"
    When I click "Generate Summary"
    Then AI generates a 1-page summary
    And summary is tailored to CalPERS

  Scenario: Summary content
    When I view the generated summary
    Then it includes:
      | Section | Content |
      | Introduction | Fund overview for CalPERS |
      | Strategy Alignment | How we match their mandate |
      | Track Record | Relevant performance highlights |
      | Team | Key partners and experience |
      | Why Now | Timeliness and opportunity |

  # Sub-feature: Personalization
  Scenario: Tailored to LP interests
    Given CalPERS focuses on ESG
    When summary is generated
    Then ESG section is prominent
    And ESG certifications are highlighted

  Scenario: Include match rationale
    Given match score is 85 with breakdown
    When summary is generated
    Then it references why we're a good fit
    And mentions specific alignment points

  # Sub-feature: Export
  Scenario: Export as PDF
    Given a summary is generated
    When I click "Download PDF"
    Then a professionally formatted PDF downloads
    And filename is "Summary_CalPERS_GrowthFundIII.pdf"

  # Sub-feature: Performance
  Scenario: Generation time
    When I generate a summary
    Then it completes in under 10 seconds
    And I see progress indicator during generation

  # Sub-feature: Editing
  Scenario: Edit before export
    Given a summary is generated
    When I click "Edit"
    Then I can modify the text
    And I can regenerate specific sections
    And I can save my edits
```

---

## F-PITCH-02: Outreach Email Draft [P0]

```gherkin
Feature: Outreach Email Draft
  As a GP
  I want to generate personalized intro emails
  So that my outreach is effective

  # Sub-feature: Email Generation
  Scenario: Generate email draft
    Given I have a match with LP "Harvard Endowment"
    When I click "Generate Email"
    Then AI generates an email draft
    And email is personalized to Harvard

  # Sub-feature: Tone Options
  Scenario: Formal tone
    When I select tone "Formal"
    Then email uses formal language
    And salutation is "Dear Mr./Ms. [Name]"
    And closing is "Respectfully yours"

  Scenario: Warm tone
    When I select tone "Warm"
    Then email uses friendly but professional language
    And may reference shared connections
    And closing is "Best regards"

  Scenario: Direct tone
    When I select tone "Direct"
    Then email is concise and to the point
    And leads with value proposition
    And call to action is clear

  # Sub-feature: Personalization
  Scenario: Reference LP specifics
    Given Harvard Endowment focuses on technology
    When email is generated
    Then it mentions our technology portfolio
    And references Harvard's known investments

  Scenario: Reference mutual connections
    Given we have a mutual connection noted
    When email is generated
    Then it mentions the connection appropriately

  # Sub-feature: Email Components
  Scenario: Email structure
    When I view the generated email
    Then I see:
      | Component | Example |
      | Subject | Introduction: Growth Fund III |
      | Greeting | Dear [Contact Name] |
      | Hook | Opening that catches attention |
      | Value Prop | Why we're relevant |
      | Ask | Clear call to action |
      | Signature | My contact info |

  # Sub-feature: No Auto-Send (Human-in-the-Loop)
  Scenario: Email is for review only
    When email is generated
    Then there is NO "Send" button
    And I see "Copy to Clipboard" button
    And I must manually send from my email client

  # Sub-feature: Copy to Clipboard
  Scenario: Copy email
    Given an email is generated
    When I click "Copy to Clipboard"
    Then email content (subject + body) is copied
    And I see "Copied!" confirmation
    And I can paste into my email client

  # Sub-feature: Edit Before Copy
  Scenario: Edit email
    Given an email is generated
    When I click "Edit"
    Then I can modify subject and body
    And I can regenerate if needed
    And edited version is what gets copied

  # Sub-feature: Save as Template
  Scenario: Save email as template
    Given I edited and like this email format
    When I click "Save as Template"
    And I name it "Tech LP Outreach"
    Then template is saved
    And I can use it for similar LPs
```

---

## F-PITCH-03: Deck Modification Suggestions [P1]

```gherkin
Feature: Deck Modification Suggestions
  As a GP
  I want AI to suggest deck changes
  So that I can tailor my pitch per LP

  # Sub-feature: Analysis
  Scenario: Analyze deck for LP
    Given I uploaded my pitch deck
    And I want to tailor it for CalPERS
    When I click "Get Suggestions"
    Then AI analyzes deck content
    And compares to CalPERS preferences

  # Sub-feature: Suggestions
  Scenario: Suggest slide order
    Given CalPERS prioritizes ESG
    When suggestions are generated
    Then I see "Move ESG slide earlier (slide 3 → slide 2)"

  Scenario: Suggest emphasis points
    When suggestions are generated
    Then I see emphasis recommendations:
      | "Highlight public pension exits" |
      | "Add CalPERS-comparable deal sizes" |
      | "Include diversity metrics" |

  # Sub-feature: Report
  Scenario: Generate modification report
    When suggestions are complete
    Then I can download a report
    And report lists all suggestions
    And I can share with my team
```

---

## F-PITCH-04: Supplementary Materials [P1]

```gherkin
Feature: Supplementary Materials
  As a GP
  I want to generate LP-specific addendum docs
  So that I can provide tailored materials

  # Sub-feature: Cover Letter
  Scenario: Generate cover letter
    Given I have a match with LP
    When I click "Generate Cover Letter"
    Then AI creates a cover letter
    And it's tailored to the LP

  # Sub-feature: Case Study Selection
  Scenario: Recommend relevant case studies
    Given LP focuses on healthcare
    When I request case study recommendations
    Then AI suggests healthcare deals from our portfolio
    And ranks them by relevance

  # Sub-feature: Track Record Highlights
  Scenario: Generate relevant track record highlights
    Given LP's check size is $25M
    When I request highlights
    Then AI selects deals in that size range
    And formats them for presentation

  # Sub-feature: Export
  Scenario: Export as PDF addendum
    When I finalize supplementary materials
    Then I can export as PDF
    And it's formatted professionally
    And can be attached to my deck
```

---

## F-PITCH-05: Deck Modification (PPTX) [P2]

```gherkin
Feature: Deck Modification (PPTX)
  As a GP
  I want AI to modify my deck directly
  So that I don't have to manually edit

  # Sub-feature: Parse PPTX
  Scenario: Parse slide structure
    Given I uploaded a PPTX deck
    When AI analyzes it
    Then it understands slide structure
    And can identify content areas

  # Sub-feature: Modify Slides
  Scenario: Add LP-specific slide
    Given I want a CalPERS-specific intro
    When I request modification
    Then AI adds a new slide
    And content is tailored to CalPERS

  Scenario: Reorder slides
    Given AI suggests moving ESG earlier
    When I approve the change
    Then slides are reordered
    And PPTX is updated

  # Sub-feature: Maintain Formatting
  Scenario: Preserve deck style
    When AI modifies the deck
    Then fonts remain consistent
    And colors match brand guidelines
    And layout is maintained

  # Sub-feature: Download
  Scenario: Download modified deck
    When modifications are complete
    Then I can download the new PPTX
    And filename indicates it's LP-specific
```

---

## F-UI-04: Match Results View [P0]

```gherkin
Feature: Match Results View
  As a GP
  I want to see matches clearly
  So that I can review and act on them

  # Sub-feature: Ranked List
  Scenario: View match list
    When I view match results
    Then I see LPs ranked by score
    And each row shows:
      | LP Name | Type | Score | Key Factors |
      | CalPERS | Pension | 92 | Strategy, ESG |
      | Harvard | Endowment | 87 | Size, Sector |

  # Sub-feature: Score Visualization
  Scenario: Visual score bar
    When I view a match
    Then score is shown as colored bar
    And color indicates quality:
      | 80-100 | Green |
      | 60-79 | Yellow |
      | Below 60 | Orange |

  # Sub-feature: Score Breakdown
  Scenario: Expand score breakdown
    When I click on a score
    Then I see breakdown:
      | Factor | Score |
      | Strategy | 95 |
      | Size Fit | 88 |
      | Semantic | 92 |
      | ESG | 85 |

  # Sub-feature: Explanation Panel
  Scenario: View explanation
    When I click "Why this match?"
    Then explanation panel expands
    And I see AI-generated explanation
    And I see talking points

  # Sub-feature: Actions
  Scenario: Actions per match
    When I view a match
    Then I see action buttons:
      | "Add to Shortlist" |
      | "Generate Pitch" |
      | "Dismiss" |

  # Sub-feature: Filtering
  Scenario: Filter by score threshold
    Given I have 100 matches
    When I set minimum score to 75
    Then I only see matches with score ≥ 75

  Scenario: Filter by LP type
    Given matches include various LP types
    When I filter by "Endowment"
    Then I only see Endowment matches
```

---

## F-HITL-01: Outreach Email Review [P0]

```gherkin
Feature: Outreach Email Review (Human-in-the-Loop)
  As a GP
  I want to review emails before sending
  So that I maintain control of my communications

  # Sub-feature: No Auto-Send
  Scenario: System never sends emails
    Given I generated an email
    Then there is no "Send" button
    And the system cannot send emails
    And I must use my own email client

  # Sub-feature: Review Flow
  Scenario: Review generated email
    Given AI generated an email draft
    When I view the email
    Then I see subject and body
    And I can read every word
    And I can edit any part

  # Sub-feature: Copy to Clipboard
  Scenario: Copy for external sending
    Given I reviewed and approved the email
    When I click "Copy to Clipboard"
    Then subject and body are copied
    And I see confirmation "Copied!"
    And I paste into Gmail/Outlook

  # Sub-feature: Track Copy Action
  Scenario: Log that email was copied
    When I copy an email
    Then system logs:
      | Timestamp | LP | Action |
      | Now | CalPERS | Email copied |
    And I can see this in activity log

  # Sub-feature: Edit Before Copy
  Scenario: Require explicit action
    Given I just generated an email
    Then I must either:
      - Edit and then copy
      - Confirm review and copy
      - Discard
    And I cannot accidentally skip review
```

---

## E2E: Match to Outreach Journey

```gherkin
Feature: Complete Pitch Generation Journey
  As a GP with matches
  I want to generate and send outreach
  So that I can start conversations

  Scenario: Generate pitches for top matches
    Given I have 45 matches for my fund
    And I shortlisted the top 10

    # View shortlist
    When I go to my shortlist
    Then I see 10 LPs ready for outreach

    # Generate summary for first LP
    When I select "CalPERS" (score 92)
    And I click "Generate Summary"
    Then summary is generated in 8 seconds
    And I see personalized 1-page summary

    # Review and download summary
    When I review the summary
    Then I see it mentions CalPERS's ESG focus
    And includes our relevant track record
    When I click "Download PDF"
    Then PDF downloads

    # Generate email
    When I click "Generate Email"
    And I select "Warm" tone
    Then email is generated
    And subject is compelling
    And body is personalized

    # Review and edit email
    When I review the email
    And I make a small edit to the opening
    Then my edit is saved

    # Copy and send externally
    When I click "Copy to Clipboard"
    Then email is copied
    And I see "Copied!"

    When I open Gmail
    And I paste the email
    And I attach the PDF summary
    And I send the email
    Then I've completed outreach

    # Mark as contacted
    When I return to the platform
    And I mark CalPERS as "Contacted"
    Then status updates
    And CalPERS moves to "Contacted" list
```
