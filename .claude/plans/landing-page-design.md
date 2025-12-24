# LPxGP Landing Page Design

**Goal:** Create a compelling landing page that conveys trust (financial/VC), modernity (AI-powered), and makes app access frictionless.

---

## Design Context

**Existing Brand Assets:**
- Colors: Navy (`#0f172a`) + Gold (`#d4a84b`) + Teal accent (`#0ea5e9`)
- Font: Inter (professional, modern)
- Logo variants: primary, dark, compact
- 30+ app mockups already exist in docs/mockups/

**Platform Nature:**
- B2B SaaS for GP-LP matching
- Invite-only (no public registration)
- Target: Fund managers (GPs) seeking LP investors

---

## Landing Page Sections

*(To discuss and finalize with user)*

### 1. Hero Section ✓
- **Headline:** "Stop Chasing. Start Matching."
- **Subheadline:** "AI-powered intelligence connecting GPs and LPs"
- **Visual:** App screenshot/preview (floating dashboard mockup)
- **Primary CTA:** "Request Demo" (gold button)
- **Secondary CTA:** "Login" (subtle link)

### 2. Problem Statement (For Both Sides)
**For GPs:**
- Manual LP research is time-consuming
- Poor-fit meetings waste everyone's time
- Data scattered across sources

**For LPs:**
- Finding quality emerging managers is hard
- Inbound deal flow is overwhelming
- Due diligence is fragmented

### 3. Solution Overview
- One platform for both sides of the market
- "The Intelligence Layer for Private Markets"

### 4. Key Features (Unified Messaging)
Present as shared benefits:
- **Intelligent Matching** - "Find your ideal partners, not just contacts"
- **Deep Profiles** - "5,000+ verified GP and LP profiles"
- **AI-Powered Insights** - "Every match comes with context"
- **Relationship Tools** - "Track, manage, and nurture connections"

### 5. AI Differentiation (Network Animation)
Visual: Animated network graph showing nodes connecting
- "Multi-perspective analysis" (underlying: Bull vs Bear debate)
- "Semantic understanding" (understands intent, not keywords)
- "Continuous learning" (improves with usage)
- Tagline: "Not just data. Intelligence."

### 6. How It Works
3-4 step visual:
1. Create your profile (GP or LP)
2. AI analyzes and matches
3. Review recommendations with context
4. Connect with confidence

### 7. Trust Signals
- Security: "Bank-grade security" / SOC 2 (future)
- Data quality: "Verified profiles"
- Invite-only: "Curated network"

### 8. Final CTA
- "Ready to transform your fundraising/deal flow?"
- Request Demo button

### 9. Footer
- About, Contact, Privacy, Terms
- Social: LinkedIn (primary for B2B)
- "Invite-only platform" badge

---

## Decisions Made ✓

| Question | Decision |
|----------|----------|
| Hero visual | App screenshot/preview |
| Primary CTA | "Request Demo" |
| Pricing | No pricing shown (contact for pricing) |
| Headline | "Stop Chasing. Start Matching." |
| GP/LP presentation | Unified messaging |
| AI visual | Network/graph animation |

---

## Visual Design

### Color Usage
- **Hero background:** Navy gradient (`#0f172a` → `#020617`)
- **CTAs:** Gold (`#d4a84b`) for primary actions
- **Accents:** Teal (`#0ea5e9`) for highlights
- **Text:** White on dark, Navy on light sections

### Typography
- **Headline:** Inter Bold, 48-64px
- **Subheadline:** Inter Regular, 20-24px
- **Body:** Inter Regular, 16-18px
- **CTAs:** Inter SemiBold, 16px

### Layout
- Full-width sections with max-width container
- Alternating light/dark sections for visual rhythm
- Generous whitespace (financial = sophisticated)

---

## Implementation

### Files to Create
- `docs/mockups/landing.html` - Main landing page
- `docs/mockups/components/network-animation.html` - Reusable AI animation (if needed)

### Assets Needed
- Dashboard screenshot for hero (crop from existing mockups)
- Network animation (CSS/JS or Lottie)
- Icons for features (can use Heroicons)

### Technical Approach
- Static HTML with Tailwind CSS (same as existing mockups)
- CSS animations for network effect
- Responsive design (mobile-first)
- Fast loading (no heavy frameworks)

---

## Page Structure

```
┌─────────────────────────────────────────────────────────────┐
│  HEADER: Logo | Login (right)                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  HERO (dark navy)                                           │
│  ┌────────────────────────┬────────────────────────────┐   │
│  │  Stop Chasing.         │    [Dashboard Preview]      │   │
│  │  Start Matching.       │         floating            │   │
│  │                        │                             │   │
│  │  AI-powered...         │                             │   │
│  │  [Request Demo] Login  │                             │   │
│  └────────────────────────┴────────────────────────────┘   │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  PROBLEM/SOLUTION (light)                                   │
│  "The old way" → "The LPxGP way"                           │
├─────────────────────────────────────────────────────────────┤
│  FEATURES (4 cards, unified messaging)                      │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                          │
│  │Match│ │Prof.│ │AI   │ │Tools│                          │
│  └─────┘ └─────┘ └─────┘ └─────┘                          │
├─────────────────────────────────────────────────────────────┤
│  AI SECTION (dark navy)                                     │
│  [Network Animation]  "Not just data. Intelligence."        │
├─────────────────────────────────────────────────────────────┤
│  HOW IT WORKS (light)                                       │
│  1 ──── 2 ──── 3 ──── 4                                    │
├─────────────────────────────────────────────────────────────┤
│  TRUST SIGNALS                                              │
│  🔒 Secure  ✓ Verified  👥 Curated                         │
├─────────────────────────────────────────────────────────────┤
│  FINAL CTA (gold accent)                                    │
│  "Ready to transform..." [Request Demo]                     │
├─────────────────────────────────────────────────────────────┤
│  FOOTER                                                     │
│  About | Contact | Privacy | Terms | LinkedIn               │
└─────────────────────────────────────────────────────────────┘
```

---

## Status: Ready to Implement

Approved design decisions captured. Ready to create `docs/mockups/landing.html`.
