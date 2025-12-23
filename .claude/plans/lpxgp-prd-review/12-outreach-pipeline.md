## 12. Outreach Pipeline Tracking & Integrations

### Current State
- Basic `pipeline_stage` enum: recommended, gp_interested, gp_pursuing, etc.
- Shortlist UI has simple tabs: To Contact, Contacted, Meeting Set
- No email integration
- No CRM sync

### Proposed: Full Outreach Pipeline

#### Pipeline Stages (Fundraising-specific)

```sql
CREATE TYPE outreach_stage AS ENUM (
    -- Pre-outreach
    'identified',           -- System recommended, not reviewed
    'shortlisted',          -- GP added to shortlist
    'researching',          -- GP doing background research

    -- Initial contact
    'intro_pending',        -- Waiting for warm intro
    'intro_requested',      -- Asked intermediary for intro
    'intro_made',           -- Intro completed, ball in LP's court
    'cold_outreach_sent',   -- Direct email sent (no intro)

    -- Response tracking
    'awaiting_response',    -- Waiting for LP reply
    'follow_up_1',          -- First follow-up sent
    'follow_up_2',          -- Second follow-up sent
    'follow_up_3',          -- Third follow-up (last attempt)

    -- LP engagement
    'responded_positive',   -- LP replied with interest
    'responded_questions',  -- LP has questions
    'responded_later',      -- "Not now, try later"
    'responded_negative',   -- Declined

    -- Meeting stages
    'call_scheduled',       -- Intro call scheduled
    'call_completed',       -- Had intro call
    'meeting_requested',    -- Requested in-person/formal meeting
    'meeting_scheduled',    -- Meeting on calendar
    'meeting_completed',    -- Had meeting

    -- Due diligence
    'dd_materials_sent',    -- Sent DDQ, data room access
    'dd_in_progress',       -- LP reviewing materials
    'dd_questions',         -- LP has DD questions
    'reference_calls',      -- LP doing reference checks
    'ic_presentation',      -- Presenting to Investment Committee

    -- Final stages
    'term_sheet_sent',      -- Sent terms
    'negotiating',          -- Negotiating terms
    'verbal_commit',        -- Verbal commitment
    'docs_in_progress',     -- Legal docs being prepared
    'committed',            -- Signed commitment

    -- Closed - unsuccessful
    'passed_by_gp',         -- GP decided not to pursue
    'passed_by_lp',         -- LP declined
    'stalled',              -- No progress, unclear status
    'lost_to_competitor'    -- LP committed to competing fund
);
```

#### Data Model

```sql
-- Enhanced outreach tracking
CREATE TABLE outreach_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fund_id UUID NOT NULL REFERENCES client_funds(id),
    lp_id UUID NOT NULL REFERENCES companies(id),

    -- Current status
    stage outreach_stage NOT NULL DEFAULT 'identified',
    sub_status TEXT,  -- Freeform for nuance

    -- Contact tracking
    primary_contact_id UUID REFERENCES people(id),
    last_contact_date TIMESTAMP,
    next_action_date TIMESTAMP,
    next_action_description TEXT,

    -- Ownership
    assigned_to UUID REFERENCES users(id),

    -- Source tracking
    created_via TEXT,  -- 'manual', 'email_sync', 'crm_sync'
    external_id TEXT,  -- CRM record ID

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Activity history (every status change, email, call, etc.)
CREATE TABLE outreach_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    outreach_id UUID NOT NULL REFERENCES outreach_activities(id),

    -- What happened
    activity_type TEXT NOT NULL,  -- 'stage_change', 'email_sent', 'email_received', 'call', 'meeting', 'note'
    old_stage outreach_stage,
    new_stage outreach_stage,

    -- Details
    subject TEXT,
    body TEXT,
    notes TEXT,

    -- Participants
    contact_id UUID REFERENCES people(id),
    performed_by UUID REFERENCES users(id),

    -- Email-specific
    email_message_id TEXT,  -- For deduplication
    email_thread_id TEXT,
    direction TEXT,  -- 'inbound', 'outbound'

    -- Scheduling
    scheduled_at TIMESTAMP,  -- For meetings/calls

    -- Source
    source TEXT,  -- 'manual', 'email_sync', 'crm_sync', 'calendar_sync'

    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_outreach_fund ON outreach_activities(fund_id);
CREATE INDEX idx_outreach_lp ON outreach_activities(lp_id);
CREATE INDEX idx_outreach_stage ON outreach_activities(stage);
CREATE INDEX idx_outreach_next_action ON outreach_activities(next_action_date);
CREATE INDEX idx_history_outreach ON outreach_history(outreach_id);
CREATE INDEX idx_history_email ON outreach_history(email_message_id);
```

### Email Integration

#### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     EMAIL INTEGRATION                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │ GP's Email Box   │───▶│ Email Sync       │                   │
│  │ (Gmail/Outlook)  │    │ Service          │                   │
│  └──────────────────┘    └────────┬─────────┘                   │
│                                   │                              │
│                    ┌──────────────┴──────────────┐              │
│                    ▼                             ▼               │
│  ┌──────────────────────┐    ┌──────────────────────┐          │
│  │ Email Parser         │    │ Contact Matcher      │          │
│  │ - Extract subject    │    │ - Match to LP        │          │
│  │ - Extract body       │    │ - Match to contact   │          │
│  │ - Detect direction   │    │ - Create if new      │          │
│  └──────────────────────┘    └──────────────────────┘          │
│                    │                             │               │
│                    └──────────────┬──────────────┘              │
│                                   ▼                              │
│                    ┌──────────────────────────┐                 │
│                    │ Stage Inference Engine   │                 │
│                    │ - Analyze email content  │                 │
│                    │ - Suggest stage change   │                 │
│                    │ - Auto-update or suggest │                 │
│                    └──────────────────────────┘                 │
│                                   │                              │
│                                   ▼                              │
│                    ┌──────────────────────────┐                 │
│                    │ outreach_history         │                 │
│                    │ (email logged)           │                 │
│                    └──────────────────────────┘                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Email Provider Support

**Phase 1: OAuth-based (recommended)**
- Gmail via Gmail API (OAuth 2.0)
- Microsoft 365 via Microsoft Graph API (OAuth 2.0)

**Phase 2: IMAP (for self-hosted)**
- Any IMAP-compatible email server
- Requires app password or OAuth

#### Email Sync Implementation

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

class EmailSyncService:
    """Sync emails from connected mailbox."""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.credentials = self._load_credentials(user_id)

    async def sync_emails(self, since: datetime = None):
        """Fetch new emails and match to outreach records."""

        # Get emails since last sync
        emails = await self._fetch_emails(since)

        for email in emails:
            # Extract LP contact from email
            contact = await self._match_contact(email)

            if not contact:
                continue  # Not a known LP contact

            # Find or create outreach record
            outreach = await self._find_outreach(contact)

            # Log email to history
            await self._log_email(outreach, email)

            # Infer stage change
            suggested_stage = await self._infer_stage(email, outreach)

            if suggested_stage != outreach.stage:
                # Auto-update or create suggestion for user
                await self._handle_stage_suggestion(outreach, suggested_stage)

    async def _match_contact(self, email: Email) -> Contact | None:
        """Match email sender/recipient to known LP contact."""

        # Check From/To/Cc for known LP emails
        addresses = email.from_addresses + email.to_addresses + email.cc_addresses

        for addr in addresses:
            contact = await db.query_one("""
                SELECT p.*, cp.company_id
                FROM people p
                JOIN company_people cp ON p.id = cp.person_id
                JOIN companies c ON cp.company_id = c.id
                WHERE p.email = $1
                AND c.type IN ('lp', 'both')
            """, addr)

            if contact:
                return contact

        return None

    async def _infer_stage(self, email: Email, outreach: Outreach) -> str:
        """Use LLM to infer stage from email content."""

        prompt = f"""
        Analyze this email in the context of LP fundraising outreach.

        Current stage: {outreach.stage}
        Email direction: {email.direction}
        Subject: {email.subject}
        Body (first 500 chars): {email.body[:500]}

        What outreach stage does this email indicate?
        Options: {', '.join(OUTREACH_STAGES)}

        Respond with just the stage name.
        """

        response = await llm.complete(prompt)
        return response.strip()
```

#### Auto-Stage Inference Rules

| Email Pattern | Inferred Stage |
|---------------|----------------|
| Outbound to LP (first) | `cold_outreach_sent` or `intro_made` |
| Inbound from LP (first reply) | `responded_positive` or `responded_questions` |
| Contains "schedule", "calendar" | `call_scheduled` |
| Contains "not interested", "pass" | `responded_negative` |
| Contains "data room", "DDQ" | `dd_materials_sent` |
| Contains "IC", "committee" | `ic_presentation` |
| Contains "commitment", "commit" | `verbal_commit` |

### CRM Integrations

#### HubSpot Integration

```python
import hubspot
from hubspot.crm.deals import Deal

class HubSpotSync:
    """Bidirectional sync with HubSpot CRM."""

    def __init__(self, api_key: str):
        self.client = hubspot.Client.create(access_token=api_key)

    async def sync_to_hubspot(self, outreach: Outreach):
        """Push outreach status to HubSpot deal."""

        # Map LPxGP stage to HubSpot pipeline stage
        hubspot_stage = self._map_stage_to_hubspot(outreach.stage)

        deal = Deal(
            properties={
                "dealname": f"{outreach.fund.name} - {outreach.lp.name}",
                "dealstage": hubspot_stage,
                "pipeline": "fundraising",
                "amount": outreach.expected_commitment,
                "closedate": outreach.target_close_date,
                # Custom properties
                "lpxgp_id": str(outreach.id),
                "lpxgp_match_score": outreach.match_score,
            }
        )

        if outreach.external_id:
            # Update existing
            await self.client.crm.deals.basic_api.update(
                outreach.external_id, deal
            )
        else:
            # Create new
            result = await self.client.crm.deals.basic_api.create(deal)
            outreach.external_id = result.id

    async def sync_from_hubspot(self, deal_id: str):
        """Pull updates from HubSpot deal."""

        deal = await self.client.crm.deals.basic_api.get_by_id(deal_id)

        # Find matching outreach
        outreach = await db.query_one(
            "SELECT * FROM outreach_activities WHERE external_id = $1",
            deal_id
        )

        if not outreach:
            return

        # Map HubSpot stage back to LPxGP
        new_stage = self._map_stage_from_hubspot(deal.properties["dealstage"])

        if new_stage != outreach.stage:
            await self._update_stage(outreach, new_stage, source='crm_sync')

    def _map_stage_to_hubspot(self, lpxgp_stage: str) -> str:
        """Map LPxGP stage to HubSpot deal stage."""
        return {
            'identified': 'qualifiedtobuy',
            'shortlisted': 'qualifiedtobuy',
            'cold_outreach_sent': 'presentationscheduled',
            'call_scheduled': 'presentationscheduled',
            'meeting_completed': 'decisionmakerboughtin',
            'dd_in_progress': 'contractsent',
            'committed': 'closedwon',
            'passed_by_lp': 'closedlost',
        }.get(lpxgp_stage, 'qualifiedtobuy')
```

#### Salesforce Integration

```python
from simple_salesforce import Salesforce

class SalesforceSync:
    """Bidirectional sync with Salesforce CRM."""

    def __init__(self, instance_url: str, access_token: str):
        self.sf = Salesforce(instance_url=instance_url, session_id=access_token)

    async def sync_to_salesforce(self, outreach: Outreach):
        """Push outreach to Salesforce Opportunity."""

        sf_stage = self._map_stage_to_salesforce(outreach.stage)

        opportunity = {
            "Name": f"{outreach.fund.name} - {outreach.lp.name}",
            "StageName": sf_stage,
            "Amount": outreach.expected_commitment,
            "CloseDate": outreach.target_close_date.isoformat(),
            "LPxGP_ID__c": str(outreach.id),  # Custom field
            "Match_Score__c": outreach.match_score,  # Custom field
        }

        if outreach.external_id:
            self.sf.Opportunity.update(outreach.external_id, opportunity)
        else:
            result = self.sf.Opportunity.create(opportunity)
            outreach.external_id = result["id"]

    async def sync_from_salesforce(self, opportunity_id: str):
        """Pull updates from Salesforce."""

        opp = self.sf.Opportunity.get(opportunity_id)

        outreach = await db.query_one(
            "SELECT * FROM outreach_activities WHERE external_id = $1",
            opportunity_id
        )

        if outreach:
            new_stage = self._map_stage_from_salesforce(opp["StageName"])
            await self._update_stage(outreach, new_stage, source='crm_sync')
```

### UI Updates for Shortlist Page

#### Enhanced Pipeline View

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Shortlist - Growth Fund III                                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ Pipeline View | List View | Calendar View                               │
│                                                                          │
│ ┌─────────┬─────────┬─────────┬─────────┬─────────┬─────────┬─────────┐ │
│ │Research │Outreach │Response │ Calls   │ DD      │ Closing │Committed│ │
│ │    (5)  │   (12)  │   (8)   │   (4)   │   (3)   │   (1)   │   (2)   │ │
│ ├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤ │
│ │ ░░░░░░░ │ ░░░░░░░ │ ░░░░░░░ │ ░░░░░░░ │ ░░░░░░░ │ ░░░░░░░ │ ░░░░░░░ │ │
│ │         │         │         │         │         │         │         │ │
│ │CalPERS  │Yale     │Ontario  │Harvard  │Texas    │Stanford │MIT      │ │
│ │92 score │88 score │79 score │85 score │76 score │81 score │90 score │ │
│ │         │         │         │         │         │         │         │ │
│ │PGGM     │...      │...      │...      │...      │         │CalSTRS  │ │
│ │87 score │         │         │         │         │         │88 score │ │
│ └─────────┴─────────┴─────────┴─────────┴─────────┴─────────┴─────────┘ │
│                                                                          │
│ Drag cards between columns to update stage                              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

#### LP Card with Activity Timeline

```
┌─────────────────────────────────────────────────────────────────┐
│ CalPERS                                           Score: 92     │
│ $450B AUM · Pension                                             │
├─────────────────────────────────────────────────────────────────┤
│ Stage: Call Scheduled                                           │
│ Next: Intro call Jan 15, 2pm                                    │
│ Contact: Sarah Chen (CIO)                                       │
├─────────────────────────────────────────────────────────────────┤
│ Recent Activity:                                                │
│ • Jan 10 - Email received: "Looking forward to our call"        │
│ • Jan 8 - Call scheduled via Calendly                           │
│ • Jan 5 - Intro email sent via mutual connection                │
│ • Jan 3 - Added to shortlist                                    │
├─────────────────────────────────────────────────────────────────┤
│ [Log Activity] [Send Email] [Schedule Call] [View Profile]      │
└─────────────────────────────────────────────────────────────────┘
```

### Integration Settings UI

```
┌─────────────────────────────────────────────────────────────────┐
│ Settings > Integrations                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ EMAIL SYNC                                                       │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ● Gmail Connected (john@acmecapital.com)                    │ │
│ │   Last sync: 5 minutes ago                                  │ │
│ │   [Disconnect] [Sync Now]                                   │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ [ ] Auto-update stages based on email content                    │
│ [ ] Create contacts from unknown senders                         │
│ [x] Log all LP-related emails to timeline                        │
│                                                                  │
│ CRM SYNC                                                         │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ○ HubSpot    [Connect]                                      │ │
│ │ ○ Salesforce [Connect]                                      │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ Sync direction:                                                  │
│ (●) LPxGP → CRM (push only)                                     │
│ ( ) CRM → LPxGP (pull only)                                     │
│ ( ) Bidirectional (two-way sync)                                │
│                                                                  │
│ Stage mapping: [Configure]                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation Phases

**Phase 1: Enhanced Pipeline (M4)**
- Add `outreach_stage` enum with full stages
- Add `outreach_activities` and `outreach_history` tables
- Update shortlist UI with pipeline view
- Manual stage updates with activity logging

**Phase 2: Email Integration (M5)**
- Gmail OAuth integration
- Email parsing and contact matching
- Auto-log emails to timeline
- Stage inference (suggest, not auto-update)

**Phase 3: CRM Integrations (M6)**
- HubSpot integration (most common for VCs)
- Salesforce integration
- Bidirectional sync
- Custom field mapping

---

