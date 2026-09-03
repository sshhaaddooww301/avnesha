"""
Security Operations & Threat Defense API.

Endpoints:
- GET /api/security/status -> Complete multi-layer defense posture & statistics
- POST /api/security/ip/block -> Manually block an IP
- POST /api/security/ip/unblock -> Unblock an IP
- POST /api/security/ip/whitelist -> Whitelist a trusted IP
- POST /api/security/lockdown -> Toggle emergency lockdown mode
- POST /api/security/circuit-breaker/reset -> Reset circuit breaker
- GET /api/security/threat-actors -> Correlated threat actor intelligence profiles
- GET /api/security/honeypot/status -> Decoy trap metrics & probe log
- POST /api/security/keys/generate -> Generate new API keys
- POST /api/security/keys/revoke -> Revoke an API key
- Decoy Honeypot endpoints: /api/v1/legacy/events, /api/qkd/admin/key-export
"""

from fastapi import APIRouter, HTTPException, Request, Body
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from app.security.ip_firewall import ip_firewall
from app.security.rate_limiter import rate_limiter
from app.security.request_validator import request_validator
from app.security.auth_middleware import api_key_manager
from app.engine.prevention import prevention_engine
from app.engine.honeypot import quantum_honeypot
from app.engine.soar import quantum_ips

router = APIRouter(prefix="/api/security", tags=["Security Operations & DEFCON"])


class IPActionRequest(BaseModel):
    ip: str
    reason: Optional[str] = "Manual operator action"


class LockdownRequest(BaseModel):
    enabled: bool


class KeyGenRequest(BaseModel):
    description: Optional[str] = "SOC Operator Key"


class KeyRevokeRequest(BaseModel):
    key_id: str


@router.get("/status")
async def get_comprehensive_security_status():
    """
    Returns full defense posture across all 6 defense layers:
    1. Threat Level (DEFCON calculation)
    2. IP Firewall & Blacklist
    3. Sliding-Window Rate Limiter
    4. API Key Authentication
    5. Payload Sanitizer / Entropy Engine
    6. Autonomous Prevention & Circuit Breaker
    7. Quantum IPS & Honeypot Telemetry
    """
    firewall_status = ip_firewall.get_status()
    rate_limit_status = rate_limiter.get_status()
    validator_status = request_validator.get_status()
    auth_status = api_key_manager.get_status()
    prevention_status = prevention_engine.get_status()
    honeypot_status = quantum_honeypot.get_status()
    ips_status = quantum_ips.get_status()

    # Calculate Real-Time DEFCON Threat Level (1 to 5)
    # 5 = Normal/Green, 4 = Guarded/Blue, 3 = Elevated/Yellow, 2 = High/Orange, 1 = Critical/Red
    crit_count = prevention_status.get("recent_critical_count_1m", 0)
    blocked_count = firewall_status.get("total_blocked", 0) + rate_limit_status.get("total_rate_limited", 0)
    
    if firewall_status.get("lockdown_mode") or prevention_status.get("circuit_breaker_active"):
        threat_level = "DEFCON 1: CRITICAL LOCKDOWN"
        threat_color = "red"
        threat_score = 1
    elif crit_count >= 3 or len(firewall_status.get("blacklisted_ips", [])) >= 5:
        threat_level = "DEFCON 2: HIGH THREAT SURGE"
        threat_color = "orange"
        threat_score = 2
    elif crit_count >= 1 or len(firewall_status.get("suspect_ips", [])) >= 2:
        threat_level = "DEFCON 3: ELEVATED THREAT ALERT"
        threat_color = "yellow"
        threat_score = 3
    elif blocked_count > 0:
        threat_level = "DEFCON 4: GUARDED - ACTIVE FILTERING"
        threat_color = "cyan"
        threat_score = 4
    else:
        threat_level = "DEFCON 5: NORMAL SECURE"
        threat_color = "green"
        threat_score = 5

    return {
        "threat_level": threat_level,
        "threat_color": threat_color,
        "threat_score": threat_score,
        "overall_defense_active": True,
        "total_active_defense_layers": 6,
        "layers": {
            "layer_1_ip_firewall": firewall_status,
            "layer_2_rate_limiter": rate_limit_status,
            "layer_3_api_auth": auth_status,
            "layer_4_payload_validator": validator_status,
            "layer_5_quantum_ips": ips_status,
            "layer_6_autonomous_prevention": prevention_status,
        },
        "honeypot_deception": honeypot_status,
    }


@router.post("/ip/block")
async def block_ip(request: IPActionRequest):
    """Manually block an IP address across IP firewall and rate limiter."""
    success = ip_firewall.blacklist_ip_manual(request.ip, request.reason)
    rate_limiter.auto_ban.record_violation(f"ip:{request.ip}")
    if not success:
        raise HTTPException(status_code=400, detail="Cannot block whitelisted or invalid IP")
    return {
        "status": "success",
        "message": f"IP [{request.ip}] permanently blacklisted and quarantined.",
        "ip": request.ip,
    }


@router.post("/ip/unblock")
async def unblock_ip(request: IPActionRequest):
    """Manually unblock an IP address across both firewall and rate limiter."""
    success_fw = ip_firewall.unblock_ip(request.ip)
    success_rl = rate_limiter.auto_ban.unban(f"ip:{request.ip}")
    return {
        "status": "success",
        "message": f"IP [{request.ip}] has been unblocked across firewall and rate limiter.",
        "firewall_unblocked": success_fw,
        "rate_limiter_unbanned": success_rl,
    }


@router.post("/rate-limit/reset")
async def reset_rate_limits():
    """Reset all active rate limiter bans, throttles, and counters."""
    rate_limiter.clear_all_bans()
    return {
        "status": "success",
        "message": "All rate limiter active bans, throttles, and sliding-window counters have been completely reset.",
    }


@router.post("/ip/whitelist")
async def whitelist_ip(request: IPActionRequest):
    """Whitelist a trusted SOC operator IP address."""
    ip_firewall.add_to_whitelist(request.ip)
    return {
        "status": "success",
        "message": f"IP [{request.ip}] added to trusted whitelist.",
    }


@router.post("/lockdown")
async def toggle_emergency_lockdown(request: LockdownRequest):
    """Engage or disengage full emergency lockdown mode."""
    ip_firewall.toggle_lockdown(request.enabled)
    if not request.enabled and prevention_engine.circuit_breaker_active:
        prevention_engine.reset_circuit_breaker()
    return {
        "status": "success",
        "lockdown_active": ip_firewall.lockdown_mode,
        "message": f"Emergency Lockdown {'ACTIVATED (All untrusted traffic blocked)' if ip_firewall.lockdown_mode else 'DEACTIVATED (Normal operations resumed)'}.",
    }


@router.post("/circuit-breaker/reset")
async def reset_circuit_breaker():
    """Reset tripped circuit breaker."""
    prevention_engine.reset_circuit_breaker()
    return {
        "status": "success",
        "message": "Circuit breaker reset. Normal traffic tolerance restored.",
    }


@router.get("/threat-actors")
async def get_threat_actor_intelligence():
    """Return aggregated threat actor profiles and correlated attack patterns."""
    return {
        "actors": prevention_engine.get_threat_actors(),
        "total_actors": len(prevention_engine.threat_actors),
    }


@router.get("/honeypot/status")
async def get_honeypot_status():
    """Return honeypot deception trap telemetry and captured probes."""
    return quantum_honeypot.get_status()


@router.post("/keys/generate")
async def generate_api_key(request: KeyGenRequest):
    """Generate a new HMAC-SHA256 API key."""
    new_key = api_key_manager.generate_new_key(request.description)
    return {
        "status": "success",
        "key_id": new_key["key_id"],
        "api_key": new_key["api_key"],
        "message": "API key successfully created. Keep the secret token secure.",
    }


@router.post("/keys/revoke")
async def revoke_api_key(request: KeyRevokeRequest):
    """Revoke an active API key."""
    success = api_key_manager.revoke_key(request.key_id)
    if not success:
        raise HTTPException(status_code=404, detail="Key ID not found")
    return {
        "status": "success",
        "message": f"API key [{request.key_id}] has been revoked.",
    }


# =========================================================================
# HONEYPOT DECOY ENDPOINTS (Captures and neutralizes malicious attackers)
# =========================================================================

@router.post("/v1/legacy/events")
@router.get("/v1/legacy/events")
async def honeypot_legacy_events(request: Request):
    """Decoy endpoint: Simulates old unauthenticated event ingestion interface."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    body = None
    try:
        if request.method == "POST":
            body = await request.json()
    except Exception:
        pass
    
    return quantum_honeypot.record_trap_trigger(
        trap_name="Legacy Ingestion Trap (/api/security/v1/legacy/events)",
        client_ip=client_ip,
        method=request.method,
        payload=body,
        headers=dict(request.headers),
    )


@router.get("/qkd/admin/key-export")
async def honeypot_key_export(request: Request):
    """Decoy endpoint: Simulates exposed QKD admin key export."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    return quantum_honeypot.record_trap_trigger(
        trap_name="QKD Key Export Trap (/api/security/qkd/admin/key-export)",
        client_ip=client_ip,
        method="GET",
        headers=dict(request.headers),
    )
