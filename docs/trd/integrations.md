# External Integrations

[Back to TRD Index](index.md)

---

## Overview

LPxGP integrates with external systems to sync data and provide seamless workflows. This document covers calendar, email, CRM integration patterns, and webhook design.

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       INTEGRATION ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                          ┌─────────────────────┐                            │
│                          │     LPxGP Core      │                            │
│                          │                     │                            │
│                          │  ┌───────────────┐  │                            │
│                          │  │ Integration   │  │                            │
│                          │  │ Manager       │  │                            │
│                          │  └───────┬───────┘  │                            │
│                          │          │          │                            │
│                          └──────────┼──────────┘                            │
│                                     │                                        │
│       ┌─────────────────────────────┼─────────────────────────────┐         │
│       │                             │                             │         │
│       ▼                             ▼                             ▼         │
│  ┌─────────────┐             ┌─────────────┐             ┌─────────────┐   │
│  │  CALENDAR   │             │    EMAIL    │             │     CRM     │   │
│  │             │             │             │             │             │   │
│  │ ┌─────────┐ │             │ ┌─────────┐ │             │ ┌─────────┐ │   │
│  │ │ Google  │ │             │ │ Gmail   │ │             │ │Salesforce││   │
│  │ │Calendar │ │             │ │         │ │             │ │         │ │   │
│  │ └─────────┘ │             │ └─────────┘ │             │ └─────────┘ │   │
│  │ ┌─────────┐ │             │ ┌─────────┐ │             │ ┌─────────┐ │   │
│  │ │ Outlook │ │             │ │Outlook  │ │             │ │ HubSpot │ │   │
│  │ │Calendar │ │             │ │         │ │             │ │         │ │   │
│  │ └─────────┘ │             │ └─────────┘ │             │ └─────────┘ │   │
│  └─────────────┘             └─────────────┘             └─────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        WEBHOOK RECEIVER                               │  │
│  │                                                                        │  │
│  │  POST /webhooks/calendar-event    - Meeting created/updated           │  │
│  │  POST /webhooks/email-received    - New email from LP/GP              │  │
│  │  POST /webhooks/crm-contact       - Contact updated in CRM            │  │
│  │  POST /webhooks/entity-updated    - Internal entity change            │  │
│  │                                                                        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Calendar Sync Architecture

### Use Cases

1. **Meeting Detection** - Identify meetings with LP contacts
2. **Pre-meeting Prep** - Auto-generate briefing materials
3. **Post-meeting Capture** - Prompt for note entry
4. **Relationship Signals** - Track meeting frequency

### OAuth Flow

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         CALENDAR OAUTH FLOW                                   │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  1. USER INITIATES                                                            │
│     ┌─────────────┐                                                          │
│     │ User clicks │                                                          │
│     │ "Connect    │                                                          │
│     │  Calendar"  │                                                          │
│     └──────┬──────┘                                                          │
│            │                                                                  │
│  2. REDIRECT TO PROVIDER                                                      │
│            │                                                                  │
│            ▼                                                                  │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │  GET https://accounts.google.com/o/oauth2/v2/auth               │     │
│     │    ?client_id=xxx                                                │     │
│     │    &redirect_uri=https://lpxgp.com/oauth/callback               │     │
│     │    &scope=https://www.googleapis.com/auth/calendar.readonly     │     │
│     │    &state={user_id}:{company_id}                                │     │
│     └─────────────────────────────────────────────────────────────────┘     │
│            │                                                                  │
│  3. USER CONSENTS                                                             │
│            │                                                                  │
│  4. CALLBACK WITH CODE                                                        │
│            │                                                                  │
│            ▼                                                                  │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │  GET /oauth/callback?code=xxx&state=...                         │     │
│     └─────────────────────────────────────────────────────────────────┘     │
│            │                                                                  │
│  5. EXCHANGE FOR TOKENS                                                       │
│            │                                                                  │
│            ▼                                                                  │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │  POST https://oauth2.googleapis.com/token                        │     │
│     │    grant_type=authorization_code                                 │     │
│     │    code=xxx                                                      │     │
│     │                                                                  │     │
│     │  Response: { access_token, refresh_token, expires_in }           │     │
│     └─────────────────────────────────────────────────────────────────┘     │
│            │                                                                  │
│  6. STORE ENCRYPTED TOKENS                                                    │
│            │                                                                  │
│            ▼                                                                  │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │  INSERT INTO user_integrations (                                 │     │
│     │    user_id, provider, encrypted_tokens, scopes, expires_at       │     │
│     │  )                                                               │     │
│     └─────────────────────────────────────────────────────────────────┘     │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Calendar Sync Implementation

```python
# src/integrations/calendar.py
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Iterator

class CalendarEvent:
    id: str
    title: str
    start: datetime
    end: datetime
    attendees: list[str]  # Email addresses
    location: str | None
    description: str | None

class CalendarAdapter(ABC):
    @abstractmethod
    async def list_events(
        self,
        start: datetime,
        end: datetime,
    ) -> Iterator[CalendarEvent]:
        pass

    @abstractmethod
    async def subscribe_to_changes(self, webhook_url: str) -> str:
        """Set up webhook for real-time updates. Returns channel ID."""
        pass

class GoogleCalendarAdapter(CalendarAdapter):
    def __init__(self, credentials: dict):
        self.service = build('calendar', 'v3', credentials=credentials)

    async def list_events(self, start: datetime, end: datetime) -> Iterator[CalendarEvent]:
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=start.isoformat() + 'Z',
            timeMax=end.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        for event in events_result.get('items', []):
            yield CalendarEvent(
                id=event['id'],
                title=event.get('summary', ''),
                start=parse(event['start'].get('dateTime', event['start'].get('date'))),
                end=parse(event['end'].get('dateTime', event['end'].get('date'))),
                attendees=[a['email'] for a in event.get('attendees', [])],
                location=event.get('location'),
                description=event.get('description'),
            )

    async def subscribe_to_changes(self, webhook_url: str) -> str:
        channel = self.service.events().watch(
            calendarId='primary',
            body={
                'id': str(uuid4()),
                'type': 'web_hook',
                'address': webhook_url,
            }
        ).execute()
        return channel['id']
```

### Meeting Detection Service

```python
# src/services/meeting_detector.py
class MeetingDetector:
    """Detect meetings with known LP/GP contacts."""

    async def process_calendar_event(self, event: CalendarEvent, user_id: str):
        """Process a calendar event to detect LP/GP meetings."""

        # Match attendees to known contacts
        matched_contacts = []
        for email in event.attendees:
            contact = await self._find_contact_by_email(email)
            if contact:
                matched_contacts.append(contact)

        if not matched_contacts:
            return  # No LP/GP contacts in this meeting

        # Create/update touchpoint
        await self._create_meeting_touchpoint(event, matched_contacts, user_id)

        # Generate pre-meeting prep if meeting is upcoming
        if event.start > datetime.now():
            await self._schedule_prep_generation(event, matched_contacts)

    async def _schedule_prep_generation(self, event: CalendarEvent, contacts: list):
        """Queue meeting prep generation for 1 hour before meeting."""
        prep_time = event.start - timedelta(hours=1)

        await supabase.table("scheduled_jobs").insert({
            "job_type": "generate_meeting_prep",
            "run_at": prep_time.isoformat(),
            "payload": {
                "event_id": event.id,
                "contact_ids": [c.id for c in contacts],
            }
        }).execute()
```

---

## Email Sync Architecture

### Use Cases

1. **Relationship Signals** - Detect email exchanges with LP contacts
2. **Thread Tracking** - Link emails to touchpoints
3. **Sentiment Analysis** - Gauge relationship health
4. **Follow-up Detection** - Identify unanswered emails

### Read-Only Email Access

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         EMAIL SYNC (READ-ONLY)                                │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  SCOPES (minimal required)                                                    │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │  Gmail: https://www.googleapis.com/auth/gmail.readonly                  │  │
│  │  Outlook: Mail.Read                                                     │  │
│  │                                                                          │  │
│  │  NO: Send, Delete, Modify                                               │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  SYNC STRATEGY                                                                │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                          │  │
│  │  Initial Sync: Last 90 days of email metadata                           │  │
│  │  Incremental: Poll every 15 minutes for new emails                      │  │
│  │  Webhook: Subscribe to push notifications (preferred)                   │  │
│  │                                                                          │  │
│  │  FILTER: Only process emails to/from known LP/GP domains                │  │
│  │                                                                          │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  PRIVACY                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                          │  │
│  │  Stored: Metadata only (from, to, date, subject, thread_id)             │  │
│  │  NOT Stored: Full email body (unless user explicitly saves)             │  │
│  │                                                                          │  │
│  │  Processing: Body read temporarily for:                                  │  │
│  │  - Sender/recipient extraction                                          │  │
│  │  - Optional: AI summary (ephemeral, not stored)                         │  │
│  │                                                                          │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Email Sync Implementation

```python
# src/integrations/email.py
class EmailAdapter(ABC):
    @abstractmethod
    async def list_messages(
        self,
        since: datetime,
        domains: list[str],  # Filter to known LP/GP domains
    ) -> Iterator[EmailMessage]:
        pass

class GmailAdapter(EmailAdapter):
    def __init__(self, credentials: dict):
        self.service = build('gmail', 'v1', credentials=credentials)

    async def list_messages(self, since: datetime, domains: list[str]) -> Iterator[EmailMessage]:
        # Build query for LP/GP domains
        domain_query = " OR ".join([f"from:{d}" for d in domains])
        query = f"after:{since.strftime('%Y/%m/%d')} ({domain_query})"

        results = self.service.users().messages().list(
            userId='me',
            q=query,
        ).execute()

        for msg in results.get('messages', []):
            full = self.service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'To', 'Subject', 'Date']
            ).execute()

            yield EmailMessage(
                id=msg['id'],
                thread_id=full['threadId'],
                from_email=self._extract_email(full, 'From'),
                to_emails=self._extract_emails(full, 'To'),
                subject=self._get_header(full, 'Subject'),
                date=parse(self._get_header(full, 'Date')),
            )
```

---

## CRM Integration Patterns

### Bidirectional Sync

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         CRM BIDIRECTIONAL SYNC                                │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌───────────────┐                               ┌───────────────┐           │
│  │               │                               │               │           │
│  │    LPxGP      │◀─────── Sync Rules ─────────▶│    CRM        │           │
│  │               │                               │               │           │
│  └───────────────┘                               └───────────────┘           │
│                                                                               │
│  SYNC DIRECTION RULES                                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                          │  │
│  │  CRM → LPxGP (read from CRM):                                           │  │
│  │  • Contact info (email, phone, title)                                   │  │
│  │  • Organization details                                                 │  │
│  │  • Notes marked for sync                                                │  │
│  │                                                                          │  │
│  │  LPxGP → CRM (write to CRM):                                            │  │
│  │  • Match scores (as custom field)                                       │  │
│  │  • AI-generated summaries                                               │  │
│  │  • Touchpoint records                                                   │  │
│  │  • Task follow-ups                                                      │  │
│  │                                                                          │  │
│  │  CONFLICT RESOLUTION: CRM wins for contact data                         │  │
│  │                                                                          │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  FIELD MAPPING (Configurable per tenant)                                      │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                          │  │
│  │  LPxGP Field          Salesforce Field         HubSpot Field            │  │
│  │  ───────────          ────────────────         ─────────────            │  │
│  │  org.name             Account.Name             company.name             │  │
│  │  person.email         Contact.Email            contact.email            │  │
│  │  match.score          Account.LPxGP_Score__c   company.lpxgp_score      │  │
│  │  touchpoint           Task                     engagement               │  │
│  │                                                                          │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Salesforce Adapter

```python
# src/integrations/crm/salesforce.py
from simple_salesforce import Salesforce

class SalesforceAdapter(CRMAdapter):
    def __init__(self, instance_url: str, access_token: str, refresh_token: str):
        self.sf = Salesforce(
            instance_url=instance_url,
            session_id=access_token
        )

    async def sync_contact(self, contact: dict, direction: str) -> dict:
        if direction == "from_crm":
            sf_contact = self.sf.Contact.get(contact["crm_id"])
            return self._map_from_salesforce(sf_contact)

        elif direction == "to_crm":
            sf_data = self._map_to_salesforce(contact)
            if contact.get("crm_id"):
                self.sf.Contact.update(contact["crm_id"], sf_data)
            else:
                result = self.sf.Contact.create(sf_data)
                return {"crm_id": result["id"]}

    async def push_match_score(self, account_id: str, score: float, summary: str):
        """Push LPxGP match score to custom Salesforce field."""
        self.sf.Account.update(account_id, {
            "LPxGP_Match_Score__c": score,
            "LPxGP_Summary__c": summary,
            "LPxGP_Last_Synced__c": datetime.now().isoformat()
        })

    async def create_task(self, contact_id: str, task: dict):
        """Create follow-up task in Salesforce."""
        self.sf.Task.create({
            "WhoId": contact_id,
            "Subject": task["title"],
            "Description": task["description"],
            "ActivityDate": task["due_date"],
            "Priority": task["priority"],
            "Status": "Not Started"
        })
```

---

## Webhook Design

### Webhook Receiver

```python
# src/routes/webhooks.py
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from hashlib import sha256
import hmac

router = APIRouter(prefix="/webhooks")

@router.post("/calendar-event")
async def calendar_event_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """Handle calendar event notifications."""
    # Verify webhook signature
    if not await verify_google_signature(request):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()

    # Queue background processing
    background_tasks.add_task(
        process_calendar_webhook,
        payload
    )

    return {"status": "accepted"}

@router.post("/email-received")
async def email_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle new email notifications."""
    if not await verify_gmail_push(request):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    background_tasks.add_task(process_email_webhook, payload)

    return {"status": "accepted"}

@router.post("/crm-contact/{provider}")
async def crm_webhook(
    provider: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """Handle CRM webhook (Salesforce, HubSpot)."""
    verifier = get_crm_verifier(provider)
    if not await verifier(request):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    background_tasks.add_task(process_crm_webhook, provider, payload)

    return {"status": "accepted"}

# Internal webhook for entity changes
@router.post("/entity-updated")
async def entity_updated(request: Request, background_tasks: BackgroundTasks):
    """Handle internal entity update notifications."""
    payload = await request.json()
    entity_type = payload["entity_type"]
    entity_id = payload["entity_id"]

    # Invalidate caches
    background_tasks.add_task(invalidate_entity_cache, entity_type, entity_id)

    # Trigger dependent updates
    background_tasks.add_task(trigger_dependent_updates, entity_type, entity_id)

    return {"status": "accepted"}
```

### Webhook Security

```python
# src/integrations/webhook_security.py
async def verify_google_signature(request: Request) -> bool:
    """Verify Google API webhook signature."""
    channel_token = request.headers.get("X-Goog-Channel-Token")
    expected_token = await get_channel_token(
        request.headers.get("X-Goog-Channel-ID")
    )
    return hmac.compare_digest(channel_token, expected_token)

async def verify_salesforce_signature(request: Request) -> bool:
    """Verify Salesforce outbound message signature."""
    signature = request.headers.get("X-Salesforce-Signature")
    body = await request.body()
    expected = hmac.new(
        SALESFORCE_WEBHOOK_SECRET.encode(),
        body,
        sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)

async def verify_hubspot_signature(request: Request) -> bool:
    """Verify HubSpot webhook signature."""
    signature = request.headers.get("X-HubSpot-Signature-v3")
    timestamp = request.headers.get("X-HubSpot-Request-Timestamp")
    body = await request.body()

    message = f"{request.method}{request.url}{body.decode()}{timestamp}"
    expected = hmac.new(
        HUBSPOT_CLIENT_SECRET.encode(),
        message.encode(),
        sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected)
```

### Webhook Retry Strategy

```python
# src/integrations/webhook_processor.py
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60)
)
async def process_webhook_with_retry(webhook_type: str, payload: dict):
    """Process webhook with exponential backoff retry."""
    processor = get_processor(webhook_type)
    await processor.process(payload)

async def handle_webhook_failure(webhook_type: str, payload: dict, error: Exception):
    """Store failed webhook for manual review."""
    await supabase.table("webhook_failures").insert({
        "webhook_type": webhook_type,
        "payload": payload,
        "error": str(error),
        "retry_count": 5,
        "created_at": datetime.now().isoformat()
    }).execute()
```

---

## Integration Database Schema

```sql
-- User integration connections
CREATE TABLE user_integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,  -- 'google', 'microsoft', 'salesforce', 'hubspot'
    integration_type TEXT NOT NULL,  -- 'calendar', 'email', 'crm'
    encrypted_tokens BYTEA NOT NULL,  -- Encrypted refresh token
    scopes TEXT[],
    expires_at TIMESTAMPTZ,
    last_sync TIMESTAMPTZ,
    sync_status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, provider, integration_type)
);

-- Webhook channel subscriptions
CREATE TABLE webhook_channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    provider TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    channel_token TEXT NOT NULL,
    resource_uri TEXT,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- CRM field mappings (per company)
CREATE TABLE crm_field_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    crm_provider TEXT NOT NULL,
    lpxgp_field TEXT NOT NULL,
    crm_field TEXT NOT NULL,
    sync_direction TEXT CHECK (sync_direction IN ('from_crm', 'to_crm', 'bidirectional')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(company_id, crm_provider, lpxgp_field)
);

-- Webhook failures for retry/review
CREATE TABLE webhook_failures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    webhook_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    error TEXT,
    retry_count INTEGER DEFAULT 0,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Token Encryption

```python
# src/integrations/token_encryption.py
from cryptography.fernet import Fernet
import os

# Generate key once and store in env
ENCRYPTION_KEY = os.environ["TOKEN_ENCRYPTION_KEY"]
fernet = Fernet(ENCRYPTION_KEY.encode())

def encrypt_tokens(tokens: dict) -> bytes:
    """Encrypt OAuth tokens for storage."""
    import json
    token_json = json.dumps(tokens)
    return fernet.encrypt(token_json.encode())

def decrypt_tokens(encrypted: bytes) -> dict:
    """Decrypt OAuth tokens from storage."""
    import json
    decrypted = fernet.decrypt(encrypted)
    return json.loads(decrypted.decode())
```

---

## Related Documents

- [Architecture](architecture.md) - System design
- [Infrastructure](infrastructure.md) - Deployment and security
