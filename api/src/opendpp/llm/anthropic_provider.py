"""AnthropicChatProvider — real Claude calls.

Uses the async Anthropic SDK. Streaming for chat (better UX), regular
non-streaming requests for translation and semantic validation (we want
the whole JSON document before we hand it off).
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from anthropic import AsyncAnthropic

from opendpp.llm.prompts import TRANSLATE_SYSTEM, VALIDATE_SYSTEM
from opendpp.llm.provider import ChatMessage, SemanticWarning

logger = logging.getLogger(__name__)


class AnthropicChatProvider:
    """Streaming Claude provider for OpenDPP.

    Designed to be safe for concurrent FastAPI request handlers.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        max_output_tokens: int = 1024,
    ) -> None:
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_output_tokens

    async def stream_chat(
        self,
        *,
        system: str,
        messages: list[ChatMessage],
    ) -> AsyncIterator[str]:
        anthropic_messages: list[dict[str, Any]] = [
            {"role": m.role, "content": m.content} for m in messages
        ]
        async with self._client.messages.stream(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            messages=anthropic_messages,
            cache_control={"type": "ephemeral"},
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def translate(self, *, source: dict, target_lang: str) -> dict:
        user_prompt = (
            f"Translate the following Digital Product Passport into language '{target_lang}'. "
            "Return ONLY the translated JSON document — no markdown fences, no commentary.\n\n"
            f"{json.dumps(source, ensure_ascii=False, indent=2)}"
        )
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens * 4,
            system=TRANSLATE_SYSTEM,
            messages=[{"role": "user", "content": user_prompt}],
            cache_control={"type": "ephemeral"},
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        cleaned = _strip_code_fences(text)
        try:
            translated = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.exception("Anthropic translate returned non-JSON: %r", text[:200])
            raise ValueError("LLM translation did not return valid JSON") from exc
        if not isinstance(translated, dict):
            raise ValueError("LLM translation must return a JSON object")
        return translated

    async def validate_semantic(self, *, dpp_data: dict) -> list[SemanticWarning]:
        user_prompt = (
            "Review the following candidate Digital Product Passport. "
            "Return a JSON array of warnings in the shape described in the system prompt.\n\n"
            f"{json.dumps(dpp_data, ensure_ascii=False, indent=2)}"
        )
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=VALIDATE_SYSTEM,
            messages=[{"role": "user", "content": user_prompt}],
            cache_control={"type": "ephemeral"},
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        cleaned = _strip_code_fences(text)
        try:
            raw = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("Anthropic semantic validation returned non-JSON: %r", text[:200])
            return []
        if not isinstance(raw, list):
            return []

        warnings: list[SemanticWarning] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            severity = item.get("severity")
            if severity not in ("info", "warning", "error"):
                continue
            warnings.append(
                SemanticWarning(
                    severity=severity,
                    field=item.get("field"),
                    message=str(item.get("message", "")),
                )
            )
        return warnings


def _strip_code_fences(text: str) -> str:
    """Best-effort strip of ```json ... ``` wrappers."""
    stripped = text.strip()
    if stripped.startswith("```"):
        # remove opening fence (with optional language tag)
        stripped = stripped.split("\n", 1)[1] if "\n" in stripped else stripped[3:]
        if stripped.endswith("```"):
            stripped = stripped[: -3]
    return stripped.strip()
