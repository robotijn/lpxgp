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
