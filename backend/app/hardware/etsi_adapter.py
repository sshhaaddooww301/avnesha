"""
ETSI GS QKD 014 / 004 Standard Hardware Telemetry Adapter.

Implements industry-standard Key Delivery & Physical Layer Ingestion interfaces
for physical Quantum Digital Signature & QKD optical nodes (e.g., ID Quantique,
Toshiba QKD, QuNu Labs, ISRO/DRDO Quantum Transceivers).
"""

import hashlib
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field


class ETSI014TelemetryPayload(BaseModel):
    """
    Standard ETSI GS QKD 014 Telemetry & Key Sync Ingestion Model.
    """
    node_id: str = Field(..., description="Unique hardware transceiver node identifier (e.g. QNODE-ALICE-1550)")
    session_id: str = Field(..., description="QDS Session / Transaction UUID")
    target_node_id: str = Field(..., description="Destination receiver node (e.g. QNODE-BOB-1550)")
    key_stream_id: str = Field(..., description="Quantum distributed entropy stream ID")
    sifted_key_bits: int = Field(..., ge=1, description="Number of sifted quantum bits")
    quantum_bit_error_rate: float = Field(..., ge=0.0, le=1.0, description="Measured QBER (e.g. 0.024 = 2.4%)")
    optical_power_uW: float = Field(default=15.0, ge=0.0, description="Laser / Channel optical power in microWatts")
    dark_count_rate_hz: float = Field(default=150.0, ge=0.0, description="SPAD single-photon detector dark count in Hz")
    deadtime_variance_ns: float = Field(default=8.5, ge=0.0, description="Detector dead-time variance in nanoseconds")
    decoy_gain_ratio: float = Field(default=1.0, ge=0.0, description="Decoy state to signal state gain ratio Y_decoy / Y_signal")
    fiber_attenuation_db_km: float = Field(default=0.20, ge=0.0, description="Optical fiber loss in dB/km (Standard telecom is ~0.2 dB/km @ 1550nm)")
    signature_payload_hex: Optional[str] = Field(None, description="Signed document / message hex digest")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


def normalize_etsi_to_qds_event(telemetry: ETSI014TelemetryPayload) -> Dict[str, Any]:
    """
    Translates raw ETSI 014 physical hardware telemetry into a normalized QDS SIEM Security Event.
    """
    qber = telemetry.quantum_bit_error_rate
    # In ideal Bell / QDS states, correlation = 1 - QBER
    expected_correlation = 1.0
    observed_correlation = max(0.0, min(1.0, 1.0 - qber))
    
    # Calculate verification result: standard QDS link passes if QBER < 11% (Shor-Preskill threshold)
    verification_passed = qber < 0.11
    
    # Generate deterministic signature hash
    sig_raw = f"{telemetry.session_id}:{telemetry.node_id}:{telemetry.target_node_id}:{telemetry.key_stream_id}"
    signature_hash = telemetry.signature_payload_hex or hashlib.sha256(sig_raw.encode()).hexdigest()
    
    # Physical anomaly heuristic flags
    is_blinded = telemetry.optical_power_uW > 60.0 or telemetry.dark_count_rate_hz > 5000.0 or telemetry.deadtime_variance_ns < 0.5
    is_pns = abs(telemetry.decoy_gain_ratio - 1.0) > 0.15
    is_evasion = 0.05 < qber <= 0.10  # Sub-threshold QBER keeping under critical cutoff
    
    event_data = {
        "event_id": str(uuid.uuid4()),
        "timestamp": telemetry.timestamp or datetime.utcnow(),
        "session_id": telemetry.session_id,
        "source_node": telemetry.node_id,
        "event_type": "QDS_HARDWARE_ETSI014",
        "quantum_state": f"Physical-SPAD|1550nm-DWDM⟩ QBER={qber*100:.2f}%",
        "expected_measurement": round(expected_correlation, 6),
        "observed_measurement": round(observed_correlation, 6),
        "verification_result": verification_passed and not is_blinded,
        "signature_hash": signature_hash,
        "metadata_json": {
            "hardware_mode": "PHYSICAL_ETSI_014",
            "node_id": telemetry.node_id,
            "target_node_id": telemetry.target_node_id,
            "key_stream_id": telemetry.key_stream_id,
            "sifted_bits": telemetry.sifted_key_bits,
            "qber": round(qber, 6),
            "optical_power_uW": round(telemetry.optical_power_uW, 2),
            "dark_count_rate_hz": round(telemetry.dark_count_rate_hz, 1),
            "deadtime_variance_ns": round(telemetry.deadtime_variance_ns, 4),
            "decoy_gain_ratio": round(telemetry.decoy_gain_ratio, 4),
            "fiber_attenuation_db_km": round(telemetry.fiber_attenuation_db_km, 3),
            "detector_blinded": is_blinded,
            "pns_attack_detected": is_pns,
            "low_slow_evasion": is_evasion,
        }
    }
    return event_data
