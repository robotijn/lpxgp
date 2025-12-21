# E2E User Journeys

Complete end-to-end scenarios that span multiple features and milestones.

> **Invite-Only Platform**
> LPxGP has no public registration. All journeys start with an invitation.

---

## Journey 0: Platform Onboarding (Super Admin)

```gherkin
Feature: Platform Onboarding Journey
  As a Super Admin (LPxGP team)
  I want to onboard new GP firms
  So that they can use the platform

  Scenario: Complete company onboarding from sales to first login
    # Step 1: Sales Process (Outside Platform)
    Given a GP firm "Acme Capital" signed up for LPxGP
    And they completed the vetting/sales process
    And we have their admin contact: partner@acme.com

    # Step 2: Create Company (M5)
    When I login as Super Admin
    And I go to Admin > Companies
    And I click "Add Company"
    And I enter:
      | Company Name | Acme Capital |
      | Admin Email | partner@acme.com |
      | Plan | Standard |
    And I click "Create & Send Invitation"
    Then company is created with status "Pending"
    And invitation email is sent to partner@acme.com

    # Step 3: Company Admin Accepts (M1)
    Given partner@acme.com receives the invitation email
    When they click the invitation link
    Then they see "Welcome to LPxGP"
    And they see "You've been invited as Admin of Acme Capital"
    When they enter their name and password
    And they click "Complete Setup"
    Then their account is created
    And they are logged in
    And company status changes to "Active"

    # Step 4: First-Time Welcome (M1)
    Then they see the first-time welcome screen:
      | "Welcome to LPxGP!" |
      | "You're the admin of Acme Capital" |
      | [Create Your First Fund] |
      | [Invite Team Members] |

    # Step 5: Verify in Admin Panel (M5)
    When I refresh Admin > Companies as Super Admin
    Then I see "Acme Capital" with status "Active"
    And user count is "1"
```

---

## Journey 1: New GP Onboarding

```gherkin
Feature: New GP Onboarding Journey
  As a newly invited GP user
  I want to set up my account and create my first fund
  So that I can start finding LPs

  Scenario: Complete onboarding from invitation to first match
    # Step 1: Receive Invitation (M1)
    Given I am a partner at "Acme Capital"
    And I received an invitation email from LPxGP
    When I click the invitation link
    Then I see "Welcome to LPxGP"
    And I see "You've been invited to join Acme Capital as Admin"

    # Step 2: Accept Invitation (M1)
    When I enter my full name "John Partner"
    And I enter password "SecurePass123!"
    And I confirm password
    And I click "Complete Setup"
    Then my account is created
    And I am logged in

    # Step 3: First Login Welcome (M1)
    Then I see the first-time welcome screen
    And I see "You're the admin of Acme Capital"
    And I see two options:
      | "Create Your First Fund" (primary) |
      | "Invite Team Members" (secondary) |

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

### Journey 1: Error Path Scenarios

```gherkin
Feature: New GP Onboarding - Error Paths
  As a newly invited GP user
  I want graceful error handling during onboarding
  So that I can recover and complete setup

  # Invitation Errors

  Scenario: Invitation link expired
    Given my invitation was sent 8 days ago
    When I click the invitation link
    Then I see "This invitation has expired"
    And I see "Please contact your administrator for a new invitation"
    And I cannot proceed to create account

  Scenario: Invitation already used
    Given I already accepted my invitation
    When I click the invitation link again
    Then I see "This invitation has already been used"
    And I see a link to "Login to your account"

  Scenario: Invalid invitation link
    Given I have a corrupted invitation link
    When I visit the corrupted link
    Then I see "Invalid invitation link"
    And I see "Contact your administrator if you need a new invitation"

  Scenario: Accept invitation with weak password
    Given I am on the invitation acceptance page
    When I enter password "weak"
    And I click "Complete Setup"
    Then I see password strength error
    And I can enter a stronger password

  Scenario: Accept invitation with mismatched passwords
    Given I am on the invitation acceptance page
    When I enter password "SecurePass123!"
    And I confirm password "DifferentPass!"
    And I click "Complete Setup"
    Then I see "Passwords do not match"
    And I can correct and try again

  Scenario: Accept invitation network failure
    Given I am on the invitation acceptance page
    And the network connection drops
    When I submit the form
    Then I see error "Unable to connect. Please check your internet connection."
    And my entered data is preserved
    When the network reconnects
    And I click "Try Again"
    Then account creation completes successfully

  Scenario: Invitation for deactivated company
    Given my invitation was for "Defunct Corp"
    And the company has been deactivated
    When I click the invitation link
    Then I see "This company is no longer active on LPxGP"
    And I cannot create an account

  # Login Errors

  Scenario: Login with wrong password
    Given I have an active account
    When I enter my email with wrong password
    And I click "Login"
    Then I see error "Invalid email or password"
    And password field is cleared
    And I can try again

  Scenario: Login rate limiting after multiple failures
    Given I have entered wrong password 5 times
    When I try to login again
    Then I see "Too many failed attempts. Please try again in 15 minutes."
    And the login form is disabled temporarily

  Scenario: Session timeout during onboarding
    Given I am on the welcome screen after first login
    And my session expires (30 minutes of inactivity)
    When I click "Create Fund"
    Then I am redirected to login
    And I see "Your session expired. Please login again."
    When I login successfully
    Then I am returned to the welcome screen

  # Pitch Deck Upload Errors

  Scenario: Upload unsupported file format
    Given I am on the fund creation page
    When I try to upload "pitch.docx" (not PDF)
    Then I see error "Please upload a PDF file"
    And I can select a different file

  Scenario: Upload file too large
    Given I am on the fund creation page
    When I try to upload a 100MB PDF
    Then I see error "File size must be under 25MB"
    And I can select a smaller file

  Scenario: Upload corrupted PDF
    Given I am on the fund creation page
    When I upload a corrupted PDF file
    Then I see error "Unable to read this PDF. Please try a different file."

  Scenario: AI extraction fails mid-process
    Given I am uploading my pitch deck
    And the upload completes
    When the AI extraction service fails
    Then I see error "Extraction failed. We'll retry automatically."
    And the system retries 3 times
    If retry succeeds:
      Then extraction results are shown
    If retry fails:
      Then I see "Manual entry required"
      And I can enter fund details manually

  Scenario: Network failure during file upload
    Given I am uploading a large pitch deck
    And upload is at 60%
    When the network connection drops
    Then I see "Upload interrupted"
    And I see "Resume Upload" button
    When network reconnects
    And I click "Resume Upload"
    Then upload continues from 60%
    And completes successfully

  # Fund Profile Errors

  Scenario: Missing required fields on confirm
    Given I have extracted fund information
    And "Fund Size" field is empty
    When I click "Confirm and Publish"
    Then I see error "Please fill in all required fields"
    And "Fund Size" is highlighted
    And I am scrolled to the first missing field

  Scenario: Invalid fund size format
    Given I am entering fund details
    When I enter "fifty million" for fund size
    Then I see error "Please enter a number (e.g., 50000000 or 50M)"

  Scenario: Save draft on browser close
    Given I am filling out fund details
    And I have entered half the fields
    When I accidentally close the browser
    And I return to lpxgp.com and login
    Then I see "You have an unsaved fund draft"
    And I can continue where I left off

  Scenario: Network failure when saving fund profile
    Given I have completed all fund details
    When I click "Confirm and Publish"
    And the network fails
    Then I see "Unable to save. Your data is preserved locally."
    When network reconnects
    And I click "Try Again"
    Then my fund profile is saved successfully

  # Matching Errors

  Scenario: Matching engine timeout
    Given my fund profile is created
    When I click "Find Matching LPs"
    And the matching takes more than 30 seconds
    Then I see "Matching is taking longer than expected"
    And I see a progress indicator
    And I can wait or check back later

  Scenario: No matches found
    Given my fund has very niche criteria
    When I click "Find Matching LPs"
    Then I see "No LPs match your current criteria"
    And I see suggestions to broaden search:
      | Consider expanding geography |
      | Consider additional strategies |
    And I can adjust fund profile and retry

  Scenario: Matching engine error
    Given my fund profile is created
    When I click "Find Matching LPs"
    And the matching service is down
    Then I see "Matching temporarily unavailable"
    And I see "We'll notify you when matches are ready"
    And I can continue to browse LPs manually

  # Pitch Generation Errors

  Scenario: AI generation timeout
    Given I am generating an executive summary
    And the generation takes more than 60 seconds
    Then I see "Generation is taking longer than expected"
    When it completes
    Then I see the generated summary

  Scenario: AI service unavailable
    Given I click "Generate Pitch"
    And the LLM service (OpenRouter) is down
    Then I see "AI generation temporarily unavailable"
    And I see "Try again in a few minutes"
    And I can still view LP details manually

  Scenario: Generated content is empty or invalid
    Given the AI generates empty content
    Then I see "Generation produced no results"
    And I can click "Regenerate" to try again

  Scenario: PDF download fails
    Given I have a generated executive summary
    When I click "Download as PDF"
    And PDF generation fails
    Then I see "PDF generation failed"
    And I see "Copy to Clipboard" as fallback
    And I can try PDF download again
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

### Journey 2: Error Path Scenarios

```gherkin
Feature: LP Research - Error Paths
  As a GP doing market research
  I want graceful error handling during research
  So that I can continue my work effectively

  # Search and Filter Errors

  Scenario: Search with no results
    Given I am on LP Search
    When I search for "unicorn rainbow investors"
    Then I see "No LPs match your search"
    And I see suggestions:
      | Try broader search terms |
      | Remove some filters |
      | Check spelling |
    And I can clear search and start over

  Scenario: Filter combination returns empty
    Given I am on LP Search
    When I apply conflicting filters:
      | Type | Family Office |
      | AUM | > $100B |
    Then I see "No LPs match these criteria"
    And I see which filter to adjust
    And filters are preserved for editing

  Scenario: Semantic search service unavailable
    Given I am on LP Search
    When I enter a semantic search query
    And the Voyage AI service is down
    Then I see "Smart search temporarily unavailable"
    And I see "Using keyword search instead"
    And basic keyword results are shown

  Scenario: Search timeout
    Given I enter a complex semantic query
    When search takes more than 10 seconds
    Then I see a loading indicator with progress
    And I can click "Cancel" to stop
    When search completes
    Then results are shown

  Scenario: Network failure during search
    Given I am performing a search
    When the network drops mid-request
    Then I see "Connection lost during search"
    And my search terms are preserved
    When network reconnects
    And I click "Retry Search"
    Then search executes successfully

  # LP Profile Errors

  Scenario: LP profile not found
    Given I have a bookmarked LP URL
    When the LP has been removed from database
    Then I see "This LP profile is no longer available"
    And I see similar LP suggestions

  Scenario: LP profile loading error
    Given I click on an LP in search results
    When the profile fails to load
    Then I see "Unable to load LP profile"
    And I see "Try Again" button
    And I can return to search results

  Scenario: Incomplete LP data
    Given I view an LP profile
    When some fields are missing (e.g., no contact info)
    Then I see placeholders: "Contact information not available"
    And I see "Request data update" link

  # Saved Search Errors

  Scenario: Save search with duplicate name
    Given I have a saved search "DeepTech Endowments"
    When I try to save another search with the same name
    Then I see "A saved search with this name already exists"
    And I can:
      | Enter a different name |
      | Replace the existing search |

  Scenario: Save search fails
    Given I configure a complex search
    When I click "Save Search"
    And the save fails
    Then I see "Unable to save search. Please try again."
    And my search configuration is preserved

  Scenario: Load saved search that's now invalid
    Given I saved a search with filter "Strategy: Crypto"
    And that strategy option has been removed
    When I load the saved search
    Then I see "Some filters in this search are no longer valid"
    And invalid filters are shown struck through
    And remaining valid filters are applied

  Scenario: Session timeout while researching
    Given I am browsing LPs
    And I have selected 15 LPs for comparison
    When my session expires
    Then I am redirected to login
    When I login again
    Then my selected LPs are preserved
    And I can continue where I left off

  # Export Errors

  Scenario: Export with too many records
    Given I select 1000 LPs for export
    When I click "Export CSV"
    Then I see "Export limited to 500 records"
    And I can:
      | Export first 500 |
      | Refine selection |

  Scenario: Export generation fails
    Given I select 20 LPs
    When I click "Export CSV"
    And export generation fails
    Then I see "Export failed. Please try again."
    And my selection is preserved
    And I can retry the export

  Scenario: Large export takes time
    Given I select 200 LPs
    When I click "Export CSV"
    Then I see "Preparing your export..."
    And I see a progress indicator
    When export completes
    Then download starts automatically

  Scenario: Network failure during download
    Given my export is ready
    When download starts but network drops
    Then I see "Download interrupted"
    And I see "Your export is saved for 24 hours"
    And I can retry download from exports page

  # Shortlist Errors

  Scenario: Add to shortlist fails
    Given I am viewing an LP
    When I click "Add to Shortlist"
    And the save fails
    Then I see "Unable to add to shortlist"
    And I can retry
    And the LP is not marked as added

  Scenario: Shortlist limit reached
    Given my shortlist has 100 LPs (maximum)
    When I try to add another LP
    Then I see "Shortlist limit reached (100 LPs)"
    And I see "Remove an LP or create a new shortlist"

  Scenario: View shortlist with deleted LPs
    Given my shortlist contains 10 LPs
    And 2 LPs have been removed from the database
    When I view my shortlist
    Then I see 8 active LPs
    And I see "2 LPs are no longer available (removed)"
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

### Journey 3: Error Path Scenarios

```gherkin
Feature: Fundraising Campaign - Error Paths
  As a GP raising a fund
  I want graceful error handling during campaigns
  So that no outreach opportunities are lost

  # Bulk Operations Errors

  Scenario: Bulk status update fails partially
    Given I select 10 LPs to mark as "Contacted"
    When I click "Update Status"
    And 7 succeed but 3 fail
    Then I see "7 of 10 LPs updated successfully"
    And I see "3 failed - click to retry"
    And failed LPs are highlighted
    When I click "Retry Failed"
    Then the 3 LPs are updated

  Scenario: Generate materials for multiple LPs fails
    Given I select 5 LPs for batch summary generation
    When I click "Generate All Summaries"
    And 2 generations fail
    Then I see "3 summaries generated, 2 failed"
    And I can view successful ones
    And I can retry failed ones individually

  # Email Generation Errors

  Scenario: Email generation produces low-quality content
    Given I generate an outreach email
    When the content is too generic or repetitive
    Then I see quality indicators (yellow/red)
    And I see "Try regenerating with different options"
    And I can provide additional context for regeneration

  Scenario: Copy to clipboard fails
    Given I have a generated email
    When I click "Copy to Clipboard"
    And the browser blocks clipboard access
    Then I see "Unable to copy automatically"
    And I see the email in a selectable text box
    And I see "Please select all and copy manually (Ctrl+C)"

  Scenario: Email personalization fields missing
    Given I generate an email for an LP
    When the LP profile is missing contact name
    Then the email shows "[Contact Name]" placeholder
    And I see warning "Some personalization fields are incomplete"
    And I can edit before copying

  # Status Tracking Errors

  Scenario: Update status with network failure
    Given I am updating an LP's status to "Interested"
    When the network drops during save
    Then I see "Unable to save status change"
    And the previous status is shown
    When network reconnects
    And I retry the update
    Then status is saved successfully

  Scenario: Concurrent edit conflict
    Given my colleague is viewing the same LP
    When I update status to "Interested"
    And colleague simultaneously updates to "Meeting Scheduled"
    Then I see "This LP was just updated by [colleague name]"
    And I see both status options
    And I can choose which to keep

  Scenario: Status update with required note
    Given I update an LP's status to "Passed"
    When I try to save without adding a reason
    Then I see "Please add a reason when marking as Passed"
    And the note field is highlighted

  Scenario: Undo accidental status change
    Given I accidentally mark an LP as "Passed"
    When I realize the mistake within 30 seconds
    Then I see "Undo" option
    When I click "Undo"
    Then the previous status is restored

  # PDF Generation Errors

  Scenario: PDF generation times out
    Given I click "Download as PDF"
    When generation takes more than 30 seconds
    Then I see "PDF generation is taking longer than expected"
    And I can:
      | Wait for completion |
      | Cancel and get email link when ready |

  Scenario: PDF contains formatting errors
    Given my executive summary has special characters
    When PDF is generated
    And some characters are corrupted
    Then I see a preview with issues highlighted
    And I can "Edit Source" to fix
    And regenerate the PDF

  # Campaign Analytics Errors

  Scenario: Analytics data temporarily unavailable
    Given I view my campaign dashboard
    When analytics service is down
    Then I see "Analytics temporarily unavailable"
    And I still see my LP list and statuses
    And I see "Last updated: [timestamp]"

  Scenario: Analytics show stale data
    Given I view campaign stats
    When data hasn't synced in 1 hour
    Then I see warning "Data may be outdated"
    And I see "Refresh" button
    When I click "Refresh"
    Then data is reloaded

  # Session and Access Errors

  Scenario: Session expires mid-outreach
    Given I am generating emails for 5 LPs
    And I have completed 3
    When my session expires
    Then I am redirected to login
    And I see "Session expired. Your work has been saved."
    When I login
    Then I see my 3 completed emails
    And I can continue with LP 4

  Scenario: Lose access to fund during campaign
    Given I am running a campaign
    When admin removes my access to the fund
    Then I see "Your access to [Fund Name] has been revoked"
    And I can view but not modify LP data
    And I see "Contact [admin email] for access"

  Scenario: Fund archived during campaign
    Given I am running a campaign for Fund III
    When the fund is archived
    Then I see "Fund III has been archived"
    And I can view historical data
    And new outreach is disabled
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

### Journey 4: Error Path Scenarios

```gherkin
Feature: Data Import - Error Paths
  As a platform admin
  I want robust error handling during data import
  So that no data is lost and issues are clearly identified

  # File Upload Errors

  Scenario: Upload unsupported file format
    Given I am on Admin > Import
    When I try to upload "data.pdf"
    Then I see "Unsupported file format"
    And I see "Supported formats: .xlsx, .xls, .csv"

  Scenario: Upload corrupted Excel file
    Given I upload a corrupted .xlsx file
    Then I see "Unable to read file. File may be corrupted."
    And I can download a sample template

  Scenario: Upload file with wrong encoding
    Given I upload a CSV with non-UTF8 encoding
    Then I see "File encoding issue detected"
    And I see "Please save as UTF-8 and re-upload"
    And I see which rows have encoding issues

  Scenario: Upload very large file
    Given I upload a file with 50,000 rows
    When upload takes more than 2 minutes
    Then I see progress: "Processing row 25,000 of 50,000"
    And I see estimated time remaining
    And I can cancel if needed

  Scenario: Upload network failure mid-transfer
    Given I am uploading a 20MB file
    And upload is at 70%
    When network connection drops
    Then I see "Upload interrupted at 70%"
    And I see "Resume" button
    When I click "Resume"
    Then upload continues from where it stopped

  Scenario: Browser closed during upload
    Given I am uploading a file
    When I accidentally close the browser
    And I reopen Admin > Import
    Then I see "You have a pending upload"
    And I can resume or cancel

  # Column Mapping Errors

  Scenario: Required column not mapped
    Given I am mapping columns
    When I don't map the required "name" field
    And I click "Continue"
    Then I see "Required field 'LP Name' is not mapped"
    And the unmapped field is highlighted

  Scenario: Same column mapped twice
    Given I am mapping columns
    When I map "Column A" to both "name" and "type"
    Then I see "Column A is mapped to multiple fields"
    And I must resolve before continuing

  Scenario: Column data type mismatch
    Given I map "Investment Amount" to "total_aum_bn"
    When the column contains text like "Ten Million"
    Then I see warning "Column may contain non-numeric data"
    And I see preview of problematic values
    And I can proceed with conversion or fix source

  Scenario: Save mapping as template fails
    Given I have completed column mapping
    When I click "Save as Template"
    And the save fails
    Then I see "Unable to save template"
    And my mapping is preserved
    And import can still proceed

  # Validation Errors

  Scenario: Validation finds critical errors
    Given I am validating 1,000 rows
    When validation finds 200 rows with missing required fields
    Then I see "200 rows have critical errors"
    And I can:
      | Download error report |
      | Fix in source and re-upload |
      | Skip invalid rows |

  Scenario: Duplicate detection finds conflicts
    Given I am importing 1,000 LPs
    When 50 match existing LPs in database
    Then I see "50 potential duplicates found"
    And for each duplicate I can:
      | Skip (keep existing) |
      | Update existing |
      | Import as new |
      | Review details |

  Scenario: Validation timeout on large file
    Given I am validating 30,000 rows
    When validation takes more than 5 minutes
    Then I see "Validation queued for background processing"
    And I see "We'll email you when complete"
    And I can close the page and return later

  # Import Execution Errors

  Scenario: Import fails mid-process
    Given I click "Approve & Import"
    And import is at row 500 of 1,000
    When database connection fails
    Then I see "Import paused at row 500"
    And I see "Successfully imported: 500, Pending: 500"
    When connection is restored
    Then I see "Resume Import" button
    When I click it
    Then import continues from row 501

  Scenario: Import transaction rollback
    Given I am importing with "All or nothing" mode
    When import fails at row 800
    Then all 800 rows are rolled back
    And I see "Import failed. No records were saved."
    And I see the specific error at row 800
    And I can fix and retry

  Scenario: Partial import with errors
    Given I am importing with "Skip errors" mode
    When 50 rows have errors
    Then 950 rows are imported
    And I see detailed error log for 50 failed rows
    And I can download failed rows as new file
    And fix and re-import just those rows

  # Cleaning Pipeline Errors

  Scenario: Strategy normalization fails
    Given import completes successfully
    When the cleaning pipeline runs
    And strategy normalization fails
    Then I see "Cleaning partially complete"
    And I see which steps succeeded/failed
    And I can retry failed steps
    And imported data is preserved

  Scenario: Cleaning produces unexpected results
    Given the cleaning pipeline runs
    When "Venture Capital Fund" is normalized to "Unknown"
    Then I see normalization report with anomalies
    And I can review and correct mappings
    And I can re-run cleaning

  Scenario: Cleaning pipeline times out
    Given I have 10,000 LPs to clean
    When cleaning takes more than 10 minutes
    Then cleaning moves to background
    And I see progress updates
    And I receive email when complete

  # Embedding Generation Errors

  Scenario: Voyage AI service unavailable
    Given import and cleaning complete
    When embedding generation starts
    And Voyage AI is unavailable
    Then I see "Embedding generation delayed"
    And I see "LPs are available but semantic search is disabled"
    And system retries automatically every 30 minutes

  Scenario: Embedding generation fails for some LPs
    Given embedding generation runs
    When 50 LPs fail to generate embeddings
    Then I see "Embeddings generated for 900 of 950 LPs"
    And I see list of failed LPs
    And I can retry failed ones
    And semantic search works for successful LPs

  Scenario: Embedding costs exceed budget
    Given I set embedding budget to $10
    When 500 LPs would cost $12
    Then I see "Embedding budget exceeded"
    And I can:
      | Increase budget |
      | Prioritize high-value LPs |
      | Skip embeddings for now |

  # Recovery and Rollback

  Scenario: Need to undo entire import
    Given I imported 1,000 LPs
    When I realize the source data was wrong
    Then I can go to Import History
    And I see "Rollback" option (within 24 hours)
    When I click "Rollback Import #123"
    Then all 1,000 LPs are removed
    And related data (embeddings) is cleaned up
    And I see confirmation of rollback

  Scenario: Audit trail for import issues
    Given an import had some errors
    When I need to investigate
    Then I can view complete audit log:
      | Timestamp | Action | Details |
      | Row numbers processed |
      | Errors encountered |
      | User actions taken |
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

### Journey 5: Error Path Scenarios

```gherkin
Feature: Match to Investment - Error Paths
  As a GP
  I want reliable tracking throughout the investment journey
  So that I never lose track of opportunities

  # Status Transition Errors

  Scenario: Invalid status transition
    Given an LP is at status "Matched"
    When I try to update to "Committed" (skipping steps)
    Then I see warning "Unusual status jump detected"
    And I see "Are you sure? This skips: Contacted, Interested, Due Diligence"
    And I can confirm or select intermediate status

  Scenario: Status update with stale data
    Given I opened LP details 1 hour ago
    And colleague updated status since then
    When I try to update status
    Then I see "Status was updated by [colleague] at [time]"
    And I see current status
    And I can confirm my update or cancel

  Scenario: Record commitment amount fails
    Given I update status to "Committed"
    When I enter commitment amount $50M
    And the save fails
    Then I see "Status updated but amount not saved"
    And I see "Retry saving amount" option
    And status change is preserved

  # Note and Activity Tracking Errors

  Scenario: Add note fails
    Given I am adding a meeting note
    When I click "Save Note"
    And the save fails
    Then I see "Note not saved"
    And the note content is preserved
    And I can retry or copy to clipboard

  Scenario: Note too long
    Given I am adding a detailed meeting note
    When the note exceeds 10,000 characters
    Then I see "Note exceeds maximum length"
    And I see character count: "10,500 / 10,000"
    And I can trim or save as multiple notes

  Scenario: Activity feed fails to load
    Given I am viewing LP details
    When activity history fails to load
    Then I see "Activity history temporarily unavailable"
    And I still see current status
    And I can add new activities

  # Briefing Material Errors

  Scenario: Generate briefing with outdated LP data
    Given LP profile was updated yesterday
    When I generate briefing materials
    Then I see warning "LP profile recently updated"
    And I see what changed
    And I can regenerate with fresh data

  Scenario: Briefing contains confidential warnings
    Given I generate talking points
    When AI detects potentially sensitive topics
    Then I see "Review before sharing externally"
    And sensitive sections are highlighted
    And I can edit or acknowledge

  # Due Diligence Tracking Errors

  Scenario: Upload DD document fails
    Given I am uploading a due diligence response
    When upload fails
    Then I see "Upload failed"
    And I can retry
    And my response notes are preserved

  Scenario: DD question tracking sync issue
    Given I am tracking DD questions
    When data sync fails
    Then I see "Some updates may not be saved"
    And I see which items are unsynced
    And local changes are preserved for retry

  # Commitment Recording Errors

  Scenario: Commitment amount format error
    Given I am recording commitment
    When I enter "fifty million dollars"
    Then I see "Please enter a numeric amount"
    And I see format examples: "$50,000,000 or $50M"

  Scenario: Commitment exceeds fund target
    Given fund target is $100M
    And current commitments total $95M
    When I add $10M commitment
    Then I see "This exceeds fund target by $5M"
    And I can confirm (oversubscription) or adjust

  Scenario: Duplicate commitment entry
    Given I recorded $50M from CalPERS
    When I try to add another commitment from CalPERS
    Then I see "CalPERS already has a commitment recorded"
    And I can:
      | Update existing amount |
      | Add as additional commitment |
      | Cancel |

  # Analytics and Funnel Errors

  Scenario: Funnel data incomplete
    Given I view my investment funnel
    When some LP records are missing status
    Then I see "5 LPs not included (missing status)"
    And I can view and fix incomplete records
    And funnel shows known data with caveat

  Scenario: Conversion calculation error
    Given I view conversion rates
    When data contains anomalies
    Then I see "Some rates may be inaccurate"
    And I see which stages have data issues
    And I can drill down to investigate

  # Recovery Scenarios

  Scenario: Recover after accidental status change
    Given I accidentally marked CalPERS as "Passed"
    When I notice within 24 hours
    Then I see full activity history
    And I see "Restore to previous status" option
    And I can restore with audit note

  Scenario: Merge duplicate LP entries
    Given I have two entries for same LP
    When I identify them as duplicates
    Then I can merge:
      | Keep all activities from both |
      | Choose primary record |
      | Combine notes |
    And I have single unified LP record

  Scenario: Export journey data fails
    Given I want to export LP journey data
    When export fails
    Then I see "Export failed"
    And I see "View in browser" fallback
    And I can copy data manually
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

### Journey 6: Error Path Scenarios

```gherkin
Feature: Multi-Fund Management - Error Paths
  As a GP with multiple funds
  I want reliable multi-fund management
  So that I never confuse fund data

  # Fund Access Errors

  Scenario: Access denied to fund
    Given I have access to Fund III
    When I try to access Fund II (no permission)
    Then I see "You don't have access to Fund II"
    And I see "Request access from [admin name]"
    And I am not shown any Fund II data

  Scenario: Fund access revoked while viewing
    Given I am viewing Fund III
    When admin revokes my access mid-session
    Then on next action I see "Your access to Fund III has been revoked"
    And I am redirected to dashboard
    And Fund III is no longer visible

  Scenario: Login to wrong organization
    Given I have accounts at two firms
    When I login and see wrong firm's funds
    Then I see org switcher in header
    And I can switch to correct organization
    And data is completely separate

  # Fund Switching Errors

  Scenario: Unsaved changes when switching funds
    Given I am editing LP notes in Fund III
    When I click to switch to Fund II
    Then I see "You have unsaved changes"
    And I can:
      | Save and switch |
      | Discard and switch |
      | Cancel and stay |

  Scenario: Fund data fails to load on switch
    Given I am viewing Fund III
    When I switch to Fund II
    And Fund II data fails to load
    Then I see "Unable to load Fund II data"
    And I remain on Fund III
    And I can retry

  Scenario: Accidental action on wrong fund
    Given I am viewing Fund III
    When I meant to mark LP in Fund II as Contacted
    And I realize I'm in wrong fund
    Then recent actions show fund context
    And I can undo recent action
    And I can switch to correct fund

  # Data Isolation Errors

  Scenario: LP appears in multiple funds incorrectly
    Given LP "CalPERS" should only be in Fund III
    When it incorrectly appears in Fund II
    Then I can report data issue
    And admin can investigate and fix
    And audit log shows the discrepancy

  Scenario: Cross-fund search returns mixed results
    Given I search for "pension" across all funds
    When results mix Fund II and Fund III
    Then each result clearly shows fund name
    And I can filter by specific fund
    And clicking takes me to correct fund context

  # Team Collaboration Errors

  Scenario: Concurrent edit conflict across team
    Given colleague is editing LP in Fund III
    When I try to edit the same LP
    Then I see "Currently being edited by [colleague]"
    And I see "Last saved: [timestamp]"
    And I can:
      | Wait and refresh |
      | View read-only |
      | Force edit (with warning) |

  Scenario: Real-time sync failure
    Given team is working on Fund III
    When real-time sync fails
    Then I see "Sync delayed - you may not see latest updates"
    And I see manual "Refresh" button
    And my changes are queued for sync

  Scenario: Team member sees stale data
    Given I updated LP status
    When colleague's session doesn't receive update
    Then they see stale status
    When they try to update
    Then they see conflict resolution dialog
    And they can see both versions and choose

  # Dashboard Errors

  Scenario: Dashboard stats inconsistent
    Given I view multi-fund dashboard
    When fund totals don't match detail counts
    Then I see "Stats are recalculating"
    And I see "Last accurate: [timestamp]"
    And stats auto-refresh when ready

  Scenario: Dashboard timeout with many funds
    Given I have access to 10 funds
    When dashboard takes more than 10 seconds
    Then I see funds loading progressively
    And I can interact with loaded funds
    And remaining funds load in background

  Scenario: Dashboard widget fails
    Given I view company dashboard
    When one widget fails to load
    Then other widgets still display
    And failed widget shows "Unable to load"
    And I can click to retry that widget

  # Organization-Level Errors

  Scenario: Organization settings change mid-session
    Given I am working in Fund III
    When admin changes organization settings
    Then I see notification "Settings have been updated"
    And affected features may require refresh
    And my unsaved work is preserved

  Scenario: Organization reaches user limit
    Given organization has 5/5 user seats
    When admin tries to add me
    Then admin sees "User limit reached"
    And admin can upgrade or remove inactive user
    And I see clear error if I try to join

  Scenario: Bulk export across funds fails
    Given I export data from all funds
    When export partially fails
    Then I see which funds succeeded
    And I see which funds failed with reasons
    And I can download partial export
    And I can retry failed funds
```

---

## Negative E2E Test Scenarios

Complete end-to-end negative test scenarios covering critical failure paths across the platform.

### Negative Journey 1: Onboarding with Expired Invitation

```gherkin
@negative @e2e
Feature: Onboarding Flow with Expired Invitation
  As a GP user with an expired invitation
  I want clear feedback and recovery options
  So that I can still join the platform

  Background:
    Given "Acme Capital" has been onboarded by Super Admin
    And an invitation was sent to partner@acme.com 8 days ago
    And the invitation has a 7-day expiration policy

  Scenario: Complete expired invitation flow with recovery
    # Step 1: Attempt to use expired link
    Given I am partner@acme.com
    When I click the invitation link from my email
    Then I see the expired invitation page with:
      | "This invitation has expired" |
      | "Invitation sent: [date 8 days ago]" |
      | "Expired: [date 1 day ago]" |
    And I see "Request New Invitation" button
    And I see company admin contact information
    And I cannot proceed to account creation

    # Step 2: Request new invitation
    When I click "Request New Invitation"
    Then I see a confirmation message:
      | "Request sent to Acme Capital admin" |
      | "You'll receive a new invitation within 24 hours" |
    And the company admin receives notification of the request

    # Step 3: Admin receives and handles request
    Given I am the company admin of Acme Capital
    When I login to the platform
    Then I see a notification "Pending invitation request from partner@acme.com"
    When I click on the notification
    Then I see options:
      | "Resend Invitation" |
      | "Decline Request" |
    When I click "Resend Invitation"
    Then a new invitation is sent with fresh 7-day expiration
    And the old invitation is marked as replaced

    # Step 4: User completes onboarding with new invitation
    Given partner@acme.com receives the new invitation email
    When they click the new invitation link
    Then they see "Welcome to LPxGP"
    And they can complete account setup normally
    And both old and new invitation tokens are now invalidated

  Scenario: Expired invitation with multiple failed attempts
    Given I clicked the expired invitation link 3 times
    When I try a fourth time
    Then I see the same expired message
    And I see "You've visited this page multiple times"
    And I see "Consider requesting a new invitation"
    And failed attempts are logged for security

  Scenario: Expired invitation after company deactivation
    Given my invitation expired
    And "Acme Capital" was deactivated after my invitation was sent
    When I click the expired invitation link
    Then I see "This invitation has expired"
    And I see "Additionally, this company is no longer active on LPxGP"
    And "Request New Invitation" is disabled
    And I see "Contact LPxGP support for assistance"

  Scenario: Race condition - invitation expires during form completion
    Given my invitation expires in 30 seconds
    When I click the invitation link (valid at this moment)
    And I see the account creation form
    And I spend 2 minutes filling out the form
    And I click "Complete Setup"
    Then I see "Your invitation expired while completing setup"
    And I see "Your information has been saved"
    And I see "Request a new invitation to continue"
    When I receive a new invitation and click the link
    Then I see the form pre-filled with my previous entries
    And I can complete setup without re-entering data
```

---

### Negative Journey 2: Fund Creation with API Failures Mid-Flow

```gherkin
@negative @e2e
Feature: Fund Creation with API Failures Mid-Flow
  As a GP creating a new fund
  I want resilient handling of API failures
  So that my fund setup is never lost or corrupted

  Background:
    Given I am logged in as partner@acme.com
    And I am on the fund creation page
    And I have a valid pitch deck ready to upload

  Scenario: Complete fund creation with cascading API failures
    # Step 1: Upload succeeds but extraction API fails
    When I upload my pitch deck "fund_iii_deck.pdf"
    Then upload completes successfully
    And I see "Analyzing your pitch deck..."
    When the AI extraction API (OpenRouter) returns 503 Service Unavailable
    Then I see "AI extraction temporarily unavailable"
    And I see extraction retry countdown: "Retrying in 30 seconds..."
    And my uploaded file is preserved

    # Step 2: First retry fails, second succeeds
    When first retry also fails
    Then I see "Retry 2 of 3..."
    When second retry succeeds
    Then I see extracted fund information
    And extraction results are cached locally

    # Step 3: Database save fails after user confirmation
    When I review and confirm the extracted fields
    And I add my investment thesis
    And I click "Confirm and Publish"
    And the Supabase database returns connection timeout
    Then I see "Unable to save fund profile"
    And I see all my entered data is preserved
    And I see "Your draft is saved locally"
    And I see "Retry Save" button

    # Step 4: Retry save succeeds
    When database connection is restored
    And I click "Retry Save"
    Then fund profile is saved successfully
    And I see "Fund III created successfully"
    And local draft is cleared

  Scenario: Embedding generation fails after successful fund creation
    Given I successfully created my fund profile
    When the platform attempts to generate embeddings for matching
    And Voyage AI returns 429 Too Many Requests
    Then I see "Fund created, but matching is temporarily delayed"
    And I see "Matches will be available within 1 hour"
    And fund is usable but without semantic matching
    And embedding generation is queued for retry

  Scenario: Multiple API failures during extraction with fallback
    When I upload my pitch deck
    And OpenRouter fails all 3 retry attempts
    Then I see "Automatic extraction failed"
    And I see "Manual entry mode"
    And I see form with all fund fields empty
    And I can manually enter fund details
    When I complete manual entry
    Then fund is created successfully
    And I see "Consider re-uploading deck later for AI enhancement"

  Scenario: Partial extraction results due to API instability
    When I upload my pitch deck
    And extraction partially completes (fund name, size) before API fails
    Then I see "Partial extraction completed"
    And I see extracted fields populated
    And I see empty fields marked "Extraction incomplete"
    And I can fill in missing fields manually
    And I can retry extraction for empty fields only

  Scenario: File storage API fails during upload
    When I start uploading my pitch deck
    And file upload is at 80% complete
    And Supabase Storage returns 500 Internal Server Error
    Then I see "Upload failed at 80%"
    And I see "Resume Upload" button
    When I click "Resume Upload"
    And storage is now available
    Then upload resumes from 80% (chunked upload)
    And upload completes successfully

  Scenario: Session expires during multi-step fund creation
    Given I uploaded my deck and received extraction results
    And I am reviewing extracted fields
    When my session expires (60 minutes)
    And I try to click "Confirm and Publish"
    Then I am redirected to login
    And I see "Your session expired. Draft saved."
    When I login again
    Then I am returned to fund creation page
    And I see my uploaded deck
    And I see my extraction results
    And I see any edits I made
    And I can continue from where I left off

  Scenario: Concurrent API failures across multiple services
    When I upload my pitch deck
    And the following services fail simultaneously:
      | Service | Error |
      | OpenRouter | 503 |
      | Voyage AI | Connection Timeout |
      | Supabase Storage | Rate Limited |
    Then I see "Multiple services experiencing issues"
    And I see status for each service
    And I see "Try again in a few minutes"
    And my local draft is preserved
    And I see LPxGP status page link
```

---

### Negative Journey 3: LP Research with Search Service Degradation

```gherkin
@negative @e2e
Feature: LP Research with Search Service Degradation
  As a GP researching LPs
  I want uninterrupted research capability
  So that service issues don't block my work

  Background:
    Given I am logged in as partner@acme.com
    And I am on the LP Search page
    And the LP database contains 1,000 records

  Scenario: Complete research session with gradual service degradation
    # Step 1: Normal search works
    When I search for "pension funds in California"
    Then I see relevant results ranked by semantic similarity
    And search completes in under 2 seconds

    # Step 2: Voyage AI becomes slow
    When I search for "endowments interested in climate tech"
    And Voyage AI response time increases to 15 seconds
    Then I see "Search is taking longer than usual"
    And I see a progress indicator
    And I can continue viewing previous results
    When search eventually completes
    Then I see new results
    And I see "Search took 15 seconds (normally <2s)"

    # Step 3: Voyage AI completely fails
    When I search for "family offices in Asia"
    And Voyage AI returns 503 Service Unavailable
    Then I see "Semantic search temporarily unavailable"
    And I see "Using keyword fallback"
    And I see keyword-based results (less relevant but functional)
    And I see "Results may be less accurate"

    # Step 4: Fallback to filters only
    When keyword search also degrades
    Then I see "Search service degraded"
    And I see "Browse using filters"
    And filter dropdowns remain functional
    When I select filters:
      | Type | Family Office |
      | Region | Asia Pacific |
    Then I see filtered results
    And results load from database cache

    # Step 5: Service recovery
    When Voyage AI service recovers
    And I perform a new search
    Then semantic search works normally
    And I see "Search service restored"

  Scenario: Search results pagination with intermittent failures
    Given I search and get 100 results
    When I click "Load More" to see next 20
    And the API fails mid-request
    Then I see "Unable to load more results"
    And my first 100 results are preserved
    And I see "Retry" button
    When I click "Retry"
    Then next 20 results load successfully
    And I see all 120 results

  Scenario: Saved search references unavailable data
    Given I have a saved search "Tech Endowments"
    And the search relies on semantic matching
    When I load the saved search
    And semantic search is unavailable
    Then I see "This saved search requires semantic matching"
    And I see "Currently unavailable - using approximate results"
    And I see best-effort keyword results
    And I can save these results as a separate list

  Scenario: Real-time filter updates fail
    Given I am applying multiple filters
    When I select "Endowment" type
    And the count update request fails
    Then filter selection is preserved
    And I see stale count: "~45 results (updating...)"
    When I click "Apply Filters"
    Then actual filtered results are shown
    And count is updated correctly

  Scenario: Export during search service outage
    Given I have 50 LPs in my current results
    And I select all for export
    When I click "Export CSV"
    And the export service fails
    Then I see "Export generation failed"
    And I see "Alternative: Copy to clipboard"
    When I click "Copy to Clipboard"
    Then tab-separated data is copied
    And I can paste into Excel

  Scenario: Browser cache exhausted during heavy research
    Given I have been researching for 2 hours
    And I have viewed 200 LP profiles
    When browser storage approaches limit
    Then I see "Some cached data will be cleared"
    And oldest viewed profiles are cleared
    And my current session data is preserved
    And I can continue researching
    When I revisit a cleared profile
    Then it reloads from server (slightly slower)
```

---

### Negative Journey 4: Pitch Generation with Network Interruption

```gherkin
@negative @e2e
Feature: Pitch Generation with Network Interruption
  As a GP generating pitch materials
  I want resilient content generation
  So that network issues don't lose my work

  Background:
    Given I am logged in as partner@acme.com
    And I am viewing LP "CalPERS" detail page
    And my fund "Fund III" profile is complete

  Scenario: Complete pitch generation with network interruption
    # Step 1: Start executive summary generation
    When I click "Generate Executive Summary"
    Then I see "Generating personalized summary..."
    And I see progress indicator at 20%

    # Step 2: Network drops mid-generation
    When network connection drops at 60% progress
    Then I see "Connection lost during generation"
    And I see "Generation will resume when connected"
    And progress bar shows paused state

    # Step 3: Network reconnects
    When network reconnects after 30 seconds
    Then I see "Reconnected - resuming generation"
    And generation continues from checkpoint
    When generation completes
    Then I see the full executive summary
    And quality is not degraded

  Scenario: Network drops after generation but before save
    Given I generated an executive summary
    And I made edits to customize it
    When network drops
    And I click "Save Changes"
    Then I see "Changes saved locally (offline)"
    And I see sync indicator showing pending
    When network reconnects
    Then changes sync automatically
    And I see "Changes synced"

  Scenario: Email generation interrupted - streaming response cut
    When I click "Generate Outreach Email"
    And streaming response begins
    And I see partial email appearing word by word
    When network drops after receiving 40% of response
    Then streaming stops
    And I see partial email that was received
    And I see "Generation interrupted"
    And I see "Complete generation" button
    When network reconnects
    And I click "Complete generation"
    Then I see options:
      | "Resume from partial" - continues where it stopped |
      | "Regenerate full" - starts fresh |
    When I choose "Resume from partial"
    Then remaining content is generated
    And email is complete and coherent

  Scenario: PDF generation fails with network issues
    Given I have a completed executive summary
    When I click "Download as PDF"
    And PDF generation starts on server
    And network drops during PDF download
    Then I see "PDF download interrupted"
    And I see "PDF is ready on server"
    And I see "Retry Download" button
    When network reconnects
    And I click "Retry Download"
    Then PDF downloads successfully
    And server-side PDF was cached for 24 hours

  Scenario: Multiple pitch generations with intermittent connectivity
    Given I am generating materials for 5 LPs
    And network is unstable (drops every 2 minutes for 10 seconds)
    When I generate summary for LP 1
    Then it completes between drops
    When I generate summary for LP 2
    And network drops mid-generation
    Then generation pauses and resumes
    And LP 2 summary completes
    When I generate summaries for LPs 3-5
    Then platform handles drops gracefully
    And all 5 summaries are generated (with delays)
    And I see "5 of 5 summaries complete"

  Scenario: Copy to clipboard fails during network outage
    Given I generated an outreach email
    And network is disconnected
    When I click "Copy to Clipboard"
    Then copy succeeds (local operation)
    And I see "Copied! (Note: you're offline)"
    And I can paste into my email client
    When network reconnects
    Then I can mark LP as "Contacted" to track

  Scenario: Regeneration after poor quality due to interruption
    Given generation was interrupted and produced poor quality content
    When I click "Regenerate"
    Then I see "Previous generation had issues"
    And I see quality improvement suggestions:
      | "Ensure stable connection" |
      | "Try a different tone" |
      | "Add more context" |
    When I regenerate with stable connection
    Then new content is higher quality
    And both versions are available for comparison
```

---

### Negative Journey 5: Multi-User Collaboration Conflicts

```gherkin
@negative @e2e
Feature: Multi-User Collaboration Conflicts
  As a GP team member
  I want conflict-free collaboration
  So that team work doesn't cause data issues

  Background:
    Given "Acme Capital" has 3 team members:
      | User | Role |
      | partner@acme.com | Admin |
      | associate@acme.com | Member |
      | analyst@acme.com | Member |
    And all are working on Fund III simultaneously
    And LP "CalPERS" is a shared target

  Scenario: Simultaneous LP status updates with conflict resolution
    # Step 1: Both users view same LP
    Given partner@acme.com opens CalPERS detail page
    And associate@acme.com opens CalPERS detail page
    And current status is "Matched"

    # Step 2: Both try to update simultaneously
    When partner@acme.com clicks to change status to "Contacted"
    And associate@acme.com clicks to change status to "Interested"
    And both submit within 1 second

    # Step 3: First update succeeds, second gets conflict
    Then partner@acme.com sees "Status updated to Contacted"
    And associate@acme.com sees conflict dialog:
      | "Status was just updated by partner@acme.com" |
      | "Their update: Matched → Contacted" |
      | "Your update: Matched → Interested" |
    And associate@acme.com sees options:
      | "Accept their change" |
      | "Apply my change instead" - with warning |
      | "Update to different status" |

    # Step 4: Resolution
    When associate@acme.com clicks "Apply my change instead"
    Then they see confirmation "This will override partner@acme.com's change"
    When they confirm
    Then status becomes "Interested"
    And partner@acme.com sees "Status was updated by associate@acme.com"
    And activity log shows both changes with timestamps

  Scenario: Concurrent note editing with merge
    Given partner@acme.com is editing meeting notes for CalPERS
    And associate@acme.com opens the same note to edit
    When partner@acme.com adds "Discussed Fund III terms"
    And associate@acme.com adds "Need to follow up on due diligence"
    And both save
    Then both changes are merged
    And both users see the merged note:
      """
      Discussed Fund III terms
      Need to follow up on due diligence
      [Merged from edits by partner@acme.com and associate@acme.com]
      """
    And merge history is available in note details

  Scenario: Conflicting shortlist modifications
    Given team shortlist "Priority LPs" contains 10 LPs
    When partner@acme.com removes CalPERS from shortlist
    And simultaneously associate@acme.com adds notes to CalPERS on shortlist
    Then partner@acme.com's removal succeeds
    And associate@acme.com sees "CalPERS was removed from shortlist by partner@acme.com"
    And associate@acme.com's notes are preserved (attached to LP, not shortlist)
    And associate@acme.com can re-add CalPERS if needed

  Scenario: Real-time sync failure with offline queue
    Given partner@acme.com and associate@acme.com are both working
    When real-time WebSocket connection fails for associate@acme.com
    Then associate@acme.com sees "Real-time sync disconnected"
    And associate@acme.com can continue working
    And their changes queue locally
    When connection restores
    Then queued changes sync automatically
    And any conflicts are presented for resolution
    And sync status shows "All changes synced"

  Scenario: Admin revokes access during active session
    Given associate@acme.com is actively working on Fund III
    When partner@acme.com (admin) revokes associate@acme.com's access
    Then associate@acme.com completes their current action
    And on next action they see "Your access has been revoked"
    And they see "Contact partner@acme.com for assistance"
    And their unsaved work is preserved locally
    And they can export their notes/work before logging out

  Scenario: Bulk operation conflicts across team
    Given partner@acme.com selects 20 LPs for bulk status update
    And associate@acme.com individually updates 3 of those LPs
    When partner@acme.com applies bulk update
    Then 17 LPs are updated successfully
    And 3 LPs show conflict:
      | "3 LPs were modified by others" |
      | LP name | Modified by | Their change |
    And partner@acme.com can choose per-LP:
      | "Keep their change" |
      | "Apply my change" |

  Scenario: Concurrent fund profile edits
    Given partner@acme.com is editing Fund III profile
    And analyst@acme.com opens Fund III profile to edit
    When partner@acme.com saves changes
    Then analyst@acme.com sees "Fund III was just updated by partner@acme.com"
    And they see diff of changes
    And they can:
      | "Reload and lose my changes" |
      | "Merge my changes" |
      | "Create conflicting version for review" |

  Scenario: Team member deletes shared resource
    Given team has a shared search "Top Endowments"
    And associate@acme.com is viewing the search
    When partner@acme.com deletes "Top Endowments"
    Then associate@acme.com sees "This saved search was deleted"
    And they see option to recreate it personally
    And deletion is logged in activity feed
    And other team members are notified
```

---

### Negative Journey 6: Session Timeout During Long Operations

```gherkin
@negative @e2e
Feature: Session Timeout During Long Operations
  As a GP performing time-intensive tasks
  I want session management that preserves my work
  So that timeouts don't cause data loss

  Background:
    Given I am logged in as partner@acme.com
    And session timeout is set to 60 minutes
    And I have been working for 50 minutes

  Scenario: Session expires during pitch deck upload and extraction
    # Step 1: Start large file upload
    Given I am uploading a 20MB pitch deck
    And upload is at 40% complete
    When session expires
    Then upload continues in background
    And session token refresh is attempted

    # Step 2: Token refresh fails
    When token refresh fails (truly expired)
    Then upload pauses at current progress
    And I see "Session expired - login to continue upload"
    And upload progress is preserved server-side

    # Step 3: Re-login and resume
    When I login again
    Then I see "Resume pending upload?"
    And I see "Fund III deck - 40% uploaded"
    When I click "Resume"
    Then upload continues from 40%
    And extraction proceeds after upload completes

  Scenario: Session expires during AI generation
    Given I clicked "Generate Executive Summary"
    And generation is in progress (30 seconds elapsed)
    When session expires
    Then generation continues server-side
    And I see "Session expired"
    When I login again
    Then I see "Generation completed while you were away"
    And I see the generated summary
    And it's automatically saved to my drafts

  Scenario: Session expires with unsaved form data
    Given I am editing fund profile
    And I have modified 10 fields
    And I have not saved
    When session expires
    Then I see "Session expired"
    And I see "Your changes are preserved"
    And browser local storage contains my edits
    When I login again
    Then I see "Restore unsaved changes?"
    And I see preview of changes
    When I click "Restore"
    Then form is populated with my previous edits
    And I can save successfully

  Scenario: Session expires during bulk operation
    Given I am performing bulk status update on 50 LPs
    And 30 have been updated
    When session expires
    Then operation pauses
    And I see "Session expired - 30 of 50 LPs updated"
    When I login again
    Then I see "Continue bulk operation?"
    And I see "30 completed, 20 remaining"
    When I click "Continue"
    Then remaining 20 are processed
    And I see "50 of 50 complete"

  Scenario: Session expires during data export
    Given I requested export of 500 LPs
    And export is processing
    When session expires
    Then export continues in background
    When I login again
    Then I see "Your export is ready"
    And I can download the file
    And export was completed despite session expiry

  Scenario: Multiple tabs with different session states
    Given I have two browser tabs open
    And Tab 1 has been active, Tab 2 idle for 55 minutes
    When I interact with Tab 1 (extends session)
    Then Tab 1 session continues
    When I switch to Tab 2 and try an action
    Then Tab 2 detects session was extended in Tab 1
    And Tab 2 syncs session state
    And I can continue working in Tab 2

  Scenario: Session timeout with pending real-time updates
    Given I am receiving real-time updates (colleague is working)
    When session expires
    Then real-time connection closes
    And pending updates are queued server-side
    When I login again
    Then I see "You missed X updates"
    And I can review what changed
    And current state is synchronized

  Scenario: Graceful session extension during active work
    Given I am actively working (typing, clicking)
    And session has 5 minutes remaining
    Then I see subtle "Session expires in 5 minutes"
    And I see "Click to extend"
    When I continue working
    Then session is auto-extended
    And I see "Session extended"
    When I stop activity for 60+ minutes
    Then session expires normally

  Scenario: Session expires on mobile with app backgrounded
    Given I am using LPxGP on mobile browser
    And I switch to another app for 70 minutes
    When I return to LPxGP
    Then I see "Session expired due to inactivity"
    And I see what I was working on
    When I login again
    Then I return to the same page
    And any local edits are restored
    And I can continue my work
```

---

## Error Recovery Principles

All error paths should follow these principles:

```gherkin
Feature: Error Recovery Standards
  The platform should handle all errors gracefully

  Rule: User data should never be lost
    Scenario: Form data preserved on error
      Given I enter data in any form
      When an error occurs
      Then my entered data should be preserved
      And I should be able to retry

  Rule: Clear error messages
    Scenario: Error shows actionable message
      Given any error occurs
      Then I see what went wrong
      And I see what I can do about it
      And technical details are available if needed

  Rule: Graceful degradation
    Scenario: Partial functionality on service failure
      Given a dependent service fails
      Then core functionality should still work
      And affected features show clear status
      And recovery happens automatically when possible

  Rule: Offline capability for critical actions
    Scenario: Work continues offline
      Given I lose network connection
      Then I see offline indicator
      And I can continue viewing cached data
      And my pending changes queue for sync
      When connection restores
      Then changes sync automatically

  Rule: Session recovery
    Scenario: Session timeout recovery
      Given my session expires
      When I login again
      Then I return to where I was
      And my unsaved work is restored
      And I see what was preserved

  Rule: Audit trail for issues
    Scenario: All errors are logged
      Given any error occurs
      Then error is logged with context
      And support can investigate
      And user can reference error ID
```
