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

  # ============================================================
  # NEGATIVE TEST CASES: Summary Generation Failures
  # ============================================================

  # Sub-feature: API Failures
  Scenario: Handle API timeout during summary generation
    Given I have a match with LP "CalPERS"
    When I click "Generate Summary"
    And the OpenRouter API times out after 30 seconds
    Then I see error message "Generation timed out. Please try again."
    And I see a "Retry" button
    And my previous data is not lost

  Scenario: Handle rate limit exceeded
    Given I have generated 10 summaries in the last minute
    When I click "Generate Summary" for another LP
    And the API returns rate limit error (429)
    Then I see error message "Rate limit reached. Please wait a moment before trying again."
    And I see estimated wait time
    And I can queue the request for later

  Scenario: Handle API service unavailable
    Given I have a match with LP "CalPERS"
    When I click "Generate Summary"
    And the OpenRouter API returns 503 Service Unavailable
    Then I see error message "AI service temporarily unavailable. Please try again later."
    And I see option to be notified when service is restored

  Scenario: Handle invalid API key
    Given OpenRouter API key is invalid or expired
    When I click "Generate Summary"
    Then I see error message "Configuration error. Please contact support."
    And error is logged for admin review
    And no sensitive details are shown to user

  # Sub-feature: Invalid Match Scenarios
  Scenario: Handle invalid match ID
    Given I navigate to summary generation with match ID "invalid-uuid"
    Then I see error message "Match not found"
    And I am redirected to match list

  Scenario: Handle deleted match
    Given I have a match with LP "CalPERS"
    And the match is deleted while I'm viewing it
    When I click "Generate Summary"
    Then I see error message "This match no longer exists"
    And I am redirected to match list

  Scenario: Handle match belonging to another GP
    Given I try to access match ID belonging to another GP
    When I click "Generate Summary"
    Then I see error message "You don't have access to this match"
    And access attempt is logged for security

  # Sub-feature: Empty or Invalid Content
  Scenario: Handle empty summary generation
    Given I have a match with LP "CalPERS"
    When I click "Generate Summary"
    And the AI returns empty content
    Then I see error message "Unable to generate summary. Please try again."
    And I see option to report the issue

  Scenario: Handle malformed AI response
    Given I have a match with LP "CalPERS"
    When I click "Generate Summary"
    And the AI returns invalid JSON
    Then I see error message "Error processing AI response. Please try again."
    And the error is logged with response details

  Scenario: Handle summary with missing sections
    Given I have a match with LP "CalPERS"
    When I click "Generate Summary"
    And the AI response is missing required sections
    Then I see warning "Some sections could not be generated"
    And I see which sections are missing
    And I can regenerate specific sections

  # Sub-feature: Missing LP Data for Personalization
  Scenario: Handle LP with missing investment focus data
    Given I have a match with LP "Unknown Fund"
    And the LP has no investment focus data
    When I click "Generate Summary"
    Then summary is generated with generic content
    And I see warning "Limited LP data available - summary may be less personalized"

  Scenario: Handle LP with no contact information
    Given I have a match with LP "Anonymous Investor"
    And the LP has no contact details
    When I click "Generate Summary"
    Then summary is generated without contact-specific personalization
    And placeholder text indicates missing data

  Scenario: Handle LP with incomplete profile
    Given I have a match with LP "Partial Data LP"
    And the LP is missing:
      | Field |
      | Investment strategy |
      | Geographic focus |
      | Check size |
    When I click "Generate Summary"
    Then I see warning "LP profile incomplete - some personalization unavailable"
    And summary uses available data only

  # Sub-feature: PDF Export Failures
  Scenario: Handle PDF generation failure
    Given a summary is generated
    When I click "Download PDF"
    And PDF generation fails
    Then I see error message "Unable to create PDF. Please try again."
    And I see option to copy summary as text instead

  Scenario: Handle PDF download interruption
    Given a summary is generated
    When I click "Download PDF"
    And the download is interrupted
    Then I see error message "Download interrupted. Please try again."
    And I can retry the download

  Scenario: Handle PDF with special characters
    Given a summary contains special characters (unicode, emojis)
    When I click "Download PDF"
    Then PDF is generated successfully
    And special characters are rendered correctly
    Or replaced with safe alternatives

  Scenario: Handle very large summary for PDF
    Given a summary is generated with 50+ pages of content
    When I click "Download PDF"
    Then I see warning "Large document - this may take a moment"
    And PDF is generated (possibly paginated)
    And file size is reasonable (< 10MB)

  # Sub-feature: Network and Browser Issues
  Scenario: Handle network disconnection during generation
    Given I have a match with LP "CalPERS"
    When I click "Generate Summary"
    And network connection is lost mid-generation
    Then I see error message "Connection lost. Please check your internet and try again."
    And partial results are not saved

  Scenario: Handle browser tab closed during generation
    Given I have a match with LP "CalPERS"
    When I click "Generate Summary"
    And I close the browser tab
    And I return to the page
    Then I see the generation did not complete
    And I can restart the generation
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

  # ============================================================
  # NEGATIVE TEST CASES: Email Generation Failures
  # ============================================================

  # Sub-feature: API Failures
  Scenario: Handle API timeout during email generation
    Given I have a match with LP "Harvard Endowment"
    When I click "Generate Email"
    And the OpenRouter API times out
    Then I see error message "Email generation timed out. Please try again."
    And I see a "Retry" button

  Scenario: Handle rate limit during email generation
    Given I have generated many emails recently
    When I click "Generate Email"
    And the API returns rate limit error
    Then I see error message "Too many requests. Please wait before trying again."
    And I see countdown timer

  # Sub-feature: Invalid Tone Selection
  Scenario: Handle invalid tone parameter
    Given I have a match with LP "Harvard Endowment"
    When I manipulate the request to send tone "InvalidTone"
    Then I see error message "Invalid tone selection"
    And I am shown valid tone options

  Scenario: Handle missing tone selection
    Given I have a match with LP "Harvard Endowment"
    When I click "Generate Email" without selecting a tone
    Then default tone "Warm" is used
    Or I am prompted to select a tone

  Scenario: Handle tone options not loading
    Given the tone options fail to load from the server
    When I try to select a tone
    Then I see error message "Unable to load tone options"
    And I can use a default tone
    And I can retry loading options

  # Sub-feature: Invalid Match and LP Data
  Scenario: Handle invalid match ID for email
    Given I navigate to email generation with invalid match ID
    Then I see error message "Match not found"
    And I am redirected to match list

  Scenario: Handle LP with no contact name
    Given I have a match with LP that has no contact name
    When I click "Generate Email"
    Then email is generated with placeholder "[Contact Name]"
    And I see warning "No contact name available - please add before sending"

  Scenario: Handle LP with no email address
    Given I have a match with LP that has no email address
    When I click "Generate Email"
    Then email is generated successfully
    And I see warning "No recipient email on file"

  # Sub-feature: Missing LP Data for Personalization
  Scenario: Handle LP with no known investments
    Given I have a match with LP "New Investor"
    And the LP has no investment history on file
    When I click "Generate Email"
    Then email is generated with generic references
    And I see note "Limited investment history available"

  Scenario: Handle LP with no geographic data
    Given I have a match with LP "Global Unknown"
    And the LP has no geographic preference data
    When I click "Generate Email"
    Then email omits geographic references
    And content focuses on other alignment factors

  Scenario: Handle LP with minimal profile
    Given I have a match with LP "Sparse Profile LP"
    And the LP only has name and type
    When I click "Generate Email"
    Then I see warning "Very limited LP data - email may require significant editing"
    And email is generated with minimal personalization

  # Sub-feature: Empty Content Generation
  Scenario: Handle empty email generation
    Given I have a match with LP "Harvard Endowment"
    When I click "Generate Email"
    And the AI returns empty subject and body
    Then I see error message "Unable to generate email. Please try again."
    And I can retry or use a template

  Scenario: Handle email with empty subject
    Given I have a match with LP "Harvard Endowment"
    When I click "Generate Email"
    And the AI returns empty subject but valid body
    Then I see warning "Subject line could not be generated"
    And I am prompted to add a subject manually

  Scenario: Handle email with empty body
    Given I have a match with LP "Harvard Endowment"
    When I click "Generate Email"
    And the AI returns valid subject but empty body
    Then I see error message "Email body could not be generated"
    And I can retry generation

  # Sub-feature: Clipboard Copy Failures
  Scenario: Handle clipboard permission denied
    Given an email is generated
    When I click "Copy to Clipboard"
    And browser denies clipboard access
    Then I see error message "Unable to copy. Please grant clipboard permission or copy manually."
    And email text is displayed for manual selection

  Scenario: Handle clipboard not available
    Given an email is generated
    And I'm using an older browser without Clipboard API
    When I click "Copy to Clipboard"
    Then I see fallback "Select All" button
    And text is highlighted for manual copy (Ctrl+C)

  Scenario: Handle clipboard copy with special characters
    Given an email contains special characters (unicode, quotes)
    When I click "Copy to Clipboard"
    Then all characters are copied correctly
    And no encoding issues occur when pasting

  Scenario: Handle very long email copy
    Given an email is generated with 5000+ characters
    When I click "Copy to Clipboard"
    Then entire email is copied successfully
    And I see "Copied!" confirmation

  # Sub-feature: Template Save Failures
  Scenario: Handle template save with duplicate name
    Given I have a template named "Tech LP Outreach"
    When I try to save another template with the same name
    Then I see error message "Template name already exists"
    And I am prompted to choose a different name

  Scenario: Handle template save with empty name
    When I try to save a template with empty name
    Then I see error message "Template name is required"
    And save button remains disabled

  Scenario: Handle template save failure
    Given I edited and like this email format
    When I click "Save as Template"
    And the save operation fails
    Then I see error message "Unable to save template. Please try again."
    And my edited email is not lost

  # Sub-feature: Edit Failures
  Scenario: Handle save edit failure
    Given an email is generated
    When I click "Edit" and make changes
    And I click "Save"
    And the save fails
    Then I see error message "Unable to save changes. Please try again."
    And my edits are preserved in the editor

  Scenario: Handle edit with concurrent modification
    Given an email is being edited in two browser tabs
    When I save in one tab and then try to save in the other
    Then I see warning "This email has been modified elsewhere"
    And I can merge or overwrite changes
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

  # ============================================================
  # NEGATIVE TEST CASES: Deck Analysis Failures
  # ============================================================

  # Sub-feature: API and Generation Failures
  Scenario: Handle API timeout during deck analysis
    Given I uploaded my pitch deck
    When I click "Get Suggestions"
    And the API times out
    Then I see error message "Analysis timed out. Your deck may be too large. Please try again."
    And I see option to analyze fewer slides

  Scenario: Handle rate limit during deck analysis
    Given I have analyzed multiple decks recently
    When I click "Get Suggestions"
    And the API returns rate limit error
    Then I see error message "Please wait before analyzing another deck"
    And I see estimated wait time

  # Sub-feature: Invalid Data
  Scenario: Handle invalid match ID for deck suggestions
    Given I navigate to deck suggestions with invalid match ID
    Then I see error message "Match not found"
    And I am redirected to match list

  Scenario: Handle no deck uploaded
    Given I have a match with LP "CalPERS"
    And I have not uploaded a pitch deck
    When I try to access deck suggestions
    Then I see message "Please upload a pitch deck first"
    And I see link to upload a deck

  Scenario: Handle corrupt deck file
    Given I uploaded a corrupt PPTX file
    When I click "Get Suggestions"
    Then I see error message "Unable to read deck file. Please upload a valid PPTX or PDF."
    And I can upload a new file

  # Sub-feature: Missing LP Data
  Scenario: Handle LP with no preference data
    Given I have a match with LP "Unknown Investor"
    And the LP has no known preferences
    When I click "Get Suggestions"
    Then I see message "Limited LP data available"
    And suggestions are based on general best practices

  # Sub-feature: Empty or No Suggestions
  Scenario: Handle no suggestions generated
    Given I uploaded my pitch deck
    When I click "Get Suggestions"
    And the AI finds no modifications needed
    Then I see message "Your deck appears well-suited for this LP"
    And I see option to request deeper analysis

  Scenario: Handle empty AI response for suggestions
    Given I uploaded my pitch deck
    When I click "Get Suggestions"
    And the AI returns empty response
    Then I see error message "Unable to generate suggestions. Please try again."

  # Sub-feature: Report Export Failures
  Scenario: Handle report download failure
    Given suggestions are complete
    When I click to download report
    And the download fails
    Then I see error message "Unable to download report. Please try again."
    And I can view suggestions on screen as fallback
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

  # ============================================================
  # NEGATIVE TEST CASES: Supplementary Materials Failures
  # ============================================================

  # Sub-feature: API Failures
  Scenario: Handle API timeout during cover letter generation
    Given I have a match with LP
    When I click "Generate Cover Letter"
    And the API times out
    Then I see error message "Cover letter generation timed out. Please try again."

  Scenario: Handle rate limit during materials generation
    Given I have generated many materials recently
    When I request any supplementary material
    And the API returns rate limit error
    Then I see error message "Please wait before generating more materials"

  # Sub-feature: Invalid Data
  Scenario: Handle invalid match ID for supplementary materials
    Given I navigate to supplementary materials with invalid match ID
    Then I see error message "Match not found"
    And I am redirected to match list

  # Sub-feature: Missing Fund Data
  Scenario: Handle no case studies available
    Given LP focuses on healthcare
    And my fund has no healthcare case studies
    When I request case study recommendations
    Then I see message "No matching case studies found"
    And I see option to add case studies

  Scenario: Handle no track record data
    Given my fund has no track record entries
    When I request track record highlights
    Then I see message "No track record data available"
    And I see link to add track record

  Scenario: Handle incomplete track record
    Given my fund has limited track record data
    When I request track record highlights
    Then I see warning "Limited track record data available"
    And available data is formatted

  # Sub-feature: Missing LP Data
  Scenario: Handle LP with no check size data
    Given LP has no check size information
    When I request track record highlights
    Then I see message "LP check size unknown - showing all deals"
    And all track record is displayed

  Scenario: Handle LP with no sector focus
    Given LP has no sector focus data
    When I request case study recommendations
    Then I see message "LP sector focus unknown"
    And I am prompted to select relevant sectors

  # Sub-feature: Empty Content Generation
  Scenario: Handle empty cover letter generation
    Given I have a match with LP
    When I click "Generate Cover Letter"
    And the AI returns empty content
    Then I see error message "Unable to generate cover letter. Please try again."

  # Sub-feature: PDF Export Failures
  Scenario: Handle PDF export failure for supplementary materials
    When I finalize supplementary materials
    And I click "Export as PDF"
    And the export fails
    Then I see error message "Unable to create PDF. Please try again."
    And I see option to export as text/HTML instead

  Scenario: Handle export with missing content
    When I finalize supplementary materials
    And some sections are empty
    Then I see warning "Some sections are empty"
    And I can proceed or fill in missing sections
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

  # ============================================================
  # NEGATIVE TEST CASES: PPTX Modification Failures
  # ============================================================

  # Sub-feature: File Parsing Failures
  Scenario: Handle corrupt PPTX file
    Given I uploaded a corrupt PPTX file
    When AI tries to analyze it
    Then I see error message "Unable to read deck file. Please upload a valid PPTX."
    And I can upload a different file

  Scenario: Handle password-protected PPTX
    Given I uploaded a password-protected PPTX
    When AI tries to analyze it
    Then I see error message "This deck is password-protected. Please remove protection and re-upload."

  Scenario: Handle unsupported file format
    Given I uploaded a Keynote or Google Slides file
    When AI tries to analyze it
    Then I see error message "Unsupported format. Please convert to PPTX."
    And I see supported formats list

  Scenario: Handle very large PPTX file
    Given I uploaded a PPTX file larger than 50MB
    When AI tries to analyze it
    Then I see error message "File too large. Maximum size is 50MB."
    And I see tips for reducing file size

  Scenario: Handle PPTX with unsupported elements
    Given I uploaded a PPTX with embedded videos or 3D objects
    When AI analyzes it
    Then I see warning "Some elements cannot be modified (videos, 3D objects)"
    And analysis continues with supported elements

  # Sub-feature: API Failures
  Scenario: Handle API timeout during slide modification
    Given I requested a slide modification
    And the API times out
    Then I see error message "Modification timed out. Please try again."
    And original deck is unchanged

  Scenario: Handle rate limit during modification
    Given I have made many modification requests
    When I request another modification
    And the API returns rate limit error
    Then I see error message "Please wait before making more changes"

  # Sub-feature: Invalid Data
  Scenario: Handle invalid match ID for deck modification
    Given I navigate to deck modification with invalid match ID
    Then I see error message "Match not found"
    And I am redirected to match list

  # Sub-feature: Missing LP Data
  Scenario: Handle LP with no data for personalization
    Given I want to add an LP-specific slide
    And the LP has minimal profile data
    When I request modification
    Then I see warning "Limited LP data - slide will be generic"
    And I can proceed or cancel

  # Sub-feature: Modification Failures
  Scenario: Handle slide addition failure
    Given I want to add a new slide
    When AI tries to add the slide
    And the operation fails
    Then I see error message "Unable to add slide. Please try again."
    And original deck is unchanged

  Scenario: Handle slide reorder failure
    Given AI suggests moving ESG earlier
    When I approve the change
    And the reorder fails
    Then I see error message "Unable to reorder slides. Please try again."
    And original order is preserved

  Scenario: Handle formatting loss during modification
    Given AI modifies the deck
    When modification completes
    And fonts or colors are different from original
    Then I see warning "Some formatting may have changed"
    And I can preview changes before downloading

  # Sub-feature: Download Failures
  Scenario: Handle modified PPTX download failure
    Given modifications are complete
    When I click to download
    And the download fails
    Then I see error message "Download failed. Please try again."
    And modified deck is still available

  Scenario: Handle modified PPTX corruption
    Given modifications are complete
    When I download the PPTX
    And the file is corrupt
    Then I can request regeneration
    And original deck is still available
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

  # ============================================================
  # NEGATIVE TEST CASES: Match Results View Failures
  # ============================================================

  # Sub-feature: Loading Failures
  Scenario: Handle match list loading failure
    Given I navigate to match results
    And the API fails to load matches
    Then I see error message "Unable to load matches. Please try again."
    And I see "Retry" button

  Scenario: Handle match list timeout
    Given I navigate to match results
    And the request times out
    Then I see error message "Loading took too long. Please try again."
    And I see "Retry" button

  # Sub-feature: Invalid Data
  Scenario: Handle invalid fund ID for matches
    Given I navigate to matches with invalid fund ID
    Then I see error message "Fund not found"
    And I am redirected to fund list

  Scenario: Handle no matches found
    Given my fund has no matches
    When I view match results
    Then I see message "No matches found"
    And I see suggestions for improving matches

  # Sub-feature: Score Display Issues
  Scenario: Handle missing score data
    Given a match has no score calculated
    When I view the match
    Then I see "Score pending" indicator
    And I see option to trigger scoring

  Scenario: Handle invalid score value
    Given a match has an invalid score (null or NaN)
    When I view the match
    Then score displays as "N/A"
    And match is still viewable

  # Sub-feature: Explanation Failures
  Scenario: Handle explanation generation failure
    When I click "Why this match?"
    And the API fails to generate explanation
    Then I see error message "Unable to load explanation. Please try again."
    And I can view other match details

  Scenario: Handle empty explanation
    When I click "Why this match?"
    And the AI returns empty explanation
    Then I see message "Explanation not available"
    And I see the score breakdown instead

  # Sub-feature: Action Failures
  Scenario: Handle add to shortlist failure
    When I click "Add to Shortlist"
    And the operation fails
    Then I see error message "Unable to add to shortlist. Please try again."
    And match remains in original state

  Scenario: Handle dismiss failure
    When I click "Dismiss"
    And the operation fails
    Then I see error message "Unable to dismiss match. Please try again."
    And match remains visible

  Scenario: Handle generate pitch for deleted match
    Given I click "Generate Pitch"
    And the match was deleted by another process
    Then I see error message "This match no longer exists"
    And match list is refreshed

  # Sub-feature: Filter Errors
  Scenario: Handle invalid filter value
    When I enter invalid minimum score "abc"
    Then I see validation error "Please enter a valid number"
    And filter is not applied

  Scenario: Handle filter with no results
    Given I have matches
    When I set minimum score to 100
    And no matches have score 100
    Then I see message "No matches meet your filter criteria"
    And I see option to adjust filters

  Scenario: Handle filter persistence failure
    When I set filters
    And I refresh the page
    And filter state fails to restore
    Then filters reset to default
    And I see all matches
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

  # ============================================================
  # NEGATIVE TEST CASES: Email Review Failures
  # ============================================================

  # Sub-feature: Clipboard Failures
  Scenario: Handle clipboard permission denied
    Given I reviewed and approved the email
    When I click "Copy to Clipboard"
    And browser denies clipboard permission
    Then I see error message "Clipboard access denied. Please copy manually."
    And email text is displayed in a selectable text area

  Scenario: Handle clipboard API not available
    Given I am using an older browser
    When I click "Copy to Clipboard"
    And Clipboard API is not supported
    Then I see fallback "Select All" functionality
    And instructions for manual copy

  Scenario: Handle clipboard write failure
    Given I reviewed and approved the email
    When I click "Copy to Clipboard"
    And the clipboard write operation fails
    Then I see error message "Copy failed. Please try again or copy manually."
    And I can retry

  Scenario: Handle copy with extremely long email
    Given email content is 10,000+ characters
    When I click "Copy to Clipboard"
    Then entire content is copied
    And I see "Copied!" confirmation
    Or I see warning if clipboard has size limits

  # Sub-feature: Activity Log Failures
  Scenario: Handle activity log save failure
    When I copy an email
    And the log save operation fails
    Then email is still copied successfully
    And I see warning "Activity could not be logged"
    And I can manually log the action

  Scenario: Handle activity log load failure
    When I try to view the activity log
    And the log fails to load
    Then I see error message "Unable to load activity log. Please try again."

  # Sub-feature: Edit Failures
  Scenario: Handle edit save failure
    Given I am editing an email
    When I make changes and click "Save"
    And the save operation fails
    Then I see error message "Unable to save changes. Please try again."
    And my edits are preserved in the editor

  Scenario: Handle edit with invalid content
    Given I am editing an email
    When I enter content with malicious scripts
    Then scripts are sanitized
    And email is saved safely

  Scenario: Handle discard without confirmation
    Given I made significant edits to an email
    When I click "Discard"
    Then I see confirmation "Are you sure? Your changes will be lost."
    And I must confirm to proceed

  # Sub-feature: Review State Failures
  Scenario: Handle review state not persisted
    Given I generated an email
    When I refresh the page
    And review state fails to restore
    Then I see the generated email
    And review confirmation is required again

  Scenario: Handle concurrent edit conflict
    Given I am editing an email in two browser tabs
    When I save in one tab
    And then try to save in the other tab
    Then I see warning "This email was modified in another session"
    And I can merge or overwrite changes
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

  # ============================================================
  # NEGATIVE E2E SCENARIOS: Error Recovery Journeys
  # ============================================================

  Scenario: Handle API failure during complete journey
    Given I have matches for my fund
    And I shortlisted LPs for outreach

    # Summary generation fails
    When I select "CalPERS"
    And I click "Generate Summary"
    And the API times out
    Then I see error message with retry option

    When I click "Retry"
    Then summary generates successfully
    And I can continue the journey

  Scenario: Handle partial journey completion with network issues
    Given I have matches for my fund
    And I successfully generated a summary for CalPERS

    # Network fails during email generation
    When I click "Generate Email"
    And network connection drops mid-generation
    Then I see error message "Connection lost"

    When I reconnect and retry
    Then email generates successfully
    And previous summary is still available

  Scenario: Handle clipboard failure in outreach journey
    Given I have generated summary and email
    And I reviewed both documents

    # Clipboard copy fails
    When I click "Copy to Clipboard"
    And clipboard permission is denied
    Then I see fallback option to select and copy manually
    And I can complete the journey using manual copy

  Scenario: Handle session timeout during long journey
    Given I am partway through outreach for multiple LPs
    And I leave the computer for 30 minutes

    When I return and try to continue
    And my session has expired
    Then I see message "Session expired. Please log in again."
    And after login, I am returned to my shortlist
    And previously generated content is preserved (if saved)

  Scenario: Handle rate limit during batch outreach
    Given I am generating pitches for multiple LPs in quick succession

    When I try to generate the 6th summary in 2 minutes
    And rate limit is hit
    Then I see warning "Slow down! Please wait before generating more."
    And I see countdown timer
    And I can continue after the wait period

  Scenario: Handle PDF export failure after successful generation
    Given I successfully generated a summary

    When I click "Download PDF"
    And PDF generation fails
    Then I see error message
    And I can retry PDF download
    And original summary content is not lost
    And I can copy summary as plain text as fallback

  Scenario: Handle multiple failures with graceful degradation
    Given I am creating outreach for an LP

    When summary generation fails
    Then I can still generate email without summary

    When email generation also fails
    Then I can use an existing template

    When template loading fails
    Then I can write email manually
    And the journey can still be completed
```

---

## Additional Negative Test Scenarios

```gherkin
Feature: Negative Test Scenarios for Pitch Generation
  As a developer
  I want comprehensive negative test coverage
  So that the system handles all edge cases gracefully

  # ============================================================
  # @negative: OpenRouter API Failures
  # ============================================================

  @negative
  Scenario: Handle OpenRouter API timeout during summary generation
    Given I have a match with LP "CalPERS"
    When I click "Generate Summary"
    And the OpenRouter API does not respond within 30 seconds
    Then the request is cancelled
    And I see error message "Request timed out. The AI service is taking too long."
    And I see a "Retry" button
    And I see option to "Try with shorter content"
    And no partial content is saved

  @negative
  Scenario: Handle OpenRouter API timeout during email generation
    Given I have a match with LP "Harvard Endowment"
    When I click "Generate Email"
    And the OpenRouter API does not respond within 30 seconds
    Then the request is cancelled
    And I see error message "Email generation timed out. Please try again."
    And I can retry with the same parameters
    And previous form selections (tone, etc.) are preserved

  @negative
  Scenario: Handle OpenRouter rate limit with retry-after header
    Given I have made multiple API requests
    When I click "Generate Summary"
    And OpenRouter returns HTTP 429 with Retry-After: 60 header
    Then I see error message "Rate limit exceeded. Please wait 60 seconds."
    And I see a countdown timer showing remaining wait time
    And the "Generate" button is disabled until countdown completes
    And I see option to upgrade plan for higher limits

  @negative
  Scenario: Handle OpenRouter rate limit without retry-after header
    Given I have made multiple API requests
    When I click "Generate Email"
    And OpenRouter returns HTTP 429 without Retry-After header
    Then I see error message "Too many requests. Please try again in a few minutes."
    And I see default wait time of 60 seconds
    And I can manually retry after waiting

  @negative
  Scenario: Handle OpenRouter content filter rejection
    Given I have a match with LP "Controversial Fund"
    And the LP profile contains potentially flagged content
    When I click "Generate Summary"
    And OpenRouter returns content filter rejection
    Then I see error message "Content could not be generated due to policy restrictions."
    And I see option to "Review LP Profile" for problematic content
    And the specific flagged content is logged for admin review
    And I can try generating with modified LP data

  @negative
  Scenario: Handle OpenRouter content filter on generated output
    Given I have a match with LP "CalPERS"
    When I click "Generate Summary"
    And OpenRouter generates content that triggers output filter
    Then I see error message "Generated content was filtered. Regenerating..."
    And the system automatically retries with modified prompt
    And if retry fails, I see "Unable to generate appropriate content"
    And I can manually create content instead

  @negative
  Scenario: Handle OpenRouter model unavailable
    Given I have a match with LP "CalPERS"
    When I click "Generate Summary"
    And the requested model is unavailable on OpenRouter
    Then I see error message "AI model temporarily unavailable."
    And I see option to use fallback model
    And fallback model selection is logged

  @negative
  Scenario: Handle OpenRouter insufficient credits
    Given our OpenRouter account has no remaining credits
    When I click "Generate Summary"
    And OpenRouter returns HTTP 402 Payment Required
    Then I see error message "AI service credits exhausted. Please contact support."
    And error is logged for admin notification
    And I cannot generate any AI content
    And I see option to use cached/template content

  @negative
  Scenario: Handle OpenRouter authentication failure
    Given the OpenRouter API key is invalid or revoked
    When I click "Generate Summary"
    And OpenRouter returns HTTP 401 Unauthorized
    Then I see error message "Configuration error. Please contact support."
    And no API key details are shown to user
    And error is logged with full details for admin
    And all AI generation features are disabled

  # ============================================================
  # @negative: LLM Response Parsing Errors
  # ============================================================

  @negative
  Scenario: Handle malformed JSON in LLM response
    Given I have a match with LP "CalPERS"
    When I click "Generate Summary"
    And the LLM returns invalid JSON (unclosed braces, missing quotes)
    Then I see error message "Error processing AI response. Retrying..."
    And the system automatically retries up to 3 times
    And if all retries fail, I see "Unable to parse AI response. Please try again."
    And the malformed response is logged for debugging

  @negative
  Scenario: Handle LLM response with wrong schema
    Given I have a match with LP "CalPERS"
    When I click "Generate Summary"
    And the LLM returns valid JSON but missing required fields
    Then I see warning "AI response incomplete"
    And I see which fields could not be generated:
      | Field |
      | track_record |
      | team_section |
    And I can regenerate specific sections
    And partial content is displayed for available fields

  @negative
  Scenario: Handle LLM response with unexpected field types
    Given I have a match with LP "CalPERS"
    When I click "Generate Summary"
    And the LLM returns a string where an object was expected
    Then the system attempts type coercion
    And if coercion fails, I see error message "Invalid response format"
    And I can retry generation

  @negative
  Scenario: Handle truncated LLM response
    Given I have a match with LP "CalPERS"
    When I click "Generate Summary"
    And the LLM response is cut off mid-sentence (token limit reached)
    Then I see warning "Content was truncated due to length limits"
    And I see the partial content with "[Content truncated]" marker
    And I can request "Continue generation" to get remaining content
    And I can edit the truncation point manually

  @negative
  Scenario: Handle LLM response with encoding issues
    Given I have a match with LP "International LP with Unicode name"
    When I click "Generate Summary"
    And the LLM returns content with invalid UTF-8 sequences
    Then invalid characters are replaced with replacement character
    And I see warning "Some characters could not be displayed correctly"
    And the content is still usable
    And I can edit to fix character issues

  @negative
  Scenario: Handle LLM response containing only whitespace
    Given I have a match with LP "CalPERS"
    When I click "Generate Summary"
    And the LLM returns a response that is only whitespace or empty strings
    Then I see error message "AI returned empty content. Please try again."
    And the system logs this as a failed generation
    And I can retry with different parameters

  @negative
  Scenario: Handle LLM response with HTML/script injection
    Given I have a match with LP "CalPERS"
    When I click "Generate Summary"
    And the LLM returns content containing <script> tags or HTML
    Then all HTML/script content is sanitized
    And content is rendered as plain text
    And no scripts are executed
    And I see the safe, sanitized content

  @negative
  Scenario: Handle LLM response exceeding maximum size
    Given I have a match with LP "CalPERS"
    When I click "Generate Summary"
    And the LLM returns content larger than 100KB
    Then content is truncated to safe limit
    And I see warning "Content exceeded maximum length and was truncated"
    And I can request a shorter version

  # ============================================================
  # @negative: Clipboard Permission Denied
  # ============================================================

  @negative
  Scenario: Handle clipboard permission denied on first attempt
    Given an email is generated for LP "CalPERS"
    When I click "Copy to Clipboard"
    And browser shows permission prompt
    And I click "Deny"
    Then I see error message "Clipboard access denied"
    And I see instructions "Please allow clipboard access in your browser settings"
    And I see a text area with content pre-selected for manual copy
    And I see button "Select All for Manual Copy"

  @negative
  Scenario: Handle clipboard permission denied after previous grant
    Given I previously granted clipboard permission
    And permission was revoked in browser settings
    When I click "Copy to Clipboard"
    Then I see error message "Clipboard permission was revoked"
    And I see link to browser settings instructions
    And I see fallback text area for manual copy

  @negative
  Scenario: Handle clipboard API not supported in browser
    Given I am using an older browser without Clipboard API
    When I click "Copy to Clipboard"
    Then I see message "Your browser does not support automatic copy"
    And a text area appears with all content
    And the text is automatically selected
    And I see instructions "Press Ctrl+C (or Cmd+C on Mac) to copy"

  @negative
  Scenario: Handle clipboard write failure due to security context
    Given I am viewing the page in an iframe or insecure context
    When I click "Copy to Clipboard"
    And the browser blocks clipboard access due to security
    Then I see error message "Copy not available in this context"
    And I see fallback manual copy option
    And I see suggestion to open in new window

  @negative
  Scenario: Handle clipboard already in use by another application
    Given another application has locked the clipboard
    When I click "Copy to Clipboard"
    And the write operation fails
    Then I see error message "Clipboard is busy. Please try again."
    And I can retry after a moment
    And manual copy fallback is available

  @negative
  Scenario: Handle partial clipboard copy failure
    Given I have a very long email content
    When I click "Copy to Clipboard"
    And only part of the content is copied (browser limit)
    Then I see warning "Content may be truncated in clipboard"
    And I see the character count that was copied
    And I see option to copy in sections

  # ============================================================
  # @negative: Pitch Generation with Stale LP Data
  # ============================================================

  @negative
  Scenario: Generate pitch when LP data was updated after match creation
    Given I have a match with LP "CalPERS" created 30 days ago
    And CalPERS's investment focus changed from "Technology" to "Healthcare"
    When I click "Generate Summary"
    Then I see warning "LP data may have changed since this match was created"
    And I see "Last updated: 30 days ago"
    And I see option to "Refresh LP Data" before generating
    And I can proceed with current data if desired

  @negative
  Scenario: Generate pitch when LP profile was deleted
    Given I have a match with LP "Former Investor"
    And the LP profile was deleted from the database
    When I click "Generate Summary"
    Then I see error message "LP profile no longer exists"
    And I see option to remove this match from my list
    And the match is flagged as orphaned

  @negative
  Scenario: Generate pitch when LP contact information is outdated
    Given I have a match with LP "CalPERS"
    And the LP contact email was marked as bounced
    When I click "Generate Email"
    Then I see warning "Contact email may be invalid (last bounce: 2 weeks ago)"
    And I can proceed with generation
    And I see suggestion to verify contact before sending

  @negative
  Scenario: Generate pitch when LP investment mandate expired
    Given I have a match with LP "Seasonal Fund"
    And the LP's current fundraising period ended
    When I click "Generate Summary"
    Then I see warning "LP's investment mandate may have expired"
    And I see "Mandate end date: [past date]"
    And I can still generate but with caution notice
    And content includes caveat about timing

  @negative
  Scenario: Generate pitch when LP AUM data is stale
    Given I have a match with LP "Growth Endowment"
    And the LP's AUM data is from 2 years ago
    When I click "Generate Summary"
    Then I see warning "LP financial data may be outdated (2 years old)"
    And summary includes disclaimer about data freshness
    And I see option to update LP data

  @negative
  Scenario: Generate pitch when match score was invalidated
    Given I have a match with LP "CalPERS" with score 92
    And the scoring algorithm was updated
    And the match score is now marked as "stale"
    When I view the match and click "Generate Summary"
    Then I see warning "Match score needs recalculation"
    And I see option to "Recalculate Score" before generating
    And I can proceed with potentially inaccurate score

  @negative
  Scenario: Generate pitch when multiple LP fields are stale
    Given I have a match with LP "Old Data LP"
    And the following data is more than 1 year old:
      | Field | Age |
      | Investment strategy | 18 months |
      | Geographic focus | 14 months |
      | Contact information | 12 months |
      | AUM | 24 months |
    When I click "Generate Summary"
    Then I see warning "Multiple LP data fields are outdated"
    And I see summary of stale fields with ages
    And I see strong recommendation to update before generating
    And I can proceed at my own risk

  @negative
  Scenario: Generate pitch with conflicting LP data versions
    Given I have a match with LP "CalPERS"
    And there are two versions of LP data (manual vs. imported)
    And versions conflict on investment focus
    When I click "Generate Summary"
    Then I see warning "Conflicting LP data detected"
    And I see comparison of conflicting values
    And I must select which version to use
    And selected version is used for generation

  # ============================================================
  # @negative: Email Template Injection Attempts
  # ============================================================

  @negative
  Scenario: Handle XSS injection in LP name field
    Given I have a match with LP named "<script>alert('xss')</script>"
    When I click "Generate Email"
    Then the LP name is HTML-escaped in the email
    And no script is executed in preview
    And copied content contains escaped characters
    And I see sanitized LP name in the email

  @negative
  Scenario: Handle SQL injection in email personalization
    Given I have a match with LP named "LP'; DROP TABLE users; --"
    When I click "Generate Email"
    Then the LP name is treated as literal text
    And no database operations are affected
    And email generates successfully with sanitized name

  @negative
  Scenario: Handle template variable injection in custom fields
    Given I am editing an email template
    And I enter "{{user.password}}" in a custom field
    When I save the template
    Then the template variable is escaped or rejected
    And I see error "Invalid template syntax" if rejected
    And no sensitive data is ever exposed

  @negative
  Scenario: Handle newline injection for email header manipulation
    Given I have a match with LP named "LP\r\nBcc: attacker@evil.com\r\n"
    When I click "Generate Email"
    Then newlines and carriage returns are stripped from LP name
    And no additional headers can be injected
    And email content is safe for all email clients

  @negative
  Scenario: Handle HTML injection in email subject
    Given I am editing the email subject
    And I enter "<img src=x onerror=alert('xss')>"
    When I save the email
    Then HTML is stripped from the subject
    And only plain text is saved
    And copied subject is safe

  @negative
  Scenario: Handle Unicode homograph attack in LP name
    Given I have a match with LP named "СаlPERS" (using Cyrillic 'С' and 'а')
    When I click "Generate Email"
    Then the system detects potential homograph attack
    And I see warning "LP name contains unusual characters"
    And I can review and confirm the name

  @negative
  Scenario: Handle CRLF injection in email body
    Given I am editing an email body
    And I enter content with embedded CRLF sequences
    When I copy to clipboard
    Then CRLF sequences are normalized
    And email body cannot break email format
    And content pastes safely in email clients

  @negative
  Scenario: Handle template variable escape attempts
    Given I am generating an email
    And the LP profile contains "{{config.api_key}}" in notes
    When I click "Generate Email"
    Then template variables in LP data are escaped
    And I see literal "{{config.api_key}}" in email
    And no system variables are exposed

  @negative
  Scenario: Handle malicious URL in LP website field
    Given I have a match with LP with website "javascript:alert('xss')"
    When I click "Generate Email"
    And the email references LP website
    Then malicious URLs are detected and removed
    And I see warning "Invalid URL removed from LP profile"
    And email does not contain malicious link

  @negative
  Scenario: Handle oversized injection payload
    Given I have a match with LP named "[1MB of repeated characters]"
    When I click "Generate Email"
    Then the LP name is truncated to safe length
    And I see warning "LP name was truncated"
    And system resources are not exhausted

  # ============================================================
  # @negative: Concurrent Pitch Edits
  # ============================================================

  @negative
  Scenario: Handle simultaneous edit in two browser tabs
    Given I generated an email for LP "CalPERS"
    And I have the email open in two browser tabs
    When I edit the subject in Tab A to "Subject A"
    And I edit the subject in Tab B to "Subject B"
    And I save in Tab A first
    And then I try to save in Tab B
    Then Tab B shows warning "This email was modified in another session"
    And I see diff showing changes made in Tab A
    And I can choose to:
      | Option | Result |
      | Keep mine | Overwrites Tab A changes |
      | Keep theirs | Discards my Tab B changes |
      | Merge | Opens merge editor |

  @negative
  Scenario: Handle concurrent edit by same user on different devices
    Given I generated an email for LP "CalPERS"
    And I am editing on my laptop
    And I open the same email on my phone
    When I make conflicting edits on both devices
    Then the last save wins (optimistic locking)
    And the overwritten device shows "Content updated from another session"
    And I can see version history

  @negative
  Scenario: Handle concurrent summary generation for same match
    Given I have a match with LP "CalPERS"
    When I click "Generate Summary" in one tab
    And I click "Generate Summary" in another tab before first completes
    Then only one generation runs
    And second request shows "Generation already in progress"
    And both tabs receive the same result when ready

  @negative
  Scenario: Handle edit during regeneration
    Given I have a generated summary for LP "CalPERS"
    And I click "Regenerate"
    When I also try to edit the current content
    Then editing is disabled during regeneration
    And I see message "Please wait for regeneration to complete"
    And I can cancel regeneration to continue editing

  @negative
  Scenario: Handle concurrent template save with same name
    Given I am saving an email as template "Tech Outreach"
    And another user saves a template with same name simultaneously
    When both saves are processed
    Then one save succeeds and one fails
    And the failed save shows "Template name already taken"
    And I can choose a different name

  @negative
  Scenario: Handle edit timeout due to session lock
    Given I started editing an email 30 minutes ago
    And the editing session has a 15-minute lock timeout
    When another user tries to edit the same email
    Then my lock has expired
    And the other user can take the lock
    And when I try to save, I see "Your editing session expired"
    And my changes are preserved locally
    And I can request a new lock

  @negative
  Scenario: Handle browser crash during edit
    Given I am editing an email for LP "CalPERS"
    And I have unsaved changes
    When my browser crashes unexpectedly
    And I reopen the browser and return to the page
    Then I see "Unsaved changes recovered" (if autosave enabled)
    And I can restore my previous edits
    Or I see "Previous session had unsaved changes" with recovery option

  @negative
  Scenario: Handle concurrent pitch copy operations
    Given I have a generated email for LP "CalPERS"
    When I click "Copy to Clipboard" rapidly multiple times
    Then only one copy operation runs at a time
    And subsequent clicks are debounced
    And I see single "Copied!" confirmation
    And clipboard contains correct content

  @negative
  Scenario: Handle version conflict during collaborative edit
    Given I am on a team with shared access to pitch content
    And team member Alice is editing the same email
    When we both make changes simultaneously
    Then we see real-time presence indicators (if supported)
    Or we see conflict resolution on save
    And no changes are silently lost
    And version history tracks all changes

  @negative
  Scenario: Handle delete during concurrent edit
    Given I am editing an email for LP "CalPERS"
    And another team member deletes the match
    When I try to save my edits
    Then I see error "This match no longer exists"
    And I see option to save content as draft
    And my work is not completely lost
```

---

## F-AGENT-04: Explanation Agent (Interaction Learning) [P1]

```gherkin
Feature: Explanation Agent Interaction Learning
  As the Explanation Agent
  I want to learn GP preferences from their interactions
  So that recommendations and pitches become personalized

  # ==========================================================================
  # Observing GP Interactions
  # ==========================================================================

  Scenario: Observe match shortlisting
    Given GP "Acme Capital" shortlists LP "CalPERS"
    When Explanation Agent observes the action
    Then interaction is logged:
      | gp_org_id | action_type | lp_org_id | timestamp |
    And implicit preference is recorded: "GP interested in pension LPs"

  Scenario: Observe match dismissal
    Given GP "Acme Capital" dismisses LP "Small Family Office"
    And GP selects reason "Check size too small"
    When Explanation Agent observes the action
    Then interaction is logged with reason
    And preference is updated: "GP prefers larger check sizes"

  Scenario: Observe pitch editing patterns
    Given GP generated email for LP "CalPERS"
    And GP edits email to shorten it by 50%
    When Explanation Agent analyzes edit
    Then pattern is detected: "GP prefers concise emails"
    And pitch_style_preference is updated

  Scenario: Observe explicit feedback
    Given GP marked a talking point as "not useful"
    When Explanation Agent processes feedback
    Then feedback is stored with context
    And future talking points are adjusted for this GP

  Scenario: Track time-based patterns
    Given GP typically engages between 9am-11am EST
    When Explanation Agent analyzes engagement times
    Then pattern is recorded
    And can be used for optimal notification timing

  # ==========================================================================
  # Learning GP Preferences
  # ==========================================================================

  Scenario: Learn email tone preference
    Given GP edited 5 emails to use more formal language
    When Explanation Agent aggregates patterns
    Then gp_learned_preferences records:
      | preference_type | preference_value | confidence | sample_size |
      | tone_preference | formal | 80% | 5 |

  Scenario: Learn LP type preference
    Given GP shortlisted 8 pension LPs and 2 endowments
    When Explanation Agent calculates preferences
    Then preference is stored:
      | preference_type | preference_value | confidence |
      | lp_type_preference | pension | 75% |

  Scenario: Learn sector emphasis preference
    Given GP always emphasizes healthcare deals in pitches
    When Explanation Agent analyzes edit patterns
    Then preference is stored:
      | preference_type | preference_value |
      | sector_emphasis | healthcare |

  Scenario: Learn track record presentation preference
    Given GP consistently adds more track record detail
    When pattern is detected
    Then preference is stored:
      | preference_type | preference_value |
      | content_preference | detailed_track_record |

  Scenario: Update scoring weight overrides
    Given GP consistently dismisses LPs with low ESG scores
    When Explanation Agent detects pattern (10+ dismissals)
    Then scoring_weight_overrides is updated:
      | factor | weight_adjustment |
      | esg_alignment | +20% |
    And future matches for this GP weight ESG higher

  # ==========================================================================
  # Applying Learned Preferences
  # ==========================================================================

  Scenario: Apply tone preference to email generation
    Given GP has learned preference tone_preference = "concise"
    When GP generates new email
    Then AI uses concise tone by default
    And email is shorter than standard

  Scenario: Apply LP type preference to match ranking
    Given GP prefers pension LPs
    When GP views matches
    Then pension LPs are ranked higher
    And ranking adjustment is explainable

  Scenario: Suggest talking points based on history
    Given GP found "ESG commitment" talking point effective (positive feedback)
    When generating new pitch for similar LP
    Then ESG talking point is included prominently
    And source is noted: "Based on your past successful pitches"

  Scenario: Personalize match explanations
    Given GP prefers detailed track record analysis
    When GP views "Why this match?" explanation
    Then explanation emphasizes track record alignment
    And other factors are summarized more briefly

  # ==========================================================================
  # Preference Decay and Updates
  # ==========================================================================

  Scenario: Decay old preferences
    Given preference was learned 12 months ago
    And no recent interactions confirm it
    When preference decay runs
    Then confidence is reduced by 20%
    And preference requires re-confirmation

  Scenario: Override preference with new behavior
    Given GP previously preferred formal tone
    And GP's last 3 emails used warm tone
    When Explanation Agent updates preferences
    Then tone_preference changes to "warm"
    And old preference is archived

  Scenario: Handle conflicting signals
    Given GP shortlists ESG LPs but also non-ESG LPs
    When Explanation Agent analyzes
    Then preference is marked as "mixed"
    And no strong weight adjustment is made

  # ==========================================================================
  # Feedback on LP Profiles
  # ==========================================================================

  Scenario: Record talking point effectiveness
    Given GP marked talking point "Mention their recent commitment" as helpful
    When feedback is processed
    Then LP profile is updated:
      | talking_point | effectiveness | source_gp_count |
      | recent_commitment | positive | 1 |
    And future pitches for this LP include similar points

  Scenario: Aggregate feedback across GPs
    Given 5 GPs found "ESG track record" talking point effective for CalPERS
    When aggregation runs
    Then CalPERS profile notes:
      | effective_talking_points |
      | ESG track record (5 confirmations) |

  Scenario: Record ineffective talking points
    Given GP marked talking point as "inaccurate"
    When feedback is processed
    Then talking point is flagged for review
    And confidence is reduced for similar points

  # ==========================================================================
  # NEGATIVE TESTS: Explanation Agent Failures
  # ==========================================================================

  @negative
  Scenario: Insufficient data for preference learning
    Given GP has only 2 interactions
    When Explanation Agent attempts to learn preferences
    Then no preferences are stored (below threshold of 5)
    And data is accumulated for future learning

  @negative
  Scenario: Preference inference is wrong
    Given system inferred GP prefers pension LPs
    But GP explicitly marks preference as incorrect
    When GP provides correction
    Then inferred preference is deleted
    And feedback is logged for model improvement

  @negative
  Scenario: Handle interaction tracking failure
    Given GP shortlists an LP
    When interaction logging fails (database error)
    Then action still completes for user
    And interaction is queued for retry
    And error is logged

  @negative
  Scenario: Preference storage conflict
    Given two team members have conflicting preferences
    When both are logged
    Then preferences are stored per-user initially
    And organization-level preference uses majority

  @negative
  Scenario: Edge case: GP reverses decisions
    Given GP shortlists then un-shortlists same LP
    When Explanation Agent processes
    Then net signal is neutral
    And no preference is inferred from this interaction

  @negative
  Scenario: Stale interactions excluded
    Given GP interaction is 18 months old
    When preference calculation runs
    Then old interaction is weighted less
    And recent interactions dominate preference

  @negative
  Scenario: GP explicitly opts out of learning
    Given GP sets allow_interaction_learning = false
    When GP performs actions
    Then interactions are not logged for learning
    And GP receives standard (non-personalized) experience

  @negative
  Scenario: Cross-company preference leakage
    Given GP A's preferences are being learned
    When system stores preferences
    Then preferences are isolated to GP A's organization
    And no preference data is shared with other companies
```

---

## F-MATCH-07: Enhanced Match Explanations with Learning [P1]

```gherkin
Feature: Enhanced Match Explanations with Learning
  As a GP
  I want match explanations to improve based on my feedback
  So that explanations become more relevant over time

  # ==========================================================================
  # Feedback-Informed Explanations
  # ==========================================================================

  Scenario: Explanation emphasizes factors GP cares about
    Given GP has learned preference for ESG factors
    When GP views match explanation
    Then ESG alignment is prominently featured
    And explanation structure reflects GP preferences

  Scenario: Explanation includes previously effective talking points
    Given previous pitches to similar LPs were successful
    When generating explanation
    Then talking points mention proven approaches
    And source is cited: "Similar approach worked with [LP type]"

  Scenario: Explanation warns about known LP sensitivities
    Given Explanation Agent learned "CalPERS is sensitive to high fees"
    When GP views CalPERS explanation
    Then concerns section highlights fee discussion
    And suggested talking points address fee value proposition

  Scenario: Explanation adapts to GP's experience level
    Given GP has been on platform 2 years with 100+ matches
    When generating explanation
    Then explanation uses industry jargon appropriately
    And basic concepts are not over-explained

  # ==========================================================================
  # Explanation Feedback Loop
  # ==========================================================================

  Scenario: GP rates explanation quality
    Given GP views match explanation
    When GP clicks "Was this helpful?"
    Then options are:
      | Yes, very helpful |
      | Somewhat helpful |
      | Not helpful |
    And rating is stored

  Scenario: GP provides specific feedback
    Given GP rated explanation as "Not helpful"
    When GP is prompted for details
    Then GP can select:
      | "Missing key information about LP" |
      | "Talking points were off-base" |
      | "Too generic" |
      | "Other" (free text) |
    And feedback is used to improve future explanations

  Scenario: Explanation improves from feedback
    Given GP indicated "Too generic" for 3 explanations
    When Explanation Agent learns from feedback
    Then future explanations include more specific details
    And personalization increases

  # ==========================================================================
  # NEGATIVE TESTS: Enhanced Explanation Failures
  # ==========================================================================

  @negative
  Scenario: No learned preferences available
    Given GP is new with no interaction history
    When generating match explanation
    Then standard explanation is generated
    And no personalization is applied

  @negative
  Scenario: Conflicting feedback signals
    Given GP rated same explanation type as "helpful" and "not helpful"
    When processing feedback
    Then most recent feedback takes precedence
    And conflicting signals are flagged for review

  @negative
  Scenario: Feedback storage fails
    Given GP provides explanation feedback
    When database write fails
    Then feedback is queued for retry
    And user sees "Feedback received"
    And experience is not degraded
```

---

## F-PITCH-CRITIC: Pitch Generation Debate System

The pitch generation system uses Generator-Critic-Synthesizer pattern to ensure
high-quality, factually accurate, personalized content.

```gherkin
Feature: F-PITCH-CRITIC - Pitch Quality Assurance
  As the pitch generation system
  I want to validate all generated content through a critic agent
  So that pitches are factually accurate and highly personalized

  Background:
    Given the pitch debate system is enabled
    And quality thresholds are configured

  # ==========================================================================
  # Core Generator-Critic Flow
  # ==========================================================================

  Scenario: Successful pitch with high quality
    Given GP requests pitch for LP "CalPERS"
    When Pitch Generator creates initial draft
    And Pitch Critic evaluates quality
    Then critique includes:
      | dimension        | score   | description                      |
      | accuracy         | 0-100   | Every claim matches source data  |
      | personalization  | 0-100   | Specific LP references, not generic |
      | tone             | 0-100   | Appropriate for LP type          |
      | structure        | 0-100   | Clear value prop, logical flow   |
    And overall_score >= 85
    And recommendation = "approve"
    And pitch is delivered to GP

  Scenario: Pitch Generator creates personalized draft
    Given Fund A is growth equity focused on SaaS
    And LP CalPERS has mandate for "technology, growth"
    When Pitch Generator runs
    Then draft includes:
      | element              | personalization                           |
      | opening              | References CalPERS by name                |
      | thesis alignment     | Mentions CalPERS tech allocation target   |
      | track record         | Highlights exits relevant to CalPERS      |
      | ESG                  | Addresses CalPERS ESG requirements        |
      | closing              | References CalPERS decision timeline      |
    And no generic placeholder text remains

  Scenario: Pitch Critic identifies quality issues
    Given Pitch Generator creates draft
    When Pitch Critic evaluates
    Then issues_found may include:
      | issue_type         | example                                   |
      | factual_error      | "Claim: LP committed $50M to Fund A" (not in DB) |
      | generic_content    | "As a leading institutional investor..."  |
      | tone_mismatch      | "Too casual for pension fund audience"    |
      | missing_data       | "No mention of LP's stated sector focus"  |
      | hallucination      | "Invented mutual connection"              |
    And issue_severity is assigned

  Scenario: Content Synthesizer approves with notes
    Given Pitch Critic overall_score = 78
    And issues_found contains only minor items
    When Content Synthesizer evaluates
    Then recommendation = "approve_with_notes"
    And improvement_notes are attached
    And pitch is delivered with suggestions
    And GP can apply suggestions before use

  # ==========================================================================
  # Quality Tiers and Actions
  # ==========================================================================

  Scenario: Excellent quality - immediate approval
    Given Pitch Critic overall_score = 92
    And no critical issues found
    Then recommendation = "approve"
    And pitch is delivered immediately
    And no regeneration needed

  Scenario: Good quality - approve with suggestions
    Given Pitch Critic overall_score = 75
    And issues_found = ["Could include more specific track record data"]
    Then recommendation = "approve_with_notes"
    And suggestions are attached
    And pitch is usable but could be improved

  Scenario: Needs revision - regenerate
    Given Pitch Critic overall_score = 58
    And issues_found contains "generic_content" (moderate severity)
    Then recommendation = "regenerate"
    And feedback is passed to Pitch Generator
    And regeneration attempt is made
    And iteration_count increments

  Scenario: Reject - fallback to template
    Given Pitch Critic overall_score = 35
    And issues_found contains "factual_error" (critical severity)
    And 3 regeneration attempts have failed
    Then recommendation = "reject"
    And fallback template is used
    And human review is flagged
    And error is logged for prompt improvement

  # ==========================================================================
  # Regeneration Flow
  # ==========================================================================

  Scenario: Regeneration with critic feedback
    Given first pitch attempt scored 55
    And Pitch Critic identified "too generic, missing ESG section"
    When regeneration runs
    Then Pitch Generator receives critic feedback
    And new draft addresses specific issues
    And ESG section is added
    And second critique is performed

  Scenario: Successful regeneration
    Given first attempt scored 52
    When regeneration runs with feedback
    Then second attempt scores 78
    And regeneration is successful
    And pitch is approved

  Scenario: Multiple regeneration attempts
    Given regeneration limit = 3
    And first attempt scored 48
    And second attempt scored 55
    When third regeneration runs
    And scores 62
    Then pitch is delivered with "best effort" flag
    And human review is suggested
    And all 3 attempts are logged

  # ==========================================================================
  # Factual Accuracy Validation
  # ==========================================================================

  Scenario: Critic verifies claims against database
    Given pitch draft states "CalPERS has $450B AUM"
    When Pitch Critic runs fact-check
    And organizations.total_aum_bn for CalPERS = 450
    Then claim is verified
    And accuracy_score is not penalized

  Scenario: Critic catches hallucinated claim
    Given pitch draft states "We previously worked with CalPERS on Fund I"
    When Pitch Critic runs fact-check
    And no record exists in lp_commitments
    Then hallucination is flagged
    And issue_type = "factual_error"
    And issue_severity = "critical"
    And claim must be removed in regeneration

  Scenario: Critic validates statistics
    Given pitch draft states "Our Fund II returned 3.2x MOIC"
    When Pitch Critic cross-references
    And funds.track_record shows 3.2x MOIC for Fund II
    Then statistic is verified
    And no issue raised

  Scenario: Critic flags unverifiable claims
    Given pitch draft states "Industry leading returns"
    When Pitch Critic evaluates
    And no benchmark data exists to verify
    Then issue_type = "unverifiable_claim"
    And issue_severity = "minor"
    And suggestion to make claim specific

  # ==========================================================================
  # Personalization Scoring
  # ==========================================================================

  Scenario: High personalization score
    Given pitch includes:
      | element                          | count |
      | LP name mentions                 | 5     |
      | LP-specific data points          | 8     |
      | LP mandate references            | 3     |
      | Decision maker name              | 1     |
    Then personalization_score >= 85

  Scenario: Low personalization score
    Given pitch includes:
      | element                          | count |
      | LP name mentions                 | 1     |
      | LP-specific data points          | 0     |
      | Generic phrases                  | 5     |
    Then personalization_score < 50
    And issue_type = "generic_content"
    And regeneration recommended

  Scenario: Personalization uses LP history
    Given LP previously rejected similar fund citing "too early stage"
    When generating pitch
    Then pitch addresses stage concern proactively
    And personalization includes "addressing prior feedback"

  # ==========================================================================
  # Tone Validation
  # ==========================================================================

  Scenario: Tone matches LP type - pension
    Given LP is Public Pension
    When evaluating tone
    Then expected tone markers include:
      | marker                           | required |
      | Formal language                  | yes      |
      | Fiduciary duty references        | optional |
      | Long-term focus                  | yes      |
      | Conservative risk language       | yes      |
    And casual language is flagged

  Scenario: Tone matches LP type - family office
    Given LP is Family Office
    When evaluating tone
    Then expected tone markers include:
      | marker                           | required |
      | More direct communication        | yes      |
      | Relationship emphasis            | yes      |
      | Flexibility mention              | optional |
    And overly formal/bureaucratic language is noted

  Scenario: Tone mismatch detected
    Given LP is Public Pension
    And pitch uses casual tone with "exciting opportunity"
    When Pitch Critic evaluates
    Then tone_score is reduced
    And issue_type = "tone_mismatch"
    And suggestion to use more formal language

  # ==========================================================================
  # Batch Processing
  # ==========================================================================

  Scenario: Pre-generate pitches for top matches
    Given nightly batch job runs
    And match scoring completed
    When top 10 matches per fund are identified
    Then pitches are pre-generated for top matches
    And cached in entity_cache
    And GP sees instant pitch when viewing match

  Scenario: Pitch cache invalidation
    Given pitch was generated for Fund A + LP B
    When Fund A profile is updated
    Then cached pitch is invalidated
    And next request regenerates pitch

  Scenario: Batch pitch quality metrics
    Given batch generated 100 pitches overnight
    When quality analysis runs
    Then metrics show:
      | metric              | value                        |
      | approved            | count with score >= 85       |
      | approved_with_notes | count with score 70-84       |
      | regenerated         | count requiring regeneration |
      | rejected            | count with score < 50        |
    And quality trends are trackable

  # ==========================================================================
  # NEGATIVE TESTS: Pitch Critic Failures
  # ==========================================================================

  @negative
  Scenario: Critic API timeout
    Given pitch is generated
    When Pitch Critic call times out
    Then retry with exponential backoff
    And if retries fail, pitch is flagged for manual review
    And basic template is available as fallback

  @negative
  Scenario: Critic returns malformed response
    Given Pitch Critic returns invalid JSON
    When parsing response
    Then parse error is caught
    And critic is re-called
    And if still malformed, manual review triggered

  @negative
  Scenario: All regeneration attempts fail quality threshold
    Given 3 regeneration attempts completed
    And best score achieved = 45
    When final evaluation runs
    Then pitch is rejected
    And fallback template is used
    And pattern is logged for prompt improvement
    And human review notification sent

  @negative
  Scenario: Database unavailable for fact-check
    Given Pitch Critic attempts fact verification
    When database query fails
    Then fact-check is skipped with warning
    And pitch continues with reduced confidence
    And "unverified claims" flag is set

  @negative
  Scenario: Critic finds irrecoverable issues
    Given pitch contains multiple critical hallucinations
    And fundamental misunderstanding of LP
    When Pitch Critic evaluates
    Then recommendation = "reject"
    And no regeneration attempted (would fail anyway)
    And error report generated for analysis

  @negative
  Scenario: Pitch generation quota exceeded
    Given GP has generated 100 pitches today
    When quota limit is 100
    Then new pitch request returns quota error
    And user is informed of reset time
    And cached pitches remain available
```
