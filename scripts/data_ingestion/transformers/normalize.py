"""
Data normalization utilities.
"""
import re
from urllib.parse import urlparse


def normalize_name(name: str | None) -> str | None:
    """
    Normalize organization or person name.
    - Strip whitespace
    - Normalize multiple spaces to single
    - Title case (optional, disabled by default)
    """
    if not name:
        return None
    # Clean whitespace
    name = " ".join(name.split())
    return name if name else None


def normalize_email(email: str | None) -> str | None:
    """
    Normalize email address.
    - Lowercase
    - Strip whitespace
    - Basic format validation
    """
    if not email:
        return None
    email = email.strip().lower()
    # Basic email pattern
    if not re.match(r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$", email):
        return None
    return email


def normalize_url(url: str | None) -> str | None:
    """
    Normalize URL.
    - Add https:// if missing scheme
    - Lowercase domain
    - Strip trailing slashes
    - Return None if invalid
    """
    if not url:
        return None
    url = url.strip()
    if not url:
        return None

    # Add scheme if missing
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return None
        # Reconstruct with lowercase domain
        normalized = f"{parsed.scheme}://{parsed.netloc.lower()}"
        if parsed.path and parsed.path != "/":
            normalized += parsed.path.rstrip("/")
        return normalized
    except Exception:
        return None


def normalize_linkedin_url(url: str | None) -> str | None:
    """
    Normalize LinkedIn profile URL.
    - Extract username/ID
    - Return standardized format
    """
    if not url:
        return None
    url = url.strip()
    if not url:
        return None

    # Handle various LinkedIn URL formats
    patterns = [
        r"linkedin\.com/in/([a-zA-Z0-9_-]+)",
        r"linkedin\.com/pub/([a-zA-Z0-9_/-]+)",
        r"linkedin\.com/profile/([a-zA-Z0-9_-]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            username = match.group(1).rstrip("/")
            return f"https://www.linkedin.com/in/{username}"

    # If it looks like a LinkedIn URL but doesn't match patterns, return as-is
    if "linkedin.com" in url.lower():
        return normalize_url(url)

    return None
