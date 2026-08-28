"""
Severity classification derived from risk score using configurable thresholds.

Default mapping:
    0-24  = Low
    25-49 = Medium
    50-74 = High
    75-100 = Critical

Thresholds are configurable via system settings.
"""

from typing import Optional, Dict


def classify_severity(
    risk_score: float,
    thresholds: Optional[Dict[str, int]] = None,
) -> str:
    """
    Derive severity from calculated risk score.

    Args:
        risk_score: 0-100 float
        thresholds: dict with keys 'low_max', 'medium_max', 'high_max'

    Returns:
        "low", "medium", "high", or "critical"
    """
    t = thresholds or {}
    low_max = t.get("low_max", 24)
    medium_max = t.get("medium_max", 49)
    high_max = t.get("high_max", 74)

    if risk_score <= low_max:
        return "low"
    elif risk_score <= medium_max:
        return "medium"
    elif risk_score <= high_max:
        return "high"
    else:
        return "critical"


def get_severity_color(severity: str) -> str:
    """Return hex color for severity level."""
    colors = {
        "critical": "#ef4444",
        "high": "#f97316",
        "medium": "#eab308",
        "low": "#22c55e",
    }
    return colors.get(severity, "#6b7280")
