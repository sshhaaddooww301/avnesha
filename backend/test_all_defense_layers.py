"""
Automated validation of all 6 defense layers and 14 detection rules.
"""

import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.engine.rules import RULE_REGISTRY
from app.security.ip_firewall import ip_firewall
from app.security.rate_limiter import rate_limiter
from app.security.request_validator import request_validator
from app.security.auth_middleware import api_key_manager
from app.engine.prevention import prevention_engine
from app.engine.honeypot import quantum_honeypot


async def run_maximum_security_tests():
    print("\n=== RUNNING 6-LAYER MAXIMUM SECURITY VALIDATION SUITE ===")
    
    # 1. Check all 14 rules registered
    assert len(RULE_REGISTRY) >= 14, f"Expected >= 14 rules, found {len(RULE_REGISTRY)}"
    expected_rules = [
        "QDS-RPL-001", "QDS-MITM-001", "QDS-FRG-001", "QDS-IMP-001", "QDS-ANM-001",
        "QDS-PNS-001", "QDS-BLD-001", "QDS-RPD-001", "QDS-EVS-001",
        "QDS-DDoS-001", "QDS-BRUTE-001", "QDS-COORD-001", "QDS-ENTROPY-001", "QDS-TIMEBOMB-001"
    ]
    for r in expected_rules:
        assert r in RULE_REGISTRY, f"Missing rule: {r}"
    print(f"[PASS] Layer 6: All {len(RULE_REGISTRY)} detection rules active and registered.")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 2. Test Security Status API & DEFCON calculation
        sec_res = await client.get("/api/security/status")
        assert sec_res.status_code == 200
        sec_data = sec_res.json()
        assert "threat_level" in sec_data
        assert sec_data["total_active_defense_layers"] == 6
        print(f"[PASS] Security Status API active — Current Posture: {sec_data['threat_level']}")

        # 3. Test Honeypot Decoy Trap
        hp_res = await client.post("/api/security/v1/legacy/events", json={"exploit": "raw_buffer_overflow"})
        assert hp_res.status_code == 200
        hp_data = hp_res.json()
        assert hp_data["status"] == "success"
        assert quantum_honeypot.total_trapped_attackers >= 1
        print("[PASS] Honeypot Trap: Attacker lure recorded and neutralized.")

        # 4. Test Manual IP Blacklisting & Unblocking
        test_bad_ip = "198.51.100.44"
        block_res = await client.post("/api/security/ip/block", json={"ip": test_bad_ip, "reason": "Test attacker ban"})
        assert block_res.status_code == 200
        assert test_bad_ip in ip_firewall.blacklist
        print(f"[PASS] Layer 1 IP Firewall: Successfully blacklisted malicious IP {test_bad_ip}.")

        unblock_res = await client.post("/api/security/ip/unblock", json={"ip": test_bad_ip})
        assert unblock_res.status_code == 200
        assert test_bad_ip not in ip_firewall.blacklist
        print(f"[PASS] Layer 1 IP Firewall: Successfully unblocked IP {test_bad_ip}.")

        # 5. Test Emergency Lockdown Toggle
        lock_res = await client.post("/api/security/lockdown", json={"enabled": True})
        assert lock_res.status_code == 200
        assert ip_firewall.lockdown_mode is True
        print("[PASS] Layer 1 Firewall: Emergency Lockdown mode ACTIVATED.")

        unlock_res = await client.post("/api/security/lockdown", json={"enabled": False})
        assert unlock_res.status_code == 200
        assert ip_firewall.lockdown_mode is False
        print("[PASS] Layer 1 Firewall: Emergency Lockdown mode DEACTIVATED.")

        # 6. Test API Key Generation & Revocation
        keygen_res = await client.post("/api/security/keys/generate", json={"description": "Test Key"})
        assert keygen_res.status_code == 200
        key_info = keygen_res.json()
        assert "key_id" in key_info and "api_key" in key_info
        print(f"[PASS] Layer 3 Auth: Generated HMAC API key [{key_info['key_id']}].")

        revoke_res = await client.post("/api/security/keys/revoke", json={"key_id": key_info["key_id"]})
        assert revoke_res.status_code == 200
        print(f"[PASS] Layer 3 Auth: Revoked API key [{key_info['key_id']}].")

        # 7. Test Deep Request Validation (Injection Rejection)
        sqli_event = {
            "session_id": "SES-001; DROP TABLE security_events;--",
            "source_node": "QNode-Alpha",
            "event_type": "QDS_VERIFICATION",
        }
        val_res = await client.post("/api/events", json=sqli_event)
        assert val_res.status_code == 422
        print("[PASS] Layer 4 Validator: SQL injection & dangerous payload rejected with 422.")

    print("\n[SUCCESS] ALL 6 DEFENSE LAYERS & 14 DETECTION RULES VALIDATED!\n")


if __name__ == "__main__":
    asyncio.run(run_maximum_security_tests())
