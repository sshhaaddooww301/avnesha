"""
Reports API endpoints.

Computes comprehensive statistical reports and CSV export data dynamically from PostgreSQL.
"""

import io
import csv
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.database import get_db
from app.models import SecurityEvent, Threat, AuditLedger
from app.blockchain.ledger import audit_ledger
from app.engine.statistics import (
    mean,
    std_deviation,
    variance,
    measurement_deviation,
)

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/summary")
async def get_report_summary(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate comprehensive statistical report over a given time window.
    All calculations are derived directly from database records.
    """
    start_time = datetime.utcnow() - timedelta(days=days)

    # 1. Total events & verification stats
    ev_result = await db.execute(
        select(
            func.count(SecurityEvent.id),
            func.count(SecurityEvent.id).filter(SecurityEvent.verification_result == True),
            func.count(SecurityEvent.id).filter(SecurityEvent.verification_result == False),
        ).where(SecurityEvent.timestamp >= start_time)
    )
    ev_row = ev_result.one()
    total_events = ev_row[0] or 0
    ver_success = ev_row[1] or 0
    ver_failure = ev_row[2] or 0
    total_verified = ver_success + ver_failure
    success_rate = round(ver_success / total_verified * 100, 2) if total_verified > 0 else None

    # 2. Total threats & severity distribution
    th_count = await db.execute(
        select(func.count(Threat.id)).where(Threat.detected_at >= start_time)
    )
    total_threats = th_count.scalar() or 0

    sev_result = await db.execute(
        select(Threat.severity, func.count(Threat.id))
        .where(Threat.detected_at >= start_time)
        .group_by(Threat.severity)
    )
    sev_rows = sev_result.all()
    severity_dist = [
        {
            "severity": row[0],
            "count": row[1],
            "percentage": round(row[1] / total_threats * 100, 2) if total_threats > 0 else 0.0,
        }
        for row in sev_rows
    ]

    # 3. Threat type distribution & most frequent attack
    type_result = await db.execute(
        select(Threat.threat_type, func.count(Threat.id))
        .where(Threat.detected_at >= start_time)
        .group_by(Threat.threat_type)
        .order_by(func.count(Threat.id).desc())
    )
    type_rows = type_result.all()
    threat_dist = [
        {
            "threat_type": row[0],
            "count": row[1],
            "percentage": round(row[1] / total_threats * 100, 2) if total_threats > 0 else 0.0,
        }
        for row in type_rows
    ]
    most_frequent = type_rows[0][0] if type_rows else None

    # 4. Quantum measurement statistics
    dev_result = await db.execute(
        select(SecurityEvent.observed_measurement, SecurityEvent.expected_measurement)
        .where(
            and_(
                SecurityEvent.timestamp >= start_time,
                SecurityEvent.observed_measurement != None,
                SecurityEvent.expected_measurement != None,
            )
        )
    )
    dev_records = dev_result.all()
    deviations = [
        measurement_deviation(r[0], r[1])
        for r in dev_records
        if r[0] is not None and r[1] is not None
    ]

    measurement_stats = None
    if deviations:
        m = mean(deviations)
        v = variance(deviations)
        std = std_deviation(deviations)
        measurement_stats = {
            "sample_count": len(deviations),
            "mean_deviation_pct": round(m * 100, 2),
            "std_deviation_pct": round(std * 100, 2),
            "variance": round(v, 6),
            "max_deviation_pct": round(max(deviations) * 100, 2),
            "min_deviation_pct": round(min(deviations) * 100, 2),
        }

    # 5. Ledger status
    ledger_status = await audit_ledger.get_status(db)

    return {
        "report_period_days": days,
        "generated_at": datetime.utcnow().isoformat(),
        "total_events": total_events,
        "total_threats": total_threats,
        "verification_success_count": ver_success,
        "verification_failure_count": ver_failure,
        "verification_success_rate": success_rate,
        "most_frequent_attack": most_frequent,
        "severity_distribution": severity_dist,
        "threat_distribution": threat_dist,
        "measurement_stats": measurement_stats,
        "ledger_integrity": ledger_status.get("integrity", "UNKNOWN"),
        "ledger_total_blocks": ledger_status.get("total_blocks", 0),
    }


@router.get("/export")
async def export_report_csv(
    data_type: str = Query("threats", regex="^(threats|events|ledger)$"),
    limit: int = Query(1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
):
    """Export SIEM records to CSV format for SOC documentation."""
    output = io.StringIO()
    writer = csv.writer(output)

    if data_type == "threats":
        writer.writerow([
            "Threat ID", "Event ID", "Threat Type", "Severity",
            "Risk Score", "Detection Rule", "Confidence", "Status",
            "Detected At", "Resolved At"
        ])
        result = await db.execute(
            select(Threat).order_by(Threat.detected_at.desc()).limit(limit)
        )
        threats = result.scalars().all()
        for t in threats:
            writer.writerow([
                t.threat_id, t.event_id, t.threat_type, t.severity,
                t.risk_score, t.detection_rule, t.confidence, t.status,
                t.detected_at.isoformat() if t.detected_at else "",
                t.resolved_at.isoformat() if t.resolved_at else "",
            ])

    elif data_type == "events":
        writer.writerow([
            "Event ID", "Timestamp", "Session ID", "Source Node",
            "Event Type", "Expected Measurement", "Observed Measurement",
            "Deviation", "Verification Result", "Signature Hash"
        ])
        result = await db.execute(
            select(SecurityEvent).order_by(SecurityEvent.timestamp.desc()).limit(limit)
        )
        events = result.scalars().all()
        for e in events:
            writer.writerow([
                e.event_id, e.timestamp.isoformat() if e.timestamp else "",
                e.session_id, e.source_node, e.event_type,
                e.expected_measurement, e.observed_measurement,
                e.measurement_deviation, e.verification_result,
                e.signature_hash or "",
            ])

    elif data_type == "ledger":
        writer.writerow([
            "Block Index", "Event ID", "Block Hash", "Previous Hash",
            "Event Hash", "Payload Hash", "Timestamp"
        ])
        result = await db.execute(
            select(AuditLedger).order_by(AuditLedger.block_index.asc()).limit(limit)
        )
        blocks = result.scalars().all()
        for b in blocks:
            writer.writerow([
                b.block_index, b.event_id, b.block_hash, b.previous_hash,
                b.event_hash, b.payload_hash,
                b.timestamp.isoformat() if b.timestamp else "",
            ])

    output.seek(0)
    filename = f"qds_siem_{data_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
