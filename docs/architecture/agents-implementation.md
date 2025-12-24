# Agent Implementation Architecture

This document specifies the implementation details for the LPxGP multi-agent debate system.

## Related Documentation

| Document | Purpose |
|----------|---------|
| [agent-prompts.md](agent-prompts.md) | Complete versioned prompts for all 42 agents (14 teams) |
| [batch-processing.md](batch-processing.md) | Scheduler, processor, and cache management |
| [monitoring-observability.md](monitoring-observability.md) | Langfuse integration, evaluation, A/B testing |

## Framework Choice: LangGraph + Langfuse

| Framework | Purpose | Why |
|-----------|---------|-----|
| **LangGraph** | Agent orchestration | State machines, cycles, parallel execution, built-in persistence |
| **Langfuse** | Monitoring & observability | Open source, self-hostable, full tracing, prompt versioning |
| **LangChain** | LLM abstraction | Model switching, prompt templates, structured outputs |
| **LangSmith** | Development debugging (optional) | Deep LangGraph integration for development |

**Why Langfuse over LangSmith as primary?**
- Open source (MIT license) - no vendor lock-in
- Self-hostable for sensitive financial data (LP/GP information)
- Framework-agnostic (works with LangGraph, not LangChain-only)
- Full prompt management with versioning and A/B testing
- See [monitoring-observability.md](monitoring-observability.md) for detailed comparison

**Why not CrewAI?**
- LangGraph has more mature monitoring integration
- Better state management for debate cycles
- More control over agent interactions

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH AGENT ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    LANGFUSE (Open Source)                           │    │
│  │  - Full trace inspection for every debate                           │    │
│  │  - Agent conversation history                                       │    │
│  │  - Token usage, latency, cost tracking                              │    │
│  │  - Prompt versioning and A/B testing                                │    │
│  │  - Evaluation datasets and feedback                                 │    │
│  │  - Self-hostable for data privacy                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      LANGGRAPH STATE MACHINE                         │    │
│  │                                                                      │    │
│  │   ┌──────────┐     ┌──────────┐     ┌───────────┐                   │    │
│  │   │  START   │────▶│  DEBATE  │────▶│ SYNTHESIZE│                   │    │
│  │   └──────────┘     └────┬─────┘     └─────┬─────┘                   │    │
│  │                         │                  │                         │    │
│  │                         │      ┌───────────┴───────────┐            │    │
│  │                         │      │     disagreement?      │            │    │
│  │                         │      └───────────┬───────────┘            │    │
│  │                         │                  │                         │    │
│  │            ┌────────────┼──────────────────┼────────────┐           │    │
│  │            ▼            ▼                  ▼            ▼           │    │
│  │       ┌────────┐   ┌────────┐       ┌──────────┐  ┌──────────┐     │    │
│  │       │COMPLETE│   │REGEN   │       │ ESCALATE │  │   END    │     │    │
│  │       └────────┘   └────┬───┘       └──────────┘  └──────────┘     │    │
│  │                         │                                           │    │
│  │                         └──────────▶ back to DEBATE                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         AGENTS (Versioned)                           │    │
│  │                                                                      │    │
│  │  v1.2.0 BullAgent    v1.2.0 BearAgent    v1.1.0 Synthesizer         │    │
│  │       │                     │                    │                   │    │
│  │       └─────────────────────┴────────────────────┘                   │    │
│  │                             │                                        │    │
│  │                     PromptRegistry (versioned)                       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
src/agents/
├── __init__.py
├── config.py                  # Agent configuration, model selection
├── registry.py                # Prompt versioning registry
│
├── core/                      # Core LangGraph components
│   ├── __init__.py
│   ├── state.py               # State definitions for each debate type
│   ├── nodes.py               # Graph nodes (agent execution)
│   ├── edges.py               # Conditional edges (routing logic)
│   └── graphs.py              # Graph builders for each debate type
│
├── agents/                    # Individual agents
│   ├── __init__.py
│   ├── base.py                # Base agent class with LangSmith integration
│   │
│   ├── constraint/
│   │   ├── __init__.py
│   │   ├── broad_interpreter.py
│   │   ├── narrow_interpreter.py
│   │   └── synthesizer.py
│   │
│   ├── research/
│   │   ├── __init__.py
│   │   ├── generator.py
│   │   ├── critic.py
│   │   └── synthesizer.py
│   │
│   ├── matching/
│   │   ├── __init__.py
│   │   ├── bull.py
│   │   ├── bear.py
│   │   └── synthesizer.py
│   │
│   └── pitch/
│       ├── __init__.py
│       ├── generator.py
│       ├── critic.py
│       └── synthesizer.py
│
├── prompts/                   # Versioned prompts
│   ├── __init__.py
│   ├── v1/                    # Version 1 prompts
│   │   ├── bull.py
│   │   ├── bear.py
│   │   └── ...
│   └── v2/                    # Version 2 prompts (experimental)
│       └── ...
│
├── monitoring/                # Observability
│   ├── __init__.py
│   ├── langsmith.py           # LangSmith setup
│   ├── metrics.py             # Custom metrics
│   └── callbacks.py           # Event callbacks
│
└── batch/                     # Batch processing
    ├── __init__.py
    ├── scheduler.py
    └── processor.py
```

---

## LangSmith Integration (Full Inspection)

### Setup

```python
# src/agents/monitoring/langsmith.py

import os
from langsmith import Client
from langsmith.wrappers import wrap_openai
from langchain_core.tracers import LangChainTracer

# Environment variables required:
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY=<your-langsmith-key>
# LANGCHAIN_PROJECT=lpxgp-agents

def setup_langsmith():
    """Initialize LangSmith for full agent monitoring."""
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "lpxgp-agents"

    client = Client()
    return client


def get_tracer(run_name: str, tags: list[str] = None) -> LangChainTracer:
    """Get a tracer for a specific run with tags for filtering."""
    return LangChainTracer(
        project_name="lpxgp-agents",
        run_name=run_name,
        tags=tags or [],
    )


# What LangSmith provides:
# 1. Full conversation traces for every debate
# 2. Token counts, latency, costs per run
# 3. Input/output inspection for every agent
# 4. Error tracking and debugging
# 5. Feedback collection for evaluation
# 6. Dataset creation from production runs
# 7. Prompt versioning and comparison
```

### Tracing Every Debate

```python
# Every debate gets full tracing
from langsmith import traceable

@traceable(
    run_type="chain",
    name="match_scoring_debate",
    tags=["debate", "matching"],
)
async def run_match_debate(fund_id: str, lp_org_id: str) -> DebateResult:
    """Run a match scoring debate with full LangSmith tracing."""
    # All agent calls inside are automatically traced
    # You can view the full conversation in LangSmith dashboard
    pass
```

---

## Agent Versioning System

### Prompt Registry

```python
# src/agents/registry.py

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable
import hashlib


class AgentVersion(Enum):
    """Semantic versioning for agents."""
    V1_0_0 = "1.0.0"
    V1_1_0 = "1.1.0"
    V1_2_0 = "1.2.0"
    V2_0_0 = "2.0.0"  # Major version = breaking changes


@dataclass
class PromptVersion:
    """A versioned prompt template."""
    version: AgentVersion
    agent_role: str
    template: str
    description: str
    created_at: datetime
    created_by: str

    # Metadata for tracking
    parent_version: AgentVersion | None = None
    change_notes: str = ""

    @property
    def hash(self) -> str:
        """Content hash for quick comparison."""
        return hashlib.sha256(self.template.encode()).hexdigest()[:12]


class PromptRegistry:
    """
    Central registry for all agent prompts with versioning.

    Features:
    - Store multiple versions of each prompt
    - Set active version per agent
    - A/B testing between versions
    - Rollback to previous versions
    - Audit trail of changes
    """

    _prompts: dict[str, dict[AgentVersion, PromptVersion]] = {}
    _active_versions: dict[str, AgentVersion] = {}

    @classmethod
    def register(cls, prompt: PromptVersion):
        """Register a new prompt version."""
        if prompt.agent_role not in cls._prompts:
            cls._prompts[prompt.agent_role] = {}

        cls._prompts[prompt.agent_role][prompt.version] = prompt

        # Auto-set as active if first version
        if prompt.agent_role not in cls._active_versions:
            cls._active_versions[prompt.agent_role] = prompt.version

    @classmethod
    def get_prompt(cls, agent_role: str, version: AgentVersion = None) -> str:
        """Get prompt template for agent (active version if not specified)."""
        if version is None:
            version = cls._active_versions.get(agent_role)

        if not version or agent_role not in cls._prompts:
            raise ValueError(f"No prompt registered for {agent_role}")

        return cls._prompts[agent_role][version].template

    @classmethod
    def set_active_version(cls, agent_role: str, version: AgentVersion):
        """Set the active version for an agent."""
        if agent_role not in cls._prompts:
            raise ValueError(f"No prompts registered for {agent_role}")
        if version not in cls._prompts[agent_role]:
            raise ValueError(f"Version {version} not found for {agent_role}")

        cls._active_versions[agent_role] = version

    @classmethod
    def get_version_history(cls, agent_role: str) -> list[PromptVersion]:
        """Get all versions for an agent, sorted by version."""
        if agent_role not in cls._prompts:
            return []
        return sorted(
            cls._prompts[agent_role].values(),
            key=lambda p: p.version.value,
        )

    @classmethod
    def compare_versions(
        cls,
        agent_role: str,
        v1: AgentVersion,
        v2: AgentVersion,
    ) -> dict:
        """Compare two prompt versions."""
        p1 = cls._prompts[agent_role][v1]
        p2 = cls._prompts[agent_role][v2]

        return {
            "v1": {"version": v1.value, "hash": p1.hash, "length": len(p1.template)},
            "v2": {"version": v2.value, "hash": p2.hash, "length": len(p2.template)},
            "changed": p1.hash != p2.hash,
            "change_notes": p2.change_notes,
        }
```

### Registering Prompts

```python
# src/agents/prompts/v1/bull.py

from src.agents.registry import PromptRegistry, PromptVersion, AgentVersion
from datetime import datetime

BULL_AGENT_V1 = PromptVersion(
    version=AgentVersion.V1_0_0,
    agent_role="bull_agent",
    template="""You are the BULL AGENT analyzing a potential match between a fund and LP.

## YOUR MISSION
Argue FOR this match. Find the best reasons why it could succeed.

## FUND PROFILE
- Name: {fund_name}
- Strategy: {fund_strategy}
- Thesis: {fund_thesis}
- Size: ${fund_size_mm}M
- Geography: {fund_geography}
- Sectors: {fund_sectors}

## LP PROFILE
- Name: {lp_name}
- Type: {lp_type}
- Mandate: {lp_mandate}
- Preferred Strategies: {lp_strategies}
- Geography Preferences: {lp_geography_preferences}
- Check Size: {lp_check_size_range}
- ESG Required: {lp_esg_required}

## YOUR ANALYSIS

Provide a JSON response with:
{{
    "overall_score": <0-100>,
    "confidence": <0.0-1.0>,
    "strategy_alignment": {{
        "score": <0-100>,
        "reasoning": "<why strategies align>",
        "specific_points": ["<point1>", "<point2>"]
    }},
    "timing_opportunity": {{
        "score": <0-100>,
        "reasoning": "<why timing is right>",
        "signals": ["<signal1>", "<signal2>"]
    }},
    "relationship_potential": {{
        "score": <0-100>,
        "warm_intro_paths": ["<path1>", "<path2>"],
        "barriers": ["<barrier1>"]
    }},
    "hidden_strengths": ["<strength1>", "<strength2>"],
    "talking_points": ["<point1>", "<point2>", "<point3>"],
    "acknowledged_concerns": ["<concern1>", "<concern2>"],
    "reasoning": "<overall reasoning for your score>"
}}

Be specific. Cite data points. Don't inflate scores just to win the debate.
""",
    description="Initial Bull Agent prompt - argues for matches",
    created_at=datetime(2024, 1, 15),
    created_by="system",
)

PromptRegistry.register(BULL_AGENT_V1)


# Version 1.1.0 - Added cross-feedback handling
BULL_AGENT_V1_1 = PromptVersion(
    version=AgentVersion.V1_1_0,
    agent_role="bull_agent",
    template="""You are the BULL AGENT analyzing a potential match between a fund and LP.

## YOUR MISSION
Argue FOR this match. Find the best reasons why it could succeed.

## FUND PROFILE
- Name: {fund_name}
- Strategy: {fund_strategy}
- Thesis: {fund_thesis}
- Size: ${fund_size_mm}M
- Geography: {fund_geography}
- Sectors: {fund_sectors}
- Track Record: {fund_track_record}
- Team: {fund_team}

## LP PROFILE
- Name: {lp_name}
- Type: {lp_type}
- Mandate: {lp_mandate}
- Preferred Strategies: {lp_strategies}
- Geography Preferences: {lp_geography_preferences}
- Check Size: {lp_check_size_range}
- ESG Required: {lp_esg_required}
- Historical Commitments: {lp_historical_commitments}

{cross_feedback_section}

## YOUR ANALYSIS

Provide a JSON response with:
{{
    "overall_score": <0-100>,
    "confidence": <0.0-1.0>,
    "strategy_alignment": {{
        "score": <0-100>,
        "reasoning": "<why strategies align>",
        "specific_points": ["<point1>", "<point2>"]
    }},
    "timing_opportunity": {{
        "score": <0-100>,
        "reasoning": "<why timing is right>",
        "signals": ["<signal1>", "<signal2>"]
    }},
    "relationship_potential": {{
        "score": <0-100>,
        "warm_intro_paths": ["<path1>", "<path2>"],
        "barriers": ["<barrier1>"]
    }},
    "hidden_strengths": ["<strength1>", "<strength2>"],
    "talking_points": ["<point1>", "<point2>", "<point3>", "<point4>", "<point5>"],
    "acknowledged_concerns": ["<concern1>", "<concern2>"],
    "response_to_bear": "<if bear feedback provided, address it here>",
    "reasoning": "<overall reasoning for your score>"
}}

IMPORTANT:
- Be specific - cite data points from the profiles
- If Bear raised valid concerns, acknowledge them but explain mitigation
- Don't inflate scores - truth matters more than winning
- Talking points should be actionable for the GP
""",
    description="Added cross-feedback handling and expanded analysis",
    created_at=datetime(2024, 2, 1),
    created_by="system",
    parent_version=AgentVersion.V1_0_0,
    change_notes="Added cross_feedback_section, response_to_bear field, expanded talking_points to 5",
)

PromptRegistry.register(BULL_AGENT_V1_1)

# Set v1.1.0 as active
PromptRegistry.set_active_version("bull_agent", AgentVersion.V1_1_0)
```

---

## LangGraph State Machine

### State Definitions

```python
# src/agents/core/state.py

from typing import TypedDict, Annotated, Sequence
from langgraph.graph.message import add_messages


class MatchDebateState(TypedDict):
    """State for match scoring debates."""

    # Input data
    fund_id: str
    lp_org_id: str
    fund_data: dict
    lp_data: dict

    # Debate tracking
    debate_id: str
    iteration: int
    max_iterations: int

    # Agent outputs (accumulated)
    bull_outputs: Annotated[Sequence[dict], add_messages]
    bear_outputs: Annotated[Sequence[dict], add_messages]
    synthesizer_outputs: Annotated[Sequence[dict], add_messages]

    # Current round outputs
    current_bull: dict | None
    current_bear: dict | None
    current_synthesis: dict | None

    # Cross-feedback for regeneration
    bull_feedback: dict | None  # Feedback from Bear to Bull
    bear_feedback: dict | None  # Feedback from Bull to Bear

    # Final results
    final_score: float | None
    confidence: float | None
    disagreement: float | None
    recommendation: str | None

    # Status
    status: str  # pending, debating, synthesizing, regenerating, completed, escalated
    requires_escalation: bool
    escalation_reason: str | None

    # Metrics
    total_tokens: int
    errors: list[str]
```

### Graph Nodes

```python
# src/agents/core/nodes.py

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langsmith import traceable

from src.agents.registry import PromptRegistry
from src.agents.core.state import MatchDebateState


def get_llm(model: str = "claude-sonnet-4-20250514"):
    """Get LLM instance with LangSmith tracing."""
    return ChatAnthropic(
        model=model,
        temperature=0.3,
        max_tokens=4096,
    )


@traceable(name="bull_agent", run_type="llm")
async def bull_node(state: MatchDebateState) -> dict:
    """
    Bull Agent node - argues FOR the match.

    Fully traced in LangSmith for inspection.
    """
    llm = get_llm()

    # Get versioned prompt
    prompt_template = PromptRegistry.get_prompt("bull_agent")

    # Build cross-feedback section if in regeneration
    cross_feedback = ""
    if state.get("bull_feedback"):
        cross_feedback = f"""
## BEAR AGENT FEEDBACK (Address these concerns)

The Bear Agent raised these points:
{state['bull_feedback']}

Consider these carefully. If valid, acknowledge but explain mitigation.
If you disagree, explain why with evidence.
"""

    prompt = prompt_template.format(
        fund_name=state["fund_data"]["name"],
        fund_strategy=state["fund_data"]["strategy"],
        fund_thesis=state["fund_data"]["thesis"],
        fund_size_mm=state["fund_data"]["size_mm"],
        fund_geography=", ".join(state["fund_data"]["geography"]),
        fund_sectors=", ".join(state["fund_data"]["sectors"]),
        fund_track_record=state["fund_data"].get("track_record", "N/A"),
        fund_team=state["fund_data"].get("team", []),
        lp_name=state["lp_data"]["name"],
        lp_type=state["lp_data"]["type"],
        lp_mandate=state["lp_data"]["mandate"],
        lp_strategies=", ".join(state["lp_data"]["strategies"]),
        lp_geography_preferences=", ".join(state["lp_data"]["geography_preferences"]),
        lp_check_size_range=state["lp_data"]["check_size_range"],
        lp_esg_required=state["lp_data"]["esg_required"],
        lp_historical_commitments=state["lp_data"].get("historical_commitments", []),
        cross_feedback_section=cross_feedback,
    )

    response = await llm.ainvoke([HumanMessage(content=prompt)])

    import json
    output = json.loads(response.content)

    return {
        "current_bull": output,
        "bull_outputs": [output],
        "total_tokens": state["total_tokens"] + response.usage_metadata["total_tokens"],
    }


@traceable(name="bear_agent", run_type="llm")
async def bear_node(state: MatchDebateState) -> dict:
    """Bear Agent node - argues AGAINST the match."""
    # Similar structure to bull_node
    # ... implementation
    pass


@traceable(name="synthesizer", run_type="llm")
async def synthesizer_node(state: MatchDebateState) -> dict:
    """
    Synthesizer node - combines Bull and Bear perspectives.

    Determines:
    - Final score
    - Whether to regenerate
    - Whether to escalate
    """
    llm = get_llm()

    prompt_template = PromptRegistry.get_prompt("match_synthesizer")

    bull_output = state["current_bull"]
    bear_output = state["current_bear"]

    # Calculate disagreement
    disagreement = abs(bull_output["overall_score"] - bear_output["overall_score"])

    prompt = prompt_template.format(
        fund_name=state["fund_data"]["name"],
        lp_name=state["lp_data"]["name"],
        iteration=state["iteration"],
        bull_score=bull_output["overall_score"],
        bull_confidence=bull_output["confidence"],
        bull_reasoning=bull_output["reasoning"],
        bull_talking_points=bull_output["talking_points"],
        bear_score=bear_output["overall_score"],
        bear_confidence=bear_output["confidence"],
        bear_reasoning=bear_output["reasoning"],
        bear_concerns=bear_output.get("hard_constraints_violated", []),
        disagreement=disagreement,
        previous_syntheses=state["synthesizer_outputs"],
    )

    response = await llm.ainvoke([HumanMessage(content=prompt)])

    import json
    output = json.loads(response.content)

    # Determine if escalation needed
    requires_escalation = (
        disagreement > 30 or
        output["confidence"] < 0.5 or
        bear_output.get("hard_exclusion", False)
    )

    escalation_reason = None
    if disagreement > 30:
        escalation_reason = f"Score disagreement: {disagreement:.0f} points"
    elif output["confidence"] < 0.5:
        escalation_reason = f"Low confidence: {output['confidence']:.2f}"
    elif bear_output.get("hard_exclusion"):
        escalation_reason = bear_output.get("exclusion_reason")

    return {
        "current_synthesis": output,
        "synthesizer_outputs": [output],
        "final_score": output["final_score"],
        "confidence": output["confidence"],
        "disagreement": disagreement,
        "recommendation": output["recommendation"],
        "requires_escalation": requires_escalation,
        "escalation_reason": escalation_reason,
        "total_tokens": state["total_tokens"] + response.usage_metadata["total_tokens"],
    }
```

### Graph Builder

```python
# src/agents/core/graphs.py

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver

from src.agents.core.state import MatchDebateState
from src.agents.core.nodes import bull_node, bear_node, synthesizer_node


def should_regenerate(state: MatchDebateState) -> str:
    """Determine next step after synthesis."""
    if state["requires_escalation"]:
        return "escalate"

    if state["disagreement"] <= 20:
        return "complete"

    if state["iteration"] >= state["max_iterations"]:
        return "escalate"  # Max iterations reached, still disagreeing

    return "regenerate"


def build_match_debate_graph():
    """
    Build the LangGraph for match scoring debates.

    Flow:
    1. Bull and Bear run in parallel
    2. Synthesizer combines
    3. Check disagreement:
       - Low disagreement → Complete
       - High disagreement + iterations left → Regenerate with cross-feedback
       - High disagreement + no iterations → Escalate
    """
    builder = StateGraph(MatchDebateState)

    # Add nodes
    builder.add_node("bull", bull_node)
    builder.add_node("bear", bear_node)
    builder.add_node("synthesize", synthesizer_node)
    builder.add_node("prepare_regeneration", prepare_regeneration_node)
    builder.add_node("escalate", escalate_node)
    builder.add_node("complete", complete_node)

    # Set entry point
    builder.set_entry_point("bull")

    # Bull and Bear run, then synthesize
    builder.add_edge("bull", "synthesize")
    builder.add_edge("bear", "synthesize")

    # After synthesis, decide next step
    builder.add_conditional_edges(
        "synthesize",
        should_regenerate,
        {
            "complete": "complete",
            "regenerate": "prepare_regeneration",
            "escalate": "escalate",
        }
    )

    # Regeneration loops back to debate
    builder.add_edge("prepare_regeneration", "bull")
    # Also triggers bear in parallel
    builder.add_edge("prepare_regeneration", "bear")

    # End states
    builder.add_edge("complete", END)
    builder.add_edge("escalate", END)

    return builder.compile()


def prepare_regeneration_node(state: MatchDebateState) -> dict:
    """Prepare cross-feedback for regeneration."""
    bull = state["current_bull"]
    bear = state["current_bear"]

    return {
        "iteration": state["iteration"] + 1,
        "bull_feedback": {
            "concerns": bear.get("hard_constraints_violated", []) + bear.get("soft_concerns", []),
            "bear_score": bear["overall_score"],
            "bear_reasoning": bear["reasoning"],
        },
        "bear_feedback": {
            "arguments": bull.get("talking_points", []),
            "bull_score": bull["overall_score"],
            "strategy_alignment": bull.get("strategy_alignment", {}),
        },
        "status": "regenerating",
    }


async def escalate_node(state: MatchDebateState) -> dict:
    """Create escalation for human review."""
    from src.db import supabase

    await supabase.table("agent_escalations").insert({
        "debate_id": state["debate_id"],
        "escalation_type": _determine_type(state),
        "priority": _determine_priority(state),
        "summary": state["escalation_reason"],
        "debate_transcript": {
            "bull_outputs": state["bull_outputs"],
            "bear_outputs": state["bear_outputs"],
            "synthesizer_outputs": state["synthesizer_outputs"],
        },
        "key_disagreement": state["escalation_reason"],
    }).execute()

    return {"status": "escalated"}


async def complete_node(state: MatchDebateState) -> dict:
    """Mark debate as complete and cache results."""
    from src.db import supabase

    # Cache the result
    await supabase.table("entity_cache").upsert({
        "entity_type": "match",
        "entity_id": f"{state['fund_id']}:{state['lp_org_id']}",
        "cache_key": "debate_result",
        "cache_value": {
            "final_score": state["final_score"],
            "confidence": state["confidence"],
            "recommendation": state["recommendation"],
            "talking_points": state["current_synthesis"]["talking_points"],
            "concerns": state["current_synthesis"]["concerns_to_address"],
        },
        "source_debate_id": state["debate_id"],
    }).execute()

    return {"status": "completed"}


# Create the compiled graph
match_debate_graph = build_match_debate_graph()
```

---

## Running Debates with Full Tracing

```python
# src/agents/orchestrator.py

from uuid import uuid4
from langsmith import traceable
from src.agents.core.graphs import match_debate_graph
from src.agents.core.state import MatchDebateState


class DebateOrchestrator:
    """
    Orchestrator for running debates with full LangSmith tracing.

    Every debate run is:
    1. Fully traced in LangSmith
    2. Inspectable via LangSmith dashboard
    3. Can be replayed for debugging
    4. Metrics automatically collected
    """

    @traceable(
        run_type="chain",
        name="match_scoring_debate",
        tags=["debate", "matching", "production"],
    )
    async def run_match_debate(
        self,
        fund_id: str,
        lp_org_id: str,
        fund_data: dict,
        lp_data: dict,
    ) -> dict:
        """
        Run a complete match scoring debate.

        Args:
            fund_id: Fund UUID
            lp_org_id: LP organization UUID
            fund_data: Fund profile data
            lp_data: LP profile data

        Returns:
            Debate result with score, confidence, talking points

        LangSmith Inspection:
            - View full trace at: https://smith.langchain.com
            - Filter by debate_id, fund_id, or lp_org_id
            - See all agent inputs/outputs
            - Analyze token usage and latency
        """
        debate_id = str(uuid4())

        initial_state = MatchDebateState(
            fund_id=fund_id,
            lp_org_id=lp_org_id,
            fund_data=fund_data,
            lp_data=lp_data,
            debate_id=debate_id,
            iteration=1,
            max_iterations=3,
            bull_outputs=[],
            bear_outputs=[],
            synthesizer_outputs=[],
            current_bull=None,
            current_bear=None,
            current_synthesis=None,
            bull_feedback=None,
            bear_feedback=None,
            final_score=None,
            confidence=None,
            disagreement=None,
            recommendation=None,
            status="pending",
            requires_escalation=False,
            escalation_reason=None,
            total_tokens=0,
            errors=[],
        )

        # Run the graph - all steps are traced in LangSmith
        final_state = await match_debate_graph.ainvoke(initial_state)

        return {
            "debate_id": debate_id,
            "status": final_state["status"],
            "final_score": final_state["final_score"],
            "confidence": final_state["confidence"],
            "recommendation": final_state["recommendation"],
            "talking_points": final_state["current_synthesis"]["talking_points"],
            "concerns": final_state["current_synthesis"]["concerns_to_address"],
            "iterations": final_state["iteration"],
            "total_tokens": final_state["total_tokens"],
        }
```

---

## Monitoring Dashboard

### What You Can Inspect in LangSmith

1. **Full Conversation Traces**
   - Every debate as a tree of agent calls
   - Input/output for each agent
   - Token counts per call
   - Latency breakdown

2. **Agent Performance**
   - Success/failure rates by agent
   - Average scores and confidence
   - Token usage trends
   - Latency percentiles

3. **Prompt Versioning**
   - Compare outputs across prompt versions
   - A/B test new prompts
   - Track which version produced which results

4. **Debugging**
   - Replay any debate
   - See exactly what each agent saw
   - Trace errors to specific agents

5. **Evaluation**
   - Create datasets from production runs
   - Run automated evaluations
   - Collect human feedback

### Custom Metrics

```python
# src/agents/monitoring/metrics.py

from langsmith import Client
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class DebateMetrics:
    """Metrics for debate quality and performance."""
    total_debates: int
    completed: int
    escalated: int
    failed: int

    avg_score: float
    avg_confidence: float
    avg_disagreement: float

    avg_iterations: float
    avg_tokens: int
    avg_latency_ms: int

    escalation_rate: float
    regeneration_rate: float


class MetricsCollector:
    """Collect and analyze debate metrics from LangSmith."""

    def __init__(self):
        self.client = Client()

    def get_metrics(
        self,
        project: str = "lpxgp-agents",
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> DebateMetrics:
        """Get aggregate metrics for debates."""
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now()

        runs = self.client.list_runs(
            project_name=project,
            start_time=start_date,
            end_time=end_date,
            filter='eq(run_type, "chain")',
        )

        # Aggregate metrics
        # ... implementation

        return DebateMetrics(...)

    def get_agent_performance(
        self,
        agent_role: str,
        version: str = None,
    ) -> dict:
        """Get performance metrics for specific agent."""
        # Query LangSmith for agent-specific runs
        pass

    def compare_prompt_versions(
        self,
        agent_role: str,
        v1: str,
        v2: str,
    ) -> dict:
        """Compare performance between prompt versions."""
        # Get runs for each version
        # Compare scores, latency, errors
        pass
```

---

## Dependencies

```toml
# pyproject.toml additions
[project.dependencies]
# LangChain ecosystem
langchain = ">=0.3.0"
langchain-anthropic = ">=0.3.0"
langchain-core = ">=0.3.0"
langgraph = ">=0.2.0"
langsmith = ">=0.1.0"

# Async support
aiohttp = ">=3.9.0"

# Structured outputs
pydantic = ">=2.0.0"
```

---

## Environment Variables

```bash
# .env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=<your-langsmith-api-key>
LANGCHAIN_PROJECT=lpxgp-agents
OPENROUTER_API_KEY=<your-openrouter-key>
```

---

## Next Documents

1. **`agent-prompts.md`** - Complete versioned prompts for all 42 agents (14 teams)
2. **`batch-processing.md`** - Scheduler, caching, invalidation
3. **`evaluation.md`** - Testing agents, creating datasets, feedback loops
