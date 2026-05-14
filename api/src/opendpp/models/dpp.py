import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, UniqueConstraint, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from opendpp.db import Base

if TYPE_CHECKING:
    from opendpp.models.product import Product

JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")


class DPPRecord(Base):
    __tablename__ = "dpp_records"
    __table_args__ = (
        UniqueConstraint("product_id", "lot", "serial", name="uq_dpp_product_lot_serial"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    lot: Mapped[str | None] = mapped_column(String(20))
    serial: Mapped[str | None] = mapped_column(String(20))
    schema_version: Mapped[str] = mapped_column(String(64), nullable=False)
    data: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    product: Mapped["Product"] = relationship(back_populates="dpp_records")
