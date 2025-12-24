# AI Agent Architecture

[Back to TRD Index](index.md)

---

## Overview

LPxGP uses a multi-agent debate architecture to generate high-quality, defensible AI outputs. Agents argue opposing perspectives, then synthesize consensus positions.

---

## Agent System Design

### 42-Agent Architecture

The system comprises **42 agents** organized into **14 debate teams**, each with 3 agents:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         42-AGENT ARCHITECTURE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DEBATE PATTERN (3 agents per team):                                         │
│                                                                              │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                   │
│  │   AGENT A   │────▶│   AGENT B   │────▶│ SYNTHESIZER │                   │
│  │  (One view) │◀────│(Opposing)   │◀────│ (Consensus) │                   │
│  └─────────────┘     └─────────────┘     └──────┬──────┘                   │
│         │                   │                    │                          │
│         └───────────────────┴───────Cross-feedback (if disagreement)        │
│                                                  │                          │
│                                                  ▼                          │
│                                        ┌─────────────────┐                  │
│                                        │ Final Decision  │                  │
│                                        │ or Escalation   │                  │
│                                        └─────────────────┘                  │
│                                                                              │
│  14 DEBATE TEAMS:                                                            │
│  ━━━━━━━━━━━━━━━━                                                           │
│                                                                              │
│  CONSTRAINT INTERPRETATION (3 teams = 9 agents)                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Team 1: LP Mandate Interpretation                                       ││
│  │   - Broad Interpreter (find flexibility)                                ││
│  │   - Narrow Interpreter (find constraints)                               ││
│  │   - Constraint Synthesizer                                              ││
│  │                                                                          ││
│  │ Team 2: GP Strategy Interpretation                                      ││
│  │   - Thesis Expander (broad interpretation)                              ││
│  │   - Thesis Refiner (narrow focus)                                       ││
│  │   - Strategy Synthesizer                                                ││
│  │                                                                          ││
│  │ Team 3: Regulatory Compliance                                           ││
│  │   - Permissive Interpreter                                              ││
│  │   - Conservative Interpreter                                            ││
│  │   - Compliance Synthesizer                                              ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  RESEARCH & ENRICHMENT (3 teams = 9 agents)                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Team 4: LP Research                                                     ││
│  │   - Research Generator (find information)                               ││
│  │   - Research Critic (validate sources)                                  ││
│  │   - Quality Synthesizer                                                 ││
│  │                                                                          ││
│  │ Team 5: GP Research                                                     ││
│  │   - Track Record Researcher                                             ││
│  │   - Track Record Validator                                              ││
│  │   - Track Record Synthesizer                                            ││
│  │                                                                          ││
│  │ Team 6: Market Intelligence                                             ││
│  │   - Trend Analyzer                                                      ││
│  │   - Trend Skeptic                                                       ││
│  │   - Market Synthesizer                                                  ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  MATCH SCORING (4 teams = 12 agents)                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Team 7: Strategy Alignment                                              ││
│  │   - Strategy Bull (argue for alignment)                                 ││
│  │   - Strategy Bear (argue against)                                       ││
│  │   - Strategy Synthesizer                                                ││
│  │                                                                          ││
│  │ Team 8: Timing Analysis                                                 ││
│  │   - Timing Optimist                                                     ││
│  │   - Timing Skeptic                                                      ││
│  │   - Timing Synthesizer                                                  ││
│  │                                                                          ││
│  │ Team 9: Relationship Potential                                          ││
│  │   - Relationship Builder                                                ││
│  │   - Relationship Barrier Finder                                         ││
│  │   - Relationship Synthesizer                                            ││
│  │                                                                          ││
│  │ Team 10: Overall Match                                                  ││
│  │   - Match Bull (overall optimist)                                       ││
│  │   - Match Bear (overall skeptic)                                        ││
│  │   - Match Synthesizer                                                   ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  CONTENT GENERATION (4 teams = 12 agents)                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Team 11: Email Pitch                                                    ││
│  │   - Email Generator                                                     ││
│  │   - Email Critic                                                        ││
│  │   - Email Synthesizer                                                   ││
│  │                                                                          ││
│  │ Team 12: Executive Summary                                              ││
│  │   - Summary Generator                                                   ││
│  │   - Summary Critic                                                      ││
│  │   - Summary Synthesizer                                                 ││
│  │                                                                          ││
│  │ Team 13: Meeting Prep                                                   ││
│  │   - Prep Generator                                                      ││
│  │   - Prep Critic                                                         ││
│  │   - Prep Synthesizer                                                    ││
│  │                                                                          ││
│  │ Team 14: Follow-up Content                                              ││
│  │   - Followup Generator                                                  ││
│  │   - Followup Critic                                                     ││
│  │   - Followup Synthesizer                                                ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## LangGraph State Machines

### Framework Choice

| Framework | Purpose | Why Chosen |
|-----------|---------|------------|
| **LangGraph** | Agent orchestration | State machines, cycles, parallel execution |
| **Langfuse** | Monitoring | Open source, self-hostable, prompt versioning |
| **OpenRouter** | LLM access | Multi-model (Claude, GPT, open models) |

### State Machine Pattern

```python
# src/agents/core/state.py
from typing import TypedDict, Annotated, Sequence
from langgraph.graph.message import add_messages

class DebateState(TypedDict):
    """Base state for all debates."""

    # Input data
    entity_data: dict
    context: dict

    # Debate tracking
    debate_id: str
    iteration: int
    max_iterations: int

    # Agent outputs (accumulated across iterations)
    agent_a_outputs: Annotated[Sequence[dict], add_messages]
    agent_b_outputs: Annotated[Sequence[dict], add_messages]
    synthesizer_outputs: Annotated[Sequence[dict], add_messages]

    # Current round
    current_a: dict | None
    current_b: dict | None
    current_synthesis: dict | None

    # Cross-feedback for regeneration
    a_feedback: dict | None
    b_feedback: dict | None

    # Final results
    final_output: dict | None
    confidence: float | None
    disagreement: float | None

    # Status
    status: str  # pending, debating, synthesizing, completed, escalated
    requires_escalation: bool
    escalation_reason: str | None

    # Metrics
    total_tokens: int
    errors: list[str]
```

### Graph Builder

```python
# src/agents/core/graphs.py
from langgraph.graph import StateGraph, END

def build_debate_graph(
    agent_a_node,
    agent_b_node,
    synthesizer_node,
    disagreement_threshold: float = 20.0,
    max_iterations: int = 3,
):
    """
    Build a generic debate graph.

    Flow:
    1. Agent A and Agent B run (can be parallel)
    2. Synthesizer combines perspectives
    3. Check disagreement:
       - Low: Complete
       - High + iterations left: Regenerate with cross-feedback
       - High + no iterations: Escalate
    """
    builder = StateGraph(DebateState)

    # Add nodes
    builder.add_node("agent_a", agent_a_node)
    builder.add_node("agent_b", agent_b_node)
    builder.add_node("synthesize", synthesizer_node)
    builder.add_node("prepare_regen", prepare_regeneration)
    builder.add_node("escalate", escalate_to_human)
    builder.add_node("complete", mark_complete)

    # Entry: both agents can run in parallel
    builder.set_entry_point("agent_a")
    builder.add_edge("agent_a", "agent_b")  # Sequential for simplicity
    builder.add_edge("agent_b", "synthesize")

    # Conditional routing after synthesis
    builder.add_conditional_edges(
        "synthesize",
        should_continue,
        {
            "complete": "complete",
            "regenerate": "prepare_regen",
            "escalate": "escalate",
        }
    )

    # Regeneration loops back
    builder.add_edge("prepare_regen", "agent_a")

    # Terminal states
    builder.add_edge("complete", END)
    builder.add_edge("escalate", END)

    return builder.compile()

def should_continue(state: DebateState) -> str:
    """Determine next step based on synthesis result."""
    if state["requires_escalation"]:
        return "escalate"

    if state["disagreement"] <= 20:
        return "complete"

    if state["iteration"] >= state["max_iterations"]:
        return "escalate"

    return "regenerate"
```

---

## Debate Team Details

### Team 10: Match Scoring (Primary Example)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     MATCH SCORING DEBATE FLOW                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  INPUT                                                                       │
│  ┌───────────────┐     ┌───────────────┐                                   │
│  │  Fund Profile │     │  LP Profile   │                                   │
│  │  - Strategy   │     │  - Mandate    │                                   │
│  │  - Thesis     │     │  - Strategies │                                   │
│  │  - Track rec  │     │  - Check size │                                   │
│  │  - Team       │     │  - History    │                                   │
│  └───────┬───────┘     └───────┬───────┘                                   │
│          │                     │                                            │
│          └─────────┬───────────┘                                            │
│                    ▼                                                         │
│  ITERATION 1                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  ┌─────────────┐                     ┌─────────────┐                │   │
│  │  │ BULL AGENT  │                     │ BEAR AGENT  │                │   │
│  │  │             │                     │             │                │   │
│  │  │ Score: 78   │                     │ Score: 52   │                │   │
│  │  │ "Strategy   │                     │ "Fund size  │                │   │
│  │  │  aligns on  │                     │  too small, │                │   │
│  │  │  growth     │                     │  track rec  │                │   │
│  │  │  equity..."│                     │  gaps..."   │                │   │
│  │  └──────┬──────┘                     └──────┬──────┘                │   │
│  │         │                                    │                       │   │
│  │         └────────────┬───────────────────────┘                       │   │
│  │                      ▼                                                │   │
│  │            ┌─────────────────┐                                       │   │
│  │            │   SYNTHESIZER   │                                       │   │
│  │            │                 │                                       │   │
│  │            │ Disagreement:26 │ ◀─── > 20, needs regeneration        │   │
│  │            │ Confidence: 0.6 │                                       │   │
│  │            └────────┬────────┘                                       │   │
│  │                     │                                                 │   │
│  │                     ▼                                                 │   │
│  │            DECISION: REGENERATE                                      │   │
│  │            Cross-feedback prepared                                   │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                    │                                                         │
│                    ▼                                                         │
│  ITERATION 2                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  ┌─────────────┐                     ┌─────────────┐                │   │
│  │  │ BULL AGENT  │                     │ BEAR AGENT  │                │   │
│  │  │             │                     │             │                │   │
│  │  │ Score: 72   │ (adjusted down     │ Score: 60   │ (adjusted up   │   │
│  │  │ after       │  after considering │ after       │  after Bull's  │   │
│  │  │ Bear's      │  Bear's concerns)  │ Bull's      │  arguments)    │   │
│  │  │ feedback)   │                     │ feedback)   │                │   │
│  │  └──────┬──────┘                     └──────┬──────┘                │   │
│  │         │                                    │                       │   │
│  │         └────────────┬───────────────────────┘                       │   │
│  │                      ▼                                                │   │
│  │            ┌─────────────────┐                                       │   │
│  │            │   SYNTHESIZER   │                                       │   │
│  │            │                 │                                       │   │
│  │            │ Disagreement:12 │ ◀─── < 20, consensus reached          │   │
│  │            │ Confidence: 0.8 │                                       │   │
│  │            │ Final Score: 66 │                                       │   │
│  │            └────────┬────────┘                                       │   │
│  │                     │                                                 │   │
│  │                     ▼                                                 │   │
│  │            DECISION: COMPLETE                                        │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                    │                                                         │
│                    ▼                                                         │
│  OUTPUT                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Final Score: 66/100                                                 │   │
│  │  Confidence: 0.82                                                    │   │
│  │  Recommendation: "investigate"                                       │   │
│  │                                                                      │   │
│  │  Talking Points:                                                     │   │
│  │  1. Lead with growth equity thesis alignment                         │   │
│  │  2. Emphasize operating experience (mitigates fund size concern)    │   │
│  │  3. Reference LP's emerging manager commitment                       │   │
│  │                                                                      │   │
│  │  Concerns to Address:                                                │   │
│  │  1. Fund size at lower end of LP range - prepare justification      │   │
│  │  2. Track record limited - emphasize team tenure                    │   │
│  │                                                                      │   │
│  │  Iterations: 2                                                       │   │
│  │  Tokens Used: 8,450                                                  │   │
│  │  Debate ID: abc123                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Prompts

### Prompt Versioning

All prompts are versioned and managed in Langfuse:

```
Version: X.Y.Z
- X (Major): Breaking changes to output schema
- Y (Minor): Significant prompt improvements
- Z (Patch): Wording tweaks, typo fixes
```

### Bull Agent (v1.1.0) - Abbreviated

```python
BULL_AGENT = """You are the BULL AGENT analyzing a potential match.

## YOUR MISSION
Argue FOR this match. Find the best reasons why it could succeed.

## FUND PROFILE
{fund_profile}

## LP PROFILE
{lp_profile}

{cross_feedback_section}

## OUTPUT (JSON)
{
    "overall_score": <0-100>,
    "confidence": <0.0-1.0>,
    "strategy_alignment": { ... },
    "timing_opportunity": { ... },
    "hidden_strengths": [...],
    "talking_points": [...],
    "acknowledged_concerns": [...],
    "response_to_bear": "...",
    "reasoning": "..."
}

Be specific. Cite data points. Don't inflate scores.
"""
```

### Bear Agent (v1.1.0) - Abbreviated

```python
BEAR_AGENT = """You are the BEAR AGENT analyzing a potential match.

## YOUR MISSION
Critically examine this match. Find reasons why it might fail.

## FUND PROFILE
{fund_profile}

## LP PROFILE
{lp_profile}

{cross_feedback_section}

## OUTPUT (JSON)
{
    "overall_score": <0-100>,
    "confidence": <0.0-1.0>,
    "hard_constraints_violated": [...],
    "soft_concerns": [...],
    "timing_issues": { ... },
    "risk_factors": [...],
    "acknowledged_positives": [...],
    "hard_exclusion": <boolean>,
    "response_to_bull": "...",
    "reasoning": "..."
}

Be skeptical but fair. Check hard constraints carefully.
"""
```

See [agent-prompts.md](../architecture/agent-prompts.md) for complete prompt specifications.

---

## Langfuse Monitoring Integration

### Tracing Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LANGFUSE TRACE HIERARCHY                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TRACE (Debate Session)                                                      │
│  ├── debate_id: uuid                                                         │
│  ├── debate_type: "match_scoring"                                           │
│  ├── fund_id, lp_id                                                         │
│  │                                                                           │
│  ├── SPAN: Iteration 1                                                       │
│  │   ├── GENERATION: Bull Agent                                             │
│  │   │   ├── prompt_name: "match_bull_agent"                                │
│  │   │   ├── prompt_version: 3                                              │
│  │   │   ├── input: {...}                                                   │
│  │   │   ├── output: {...}                                                  │
│  │   │   ├── tokens: {input: 2500, output: 800}                             │
│  │   │   ├── latency_ms: 3200                                               │
│  │   │   └── cost_usd: 0.042                                                │
│  │   │                                                                       │
│  │   ├── GENERATION: Bear Agent                                             │
│  │   │   └── ... (similar structure)                                        │
│  │   │                                                                       │
│  │   └── GENERATION: Synthesizer                                            │
│  │       └── decision: "regenerate"                                         │
│  │                                                                           │
│  ├── SPAN: Iteration 2                                                       │
│  │   └── ... (with cross-feedback)                                          │
│  │                                                                           │
│  └── SPAN: Final Output                                                      │
│      ├── final_score: 66                                                     │
│      ├── confidence: 0.82                                                    │
│      └── iterations: 2                                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Integration Code

```python
# src/agents/tracing.py
from langfuse.decorators import observe, langfuse_context

@observe(name="match_debate")
async def run_match_debate(fund_id: str, lp_id: str) -> dict:
    """Run debate with full Langfuse tracing."""

    langfuse_context.update_current_trace(
        name=f"match_debate_{fund_id}_{lp_id}",
        metadata={
            "fund_id": fund_id,
            "lp_id": lp_id,
            "debate_type": "match_scoring"
        },
        tags=["match_debate", "production"]
    )

    # Graph execution - all steps traced
    result = await match_debate_graph.ainvoke(initial_state)

    # Score the trace
    langfuse_context.score_current_trace(
        name="debate_quality",
        value=result["confidence"],
        comment=f"Iterations: {result['iteration']}"
    )

    return result
```

---

## Prompt A/B Testing

```python
# src/agents/ab_testing.py
class PromptABTest:
    """A/B test different prompt versions."""

    def __init__(self, prompt_name: str, variants: list[int], weights: list[float]):
        self.prompt_name = prompt_name
        self.variants = variants
        self.weights = weights

    def select_version(self, entity_id: str) -> int:
        """Deterministic version selection for fair comparison."""
        # Same entity always gets same version
        hash_val = hash(f"{self.prompt_name}:{entity_id}") % 100

        cumulative = 0
        for variant, weight in zip(self.variants, self.weights):
            cumulative += weight * 100
            if hash_val < cumulative:
                return variant

        return self.variants[-1]

# Usage
bull_ab = PromptABTest(
    prompt_name="match_bull_agent",
    variants=[2, 3],  # v2 vs v3
    weights=[0.5, 0.5]  # 50/50 split
)
```

---

## Batch Processing

Debates run as **nightly batch jobs**, with results cached for instant retrieval:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BATCH PROCESSING                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SCHEDULE                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  2:00 AM UTC: Nightly full batch                                     │   │
│  │  Every 4h: Incremental updates (changed entities only)              │   │
│  │  On-demand: Entity-specific triggers (via webhook)                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  FLOW                                                                        │
│                                                                              │
│  ┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────┐       │
│  │ Identify│────▶│ Queue       │────▶│ Run Debates │────▶│ Cache   │       │
│  │ Changes │     │ Debates     │     │ (parallel)  │     │ Results │       │
│  └─────────┘     └─────────────┘     └─────────────┘     └─────────┘       │
│                                                                              │
│  CACHE LIFETIME                                                              │
│  - Match results: Valid until entity changes (months)                       │
│  - Pitches: Valid until match or entity changes                             │
│  - Constraints: Valid until mandate changes                                 │
│                                                                              │
│  INVALIDATION TRIGGERS                                                       │
│  - Fund updated → Invalidate all fund's matches                             │
│  - LP updated → Invalidate all LP's matches                                 │
│  - LP mandate changed → Re-run constraint interpretation                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

See [batch-processing.md](../architecture/batch-processing.md) for implementation details.

---

## Escalation Handling

When agents cannot reach consensus:

```python
# Escalation criteria
ESCALATION_TRIGGERS = {
    "high_disagreement": lambda s: s["disagreement"] > 30,
    "low_confidence": lambda s: s["confidence"] < 0.5,
    "hard_exclusion": lambda s: s["current_b"].get("hard_exclusion"),
    "max_iterations": lambda s: s["iteration"] >= s["max_iterations"],
}

# Escalation record
async def escalate_to_human(state: DebateState) -> dict:
    await supabase.table("agent_escalations").insert({
        "debate_id": state["debate_id"],
        "escalation_type": determine_type(state),
        "priority": determine_priority(state),
        "summary": state["escalation_reason"],
        "debate_transcript": {
            "agent_a_outputs": state["agent_a_outputs"],
            "agent_b_outputs": state["agent_b_outputs"],
        },
    }).execute()

    return {"status": "escalated"}
```

---

## Model Selection

| Use Case | Model | Why |
|----------|-------|-----|
| **Debate agents** | Claude Sonnet 4 | Best reasoning, structured output |
| **Synthesizers** | Claude Sonnet 4 | Needs nuanced judgment |
| **Simple extraction** | Claude Haiku | Fast, cheap |
| **Embeddings** | Voyage AI | Best for financial domain |

```python
# Model routing
def select_model(agent_type: str) -> str:
    model_map = {
        "bull_agent": "anthropic/claude-sonnet-4-20250514",
        "bear_agent": "anthropic/claude-sonnet-4-20250514",
        "synthesizer": "anthropic/claude-sonnet-4-20250514",
        "extractor": "anthropic/claude-3-5-haiku-20241022",
    }
    return model_map.get(agent_type, "anthropic/claude-sonnet-4-20250514")
```

---

## Dependencies

```toml
[project.dependencies]
# LangChain ecosystem
langchain = ">=0.3.0"
langchain-anthropic = ">=0.3.0"
langgraph = ">=0.2.0"
langfuse = ">=2.0.0"

# Async support
aiohttp = ">=3.9.0"
```

---

## Related Documents

- [Agent Prompts](../architecture/agent-prompts.md) - Complete versioned prompts
- [Batch Processing](../architecture/batch-processing.md) - Scheduler and cache
- [Monitoring](../architecture/monitoring-observability.md) - Langfuse integration
