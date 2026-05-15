import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, LargeBinary, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from opendpp.db import Base

if TYPE_CHECKING:
    from opendpp.models.verifiable_credential import VerifiableCredential


class Supplier(Base):
    """A demo supplier with an Ed25519 keypair and a did:key DID.

    `private_key_bytes` is kept here so the demo can issue credentials on
    the supplier's behalf — in a real deployment the private key would
    live with the supplier and OpenDPP would only ever hold the DID.
    """

    __tablename__ = "suppliers"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    did: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    public_key_bytes: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    private_key_bytes: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    credentials: Mapped[list["VerifiableCredential"]] = relationship(
        back_populates="supplier", cascade="all, delete-orphan"
    )
