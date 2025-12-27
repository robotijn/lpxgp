"""LLM-powered pitch deck analysis for enhanced matching.

This module uses LLMs (via OpenRouter or Ollama) to extract structured
information from pitch deck text, enabling more sophisticated GP-LP matching.

Extracted Information:
    - Investment strategy details (primary, sub-strategies, stage, deal size)
    - Geographic focus with specificity levels
    - Sector expertise and thematic investments
    - Track record metrics (IRR, MOIC, DPI, exits)
    - Team composition and experience
    - Fund terms (fees, carry, GP commitment)
    - ESG/Impact alignment
    - Key differentiators and thesis

Usage:
    from src.pitch_deck_analyzer import analyze_pitch_deck

    extracted = await analyze_pitch_deck(pitch_deck_text)
    if extracted:
        print(f"Strategy: {extracted['strategy_details']['primary']}")
        print(f"Track Record IRR: {extracted['track_record']['gross_irr']}")

The extracted data integrates with the matching algorithm to provide:
    - More granular strategy alignment scoring
    - Track record quality assessment
    - Team experience matching
    - ESG mandate alignment
"""

from __future__ import annotations

import json
import logging
from typing import Any, TypedDict

import httpx

from src.config import get_settings

logger = logging.getLogger(__name__)


# =============================================================================
# Type Definitions for Extracted Data
# =============================================================================


class StrategyDetails(TypedDict, total=False):
    """Extracted investment strategy information."""

    primary: str  # buyout, growth, venture, credit, etc.
    sub_strategies: list[str]  # sector-specific, stage-specific
    stage: str  # early, growth, late, multi-stage
    deal_size_min_mm: float | None
    deal_size_max_mm: float | None
    hold_period_years: float | None
    value_creation_approach: str | None


class GeographicDetails(TypedDict, total=False):
    """Extracted geographic focus information."""

    primary_regions: list[str]  # North America, Europe, Asia, etc.
    countries: list[str]  # Specific countries
    emerging_market_allocation_pct: float | None
    local_focus: bool  # Whether focused on local/domestic only


class SectorDetails(TypedDict, total=False):
    """Extracted sector focus information."""

    primary_sectors: list[str]  # Technology, Healthcare, Consumer, etc.
    sub_sectors: list[str]  # SaaS, Fintech, Biotech, etc.
    themes: list[str]  # AI/ML, Climate, Digital Transformation, etc.
    excluded_sectors: list[str]  # Sectors explicitly avoided


class TrackRecordDetails(TypedDict, total=False):
    """Extracted track record information."""

    prior_funds: int | None
    total_capital_managed_mm: float | None
    gross_irr_pct: float | None
    net_irr_pct: float | None
    gross_moic: float | None
    net_moic: float | None
    dpi: float | None  # Distributions to Paid-In
    rvpi: float | None  # Residual Value to Paid-In
    notable_exits: list[str]  # Company names with multiples
    realized_investments: int | None
    unrealized_investments: int | None


class TeamDetails(TypedDict, total=False):
    """Extracted team information."""

    total_partners: int | None
    total_investment_professionals: int | None
    avg_experience_years: float | None
    domain_expertise: list[str]  # Areas of expertise
    prior_firms: list[str]  # Previous notable firms
    key_person_names: list[str]
    operator_experience: bool  # Whether team has operating experience


class FundTermsDetails(TypedDict, total=False):
    """Extracted fund terms information."""

    target_size_mm: float | None
    hard_cap_mm: float | None
    management_fee_pct: float | None
    carried_interest_pct: float | None
    preferred_return_pct: float | None
    gp_commitment_pct: float | None
    fund_term_years: int | None
    investment_period_years: int | None


class ESGDetails(TypedDict, total=False):
    """Extracted ESG/Impact information."""

    has_esg_policy: bool
    is_impact_fund: bool
    un_sdg_aligned: list[str]  # UN Sustainable Development Goals
    dei_focus: bool  # Diversity, Equity, Inclusion focus
    climate_focus: bool
    impact_metrics: list[str]  # Tracked impact metrics
    pri_signatory: bool  # UN PRI Signatory


class ExtractedPitchDeckData(TypedDict, total=False):
    """Complete extracted data from a pitch deck."""

    strategy_details: StrategyDetails
    geographic_details: GeographicDetails
    sector_details: SectorDetails
    track_record: TrackRecordDetails
    team_details: TeamDetails
    fund_terms: FundTermsDetails
    esg_details: ESGDetails
    investment_thesis_summary: str
    key_differentiators: list[str]
    target_lp_types: list[str]  # pension, endowment, family_office, etc.
    extraction_confidence: float  # 0-1 confidence score
    extraction_notes: list[str]  # Caveats or missing data notes


# =============================================================================
# LLM Extraction Prompt
# =============================================================================

EXTRACTION_PROMPT = """You are an expert private equity analyst. Extract structured information from this pitch deck text.

PITCH DECK TEXT:
{pitch_deck_text}

---

Extract the following information. Use null for any field where information is not available or unclear.
Be conservative with numerical estimates - only extract numbers explicitly stated.

Output a JSON object with this exact structure:

{{
  "strategy_details": {{
    "primary": "one of: buyout, growth_equity, venture_capital, credit, real_estate, infrastructure, secondaries, fund_of_funds, other",
    "sub_strategies": ["list of specific focus areas"],
    "stage": "one of: seed, early, growth, late, multi_stage, buyout",
    "deal_size_min_mm": null or number,
    "deal_size_max_mm": null or number,
    "hold_period_years": null or number,
    "value_creation_approach": "brief description or null"
  }},
  "geographic_details": {{
    "primary_regions": ["list of regions: North America, Western Europe, Asia Pacific, etc."],
    "countries": ["list of specific countries"],
    "emerging_market_allocation_pct": null or number 0-100,
    "local_focus": true/false
  }},
  "sector_details": {{
    "primary_sectors": ["list: Technology, Healthcare, Consumer, Industrials, Financial Services, etc."],
    "sub_sectors": ["more specific: SaaS, Fintech, Biotech, E-commerce, etc."],
    "themes": ["investment themes: AI/ML, Climate Tech, Digital Transformation, etc."],
    "excluded_sectors": ["sectors explicitly avoided"]
  }},
  "track_record": {{
    "prior_funds": null or number,
    "total_capital_managed_mm": null or number,
    "gross_irr_pct": null or number,
    "net_irr_pct": null or number,
    "gross_moic": null or number,
    "net_moic": null or number,
    "dpi": null or number,
    "notable_exits": ["Company Name (Xm multiple)", ...],
    "realized_investments": null or number,
    "unrealized_investments": null or number
  }},
  "team_details": {{
    "total_partners": null or number,
    "total_investment_professionals": null or number,
    "avg_experience_years": null or number,
    "domain_expertise": ["areas of expertise"],
    "prior_firms": ["previous notable firms"],
    "key_person_names": ["partner names mentioned"],
    "operator_experience": true/false
  }},
  "fund_terms": {{
    "target_size_mm": null or number,
    "hard_cap_mm": null or number,
    "management_fee_pct": null or number,
    "carried_interest_pct": null or number,
    "preferred_return_pct": null or number,
    "gp_commitment_pct": null or number,
    "fund_term_years": null or number,
    "investment_period_years": null or number
  }},
  "esg_details": {{
    "has_esg_policy": true/false,
    "is_impact_fund": true/false,
    "un_sdg_aligned": ["SDG numbers or names if mentioned"],
    "dei_focus": true/false,
    "climate_focus": true/false,
    "impact_metrics": ["metrics tracked"],
    "pri_signatory": true/false
  }},
  "investment_thesis_summary": "2-3 sentence summary of the investment thesis",
  "key_differentiators": ["3-5 key competitive advantages"],
  "target_lp_types": ["types of LPs targeted: pension, endowment, family_office, sovereign_wealth, insurance, etc."],
  "extraction_confidence": 0.0 to 1.0,
  "extraction_notes": ["any caveats about missing or unclear data"]
}}

Output ONLY the JSON, no other text. Ensure all JSON is valid."""


# =============================================================================
# Analysis Functions
# =============================================================================


async def analyze_pitch_deck(
    pitch_deck_text: str,
    use_openrouter: bool = True,
) -> ExtractedPitchDeckData | None:
    """Extract structured information from pitch deck text using LLM.

    Uses either OpenRouter (cloud) or Ollama (local) to analyze the pitch
    deck text and extract structured data for enhanced matching.

    Args:
        pitch_deck_text: Raw text extracted from the pitch deck.
        use_openrouter: If True, use OpenRouter API. If False, use local Ollama.

    Returns:
        ExtractedPitchDeckData with structured fields, or None if extraction fails.

    Example:
        >>> text = "Fund III targets $500M for growth equity in technology..."
        >>> data = await analyze_pitch_deck(text)
        >>> print(data["strategy_details"]["primary"])
        "growth_equity"
    """
    if not pitch_deck_text or len(pitch_deck_text) < 100:
        logger.warning("Pitch deck text too short for meaningful analysis")
        return None

    # Truncate if too long (model context limits)
    max_chars = 50000
    if len(pitch_deck_text) > max_chars:
        pitch_deck_text = pitch_deck_text[:max_chars] + "\n[Text truncated...]"
        logger.info(f"Truncated pitch deck text to {max_chars} characters")

    settings = get_settings()

    if use_openrouter and settings.openrouter_api_key:
        return await _analyze_with_openrouter(pitch_deck_text, settings)
    else:
        return await _analyze_with_ollama(pitch_deck_text, settings)


async def _analyze_with_openrouter(
    pitch_deck_text: str,
    settings: Any,
) -> ExtractedPitchDeckData | None:
    """Analyze pitch deck using OpenRouter API.

    Args:
        pitch_deck_text: Text to analyze.
        settings: Application settings with API key.

    Returns:
        Extracted data or None if analysis fails.
    """
    prompt = EXTRACTION_PROMPT.format(pitch_deck_text=pitch_deck_text)

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://lpxgp.com",
                    "X-Title": "LPxGP Pitch Deck Analyzer",
                },
                json={
                    "model": "anthropic/claude-3.5-sonnet",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert private equity analyst. "
                            "Extract structured data from pitch decks. "
                            "Output only valid JSON.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 4000,
                },
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return _parse_extraction_response(content)
            else:
                logger.error(
                    f"OpenRouter API error: {response.status_code} - {response.text}"
                )
                return None

    except Exception as e:
        logger.error(f"OpenRouter analysis failed: {e}")
        return None


async def _analyze_with_ollama(
    pitch_deck_text: str,
    settings: Any,
) -> ExtractedPitchDeckData | None:
    """Analyze pitch deck using local Ollama instance.

    Args:
        pitch_deck_text: Text to analyze.
        settings: Application settings with Ollama config.

    Returns:
        Extracted data or None if analysis fails.
    """
    prompt = EXTRACTION_PROMPT.format(pitch_deck_text=pitch_deck_text)

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                },
            )

            if response.status_code == 200:
                result = response.json()
                content = result.get("response", "").strip()
                return _parse_extraction_response(content)
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return None

    except Exception as e:
        logger.warning(f"Ollama analysis failed (may not be running): {e}")
        return None


def _parse_extraction_response(raw_response: str) -> ExtractedPitchDeckData | None:
    """Parse LLM response into structured data.

    Handles markdown code blocks and validates JSON structure.

    Args:
        raw_response: Raw text response from LLM.

    Returns:
        Parsed ExtractedPitchDeckData or None if parsing fails.
    """
    try:
        # Handle markdown code blocks
        if "```json" in raw_response:
            raw_response = raw_response.split("```json")[1].split("```")[0]
        elif "```" in raw_response:
            parts = raw_response.split("```")
            if len(parts) >= 2:
                raw_response = parts[1]

        # Clean up response
        raw_response = raw_response.strip()

        # Parse JSON
        data = json.loads(raw_response)

        # Validate required fields exist (with defaults)
        return _normalize_extracted_data(data)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON response: {e}")
        logger.debug(f"Raw response: {raw_response[:500]}")
        return None
    except Exception as e:
        logger.error(f"Failed to process extraction response: {e}")
        return None


def _normalize_extracted_data(data: dict[str, Any]) -> ExtractedPitchDeckData:
    """Normalize and validate extracted data structure.

    Ensures all expected fields exist with appropriate defaults.

    Args:
        data: Raw parsed JSON data.

    Returns:
        Normalized ExtractedPitchDeckData.
    """
    normalized: ExtractedPitchDeckData = {
        "strategy_details": _normalize_strategy(data.get("strategy_details", {})),
        "geographic_details": _normalize_geographic(
            data.get("geographic_details", {})
        ),
        "sector_details": _normalize_sector(data.get("sector_details", {})),
        "track_record": _normalize_track_record(data.get("track_record", {})),
        "team_details": _normalize_team(data.get("team_details", {})),
        "fund_terms": _normalize_fund_terms(data.get("fund_terms", {})),
        "esg_details": _normalize_esg(data.get("esg_details", {})),
        "investment_thesis_summary": data.get("investment_thesis_summary", ""),
        "key_differentiators": data.get("key_differentiators", []),
        "target_lp_types": data.get("target_lp_types", []),
        "extraction_confidence": float(data.get("extraction_confidence", 0.5)),
        "extraction_notes": data.get("extraction_notes", []),
    }
    return normalized


def _normalize_strategy(data: dict[str, Any]) -> StrategyDetails:
    """Normalize strategy details."""
    return StrategyDetails(
        primary=data.get("primary", ""),
        sub_strategies=data.get("sub_strategies", []),
        stage=data.get("stage", ""),
        deal_size_min_mm=_safe_float(data.get("deal_size_min_mm")),
        deal_size_max_mm=_safe_float(data.get("deal_size_max_mm")),
        hold_period_years=_safe_float(data.get("hold_period_years")),
        value_creation_approach=data.get("value_creation_approach"),
    )


def _normalize_geographic(data: dict[str, Any]) -> GeographicDetails:
    """Normalize geographic details."""
    return GeographicDetails(
        primary_regions=data.get("primary_regions", []),
        countries=data.get("countries", []),
        emerging_market_allocation_pct=_safe_float(
            data.get("emerging_market_allocation_pct")
        ),
        local_focus=bool(data.get("local_focus", False)),
    )


def _normalize_sector(data: dict[str, Any]) -> SectorDetails:
    """Normalize sector details."""
    return SectorDetails(
        primary_sectors=data.get("primary_sectors", []),
        sub_sectors=data.get("sub_sectors", []),
        themes=data.get("themes", []),
        excluded_sectors=data.get("excluded_sectors", []),
    )


def _normalize_track_record(data: dict[str, Any]) -> TrackRecordDetails:
    """Normalize track record details."""
    return TrackRecordDetails(
        prior_funds=_safe_int(data.get("prior_funds")),
        total_capital_managed_mm=_safe_float(data.get("total_capital_managed_mm")),
        gross_irr_pct=_safe_float(data.get("gross_irr_pct")),
        net_irr_pct=_safe_float(data.get("net_irr_pct")),
        gross_moic=_safe_float(data.get("gross_moic")),
        net_moic=_safe_float(data.get("net_moic")),
        dpi=_safe_float(data.get("dpi")),
        rvpi=_safe_float(data.get("rvpi")),
        notable_exits=data.get("notable_exits", []),
        realized_investments=_safe_int(data.get("realized_investments")),
        unrealized_investments=_safe_int(data.get("unrealized_investments")),
    )


def _normalize_team(data: dict[str, Any]) -> TeamDetails:
    """Normalize team details."""
    return TeamDetails(
        total_partners=_safe_int(data.get("total_partners")),
        total_investment_professionals=_safe_int(
            data.get("total_investment_professionals")
        ),
        avg_experience_years=_safe_float(data.get("avg_experience_years")),
        domain_expertise=data.get("domain_expertise", []),
        prior_firms=data.get("prior_firms", []),
        key_person_names=data.get("key_person_names", []),
        operator_experience=bool(data.get("operator_experience", False)),
    )


def _normalize_fund_terms(data: dict[str, Any]) -> FundTermsDetails:
    """Normalize fund terms details."""
    return FundTermsDetails(
        target_size_mm=_safe_float(data.get("target_size_mm")),
        hard_cap_mm=_safe_float(data.get("hard_cap_mm")),
        management_fee_pct=_safe_float(data.get("management_fee_pct")),
        carried_interest_pct=_safe_float(data.get("carried_interest_pct")),
        preferred_return_pct=_safe_float(data.get("preferred_return_pct")),
        gp_commitment_pct=_safe_float(data.get("gp_commitment_pct")),
        fund_term_years=_safe_int(data.get("fund_term_years")),
        investment_period_years=_safe_int(data.get("investment_period_years")),
    )


def _normalize_esg(data: dict[str, Any]) -> ESGDetails:
    """Normalize ESG details."""
    return ESGDetails(
        has_esg_policy=bool(data.get("has_esg_policy", False)),
        is_impact_fund=bool(data.get("is_impact_fund", False)),
        un_sdg_aligned=data.get("un_sdg_aligned", []),
        dei_focus=bool(data.get("dei_focus", False)),
        climate_focus=bool(data.get("climate_focus", False)),
        impact_metrics=data.get("impact_metrics", []),
        pri_signatory=bool(data.get("pri_signatory", False)),
    )


def _safe_float(value: Any) -> float | None:
    """Safely convert value to float."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    """Safely convert value to int."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# =============================================================================
# Matching Enhancement Functions
# =============================================================================


def calculate_enhanced_match_score(
    extracted_data: ExtractedPitchDeckData,
    lp_preferences: dict[str, Any],
) -> dict[str, float]:
    """Calculate additional match scores using extracted pitch deck data.

    Provides enhanced scoring dimensions beyond the basic matching algorithm.

    Args:
        extracted_data: Structured data extracted from pitch deck.
        lp_preferences: LP's investment preferences and requirements.

    Returns:
        Dictionary of additional score components:
            - track_record_quality: 0-100 based on IRR, MOIC, DPI
            - team_experience: 0-100 based on years and expertise overlap
            - esg_alignment: 0-100 based on ESG policy match
            - sector_depth: 0-100 based on sub-sector and theme overlap
            - thesis_alignment: 0-100 based on thesis similarity
    """
    scores: dict[str, float] = {}

    # Track Record Quality Score
    track_record = extracted_data.get("track_record", {})
    irr = track_record.get("gross_irr_pct")
    moic = track_record.get("gross_moic")
    dpi = track_record.get("dpi")

    track_score = 50.0  # Base score
    if irr is not None:
        # IRR benchmarks: <10% poor, 10-20% average, 20-30% good, >30% excellent
        if irr >= 30:
            track_score += 30
        elif irr >= 20:
            track_score += 20
        elif irr >= 10:
            track_score += 10

    if moic is not None:
        # MOIC benchmarks: <1.5x poor, 1.5-2x average, 2-3x good, >3x excellent
        if moic >= 3.0:
            track_score += 15
        elif moic >= 2.0:
            track_score += 10
        elif moic >= 1.5:
            track_score += 5

    if dpi is not None:
        # DPI benchmarks: >1 means returned capital, >1.5 good, >2 excellent
        if dpi >= 2.0:
            track_score += 5
        elif dpi >= 1.0:
            track_score += 3

    scores["track_record_quality"] = min(100.0, track_score)

    # Team Experience Score
    team = extracted_data.get("team_details", {})
    avg_exp = team.get("avg_experience_years")
    partners = team.get("total_partners")
    has_operator = team.get("operator_experience", False)

    team_score = 50.0
    if avg_exp is not None:
        if avg_exp >= 20:
            team_score += 25
        elif avg_exp >= 15:
            team_score += 15
        elif avg_exp >= 10:
            team_score += 10

    if partners and partners >= 3:
        team_score += 10
    if has_operator:
        team_score += 15

    scores["team_experience"] = min(100.0, team_score)

    # ESG Alignment Score
    esg = extracted_data.get("esg_details", {})
    lp_esg_required = lp_preferences.get("esg_required", False)
    lp_impact_focus = lp_preferences.get("impact_focus", False)

    esg_score = 50.0
    if lp_esg_required:
        if esg.get("has_esg_policy"):
            esg_score = 80.0
            if esg.get("pri_signatory"):
                esg_score += 10
            if esg.get("climate_focus"):
                esg_score += 10
        else:
            esg_score = 20.0  # Penalty for not having ESG when required
    else:
        if esg.get("has_esg_policy"):
            esg_score = 70.0  # Bonus for having ESG even when not required

    if lp_impact_focus and esg.get("is_impact_fund"):
        esg_score += 20

    scores["esg_alignment"] = min(100.0, esg_score)

    # Sector Depth Score
    sectors = extracted_data.get("sector_details", {})
    fund_sectors = set(s.lower() for s in sectors.get("primary_sectors", []))
    fund_themes = set(t.lower() for t in sectors.get("themes", []))

    lp_sectors = set(
        s.lower() for s in lp_preferences.get("sector_preferences", [])
    )

    # Calculate overlap
    sector_overlap = len(fund_sectors & lp_sectors)
    theme_overlap = len(fund_themes & lp_sectors)

    if lp_sectors:
        sector_score = (sector_overlap / len(lp_sectors)) * 70
        sector_score += (theme_overlap / len(lp_sectors)) * 30
    else:
        sector_score = 50.0  # Neutral if LP has no sector preference

    scores["sector_depth"] = min(100.0, sector_score)

    return scores


def get_matching_insights(
    extracted_data: ExtractedPitchDeckData,
) -> dict[str, Any]:
    """Generate insights from extracted data for matching UI display.

    Args:
        extracted_data: Structured data extracted from pitch deck.

    Returns:
        Dictionary with summarized insights for display:
            - headline_metrics: Key numbers (IRR, MOIC, fund size)
            - strengths: List of notable strengths
            - considerations: Points requiring attention
    """
    insights: dict[str, Any] = {
        "headline_metrics": {},
        "strengths": [],
        "considerations": [],
    }

    # Headline metrics
    track_record = extracted_data.get("track_record", {})
    fund_terms = extracted_data.get("fund_terms", {})

    if track_record.get("gross_irr_pct"):
        insights["headline_metrics"]["irr"] = f"{track_record['gross_irr_pct']:.1f}%"
    if track_record.get("gross_moic"):
        insights["headline_metrics"]["moic"] = f"{track_record['gross_moic']:.1f}x"
    if fund_terms.get("target_size_mm"):
        insights["headline_metrics"]["target_size"] = (
            f"${fund_terms['target_size_mm']:.0f}M"
        )
    if track_record.get("prior_funds") is not None:
        prior_funds = track_record.get("prior_funds") or 0
        insights["headline_metrics"]["fund_number"] = f"Fund {prior_funds + 1}"

    # Strengths
    if (track_record.get("gross_irr_pct") or 0) >= 25:
        insights["strengths"].append("Strong track record with top-quartile returns")

    team = extracted_data.get("team_details", {})
    if (team.get("avg_experience_years") or 0) >= 15:
        insights["strengths"].append(
            f"Experienced team averaging {team['avg_experience_years']:.0f} years"
        )

    if team.get("operator_experience"):
        insights["strengths"].append("Team includes operators with direct experience")

    esg = extracted_data.get("esg_details", {})
    if esg.get("has_esg_policy") and esg.get("pri_signatory"):
        insights["strengths"].append("ESG policy with UN PRI signatory status")

    sectors = extracted_data.get("sector_details", {})
    if sectors.get("themes"):
        insights["strengths"].append(
            f"Thematic focus: {', '.join(sectors['themes'][:3])}"
        )

    # Considerations
    if not track_record.get("gross_irr_pct"):
        insights["considerations"].append("Track record metrics not disclosed")

    if (track_record.get("prior_funds") or 0) < 2:
        insights["considerations"].append("Emerging manager - limited fund history")

    if not esg.get("has_esg_policy"):
        insights["considerations"].append("No formal ESG policy disclosed")

    differentiators = extracted_data.get("key_differentiators", [])
    if differentiators:
        insights["key_differentiators"] = differentiators[:3]

    return insights
