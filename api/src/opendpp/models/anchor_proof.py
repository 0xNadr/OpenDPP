import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from opendpp.db import Base

if TYPE_CHECKING:
    from opendpp.models.dpp import DPPRecord


class AnchorProof(Base):
    """A record of a snapshot hash being anchored on a public ledger.

    `snapshot_hash` is the SHA-256 of the canonicalized DPP `data` at the
    time of anchoring; if the DPP changes later, the proof no longer
    corresponds to its current state.
    """

    __tablename__ = "anchor_proofs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    dpp_record_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("dpp_records.id", ondelete="CASCADE"), nullable=False
    )
    chain: Mapped[str] = mapped_column(String(64), nullable=False)
    snapshot_hash: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False, index=True)
    tx_hash: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    block_number: Mapped[int] = mapped_column(Integer, nullable=False)
    explorer_tx_url: Mapped[str | None] = mapped_column(String(512))
    anchored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    dpp_record: Mapped["DPPRecord"] = relationship()
