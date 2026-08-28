"""
IP Firewall with Reputation Scoring & Auto-Ban.

Defense Layer 1: First line of defense against known malicious IPs.

Features:
- IP reputation scoring (0-100, starts at 50)
- Auto-blacklist on reputation < 10
- Permanent blacklist for repeat offenders
- Whitelist for trusted SOC operator IPs
- CIDR range blocking
- Per-IP hit tracking (count, error rate, threat trigger rate)
"""

import time
import ipaddress
import logging
from typing import Dict, Any, Optional, Tuple, Set, List
from collections import defaultdict

logger = logging.getLogger("qds.ip_firewall")


class IPProfile:
    """Track behavioral profile of an IP address."""

    def __init__(self, ip: str):
        self.ip = ip
        self.reputation: float = 50.0  # Start neutral
        self.total_requests: int = 0
        self.total_errors: int = 0
        self.total_threats_triggered: int = 0
        self.first_seen: float = time.time()
        self.last_seen: float = time.time()
        self.attack_types: Dict[str, int] = defaultdict(int)
        self.is_blacklisted: bool = False
        self.blacklist_reason: str = ""
        self.blacklisted_at: Optional[float] = None

    def record_request(self):
        self.total_requests += 1
        self.last_seen = time.time()
        # Slight reputation recovery for normal requests
        if self.reputation < 50.0:
            self.reputation = min(50.0, self.reputation + 0.1)

    def record_error(self):
        self.total_errors += 1
        self.reputation = max(0.0, self.reputation - 2.0)

    def record_threat(self, threat_type: str, severity: str):
        self.total_threats_triggered += 1
        self.attack_types[threat_type] = self.attack_types.get(threat_type, 0) + 1

        # Severity-based reputation penalty
        penalties = {"low": 5.0, "medium": 10.0, "high": 20.0, "critical": 35.0}
        penalty = penalties.get(severity, 10.0)
        self.reputation = max(0.0, self.reputation - penalty)

        logger.info(
            f"IP FIREWALL: Reputation for [{self.ip}] dropped to {self.reputation:.1f} "
            f"(threat: {threat_type}, severity: {severity})"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ip": self.ip,
            "reputation": round(self.reputation, 1),
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "total_threats_triggered": self.total_threats_triggered,
            "attack_types": dict(self.attack_types),
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "is_blacklisted": self.is_blacklisted,
            "blacklist_reason": self.blacklist_reason,
            "blacklisted_at": self.blacklisted_at,
            "error_rate": round(
                self.total_errors / max(self.total_requests, 1) * 100, 1
            ),
        }


class IPFirewall:
    """
    IP-level firewall with reputation tracking and auto-blacklisting.
    """

    REPUTATION_BLACKLIST_THRESHOLD = 10.0
    REPUTATION_SUSPECT_THRESHOLD = 25.0

    def __init__(self):
        self.profiles: Dict[str, IPProfile] = {}
        self.blacklist: Dict[str, Dict[str, Any]] = {}
        self.whitelist: Set[str] = {
            "127.0.0.1",
            "::1",
            "localhost",
        }
        self.blocked_cidr_ranges: List[str] = []
        self.total_blocked: int = 0
        self.total_checked: int = 0
        self.lockdown_mode: bool = False  # Emergency lockdown

    def _get_profile(self, ip: str) -> IPProfile:
        """Get or create IP profile."""
        if ip not in self.profiles:
            self.profiles[ip] = IPProfile(ip)
        return self.profiles[ip]

    def _is_private_ip(self, ip: str) -> bool:
        """Check if IP is in private/local range."""
        try:
            addr = ipaddress.ip_address(ip)
            return addr.is_private or addr.is_loopback
        except ValueError:
            return False

    def _check_cidr_block(self, ip: str) -> bool:
        """Check if IP falls within any blocked CIDR range."""
        try:
            addr = ipaddress.ip_address(ip)
            for cidr in self.blocked_cidr_ranges:
                if addr in ipaddress.ip_network(cidr, strict=False):
                    return True
        except ValueError:
            pass
        return False

    def check_ip(self, ip: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if an IP should be allowed through the firewall.

        Returns:
            (allowed: bool, rejection_info: Optional[dict])
        """
        self.total_checked += 1

        # Always allow whitelisted IPs
        if ip in self.whitelist:
            profile = self._get_profile(ip)
            profile.record_request()
            return True, None

        # Emergency lockdown: block everything except whitelist
        if self.lockdown_mode:
            # Allow private IPs during lockdown for local development
            if self._is_private_ip(ip):
                profile = self._get_profile(ip)
                profile.record_request()
                return True, None

            self.total_blocked += 1
            return False, {
                "reason": "EMERGENCY_LOCKDOWN",
                "detail": "System is in emergency lockdown mode. Only whitelisted IPs are allowed.",
                "ip": ip,
            }

        # Check explicit blacklist
        if ip in self.blacklist:
            self.total_blocked += 1
            bl_info = self.blacklist[ip]
            logger.warning(f"IP FIREWALL: Blocked blacklisted IP [{ip}]")
            return False, {
                "reason": "IP_BLACKLISTED",
                "detail": f"IP {ip} is blacklisted: {bl_info.get('reason', 'Unknown')}",
                "ip": ip,
                "blacklisted_at": bl_info.get("blacklisted_at"),
                "attack_history": bl_info.get("attack_types", {}),
            }

        # Check CIDR range blocks
        if self._check_cidr_block(ip):
            self.total_blocked += 1
            return False, {
                "reason": "CIDR_BLOCKED",
                "detail": f"IP {ip} falls within a blocked network range",
                "ip": ip,
            }

        # Check reputation-based auto-blacklist
        profile = self._get_profile(ip)
        profile.record_request()

        if profile.reputation < self.REPUTATION_BLACKLIST_THRESHOLD:
            # Auto-blacklist
            self._blacklist_ip(
                ip,
                reason=f"Reputation dropped below threshold ({profile.reputation:.1f} < {self.REPUTATION_BLACKLIST_THRESHOLD})",
                attack_types=dict(profile.attack_types),
            )
            self.total_blocked += 1
            return False, {
                "reason": "REPUTATION_BLACKLISTED",
                "detail": f"IP {ip} auto-blacklisted due to low reputation score ({profile.reputation:.1f})",
                "ip": ip,
                "reputation": profile.reputation,
            }

        return True, None

    def _blacklist_ip(self, ip: str, reason: str, attack_types: Optional[dict] = None):
        """Add IP to permanent blacklist."""
        profile = self._get_profile(ip)
        profile.is_blacklisted = True
        profile.blacklist_reason = reason
        profile.blacklisted_at = time.time()

        self.blacklist[ip] = {
            "ip": ip,
            "reason": reason,
            "blacklisted_at": time.time(),
            "attack_types": attack_types or {},
            "total_threats": profile.total_threats_triggered,
            "reputation_at_ban": round(profile.reputation, 1),
        }
        logger.warning(f"IP FIREWALL: Blacklisted IP [{ip}] — {reason}")

    def record_threat_from_ip(self, ip: str, threat_type: str, severity: str):
        """Record that a threat was detected from this IP."""
        profile = self._get_profile(ip)
        profile.record_threat(threat_type, severity)

    def record_error_from_ip(self, ip: str):
        """Record an error from this IP (validation failure, etc)."""
        profile = self._get_profile(ip)
        profile.record_error()

    def blacklist_ip_manual(self, ip: str, reason: str = "Manual block by SOC operator") -> bool:
        """Manually blacklist an IP."""
        if ip in self.whitelist:
            return False
        self._blacklist_ip(ip, reason)
        return True

    def unblock_ip(self, ip: str) -> bool:
        """Remove IP from blacklist."""
        if ip in self.blacklist:
            del self.blacklist[ip]
            profile = self._get_profile(ip)
            profile.is_blacklisted = False
            profile.reputation = 30.0  # Partially restore reputation
            logger.info(f"IP FIREWALL: Unblocked IP [{ip}]")
            return True
        return False

    def add_to_whitelist(self, ip: str) -> bool:
        """Add IP to trusted whitelist."""
        self.whitelist.add(ip)
        # Remove from blacklist if present
        if ip in self.blacklist:
            del self.blacklist[ip]
        return True

    def remove_from_whitelist(self, ip: str) -> bool:
        """Remove IP from whitelist."""
        if ip in self.whitelist and ip not in {"127.0.0.1", "::1", "localhost"}:
            self.whitelist.discard(ip)
            return True
        return False

    def add_cidr_block(self, cidr: str) -> bool:
        """Block an entire CIDR range."""
        try:
            ipaddress.ip_network(cidr, strict=False)
            if cidr not in self.blocked_cidr_ranges:
                self.blocked_cidr_ranges.append(cidr)
                logger.warning(f"IP FIREWALL: Blocked CIDR range [{cidr}]")
            return True
        except ValueError:
            return False

    def toggle_lockdown(self, enable: bool):
        """Toggle emergency lockdown mode."""
        self.lockdown_mode = enable
        status = "ACTIVATED" if enable else "DEACTIVATED"
        logger.critical(f"IP FIREWALL: Emergency Lockdown {status}")

    def get_status(self) -> Dict[str, Any]:
        """Get full firewall status."""
        suspect_ips = [
            p.to_dict()
            for p in self.profiles.values()
            if p.reputation < self.REPUTATION_SUSPECT_THRESHOLD and not p.is_blacklisted
        ]

        return {
            "lockdown_mode": self.lockdown_mode,
            "total_checked": self.total_checked,
            "total_blocked": self.total_blocked,
            "block_rate": round(
                self.total_blocked / max(self.total_checked, 1) * 100, 2
            ),
            "blacklisted_ips": list(self.blacklist.values()),
            "blacklist_count": len(self.blacklist),
            "whitelisted_ips": list(self.whitelist),
            "blocked_cidr_ranges": self.blocked_cidr_ranges,
            "suspect_ips": suspect_ips,
            "total_tracked_ips": len(self.profiles),
        }

    def get_ip_profile(self, ip: str) -> Optional[Dict[str, Any]]:
        """Get detailed profile for a specific IP."""
        if ip in self.profiles:
            return self.profiles[ip].to_dict()
        return None


# Global singleton
ip_firewall = IPFirewall()
