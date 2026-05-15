"""MockChatProvider — canned but plausible responses.

Used when ANTHROPIC_API_KEY is missing or when LLM_PROVIDER=mock. Lets the
demo and CI run without a live key. Behavior is deterministic so tests can
assert against it.
"""

from __future__ import annotations

import asyncio
import copy
from collections.abc import AsyncIterator

from opendpp.llm.provider import ChatMessage, SemanticWarning

_TRANSLATABLE_KEYS = {
    "productName",
    "model",
    "repairGuidance",
    "careInstructions",
    "endOfLifeOptions",
    "name",
    "address",
}

_LANG_PREFIX = {
    "de": "[DE] ",
    "fr": "[FR] ",
    "ar": "[AR] ",
    "en": "",
}


def _translate_strings(node, target_lang: str, *, in_translatable: bool = False):
    if isinstance(node, dict):
        return {
            k: _translate_strings(
                v,
                target_lang,
                in_translatable=in_translatable or k in _TRANSLATABLE_KEYS,
            )
            for k, v in node.items()
        }
    if isinstance(node, list):
        return [
            _translate_strings(v, target_lang, in_translatable=in_translatable)
            for v in node
        ]
    if isinstance(node, str) and in_translatable and target_lang != "en":
        return f"{_LANG_PREFIX.get(target_lang, '')}{node}"
    return node


class MockChatProvider:
    """Deterministic stand-in for tests and no-key dev."""

    async def stream_chat(
        self,
        *,
        system: str,
        messages: list[ChatMessage],
    ) -> AsyncIterator[str]:
        last_user = next((m for m in reversed(messages) if m.role == "user"), None)
        question = last_user.content if last_user else ""
        reply = (
            "I'm the OpenDPP mock assistant — running without a live LLM key. "
            "In a real deployment I'd ground my answer in the product's Digital "
            f"Product Passport. You asked: {question!r}."
        )
        # Stream in small chunks so the SSE plumbing exercises real delivery.
        for chunk in reply.split(" "):
            await asyncio.sleep(0)
            yield chunk + " "

    async def translate(self, *, source: dict, target_lang: str) -> dict:
        await asyncio.sleep(0)
        translated = copy.deepcopy(source)
        return _translate_strings(translated, target_lang)

    async def validate_semantic(self, *, dpp_data: dict) -> list[SemanticWarning]:
        warnings: list[SemanticWarning] = []
        composition = dpp_data.get("composition") or {}
        materials = composition.get("materials") or []
        total = sum((m.get("percentage") or 0) for m in materials)
        if materials and abs(total - 100) > 0.01:
            warnings.append(
                SemanticWarning(
                    severity="error",
                    field="composition.materials",
                    message=f"Material percentages sum to {total}, expected 100.",
                )
            )
        return warnings
