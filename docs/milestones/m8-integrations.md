# M8: External Integrations

**"Email, calendar, CRM connected"**

Connect LPxGP to the tools users already work with - email, calendar, and CRM systems.

---

## Business Value

**Why this matters to customers:**

Users don't live in LPxGP - they live in email, calendar, and CRM:

- **Reduced Context Switching:** Email conversations with LPs appear in timeline without manual logging
- **Complete Picture:** Calendar meetings auto-sync so the platform knows when relationships advance
- **Easy Scheduling:** Generate booking links LPs can use - no back-and-forth emails
- **CRM Sync:** Keep Salesforce/HubSpot updated automatically - single source of truth
- **User Control:** Granular preferences let users choose their automation comfort level

After M8, LPxGP fits into existing workflows rather than replacing them.

---

## What We Build

- Email sync (Gmail OAuth, Microsoft Graph)
- Email content analysis for AI learning
- Calendar sync (Google Calendar, Microsoft Outlook)
- Scheduling links (Calendly-style)
- CRM integrations (HubSpot, Salesforce)
- User preferences for automation behavior

---

## Email Integration

- OAuth connection to mailbox
- Sync emails to/from LP contacts
- AI analysis (sentiment, topics, objections)
- Build LP communication profiles
- Stage inference from email content

---

## Calendar Integration

- OAuth connection
- Sync meetings with LPs
- Auto-detect LP meetings
- Display in outreach timeline

---

## Scheduling Links

- GP creates availability slots
- Generate LP-facing booking page
- Auto-create video meeting link
- Auto-update outreach stage on booking

---

## CRM Integration

- HubSpot: Push outreach status as deals
- Salesforce: Push as opportunities
- Bidirectional sync option
- Custom field mapping

---

## User Preferences

- Email sync mode: disabled / log_only / suggest / auto_update
- Stage update confirmation: always / major_only / never
- CRM sync direction: push / pull / bidirectional

---

## Deliverables

- [ ] Gmail OAuth integration
- [ ] Microsoft OAuth integration
- [ ] Email sync service
- [ ] Email analysis pipeline
- [ ] LP communication profiles (aggregated insights)
- [ ] Google Calendar OAuth
- [ ] Microsoft Calendar OAuth
- [ ] Calendar sync service
- [ ] Meeting display in timeline
- [ ] Scheduling link generator
- [ ] LP booking page UI
- [ ] HubSpot integration
- [ ] Salesforce integration
- [ ] User preferences UI
- [ ] Confirmation queue (for suggest mode)

---

## Exit Criteria

- [ ] Connect Gmail -> emails appear in timeline
- [ ] Connect calendar -> meetings appear
- [ ] Generate scheduling link -> LP can book
- [ ] Connect HubSpot -> outreach syncs as deals
- [ ] User can control automation level
- [ ] Live on lpxgp.com

---

## Demo

```
1. Connect Gmail
2. See email thread with LP in timeline
3. Connect calendar
4. Generate scheduling link
5. LP books via link
6. See meeting in calendar + outreach updated
```

---

[← M7: Bidirectional Matching](m7-bidirectional.md) | [Index](index.md) | [M9: IR Advanced →](m9-ir-events.md)
