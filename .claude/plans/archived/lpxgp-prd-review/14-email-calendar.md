## 14. Email Analysis for AI Learning & Calendar Integration

### Overview

Three new capabilities to enhance outreach effectiveness:
1. **Email analysis for AI** - Store and analyze email content for AI recommendations
2. **User preferences** - Control what gets auto-updated vs requires confirmation
3. **Calendar integration** - Connect calendars and offer automated scheduling links

---

### 14.1 Email Content Storage for AI Learning

#### Problem
Currently, email sync only tracks stage changes. The actual content of LP conversations is valuable for:
- Understanding LP preferences and objections
- Improving pitch generation
- Training personalization models
- Predicting success likelihood

#### Data Model

```sql
-- Store email content for AI analysis
CREATE TABLE email_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    outreach_id UUID NOT NULL REFERENCES outreach_activities(id),

    -- Email metadata
    message_id TEXT UNIQUE,  -- For deduplication
    thread_id TEXT,  -- Group conversations
    direction TEXT NOT NULL,  -- 'inbound' | 'outbound'

    -- Participants
    from_email TEXT NOT NULL,
    from_name TEXT,
    to_emails TEXT[] NOT NULL,
    cc_emails TEXT[],

    -- Content (for AI)
    subject TEXT,
    body_text TEXT,  -- Plain text version
    body_html TEXT,  -- Original HTML (optional)

    -- AI-extracted insights (populated async)
    sentiment TEXT,  -- 'positive' | 'neutral' | 'negative'
    key_topics TEXT[],  -- ['terms', 'timeline', 'team']
    objections_raised TEXT[],  -- ['fund_size_too_small', 'no_track_record']
    questions_asked TEXT[],  -- Questions LP asked
    commitments_made TEXT[],  -- Promises either party made
    next_steps_mentioned TEXT[],  -- Action items mentioned
    ai_summary TEXT,  -- 2-3 sentence summary

    -- Metadata
    sent_at TIMESTAMP NOT NULL,
    received_at TIMESTAMP,
    analyzed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for AI queries
CREATE INDEX idx_email_conversations_outreach ON email_conversations(outreach_id);
CREATE INDEX idx_email_conversations_thread ON email_conversations(thread_id);
CREATE INDEX idx_email_conversations_sentiment ON email_conversations(sentiment);
CREATE INDEX idx_email_conversations_topics ON email_conversations USING GIN(key_topics);

-- Aggregate LP communication patterns
CREATE TABLE lp_communication_profile (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lp_id UUID NOT NULL REFERENCES companies(id),

    -- Aggregated from all email conversations
    avg_response_time_hours NUMERIC,
    preferred_communication_style TEXT,  -- 'formal' | 'casual' | 'technical'
    common_objections TEXT[],
    decision_factors TEXT[],  -- What seems to matter to this LP

    -- Patterns
    typical_questions TEXT[],
    engagement_level TEXT,  -- 'high' | 'medium' | 'low'

    -- Timing
    best_contact_days TEXT[],  -- ['tuesday', 'wednesday']
    best_contact_hours TEXT,  -- '9am-11am'

    last_updated TIMESTAMP DEFAULT NOW(),

    UNIQUE(lp_id)
);
```

#### Email Analysis Pipeline

```python
class EmailAnalyzer:
    """Analyze email content for AI learning."""

    async def analyze_email(self, email: EmailConversation) -> dict:
        """Extract structured insights from email content."""

        prompt = f"""
        Analyze this fundraising email conversation.

        Direction: {email.direction}
        Subject: {email.subject}
        Body:
        {email.body_text}

        Extract:
        1. Overall sentiment (positive/neutral/negative)
        2. Key topics discussed (list)
        3. Any objections or concerns raised (list)
        4. Questions asked (list)
        5. Commitments or promises made (list)
        6. Next steps mentioned (list)
        7. 2-3 sentence summary

        Return as JSON:
        {{
            "sentiment": "...",
            "key_topics": [...],
            "objections_raised": [...],
            "questions_asked": [...],
            "commitments_made": [...],
            "next_steps_mentioned": [...],
            "summary": "..."
        }}
        """

        response = await llm.complete(prompt, response_format="json")
        return json.loads(response)

    async def update_lp_profile(self, lp_id: UUID):
        """Update LP communication profile from all emails."""

        emails = await db.query("""
            SELECT ec.*
            FROM email_conversations ec
            JOIN outreach_activities oa ON ec.outreach_id = oa.id
            WHERE oa.lp_id = $1
            ORDER BY ec.sent_at
        """, lp_id)

        if len(emails) < 3:
            return  # Not enough data

        # Calculate patterns
        response_times = self._calculate_response_times(emails)
        common_objections = self._aggregate_field(emails, 'objections_raised')
        decision_factors = self._extract_decision_factors(emails)

        await db.execute("""
            INSERT INTO lp_communication_profile
            (lp_id, avg_response_time_hours, common_objections, decision_factors)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (lp_id) DO UPDATE SET
                avg_response_time_hours = $2,
                common_objections = $3,
                decision_factors = $4,
                last_updated = NOW()
        """, lp_id, response_times, common_objections, decision_factors)
```

#### AI Agent Integration

The email insights feed into the agent debates:

```python
# In Pitch Generation debate
class PitchGenerator:
    async def generate(self, match: Match) -> str:
        # Get LP communication profile
        lp_profile = await get_lp_communication_profile(match.lp_id)

        # Get recent email context
        recent_emails = await get_recent_emails(match.outreach_id, limit=5)

        prompt = f"""
        Generate a pitch for {match.lp_name}.

        ## LP Communication Style
        - Preferred style: {lp_profile.preferred_communication_style}
        - Common objections they raise: {lp_profile.common_objections}
        - Decision factors that matter to them: {lp_profile.decision_factors}

        ## Recent Conversation Context
        {format_email_summaries(recent_emails)}

        ## Generate
        A personalized pitch that:
        1. Matches their communication style
        2. Proactively addresses their typical objections
        3. Emphasizes factors they care about
        """

        return await llm.complete(prompt)

# In Objection Handling debate
class ObjectionAnticipator:
    async def anticipate(self, match: Match) -> list:
        # LP-specific objection history
        lp_profile = await get_lp_communication_profile(match.lp_id)

        # Weight objections based on what this LP actually asked before
        if lp_profile and lp_profile.common_objections:
            return self._prioritize_objections(
                generic_objections=self.get_generic_objections(match),
                lp_specific=lp_profile.common_objections
            )
```

---

### 14.2 User Preferences for Update Behavior

#### Problem
Different users want different levels of automation:
- Some want everything auto-updated
- Some want to review every change
- Some want a middle ground

#### Data Model

```sql
-- User notification and automation preferences
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),

    -- Email sync behavior
    email_sync_mode TEXT DEFAULT 'log_only',
    -- Options:
    -- 'disabled': Don't sync emails
    -- 'log_only': Log emails but don't update stages
    -- 'suggest': Log and suggest stage changes (need confirmation)
    -- 'auto_update': Automatically update stages

    -- Stage update behavior
    stage_update_confirmation TEXT DEFAULT 'major_only',
    -- Options:
    -- 'always': Confirm every stage change
    -- 'major_only': Confirm major stages (meeting, DD, committed)
    -- 'never': Auto-update all stages

    -- CRM sync behavior
    crm_sync_mode TEXT DEFAULT 'push_only',
    -- Options:
    -- 'disabled': No CRM sync
    -- 'push_only': LPxGP → CRM only
    -- 'pull_only': CRM → LPxGP only
    -- 'bidirectional': Two-way sync

    -- Notification preferences
    notify_new_match BOOLEAN DEFAULT TRUE,
    notify_lp_response BOOLEAN DEFAULT TRUE,
    notify_stage_change BOOLEAN DEFAULT TRUE,
    notify_meeting_reminder BOOLEAN DEFAULT TRUE,

    -- Notification channels
    notification_email BOOLEAN DEFAULT TRUE,
    notification_sms BOOLEAN DEFAULT FALSE,  -- Requires phone
    notification_in_app BOOLEAN DEFAULT TRUE,

    -- AI behavior
    ai_pitch_auto_generate BOOLEAN DEFAULT TRUE,
    ai_email_suggestions BOOLEAN DEFAULT TRUE,
    ai_objection_prep BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id)
);

-- Pending confirmations queue
CREATE TABLE pending_confirmations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),

    -- What needs confirmation
    confirmation_type TEXT NOT NULL,  -- 'stage_change' | 'crm_sync' | 'email_analysis'

    -- Context
    outreach_id UUID REFERENCES outreach_activities(id),

    -- The proposed change
    proposed_change JSONB NOT NULL,
    -- Example: {"old_stage": "outreach", "new_stage": "call_scheduled", "reason": "Email contains 'calendar invite'"}

    -- Status
    status TEXT DEFAULT 'pending',  -- 'pending' | 'approved' | 'rejected' | 'expired'
    responded_at TIMESTAMP,

    -- Expiry
    expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '7 days'),

    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Settings UI

```
┌─────────────────────────────────────────────────────────────────┐
│ Settings > Preferences                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ EMAIL SYNC BEHAVIOR                                              │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ When emails are synced:                                     │ │
│ │                                                             │ │
│ │ ( ) Don't sync emails                                       │ │
│ │ ( ) Log emails only (don't update stages)                   │ │
│ │ (●) Suggest stage changes (I'll confirm)          [Default] │ │
│ │ ( ) Auto-update stages based on email content               │ │
│ │                                                             │ │
│ │ ⓘ "Suggest" mode will show a notification when we think     │ │
│ │   a stage should change. You can approve or dismiss.        │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ STAGE CHANGE CONFIRMATIONS                                       │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Require my confirmation for:                                │ │
│ │                                                             │ │
│ │ ( ) All stage changes                                       │ │
│ │ (●) Major milestones only (meeting, DD, committed)          │ │
│ │ ( ) Never (auto-update everything)                          │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ AI FEATURES                                                      │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ [x] Auto-generate pitch content for new matches             │ │
│ │ [x] Suggest email responses based on LP communication       │ │
│ │ [x] Prepare objection handling based on email history       │ │
│ │ [ ] Auto-schedule follow-ups (coming soon)                  │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ NOTIFICATIONS                                                    │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │                           Email   SMS    In-App             │ │
│ │ New LP match              [x]     [ ]     [x]               │ │
│ │ LP response received      [x]     [x]     [x]               │ │
│ │ Stage change              [x]     [ ]     [x]               │ │
│ │ Meeting reminder          [x]     [x]     [x]               │ │
│ │                                                             │ │
│ │ ⓘ SMS requires verified phone number                        │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│                                        [Cancel]  [Save Changes] │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Confirmation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 🔔 Pending Confirmations (3)                              [x]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Stage Change Suggested                           2 hours ago │ │
│ │                                                              │ │
│ │ CalPERS: Outreach → Call Scheduled                          │ │
│ │                                                              │ │
│ │ Reason: Email received contains "looking forward to our     │ │
│ │ call on Tuesday" and calendar invite detected.              │ │
│ │                                                              │ │
│ │ [View Email]          [Reject]  [Approve]                   │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Stage Change Suggested                           5 hours ago │ │
│ │                                                              │ │
│ │ Yale Endowment: Response → Meeting Scheduled                │ │
│ │                                                              │ │
│ │ Reason: Email mentions "we'd like to schedule a meeting"    │ │
│ │                                                              │ │
│ │ [View Email]          [Reject]  [Approve]                   │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 14.3 Calendar Integration & Automated Scheduling

#### Overview

Two calendar features:
1. **Calendar sync** - See meetings in LPxGP, get reminders
2. **Automated scheduling** - Generate LP-facing booking links

#### Data Model

```sql
-- Connected calendars
CREATE TABLE calendar_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),

    -- Provider
    provider TEXT NOT NULL,  -- 'google' | 'microsoft' | 'apple'

    -- OAuth
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_expires_at TIMESTAMP,

    -- Calendar selection
    calendar_id TEXT NOT NULL,  -- Specific calendar to sync
    calendar_name TEXT,

    -- Sync settings
    sync_enabled BOOLEAN DEFAULT TRUE,
    last_sync_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id, provider, calendar_id)
);

-- Meetings tracked
CREATE TABLE meetings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Link to outreach
    outreach_id UUID REFERENCES outreach_activities(id),

    -- Meeting details
    title TEXT NOT NULL,
    description TEXT,
    location TEXT,  -- Physical address or video link

    -- Timing
    start_at TIMESTAMP NOT NULL,
    end_at TIMESTAMP NOT NULL,
    timezone TEXT DEFAULT 'UTC',

    -- Participants
    organizer_id UUID REFERENCES users(id),
    attendees JSONB,  -- [{"email": "...", "name": "...", "status": "accepted"}]

    -- External IDs
    calendar_event_id TEXT,  -- ID in Google/Microsoft calendar
    video_link TEXT,  -- Zoom/Meet/Teams link

    -- Status
    status TEXT DEFAULT 'scheduled',  -- 'scheduled' | 'completed' | 'cancelled' | 'rescheduled'

    -- Notes (post-meeting)
    meeting_notes TEXT,
    outcome TEXT,  -- 'positive' | 'neutral' | 'negative'
    next_steps TEXT[],

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Scheduling links (Calendly-style)
CREATE TABLE scheduling_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Owner
    user_id UUID NOT NULL REFERENCES users(id),

    -- Link configuration
    slug TEXT UNIQUE NOT NULL,  -- lpxgp.com/schedule/abc123
    title TEXT NOT NULL,  -- "30-min Intro Call with John"
    description TEXT,

    -- Duration options
    duration_minutes INTEGER NOT NULL DEFAULT 30,

    -- Availability (JSON for flexibility)
    availability JSONB NOT NULL,
    -- Example: {
    --   "monday": [{"start": "09:00", "end": "12:00"}, {"start": "14:00", "end": "17:00"}],
    --   "tuesday": [{"start": "09:00", "end": "17:00"}],
    --   ...
    -- }

    -- Booking window
    min_notice_hours INTEGER DEFAULT 24,  -- Can't book less than 24h ahead
    max_future_days INTEGER DEFAULT 60,  -- Can book up to 60 days out

    -- Buffer
    buffer_before_minutes INTEGER DEFAULT 15,
    buffer_after_minutes INTEGER DEFAULT 15,

    -- Video conferencing
    auto_create_video_link BOOLEAN DEFAULT TRUE,
    video_provider TEXT DEFAULT 'google_meet',  -- 'google_meet' | 'zoom' | 'teams'

    -- Customization
    confirmation_message TEXT,
    reminder_hours INTEGER[] DEFAULT '{24, 1}',  -- Send reminders 24h and 1h before

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT NOW()
);

-- Bookings made via scheduling links
CREATE TABLE scheduling_bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Link used
    scheduling_link_id UUID NOT NULL REFERENCES scheduling_links(id),

    -- Who booked
    booker_email TEXT NOT NULL,
    booker_name TEXT,
    booker_company TEXT,

    -- Link to LP if known
    lp_id UUID REFERENCES companies(id),
    outreach_id UUID REFERENCES outreach_activities(id),

    -- Meeting created
    meeting_id UUID REFERENCES meetings(id),

    -- Booking details
    selected_time TIMESTAMP NOT NULL,
    timezone TEXT NOT NULL,

    -- Status
    status TEXT DEFAULT 'confirmed',  -- 'confirmed' | 'cancelled' | 'rescheduled'

    -- Notes from booker
    booker_notes TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Calendar Sync Implementation

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

class GoogleCalendarSync:
    """Sync meetings with Google Calendar."""

    def __init__(self, connection: CalendarConnection):
        self.connection = connection
        self.service = self._build_service()

    def _build_service(self):
        creds = Credentials(
            token=self.connection.access_token,
            refresh_token=self.connection.refresh_token
        )
        return build('calendar', 'v3', credentials=creds)

    async def sync_events(self, since: datetime = None):
        """Pull events from Google Calendar."""

        events = self.service.events().list(
            calendarId=self.connection.calendar_id,
            timeMin=since.isoformat() if since else None,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        for event in events.get('items', []):
            # Check if this is an LP meeting
            lp_match = await self._match_to_lp(event)

            if lp_match:
                await self._upsert_meeting(event, lp_match)

    async def _match_to_lp(self, event: dict) -> dict | None:
        """Try to match calendar event to an LP."""

        attendees = event.get('attendees', [])

        for attendee in attendees:
            email = attendee.get('email')

            # Check if attendee is a known LP contact
            contact = await db.query_one("""
                SELECT p.*, c.id as company_id, c.name as company_name
                FROM people p
                JOIN company_people cp ON p.id = cp.person_id
                JOIN companies c ON cp.company_id = c.id
                WHERE p.email = $1
                AND c.type IN ('lp', 'both')
            """, email)

            if contact:
                return {
                    "lp_id": contact["company_id"],
                    "lp_name": contact["company_name"],
                    "contact_id": contact["id"]
                }

        return None

    async def create_event(self, meeting: Meeting) -> str:
        """Create event in Google Calendar."""

        event = {
            'summary': meeting.title,
            'description': meeting.description,
            'start': {
                'dateTime': meeting.start_at.isoformat(),
                'timeZone': meeting.timezone,
            },
            'end': {
                'dateTime': meeting.end_at.isoformat(),
                'timeZone': meeting.timezone,
            },
            'attendees': [
                {'email': a['email']} for a in meeting.attendees
            ],
            'conferenceData': {
                'createRequest': {'requestId': str(meeting.id)}
            } if meeting.auto_create_video else None
        }

        result = self.service.events().insert(
            calendarId=self.connection.calendar_id,
            body=event,
            conferenceDataVersion=1
        ).execute()

        return result['id']
```

#### Scheduling Link Flow

```
LP receives email with scheduling link:
"Book a time to chat: https://lpxgp.com/schedule/john-acme"
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│           Schedule a Meeting with John Smith                     │
│           Acme Capital Partners                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  30-min Intro Call                                               │
│                                                                  │
│  Select a date:                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │     December 2025                        < >                ││
│  │  Su  Mo  Tu  We  Th  Fr  Sa                                 ││
│  │                   1   2   3   4   5   6                     ││
│  │   7   8   9  10  11  12  13                                 ││
│  │  14  15  16 [17] 18  19  20   ← Available days highlighted  ││
│  │  21  22  23  24  25  26  27                                 ││
│  │  28  29  30  31                                             ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  Available times on Dec 17:                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ 9:00 AM  │ │ 9:30 AM  │ │ 10:00 AM │ │ 10:30 AM │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                        │
│  │ 2:00 PM  │ │ 2:30 PM  │ │ 3:00 PM  │                        │
│  └──────────┘ └──────────┘ └──────────┘                        │
│                                                                  │
│  Timezone: [America/New_York ▼]                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼ (LP selects time)
┌─────────────────────────────────────────────────────────────────┐
│           Confirm Your Booking                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  30-min Intro Call with John Smith                               │
│  Wednesday, December 17, 2025 at 10:00 AM EST                    │
│                                                                  │
│  Your Details:                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Name *         [Sarah Chen________________]                 ││
│  │ Email *        [sarah.chen@calpensions.org]                 ││
│  │ Company        [CalPERS___________________]                 ││
│  │                                                             ││
│  │ Anything you'd like to discuss?                             ││
│  │ [Interested in learning more about Fund III___________]    ││
│  │ [_____________________________________________________]    ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│                                         [Cancel]  [Confirm]     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼ (Booking confirmed)
┌─────────────────────────────────────────────────────────────────┐
│           ✓ Meeting Scheduled!                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Your meeting with John Smith is confirmed.                      │
│                                                                  │
│  📅 Wednesday, December 17, 2025                                 │
│  🕐 10:00 AM - 10:30 AM EST                                      │
│  📍 Google Meet: https://meet.google.com/abc-defg-hij           │
│                                                                  │
│  A calendar invite has been sent to sarah.chen@calpensions.org   │
│                                                                  │
│  [Add to Calendar]  [Reschedule]  [Cancel]                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Schedule Button in LP Card

```
┌─────────────────────────────────────────────────────────────────┐
│ CalPERS                                           Score: 92     │
│ $450B AUM · Pension                                             │
├─────────────────────────────────────────────────────────────────┤
│ Stage: Response Received                                        │
│ Contact: Sarah Chen (CIO)                                       │
├─────────────────────────────────────────────────────────────────┤
│ Recent Activity:                                                │
│ • Dec 10 - Email: "Would love to learn more about Fund III"     │
├─────────────────────────────────────────────────────────────────┤
│ [Log Activity] [Send Email] [📅 Schedule Meeting] [View]        │
│                                   ▲                             │
│                    Generates scheduling link                    │
│                    for this specific LP                         │
└─────────────────────────────────────────────────────────────────┘
```

When GP clicks "Schedule Meeting":

```
┌─────────────────────────────────────────────────────────────────┐
│ Schedule Meeting with CalPERS                              [x]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Meeting Type:                                                    │
│ (●) 30-min Intro Call                                           │
│ ( ) 60-min Deep Dive                                            │
│ ( ) Custom...                                                    │
│                                                                  │
│ Send scheduling link to:                                         │
│ [sarah.chen@calpensions.org_______] ← Auto-filled from contact  │
│                                                                  │
│ Include message:                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Hi Sarah,                                                   │ │
│ │                                                             │ │
│ │ Great to hear from you! I'd love to tell you more about    │ │
│ │ Growth Fund III. Please pick a time that works for you:    │ │
│ │                                                             │ │
│ │ [Scheduling link will be inserted automatically]           │ │
│ │                                                             │ │
│ │ Looking forward to connecting,                              │ │
│ │ John                                                        │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ Preview link: lpxgp.com/schedule/john-acme/calpens-dec2025      │
│               ▲ LP-specific, auto-expires                       │
│                                                                  │
│                              [Cancel]  [Send Scheduling Email]  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Integration Settings for Calendar

```
┌─────────────────────────────────────────────────────────────────┐
│ Settings > Calendar                                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ CONNECTED CALENDARS                                              │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ● Google Calendar Connected                                 │ │
│ │   john@acmecapital.com - "Work Calendar"                    │ │
│ │   Last sync: 10 minutes ago                                 │ │
│ │   [Disconnect] [Sync Now]                                   │ │
│ │                                                             │ │
│ │ ○ Microsoft Outlook  [Connect]                              │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ SCHEDULING LINKS                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Your scheduling page: lpxgp.com/schedule/john-acme          │ │
│ │                                                             │ │
│ │ Meeting Types:                                              │ │
│ │ ┌─────────────────────────────────────────────────────────┐ │ │
│ │ │ 30-min Intro Call        [Edit] [Copy Link] [Active ●] │ │ │
│ │ │ 60-min Deep Dive         [Edit] [Copy Link] [Inactive] │ │ │
│ │ └─────────────────────────────────────────────────────────┘ │ │
│ │                                                             │ │
│ │ [+ Add Meeting Type]                                        │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ DEFAULT SETTINGS                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Video conferencing: [Google Meet ▼]                         │ │
│ │ Minimum notice: [24 hours ▼]                                │ │
│ │ Buffer between meetings: [15 min ▼]                         │ │
│ │ Booking window: [60 days ▼]                                 │ │
│ │                                                             │ │
│ │ Send reminders: [x] 24 hours before  [x] 1 hour before     │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ AVAILABILITY                                                     │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ○ Use calendar availability (block when busy)               │ │
│ │ ● Set custom hours:                                         │ │
│ │                                                             │ │
│ │ Monday    [x] 9:00 AM - 12:00 PM, 2:00 PM - 5:00 PM        │ │
│ │ Tuesday   [x] 9:00 AM - 5:00 PM                            │ │
│ │ Wednesday [x] 9:00 AM - 5:00 PM                            │ │
│ │ Thursday  [x] 9:00 AM - 5:00 PM                            │ │
│ │ Friday    [x] 9:00 AM - 12:00 PM                           │ │
│ │ Saturday  [ ]                                               │ │
│ │ Sunday    [ ]                                               │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 14.4 Implementation Phases

**Phase 1: Calendar Sync (M5)**
- Google Calendar OAuth integration
- Microsoft Outlook OAuth integration
- Sync existing meetings
- Auto-detect LP meetings
- Display meetings in outreach timeline

**Phase 2: Email Content Analysis (M5)**
- Store full email content (with user consent)
- Run AI analysis pipeline async
- Build LP communication profiles
- Feed insights into agent debates

**Phase 3: User Preferences (M5)**
- Implement preferences data model
- Build settings UI
- Add confirmation queue
- Respect preferences in all automation

**Phase 4: Scheduling Links (M6)**
- Build scheduling link infrastructure
- Create LP-facing booking pages
- Generate video meeting links
- Auto-update outreach stages on booking

---

### 14.5 Privacy & Data Handling

**Email Content:**
- User explicitly opts in to email analysis
- Content encrypted at rest
- Retention policy: 2 years, then anonymize
- GDPR: Right to deletion

**Calendar:**
- Only sync specified calendar(s)
- Don't store non-LP meeting details
- Clear OAuth tokens on disconnect

**LP Data:**
- Communication profiles aggregated (not individual emails)
- LPs can request data about themselves (GDPR)

---

*Section 14 complete. Email analysis for AI, user preferences, and calendar integration documented.*

---

