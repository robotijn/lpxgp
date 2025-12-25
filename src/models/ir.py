"""IR (Investor Relations) Core models - Events, Touchpoints, Tasks."""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator

from src.models.base import BaseModel, BaseResponse, LongText, MediumText, ShortText

# Event types
EventType = Literal[
    "conference",
    "summit",
    "dinner",
    "roadshow",
    "webinar",
    "meeting",
    "call",
    "other",
]

EventStatus = Literal[
    "planning",
    "confirmed",
    "in_progress",
    "completed",
    "cancelled",
]

# Touchpoint types
TouchpointType = Literal[
    "meeting",
    "call",
    "email",
    "event_interaction",
    "video_call",
    "linkedin",
    "text",
    "other",
]

Sentiment = Literal["positive", "neutral", "negative", "mixed"]

# Task types
TaskStatus = Literal["pending", "in_progress", "completed", "cancelled", "deferred"]
TaskPriority = Literal["low", "medium", "high", "urgent"]

# Attendance
RegistrationStatus = Literal[
    "invited",
    "registered",
    "confirmed",
    "attended",
    "no_show",
    "cancelled",
]

PriorityLevel = Literal["must_meet", "should_meet", "nice_to_meet", "avoid"]


# ============================================================================
# Events
# ============================================================================


class EventCreate(BaseModel):
    """Create a new event."""

    name: ShortText = Field(min_length=2, description="Event name")
    event_type: EventType = Field(description="Type of event")
    description: MediumText | None = None

    # Dates
    start_date: date = Field(description="Event start date")
    end_date: date | None = Field(default=None, description="Event end date")

    # Location
    city: ShortText | None = None
    country: ShortText | None = None
    venue: ShortText | None = None
    is_virtual: bool = Field(default=False)

    # Status
    status: EventStatus = Field(default="planning")

    # Notes
    notes: LongText | None = None

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v, info):
        """End date must be >= start date."""
        if v is not None and info.data.get("start_date"):
            if v < info.data["start_date"]:
                raise ValueError("End date must be >= start date")
        return v


class EventUpdate(BaseModel):
    """Update an event (partial)."""

    name: ShortText | None = None
    event_type: EventType | None = None
    description: MediumText | None = None
    start_date: date | None = None
    end_date: date | None = None
    city: ShortText | None = None
    country: ShortText | None = None
    venue: ShortText | None = None
    is_virtual: bool | None = None
    status: EventStatus | None = None
    notes: LongText | None = None


class EventResponse(BaseResponse):
    """Event response."""

    org_id: UUID
    name: str
    event_type: EventType
    description: str | None = None
    start_date: date
    end_date: date | None = None
    city: str | None = None
    country: str | None = None
    venue: str | None = None
    is_virtual: bool
    status: EventStatus
    notes: str | None = None

    # Computed
    attendee_count: int = 0


class EventAttendeeCreate(BaseModel):
    """Add attendee to event."""

    person_id: UUID | None = Field(default=None, description="Person attending")
    company_id: UUID | None = Field(default=None, description="Company attending")
    registration_status: RegistrationStatus = Field(default="registered")
    priority_level: PriorityLevel | None = None
    notes: MediumText | None = None

    @field_validator("company_id")
    @classmethod
    def require_person_or_company(cls, v, info):
        """At least one of person_id or company_id required."""
        if v is None and info.data.get("person_id") is None:
            raise ValueError("Either person_id or company_id is required")
        return v


# ============================================================================
# Touchpoints
# ============================================================================


class TouchpointCreate(BaseModel):
    """Log a touchpoint (interaction)."""

    # Who
    person_id: UUID | None = Field(default=None, description="Person contacted")
    company_id: UUID | None = Field(default=None, description="Company contacted")

    # Context
    event_id: UUID | None = Field(default=None, description="Related event if any")

    # Details
    touchpoint_type: TouchpointType = Field(description="Type of interaction")
    occurred_at: datetime = Field(description="When the interaction occurred")
    duration_minutes: int | None = Field(default=None, ge=0, le=1440)

    # Content
    summary: MediumText = Field(min_length=5, description="Brief summary of interaction")
    detailed_notes: LongText | None = None

    # Sentiment
    sentiment: Sentiment | None = None

    # Follow-up
    follow_up_required: bool = Field(default=False)
    follow_up_date: date | None = None

    @field_validator("company_id")
    @classmethod
    def require_person_or_company(cls, v, info):
        """At least one of person_id or company_id required."""
        if v is None and info.data.get("person_id") is None:
            raise ValueError("Either person_id or company_id is required")
        return v


class TouchpointResponse(BaseResponse):
    """Touchpoint response."""

    org_id: UUID
    person_id: UUID | None = None
    person_name: str | None = None
    company_id: UUID | None = None
    company_name: str | None = None
    event_id: UUID | None = None
    event_name: str | None = None

    touchpoint_type: TouchpointType
    occurred_at: datetime
    duration_minutes: int | None = None

    summary: str
    detailed_notes: str | None = None
    sentiment: Sentiment | None = None

    follow_up_required: bool
    follow_up_date: date | None = None

    # AI fields (M9)
    ai_sentiment: str | None = None
    ai_topics: list[str] | None = None

    created_by_name: str | None = None


# ============================================================================
# Tasks
# ============================================================================


class TaskCreate(BaseModel):
    """Create a follow-up task."""

    title: ShortText = Field(min_length=3, description="Task title")
    description: MediumText | None = None

    # Related entities
    person_id: UUID | None = None
    company_id: UUID | None = None
    event_id: UUID | None = None
    touchpoint_id: UUID | None = None

    # Assignment
    assigned_to: UUID | None = Field(default=None, description="Person to assign task to")

    # Timeline
    due_date: date | None = None
    reminder_date: date | None = None

    # Priority
    priority: TaskPriority = Field(default="medium")


class TaskUpdate(BaseModel):
    """Update a task (partial)."""

    title: ShortText | None = None
    description: MediumText | None = None
    assigned_to: UUID | None = None
    due_date: date | None = None
    reminder_date: date | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    completion_notes: MediumText | None = None


class TaskResponse(BaseResponse):
    """Task response."""

    org_id: UUID
    title: str
    description: str | None = None

    # Related
    person_id: UUID | None = None
    person_name: str | None = None
    company_id: UUID | None = None
    company_name: str | None = None
    event_id: UUID | None = None
    touchpoint_id: UUID | None = None

    # Assignment
    assigned_to: UUID | None = None
    assigned_to_name: str | None = None

    # Timeline
    due_date: date | None = None
    reminder_date: date | None = None

    # Status
    status: TaskStatus
    priority: TaskPriority

    # Completion
    completed_at: datetime | None = None
    completed_by_name: str | None = None
    completion_notes: str | None = None

    # Computed
    is_overdue: bool = False


class TaskComplete(BaseModel):
    """Mark task as complete."""

    completion_notes: MediumText | None = None
