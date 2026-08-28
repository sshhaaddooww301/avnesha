"""
Risk Score Calculator for QDS SIEM.

Multi-factor weighted scoring formula:

risk_score = clamp(0, 100,
    w1 * deviation_score +      # 0-100 from measurement deviation
    w2 * verification_penalty + # 0 or 100 based on verification failure
    w3 * frequency_score +      # 0-100 from repeat frequency
    w4 * anomaly_score +        # 0-100 from z-score magnitude
    w5 * hash_mismatch_penalty  # 0 or 100 if signature mismatch
)

Default weights: w1=0.30, w2=0.25, w3=0.15, w4=0.20, w5=0.10

Every risk score stores its breakdown so results are explainable.
"""

from typing import Dict, Any, Optional
from app.engine.statistics import (
    deviation_to_score,
    zscore_to_score,
    frequency_to_score,
    measurement_deviation,
)


def compute_risk_score(
    event: Dict[str, Any],
    rule_evidence: Dict[str, Any],
    weights: Optional[Dict[str, float]] = None,
    thresholds: Optional[Dict[str, float]] = None,
) -> tuple[float, Dict[str, Any]]:
    """
    Compute a mathematically explainable risk score from 0-100.

    Returns:
        (score: float, breakdown: dict)
    """
    w = weights or {}
    w1 = w.get("weight_deviation", 0.30)
    w2 = w.get("weight_verification", 0.25)
    w3 = w.get("weight_frequency", 0.15)
    w4 = w.get("weight_anomaly", 0.20)
    w5 = w.get("weight_hash_mismatch", 0.10)

    t = thresholds or {}
    dev_threshold = t.get("deviation_threshold", 0.30)
    z_threshold = t.get("zscore_threshold", 2.5)

    # Factor 1: Measurement deviation score
    expected = event.get("expected_measurement")
    observed = event.get("observed_measurement")
    if expected is not None and observed is not None:
        dev = measurement_deviation(observed, expected)
        dev_score = deviation_to_score(dev, dev_threshold)
    else:
        dev = 0.0
        dev_score = 0.0

    # Factor 2: Verification failure penalty
    verification = event.get("verification_result")
    if verification is False:
        verification_score = 100.0
    elif verification is True:
        verification_score = 0.0
    else:
        verification_score = 0.0  # Unknown/null → no penalty

    # Factor 3: Repeated event frequency
    freq = rule_evidence.get("frequency_score", 0.0)
    matching_events = rule_evidence.get("matching_events", 0)
    if matching_events > 0:
        freq_score = min(matching_events / 5.0 * 100.0, 100.0)
    else:
        freq_score = freq * 100.0

    # Factor 4: Statistical anomaly score (from z-score)
    z = rule_evidence.get("z_score")
    if z is not None:
        anomaly_score = zscore_to_score(z, z_threshold)
    else:
        # Fallback: use deviation magnitude if high
        anomaly_score = dev_score * 0.5

    # Factor 5: Hash mismatch penalty
    hash_mismatch = rule_evidence.get("hash_mismatch", False)
    forgery_indicator = rule_evidence.get("forgery_indicator", False)
    if hash_mismatch or forgery_indicator:
        hash_score = 100.0
    else:
        hash_score = 0.0

    # Weighted sum
    raw_score = (
        w1 * dev_score
        + w2 * verification_score
        + w3 * freq_score
        + w4 * anomaly_score
        + w5 * hash_score
    )

    # Clamp to 0-100
    final_score = max(0.0, min(100.0, raw_score))

    breakdown = {
        "risk_score": round(final_score, 2),
        "formula": f"({w1}×deviation + {w2}×verification + {w3}×frequency + {w4}×anomaly + {w5}×hash_mismatch)",
        "factors": {
            "measurement_deviation": {
                "raw_value": round(dev, 6),
                "score": round(dev_score, 2),
                "weight": w1,
                "weighted": round(w1 * dev_score, 2),
            },
            "verification_failure": {
                "failed": verification is False,
                "score": round(verification_score, 2),
                "weight": w2,
                "weighted": round(w2 * verification_score, 2),
            },
            "repeated_frequency": {
                "matching_events": matching_events,
                "score": round(freq_score, 2),
                "weight": w3,
                "weighted": round(w3 * freq_score, 2),
            },
            "anomaly_zscore": {
                "z_score": round(z, 4) if z is not None else None,
                "score": round(anomaly_score, 2),
                "weight": w4,
                "weighted": round(w4 * anomaly_score, 2),
            },
            "hash_mismatch": {
                "mismatch": hash_mismatch or forgery_indicator,
                "score": round(hash_score, 2),
                "weight": w5,
                "weighted": round(w5 * hash_score, 2),
            },
        },
    }

    return final_score, breakdown
