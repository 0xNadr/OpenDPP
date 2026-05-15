"""LLM-backed translation endpoint with Postgres cache."""

import hashlib
import json
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from opendpp.db import get_session
from opendpp.llm import get_provider
from opendpp.models import DPPRecord, TranslationCache

router = APIRouter(prefix="/api/dpp", tags=["translate"])

Lang = Literal["en", "de", "fr", "ar"]


def _content_hash(data: dict) -> str:
    return hashlib.sha256(
        json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


@router.get("/{record_id}/translate")
async def translate_dpp(
    record_id: uuid.UUID,
    lang: Lang = Query(default="en"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    record = await session.get(DPPRecord, record_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "DPP record not found")

    if lang == "en":
        return {"lang": lang, "data": record.data, "cached": False}

    digest = _content_hash(record.data)

    cached = (
        await session.execute(
            select(TranslationCache).where(
                TranslationCache.lang == lang,
                TranslationCache.content_hash == digest,
            )
        )
    ).scalar_one_or_none()
    if cached is not None:
        return {"lang": lang, "data": cached.payload, "cached": True}

    provider = get_provider()
    try:
        translated = await provider.translate(source=record.data, target_lang=lang)
    except ValueError as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            f"LLM translation failed: {exc}",
        ) from exc

    entry = TranslationCache(lang=lang, content_hash=digest, payload=translated)
    session.add(entry)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()  # another request beat us; harmless

    return {"lang": lang, "data": translated, "cached": False}
