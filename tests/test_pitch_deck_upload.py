"""Tests for pitch deck upload functionality.

Tests cover:
- File upload validation (extension, size, MIME type)
- Text extraction from PDF and PPTX
- API endpoint authentication and authorization
- Error handling and cleanup
"""

from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.document_parser import (
    extract_pitch_deck_text,
    extract_text_from_pdf,
    extract_text_from_pptx,
    get_supported_extensions,
)
from src.file_upload import (
    UPLOAD_DIR,
    delete_upload,
    ensure_upload_dir,
    get_relative_url,
    get_upload_path,
    validate_upload,
)

# =============================================================================
# File Upload Utility Tests
# =============================================================================


class TestValidateUpload:
    """Tests for the validate_upload function."""

    def test_valid_pdf_upload(self):
        """Valid PDF file should pass validation."""
        mock_file = MagicMock()
        mock_file.filename = "pitch_deck.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.file.seek = MagicMock()
        mock_file.file.tell = MagicMock(return_value=1024 * 1024)  # 1MB

        is_valid, error = validate_upload(mock_file)

        assert is_valid is True
        assert error == ""

    def test_valid_pptx_upload(self):
        """Valid PPTX file should pass validation."""
        mock_file = MagicMock()
        mock_file.filename = "pitch_deck.pptx"
        mock_file.content_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        mock_file.file.seek = MagicMock()
        mock_file.file.tell = MagicMock(return_value=5 * 1024 * 1024)  # 5MB

        is_valid, error = validate_upload(mock_file)

        assert is_valid is True
        assert error == ""

    def test_valid_ppt_upload(self):
        """Valid legacy PPT file should pass validation."""
        mock_file = MagicMock()
        mock_file.filename = "old_deck.ppt"
        mock_file.content_type = "application/vnd.ms-powerpoint"
        mock_file.file.seek = MagicMock()
        mock_file.file.tell = MagicMock(return_value=2 * 1024 * 1024)  # 2MB

        is_valid, error = validate_upload(mock_file)

        assert is_valid is True
        assert error == ""

    def test_no_filename_rejected(self):
        """File without filename should be rejected."""
        mock_file = MagicMock()
        mock_file.filename = None

        is_valid, error = validate_upload(mock_file)

        assert is_valid is False
        assert "filename" in error.lower()

    def test_empty_filename_rejected(self):
        """File with empty filename should be rejected."""
        mock_file = MagicMock()
        mock_file.filename = ""

        is_valid, error = validate_upload(mock_file)

        assert is_valid is False
        assert "filename" in error.lower()

    def test_invalid_extension_rejected(self):
        """File with unsupported extension should be rejected."""
        mock_file = MagicMock()
        mock_file.filename = "document.doc"

        is_valid, error = validate_upload(mock_file)

        assert is_valid is False
        assert "file type" in error.lower() or "allowed" in error.lower()

    def test_txt_extension_rejected(self):
        """TXT files should be rejected."""
        mock_file = MagicMock()
        mock_file.filename = "notes.txt"

        is_valid, error = validate_upload(mock_file)

        assert is_valid is False

    def test_oversized_file_rejected(self):
        """File exceeding max size should be rejected."""
        mock_file = MagicMock()
        mock_file.filename = "huge_deck.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.file.seek = MagicMock()
        mock_file.file.tell = MagicMock(return_value=100 * 1024 * 1024)  # 100MB

        is_valid, error = validate_upload(mock_file)

        assert is_valid is False
        assert "too large" in error.lower() or "maximum" in error.lower()

    def test_empty_file_rejected(self):
        """Empty file (0 bytes) should be rejected."""
        mock_file = MagicMock()
        mock_file.filename = "empty.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.file.seek = MagicMock()
        mock_file.file.tell = MagicMock(return_value=0)

        is_valid, error = validate_upload(mock_file)

        assert is_valid is False
        assert "empty" in error.lower()

    def test_mime_type_mismatch_logged_but_allowed(self):
        """MIME type mismatch should be logged but not rejected.

        Some browsers send incorrect MIME types, so we log but don't reject.
        """
        mock_file = MagicMock()
        mock_file.filename = "deck.pdf"
        mock_file.content_type = "application/octet-stream"  # Wrong MIME
        mock_file.file.seek = MagicMock()
        mock_file.file.tell = MagicMock(return_value=1024)

        is_valid, error = validate_upload(mock_file)

        # Should still pass - we only log the mismatch
        assert is_valid is True


class TestEnsureUploadDir:
    """Tests for the ensure_upload_dir function."""

    def test_creates_directory_if_not_exists(self, tmp_path):
        """Should create upload directory if it doesn't exist."""
        with patch("src.file_upload.UPLOAD_DIR", tmp_path / "new_uploads"):
            from src.file_upload import UPLOAD_DIR as patched_dir

            ensure_upload_dir()
            assert patched_dir.exists()


class TestDeleteUpload:
    """Tests for the delete_upload function."""

    def test_deletes_existing_file(self, tmp_path):
        """Should delete an existing file."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("test content")

        result = delete_upload(test_file)

        assert result is True
        assert not test_file.exists()

    def test_returns_false_for_nonexistent_file(self, tmp_path):
        """Should return False for file that doesn't exist."""
        fake_path = tmp_path / "nonexistent.pdf"

        result = delete_upload(fake_path)

        assert result is False


class TestGetRelativeUrl:
    """Tests for the get_relative_url function."""

    def test_returns_correct_url_path(self):
        """Should return correct relative URL."""
        file_path = Path("/some/path/uploads/pitch_decks/fund123_20240101_120000.pdf")

        result = get_relative_url(file_path)

        assert result == "/uploads/pitch_decks/fund123_20240101_120000.pdf"


class TestGetUploadPath:
    """Tests for the get_upload_path function."""

    def test_returns_path_for_existing_file(self, tmp_path):
        """Should return path for existing file."""
        with patch("src.file_upload.UPLOAD_DIR", tmp_path):
            test_file = tmp_path / "test.pdf"
            test_file.write_text("content")

            result = get_upload_path("test.pdf")

            assert result == test_file

    def test_returns_none_for_nonexistent_file(self, tmp_path):
        """Should return None for nonexistent file."""
        with patch("src.file_upload.UPLOAD_DIR", tmp_path):
            result = get_upload_path("nonexistent.pdf")

            assert result is None


# =============================================================================
# Document Parser Tests
# =============================================================================


class TestGetSupportedExtensions:
    """Tests for supported extensions."""

    def test_includes_pdf(self):
        """Should include PDF extension."""
        extensions = get_supported_extensions()
        assert ".pdf" in extensions

    def test_includes_pptx(self):
        """Should include PPTX extension."""
        extensions = get_supported_extensions()
        assert ".pptx" in extensions

    def test_includes_ppt(self):
        """Should include legacy PPT extension."""
        extensions = get_supported_extensions()
        assert ".ppt" in extensions


class TestExtractPitchDeckText:
    """Tests for the extract_pitch_deck_text dispatcher."""

    def test_returns_empty_for_nonexistent_file(self, tmp_path):
        """Should return empty string for nonexistent file."""
        fake_path = tmp_path / "nonexistent.pdf"

        result = extract_pitch_deck_text(fake_path)

        assert result == ""

    def test_returns_empty_for_unsupported_extension(self, tmp_path):
        """Should return empty string for unsupported extension."""
        test_file = tmp_path / "document.docx"
        test_file.write_text("content")

        result = extract_pitch_deck_text(test_file)

        assert result == ""

    def test_dispatches_pdf_to_pdf_extractor(self, tmp_path):
        """Should dispatch PDF files to PDF extractor."""
        test_pdf = tmp_path / "test.pdf"
        test_pdf.write_bytes(b"%PDF-1.4 test")  # Minimal PDF header

        with patch("src.document_parser.extract_text_from_pdf") as mock_extract:
            mock_extract.return_value = "extracted text"

            result = extract_pitch_deck_text(test_pdf)

            mock_extract.assert_called_once_with(test_pdf)
            assert result == "extracted text"

    def test_dispatches_pptx_to_pptx_extractor(self, tmp_path):
        """Should dispatch PPTX files to PPTX extractor."""
        test_pptx = tmp_path / "test.pptx"
        test_pptx.write_bytes(b"PK test")  # ZIP header (PPTX is a ZIP)

        with patch("src.document_parser.extract_text_from_pptx") as mock_extract:
            mock_extract.return_value = "pptx text"

            result = extract_pitch_deck_text(test_pptx)

            mock_extract.assert_called_once_with(test_pptx)
            assert result == "pptx text"


class TestExtractTextFromPdf:
    """Tests for PDF text extraction."""

    def test_handles_extraction_gracefully(self, tmp_path):
        """Should handle extraction errors gracefully."""
        # Create a file with PDF extension but invalid content
        test_pdf = tmp_path / "test.pdf"
        test_pdf.write_bytes(b"%PDF-1.4 minimal invalid")

        # Should not raise exception, just return empty or partial content
        result = extract_text_from_pdf(test_pdf)
        assert isinstance(result, str)

    def test_returns_empty_on_invalid_pdf(self, tmp_path):
        """Should return empty string for invalid PDF."""
        test_pdf = tmp_path / "invalid.pdf"
        test_pdf.write_bytes(b"not a real pdf")

        result = extract_text_from_pdf(test_pdf)

        assert result == ""


class TestExtractTextFromPptx:
    """Tests for PPTX text extraction."""

    def test_returns_empty_on_invalid_pptx(self, tmp_path):
        """Should return empty string for invalid PPTX."""
        test_pptx = tmp_path / "invalid.pptx"
        test_pptx.write_bytes(b"not a real pptx")

        result = extract_text_from_pptx(test_pptx)

        assert result == ""


# =============================================================================
# API Endpoint Tests
# =============================================================================


class TestPitchDeckUploadEndpoint:
    """Tests for the POST /api/funds/{fund_id}/pitch-deck endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.main import app
        return TestClient(app)

    @pytest.fixture
    def mock_auth_user(self):
        """Mock authenticated user."""
        return {
            "id": "user-123",
            "email": "gp@demo.com",
            "role": "gp",
        }

    def test_requires_authentication(self, client):
        """Should require authentication."""
        files = {"file": ("deck.pdf", BytesIO(b"test"), "application/pdf")}

        response = client.post(
            "/api/funds/a1000001-0000-0000-0000-000000000001/pitch-deck",
            files=files,
        )

        assert response.status_code == 401

    def test_rejects_invalid_fund_id(self, client, mock_auth_user):
        """Should reject invalid fund ID."""
        files = {"file": ("deck.pdf", BytesIO(b"test content"), "application/pdf")}

        with patch("src.routers.funds.auth.get_current_user", return_value=mock_auth_user):
            response = client.post(
                "/api/funds/invalid-uuid/pitch-deck",
                files=files,
            )

        assert response.status_code == 400
        assert "Invalid" in response.text

    def test_rejects_invalid_extension(self, client, mock_auth_user):
        """Should reject files with invalid extension."""
        files = {"file": ("document.exe", BytesIO(b"test content"), "application/octet-stream")}

        with patch("src.routers.funds.auth.get_current_user", return_value=mock_auth_user):
            response = client.post(
                "/api/funds/a1000001-0000-0000-0000-000000000001/pitch-deck",
                files=files,
            )

        assert response.status_code == 400
        assert "file type" in response.text.lower() or "allowed" in response.text.lower()

    def test_rejects_empty_file(self, client, mock_auth_user):
        """Should reject empty files."""
        files = {"file": ("deck.pdf", BytesIO(b""), "application/pdf")}

        with patch("src.routers.funds.auth.get_current_user", return_value=mock_auth_user):
            response = client.post(
                "/api/funds/a1000001-0000-0000-0000-000000000001/pitch-deck",
                files=files,
            )

        assert response.status_code == 400
        assert "empty" in response.text.lower()

    def test_fund_not_found(self, client, mock_auth_user):
        """Should return 404 when fund doesn't exist."""
        files = {"file": ("deck.pdf", BytesIO(b"test content"), "application/pdf")}

        with patch("src.routers.funds.auth.get_current_user", return_value=mock_auth_user):
            with patch("src.routers.funds.get_db") as mock_db:
                mock_conn = MagicMock()
                mock_cursor = MagicMock()
                mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
                mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
                mock_cursor.fetchone.return_value = None  # Fund not found
                mock_db.return_value = mock_conn

                response = client.post(
                    "/api/funds/a1000001-0000-0000-0000-000000000001/pitch-deck",
                    files=files,
                )

        assert response.status_code == 404
        assert "not found" in response.text.lower()


# =============================================================================
# Integration Tests
# =============================================================================


class TestPitchDeckUploadIntegration:
    """Integration tests for pitch deck upload workflow."""

    def test_upload_directory_exists(self):
        """Upload directory should exist."""
        ensure_upload_dir()
        assert UPLOAD_DIR.exists()

    def test_full_upload_workflow_with_mock_file(self, tmp_path):
        """Test full upload workflow with mocked file."""
        # Create a test file
        test_file = tmp_path / "test_deck.pdf"
        test_file.write_bytes(b"%PDF-1.4 test content")

        # Verify file exists
        assert test_file.exists()

        # Extract text (will return empty for invalid PDF but shouldn't error)
        result = extract_pitch_deck_text(test_file)
        assert isinstance(result, str)
