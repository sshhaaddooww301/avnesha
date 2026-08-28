"""
Hardware Link Manager for QDS SIEM.

Manages physical link state, live optical telemetry statistics,
and hardware interfaces (ETSI 014, Serial COM, TCP Raw Sockets).
Includes dynamic heartbeat detection: nodes only show CONNECTED if active
telemetry was received within the heartbeat window (15s).
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

logger = logging.getLogger("qds.hardware")

HEARTBEAT_TIMEOUT_SECONDS = 15.0


class HardwareNodeStatus(BaseModel):
    node_id: str
    label: str
    status: str  # "CONNECTED", "DISCONNECTED", "STANDBY", "DEGRADED"
    interface_type: str  # "ETSI_014", "SERIAL_COM", "TCP_SOCKET"
    wavelength_nm: float
    current_qber: float
    optical_power_uW: float
    dark_count_rate_hz: float
    deadtime_ns: float
    fiber_length_km: float
    total_keys_sifted: int
    last_heartbeat: Optional[datetime]


class HardwareManager:
    """Singleton manager tracking physical quantum link telemetry."""

    def __init__(self):
        self.mode = "STANDBY"  # "STANDBY", "LIVE_STREAM", "PHYSICAL_LINK"
        self.active_nodes: Dict[str, Dict[str, Any]] = {
            "QNODE-ALPHA-HQ": {
                "node_id": "QNODE-ALPHA-HQ",
                "label": "Primary Base Transceiver (Alice HQ)",
                "interface_type": "ETSI_014",
                "wavelength_nm": 1550.12,
                "current_qber": 0.0,
                "optical_power_uW": 0.0,
                "dark_count_rate_hz": 0.0,
                "deadtime_ns": 0.0,
                "fiber_length_km": 42.5,
                "total_keys_sifted": 0,
                "last_heartbeat": None,
            },
            "QNODE-BETA-BRANCH": {
                "node_id": "QNODE-BETA-BRANCH",
                "label": "Branch Receiver Node (Bob)",
                "interface_type": "ETSI_014",
                "wavelength_nm": 1550.12,
                "current_qber": 0.0,
                "optical_power_uW": 0.0,
                "dark_count_rate_hz": 0.0,
                "deadtime_ns": 0.0,
                "fiber_length_km": 42.5,
                "total_keys_sifted": 0,
                "last_heartbeat": None,
            },
            "QNODE-GAMMA-VERIFIER": {
                "node_id": "QNODE-GAMMA-VERIFIER",
                "label": "3-Party Verifier (Charlie)",
                "interface_type": "ETSI_014",
                "wavelength_nm": 1550.52,
                "current_qber": 0.0,
                "optical_power_uW": 0.0,
                "dark_count_rate_hz": 0.0,
                "deadtime_ns": 0.0,
                "fiber_length_km": 68.0,
                "total_keys_sifted": 0,
                "last_heartbeat": None,
            }
        }
        self.serial_config = {
            "port": "COM3",
            "baudrate": 115200,
            "connected": False,
            "device_name": "SPAD_FPGA_TimeTagger_v2",
        }

    def _is_node_alive(self, node: Dict[str, Any]) -> bool:
        """Check if node received a heartbeat packet recently."""
        last = node.get("last_heartbeat")
        if not last:
            return False
        if isinstance(last, str):
            last = datetime.fromisoformat(last)
        return (datetime.utcnow() - last).total_seconds() < HEARTBEAT_TIMEOUT_SECONDS

    def get_system_telemetry(self) -> Dict[str, Any]:
        """Returns physical layer optical telemetry with live heartbeat statuses."""
        nodes_out = []
        live_count = 0
        qbers = []
        powers = []
        total_keys = 0

        for n in self.active_nodes.values():
            alive = self._is_node_alive(n)
            status = "CONNECTED" if alive else "DISCONNECTED"
            if alive:
                live_count += 1
                qbers.append(n.get("current_qber", 0.0))
                powers.append(n.get("optical_power_uW", 0.0))
            total_keys += n.get("total_keys_sifted", 0)

            nodes_out.append({
                **n,
                "status": status,
                "is_live": alive,
                "last_heartbeat": n["last_heartbeat"].isoformat() if n.get("last_heartbeat") else None,
            })

        avg_qber = sum(qbers) / len(qbers) if qbers else 0.0
        avg_power = sum(powers) / len(powers) if powers else 0.0

        current_mode = "LIVE_STREAM" if live_count > 0 else "STANDBY (AWAITING PHYSICAL HARDWARE)"

        return {
            "mode": current_mode,
            "is_hardware_live": live_count > 0,
            "standard_compliance": ["ETSI GS QKD 014", "ETSI GS QKD 004", "ITU-T Y.3800"],
            "nodes_count": len(self.active_nodes),
            "healthy_links": live_count,
            "average_qber": round(avg_qber, 4),
            "average_optical_power_uW": round(avg_power, 2),
            "total_sifted_bits": total_keys,
            "serial_interface": self.serial_config,
            "nodes": nodes_out,
        }

    def update_node_telemetry(self, node_id: str, telemetry_dict: Dict[str, Any]):
        """Updates live physical parameters for a specific hardware node upon receiving a packet."""
        now = datetime.utcnow()
        if node_id in self.active_nodes:
            node = self.active_nodes[node_id]
            node["current_qber"] = telemetry_dict.get("qber", node.get("current_qber", 0.02))
            node["optical_power_uW"] = telemetry_dict.get("optical_power_uW", node.get("optical_power_uW", 15.0))
            node["dark_count_rate_hz"] = telemetry_dict.get("dark_count_rate_hz", node.get("dark_count_rate_hz", 120.0))
            node["deadtime_ns"] = telemetry_dict.get("deadtime_variance_ns", node.get("deadtime_ns", 8.5))
            node["total_keys_sifted"] = node.get("total_keys_sifted", 0) + telemetry_dict.get("sifted_bits", 1024)
            node["last_heartbeat"] = now
        else:
            self.active_nodes[node_id] = {
                "node_id": node_id,
                "label": f"External Optical Node ({node_id})",
                "interface_type": "ETSI_014",
                "wavelength_nm": telemetry_dict.get("wavelength_nm", 1550.12),
                "current_qber": telemetry_dict.get("qber", 0.02),
                "optical_power_uW": telemetry_dict.get("optical_power_uW", 15.0),
                "dark_count_rate_hz": telemetry_dict.get("dark_count_rate_hz", 120.0),
                "deadtime_ns": telemetry_dict.get("deadtime_variance_ns", 8.5),
                "fiber_length_km": telemetry_dict.get("fiber_length_km", 20.0),
                "total_keys_sifted": telemetry_dict.get("sifted_bits", 1024),
                "last_heartbeat": now,
            }


hardware_manager = HardwareManager()
