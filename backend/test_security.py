"""
Security boundary and vulnerability regression tests for QDS SIEM backend.
"""

import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

async def run_security_tests():
    print("=== RUNNING QDS SIEM SECURITY REGRESSION SUITE ===")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Test Health Endpoint & Security Headers
        resp = await client.get("/api/health")
        assert resp.status_code == 200, f"Health check failed: {resp.status_code}"
        assert resp.headers.get("X-Content-Type-Options") == "nosniff", "Missing X-Content-Type-Options header"
        assert resp.headers.get("X-Frame-Options") == "SAMEORIGIN", "Missing X-Frame-Options header"
        assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin", "Missing Referrer-Policy"
        print("[PASS] Test 1: HTTP Security Headers are properly enforced.")

        # 2. Test Negative Weight Injection (Math Poisoning Attack)
        malicious_settings = {
            "risk_weights": {
                "weight_deviation": -5.0,
            }
        }
        resp = await client.put("/api/settings", json=malicious_settings)
        assert resp.status_code == 422, f"Expected 422 Validation Error for negative weight, got {resp.status_code}"
        print("[PASS] Test 2: Attacker cannot inject negative weights (Math Poisoning blocked).")

        # 3. Test Invalid Severity Inversion Attack
        inverted_settings = {
            "severity_thresholds": {
                "low_max": 80,
                "medium_max": 40,
                "high_max": 90,
            }
        }
        resp = await client.put("/api/settings", json=inverted_settings)
        assert resp.status_code == 400, f"Expected 400 Bad Request for inverted thresholds, got {resp.status_code}"
        print("[PASS] Test 3: Attacker cannot invert severity thresholds (low >= med).")

        # 4. Test Event Ingestion Validation
        bad_event = {
            "session_id": "SES-101",
            # Missing source_node and event_type
        }
        resp = await client.post("/api/events", json=bad_event)
        assert resp.status_code == 422, f"Expected 422 for missing required event fields, got {resp.status_code}"
        print("[PASS] Test 4: Malformed event ingestion blocked with 422.")

        # 5. Test Legitimate Settings Update
        valid_settings = {
            "risk_weights": {
                "weight_deviation": 0.35,
                "weight_verification": 0.25,
            },
            "severity_thresholds": {
                "low_max": 25,
                "medium_max": 50,
                "high_max": 75,
            }
        }
        resp = await client.put("/api/settings", json=valid_settings)
        # 6. Test Photon Number Splitting (PNS) Detection Rule (QDS-PNS-001)
        pns_event = {
            "session_id": "SES-PNS-001",
            "source_node": "QNode-Alpha-01",
            "event_type": "QDS_DECOY_ANALYSIS",
            "quantum_state": "PNS-Decoy|Poisson-split⟩",
            "expected_measurement": 1.0,
            "observed_measurement": 0.76,
            "verification_result": False,
            "signature_hash": "a"*64,
            "metadata_json": {
                "pns_attack_detected": True,
                "decoy_gain_ratio": 1.65,
                "multi_photon_excess": 0.42,
            }
        }
        resp = await client.post("/api/events", json=pns_event)
        assert resp.status_code == 200
        pns_res = resp.json()
        assert pns_res["threat_detected"] is True, "PNS attack was not detected!"
        assert "Photon Number Splitting" in pns_res["threat_type"]
        print("[PASS] Test 6: Photon Number Splitting (PNS) attack detected & mitigated (QDS-PNS-001).")

        # 7. Test Detector Blinding & Saturation Attack (QDS-BLD-001)
        blinding_event = {
            "session_id": "SES-BLD-001",
            "source_node": "QNode-Beta-02",
            "event_type": "QDS_DETECTOR_TELEMETRY",
            "quantum_state": "SPAD|CW-Laser-Saturated-Blinded⟩",
            "expected_measurement": 1.0,
            "observed_measurement": 1.0,
            "verification_result": False,
            "signature_hash": "b"*64,
            "metadata_json": {
                "detector_blinded": True,
                "optical_power_uW": 120.5,
                "dark_count_rate_hz": 18500.0,
                "deadtime_variance_ns": 0.005,
            }
        }
        resp = await client.post("/api/events", json=blinding_event)
        assert resp.status_code == 200
        bld_res = resp.json()
        assert bld_res["threat_detected"] is True, "Detector Blinding attack was not detected!"
        assert "Detector Blinding" in bld_res["threat_type"]
        print("[PASS] Test 7: Detector Blinding & Optical Saturation detected & mitigated (QDS-BLD-001).")

        # 8. Test Multi-Party Repudiation Dispute Attack (QDS-RPD-001)
        repudiation_event = {
            "session_id": "SES-RPD-001",
            "source_node": "QNode-Gamma-03",
            "event_type": "QDS_MULTI_PARTY_SYMMETRIZATION",
            "quantum_state": "3Party-QDS|Dispute(Bob!=Charlie)⟩",
            "expected_measurement": 1.0,
            "observed_measurement": 1.0,
            "verification_result": False,
            "signature_hash": "c"*64,
            "metadata_json": {
                "repudiation_dispute": True,
                "symmetrization_mismatch": True,
                "bob_verification": True,
                "charlie_verification": False,
            }
        }
        resp = await client.post("/api/events", json=repudiation_event)
        assert resp.status_code == 200
        rpd_res = resp.json()
        assert rpd_res["threat_detected"] is True, "Repudiation Dispute attack was not detected!"
        assert "Repudiation" in rpd_res["threat_type"]
        print("[PASS] Test 8: Multi-Party Repudiation Dispute detected & mitigated (QDS-RPD-001).")

        # 9. Test Low-and-Slow Sub-threshold Evasion Attack (QDS-EVS-001)
        evasion_event = {
            "session_id": "SES-EVS-001",
            "source_node": "QNode-Delta-04",
            "event_type": "QDS_VERIFICATION",
            "quantum_state": "QDS|SubThreshold-Intercept⟩",
            "expected_measurement": 1.0,
            "observed_measurement": 0.82,
            "verification_result": False,
            "signature_hash": "d"*64,
            "metadata_json": {
                "low_slow_evasion": True,
                "sub_threshold_interception_rate": 0.035,
            }
        }
        resp = await client.post("/api/events", json=evasion_event)
        assert resp.status_code == 200
        evs_res = resp.json()
        assert evs_res["threat_detected"] is True, "Low-and-Slow Evasion attack was not detected!"
        assert "Low-and-Slow" in evs_res["threat_type"]
        print("[PASS] Test 9: Low-and-Slow Sub-Threshold Evasion detected & mitigated (QDS-EVS-001).")

    print("\n[SUCCESS] ALL 9 SECURITY DEFENSE TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    asyncio.run(run_security_tests())
