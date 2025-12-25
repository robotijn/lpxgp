"""Base Pydantic models with common configuration."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Field, field_validator

# Custom types with validation
PositiveDecimal = Annotated[Decimal, Field(ge=0)]
Percentage = Annotated[Decimal, Field(ge=0, le=100)]
FinancialAmountMM = Annotated[Decimal, Field(ge=0, le=1_000_000, description="Amount in millions USD")]
ShortText = Annotated[str, Field(max_length=255)]
MediumText = Annotated[str, Field(max_length=2000)]
LongText = Annotated[str, Field(max_length=50000)]


class BaseModel(PydanticBaseModel):
    """Base model with common configuration for all LPxGP models."""

    model_config = ConfigDict(
        # Use enum values instead of names
        use_enum_values=True,
        # Strip whitespace from strings
        str_strip_whitespace=True,
        # Validate on assignment
        validate_assignment=True,
        # Allow population by field name
        populate_by_name=True,
        # Strict mode for better type checking
        strict=False,
        # JSON serialization settings
        json_encoders={
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
            UUID: lambda v: str(v),
        },
    )

    @field_validator("*", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Any) -> Any:
        """Convert empty strings to None for optional fields."""
        if v == "":
            return None
        return v


class BaseResponse(BaseModel):
    """Base response model with common fields."""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None


class TimestampMixin(BaseModel):
    """Mixin for models with timestamp fields."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None


class OrgScopedMixin(BaseModel):
    """Mixin for models that belong to an organization."""

    org_id: UUID
