"""AI-Powered Matching Service for LPxGP.

This module provides intelligent matching between investment funds and
Limited Partners (LPs), combining rule-based scoring with optional
LLM-powered content generation.

Features:
    - Rule-based compatibility scoring with hard and soft filters
    - LLM-powered match explanations via Ollama
    - Fallback template-based content generation
    - Detailed score breakdowns for transparency

The matching algorithm evaluates:
    - Strategy alignment (hard filter)
    - ESG policy requirements (hard filter)
    - Emerging manager preferences (hard filter)
    - Fund size fit (hard filter)
    - Geographic overlap (soft score, 30% weight)
    - Sector overlap (soft score, 30% weight)
    - Track record (soft score, 20% weight)
    - Size fit quality (soft score, 20% weight)

Example:
    Basic matching workflow::

        from src.matching import calculate_match_score, generate_match_content

        # Calculate compatibility score
        result = calculate_match_score(fund_data, lp_data)
        if result["passed_hard_filters"]:
            print(f"Match score: {result['score']}")

        # Generate AI content for the match
        content = await generate_match_content(
            fund_data, lp_data, result["score_breakdown"]
        )
        print(content["explanation"])
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, TypedDict

import httpx

if TYPE_CHECKING:
    pass


# =============================================================================
# Type Definitions
# =============================================================================


class ScoreBreakdown(TypedDict):
    """Breakdown of individual scoring components.

    Attributes:
        strategy: Strategy match score (0 or 100, hard filter).
        esg: ESG policy compliance score (0 or 100, hard filter).
        emerging_manager: Emerging manager acceptance score (0 or 100, hard filter).
        fund_size: Fund size fit score (0 or 100, hard filter).
        geography: Geographic overlap score (0-100, soft score).
        sector: Sector overlap score (0-100, soft score).
        track_record: Track record score (0-100, soft score).
        size_fit: Size fit quality score (0-100, soft score).
    """

    strategy: int | float
    esg: int | float
    emerging_manager: int | float
    fund_size: int | float
    geography: float
    sector: float
    track_record: float
    size_fit: float


class MatchResult(TypedDict):
    """Result of a fund-LP compatibility calculation.

    Attributes:
        score: Overall compatibility score (0-100), or 0 if hard filters failed.
        score_breakdown: Individual scores for each matching criterion.
        passed_hard_filters: Whether all mandatory requirements were met.
    """

    score: float
    score_breakdown: ScoreBreakdown
    passed_hard_filters: bool


class MatchContent(TypedDict):
    """AI-generated content for a fund-LP match.

    Attributes:
        explanation: 1-2 sentence summary of match quality.
        talking_points: List of 3 key points for GP to emphasize.
        concerns: List of 2 potential objections LP might raise.
    """

    explanation: str
    talking_points: list[str]
    concerns: list[str]


class FundData(TypedDict, total=False):
    """Fund data structure for matching.

    All fields are optional to handle partial data gracefully.

    Attributes:
        name: Fund name.
        gp_name: General Partner organization name.
        strategy: Primary investment strategy (buyout, growth, venture, etc.).
        target_size_mm: Target fund size in millions USD.
        vintage_year: Fund vintage year.
        fund_number: Fund sequence number (1, 2, 3, etc.).
        geographic_focus: List of target geographies.
        sector_focus: List of target sectors.
        investment_thesis: Fund's investment thesis description.
        esg_policy: Whether fund has ESG policy.
        pitch_deck_extracted: Structured data extracted from pitch deck (JSON).
    """

    name: str
    gp_name: str
    strategy: str
    target_size_mm: float | int | None
    vintage_year: int | None
    fund_number: int | None
    geographic_focus: list[str] | None
    sector_focus: list[str] | None
    investment_thesis: str | None
    esg_policy: bool
    pitch_deck_extracted: dict[str, Any] | None


class LPData(TypedDict, total=False):
    """LP profile data structure for matching.

    All fields are optional to handle partial data gracefully.

    Attributes:
        name: LP organization name.
        lp_type: Type of LP (pension, endowment, family_office, etc.).
        total_aum_bn: Total assets under management in billions USD.
        pe_allocation_pct: Percentage allocated to private equity.
        strategies: List of acceptable investment strategies.
        geographic_preferences: List of preferred geographies.
        sector_preferences: List of preferred sectors.
        fund_size_min_mm: Minimum acceptable fund size in millions USD.
        fund_size_max_mm: Maximum acceptable fund size in millions USD.
        esg_required: Whether ESG policy is required.
        emerging_manager_ok: Whether emerging managers are acceptable.
        min_fund_number: Minimum acceptable fund number.
        mandate_description: Description of investment mandate.
    """

    name: str
    lp_type: str
    total_aum_bn: float | None
    pe_allocation_pct: float | None
    strategies: list[str] | None
    geographic_preferences: list[str] | None
    sector_preferences: list[str] | None
    fund_size_min_mm: float | None
    fund_size_max_mm: float | None
    esg_required: bool
    emerging_manager_ok: bool
    min_fund_number: int | None
    min_track_record_years: int | None
    mandate_description: str | None


# =============================================================================
# Module Configuration
# =============================================================================

logger: logging.Logger = logging.getLogger(__name__)

# Scoring weights for soft scores (must sum to 1.0)
_SCORING_WEIGHTS: dict[str, float] = {
    "geography": 0.30,
    "sector": 0.30,
    "track_record": 0.20,
    "size_fit": 0.20,
}


# =============================================================================
# Utility Functions
# =============================================================================


def _to_float(val: Any, default: float = 0.0) -> float:
    """Safely convert a value to float.

    Handles various input types including Decimal, None, and invalid values.
    This is necessary because database queries may return Decimal types
    which don't work directly with float arithmetic.

    Args:
        val: Value to convert (int, float, Decimal, str, or None).
        default: Default value if conversion fails. Defaults to 0.0.

    Returns:
        Float representation of the value, or default if conversion fails.

    Example:
        >>> from decimal import Decimal
        >>> _to_float(Decimal("100.50"))
        100.5
        >>> _to_float(None, default=0.0)
        0.0
        >>> _to_float("invalid", default=-1.0)
        -1.0
    """
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _normalize_string_list(items: list[str] | None) -> list[str]:
    """Normalize a list of strings to lowercase.

    Args:
        items: List of strings to normalize, or None.

    Returns:
        List of lowercase strings, or empty list if input is None.

    Example:
        >>> _normalize_string_list(["BUYOUT", "Growth"])
        ['buyout', 'growth']
        >>> _normalize_string_list(None)
        []
    """
    if not items:
        return []
    return [item.lower() for item in items]


# =============================================================================
# Matching Algorithm
# =============================================================================


def calculate_match_score(fund: FundData, lp: LPData) -> MatchResult:
    """Calculate compatibility score between a fund and an LP.

    Evaluates multiple criteria to determine how well a fund matches
    an LP's investment preferences. The algorithm uses:

    Hard Filters (all must pass for score > 0):
        - Strategy: Fund strategy must be in LP's acceptable strategies
        - ESG: If LP requires ESG, fund must have ESG policy
        - Emerging Manager: If fund is emerging (fund_number <= 2), LP must allow it
        - Fund Size: Fund target must be within LP's acceptable range

    Soft Scores (weighted average if hard filters pass):
        - Geography (30%): Overlap between fund and LP geographic focus
        - Sector (30%): Overlap between fund and LP sector preferences
        - Track Record (20%): Fund number vs LP's minimum requirement
        - Size Fit (20%): How centered fund is in LP's preferred range

    Args:
        fund: Fund profile data containing strategy, size, focus areas, etc.
        lp: LP profile data containing preferences and requirements.

    Returns:
        MatchResult containing:
            - score: 0-100 compatibility score (0 if hard filters fail)
            - score_breakdown: Individual scores for each criterion
            - passed_hard_filters: Whether all hard filters passed

    Example:
        >>> fund = {"strategy": "buyout", "target_size_mm": 500}
        >>> lp = {"strategies": ["buyout", "growth"], "fund_size_min_mm": 100}
        >>> result = calculate_match_score(fund, lp)
        >>> print(f"Score: {result['score']}, Passed: {result['passed_hard_filters']}")
    """
    score_breakdown: dict[str, int | float] = {}

    # =========================================================================
    # HARD FILTERS (must all pass)
    # =========================================================================

    # 1. Strategy match - fund strategy must be in LP's acceptable strategies
    lp_strategies = _normalize_string_list(lp.get("strategies"))
    fund_strategy = (fund.get("strategy") or "").lower()
    strategy_match = fund_strategy in lp_strategies if fund_strategy else False
    score_breakdown["strategy"] = 100 if strategy_match else 0

    # 2. ESG requirement - if LP requires ESG, fund must have ESG policy
    esg_required = lp.get("esg_required", False)
    fund_esg = fund.get("esg_policy", False)
    esg_match = (not esg_required) or fund_esg
    score_breakdown["esg"] = 100 if esg_match else 0

    # 3. Emerging manager check - if fund is emerging, LP must allow it
    # Funds with fund_number <= 2 are considered emerging managers
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
        size_match,
    ])

    # =========================================================================
    # SOFT SCORES (always calculate for breakdown visibility)
    # =========================================================================

    # 5. Geography overlap (30% weight)
    fund_geo = fund.get("geographic_focus") or []
    lp_geo = lp.get("geographic_preferences") or []

    if fund_geo and lp_geo:
        fund_geo_lower = _normalize_string_list(fund_geo)
        lp_geo_lower = _normalize_string_list(lp_geo)

        # "Global" matches everything
        if "global" in lp_geo_lower:
            geo_score = 100.0
        else:
            overlap = sum(1 for g in fund_geo_lower if g in lp_geo_lower)
            geo_score = (overlap / len(fund_geo)) * 100 if fund_geo else 0.0
    else:
        # Neutral score if either is missing
        geo_score = 50.0
    score_breakdown["geography"] = round(geo_score, 1)

    # 6. Sector overlap (30% weight)
    fund_sectors = fund.get("sector_focus") or []
    lp_sectors = lp.get("sector_preferences") or []

    if fund_sectors and lp_sectors:
        # Normalize with underscore replacement for fuzzy matching
        fund_sectors_lower = [s.lower().replace("_", " ") for s in fund_sectors]
        lp_sectors_lower = [s.lower().replace("_", " ") for s in lp_sectors]

        # Fuzzy matching - check for partial matches
        overlap = 0
        for fs in fund_sectors_lower:
            for ls in lp_sectors_lower:
                if fs in ls or ls in fs:
                    overlap += 1
                    break
        sector_score = (overlap / len(fund_sectors)) * 100 if fund_sectors else 0.0
    else:
        # Neutral score if either is missing
        sector_score = 50.0
    score_breakdown["sector"] = round(sector_score, 1)

    # 7. Track record score (20% weight)
    min_fund_number = lp.get("min_fund_number") or 1
    if fund_number >= min_fund_number:
        track_score = 100.0
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
            size_fit_score = max(0.0, 100 - (distance_from_mid / range_span * 100))
        else:
            size_fit_score = 100.0 if target_size == fund_size_min else 0.0
    else:
        size_fit_score = 100.0 if size_match else 50.0
    score_breakdown["size_fit"] = round(size_fit_score, 1)

    # =========================================================================
    # FINAL SCORE CALCULATION
    # =========================================================================

    # If hard filters failed, return 0 score but with full breakdown
    if not passed_hard_filters:
        return MatchResult(
            score=0,
            score_breakdown=ScoreBreakdown(**score_breakdown),  # type: ignore
            passed_hard_filters=False,
        )

    # Calculate weighted average of soft scores
    final_score = sum(
        score_breakdown[key] * weight
        for key, weight in _SCORING_WEIGHTS.items()
    )

    return MatchResult(
        score=round(final_score, 1),
        score_breakdown=ScoreBreakdown(**score_breakdown),  # type: ignore
        passed_hard_filters=True,
    )


def calculate_enhanced_match_score(fund: FundData, lp: LPData) -> MatchResult:
    """Calculate enhanced match score using pitch deck extracted data.

    Extends the basic matching algorithm with insights from LLM-extracted
    pitch deck data. If no extracted data is available, falls back to
    the basic algorithm.

    Enhanced scoring includes:
        - Track record quality from IRR/MOIC metrics
        - Team experience depth
        - Sector theme alignment
        - ESG policy strength

    Args:
        fund: Fund profile data with optional pitch_deck_extracted.
        lp: LP profile data with preferences.

    Returns:
        MatchResult with potentially higher precision scoring.
    """
    # Start with basic score
    base_result = calculate_match_score(fund, lp)

    # If hard filters failed, return immediately
    if not base_result["passed_hard_filters"]:
        return base_result

    # Check for extracted pitch deck data
    extracted = fund.get("pitch_deck_extracted")
    if not extracted:
        return base_result

    # Apply enhanced scoring adjustments
    enhanced_adjustments: dict[str, float] = {}

    # Track record quality bonus (up to +10 points)
    track_record = extracted.get("track_record", {})
    irr = track_record.get("gross_irr_pct")
    moic = track_record.get("gross_moic")

    track_bonus = 0.0
    if irr is not None and irr > 0:
        if irr >= 30:
            track_bonus += 5
        elif irr >= 20:
            track_bonus += 3
        elif irr >= 15:
            track_bonus += 1

    if moic is not None and moic > 0:
        if moic >= 3.0:
            track_bonus += 5
        elif moic >= 2.0:
            track_bonus += 3
        elif moic >= 1.5:
            track_bonus += 1

    enhanced_adjustments["track_record_bonus"] = track_bonus

    # Team experience bonus (up to +5 points)
    team = extracted.get("team_details", {})
    avg_exp = team.get("avg_experience_years")
    team_bonus = 0.0

    if avg_exp is not None and avg_exp >= 15:
        team_bonus += 3
    if team.get("operator_experience"):
        team_bonus += 2

    enhanced_adjustments["team_bonus"] = team_bonus

    # ESG alignment bonus (up to +5 points if LP cares about ESG)
    esg_details = extracted.get("esg_details", {})
    esg_bonus = 0.0

    if lp.get("esg_required"):
        if esg_details.get("has_esg_policy"):
            esg_bonus += 3
        if esg_details.get("pri_signatory"):
            esg_bonus += 2

    enhanced_adjustments["esg_bonus"] = esg_bonus

    # Sector depth bonus (up to +5 points)
    sectors = extracted.get("sector_details", {})
    fund_themes = [t.lower() for t in sectors.get("themes", [])]
    lp_sectors = [s.lower() for s in (lp.get("sector_preferences") or [])]

    sector_bonus = 0.0
    if fund_themes and lp_sectors:
        theme_overlap = sum(1 for t in fund_themes if any(s in t or t in s for s in lp_sectors))
        if theme_overlap > 0:
            sector_bonus = min(5.0, theme_overlap * 2)

    enhanced_adjustments["sector_bonus"] = sector_bonus

    # Calculate enhanced score (capped at 100)
    total_bonus = sum(enhanced_adjustments.values())
    enhanced_score = min(100.0, base_result["score"] + total_bonus)

    # Log the enhancement for debugging
    if total_bonus > 0:
        logger.debug(
            f"Enhanced matching: base={base_result['score']:.1f}, "
            f"bonus={total_bonus:.1f}, final={enhanced_score:.1f}"
        )

    return MatchResult(
        score=round(enhanced_score, 1),
        score_breakdown=base_result["score_breakdown"],
        passed_hard_filters=True,
    )


# =============================================================================
# LLM Content Generation
# =============================================================================


async def generate_match_content(
    fund: FundData,
    lp: LPData,
    score_breakdown: ScoreBreakdown,
    ollama_base_url: str = "http://localhost:11434",
    ollama_model: str = "deepseek-r1:8b",
) -> MatchContent:
    """Generate AI-powered match explanation using Ollama LLM.

    Uses a local Ollama instance to generate contextual explanations,
    talking points, and potential concerns for a fund-LP match.
    Falls back to template-based generation if LLM is unavailable.

    Args:
        fund: Fund profile data.
        lp: LP profile data.
        score_breakdown: Scores from calculate_match_score().
        ollama_base_url: Ollama API base URL. Defaults to localhost.
        ollama_model: Ollama model to use. Defaults to "deepseek-r1:8b".

    Returns:
        MatchContent containing:
            - explanation: Summary of match quality
            - talking_points: 3 key points for GP
            - concerns: 2 potential LP objections

    Example:
        >>> content = await generate_match_content(fund, lp, score_breakdown)
        >>> print(content["explanation"])
        "Strong fit: Fund's buyout strategy aligns well with LP's mandate..."
    """
    # Build context prompt for the LLM
    prompt = _build_llm_prompt(fund, lp, score_breakdown)

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{ollama_base_url}/api/generate",
                json={
                    "model": ollama_model,
                    "prompt": prompt,
                    "stream": False,
                },
            )

            if response.status_code == 200:
                result = response.json()
                raw_response = result.get("response", "").strip()

                # Try to extract JSON from the response
                content = _parse_llm_response(raw_response)
                if content:
                    return content

    except Exception as e:
        logger.warning(f"Ollama not available or error: {e}")

    # Fallback to template-based content
    return _generate_fallback_content(fund, lp, score_breakdown)


def _build_llm_prompt(
    fund: FundData,
    lp: LPData,
    score_breakdown: ScoreBreakdown,
) -> str:
    """Build the prompt for LLM content generation.

    Args:
        fund: Fund profile data.
        lp: LP profile data.
        score_breakdown: Matching scores.

    Returns:
        Formatted prompt string for the LLM.
    """
    # Helper to format lists safely
    def format_list(items: list[str] | None) -> str:
        if items:
            return ", ".join(items)
        return "Not specified"

    prompt = f"""You are an expert private equity advisor. Analyze this GP-LP match and provide insights.

FUND DETAILS:
- Name: {fund.get('name', 'Unknown Fund')}
- GP: {fund.get('gp_name', 'Unknown GP')}
- Strategy: {fund.get('strategy', 'Not specified')}
- Target Size: ${fund.get('target_size_mm', 0)}M
- Vintage: {fund.get('vintage_year', 'TBD')}
- Fund Number: {fund.get('fund_number', 1)}
- Geographic Focus: {format_list(fund.get('geographic_focus'))}
- Sector Focus: {format_list(fund.get('sector_focus'))}
- Investment Thesis: {fund.get('investment_thesis', 'Not provided')}

LP DETAILS:
- Name: {lp.get('name', 'Unknown LP')}
- Type: {lp.get('lp_type', 'Institutional')}
- Total AUM: ${lp.get('total_aum_bn', 0)}B
- PE Allocation: {lp.get('pe_allocation_pct', 0)}%
- Preferred Strategies: {format_list(lp.get('strategies'))}
- Geographic Preferences: {format_list(lp.get('geographic_preferences'))}
- Sector Preferences: {format_list(lp.get('sector_preferences'))}
- Fund Size Range: ${lp.get('fund_size_min_mm', 0)}M - ${lp.get('fund_size_max_mm', 0)}M
- ESG Required: {'Yes' if lp.get('esg_required') else 'No'}
- Emerging Managers OK: {'Yes' if lp.get('emerging_manager_ok') else 'No'}
- Mandate: {lp.get('mandate_description', 'Not provided')}

MATCH SCORES:
{json.dumps(dict(score_breakdown), indent=2)}

Based on this analysis, provide a JSON response with EXACTLY this structure:
{{
    "explanation": "1-2 sentence summary explaining why this is or isn't a good fit",
    "talking_points": ["point 1", "point 2", "point 3"],
    "concerns": ["concern 1", "concern 2"]
}}

The talking_points should be specific things the GP can emphasize when approaching this LP.
The concerns should be potential objections the LP might raise.

Output ONLY valid JSON, no other text."""

    return prompt


def _parse_llm_response(raw_response: str) -> MatchContent | None:
    """Parse LLM response into structured content.

    Handles responses that may include markdown code blocks.

    Args:
        raw_response: Raw text response from LLM.

    Returns:
        Parsed MatchContent if successful, None if parsing fails.
    """
    try:
        # Handle case where LLM includes markdown code blocks
        if "```json" in raw_response:
            raw_response = raw_response.split("```json")[1].split("```")[0]
        elif "```" in raw_response:
            raw_response = raw_response.split("```")[1].split("```")[0]

        content = json.loads(raw_response)
        return MatchContent(
            explanation=content.get("explanation", "Match analysis pending."),
            talking_points=content.get("talking_points", [])[:3],
            concerns=content.get("concerns", [])[:2],
        )
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse LLM response as JSON: {raw_response[:200]}")
        return None


def _generate_fallback_content(
    fund: FundData,
    lp: LPData,
    score_breakdown: ScoreBreakdown,
) -> MatchContent:
    """Generate template-based content when LLM is unavailable.

    Provides reasonable default content based on the score breakdown.

    Args:
        fund: Fund profile data.
        lp: LP profile data.
        score_breakdown: Matching scores.

    Returns:
        Template-based MatchContent.
    """
    # Calculate quality assessment
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

    # Build explanation
    explanation = (
        f"{quality} fit: {fund_name}'s {strategy} strategy "
        f"aligns with {lp_name}'s investment mandate. "
    )

    if score_breakdown.get("geography", 0) >= 80:
        explanation += "Strong geographic overlap. "
    if score_breakdown.get("sector", 0) >= 80:
        explanation += "Sector focus matches LP preferences."

    # Build talking points
    talking_points: list[str] = []
    if score_breakdown.get("track_record", 0) >= 80:
        talking_points.append(
            f"Fund {fund.get('fund_number', 'N')} demonstrates proven track record"
        )
    if score_breakdown.get("geography", 0) >= 70:
        geo_prefs = lp.get("geographic_preferences") or ["regional"]
        talking_points.append(
            f"Geographic focus aligns with LP's {', '.join(geo_prefs[:2])} mandate"
        )
    if score_breakdown.get("sector", 0) >= 70:
        sectors = fund.get("sector_focus") or ["target"]
        talking_points.append(
            f"Sector expertise in {', '.join(sectors[:2])} matches LP interests"
        )

    # Ensure we have at least 3 talking points
    defaults = [
        "Strong alignment with LP's investment strategy",
        "Fund size within LP's preferred range",
        "Experienced team with relevant domain expertise",
    ]
    for default in defaults:
        if len(talking_points) >= 3:
            break
        if default not in talking_points:
            talking_points.append(default)

    # Build concerns
    concerns: list[str] = []
    if score_breakdown.get("strategy", 100) < 100:
        concerns.append("Strategy may not be a perfect fit for LP's core mandate")
    if score_breakdown.get("emerging_manager", 100) < 100:
        concerns.append("LP may prefer more established managers")
    if score_breakdown.get("size_fit", 100) < 80:
        concerns.append("Fund size is at edge of LP's typical commitment range")

    # Ensure we have at least 2 concerns
    concern_defaults = [
        "Competitive market with many similar funds seeking LP commitments",
        "LP may have limited allocation capacity in current cycle",
    ]
    for default in concern_defaults:
        if len(concerns) >= 2:
            break
        if default not in concerns:
            concerns.append(default)

    return MatchContent(
        explanation=explanation.strip(),
        talking_points=talking_points[:3],
        concerns=concerns[:2],
    )
