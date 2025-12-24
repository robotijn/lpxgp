# M2: Semantic Search

**"Natural language search works"**

Upgrade from keyword filtering to AI-powered semantic search, letting users describe what they're looking for in natural language.

---

## Business Value

**Why this matters to customers:**

Traditional database filters require users to know exact categories. Semantic search transforms how GPs find LPs:

- **Natural Language Queries:** "Family offices interested in climate tech in the Nordics" just works
- **Discovery of Non-Obvious Matches:** Find LPs whose mandates align conceptually, not just by keywords
- **Time Savings:** One natural language query replaces multiple filter combinations
- **Competitive Advantage:** Most LP databases still rely on rigid category filters

This is the first "AI-powered" feature users experience - it sets expectations for the intelligence to come.

---

## What We Build

- Voyage AI embeddings for LPs
- Semantic search endpoint
- Combined filters + semantic ranking

---

## Deliverables

- [ ] Voyage AI configured
- [ ] Embeddings for all LPs
- [ ] API: POST /api/v1/lps/semantic-search
- [ ] UI: Natural language search box
- [ ] Auto-deploys on merge

---

## CLI Learning

- Module 6: Skills (`.claude/skills/`)
- Module 7: Agents (`pytest-runner`)

---

## Exit Criteria

- [ ] "climate tech investors" returns relevant results
- [ ] Semantic search < 2 seconds
- [ ] Live on lpxgp.com after merge

---

## Demo

```
1. Open lpxgp.com
2. Type: "Family offices in healthcare"
3. See ranked results with scores
```

---

[<- Previous: M1 Auth + Search](m1-auth-search.md) | [Index](index.md) | [Next: M3 GP Profiles + Matching](m3-matching.md) ->
