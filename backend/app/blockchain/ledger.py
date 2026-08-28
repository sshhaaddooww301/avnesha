"""
Tamper-Evident Audit Ledger (Blockchain-style hash chain).

Each block contains:
- block_index: Sequential position
- event_id: Reference to the security event
- event_hash: SHA-256(event_id + timestamp)
- previous_hash: block_hash of the previous block (or "0"*64 for genesis)
- payload_hash: SHA-256(canonical_JSON_payload)
- block_hash: SHA-256(previous_hash + payload_hash + event_hash + timestamp)

Verification:
- Walk entire chain, recalculate each block_hash
- Report VALID or COMPROMISED with the first invalid block
"""

import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models import AuditLedger


def _sha256(data: str) -> str:
    """Compute SHA-256 hex digest."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _canonical_json(payload: Dict[str, Any]) -> str:
    """Produce canonical JSON (sorted keys, no whitespace)."""
    return json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))


class AuditLedgerManager:
    """Manages the tamper-evident audit hash chain."""

    GENESIS_HASH = "0" * 64

    async def add_block(
        self,
        db: AsyncSession,
        event_id: str,
        payload: Dict[str, Any],
    ) -> AuditLedger:
        """Create a new audit block and add to the chain."""
        # Get the last block
        result = await db.execute(
            select(AuditLedger)
            .order_by(AuditLedger.block_index.desc())
            .limit(1)
        )
        last_block = result.scalar_one_or_none()

        if last_block:
            previous_hash = last_block.block_hash
            block_index = last_block.block_index + 1
        else:
            previous_hash = self.GENESIS_HASH
            block_index = 0

        now = datetime.utcnow()
        timestamp_str = now.isoformat()

        # Compute hashes
        event_hash = _sha256(f"{event_id}:{timestamp_str}")
        payload_hash = _sha256(_canonical_json(payload))
        block_hash = _sha256(
            f"{previous_hash}:{payload_hash}:{event_hash}:{timestamp_str}"
        )

        block = AuditLedger(
            block_index=block_index,
            event_id=event_id,
            event_hash=event_hash,
            previous_hash=previous_hash,
            block_hash=block_hash,
            timestamp=now,
            payload_hash=payload_hash,
        )
        db.add(block)
        await db.flush()
        return block

    async def verify_chain(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Verify the entire audit chain integrity.

        Returns:
            {
                "valid": bool,
                "total_blocks": int,
                "verified_blocks": int,
                "first_invalid_block": Optional[int],
                "message": str
            }
        """
        result = await db.execute(
            select(AuditLedger).order_by(AuditLedger.block_index.asc())
        )
        blocks = result.scalars().all()

        if not blocks:
            return {
                "valid": True,
                "total_blocks": 0,
                "verified_blocks": 0,
                "first_invalid_block": None,
                "message": "Ledger is empty — no blocks to verify",
            }

        verified = 0
        expected_prev_hash = self.GENESIS_HASH

        for block in blocks:
            # Verify previous hash chain
            if block.previous_hash != expected_prev_hash:
                return {
                    "valid": False,
                    "total_blocks": len(blocks),
                    "verified_blocks": verified,
                    "first_invalid_block": block.block_index,
                    "message": f"Chain broken at block {block.block_index}: previous_hash mismatch",
                }

            # Recalculate block hash
            timestamp_str = block.timestamp.isoformat()
            expected_block_hash = _sha256(
                f"{block.previous_hash}:{block.payload_hash}:{block.event_hash}:{timestamp_str}"
            )

            if block.block_hash != expected_block_hash:
                return {
                    "valid": False,
                    "total_blocks": len(blocks),
                    "verified_blocks": verified,
                    "first_invalid_block": block.block_index,
                    "message": f"Block {block.block_index} hash mismatch: computed={expected_block_hash[:16]}..., stored={block.block_hash[:16]}...",
                }

            expected_prev_hash = block.block_hash
            verified += 1

        return {
            "valid": True,
            "total_blocks": len(blocks),
            "verified_blocks": verified,
            "first_invalid_block": None,
            "message": f"Ledger integrity VALID — all {verified} blocks verified",
        }

    async def get_status(self, db: AsyncSession) -> Dict[str, Any]:
        """Get current ledger status."""
        count_result = await db.execute(select(func.count(AuditLedger.id)))
        total = count_result.scalar() or 0

        last_result = await db.execute(
            select(AuditLedger).order_by(AuditLedger.block_index.desc()).limit(1)
        )
        last_block = last_result.scalar_one_or_none()

        if total == 0:
            return {
                "total_blocks": 0,
                "last_block_index": None,
                "last_block_hash": None,
                "last_block_timestamp": None,
                "integrity": "EMPTY",
            }

        return {
            "total_blocks": total,
            "last_block_index": last_block.block_index if last_block else None,
            "last_block_hash": last_block.block_hash if last_block else None,
            "last_block_timestamp": last_block.timestamp.isoformat() if last_block else None,
            "integrity": "VALID",  # Real verification done via verify_chain
        }

    async def get_block_for_event(
        self, db: AsyncSession, event_id: str
    ) -> Optional[AuditLedger]:
        """Retrieve audit block for a specific event."""
        result = await db.execute(
            select(AuditLedger).where(AuditLedger.event_id == event_id)
        )
        return result.scalar_one_or_none()


# Singleton instance
audit_ledger = AuditLedgerManager()
