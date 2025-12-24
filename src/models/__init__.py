"""LPxGP Pydantic Models - Request/Response validation."""

from src.models.base import BaseModel, BaseResponse
from src.models.auth import (
    LoginRequest,
    InvitationRequest,
    InvitationAcceptRequest,
    PasswordResetRequest,
)
from src.models.funds import (
    FundCreate,
    FundUpdate,
    FundResponse,
    FundTeamMemberCreate,
)
from src.models.lp import (
    LPSearchRequest,
    LPProfileResponse,
    LPProfileUpdate,
)
from src.models.matching import (
    MatchGenerateRequest,
    MatchResponse,
    MatchStatusUpdate,
)
from src.models.pitch import (
    PitchGenerateRequest,
    PitchResponse,
    PitchFeedback,
)
from src.models.ir import (
    EventCreate,
    EventUpdate,
    EventResponse,
    TouchpointCreate,
    TouchpointResponse,
    TaskCreate,
    TaskUpdate,
    TaskResponse,
)
from src.models.responses import (
    APIResponse,
    PaginatedResponse,
    ErrorResponse,
)

__all__ = [
    # Base
    "BaseModel",
    "BaseResponse",
    # Auth
    "LoginRequest",
    "InvitationRequest",
    "InvitationAcceptRequest",
    "PasswordResetRequest",
    # Funds
    "FundCreate",
    "FundUpdate",
    "FundResponse",
    "FundTeamMemberCreate",
    # LP
    "LPSearchRequest",
    "LPProfileResponse",
    "LPProfileUpdate",
    # Matching
    "MatchGenerateRequest",
    "MatchResponse",
    "MatchStatusUpdate",
    # Pitch
    "PitchGenerateRequest",
    "PitchResponse",
    "PitchFeedback",
    # IR
    "EventCreate",
    "EventUpdate",
    "EventResponse",
    "TouchpointCreate",
    "TouchpointResponse",
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    # Responses
    "APIResponse",
    "PaginatedResponse",
    "ErrorResponse",
]
