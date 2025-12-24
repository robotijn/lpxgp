# M0: Setup + Data Import

**"Data imported, schema ready"**

Foundation milestone that establishes the technical infrastructure and imports existing LP/GP data into the system.

---

## Business Value

**Why this matters to customers:**

Before users can find and connect with investors, we need clean, structured data to work with. M0 ensures:

- **Data Foundation:** Your existing LP and GP contacts become searchable and analyzable
- **Clean Architecture:** A solid technical base prevents costly rewrites later
- **Two-Database Model:** Separates market intelligence from client data, enabling future data partnerships and multi-tenant security
- **Development Velocity:** Proper setup now means faster feature delivery in later milestones

This milestone has no direct user-facing features, but every future capability depends on it.

---

## What We Build

- Project structure (Python + FastAPI + HTMX)
- Supabase schema with two-database model
- Import existing LP/GP data into Market DB
- Data cleaning with Claude CLI

---

## Two-Database Architecture

```sql
-- Market Data (Intelligence Layer)
companies (id, name, type, lp_type, aum_usd_mm, strategies, ...)
people (id, full_name, email, linkedin_url, ...)
company_people (company_id, person_id, title, is_decision_maker, ...)

-- Client Data (Application Layer)
clients (id, company_id, client_type, subscription_tier, ...)
users (id, client_id, email, role, ...)
```

---

## Deliverables

- [ ] main.py + base.html + Supabase tables
- [ ] Two-database schema implemented
- [ ] LP market data imported
- [ ] GP market data imported
- [ ] CDN setup (HTMX + Tailwind, no npm)

---

## CLI Learning

- Module 1: CLAUDE.md
- Module 2: Commands (`/status`, `/test`)

---

## Exit Criteria

- [ ] `uv run pytest` passes
- [ ] localhost:8000/health returns 200
- [ ] Market data queryable

---

## Demo

Local only - show Supabase dashboard with your data

---

[Index](index.md) | [Next: M1 Auth + Search](m1-auth-search.md) ->
