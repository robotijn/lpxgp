# Agent Monitoring & Observability

This document specifies the monitoring, observability, and prompt versioning strategy for LPxGP's multi-agent system.

## Framework Evaluation

After evaluating the leading 2025 frameworks for LLM observability and prompt versioning, here's our recommendation:

### Framework Comparison

| Framework | Type | Prompt Versioning | Agent Tracing | Self-Hosted | Best For |
|-----------|------|-------------------|---------------|-------------|----------|
| **Langfuse** | Open Source (MIT) | ✅ Full registry | ✅ End-to-end | ✅ Free | Framework-agnostic teams |
| **LangSmith** | Closed Source | ✅ Basic | ✅ Deep LangChain | ❌ Enterprise only | LangChain/LangGraph users |
| **PromptLayer** | Commercial | ✅ Best-in-class | ✅ Good | ❌ | Prompt-focused teams |
| **W&B Weave** | Commercial | ✅ Good | ✅ Good | ❌ | Teams using W&B for ML |
| **Braintrust** | Commercial | ✅ With CI/CD | ✅ Evaluation-first | ❌ | Evaluation-heavy workflows |
| **Helicone** | Open Source | ❌ Limited | ✅ Simple | ✅ Free | Quick setup, cost tracking |

### Recommendation: Langfuse (Primary) + LangSmith (Optional)

**Primary: Langfuse**
- Open source (MIT) - no vendor lock-in
- Self-hostable for data privacy (sensitive LP/GP data)
- Framework-agnostic (works with LangGraph)
- Full prompt management with versioning
- End-to-end tracing for multi-agent debates
- Cost tracking and analytics

**Optional: LangSmith**
- Best integration with LangGraph state machines
- Useful during development for debugging
- Can run alongside Langfuse

---

## Langfuse Integration

### Installation

```bash
uv add langfuse langfuse-langchain
```

### Configuration

```python
# src/agents/config.py
from pydantic_settings import BaseSettings

class AgentSettings(BaseSettings):
    # Langfuse (primary observability)
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_SECRET_KEY: str
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"  # or self-hosted URL

    # Optional: LangSmith for development
    LANGSMITH_API_KEY: str | None = None
    LANGSMITH_PROJECT: str = "lpxgp-agents"

    # Tracing control
    TRACING_ENABLED: bool = True
    TRACE_SAMPLE_RATE: float = 1.0  # 100% in dev, lower in prod

    class Config:
        env_file = ".env"
```

### Tracing Setup

```python
# src/agents/tracing.py
from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context
from functools import wraps
import os

# Initialize Langfuse client
langfuse = Langfuse()

def trace_debate(debate_type: str):
    """Decorator to trace entire debate sessions."""
    def decorator(func):
        @wraps(func)
        @observe(name=func.__name__)
        async def wrapper(*args, **kwargs):
            # Add debate context
            langfuse_context.update_current_trace(
                name=f"{debate_type}_debate",
                metadata={
                    "debate_type": debate_type,
                    "version": kwargs.get("prompt_version", "latest")
                }
            )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def trace_agent(agent_role: str, version: str):
    """Decorator to trace individual agent calls."""
    def decorator(func):
        @wraps(func)
        @observe(name=f"{agent_role}_agent")
        async def wrapper(*args, **kwargs):
            langfuse_context.update_current_observation(
                metadata={
                    "agent_role": agent_role,
                    "agent_version": version
                }
            )
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

---

## Prompt Management with Langfuse

### Prompt Registry Integration

```python
# src/agents/prompts/registry.py
from langfuse import Langfuse
from dataclasses import dataclass
from typing import Optional
import json

langfuse = Langfuse()

@dataclass
class PromptConfig:
    """Configuration for a prompt version."""
    name: str
    version: int
    template: str
    model: str
    temperature: float
    config: dict

class LangfusePromptRegistry:
    """
    Prompt registry using Langfuse for versioning.

    Benefits over custom registry:
    - Visual prompt editor in Langfuse UI
    - Automatic version history
    - A/B testing support
    - Usage analytics per prompt version
    - Rollback capability
    """

    @staticmethod
    def get_prompt(name: str, version: Optional[int] = None) -> PromptConfig:
        """
        Fetch prompt from Langfuse.

        Args:
            name: Prompt name (e.g., "match_bull_agent")
            version: Specific version or None for latest
        """
        prompt = langfuse.get_prompt(
            name=name,
            version=version,  # None = latest production version
            type="chat"  # or "text"
        )

        return PromptConfig(
            name=name,
            version=prompt.version,
            template=prompt.prompt,
            model=prompt.config.get("model", "claude-sonnet-4"),
            temperature=prompt.config.get("temperature", 0.3),
            config=prompt.config
        )

    @staticmethod
    def compile_prompt(name: str, variables: dict, version: Optional[int] = None) -> str:
        """
        Fetch and compile prompt with variables.

        Usage:
            compiled = registry.compile_prompt(
                "match_bull_agent",
                {"fund_data": fund_json, "lp_data": lp_json}
            )
        """
        prompt = langfuse.get_prompt(name=name, version=version)
        return prompt.compile(**variables)
```

### Prompt Organization in Langfuse

```
Langfuse Prompt Library:
├── constraint_interpretation/
│   ├── broad_interpreter      (v1, v2, v3...)
│   ├── narrow_interpreter     (v1, v2...)
│   └── constraint_synthesizer (v1...)
│
├── research_enrichment/
│   ├── research_generator     (v1, v2...)
│   ├── research_critic        (v1...)
│   └── quality_synthesizer    (v1...)
│
├── match_scoring/
│   ├── match_bull_agent       (v1, v2, v3...)
│   ├── match_bear_agent       (v1, v2...)
│   └── match_synthesizer      (v1...)
│
└── pitch_generation/
    ├── pitch_generator        (v1, v2...)
    ├── pitch_critic           (v1...)
    └── content_synthesizer    (v1...)
```

---

## Comprehensive Tracing Architecture

### Trace Hierarchy

```
TRACE (Debate Session)
├── debate_id: uuid
├── debate_type: "match_scoring"
├── entity_id: match_id
├── metadata: {fund_id, lp_id, initiated_by, batch_job_id}
│
├── SPAN: Iteration 1
│   ├── GENERATION: Bull Agent
│   │   ├── prompt_name: "match_bull_agent"
│   │   ├── prompt_version: 3
│   │   ├── input: {fund_data, lp_data, context}
│   │   ├── output: {score, reasoning, talking_points}
│   │   ├── model: "claude-sonnet-4"
│   │   ├── tokens: {input: 2500, output: 800}
│   │   ├── latency_ms: 3200
│   │   └── cost_usd: 0.042
│   │
│   ├── GENERATION: Bear Agent
│   │   └── ... (parallel execution)
│   │
│   └── GENERATION: Synthesizer
│       ├── input: {bull_output, bear_output}
│       ├── output: {final_score, confidence, decision}
│       └── decision: "regenerate" | "complete" | "escalate"
│
├── SPAN: Iteration 2 (if regeneration)
│   └── ... (cross-feedback round)
│
└── SPAN: Final Output
    ├── final_score: 78.5
    ├── confidence: 0.82
    ├── iterations: 2
    └── escalated: false
```

### Implementation

```python
# src/agents/core/traced_graph.py
from langfuse.decorators import observe, langfuse_context
from langgraph.graph import StateGraph
from typing import TypedDict

class MatchDebateState(TypedDict):
    fund_data: dict
    lp_data: dict
    bull_output: dict | None
    bear_output: dict | None
    synthesizer_output: dict | None
    iteration: int
    status: str

@observe(name="match_debate")
async def run_match_debate(fund_id: str, lp_id: str) -> dict:
    """
    Run a complete match debate with full tracing.
    """
    # Set trace metadata
    langfuse_context.update_current_trace(
        name=f"match_debate_{fund_id}_{lp_id}",
        user_id=fund_id,  # GP organization
        session_id=f"batch_{datetime.now().strftime('%Y%m%d')}",
        metadata={
            "fund_id": fund_id,
            "lp_id": lp_id,
            "debate_type": "match_scoring"
        },
        tags=["match_debate", "batch_job"]
    )

    # Load data
    fund_data = await load_fund(fund_id)
    lp_data = await load_lp(lp_id)

    # Build and run graph
    graph = build_match_debate_graph()

    initial_state = MatchDebateState(
        fund_data=fund_data,
        lp_data=lp_data,
        bull_output=None,
        bear_output=None,
        synthesizer_output=None,
        iteration=0,
        status="pending"
    )

    result = await graph.ainvoke(initial_state)

    # Score the trace for evaluation
    langfuse_context.score_current_trace(
        name="debate_quality",
        value=result["synthesizer_output"]["confidence"],
        comment=f"Iterations: {result['iteration']}"
    )

    return result

@observe(name="bull_agent", capture_input=True, capture_output=True)
async def bull_node(state: MatchDebateState) -> dict:
    """Bull agent node with automatic tracing."""
    prompt_config = LangfusePromptRegistry.get_prompt("match_bull_agent")

    # Update observation with prompt version
    langfuse_context.update_current_observation(
        metadata={
            "prompt_version": prompt_config.version,
            "model": prompt_config.model
        }
    )

    # Call LLM (traced automatically)
    response = await call_llm(
        prompt=prompt_config.compile_prompt({
            "fund_data": state["fund_data"],
            "lp_data": state["lp_data"],
            "bear_feedback": state.get("bear_output", {}).get("feedback")
        }),
        model=prompt_config.model,
        temperature=prompt_config.temperature
    )

    return {"bull_output": response}
```

---

## Evaluation & Quality Metrics

### Langfuse Evaluation Datasets

```python
# src/agents/evaluation/datasets.py
from langfuse import Langfuse

langfuse = Langfuse()

def create_match_evaluation_dataset():
    """
    Create evaluation dataset for match scoring quality.

    Dataset includes:
    - Known good matches (LP committed)
    - Known bad matches (LP declined after review)
    - Edge cases (high disagreement, escalated)
    """
    dataset = langfuse.create_dataset(
        name="match_scoring_golden",
        description="Golden dataset for match scoring evaluation",
        metadata={"version": "1.0", "created": "2025-01-15"}
    )

    # Add items from historical outcomes
    golden_matches = get_golden_matches()  # From match_outcomes table

    for match in golden_matches:
        langfuse.create_dataset_item(
            dataset_name="match_scoring_golden",
            input={
                "fund_data": match.fund_data,
                "lp_data": match.lp_data
            },
            expected_output={
                "outcome": match.outcome,  # committed, declined, etc.
                "expected_score_range": match.expected_score_range
            },
            metadata={
                "match_id": str(match.id),
                "outcome_type": match.outcome
            }
        )
```

### Automated Evaluation

```python
# src/agents/evaluation/runner.py
from langfuse import Langfuse

langfuse = Langfuse()

async def evaluate_prompt_version(prompt_name: str, version: int):
    """
    Run evaluation suite against a prompt version.

    Returns metrics comparing this version to production.
    """
    dataset = langfuse.get_dataset("match_scoring_golden")

    for item in dataset.items:
        # Run debate with specific prompt version
        result = await run_match_debate(
            fund_data=item.input["fund_data"],
            lp_data=item.input["lp_data"],
            prompt_version=version
        )

        # Score against expected outcome
        score = calculate_outcome_score(
            predicted_score=result["final_score"],
            expected_outcome=item.expected_output["outcome"]
        )

        # Link run to dataset item
        langfuse.create_dataset_run_item(
            dataset_name="match_scoring_golden",
            dataset_item_id=item.id,
            observation_id=result["trace_id"],
            run_name=f"prompt_v{version}_eval"
        )

        # Record score
        langfuse.score(
            observation_id=result["trace_id"],
            name="outcome_prediction",
            value=score
        )
```

---

## Real-Time Monitoring Dashboard

### Key Metrics to Track

```yaml
# Langfuse Dashboard Configuration

metrics:
  operational:
    - trace_count_by_debate_type
    - average_latency_per_agent
    - token_usage_by_model
    - cost_per_debate
    - error_rate

  quality:
    - score_distribution
    - confidence_distribution
    - disagreement_rate
    - escalation_rate
    - iteration_count_distribution

  business:
    - matches_scored_per_day
    - high_confidence_match_rate
    - prompt_version_performance

alerts:
  - name: high_error_rate
    condition: error_rate > 5%
    notify: slack

  - name: latency_spike
    condition: avg_latency > 10s
    notify: email

  - name: cost_anomaly
    condition: daily_cost > $100
    notify: slack
```

### Custom Analytics Queries

```python
# src/agents/analytics.py
from langfuse import Langfuse
from datetime import datetime, timedelta

langfuse = Langfuse()

def get_agent_performance_report(days: int = 7) -> dict:
    """
    Generate agent performance report for the last N days.

    Uses Langfuse API to aggregate metrics.
    """
    # Query traces
    traces = langfuse.get_traces(
        filter={
            "created_at": {
                "gte": (datetime.now() - timedelta(days=days)).isoformat()
            },
            "tags": ["match_debate"]
        },
        limit=10000
    )

    # Aggregate metrics
    return {
        "total_debates": len(traces),
        "avg_latency_ms": sum(t.latency for t in traces) / len(traces),
        "avg_cost_usd": sum(t.total_cost for t in traces) / len(traces),
        "escalation_rate": sum(1 for t in traces if t.metadata.get("escalated")) / len(traces),
        "avg_iterations": sum(t.metadata.get("iterations", 1) for t in traces) / len(traces),
        "by_prompt_version": aggregate_by_prompt_version(traces),
        "score_distribution": get_score_distribution(traces)
    }
```

---

## A/B Testing Prompts

### Version Rollout Strategy

```python
# src/agents/prompts/ab_testing.py
from langfuse import Langfuse
import random

langfuse = Langfuse()

class PromptABTest:
    """
    A/B test different prompt versions.

    Uses Langfuse to:
    1. Route traffic between versions
    2. Track performance per version
    3. Automatically promote winners
    """

    def __init__(self, prompt_name: str, variants: list[int], weights: list[float]):
        self.prompt_name = prompt_name
        self.variants = variants  # Version numbers
        self.weights = weights    # Traffic weights (must sum to 1.0)

    def select_version(self, entity_id: str) -> int:
        """
        Select prompt version for this entity.
        Uses deterministic hashing for consistency.
        """
        # Same entity always gets same version (for fair comparison)
        hash_val = hash(f"{self.prompt_name}:{entity_id}") % 100

        cumulative = 0
        for variant, weight in zip(self.variants, self.weights):
            cumulative += weight * 100
            if hash_val < cumulative:
                return variant

        return self.variants[-1]  # Fallback

# Usage
bull_agent_ab = PromptABTest(
    prompt_name="match_bull_agent",
    variants=[2, 3],  # Testing v2 vs v3
    weights=[0.5, 0.5]  # 50/50 split
)

async def run_bull_agent(state: MatchDebateState) -> dict:
    version = bull_agent_ab.select_version(state["lp_data"]["id"])
    prompt = LangfusePromptRegistry.get_prompt("match_bull_agent", version=version)
    # ... rest of agent logic
```

---

## Self-Hosted Deployment (Langfuse)

For sensitive financial data, self-host Langfuse:

```yaml
# docker-compose.langfuse.yml
version: "3.8"

services:
  langfuse-server:
    image: ghcr.io/langfuse/langfuse:latest
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/langfuse
      - NEXTAUTH_SECRET=${LANGFUSE_SECRET}
      - NEXTAUTH_URL=https://langfuse.lpxgp.internal
      - SALT=${LANGFUSE_SALT}
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=langfuse
    volumes:
      - langfuse-data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  langfuse-data:
```

### Railway Deployment

```bash
# Deploy Langfuse to Railway (same platform as main app)
railway link
railway add --name langfuse
railway env:set DATABASE_URL=$RAILWAY_DATABASE_URL
railway env:set NEXTAUTH_SECRET=$(openssl rand -hex 32)
railway up
```

---

## Integration Summary

```python
# src/agents/__init__.py
"""
LPxGP Agent System

Observability: Langfuse (MIT open source)
Orchestration: LangGraph
LLM Provider: OpenRouter (Claude, etc.)

Quick Start:
    from agents import run_match_debate

    result = await run_match_debate(fund_id, lp_id)
    # Automatically traced to Langfuse
    # Prompt versions managed in Langfuse UI
    # View at: https://langfuse.lpxgp.com (self-hosted)
"""

from .core.graphs import run_match_debate, run_constraint_debate, run_pitch_debate
from .prompts.registry import LangfusePromptRegistry
from .tracing import langfuse

__all__ = [
    "run_match_debate",
    "run_constraint_debate",
    "run_pitch_debate",
    "LangfusePromptRegistry",
    "langfuse"
]
```

---

## Environment Variables

```bash
# .env.example additions for agents

# Langfuse (Required - Primary Observability)
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=https://cloud.langfuse.com  # or self-hosted URL

# LangSmith (Optional - Development)
LANGSMITH_API_KEY=lsv2_xxx
LANGSMITH_PROJECT=lpxgp-agents

# Agent Configuration
AGENT_TRACING_ENABLED=true
AGENT_TRACE_SAMPLE_RATE=1.0  # 1.0 = 100% in dev
AGENT_MAX_DEBATE_ITERATIONS=3
AGENT_ESCALATION_THRESHOLD=20  # Score disagreement threshold
```

---

## Summary

| Component | Tool | Why |
|-----------|------|-----|
| **Observability** | Langfuse | Open source, self-hostable, full tracing |
| **Prompt Versioning** | Langfuse Prompt Management | Visual editor, version history, A/B testing |
| **Evaluation** | Langfuse Datasets | Automated testing against golden sets |
| **Orchestration** | LangGraph | State machines for debate cycles |
| **Development Debugging** | LangSmith (optional) | Deep LangGraph integration |

### Next Steps

1. Create Langfuse account or deploy self-hosted
2. Upload initial prompts from `agent-prompts.md`
3. Configure tracing in agent code
4. Set up evaluation dataset from historical matches
5. Configure alerting for production monitoring

---

## Sources

Framework comparison research:
- [Best LLM Observability Tools 2025](https://www.firecrawl.dev/blog/best-llm-observability-tools)
- [Top 6 LangSmith Alternatives](https://orq.ai/blog/langsmith-alternatives)
- [9 LangSmith Alternatives](https://mirascope.com/blog/langsmith-alternatives)
- [Best Prompt Versioning Tools 2025](https://www.braintrust.dev/articles/best-prompt-versioning-tools-2025)
- [PromptLayer Platform](https://www.promptlayer.com/)
