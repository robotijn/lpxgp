# M5: Shortlist + Pipeline + Admin Foundation

**"GPs can track outreach, admins can manage"**

Transform LPxGP from a matching tool into a complete workflow system with pipeline tracking and administrative controls.

---

## Business Value

**Why this matters to customers:**

Recommendations are useless if you can't act on them systematically:

- **Organized Outreach:** Shortlists let GPs save and prioritize top matches instead of losing them in search results
- **Pipeline Visibility:** Track where each LP relationship stands - no more spreadsheets or lost context
- **Activity History:** Every interaction logged so team members can pick up where others left off
- **Team Collaboration:** Multiple team members can work the same pipeline without stepping on each other
- **Admin Oversight:** Platform operators can monitor client activity and manage user access

After M5, GPs can manage their entire LP outreach workflow within LPxGP.

---

## What We Build

- GP Shortlist (add/remove LPs)
- Outreach pipeline tracking (manual stage updates)
- Activity logging
- Admin dashboard structure
- Basic team management

---

## Outreach Pipeline Stages

```
identified -> shortlisted -> researching ->
contacted -> awaiting_response -> responded ->
meeting_scheduled -> meeting_completed ->
dd_in_progress -> committed/passed
```

---

## Admin Dashboard Structure

```
Admin
+-- Overview (stats)
+-- CLIENTS
|   +-- GP Clients
|   +-- LP Clients (placeholder)
|   +-- Users
+-- MARKET DATA
|   +-- Companies
|   +-- People
+-- SYSTEM
    +-- Health
    +-- Jobs
```

---

## Deliverables

- [ ] API: Shortlist CRUD
- [ ] API: Pipeline stage updates
- [ ] UI: Shortlist page with pipeline columns
- [ ] UI: LP card with activity timeline
- [ ] UI: Manual stage updates (drag-and-drop or buttons)
- [ ] Admin: Dashboard navigation structure
- [ ] Admin: GP Clients list
- [ ] Admin: Users list
- [ ] Admin: Market Companies list
- [ ] Admin: Market People list
- [ ] Team: Invite members, role assignment

---

## Exit Criteria

- [ ] GP can shortlist LPs
- [ ] GP can move LPs through pipeline stages
- [ ] Activity logged on LP card
- [ ] Admin can view clients and users
- [ ] Live on lpxgp.com

---

## Demo

```
1. View LP match -> Add to Shortlist
2. Move LP through pipeline stages
3. See activity timeline
4. Login as admin -> see dashboard
```

---

[<- Previous: M4 Pitch Generation](m4-pitch.md) | [Index](index.md) | [Next: M6 Data Quality](m6-data-quality.md) ->
