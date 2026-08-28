"""
QDS Quantum Simulator for SIEM.

Generates realistic quantum digital signature verification events
using either Qiskit (if available) or a numpy-based fallback.

Simulation modes:
- normal: Mostly legitimate events with natural quantum noise
- attack_mix: Blend of normal + attack scenarios
- replay: Replay attack scenarios
- mitm: Man-in-the-middle scenarios
- forgery: Signature forgery scenarios
- impersonation: Identity spoofing scenarios
- anomaly: Statistical anomaly scenarios

Every generated event enters the standard detection pipeline —
no separate fake frontend data.
"""

import uuid
import hashlib
import random
import math
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import numpy as np

logger = logging.getLogger("qds.simulator")

# Try to import Qiskit; fall back to numpy simulation
QISKIT_AVAILABLE = False
try:
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator
    QISKIT_AVAILABLE = True
    logger.info("Qiskit available — using quantum circuit simulation")
except ImportError:
    logger.info("Qiskit not available — using numpy-based quantum simulation")


# Node names for simulation
NODE_POOL = [
    "QNode-Alpha-01", "QNode-Beta-02", "QNode-Gamma-03",
    "QNode-Delta-04", "QNode-Epsilon-05", "QNode-Zeta-06",
    "QNode-Eta-07", "QNode-Theta-08",
]

NODE_IP_MAP = {
    "QNode-Alpha-01": "10.0.1.10",
    "QNode-Beta-02": "10.0.1.20",
    "QNode-Gamma-03": "10.0.1.30",
    "QNode-Delta-04": "10.0.1.40",
    "QNode-Epsilon-05": "198.51.100.55",
    "QNode-Zeta-06": "198.51.100.66",
    "QNode-Eta-07": "203.0.113.77",
    "QNode-Theta-08": "203.0.113.88",
}

ATTACKER_IP_POOL = [
    "185.220.101.5",
    "194.26.29.112",
    "45.142.214.88",
    "103.208.220.14",
    "198.51.100.44",
]


def get_node_ip(source_node: str, is_attack: bool = False) -> str:
    """Resolve IP address for source node or attacker."""
    if is_attack and random.random() < 0.6:
        return random.choice(ATTACKER_IP_POOL)
    return NODE_IP_MAP.get(source_node, "10.0.1.10")


def _generate_signature_hash(data: str) -> str:
    """Generate a deterministic signature hash."""
    return hashlib.sha256(data.encode()).hexdigest()


def _qiskit_bell_measurement() -> tuple:
    """
    Run a Bell state circuit using Qiskit and return measurement results.
    Returns (expected, observed, state_description)
    """
    if not QISKIT_AVAILABLE:
        return _numpy_bell_measurement()

    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])

    simulator = AerSimulator()
    result = simulator.run(qc, shots=1024).result()
    counts = result.get_counts(qc)

    # For a Bell state |Φ+⟩, expect roughly 50% |00⟩ and 50% |11⟩
    total = sum(counts.values())
    correlated = counts.get("00", 0) + counts.get("11", 0)
    expected_correlation = 1.0  # Perfect Bell state
    observed_correlation = correlated / total if total > 0 else 0

    state_desc = f"Bell|Φ+⟩ counts={counts}"

    return expected_correlation, observed_correlation, state_desc


def _numpy_bell_measurement() -> tuple:
    """
    Simulate Bell state measurement using numpy.
    Returns (expected, observed, state_description)
    """
    # Simulate 1024 shots of Bell state measurement
    shots = 1024
    # In ideal Bell state, only |00⟩ and |11⟩ should appear
    # Add small natural noise (as real quantum hardware would)
    noise = np.random.normal(0, 0.02)
    correlation = np.clip(1.0 + noise, 0.9, 1.0)

    # Simulate counts
    correlated_shots = int(correlation * shots)
    counts = {
        "00": correlated_shots // 2,
        "11": correlated_shots - correlated_shots // 2,
        "01": (shots - correlated_shots) // 2,
        "10": shots - correlated_shots - (shots - correlated_shots) // 2,
    }

    expected_correlation = 1.0
    observed_correlation = correlated_shots / shots

    state_desc = f"Bell|Φ+⟩(numpy) counts={counts}"

    return expected_correlation, observed_correlation, state_desc


def _qiskit_qds_verification(tamper: bool = False) -> tuple:
    """
    Simulate QDS verification using quantum circuit.
    Returns (expected, observed, state_description, verification_passed)
    """
    if not QISKIT_AVAILABLE:
        return _numpy_qds_verification(tamper)

    qc = QuantumCircuit(3, 3)
    # Prepare signature state
    qc.h(0)
    qc.cx(0, 1)
    # Verification qubit
    qc.cx(0, 2)

    if tamper:
        # Inject tampering: random rotation
        angle = random.uniform(0.5, math.pi)
        qc.ry(angle, 1)

    qc.measure([0, 1, 2], [0, 1, 2])

    simulator = AerSimulator()
    result = simulator.run(qc, shots=1024).result()
    counts = result.get_counts(qc)

    total = sum(counts.values())
    # Verification: qubits 0 and 2 should be correlated
    verified = sum(v for k, v in counts.items() if k[0] == k[2])
    expected = 1.0
    observed = verified / total if total > 0 else 0

    verification_passed = observed > 0.85
    state_desc = f"QDS-3q counts={counts}"

    return expected, observed, state_desc, verification_passed


def _numpy_qds_verification(tamper: bool = False) -> tuple:
    """Numpy fallback for QDS verification simulation."""
    if tamper:
        noise = random.uniform(0.15, 0.55)
        observed = max(0.3, 1.0 - noise)
        verification_passed = observed > 0.85
    else:
        noise = np.random.normal(0, 0.03)
        observed = np.clip(1.0 + noise, 0.92, 1.0)
        verification_passed = True

    expected = 1.0
    state_desc = f"QDS-3q(numpy) correlation={observed:.4f}"

    return expected, observed, state_desc, verification_passed


class QDSSimulator:
    """Quantum Digital Signature event simulator."""

    def __init__(self):
        self._session_counter = 0
        self._recent_hashes: List[str] = []
        self._recent_sessions: Dict[str, str] = {}  # session_id -> source_node

    def _new_session_id(self) -> str:
        self._session_counter += 1
        return f"QDS-SES-{self._session_counter:06d}"

    def generate_normal_event(self) -> Dict[str, Any]:
        """Generate a normal QDS verification event."""
        session_id = self._new_session_id()
        source = random.choice(NODE_POOL)
        ip = get_node_ip(source, is_attack=False)
        self._recent_sessions[session_id] = source

        expected, observed, state, verified = _numpy_qds_verification(tamper=False)
        if QISKIT_AVAILABLE:
            expected, observed, state, verified = _qiskit_qds_verification(tamper=False)

        sig_data = f"{session_id}:{source}:{datetime.utcnow().isoformat()}"
        sig_hash = _generate_signature_hash(sig_data)
        self._recent_hashes.append(sig_hash)
        if len(self._recent_hashes) > 50:
            self._recent_hashes = self._recent_hashes[-50:]

        return {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow(),
            "session_id": session_id,
            "source_node": source,
            "source_ip": ip,
            "event_type": "QDS_VERIFICATION",
            "quantum_state": state,
            "expected_measurement": round(expected, 6),
            "observed_measurement": round(observed, 6),
            "verification_result": verified,
            "signature_hash": sig_hash,
            "metadata_json": {
                "simulation": True,
                "mode": "normal",
                "source_ip": ip,
                "qiskit_used": QISKIT_AVAILABLE,
            },
        }

    def generate_replay_event(self) -> Dict[str, Any]:
        """Generate a replay attack event (reuses a previous signature hash)."""
        event = self.generate_normal_event()
        ip = get_node_ip(event["source_node"], is_attack=True)
        event["source_ip"] = ip

        if self._recent_hashes and len(self._recent_hashes) > 1:
            # Reuse a recent hash
            replayed_hash = random.choice(self._recent_hashes[:-1])
            event["signature_hash"] = replayed_hash
            event["event_type"] = "QDS_VERIFICATION"
            event["metadata_json"] = {
                "simulation": True,
                "mode": "replay",
                "source_ip": ip,
                "replayed_hash": replayed_hash,
            }

        return event

    def generate_mitm_event(self) -> Dict[str, Any]:
        """Generate a MITM attack event (tampered measurement + verification failure)."""
        session_id = self._new_session_id()
        source = random.choice(NODE_POOL)
        ip = get_node_ip(source, is_attack=True)
        self._recent_sessions[session_id] = source

        expected, observed, state, verified = _numpy_qds_verification(tamper=True)
        if QISKIT_AVAILABLE:
            expected, observed, state, verified = _qiskit_qds_verification(tamper=True)

        sig_data = f"{session_id}:{source}:{datetime.utcnow().isoformat()}"
        sig_hash = _generate_signature_hash(sig_data)

        return {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow(),
            "session_id": session_id,
            "source_node": source,
            "source_ip": ip,
            "event_type": "QDS_VERIFICATION",
            "quantum_state": state,
            "expected_measurement": round(expected, 6),
            "observed_measurement": round(observed, 6),
            "verification_result": False,
            "signature_hash": sig_hash,
            "metadata_json": {
                "simulation": True,
                "mode": "mitm",
                "source_ip": ip,
                "tampered": True,
            },
        }

    def generate_forgery_event(self) -> Dict[str, Any]:
        """Generate a forgery event (signature hash mismatch)."""
        session_id = self._new_session_id()
        source = random.choice(NODE_POOL)
        ip = get_node_ip(source, is_attack=True)

        expected, observed, state, _ = _numpy_qds_verification(tamper=False)

        # Create legitimate hash and a different forged hash
        sig_data = f"{session_id}:{source}:{datetime.utcnow().isoformat()}"
        legitimate_hash = _generate_signature_hash(sig_data)
        forged_hash = _generate_signature_hash(f"FORGED:{uuid.uuid4()}")

        return {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow(),
            "session_id": session_id,
            "source_node": source,
            "source_ip": ip,
            "event_type": "QDS_VERIFICATION",
            "quantum_state": state,
            "expected_measurement": round(expected, 6),
            "observed_measurement": round(observed, 6),
            "verification_result": False,
            "signature_hash": forged_hash,
            "metadata_json": {
                "simulation": True,
                "mode": "forgery",
                "source_ip": ip,
                "expected_signature_hash": legitimate_hash,
                "forgery_indicator": True,
            },
        }

    def generate_impersonation_event(self) -> Dict[str, Any]:
        """Generate an impersonation event (session hijack from different source)."""
        # Pick an existing session and use a different source
        if self._recent_sessions:
            session_id = random.choice(list(self._recent_sessions.keys()))
            original_source = self._recent_sessions[session_id]
            # Use a different source node
            other_sources = [n for n in NODE_POOL if n != original_source]
            source = random.choice(other_sources) if other_sources else NODE_POOL[0]
        else:
            session_id = self._new_session_id()
            source = random.choice(NODE_POOL)

        ip = get_node_ip(source, is_attack=True)
        expected, observed, state, _ = _numpy_qds_verification(tamper=True)

        sig_data = f"{session_id}:{source}:{datetime.utcnow().isoformat()}"
        sig_hash = _generate_signature_hash(sig_data)

        return {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow(),
            "session_id": session_id,
            "source_node": source,
            "source_ip": ip,
            "event_type": "QDS_VERIFICATION",
            "quantum_state": state,
            "expected_measurement": round(expected, 6),
            "observed_measurement": round(observed, 6),
            "verification_result": False,
            "signature_hash": sig_hash,
            "metadata_json": {
                "simulation": True,
                "mode": "impersonation",
                "source_ip": ip,
                "impersonated_session": session_id,
            },
        }

    def generate_anomaly_event(self) -> Dict[str, Any]:
        """Generate an anomalous quantum measurement event."""
        session_id = self._new_session_id()
        source = random.choice(NODE_POOL)
        ip = get_node_ip(source, is_attack=True)

        expected = 1.0
        # Generate highly anomalous measurement
        observed = random.uniform(0.1, 0.6)

        state = f"ANOMALY correlation={observed:.4f}"

        sig_data = f"{session_id}:{source}:{datetime.utcnow().isoformat()}"
        sig_hash = _generate_signature_hash(sig_data)

        return {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow(),
            "session_id": session_id,
            "source_node": source,
            "source_ip": ip,
            "event_type": "QDS_MEASUREMENT",
            "quantum_state": state,
            "expected_measurement": round(expected, 6),
            "observed_measurement": round(observed, 6),
            "verification_result": observed > 0.85,
            "signature_hash": sig_hash,
            "metadata_json": {
                "simulation": True,
                "mode": "anomaly",
                "source_ip": ip,
                "anomalous_correlation": round(observed, 6),
            },
        }

    def generate_pns_event(self) -> Dict[str, Any]:
        """Generate a Photon Number Splitting (PNS) attack event."""
        session_id = self._new_session_id()
        source = random.choice(NODE_POOL)
        ip = get_node_ip(source, is_attack=True)

        expected = 1.0
        # PNS splits photons, resulting in slight deviation + decoy state gain mismatch
        observed = random.uniform(0.72, 0.84)
        state = f"PNS-Decoy|Poisson-split⟩ gain={observed:.4f}"
        sig_data = f"{session_id}:{source}:{datetime.utcnow().isoformat()}"
        sig_hash = _generate_signature_hash(sig_data)

        return {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow(),
            "session_id": session_id,
            "source_node": source,
            "source_ip": ip,
            "event_type": "QDS_DECOY_ANALYSIS",
            "quantum_state": state,
            "expected_measurement": round(expected, 6),
            "observed_measurement": round(observed, 6),
            "verification_result": False,
            "signature_hash": sig_hash,
            "metadata_json": {
                "simulation": True,
                "mode": "pns",
                "source_ip": ip,
                "pns_attack_detected": True,
                "decoy_gain_ratio": round(random.uniform(1.35, 1.85), 4),
                "expected_decoy_gain_ratio": 1.0,
                "multi_photon_excess": round(random.uniform(0.25, 0.55), 4),
            },
        }

    def generate_blinding_event(self) -> Dict[str, Any]:
        """Generate a Detector Blinding & Saturation attack event."""
        session_id = self._new_session_id()
        source = random.choice(NODE_POOL)
        ip = get_node_ip(source, is_attack=True)

        expected = 1.0
        # Saturated SPAD gives 100% deterministic (fake) clicks
        observed = 1.0
        state = "SPAD|CW-Laser-Saturated-Blinded⟩"
        sig_data = f"{session_id}:{source}:{datetime.utcnow().isoformat()}"
        sig_hash = _generate_signature_hash(sig_data)

        return {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow(),
            "session_id": session_id,
            "source_node": source,
            "source_ip": ip,
            "event_type": "QDS_DETECTOR_TELEMETRY",
            "quantum_state": state,
            "expected_measurement": round(expected, 6),
            "observed_measurement": round(observed, 6),
            "verification_result": False,
            "signature_hash": sig_hash,
            "metadata_json": {
                "simulation": True,
                "mode": "blinding",
                "source_ip": ip,
                "detector_blinded": True,
                "optical_power_uW": round(random.uniform(75.0, 250.0), 2),
                "dark_count_rate_hz": round(random.uniform(8000.0, 45000.0), 1),
                "deadtime_variance_ns": round(random.uniform(0.001, 0.08), 4),
            },
        }

    def generate_repudiation_event(self) -> Dict[str, Any]:
        """Generate a Multi-Party Repudiation / Symmetrization Dispute event."""
        session_id = self._new_session_id()
        source = random.choice(NODE_POOL)
        ip = get_node_ip(source, is_attack=True)

        expected, observed, state, _ = _numpy_qds_verification(tamper=False)
        sig_data = f"{session_id}:{source}:{datetime.utcnow().isoformat()}"
        sig_hash = _generate_signature_hash(sig_data)

        return {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow(),
            "session_id": session_id,
            "source_node": source,
            "source_ip": ip,
            "event_type": "QDS_MULTI_PARTY_SYMMETRIZATION",
            "quantum_state": f"3Party-QDS|Dispute(Bob!=Charlie)⟩",
            "expected_measurement": round(expected, 6),
            "observed_measurement": round(observed, 6),
            "verification_result": False,
            "signature_hash": sig_hash,
            "metadata_json": {
                "simulation": True,
                "mode": "repudiation",
                "source_ip": ip,
                "repudiation_dispute": True,
                "symmetrization_mismatch": True,
                "bob_verification": True,
                "charlie_verification": False,
                "dispute_reason": "Alice transmitted orthogonal basis subsets to Bob and Charlie",
            },
        }

    def generate_evasion_event(self) -> Dict[str, Any]:
        """Generate a Low-and-Slow Sub-threshold Evasion attack event."""
        session_id = self._new_session_id()
        source = random.choice(NODE_POOL)
        ip = get_node_ip(source, is_attack=True)

        expected = 1.0
        # Eavesdropper causes small sub-threshold deviation (0.12 - 0.22)
        observed = round(random.uniform(0.78, 0.88), 4)
        state = f"QDS|SubThreshold-Intercept⟩ dev={round(1.0 - observed, 4)}"
        sig_data = f"{session_id}:{source}:{datetime.utcnow().isoformat()}"
        sig_hash = _generate_signature_hash(sig_data)

        return {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow(),
            "session_id": session_id,
            "source_node": source,
            "source_ip": ip,
            "event_type": "QDS_VERIFICATION",
            "quantum_state": state,
            "expected_measurement": round(expected, 6),
            "observed_measurement": round(observed, 6),
            "verification_result": False,
            "signature_hash": sig_hash,
            "metadata_json": {
                "simulation": True,
                "mode": "evasion",
                "source_ip": ip,
                "low_slow_evasion": True,
                "sub_threshold_interception_rate": round(random.uniform(0.02, 0.05), 4),
            },
        }


    def generate_events(
        self,
        mode: str = "normal",
        count: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Generate a batch of events based on the specified mode.
        """
        events = []

        if mode == "normal":
            for _ in range(count):
                if random.random() < 0.85:
                    events.append(self.generate_normal_event())
                else:
                    events.append(self.generate_anomaly_event())

        elif mode == "attack_mix":
            attack_generators = [
                self.generate_replay_event,
                self.generate_mitm_event,
                self.generate_forgery_event,
                self.generate_impersonation_event,
                self.generate_anomaly_event,
                self.generate_pns_event,
                self.generate_blinding_event,
                self.generate_repudiation_event,
                self.generate_evasion_event,
            ]
            for _ in range(count):
                if random.random() < 0.30:
                    events.append(self.generate_normal_event())
                else:
                    generator = random.choice(attack_generators)
                    events.append(generator())

        elif mode == "replay":
            for i in range(count):
                if i < max(1, count // 3):
                    events.append(self.generate_normal_event())
                else:
                    events.append(self.generate_replay_event())

        elif mode == "mitm":
            for _ in range(count):
                events.append(self.generate_mitm_event())

        elif mode == "forgery":
            for _ in range(count):
                events.append(self.generate_forgery_event())

        elif mode == "impersonation":
            for i in range(count):
                if i < max(1, count // 4):
                    events.append(self.generate_normal_event())
                else:
                    events.append(self.generate_impersonation_event())

        elif mode == "anomaly":
            for _ in range(count):
                events.append(self.generate_anomaly_event())

        elif mode == "pns":
            for _ in range(count):
                events.append(self.generate_pns_event())

        elif mode == "blinding":
            for _ in range(count):
                events.append(self.generate_blinding_event())

        elif mode == "repudiation":
            for _ in range(count):
                events.append(self.generate_repudiation_event())

        elif mode == "evasion":
            for _ in range(count):
                events.append(self.generate_evasion_event())

        else:
            for _ in range(count):
                events.append(self.generate_normal_event())

        return events


# Singleton
qds_simulator = QDSSimulator()
