"""SSE chat endpoint grounded in a single DPP record."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from opendpp.db import get_session
from opendpp.llm import ChatMessage, get_provider
from opendpp.llm.prompts import build_chat_system
from opendpp.models import DPPRecord

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatTurn(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatTurn] = Field(min_length=1)


@router.post("/{record_id}")
async def chat(
    record_id: uuid.UUID,
    payload: ChatRequest,
    session: AsyncSession = Depends(get_session),
) -> EventSourceResponse:
    record = await session.get(DPPRecord, record_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "DPP record not found")

    provider = get_provider()
    system = build_chat_system(record.data)
    messages = [ChatMessage(role=t.role, content=t.content) for t in payload.messages]

    async def event_stream():
        try:
            async for delta in provider.stream_chat(system=system, messages=messages):
                yield {"event": "delta", "data": delta}
        except Exception as exc:
            yield {"event": "error", "data": str(exc)}
        else:
            yield {"event": "done", "data": ""}

    return EventSourceResponse(event_stream())
