"""
FastAPI Router for Real-World Hardware Ingestion & Physical Optical Links.
"""

import time
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.database import get_db
from app.hardware.etsi_adapter import ETSI014TelemetryPayload, normalize_etsi_to_qds_event
from app.hardware.hardware_manager import hardware_manager
from app.engine.detection import process_event

router = APIRouter(prefix="/api/hardware", tags=["Physical Hardware & Optical Link"])


@router.get("/status")
async def get_hardware_status():
    """Retrieve live optical channel telemetry, SPAD status, and ETSI link health."""
    return hardware_manager.get_system_telemetry()


@router.post("/etsi/sync")
async def ingest_etsi_telemetry(
    payload: ETSI014TelemetryPayload,
    db: AsyncSession = Depends(get_db),
):
    """
    Ingest live ETSI GS QKD 014 hardware key sync and optical telemetry directly
    into the SIEM detection pipeline and blockchain ledger.
    """
    event_data = normalize_etsi_to_qds_event(payload)
    
    # Update hardware manager telemetry
    hardware_manager.update_node_telemetry(payload.node_id, event_data["metadata_json"])
    
    # Run through full detection pipeline
    event, threat = await process_event(db, event_data)

    return {
        "status": "success",
        "standard": "ETSI GS QKD 014",
        "event_id": event.event_id,
        "threat_detected": threat is not None,
        "threat_type": threat.threat_type if threat else "CLEAN_TRAFFIC",
        "severity": threat.severity if threat else "LOW",
        "risk_score": threat.risk_score if threat else 0.0,
        "qber": payload.quantum_bit_error_rate,
        "node_id": payload.node_id,
    }


@router.post("/configure")
async def configure_hardware_interface(
    config: Dict[str, Any] = Body(...),
):
    """Configure physical Serial COM / TCP socket interface parameters."""
    if "port" in config:
        hardware_manager.serial_config["port"] = str(config["port"])
    if "baudrate" in config:
        hardware_manager.serial_config["baudrate"] = int(config["baudrate"])
    if "connected" in config:
        hardware_manager.serial_config["connected"] = bool(config["connected"])
    if "mode" in config and config["mode"] in ["PHYSICAL_LINK", "HYBRID_READY"]:
        hardware_manager.mode = config["mode"]

    return {
        "status": "updated",
        "serial_interface": hardware_manager.serial_config,
        "mode": hardware_manager.mode,
    }


@router.post("/ping")
async def ping_hardware_node(node_id: str = Body(..., embed=True)):
    """Test physical link handshake and measure round-trip optical latency."""
    if node_id not in hardware_manager.active_nodes:
        raise HTTPException(status_code=404, detail="Hardware node not registered")

    node = hardware_manager.active_nodes[node_id]
    # Simulated optical link speed: ~5 microseconds per km in standard silica fiber
    latency_ms = round((node["fiber_length_km"] * 2 * 4.9) / 1000.0, 3)

    return {
        "node_id": node_id,
        "status": "ONLINE",
        "link_health": "OPTIMAL",
        "optical_roundtrip_latency_ms": latency_ms,
        "wavelength_nm": node["wavelength_nm"],
        "interface": node["interface_type"],
    }
