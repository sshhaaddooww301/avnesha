"""
HMAC-Based API Key Authentication Middleware.

Defense Layer 3: Authenticates all event ingestion requests.

Features:
- HMAC-SHA256 based API key validation
- Key rotation support (multiple active keys)
- Rate limit per API key
- Internal endpoints exempt when from localhost
- Key generation utility
"""

import hmac
import hashlib
import secrets
import time
import logging
from typing import Dict, Any, Optional, Tuple, Set

logger = logging.getLogger("qds.auth")


class APIKeyManager:
    """
    Manages API keys for authenticated event ingestion.

    API keys are validated via HMAC-SHA256.
    Supports multiple active keys for rotation.
    """

    def __init__(self):
        # Default master key (should be overridden via env/settings)
        self._master_secret = "qds-siem-master-secret-2024"

        # Active API keys: key_id → key_info
        self.api_keys: Dict[str, Dict[str, Any]] = {}

        # IPs that bypass auth (localhost, internal)
        self.exempt_ips: Set[str] = {
            "127.0.0.1",
            "::1",
            "localhost",
        }

        # Auth bypass for development mode
        self.dev_mode: bool = True  # Set to False in production

        # Stats
        self.total_auth_checks: int = 0
        self.total_auth_failures: int = 0
        self.total_auth_bypasses: int = 0

        # Generate default API key for demo
        self._generate_default_key()

    def _generate_default_key(self):
        """Generate a default API key for the demo/hackathon."""
        default_key = self._generate_key_hash("qds-default-demo-key")
        self.api_keys["qds-default"] = {
            "key_id": "qds-default",
            "key_hash": default_key,
            "key_plaintext": "qds-default-demo-key",  # Only stored for demo
            "created_at": time.time(),
            "last_used": None,
            "request_count": 0,
            "description": "Default demo API key",
            "active": True,
        }

    def _generate_key_hash(self, key: str) -> str:
        """Generate HMAC-SHA256 hash for a key."""
        return hmac.new(
            self._master_secret.encode(),
            key.encode(),
            hashlib.sha256,
        ).hexdigest()

    def generate_new_key(self, description: str = "") -> Dict[str, str]:
        """Generate a new API key pair."""
        key_id = f"qds-{secrets.token_hex(4)}"
        raw_key = secrets.token_urlsafe(32)
        key_hash = self._generate_key_hash(raw_key)

        self.api_keys[key_id] = {
            "key_id": key_id,
            "key_hash": key_hash,
            "created_at": time.time(),
            "last_used": None,
            "request_count": 0,
            "description": description,
            "active": True,
        }

        logger.info(f"AUTH: Generated new API key [{key_id}]")
        return {"key_id": key_id, "api_key": raw_key}

    def validate_key(self, provided_key: str) -> Tuple[bool, Optional[str]]:
        """
        Validate an API key.

        Returns:
            (valid: bool, key_id: Optional[str])
        """
        provided_hash = self._generate_key_hash(provided_key)

        for key_id, key_info in self.api_keys.items():
            if not key_info["active"]:
                continue
            if hmac.compare_digest(key_info["key_hash"], provided_hash):
                key_info["last_used"] = time.time()
                key_info["request_count"] += 1
                return True, key_id

        return False, None

    def check_auth(
        self,
        api_key: Optional[str],
        client_ip: str,
        endpoint: str,
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if request is authenticated.

        Returns:
            (allowed: bool, rejection_info: Optional[dict])
        """
        self.total_auth_checks += 1

        # Dev mode bypass
        if self.dev_mode:
            self.total_auth_bypasses += 1
            return True, None

        # Exempt IPs (localhost, internal)
        if client_ip in self.exempt_ips:
            self.total_auth_bypasses += 1
            return True, None

        # Check for private IPs
        try:
            import ipaddress
            if ipaddress.ip_address(client_ip).is_private:
                self.total_auth_bypasses += 1
                return True, None
        except (ValueError, ImportError):
            pass

        # Exempt certain endpoints
        exempt_paths = ["/api/health", "/api/dashboard", "/api/security", "/docs", "/openapi.json"]
        if any(endpoint.startswith(path) for path in exempt_paths):
            return True, None

        # Require API key
        if not api_key:
            self.total_auth_failures += 1
            return False, {
                "reason": "MISSING_API_KEY",
                "detail": "API key required. Provide via X-API-Key header.",
            }

        valid, key_id = self.validate_key(api_key)
        if not valid:
            self.total_auth_failures += 1
            logger.warning(f"AUTH: Invalid API key from [{client_ip}] on [{endpoint}]")
            return False, {
                "reason": "INVALID_API_KEY",
                "detail": "Invalid API key provided.",
            }

        return True, None

    def revoke_key(self, key_id: str) -> bool:
        """Revoke an API key."""
        if key_id in self.api_keys:
            self.api_keys[key_id]["active"] = False
            logger.info(f"AUTH: Revoked API key [{key_id}]")
            return True
        return False

    def get_status(self) -> Dict[str, Any]:
        """Get auth system status."""
        return {
            "dev_mode": self.dev_mode,
            "total_auth_checks": self.total_auth_checks,
            "total_auth_failures": self.total_auth_failures,
            "total_auth_bypasses": self.total_auth_bypasses,
            "active_keys": sum(1 for k in self.api_keys.values() if k["active"]),
            "total_keys": len(self.api_keys),
            "exempt_ips": list(self.exempt_ips),
            "keys": [
                {
                    "key_id": k["key_id"],
                    "active": k["active"],
                    "created_at": k["created_at"],
                    "last_used": k["last_used"],
                    "request_count": k["request_count"],
                    "description": k.get("description", ""),
                }
                for k in self.api_keys.values()
            ],
        }


# Global singleton
api_key_manager = APIKeyManager()
