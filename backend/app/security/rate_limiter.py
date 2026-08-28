"""
Sliding-Window Rate Limiter with Auto-Ban.

Defense Layer 2: Prevents DDoS, brute-force, and flooding attacks.

Features:
- Per-IP rate limiting (30 req/min default)
- Per-session rate limiting (50 req/min default)
- Global burst protection (200 req/min default)
- Auto-ban after 3 consecutive rate limit violations
- Exponential backoff on bans (15min → 1hr → 24hr)
"""

import time
import logging
from typing import Dict, Any, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger("qds.rate_limiter")


class SlidingWindowCounter:
    """Efficient sliding window rate counter using sub-windows."""

    def __init__(self, window_seconds: int = 60, num_buckets: int = 6):
        self.window_seconds = window_seconds
        self.num_buckets = num_buckets
        self.bucket_size = window_seconds / num_buckets
        self.buckets: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        self.last_cleanup = time.time()

    def _current_bucket(self) -> int:
        return int(time.time() / self.bucket_size)

    def _cleanup_old_buckets(self, key: str):
        current = self._current_bucket()
        cutoff = current - self.num_buckets
        if key in self.buckets:
            old_keys = [b for b in self.buckets[key] if b <= cutoff]
            for b in old_keys:
                del self.buckets[key][b]

    def increment(self, key: str) -> int:
        """Increment counter for key and return current window count."""
        current = self._current_bucket()
        self.buckets[key][current] += 1
        self._cleanup_old_buckets(key)
        return self.get_count(key)

    def get_count(self, key: str) -> int:
        """Get total count in current window."""
        current = self._current_bucket()
        cutoff = current - self.num_buckets
        self._cleanup_old_buckets(key)
        return sum(
            count for bucket, count in self.buckets[key].items()
            if bucket > cutoff
        )


class AutoBanManager:
    """Tracks rate limit violations and auto-bans repeat offenders."""

    # Exponential backoff durations in seconds
    BAN_DURATIONS = [
        900,     # 15 minutes (1st ban)
        3600,    # 1 hour (2nd ban)
        86400,   # 24 hours (3rd+ ban)
    ]

    def __init__(self):
        self.violations: Dict[str, int] = defaultdict(int)  # key → violation count
        self.bans: Dict[str, Dict[str, Any]] = {}  # key → ban info
        self.total_bans: int = 0

    def record_violation(self, key: str) -> Optional[Dict[str, Any]]:
        """Record a rate limit violation. Returns ban info if ban threshold reached."""
        self.violations[key] += 1

        if self.violations[key] >= 3:
            return self._ban(key)
        return None

    def _ban(self, key: str) -> Dict[str, Any]:
        """Ban a key with exponential backoff duration."""
        ban_count = len([1 for k, v in self.bans.items() if k == key]) + 1
        duration_idx = min(ban_count - 1, len(self.BAN_DURATIONS) - 1)
        duration = self.BAN_DURATIONS[duration_idx]

        ban_info = {
            "key": key,
            "banned_at": time.time(),
            "expires_at": time.time() + duration,
            "duration_seconds": duration,
            "ban_number": ban_count,
            "violation_count": self.violations[key],
            "reason": f"Rate limit exceeded {self.violations[key]} times",
        }
        self.bans[key] = ban_info
        self.total_bans += 1
        self.violations[key] = 0  # Reset violation counter

        logger.warning(
            f"RATE LIMITER: Auto-banned [{key}] for {duration}s "
            f"(ban #{ban_count}, violations: {ban_info['violation_count']})"
        )
        return ban_info

    def is_banned(self, key: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Check if a key is currently banned."""
        if key not in self.bans:
            return False, None

        ban_info = self.bans[key]
        if time.time() >= ban_info["expires_at"]:
            # Ban expired, remove it
            del self.bans[key]
            logger.info(f"RATE LIMITER: Ban expired for [{key}]")
            return False, None

        remaining = int(ban_info["expires_at"] - time.time())
        return True, {**ban_info, "remaining_seconds": remaining}

    def unban(self, key: str) -> bool:
        """Manually unban a key."""
        if key in self.bans:
            del self.bans[key]
            self.violations.pop(key, None)
            return True
        return False

    def get_all_bans(self) -> list:
        """Get all currently active bans."""
        active = []
        expired = []
        now = time.time()
        for key, info in self.bans.items():
            if now < info["expires_at"]:
                active.append({**info, "remaining_seconds": int(info["expires_at"] - now)})
            else:
                expired.append(key)
        for k in expired:
            del self.bans[k]
        return active


class RateLimiter:
    """
    Multi-tier sliding-window rate limiter.

    Limits:
    - Per-IP: 30 requests per minute (default)
    - Per-session: 50 requests per minute (default)
    - Global: 200 requests per minute (default)
    """

    def __init__(
        self,
        per_ip_limit: int = 30,
        per_session_limit: int = 50,
        global_limit: int = 200,
        window_seconds: int = 60,
    ):
        self.per_ip_limit = per_ip_limit
        self.per_session_limit = per_session_limit
        self.global_limit = global_limit

        self.ip_counter = SlidingWindowCounter(window_seconds)
        self.session_counter = SlidingWindowCounter(window_seconds)
        self.global_counter = SlidingWindowCounter(window_seconds)

        self.auto_ban = AutoBanManager()
        self.total_rate_limited: int = 0
        self.total_requests: int = 0

    def check_rate_limit(
        self,
        ip_address: str,
        session_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if request should be rate limited.

        Returns:
            (allowed: bool, rejection_info: Optional[dict])
        """
        self.total_requests += 1

        # Exempt loopback / local development IPs from rate limiting so dashboard is never throttled
        if ip_address in ["127.0.0.1", "::1", "localhost"]:
            return True, None

        # Check if IP is auto-banned
        banned, ban_info = self.auto_ban.is_banned(f"ip:{ip_address}")
        if banned:
            self.total_rate_limited += 1
            return False, {
                "reason": "IP_AUTO_BANNED",
                "detail": f"IP {ip_address} is temporarily banned due to excessive rate limit violations",
                "ban_info": ban_info,
                "retry_after": ban_info.get("remaining_seconds", 60),
            }

        # Layer 1: Global rate limit
        global_count = self.global_counter.increment("global")
        if global_count > self.global_limit:
            self.total_rate_limited += 1
            return False, {
                "reason": "GLOBAL_RATE_LIMIT",
                "detail": f"Global rate limit exceeded ({global_count}/{self.global_limit} per minute)",
                "retry_after": 60,
            }

        # Layer 2: Per-IP rate limit
        ip_count = self.ip_counter.increment(ip_address)
        if ip_count > self.per_ip_limit:
            self.total_rate_limited += 1
            ban_result = self.auto_ban.record_violation(f"ip:{ip_address}")
            return False, {
                "reason": "IP_RATE_LIMIT",
                "detail": f"IP rate limit exceeded ({ip_count}/{self.per_ip_limit} per minute)",
                "ip": ip_address,
                "auto_banned": ban_result is not None,
                "retry_after": ban_result["duration_seconds"] if ban_result else 60,
            }

        # Layer 3: Per-session rate limit
        if session_id:
            session_count = self.session_counter.increment(session_id)
            if session_count > self.per_session_limit:
                self.total_rate_limited += 1
                return False, {
                    "reason": "SESSION_RATE_LIMIT",
                    "detail": f"Session rate limit exceeded ({session_count}/{self.per_session_limit} per minute)",
                    "session_id": session_id,
                    "retry_after": 60,
                }

        return True, None

    def get_status(self) -> Dict[str, Any]:
        """Get current rate limiter status."""
        return {
            "total_requests": self.total_requests,
            "total_rate_limited": self.total_rate_limited,
            "rate_limit_percentage": round(
                (self.total_rate_limited / max(self.total_requests, 1)) * 100, 2
            ),
            "limits": {
                "per_ip": self.per_ip_limit,
                "per_session": self.per_session_limit,
                "global": self.global_limit,
            },
            "active_bans": self.auto_ban.get_all_bans(),
            "total_auto_bans": self.auto_ban.total_bans,
        }


# Global singleton
rate_limiter = RateLimiter()
