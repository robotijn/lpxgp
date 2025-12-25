"""Authentication module for LPxGP.

This module provides session-based authentication for the LPxGP platform,
including user management, session handling, and route protection.

Features:
    - User registration and authentication
    - Session management via signed cookies
    - Route protection helpers
    - Mock user store for local development (replaceable with Supabase)

Example:
    Basic authentication flow::

        from src.auth import authenticate_user, login_response

        # Authenticate user
        user = authenticate_user("user@example.com", "password123")
        if user:
            return login_response(user)

Note:
    In production, replace the mock user store with Supabase queries
    and use proper password hashing (bcrypt/argon2).
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Literal, TypedDict

from fastapi import HTTPException, Request, Response
from fastapi.responses import RedirectResponse

if TYPE_CHECKING:
    pass


# =============================================================================
# Type Definitions
# =============================================================================


class UserData(TypedDict):
    """User data structure returned by authentication functions.

    Attributes:
        id: Unique user identifier (UUID string).
        email: User's email address (lowercase).
        name: User's display name.
        role: User role - 'gp', 'lp', or 'admin'.
        created_at: ISO format timestamp of account creation.
    """

    id: str
    email: str
    name: str
    role: Literal["gp", "lp", "admin", "fa"]
    created_at: str


class UserDataInternal(UserData):
    """Internal user data including password hash.

    Extends UserData with password_hash field for internal storage.
    Never expose this type externally.

    Attributes:
        password_hash: SHA-256 hash of salted password.
    """

    password_hash: str


class SessionData(TypedDict):
    """Session data structure stored in memory.

    Attributes:
        user_id: Reference to the user's ID.
        email: User's email for quick access.
        name: User's display name for quick access.
        role: User's role for authorization checks.
        created_at: Timestamp when session was created.
        expires_at: Timestamp when session expires.
    """

    user_id: str
    email: str
    name: str
    role: Literal["gp", "lp", "admin", "fa"]
    created_at: datetime
    expires_at: datetime


class CurrentUser(TypedDict):
    """Current user data extracted from session.

    Simplified user data for use in request handlers.

    Attributes:
        id: User's unique identifier.
        email: User's email address.
        name: User's display name.
        role: User's role for authorization.
    """

    id: str
    email: str
    name: str
    role: Literal["gp", "lp", "admin", "fa"]


class DemoUserConfig(TypedDict):
    """Configuration for demo user creation.

    Attributes:
        email: Demo user's email address.
        password: Demo user's plain text password.
        name: Demo user's display name.
        role: Demo user's role.
    """

    email: str
    password: str
    name: str
    role: Literal["gp", "lp", "admin", "fa"]


# Type alias for user roles
UserRole = Literal["gp", "lp", "admin", "fa"]


# =============================================================================
# Constants
# =============================================================================

# Session cookie configuration
SESSION_COOKIE_NAME: str = "lpxgp_session"
"""Name of the session cookie set in browser."""

SESSION_DURATION_HOURS: int = 24
"""Duration in hours before session expires."""

# Password hashing salt (in production, use per-user salts)
_PASSWORD_SALT: str = "lpxgp_salt_v1"
"""Salt used for password hashing. In production, use per-user salts."""


# =============================================================================
# In-Memory Storage (Mock Database)
# =============================================================================

# In-memory user store: {email: UserDataInternal}
# In production, replace with Supabase queries
_mock_users: dict[str, UserDataInternal] = {}

# In-memory sessions: {session_id: SessionData}
# In production, use Redis or database-backed sessions
_sessions: dict[str, SessionData] = {}


# =============================================================================
# Password Utilities
# =============================================================================


def _hash_password(password: str) -> str:
    """Hash a password using SHA-256 with a salt.

    Args:
        password: Plain text password to hash.

    Returns:
        Hexadecimal string of the hashed password.

    Note:
        In production, use bcrypt or argon2 instead of SHA-256.
        This implementation is for demonstration purposes only.

    Example:
        >>> _hash_password("mypassword")
        'a1b2c3d4...'  # 64-character hex string
    """
    salted_password = f"{_PASSWORD_SALT}{password}"
    return hashlib.sha256(salted_password.encode()).hexdigest()


def _verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash.

    Args:
        password: Plain text password to verify.
        password_hash: Previously hashed password to compare against.

    Returns:
        True if password matches the hash, False otherwise.

    Example:
        >>> hashed = _hash_password("mypassword")
        >>> _verify_password("mypassword", hashed)
        True
        >>> _verify_password("wrongpassword", hashed)
        False
    """
    return _hash_password(password) == password_hash


def _sanitize_user(user: UserDataInternal) -> UserData:
    """Remove sensitive fields from user data.

    Creates a copy of user data without the password_hash field,
    safe for returning to clients.

    Args:
        user: Internal user data including password hash.

    Returns:
        User data without sensitive fields.
    """
    return UserData(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        role=user["role"],
        created_at=user["created_at"],
    )


# =============================================================================
# User Management
# =============================================================================


def create_user(
    email: str,
    password: str,
    name: str,
    role: UserRole = "gp",
) -> UserData:
    """Create a new user account.

    Registers a new user with the provided credentials. Email addresses
    are normalized to lowercase and stripped of whitespace.

    Args:
        email: User's email address (will be lowercased).
        password: Plain text password (will be hashed).
        name: User's display name.
        role: User role, one of 'gp', 'lp', 'admin', or 'fa'. Defaults to 'gp'.

    Returns:
        Created user data (without password hash).

    Raises:
        ValueError: If email is already registered.

    Example:
        >>> user = create_user(
        ...     email="john@example.com",
        ...     password="securepassword123",
        ...     name="John Smith",
        ...     role="gp"
        ... )
        >>> print(user["email"])
        'john@example.com'
    """
    # Normalize email
    normalized_email = email.lower().strip()

    # Check for existing user
    if normalized_email in _mock_users:
        raise ValueError("Email already registered")

    # Generate unique ID
    from uuid import uuid4

    user_id = str(uuid4())

    # Create user record
    user: UserDataInternal = {
        "id": user_id,
        "email": normalized_email,
        "password_hash": _hash_password(password),
        "name": name,
        "role": role,
        "created_at": datetime.now(UTC).isoformat(),
    }

    # Store user
    _mock_users[normalized_email] = user

    # Return sanitized user data
    return _sanitize_user(user)


def authenticate_user(email: str, password: str) -> UserData | None:
    """Authenticate a user with email and password.

    Attempts to authenticate a user by verifying their credentials.
    Email comparison is case-insensitive.

    Args:
        email: User's email address.
        password: User's plain text password.

    Returns:
        User data if authentication successful, None if credentials
        are invalid or user doesn't exist.

    Example:
        >>> user = authenticate_user("john@example.com", "password123")
        >>> if user:
        ...     print(f"Welcome, {user['name']}!")
        ... else:
        ...     print("Invalid credentials")
    """
    # Normalize email
    normalized_email = email.lower().strip()

    # Look up user
    user = _mock_users.get(normalized_email)
    if not user:
        return None

    # Verify password
    if not _verify_password(password, user["password_hash"]):
        return None

    # Return sanitized user data
    return _sanitize_user(user)


def get_user_by_id(user_id: str) -> UserData | None:
    """Retrieve a user by their unique ID.

    Args:
        user_id: The user's UUID string.

    Returns:
        User data if found, None otherwise.

    Example:
        >>> user = get_user_by_id("550e8400-e29b-41d4-a716-446655440000")
        >>> if user:
        ...     print(user["name"])
    """
    for user in _mock_users.values():
        if user["id"] == user_id:
            return _sanitize_user(user)
    return None


def get_user_by_email(email: str) -> UserData | None:
    """Retrieve a user by their email address.

    Email lookup is case-insensitive.

    Args:
        email: The user's email address.

    Returns:
        User data if found, None otherwise.

    Example:
        >>> user = get_user_by_email("john@example.com")
        >>> if user:
        ...     print(f"Found user: {user['name']}")
    """
    normalized_email = email.lower().strip()
    user = _mock_users.get(normalized_email)
    if user:
        return _sanitize_user(user)
    return None


# =============================================================================
# Session Management
# =============================================================================


def create_session(user: UserData) -> str:
    """Create a new session for an authenticated user.

    Generates a cryptographically secure session ID and stores
    session data in memory.

    Args:
        user: Authenticated user data.

    Returns:
        Session ID string (to be stored in cookie).

    Example:
        >>> user = authenticate_user("john@example.com", "password")
        >>> if user:
        ...     session_id = create_session(user)
        ...     # Store session_id in cookie
    """
    # Generate secure session ID
    session_id = secrets.token_urlsafe(32)

    # Calculate expiration time
    now = datetime.now(UTC)
    expires_at = now + timedelta(hours=SESSION_DURATION_HOURS)

    # Store session data
    _sessions[session_id] = SessionData(
        user_id=user["id"],
        email=user["email"],
        name=user["name"],
        role=user["role"],
        created_at=now,
        expires_at=expires_at,
    )

    return session_id


def get_session(session_id: str) -> SessionData | None:
    """Retrieve a session by ID if valid and not expired.

    Automatically cleans up expired sessions.

    Args:
        session_id: The session ID from cookie.

    Returns:
        Session data if valid and not expired, None otherwise.

    Example:
        >>> session = get_session("abc123...")
        >>> if session:
        ...     print(f"Session for user: {session['email']}")
    """
    if not session_id:
        return None

    session = _sessions.get(session_id)
    if not session:
        return None

    # Check expiration
    if datetime.now(UTC) > session["expires_at"]:
        # Session expired, clean up
        del _sessions[session_id]
        return None

    return session


def delete_session(session_id: str) -> None:
    """Delete a session (logout).

    Removes the session from storage. Safe to call with
    non-existent session IDs.

    Args:
        session_id: The session ID to delete.

    Example:
        >>> delete_session("abc123...")  # Session removed
        >>> delete_session("nonexistent")  # No error
    """
    if session_id in _sessions:
        del _sessions[session_id]


def get_current_user(request: Request) -> CurrentUser | None:
    """Extract the current user from a request's session cookie.

    Reads the session cookie, validates the session, and returns
    the associated user data.

    Args:
        request: FastAPI Request object.

    Returns:
        Current user data if authenticated, None otherwise.

    Example:
        >>> @app.get("/profile")
        ... async def profile(request: Request):
        ...     user = get_current_user(request)
        ...     if not user:
        ...         return RedirectResponse("/login")
        ...     return {"user": user}
    """
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return None

    session = get_session(session_id)
    if not session:
        return None

    return CurrentUser(
        id=session["user_id"],
        email=session["email"],
        name=session["name"],
        role=session["role"],
    )


# =============================================================================
# Response Helpers
# =============================================================================


def login_response(
    user: UserData,
    redirect_to: str = "/dashboard",
    request: Request | None = None,
) -> Response | RedirectResponse:
    """Create a login response with session cookie.

    Creates a new session for the user and returns a redirect response
    with the session cookie set. Handles both HTMX and regular requests.

    Args:
        user: Authenticated user data.
        redirect_to: URL to redirect to after login. Defaults to "/dashboard".
        request: Optional request object to detect HTMX requests.

    Returns:
        Response with HX-Redirect for HTMX, or RedirectResponse for regular requests.

    Example:
        >>> user = authenticate_user(email, password)
        >>> if user:
        ...     return login_response(user, request=request)
    """
    session_id = create_session(user)

    # Check if this is an HTMX request
    is_htmx = request and request.headers.get("HX-Request") == "true"

    if is_htmx:
        # HTMX needs 200 with HX-Redirect header to follow redirects
        response = Response(
            status_code=200,
            headers={"HX-Redirect": redirect_to}
        )
    else:
        # Standard HTTP redirect for non-HTMX requests
        response = RedirectResponse(url=redirect_to, status_code=303)

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,  # Prevent JavaScript access
        secure=False,  # Set True in production with HTTPS
        samesite="lax",  # CSRF protection
        max_age=SESSION_DURATION_HOURS * 3600,  # Convert to seconds
    )

    return response


def logout_response(
    request: Request,
    redirect_to: str = "/",
) -> RedirectResponse:
    """Create a logout response, clearing the session.

    Deletes the server-side session and clears the session cookie.

    Args:
        request: FastAPI Request object (to read current session).
        redirect_to: URL to redirect to after logout. Defaults to "/".

    Returns:
        RedirectResponse with session cookie cleared.

    Example:
        >>> @app.get("/logout")
        ... async def logout(request: Request):
        ...     return logout_response(request)
    """
    # Delete server-side session
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        delete_session(session_id)

    # Create redirect response with cleared cookie
    response = RedirectResponse(url=redirect_to, status_code=303)
    response.delete_cookie(SESSION_COOKIE_NAME)

    return response


# =============================================================================
# Route Protection
# =============================================================================


def require_auth(request: Request) -> CurrentUser:
    """Require authentication for a route.

    Use this function to protect routes that require authentication.

    Args:
        request: FastAPI Request object.

    Returns:
        Current user data if authenticated.

    Raises:
        HTTPException: 401 error if not authenticated.

    Example:
        >>> @app.get("/protected")
        ... async def protected_route(request: Request):
        ...     user = require_auth(request)
        ...     return {"message": f"Hello, {user['name']}!"}
    """
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_role(request: Request, *roles: UserRole) -> CurrentUser:
    """Require specific role(s) for a route.

    Use this function to protect routes that require specific user roles.
    User must be authenticated AND have one of the specified roles.

    Args:
        request: FastAPI Request object.
        *roles: One or more allowed roles ('gp', 'lp', 'admin').

    Returns:
        Current user data if authenticated with correct role.

    Raises:
        HTTPException: 401 if not authenticated, 403 if wrong role.

    Example:
        >>> @app.get("/admin/users")
        ... async def admin_users(request: Request):
        ...     user = require_role(request, "admin")
        ...     return {"admin": user["name"]}
        ...
        >>> @app.get("/gp-or-admin")
        ... async def gp_or_admin(request: Request):
        ...     user = require_role(request, "gp", "admin")
        ...     return {"user": user}
    """
    user = require_auth(request)
    if user["role"] not in roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return user


# =============================================================================
# Demo Users (Local Development)
# =============================================================================


def init_demo_users() -> None:
    """Initialize demo users for local development.

    Creates four demo accounts if they don't already exist:
        - gp@demo.com (password: demo123) - GP role
        - lp@demo.com (password: demo123) - LP role
        - fa@demo.com (password: demo123) - FA role (Fund Advisor)
        - admin@demo.com (password: admin123) - Admin role

    This function is called automatically on module import.
    In production, this should be disabled or removed.
    """
    demo_users: list[DemoUserConfig] = [
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
            "email": "fa@demo.com",
            "password": "demo123",
            "name": "Demo Fund Advisor",
            "role": "fa",
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
            # User already exists, skip
            pass


# Initialize demo users on module load
init_demo_users()
