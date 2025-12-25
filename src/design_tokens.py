"""
LPxGP Design Tokens

Centralized color palette and design variables for Python code.
Use these for PDF generation, charts, email templates, etc.

Usage:
    from src.design_tokens import colors, NAVY, ACCENT

    # Access individual colors
    header_color = colors.navy[900]
    accent_color = colors.accent.DEFAULT

    # Or use shortcuts
    primary = NAVY[900]
    link_color = ACCENT
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class NavyPalette:
    """Conservative financial color palette - primary brand colors."""

    n50: str = "#f0f4f8"
    n100: str = "#d9e2ec"
    n200: str = "#bcccdc"
    n300: str = "#9fb3c8"
    n400: str = "#829ab1"
    n500: str = "#627d98"
    n600: str = "#486581"
    n700: str = "#334e68"
    n800: str = "#243b53"
    n900: str = "#102a43"

    def __getitem__(self, key: int) -> str:
        """Allow dict-like access: navy[900]."""
        return getattr(self, f"n{key}")


@dataclass(frozen=True)
class AccentPalette:
    """Accent colors for primary actions, links, and highlights."""

    DEFAULT: str = "#0d6efd"
    dark: str = "#0b5ed7"
    light: str = "#3d8bfd"


@dataclass(frozen=True)
class SlatePalette:
    """Neutral colors for backgrounds, borders, and text."""

    n50: str = "#f8fafc"
    n100: str = "#f1f5f9"
    n200: str = "#e2e8f0"
    n300: str = "#cbd5e1"
    n400: str = "#94a3b8"
    n500: str = "#64748b"
    n600: str = "#475569"
    n700: str = "#334155"
    n800: str = "#1e293b"
    n900: str = "#0f172a"

    def __getitem__(self, key: int) -> str:
        """Allow dict-like access: slate[500]."""
        return getattr(self, f"n{key}")


@dataclass(frozen=True)
class SemanticColors:
    """Status and feedback colors."""

    # Success
    success: str = "#10b981"
    success_light: str = "#d1fae5"
    success_dark: str = "#059669"

    # Warning
    warning: str = "#f59e0b"
    warning_light: str = "#fef3c7"
    warning_dark: str = "#d97706"

    # Error
    error: str = "#ef4444"
    error_light: str = "#fee2e2"
    error_dark: str = "#dc2626"

    # Info
    info: str = "#3b82f6"
    info_light: str = "#dbeafe"
    info_dark: str = "#2563eb"


@dataclass(frozen=True)
class ScoreColors:
    """Color scale for LP match scores (0-100)."""

    excellent: str = "#10b981"  # 90-100: Excellent match
    good: str = "#22c55e"  # 80-89: Good match
    moderate: str = "#eab308"  # 70-79: Moderate match
    low: str = "#f97316"  # 60-69: Low match
    poor: str = "#ef4444"  # <60: Poor match

    def for_score(self, score: int) -> str:
        """Get the appropriate color for a match score."""
        if score >= 90:
            return self.excellent
        elif score >= 80:
            return self.good
        elif score >= 70:
            return self.moderate
        elif score >= 60:
            return self.low
        else:
            return self.poor


@dataclass(frozen=True)
class Colors:
    """All color palettes in one place."""

    navy: NavyPalette = NavyPalette()
    accent: AccentPalette = AccentPalette()
    slate: SlatePalette = SlatePalette()
    semantic: SemanticColors = SemanticColors()
    scores: ScoreColors = ScoreColors()


# Main export
colors = Colors()

# Convenience shortcuts
NAVY: dict[int, str] = {
    50: colors.navy.n50,
    100: colors.navy.n100,
    200: colors.navy.n200,
    300: colors.navy.n300,
    400: colors.navy.n400,
    500: colors.navy.n500,
    600: colors.navy.n600,
    700: colors.navy.n700,
    800: colors.navy.n800,
    900: colors.navy.n900,
}

SLATE: dict[int, str] = {
    50: colors.slate.n50,
    100: colors.slate.n100,
    200: colors.slate.n200,
    300: colors.slate.n300,
    400: colors.slate.n400,
    500: colors.slate.n500,
    600: colors.slate.n600,
    700: colors.slate.n700,
    800: colors.slate.n800,
    900: colors.slate.n900,
}

ACCENT = colors.accent.DEFAULT
ACCENT_DARK = colors.accent.dark

# Typography
FONT_SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
FONT_MONO = "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"


def get_tailwind_config() -> dict:
    """
    Get the Tailwind CSS config object for use in templates.

    Usage in Jinja2:
        <script>
        tailwind.config = {{ get_tailwind_config() | tojson }}
        </script>
    """
    return {
        "theme": {
            "extend": {
                "colors": {
                    "navy": {
                        "50": NAVY[50],
                        "100": NAVY[100],
                        "200": NAVY[200],
                        "300": NAVY[300],
                        "400": NAVY[400],
                        "500": NAVY[500],
                        "600": NAVY[600],
                        "700": NAVY[700],
                        "800": NAVY[800],
                        "900": NAVY[900],
                    },
                    "accent": {
                        "DEFAULT": ACCENT,
                        "dark": ACCENT_DARK,
                    },
                },
                "fontFamily": {
                    "sans": FONT_SANS.split(", "),
                },
            }
        }
    }
