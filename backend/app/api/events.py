"""
Events API endpoints.

Provides paginated, filterable, sortable access to security events.
"""

import math
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.database import get_db
from app.models import SecurityEvent, Threat, AuditLedger
from app.schemas import SecurityEventResponse, SecurityEventDetail, AuditBlockResponse
from app.engine.detection import process_event
from app.blockchain.ledger import audit_ledger as audit_ledger_manager

router = APIRouter(prefix="/api/events", tags=["Events"])


@router.get("")
async def list_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    event_type: str = Query(None, max_length=100),
    session_id: str = Query(None, max_length=100),
    source_node: str = Query(None, max_length=100),
    verification_result: bool = Query(None),
    severity: str = Query(None, max_length=50),
    search: str = Query(None, max_length=100),
    date_from: datetime = Query(None),
    date_to: datetime = Query(None),
    sort_by: str = Query("timestamp", max_length=50),
    sort_order: str = Query("desc", max_length=10),
    db: AsyncSession = Depends(get_db),
):
    """List security events with filters, pagination, and sorting."""
    query = select(SecurityEvent)
    count_query = select(func.count(SecurityEvent.id))

    # Apply filters
    filters = []
    if event_type:
        filters.append(SecurityEvent.event_type == event_type)
    if session_id:
        filters.append(SecurityEvent.session_id.ilike(f"%{session_id}%"))
    if source_node:
        filters.append(SecurityEvent.source_node.ilike(f"%{source_node}%"))
    if verification_result is not None:
        filters.append(SecurityEvent.verification_result == verification_result)
    if date_from:
        filters.append(SecurityEvent.timestamp >= date_from)
    if date_to:
        filters.append(SecurityEvent.timestamp <= date_to)
    if search:
        filters.append(
            or_(
                SecurityEvent.event_id.ilike(f"%{search}%"),
                SecurityEvent.session_id.ilike(f"%{search}%"),
                SecurityEvent.source_node.ilike(f"%{search}%"),
                SecurityEvent.event_type.ilike(f"%{search}%"),
            )
        )

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply sorting
    sort_column = getattr(SecurityEvent, sort_by, SecurityEvent.timestamp)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    events = result.scalars().all()

    return {
        "items": [
            {
                "id": e.id,
                "event_id": e.event_id,
                "timestamp": e.timestamp.isoformat(),
                "session_id": e.session_id,
                "source_node": e.source_node,
                "event_type": e.event_type,
                "expected_measurement": e.expected_measurement,
                "observed_measurement": e.observed_measurement,
                "measurement_deviation": e.measurement_deviation,
                "verification_result": e.verification_result,
                "signature_hash": e.signature_hash,
                "has_threats": len(e.threats) > 0 if e.threats else False,
                "threat_count": len(e.threats) if e.threats else 0,
            }
            for e in events
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total > 0 else 0,
    }


@router.get("/{event_id}")
async def get_event_detail(event_id: str, db: AsyncSession = Depends(get_db)):
    """Get full event detail with related threats and audit block."""
    result = await db.execute(
        select(SecurityEvent).where(SecurityEvent.event_id == event_id)
    )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Get audit block
    audit_block = await audit_ledger_manager.get_block_for_event(db, event_id)

    return {
        "id": event.id,
        "event_id": event.event_id,
        "timestamp": event.timestamp.isoformat(),
        "session_id": event.session_id,
        "source_node": event.source_node,
        "event_type": event.event_type,
        "quantum_state": event.quantum_state,
        "expected_measurement": event.expected_measurement,
        "observed_measurement": event.observed_measurement,
        "measurement_deviation": event.measurement_deviation,
        "verification_result": event.verification_result,
        "signature_hash": event.signature_hash,
        "metadata_json": event.metadata_json,
        "created_at": event.created_at.isoformat(),
        "threats": [
            {
                "threat_id": t.threat_id,
                "threat_type": t.threat_type,
                "severity": t.severity,
                "risk_score": t.risk_score,
                "detection_rule": t.detection_rule,
                "status": t.status,
                "detected_at": t.detected_at.isoformat(),
            }
            for t in (event.threats or [])
        ],
        "audit_block": {
            "block_index": audit_block.block_index,
            "event_hash": audit_block.event_hash,
            "previous_hash": audit_block.previous_hash,
            "block_hash": audit_block.block_hash,
            "payload_hash": audit_block.payload_hash,
            "timestamp": audit_block.timestamp.isoformat(),
        } if audit_block else None,
    }


from app.schemas import SecurityEventCreate, SecurityEventResponse, SecurityEventDetail, AuditBlockResponse
from app.engine.soar import quantum_ips
from app.security.request_validator import request_validator
from app.security.auth_middleware import api_key_manager
from app.security.ip_firewall import ip_firewall
from fastapi import Request


@router.post("")
async def create_event(
    event_payload: SecurityEventCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually ingest a validated security event through the detection pipeline with
    multi-layer Quantum IPS, deep validation, and API authentication.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    event_data = event_payload.model_dump()
    event_data["metadata_json"] = {**(event_data.get("metadata_json") or {}), "client_ip": client_ip}

    # Layer 3: API Key Authentication Check (if enabled/non-exempt)
    api_key = request.headers.get("X-API-Key")
    auth_allowed, auth_error = api_key_manager.check_auth(api_key, client_ip, request.url.path)
    if not auth_allowed:
        raise HTTPException(status_code=401, detail=auth_error)

    # Layer 4: Deep Payload Sanitization & Shannon Entropy Check
    payload_valid, val_error = request_validator.validate_event_payload(event_data)
    if not payload_valid:
        ip_firewall.record_error_from_ip(client_ip)
        raise HTTPException(
            status_code=422,
            detail={
                "error": "PAYLOAD_VALIDATION_REJECTED",
                "message": "Malformed or high-entropy payload blocked by Request Validator",
                "details": val_error,
            },
        )

    # Layer 5: Ingress Pre-filtering via Quantum IPS Firewall
    allowed, rejection_reason, mitigation_details = quantum_ips.check_inbound_firewall(event_data)
    if not allowed:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "BLOCKED_BY_QUANTUM_IPS",
                "message": rejection_reason,
                "mitigation": mitigation_details,
            },
        )

    # Layer 6: Process through 14-Rule Detection Engine & Autonomous Prevention
    event, threat = await process_event(db, event_data)

    return {
        "event_id": event.event_id,
        "threat_detected": threat is not None,
        "threat_id": threat.threat_id if threat else None,
        "threat_type": threat.threat_type if threat else "CLEAN_TRAFFIC",
        "severity": threat.severity if threat else "LOW",
        "risk_score": threat.risk_score if threat else 0.0,
        "mitigation_action": "BLOCKED_AND_QUARANTINED" if threat else "VERIFIED_ALLOW",
        "active_defense_status": "ENFORCING",
    }

