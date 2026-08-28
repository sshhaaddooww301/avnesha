"""
Dashboard API endpoints.

All data comes from PostgreSQL queries — no hardcoded values.
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, and_

from app.database import get_db
from app.models import SecurityEvent, Threat, AuditLedger
from app.schemas import DashboardSummary, TimelinePoint, SeverityDistribution, TopOffense
from app.blockchain.ledger import audit_ledger

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """Get dashboard summary with severity counts from database."""
    # Total events
    event_count = await db.execute(select(func.count(SecurityEvent.id)))
    total_events = event_count.scalar() or 0

    # Total threats
    threat_count = await db.execute(select(func.count(Threat.id)))
    total_threats = threat_count.scalar() or 0

    # Severity counts from database
    severity_counts = await db.execute(
        select(
            Threat.severity,
            func.count(Threat.id),
        ).group_by(Threat.severity)
    )
    counts = {row[0]: row[1] for row in severity_counts.all()}

    # Open threats
    open_count = await db.execute(
        select(func.count(Threat.id)).where(
            Threat.status.in_(["open", "investigating"])
        )
    )
    open_threats = open_count.scalar() or 0

    # Verification success rate
    ver_result = await db.execute(
        select(
            func.count(SecurityEvent.id).filter(SecurityEvent.verification_result == True),
            func.count(SecurityEvent.id).filter(SecurityEvent.verification_result != None),
        )
    )
    ver_row = ver_result.one()
    success_count = ver_row[0] or 0
    total_verified = ver_row[1] or 0
    verification_rate = (
        round(success_count / total_verified * 100, 2) if total_verified > 0 else None
    )

    # Ledger integrity
    ledger_status = await audit_ledger.get_status(db)

    return DashboardSummary(
        total_events=total_events,
        total_threats=total_threats,
        critical_count=counts.get("critical", 0),
        high_count=counts.get("high", 0),
        medium_count=counts.get("medium", 0),
        low_count=counts.get("low", 0),
        open_threats=open_threats,
        verification_success_rate=verification_rate,
        ledger_integrity=ledger_status.get("integrity", "UNKNOWN"),
    )


@router.get("/timeline")
async def get_alerts_timeline(
    range: str = Query("24h", regex="^(1h|6h|24h|7d|30d)$"),
    db: AsyncSession = Depends(get_db),
):
    """Get alerts over time, bucketed by interval."""
    now = datetime.utcnow()

    range_map = {
        "1h": (timedelta(hours=1), timedelta(minutes=5), "%H:%M"),
        "6h": (timedelta(hours=6), timedelta(minutes=30), "%H:%M"),
        "24h": (timedelta(hours=24), timedelta(hours=1), "%m/%d %H:00"),
        "7d": (timedelta(days=7), timedelta(hours=6), "%m/%d %H:00"),
        "30d": (timedelta(days=30), timedelta(days=1), "%m/%d"),
    }

    total_delta, bucket_delta, fmt = range_map[range]
    start = now - total_delta

    # Get all threats in range
    result = await db.execute(
        select(Threat.detected_at, Threat.severity).where(
            Threat.detected_at >= start
        ).order_by(Threat.detected_at.asc())
    )
    threats = result.all()

    # Bucket the threats
    buckets = {}
    current = start
    while current <= now:
        key = current.strftime(fmt)
        buckets[key] = {"timestamp": key, "count": 0, "critical": 0, "high": 0, "medium": 0, "low": 0}
        current += bucket_delta

    for detected_at, severity in threats:
        # Find the bucket
        for key in reversed(list(buckets.keys())):
            bucket_time = start
            idx = list(buckets.keys()).index(key)
            bucket_time = start + bucket_delta * idx
            if detected_at >= bucket_time:
                buckets[key]["count"] += 1
                if severity in buckets[key]:
                    buckets[key][severity] += 1
                break

    return list(buckets.values())


@router.get("/severity-distribution")
async def get_severity_distribution(db: AsyncSession = Depends(get_db)):
    """Calculate severity distribution percentages from database."""
    result = await db.execute(
        select(Threat.severity, func.count(Threat.id))
        .group_by(Threat.severity)
    )
    rows = result.all()
    total = sum(r[1] for r in rows)

    if total == 0:
        return []

    return [
        SeverityDistribution(
            severity=row[0],
            count=row[1],
            percentage=round(row[1] / total * 100, 2),
        )
        for row in rows
    ]


@router.get("/top-offenses")
async def get_top_offenses(
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Get most frequently detected threat types from database."""
    result = await db.execute(
        select(Threat.threat_type, func.count(Threat.id))
        .group_by(Threat.threat_type)
        .order_by(func.count(Threat.id).desc())
        .limit(limit)
    )
    rows = result.all()
    total = sum(r[1] for r in rows)

    if total == 0:
        return []

    return [
        TopOffense(
            threat_type=row[0],
            count=row[1],
            percentage=round(row[1] / total * 100, 2),
        )
        for row in rows
    ]


@router.get("/recent-incidents")
async def get_recent_incidents(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get latest threats with event details."""
    result = await db.execute(
        select(Threat)
        .order_by(Threat.detected_at.desc())
        .limit(limit)
    )
    threats = result.scalars().all()

    return [
        {
            "threat_id": t.threat_id,
            "threat_type": t.threat_type,
            "severity": t.severity,
            "risk_score": t.risk_score,
            "detection_rule": t.detection_rule,
            "status": t.status,
            "event_id": t.event_id,
            "detected_at": t.detected_at.isoformat(),
            "source_node": t.event.source_node if t.event else None,
            "session_id": t.event.session_id if t.event else None,
        }
        for t in threats
    ]


@router.get("/log-timeline")
async def get_log_timeline(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get recent security events for log timeline."""
    result = await db.execute(
        select(SecurityEvent)
        .order_by(SecurityEvent.timestamp.desc())
        .limit(limit)
    )
    events = result.scalars().all()

    return [
        {
            "event_id": e.event_id,
            "timestamp": e.timestamp.isoformat(),
            "event_type": e.event_type,
            "session_id": e.session_id,
            "source_node": e.source_node,
            "verification_result": e.verification_result,
            "measurement_deviation": e.measurement_deviation,
            "has_threats": len(e.threats) > 0 if e.threats else False,
            "threat_severity": e.threats[0].severity if e.threats else None,
        }
        for e in events
    ]
