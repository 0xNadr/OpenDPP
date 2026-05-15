"""LLM provider abstraction.

Real LLM calls go through `AnthropicChatProvider`; tests and no-key dev fall
back to `MockChatProvider`. Provider selection is driven by `Settings`.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal, Protocol

from opendpp.config import get_settings

logger = logging.getLogger(__name__)

Role = Literal["user", "assistant"]


@dataclass(frozen=True)
class ChatMessage:
    role: Role
    content: str


@dataclass(frozen=True)
class SemanticWarning:
    """A non-blocking concern flagged by the LLM about candidate DPP data."""

    severity: Literal["info", "warning", "error"]
    field: str | None
    message: str


class ChatProvider(Protocol):
    """Minimal surface every LLM provider must satisfy.

    Methods return either a single string or an async iterator of token chunks.
    Providers MUST be safe to call concurrently from FastAPI request handlers.
    """

    async def stream_chat(
        self,
        *,
        system: str,
        messages: list[ChatMessage],
    ) -> AsyncIterator[str]:
        """Stream a chat completion. Yields text deltas as they arrive."""
        ...

    async def translate(self, *, source: dict, target_lang: str) -> dict:
        """Translate user-facing strings in a DPP JSON document.

        Returns a copy of `source` with translatable strings replaced.
        """
        ...

    async def validate_semantic(self, *, dpp_data: dict) -> list[SemanticWarning]:
        """Inspect a candidate DPP and return any semantic issues found."""
        ...


@lru_cache
def get_provider() -> ChatProvider:
    """Return the configured provider, falling back to mock if the key is missing."""
    settings = get_settings()
    requested = settings.llm_provider.lower()

    if requested == "mock":
        from opendpp.llm.mock import MockChatProvider

        logger.info("LLM provider: mock (explicitly selected)")
        return MockChatProvider()

    if requested == "anthropic":
        if not settings.anthropic_api_key:
            logger.warning(
                "LLM provider 'anthropic' selected but ANTHROPIC_API_KEY is empty; falling back to mock."
            )
            from opendpp.llm.mock import MockChatProvider

            return MockChatProvider()

        from opendpp.llm.anthropic_provider import AnthropicChatProvider

        logger.info("LLM provider: anthropic (model=%s)", settings.anthropic_model)
        return AnthropicChatProvider(  # type: ignore[return-value]
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
            max_output_tokens=settings.llm_max_output_tokens,
        )

    raise ValueError(f"Unknown LLM_PROVIDER: {requested!r}")
