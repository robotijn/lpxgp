# Feature Requirements

[← Back to PRD Index](../index.md)

---

## 5.1 Priority Definitions

| Priority | Definition | MVP? |
|----------|------------|------|
| **P0** | Must have for launch | Yes |
| **P1** | Important, soon after launch | No |
| **P2** | Nice to have | No |
| **P3** | Future consideration | No |

## 5.2 MVP Feature Priority Order

Based on confirmed priorities:

```
Priority A (First): LP Search & Database
├── F-LP-01: LP Profile Storage [P0]
├── F-LP-02: LP Search & Filter [P0]
├── F-LP-03: Semantic Search [P0]
├── F-LP-04: LP Data Import [P0]
├── F-LP-05: LP Data Cleaning Pipeline [P0]
└── F-LP-06: LP Data Enrichment [P1] (post-MVP)

Priority B (Second): Matching Engine
├── F-MATCH-01: Hard Filter Matching [P0]
├── F-MATCH-02: Soft Scoring [P0]
├── F-MATCH-03: Semantic Matching [P0]
├── F-MATCH-04: Match Explanations [P0]
├── F-MATCH-05: Match Feedback [P1] (post-MVP)
├── F-MATCH-06: LP-Side Matching [Post-MVP] (bidirectional)
└── F-MATCH-07: Enhanced Match Explanations [P0]

Priority C (Third): Pitch Generation
├── F-PITCH-01: LP-Specific Executive Summary [P0]
└── F-PITCH-02: Outreach Email Draft [P0]

Priority D: Authentication & Authorization (Section 5.3)
├── F-AUTH-01: User Login [P0]
├── F-AUTH-02: Multi-tenancy [P0]
├── F-AUTH-03: Role-Based Access [P0]
└── F-AUTH-04: Invitation System [P0]

Priority E: Multi-Agent Architecture (Section 5.6.2-5.6.3)
├── F-AGENT-01: Research Agent (Data Enrichment) [P0] (M3)
├── F-AGENT-02: LLM-Interpreted Constraints [P0] (M3)
├── F-AGENT-03: Learning Agent (Cross-Company) [P0] (M3)
└── F-AGENT-04: Explanation Agent (Interaction Learning) [P0] (M4)

Priority F: User Interface (Section 5.8)
├── F-UI-01: Dashboard [P0]
├── F-UI-02: Fund Profile Form [P0]
├── F-UI-03: LP Search Interface [P0]
├── F-UI-04: Match Results View [P0]
└── F-UI-05: Admin Interface [P0]

Priority G: Human-in-the-Loop (Section 5.9)
├── F-HITL-01: Outreach Email Review [P0]
├── F-HITL-02: Match Selection [P0]
├── F-HITL-03: Fund Profile Confirmation [P0]
├── F-HITL-04: Data Import Preview [P0]
└── F-HITL-05: LP Data Corrections [P1]
```

---

## Feature Documentation

| Feature Area | File | Key Features |
|--------------|------|--------------|
| Authentication | [auth.md](auth.md) | F-AUTH-01 through F-AUTH-12 |
| GP Profiles | [gp-profile.md](gp-profile.md) | F-GP-01 through F-GP-04 |
| LP Database | [lp-database.md](lp-database.md) | F-LP-01 through F-LP-06 |
| Matching Engine | [matching.md](matching.md) | F-MATCH-*, F-AGENT-*, F-DEBATE-* |
| Pitch Generation | [pitch.md](pitch.md) | F-PITCH-01 through F-PITCH-05 |
| User Interface | [ui.md](ui.md) | F-UI-01 through F-UI-05 |
| Human-in-the-Loop | [hitl.md](hitl.md) | F-HITL-01 through F-HITL-05 |
| IR & Analytics | [ir-analytics.md](ir-analytics.md) | F-IR-*, F-ER-*, F-BB-*, F-RI-*, F-AA-* |

---

[Next: Authentication →](auth.md)
