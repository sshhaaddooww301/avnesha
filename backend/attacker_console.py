#!/usr/bin/env python3
"""
QDS Red-Team Attacker Console (Multi-Laptop Live Attack Tool).

Run this script on Laptop 2 (Attacker Laptop) to launch live quantum attacks
against Laptop 1 (SIEM / SOC Server) across the local Wi-Fi / LAN network.

Usage:
    python attacker_console.py --target http://<LAPTOP_1_IP>:8000
"""

import time
import argparse
import random
import uuid
import hashlib
import json
from datetime import datetime

try:
    import requests
except ImportError:
    print("Please install requests: pip install requests")
    exit(1)


def generate_sha256(val: str) -> str:
    return hashlib.sha256(val.encode()).hexdigest()


class RedTeamAttacker:
    def __init__(self, target_url: str):
        self.target_url = target_url.rstrip("/")
        self.events_url = f"{self.target_url}/api/events"
        self.test_lab_url = f"{self.target_url}/api/test-lab/run"
        self.recent_hashes = []

    def check_connection(self) -> bool:
        try:
            r = requests.get(f"{self.target_url}/api/health", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    def attack_mitm(self, count=1):
        print(f"\n[+] Infiltrating Quantum Channel with Intercept-Resend Eavesdropping ({count} packets)...")
        for i in range(count):
            session_id = f"QDS-ATK-MITM-{uuid.uuid4().hex[:8].upper()}"
            source = f"QNode-Alpha-01"
            noise = random.uniform(0.35, 0.65)
            observed = max(0.2, 1.0 - noise)
            
            payload = {
                "session_id": session_id,
                "source_node": source,
                "event_type": "QDS_VERIFICATION",
                "quantum_state": f"Eavesdropped|Decohered-State⟩ correlation={observed:.4f}",
                "expected_measurement": 1.0,
                "observed_measurement": round(observed, 6),
                "verification_result": False,
                "signature_hash": generate_sha256(f"{session_id}:{source}"),
                "metadata_json": {"attack": "MITM", "eavesdropper": "Eve-RedTeam-Laptop2"}
            }
            res = requests.post(self.events_url, json=payload)
            data = res.json()
            threat = "CAUGHT (Threat Triggered)" if data.get("threat_detected") else "BYPASS"
            print(f"  [Packet #{i+1}] Session: {session_id} | Result: {threat} | Threat Type: {data.get('threat_type')}")
            time.sleep(0.3)

    def attack_forgery(self, count=1):
        print(f"\n[+] Forging Quantum Digital Signature Hashes ({count} packets)...")
        for i in range(count):
            session_id = f"QDS-ATK-FORGE-{uuid.uuid4().hex[:8].upper()}"
            source = "QNode-Beta-02"
            real_hash = generate_sha256(f"VALID:{session_id}")
            forged_hash = generate_sha256(f"TAMPERED-PAYLOAD-LAPTOP2-{uuid.uuid4().hex}")
            
            payload = {
                "session_id": session_id,
                "source_node": source,
                "event_type": "QDS_VERIFICATION",
                "quantum_state": "QDS-3q|Forged-Signature⟩",
                "expected_measurement": 1.0,
                "observed_measurement": 0.98,
                "verification_result": False,
                "signature_hash": forged_hash,
                "metadata_json": {
                    "attack": "FORGERY",
                    "expected_signature_hash": real_hash,
                    "forgery_indicator": True,
                }
            }
            res = requests.post(self.events_url, json=payload)
            data = res.json()
            print(f"  [Packet #{i+1}] Hash: {forged_hash[:16]}... | SIEM Caught: {data.get('threat_detected')} | Rule: {data.get('threat_type')}")
            time.sleep(0.3)

    def attack_replay(self, count=3):
        print(f"\n[+] Inundating Target with Replayed Old Valid Signatures ({count} packets)...")
        replayed_hash = generate_sha256("REPLAYED-HISTORICAL-SIGNATURE-001")
        for i in range(count):
            session_id = f"QDS-ATK-RPL-{uuid.uuid4().hex[:8].upper()}"
            source = "QNode-Gamma-03"
            
            payload = {
                "session_id": session_id,
                "source_node": source,
                "event_type": "QDS_VERIFICATION",
                "quantum_state": "QDS|Replayed-Token⟩",
                "expected_measurement": 1.0,
                "observed_measurement": 0.99,
                "verification_result": True,
                "signature_hash": replayed_hash,
                "metadata_json": {"attack": "REPLAY", "replayed_hash": replayed_hash}
            }
            res = requests.post(self.events_url, json=payload)
            data = res.json()
            print(f"  [Packet #{i+1}] Replaying Hash {replayed_hash[:16]}... | SIEM Detected: {data.get('threat_detected')}")
            time.sleep(0.4)

    def attack_blinding(self):
        print("\n[+] Injecting Continuous-Wave (CW) High-Power Laser into SPAD Detectors...")
        payload = {
            "session_id": f"QDS-ATK-BLD-{uuid.uuid4().hex[:8].upper()}",
            "source_node": "QNode-Alpha-01",
            "event_type": "QDS_DETECTOR_TELEMETRY",
            "quantum_state": "SPAD|CW-Laser-Saturated-Blinded⟩",
            "expected_measurement": 1.0,
            "observed_measurement": 1.0,
            "verification_result": False,
            "signature_hash": generate_sha256("BLINDED-SPAD"),
            "metadata_json": {
                "detector_blinded": True,
                "optical_power_uW": 180.5,
                "dark_count_rate_hz": 32000.0,
                "deadtime_variance_ns": 0.002,
            }
        }
        res = requests.post(self.events_url, json=payload)
        data = res.json()
        print(f"  [+] Detector Saturated! SIEM Alert Triggered: {data.get('threat_detected')} | Severity: {data.get('severity')}")

    def attack_pns(self):
        print("\n[+] Executing Photon Number Splitting (PNS) on Weak Faint Laser Pulses...")
        payload = {
            "session_id": f"QDS-ATK-PNS-{uuid.uuid4().hex[:8].upper()}",
            "source_node": "QNode-Beta-02",
            "event_type": "QDS_DECOY_ANALYSIS",
            "quantum_state": "PNS-Decoy|Poisson-split⟩",
            "expected_measurement": 1.0,
            "observed_measurement": 0.74,
            "verification_result": False,
            "signature_hash": generate_sha256("PNS-SPLIT"),
            "metadata_json": {
                "pns_attack_detected": True,
                "decoy_gain_ratio": 1.72,
                "multi_photon_excess": 0.48,
            }
        }
    def attack_ddos(self, count=40):
        print(f"\n[+] Launching DDoS / High-Volume Rate Inundation ({count} packets rapid-fire)...")
        blocked_count = 0
        for i in range(count):
            session_id = f"QDS-FLOOD-{uuid.uuid4().hex[:6]}"
            payload = {
                "session_id": session_id,
                "source_node": "QNode-Attacker-Botnet",
                "event_type": "QDS_VERIFICATION",
                "quantum_state": "|Flood⟩",
                "expected_measurement": 1.0,
                "observed_measurement": 0.5,
                "verification_result": False,
                "signature_hash": generate_sha256(f"FLOOD-{i}"),
                "metadata_json": {"attack": "DDOS_FLOOD"}
            }
            try:
                res = requests.post(self.events_url, json=payload, timeout=2)
                if res.status_code == 429:
                    blocked_count += 1
                    print(f"  [Packet #{i+1}] 🛡️ BLOCKED BY RATE LIMITER (HTTP 429 Throttle Active)")
                elif res.status_code == 403:
                    blocked_count += 1
                    print(f"  [Packet #{i+1}] 🚫 DROPPED BY IP FIREWALL / AUTO-BAN (HTTP 403)")
                elif res.status_code == 200:
                    data = res.json()
                    print(f"  [Packet #{i+1}] Ingested -> Threat Detected: {data.get('threat_detected')} | Rule: {data.get('threat_type')}")
            except Exception as e:
                print(f"  [Packet #{i+1}] Connection dropped: {e}")
            time.sleep(0.02)
        print(f"\n[✓] Inundation Finished. SIEM Hardening Blocked {blocked_count}/{count} packets!")

    def attack_sqli_fuzz(self):
        print("\n[+] Injecting Malformed SQLi & Exploit Payloads into SIEM Engine...")
        payload = {
            "session_id": "SES-INJECT'; DROP TABLE security_events;--",
            "source_node": "QNode-Hacker-01",
            "event_type": "QDS_VERIFICATION",
            "quantum_state": "<script>alert('XSS')</script> | bash",
            "expected_measurement": 1.0,
            "observed_measurement": 0.99,
            "signature_hash": "abc",
        }
        res = requests.post(self.events_url, json=payload)
        print(f"  HTTP Status: {res.status_code} (Expected 422 Rejection)")
        if res.status_code == 422:
            print("  [✓] Exploit Blocked by Deep Request Validator!")
        else:
            print("  [!] Response:", res.text)

    def attack_honeypot(self):
        print("\n[+] Probing Hidden / Unauthenticated Legacy Endpoints (Honeypot Trap)...")
        hp_url = f"{self.target_url}/api/security/v1/legacy/events"
        res = requests.post(hp_url, json={"dump_keys": True, "exploit": "legacy_admin_auth"})
        print(f"  HTTP Status: {res.status_code}")
        print("  Decoy Response Received:", res.json())
        print("  [!] Attacker IP is now trapped and blacklisted in SIEM SOC!")


def main():
    parser = argparse.ArgumentParser(description="QDS Red-Team Remote Attack Console")
    parser.add_argument("--target", default="http://10.85.193.131:8005", help="Target SIEM IP:Port (e.g. http://10.85.193.131:8005)")
    args = parser.parse_args()

    attacker = RedTeamAttacker(args.target)

    print("==============================================================")
    print("   🔥 QDS RED TEAM ATTACK CONSOLE (LAPTOP 2 CONTROLLER)")
    print(f"   Target SIEM URL: {args.target}")
    print("==============================================================")

    if not attacker.check_connection():
        print(f"[!] Warning: Cannot reach target SIEM at {args.target}.")
        print("    Make sure Laptop 1 backend is running with: uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print("    And check that both laptops are on the same Wi-Fi network.")
    else:
        print("[✓] Connected successfully to Target SIEM SOC!")

    while True:
        print("\n--------------------------------------------------------------")
        print(" CHOOSE ATTACK VECTOR TO LAUNCH ON TARGET SIEM:")
        print(" [1] Quantum Channel MITM / State Decoherence Attack")
        print(" [2] Signature Hash Forgery Attack")
        print(" [3] Replay Attack Inundation")
        print(" [4] SPAD Detector Blinding / Saturation Attack")
        print(" [5] Photon Number Splitting (PNS) Decoy Attack")
        print(" [6] Rapid-Fire DDoS / Rate Limit Inundation (40 Packets)")
        print(" [7] SQLi & Payload Injection Fuzzing (Validation Test)")
        print(" [8] Reconnaissance on Legacy Honeypot Traps")
        print(" [9] Launch 10-Packet Rapid Mixed Attack Flood")
        print(" [0] Exit")
        print("--------------------------------------------------------------")
        
        choice = input("Enter Choice (0-9): ").strip()

        if choice == "1":
            attacker.attack_mitm(count=3)
        elif choice == "2":
            attacker.attack_forgery(count=3)
        elif choice == "3":
            attacker.attack_replay(count=4)
        elif choice == "4":
            attacker.attack_blinding()
        elif choice == "5":
            attacker.attack_pns()
        elif choice == "6":
            attacker.attack_ddos(count=40)
        elif choice == "7":
            attacker.attack_sqli_fuzz()
        elif choice == "8":
            attacker.attack_honeypot()
        elif choice == "9":
            print("\n[!] Launching 10-Packet Rapid Attack Inundation...")
            attacker.attack_mitm(2)
            attacker.attack_forgery(2)
            attacker.attack_replay(3)
            attacker.attack_blinding()
            attacker.attack_pns()
            print("\n[✓] Inundation Complete! Check Laptop 1 Dashboard for Live Threat Spikes.")
        elif choice == "0":
            print("Exiting Red Team Console. Stay secure!")
            break
        else:
            print("[!] Invalid selection.")


if __name__ == "__main__":
    main()
