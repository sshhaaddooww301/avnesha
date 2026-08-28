"""
Main Detection Pipeline for QDS SIEM.

Flow:
1. Receive event
2. Calculate measurement deviation
3. Query historical events for statistical context
4. Run all enabled detection rules
5. If any rule triggers → compute risk score → derive severity → create threat
6. Write event + threat to database
7. Add to audit ledger
8. Broadcast via WebSocket
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models import SecurityEvent, Threat, DetectionRule as DetectionRuleModel, SystemSetting
from app.engine.rules import RULE_REGISTRY
from app.engine.risk_scorer import compute_risk_score
from app.engine.severity import classify_severity
from app.engine.statistics import measurement_deviation, compute_session_statistics
from app.blockchain.ledger import audit_ledger
from app.websocket.manager import ws_manager
from app.engine.soar import quantum_ips
from app.engine.prevention import prevention_engine
from app.security.ip_firewall import ip_firewall

logger = logging.getLogger("qds.detection")


async def get_system_parameters(db: AsyncSession) -> Dict[str, Any]:
    """Load detection parameters from system_settings table."""
    params = {}
    result = await db.execute(select(SystemSetting))
    settings = result.scalars().all()
    for s in settings:
        val = s.value
        if isinstance(val, dict) and "value" in val:
            params[s.key] = val["value"]
        else:
            params[s.key] = val
    return params


async def get_enabled_rules(db: AsyncSession) -> List[str]:
    """Get list of enabled rule IDs from database."""
    result = await db.execute(
        select(DetectionRuleModel.rule_id).where(DetectionRuleModel.enabled == True)
    )
    return [r[0] for r in result.all()]


async def get_historical_events(
    db: AsyncSession,
    session_id: str,
    source_node: str,
    signature_hash: Optional[str] = None,
    window_seconds: int = 3600,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    """Fetch recent historical events for statistical and rule context."""
    cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
    result = await db.execute(
        select(SecurityEvent)
        .where(SecurityEvent.timestamp >= cutoff)
        .order_by(SecurityEvent.timestamp.desc())
        .limit(limit)
    )
    events = result.scalars().all()
    return [
        {
            "event_id": e.event_id,
            "timestamp": e.timestamp,
            "session_id": e.session_id,
            "source_node": e.source_node,
            "event_type": e.event_type,
            "expected_measurement": e.expected_measurement,
            "observed_measurement": e.observed_measurement,
            "measurement_deviation": e.measurement_deviation,
            "verification_result": e.verification_result,
            "signature_hash": e.signature_hash,
            "metadata_json": e.metadata_json,
        }
        for e in events
    ]



async def process_event(
    db: AsyncSession,
    event_data: Dict[str, Any],
) -> Tuple[SecurityEvent, Optional[Threat]]:
    """
    Main detection pipeline entry point.

    Takes raw event data, runs through full detection pipeline,
    stores in database, creates audit trail, broadcasts updates.
    """
    # Step 1: Calculate measurement deviation
    expected = event_data.get("expected_measurement")
    observed = event_data.get("observed_measurement")
    if expected is not None and observed is not None:
        dev = measurement_deviation(observed, expected)
    else:
        dev = None

    # Step 2: Create and store security event
    meta = dict(event_data.get("metadata_json") or {})
    source_ip = event_data.get("source_ip") or meta.get("source_ip") or "10.0.1.10"
    meta["source_ip"] = source_ip

    event = SecurityEvent(
        event_id=event_data.get("event_id", str(uuid.uuid4())),
        timestamp=event_data.get("timestamp", datetime.utcnow()),
        session_id=event_data["session_id"],
        source_node=event_data["source_node"],
        event_type=event_data["event_type"],
        quantum_state=event_data.get("quantum_state"),
        expected_measurement=expected,
        observed_measurement=observed,
        measurement_deviation=dev,
        verification_result=event_data.get("verification_result"),
        signature_hash=event_data.get("signature_hash"),
        metadata_json=meta,
        created_at=datetime.utcnow(),
    )

    db.add(event)
    await db.flush()

    # Step 3: Add to audit ledger
    try:
        await audit_ledger.add_block(
            db=db,
            event_id=event.event_id,
            payload={
                "event_type": event.event_type,
                "session_id": event.session_id,
                "source_node": event.source_node,
                "measurement_deviation": dev,
                "verification_result": event.verification_result,
                "signature_hash": event.signature_hash,
                "timestamp": event.timestamp.isoformat(),
            },
        )
    except Exception as e:
        logger.error(f"Audit ledger error: {e}")

    # Step 4: Load system parameters and enabled rules
    sys_params = await get_system_parameters(db)
    enabled_rules = await get_enabled_rules(db)

    parameters = {
        "replay_window_seconds": sys_params.get("replay_window_seconds", {}).get("value", 300) if isinstance(sys_params.get("replay_window_seconds"), dict) else sys_params.get("replay_window_seconds", 300),
        "deviation_threshold": sys_params.get("deviation_threshold", {}).get("value", 0.30) if isinstance(sys_params.get("deviation_threshold"), dict) else sys_params.get("deviation_threshold", 0.30),
        "zscore_threshold": sys_params.get("zscore_threshold", {}).get("value", 2.5) if isinstance(sys_params.get("zscore_threshold"), dict) else sys_params.get("zscore_threshold", 2.5),
    }

    # Step 5: Fetch historical events
    historical = await get_historical_events(
        db,
        event.session_id,
        event.source_node,
        window_seconds=max(parameters.get("replay_window_seconds", 300), 3600),
    )

    # Step 6: Run all enabled detection rules
    event_dict = {
        "event_id": event.event_id,
        "timestamp": event.timestamp,
        "session_id": event.session_id,
        "source_node": event.source_node,
        "event_type": event.event_type,
        "expected_measurement": event.expected_measurement,
        "observed_measurement": event.observed_measurement,
        "measurement_deviation": event.measurement_deviation,
        "verification_result": event.verification_result,
        "signature_hash": event.signature_hash,
        "metadata_json": event.metadata_json,
    }

    triggered_rules = []
    all_evidence = {}

    for rule_id, rule in RULE_REGISTRY.items():
        if rule_id not in enabled_rules:
            continue
        try:
            triggered, confidence, evidence = rule.evaluate(
                event_dict, historical, parameters
            )
            if triggered:
                triggered_rules.append((rule_id, confidence, evidence))
                all_evidence.update(evidence)
        except Exception as e:
            logger.error(f"Rule {rule_id} error: {e}")

    # Step 7: If any rule triggered, create threat
    threat = None
    if triggered_rules:
        # Pick highest-confidence rule as primary
        triggered_rules.sort(key=lambda x: x[1], reverse=True)
        primary_rule_id, primary_confidence, primary_evidence = triggered_rules[0]

        # Map rule to threat type (all 14 rules)
        rule_threat_map = {
            "QDS-RPL-001": "Replay Attack",
            "QDS-MITM-001": "MITM Attack",
            "QDS-FRG-001": "Forgery",
            "QDS-IMP-001": "Impersonation",
            "QDS-ANM-001": "Quantum Measurement Anomaly",
            "QDS-PNS-001": "Photon Number Splitting (PNS)",
            "QDS-BLD-001": "Detector Blinding Attack",
            "QDS-RPD-001": "Multi-Party Repudiation Dispute",
            "QDS-EVS-001": "Low-and-Slow Evasion Attack",
            "QDS-DDoS-001": "DDoS Volumetric Inundation",
            "QDS-BRUTE-001": "Brute Force Verification Attempt",
            "QDS-COORD-001": "Coordinated Multi-Vector Campaign",
            "QDS-ENTROPY-001": "High Entropy / Obfuscated Payload",
            "QDS-TIMEBOMB-001": "Temporal Clock Manipulation / Time-Bomb",
        }

        # Apply Adaptive Thresholds under attack conditions
        adaptive_dev, adaptive_z = prevention_engine.get_adaptive_thresholds(
            default_deviation=parameters["deviation_threshold"],
            default_zscore=parameters["zscore_threshold"],
        )

        # Load weights
        weights = {
            "weight_deviation": sys_params.get("weight_deviation", 0.30),
            "weight_verification": sys_params.get("weight_verification", 0.25),
            "weight_frequency": sys_params.get("weight_frequency", 0.15),
            "weight_anomaly": sys_params.get("weight_anomaly", 0.20),
            "weight_hash_mismatch": sys_params.get("weight_hash_mismatch", 0.10),
        }

        thresholds = {
            "deviation_threshold": parameters["deviation_threshold"],
            "zscore_threshold": parameters["zscore_threshold"],
        }

        # Compute risk score
        risk_score, risk_breakdown = compute_risk_score(
            event_dict, all_evidence, weights, thresholds
        )

        # Ensure minimum score for triggered rules
        if risk_score < 15.0:
            risk_score = max(15.0 + primary_confidence * 30, risk_score)
            risk_score = min(risk_score, 100.0)

        # Load severity thresholds
        severity_thresholds = {
            "low_max": sys_params.get("severity_low_max", 24),
            "medium_max": sys_params.get("severity_medium_max", 49),
            "high_max": sys_params.get("severity_high_max", 74),
        }
        severity = classify_severity(risk_score, severity_thresholds)

        # Execute Active Quantum IPS & SOAR Countermeasures
        mitigation_record = quantum_ips.execute_countermeasures(
            event_dict=event_dict,
            threat_type=rule_threat_map.get(primary_rule_id, "Unknown"),
            severity=severity,
            risk_score=round(risk_score, 2),
            detection_rule=primary_rule_id,
        )

        # Trigger Autonomous Prevention Escalation & Threat Actor Profiling
        prevention_result = prevention_engine.evaluate_threat(
            event_dict=event_dict,
            threat_type=rule_threat_map.get(primary_rule_id, "Unknown"),
            severity=severity,
            risk_score=round(risk_score, 2),
            detection_rule=primary_rule_id,
        )

        # Force fail compromised quantum verification (Block & Invalidate Attack)
        event.verification_result = False
        event.metadata_json = {
            **(event.metadata_json or {}),
            "mitigation": mitigation_record,
            "prevention": prevention_result,
        }

        # Record IP Threat & Automated IPS Quarantine
        threat_type_str = rule_threat_map.get(primary_rule_id, "Unknown")
        try:
            ip_firewall.record_threat_from_ip(source_ip, threat_type_str, severity)
            if severity in ["high", "critical"] or risk_score >= 50.0:
                ip_firewall.blacklist_ip_manual(
                    source_ip,
                    f"Automated IPS Defense: Quarantined on {threat_type_str} (Risk: {round(risk_score, 1)})",
                )
        except Exception as err:
            logger.error(f"IP Firewall telemetry error: {err}")

        threat = Threat(
            threat_id=str(uuid.uuid4()),
            event_id=event.event_id,
            threat_type=threat_type_str,
            severity=severity,
            risk_score=round(risk_score, 2),
            detection_rule=primary_rule_id,
            confidence=round(primary_confidence, 4),
            status="mitigated",
            evidence={
                "source_ip": source_ip,
                "risk_breakdown": risk_breakdown,
                "triggered_rules": [
                    {"rule_id": r[0], "confidence": r[1]} for r in triggered_rules
                ],
                "primary_evidence": primary_evidence,
                "all_triggered": [r[0] for r in triggered_rules],
                "mitigation": mitigation_record,
                "prevention": prevention_result,
            },
            detected_at=datetime.utcnow(),
        )
        db.add(threat)

    await db.commit()
    await db.refresh(event)
    if threat:
        await db.refresh(threat)

    # Step 8: Broadcast via WebSocket
    try:
        event_msg = {
            "type": "new_event",
            "data": {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
                "session_id": event.session_id,
                "source_node": event.source_node,
                "verification_result": event.verification_result,
                "measurement_deviation": event.measurement_deviation,
            },
        }
        await ws_manager.broadcast(event_msg)

        if threat:
            threat_msg = {
                "type": "new_threat",
                "data": {
                    "threat_id": threat.threat_id,
                    "threat_type": threat.threat_type,
                    "severity": threat.severity,
                    "risk_score": threat.risk_score,
                    "detection_rule": threat.detection_rule,
                    "event_id": threat.event_id,
                    "detected_at": threat.detected_at.isoformat(),
                },
            }
            await ws_manager.broadcast(threat_msg)
    except Exception as e:
        logger.error(f"WebSocket broadcast error: {e}")

    return event, threat
