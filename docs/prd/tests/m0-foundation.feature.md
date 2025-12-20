# Milestone 0: Foundation Tests
## "Data is imported and clean"

---

## F-LP-01: LP Profile Storage [P0]

```gherkin
Feature: LP Profile Storage
  As a platform
  I want to store comprehensive LP profiles
  So that GPs can find relevant investors

  # Sub-feature: Core LP Data
  Scenario: Store LP organization details
    Given I am importing LP data
    When I create an LP with:
      | Field | Value |
      | Name | CalPERS |
      | Type | Public Pension |
      | Sub-type | State Pension |
      | Total AUM | $450B |
      | Headquarters | Sacramento, CA |
    Then the LP is stored in the database
    And all fields are properly indexed

  Scenario: Store LP investment criteria
    Given I am creating an LP profile
    When I set investment criteria:
      | Field | Value |
      | Strategies | Private Equity, Venture Capital |
      | Check Size Min | $10M |
      | Check Size Max | $100M |
      | Sweet Spot | $50M |
      | Geographic Preferences | North America, Europe |
    Then the criteria are stored
    And they can be used for filtering

  Scenario: Store LP requirements
    Given I am creating an LP profile
    When I set LP requirements:
      | Field | Value |
      | Min Track Record Years | 10 |
      | Min Fund Number | 2 |
      | Min IRR Threshold | 15% |
      | ESG Required | Yes |
    Then the requirements are stored
    And they can be used for hard filtering

  # Sub-feature: Contact Management
  Scenario: Store multiple contacts per LP
    Given an LP "Yale Endowment" exists
    When I add contacts:
      | Name | Title | Decision Maker |
      | John Smith | CIO | Yes |
      | Jane Doe | Director of PE | Yes |
      | Bob Wilson | Associate | No |
    Then the LP has 3 contacts
    And 2 are marked as decision makers

  Scenario: Store contact details
    Given I am adding a contact to an LP
    When I enter:
      | Field | Value |
      | Full Name | John Smith |
      | Title | Chief Investment Officer |
      | Email | jsmith@yale.edu |
      | Phone | +1-203-555-0100 |
      | LinkedIn | linkedin.com/in/jsmith |
      | Focus Areas | PE, VC, Real Estate |
    Then the contact is stored with all details

  # Sub-feature: Historical Data
  Scenario: Store LP commitment history
    Given an LP "CalPERS" exists
    When I add historical commitments:
      | Fund | Manager | Amount | Vintage |
      | Sequoia Capital XVI | Sequoia | $200M | 2020 |
      | Andreessen Horowitz V | a16z | $150M | 2019 |
    Then the LP has 2 historical commitments
    And I can see their investment patterns

  # Sub-feature: Data Quality
  Scenario: Calculate data quality score
    Given an LP with minimal data (only name and type)
    Then the data quality score is below 30%

    Given an LP with complete data (all fields filled)
    Then the data quality score is above 80%

  Scenario: Track data source
    Given I import an LP from CSV
    Then the data_source is "import"

    Given I manually create an LP
    Then the data_source is "manual"

  Scenario: Track verification status
    Given a newly imported LP
    Then verification_status is "unverified"

    When an admin verifies the LP data
    Then verification_status is "verified"
    And last_verified timestamp is updated
```

---

## F-LP-04: LP Data Import [P0]

```gherkin
Feature: LP Data Import
  As an admin
  I want to bulk import LP data
  So that I can quickly populate the database

  # Sub-feature: File Upload
  Scenario: Upload CSV file
    Given I am on the import page
    When I upload "lps.csv"
    Then the file is accepted
    And I see a preview of the data

  Scenario: Upload Excel file
    Given I am on the import page
    When I upload "lps.xlsx"
    Then the file is accepted
    And I see a preview of the data

  Scenario: Reject invalid file format
    Given I am on the import page
    When I upload "lps.txt"
    Then I see an error "Unsupported file format"

  Scenario: Handle large file
    Given I am on the import page
    When I upload a file with 10,000 rows
    Then the file is accepted
    And processing happens in background

  # Sub-feature: Field Mapping
  Scenario: Map CSV columns to LP fields
    Given I uploaded a CSV with columns:
      | CSV Column | LP Field |
      | Organization Name | name |
      | Investor Type | type |
      | Assets Under Management | total_aum_bn |
    When I map each column to the correct field
    Then the mapping is saved
    And preview updates to show mapped data

  Scenario: Auto-detect common column names
    Given I upload a CSV with standard column names
    Then the system auto-maps recognized columns:
      | Column | Auto-mapped to |
      | LP Name | name |
      | Type | type |
      | AUM | total_aum_bn |
      | Strategies | strategies |

  Scenario: Handle unmapped columns
    Given my CSV has a column "Custom Notes"
    When I cannot find a matching LP field
    Then I can skip this column
    Or I can map it to the "notes" field

  # Sub-feature: Validation
  Scenario: Validate required fields
    Given I mapped the CSV columns
    When a row is missing the "name" field
    Then that row is marked as invalid
    And I see "Name is required" error

  Scenario: Validate field formats
    Given I am importing LP data
    When a row has invalid AUM "not-a-number"
    Then that row is marked as invalid
    And I see "AUM must be a number" error

  Scenario: Show validation summary
    Given I imported 100 rows
    And 95 rows are valid
    And 5 rows have errors
    Then I see a summary:
      | Total | Valid | Errors |
      | 100 | 95 | 5 |
    And I can download error report

  # Sub-feature: Duplicate Detection
  Scenario: Detect duplicate by name and location
    Given "CalPERS" from "Sacramento" already exists
    When I import a row with same name and location
    Then it is flagged as potential duplicate
    And I can choose to skip or merge

  Scenario: Handle duplicates
    Given a duplicate is detected
    When I choose "Skip"
    Then the existing record is kept

    When I choose "Merge"
    Then the records are merged
    And newer data takes precedence

  # Sub-feature: Preview and Commit
  Scenario: Preview before commit
    Given I mapped and validated my import
    Then I see a preview of first 20 rows
    And I see the total count to import
    And I see "Approve Import" button

  Scenario: Approve import
    Given I reviewed the preview
    When I click "Approve Import"
    Then the import job starts
    And I see progress indicator
    And records are inserted into database

  Scenario: Cancel import
    Given I reviewed the preview
    When I click "Cancel"
    Then no data is imported
    And I return to the import page

  Scenario: Import job progress
    Given an import job is running
    Then I see:
      | Processed | Successful | Failed |
      | 50/100 | 48 | 2 |
    And I can see which rows failed
```

---

## F-LP-05: LP Data Cleaning Pipeline [P0]

```gherkin
Feature: LP Data Cleaning Pipeline
  As a platform
  I want to standardize imported data
  So that matching is accurate

  # Sub-feature: Strategy Normalization
  Scenario: Normalize strategy names
    Given raw strategy data:
      | Input | Expected Output |
      | pe | Private Equity |
      | PE | Private Equity |
      | Private equity | Private Equity |
      | vc | Venture Capital |
      | venture | Venture Capital |
      | buyout | Private Equity - Buyout |
      | growth equity | Private Equity - Growth |
    When the cleaning pipeline runs
    Then strategies are normalized to taxonomy

  Scenario: Handle unknown strategies
    Given raw strategy "Cryptocurrency Funds"
    When it's not in our taxonomy
    Then it passes through unchanged
    And it's flagged for review

  # Sub-feature: Geography Normalization
  Scenario: Normalize country names
    Given raw geography data:
      | Input | Expected Code | Region |
      | us | US | North America |
      | USA | US | North America |
      | United States | US | North America |
      | uk | GB | Europe |
      | United Kingdom | GB | Europe |
    When the cleaning pipeline runs
    Then countries are normalized to ISO codes
    And regions are assigned

  Scenario: Handle city names
    Given raw geography "San Francisco"
    When the cleaning pipeline runs
    Then it's mapped to "US" country code
    And region is "North America"

  # Sub-feature: LP Type Normalization
  Scenario: Normalize LP types
    Given raw type data:
      | Input | Expected Output |
      | pension | Public Pension |
      | Pension Fund | Public Pension |
      | endowment | Endowment |
      | FO | Family Office |
      | family office | Family Office |
      | sovereign wealth | Sovereign Wealth Fund |
    When the cleaning pipeline runs
    Then types are normalized

  # Sub-feature: Contact Parsing
  Scenario: Parse contact information
    Given raw contact "John Smith, CIO, jsmith@calpers.ca.gov"
    When the cleaning pipeline runs
    Then I get:
      | Field | Value |
      | Name | John Smith |
      | Title | CIO |
      | Email | jsmith@calpers.ca.gov |

  Scenario: Validate email format
    Given raw email "not-valid-email"
    When the cleaning pipeline runs
    Then the email is flagged as invalid
    And the record is queued for review

  # Sub-feature: Duplicate Detection and Merge
  Scenario: Detect duplicates
    Given two records:
      | Name | Location |
      | CalPERS | Sacramento, CA |
      | California Public Employees | Sacramento |
    When the cleaning pipeline runs
    Then they are flagged as potential duplicates
    And similarity score is shown

  Scenario: Merge duplicate records
    Given confirmed duplicate records
    When I merge them
    Then the most complete data is kept
    And a single record remains
    And merge history is logged

  # Sub-feature: Data Quality Flags
  Scenario: Flag low-quality records
    Given an LP with only name and type filled
    When the cleaning pipeline runs
    Then data_quality_score is calculated
    And records below threshold are flagged
    And they're added to review queue

  Scenario: Manual review queue
    Given records are flagged for review
    When an admin views the review queue
    Then they see:
      | LP Name | Issue | Data Quality |
      | Unknown LP | Missing type | 25% |
      | Bad Data Inc | Invalid email | 40% |
    And they can fix or delete each record

  # Sub-feature: AI-Assisted Extraction
  Scenario: Extract fields from messy data
    Given raw notes "Looking for PE funds, $25-50M checks, US focused"
    When AI extraction runs
    Then it suggests:
      | Field | Extracted Value |
      | Strategies | Private Equity |
      | Check Size Min | $25M |
      | Check Size Max | $50M |
      | Geography | US |
    And admin can approve or edit
```

---

## E2E: Data Import Journey

```gherkin
Feature: Complete Data Import Journey
  As an admin
  I want to import and clean LP data
  So that the database is populated with quality data

  Scenario: Import LP data from spreadsheet
    Given I am logged in as admin
    And I have a spreadsheet with 500 LPs

    # Upload
    When I go to Admin > Import
    And I upload "lp_database.xlsx"
    Then I see "File uploaded successfully"

    # Map columns
    When I map CSV columns to LP fields
    And I confirm the mapping
    Then I see a preview of 20 rows

    # Validation
    When validation runs
    Then I see:
      | Valid Rows | Errors | Duplicates |
      | 480 | 10 | 10 |
    And I can download error report

    # Review errors
    When I click "View Errors"
    Then I see each error with details
    And I can fix in-line or skip

    # Handle duplicates
    When I click "View Duplicates"
    Then I see potential matches
    And I choose Skip or Merge for each

    # Approve import
    When I click "Approve Import"
    Then import job starts
    And I see progress bar
    And after completion I see "480 LPs imported"

    # Cleaning
    When the cleaning pipeline runs
    Then strategies are normalized
    And geographies are standardized
    And quality scores are calculated
    And 15 records are flagged for review

    # Final review
    When I go to Review Queue
    Then I see 15 low-quality records
    And I can fix or delete each one
```
