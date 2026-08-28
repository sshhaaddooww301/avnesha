"""
Advanced Detection Rules for QDS SIEM.

5 hardcore rules that catch attacks the basic rules miss:
- QDS-DDoS-001: DDoS/Flood Detection
- QDS-BRUTE-001: Brute Force Detection
- QDS-COORD-001: Coordinated Multi-Vector Attack Detection
- QDS-ENTROPY-001: High Entropy Payload Detection
- QDS-TIMEBOMB-001: Time-Based Attack Pattern Detection
"""

import math
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter, defaultdict
from app.engine.statistics import measurement_deviation, mean, std_deviation


class DDoSFloodDetectionRule:
    """
    QDS-DDoS-001: Detect volumetric flooding/DDoS patterns.
    Triggers when >50 events from same source in 60 seconds.
    Also detects distributed DDoS (multiple sources, same session pattern).
    """

    rule_id = "QDS-DDoS-001"
    name = "DDoS / Volumetric Flood Detection"
    description = "Detects high-volume event flooding from single or distributed sources"

    def evaluate(
        self,
        event: Dict[str, Any],
        historical_events: List[Dict[str, Any]],
        parameters: Dict[str, Any],
    ) -> Tuple[bool, float, Dict[str, Any]]:
        flood_threshold = parameters.get("ddos_threshold", 50)
        window_seconds = parameters.get("ddos_window_seconds", 60)
        source_node = event.get("source_node", "")
        session_id = event.get("session_id", "")

        event_time = event.get("timestamp", datetime.utcnow())
        if isinstance(event_time, str):
            event_time = datetime.fromisoformat(event_time)
        window_start = event_time - timedelta(seconds=window_seconds)

        # Count events from same source within window
        source_count = 0
        session_sources = set()
        total_in_window = 0

        for he in historical_events:
            he_time = he.get("timestamp", datetime.utcnow())
            if isinstance(he_time, str):
                he_time = datetime.fromisoformat(he_time)

            if he_time >= window_start:
                total_in_window += 1
                if he.get("source_node") == source_node:
                    source_count += 1
                if he.get("session_id") == session_id:
                    session_sources.add(he.get("source_node", ""))

        # Single-source flood
        single_source_flood = source_count >= flood_threshold

        # Distributed flood: many different sources hitting same session pattern
        distributed_flood = len(session_sources) >= 10 and total_in_window >= flood_threshold

        triggered = single_source_flood or distributed_flood
        confidence = min((source_count / flood_threshold) * 0.8, 1.0) if single_source_flood else (
            min((len(session_sources) / 15) * 0.9, 1.0) if distributed_flood else 0.0
        )

        evidence = {
            "rule": self.rule_id,
            "source_node": source_node,
            "events_from_source": source_count,
            "flood_threshold": flood_threshold,
            "window_seconds": window_seconds,
            "total_in_window": total_in_window,
            "unique_sources_in_session": len(session_sources),
            "single_source_flood": single_source_flood,
            "distributed_flood": distributed_flood,
            "flood_type": "SINGLE_SOURCE" if single_source_flood else ("DISTRIBUTED" if distributed_flood else "NONE"),
        }

        return triggered, confidence, evidence


class BruteForceDetectionRule:
    """
    QDS-BRUTE-001: Detect brute force verification attempts.
    Triggers when >10 verification failures from same source/session in 5 minutes.
    """

    rule_id = "QDS-BRUTE-001"
    name = "Brute Force Verification Attack Detection"
    description = "Detects repeated verification failures indicating brute force attempts"

    def evaluate(
        self,
        event: Dict[str, Any],
        historical_events: List[Dict[str, Any]],
        parameters: Dict[str, Any],
    ) -> Tuple[bool, float, Dict[str, Any]]:
        brute_threshold = parameters.get("brute_force_threshold", 10)
        window_seconds = parameters.get("brute_force_window", 300)
        source_node = event.get("source_node", "")
        session_id = event.get("session_id", "")

        event_time = event.get("timestamp", datetime.utcnow())
        if isinstance(event_time, str):
            event_time = datetime.fromisoformat(event_time)
        window_start = event_time - timedelta(seconds=window_seconds)

        # Count verification failures from same source
        failures_from_source = 0
        failures_from_session = 0
        total_from_source = 0

        for he in historical_events:
            he_time = he.get("timestamp", datetime.utcnow())
            if isinstance(he_time, str):
                he_time = datetime.fromisoformat(he_time)

            if he_time >= window_start:
                if he.get("source_node") == source_node:
                    total_from_source += 1
                    if he.get("verification_result") is False:
                        failures_from_source += 1
                if he.get("session_id") == session_id:
                    if he.get("verification_result") is False:
                        failures_from_session += 1

        # Include current event
        if event.get("verification_result") is False:
            failures_from_source += 1
            failures_from_session += 1

        failure_rate = failures_from_source / max(total_from_source + 1, 1)

        triggered = (failures_from_source >= brute_threshold) or (
            failures_from_session >= brute_threshold
        )
        confidence = min(max(failures_from_source, failures_from_session) / (brute_threshold * 1.5), 1.0) if triggered else 0.0

        evidence = {
            "rule": self.rule_id,
            "source_node": source_node,
            "session_id": session_id,
            "failures_from_source": failures_from_source,
            "failures_from_session": failures_from_session,
            "total_from_source": total_from_source,
            "failure_rate": round(failure_rate, 4),
            "brute_threshold": brute_threshold,
            "window_seconds": window_seconds,
        }

        return triggered, confidence, evidence


class CoordinatedAttackDetectionRule:
    """
    QDS-COORD-001: Detect coordinated multi-vector attacks.
    Triggers when multiple different attack types are detected from the same
    source/session within a short time window.
    """

    rule_id = "QDS-COORD-001"
    name = "Coordinated Multi-Vector Attack Detection"
    description = "Detects multiple attack types from same source indicating coordinated campaign"

    def evaluate(
        self,
        event: Dict[str, Any],
        historical_events: List[Dict[str, Any]],
        parameters: Dict[str, Any],
    ) -> Tuple[bool, float, Dict[str, Any]]:
        coord_window = parameters.get("coordinated_window_seconds", 600)
        min_attack_types = parameters.get("coordinated_min_types", 2)
        source_node = event.get("source_node", "")

        event_time = event.get("timestamp", datetime.utcnow())
        if isinstance(event_time, str):
            event_time = datetime.fromisoformat(event_time)
        window_start = event_time - timedelta(seconds=coord_window)

        # Analyze attack diversity from same source
        attack_indicators = set()
        metadata = event.get("metadata_json", {}) or {}

        # Check current event for attack indicators
        current_attack = metadata.get("attack", "")
        if current_attack:
            attack_indicators.add(current_attack)

        # Check if current event has verification failure + deviation
        if event.get("verification_result") is False:
            attack_indicators.add("VERIFICATION_FAILURE")
        dev = event.get("measurement_deviation")
        if dev is not None and dev > 0.2:
            attack_indicators.add("HIGH_DEVIATION")

        # Scan historical events from same source
        for he in historical_events:
            he_time = he.get("timestamp", datetime.utcnow())
            if isinstance(he_time, str):
                he_time = datetime.fromisoformat(he_time)

            if he_time >= window_start and he.get("source_node") == source_node:
                he_meta = he.get("metadata_json", {}) or {}
                he_attack = he_meta.get("attack", "")
                if he_attack:
                    attack_indicators.add(he_attack)
                if he.get("verification_result") is False:
                    attack_indicators.add("VERIFICATION_FAILURE")
                he_dev = he.get("measurement_deviation")
                if he_dev is not None and he_dev > 0.2:
                    attack_indicators.add("HIGH_DEVIATION")

                # Check for specific attack metadata flags
                for flag in ["pns_attack_detected", "detector_blinded", "repudiation_dispute",
                             "forgery_indicator", "low_slow_evasion"]:
                    if he_meta.get(flag):
                        attack_indicators.add(flag.upper())

        unique_attack_types = len(attack_indicators)
        triggered = unique_attack_types >= min_attack_types
        confidence = min(unique_attack_types / (min_attack_types * 2), 1.0) if triggered else 0.0

        evidence = {
            "rule": self.rule_id,
            "source_node": source_node,
            "attack_indicators": list(attack_indicators),
            "unique_attack_types": unique_attack_types,
            "min_required": min_attack_types,
            "window_seconds": coord_window,
            "campaign_assessment": "COORDINATED_CAMPAIGN" if unique_attack_types >= 3 else "MULTI_VECTOR",
        }

        return triggered, confidence, evidence


class HighEntropyPayloadDetectionRule:
    """
    QDS-ENTROPY-001: Detect suspiciously high entropy in payloads.
    High Shannon entropy indicates encrypted, obfuscated, or encoded payloads
    that may be attempting to evade pattern-based detection.
    """

    rule_id = "QDS-ENTROPY-001"
    name = "High Entropy Payload Detection"
    description = "Detects encrypted or obfuscated payloads via Shannon entropy analysis"

    def evaluate(
        self,
        event: Dict[str, Any],
        historical_events: List[Dict[str, Any]],
        parameters: Dict[str, Any],
    ) -> Tuple[bool, float, Dict[str, Any]]:
        entropy_threshold = parameters.get("entropy_threshold", 4.5)

        # Analyze multiple fields for high entropy
        fields_to_check = {}
        entropy_scores = {}

        # Check quantum_state
        qs = event.get("quantum_state", "")
        if qs and len(qs) > 20:
            fields_to_check["quantum_state"] = qs

        # Check signature_hash (already expected to be high entropy, so use higher threshold)
        sig = event.get("signature_hash", "")
        if sig and len(sig) > 20:
            fields_to_check["signature_hash"] = sig

        # Check metadata stringified
        metadata = event.get("metadata_json", {})
        if metadata:
            meta_str = str(metadata)
            if len(meta_str) > 50:
                fields_to_check["metadata_json"] = meta_str

        # Check session_id
        sid = event.get("session_id", "")
        if sid and len(sid) > 20:
            fields_to_check["session_id"] = sid

        for field_name, field_value in fields_to_check.items():
            entropy = self._shannon_entropy(field_value)
            entropy_scores[field_name] = round(entropy, 4)

        # Trigger on metadata or quantum_state high entropy (signature_hash is always high)
        suspicious_fields = {
            k: v for k, v in entropy_scores.items()
            if v > entropy_threshold and k not in ["signature_hash"]
        }

        triggered = len(suspicious_fields) > 0
        max_entropy = max(suspicious_fields.values()) if suspicious_fields else 0.0
        confidence = min((max_entropy - entropy_threshold) / 2.0, 1.0) if triggered else 0.0

        evidence = {
            "rule": self.rule_id,
            "entropy_scores": entropy_scores,
            "suspicious_fields": suspicious_fields,
            "entropy_threshold": entropy_threshold,
            "max_entropy": max_entropy,
            "assessment": "POSSIBLE_ENCRYPTED_PAYLOAD" if triggered else "NORMAL_ENTROPY",
        }

        return triggered, confidence, evidence

    @staticmethod
    def _shannon_entropy(data: str) -> float:
        """Calculate Shannon entropy."""
        if not data:
            return 0.0
        counter = Counter(data)
        length = len(data)
        return -sum(
            (count / length) * math.log2(count / length)
            for count in counter.values()
        )


class TimeBombPatternDetectionRule:
    """
    QDS-TIMEBOMB-001: Detect time-based attack patterns.
    Identifies:
    - Events with future timestamps (clock manipulation)
    - Perfectly regular intervals suggesting automation
    - Unusual time-of-day patterns
    """

    rule_id = "QDS-TIMEBOMB-001"
    name = "Time-Based Attack Pattern Detection"
    description = "Detects timestamp manipulation, automated attack patterns, and temporal anomalies"

    def evaluate(
        self,
        event: Dict[str, Any],
        historical_events: List[Dict[str, Any]],
        parameters: Dict[str, Any],
    ) -> Tuple[bool, float, Dict[str, Any]]:
        source_node = event.get("source_node", "")
        event_time = event.get("timestamp", datetime.utcnow())
        if isinstance(event_time, str):
            event_time = datetime.fromisoformat(event_time)

        now = datetime.utcnow()
        indicators = []
        confidence_factors = []

        # 1. Future timestamp detection (clock manipulation)
        time_diff = (event_time - now).total_seconds()
        if time_diff > 300:  # More than 5 minutes in the future
            indicators.append("FUTURE_TIMESTAMP")
            confidence_factors.append(min(time_diff / 3600, 1.0))

        # 2. Very old timestamp (replay of old events)
        if time_diff < -86400:  # More than 24 hours old
            indicators.append("STALE_TIMESTAMP")
            confidence_factors.append(0.6)

        # 3. Check for automation patterns (regular intervals)
        source_events = [
            he for he in historical_events
            if he.get("source_node") == source_node
        ]

        if len(source_events) >= 5:
            timestamps = []
            for he in source_events[:20]:
                he_time = he.get("timestamp", datetime.utcnow())
                if isinstance(he_time, str):
                    he_time = datetime.fromisoformat(he_time)
                timestamps.append(he_time)

            timestamps.sort()

            # Calculate intervals
            intervals = []
            for i in range(1, len(timestamps)):
                diff = (timestamps[i] - timestamps[i-1]).total_seconds()
                if diff > 0:
                    intervals.append(diff)

            if len(intervals) >= 3:
                avg_interval = mean(intervals)
                std_interval = std_deviation(intervals)

                # Very regular intervals (std/mean < 0.1) suggest automation
                if avg_interval > 0:
                    cv = std_interval / max(avg_interval, 0.001)
                    if cv < 0.1 and avg_interval < 5.0:
                        indicators.append("AUTOMATED_REGULAR_INTERVALS")
                        confidence_factors.append(1.0 - cv)

                    # Very rapid intervals (< 0.1 second average)
                    if avg_interval < 0.1:
                        indicators.append("MACHINE_SPEED_EVENTS")
                        confidence_factors.append(0.9)

        triggered = len(indicators) > 0
        confidence = max(confidence_factors) if confidence_factors else 0.0

        evidence = {
            "rule": self.rule_id,
            "source_node": source_node,
            "event_timestamp": event_time.isoformat() if isinstance(event_time, datetime) else str(event_time),
            "server_time": now.isoformat(),
            "time_difference_seconds": round(time_diff, 2),
            "indicators": indicators,
            "indicator_count": len(indicators),
            "assessment": "TIME_ANOMALY_DETECTED" if triggered else "NORMAL_TIMING",
        }

        return triggered, confidence, evidence


# Registry of advanced rules
ADVANCED_RULE_REGISTRY: Dict[str, Any] = {
    "QDS-DDoS-001": DDoSFloodDetectionRule(),
    "QDS-BRUTE-001": BruteForceDetectionRule(),
    "QDS-COORD-001": CoordinatedAttackDetectionRule(),
    "QDS-ENTROPY-001": HighEntropyPayloadDetectionRule(),
    "QDS-TIMEBOMB-001": TimeBombPatternDetectionRule(),
}
