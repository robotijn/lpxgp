## 10. Learned Ensemble Weights

### Current Problem: Fixed/Arbitrary Weights

The Match Synthesizer currently lets the LLM decide weights ad-hoc:
```python
"bull_weight": 0.6,  # Why 0.6? No data-driven reason.
"bear_weight": 0.4,
```

**Issues:**
- A) Numbers come from: LLM intuition (arbitrary)
- B) No learning from actual outcomes
- C) Same weights for all LP types (wrong—pension vs family office should differ)
- D) No confidence-weighted blending

### Proposed: Outcome-Driven Weight Learning

#### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT OUTPUTS                            │
│  Bull: 85    Bear: 62    Relationship: 78    Timing: 45    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  LEARNED ENSEMBLE MODEL                      │
│                                                             │
│  final_score = Σ (weight_i × agent_score_i × confidence_i) │
│                                                             │
│  Weights learned from historical outcomes:                  │
│  - Meeting scheduled? (+1 signal)                          │
│  - DD process started? (+2 signal)                         │
│  - Commitment made? (+5 signal)                            │
│  - Rejection? (-1 signal)                                   │
└─────────────────────────────────────────────────────────────┘
```

#### Data Model for Learning

```sql
-- Track outcomes for learning
CREATE TABLE match_outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id UUID NOT NULL,  -- fund-LP pair
    fund_id UUID NOT NULL,
    lp_id UUID NOT NULL,

    -- Agent scores at time of match
    agent_scores JSONB NOT NULL,
    -- Example: {
    --   "bull": {"score": 85, "confidence": 0.8},
    --   "bear": {"score": 62, "confidence": 0.7},
    --   "relationship": {"score": 78, "confidence": 0.6},
    --   "timing": {"score": 45, "confidence": 0.5},
    --   ...
    -- }

    -- Final ensemble score used
    ensemble_score NUMERIC NOT NULL,
    ensemble_weights JSONB NOT NULL,

    -- Actual outcomes (filled in over time)
    outcome_meeting_scheduled BOOLEAN,
    outcome_meeting_date TIMESTAMP,
    outcome_dd_started BOOLEAN,
    outcome_commitment_made BOOLEAN,
    outcome_commitment_amount_mm NUMERIC,
    outcome_rejection BOOLEAN,
    outcome_rejection_reason TEXT,

    -- Timing
    created_at TIMESTAMP DEFAULT NOW(),
    outcome_recorded_at TIMESTAMP,

    -- For segmentation
    lp_type TEXT,
    fund_strategy TEXT
);

-- Index for learning queries
CREATE INDEX idx_match_outcomes_outcome ON match_outcomes(outcome_commitment_made);
CREATE INDEX idx_match_outcomes_lp_type ON match_outcomes(lp_type);
```

#### Weight Learning Algorithm

```python
from sklearn.linear_model import LogisticRegression
import numpy as np

class EnsembleWeightLearner:
    """Learn optimal weights from historical outcomes."""

    def __init__(self):
        self.models = {}  # One model per LP type

    def train(self, outcomes: list[MatchOutcome]):
        """Train weight models from historical data."""

        # Group by LP type (different segments have different patterns)
        by_lp_type = defaultdict(list)
        for outcome in outcomes:
            by_lp_type[outcome.lp_type].append(outcome)

        for lp_type, type_outcomes in by_lp_type.items():
            if len(type_outcomes) < 50:  # Need minimum data
                continue

            # Build feature matrix (agent scores)
            X = []
            y = []

            for o in type_outcomes:
                features = [
                    o.agent_scores["bull"]["score"] * o.agent_scores["bull"]["confidence"],
                    o.agent_scores["bear"]["score"] * o.agent_scores["bear"]["confidence"],
                    o.agent_scores["relationship"]["score"] * o.agent_scores["relationship"]["confidence"],
                    o.agent_scores["timing"]["score"] * o.agent_scores["timing"]["confidence"],
                    o.agent_scores["competitive"]["score"] * o.agent_scores["competitive"]["confidence"],
                    o.agent_scores["persona"]["score"] * o.agent_scores["persona"]["confidence"],
                    o.agent_scores["market"]["score"] * o.agent_scores["market"]["confidence"],
                    o.agent_scores["objection"]["score"] * o.agent_scores["objection"]["confidence"],
                    o.agent_scores["prioritization"]["score"] * o.agent_scores["prioritization"]["confidence"],
                ]
                X.append(features)

                # Target: commitment made (or meeting scheduled for faster feedback)
                y.append(1 if o.outcome_commitment_made else 0)

            X = np.array(X)
            y = np.array(y)

            # Train logistic regression (coefficients = weights)
            model = LogisticRegression(fit_intercept=False, solver='lbfgs')
            model.fit(X, y)

            # Normalize coefficients to weights (sum to 1)
            weights = np.abs(model.coef_[0])
            weights = weights / weights.sum()

            self.models[lp_type] = {
                "weights": {
                    "bull": float(weights[0]),
                    "bear": float(weights[1]),
                    "relationship": float(weights[2]),
                    "timing": float(weights[3]),
                    "competitive": float(weights[4]),
                    "persona": float(weights[5]),
                    "market": float(weights[6]),
                    "objection": float(weights[7]),
                    "prioritization": float(weights[8]),
                },
                "training_samples": len(type_outcomes),
                "training_date": datetime.now().isoformat()
            }

    def get_weights(self, lp_type: str) -> dict:
        """Get learned weights for LP type, or defaults if not enough data."""

        if lp_type in self.models:
            return self.models[lp_type]["weights"]

        # Default weights (equal, conservative)
        return {
            "bull": 0.15,
            "bear": 0.15,
            "relationship": 0.15,
            "timing": 0.10,
            "competitive": 0.10,
            "persona": 0.10,
            "market": 0.10,
            "objection": 0.10,
            "prioritization": 0.05,
        }

    def calculate_ensemble_score(
        self,
        agent_scores: dict,
        lp_type: str
    ) -> tuple[float, dict]:
        """Calculate final score using learned weights."""

        weights = self.get_weights(lp_type)

        # Confidence-weighted ensemble
        weighted_sum = 0
        weight_sum = 0

        for agent, weight in weights.items():
            if agent in agent_scores:
                score = agent_scores[agent]["score"]
                confidence = agent_scores[agent]["confidence"]

                weighted_sum += weight * score * confidence
                weight_sum += weight * confidence

        final_score = weighted_sum / weight_sum if weight_sum > 0 else 50

        return final_score, weights
```

#### Expected Learned Weight Patterns

Based on domain intuition (to be validated with real data):

| Agent | Pension | Endowment | Family Office | Fund of Funds |
|-------|---------|-----------|---------------|---------------|
| Bull | 0.12 | 0.15 | 0.18 | 0.14 |
| Bear | 0.18 | 0.12 | 0.10 | 0.16 |
| Relationship | 0.10 | 0.20 | 0.25 | 0.12 |
| Timing | 0.15 | 0.12 | 0.08 | 0.10 |
| Competitive | 0.15 | 0.12 | 0.10 | 0.18 |
| Persona | 0.08 | 0.12 | 0.15 | 0.08 |
| Market | 0.10 | 0.08 | 0.06 | 0.10 |
| Objection | 0.07 | 0.05 | 0.04 | 0.08 |
| Prioritization | 0.05 | 0.04 | 0.04 | 0.04 |

**Intuition:**
- Pensions: Bear weight high (conservative), timing important (allocation cycles)
- Endowments: Relationship weight high (network-driven)
- Family Offices: Relationship very high (principal access), Bear low (more risk-tolerant)
- Fund of Funds: Competitive weight high (portfolio construction)

#### Cold Start Strategy

Before we have outcome data:

1. **Phase 1: Expert-set weights** (Month 1-3)
   - Use domain expert intuition
   - Different defaults per LP type
   - Log all predictions

2. **Phase 2: Proxy outcomes** (Month 3-6)
   - Use "meeting scheduled" as proxy for success
   - Faster feedback loop than commitments

3. **Phase 3: Full outcome learning** (Month 6+)
   - Enough commitment data to train on actual outcomes
   - Continuous retraining (monthly)

#### Weight Update Cycle

```python
# Weekly weight refresh job
async def refresh_ensemble_weights():
    """Retrain ensemble weights from recent outcomes."""

    # Get outcomes from last 6 months
    outcomes = await get_recent_outcomes(months=6)

    if len(outcomes) < 100:
        logger.info("Not enough data for weight learning, using defaults")
        return

    learner = EnsembleWeightLearner()
    learner.train(outcomes)

    # Store new weights
    await store_learned_weights(learner.models)

    # Log weight changes for monitoring
    for lp_type, model in learner.models.items():
        logger.info(f"Updated weights for {lp_type}: {model['weights']}")
```

### Summary

| Aspect | Before | After |
|--------|--------|-------|
| Weight source | LLM intuition | Learned from outcomes |
| LP type customization | None | Per-type weights |
| Confidence handling | Ignored | Confidence-weighted |
| Feedback loop | None | Continuous learning |
| Cold start | N/A | Expert defaults → proxy → full |

---

