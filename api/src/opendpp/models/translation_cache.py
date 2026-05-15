import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, String, UniqueConstraint, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from opendpp.db import Base

JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")


class TranslationCache(Base):
    """LLM translation cache keyed by (lang, content_hash).

    Invalidates implicitly: when a DPP's `data` changes, its sha256 changes,
    and the next translation request misses the cache and refreshes.
    """

    __tablename__ = "translation_cache"
    __table_args__ = (
        UniqueConstraint("lang", "content_hash", name="uq_translation_cache_lang_hash"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lang: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSON_TYPE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
