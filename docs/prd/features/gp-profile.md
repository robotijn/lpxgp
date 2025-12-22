# GP Profile Management

[← Back to Features Index](index.md)

---

## F-GP-01: Fund Profile Creation [P0]

**Description:** GPs can create detailed fund profiles

**Requirements:**
- All fields from data model (see [Data Model](../data-model.md))
- Save as draft, publish when ready
- Multiple funds per company
- Profile completeness indicator

**Test Cases:** See TEST-GP-01 in Testing Strategy

---

## F-GP-02: Pitch Deck Upload [P0]

**Description:** Upload and process fund pitch decks with AI-assisted profile creation

**Requirements:**
- Accept PDF and PPTX formats
- Max file size: 100MB
- Store securely in Supabase Storage

**Flow:**
1. GP uploads PDF/PPT pitch deck
2. LLM extracts fund information (strategy, size, team, track record, etc.)
3. System displays extracted fields for GP review and confirmation
4. Interactive questionnaire prompts GP for any missing required fields
5. GP reviews complete profile and approves before saving
6. Profile saved with confirmation status

**Test Cases:** See TEST-GP-02 in Testing Strategy

---

## F-GP-03: AI Profile Extraction [P0]

**Description:** Auto-populate profile from uploaded deck

**Requirements:**
- Parse PDF/PPTX content
- Use LLM to extract structured data
- Present extracted data for user confirmation
- Map to profile fields

---

## F-GP-04: Fund Profile Editing [P0]

**Description:** Edit and update fund profiles

**Requirements:**
- Form-based editing
- Version history (audit trail)
- Validation rules
- Auto-save drafts

**Test Cases:** See TEST-GP-04 in Testing Strategy

---

[Next: LP Database →](lp-database.md)
