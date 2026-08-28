import urllib.request
import json

endpoints = [
    "/api/health",
    "/api/dashboard/summary",
    "/api/dashboard/timeline?range=24h",
    "/api/dashboard/severity-distribution",
    "/api/dashboard/top-offenses",
    "/api/dashboard/recent-incidents",
    "/api/dashboard/log-timeline",
    "/api/events?page=1&page_size=5",
    "/api/threats?page=1&page_size=5",
    "/api/ledger/status",
    "/api/reports/summary?days=30",
    "/api/settings",
    "/api/hardware/status",
]

print("=== QDS SIEM SYSTEM INTEGRATION TESTS ===")
passed = 0
for ep in endpoints:
    url = f"http://127.0.0.1:8000{ep}"
    try:
        resp = urllib.request.urlopen(url)
        data = json.loads(resp.read().decode())
        count = len(data) if isinstance(data, (list, dict)) else 1
        print(f"[PASS] {ep:40} HTTP {resp.status} (records/keys: {count})")
        passed += 1
    except Exception as e:
        print(f"[FAIL] {ep:40} Error: {e}")

# Test Ledger Verification
try:
    req = urllib.request.Request("http://127.0.0.1:8000/api/ledger/verify", method="POST")
    resp = urllib.request.urlopen(req)
    res = json.loads(resp.read().decode())
    print(f"[PASS] {'/api/ledger/verify (POST)':40} Valid: {res.get('valid')} - {res.get('message')}")
    passed += 1
except Exception as e:
    print(f"[FAIL] {'/api/ledger/verify (POST)':40} Error: {e}")

print(f"\nResults: {passed} / {len(endpoints) + 1} tests passed successfully!")
