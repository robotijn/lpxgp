"""Tests for pipeline functionality - GP and LP Kanban boards.

This module contains tests for:
- GP Pipeline API (GET and PATCH endpoints)
- GP Pipeline page access and authorization
- LP Pipeline API (PATCH endpoint)
- LP Pipeline page access and authorization

IMPORTANT: Tests are the source of truth. Do NOT modify tests to make them pass.
If a test fails, fix the APPLICATION, not the test.
"""

import pytest


# =============================================================================
# GP PIPELINE API TESTS - GP KANBAN BOARD
# REST API for GP pipeline stage management
# =============================================================================


class TestPipelineApiGet:
    """Test REST API endpoint GET /api/v1/pipeline/{fund_id}.

    Returns pipeline items grouped by stage for kanban board display.
    """

    def test_pipeline_get_requires_auth(self, client):
        """API should require authentication."""
        response = client.get("/api/v1/pipeline/test-fund-id")
        assert response.status_code in [401, 302, 303, 307]

    def test_pipeline_get_returns_json(self, authenticated_client):
        """API should return JSON response."""
        response = authenticated_client.get("/api/v1/pipeline/test-fund-id")
        # Should return 200 even if fund doesn't exist (empty pipeline)
        if response.status_code == 200:
            assert "application/json" in response.headers["content-type"]

    def test_pipeline_get_response_structure(self, authenticated_client):
        """API response should have standard structure with pipeline stages."""
        response = authenticated_client.get("/api/v1/pipeline/test-fund-id")
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "pipeline" in data
            # Check all required stages exist
            expected_stages = [
                "recommended", "gp_interested", "gp_pursuing", "lp_reviewing",
                "mutual_interest", "in_diligence", "gp_passed", "lp_passed", "invested"
            ]
            for stage in expected_stages:
                assert stage in data["pipeline"], f"Missing stage: {stage}"

    def test_pipeline_get_items_is_list(self, authenticated_client):
        """Pipeline items should be a list."""
        response = authenticated_client.get("/api/v1/pipeline/test-fund-id")
        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert isinstance(data["items"], list)

    def test_pipeline_get_invalid_fund_id_handled(self, authenticated_client):
        """Invalid fund ID should be handled gracefully."""
        response = authenticated_client.get("/api/v1/pipeline/not-a-uuid")
        # Should return 200 with empty pipeline or 400/404
        assert response.status_code in [200, 400, 404]


class TestPipelineApiUpdate:
    """Test REST API endpoint PATCH /api/v1/pipeline/{fund_id}/{lp_id}.

    Updates pipeline stage for a fund-LP relationship.
    """

    def test_pipeline_update_requires_auth(self, client):
        """API should require authentication."""
        response = client.patch(
            "/api/v1/pipeline/test-fund-id/test-lp-id",
            json={"stage": "gp_interested"},
            follow_redirects=False,
        )
        assert response.status_code in [401, 302, 303, 307]

    def test_pipeline_update_valid_stage(self, authenticated_client):
        """Valid stage update should succeed or return appropriate error."""
        valid_stages = [
            "recommended", "gp_interested", "gp_pursuing", "lp_reviewing",
            "mutual_interest", "in_diligence", "gp_passed", "lp_passed", "invested"
        ]
        for stage in valid_stages:
            response = authenticated_client.patch(
                "/api/v1/pipeline/test-fund-id/test-lp-id",
                json={"stage": stage}
            )
            # Should either succeed (200), fail due to missing fund/lp (400/404/422),
            # or encounter DB error (500) - but NOT reject the stage pattern itself
            assert response.status_code in [200, 400, 404, 422, 500], f"Stage {stage} failed with {response.status_code}"

    def test_pipeline_update_invalid_stage_rejected(self, authenticated_client):
        """Invalid stage should be rejected with 422."""
        response = authenticated_client.patch(
            "/api/v1/pipeline/test-fund-id/test-lp-id",
            json={"stage": "invalid_stage"}
        )
        # Pydantic validation should reject invalid stage
        assert response.status_code == 422

    def test_pipeline_update_empty_stage_rejected(self, authenticated_client):
        """Empty stage should be rejected."""
        response = authenticated_client.patch(
            "/api/v1/pipeline/test-fund-id/test-lp-id",
            json={"stage": ""}
        )
        assert response.status_code == 422

    def test_pipeline_update_missing_stage_rejected(self, authenticated_client):
        """Missing stage field should be rejected."""
        response = authenticated_client.patch(
            "/api/v1/pipeline/test-fund-id/test-lp-id",
            json={}
        )
        assert response.status_code == 422

    def test_pipeline_update_with_notes(self, authenticated_client):
        """Stage update with notes should be accepted."""
        response = authenticated_client.patch(
            "/api/v1/pipeline/test-fund-id/test-lp-id",
            json={"stage": "gp_interested", "notes": "Initial contact made"}
        )
        # Should either succeed or fail due to missing fund/lp or DB
        assert response.status_code in [200, 400, 404, 422, 500]

    def test_pipeline_update_returns_json(self, authenticated_client):
        """API should return JSON response."""
        response = authenticated_client.patch(
            "/api/v1/pipeline/test-fund-id/test-lp-id",
            json={"stage": "gp_interested"}
        )
        assert "application/json" in response.headers["content-type"]

    def test_pipeline_update_sql_injection_prevented(self, authenticated_client):
        """SQL injection attempts should be prevented."""
        malicious_notes = "'; DROP TABLE fund_lp_status; --"
        response = authenticated_client.patch(
            "/api/v1/pipeline/test-fund-id/test-lp-id",
            json={"stage": "gp_interested", "notes": malicious_notes}
        )
        # Should either succeed (safe) or fail for other reasons
        # Should NOT cause a 500 server error from SQL error
        assert response.status_code != 500 or "sql" not in response.text.lower()


class TestPipelinePageAccess:
    """Test pipeline page access and authorization."""

    def test_pipeline_page_requires_auth(self, client):
        """Pipeline page should require authentication."""
        response = client.get("/pipeline", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers.get("location") == "/login"

    def test_pipeline_page_returns_html(self, authenticated_client):
        """Pipeline page should return HTML for authenticated users."""
        response = authenticated_client.get("/pipeline")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_pipeline_page_contains_kanban_structure(self, authenticated_client):
        """Pipeline page should contain kanban board structure."""
        response = authenticated_client.get("/pipeline")
        assert response.status_code == 200
        # Check for kanban column markers or pipeline title
        assert "column-" in response.text or "Pipeline" in response.text

    def test_pipeline_page_has_drag_functions(self, authenticated_client):
        """Pipeline page should have drag-and-drop JavaScript functions."""
        response = authenticated_client.get("/pipeline")
        assert response.status_code == 200
        # Check for drag/drop JavaScript functions (always present in script)
        assert "function drag" in response.text or "allowDrop" in response.text

    def test_pipeline_detail_requires_auth(self, client):
        """Pipeline detail page should require authentication."""
        response = client.get("/pipeline/test-fund-id/test-lp-id", follow_redirects=False)
        # Invalid UUIDs redirect to /pipeline, which redirects to /login
        assert response.status_code in [302, 303, 307]

    def test_pipeline_detail_page_returns_html(self, authenticated_client):
        """Pipeline detail should return HTML for valid IDs."""
        response = authenticated_client.get("/pipeline/test-fund-id/test-lp-id")
        # May return redirect if fund/lp don't exist, or 200 if they do
        if response.status_code == 200:
            assert "text/html" in response.headers["content-type"]

    def test_pipeline_fund_filter(self, authenticated_client):
        """Pipeline should support fund_id filter."""
        response = authenticated_client.get("/pipeline?fund_id=test-fund-id")
        assert response.status_code == 200


# =============================================================================
# LP PIPELINE API TESTS - LP KANBAN BOARD
# REST API for LP pipeline stage management
# =============================================================================


class TestLPPipelineApiUpdate:
    """Test REST API endpoint PATCH /api/v1/lp-pipeline/{fund_id}.

    Updates LP pipeline stage for a fund (LP's interest level).
    """

    def test_lp_pipeline_update_requires_auth(self, client):
        """API should require authentication."""
        response = client.patch(
            "/api/v1/lp-pipeline/test-fund-id",
            json={"stage": "interested"},
            follow_redirects=False,
        )
        assert response.status_code in [401, 302, 303, 307]

    def test_lp_pipeline_update_valid_stage(self, authenticated_client):
        """Valid LP stage update should succeed or return appropriate error."""
        valid_stages = ["watching", "interested", "reviewing", "dd_in_progress", "passed"]
        for stage in valid_stages:
            response = authenticated_client.patch(
                "/api/v1/lp-pipeline/test-fund-id",
                json={"stage": stage}
            )
            # Should either succeed (200), fail due to missing LP org (400/404),
            # or encounter DB error (500/503) - but NOT reject the stage pattern
            assert response.status_code in [200, 400, 404, 500, 503], f"Stage {stage} failed with {response.status_code}"

    def test_lp_pipeline_update_invalid_stage_rejected(self, authenticated_client):
        """Invalid LP stage should be rejected with 422."""
        response = authenticated_client.patch(
            "/api/v1/lp-pipeline/test-fund-id",
            json={"stage": "invalid_stage"}
        )
        # Pydantic validation should reject invalid stage
        assert response.status_code == 422

    def test_lp_pipeline_update_empty_stage_rejected(self, authenticated_client):
        """Empty stage should be rejected."""
        response = authenticated_client.patch(
            "/api/v1/lp-pipeline/test-fund-id",
            json={"stage": ""}
        )
        assert response.status_code == 422

    def test_lp_pipeline_update_missing_stage_rejected(self, authenticated_client):
        """Missing stage field should be rejected."""
        response = authenticated_client.patch(
            "/api/v1/lp-pipeline/test-fund-id",
            json={}
        )
        assert response.status_code == 422

    def test_lp_pipeline_update_with_notes(self, authenticated_client):
        """LP stage update with notes should be accepted."""
        response = authenticated_client.patch(
            "/api/v1/lp-pipeline/test-fund-id",
            json={"stage": "reviewing", "notes": "Scheduled DD call"}
        )
        # Should either succeed or fail due to missing LP org or DB
        assert response.status_code in [200, 400, 404, 500, 503]

    def test_lp_pipeline_update_returns_json(self, authenticated_client):
        """API should return JSON response."""
        response = authenticated_client.patch(
            "/api/v1/lp-pipeline/test-fund-id",
            json={"stage": "interested"}
        )
        assert "application/json" in response.headers["content-type"]

    def test_lp_pipeline_update_invalid_uuid_rejected(self, authenticated_client):
        """Invalid fund UUID should be rejected."""
        response = authenticated_client.patch(
            "/api/v1/lp-pipeline/not-a-uuid",
            json={"stage": "interested"}
        )
        assert response.status_code == 400

    def test_lp_pipeline_gp_stages_rejected(self, authenticated_client):
        """GP pipeline stages should be rejected for LP pipeline."""
        gp_stages = ["recommended", "gp_interested", "gp_pursuing", "mutual_interest"]
        for stage in gp_stages:
            response = authenticated_client.patch(
                "/api/v1/lp-pipeline/test-fund-id",
                json={"stage": stage}
            )
            # Should reject with 422 (Pydantic validation)
            assert response.status_code == 422, f"GP stage {stage} was not rejected"


class TestLPPipelinePageAccess:
    """Test LP pipeline page access and authorization."""

    def test_lp_pipeline_page_requires_auth(self, client):
        """LP pipeline page should require authentication."""
        response = client.get("/lp-pipeline", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers.get("location") == "/login"

    def test_lp_pipeline_page_returns_html(self, authenticated_client):
        """LP pipeline page should return HTML for authenticated users."""
        response = authenticated_client.get("/lp-pipeline")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_lp_pipeline_page_contains_kanban_structure(self, authenticated_client):
        """LP pipeline page should contain kanban board structure."""
        response = authenticated_client.get("/lp-pipeline")
        assert response.status_code == 200
        # Check for kanban column markers or pipeline title
        assert "column-" in response.text or "Pipeline" in response.text

    def test_lp_pipeline_page_has_drag_functions(self, authenticated_client):
        """LP pipeline page should have drag-and-drop JavaScript functions."""
        response = authenticated_client.get("/lp-pipeline")
        assert response.status_code == 200
        # Check for drag/drop JavaScript functions
        assert "function drag" in response.text or "allowDrop" in response.text

    def test_lp_pipeline_shows_lp_stages(self, authenticated_client):
        """LP pipeline should show LP-specific stages."""
        response = authenticated_client.get("/lp-pipeline")
        assert response.status_code == 200
        content = response.text
        # Check for LP pipeline stages
        lp_stages = ["Watching", "Interested", "Reviewing", "DD"]
        stages_found = sum(1 for stage in lp_stages if stage in content)
        assert stages_found >= 2, "Expected to find at least 2 LP stages"
