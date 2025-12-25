"""Match generation and management models."""

from typing import Literal
from uuid import UUID

from pydantic import Field

from src.models.base import BaseModel, BaseResponse, MediumText, Percentage, ShortText

# Pipeline stages
PipelineStage = Literal[
    "recommended",
    "gp_interested",
    "gp_pursuing",
    "lp_reviewing",
    "mutual_interest",
    "in_diligence",
    "invested",
    "gp_passed",
    "lp_passed",
]


class MatchGenerateRequest(BaseModel):
    """Request to generate matches for a fund."""

    fund_id: UUID = Field(description="Fund to generate matches for")

    # Optional filters
    min_score: int = Field(default=50, ge=0, le=100, description="Minimum match score (0-100)")
    max_results: int = Field(default=100, ge=1, le=500, description="Maximum results to return")

    # Filter by LP type
    lp_types: list[str] | None = Field(default=None, max_length=8)

    # Filter by geography
    geographies: list[str] | None = Field(default=None, max_length=20)

    # Processing mode
    mode: Literal["real_time", "batch"] = Field(
        default="real_time",
        description="Processing mode: real_time (sync) or batch (async)",
    )


class MatchScoreBreakdown(BaseModel):
    """Score breakdown for a match."""

    strategy_score: int = Field(ge=0, le=100)
    geography_score: int = Field(ge=0, le=100)
    size_score: int = Field(ge=0, le=100)
    semantic_score: int = Field(ge=0, le=100)
    relationship_score: int = Field(default=0, ge=0, le=100)

    # Weights used
    strategy_weight: Percentage = Field(default=30)
    geography_weight: Percentage = Field(default=20)
    size_weight: Percentage = Field(default=20)
    semantic_weight: Percentage = Field(default=25)
    relationship_weight: Percentage = Field(default=5)


class MatchResponse(BaseResponse):
    """Match response with scores and explanation."""

    fund_id: UUID
    lp_org_id: UUID
    lp_name: str
    lp_type: str

    # Scores
    overall_score: int = Field(ge=0, le=100)
    score_breakdown: MatchScoreBreakdown

    # Explanation
    match_rationale: str | None = None
    key_alignment_points: list[str] | None = None
    potential_concerns: list[str] | None = None

    # Agent debate (M3+)
    debate_id: UUID | None = None
    bull_case: str | None = None
    bear_case: str | None = None
    consensus_view: str | None = None

    # Status
    pipeline_stage: PipelineStage = "recommended"


class MatchStatusUpdate(BaseModel):
    """Update match pipeline status."""

    pipeline_stage: PipelineStage = Field(description="New pipeline stage")
    notes: MediumText | None = Field(default=None, description="Notes about this status change")

    # Optional: reason for pass
    pass_reason: ShortText | None = Field(
        default=None,
        description="Reason for passing (if gp_passed or lp_passed)",
    )


class MatchBatchJobResponse(BaseModel):
    """Response for batch match generation job."""

    job_id: UUID
    fund_id: UUID
    status: Literal["queued", "processing", "completed", "failed"]
    total_lps: int | None = None
    processed_lps: int | None = None
    matches_found: int | None = None
    error_message: str | None = None
