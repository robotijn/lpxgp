## 13. Team Member Onboarding & Profile Management

### Current State
- Basic team settings page exists (`settings-team.html`)
- No onboarding flow for new team members
- No profile completion incentives

### Proposed: Team Member Onboarding Flow

#### Onboarding Journey

```
┌─────────────────────────────────────────────────────────────────┐
│                  NEW TEAM MEMBER ONBOARDING                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. INVITE RECEIVED                                              │
│     ↓                                                            │
│  2. ACCOUNT CREATION (email + password)                          │
│     ↓                                                            │
│  3. PROFILE COMPLETION ←── Entice to complete fully             │
│     ├── Required: Name, Role                                     │
│     ├── Encouraged: Phone, LinkedIn, Bio, Photo                  │
│     └── Progress bar shows completion %                          │
│     ↓                                                            │
│  4. WELCOME TOUR (optional)                                      │
│     ↓                                                            │
│  5. DASHBOARD                                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Profile Completion Screen

```
┌─────────────────────────────────────────────────────────────────┐
│ Complete Your Profile                                           │
│                                                                  │
│ Profile Strength: ████████░░░░░░░░░░ 60%                        │
│ "Add your phone number to reach 80%"                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ ┌─────────┐                                                     │
│ │  Photo  │  Upload profile photo                               │
│ │  (opt)  │  [Choose File]                                      │
│ └─────────┘                                                     │
│                                                                  │
│ BASIC INFO                                                       │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ First Name *         Last Name *                            │ │
│ │ [John____________]   [Smith___________]                     │ │
│ │                                                             │ │
│ │ Job Title *                                                 │ │
│ │ [Principal__________]                                       │ │
│ │                                                             │ │
│ │ Email (from invite)                                         │ │
│ │ [john@acmecapital.com] (cannot change)                      │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ CONTACT INFO                                                     │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 📱 Phone Number                              [+1 ▼]         │ │
│ │ [___________________]                                       │ │
│ │                                                             │ │
│ │ 💡 Adding your phone helps your team reach you quickly      │ │
│ │    and enables SMS notifications for urgent LP responses.   │ │
│ │                                                             │ │
│ │ LinkedIn Profile URL                                        │ │
│ │ [https://linkedin.com/in/__________]                        │ │
│ │                                                             │ │
│ │ 💡 Your LinkedIn helps LPs verify your background and       │ │
│ │    builds trust in outreach.                                │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ ABOUT YOU (Optional)                                             │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Short Bio                                                   │ │
│ │ [                                                         ] │ │
│ │ [                                                         ] │ │
│ │ 0/300 characters                                            │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│                    [Skip for Now]  [Save & Continue]            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Profile Completion Incentives

| Field | Required | Completion % | Incentive Message |
|-------|----------|--------------|-------------------|
| Name | Yes | 20% | — |
| Job Title | Yes | 10% | — |
| Email | Yes (auto) | 10% | — |
| Phone | No | +15% | "Enable SMS alerts for LP responses" |
| LinkedIn | No | +15% | "Help LPs verify your background" |
| Photo | No | +15% | "Build trust with a professional photo" |
| Bio | No | +15% | "Share your expertise with the team" |

**Completion Rewards:**
- 80%+: "Complete Profile" badge on team page
- 100%: Profile highlighted in team directory
- Periodic nudges: "You're almost there! Add your phone to complete your profile."

#### Data Model

```sql
-- Extend users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS (
    phone TEXT,
    phone_verified BOOLEAN DEFAULT FALSE,
    linkedin_url TEXT,
    bio TEXT,
    photo_url TEXT,
    profile_completed_at TIMESTAMP,
    onboarding_completed_at TIMESTAMP
);

-- Calculate profile completion
CREATE FUNCTION calculate_profile_completion(user_uuid UUID)
RETURNS INTEGER AS $$
DECLARE
    completion INTEGER := 0;
    u RECORD;
BEGIN
    SELECT * INTO u FROM users WHERE id = user_uuid;

    -- Required fields (40% total)
    IF u.first_name IS NOT NULL THEN completion := completion + 20; END IF;
    IF u.last_name IS NOT NULL THEN completion := completion + 10; END IF;
    IF u.job_title IS NOT NULL THEN completion := completion + 10; END IF;

    -- Optional but encouraged fields (60% total)
    IF u.phone IS NOT NULL THEN completion := completion + 15; END IF;
    IF u.linkedin_url IS NOT NULL THEN completion := completion + 15; END IF;
    IF u.photo_url IS NOT NULL THEN completion := completion + 15; END IF;
    IF u.bio IS NOT NULL AND LENGTH(u.bio) > 20 THEN completion := completion + 15; END IF;

    RETURN completion;
END;
$$ LANGUAGE plpgsql;
```

#### Team Settings Page Enhancement

```
┌─────────────────────────────────────────────────────────────────┐
│ Settings > Team                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ TEAM MEMBERS (5)                               [+ Invite Member] │
│                                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 👤 John Smith          Principal       ████████████ 100%    │ │
│ │    john@acme.com       Admin           Profile Complete ✓   │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ 👤 Sarah Chen          Associate       ████████░░░░  65%    │ │
│ │    sarah@acme.com      Member          Missing: Phone, Bio  │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ 📧 mike@acme.com       —               Invite Pending       │ │
│ │    Sent 2 days ago                     [Resend] [Revoke]    │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ TEAM PROFILE COMPLETION                                          │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Average: 72%                                                │ │
│ │ ████████████████░░░░░░░░                                    │ │
│ │                                                             │ │
│ │ 💡 2 team members haven't added phone numbers.              │ │
│ │    [Send Reminder]                                          │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Phone Number Handling

```python
# Phone validation and formatting
import phonenumbers

def validate_and_format_phone(phone: str, country_code: str = "US") -> dict:
    """Validate and format phone number."""
    try:
        parsed = phonenumbers.parse(phone, country_code)

        if not phonenumbers.is_valid_number(parsed):
            return {"valid": False, "error": "Invalid phone number"}

        return {
            "valid": True,
            "e164": phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            ),
            "national": phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.NATIONAL
            ),
            "country": phonenumbers.region_code_for_number(parsed)
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}

# Optional: Phone verification via SMS
async def send_verification_code(phone: str, user_id: str):
    """Send SMS verification code."""
    code = generate_6_digit_code()

    # Store code with expiry
    await cache.set(f"phone_verify:{user_id}", code, ttl=600)

    # Send via Twilio/similar
    await sms_service.send(
        to=phone,
        body=f"Your LPxGP verification code is: {code}"
    )
```

#### Nudge System

```python
# Periodic nudges for incomplete profiles
async def send_profile_completion_nudges():
    """Send nudges to users with incomplete profiles."""

    incomplete_users = await db.query("""
        SELECT id, email, first_name,
               calculate_profile_completion(id) as completion
        FROM users
        WHERE calculate_profile_completion(id) < 80
        AND onboarding_completed_at IS NOT NULL
        AND last_nudge_at < NOW() - INTERVAL '7 days'
    """)

    for user in incomplete_users:
        missing = get_missing_fields(user.id)

        await send_email(
            to=user.email,
            subject="Complete your LPxGP profile",
            template="profile_nudge",
            context={
                "name": user.first_name,
                "completion": user.completion,
                "missing": missing,
                "benefit": get_benefit_message(missing[0])
            }
        )

        await db.execute(
            "UPDATE users SET last_nudge_at = NOW() WHERE id = $1",
            user.id
        )
```

---

