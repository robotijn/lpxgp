"""Pitch generation models."""

from typing import Literal
from uuid import UUID

from pydantic import Field

from src.models.base import BaseModel, BaseResponse, LongText, MediumText, ShortText

# Pitch types
PitchType = Literal[
    "executive_summary",
    "initial_outreach_email",
    "follow_up_email",
    "meeting_request",
    "talking_points",
    "one_pager",
]

# Tone options
PitchTone = Literal[
    "formal",
    "professional",
    "friendly",
    "direct",
]


class PitchGenerateRequest(BaseModel):
    """Request to generate a pitch."""

    match_id: UUID = Field(description="Match to generate pitch for")
    pitch_type: PitchType = Field(description="Type of pitch to generate")

    # Customization
    tone: PitchTone = Field(default="professional")
    max_length: int = Field(default=500, ge=100, le=5000, description="Max length in words")

    # Context (optional)
    key_points_to_emphasize: list[str] | None = Field(
        default=None,
        max_length=5,
        description="Key points to emphasize in the pitch",
    )
    topics_to_avoid: list[str] | None = Field(
        default=None,
        max_length=5,
        description="Topics to avoid mentioning",
    )

    # Previous context (for follow-ups)
    previous_interaction_summary: MediumText | None = Field(
        default=None,
        description="Summary of previous interactions for context",
    )


class PitchResponse(BaseResponse):
    """Generated pitch response."""

    match_id: UUID
    pitch_type: PitchType
    tone: PitchTone

    # Content
    subject_line: ShortText | None = None  # For emails
    content: LongText = Field(description="Generated pitch content")

    # Metadata
    word_count: int
    generation_model: str | None = None
    generation_time_ms: int | None = None

    # Quality (M4+)
    quality_score: int | None = Field(default=None, ge=0, le=100)
    quality_feedback: str | None = None


class PitchFeedback(BaseModel):
    """Feedback on a generated pitch."""

    pitch_id: UUID = Field(description="Pitch being rated")

    # Rating
    rating: int = Field(ge=1, le=5, description="Quality rating 1-5")
    was_used: bool = Field(description="Was this pitch actually used?")

    # Specific feedback
    accuracy_rating: int | None = Field(default=None, ge=1, le=5)
    tone_rating: int | None = Field(default=None, ge=1, le=5)
    relevance_rating: int | None = Field(default=None, ge=1, le=5)

    # Text feedback
    what_worked: MediumText | None = None
    what_to_improve: MediumText | None = None

    # Edits made
    edits_made: Literal["none", "minor", "moderate", "major"] = Field(default="none")
    edited_content: LongText | None = Field(
        default=None,
        description="The edited version if edits were made",
    )


class PitchTemplate(BaseModel):
    """Custom pitch template."""

    id: UUID | None = None
    name: ShortText = Field(min_length=2)
    pitch_type: PitchType
    template_content: LongText = Field(description="Template with {{placeholders}}")
    placeholders: list[str] = Field(description="List of placeholder names")
    is_default: bool = False
