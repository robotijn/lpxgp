"""CRM/IR feature routes for events, touchpoints, and tasks.

This router provides:
- /events: Events management page
- /api/events: CRUD operations for events
- /touchpoints: Touchpoints/interactions log
- /api/touchpoints: Create touchpoints
- /tasks: Task management page
- /api/tasks: CRUD operations for tasks
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src import auth
from src.database import get_db
from src.logging_config import get_logger
from src.utils import is_valid_uuid

logger = get_logger(__name__)

router = APIRouter(tags=["crm"])

# Templates setup
templates_path = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=templates_path)


# =============================================================================
# Events
# =============================================================================


@router.get("/events", response_class=HTMLResponse, response_model=None)
async def events_page(request: Request) -> HTMLResponse | RedirectResponse:
    """Events management page for IR team.

    Lists all events with filtering and CRUD operations.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Default empty state
    events: list[dict[str, Any]] = []
    upcoming_count = 0
    past_count = 0

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        e.*,
                        COUNT(DISTINCT ea.id) as attendee_count
                    FROM events e
                    LEFT JOIN event_attendance ea ON ea.event_id = e.id
                    GROUP BY e.id
                    ORDER BY e.start_date DESC NULLS LAST
                    """
                )
                events = cur.fetchall()

                # Count upcoming vs past
                today = date.today()
                for event in events:
                    if event.get("start_date"):
                        if event["start_date"] >= today:
                            upcoming_count += 1
                        else:
                            past_count += 1
        finally:
            conn.close()

    return templates.TemplateResponse(
        request,
        "pages/events.html",
        {
            "title": "Events - LPxGP",
            "user": user,
            "events": events,
            "upcoming_count": upcoming_count,
            "past_count": past_count,
        },
    )


@router.post("/api/events", response_class=HTMLResponse)
async def create_event(
    request: Request,
    name: str = Form(...),
    event_type: str = Form("conference"),
    start_date: str | None = Form(None),
    end_date: str | None = Form(None),
    city: str | None = Form(None),
    country: str | None = Form(None),
    notes: str | None = Form(None),
) -> HTMLResponse:
    """Create a new event."""
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(content="<div>Not authenticated</div>", status_code=401)

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content='<div class="text-yellow-500">Database unavailable</div>',
            status_code=503,
        )

    try:
        with conn.cursor() as cur:
            # Get user's org_id
            cur.execute(
                "SELECT org_id FROM people WHERE auth_user_id = %s",
                (user.get("id"),),
            )
            person = cur.fetchone()
            org_id = person["org_id"] if person else None

            if not org_id:
                # Create a default org if none exists
                cur.execute("SELECT id FROM organizations LIMIT 1")
                org = cur.fetchone()
                org_id = org["id"] if org else None

            cur.execute(
                """
                INSERT INTO events (
                    org_id, name, event_type, start_date, end_date,
                    city, country, notes, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'planning')
                RETURNING id
                """,
                (
                    org_id,
                    name,
                    event_type,
                    start_date or None,
                    end_date or None,
                    city,
                    country,
                    notes,
                ),
            )
            cur.fetchone()  # Consume the RETURNING result
            conn.commit()

            return HTMLResponse(
                content=f"""
                <div class="text-center p-4">
                    <div class="text-green-500 text-lg mb-2">✓ Event Created</div>
                    <p class="text-navy-600">{name}</p>
                    <script>
                        setTimeout(() => window.location.href = '/events', 1500);
                    </script>
                </div>
                """,
            )
    except Exception as e:
        logger.error(f"Event creation error: {e}")
        return HTMLResponse(
            content=f'<div class="text-red-500">Error: {e}</div>',
            status_code=500,
        )
    finally:
        conn.close()


@router.get("/api/events/{event_id}", response_class=HTMLResponse)
async def get_event_detail(request: Request, event_id: str) -> HTMLResponse:
    """Get event detail modal content."""
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(content="<div>Not authenticated</div>", status_code=401)

    if not is_valid_uuid(event_id):
        return HTMLResponse(
            content='<div class="text-red-500">Invalid event ID</div>',
            status_code=400,
        )

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content='<div class="text-yellow-500">Database unavailable</div>',
            status_code=503,
        )

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT e.*,
                    COUNT(DISTINCT ea.id) as attendee_count
                FROM events e
                LEFT JOIN event_attendance ea ON ea.event_id = e.id
                WHERE e.id = %s
                GROUP BY e.id
                """,
                (event_id,),
            )
            event = cur.fetchone()

            if not event:
                return HTMLResponse(
                    content='<div class="text-red-500">Event not found</div>',
                    status_code=404,
                )

            # Get attendees
            cur.execute(
                """
                SELECT ea.*, p.full_name, o.name as org_name
                FROM event_attendance ea
                LEFT JOIN people p ON p.id = ea.person_id
                LEFT JOIN organizations o ON o.id = ea.company_id
                WHERE ea.event_id = %s
                """,
                (event_id,),
            )
            attendees = cur.fetchall()

            return templates.TemplateResponse(
                request,
                "partials/event_detail_modal.html",
                {"event": event, "attendees": attendees},
            )
    finally:
        conn.close()


@router.delete("/api/events/{event_id}", response_class=HTMLResponse)
async def delete_event(request: Request, event_id: str) -> HTMLResponse:
    """Delete an event."""
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(content="<div>Not authenticated</div>", status_code=401)

    if not is_valid_uuid(event_id):
        return HTMLResponse(
            content='<div class="text-red-500">Invalid event ID</div>',
            status_code=400,
        )

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content='<div class="text-yellow-500">Database unavailable</div>',
            status_code=503,
        )

    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM events WHERE id = %s", (event_id,))
            conn.commit()

            return HTMLResponse(
                content="""
                <div class="text-center p-4">
                    <div class="text-green-500">Event deleted</div>
                    <script>
                        document.body.dispatchEvent(new Event('eventDeleted'));
                        setTimeout(() => window.location.reload(), 1000);
                    </script>
                </div>
                """,
            )
    except Exception as e:
        logger.error(f"Event deletion error: {e}")
        return HTMLResponse(
            content=f'<div class="text-red-500">Error: {e}</div>',
            status_code=500,
        )
    finally:
        conn.close()


# =============================================================================
# Touchpoints
# =============================================================================


@router.get("/touchpoints", response_class=HTMLResponse, response_model=None)
async def touchpoints_page(request: Request) -> HTMLResponse | RedirectResponse:
    """Touchpoints/interactions log page."""
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    touchpoints: list[dict[str, Any]] = []

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        t.*,
                        p.full_name as person_name,
                        o.name as company_name,
                        e.name as event_name
                    FROM touchpoints t
                    LEFT JOIN people p ON p.id = t.person_id
                    LEFT JOIN organizations o ON o.id = t.company_id
                    LEFT JOIN events e ON e.id = t.event_id
                    ORDER BY t.occurred_at DESC
                    LIMIT 100
                    """
                )
                touchpoints = cur.fetchall()
        finally:
            conn.close()

    return templates.TemplateResponse(
        request,
        "pages/touchpoints.html",
        {
            "title": "Touchpoints - LPxGP",
            "user": user,
            "touchpoints": touchpoints,
        },
    )


@router.post("/api/touchpoints", response_class=HTMLResponse)
async def create_touchpoint(
    request: Request,
    touchpoint_type: str = Form(...),
    occurred_at: str = Form(...),
    summary: str | None = Form(None),
    person_id: str | None = Form(None),
    company_id: str | None = Form(None),
    sentiment: str | None = Form(None),
    follow_up_required: bool = Form(False),
) -> HTMLResponse:
    """Log a new touchpoint/interaction."""
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(content="<div>Not authenticated</div>", status_code=401)

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content='<div class="text-yellow-500">Database unavailable</div>',
            status_code=503,
        )

    try:
        with conn.cursor() as cur:
            # Get user's org_id
            cur.execute(
                "SELECT id, org_id FROM people WHERE auth_user_id = %s",
                (user.get("id"),),
            )
            person = cur.fetchone()
            org_id = person["org_id"] if person else None
            created_by = person["id"] if person else None

            if not org_id:
                cur.execute("SELECT id FROM organizations LIMIT 1")
                org = cur.fetchone()
                org_id = org["id"] if org else None

            cur.execute(
                """
                INSERT INTO touchpoints (
                    org_id, touchpoint_type, occurred_at, summary,
                    person_id, company_id, sentiment, follow_up_required,
                    created_by
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    org_id,
                    touchpoint_type,
                    occurred_at,
                    summary,
                    person_id if person_id and is_valid_uuid(person_id) else None,
                    company_id if company_id and is_valid_uuid(company_id) else None,
                    sentiment,
                    follow_up_required,
                    created_by,
                ),
            )
            conn.commit()

            return HTMLResponse(
                content="""
                <div class="text-center p-4">
                    <div class="text-green-500 text-lg mb-2">✓ Touchpoint Logged</div>
                    <script>
                        setTimeout(() => window.location.href = '/touchpoints', 1500);
                    </script>
                </div>
                """,
            )
    except Exception as e:
        logger.error(f"Touchpoint creation error: {e}")
        return HTMLResponse(
            content=f'<div class="text-red-500">Error: {e}</div>',
            status_code=500,
        )
    finally:
        conn.close()


# =============================================================================
# Tasks
# =============================================================================


@router.get("/tasks", response_class=HTMLResponse, response_model=None)
async def tasks_page(request: Request) -> HTMLResponse | RedirectResponse:
    """Task management page."""
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    tasks: list[dict[str, Any]] = []
    pending_count = 0
    overdue_count = 0

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        t.*,
                        p.full_name as contact_name,
                        o.name as company_name,
                        e.name as event_name,
                        ap.full_name as assigned_name
                    FROM tasks t
                    LEFT JOIN people p ON p.id = t.person_id
                    LEFT JOIN organizations o ON o.id = t.company_id
                    LEFT JOIN events e ON e.id = t.event_id
                    LEFT JOIN people ap ON ap.id = t.assigned_to
                    ORDER BY
                        CASE t.priority
                            WHEN 'urgent' THEN 1
                            WHEN 'high' THEN 2
                            WHEN 'medium' THEN 3
                            ELSE 4
                        END,
                        t.due_date ASC NULLS LAST
                    """
                )
                tasks = cur.fetchall()

                today = date.today()
                for task in tasks:
                    if task["status"] in ("pending", "in_progress"):
                        pending_count += 1
                        if task.get("due_date") and task["due_date"] < today:
                            overdue_count += 1
        finally:
            conn.close()

    return templates.TemplateResponse(
        request,
        "pages/tasks.html",
        {
            "title": "Tasks - LPxGP",
            "user": user,
            "tasks": tasks,
            "pending_count": pending_count,
            "overdue_count": overdue_count,
        },
    )


@router.post("/api/tasks", response_class=HTMLResponse)
async def create_task(
    request: Request,
    title: str = Form(...),
    description: str | None = Form(None),
    due_date: str | None = Form(None),
    priority: str = Form("medium"),
    person_id: str | None = Form(None),
    company_id: str | None = Form(None),
) -> HTMLResponse:
    """Create a new task."""
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(content="<div>Not authenticated</div>", status_code=401)

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content='<div class="text-yellow-500">Database unavailable</div>',
            status_code=503,
        )

    try:
        with conn.cursor() as cur:
            # Get user's org_id and person_id
            cur.execute(
                "SELECT id, org_id FROM people WHERE auth_user_id = %s",
                (user.get("id"),),
            )
            person = cur.fetchone()
            org_id = person["org_id"] if person else None
            assigned_to = person["id"] if person else None

            if not org_id:
                cur.execute("SELECT id FROM organizations LIMIT 1")
                org = cur.fetchone()
                org_id = org["id"] if org else None

            cur.execute(
                """
                INSERT INTO tasks (
                    org_id, title, description, due_date, priority,
                    person_id, company_id, assigned_to, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')
                RETURNING id
                """,
                (
                    org_id,
                    title,
                    description,
                    due_date or None,
                    priority,
                    person_id if person_id and is_valid_uuid(person_id) else None,
                    company_id if company_id and is_valid_uuid(company_id) else None,
                    assigned_to,
                ),
            )
            conn.commit()

            return HTMLResponse(
                content="""
                <div class="text-center p-4">
                    <div class="text-green-500 text-lg mb-2">✓ Task Created</div>
                    <script>
                        setTimeout(() => window.location.href = '/tasks', 1500);
                    </script>
                </div>
                """,
            )
    except Exception as e:
        logger.error(f"Task creation error: {e}")
        return HTMLResponse(
            content=f'<div class="text-red-500">Error: {e}</div>',
            status_code=500,
        )
    finally:
        conn.close()


@router.put("/api/tasks/{task_id}/complete", response_class=HTMLResponse)
async def complete_task(request: Request, task_id: str) -> HTMLResponse:
    """Mark a task as complete."""
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(content="<div>Not authenticated</div>", status_code=401)

    if not is_valid_uuid(task_id):
        return HTMLResponse(
            content='<div class="text-red-500">Invalid task ID</div>',
            status_code=400,
        )

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content='<div class="text-yellow-500">Database unavailable</div>',
            status_code=503,
        )

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE tasks
                SET status = 'completed', completed_at = NOW()
                WHERE id = %s
                RETURNING title
                """,
                (task_id,),
            )
            result = cur.fetchone()
            conn.commit()

            if not result:
                return HTMLResponse(
                    content='<div class="text-red-500">Task not found</div>',
                    status_code=404,
                )

            return HTMLResponse(
                content="""
                <span class="px-2 py-1 text-xs bg-green-100 text-green-700 rounded-full">
                    Completed ✓
                </span>
                """,
            )
    except Exception as e:
        logger.error(f"Task complete error: {e}")
        return HTMLResponse(
            content=f'<div class="text-red-500">Error: {e}</div>',
            status_code=500,
        )
    finally:
        conn.close()
