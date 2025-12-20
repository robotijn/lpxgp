# M5: Production Tests
### "Live system with automation"

## M5-INT: Integration Tests

```python
# tests/integration/test_admin.py

class TestAdminDashboard:
    """Test admin functionality."""

    async def test_super_admin_sees_all_companies(self, client, super_admin_session):
        response = await client.get(
            "/api/v1/admin/companies",
            cookies={"session": super_admin_session}
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) > 0

    async def test_regular_user_cannot_access_admin(self, client, auth_session):
        response = await client.get(
            "/api/v1/admin/companies",
            cookies={"session": auth_session}
        )
        assert response.status_code == 403

    async def test_data_quality_stats(self, client, super_admin_session):
        response = await client.get(
            "/api/v1/admin/stats/data-quality",
            cookies={"session": super_admin_session}
        )
        assert response.status_code == 200
        assert "average_score" in response.json()
        assert "lps_needing_review" in response.json()
```

## M5-PERF: Performance Tests

```python
# tests/performance/test_performance.py

class TestPerformance:
    """Performance benchmarks."""

    @pytest.mark.benchmark
    async def test_search_10k_lps(self, client, auth_session, setup_10k_lps):
        times = []
        for _ in range(10):
            start = time.time()
            await client.get(
                "/api/v1/lps?type=Public%20Pension",
                cookies={"session": auth_session}
            )
            times.append((time.time() - start) * 1000)

        avg = sum(times) / len(times)
        p95 = sorted(times)[9]

        assert avg < 300, f"Average {avg}ms > 300ms"
        assert p95 < 500, f"P95 {p95}ms > 500ms"

    @pytest.mark.benchmark
    async def test_match_generation_1k_lps(self, client, auth_session, fund, setup_1k_lps):
        start = time.time()
        await client.post(
            f"/api/v1/funds/{fund['id']}/matches/generate",
            cookies={"session": auth_session}
        )
        duration = time.time() - start
        assert duration < 30.0

    @pytest.mark.benchmark
    async def test_concurrent_users(self, client, supabase, setup_test_users):
        async def user_session(user_creds):
            auth = supabase.auth.sign_in_with_password(user_creds)
            session = auth.session.access_token
            r = await client.get(
                "/api/v1/lps",
                cookies={"session": session}
            )
            return r.status_code == 200

        results = await asyncio.gather(*[
            user_session(u) for u in setup_test_users[:100]
        ])
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.99
```

## M5-SEC: Security Tests

```python
# tests/security/test_security.py

class TestSecurity:
    """Security tests."""

    async def test_sql_injection_blocked(self, client, auth_session):
        payloads = [
            "'; DROP TABLE lps; --",
            "1 OR 1=1",
            "' UNION SELECT * FROM users --"
        ]
        for payload in payloads:
            response = await client.get(
                f"/api/v1/lps?name={payload}",
                cookies={"session": auth_session}
            )
            assert response.status_code in [200, 422]  # Not 500

    async def test_rate_limiting(self, client, auth_session):
        responses = []
        for _ in range(150):  # Exceed 100/min
            r = await client.get(
                "/api/v1/lps",
                cookies={"session": auth_session}
            )
            responses.append(r.status_code)

        assert 429 in responses  # Some should be rate limited

    async def test_expired_session_rejected(self, client, expired_session):
        """Expired Supabase session is rejected."""
        response = await client.get(
            "/api/v1/lps",
            cookies={"session": expired_session}
        )
        assert response.status_code in [401, 302]  # Unauthorized or redirect to login
```
