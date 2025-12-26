"""Authentication routes for login, registration, and logout.

This router provides:
- /login: Login page
- /register: Registration page
- /api/auth/login: Login form handler
- /api/auth/register: Registration form handler
- /logout: Logout handler
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from src import auth

router = APIRouter(tags=["auth"])

# Templates - need to use the same templates as main
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/login", response_class=HTMLResponse, response_model=None)
async def login_page(request: Request) -> HTMLResponse | RedirectResponse:
    """Render the login page.

    Redirects authenticated users to the dashboard.

    Args:
        request: FastAPI request object.

    Returns:
        Login page HTML or redirect to dashboard if already authenticated.
    """
    user = auth.get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=303)

    return templates.TemplateResponse(
        request,
        "pages/login.html",
        {"title": "Login - LPxGP"},
    )


@router.get("/register", response_class=HTMLResponse, response_model=None)
async def register_page(request: Request) -> HTMLResponse | RedirectResponse:
    """Render the registration page.

    Redirects authenticated users to the dashboard.

    Args:
        request: FastAPI request object.

    Returns:
        Registration page HTML or redirect to dashboard if already authenticated.
    """
    user = auth.get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=303)

    return templates.TemplateResponse(
        request,
        "pages/register.html",
        {"title": "Register - LPxGP"},
    )


@router.post("/api/auth/login", response_model=None)
async def api_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
) -> HTMLResponse | RedirectResponse | Response:
    """Handle login form submission via HTMX.

    Authenticates the user and either redirects to dashboard on success
    or returns an error partial for HTMX to display.

    Args:
        request: FastAPI request object.
        email: User's email address from form.
        password: User's password from form.

    Returns:
        Redirect to dashboard on success, or error HTML partial on failure.
    """
    user = auth.authenticate_user(email, password)

    if not user:
        # HTMX ignores non-2xx responses by default, so return 200 for HTMX
        # but 401 for regular requests (API clients, unit tests)
        is_htmx = request.headers.get("HX-Request") == "true"
        return templates.TemplateResponse(
            request,
            "partials/auth_error.html",
            {"error": "Invalid email or password"},
            status_code=200 if is_htmx else 401,
        )

    return auth.login_response(user, redirect_to="/dashboard", request=request)


@router.post("/api/auth/register", response_model=None)
async def api_register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    role: str = Form(default="gp"),
) -> HTMLResponse | RedirectResponse | Response:
    """Handle registration form submission via HTMX.

    Creates a new user account and logs them in on success.

    Args:
        request: FastAPI request object.
        email: User's email address from form.
        password: User's password from form.
        name: User's display name from form.
        role: User role ('gp', 'lp', or 'admin'). Defaults to 'gp'.

    Returns:
        Redirect to dashboard on success, or error HTML partial on failure.
    """
    try:
        # Validate and cast role to UserRole
        validated_role: auth.UserRole
        if role == "lp":
            validated_role = "lp"
        elif role == "admin":
            validated_role = "admin"
        else:
            validated_role = "gp"
        user = auth.create_user(email=email, password=password, name=name, role=validated_role)
        return auth.login_response(user, redirect_to="/dashboard", request=request)
    except ValueError as e:
        return templates.TemplateResponse(
            request,
            "partials/auth_error.html",
            {"error": str(e)},
            status_code=400,
        )


@router.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    """Handle user logout.

    Clears the session and redirects to the home page.

    Args:
        request: FastAPI request object.

    Returns:
        Redirect to home page with cleared session cookie.
    """
    return auth.logout_response(request, redirect_to="/")
