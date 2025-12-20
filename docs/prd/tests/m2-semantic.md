# M2: Semantic Search Tests
### "Find LPs using natural language"

## M2-UNIT: Unit Tests

```python
# tests/unit/test_embeddings.py

class TestEmbeddingGeneration:
    """Test Voyage AI embedding generation."""

    async def test_embedding_has_correct_dimensions(self, mock_voyage):
        embedding = await generate_embedding("test text")
        assert len(embedding) == 1024

    async def test_similar_text_similar_embeddings(self, mock_voyage):
        e1 = await generate_embedding("growth equity technology")
        e2 = await generate_embedding("growth stage tech investing")
        similarity = cosine_similarity(e1, e2)
        assert similarity > 0.7

    async def test_different_text_different_embeddings(self, mock_voyage):
        e1 = await generate_embedding("real estate core")
        e2 = await generate_embedding("venture capital biotech")
        similarity = cosine_similarity(e1, e2)
        assert similarity < 0.5

    async def test_empty_text_raises_error(self, mock_voyage):
        with pytest.raises(ValueError):
            await generate_embedding("")
```

## M2-INT: Integration Tests

```python
# tests/integration/test_semantic_search.py

class TestSemanticSearch:
    """Test semantic LP search with Voyage AI embeddings."""

    async def test_semantic_search_returns_results(
        self, client, auth_session, lps_with_embeddings
    ):
        response = await client.post(
            "/api/v1/lps/semantic-search",
            cookies={"session": auth_session},
            json={"query": "climate tech investors in Europe"}
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) > 0

    async def test_results_have_similarity_scores(
        self, client, auth_session, lps_with_embeddings
    ):
        response = await client.post(
            "/api/v1/lps/semantic-search",
            cookies={"session": auth_session},
            json={"query": "growth equity"}
        )
        for item in response.json()["items"]:
            assert "similarity_score" in item
            assert 0 <= item["similarity_score"] <= 1

    async def test_results_sorted_by_relevance(
        self, client, auth_session, lps_with_embeddings
    ):
        response = await client.post(
            "/api/v1/lps/semantic-search",
            cookies={"session": auth_session},
            json={"query": "technology growth"}
        )
        scores = [r["similarity_score"] for r in response.json()["items"]]
        assert scores == sorted(scores, reverse=True)

    async def test_semantic_combined_with_filters(
        self, client, auth_session, lps_with_embeddings
    ):
        response = await client.post(
            "/api/v1/lps/semantic-search",
            cookies={"session": auth_session},
            json={
                "query": "technology",
                "filters": {"type": ["Endowment"]}
            }
        )
        for item in response.json()["items"]:
            assert item["type"] == "Endowment"

    async def test_semantic_search_performance(
        self, client, auth_session, many_lps_with_embeddings
    ):
        """Semantic search completes in < 2 seconds."""
        import time
        start = time.time()
        await client.post(
            "/api/v1/lps/semantic-search",
            cookies={"session": auth_session},
            json={"query": "healthcare focused investor"}
        )
        duration = time.time() - start
        assert duration < 2.0
```

## M2-E2E: End-to-End Tests

```python
# tests/e2e/test_m2_semantic_search.py

import pytest
from playwright.sync_api import Page, expect


class TestM2SemanticSearch:
    """E2E tests for M2: Semantic Search milestone."""

    def test_natural_language_search_returns_results(self, page: Page, logged_in_user):
        """User can search using natural language via HTMX."""
        page.goto("/lps")

        # Enter semantic search query
        page.fill('[data-testid="semantic-search"]', "family offices interested in fintech")
        page.press('[data-testid="semantic-search"]', "Enter")

        # Wait for HTMX to complete the search
        page.wait_for_selector('[data-testid="lp-card"]')
        expect(page.locator('[data-testid="loading"]')).not_to_be_visible()

        # Should have results with similarity scores
        expect(page.locator('[data-testid="lp-card"]')).to_have_count(
            greater_than_or_equal=1
        )
        expect(page.locator('[data-testid="similarity-score"]').first).to_be_visible()

    def test_combine_semantic_search_with_filters(self, page: Page, logged_in_user):
        """User can combine semantic search with type filters."""
        page.goto("/lps")

        # Apply filter first
        page.click('[data-testid="type-filter"]')
        page.click("text=Endowment")

        # Wait for filter to apply
        page.wait_for_load_state("networkidle")

        # Then perform semantic search
        page.fill('[data-testid="semantic-search"]', "technology")
        page.press('[data-testid="semantic-search"]', "Enter")

        # Wait for search results
        page.wait_for_load_state("networkidle")

        # All results should be Endowments
        type_elements = page.locator('[data-testid="lp-type"]').all()
        for elem in type_elements:
            expect(elem).to_have_text("Endowment")

    def test_search_shows_loading_indicator(self, page: Page, logged_in_user):
        """Loading indicator appears during HTMX search request."""
        page.goto("/lps")

        # Start search
        page.fill('[data-testid="semantic-search"]', "healthcare investors")

        # Check loading indicator appears (htmx-indicator class)
        page.press('[data-testid="semantic-search"]', "Enter")
        expect(page.locator('[data-testid="loading"]')).to_be_visible()

        # Wait for completion
        page.wait_for_load_state("networkidle")
        expect(page.locator('[data-testid="loading"]')).not_to_be_visible()
```
