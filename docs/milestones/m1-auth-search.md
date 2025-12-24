# M1: Auth + Search + Deploy

**"Can search LPs, site is live"**

First public milestone that puts the platform live on lpxgp.com with authentication and basic LP search.

---

## Business Value

**Why this matters to customers:**

This is the first milestone where users can actually interact with the product:

- **Immediate Utility:** GPs can search and filter LPs by type, strategy, and geography - useful from day one
- **Secure Multi-Tenancy:** Each GP's data is isolated; you can onboard multiple clients safely
- **Production Ready:** Auto-deployment means fixes and features ship instantly
- **Credibility:** A working live site at lpxgp.com demonstrates the product is real

After M1, every subsequent feature is available to users immediately upon merge.

---

## What We Build

- Supabase Auth UI (don't build custom login forms)
- Row-Level Security (multi-tenant)
- LP full-text search (no embeddings yet)
- Basic GP dashboard
- **Deploy to Railway**
- **CI/CD pipeline (GitHub Actions)**

---

## Deliverables

- [ ] Auth: Supabase Auth UI (register, login, logout)
- [ ] RLS policies for multi-tenancy
- [ ] API: GET /api/v1/lps with filters
- [ ] UI: Login + LP search page
- [ ] UI: Simple GP dashboard
- [ ] **GitHub Actions: test -> deploy to Railway**
- [ ] **Live at lpxgp.com**

---

## CLI Learning

- Module 3: Project rules
- Module 4: GitHub Actions CI/CD
- Module 5: HTMX patterns

---

## Exit Criteria

- [ ] lpxgp.com shows login page
- [ ] Can register, login, search LPs
- [ ] Push to main -> auto deploys
- [ ] All M1 tests pass

---

## Demo

```
1. Open lpxgp.com in browser
2. Register account
3. Search: "Public Pension" + "Private Equity"
4. Show filtered results
```

---

[<- Previous: M0 Setup](m0-setup.md) | [Index](index.md) | [Next: M2 Semantic Search](m2-semantic.md) ->
