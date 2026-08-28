"""
Quantum Honeypot & Deception Trap System.

Features:
- Decoy endpoints that simulate vulnerable legacy quantum key management and unauthenticated event ingestion.
- Automatically traps and records attacker reconnaissance and exploit payloads.
- Instantly flags, penalizes, and blacklists probing IPs.
- Returns realistic simulated responses to delay and deceive threat actors.
"""

import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.security.ip_firewall import ip_firewall
from app.security.rate_limiter import rate_limiter

logger = logging.getLogger("qds.honeypot")


class QuantumHoneypotManager:
    """
    Manages active honeypot traps and deceptive SOC telemetry.
    """

    def __init__(self):
        self.trap_hits: List[Dict[str, Any]] = []
        self.total_trapped_attackers: int = 0
        self.trapped_ips: set = set()

    def record_trap_trigger(
        self,
        trap_name: str,
        client_ip: str,
        method: str,
        payload: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Record interaction with a honeypot trap, blacklist attacker IP, and return realistic decoy response.
        """
        now = datetime.utcnow().isoformat()
        self.total_trapped_attackers += 1
        self.trapped_ips.add(client_ip)

        trap_record = {
            "id": f"TRAP-{len(self.trap_hits) + 1}",
            "timestamp": now,
            "trap_name": trap_name,
            "client_ip": client_ip,
            "http_method": method,
            "captured_payload": payload or {},
            "headers_summary": {k: v for k, v in (headers or {}).items() if k.lower() in ["user-agent", "authorization", "x-forwarded-for"]},
            "action_taken": "IMMEDIATE_IP_BLACKLIST_AND_TARPIT",
        }
        self.trap_hits.append(trap_record)
        if len(self.trap_hits) > 100:
            self.trap_hits.pop(0)

        # Autonomous Countermeasure: Immediate Hard Blacklist on Honeypot Tripping
        if client_ip not in ip_firewall.whitelist:
            ip_firewall.blacklist_ip_manual(
                client_ip,
                reason=f"Decoy Honeypot Tripped: Probed trap endpoint [{trap_name}]"
            )
            rate_limiter.auto_ban.record_violation(f"ip:{client_ip}")

        logger.critical(f"🪤 HONEYPOT TRAP TRIPPED: Attacker [{client_ip}] accessed decoy [{trap_name}] — IP BLACKLISTED!")

        return {
            "status": "success",
            "code": 200,
            "decoy_quantum_state": "|00⟩+|11⟩_legacy_qkd_channel_acknowledged",
            "message": "Legacy quantum node synchronization successful. Frame accepted.",
            "server_epoch": int(time.time()),
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "total_trapped": self.total_trapped_attackers,
            "unique_trapped_ips": len(self.trapped_ips),
            "recent_hits": self.trap_hits[-15:],
            "active_decoys": [
                "/api/v1/legacy/events (Legacy Ingestion Trap)",
                "/api/qkd/admin/key-export (Exposed Key Trap)",
                "/api/v1/debug/quantum-matrix (Raw State Exploit Trap)",
            ],
        }


# Global singleton
quantum_honeypot = QuantumHoneypotManager()
