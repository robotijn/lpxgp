## 20. Financial Analyst Tooling & External Subscriptions

### Overview

The Financial Analyst role requires external data sources and AI tools to efficiently enrich market data. This section plans the integrations, subscriptions, and agentic workflows.

---

### 20.1 External Data Subscriptions

| Service | Purpose | Cost Tier | Priority |
|---------|---------|-----------|----------|
| **LinkedIn Sales Navigator** | People lookup, company info, job changes | $99-150/mo per seat | High |
| **Perplexity Pro** | AI-powered web research, citation-backed answers | $20/mo per seat | High |
| **Pitchbook** | GP/LP database, fund data, commitments | Enterprise ($$$) | Medium |
| **Preqin** | LP allocations, fund performance | Enterprise ($$$) | Medium |
| **Crunchbase** | Company/startup data, funding rounds | $29-49/mo | Low |
| **Apollo.io** | Email finder, contact enrichment | $49-99/mo | Medium |
| **Clearbit** | Company enrichment API | Pay-per-use | Low |

#### Recommended Starter Stack

**Phase 1 (MVP - $200/mo per analyst):**
- Perplexity Pro ($20/mo) - AI research assistant
- LinkedIn Sales Navigator ($150/mo) - People/company data
- Manual web research for everything else

**Phase 2 (Scale - $500/mo per analyst):**
- Add Apollo.io for email discovery
- Add Crunchbase for startup/VC data
- Consider Pitchbook/Preqin API access

---

### 20.2 Agentic AI Architecture for Data Enrichment

```
┌─────────────────────────────────────────────────────────────────┐
│              FINANCIAL ANALYST AGENTIC SYSTEM                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ANALYST REQUEST: "Enrich CalPERS - need PE allocation, contacts"│
│                              │                                   │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  RESEARCH ORCHESTRATOR                     │  │
│  │  - Analyzes what's missing                                 │  │
│  │  - Plans research strategy                                 │  │
│  │  - Dispatches to specialist agents                         │  │
│  │  - Synthesizes findings                                    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│         ┌────────────────────┼────────────────────┐             │
│         ▼                    ▼                    ▼              │
│  ┌─────────────┐     ┌─────────────┐      ┌─────────────┐       │
│  │ Perplexity  │     │ LinkedIn    │      │ Web Search  │       │
│  │ Agent       │     │ Agent       │      │ Agent       │       │
│  │             │     │             │      │             │       │
│  │ • Factual   │     │ • People    │      │ • Annual    │       │
│  │   research  │     │   lookup    │      │   reports   │       │
│  │ • Citations │     │ • Job titles│      │ • News      │       │
│  │ • Summaries │     │ • Companies │      │ • Filings   │       │
│  └─────────────┘     └─────────────┘      └─────────────┘       │
│         │                    │                    │              │
│         └────────────────────┴────────────────────┘              │
│                              │                                   │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  SYNTHESIS AGENT                           │  │
│  │  - Combines findings from all sources                      │  │
│  │  - Resolves conflicts (source priority)                    │  │
│  │  - Assigns confidence scores                               │  │
│  │  - Formats for human review                                │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│                    HUMAN REVIEW QUEUE                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 20.3 Agent Specifications

#### Perplexity Research Agent

```python
class PerplexityResearchAgent:
    """Uses Perplexity API for factual research with citations."""

    def __init__(self):
        self.api_key = settings.PERPLEXITY_API_KEY
        self.model = "llama-3.1-sonar-large-128k-online"  # Web-connected

    async def research(self, query: str, context: dict) -> ResearchResult:
        """
        Research a specific question about a company/person.

        Examples:
        - "What is CalPERS current private equity allocation percentage?"
        - "When does CalPERS fiscal year end?"
        - "What is the total AUM of Ontario Teachers Pension Plan?"
        """

        prompt = f"""
        Research the following question and provide a factual answer with sources.

        Question: {query}

        Context:
        - Entity: {context.get('entity_name')}
        - Type: {context.get('entity_type')}
        - Known info: {context.get('known_info')}

        Requirements:
        1. Provide the most recent data available
        2. Include source URLs for verification
        3. Note the date of the information
        4. Express confidence level (high/medium/low)
        5. If information is not found, say so explicitly

        Format response as JSON:
        {{
            "answer": "...",
            "value": "...",  // Structured value if applicable
            "sources": [
                {{"url": "...", "title": "...", "date": "..."}}
            ],
            "confidence": "high|medium|low",
            "data_date": "YYYY-MM or YYYY",
            "notes": "..."
        }}
        """

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )

        return self._parse_response(response)
```

#### LinkedIn Agent (via Proxycurl)

```python
class LinkedInAgent:
    """Uses Proxycurl API for LinkedIn data (compliant alternative to scraping)."""

    def __init__(self):
        self.proxycurl_key = settings.PROXYCURL_API_KEY
        # Proxycurl: $0.01/credit, LinkedIn-compliant

    async def find_people_at_company(self, company_name: str) -> list[Person]:
        """Find key decision-makers at a company."""

        # Default titles for LP investment teams
        target_titles = [
            "Chief Investment Officer",
            "Head of Private Equity",
            "Director, Private Markets",
            "Senior Investment Officer",
            "Portfolio Manager"
        ]

        company_url = await self._resolve_company_linkedin(company_name)
        if not company_url:
            return []

        response = await self.client.get(
            "https://nubela.co/proxycurl/api/linkedin/company/employees/",
            params={
                "url": company_url,
                "role_search": ",".join(target_titles),
                "page_size": 20
            }
        )

        return [self._parse_person(p) for p in response.json().get("employees", [])]

    async def enrich_person(self, linkedin_url: str) -> PersonDetails:
        """Get full profile for a person."""

        response = await self.client.get(
            "https://nubela.co/proxycurl/api/v2/linkedin",
            params={"url": linkedin_url}
        )

        data = response.json()
        return PersonDetails(
            full_name=data.get("full_name"),
            title=data.get("occupation"),
            company=data.get("experiences", [{}])[0].get("company"),
            email=data.get("personal_emails", [None])[0],
            linkedin_url=linkedin_url
        )
```

#### Web Search Agent (via Tavily)

```python
class WebSearchAgent:
    """Web search and document extraction."""

    def __init__(self):
        self.tavily_key = settings.TAVILY_API_KEY
        # Tavily: $0.01/search, optimized for AI agents

    async def search_documents(self, company_name: str) -> list[Document]:
        """Find official documents (annual reports, filings)."""

        response = await self.tavily.search(
            query=f"{company_name} annual report private equity allocation PDF",
            search_depth="advanced",
            include_domains=["*.gov", "*.org", "*.edu"],
            max_results=10
        )

        return [Document(
            title=r["title"],
            url=r["url"],
            snippet=r["content"],
            score=r["score"]
        ) for r in response["results"]]

    async def extract_from_pdf(self, url: str, fields: list[str]) -> dict:
        """Download PDF and extract specific fields."""

        # Download
        pdf_bytes = await self._download(url)
        text = await self._pdf_to_text(pdf_bytes)

        # LLM extraction
        prompt = f"""
        Extract these fields from the document:
        {fields}

        Document:
        {text[:50000]}

        Return JSON with field values and page numbers where found.
        """

        return await llm.complete(prompt, response_format="json")
```

---

### 20.4 Research Orchestrator

```python
class ResearchOrchestrator:
    """Coordinates agents for company enrichment."""

    async def enrich_company(self, company: Company, missing_fields: list[str]) -> EnrichmentResult:
        """Full enrichment workflow."""

        # 1. Parallel research
        perplexity_task = self.perplexity.batch_research(company, missing_fields)
        linkedin_task = self.linkedin.find_people_at_company(company.name)
        docs_task = self.web_search.search_documents(company.name)

        perplexity_results, people, docs = await asyncio.gather(
            perplexity_task, linkedin_task, docs_task,
            return_exceptions=True
        )

        # 2. Synthesize findings
        synthesized = await self._synthesize(company, perplexity_results, people, docs)

        # 3. Return for human review
        return EnrichmentResult(
            company_id=company.id,
            field_updates=synthesized.field_updates,
            new_people=synthesized.new_people,
            sources=synthesized.all_sources,
            conflicts=synthesized.conflicts,
            requires_review=synthesized.has_conflicts or synthesized.low_confidence
        )
```

---

### 20.5 API Costs Summary

| Service | Per-Unit Cost | Estimated Monthly (10 analysts) |
|---------|---------------|--------------------------------|
| **Perplexity API** | $5/1000 queries | $200-500 |
| **Proxycurl** | $0.01/profile | $100-300 |
| **Tavily** | $0.01/search | $50-100 |
| **LLM (synthesis)** | $3-15/1M tokens | $200-500 |
| **Subscriptions** | — | $1,700 (LinkedIn + Perplexity Pro) |
| **Total** | | **~$2,500-3,500/mo** |

---

### 20.6 Source Authority Ranking

When sources conflict:

| Tier | Sources | Auto-Accept? |
|------|---------|--------------|
| **1 - Definitive** | Official annual reports, regulatory filings | Yes |
| **2 - Highly Reliable** | Company website, Bloomberg, Reuters | Yes with note |
| **3 - Reliable** | Preqin, Pitchbook, LinkedIn, WSJ | Review if conflict |
| **4 - Supplementary** | General web, Wikipedia | Never auto-accept |

---

### 20.7 Implementation Phases

| Phase | Scope | Duration |
|-------|-------|----------|
| **1** | Perplexity Pro (manual), basic UI | Week 1-2 |
| **2** | Perplexity API integration | Week 3-4 |
| **3** | LinkedIn/Proxycurl integration | Week 5-6 |
| **4** | Web search + PDF extraction | Week 7-8 |
| **5** | Full orchestration | Week 9-10 |

---

*Section 20 complete. Financial Analyst tooling and external subscriptions planned.*
