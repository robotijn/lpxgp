# Human-in-the-Loop Requirements

[← Back to Features Index](index.md)

---

The platform prioritizes human oversight for critical actions. AI assists but humans decide.

---

## F-HITL-01: Outreach Email Review [P0]

**Description:** Human reviews and manually sends all outreach

**Requirements:**
- AI generates draft email, displayed for review
- GP can edit email content before proceeding
- "Copy to Clipboard" button (no auto-send)
- GP manually pastes into their email client
- Track that email was copied (not sent)

**BDD Tests:** `m4-pitch.feature.md` - Generate email draft, Email is for review only, Copy email, Edit email, Save email as template

---

## F-HITL-02: Match Selection [P0]

**Description:** GP explicitly approves matches for outreach

**Requirements:**
- Matches shown as recommendations, not actions
- GP must explicitly add LP to shortlist
- Shortlist is separate from match results
- Bulk add to shortlist supported
- Clear distinction between "matched" and "shortlisted"

**BDD Tests:** `m3-matching.feature.md` - Save match to shortlist, Dismiss match, Bulk shortlist operations

---

## F-HITL-03: Fund Profile Confirmation [P0]

**Description:** GP confirms AI-extracted fund information

**Requirements:**
- AI extraction shows confidence scores per field
- GP reviews each extracted field
- Required fields highlighted if missing
- GP must explicitly approve profile before saving
- Audit trail of what was AI-extracted vs manually entered

**BDD Tests:** `e2e-journeys.feature.md` - AI extraction fails mid-process, Missing required fields on confirm; `m3-matching.feature.md` - Publish fund (requires confirmation)

---

## F-HITL-04: Data Import Preview [P0]

**Description:** Preview and approve data before committing

**Requirements:**
- Show preview of first N rows after mapping
- Highlight validation errors and warnings
- Show duplicate detection results
- Require explicit "Confirm Import" action
- Rollback option within 24 hours

**BDD Tests:** `m0-foundation.feature.md` - CSV import validation, Handle malformed CSV, Handle duplicate records; `m5-production.feature.md` - Admin bulk operations, Import rollback

---

## F-HITL-05: LP Data Corrections [P1]

**Description:** GPs can flag outdated or incorrect LP information

**Requirements:**
- "Flag as outdated" button on LP profiles
- Optional correction suggestion field
- Flagged records queued for admin review
- Track flag history per LP
- Notify admin of new flags

**BDD Tests:** `m0-foundation.feature.md` - LP data validation, Handle incomplete LP data; `m5-production.feature.md` - Data quality monitoring, Admin review queue

---

[Back to PRD Index →](../index.md)
