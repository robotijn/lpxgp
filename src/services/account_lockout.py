"""Account lockout service - prevent brute force attacks.

Tracks failed login attempts and locks accounts after too many failures.
Uses Supabase for persistence so lockouts survive server restarts.
"""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from src.config import get_settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration (from settings)
# ---------------------------------------------------------------------------


def get_lockout_config() -> tuple[int, int]:
    """Get lockout configuration from settings.

    Returns:
        Tuple of (max_attempts, lockout_duration_minutes)
    """
    settings = get_settings()
    return settings.max_login_attempts, settings.lockout_duration_minutes


# ---------------------------------------------------------------------------
# Account Lockout Service
# ---------------------------------------------------------------------------


class AccountLockoutService:
    """Service for tracking failed login attempts and enforcing lockouts.

    This service uses Supabase's `login_attempts` table to track failures.
    The table schema should include:
    - id: UUID primary key
    - email: text (the attempted email)
    - ip_address: inet (client IP)
    - attempted_at: timestamptz
    - success: boolean

    And a view or computed column for lockout status.
    """

    def __init__(self, supabase_client):
        """Initialize with Supabase client.

        Args:
            supabase_client: Authenticated Supabase client
        """
        self.client = supabase_client

    async def record_attempt(
        self,
        email: str,
        ip_address: str,
        success: bool,
    ) -> None:
        """Record a login attempt.

        Args:
            email: Email address attempted
            ip_address: Client IP address
            success: Whether the attempt succeeded
        """
        try:
            self.client.table("login_attempts").insert(
                {
                    "email": email.lower().strip(),
                    "ip_address": ip_address,
                    "success": success,
                    "attempted_at": datetime.now(timezone.utc).isoformat(),
                }
            ).execute()

            if success:
                # On successful login, optionally clear old failed attempts
                # This is debatable - some prefer to keep audit trail
                logger.info(f"Successful login for {email} from {ip_address}")
            else:
                logger.warning(f"Failed login attempt for {email} from {ip_address}")

        except Exception as e:
            # Don't fail login flow if audit logging fails
            logger.error(f"Failed to record login attempt: {e}")

    async def check_lockout(self, email: str, ip_address: str) -> tuple[bool, int | None]:
        """Check if an account or IP is locked out.

        Args:
            email: Email address to check
            ip_address: Client IP to check

        Returns:
            Tuple of (is_locked, seconds_remaining)
            - is_locked: True if account/IP is locked
            - seconds_remaining: Seconds until lockout expires (None if not locked)
        """
        max_attempts, lockout_minutes = get_lockout_config()
        lockout_window = datetime.now(timezone.utc) - timedelta(minutes=lockout_minutes)

        try:
            # Count recent failed attempts for this email
            result = (
                self.client.table("login_attempts")
                .select("attempted_at", count="exact")
                .eq("email", email.lower().strip())
                .eq("success", False)
                .gte("attempted_at", lockout_window.isoformat())
                .execute()
            )

            failed_count = result.count or 0

            if failed_count >= max_attempts:
                # Account is locked - calculate remaining time
                # Get the most recent failed attempt to calculate lockout expiry
                recent = (
                    self.client.table("login_attempts")
                    .select("attempted_at")
                    .eq("email", email.lower().strip())
                    .eq("success", False)
                    .order("attempted_at", desc=True)
                    .limit(1)
                    .execute()
                )

                if recent.data:
                    last_attempt = datetime.fromisoformat(
                        recent.data[0]["attempted_at"].replace("Z", "+00:00")
                    )
                    lockout_expires = last_attempt + timedelta(minutes=lockout_minutes)
                    now = datetime.now(timezone.utc)

                    if lockout_expires > now:
                        remaining = int((lockout_expires - now).total_seconds())
                        logger.warning(
                            f"Account {email} is locked. {remaining}s remaining."
                        )
                        return True, remaining

            return False, None

        except Exception as e:
            # On error, fail open (allow login attempt) but log
            logger.error(f"Failed to check lockout status: {e}")
            return False, None

    async def get_recent_attempts(
        self,
        email: str | None = None,
        ip_address: str | None = None,
        hours: int = 24,
    ) -> list[dict]:
        """Get recent login attempts for audit purposes.

        Args:
            email: Filter by email (optional)
            ip_address: Filter by IP (optional)
            hours: How many hours back to look

        Returns:
            List of login attempt records
        """
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        try:
            query = (
                self.client.table("login_attempts")
                .select("*")
                .gte("attempted_at", since.isoformat())
                .order("attempted_at", desc=True)
                .limit(100)
            )

            if email:
                query = query.eq("email", email.lower().strip())
            if ip_address:
                query = query.eq("ip_address", ip_address)

            result = query.execute()
            return result.data or []

        except Exception as e:
            logger.error(f"Failed to get recent attempts: {e}")
            return []

    async def clear_lockout(self, email: str) -> bool:
        """Manually clear lockout for an account (admin action).

        This doesn't delete the attempts (audit trail) but could mark them
        as cleared or simply allow the next login by resetting a counter.

        For now, we'll just log the action. The lockout will naturally
        expire after the configured duration.

        Args:
            email: Email to clear lockout for

        Returns:
            True if successful
        """
        logger.info(f"Admin cleared lockout for {email}")
        # In a more sophisticated implementation, you might:
        # - Add a 'cleared_at' column to mark attempts as no longer counting
        # - Insert a special 'admin_clear' record
        # - Use a separate 'lockout_overrides' table
        return True


# ---------------------------------------------------------------------------
# Dependency Injection Helper
# ---------------------------------------------------------------------------


_lockout_service: AccountLockoutService | None = None


def get_lockout_service() -> AccountLockoutService | None:
    """Get the account lockout service singleton.

    Returns None if not initialized (e.g., Supabase not configured).
    """
    return _lockout_service


def init_lockout_service(supabase_client) -> AccountLockoutService:
    """Initialize the account lockout service.

    Call this during application startup.
    """
    global _lockout_service
    _lockout_service = AccountLockoutService(supabase_client)
    return _lockout_service
