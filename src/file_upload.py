"""File upload utilities for handling pitch deck uploads.

This module provides functions to validate, save, and manage uploaded files,
with a focus on pitch deck uploads (PDF, PPTX).

Usage:
    from src.file_upload import validate_upload, save_upload

    is_valid, error = validate_upload(file)
    if is_valid:
        path = await save_upload(file, fund_id)
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile

from src.config import get_settings
from src.logging_config import get_logger

logger = get_logger(__name__)

# Upload directory relative to project root
UPLOAD_DIR = Path(__file__).parent.parent / "uploads" / "pitch_decks"

# MIME type mapping for validation
ALLOWED_MIME_TYPES: dict[str, list[str]] = {
    ".pdf": ["application/pdf"],
    ".pptx": [
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    ],
    ".ppt": ["application/vnd.ms-powerpoint"],
}


def ensure_upload_dir() -> Path:
    """Ensure the upload directory exists.

    Returns:
        Path to the upload directory.
    """
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOAD_DIR


def validate_upload(file: UploadFile) -> tuple[bool, str]:
    """Validate an uploaded file.

    Checks:
    - File has a filename
    - Extension is allowed (.pdf, .pptx, .ppt)
    - File size is within limits
    - MIME type matches extension (if provided)

    Args:
        file: The uploaded file from FastAPI.

    Returns:
        Tuple of (is_valid, error_message).
        If valid, error_message is empty string.

    Example:
        >>> is_valid, error = validate_upload(file)
        >>> if not is_valid:
        ...     return error_response(error)
    """
    settings = get_settings()

    # Check filename exists
    if not file.filename:
        return False, "No filename provided"

    # Check extension
    suffix = Path(file.filename).suffix.lower()
    if suffix not in settings.allowed_upload_extensions:
        allowed = ", ".join(settings.allowed_upload_extensions)
        return False, f"Invalid file type. Allowed: {allowed}"

    # Check MIME type if available
    if file.content_type:
        expected_mimes = ALLOWED_MIME_TYPES.get(suffix, [])
        if expected_mimes and file.content_type not in expected_mimes:
            logger.warning(
                f"MIME mismatch: expected {expected_mimes}, got {file.content_type}"
            )
            # Don't reject - some browsers send wrong MIME types

    # Check file size (need to read to check)
    # Note: For large files, consider streaming validation
    try:
        file.file.seek(0, 2)  # Seek to end
        size = file.file.tell()
        file.file.seek(0)  # Reset to beginning

        if size > settings.max_file_upload_bytes:
            max_mb = settings.max_file_upload_mb
            return False, f"File too large. Maximum size: {max_mb}MB"

        if size == 0:
            return False, "File is empty"

    except Exception as e:
        logger.error(f"Error checking file size: {e}")
        return False, "Could not validate file size"

    return True, ""


async def save_upload(file: UploadFile, fund_id: str) -> Path:
    """Save an uploaded file to disk.

    Files are saved with a unique name: {fund_id}_{timestamp}.{ext}

    Args:
        file: The uploaded file from FastAPI.
        fund_id: The fund ID to associate with this upload.

    Returns:
        Path to the saved file.

    Raises:
        ValueError: If file has no filename.
        IOError: If file cannot be saved.

    Example:
        >>> path = await save_upload(file, "fund-123")
        >>> path.exists()
        True
    """
    if not file.filename:
        raise ValueError("File has no filename")

    ensure_upload_dir()

    # Generate unique filename
    suffix = Path(file.filename).suffix.lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_fund_id = "".join(c for c in fund_id if c.isalnum() or c in "-_")
    filename = f"{safe_fund_id}_{timestamp}{suffix}"

    file_path = UPLOAD_DIR / filename

    try:
        # Save file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Saved upload: {file_path}")
        return file_path

    except Exception as e:
        logger.error(f"Failed to save upload: {e}")
        # Clean up partial file if exists
        if file_path.exists():
            file_path.unlink()
        raise OSError(f"Could not save file: {e}") from e


def delete_upload(file_path: Path) -> bool:
    """Delete an uploaded file.

    Args:
        file_path: Path to the file to delete.

    Returns:
        True if deleted successfully, False otherwise.
    """
    try:
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted upload: {file_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to delete upload {file_path}: {e}")
        return False


def get_upload_path(filename: str) -> Path | None:
    """Get the full path to an uploaded file.

    Args:
        filename: The filename (not full path).

    Returns:
        Full path if file exists, None otherwise.
    """
    file_path = UPLOAD_DIR / filename
    if file_path.exists():
        return file_path
    return None


def get_relative_url(file_path: Path) -> str:
    """Get the relative URL for an uploaded file.

    Args:
        file_path: Full path to the file.

    Returns:
        Relative URL path for serving the file.
    """
    return f"/uploads/pitch_decks/{file_path.name}"
