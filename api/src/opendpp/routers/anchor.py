"""Anchor a DPP snapshot hash on a public ledger and serve verification."""

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opendpp.anchor import (
    AnchorNotConfigured,
    canonical_snapshot_hash,
    get_anchor_service,
)
from opendpp.db import get_session
from opendpp.models import AnchorProof, DPPRecord

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/anchor", tags=["anchor"])


class AnchorProofOut(BaseModel):
    id: uuid.UUID
    chain: str
    snapshot_hash: str
    tx_hash: str
    block_number: int
    explorer_tx_url: str | None
    anchored_at: datetime


class AnchorVerificationOut(BaseModel):
    """Result of querying the chain directly with the current DPP hash.

    `current_snapshot_hash` is the hash of the DPP *right now*. `anchored` is
    True only if that exact hash has been recorded on-chain — which means
    no tampering has happened since the anchor was created.
    """

    chain: str
    current_snapshot_hash: str
    anchored: bool
    on_chain_timestamp: int
    matches_stored_proof: bool


@router.post(
    "/{record_id}",
    response_model=AnchorProofOut,
    status_code=status.HTTP_201_CREATED,
)
async def anchor_dpp(
    record_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> AnchorProofOut:
    record = await session.get(DPPRecord, record_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "DPP record not found")

    snapshot = canonical_snapshot_hash(record.data)
    service = get_anchor_service()

    # Allow re-querying if already anchored — the contract rejects duplicates,
    # but we also want to surface the proof we already have.
    existing = (
        await session.execute(
            select(AnchorProof).where(
                AnchorProof.dpp_record_id == record.id,
                AnchorProof.snapshot_hash == snapshot,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return _to_out(existing)

    try:
        receipt = await run_in_threadpool(service.anchor, snapshot)
    except AnchorNotConfigured as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            f"anchor service not configured: {exc}",
        ) from exc
    except Exception as exc:
        logger.exception("anchor tx failed")
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            f"anchor transaction failed: {exc}",
        ) from exc

    proof = AnchorProof(
        dpp_record_id=record.id,
        chain=receipt.chain,
        snapshot_hash=receipt.snapshot_hash,
        tx_hash=receipt.tx_hash,
        block_number=receipt.block_number,
        explorer_tx_url=receipt.explorer_tx_url,
        anchored_at=receipt.anchored_at,
    )
    session.add(proof)
    await session.commit()
    await session.refresh(proof)
    return _to_out(proof)


@router.get("/{record_id}/proof", response_model=list[AnchorProofOut])
async def list_proofs(
    record_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> list[AnchorProofOut]:
    record = await session.get(DPPRecord, record_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "DPP record not found")

    rows = (
        await session.execute(
            select(AnchorProof)
            .where(AnchorProof.dpp_record_id == record_id)
            .order_by(AnchorProof.created_at.desc())
        )
    ).scalars().all()
    return [_to_out(r) for r in rows]


@router.get("/{record_id}/verify", response_model=AnchorVerificationOut)
async def verify_anchor(
    record_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> AnchorVerificationOut:
    """Re-compute the DPP hash and query the contract directly.

    `matches_stored_proof` is True when the on-chain anchor matches a proof
    we already have in the DB — meaning the DPP hasn't been tampered with
    since anchoring.
    """
    record = await session.get(DPPRecord, record_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "DPP record not found")

    current_hash = canonical_snapshot_hash(record.data)
    service = get_anchor_service()

    try:
        result = await run_in_threadpool(service.verify, current_hash)
    except AnchorNotConfigured as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            f"anchor service not configured: {exc}",
        ) from exc

    stored = (
        await session.execute(
            select(AnchorProof).where(
                AnchorProof.dpp_record_id == record_id,
                AnchorProof.snapshot_hash == current_hash,
            )
        )
    ).scalar_one_or_none()

    return AnchorVerificationOut(
        chain=result.chain,
        current_snapshot_hash="0x" + current_hash.hex(),
        anchored=result.anchored,
        on_chain_timestamp=result.on_chain_timestamp,
        matches_stored_proof=stored is not None and result.anchored,
    )


def _to_out(p: AnchorProof) -> AnchorProofOut:
    return AnchorProofOut(
        id=p.id,
        chain=p.chain,
        snapshot_hash="0x" + p.snapshot_hash.hex(),
        tx_hash=p.tx_hash,
        block_number=p.block_number,
        explorer_tx_url=p.explorer_tx_url,
        anchored_at=p.anchored_at,
    )
