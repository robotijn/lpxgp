# M4: Pitch Generation + Explanations

**"AI generates pitches and explanations"**

Transform match scores into actionable outreach materials - personalized pitches, email drafts, and talking points.

---

## Business Value

**Why this matters to customers:**

Knowing which LPs to pursue is only half the battle - you need to know what to say:

- **Personalized at Scale:** Every LP gets tailored messaging that speaks to their specific mandate and concerns
- **Actionable Insights:** "Why this LP?" explanations help GPs understand the match and prepare for conversations
- **Time Savings:** Hours of pitch customization reduced to minutes of review and refinement
- **Human Control:** All content is reviewed before use - AI drafts, humans decide
- **Professional Output:** PDF exports ready for internal stakeholders or board meetings

After M4, GPs have everything they need to start reaching out to matched LPs.

---

## What We Build

- Pitch generation from debates (uses Pitch debate output)
- LP-specific executive summaries
- Personalized outreach emails (copy to clipboard, no auto-send)
- Human-in-loop review flow
- PDF export

---

## Human-in-Loop Flow

- Generate content -> GP reviews/edits -> copy to clipboard
- No auto-send functionality
- GP feedback improves future explanations

---

## Deliverables

- [ ] API: GET /api/v1/matches/{id}/pitch
- [ ] API: GET /api/v1/matches/{id}/email-draft
- [ ] UI: Pitch panel with talking points
- [ ] UI: Email editor with copy to clipboard
- [ ] UI: PDF export
- [ ] Human review workflow (generate -> review -> copy)

---

## CLI Learning

- Module 9: LLM API (OpenRouter)
- Module 10: Prompt engineering

---

## Exit Criteria

- [ ] View match -> see pitch
- [ ] Generate email -> copy to clipboard
- [ ] Download PDF summary
- [ ] Live on lpxgp.com

---

## Demo

```
1. View match -> "Why this LP?"
2. See explanation + talking points
3. Generate email -> copy
4. Generate summary -> download PDF
```

---

[<- Previous: M3 GP Profiles + Matching](m3-matching.md) | [Index](index.md) | [Next: M5 Shortlist + Pipeline](m5-operations.md) ->
