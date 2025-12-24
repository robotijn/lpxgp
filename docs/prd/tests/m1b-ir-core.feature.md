# M1b: IR Core - Test Specifications

**Milestone:** M1b - IR Team Core
**Focus:** Contact lookup, event management, touchpoint logging, task management

---

## Feature: Contact Quick Lookup

### F-IR-01: Contact Search

```gherkin
Feature: Contact Quick Lookup
  As an IR team member
  I want to quickly search for any contact
  So that I'm prepared for conversations

  Background:
    Given I am logged in as an IR team member
    And the system has contacts in the database

  Scenario: Search contact by name
    When I enter "John Smith" in the search bar
    And I click search
    Then I see matching contacts within 1 second
    And results show name, title, and organization

  Scenario: Search contact by organization
    When I enter "CalPERS" in the search bar
    Then I see all contacts at CalPERS
    And results are sorted by relevance

  Scenario: Search with partial match
    When I enter "Joh" in the search bar
    Then I see contacts starting with "Joh"
    And I see "John Smith" in results

  Scenario: Search returns no results
    When I enter "xyznonexistent123"
    Then I see "No contacts found"
    And I see suggestion to refine search

  Scenario: Mobile-friendly profile card
    Given I am on a mobile device
    When I tap on a contact in search results
    Then I see a mobile-optimized profile card
    And key information is visible without scrolling
```

---

## Feature: Event Management

### F-IR-02: Event CRUD

```gherkin
Feature: Event Management
  As an IR team member
  I want to create and manage events
  So that I can track conferences, dinners, and meetings

  Background:
    Given I am logged in as an IR team member

  Scenario: Create new event
    When I click "New Event"
    And I enter name "SuperReturn 2025"
    And I select type "Conference"
    And I enter start date "2025-06-15"
    And I enter end date "2025-06-18"
    And I enter city "Berlin"
    And I click "Create"
    Then I see "Event created successfully"
    And the event appears in my event list

  Scenario: Edit existing event
    Given I have an event "Q1 LP Summit"
    When I click edit on "Q1 LP Summit"
    And I change the city to "New York"
    And I click "Save"
    Then I see "Event updated"
    And the city shows "New York"

  Scenario: Delete event
    Given I have an event "Cancelled Meeting"
    When I click delete on "Cancelled Meeting"
    And I confirm deletion
    Then the event is removed from my list
    And associated attendance records are removed

  Scenario: View upcoming events
    Given I have multiple events
    When I view the event list
    Then events are sorted by start date
    And past events are marked as "Completed"
    And I can filter by status
```

### F-IR-03: Attendee Management

```gherkin
Feature: Attendee Management
  As an IR team member
  I want to manage event attendees
  So that I know who to meet at events

  Background:
    Given I am logged in as an IR team member
    And I have an event "SuperReturn 2025"

  Scenario: Add attendee to event
    When I open "SuperReturn 2025"
    And I click "Add Attendee"
    And I search for "John Smith"
    And I select "John Smith - CalPERS"
    And I set priority to "Must Meet"
    And I click "Add"
    Then John Smith appears in the attendee list
    And priority badge shows "Must Meet"

  Scenario: Remove attendee from event
    Given "John Smith" is an attendee
    When I click remove on "John Smith"
    And I confirm removal
    Then John Smith is removed from attendee list

  Scenario: Update attendee priority
    Given "John Smith" is an attendee with priority "Should Meet"
    When I change priority to "Must Meet"
    Then the priority badge updates immediately

  Scenario: View attendee list with filters
    Given the event has 50 attendees
    When I filter by priority "Must Meet"
    Then I see only "Must Meet" attendees
    And attendee count shows filtered total
```

---

## Feature: Touchpoint Logging

### F-IR-04: Log Interactions

```gherkin
Feature: Touchpoint Logging
  As an IR team member
  I want to log interactions with contacts
  So that the team knows what was discussed

  Background:
    Given I am logged in as an IR team member
    And I have a contact "John Smith"

  Scenario: Log meeting touchpoint
    When I open John Smith's profile
    And I click "Log Touchpoint"
    And I select type "Meeting"
    And I enter date "2025-01-15"
    And I enter summary "Discussed Q1 allocation plans"
    And I select sentiment "Positive"
    And I click "Save"
    Then the touchpoint appears in John's timeline
    And the timestamp shows "2025-01-15"

  Scenario: Log touchpoint with follow-up
    When I log a touchpoint
    And I check "Follow-up required"
    And I click "Save"
    Then I am prompted to create a task
    And the touchpoint is linked to the task

  Scenario: Log touchpoint from event
    Given I am viewing event "SuperReturn 2025"
    And "John Smith" is an attendee
    When I click "Log Interaction" on John Smith
    Then the event is pre-filled
    And I can add meeting notes

  Scenario: View touchpoint timeline
    Given John Smith has 10 touchpoints
    When I view John's profile
    Then I see touchpoints in reverse chronological order
    And each shows type, date, and summary
    And I can expand to see full details

  Scenario: Edit touchpoint
    Given I logged a touchpoint yesterday
    When I click edit on the touchpoint
    And I update the summary
    And I click "Save"
    Then the touchpoint is updated
    And "Edited" indicator appears
```

---

## Feature: Task Management

### F-IR-05: Task CRUD

```gherkin
Feature: Task Management
  As an IR team member
  I want to create and manage follow-up tasks
  So that nothing falls through the cracks

  Background:
    Given I am logged in as an IR team member

  Scenario: Create task from touchpoint
    Given I just logged a touchpoint with "Follow-up required"
    When I click "Create Task"
    And I enter title "Send materials to John"
    And I set due date to "2025-01-20"
    And I assign to myself
    And I click "Create"
    Then the task appears in my task list
    And it's linked to the touchpoint

  Scenario: Create standalone task
    When I click "New Task"
    And I enter title "Prepare Q1 report"
    And I set due date to "2025-01-31"
    And I click "Create"
    Then the task appears in my task list

  Scenario: Mark task complete
    Given I have a task "Send materials"
    When I click the checkbox on "Send materials"
    Then the task is marked complete
    And completion timestamp is recorded
    And task moves to "Completed" section

  Scenario: View overdue tasks
    Given I have tasks with past due dates
    When I view my task list
    Then overdue tasks are highlighted in red
    And I can filter to show only overdue

  Scenario: Assign task to team member
    Given I am a team manager
    When I create a task
    And I assign it to "Sarah Johnson"
    Then Sarah sees the task in her list
    And I can track Sarah's task completion
```

---

## Feature: IR Dashboard

### F-IR-06: Dashboard Overview

```gherkin
Feature: IR Dashboard
  As an IR team member
  I want a dashboard showing my priorities
  So that I can focus on what matters today

  Background:
    Given I am logged in as an IR team member

  Scenario: View today's tasks
    Given I have 5 tasks due today
    When I view the IR dashboard
    Then I see "Today's Tasks" section
    And it shows 5 tasks with due dates

  Scenario: View upcoming events
    Given I have 3 events in the next 30 days
    When I view the dashboard
    Then I see "Upcoming Events" section
    And events are sorted by date
    And each shows attendee count

  Scenario: View recent touchpoints
    Given the team logged 10 touchpoints this week
    When I view the dashboard
    Then I see "Recent Activity" section
    And it shows the 10 most recent touchpoints
    And I can click to see details

  Scenario: Quick search from dashboard
    When I type in the dashboard search bar
    Then I see instant search results
    And I can click to open contact profile

  Scenario: Dashboard loads quickly
    When I navigate to the IR dashboard
    Then the page loads in under 2 seconds
    And all sections are visible
```

---

## Non-Functional Requirements

### Performance

```gherkin
Scenario: Contact search performance
  Given the database has 50,000 contacts
  When I search for "John"
  Then results appear in under 1 second

Scenario: Mobile profile card load time
  Given I am on a mobile device with 3G connection
  When I tap on a contact
  Then the profile card loads in under 2 seconds

Scenario: Event attendee list performance
  Given an event has 500 attendees
  When I view the attendee list
  Then the list loads in under 1 second
  And scrolling is smooth
```

### Security

```gherkin
Scenario: IR users only see their organization's data
  Given I am logged in as IR at "Acme Capital"
  When I search for contacts
  Then I see contacts from my organization
  And I see LP contacts (public database)
  And I do not see other GP organization's private contacts

Scenario: Touchpoints are organization-scoped
  Given "Acme Capital" logged a touchpoint with John Smith
  And "Beta Partners" also uses the platform
  When Beta Partners views John Smith's profile
  Then they do not see Acme's touchpoint
  And they see only their own touchpoints

Scenario: Tasks cannot be assigned cross-organization
  Given I am at "Acme Capital"
  When I try to assign a task to a user at "Beta Partners"
  Then I see an error "Cannot assign to users outside your organization"
```

---

## Exit Criteria Verification

```gherkin
Feature: M1b Exit Criteria

  Scenario: All exit criteria met
    Then IR user can search contacts (people + organizations)
    And IR user can view profile card on mobile
    And IR user can create events and manage attendees
    And IR user can log touchpoints with notes
    And IR user can create and complete tasks
    And IR dashboard shows today's priorities
    And all features are live on lpxgp.com
```
