"""Fund-related Pydantic models."""

from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator

from src.models.base import (
    BaseModel,
    BaseResponse,
    FinancialAmountMM,
    LongText,
    MediumText,
    Percentage,
    ShortText,
)

# Enum types for fund fields
FundStrategy = Literal[
    "buyout",
    "growth_equity",
    "venture_capital",
    "real_estate",
    "infrastructure",
    "credit",
    "secondaries",
    "fund_of_funds",
    "other",
]

FundStage = Literal[
    "seed",
    "early_stage",
    "growth",
    "late_stage",
    "multi_stage",
]

FundStatus = Literal[
    "draft",
    "fundraising",
    "final_close",
    "closed",
    "investing",
    "harvesting",
]


class FundCreate(BaseModel):
    """Create a new fund."""

    name: ShortText = Field(min_length=2, description="Fund name")
    vintage_year: int = Field(ge=1990, le=2100, description="Fund vintage year")

    # Strategy
    strategy: FundStrategy = Field(description="Primary investment strategy")
    stage_focus: FundStage | None = Field(default=None, description="Stage focus (for VC)")
    sector_focus: list[str] | None = Field(
        default=None,
        max_length=10,
        description="Target sectors",
    )

    # Size
    target_size_mm: FinancialAmountMM = Field(description="Target fund size in millions USD")
    hard_cap_mm: FinancialAmountMM | None = Field(default=None, description="Hard cap in millions USD")
    first_close_mm: FinancialAmountMM | None = Field(default=None, description="First close amount")

    # Geography
    geography_focus: list[str] | None = Field(
        default=None,
        max_length=20,
        description="Target geographies",
    )
    headquarters_city: ShortText | None = None
    headquarters_country: ShortText | None = None

    # Terms
    management_fee_pct: Percentage | None = Field(default=None, description="Management fee %")
    carried_interest_pct: Percentage | None = Field(default=None, description="Carried interest %")
    preferred_return_pct: Percentage | None = Field(default=None, description="Preferred return %")

    # Content
    thesis: MediumText | None = Field(default=None, description="Investment thesis")
    description: LongText | None = Field(default=None, description="Fund description")

    # Status
    status: FundStatus = Field(default="draft")

    @field_validator("hard_cap_mm")
    @classmethod
    def hard_cap_gte_target(cls, v, info):
        """Hard cap must be >= target size if specified."""
        if v is not None and info.data.get("target_size_mm"):
            if v < info.data["target_size_mm"]:
                raise ValueError("Hard cap must be >= target size")
        return v


class FundUpdate(BaseModel):
    """Update an existing fund (partial update)."""

    name: ShortText | None = None
    vintage_year: int | None = Field(default=None, ge=1990, le=2100)
    strategy: FundStrategy | None = None
    stage_focus: FundStage | None = None
    sector_focus: list[str] | None = None
    target_size_mm: FinancialAmountMM | None = None
    hard_cap_mm: FinancialAmountMM | None = None
    first_close_mm: FinancialAmountMM | None = None
    geography_focus: list[str] | None = None
    headquarters_city: ShortText | None = None
    headquarters_country: ShortText | None = None
    management_fee_pct: Percentage | None = None
    carried_interest_pct: Percentage | None = None
    preferred_return_pct: Percentage | None = None
    thesis: MediumText | None = None
    description: LongText | None = None
    status: FundStatus | None = None


class FundResponse(BaseResponse):
    """Fund response with all fields."""

    org_id: UUID
    name: str
    vintage_year: int
    strategy: FundStrategy
    stage_focus: FundStage | None = None
    sector_focus: list[str] | None = None
    target_size_mm: float
    hard_cap_mm: float | None = None
    first_close_mm: float | None = None
    geography_focus: list[str] | None = None
    headquarters_city: str | None = None
    headquarters_country: str | None = None
    management_fee_pct: float | None = None
    carried_interest_pct: float | None = None
    preferred_return_pct: float | None = None
    thesis: str | None = None
    description: str | None = None
    status: FundStatus


class FundTeamMemberCreate(BaseModel):
    """Add a team member to a fund."""

    person_id: UUID = Field(description="Person to add to fund team")
    role: ShortText = Field(min_length=2, description="Role on the fund (e.g., Partner, Associate)")
    allocation_pct: Percentage | None = Field(
        default=None,
        description="Allocation percentage (0-100)",
    )
    is_lead: bool = Field(default=False, description="Is this person the fund lead?")


class FundTeamMemberResponse(BaseModel):
    """Fund team member response."""

    id: UUID
    fund_id: UUID
    person_id: UUID
    person_name: str
    role: str
    allocation_pct: float | None = None
    is_lead: bool


class NotableExit(BaseModel):
    """Notable exit from a fund."""

    company_name: ShortText = Field(min_length=1)
    exit_year: int = Field(ge=1990, le=2100)
    multiple_return: float | None = Field(default=None, ge=0)
    details: MediumText | None = None
