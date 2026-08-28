"""
Autonomous Prevention Engine & Threat Intelligence Correlation.

Features:
- Auto-Escalation Matrix (Low/Medium/High/Critical automated responses)
- Circuit Breaker (Triggers automatic lockdown upon attack surge)
- Adaptive Thresholds (Tightens detection tolerances under heavy attack)
- Threat Intelligence Correlation (Correlates multi-source attacks & builds threat actor profiles)
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict

from app.security.ip_firewall import ip_firewall
from app.security.rate_limiter import rate_limiter

logger = logging.getLogger("qds.prevention")


class ThreatActorProfile:
    """Consolidated threat intelligence profile for an identified attacker."""

    def __init__(self, actor_id: str):
        self.actor_id = actor_id
        self.associated_ips: set = set()
        self.associated_nodes: set = set()
        self.associated_sessions: set = set()
        self.attack_vectors: Dict[str, int] = defaultdict(int)
        self.total_attacks: int = 0
        self.highest_severity: str = "low"
        self.highest_risk_score: float = 0.0
        self.first_detected: float = time.time()
        self.last_detected: float = time.time()
        self.is_contained: bool = False

    def record_incident(
        self,
        ip: Optional[str],
        node_id: Optional[str],
        session_id: Optional[str],
        threat_type: str,
        severity: str,
        risk_score: float,
    ):
        if ip:
            self.associated_ips.add(ip)
        if node_id:
            self.associated_nodes.add(node_id)
        if session_id:
            self.associated_sessions.add(session_id)

        self.attack_vectors[threat_type] += 1
        self.total_attacks += 1
        self.last_detected = time.time()

        severity_ranks = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        if severity_ranks.get(severity, 1) > severity_ranks.get(self.highest_severity, 1):
            self.highest_severity = severity
        if risk_score > self.highest_risk_score:
            self.highest_risk_score = risk_score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "actor_id": self.actor_id,
            "associated_ips": list(self.associated_ips),
            "associated_nodes": list(self.associated_nodes),
            "associated_sessions": list(self.associated_sessions),
            "attack_vectors": dict(self.attack_vectors),
            "total_attacks": self.total_attacks,
            "highest_severity": self.highest_severity,
            "highest_risk_score": round(self.highest_risk_score, 2),
            "first_detected": datetime.fromtimestamp(self.first_detected).isoformat(),
            "last_detected": datetime.fromtimestamp(self.last_detected).isoformat(),
            "is_contained": self.is_contained,
        }


class AutonomousPreventionEngine:
    """
    Autonomous Security Operations & Escalation Engine.
    """

    def __init__(self):
        self.threat_actors: Dict[str, ThreatActorProfile] = {}
        self.recent_critical_threats: List[float] = []
        self.circuit_breaker_active: bool = False
        self.circuit_breaker_triggered_at: Optional[float] = None
        self.adaptive_mode_active: bool = False
        self.total_preventive_actions: int = 0
        self.prevention_log: List[Dict[str, Any]] = []

    def evaluate_threat(
        self,
        event_dict: Dict[str, Any],
        threat_type: str,
        severity: str,
        risk_score: float,
        detection_rule: str,
        client_ip: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute automated escalation actions based on threat assessment.
        """
        now = time.time()
        source_node = event_dict.get("source_node", "Unknown")
        session_id = event_dict.get("session_id", "Unknown")
        ip = client_ip or event_dict.get("metadata_json", {}).get("client_ip", "127.0.0.1")

        # 1. Update Threat Actor Intelligence Profile
        actor_key = f"ACTOR-{source_node}" if source_node != "Unknown" else f"IP-{ip}"
        if actor_key not in self.threat_actors:
            self.threat_actors[actor_key] = ThreatActorProfile(actor_key)
        
        actor = self.threat_actors[actor_key]
        actor.record_incident(ip, source_node, session_id, threat_type, severity, risk_score)

        actions_taken = []

        # 2. Escalation Matrix Execution
        if severity == "critical" or risk_score >= 75.0:
            # Track critical frequency for circuit breaker
            self.recent_critical_threats.append(now)
            
            # Action: IP Auto-Blacklist
            if ip and ip not in ip_firewall.whitelist:
                ip_firewall.blacklist_ip_manual(ip, f"Automated block: Critical threat [{threat_type}] detected (Risk: {risk_score})")
                actions_taken.append(f"IP_BLACKLISTED:[{ip}]")
            
            # Action: Ban actor in rate limiter
            rate_limiter.auto_ban.record_violation(f"ip:{ip}")
            actions_taken.append("RATE_LIMITER_PENALTY_ENFORCED")
            actor.is_contained = True

        elif severity == "high" or risk_score >= 50.0:
            if ip:
                ip_firewall.record_threat_from_ip(ip, threat_type, severity)
                actions_taken.append(f"IP_REPUTATION_PENALIZED:[{ip}]")

        # 3. Check Circuit Breaker Condition (e.g., > 5 critical threats in 60 seconds)
        self._check_circuit_breaker(now)
        if self.circuit_breaker_active:
            actions_taken.append("CIRCUIT_BREAKER_DEFENSE_ACTIVE")

        # 4. Check Adaptive Thresholds
        if len(self.recent_critical_threats) >= 3:
            self.adaptive_mode_active = True
            actions_taken.append("ADAPTIVE_SENSITIVITY_ENGAGED")

        self.total_preventive_actions += len(actions_taken)
        
        prevention_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "threat_type": threat_type,
            "severity": severity,
            "risk_score": risk_score,
            "rule": detection_rule,
            "source_node": source_node,
            "client_ip": ip,
            "actions": actions_taken,
        }
        self.prevention_log.append(prevention_entry)
        if len(self.prevention_log) > 200:
            self.prevention_log.pop(0)

        logger.info(f"PREVENTION ENGINE ACTION for {threat_type} (Severity: {severity}): {actions_taken}")
        return {
            "actions": actions_taken,
            "actor_id": actor.actor_id,
            "actor_total_attacks": actor.total_attacks,
            "circuit_breaker": self.circuit_breaker_active,
            "adaptive_mode": self.adaptive_mode_active,
        }

    def _check_circuit_breaker(self, current_time: float):
        # Keep only threats in last 60 seconds
        self.recent_critical_threats = [
            t for t in self.recent_critical_threats if current_time - t <= 60.0
        ]
        if len(self.recent_critical_threats) >= 5 and not self.circuit_breaker_active:
            self.circuit_breaker_active = True
            self.circuit_breaker_triggered_at = current_time
            ip_firewall.toggle_lockdown(True)
            logger.critical("🚨 CIRCUIT BREAKER TRIPPED! Automated Emergency Lockdown Initiated.")

    def reset_circuit_breaker(self):
        self.circuit_breaker_active = False
        self.circuit_breaker_triggered_at = None
        self.recent_critical_threats.clear()
        ip_firewall.toggle_lockdown(False)
        logger.info("Circuit breaker manually reset by SOC Operator.")

    def get_adaptive_thresholds(self, default_deviation: float = 0.30, default_zscore: float = 2.5) -> Tuple[float, float]:
        """
        Dynamically tighten detection thresholds if system is experiencing an attack surge.
        """
        if self.adaptive_mode_active:
            # 50% tighter tolerance under attack
            return default_deviation * 0.5, default_zscore * 0.6
        return default_deviation, default_zscore

    def get_threat_actors(self) -> List[Dict[str, Any]]:
        return [actor.to_dict() for actor in self.threat_actors.values()]

    def get_status(self) -> Dict[str, Any]:
        return {
            "circuit_breaker_active": self.circuit_breaker_active,
            "circuit_breaker_triggered_at": self.circuit_breaker_triggered_at,
            "adaptive_mode_active": self.adaptive_mode_active,
            "total_preventive_actions": self.total_preventive_actions,
            "total_tracked_actors": len(self.threat_actors),
            "recent_critical_count_1m": len(self.recent_critical_threats),
            "recent_actions": self.prevention_log[-10:],
        }


# Global singleton
prevention_engine = AutonomousPreventionEngine()
