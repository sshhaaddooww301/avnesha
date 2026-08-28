"""
Statistical analysis module for QDS SIEM Detection Engine.

All calculations are mathematically rigorous — no fake values.
Functions operate on sequences of float measurements.
"""

import math
from typing import List, Optional, Tuple


EPSILON = 1e-10  # Guard against division by zero


def mean(values: List[float]) -> float:
    """Calculate arithmetic mean: Σx / n"""
    if not values:
        return 0.0
    return sum(values) / len(values)


def variance(values: List[float], population: bool = True) -> float:
    """
    Calculate variance: Σ(x - mean)² / n  (population)
    or Σ(x - mean)² / (n-1) (sample)
    """
    if len(values) < 2:
        return 0.0
    m = mean(values)
    divisor = len(values) if population else (len(values) - 1)
    return sum((x - m) ** 2 for x in values) / divisor


def std_deviation(values: List[float], population: bool = True) -> float:
    """Calculate standard deviation: √variance"""
    return math.sqrt(variance(values, population))


def z_score(value: float, m: float, std: float) -> float:
    """
    Calculate z-score: (x - mean) / std_deviation
    Returns 0.0 if std is near zero (insufficient variance).
    """
    if abs(std) < EPSILON:
        return 0.0
    return (value - m) / std


def measurement_deviation(observed: float, expected: float) -> float:
    """
    Calculate measurement deviation as a ratio:
    |observed - expected| / max(|expected|, epsilon)

    Returns a value where 0.0 = perfect match, 1.0 = 100% deviation.
    """
    denominator = max(abs(expected), EPSILON)
    return abs(observed - expected) / denominator


def measurement_deviation_pct(observed: float, expected: float) -> float:
    """Measurement deviation as a percentage (0-100)."""
    return measurement_deviation(observed, expected) * 100.0


def rolling_average(values: List[float], window: int) -> List[float]:
    """
    Calculate rolling average over a window.
    Returns a list of the same length as input (first entries use smaller windows).
    """
    if not values or window < 1:
        return []
    result = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        window_vals = values[start:i + 1]
        result.append(mean(window_vals))
    return result


def verification_failure_rate(results: List[bool]) -> float:
    """
    Calculate the rate of verification failures (False values).
    Returns 0.0 - 1.0
    """
    if not results:
        return 0.0
    failures = sum(1 for r in results if not r)
    return failures / len(results)


def repeated_event_frequency(timestamps: List[float], time_window: float) -> float:
    """
    Calculate the frequency of events within a time window (in seconds).
    Returns events-per-window ratio.

    timestamps: list of epoch timestamps
    time_window: window size in seconds
    """
    if len(timestamps) < 2 or time_window <= 0:
        return 0.0

    sorted_ts = sorted(timestamps)
    max_count = 0

    for i, t in enumerate(sorted_ts):
        count = sum(1 for t2 in sorted_ts[i:] if t2 - t <= time_window)
        max_count = max(max_count, count)

    # Normalize: 1 event = 0, window full of events = high score
    return max(0.0, (max_count - 1)) / max(1, len(timestamps))


def deviation_to_score(deviation: float, threshold: float = 0.30) -> float:
    """
    Convert measurement deviation to a 0-100 score.
    deviation=0 → 0, deviation=threshold → 50, deviation=2*threshold → 100
    """
    if deviation <= 0:
        return 0.0
    normalized = min(deviation / (2 * max(threshold, EPSILON)), 1.0)
    return normalized * 100.0


def zscore_to_score(z: float, threshold: float = 2.5) -> float:
    """
    Convert absolute z-score to a 0-100 anomaly score.
    |z|=0 → 0, |z|=threshold → 50, |z|=2*threshold → 100
    """
    abs_z = abs(z)
    if abs_z <= 0:
        return 0.0
    normalized = min(abs_z / (2 * max(threshold, EPSILON)), 1.0)
    return normalized * 100.0


def frequency_to_score(freq: float) -> float:
    """
    Convert repeated event frequency (0-1) to a 0-100 score.
    """
    return min(freq * 100.0, 100.0)


def compute_session_statistics(
    measurements: List[float],
) -> dict:
    """
    Compute full statistical profile for a sequence of measurements.
    Used for session-level anomaly indicators.
    """
    if not measurements:
        return {
            "count": 0,
            "mean": None,
            "variance": None,
            "std_deviation": None,
            "min": None,
            "max": None,
            "range": None,
        }

    m = mean(measurements)
    v = variance(measurements)
    std = std_deviation(measurements)

    return {
        "count": len(measurements),
        "mean": round(m, 6),
        "variance": round(v, 6),
        "std_deviation": round(std, 6),
        "min": round(min(measurements), 6),
        "max": round(max(measurements), 6),
        "range": round(max(measurements) - min(measurements), 6),
    }
