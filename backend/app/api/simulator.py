"""
Quantum Simulator API endpoints.

Triggers real simulation runs that feed directly into the detection pipeline.
"""

import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session_factory
from app.schemas import SimulatorRequest, SimulatorResponse
from app.quantum.simulator import qds_simulator, QISKIT_AVAILABLE
from app.engine.detection import process_event

router = APIRouter(prefix="/api/simulator", tags=["Simulator"])


async def run_simulation_batch(mode: str, count: int, interval_ms: int):
    """Background task to simulate events with realistic time gaps."""
    events = qds_simulator.generate_events(mode=mode, count=count)
    for ev_data in events:
        async with async_session_factory() as db:
            try:
                await process_event(db, ev_data)
            except Exception as e:
                print(f"Simulation event processing error: {e}")
        if interval_ms > 0:
            await asyncio.sleep(interval_ms / 1000.0)


@router.post("/run", response_model=SimulatorResponse)
async def trigger_simulation(
    request: SimulatorRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Run quantum simulation events.
    If count <= 10, runs immediately and returns accurate count of events and threats.
    If count > 10, executes remaining in background task to avoid HTTP timeout.
    """
    events = qds_simulator.generate_events(mode=request.mode.value, count=request.count)
    
    events_generated = 0
    threats_detected = 0

    if request.count <= 10:
        for ev_data in events:
            ev, threat = await process_event(db, ev_data)
            events_generated += 1
            if threat:
                threats_detected += 1
        
        return SimulatorResponse(
            status="completed",
            events_generated=events_generated,
            threats_detected=threats_detected,
            message=f"Successfully generated {events_generated} events via {'Qiskit' if QISKIT_AVAILABLE else 'QDS Quantum Engine'}. {threats_detected} threats identified.",
        )
    else:
        # Process first 5 synchronously so immediate feedback is given
        for ev_data in events[:5]:
            ev, threat = await process_event(db, ev_data)
            events_generated += 1
            if threat:
                threats_detected += 1

        # Queue the rest in background
        background_tasks.add_task(
            run_simulation_batch,
            mode=request.mode.value,
            count=request.count - 5,
            interval_ms=request.interval_ms,
        )

        return SimulatorResponse(
            status="running",
            events_generated=request.count,
            threats_detected=threats_detected,
            message=f"Queued simulation of {request.count} events in background with {request.interval_ms}ms intervals.",
        )


@router.get("/status")
async def get_simulator_status():
    """Get quantum simulator engine capabilities and status."""
    return {
        "engine": "Qiskit Quantum Circuit Simulator" if QISKIT_AVAILABLE else "High-Fidelity Quantum State Engine",
        "qiskit_installed": QISKIT_AVAILABLE,
        "available_modes": [
            {"id": "normal", "name": "Normal QDS Traffic", "description": "Legitimate QDS signature exchanges with natural noise"},
            {"id": "attack_mix", "name": "Mixed Attack Scenario", "description": "Realistic attack blend including MITM, replay, forgery, impersonation"},
            {"id": "replay", "name": "Replay Attack Inundation", "description": "Signatures reused across rapid time windows"},
            {"id": "mitm", "name": "Quantum Channel MITM / Eavesdropping", "description": "Quantum state decoherence & measurement manipulation"},
            {"id": "forgery", "name": "Digital Signature Forgery", "description": "Cryptographic signature hash tampering"},
            {"id": "impersonation", "name": "Node / Identity Impersonation", "description": "Unauthorized node hijacking valid session credentials"},
            {"id": "anomaly", "name": "Quantum State Deviation Anomaly", "description": "Abnormal Bell-state correlations and statistical outliers"},
        ],
        "node_pool_size": 8,
    }
