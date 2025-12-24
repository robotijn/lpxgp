"""LP (Limited Partner) related models."""

from typing import Literal
from uuid import UUID

from pydantic import Field

from src.models.base import (
    BaseModel,
    BaseResponse,
    FinancialAmountMM,
    LongText,
    MediumText,
    Percentage,
    PositiveDecimal,
    ShortText,
)


# LP Type enum
LPType = Literal[
    "pension",
    "endowment",
    "foundation",
    "family_office",
    "sovereign_wealth",
    "insurance",
    "fund_of_funds",
    "other",
]


class LPSearchRequest(BaseModel):
    """Search for LPs with filters."""

    # Text search
    query: str | None = Field(default=None, max_length=500, description="Free-text search query")

    # Filters
    lp_types: list[LPType] | None = Field(default=None, max_length=8)
    strategies: list[str] | None = Field(default=None, max_length=10)
    geographies: list[str] | None = Field(default=None, max_length=20)

    # Size filters
    min_aum_bn: PositiveDecimal | None = Field(default=None, description="Minimum AUM in billions")
    max_aum_bn: PositiveDecimal | None = Field(default=None, description="Maximum AUM in billions")
    min_check_size_mm: FinancialAmountMM | None = Field(default=None, description="Min check size in millions")
    max_check_size_mm: FinancialAmountMM | None = Field(default=None, description="Max check size in millions")

    # Pagination
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    # Sorting
    sort_by: Literal["name", "aum", "relevance", "updated_at"] = Field(default="relevance")
    sort_order: Literal["asc", "desc"] = Field(default="desc")


class LPProfileResponse(BaseResponse):
    """LP profile response."""

    org_id: UUID
    name: str
    lp_type: LPType
    headquarters_city: str | None = None
    headquarters_country: str | None = None

    # Size
    total_aum_bn: float | None = None
    pe_allocation_bn: float | None = None
    pe_target_pct: float | None = None

    # Check size
    check_size_min_mm: float | None = None
    check_size_max_mm: float | None = None

    # Preferences
    strategy_preferences: list[str] | None = None
    geography_preferences: list[str] | None = None
    sector_preferences: list[str] | None = None

    # Content
    mandate_description: str | None = None

    # Metadata
    data_quality_score: float | None = None


class LPProfileUpdate(BaseModel):
    """Update LP profile (super admin only)."""

    name: ShortText | None = None
    lp_type: LPType | None = None
    headquarters_city: ShortText | None = None
    headquarters_country: ShortText | None = None

    total_aum_bn: PositiveDecimal | None = None
    pe_allocation_bn: PositiveDecimal | None = None
    pe_target_pct: Percentage | None = None

    check_size_min_mm: FinancialAmountMM | None = None
    check_size_max_mm: FinancialAmountMM | None = None

    strategy_preferences: list[str] | None = Field(default=None, max_length=10)
    geography_preferences: list[str] | None = Field(default=None, max_length=20)
    sector_preferences: list[str] | None = Field(default=None, max_length=20)

    mandate_description: LongText | None = None


class LPContactResponse(BaseModel):
    """LP contact (person at LP org)."""

    id: UUID
    lp_org_id: UUID
    first_name: str
    last_name: str
    title: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    is_decision_maker: bool = False
