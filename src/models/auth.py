"""Authentication and authorization models."""

from typing import Literal
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from src.models.base import BaseModel, ShortText


class LoginRequest(BaseModel):
    """Login request with email and password."""

    email: EmailStr = Field(description="User email address")
    password: str = Field(min_length=8, max_length=128, description="User password")

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Basic password strength validation."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class InvitationRequest(BaseModel):
    """Request to invite a new user to an organization."""

    email: EmailStr = Field(description="Email address to invite")
    role: Literal["admin", "member", "viewer"] = Field(
        default="member",
        description="Role to assign to the invited user",
    )
    message: ShortText | None = Field(
        default=None,
        description="Optional personal message to include in invitation",
    )


class InvitationAcceptRequest(BaseModel):
    """Request to accept an invitation."""

    token: str = Field(min_length=32, max_length=128, description="Invitation token")
    first_name: ShortText = Field(min_length=1, description="User's first name")
    last_name: ShortText = Field(min_length=1, description="User's last name")
    password: str = Field(min_length=8, max_length=128, description="New password")

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Same password validation as LoginRequest."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class PasswordResetRequest(BaseModel):
    """Request to reset password."""

    email: EmailStr = Field(description="Email address for password reset")


class PasswordResetConfirm(BaseModel):
    """Confirm password reset with token."""

    token: str = Field(min_length=32, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Same password validation."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserProfile(BaseModel):
    """User profile information."""

    id: UUID
    email: EmailStr
    first_name: ShortText
    last_name: ShortText
    role: Literal["admin", "member", "viewer", "fund_admin"]
    org_id: UUID
    org_name: ShortText
    is_super_admin: bool = False
