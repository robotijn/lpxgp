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

---

## Negative Test Scenarios

### Database Constraint Violations

```gherkin
Feature: Database Constraint Handling
  As a platform
  I want to handle database constraint violations gracefully
  So that data integrity is maintained and users get clear error messages

  @negative
  Scenario: Reject duplicate LP name and location (unique constraint)
    Given an LP exists:
      | Name | Headquarters |
      | CalPERS | Sacramento, CA |
    When I create an LP with:
      | Name | Headquarters |
      | CalPERS | Sacramento, CA |
    Then I see error "An LP with this name and location already exists"
    And the duplicate is not created

  @negative
  Scenario: Reject person with duplicate email (unique constraint)
    Given a person exists with email "jsmith@example.com"
    When I create a person with:
      | Full Name | Email |
      | Jane Doe | jsmith@example.com |
    Then I see error "A person with this email already exists"
    And the duplicate person is not created

  @negative
  Scenario: Reject employment referencing non-existent organization (foreign key)
    Given no LP with ID "non-existent-lp-id" exists
    When I create an employment record:
      | Organization ID | Title |
      | non-existent-lp-id | CIO |
    Then I see error "Organization not found"
    And the employment record is not created

  @negative
  Scenario: Reject commitment referencing non-existent LP (foreign key)
    Given no LP with ID "non-existent-lp-id" exists
    When I add a historical commitment:
      | LP ID | Fund | Amount |
      | non-existent-lp-id | Sequoia XVI | $200M |
    Then I see error "LP not found"
    And the commitment is not created

  @negative
  Scenario: Reject employment referencing non-existent person (foreign key)
    Given no person with ID "non-existent-person-id" exists
    When I create an employment record:
      | Person ID | Organization | Title |
      | non-existent-person-id | CalPERS | CIO |
    Then I see error "Person not found"
    And the employment record is not created

  @negative
  Scenario: Handle cascade delete protection for LP with relationships
    Given an LP "CalPERS" exists
    And CalPERS has 5 associated people via employment
    And CalPERS has 10 historical commitments
    When I try to delete CalPERS
    Then I see error "Cannot delete LP with existing relationships"
    And I see "5 employment records and 10 commitments reference this LP"
    And the LP is not deleted

  @negative
  Scenario: Handle cascade delete protection for person with employment
    Given a person "John Smith" exists
    And John Smith has 3 employment records
    When I try to delete John Smith
    Then I see error "Cannot delete person with existing employment history"
    And I see "3 employment records reference this person"
    And the person is not deleted

  @negative
  Scenario: Reject invalid enum value (check constraint)
    Given I am creating an LP
    When I set verification_status to "invalid_status"
    Then I see error "Invalid verification status"
    And valid options are shown: "unverified, verified, pending_review"

  @negative
  Scenario: Reject data_source with invalid value (check constraint)
    Given I am creating an LP
    When I set data_source to "magic"
    Then I see error "Invalid data source"
    And valid options are shown: "import, manual, api, enrichment"
```

### Invalid Data Formats in Imports

```gherkin
Feature: Invalid Import Data Format Handling
  As an admin
  I want clear errors when import data has invalid formats
  So that I can fix the source data

  @negative
  Scenario: Reject CSV with binary content
    Given I am on the import page
    When I upload a file that is actually a PNG image renamed to .csv
    Then I see error "File content does not match CSV format"
    And the file is rejected

  @negative
  Scenario: Reject CSV with null bytes
    Given I am on the import page
    When I upload a CSV containing null bytes (binary data)
    Then I see error "File contains invalid characters (null bytes)"
    And the file is rejected

  @negative
  Scenario: Handle CSV with mixed line endings
    Given I am on the import page
    When I upload a CSV with mixed CRLF and LF line endings
    Then the file is normalized
    And all rows are parsed correctly

  @negative
  Scenario: Reject CSV with BOM causing column issues
    Given I am on the import page
    When I upload a CSV with UTF-8 BOM
    Then the BOM is stripped
    And the first column name is parsed correctly
    And no hidden characters remain

  @negative
  Scenario: Handle CSV with quoted fields containing newlines
    Given I am on the import page
    When I upload a CSV where a field contains:
      """
      "Multi
      line
      value"
      """
    Then the field is parsed as single value with newlines
    And the row count is correct

  @negative
  Scenario: Reject CSV with unescaped quotes
    Given I am on the import page
    When I upload a CSV with field: "Value with "unescaped" quotes"
    Then I see error "Malformed CSV: unescaped quotes on row 5"
    And the row number is indicated

  @negative
  Scenario: Handle extremely long single row
    Given I am on the import page
    When I upload a CSV where one row has 100,000+ characters
    Then I see error "Row 42 exceeds maximum length (10,000 characters)"
    And the row is skipped
    And processing continues

  @negative
  Scenario: Reject CSV with too many columns
    Given I am on the import page
    When I upload a CSV with 500 columns
    Then I see error "Too many columns (max 100)"
    And the file is rejected

  @negative
  Scenario: Handle date format variations
    Given I am importing data with date fields
    When dates are in various formats:
      | Input | Parsed |
      | 2024-01-15 | 2024-01-15 |
      | 01/15/2024 | 2024-01-15 |
      | 15-Jan-2024 | 2024-01-15 |
      | January 15, 2024 | 2024-01-15 |
    Then all valid dates are parsed correctly

  @negative
  Scenario: Reject invalid date formats
    Given I am importing data with date fields
    When a date field contains:
      | Invalid Date |
      | not-a-date |
      | 2024-13-45 |
      | 00/00/0000 |
      | 32-Jan-2024 |
    Then each is flagged as invalid
    And I see "Invalid date format" error

  @negative
  Scenario: Handle AUM format variations
    Given I am importing LP data
    When AUM values are in various formats:
      | Input | Parsed |
      | $450B | 450000000000 |
      | 450 billion | 450000000000 |
      | $10M | 10000000 |
      | 10,000,000 | 10000000 |
      | 450bn | 450000000000 |
    Then all valid AUM values are parsed correctly

  @negative
  Scenario: Reject ambiguous AUM formats
    Given I am importing LP data
    When AUM value is "450" without unit
    Then it is flagged as ambiguous
    And I see warning "AUM value lacks unit (M/B/T) - please verify"

  @negative
  Scenario: Handle percentage format variations
    Given I am importing LP requirements
    When IRR threshold values are:
      | Input | Parsed |
      | 15% | 0.15 |
      | 15 | 0.15 |
      | 0.15 | 0.15 |
      | 15 percent | 0.15 |
    Then all valid percentages are parsed correctly

  @negative
  Scenario: Reject Excel file with password protection
    Given I am on the import page
    When I upload a password-protected Excel file
    Then I see error "Password-protected files are not supported"
    And the file is rejected
```

### Data Corruption Handling

```gherkin
Feature: Data Corruption Detection and Recovery
  As a platform
  I want to detect and handle data corruption
  So that data integrity is maintained

  @negative
  Scenario: Detect corrupted JSON in strategy field
    Given an LP record has corrupted JSON in strategies field: "{invalid json"
    When I try to load the LP profile
    Then the error is logged
    And I see a graceful error message: "Some data could not be loaded"
    And the page still renders with available data
    And the record is flagged for admin review

  @negative
  Scenario: Detect orphaned employment records
    Given an employment record references LP ID "deleted-lp"
    And no LP with that ID exists (orphaned record)
    When the data integrity check runs
    Then the orphaned record is detected
    And it is moved to a quarantine table
    And admin is notified

  @negative
  Scenario: Detect orphaned commitment records
    Given a commitment record references a non-existent LP
    When the data integrity check runs
    Then the orphaned record is detected
    And it is logged for admin review
    And it does not break LP listing queries

  @negative
  Scenario: Handle truncated data in long text fields
    Given notes field was truncated mid-sentence: "This LP focuses on growth equi..."
    When I view the LP profile
    Then the truncated data is displayed
    And a warning icon indicates incomplete data

  @negative
  Scenario: Detect and handle invalid UTF-8 sequences
    Given a record contains invalid UTF-8 bytes
    When I try to load the record
    Then invalid sequences are replaced with replacement character
    And the record is flagged for cleaning
    And the page renders successfully

  @negative
  Scenario: Handle database connection failure during write
    Given I am creating a new LP
    When the database connection fails mid-transaction
    Then the transaction is rolled back
    And I see error "Unable to save. Please try again."
    And no partial data is written

  @negative
  Scenario: Handle database timeout during read
    Given I am loading an LP profile
    When the database query times out after 30 seconds
    Then I see error "Request timed out. Please try again."
    And a retry button is shown

  @negative
  Scenario: Detect circular employment references
    Given person A has employment at org B
    And org B is somehow linked to person A as owner
    When the data integrity check runs
    Then circular references are detected
    And they are flagged for manual resolution

  @negative
  Scenario: Handle corrupted file upload (partial upload)
    Given I am uploading a large CSV file
    When the upload is interrupted at 50%
    Then I see error "Upload incomplete"
    And no partial file is processed
    And I can retry the upload

  @negative
  Scenario: Detect schema version mismatch
    Given the database schema was updated
    And some records have old schema format
    When I load a record with old format
    Then backward compatibility handler runs
    And the record is migrated to new format
    And migration is logged

  @negative
  Scenario: Handle vector embedding corruption
    Given an LP has a corrupted embedding (wrong dimensions)
    When semantic search runs
    Then the corrupted embedding is skipped
    And search results exclude that LP
    And the LP is flagged for re-embedding

  @negative
  Scenario: Detect duplicate primary keys after restore
    Given database was restored from backup
    And new records were created before restore
    When I try to create a record with existing ID
    Then I see error "Record ID conflict"
    And the conflict is logged for admin resolution
```

### Concurrent Edit Conflicts

```gherkin
Feature: Concurrent Edit Conflict Handling
  As a platform
  I want to handle concurrent edits gracefully
  So that users don't lose their work

  @negative
  Scenario: Detect concurrent edit on LP profile
    Given user A is editing LP "CalPERS"
    And user B is also editing LP "CalPERS"
    When user A saves changes at 10:00:00
    And user B tries to save changes at 10:00:05
    Then user B sees error "This record was modified by another user"
    And user B sees the conflicting changes
    And user B can choose to:
      | Option |
      | Overwrite with my changes |
      | Discard my changes |
      | Merge changes manually |

  @negative
  Scenario: Prevent lost updates with optimistic locking
    Given I loaded LP "CalPERS" at version 5
    When another user updates it to version 6
    And I try to save my changes
    Then I see error "Record has been updated since you loaded it"
    And my changes are preserved in the form
    And I can reload and reapply changes

  @negative
  Scenario: Handle concurrent import jobs
    Given admin A starts importing "file1.csv" with 500 LPs
    And admin B starts importing "file2.csv" with 500 LPs
    When both jobs try to create LP "CalPERS"
    Then one job succeeds
    And the other job flags it as duplicate
    And no data corruption occurs

  @negative
  Scenario: Handle concurrent delete and update
    Given user A is editing LP "CalPERS"
    When user B deletes LP "CalPERS"
    And user A tries to save changes
    Then user A sees error "This record has been deleted"
    And user A's changes are not saved
    And user A can create a new record with their data

  @negative
  Scenario: Handle concurrent person merge
    Given two merge operations on the same person are initiated
    When both try to execute simultaneously
    Then only one merge succeeds
    And the other sees error "Record is being modified"
    And data integrity is maintained

  @negative
  Scenario: Handle session timeout during edit
    Given I am editing an LP profile
    And my session has been open for 2 hours
    When my session expires
    And I try to save changes
    Then I see "Session expired. Please log in again."
    And my changes are preserved in local storage
    And after re-login I can recover my edits

  @negative
  Scenario: Handle concurrent employment updates for same person
    Given person "John Smith" works at "CalPERS"
    And admin A is updating John's title to "CIO"
    And admin B is updating John's title to "Director"
    When both save simultaneously
    Then one update succeeds
    And the other sees conflict notification
    And employment history shows both attempts

  @negative
  Scenario: Prevent race condition in duplicate detection
    Given I am importing 1000 LPs
    And "CalPERS" appears twice in the file (rows 50 and 500)
    When import runs in parallel batches
    Then only one "CalPERS" is created
    And the duplicate is detected and skipped
    And no constraint violation occurs

  @negative
  Scenario: Handle concurrent data quality score updates
    Given LP "CalPERS" has quality score 75%
    And two different enrichment jobs update it simultaneously
    When both try to update the quality score
    Then the final score reflects the latest complete calculation
    And intermediate states are not visible to users

  @negative
  Scenario: Lock record during long-running operation
    Given I initiate AI extraction on LP notes (takes 30 seconds)
    When another user tries to edit the LP
    Then they see warning "Record is being processed"
    And they can choose to wait or edit anyway
    And if they edit anyway, they're warned of potential conflicts
```

### Large File Handling Edge Cases

```gherkin
Feature: Large File Handling Edge Cases
  As an admin
  I want reliable handling of large import files
  So that bulk imports don't fail unexpectedly

  @negative
  Scenario: Handle file with 100,000+ rows
    Given I am on the import page
    When I upload a CSV with 150,000 rows
    Then the file is accepted
    And processing is queued for background execution
    And I see estimated processing time: "~15 minutes"
    And I receive email notification on completion

  @negative
  Scenario: Handle file approaching memory limits
    Given I am on the import page
    When I upload a 45MB CSV file (near the 50MB limit)
    Then the file is accepted
    And streaming processing is used
    And memory usage remains stable
    And progress is reported every 1000 rows

  @negative
  Scenario: Reject file exceeding absolute limit
    Given I am on the import page
    When I upload a 100MB CSV file
    Then I see error "File too large (max 50MB)"
    And the upload is rejected before complete transfer
    And server resources are not exhausted

  @negative
  Scenario: Handle slow upload on poor connection
    Given I am on the import page
    And my connection speed is 100Kbps
    When I upload a 10MB file
    Then upload progress is shown
    And timeout is extended for slow connections
    And upload completes successfully after 15 minutes

  @negative
  Scenario: Handle upload interruption and resume
    Given I am uploading a 40MB file
    And upload reaches 60% complete
    When network interruption occurs
    Then I see "Upload interrupted"
    And I can resume from 60%
    And I don't need to restart from beginning

  @negative
  Scenario: Handle file with very wide rows (many columns)
    Given I am on the import page
    When I upload a CSV with 80 columns and 10,000 rows
    Then the file is accepted
    And column mapping interface handles scrolling
    And performance remains acceptable

  @negative
  Scenario: Handle file with very long cell values
    Given I am on the import page
    When I upload a CSV where notes field contains 50,000 characters
    Then I see warning "Row 42: notes field truncated to 10,000 characters"
    And import continues with truncated data
    And original full text is logged for recovery

  @negative
  Scenario: Handle compressed file uploads
    Given I am on the import page
    When I upload "lps.csv.gz" (gzipped CSV)
    Then the file is decompressed
    And the CSV is processed normally
    And I see "Decompressed size: 40MB"

  @negative
  Scenario: Reject zip bomb attack
    Given I am on the import page
    When I upload a small file that expands to 10GB when decompressed
    Then decompression stops at 50MB limit
    And I see error "Compressed file expands beyond limits"
    And the file is rejected

  @negative
  Scenario: Handle background job failure recovery
    Given I started a large import (50,000 rows)
    And processing fails at row 25,000 due to server restart
    When the server recovers
    Then the job is automatically resumed
    And processing continues from row 25,000
    And no duplicate records are created

  @negative
  Scenario: Handle concurrent large imports from multiple admins
    Given admin A uploads 50,000 rows
    And admin B uploads 30,000 rows simultaneously
    When both imports run in parallel
    Then both complete successfully
    And system resources are balanced fairly
    And neither job starves the other

  @negative
  Scenario: Report progress accurately for large files
    Given I am importing 100,000 rows
    When I check progress at various points
    Then progress percentage matches actual row count
    And estimated time remaining is reasonably accurate
    And I can see rows processed per second

  @negative
  Scenario: Handle import cancellation midway
    Given I started importing 50,000 rows
    And 20,000 rows have been processed
    When I click "Cancel Import"
    Then processing stops within 5 seconds
    And already-imported records remain (no rollback)
    And I see "Import cancelled. 20,000 records imported."
    And I can continue or restart import later

  @negative
  Scenario: Handle validation on very large files
    Given I upload a CSV with 100,000 rows
    When validation runs on all rows
    Then validation completes in reasonable time (<5 minutes)
    And errors are batched for display (show first 100)
    And I can download full error report as CSV

  @negative
  Scenario: Handle preview for large files
    Given I upload a CSV with 100,000 rows
    When I reach the preview step
    Then only first 100 rows are shown
    And I see "Showing 100 of 100,000 rows"
    And I can paginate through preview data
    And full import only starts when I approve
```

---

## Large Data Operations

```gherkin
Feature: Large Data Operations
  As a platform
  I want to handle large-scale data operations reliably
  So that the system can scale with growing LP databases

  # ==========================================================================
  # Bulk Import of 50,000+ LPs
  # ==========================================================================

  Scenario: Bulk import of 50,000 LPs with progress tracking
    Given I am an admin
    When I upload a CSV file with 50,000 LP records
    Then the file is accepted for background processing
    And I see "Processing 50,000 records in background"
    And progress updates every 5 seconds:
      | Progress | Records | ETA |
      | 10% | 5,000/50,000 | ~8 minutes |
      | 50% | 25,000/50,000 | ~4 minutes |
      | 100% | 50,000/50,000 | Complete |
    And I receive email notification on completion

  Scenario: Progress persistence across page reloads
    Given I started a bulk import of 50,000 LPs
    And 20,000 have been processed
    When I refresh the browser
    Then I still see the import progress
    And progress shows "20,000/50,000 (40%)"
    And I can continue monitoring

  Scenario: Progress available via API for external monitoring
    Given a bulk import job is running
    When I query the job status API
    Then I receive JSON with:
      | Field | Value |
      | job_id | uuid |
      | status | running |
      | total | 50000 |
      | processed | 25000 |
      | successful | 24800 |
      | failed | 200 |
      | started_at | timestamp |
      | estimated_completion | timestamp |

  Scenario: Bulk import cancellation
    Given I started a bulk import of 50,000 LPs
    And 15,000 have been processed
    When I click "Cancel Import"
    Then I see confirmation "Cancel import? 15,000 records already imported will remain."
    When I confirm cancellation
    Then the import job stops within 10 seconds
    And I see "Import cancelled. 15,000 of 50,000 records imported."
    And already-imported records are kept in database
    And I can export a list of unprocessed records

  Scenario: Bulk import cancellation and restart
    Given I cancelled an import at 15,000/50,000 records
    When I upload the same file again
    Then I see "Detected previously cancelled import"
    And I can choose to:
      | Option | Description |
      | Resume | Continue from record 15,001 |
      | Restart | Start over from beginning |
      | Skip imported | Import only records not yet in database |

  Scenario: Bulk import with partial success
    Given I am importing 50,000 LPs
    And 500 records have validation errors
    When the import completes
    Then I see "49,500 records imported successfully, 500 failed"
    And I can download error report with failed records
    And error report includes:
      | Row | Error | Original Data |
      | 1542 | Invalid LP type | ... |
      | 3201 | Missing name | ... |

  # ==========================================================================
  # Concurrent Edit Conflict Detection at Scale
  # ==========================================================================

  Scenario: Concurrent edits from 100 users on different LPs
    Given 100 users are editing different LPs simultaneously
    When all users save their changes within 1 minute
    Then all edits are saved successfully
    And no data corruption occurs
    And database handles concurrent writes efficiently

  Scenario: Concurrent edits on same LP by multiple users
    Given 10 users are editing the same LP "CalPERS"
    When all users try to save within 5 seconds
    Then the first user's save succeeds
    And remaining 9 users see "This record was modified by another user"
    And conflict resolution options are shown:
      | Option |
      | View changes and merge |
      | Overwrite with my changes |
      | Discard my changes |

  Scenario: Optimistic locking with version numbers at scale
    Given LP "CalPERS" is at version 42
    And 50 concurrent requests try to update it
    When all requests are processed
    Then exactly 1 request succeeds (becomes version 43)
    And 49 requests fail with version conflict
    And all failed requests receive consistent error message
    And database version is exactly 43

  Scenario: Concurrent import and manual edit conflict
    Given admin A is bulk importing LPs
    And admin B is manually editing LP "Yale Endowment"
    When import tries to update "Yale Endowment" while B is editing
    Then import marks that record for review
    And B's manual edit is prioritized
    And admin is notified of import conflict

  Scenario: Lock escalation prevention under high concurrency
    Given 500 concurrent database transactions
    When operations are executing
    Then row-level locking is used (not table-level)
    And no deadlocks occur
    And operations complete within acceptable time
    And monitoring tracks lock wait times

  # ==========================================================================
  # Database Performance with 100k+ Records
  # ==========================================================================

  Scenario: LP listing performance with 100,000 records
    Given the database contains 100,000 LP records
    When I load the LP listing page
    Then the first page loads in under 1 second
    And pagination is server-side
    And I see "Showing 1-50 of 100,000 LPs"

  Scenario: LP search performance with 100,000 records
    Given the database contains 100,000 LP records
    When I search for "pension" in LP names
    Then results return in under 500ms
    And results are properly indexed
    And search uses database full-text index

  Scenario: LP filtering performance with 100,000 records
    Given the database contains 100,000 LP records
    When I filter by:
      | Filter | Value |
      | Type | Public Pension |
      | Geography | North America |
      | AUM | > $10B |
    Then results return in under 500ms
    And query uses appropriate indexes
    And filter counts are calculated efficiently

  Scenario: Aggregation queries on 100,000 records
    Given the database contains 100,000 LP records
    When I view dashboard with aggregate statistics:
      | Metric |
      | Total LPs by type |
      | Average AUM by region |
      | Data quality distribution |
    Then all aggregations complete in under 2 seconds
    And results are cached for 5 minutes

  Scenario: Export all 100,000 LPs to CSV
    Given the database contains 100,000 LP records
    When I click "Export All LPs"
    Then export runs in background
    And I see "Generating export file..."
    And I receive download link within 5 minutes
    And exported file is properly formatted

  Scenario: Database vacuum and performance maintenance
    Given the database has 100,000 LPs with frequent updates
    When auto-vacuum runs
    Then table bloat is managed
    And query performance remains stable
    And no visible impact to users during maintenance

  Scenario: Index performance with 100,000 records
    Given the database contains 100,000 LP records
    When I query by various indexed fields:
      | Query Type | Expected Time |
      | By ID (primary key) | < 10ms |
      | By name (text index) | < 100ms |
      | By type (enum index) | < 50ms |
      | By created_at (date range) | < 100ms |
    Then all queries meet performance targets
    And index usage is verified in query plans

  Scenario: Memory usage with large result sets
    Given the database contains 100,000 LP records
    When a query returns 10,000 records
    Then results are streamed, not loaded entirely into memory
    And server memory usage remains stable
    And client receives data progressively

  Scenario: Database connection pool under load
    Given 200 concurrent users are accessing LP data
    When all make database queries
    Then connection pool manages connections efficiently
    And no "too many connections" errors occur
    And query wait times remain under 100ms

  Scenario: Stress test with sustained high load
    Given 100 users performing continuous operations
    When load is sustained for 1 hour:
      | Operation | Frequency |
      | LP list/search | 10 req/sec |
      | LP view | 5 req/sec |
      | LP edit | 1 req/sec |
    Then system remains responsive throughout
    And error rate stays below 0.1%
    And p99 latency stays under 2 seconds
```
