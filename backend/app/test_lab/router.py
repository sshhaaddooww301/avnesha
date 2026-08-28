"""
FastAPI Router for QDS Attack / Test Lab Endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional, List

from app.database import get_db
from app.models import TestRun, TestResult
from app.test_lab.schemas import (
    TestLabRunRequest,
    TestLabRunResponse,
    TestRunSummary,
    TestResultDetail,
    TestRunMetrics,
    TestRunDetailResponse,
)
from app.test_lab.controller import test_lab_controller
from app.test_lab.attack_mapping import (
    ATTACK_TYPE_MAP,
    ATTACK_DISPLAY_NAMES,
    ATTACK_DESCRIPTIONS,
)

router = APIRouter(prefix="/api/test-lab", tags=["Attack Test Lab"])


@router.get("/scenarios")
async def get_test_scenarios():
    """Get list of supported attack scenarios and their descriptions."""
    rule_map = {
        "normal": "BASELINE",
        "replay": "QDS-RPL-001",
        "manipulation": "QDS-MITM-001",
        "forgery": "QDS-FRG-001",
        "impersonation": "QDS-IMP-001",
        "measurement_anomaly": "QDS-ANM-001",
        "pns": "QDS-PNS-001",
        "blinding": "QDS-BLD-001",
        "repudiation": "QDS-RPD-001",
        "evasion": "QDS-EVS-001",
    }
    all_keys = [
        "normal", "replay", "manipulation", "forgery",
        "impersonation", "measurement_anomaly", "pns",
        "blinding", "repudiation", "evasion"
    ]
    return [
        {
            "id": key,
            "name": ATTACK_DISPLAY_NAMES.get(key, key.title()),
            "description": ATTACK_DESCRIPTIONS.get(key, ""),
            "detection_rule": rule_map.get(key, "CUSTOM"),
        }
        for key in all_keys
    ]


@router.post("/run", response_model=TestLabRunResponse)
async def run_attack_test(
    request: TestLabRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Launch a controlled QDS attack simulation session.
    Simulations run through the production detection engine and persist results to PostgreSQL.
    """
    attack_val = request.attack_type.value
    if attack_val not in ATTACK_TYPE_MAP:
        raise HTTPException(status_code=400, detail=f"Unsupported attack scenario: {attack_val}")

    params = {
        "attack_intensity": request.attack_intensity,
        "replay_window": request.replay_window,
        "measurement_perturbation": request.measurement_perturbation,
    }

    # Create test session record
    test_run = await test_lab_controller.create_test_session(
        db=db,
        attack_type=attack_val,
        runs=request.runs,
        params=params,
    )

    # Launch execution in background task so UI gets immediate test_id and listens to WS
    background_tasks.add_task(
        test_lab_controller.execute_test_session,
        test_id=test_run.test_id,
        attack_type=attack_val,
        runs=request.runs,
        params=params,
    )

    return TestLabRunResponse(
        test_id=test_run.test_id,
        status="running",
        attack_type=attack_val,
        runs=request.runs,
        message=f"Initialized {ATTACK_DISPLAY_NAMES.get(attack_val, attack_val)} test with {request.runs} iterations.",
    )


@router.get("/history")
async def get_test_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    attack_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve paginated historical test runs."""
    query = select(TestRun)
    count_query = select(func.count(TestRun.id))

    if attack_type:
        query = query.where(TestRun.attack_type == attack_type)
        count_query = count_query.where(TestRun.attack_type == attack_type)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(desc(TestRun.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return {
        "items": [
            {
                "id": r.id,
                "test_id": r.test_id,
                "attack_type": r.attack_type,
                "attack_name": ATTACK_DISPLAY_NAMES.get(r.attack_type, r.attack_type.title()),
                "total_runs": r.total_runs,
                "status": r.status,
                "params": r.params,
                "metrics": r.metrics,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/{test_id}")
async def get_test_run(
    test_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get full details of a specific test run including computed metrics."""
    result = await db.execute(select(TestRun).where(TestRun.test_id == test_id))
    run_obj = result.scalar_one_or_none()
    if not run_obj:
        raise HTTPException(status_code=404, detail="Test session not found")

    # If completed without metrics cached, compute them
    metrics = run_obj.metrics
    if not metrics or len(metrics) == 0:
        metrics = await test_lab_controller.compute_test_metrics(db, test_id)

    # Fetch last 15 run results
    res_result = await db.execute(
        select(TestResult).where(TestResult.test_id == test_id).order_by(TestResult.run_index.asc()).limit(50)
    )
    recent_results = res_result.scalars().all()

    return {
        "summary": {
            "id": run_obj.id,
            "test_id": run_obj.test_id,
            "attack_type": run_obj.attack_type,
            "attack_name": ATTACK_DISPLAY_NAMES.get(run_obj.attack_type, run_obj.attack_type.title()),
            "total_runs": run_obj.total_runs,
            "status": run_obj.status,
            "params": run_obj.params,
            "created_at": run_obj.created_at.isoformat() if run_obj.created_at else None,
            "completed_at": run_obj.completed_at.isoformat() if run_obj.completed_at else None,
        },
        "metrics": metrics,
        "results_count": len(recent_results),
        "results": [
            {
                "id": r.id,
                "run_index": r.run_index,
                "event_id": r.event_id,
                "attack_injected": r.attack_injected,
                "threat_detected": r.threat_detected,
                "threat_id": r.threat_id,
                "risk_score": r.risk_score,
                "severity": r.severity,
                "detection_rule": r.detection_rule,
                "detection_time_ms": r.detection_time_ms,
                "measurement_deviation": r.measurement_deviation,
                "expected_measurement": r.expected_measurement,
                "observed_measurement": r.observed_measurement,
                "source_ip": (r.event.metadata_json or {}).get("source_ip", "10.0.1.10") if r.event else "10.0.1.10",
                "source_node": r.event.source_node if r.event else "QNode-Alpha-01",
                "session_id": r.event.session_id if r.event else "",
                "ips_action": "QUARANTINED" if (r.risk_score and r.risk_score >= 50) else ("BLOCKED" if r.threat_detected else "PASSED"),
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in recent_results
        ],
    }


@router.get("/{test_id}/results")
async def get_test_results(
    test_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated individual simulation results for a specific test run."""
    count_query = select(func.count(TestResult.id)).where(TestResult.test_id == test_id)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = (
        select(TestResult)
        .where(TestResult.test_id == test_id)
        .order_by(TestResult.run_index.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    items = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return {
        "test_id": test_id,
        "items": [
            {
                "id": r.id,
                "run_index": r.run_index,
                "event_id": r.event_id,
                "attack_injected": r.attack_injected,
                "threat_detected": r.threat_detected,
                "threat_id": r.threat_id,
                "risk_score": r.risk_score,
                "severity": r.severity,
                "detection_rule": r.detection_rule,
                "detection_time_ms": r.detection_time_ms,
                "measurement_deviation": r.measurement_deviation,
                "expected_measurement": r.expected_measurement,
                "observed_measurement": r.observed_measurement,
                "source_ip": (r.event.metadata_json or {}).get("source_ip", "10.0.1.10") if r.event else "10.0.1.10",
                "source_node": r.event.source_node if r.event else "QNode-Alpha-01",
                "session_id": r.event.session_id if r.event else "",
                "ips_action": "QUARANTINED" if (r.risk_score and r.risk_score >= 50) else ("BLOCKED" if r.threat_detected else "PASSED"),
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/{test_id}/metrics")
async def get_test_metrics(
    test_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve computed metrics for a test run."""
    result = await db.execute(select(TestRun).where(TestRun.test_id == test_id))
    run_obj = result.scalar_one_or_none()
    if not run_obj:
        raise HTTPException(status_code=404, detail="Test session not found")

    metrics = run_obj.metrics
    if not metrics or len(metrics) == 0:
        metrics = await test_lab_controller.compute_test_metrics(db, test_id)

    return metrics
