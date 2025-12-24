## 16. Financial Analyst Role & Data Enrichment

### Overview

A specialized user role for the team of financial experts who continuously improve market data quality.

**Key capabilities:**
1. Full CRUD on market data (companies, people)
2. Prioritized work queue (what the AI needs most)
3. Document upload for extraction (pitch decks, DDQs)
4. Agentic internet scouting integration
5. Human-in-the-loop validation

---

### 16.1 User Roles Updated

| Role | Scope | Capabilities |
|------|-------|--------------|
| **Admin** | System-wide | Everything, including billing, user management |
| **Financial Analyst** | Market data | CRUD on companies/people, data enrichment, document upload |
| **GP User** | Own client | View matches, manage funds, outreach |
| **LP User** | Own client | View matches, manage mandates |
| **Viewer** | Own client | Read-only access |

```sql
-- Updated user roles
ALTER TABLE users
ALTER COLUMN role TYPE TEXT;

-- Role permissions matrix
CREATE TABLE role_permissions (
    role TEXT PRIMARY KEY,
    permissions JSONB NOT NULL
);

INSERT INTO role_permissions VALUES
('admin', '{
    "market_data": "full",
    "clients": "full",
    "users": "full",
    "system": "full",
    "billing": "full"
}'),
('financial_analyst', '{
    "market_data": "full",
    "clients": "read",
    "users": "none",
    "system": "read",
    "billing": "none"
}'),
('member', '{
    "market_data": "none",
    "clients": "own",
    "users": "none",
    "system": "none",
    "billing": "none"
}'),
('viewer', '{
    "market_data": "none",
    "clients": "own_read",
    "users": "none",
    "system": "none",
    "billing": "none"
}');
```

---

### 16.2 Data Enrichment Dashboard

#### What Financial Analysts See

```
┌─────────────────────────────────────────────────────────────────┐
│ 📊 Data Enrichment Dashboard                                    │
│ Welcome back, Maria (Financial Analyst)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ YOUR QUEUE                                          [Refresh]   │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🔴 High Priority (AI needs this for active matches)         │ │
│ │                                                             │ │
│ │ • CalPERS - Missing: allocation percentages, FY end         │ │
│ │   Reason: 3 GP clients matching, critical for scoring       │ │
│ │   [Start Research] [Skip] [Flag as Unavailable]             │ │
│ │                                                             │ │
│ │ • Ontario Teachers - Missing: recent commitments            │ │
│ │   Reason: Timing agent needs deployment pace data           │ │
│ │   [Start Research] [Skip] [Flag as Unavailable]             │ │
│ │                                                             │ │
│ │ • Harvard Management - Outdated: AUM is 2 years old         │ │
│ │   Reason: Fund size scoring may be inaccurate               │ │
│ │   [Start Research] [Skip] [Flag as Unavailable]             │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ 🟡 Medium Priority (12)  │  🟢 Low Priority (47)               │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ QUICK ACTIONS                                                    │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│ │ 📤 Upload   │ │ 🔍 Search   │ │ ➕ Add      │ │ 🤖 Scout    │ │
│ │ Document    │ │ Companies   │ │ Company    │ │ Internet    │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ TODAY'S STATS                                                    │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Records updated: 23  │  Documents processed: 4              │ │
│ │ Scout jobs run: 7    │  Data quality Δ: +2.3%               │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ RECENT ACTIVITY                                                  │
│ • 10:34 - Updated CalPERS allocation data                       │
│ • 10:12 - Processed pitch deck for Acme Growth Fund III         │
│ • 09:45 - Scout found LinkedIn for 3 Ontario contacts           │
│ • 09:30 - Verified Yale Endowment AUM from annual report        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 16.3 Priority Queue System

#### How Priority is Calculated

```python
class DataPriorityCalculator:
    """Calculate which data gaps hurt the AI most."""

    async def calculate_priorities(self) -> list[DataGap]:
        """Return prioritized list of data gaps to fill."""

        gaps = []

        # 1. Find companies in active matches with missing critical fields
        active_match_gaps = await self._get_active_match_gaps()
        for gap in active_match_gaps:
            gap.priority = "high"
            gap.reason = f"{gap.match_count} active matches need this"
            gaps.append(gap)

        # 2. Find companies with low data quality scores
        low_quality = await self._get_low_quality_companies()
        for gap in low_quality:
            gap.priority = "medium"
            gap.reason = f"Data quality score: {gap.quality_score}/100"
            gaps.append(gap)

        # 3. Find stale data (not updated in N months)
        stale = await self._get_stale_data()
        for gap in stale:
            gap.priority = "low"
            gap.reason = f"Last updated: {gap.last_updated}"
            gaps.append(gap)

        return sorted(gaps, key=lambda g: g.priority_score, reverse=True)

    async def _get_active_match_gaps(self) -> list:
        """Find missing data for companies in active GP pipelines."""

        return await db.query("""
            WITH active_lps AS (
                -- LPs that are in active GP pipelines
                SELECT DISTINCT oa.lp_id, COUNT(*) as match_count
                FROM outreach_activities oa
                WHERE oa.stage NOT IN ('passed_by_gp', 'passed_by_lp', 'committed')
                GROUP BY oa.lp_id
            )
            SELECT
                c.id,
                c.name,
                al.match_count,
                -- Check which critical fields are missing
                CASE WHEN c.aum_usd_mm IS NULL THEN 'aum_usd_mm' END,
                CASE WHEN c.lp_type IS NULL THEN 'lp_type' END,
                CASE WHEN c.allocation_pe_pct IS NULL THEN 'allocation_pe_pct' END,
                CASE WHEN c.fiscal_year_end IS NULL THEN 'fiscal_year_end' END
            FROM companies c
            JOIN active_lps al ON c.id = al.lp_id
            WHERE c.aum_usd_mm IS NULL
               OR c.lp_type IS NULL
               OR c.allocation_pe_pct IS NULL
        """)
```

#### Data Model for Queue

```sql
-- Track data enrichment tasks
CREATE TABLE enrichment_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What needs enrichment
    company_id UUID REFERENCES companies(id),
    person_id UUID REFERENCES people(id),

    -- What's missing
    missing_fields TEXT[] NOT NULL,
    reason TEXT,

    -- Priority
    priority TEXT NOT NULL,  -- 'high', 'medium', 'low'
    priority_score NUMERIC,  -- For sorting

    -- Assignment
    assigned_to UUID REFERENCES users(id),
    assigned_at TIMESTAMP,

    -- Status
    status TEXT DEFAULT 'pending',  -- 'pending', 'in_progress', 'completed', 'skipped', 'unavailable'
    completed_at TIMESTAMP,
    completed_by UUID REFERENCES users(id),

    -- Notes
    notes TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);

-- Track enrichment activity
CREATE TABLE enrichment_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),

    -- What was enriched
    company_id UUID REFERENCES companies(id),
    person_id UUID REFERENCES people(id),

    -- What changed
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,

    -- How
    source TEXT,  -- 'manual', 'document_upload', 'scout', 'import'
    source_url TEXT,  -- If from a specific source

    created_at TIMESTAMP DEFAULT NOW()
);
```

---

### 16.4 Document Upload & Extraction

#### Supported Document Types

| Type | Extension | What We Extract |
|------|-----------|-----------------|
| Pitch Deck | PDF, PPTX | Fund name, strategy, size, team, thesis |
| DDQ | PDF, DOCX | Detailed fund/LP info, history, terms |
| Annual Report | PDF | AUM, allocations, commitments, returns |
| LP Profile | PDF | Mandate, preferences, restrictions |
| One-Pager | PDF | Summary info, key contacts |

#### Upload Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 📤 Upload Document                                         [x]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │                                                             │ │
│ │         Drag and drop files here, or click to browse        │ │
│ │                                                             │ │
│ │         Supported: PDF, PPTX, DOCX (max 50MB)              │ │
│ │                                                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ Document Type: [Pitch Deck ▼]                                   │
│                                                                  │
│ Related Company: [Search or create..._______________]           │
│                  └─ Optional: auto-detected from content        │
│                                                                  │
│                                          [Cancel] [Upload]      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Extraction Pipeline

```python
class DocumentExtractor:
    """Extract structured data from uploaded documents."""

    async def process_document(
        self,
        file_path: str,
        doc_type: str,
        related_company_id: UUID | None = None
    ) -> ExtractionResult:
        """Process document and extract relevant data."""

        # 1. Convert to text
        if file_path.endswith('.pdf'):
            text = await self._extract_pdf_text(file_path)
            images = await self._extract_pdf_images(file_path)
        elif file_path.endswith('.pptx'):
            text, images = await self._extract_pptx(file_path)
        elif file_path.endswith('.docx'):
            text = await self._extract_docx_text(file_path)
            images = []

        # 2. Run extraction based on document type
        if doc_type == 'pitch_deck':
            extracted = await self._extract_pitch_deck(text, images)
        elif doc_type == 'ddq':
            extracted = await self._extract_ddq(text)
        elif doc_type == 'annual_report':
            extracted = await self._extract_annual_report(text)
        elif doc_type == 'lp_profile':
            extracted = await self._extract_lp_profile(text)
        else:
            extracted = await self._extract_generic(text)

        # 3. Match to existing company or suggest new
        if related_company_id:
            extracted.company_id = related_company_id
        else:
            extracted.company_match = await self._find_company_match(extracted)

        return extracted

    async def _extract_pitch_deck(self, text: str, images: list) -> dict:
        """Extract fund information from pitch deck."""

        prompt = """
        Extract the following information from this pitch deck:

        FUND INFORMATION:
        - Fund name
        - Fund number (I, II, III, etc.)
        - Target fund size
        - Strategy (buyout, growth, venture, etc.)
        - Geography focus
        - Sector focus
        - Target company size / check size

        GP INFORMATION:
        - Firm name
        - Founded year
        - Team members (names, titles)
        - Track record / prior funds
        - Headquarters location

        THESIS:
        - Investment thesis summary
        - Key differentiators
        - Value-add approach

        Return as JSON with confidence scores (0-1) for each field.
        Mark fields as null if not found in the document.

        DOCUMENT TEXT:
        {text}
        """

        response = await llm.complete(prompt.format(text=text[:50000]))
        return json.loads(response)
```

#### Extraction Review UI

```
┌─────────────────────────────────────────────────────────────────┐
│ 📄 Document Extraction Review                                   │
│ Acme_Growth_Fund_III_Pitch.pdf                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ MATCHED COMPANY                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ● Acme Capital Partners (existing)     Confidence: 95%      │ │
│ │ ○ Create new company                                        │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ EXTRACTED FIELDS                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Field              │ Extracted Value    │ Conf. │ Current   │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ Fund Name          │ Growth Fund III    │ 98%   │ —         │ │
│ │ ✓ Accept                                                    │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ Target Size        │ $500M              │ 92%   │ $450M     │ │
│ │ ○ Accept extracted  ● Keep current  ○ Enter manually: [__] │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ Strategy           │ Growth Equity      │ 95%   │ Growth    │ │
│ │ ✓ Accept (matches current)                                  │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ Geography          │ North America      │ 88%   │ US        │ │
│ │ ○ Accept extracted  ○ Keep current  ● Enter: [US, Canada]  │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ Team Members       │ 4 extracted        │ 75%   │ 2 known   │ │
│ │ [Review team members...]                                    │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ LOW CONFIDENCE EXTRACTIONS (Review carefully)                   │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ First Close Date   │ Q2 2025            │ 45%   │ —         │ │
│ │ ○ Accept  ○ Reject  ○ Enter manually: [__________]         │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ SOURCE DOCUMENT                                      [View PDF] │
│                                                                  │
│                              [Cancel]  [Save Selected Changes]  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 16.5 Agentic Internet Scouting

#### Overview

An autonomous agent system that finds missing data on the internet.

```
Financial Analyst clicks "Scout Internet"
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SCOUT ORCHESTRATOR                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Input: Company "CalPERS", Missing: [allocation_pe_pct, FY_end] │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Web Search  │  │ LinkedIn    │  │ SEC/Filings │              │
│  │ Agent       │  │ Scraper     │  │ Agent       │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│         │                │                │                      │
│         └────────────────┴────────────────┘                      │
│                          │                                       │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ SYNTHESIS AGENT                                             ││
│  │ - Combine findings from all sources                         ││
│  │ - Assess confidence per field                               ││
│  │ - Flag contradictions                                       ││
│  └─────────────────────────────────────────────────────────────┘│
│                          │                                       │
│                          ▼                                       │
│              Findings ready for human review                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Scout Agents

**1. Web Search Agent**
```python
class WebSearchScout:
    """Search the web for company/person information."""

    async def scout(self, entity: Company | Person, missing_fields: list[str]) -> list[Finding]:
        findings = []

        # Generate search queries based on what's missing
        queries = self._generate_queries(entity, missing_fields)

        for query in queries:
            results = await web_search(query)

            for result in results[:5]:  # Top 5 results
                # Fetch and analyze page
                content = await fetch_page(result.url)
                extracted = await self._extract_relevant_data(
                    content,
                    entity,
                    missing_fields
                )

                if extracted:
                    findings.append(Finding(
                        source_url=result.url,
                        source_type='web',
                        data=extracted,
                        confidence=extracted.confidence
                    ))

        return findings

    def _generate_queries(self, entity: Company, missing_fields: list[str]) -> list[str]:
        """Generate search queries for missing data."""

        queries = []
        name = entity.name

        if 'aum_usd_mm' in missing_fields:
            queries.append(f"{name} assets under management")
            queries.append(f"{name} AUM")

        if 'allocation_pe_pct' in missing_fields:
            queries.append(f"{name} private equity allocation")
            queries.append(f"{name} asset allocation")

        if 'fiscal_year_end' in missing_fields:
            queries.append(f"{name} fiscal year")
            queries.append(f"{name} annual report")

        return queries
```

**2. LinkedIn Scout**
```python
class LinkedInScout:
    """Find people and company info from LinkedIn."""

    async def scout_company(self, company: Company) -> list[Finding]:
        """Find company page and extract info."""

        # Search for company on LinkedIn
        company_url = await self._find_company_page(company.name)

        if company_url:
            data = await self._extract_company_data(company_url)
            return [Finding(
                source_url=company_url,
                source_type='linkedin',
                data=data
            )]

        return []

    async def scout_people(self, company: Company) -> list[Finding]:
        """Find key people at the company."""

        findings = []

        # Search for people at company
        people = await self._search_people_at_company(company.name)

        for person in people:
            if self._is_relevant_role(person.title):
                findings.append(Finding(
                    source_url=person.linkedin_url,
                    source_type='linkedin',
                    data={
                        'name': person.name,
                        'title': person.title,
                        'linkedin_url': person.linkedin_url
                    }
                ))

        return findings
```

**3. Regulatory Filings Scout**
```python
class FilingsScout:
    """Search regulatory filings (SEC, pension disclosures, etc.)."""

    async def scout(self, company: Company, missing_fields: list[str]) -> list[Finding]:
        findings = []

        if company.lp_type == 'pension':
            # Search pension disclosure databases
            filings = await self._search_pension_filings(company.name)
        elif company.type == 'gp':
            # Search SEC Form D, ADV
            filings = await self._search_sec_filings(company.name)

        for filing in filings:
            extracted = await self._extract_from_filing(filing, missing_fields)
            if extracted:
                findings.append(Finding(
                    source_url=filing.url,
                    source_type='regulatory_filing',
                    data=extracted,
                    confidence=0.9  # Regulatory = high confidence
                ))

        return findings
```

#### Scout Review UI

```
┌─────────────────────────────────────────────────────────────────┐
│ 🤖 Scout Results: CalPERS                                       │
│ Searched for: allocation_pe_pct, fiscal_year_end                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ FINDINGS (3 sources)                                             │
│                                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 📄 CalPERS 2024 Annual Report (calpers.ca.gov)              │ │
│ │ Confidence: HIGH                                            │ │
│ │                                                             │ │
│ │ • PE Allocation: 13% of total portfolio                     │ │
│ │   [Accept] [Reject]                                         │ │
│ │                                                             │ │
│ │ • Fiscal Year End: June 30                                  │ │
│ │   [Accept] [Reject]                                         │ │
│ │                                                             │ │
│ │ • AUM: $502B (bonus finding!)                               │ │
│ │   [Accept] [Reject]                                         │ │
│ │                                                             │ │
│ │ [View Source]                                               │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🔗 LinkedIn Company Page                                    │ │
│ │ Confidence: MEDIUM                                          │ │
│ │                                                             │ │
│ │ • 3 new contacts found:                                     │ │
│ │   - Sarah Chen, CIO                     [Add to People]     │ │
│ │   - Mike Rodriguez, Head of PE          [Add to People]     │ │
│ │   - Lisa Wang, Senior Investment Officer [Add to People]    │ │
│ │                                                             │ │
│ │ [View Source]                                               │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🌐 Pensions & Investments Article (pionline.com)            │ │
│ │ Confidence: MEDIUM                                          │ │
│ │                                                             │ │
│ │ • PE Allocation: 14% (⚠️ conflicts with annual report)      │ │
│ │   ○ Accept  ● Reject (annual report more authoritative)     │ │
│ │                                                             │ │
│ │ [View Source]                                               │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│                                    [Cancel]  [Apply Selections] │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 16.6 Data Quality Metrics

#### What Financial Analysts Track

```
┌─────────────────────────────────────────────────────────────────┐
│ 📈 Data Quality Dashboard                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ OVERALL QUALITY SCORE                                            │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Companies: ████████████████░░░░ 78%     (+2.1% this week)   │ │
│ │ People:    ████████████░░░░░░░░ 62%     (+0.8% this week)   │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ FIELD COMPLETENESS (Companies)                                   │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Field              │ GPs     │ LPs     │ Overall │ Trend    │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ Name               │ 100%    │ 100%    │ 100%    │ —        │ │
│ │ Type               │ 100%    │ 100%    │ 100%    │ —        │ │
│ │ AUM/Fund Size      │ 72%     │ 81%     │ 77%     │ ↑        │ │
│ │ Strategy           │ 85%     │ —       │ 85%     │ ↑        │ │
│ │ LP Type            │ —       │ 89%     │ 89%     │ →        │ │
│ │ PE Allocation      │ —       │ 45%     │ 45%     │ ↑ 🔴     │ │
│ │ Headquarters       │ 68%     │ 71%     │ 70%     │ ↑        │ │
│ │ Website            │ 82%     │ 76%     │ 79%     │ →        │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ STALENESS                                                        │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Updated < 1 month:  ████████░░ 43%                          │ │
│ │ Updated 1-3 months: ██████░░░░ 31%                          │ │
│ │ Updated 3-12 months:████░░░░░░ 18%                          │ │
│ │ Updated > 1 year:   ██░░░░░░░░ 8%  🔴                       │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ IMPACT ON MATCHING                                               │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ • 23 matches have low-confidence scores due to missing data │ │
│ │ • PE Allocation gap affects 45% of LP match calculations    │ │
│ │ • 12 GPs waiting for LP data enrichment                     │ │
│ │                                                             │ │
│ │ [View Impacted Matches]                                     │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Quality Score Calculation

```python
def calculate_company_quality_score(company: Company) -> float:
    """Calculate data quality score (0-100)."""

    score = 0
    weights = {
        # Critical fields (high weight)
        'name': 10,
        'type': 10,
        'aum_usd_mm': 15,
        'lp_type': 10,  # For LPs
        'strategies': 10,  # For GPs

        # Important fields (medium weight)
        'headquarters_city': 5,
        'headquarters_country': 5,
        'website': 5,
        'allocation_pe_pct': 10,  # For LPs
        'fiscal_year_end': 5,  # For LPs

        # Nice to have (low weight)
        'founded_year': 3,
        'description': 5,
    }

    applicable_weights = 0

    for field, weight in weights.items():
        # Skip fields not applicable to this company type
        if field in ['lp_type', 'allocation_pe_pct', 'fiscal_year_end'] and company.type == 'gp':
            continue
        if field == 'strategies' and company.type == 'lp':
            continue

        applicable_weights += weight

        if getattr(company, field, None):
            score += weight

    # Freshness bonus (up to 7 points)
    if company.last_enriched_at:
        days_since_update = (now() - company.last_enriched_at).days
        if days_since_update < 30:
            score += 7
        elif days_since_update < 90:
            score += 5
        elif days_since_update < 365:
            score += 2

    return (score / (applicable_weights + 7)) * 100
```

---

### 16.7 Financial Analyst Permissions

```sql
-- RLS policies for financial analysts
CREATE POLICY "financial_analysts_read_all_companies" ON companies
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE users.supabase_user_id = auth.uid()
            AND users.role = 'financial_analyst'
        )
    );

CREATE POLICY "financial_analysts_write_all_companies" ON companies
    FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE users.supabase_user_id = auth.uid()
            AND users.role IN ('admin', 'financial_analyst')
        )
    );

-- Same for people table
CREATE POLICY "financial_analysts_full_access_people" ON people
    FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE users.supabase_user_id = auth.uid()
            AND users.role IN ('admin', 'financial_analyst')
        )
    );

-- Financial analysts CANNOT access client billing
CREATE POLICY "no_billing_for_analysts" ON clients
    FOR SELECT
    TO authenticated
    USING (
        -- Admins see everything
        EXISTS (
            SELECT 1 FROM users
            WHERE users.supabase_user_id = auth.uid()
            AND users.role = 'admin'
        )
        OR
        -- Analysts see non-billing fields only
        (
            EXISTS (
                SELECT 1 FROM users
                WHERE users.supabase_user_id = auth.uid()
                AND users.role = 'financial_analyst'
            )
            -- Billing fields filtered out at API level
        )
    );
```

---

### 16.8 Implementation Phases

**Phase 1: Role & Dashboard (M4)**
- Add financial_analyst role
- Basic enrichment dashboard
- Priority queue (manual calculation)
- Simple CRUD with audit log

**Phase 2: Document Upload (M5)**
- PDF/PPTX upload
- AI extraction pipeline
- Human review UI
- Store source documents

**Phase 3: Internet Scouting (M6)**
- Web search agent
- LinkedIn integration
- Regulatory filings search
- Synthesis and conflict detection

**Phase 4: Quality Metrics (M6)**
- Quality score calculation
- Staleness tracking
- Impact analysis
- Team productivity metrics

---

*Section 16 complete. Financial Analyst role and data enrichment workflow documented.*

### Overview

A dedicated role for financial experts who continuously improve market data quality:
- **Financial Analyst** user role with specialized dashboard
- **AI-guided prioritization** of which data fields to work on
- **Agentic internet scouting** to find missing data
- **Document upload** (pitch decks, PDFs) to extract information
- **Human-in-the-loop** validation workflow

---

### 16.1 User Roles Clarification

| Role | Market Data | Client Data | Admin |
|------|-------------|-------------|-------|
| **Admin** | Full CRUD | Full CRUD | Full access |
| **Financial Analyst** | Full CRUD | View only | No access |
| **GP/LP User** | View only (via matching) | Own client only | No access |

#### Financial Analyst Profile

```sql
-- Add to users table or create separate analyst_profiles
CREATE TABLE analyst_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),

    -- Analyst info
    specialization TEXT[],  -- ['pensions', 'endowments', 'europe']
    regions TEXT[],  -- Geographic focus
    languages TEXT[],  -- For international research

    -- Performance tracking
    records_updated_count INTEGER DEFAULT 0,
    data_quality_contribution NUMERIC DEFAULT 0,

    -- Workload
    assigned_companies UUID[],  -- Companies they're responsible for
    current_queue_size INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW()
);
```

---

### 16.2 Analyst Dashboard

#### Main Dashboard View

```
┌─────────────────────────────────────────────────────────────────┐
│ 📊 Data Analyst Dashboard                     Welcome, Sarah    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ YOUR QUEUE                                    AI PRIORITY SCORE │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🔴 High Priority (12)                                       │ │
│ │ ┌─────────────────────────────────────────────────────────┐ │ │
│ │ │ CalPERS         Missing: allocation_pe_pct, mandate     │ │ │
│ │ │                 AI Score: 98  Reason: Active GP match   │ │ │
│ │ │                                         [Work on This]  │ │ │
│ │ ├─────────────────────────────────────────────────────────┤ │ │
│ │ │ Ontario Teachers Missing: fiscal_year_end, check_size   │ │ │
│ │ │                 AI Score: 95  Reason: 3 GPs waiting     │ │ │
│ │ │                                         [Work on This]  │ │ │
│ │ └─────────────────────────────────────────────────────────┘ │ │
│ │                                                             │ │
│ │ 🟡 Medium Priority (34)                           [View All]│ │
│ │ 🟢 Low Priority (156)                             [View All]│ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ QUICK ACTIONS                                                    │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ [📄 Upload Pitch Deck]  [🔍 Research Company]  [➕ Add New] │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ YOUR STATS THIS WEEK                                            │
│ ┌──────────────┬──────────────┬──────────────┬───────────────┐ │
│ │ Records      │ Fields       │ Quality      │ AI Requests   │ │
│ │ Updated: 47  │ Filled: 312  │ Score: +2.3% │ Processed: 23 │ │
│ └──────────────┴──────────────┴──────────────┴───────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### AI Priority Scoring Algorithm

```python
class DataPriorityScorer:
    """Score which records need attention most urgently."""

    async def calculate_priority(self, company_id: UUID) -> dict:
        """Calculate priority score for a company record."""

        score = 0
        reasons = []

        # 1. Is this company in active matching pipelines?
        active_matches = await self._count_active_matches(company_id)
        if active_matches > 0:
            score += 30 * min(active_matches, 5)  # Cap at 150
            reasons.append(f"{active_matches} active GP matches waiting")

        # 2. How many critical fields are missing?
        missing_critical = await self._get_missing_critical_fields(company_id)
        score += 10 * len(missing_critical)
        if missing_critical:
            reasons.append(f"Missing: {', '.join(missing_critical[:3])}")

        # 3. Is this a client company? (higher priority)
        is_client = await self._is_client(company_id)
        if is_client:
            score += 50
            reasons.append("Client company - high priority")

        # 4. How stale is the data?
        staleness_days = await self._get_staleness_days(company_id)
        if staleness_days > 365:
            score += 20
            reasons.append(f"Data is {staleness_days} days old")

        # 5. Data quality score is low
        quality_score = await self._get_quality_score(company_id)
        if quality_score < 50:
            score += 15
            reasons.append(f"Low quality score: {quality_score}%")

        return {
            "score": min(score, 100),  # Cap at 100
            "priority": "high" if score >= 70 else "medium" if score >= 40 else "low",
            "reasons": reasons,
            "missing_fields": missing_critical
        }

    async def _get_missing_critical_fields(self, company_id: UUID) -> list:
        """Get list of critical fields that are missing."""

        company = await db.query_one(
            "SELECT * FROM companies WHERE id = $1", company_id
        )

        missing = []

        # LP critical fields
        if company["type"] in ("lp", "both"):
            critical_lp = [
                ("lp_type", company.get("lp_type")),
                ("aum_usd_mm", company.get("aum_usd_mm")),
                ("allocation_pe_pct", company.get("allocation_pe_pct")),
                ("check_size_min_mm", company.get("check_size_min_mm")),
            ]
            missing.extend([f for f, v in critical_lp if not v])

        # GP critical fields
        if company["type"] in ("gp", "both"):
            critical_gp = [
                ("strategies", company.get("strategies")),
                ("flagship_fund_size_mm", company.get("flagship_fund_size_mm")),
            ]
            missing.extend([f for f, v in critical_gp if not v])

        return missing
```

---

### 16.3 Company Data Editor

When analyst clicks "Work on This":

```
┌─────────────────────────────────────────────────────────────────┐
│ Edit: CalPERS                                    Priority: 🔴 98 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ MISSING FIELDS (AI needs these for matching)                    │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ allocation_pe_pct    [________%]                            │ │
│ │   💡 AI found: "12-15% target PE allocation" (2023 report)  │ │
│ │      Source: calpers.ca.gov/annual-report-2023.pdf          │ │
│ │      [Accept 13.5%] [Research More] [Enter Manually]        │ │
│ │                                                             │ │
│ │ mandate_text         [_________________________________]    │ │
│ │   💡 AI found: No results. Try uploading investment policy. │ │
│ │      [Upload Document] [Research More]                      │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ EXISTING DATA (editable)                                        │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Name:           [CalPERS____________________________]       │ │
│ │ Type:           [LP ▼]                                      │ │
│ │ LP Type:        [Pension ▼]                                 │ │
│ │ AUM:            [$450______] billion                        │ │
│ │ Headquarters:   [Sacramento, CA_____]                       │ │
│ │ Website:        [https://calpers.ca.gov____]                │ │
│ │ Fiscal Year:    [June 30 ▼]                                 │ │
│ │                                                             │ │
│ │ Description:                                                │ │
│ │ [California Public Employees' Retirement System, the       ]│ │
│ │ [largest public pension fund in the US...                  ]│ │
│ │                                                             │ │
│ │ Last Updated: Jan 15, 2024 by Mike                         │ │
│ │ Data Source: Manual + Preqin                               │ │
│ │ Quality Score: ●●●○○ (67%)                                 │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ AI RESEARCH ASSISTANT                                            │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ [🔍 Scout Internet for CalPERS data]                        │ │
│ │                                                             │ │
│ │ Recent findings:                                            │ │
│ │ • Found 2023 annual report (PDF, 142 pages)                │ │
│ │ • Found board meeting minutes (Dec 2024)                   │ │
│ │ • Found investment policy statement                        │ │
│ │                                                             │ │
│ │ [View Findings] [Extract Data from These]                  │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│                              [Cancel] [Save] [Save & Next]      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 16.4 Document Upload & Extraction

#### Upload Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ Upload Document                                            [x]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Document Type:                                                   │
│ (●) Pitch Deck (PDF/PPT)    - Extract GP fund info             │
│ ( ) Annual Report           - Extract LP allocation data        │
│ ( ) Investment Policy       - Extract LP mandate constraints    │
│ ( ) DDQ Response            - Extract fund details              │
│ ( ) Other                   - General extraction                │
│                                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │                                                             │ │
│ │     📄 Drop file here or click to browse                   │ │
│ │                                                             │ │
│ │     Supported: PDF, PPT, PPTX, DOC, DOCX                   │ │
│ │     Max size: 50MB                                         │ │
│ │                                                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ Link to company (optional):                                      │
│ [Search company...________________________] [+ Create New]       │
│                                                                  │
│                                        [Cancel] [Upload & Extract]│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Extraction Results (Human-in-the-Loop)

```
┌─────────────────────────────────────────────────────────────────┐
│ Extraction Results: Acme_Capital_Fund_III_Deck.pdf              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ 📄 Document Preview                    📊 Extracted Data        │
│ ┌───────────────────────┐              ┌──────────────────────┐ │
│ │ [Page 1 thumbnail]    │              │                      │ │
│ │                       │              │ FUND INFORMATION     │ │
│ │ "Acme Capital         │              │ ────────────────────│ │
│ │  Fund III             │              │                      │ │
│ │  $500M Target"        │              │ Fund Name:           │ │
│ │                       │              │ [Acme Capital Fund III]│
│ │ [< Page 1 of 24 >]    │              │ ✓ High confidence    │ │
│ │                       │              │                      │ │
│ └───────────────────────┘              │ Target Size:         │ │
│                                        │ [$500_____] M        │ │
│ AI CONFIDENCE: 87%                     │ ✓ High confidence    │ │
│                                        │                      │ │
│                                        │ Strategy:            │ │
│                                        │ [Growth Equity ▼]    │ │
│                                        │ ⚠ Medium confidence  │ │
│                                        │   (page 3 says       │ │
│                                        │   "growth/buyout")   │ │
│                                        │                      │ │
│                                        │ Geography:           │ │
│                                        │ [x] North America    │ │
│                                        │ [x] Europe           │ │
│                                        │ [ ] Asia             │ │
│                                        │ ✓ High confidence    │ │
│                                        │                      │ │
│                                        │ Sectors:             │ │
│                                        │ [x] Technology       │ │
│                                        │ [x] Healthcare       │ │
│                                        │ [ ] Consumer         │ │
│                                        │ ⚠ Medium confidence  │ │
│                                        │                      │ │
│                                        │ Team (from page 8):  │ │
│                                        │ • John Smith, MP     │ │
│                                        │ • Sarah Chen, Partner│ │
│                                        │ [Edit Team]          │ │
│                                        │                      │ │
│                                        └──────────────────────┘ │
│                                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ⚠ 2 fields need your review (yellow highlights above)       │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ Link to: [Acme Capital_________▼]                               │
│          [+ Create New Company]                                  │
│                                                                  │
│                         [Discard] [Save as Draft] [Apply to DB] │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 16.5 Agentic Internet Research System

#### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                 INTERNET RESEARCH AGENT                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Analyst Request: "Find PE allocation for CalPERS"              │
│                              │                                   │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    RESEARCH ORCHESTRATOR                   │  │
│  │  - Plans search strategy                                   │  │
│  │  - Coordinates specialist agents                           │  │
│  │  - Synthesizes findings                                    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│         ┌────────────────────┼────────────────────┐             │
│         ▼                    ▼                    ▼              │
│  ┌─────────────┐     ┌─────────────┐      ┌─────────────┐       │
│  │ Web Search  │     │ PDF Parser  │      │ News Scanner│       │
│  │ Agent       │     │ Agent       │      │ Agent       │       │
│  │             │     │             │      │             │       │
│  │ - Google    │     │ - Extract   │      │ - Recent    │       │
│  │ - Bing      │     │   tables    │      │   articles  │       │
│  │ - LinkedIn  │     │ - Find key  │      │ - Press     │       │
│  │             │     │   metrics   │      │   releases  │       │
│  └─────────────┘     └─────────────┘      └─────────────┘       │
│         │                    │                    │              │
│         └────────────────────┼────────────────────┘             │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    FINDINGS VALIDATOR                      │  │
│  │  - Cross-reference sources                                 │  │
│  │  - Assign confidence scores                                │  │
│  │  - Flag contradictions                                     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│                     HUMAN REVIEW QUEUE                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Research Agent Implementation

```python
class InternetResearchAgent:
    """Agent that scouts the internet for company data."""

    async def research_company(
        self,
        company_id: UUID,
        target_fields: list[str]
    ) -> ResearchResults:
        """Research missing data for a company."""

        company = await self._get_company(company_id)

        # Plan search strategy
        search_plan = await self._plan_searches(company, target_fields)

        # Execute searches in parallel
        results = await asyncio.gather(*[
            self._execute_search(search)
            for search in search_plan
        ])

        # Find and download relevant documents
        documents = await self._find_documents(company, target_fields)
        doc_extractions = await asyncio.gather(*[
            self._extract_from_document(doc)
            for doc in documents
        ])

        # Synthesize all findings
        synthesized = await self._synthesize_findings(
            company=company,
            target_fields=target_fields,
            search_results=results,
            document_extractions=doc_extractions
        )

        # Validate and score confidence
        validated = await self._validate_findings(synthesized)

        return validated

    async def _plan_searches(
        self,
        company: dict,
        target_fields: list[str]
    ) -> list[SearchPlan]:
        """Plan optimal search strategy."""

        plans = []

        for field in target_fields:
            if field == "allocation_pe_pct":
                plans.append(SearchPlan(
                    query=f"{company['name']} private equity allocation",
                    sources=["google", "company_website"],
                    document_types=["annual_report", "investment_policy"]
                ))

            elif field == "aum_usd_mm":
                plans.append(SearchPlan(
                    query=f"{company['name']} assets under management AUM",
                    sources=["google", "news"],
                    document_types=["annual_report", "press_release"]
                ))

            elif field == "check_size_min_mm":
                plans.append(SearchPlan(
                    query=f"{company['name']} typical commitment size private equity",
                    sources=["preqin_public", "news"],
                    document_types=["investment_policy"]
                ))

        return plans

    async def _find_documents(
        self,
        company: dict,
        target_fields: list[str]
    ) -> list[Document]:
        """Find relevant documents to download and parse."""

        documents = []

        # Try company website first
        website = company.get("website")
        if website:
            # Look for annual reports, investment policies
            pages = await self._crawl_for_documents(
                website,
                patterns=[
                    "*annual*report*",
                    "*investment*policy*",
                    "*allocation*",
                ]
            )
            documents.extend(pages)

        # Search for public filings
        if company.get("lp_type") == "pension":
            # Pensions often have public filings
            filings = await self._search_public_filings(company["name"])
            documents.extend(filings)

        return documents[:5]  # Limit to top 5

    async def _synthesize_findings(
        self,
        company: dict,
        target_fields: list[str],
        search_results: list,
        document_extractions: list
    ) -> dict:
        """Use LLM to synthesize all findings."""

        prompt = f"""
        Synthesize research findings for {company['name']}.

        Target fields to find: {target_fields}

        Search results:
        {json.dumps(search_results, indent=2)}

        Document extractions:
        {json.dumps(document_extractions, indent=2)}

        For each target field, provide:
        1. Best value found
        2. Confidence (high/medium/low)
        3. Source citation
        4. Any conflicting information found

        Return as JSON:
        {{
            "field_name": {{
                "value": "...",
                "confidence": "high|medium|low",
                "source": "URL or document name",
                "source_date": "YYYY-MM-DD if known",
                "conflicts": ["any contradicting info"],
                "notes": "additional context"
            }}
        }}
        """

        response = await llm.complete(prompt, response_format="json")
        return json.loads(response)
```

#### Research Results UI

```
┌─────────────────────────────────────────────────────────────────┐
│ Research Results: CalPERS                           Status: ✓   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ FINDINGS FOR: allocation_pe_pct                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🎯 Recommended Value: 13%                                    │ │
│ │    Confidence: ●●●○○ Medium                                  │ │
│ │                                                              │ │
│ │ Sources Found:                                               │ │
│ │ ┌───────────────────────────────────────────────────────┐   │ │
│ │ │ 1. CalPERS 2023 Annual Report (PDF)                   │   │ │
│ │ │    "Target allocation to Private Equity: 13%"         │   │ │
│ │ │    Page 47, Table 3.2                                 │   │ │
│ │ │    [View Source]                         Confidence: ●●●  │ │
│ │ ├───────────────────────────────────────────────────────┤   │ │
│ │ │ 2. Reuters Article (Nov 2024)                         │   │ │
│ │ │    "CalPERS increased PE target to 13% from 8%"       │   │ │
│ │ │    [View Source]                         Confidence: ●●○  │ │
│ │ ├───────────────────────────────────────────────────────┤   │ │
│ │ │ 3. Board Meeting Minutes (Dec 2024)                   │   │ │
│ │ │    "Approved 13% strategic allocation to PE"          │   │ │
│ │ │    [View Source]                         Confidence: ●●●  │ │
│ │ └───────────────────────────────────────────────────────┘   │ │
│ │                                                              │ │
│ │ ⚠ Note: Previous year (2022) showed 8%. Increase confirmed. │ │
│ │                                                              │ │
│ │ [Accept 13%] [Enter Different Value] [Need More Research]   │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ FINDINGS FOR: check_size_min_mm                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🎯 Recommended Value: $200M minimum                          │ │
│ │    Confidence: ●●○○○ Low                                     │ │
│ │                                                              │ │
│ │ Sources Found:                                               │ │
│ │ ┌───────────────────────────────────────────────────────┐   │ │
│ │ │ 1. Preqin Profile (2023)                              │   │ │
│ │ │    "Typical commitment: $200M - $500M"                │   │ │
│ │ │    [View Source]                         Confidence: ●●○  │ │
│ │ └───────────────────────────────────────────────────────┘   │ │
│ │                                                              │ │
│ │ ❌ Only 1 source found. Recommend manual verification.       │ │
│ │                                                              │ │
│ │ [Accept $200M] [Enter Different Value] [Need More Research] │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 16.6 Data Quality Tracking

```sql
-- Track every change for audit and quality
CREATE TABLE data_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    person_id UUID REFERENCES people(id),

    -- What changed
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,

    -- Who/what made the change
    changed_by UUID REFERENCES users(id),
    change_source TEXT NOT NULL,  -- 'manual', 'ai_research', 'document_extraction', 'import'

    -- Confidence and sourcing
    confidence TEXT,  -- 'high', 'medium', 'low'
    source_url TEXT,
    source_document TEXT,

    -- Validation
    validated_by UUID REFERENCES users(id),
    validated_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW()
);

-- Quality score per company
CREATE TABLE company_quality_scores (
    company_id UUID PRIMARY KEY REFERENCES companies(id),

    -- Overall score (0-100)
    quality_score NUMERIC NOT NULL DEFAULT 0,

    -- Component scores
    completeness_score NUMERIC,  -- % of critical fields filled
    freshness_score NUMERIC,  -- How recent is the data
    source_score NUMERIC,  -- Quality of sources
    validation_score NUMERIC,  -- Has human validated

    -- Tracking
    last_calculated TIMESTAMP DEFAULT NOW(),
    last_updated_by UUID REFERENCES users(id),
    last_updated_at TIMESTAMP
);

-- Analyst performance tracking
CREATE TABLE analyst_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),

    -- Period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    -- Metrics
    records_updated INTEGER DEFAULT 0,
    fields_filled INTEGER DEFAULT 0,
    documents_processed INTEGER DEFAULT 0,
    ai_suggestions_accepted INTEGER DEFAULT 0,
    ai_suggestions_rejected INTEGER DEFAULT 0,
    quality_score_improvement NUMERIC,

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id, period_start)
);
```

---

### 16.7 Analyst Workflow Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                  ANALYST DAILY WORKFLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. CHECK PRIORITY QUEUE                                         │
│     └── AI scores which records need attention                   │
│         └── Based on: matching needs, staleness, missing fields  │
│                                                                  │
│  2. WORK ON HIGH PRIORITY RECORD                                 │
│     ├── View what's missing                                      │
│     ├── Check AI research suggestions                            │
│     │   └── AI has pre-scouted internet for data                │
│     ├── Accept/reject AI findings                                │
│     ├── Or: Research manually                                    │
│     └── Or: Upload document for extraction                       │
│                                                                  │
│  3. VALIDATE & SAVE                                              │
│     ├── Review confidence scores                                 │
│     ├── Add source citations                                     │
│     └── Save and move to next                                    │
│                                                                  │
│  4. BATCH OPERATIONS                                             │
│     ├── Upload multiple pitch decks                              │
│     ├── Bulk research requests                                   │
│     └── Import from CSV/Excel                                    │
│                                                                  │
│  5. END OF DAY                                                   │
│     └── View personal stats and contribution                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 16.8 Files to Create/Update

| File | Purpose |
|------|---------|
| NEW: `docs/mockups/analyst-dashboard.html` | Main analyst view |
| NEW: `docs/mockups/analyst-company-editor.html` | Edit company with AI assist |
| NEW: `docs/mockups/analyst-upload.html` | Document upload flow |
| NEW: `docs/mockups/analyst-research-results.html` | Review AI findings |
| `docs/prd/data-model.md` | Add analyst tables |
| `docs/prd/PRD-v1.md` | Add Financial Analyst role |
| `docs/architecture/agents-implementation.md` | Add research agent architecture |

---

*Section 16 complete. Financial Analyst role and data curation system documented.*

---

