import uuid

import pytest

from opendpp.llm import ChatMessage, get_provider
from opendpp.llm.mock import MockChatProvider
from opendpp.llm.prompts import build_chat_system
from opendpp.llm.provider import SemanticWarning


@pytest.fixture(autouse=True)
def _force_mock(monkeypatch):
    from opendpp.config import get_settings

    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    get_settings.cache_clear()  # type: ignore[attr-defined]
    get_provider.cache_clear()  # type: ignore[attr-defined]
    yield
    get_settings.cache_clear()  # type: ignore[attr-defined]
    get_provider.cache_clear()  # type: ignore[attr-defined]


def test_factory_returns_mock_when_selected():
    provider = get_provider()
    assert isinstance(provider, MockChatProvider)


async def test_mock_stream_chat_yields_deltas(textile_dpp_data):
    provider = MockChatProvider()
    system = build_chat_system(textile_dpp_data)
    chunks: list[str] = []
    async for chunk in provider.stream_chat(
        system=system, messages=[ChatMessage(role="user", content="What is this?")]
    ):
        chunks.append(chunk)
    joined = "".join(chunks)
    assert "What is this?" in joined or "What is this?".lower() in joined.lower()
    assert len(chunks) > 1, "expected streamed chunks, not one blob"


async def test_mock_translate_prefixes_translatable_strings(textile_dpp_data):
    provider = MockChatProvider()
    translated = await provider.translate(source=textile_dpp_data, target_lang="de")
    assert translated["identification"]["productName"].startswith("[DE] ")
    # GTIN must NOT be translated
    assert translated["identification"]["gtin"] == textile_dpp_data["identification"]["gtin"]
    # Country code must NOT be translated
    assert translated["origin"]["countryOfManufacture"] == "PT"


async def test_mock_translate_passes_through_for_en(textile_dpp_data):
    provider = MockChatProvider()
    translated = await provider.translate(source=textile_dpp_data, target_lang="en")
    assert translated == textile_dpp_data


async def test_mock_validate_semantic_clean_data(textile_dpp_data):
    provider = MockChatProvider()
    warnings = await provider.validate_semantic(dpp_data=textile_dpp_data)
    assert warnings == []


async def test_mock_validate_semantic_catches_bad_percentages():
    provider = MockChatProvider()
    bad = {
        "composition": {
            "materials": [
                {"name": "Cotton", "percentage": 30},
                {"name": "Polyester", "percentage": 40},
            ]
        }
    }
    warnings = await provider.validate_semantic(dpp_data=bad)
    assert len(warnings) == 1
    assert warnings[0].severity == "error"
    assert "70" in warnings[0].message


async def test_chat_endpoint_streams_sse(client, textile_dpp_data):
    # seed product + DPP
    p = await client.post("/api/products", json={"gtin": "01230000000017", "name": "Test"})
    record = await client.post(
        "/api/dpp",
        json={"product_id": p.json()["id"], "data": textile_dpp_data},
    )
    record_id = record.json()["id"]

    r = await client.post(
        f"/api/chat/{record_id}",
        json={"messages": [{"role": "user", "content": "What is this?"}]},
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    assert b"event: delta" in r.content
    assert b"event: done" in r.content


async def test_translate_endpoint_cache_hit(client, textile_dpp_data):
    p = await client.post("/api/products", json={"gtin": "01230000000024", "name": "Test2"})
    record = await client.post(
        "/api/dpp", json={"product_id": p.json()["id"], "data": textile_dpp_data}
    )
    record_id = record.json()["id"]

    r1 = await client.get(f"/api/dpp/{record_id}/translate?lang=de")
    assert r1.status_code == 200
    assert r1.json()["cached"] is False

    r2 = await client.get(f"/api/dpp/{record_id}/translate?lang=de")
    assert r2.status_code == 200
    assert r2.json()["cached"] is True
    assert r2.json()["data"] == r1.json()["data"]


async def test_translate_endpoint_en_is_passthrough(client, textile_dpp_data):
    p = await client.post("/api/products", json={"gtin": "01230000000031", "name": "Test3"})
    record = await client.post(
        "/api/dpp", json={"product_id": p.json()["id"], "data": textile_dpp_data}
    )
    record_id = record.json()["id"]

    r = await client.get(f"/api/dpp/{record_id}/translate?lang=en")
    assert r.status_code == 200
    assert r.json()["lang"] == "en"
    assert r.json()["data"] == textile_dpp_data


async def test_translate_endpoint_404_for_unknown_record(client):
    r = await client.get(
        "/api/dpp/00000000-0000-0000-0000-000000000000/translate?lang=de"
    )
    assert r.status_code == 404


async def test_semantic_validation_endpoint(client, textile_dpp_data):
    r = await client.post(
        "/api/validate/semantic",
        json={"schema_version": "textile-dpp.v1", "data": textile_dpp_data},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["schema_errors"] == []
    assert body["semantic_warnings"] == []


async def test_semantic_validation_flags_bad_percentages(client):
    bad = {
        "composition": {
            "materials": [
                {"name": "Cotton", "percentage": 30},
                {"name": "Polyester", "percentage": 40},
            ]
        }
    }
    r = await client.post("/api/validate/semantic", json={"data": bad})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is False
    # schema validation catches missing required fields
    assert len(body["schema_errors"]) > 0
    # semantic catches the percentage sum
    assert any("70" in w["message"] for w in body["semantic_warnings"])


def test_semantic_warning_dataclass_fields():
    w = SemanticWarning(severity="warning", field="x.y", message="z")
    assert w.severity == "warning"
    assert w.field == "x.y"
    assert w.message == "z"
    assert uuid.UUID  # sanity: imports work
