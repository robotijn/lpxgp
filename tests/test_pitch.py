"""Tests for pitch generation API endpoints.

IMPORTANT: Tests are the source of truth. Do NOT modify tests to make them pass.
If a test fails, fix the APPLICATION, not the test.

Based on BDD Gherkin specs from docs/prd/tests/*.feature.md
"""

import pytest

# =============================================================================
# PITCH GENERATION TESTS
# =============================================================================


class TestPitchGeneration:
    """Test pitch generation API endpoint.

    Gherkin Reference: M3 - AI Pitch Generation
    """

    def test_generate_pitch_invalid_match_id_returns_400(self, client):
        """Generating pitch with invalid match ID should return 400."""
        response = client.post("/api/match/invalid-uuid/generate-pitch")
        assert response.status_code == 400

    def test_generate_pitch_valid_uuid_without_db(self, client):
        """Generating pitch with valid UUID but no DB should return 503."""
        response = client.post(
            "/api/match/00000000-0000-0000-0000-000000000000/generate-pitch"
        )
        assert response.status_code in [503, 404]

    def test_generate_pitch_accepts_pitch_type(self, client):
        """Pitch generation should accept pitch_type parameter."""
        response = client.post(
            "/api/match/00000000-0000-0000-0000-000000000000/generate-pitch",
            data={"pitch_type": "email", "tone": "professional"}
        )
        assert response.status_code in [503, 404]

    def test_generate_pitch_invalid_pitch_type(self, client):
        """Invalid pitch type should be handled gracefully."""
        response = client.post(
            "/api/match/00000000-0000-0000-0000-000000000000/generate-pitch",
            data={"pitch_type": "invalid_type", "tone": "professional"}
        )
        # Should handle gracefully, not crash
        assert response.status_code != 500

    def test_generate_pitch_xss_in_tone(self, client):
        """XSS in tone parameter should be safely handled."""
        response = client.post(
            "/api/match/00000000-0000-0000-0000-000000000000/generate-pitch",
            data={"pitch_type": "email", "tone": "<script>alert(1)</script>"}
        )
        assert response.status_code != 500

    def test_generate_pitch_sql_injection_in_uuid(self, client):
        """SQL injection in match UUID should be rejected."""
        response = client.post(
            "/api/match/'; DROP TABLE fund_lp_matches; --/generate-pitch"
        )
        assert response.status_code == 400


class TestPitchGenerationUUIDValidation:
    """Test UUID validation for pitch generation endpoint."""

    @pytest.mark.parametrize("invalid_id", [
        "",
        "not-a-uuid",
        "../../../etc/passwd",
        "00000000-0000-0000-0000",  # incomplete
        "'; DROP TABLE fund_lp_matches; --",
    ])
    def test_pitch_rejects_invalid_uuids(self, client, invalid_id):
        """Pitch endpoint should reject invalid match UUIDs."""
        response = client.post(f"/api/match/{invalid_id}/generate-pitch")
        assert response.status_code in [400, 404, 422]
        assert response.status_code != 500
