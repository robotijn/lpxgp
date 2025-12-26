"""Tests for shortlist functionality.

IMPORTANT: Tests are the source of truth. Do NOT modify tests to make them pass.
If a test fails, fix the APPLICATION, not the test.

Based on BDD Gherkin specs from docs/prd/tests/*.feature.md

Test Categories:
- Shortlist page authentication and content
- Shortlist API operations (add, get, remove, update, check, clear, toggle)
- User isolation and edge cases
"""



class TestShortlistPageAuth:
    """Test shortlist page requires authentication.

    Gherkin Reference: F-UI-01 - Protected Pages
    """

    def test_shortlist_requires_auth(self, client):
        """Shortlist page should redirect unauthenticated users to login."""
        response = client.get("/shortlist", follow_redirects=False)
        assert response.status_code == 303 or response.status_code == 302
        assert "/login" in response.headers.get("location", "")

    def test_shortlist_accessible_when_logged_in(self, client):
        """Shortlist page should be accessible when authenticated."""
        # Login first
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/shortlist")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestShortlistPageContent:
    """Test shortlist page content and structure."""

    def test_shortlist_page_has_title(self, client):
        """Shortlist page should have appropriate title."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/shortlist")
        assert "Shortlist" in response.text

    def test_shortlist_page_has_navigation(self, client):
        """Shortlist page should have navigation links."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/shortlist")
        assert 'href="/dashboard"' in response.text
        assert 'href="/lps"' in response.text

    def test_shortlist_page_shows_empty_state(self, client):
        """Shortlist page should show empty state when no items."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/shortlist")
        # Empty state message or stats should show 0
        assert "0" in response.text or "empty" in response.text.lower() or "no saved" in response.text.lower()


class TestShortlistApiAdd:
    """Test adding items to shortlist via API.

    Gherkin Reference: F-SHORTLIST-01 - Add LP to Shortlist
    """

    def test_add_to_shortlist_requires_auth(self, client):
        """Adding to shortlist should require authentication."""
        response = client.post(
            "/api/shortlist",
            json={"lp_id": "test-lp-001"},
        )
        assert response.status_code == 401

    def test_add_to_shortlist_success(self, client):
        """Should successfully add LP to shortlist."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.post(
            "/api/shortlist",
            json={"lp_id": "00000001-0000-0000-0000-000000000001"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["item"]["lp_id"] == "00000001-0000-0000-0000-000000000001"

    def test_add_to_shortlist_with_notes(self, client):
        """Should add LP with notes."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.post(
            "/api/shortlist",
            json={
                "lp_id": "00000002-0000-0000-0000-000000000002",
                "notes": "Great potential partner",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True

    def test_add_to_shortlist_with_priority(self, client):
        """Should add LP with priority level."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.post(
            "/api/shortlist",
            json={
                "lp_id": "00000003-0000-0000-0000-000000000003",
                "priority": 1,  # High priority
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True

    def test_add_to_shortlist_with_fund_id(self, client):
        """Should add LP with fund context."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.post(
            "/api/shortlist",
            json={
                "lp_id": "00000004-0000-0000-0000-000000000004",
                "fund_id": "00000001-0000-0000-0000-000000000001",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True

    def test_add_duplicate_to_shortlist_fails(self, client):
        """Adding same LP twice should fail."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # Add once
        client.post(
            "/api/shortlist",
            json={"lp_id": "00000005-0000-0000-0000-000000000005"},
        )
        # Try to add again
        response = client.post(
            "/api/shortlist",
            json={"lp_id": "00000005-0000-0000-0000-000000000005"},
        )
        assert response.status_code == 409  # Conflict

    def test_add_empty_lp_id_fails(self, client):
        """Adding with empty lp_id should fail validation."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.post(
            "/api/shortlist",
            json={"lp_id": ""},
        )
        assert response.status_code == 400  # Invalid LP ID

    def test_add_invalid_lp_id_format_fails(self, client):
        """Adding with non-UUID lp_id should fail validation."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.post(
            "/api/shortlist",
            json={"lp_id": "not-a-valid-uuid"},
        )
        assert response.status_code == 400  # Invalid LP ID

    def test_add_invalid_priority_fails(self, client):
        """Adding with invalid priority should fail validation."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # Priority 0 is invalid (must be 1-3)
        response = client.post(
            "/api/shortlist",
            json={"lp_id": "00000006-0000-0000-0000-000000000006", "priority": 0},
        )
        assert response.status_code == 422

        # Priority 4 is invalid (must be 1-3)
        response = client.post(
            "/api/shortlist",
            json={"lp_id": "00000007-0000-0000-0000-000000000007", "priority": 4},
        )
        assert response.status_code == 422


class TestShortlistApiGet:
    """Test getting shortlist via API.

    Gherkin Reference: F-SHORTLIST-02 - View Shortlist
    """

    def test_get_shortlist_requires_auth(self, client):
        """Getting shortlist should require authentication."""
        response = client.get("/api/shortlist")
        assert response.status_code == 401

    def test_get_shortlist_empty(self, client):
        """Should return empty list when no items."""
        client.post(
            "/api/auth/login",
            data={"email": "lp@demo.com", "password": "demo123"},  # Different user
        )
        response = client.get("/api/shortlist")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["count"] == 0

    def test_get_shortlist_with_items(self, client):
        """Should return items after adding."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # Add an item
        lp_id = "10000001-0000-0000-0000-000000000001"
        client.post(
            "/api/shortlist",
            json={"lp_id": lp_id},
        )
        # Get shortlist
        response = client.get("/api/shortlist")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        lp_ids = [item["lp_id"] for item in data["items"]]
        assert lp_id in lp_ids


class TestShortlistApiRemove:
    """Test removing items from shortlist via API.

    Gherkin Reference: F-SHORTLIST-03 - Remove from Shortlist
    """

    def test_remove_from_shortlist_requires_auth(self, client):
        """Removing from shortlist should require authentication."""
        response = client.delete("/api/shortlist/20000001-0000-0000-0000-000000000001")
        assert response.status_code == 401

    def test_remove_from_shortlist_success(self, client):
        """Should successfully remove LP from shortlist."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # Add first
        lp_id = "20000001-0000-0000-0000-000000000001"
        client.post(
            "/api/shortlist",
            json={"lp_id": lp_id},
        )
        # Remove
        response = client.delete(f"/api/shortlist/{lp_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_remove_nonexistent_fails(self, client):
        """Removing non-existent LP should fail."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.delete("/api/shortlist/99999999-9999-9999-9999-999999999999")
        assert response.status_code == 404

    def test_remove_invalid_uuid_fails(self, client):
        """Removing with invalid UUID should fail."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.delete("/api/shortlist/not-a-valid-uuid")
        assert response.status_code == 400


class TestShortlistApiUpdate:
    """Test updating shortlist items via API.

    Gherkin Reference: F-SHORTLIST-04 - Update Shortlist Item
    """

    def test_update_shortlist_requires_auth(self, client):
        """Updating shortlist should require authentication."""
        response = client.patch(
            "/api/shortlist/30000001-0000-0000-0000-000000000001",
            json={"notes": "Updated notes"},
        )
        assert response.status_code == 401

    def test_update_notes_success(self, client):
        """Should successfully update notes."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # Add first
        lp_id = "30000001-0000-0000-0000-000000000001"
        client.post(
            "/api/shortlist",
            json={"lp_id": lp_id},
        )
        # Update notes
        response = client.patch(
            f"/api/shortlist/{lp_id}",
            json={"notes": "Updated notes for testing"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_update_priority_success(self, client):
        """Should successfully update priority."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # Add first
        lp_id = "30000002-0000-0000-0000-000000000002"
        client.post(
            "/api/shortlist",
            json={"lp_id": lp_id, "priority": 2},
        )
        # Update priority
        response = client.patch(
            f"/api/shortlist/{lp_id}",
            json={"priority": 1},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_update_nonexistent_fails(self, client):
        """Updating non-existent LP should fail."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.patch(
            "/api/shortlist/99999999-9999-9999-9999-999999999998",
            json={"notes": "Test"},
        )
        assert response.status_code == 404

    def test_update_invalid_uuid_fails(self, client):
        """Updating with invalid UUID should fail."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.patch(
            "/api/shortlist/not-a-valid-uuid",
            json={"notes": "Test"},
        )
        assert response.status_code == 400

    def test_update_invalid_priority_fails(self, client):
        """Updating with invalid priority should fail."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # Add first
        lp_id = "30000003-0000-0000-0000-000000000003"
        client.post(
            "/api/shortlist",
            json={"lp_id": lp_id},
        )
        # Try invalid update
        response = client.patch(
            f"/api/shortlist/{lp_id}",
            json={"priority": 5},  # Invalid - must be 1-3
        )
        assert response.status_code == 422


class TestShortlistApiCheck:
    """Test checking if LP is in shortlist via API.

    Gherkin Reference: F-SHORTLIST-05 - Check Shortlist Status
    """

    def test_check_shortlist_requires_auth(self, client):
        """Checking shortlist should require authentication."""
        response = client.get("/api/shortlist/check/40000001-0000-0000-0000-000000000001")
        assert response.status_code == 401

    def test_check_lp_not_in_shortlist(self, client):
        """Should return false for LP not in shortlist."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/api/shortlist/check/99999999-9999-9999-9999-999999999997")
        assert response.status_code == 200
        data = response.json()
        assert data["in_shortlist"] is False

    def test_check_lp_in_shortlist(self, client):
        """Should return true for LP in shortlist."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # Add to shortlist
        lp_id = "40000001-0000-0000-0000-000000000001"
        client.post(
            "/api/shortlist",
            json={"lp_id": lp_id},
        )
        # Check
        response = client.get(f"/api/shortlist/check/{lp_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["in_shortlist"] is True


class TestShortlistApiClear:
    """Test clearing all shortlist items via API.

    Gherkin Reference: F-SHORTLIST-06 - Clear Shortlist
    """

    def test_clear_shortlist_requires_auth(self, client):
        """Clearing shortlist should require authentication."""
        response = client.delete("/api/shortlist")
        assert response.status_code == 401

    def test_clear_shortlist_success(self, client):
        """Should successfully clear all items."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # Add some items
        lp_id_1 = "50000001-0000-0000-0000-000000000001"
        lp_id_2 = "50000002-0000-0000-0000-000000000002"
        client.post("/api/shortlist", json={"lp_id": lp_id_1})
        client.post("/api/shortlist", json={"lp_id": lp_id_2})
        # Clear
        response = client.delete("/api/shortlist")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Verify empty
        get_response = client.get("/api/shortlist")
        get_data = get_response.json()
        # Should not contain the cleared items
        lp_ids = [item["lp_id"] for item in get_data["items"]]
        assert lp_id_1 not in lp_ids
        assert lp_id_2 not in lp_ids


class TestShortlistApiToggle:
    """Test toggling shortlist status via API.

    Gherkin Reference: F-SHORTLIST-07 - Toggle Shortlist (HTMX)
    """

    def test_toggle_shortlist_requires_auth(self, client):
        """Toggling shortlist should require authentication."""
        response = client.post("/api/shortlist/60000001-0000-0000-0000-000000000001/toggle")
        assert response.status_code == 401

    def test_toggle_adds_when_not_in_shortlist(self, client):
        """Toggle should add LP when not in shortlist."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.post("/api/shortlist/60000001-0000-0000-0000-000000000001/toggle")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # Response should contain "saved" or similar indicator
        assert "Saved" in response.text or "Remove" in response.text

    def test_toggle_removes_when_in_shortlist(self, client):
        """Toggle should remove LP when already in shortlist."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # Add first
        lp_id = "60000002-0000-0000-0000-000000000002"
        client.post("/api/shortlist", json={"lp_id": lp_id})
        # Toggle (should remove)
        response = client.post(f"/api/shortlist/{lp_id}/toggle")
        assert response.status_code == 200
        # Response should contain "save" indicator
        assert "Save" in response.text

    def test_toggle_returns_html_for_htmx(self, client):
        """Toggle should return HTML for HTMX swap."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.post("/api/shortlist/60000003-0000-0000-0000-000000000003/toggle")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # Should be a button element
        assert "<button" in response.text or "<svg" in response.text


class TestShortlistUserIsolation:
    """Test that shortlists are isolated per user.

    Gherkin Reference: Security - User Data Isolation
    """

    def test_users_have_separate_shortlists(self, client):
        """Each user should have their own separate shortlist."""
        lp_id = "70000001-0000-0000-0000-000000000001"

        # User 1 adds an item
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        client.post("/api/shortlist", json={"lp_id": lp_id})

        # Verify user 1 has it
        response1 = client.get("/api/shortlist")
        data1 = response1.json()
        user1_lps = [item["lp_id"] for item in data1["items"]]
        assert lp_id in user1_lps

        # Logout
        client.get("/logout")

        # User 2 should not see user 1's items
        client.post(
            "/api/auth/login",
            data={"email": "lp@demo.com", "password": "demo123"},
        )
        response2 = client.get("/api/shortlist")
        data2 = response2.json()
        user2_lps = [item["lp_id"] for item in data2["items"]]
        assert lp_id not in user2_lps


class TestShortlistEdgeCases:
    """Test shortlist edge cases and special inputs.

    Gherkin Reference: Edge Cases & Error Handling
    """

    def test_shortlist_handles_unicode_notes(self, client):
        """Shortlist should handle unicode in notes."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.post(
            "/api/shortlist",
            json={
                "lp_id": "80000001-0000-0000-0000-000000000001",
                "notes": "北京投资基金 - Great partner 👍",
            },
        )
        assert response.status_code == 201

    def test_shortlist_handles_emoji_notes(self, client):
        """Shortlist should handle emojis in notes."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.post(
            "/api/shortlist",
            json={
                "lp_id": "80000002-0000-0000-0000-000000000002",
                "notes": "Top tier LP 🌟📈💰",
            },
        )
        assert response.status_code == 201

    def test_shortlist_handles_long_notes(self, client):
        """Shortlist should handle long notes."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        long_notes = "A" * 1000  # 1000 character notes
        response = client.post(
            "/api/shortlist",
            json={
                "lp_id": "80000003-0000-0000-0000-000000000003",
                "notes": long_notes,
            },
        )
        assert response.status_code == 201

    def test_shortlist_handles_valid_uuid_format(self, client):
        """Shortlist should handle valid UUID format LP IDs."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # UUID-like IDs should work
        response = client.post(
            "/api/shortlist",
            json={"lp_id": "550e8400-e29b-41d4-a716-446655440000"},
        )
        assert response.status_code == 201
