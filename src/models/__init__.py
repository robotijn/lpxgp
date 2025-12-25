"""LPxGP Pydantic Models - Request/Response validation."""

from src.models.auth import (
    InvitationAcceptRequest,
    InvitationRequest,
    LoginRequest,
    PasswordResetRequest,
)
from src.models.base import BaseModel, BaseResponse
from src.models.funds import (
    FundCreate,
    FundResponse,
    FundTeamMemberCreate,
    FundUpdate,
)
from src.models.ir import (
    EventCreate,
    EventResponse,
    EventUpdate,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
    TouchpointCreate,
    TouchpointResponse,
)
from src.models.lp import (
    LPProfileResponse,
    LPProfileUpdate,
    LPSearchRequest,
)
from src.models.matching import (
    MatchGenerateRequest,
    MatchResponse,
    MatchStatusUpdate,
)
from src.models.pitch import (
    PitchFeedback,
    PitchGenerateRequest,
    PitchResponse,
)
from src.models.responses import (
    APIResponse,
    ErrorResponse,
    PaginatedResponse,
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
