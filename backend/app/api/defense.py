"""
Quantum Active Defense & SOAR Management API.

Allows SOC operators to:
- Monitor live Quarantined Nodes & Blocked Attacks
- Release nodes from isolation
- Toggle between ACTIVE_ENFORCING and AUDIT_ONLY modes
- Clear blacklists
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.engine.soar import quantum_ips

router = APIRouter(prefix="/api/defense", tags=["Active Defense & IPS"])


class ReleaseNodeRequest(BaseModel):
    node_id: str


class ToggleModeRequest(BaseModel):
    enforcing: bool


@router.get("/status")
async def get_defense_status():
    """Return active IPS defense posture, quarantined nodes, and blocked stats."""
    return quantum_ips.get_status()


@router.post("/quarantine/release")
async def release_node_from_quarantine(request: ReleaseNodeRequest):
    """Release a quarantined node back into normal operation."""
    success = quantum_ips.release_node(request.node_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Node '{request.node_id}' is not in active quarantine."
        )
    return {
        "status": "success",
        "message": f"Node '{request.node_id}' successfully unquarantined.",
        "active_quarantined_count": len(quantum_ips.quarantined_nodes),
    }


@router.post("/toggle-mode")
async def toggle_defense_mode(request: ToggleModeRequest):
    """Toggle between ACTIVE_ENFORCING (blocking) and AUDIT_ONLY modes."""
    quantum_ips.enforcing_mode = request.enforcing
    return {
        "status": "success",
        "enforcing_mode": quantum_ips.enforcing_mode,
        "message": f"IPS Mode set to {'ACTIVE_ENFORCING (Drop & Quarantine)' if quantum_ips.enforcing_mode else 'AUDIT_ONLY (Monitoring Only)'}.",
    }


@router.post("/clear-all")
async def clear_all_quarantine():
    """Reset all quarantine and blacklists."""
    quantum_ips.clear_all()
    return {
        "status": "success",
        "message": "All quarantine lists, revoked sessions, and tainted signature hashes have been cleared.",
    }
