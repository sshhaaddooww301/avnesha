"""
Audit Ledger API endpoints.

Exposes tamper-evident blockchain verification and block exploration.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import AuditLedger
from app.schemas import LedgerVerificationResponse, LedgerStatusResponse
from app.blockchain.ledger import audit_ledger

router = APIRouter(prefix="/api/ledger", tags=["Audit Ledger"])


@router.post("/verify", response_model=LedgerVerificationResponse)
async def verify_ledger(db: AsyncSession = Depends(get_db)):
    """
    Perform full cryptographic verification of the audit hash chain.
    Recalculates every SHA-256 block hash and verifies linkage.
    """
    result = await audit_ledger.verify_chain(db)
    return LedgerVerificationResponse(**result)


@router.get("/status", response_model=LedgerStatusResponse)
async def get_ledger_status(db: AsyncSession = Depends(get_db)):
    """Get high-level summary of audit ledger."""
    status = await audit_ledger.get_status(db)
    return LedgerStatusResponse(**status)


@router.get("/blocks")
async def list_blocks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List ledger blocks with pagination."""
    total_result = await db.execute(select(func.count(AuditLedger.id)))
    total = total_result.scalar() or 0

    query = (
        select(AuditLedger)
        .order_by(AuditLedger.block_index.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    blocks = result.scalars().all()

    return {
        "items": [
            {
                "id": b.id,
                "block_index": b.block_index,
                "event_id": b.event_id,
                "event_hash": b.event_hash,
                "previous_hash": b.previous_hash,
                "block_hash": b.block_hash,
                "payload_hash": b.payload_hash,
                "timestamp": b.timestamp.isoformat(),
            }
            for b in blocks
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
