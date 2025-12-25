"""
AI-Powered Matching Service for LPxGP

This module provides:
1. Rule-based scoring between funds and LPs
2. LLM-powered content generation for match explanations
"""

import json
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


def _to_float(val, default=0.0):
    """Convert value to float, handling Decimal, None, etc."""
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def calculate_match_score(fund: dict, lp: dict) -> dict:
    """
    Calculate compatibility score between a fund and an LP.

    Args:
        fund: Fund data with keys: strategy, geographic_focus, sector_focus,
              target_size_mm, fund_number, esg_policy
        lp: LP profile with keys: strategies, geographic_preferences,
            sector_preferences, fund_size_min_mm, fund_size_max_mm,
            esg_required, emerging_manager_ok, min_fund_number

    Returns:
        dict with keys:
            - score: Overall score 0-100
            - score_breakdown: Dict of individual scores
            - passed_hard_filters: Whether all hard filters passed
    """
    score_breakdown = {}

    # === HARD FILTERS (must all pass) ===

    # 1. Strategy match - fund strategy must be in LP's acceptable strategies
    lp_strategies = lp.get("strategies") or []
    fund_strategy = fund.get("strategy") or ""
    strategy_match = fund_strategy.lower() in [s.lower() for s in lp_strategies] if fund_strategy else False
    score_breakdown["strategy"] = 100 if strategy_match else 0

    # 2. ESG requirement - if LP requires ESG, fund must have ESG policy
    esg_required = lp.get("esg_required", False)
    fund_esg = fund.get("esg_policy", False)
    esg_match = (not esg_required) or fund_esg
    score_breakdown["esg"] = 100 if esg_match else 0

    # 3. Emerging manager check - if fund is emerging (fund_number <= 2), LP must allow it
    fund_number = fund.get("fund_number") or 1
    emerging_manager_ok = lp.get("emerging_manager_ok", False)
    is_emerging = fund_number <= 2
    emerging_match = (not is_emerging) or emerging_manager_ok
    score_breakdown["emerging_manager"] = 100 if emerging_match else 0

    # 4. Fund size fit - fund target must be within LP's acceptable range
    target_size = _to_float(fund.get("target_size_mm"), 0)
    fund_size_min = _to_float(lp.get("fund_size_min_mm"), 0)
    fund_size_max = _to_float(lp.get("fund_size_max_mm"), float("inf"))

    # Handle None/0 max as unlimited
    if fund_size_max == 0:
        fund_size_max = float("inf")

    size_match = fund_size_min <= target_size <= fund_size_max
    score_breakdown["fund_size"] = 100 if size_match else 0

    # Check if all hard filters passed
    passed_hard_filters = all([
        strategy_match,
        esg_match,
        emerging_match,
        size_match
    ])

    # === SOFT SCORES (always calculate for breakdown visibility) ===

    # 5. Geography overlap (30% weight)
    fund_geo = fund.get("geographic_focus") or []
    lp_geo = lp.get("geographic_preferences") or []

    if fund_geo and lp_geo:
        # Normalize to lowercase for comparison
        fund_geo_lower = [g.lower() for g in fund_geo]
        lp_geo_lower = [g.lower() for g in lp_geo]

        # Check for "global" which matches everything
        if "global" in lp_geo_lower:
            geo_score = 100
        else:
            overlap = sum(1 for g in fund_geo_lower if g in lp_geo_lower)
            geo_score = (overlap / len(fund_geo)) * 100 if fund_geo else 0
    else:
        geo_score = 50  # Neutral if either is missing
    score_breakdown["geography"] = round(geo_score, 1)

    # 6. Sector overlap (30% weight)
    fund_sectors = fund.get("sector_focus") or []
    lp_sectors = lp.get("sector_preferences") or []

    if fund_sectors and lp_sectors:
        fund_sectors_lower = [s.lower().replace("_", " ") for s in fund_sectors]
        lp_sectors_lower = [s.lower().replace("_", " ") for s in lp_sectors]

        # Fuzzy matching - check for partial matches
        overlap = 0
        for fs in fund_sectors_lower:
            for ls in lp_sectors_lower:
                if fs in ls or ls in fs:
                    overlap += 1
                    break
        sector_score = (overlap / len(fund_sectors)) * 100 if fund_sectors else 0
    else:
        sector_score = 50  # Neutral if either is missing
    score_breakdown["sector"] = round(sector_score, 1)

    # 7. Track record score (20% weight)
    min_fund_number = lp.get("min_fund_number") or 1
    if fund_number >= min_fund_number:
        track_score = 100
    else:
        # Partial credit based on how close they are
        track_score = (fund_number / min_fund_number) * 100
    score_breakdown["track_record"] = round(track_score, 1)

    # 8. Size fit quality (20% weight) - how centered is fund in LP's range?
    if target_size and fund_size_min and fund_size_max < float("inf"):
        range_mid = (fund_size_min + fund_size_max) / 2
        range_span = fund_size_max - fund_size_min
        if range_span > 0:
            distance_from_mid = abs(target_size - range_mid)
            size_fit_score = max(0, 100 - (distance_from_mid / range_span * 100))
        else:
            size_fit_score = 100 if target_size == fund_size_min else 0
    else:
        size_fit_score = 100 if size_match else 50
    score_breakdown["size_fit"] = round(size_fit_score, 1)

    # If hard filters failed, return 0 score but with full breakdown
    if not passed_hard_filters:
        return {
            "score": 0,
            "score_breakdown": score_breakdown,
            "passed_hard_filters": False
        }

    # Calculate weighted average of soft scores
    weights = {
        "geography": 0.30,
        "sector": 0.30,
        "track_record": 0.20,
        "size_fit": 0.20
    }

    final_score = sum(
        score_breakdown[key] * weight
        for key, weight in weights.items()
    )

    return {
        "score": round(final_score, 1),
        "score_breakdown": score_breakdown,
        "passed_hard_filters": True
    }


async def generate_match_content(
    fund: dict,
    lp: dict,
    score_breakdown: dict,
    ollama_base_url: str = "http://localhost:11434",
    ollama_model: str = "deepseek-r1:8b"
) -> dict:
    """
    Use Ollama LLM to generate match explanation, talking points, and concerns.

    Args:
        fund: Fund data
        lp: LP profile data
        score_breakdown: Scores from calculate_match_score
        ollama_base_url: Ollama API base URL
        ollama_model: Model to use

    Returns:
        dict with keys: explanation, talking_points, concerns
    """

    # Build context for the LLM
    prompt = f"""You are an expert private equity advisor. Analyze this GP-LP match and provide insights.

FUND DETAILS:
- Name: {fund.get('name', 'Unknown Fund')}
- GP: {fund.get('gp_name', 'Unknown GP')}
- Strategy: {fund.get('strategy', 'Not specified')}
- Target Size: ${fund.get('target_size_mm', 0)}M
- Vintage: {fund.get('vintage_year', 'TBD')}
- Fund Number: {fund.get('fund_number', 1)}
- Geographic Focus: {', '.join(fund.get('geographic_focus', []) or ['Not specified'])}
- Sector Focus: {', '.join(fund.get('sector_focus', []) or ['Not specified'])}
- Investment Thesis: {fund.get('investment_thesis', 'Not provided')}

LP DETAILS:
- Name: {lp.get('name', 'Unknown LP')}
- Type: {lp.get('lp_type', 'Institutional')}
- Total AUM: ${lp.get('total_aum_bn', 0)}B
- PE Allocation: {lp.get('pe_allocation_pct', 0)}%
- Preferred Strategies: {', '.join(lp.get('strategies', []) or ['Not specified'])}
- Geographic Preferences: {', '.join(lp.get('geographic_preferences', []) or ['Not specified'])}
- Sector Preferences: {', '.join(lp.get('sector_preferences', []) or ['Not specified'])}
- Fund Size Range: ${lp.get('fund_size_min_mm', 0)}M - ${lp.get('fund_size_max_mm', 0)}M
- ESG Required: {'Yes' if lp.get('esg_required') else 'No'}
- Emerging Managers OK: {'Yes' if lp.get('emerging_manager_ok') else 'No'}
- Mandate: {lp.get('mandate_description', 'Not provided')}

MATCH SCORES:
{json.dumps(score_breakdown, indent=2)}

Based on this analysis, provide a JSON response with EXACTLY this structure:
{{
    "explanation": "1-2 sentence summary explaining why this is or isn't a good fit",
    "talking_points": ["point 1", "point 2", "point 3"],
    "concerns": ["concern 1", "concern 2"]
}}

The talking_points should be specific things the GP can emphasize when approaching this LP.
The concerns should be potential objections the LP might raise.

Output ONLY valid JSON, no other text."""

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{ollama_base_url}/api/generate",
                json={
                    "model": ollama_model,
                    "prompt": prompt,
                    "stream": False,
                }
            )

            if response.status_code == 200:
                result = response.json()
                raw_response = result.get("response", "").strip()

                # Try to extract JSON from the response
                try:
                    # Handle case where LLM includes markdown code blocks
                    if "```json" in raw_response:
                        raw_response = raw_response.split("```json")[1].split("```")[0]
                    elif "```" in raw_response:
                        raw_response = raw_response.split("```")[1].split("```")[0]

                    content = json.loads(raw_response)
                    return {
                        "explanation": content.get("explanation", "Match analysis pending."),
                        "talking_points": content.get("talking_points", [])[:3],
                        "concerns": content.get("concerns", [])[:2]
                    }
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse LLM response as JSON: {raw_response[:200]}")

    except Exception as e:
        logger.warning(f"Ollama not available or error: {e}")

    # Fallback to template-based content
    return _generate_fallback_content(fund, lp, score_breakdown)


def _generate_fallback_content(fund: dict, lp: dict, score_breakdown: dict) -> dict:
    """Generate template-based content when LLM is unavailable."""

    score = score_breakdown.get("geography", 50) + score_breakdown.get("sector", 50)
    avg_score = score / 2

    if avg_score >= 80:
        quality = "Excellent"
    elif avg_score >= 60:
        quality = "Strong"
    elif avg_score >= 40:
        quality = "Moderate"
    else:
        quality = "Limited"

    fund_name = fund.get("name", "This fund")
    lp_name = lp.get("name", "This LP")
    strategy = fund.get("strategy", "investment strategy")

    explanation = f"{quality} fit: {fund_name}'s {strategy} strategy aligns with {lp_name}'s investment mandate. "

    if score_breakdown.get("geography", 0) >= 80:
        explanation += "Strong geographic overlap. "
    if score_breakdown.get("sector", 0) >= 80:
        explanation += "Sector focus matches LP preferences."

    talking_points = []
    if score_breakdown.get("track_record", 0) >= 80:
        talking_points.append(f"Fund {fund.get('fund_number', 'N')} demonstrates proven track record")
    if score_breakdown.get("geography", 0) >= 70:
        talking_points.append(f"Geographic focus aligns with LP's {', '.join(lp.get('geographic_preferences', ['regional'])[:2])} mandate")
    if score_breakdown.get("sector", 0) >= 70:
        talking_points.append(f"Sector expertise in {', '.join(fund.get('sector_focus', ['target'])[:2])} matches LP interests")

    # Ensure we have at least 3 talking points
    while len(talking_points) < 3:
        defaults = [
            "Strong alignment with LP's investment strategy",
            "Fund size within LP's preferred range",
            "Experienced team with relevant domain expertise"
        ]
        for d in defaults:
            if d not in talking_points and len(talking_points) < 3:
                talking_points.append(d)

    concerns = []
    if score_breakdown.get("strategy", 100) < 100:
        concerns.append("Strategy may not be a perfect fit for LP's core mandate")
    if score_breakdown.get("emerging_manager", 100) < 100:
        concerns.append("LP may prefer more established managers")
    if score_breakdown.get("size_fit", 100) < 80:
        concerns.append("Fund size is at edge of LP's typical commitment range")

    # Ensure we have at least 2 concerns
    while len(concerns) < 2:
        defaults = [
            "Competitive market with many similar funds seeking LP commitments",
            "LP may have limited allocation capacity in current cycle"
        ]
        for d in defaults:
            if d not in concerns and len(concerns) < 2:
                concerns.append(d)

    return {
        "explanation": explanation.strip(),
        "talking_points": talking_points[:3],
        "concerns": concerns[:2]
    }
