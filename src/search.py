"""AI-powered search query parsing using local Ollama.

This module provides natural language query parsing for LP search,
converting queries like "50m or more aum" into structured SQL filters.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from src.config import get_settings

logger = logging.getLogger(__name__)


async def parse_lp_search_query(query: str) -> dict[str, Any]:
    """Use Ollama to parse natural language into structured filters.

    Args:
        query: Natural language search query (e.g., "50m or more aum")

    Returns:
        Dictionary with extracted filters:
        - aum_min: float (in billions)
        - aum_max: float (in billions)
        - lp_type: str
        - location: str
        - strategies: list[str]
        - check_size_min: float (in millions)
        - check_size_max: float (in millions)
        - text_search: str (fallback text to search)

    Example:
        >>> filters = await parse_lp_search_query("50m or more aum")
        >>> print(filters)
        {'aum_min': 0.05}
    """
    settings = get_settings()

    prompt = f"""You are a search query parser for an LP (Limited Partner) database.
Extract structured filters from this search query. Return ONLY valid JSON.

Available filters:
- aum_min: minimum AUM in BILLIONS (convert: 50M = 0.05, 1B = 1.0, 500M = 0.5)
- aum_max: maximum AUM in BILLIONS
- lp_type: one of: pension, endowment, foundation, family_office, sovereign_wealth, insurance
- location: city, state, or country name
- strategies: list of: buyout, growth, venture, real_estate, infrastructure
- check_size_min: minimum check size in MILLIONS
- check_size_max: maximum check size in MILLIONS
- text_search: any text to search by name (use if query is just a name)

Query: "{query}"

Return ONLY a JSON object with the relevant filters. Example:
{{"aum_min": 0.05}}

JSON:"""

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistent parsing
                    },
                },
            )
            response.raise_for_status()

            result = response.json()
            text = result.get("response", "").strip()

            # Try to extract JSON from the response
            filters = _extract_json(text)
            if filters:
                logger.info(f"Parsed query '{query}' -> {filters}")
                return filters

            logger.warning(f"Could not parse JSON from Ollama response: {text}")
            return {"text_search": query}

    except httpx.TimeoutException:
        logger.warning("Ollama request timed out, falling back to text search")
        return {"text_search": query}
    except httpx.HTTPError as e:
        logger.warning(f"Ollama HTTP error: {e}, falling back to text search")
        return {"text_search": query}
    except Exception as e:
        logger.warning(f"Ollama error: {e}, falling back to text search")
        return {"text_search": query}


def _extract_json(text: str) -> dict[str, Any] | None:
    """Extract JSON object from text that may contain extra content.

    Args:
        text: Raw text that should contain JSON

    Returns:
        Parsed JSON dict or None if extraction fails
    """
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in the text
    match = re.search(r"\{[^{}]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None


def build_lp_search_sql(
    filters: dict[str, Any],
    base_conditions: list[str] | None = None,
) -> tuple[str, list[Any]]:
    """Build parameterized SQL WHERE clause from parsed filters.

    Args:
        filters: Dictionary of filters from parse_lp_search_query
        base_conditions: Optional base conditions to include

    Returns:
        Tuple of (WHERE clause string, list of parameters)

    Example:
        >>> where, params = build_lp_search_sql({"aum_min": 0.05})
        >>> print(where)
        'o.is_lp = TRUE AND lp.total_aum_bn >= %s'
        >>> print(params)
        [0.05]
    """
    conditions = base_conditions or ["o.is_lp = TRUE"]
    params: list[Any] = []

    # AUM filters (stored in billions)
    if filters.get("aum_min") is not None:
        conditions.append("lp.total_aum_bn >= %s")
        params.append(float(filters["aum_min"]))

    if filters.get("aum_max") is not None:
        conditions.append("lp.total_aum_bn <= %s")
        params.append(float(filters["aum_max"]))

    # LP type filter
    if filters.get("lp_type"):
        conditions.append("lp.lp_type = %s")
        params.append(filters["lp_type"])

    # Location filter (search city and country)
    if filters.get("location"):
        conditions.append("(o.hq_city ILIKE %s OR o.hq_country ILIKE %s)")
        location_pattern = f"%{filters['location']}%"
        params.extend([location_pattern, location_pattern])

    # Strategy filter (array contains)
    if filters.get("strategies"):
        strategies = filters["strategies"]
        if isinstance(strategies, str):
            strategies = [strategies]
        # Use array overlap operator
        conditions.append("lp.strategies && %s::text[]")
        params.append(strategies)

    # Check size filters (stored in millions)
    if filters.get("check_size_min") is not None:
        conditions.append("lp.check_size_max_mm >= %s")
        params.append(float(filters["check_size_min"]))

    if filters.get("check_size_max") is not None:
        conditions.append("lp.check_size_min_mm <= %s")
        params.append(float(filters["check_size_max"]))

    # Text search fallback
    if filters.get("text_search"):
        conditions.append("(o.name ILIKE %s OR o.hq_city ILIKE %s)")
        text_pattern = f"%{filters['text_search']}%"
        params.extend([text_pattern, text_pattern])

    return " AND ".join(conditions), params


def is_natural_language_query(query: str) -> bool:
    """Detect if a query looks like natural language vs simple text.

    Args:
        query: Search query string

    Returns:
        True if query appears to be natural language

    Example:
        >>> is_natural_language_query("CalPERS")
        False
        >>> is_natural_language_query("50m or more aum")
        True
    """
    if not query or len(query) < 5:
        return False

    # Keywords that suggest natural language
    nl_patterns = [
        r"\d+[mMbB]",  # Numbers with M/B suffix (50M, 1B)
        r"more than",
        r"less than",
        r"at least",
        r"greater than",
        r"over \d",
        r"under \d",
        r"between \d",
        r"with .+ aum",
        r"pension|endowment|family office|sovereign",
        r"buyout|growth|venture|infrastructure",
        r"in (california|new york|texas|london|europe)",
        r"europe|asia|americas|middle east|africa",  # Continent/region names
    ]

    query_lower = query.lower()
    for pattern in nl_patterns:
        if re.search(pattern, query_lower):
            return True

    return False
