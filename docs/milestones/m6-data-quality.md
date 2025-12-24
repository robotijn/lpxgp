# M6: Data Quality + Financial Analyst

**"Analysts curate data, health dashboards work"**

Establish data quality operations with dedicated analyst workflows and health monitoring dashboards.

---

## Business Value

**Why this matters to customers:**

AI matching is only as good as the underlying data:

- **Data Accuracy:** Dedicated analyst workflows ensure LP information stays current and complete
- **Prioritized Effort:** AI identifies which records need attention most, maximizing analyst productivity
- **Document Intelligence:** Upload pitch decks and PDFs to automatically extract structured data
- **Trust Through Transparency:** Health dashboards show data quality metrics so clients know what they're working with
- **Funnel Insights:** GP Health dashboard reveals where deals are stuck and conversion rates by stage

After M6, the platform maintains data quality systematically rather than ad-hoc.

---

## What We Build

- Financial Analyst user role
- Analyst dashboard with AI-prioritized queue
- Document upload + extraction (pitch decks, PDFs)
- Agentic internet research (with human validation)
- Data Health dashboard
- GP Health dashboard (funnel metrics)

---

## User Roles

| Role | Market Data | Client Data | Admin |
|------|-------------|-------------|-------|
| Admin | Full CRUD | Full CRUD | Full access |
| Financial Analyst | Full CRUD | View only | No access |
| GP/LP User | View only | Own client only | No access |

---

## Financial Analyst Workflow

```
1. Check priority queue (AI scores what needs attention)
2. Work on record:
   - View missing fields
   - Accept/reject AI research suggestions
   - Upload document for extraction
   - Manual entry
3. Validate and save
```

---

## Health Dashboards

- **Data Health:** Quality scores, field completeness, freshness, analyst activity
- **GP Health:** Funnel (recommendations -> committed), conversion rates, bottlenecks

---

## Deliverables

- [ ] User role: financial_analyst
- [ ] Analyst dashboard with priority queue
- [ ] AI priority scoring algorithm
- [ ] Document upload endpoint
- [ ] PDF/PPT extraction pipeline
- [ ] Internet research agent (find missing data)
- [ ] Human-in-loop validation UI
- [ ] Data Health dashboard with charts
- [ ] GP Health dashboard with funnel
- [ ] Quality score tracking per company

---

## Exit Criteria

- [ ] Analyst can see prioritized work queue
- [ ] Upload pitch deck -> extract fund info
- [ ] AI suggests data -> analyst validates
- [ ] Data Health shows quality trends
- [ ] GP Health shows conversion funnel
- [ ] Live on lpxgp.com

---

## Demo

```
1. Login as analyst
2. See priority queue with AI scores
3. Upload pitch deck -> review extracted data
4. Accept AI suggestions
5. View Data Health dashboard
```

---

[<- Previous: M5 Shortlist + Pipeline](m5-operations.md) | [Index](index.md) | [Next: M7 Bidirectional Matching](m7-bidirectional.md) ->
