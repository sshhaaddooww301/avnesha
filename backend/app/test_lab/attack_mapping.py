"""
Attack Type Mapping for QDS Test Lab.

Canonical single source of truth mapping frontend labels/keys to backend simulator attack generators.
"""

ATTACK_TYPE_MAP = {
    "normal": "normal",
    "replay": "replay",
    "manipulation": "mitm",
    "mitm": "mitm",
    "forgery": "forgery",
    "impersonation": "impersonation",
    "measurement_anomaly": "anomaly",
    "anomaly": "anomaly",
    "pns": "pns",
    "blinding": "blinding",
    "repudiation": "repudiation",
    "evasion": "evasion",
}

ATTACK_DISPLAY_NAMES = {
    "normal": "Normal QDS Signature Traffic",
    "replay": "Replay Attack Inundation",
    "manipulation": "MITM / Channel State Tampering",
    "forgery": "Signature Hash Forgery",
    "impersonation": "Identity / Node Impersonation",
    "measurement_anomaly": "Quantum Measurement Anomaly",
    "pns": "Photon Number Splitting (PNS)",
    "blinding": "Detector Blinding / Trojan-Horse Attack",
    "repudiation": "Multi-Party Repudiation Dispute",
    "evasion": "Low-and-Slow Sub-Threshold Evasion",
}

ATTACK_DESCRIPTIONS = {
    "normal": "Legitimate QDS quantum signature verifications with baseline quantum noise.",
    "replay": "Reusing previously validated signature hashes within rapid temporal sliding windows (QDS-RPL-001).",
    "manipulation": "Quantum channel eavesdropping resulting in state decoherence and elevated measurement deviation (QDS-MITM-001).",
    "forgery": "Cryptographic payload tampering where signature hash fails verification check (QDS-FRG-001).",
    "impersonation": "Unauthorized origin node hijacking valid session credentials across endpoints (QDS-IMP-001).",
    "measurement_anomaly": "Bell-state correlation statistical outliers violating normal quantum distributions (QDS-ANM-001).",
    "pns": "Eavesdropper splitting multi-photon pulses detected via decoy-state statistics and gain anomalies (QDS-PNS-001).",
    "blinding": "Continuous optical power injection forcing SPAD detectors into linear saturated regime (QDS-BLD-001).",
    "repudiation": "Dishonest sender transmitting differing quantum states to Bob and Charlie causing cross-verification dispute (QDS-RPD-001).",
    "evasion": "Subtle low-intensity eavesdropping detected via multi-window CUSUM baseline drift analysis (QDS-EVS-001).",
}
