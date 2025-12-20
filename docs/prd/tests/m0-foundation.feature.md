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

  # Negative: Missing required fields
  Scenario: Reject LP without name
    Given I am importing LP data
    When I create an LP with:
      | Field | Value |
      | Name | |
      | Type | Public Pension |
    Then I see error "Name is required"
    And the LP is not created

  Scenario: Reject LP with whitespace-only name
    Given I am importing LP data
    When I create an LP with:
      | Field | Value |
      | Name | "   " |
      | Type | Public Pension |
    Then I see error "Name is required"
    And the LP is not created

  Scenario: Reject LP without type
    Given I am importing LP data
    When I create an LP with:
      | Field | Value |
      | Name | Test LP |
      | Type | |
    Then I see error "Type is required"
    And the LP is not created

  # Negative: Invalid field values
  Scenario: Reject invalid LP type
    Given I am importing LP data
    When I create an LP with:
      | Field | Value |
      | Name | Test LP |
      | Type | Invalid Type XYZ |
    Then I see error "Invalid LP type"
    And the LP is not created

  Scenario: Reject negative AUM
    Given I am importing LP data
    When I create an LP with:
      | Field | Value |
      | Name | Test LP |
      | Type | Public Pension |
      | Total AUM | -$10B |
    Then I see error "AUM cannot be negative"

  Scenario: Reject unrealistic AUM
    Given I am importing LP data
    When I create an LP with:
      | Field | Value |
      | Name | Test LP |
      | Type | Public Pension |
      | Total AUM | $999999999T |
    Then I see error "AUM value is unrealistic"

  # Negative: Name length limits
  Scenario: Reject name that is too long
    Given I am importing LP data
    When I create an LP with a name longer than 500 characters
    Then I see error "Name is too long (max 500 characters)"

  Scenario: Accept minimum valid name
    Given I am importing LP data
    When I create an LP with:
      | Field | Value |
      | Name | AB |
      | Type | Family Office |
    Then the LP is created successfully

  # Security: Injection attempts
  Scenario: Sanitize SQL injection in name
    Given I am importing LP data
    When I create an LP with:
      | Field | Value |
      | Name | '; DROP TABLE lps; -- |
      | Type | Public Pension |
    Then the name is stored as literal text
    And no SQL is executed
    And the database is intact

  Scenario: Sanitize XSS in name
    Given I am importing LP data
    When I create an LP with:
      | Field | Value |
      | Name | <script>alert('xss')</script> |
      | Type | Public Pension |
    Then the name is HTML-escaped when displayed
    And no script is executed

  # Edge cases: Unicode and special characters
  Scenario: Handle unicode in LP name
    Given I am importing LP data
    When I create an LP with:
      | Field | Value |
      | Name | 北京投资基金 |
      | Type | Sovereign Wealth Fund |
    Then the LP is stored correctly
    And the name displays properly

  Scenario: Handle emojis in notes
    Given I am importing LP data
    When I create an LP with notes containing "Great partner 👍🏼"
    Then the notes are stored correctly

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

  # Negative: Invalid investment criteria
  Scenario: Reject check size min greater than max
    Given I am creating an LP profile
    When I set investment criteria:
      | Field | Value |
      | Check Size Min | $100M |
      | Check Size Max | $10M |
    Then I see error "Minimum check size cannot exceed maximum"

  Scenario: Reject negative check sizes
    Given I am creating an LP profile
    When I set investment criteria:
      | Field | Value |
      | Check Size Min | -$10M |
    Then I see error "Check size cannot be negative"

  Scenario: Reject sweet spot outside min/max range
    Given I am creating an LP profile
    When I set investment criteria:
      | Field | Value |
      | Check Size Min | $10M |
      | Check Size Max | $50M |
      | Sweet Spot | $100M |
    Then I see error "Sweet spot must be between min and max check size"

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

  # Negative: Invalid requirements
  Scenario: Reject negative track record years
    Given I am creating an LP profile
    When I set LP requirements:
      | Field | Value |
      | Min Track Record Years | -5 |
    Then I see error "Track record years cannot be negative"

  Scenario: Reject negative fund number
    Given I am creating an LP profile
    When I set LP requirements:
      | Field | Value |
      | Min Fund Number | -1 |
    Then I see error "Fund number cannot be negative"

  Scenario: Reject IRR threshold over 100%
    Given I am creating an LP profile
    When I set LP requirements:
      | Field | Value |
      | Min IRR Threshold | 150% |
    Then I see error "IRR threshold must be between 0% and 100%"

  # Sub-feature: People & Employment Management
  # Note: Contacts are stored in global "people" table with "employment" records
  # linking them to organizations. This enables career tracking across the industry.

  Scenario: Store multiple contacts for an LP
    Given an LP "Yale Endowment" exists
    When I create people with current employment at Yale Endowment:
      | Name | Title | Decision Maker |
      | John Smith | CIO | Yes |
      | Jane Doe | Director of PE | Yes |
      | Bob Wilson | Associate | No |
    Then 3 people are linked to Yale Endowment via employment records
    And 2 are marked as decision makers

  Scenario: Store person details with employment
    Given an LP "Yale Endowment" exists
    When I create a person:
      | Field | Value |
      | Full Name | John Smith |
      | Email | jsmith@yale.edu |
      | Phone | +1-203-555-0100 |
      | LinkedIn | linkedin.com/in/jsmith |
      | Focus Areas | PE, VC, Real Estate |
    And I create an employment record:
      | Field | Value |
      | Organization | Yale Endowment |
      | Org Type | lp |
      | Title | Chief Investment Officer |
      | Is Current | Yes |
      | Start Date | 2015-01-01 |
    Then the person is stored in the global people table
    And the employment record links them to Yale Endowment

  Scenario: Track employment history
    Given a person "John Smith" worked at:
      | Organization | Title | Start Date | End Date |
      | Stanford Endowment | Associate | 2010-01-01 | 2014-12-31 |
      | Yale Endowment | CIO | 2015-01-01 | NULL |
    Then John Smith has 2 employment records
    And 1 is marked as current (Yale)
    And 1 is marked as historical (Stanford)

  # Negative: Invalid person data
  Scenario: Reject person without name
    Given I am creating a person
    When I enter:
      | Field | Value |
      | Full Name | |
      | Email | test@example.com |
    Then I see error "Name is required"
    And the person is not created

  Scenario: Reject invalid email format
    Given I am creating a person
    When I enter:
      | Field | Value |
      | Full Name | John Smith |
      | Email | not-a-valid-email |
    Then I see error "Invalid email format"

  Scenario: Reject invalid email formats (variations)
    Given I am creating a person
    When I try these invalid emails:
      | Invalid Email |
      | @example.com |
      | user@ |
      | user@.com |
      | user space@example.com |
      | user@example |
    Then each is rejected with "Invalid email format"

  Scenario: Accept valid email edge cases
    Given I am creating a person
    When I try these valid emails:
      | Valid Email |
      | user+tag@example.com |
      | user.name@subdomain.example.com |
      | user@example.co.uk |
    Then each is accepted

  Scenario: Reject invalid phone format
    Given I am creating a person
    When I enter:
      | Field | Value |
      | Full Name | John Smith |
      | Phone | abc123 |
    Then I see error "Invalid phone number format"

  Scenario: Reject invalid LinkedIn URL
    Given I am creating a person
    When I enter:
      | Field | Value |
      | Full Name | John Smith |
      | LinkedIn | facebook.com/jsmith |
    Then I see error "LinkedIn URL must be from linkedin.com"

  Scenario: Reject employment with end date before start date
    Given I am creating an employment record
    When I enter:
      | Field | Value |
      | Start Date | 2020-01-01 |
      | End Date | 2019-01-01 |
    Then I see error "End date cannot be before start date"

  Scenario: Handle person moving between organizations
    Given a person "John Smith" is currently at "Stanford Endowment"
    When I update their employment:
      | Action | Details |
      | End current | Stanford Endowment ends 2024-12-01 |
      | Start new | Yale Endowment starts 2024-12-15 |
    Then John Smith's current org is "Yale Endowment"
    And Stanford employment is marked as historical
    And all employment history is preserved

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

  # Negative: File upload errors
  Scenario: Reject empty file
    Given I am on the import page
    When I upload an empty CSV file
    Then I see error "File is empty"

  Scenario: Reject file with only headers
    Given I am on the import page
    When I upload a CSV with headers but no data rows
    Then I see error "File contains no data rows"

  Scenario: Reject file exceeding size limit
    Given I am on the import page
    When I upload a file larger than 50MB
    Then I see error "File too large (max 50MB)"

  Scenario: Reject malformed CSV
    Given I am on the import page
    When I upload a CSV with inconsistent column counts
    Then I see error "Malformed CSV: inconsistent column count"

  Scenario: Handle wrong encoding gracefully
    Given I am on the import page
    When I upload a CSV with non-UTF8 encoding
    Then I see warning "File encoding detected as [encoding]"
    And file is converted to UTF-8

  Scenario: Reject file without headers
    Given I am on the import page
    When I upload a CSV without a header row
    Then I see error "CSV must have a header row"

  # Security: Malicious file uploads
  Scenario: Reject file with executable content
    Given I am on the import page
    When I upload a file named "data.csv.exe"
    Then I see error "Unsupported file format"

  Scenario: Reject file with embedded macros
    Given I am on the import page
    When I upload an Excel file with macros (.xlsm)
    Then I see error "Excel files with macros are not allowed"

  Scenario: Scan for formula injection
    Given I am on the import page
    When I upload a CSV with cells starting with "=", "+", "-", or "@"
    Then those cells are escaped or flagged
    And no formulas are executed

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

  # Negative: Field mapping errors
  Scenario: Require mapping of required fields
    Given I uploaded a CSV
    When I try to proceed without mapping "name" column
    Then I see error "Required field 'name' must be mapped"
    And I cannot proceed to preview

  Scenario: Prevent duplicate field mappings
    Given I uploaded a CSV
    When I map two columns to the same field "name"
    Then I see error "Field 'name' is already mapped"

  Scenario: Warn about unmapped columns
    Given I uploaded a CSV with 10 columns
    When I only map 3 columns
    Then I see warning "7 columns will be ignored"
    And I can proceed if I acknowledge

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

  # Negative: Validation edge cases
  Scenario: Handle all rows invalid
    Given I imported 100 rows
    And all rows have errors
    Then I see error "No valid rows to import"
    And I cannot proceed to import

  Scenario: Show row-level error details
    Given a row has multiple validation errors
    Then I see all errors for that row:
      | Error |
      | Name is required |
      | Invalid AUM format |
      | Unknown LP type |

  Scenario: Handle very long field values
    Given a row has a name field with 10,000 characters
    Then that row is marked as invalid
    And I see "Name exceeds maximum length (500 characters)"

  Scenario: Handle special characters in data
    Given a row has a name containing "Acme & Partners, LLC (\"The Fund\")"
    Then the name is stored correctly
    And special characters are preserved

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

  # Negative: Normalization edge cases
  Scenario: Handle empty strategy field
    Given raw strategy is empty or null
    When the cleaning pipeline runs
    Then the field remains empty
    And record is flagged for review

  Scenario: Handle strategy with only whitespace
    Given raw strategy "   "
    When the cleaning pipeline runs
    Then the field is set to null
    And record is flagged for review

  Scenario: Handle multiple strategies with typos
    Given raw strategy "PE, VC, Real Esstate, Infrastucture"
    When the cleaning pipeline runs
    Then correctly spelled ones are normalized
    And "Real Esstate" and "Infrastucture" are flagged for review

  Scenario: Handle comma vs semicolon separators
    Given raw strategy "PE; VC; Real Estate"
    When the cleaning pipeline runs
    Then all three strategies are parsed correctly

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

  # Negative: Geography edge cases
  Scenario: Handle unknown geography
    Given raw geography "Atlantis"
    When the cleaning pipeline runs
    Then it passes through unchanged
    And record is flagged for review

  Scenario: Handle ambiguous city names
    Given raw geography "London" (could be UK or Canada)
    When the cleaning pipeline runs
    Then it's flagged as ambiguous
    And admin can resolve manually

  Scenario: Handle misspelled countries
    Given raw geography "Unted States" or "Gerrmany"
    When the cleaning pipeline runs
    Then fuzzy matching suggests corrections
    And record is flagged for review

  Scenario: Handle mixed geography formats
    Given raw geography "New York, NY, USA"
    When the cleaning pipeline runs
    Then country is extracted as "US"
    And state/city info is preserved

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

  # Sub-feature: Person/Contact Parsing
  # Note: Parsed contacts become people records with employment links

  Scenario: Parse contact information into person + employment
    Given raw contact "John Smith, CIO, jsmith@calpers.ca.gov" for LP "CalPERS"
    When the cleaning pipeline runs
    Then I get a person record:
      | Field | Value |
      | Name | John Smith |
      | Email | jsmith@calpers.ca.gov |
    And an employment record:
      | Field | Value |
      | Title | CIO |
      | Org | CalPERS |
      | Is Current | Yes |

  Scenario: Validate email format
    Given raw email "not-valid-email"
    When the cleaning pipeline runs
    Then the email is flagged as invalid
    And the record is queued for review

  # Negative: Person parsing edge cases
  Scenario: Handle unparseable contact string
    Given raw contact "asdfghjkl random text"
    When the cleaning pipeline runs
    Then the raw text is stored as notes on the person
    And record is flagged for manual entry

  Scenario: Handle contact with missing components
    Given raw contact "John Smith" (no title or email)
    When the cleaning pipeline runs
    Then name is extracted
    And title and email remain empty
    And person is created with employment (title empty)
    And record is flagged for enrichment

  Scenario: Handle international phone formats
    Given raw phone numbers:
      | Input | Valid |
      | +1 (555) 123-4567 | Yes |
      | +44 20 7946 0958 | Yes |
      | +86 21 1234 5678 | Yes |
      | 555-1234 | Partial (missing area code) |
    When the cleaning pipeline runs
    Then valid formats are stored
    And partial formats are flagged

  Scenario: Handle multiple emails in one field
    Given raw contact with "john@example.com; jane@example.com" for LP "CalPERS"
    When the cleaning pipeline runs
    Then two person records are created
    And each has employment linking to CalPERS

  Scenario: Detect existing person by email
    Given a person "John Smith" exists with email "jsmith@calpers.ca.gov"
    When importing contact "J. Smith, CIO, jsmith@calpers.ca.gov" for LP "Yale Endowment"
    Then the existing person is found (not duplicated)
    And a new employment record links them to Yale Endowment
    And previous CalPERS employment remains intact

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

  # Negative: Duplicate detection edge cases
  Scenario: Handle false positive duplicates
    Given two genuinely different LPs with similar names:
      | Name |
      | Capital One Ventures |
      | Capital Two Partners |
    When the cleaning pipeline runs
    Then they are NOT flagged as duplicates

  Scenario: Handle exact duplicate entries
    Given two records with identical data
    When the cleaning pipeline runs
    Then one is automatically removed
    And the other is kept

  Scenario: Handle partial duplicates with conflicts
    Given two records with same name but different data:
      | Field | Record 1 | Record 2 |
      | Name | CalPERS | CalPERS |
      | AUM | $450B | $480B |
      | Contact | John | Jane |
    When they are merged
    Then admin must resolve conflicts
    And merge is not automatic

  Scenario: Prevent merge of different LP types
    Given two records with same name but different types:
      | Name | Type |
      | Alpha Capital | Family Office |
      | Alpha Capital | Public Pension |
    When duplicate is flagged
    Then merge requires explicit confirmation
    And type mismatch is highlighted

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

  # Error scenarios for E2E
  Scenario: Handle import failure gracefully
    Given I am logged in as admin
    And I have a spreadsheet with 500 LPs

    When I upload "lp_database.xlsx"
    And the file is corrupted
    Then I see error "Unable to read file. Please check the file format."
    And no partial data is imported

  Scenario: Handle network failure during import
    Given I approved an import of 500 LPs
    And 250 records have been imported
    When the network connection fails
    Then the import is paused
    And I can resume from where it stopped
    And no data is lost or duplicated

  Scenario: Handle validation blocking import
    Given I uploaded a CSV
    And 100% of rows have validation errors
    Then I cannot proceed to import
    And I see "No valid rows to import"
    And I must fix errors or cancel

  Scenario: Timeout handling for large imports
    Given I am importing 50,000 LPs
    When the import takes longer than 30 minutes
    Then it continues in background
    And I receive email notification on completion
    And I can check status anytime
```
