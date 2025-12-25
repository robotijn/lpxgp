"""Authentication module for LPxGP.

Provides session-based authentication with:
- Login/Register/Logout functionality
- Session management via signed cookies
- Route protection decorator
- Mock user store for local development (replaceable with Supabase)
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Optional
from uuid import uuid4

from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse


# -----------------------------------------------------------------------------
# Mock User Store (for local development without database)
# In production, replace with Supabase queries
# -----------------------------------------------------------------------------

# In-memory user store: {email: {id, email, password_hash, name, role, created_at}}
_mock_users: dict[str, dict] = {}

# In-memory sessions: {session_id: {user_id, email, created_at, expires_at}}
_sessions: dict[str, dict] = {}


def _hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = "lpxgp_salt_v1"  # In production, use per-user salt
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def _verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    return _hash_password(password) == password_hash


# -----------------------------------------------------------------------------
# User Management
# -----------------------------------------------------------------------------

def create_user(email: str, password: str, name: str, role: str = "gp") -> dict:
    """Create a new user.

    Args:
        email: User email (unique identifier)
        password: Plain text password (will be hashed)
        name: Display name
        role: User role (gp, lp, admin)

    Returns:
        User dict (without password_hash)

    Raises:
        ValueError: If email already exists
    """
    email = email.lower().strip()

    if email in _mock_users:
        raise ValueError("Email already registered")

    user = {
        "id": str(uuid4()),
        "email": email,
        "password_hash": _hash_password(password),
        "name": name,
        "role": role,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    _mock_users[email] = user

    # Return user without password_hash
    return {k: v for k, v in user.items() if k != "password_hash"}


def authenticate_user(email: str, password: str) -> Optional[dict]:
    """Authenticate user with email and password.

    Returns:
        User dict if authentication successful, None otherwise
    """
    email = email.lower().strip()
    user = _mock_users.get(email)

    if not user:
        return None

    if not _verify_password(password, user["password_hash"]):
        return None

    return {k: v for k, v in user.items() if k != "password_hash"}


def get_user_by_id(user_id: str) -> Optional[dict]:
    """Get user by ID."""
    for user in _mock_users.values():
        if user["id"] == user_id:
            return {k: v for k, v in user.items() if k != "password_hash"}
    return None


def get_user_by_email(email: str) -> Optional[dict]:
    """Get user by email."""
    email = email.lower().strip()
    user = _mock_users.get(email)
    if user:
        return {k: v for k, v in user.items() if k != "password_hash"}
    return None


# -----------------------------------------------------------------------------
# Session Management
# -----------------------------------------------------------------------------

SESSION_COOKIE_NAME = "lpxgp_session"
SESSION_DURATION_HOURS = 24


def create_session(user: dict) -> str:
    """Create a new session for user.

    Returns:
        Session ID (to be stored in cookie)
    """
    session_id = secrets.token_urlsafe(32)

    _sessions[session_id] = {
        "user_id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=SESSION_DURATION_HOURS),
    }

    return session_id


def get_session(session_id: str) -> Optional[dict]:
    """Get session by ID if valid and not expired."""
    if not session_id:
        return None

    session = _sessions.get(session_id)
    if not session:
        return None

    if datetime.now(timezone.utc) > session["expires_at"]:
        # Session expired, clean up
        del _sessions[session_id]
        return None

    return session


def delete_session(session_id: str) -> None:
    """Delete a session (logout)."""
    if session_id in _sessions:
        del _sessions[session_id]


def get_current_user(request: Request) -> Optional[dict]:
    """Get current user from request session.

    Returns:
        User dict if authenticated, None otherwise
    """
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return None

    session = get_session(session_id)
    if not session:
        return None

    return {
        "id": session["user_id"],
        "email": session["email"],
        "name": session["name"],
        "role": session["role"],
    }


# -----------------------------------------------------------------------------
# Response Helpers
# -----------------------------------------------------------------------------

def login_response(user: dict, redirect_to: str = "/dashboard") -> RedirectResponse:
    """Create login response with session cookie."""
    session_id = create_session(user)

    response = RedirectResponse(url=redirect_to, status_code=303)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        secure=False,  # Set True in production with HTTPS
        samesite="lax",
        max_age=SESSION_DURATION_HOURS * 3600,
    )

    return response


def logout_response(request: Request, redirect_to: str = "/") -> RedirectResponse:
    """Create logout response, clearing session."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        delete_session(session_id)

    response = RedirectResponse(url=redirect_to, status_code=303)
    response.delete_cookie(SESSION_COOKIE_NAME)

    return response


# -----------------------------------------------------------------------------
# Route Protection
# -----------------------------------------------------------------------------

def require_auth(request: Request) -> dict:
    """Check if user is authenticated.

    Returns:
        Current user dict

    Raises:
        HTTPException: If not authenticated
    """
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_role(request: Request, *roles: str) -> dict:
    """Check if user has required role.

    Args:
        request: FastAPI request
        *roles: Allowed roles

    Returns:
        Current user dict

    Raises:
        HTTPException: If not authenticated or wrong role
    """
    user = require_auth(request)
    if user["role"] not in roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return user


# -----------------------------------------------------------------------------
# Demo Users (for local development)
# -----------------------------------------------------------------------------

def init_demo_users():
    """Initialize demo users for local development."""
    demo_users = [
        {
            "email": "gp@demo.com",
            "password": "demo123",
            "name": "Demo GP User",
            "role": "gp",
        },
        {
            "email": "lp@demo.com",
            "password": "demo123",
            "name": "Demo LP User",
            "role": "lp",
        },
        {
            "email": "admin@demo.com",
            "password": "admin123",
            "name": "Admin User",
            "role": "admin",
        },
    ]

    for user_data in demo_users:
        try:
            create_user(**user_data)
        except ValueError:
            pass  # User already exists


# Initialize demo users on module load
init_demo_users()
