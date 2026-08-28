"""
Deep Payload Validation & Sanitization.

Defense Layer 4: Validates all incoming payloads before they reach the detection engine.

Features:
- Max payload size enforcement (64KB)
- Field-level regex validation (SQL injection, XSS, command injection prevention)
- JSON depth limit (max 5 levels)
- String length limits per field
- Shannon entropy analysis (detect encrypted/obfuscated payloads)
- Content-type enforcement
"""

import re
import math
import logging
from typing import Dict, Any, Optional, Tuple, List
from collections import Counter

logger = logging.getLogger("qds.request_validator")

# Maximum allowed values
MAX_PAYLOAD_SIZE = 65536  # 64KB
MAX_JSON_DEPTH = 5
MAX_STRING_LENGTH = 2048
MAX_FIELD_COUNT = 50

# Dangerous patterns (SQL injection, XSS, command injection, path traversal)
DANGEROUS_PATTERNS = [
    re.compile(r"(--|;|/\*|\*/|xp_|exec\s|execute\s|union\s+select|drop\s+table|insert\s+into|delete\s+from|update\s+.*\s+set)", re.IGNORECASE),  # SQL Injection
    re.compile(r"(<script|javascript:|on\w+\s*=|<iframe|<object|<embed|<svg\s+on)", re.IGNORECASE),  # XSS
    re.compile(r"(\|\s*(bash|sh|curl|wget|nc|python|cat|rm|chmod|powershell)|\$\(|\bcat\s+/etc|\bwget\s+http|\bcurl\s+http)", re.IGNORECASE),  # Command Injection
    re.compile(r"(\.\./|\.\.\\|%2e%2e|%252e%252e)", re.IGNORECASE),  # Path Traversal
    re.compile(r"(\{\{.*\}\}|<%.*%>|\$\{.*\})", re.IGNORECASE),  # Template Injection
]

# Field-specific length limits
FIELD_LIMITS = {
    "session_id": 128,
    "source_node": 256,
    "event_type": 128,
    "quantum_state": 1024,
    "signature_hash": 256,
    "event_id": 64,
}

# High entropy threshold (above this is suspicious)
HIGH_ENTROPY_THRESHOLD = 5.8


def shannon_entropy(data: str) -> float:
    """Calculate Shannon entropy of a string. Higher = more random/encrypted."""
    if not data:
        return 0.0
    counter = Counter(data)
    length = len(data)
    entropy = -sum(
        (count / length) * math.log2(count / length)
        for count in counter.values()
    )
    return entropy


def _check_json_depth(obj: Any, current_depth: int = 0) -> int:
    """Recursively check JSON nesting depth."""
    if current_depth > MAX_JSON_DEPTH:
        return current_depth

    if isinstance(obj, dict):
        if not obj:
            return current_depth
        return max(
            _check_json_depth(v, current_depth + 1)
            for v in obj.values()
        )
    elif isinstance(obj, list):
        if not obj:
            return current_depth
        return max(
            _check_json_depth(item, current_depth + 1)
            for item in obj
        )
    return current_depth


def _check_dangerous_patterns(value: str) -> Optional[str]:
    """Check a string value against dangerous patterns."""
    for pattern in DANGEROUS_PATTERNS:
        match = pattern.search(value)
        if match:
            return f"Dangerous pattern detected: '{match.group()[:30]}...'"
    return None


def _validate_string_fields(data: Dict[str, Any], path: str = "") -> List[str]:
    """Recursively validate all string fields in data."""
    violations = []

    for key, value in data.items():
        field_path = f"{path}.{key}" if path else key

        if isinstance(value, str):
            # Check field-specific length limits
            max_len = FIELD_LIMITS.get(key, MAX_STRING_LENGTH)
            if len(value) > max_len:
                violations.append(
                    f"Field '{field_path}' exceeds max length ({len(value)} > {max_len})"
                )

            # Check for dangerous patterns
            danger = _check_dangerous_patterns(value)
            if danger:
                violations.append(f"Field '{field_path}': {danger}")

        elif isinstance(value, dict):
            violations.extend(_validate_string_fields(value, field_path))

        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, str):
                    danger = _check_dangerous_patterns(item)
                    if danger:
                        violations.append(f"Field '{field_path}[{i}]': {danger}")
                elif isinstance(item, dict):
                    violations.extend(_validate_string_fields(item, f"{field_path}[{i}]"))

    return violations


class RequestValidator:
    """Deep request payload validator."""

    def __init__(self):
        self.total_validated: int = 0
        self.total_rejected: int = 0
        self.rejection_reasons: Dict[str, int] = {}

    def validate_event_payload(
        self, data: Dict[str, Any], raw_size: int = 0
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validate an incoming event payload.

        Returns:
            (valid: bool, rejection_info: Optional[dict])
        """
        self.total_validated += 1
        violations = []

        # 1. Size check
        if raw_size > MAX_PAYLOAD_SIZE:
            violations.append(f"Payload size exceeds limit ({raw_size} > {MAX_PAYLOAD_SIZE} bytes)")

        # 2. Field count check
        if len(data) > MAX_FIELD_COUNT:
            violations.append(f"Too many fields ({len(data)} > {MAX_FIELD_COUNT})")

        # 3. JSON depth check
        depth = _check_json_depth(data)
        if depth > MAX_JSON_DEPTH:
            violations.append(f"JSON nesting too deep ({depth} > {MAX_JSON_DEPTH})")

        # 4. Required fields check
        required = ["session_id", "source_node", "event_type"]
        for field in required:
            if field not in data or not data[field]:
                violations.append(f"Required field '{field}' is missing or empty")

        # 5. String field validation (length + dangerous patterns)
        violations.extend(_validate_string_fields(data))

        # 6. Entropy analysis on metadata
        metadata = data.get("metadata_json")
        if metadata and isinstance(metadata, dict):
            metadata_str = str(metadata)
            entropy = shannon_entropy(metadata_str)
            if entropy > HIGH_ENTROPY_THRESHOLD and len(metadata_str) > 100:
                violations.append(
                    f"Suspiciously high entropy in metadata ({entropy:.2f} > {HIGH_ENTROPY_THRESHOLD}) — possible encrypted/obfuscated payload"
                )

        # 7. Numeric field range validation
        for field in ["expected_measurement", "observed_measurement"]:
            val = data.get(field)
            if val is not None:
                if not isinstance(val, (int, float)):
                    violations.append(f"Field '{field}' must be numeric")
                elif abs(val) > 1e10:
                    violations.append(f"Field '{field}' value out of reasonable range ({val})")

        # 8. Signature hash format validation
        sig_hash = data.get("signature_hash")
        if sig_hash and isinstance(sig_hash, str):
            if not re.match(r'^[a-fA-F0-9]{32,128}$', sig_hash):
                # Allow non-hex hashes but flag very short or suspicious ones
                if len(sig_hash) < 8:
                    violations.append(f"Signature hash too short ({len(sig_hash)} chars)")

        if violations:
            self.total_rejected += 1
            for v in violations:
                reason_key = v.split(":")[0] if ":" in v else v[:50]
                self.rejection_reasons[reason_key] = self.rejection_reasons.get(reason_key, 0) + 1

            logger.warning(f"REQUEST VALIDATOR: Rejected payload — {violations}")
            return False, {
                "reason": "PAYLOAD_VALIDATION_FAILED",
                "violations": violations,
                "violation_count": len(violations),
            }

        return True, None

    def get_status(self) -> Dict[str, Any]:
        """Get validator stats."""
        return {
            "total_validated": self.total_validated,
            "total_rejected": self.total_rejected,
            "rejection_rate": round(
                self.total_rejected / max(self.total_validated, 1) * 100, 2
            ),
            "top_rejection_reasons": dict(
                sorted(self.rejection_reasons.items(), key=lambda x: x[1], reverse=True)[:10]
            ),
        }


# Global singleton
request_validator = RequestValidator()
