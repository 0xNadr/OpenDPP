import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from opendpp.db import Base

if TYPE_CHECKING:
    from opendpp.models.dpp import DPPRecord
    from opendpp.models.supplier import Supplier

JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")


class VerifiableCredential(Base):
    """A W3C Verifiable Credential bound to a DPP record.

    `jwt` is the canonical signed form. `body` is the unsigned credential
    JSON (the `vc` payload claim) cached for easy display in the UI.
    """

    __tablename__ = "verifiable_credentials"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    dpp_record_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("dpp_records.id", ondelete="CASCADE"), nullable=False
    )
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False
    )
    attestation_type: Mapped[str] = mapped_column(String(128), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(512), nullable=False)
    jwt: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    dpp_record: Mapped["DPPRecord"] = relationship()
    supplier: Mapped["Supplier"] = relationship(back_populates="credentials")
