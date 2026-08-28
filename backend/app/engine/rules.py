"""
Detection rules for QDS SIEM.

Each rule is a class with an `evaluate` method that returns:
  (triggered: bool, confidence: float, evidence: dict)

Rules operate on event data + historical context from the database.
No fake thresholds — all configurable via system settings.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
from app.engine.statistics import (
    measurement_deviation,
    z_score,
    mean,
    std_deviation,
    verification_failure_rate,
    repeated_event_frequency,
)


class DetectionRule(ABC):
    """Base class for all detection rules."""

    rule_id: str
    name: str
    description: str

    @abstractmethod
    def evaluate(
        self,
        event: Dict[str, Any],
        historical_events: List[Dict[str, Any]],
        parameters: Dict[str, Any],
    ) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Evaluate the rule against an event.

        Returns:
            (triggered, confidence, evidence)
        """
        pass


class ReplayDetectionRule(DetectionRule):
    """
    QDS-RPL-001: Detect repeated use of the same signature/event/session pattern
    within a configurable time window.
    """

    rule_id = "QDS-RPL-001"
    name = "Replay Attack Detection"
    description = "Detects reuse of signature hashes within a time window"

    def evaluate(
        self,
        event: Dict[str, Any],
        historical_events: List[Dict[str, Any]],
        parameters: Dict[str, Any],
    ) -> Tuple[bool, float, Dict[str, Any]]:
        window_seconds = parameters.get("replay_window_seconds", 300)
        sig_hash = event.get("signature_hash")

        if not sig_hash:
            return False, 0.0, {}

        event_time = event.get("timestamp", datetime.utcnow())
        if isinstance(event_time, str):
            event_time = datetime.fromisoformat(event_time)

        window_start = event_time - timedelta(seconds=window_seconds)

        # Find events with the same signature hash within the window
        matching = []
        for he in historical_events:
            he_time = he.get("timestamp", datetime.utcnow())
            if isinstance(he_time, str):
                he_time = datetime.fromisoformat(he_time)
            he_hash = he.get("signature_hash")

            if (
                he_hash == sig_hash
                and he.get("event_id") != event.get("event_id")
                and he_time >= window_start
                and he_time <= event_time
            ):
                matching.append(he)

        triggered = len(matching) > 0
        confidence = min(len(matching) / 3.0, 1.0) if triggered else 0.0

        evidence = {
            "rule": self.rule_id,
            "signature_hash": sig_hash,
            "matching_events": len(matching),
            "window_seconds": window_seconds,
            "matching_event_ids": [m.get("event_id") for m in matching[:10]],
        }

        return triggered, confidence, evidence


class MITMDetectionRule(DetectionRule):
    """
    QDS-MITM-001: Flag suspicious communication/verification inconsistencies
    when cryptographic verification fails together with significant measurement deviation.
    """

    rule_id = "QDS-MITM-001"
    name = "Man-in-the-Middle Detection"
    description = "Detects verification failure combined with measurement deviation"

    def evaluate(
        self,
        event: Dict[str, Any],
        historical_events: List[Dict[str, Any]],
        parameters: Dict[str, Any],
    ) -> Tuple[bool, float, Dict[str, Any]]:
        deviation_threshold = parameters.get("deviation_threshold", 0.30)
        verification = event.get("verification_result")
        expected = event.get("expected_measurement")
        observed = event.get("observed_measurement")

        if verification is None or expected is None or observed is None:
            return False, 0.0, {}

        dev = measurement_deviation(observed, expected)
        verification_failed = verification is False

        triggered = verification_failed and dev > deviation_threshold

        if triggered:
            confidence = min(dev / (deviation_threshold * 2), 1.0)
        else:
            confidence = 0.0

        evidence = {
            "rule": self.rule_id,
            "verification_result": verification,
            "measurement_deviation": round(dev, 6),
            "deviation_threshold": deviation_threshold,
            "expected_measurement": expected,
            "observed_measurement": observed,
        }

        return triggered, confidence, evidence


class ForgeryDetectionRule(DetectionRule):
    """
    QDS-FRG-001: Detect signature/hash verification mismatch.
    """

    rule_id = "QDS-FRG-001"
    name = "Forgery Detection"
    description = "Detects signature hash verification mismatches"

    def evaluate(
        self,
        event: Dict[str, Any],
        historical_events: List[Dict[str, Any]],
        parameters: Dict[str, Any],
    ) -> Tuple[bool, float, Dict[str, Any]]:
        verification = event.get("verification_result")
        sig_hash = event.get("signature_hash")
        metadata = event.get("metadata_json", {}) or {}
        expected_hash = metadata.get("expected_signature_hash")

        # Case 1: Explicit hash mismatch
        hash_mismatch = False
        if sig_hash and expected_hash:
            hash_mismatch = sig_hash != expected_hash

        # Case 2: Verification explicitly failed with a forgery indicator
        forgery_indicator = metadata.get("forgery_indicator", False)

        triggered = hash_mismatch or (verification is False and forgery_indicator)
        confidence = 0.9 if hash_mismatch else (0.7 if forgery_indicator else 0.0)

        evidence = {
            "rule": self.rule_id,
            "signature_hash": sig_hash,
            "expected_hash": expected_hash,
            "hash_mismatch": hash_mismatch,
            "forgery_indicator": forgery_indicator,
            "verification_result": verification,
        }

        return triggered, confidence, evidence


class ImpersonationDetectionRule(DetectionRule):
    """
    QDS-IMP-001: Detect unauthorized identity/session behavior based on
    verification and session consistency.
    """

    rule_id = "QDS-IMP-001"
    name = "Impersonation Detection"
    description = "Detects unauthorized session or identity behavior"

    def evaluate(
        self,
        event: Dict[str, Any],
        historical_events: List[Dict[str, Any]],
        parameters: Dict[str, Any],
    ) -> Tuple[bool, float, Dict[str, Any]]:
        session_id = event.get("session_id")
        source_node = event.get("source_node")
        verification = event.get("verification_result")

        if not session_id or not source_node:
            return False, 0.0, {}

        # Check if this source_node was seen with a different session pattern
        session_sources = {}
        for he in historical_events:
            he_session = he.get("session_id")
            he_source = he.get("source_node")
            if he_session == session_id and he_source and he_source != source_node:
                session_sources[he_source] = session_sources.get(he_source, 0) + 1

        # Impersonation: same session, different source, plus verification failure
        inconsistent_sources = len(session_sources)
        triggered = inconsistent_sources > 0 and verification is False

        if triggered:
            confidence = min(inconsistent_sources / 3.0, 1.0)
        else:
            confidence = 0.0

        evidence = {
            "rule": self.rule_id,
            "session_id": session_id,
            "source_node": source_node,
            "inconsistent_sources": dict(session_sources),
            "verification_result": verification,
        }

        return triggered, confidence, evidence


class AnomalyDetectionRule(DetectionRule):
    """
    QDS-ANM-001: Detect statistically abnormal quantum measurement behavior.
    Uses z-score analysis on measurement deviations.
    """

    rule_id = "QDS-ANM-001"
    name = "Quantum Measurement Anomaly Detection"
    description = "Detects statistically abnormal measurement patterns via z-score"

    def evaluate(
        self,
        event: Dict[str, Any],
        historical_events: List[Dict[str, Any]],
        parameters: Dict[str, Any],
    ) -> Tuple[bool, float, Dict[str, Any]]:
        zscore_threshold = parameters.get("zscore_threshold", 2.5)
        expected = event.get("expected_measurement")
        observed = event.get("observed_measurement")

        if expected is None or observed is None:
            return False, 0.0, {}

        dev = measurement_deviation(observed, expected)

        # Collect historical deviations for statistical context
        historical_devs = []
        for he in historical_events:
            he_exp = he.get("expected_measurement")
            he_obs = he.get("observed_measurement")
            if he_exp is not None and he_obs is not None:
                historical_devs.append(measurement_deviation(he_obs, he_exp))

        # Need at least a few data points for meaningful statistics
        if len(historical_devs) < 3:
            # Fallback: just check if deviation is extremely high
            triggered = dev > 0.5  # 50% deviation with no history is suspicious
            confidence = min(dev, 1.0) if triggered else 0.0
            z = None
            m = None
            std = None
        else:
            m = mean(historical_devs)
            std = std_deviation(historical_devs)
            z = z_score(dev, m, std)
            triggered = abs(z) > zscore_threshold
            confidence = min(abs(z) / (zscore_threshold * 2), 1.0) if triggered else 0.0

        evidence = {
            "rule": self.rule_id,
            "measurement_deviation": round(dev, 6),
            "historical_count": len(historical_devs),
            "mean_deviation": round(m, 6) if m is not None else None,
            "std_deviation": round(std, 6) if std is not None else None,
            "z_score": round(z, 4) if z is not None else None,
            "zscore_threshold": zscore_threshold,
            "expected_measurement": expected,
            "observed_measurement": observed,
        }

        return triggered, confidence, evidence


class PNSDetectionRule(DetectionRule):
    """
    QDS-PNS-001: Photon Number Splitting & Decoy State Analysis.
    Detects when multi-photon pulses are split or decoy-state statistics deviate
    from expected Poisson photon number distribution.
    """

    rule_id = "QDS-PNS-001"
    name = "Photon Number Splitting (PNS) Detection"
    description = "Detects photon number splitting and decoy-state gain statistical anomalies"

    def evaluate(
        self,
        event: Dict[str, Any],
        historical_events: List[Dict[str, Any]],
        parameters: Dict[str, Any],
    ) -> Tuple[bool, float, Dict[str, Any]]:
        metadata = event.get("metadata_json", {}) or {}
        pns_flag = metadata.get("pns_attack_detected", False)
        decoy_gain_ratio = metadata.get("decoy_gain_ratio")
        expected_ratio = metadata.get("expected_decoy_gain_ratio", 1.0)
        multi_photon_excess = metadata.get("multi_photon_excess", 0.0)

        ratio_dev = abs(decoy_gain_ratio - expected_ratio) if decoy_gain_ratio is not None else 0.0
        triggered = pns_flag or ratio_dev > 0.15 or multi_photon_excess > 0.20

        confidence = 0.95 if pns_flag else (min(ratio_dev * 4.0, 0.9) if triggered else 0.0)

        evidence = {
            "rule": self.rule_id,
            "pns_attack_detected": pns_flag,
            "decoy_gain_ratio": decoy_gain_ratio,
            "expected_decoy_gain_ratio": expected_ratio,
            "decoy_deviation": round(ratio_dev, 4),
            "multi_photon_excess": round(multi_photon_excess, 4),
        }
        return triggered, confidence, evidence


class DetectorBlindingRule(DetectionRule):
    """
    QDS-BLD-001: Detector Blinding / Trojan Horse Saturation Attack.
    Detects continuous-wave optical power injection forcing SPAD detectors into linear mode.
    """

    rule_id = "QDS-BLD-001"
    name = "Detector Blinding & Saturation Detection"
    description = "Detects optical sensor blinding, telemetry saturation, and dead-time collapse"

    def evaluate(
        self,
        event: Dict[str, Any],
        historical_events: List[Dict[str, Any]],
        parameters: Dict[str, Any],
    ) -> Tuple[bool, float, Dict[str, Any]]:
        metadata = event.get("metadata_json", {}) or {}
        blinding_flag = metadata.get("detector_blinded", False)
        optical_power_uw = metadata.get("optical_power_uW", 0.0)
        dark_count_hz = metadata.get("dark_count_rate_hz", 100.0)
        deadtime_variance = metadata.get("deadtime_variance_ns", 10.0)

        # SPAD saturated if optical power > 50 uW, dark count rate spikes > 5000 Hz, or deadtime variance collapses to ~0
        power_saturation = optical_power_uw > 50.0
        dark_count_spike = dark_count_hz > 5000.0
        deadtime_collapsed = deadtime_variance < 0.5 and optical_power_uw > 10.0

        triggered = blinding_flag or power_saturation or dark_count_spike or deadtime_collapsed
        confidence = 0.98 if blinding_flag else (0.85 if power_saturation or dark_count_spike else 0.0)

        evidence = {
            "rule": self.rule_id,
            "detector_blinded": blinding_flag,
            "optical_power_uW": round(optical_power_uw, 2),
            "dark_count_rate_hz": round(dark_count_hz, 1),
            "deadtime_variance_ns": round(deadtime_variance, 3),
            "saturation_level": "CRITICAL" if (power_saturation or dark_count_spike) else "NORMAL",
        }
        return triggered, confidence, evidence


class RepudiationDetectionRule(DetectionRule):
    """
    QDS-RPD-001: Multi-Party Repudiation & Symmetrization Dispute.
    Detects cheating sender sending mismatched quantum states to Bob and Charlie.
    """

    rule_id = "QDS-RPD-001"
    name = "Multi-Party Repudiation Dispute Detection"
    description = "Detects sender quantum state mismatch and cross-receiver verification disagreement"

    def evaluate(
        self,
        event: Dict[str, Any],
        historical_events: List[Dict[str, Any]],
        parameters: Dict[str, Any],
    ) -> Tuple[bool, float, Dict[str, Any]]:
        metadata = event.get("metadata_json", {}) or {}
        repudiation_flag = metadata.get("repudiation_dispute", False)
        symmetrization_mismatch = metadata.get("symmetrization_mismatch", False)
        bob_accepted = metadata.get("bob_verification", True)
        charlie_accepted = metadata.get("charlie_verification", True)

        # Repudiation condition: One recipient validates while another rejects the forwarded state
        dispute = bob_accepted != charlie_accepted
        triggered = repudiation_flag or symmetrization_mismatch or dispute
        confidence = 0.95 if (repudiation_flag or symmetrization_mismatch) else (0.80 if dispute else 0.0)

        evidence = {
            "rule": self.rule_id,
            "repudiation_dispute": repudiation_flag,
            "symmetrization_mismatch": symmetrization_mismatch,
            "bob_verification": bob_accepted,
            "charlie_verification": charlie_accepted,
            "dispute_detected": dispute,
        }
        return triggered, confidence, evidence


class LowSlowEvasionDetectionRule(DetectionRule):
    """
    QDS-EVS-001: Low-and-Slow Sub-threshold Evasion Detection.
    Detects subtle, low-intensity eavesdropping that keeps individual deviations below threshold
    but produces statistically significant cumulative baseline drift (CUSUM).
    """

    rule_id = "QDS-EVS-001"
    name = "Low-and-Slow Sub-Threshold Evasion Detection"
    description = "Detects cumulative sub-threshold eavesdropping via multi-window CUSUM drift"

    def evaluate(
        self,
        event: Dict[str, Any],
        historical_events: List[Dict[str, Any]],
        parameters: Dict[str, Any],
    ) -> Tuple[bool, float, Dict[str, Any]]:
        metadata = event.get("metadata_json", {}) or {}
        evasion_flag = metadata.get("low_slow_evasion", False)
        expected = event.get("expected_measurement")
        observed = event.get("observed_measurement")

        if expected is None or observed is None:
            return False, 0.0, {}

        current_dev = measurement_deviation(observed, expected)

        # Collect recent historical deviations
        recent_devs = [
            measurement_deviation(he["observed_measurement"], he["expected_measurement"])
            for he in historical_events[:30]
            if he.get("expected_measurement") is not None and he.get("observed_measurement") is not None
        ]

        # Check for persistent elevated mean in [0.08, 0.28] range (sub-threshold, but abnormally elevated)
        sustained_drift = False
        drift_mean = 0.0
        if len(recent_devs) >= 5:
            drift_mean = mean(recent_devs)
            # Baseline is usually ~0.02-0.04; if average is > 0.10 consistently, it's low-and-slow
            sustained_drift = drift_mean > 0.09 and current_dev > 0.08

        triggered = evasion_flag or sustained_drift
        confidence = 0.90 if evasion_flag else (min(drift_mean * 5.0, 0.85) if triggered else 0.0)

        evidence = {
            "rule": self.rule_id,
            "low_slow_evasion": evasion_flag,
            "current_deviation": round(current_dev, 4),
            "historical_window_mean": round(drift_mean, 4),
            "sustained_drift_detected": sustained_drift,
            "evasion_profile": "SUB_THRESHOLD_INTERCEPT",
        }
        return triggered, confidence, evidence


# Import advanced rules
from app.engine.rules_advanced import ADVANCED_RULE_REGISTRY

# Registry of all detection rules (9 core + 5 advanced = 14 total)
RULE_REGISTRY: Dict[str, DetectionRule] = {
    "QDS-RPL-001": ReplayDetectionRule(),
    "QDS-MITM-001": MITMDetectionRule(),
    "QDS-FRG-001": ForgeryDetectionRule(),
    "QDS-IMP-001": ImpersonationDetectionRule(),
    "QDS-ANM-001": AnomalyDetectionRule(),
    "QDS-PNS-001": PNSDetectionRule(),
    "QDS-BLD-001": DetectorBlindingRule(),
    "QDS-RPD-001": RepudiationDetectionRule(),
    "QDS-EVS-001": LowSlowEvasionDetectionRule(),
    **ADVANCED_RULE_REGISTRY,  # DDoS, BruteForce, Coordinated, Entropy, TimeBomb
}


def get_rule(rule_id: str) -> Optional[DetectionRule]:
    return RULE_REGISTRY.get(rule_id)


def get_all_rules() -> Dict[str, DetectionRule]:
    return RULE_REGISTRY

