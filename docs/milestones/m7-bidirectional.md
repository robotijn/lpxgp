# M7: LP->GP Bidirectional Matching

**"LPs can discover and track funds"**

Extend the platform to serve LPs with the same intelligence currently offered to GPs - fund discovery, watchlists, and meeting requests.

---

## Business Value

**Why this matters to customers:**

Doubling down on one side of the market leaves value on the table:

- **Doubled TAM:** LPs are also looking for funds - serve both sides of the marketplace
- **Network Effects:** More LPs on platform = more value for GPs, and vice versa
- **Mutual Interest Detection:** When GP and LP both show interest, surface these high-probability matches
- **LP Efficiency:** LPs filter through hundreds of GP requests - help them find funds that actually fit their mandate
- **Premium Positioning:** Full bidirectional platform commands premium pricing vs. one-sided tools

After M7, LPxGP is a true two-sided marketplace, not just a GP prospecting tool.

---

## What We Build

- LP client onboarding
- LP mandate profiles
- LP->GP matching (same 42 agents, reversed perspective)
- LP dashboard (mirror of GP dashboard)
- LP watchlist (equivalent of GP shortlist)
- LP interest pipeline (evaluating funds)
- Inbound request handling (GP requests meeting)
- Meeting request generation (LP initiates)
- LP Health dashboard
- Mutual interest detection

---

## Bidirectional Principle

> Whatever a GP can do with LPs, an LP should be able to do with GPs.

---

## LP Feature Symmetry

| GP Feature | LP Equivalent |
|------------|---------------|
| Fund Profile | Mandate Profile |
| LP Recommendations | Fund Recommendations |
| Shortlist | Watchlist |
| Outreach Pipeline | Interest Pipeline |
| Pitch Generation | Meeting Request Generation |

---

## Deliverables

- [ ] API: LP mandate CRUD
- [ ] API: Fund recommendations for LP
- [ ] UI: LP dashboard
- [ ] UI: Mandate profile editor
- [ ] UI: Fund recommendations list
- [ ] UI: LP watchlist
- [ ] UI: Interest pipeline (reviewing, requested, inbound, meeting, DD, committed)
- [ ] UI: Meeting request generator
- [ ] UI: Inbound GP requests list
- [ ] LP Health dashboard (funnel from LP perspective)
- [ ] Mutual interest alerts

---

## Exit Criteria

- [ ] LP can create mandate
- [ ] LP sees fund recommendations
- [ ] LP can watchlist and track funds
- [ ] LP can request meetings with GPs
- [ ] LP can accept/decline GP requests
- [ ] Mutual interest detected and shown
- [ ] Live on lpxgp.com

---

## Demo

```
1. Login as LP
2. Create mandate
3. See fund recommendations
4. Add to watchlist
5. Request meeting with GP
6. See "Mutual Interest Detected" alert
```

---

[<- Previous: M6 Data Quality](m6-data-quality.md) | [Index](index.md) | [Next: M8 External Integrations](m8-integrations.md) ->
