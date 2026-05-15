"""Unit + endpoint tests for the anchor layer.

The endpoint tests bypass the real web3 client by patching the anchor
service's `anchor` / `verify` methods, so they don't require a live chain.
A separate live test against the running hardhat container is exercised
end-to-end via `make seed` and the curl smoke tests in the README; we
don't reach across to it from pytest to keep the unit suite hermetic.
"""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from opendpp.anchor import (
    AnchorNotConfigured,
    AnchorReceipt,
    AnchorVerification,
    canonical_snapshot_hash,
    get_anchor_service,
)


def test_canonical_hash_is_stable_under_key_reordering():
    a = canonical_snapshot_hash({"b": 1, "a": 2, "nested": {"y": 1, "x": 2}})
    b = canonical_snapshot_hash({"a": 2, "b": 1, "nested": {"x": 2, "y": 1}})
    assert a == b
    assert len(a) == 32


def test_canonical_hash_changes_with_content():
    a = canonical_snapshot_hash({"a": 1})
    b = canonical_snapshot_hash({"a": 2})
    assert a != b


def test_canonical_hash_handles_unicode():
    h = canonical_snapshot_hash({"name": "تي شيرت"})
    assert len(h) == 32


@pytest.fixture(autouse=True)
def _reset_anchor_cache():
    get_anchor_service.cache_clear()  # type: ignore[attr-defined]
    yield
    get_anchor_service.cache_clear()  # type: ignore[attr-defined]


async def _seed_record(client, textile_dpp_data, gtin: str):
    p = await client.post("/api/products", json={"gtin": gtin, "name": "Test"})
    r = await client.post(
        "/api/dpp", json={"product_id": p.json()["id"], "data": textile_dpp_data}
    )
    return r.json()["id"]


async def test_anchor_endpoint_persists_proof(client, textile_dpp_data):
    record_id = await _seed_record(client, textile_dpp_data, "01230000000048")

    fake_receipt = AnchorReceipt(
        snapshot_hash=canonical_snapshot_hash(textile_dpp_data),
        tx_hash="0x" + "ab" * 32,
        block_number=42,
        anchored_at=datetime(2026, 5, 15, 16, 30, tzinfo=UTC),
        chain="testnet",
        explorer_tx_url="https://example.com/tx/0x" + "ab" * 32,
    )

    with patch(
        "opendpp.routers.anchor.get_anchor_service"
    ) as mock_get:
        mock_get.return_value.anchor.return_value = fake_receipt
        r = await client.post(f"/api/anchor/{record_id}")

    assert r.status_code == 201
    body = r.json()
    assert body["tx_hash"] == fake_receipt.tx_hash
    assert body["block_number"] == 42
    assert body["chain"] == "testnet"
    assert body["snapshot_hash"].startswith("0x")


async def test_anchor_endpoint_returns_existing_proof_idempotently(
    client, textile_dpp_data
):
    record_id = await _seed_record(client, textile_dpp_data, "01230000000055")
    fake_receipt = AnchorReceipt(
        snapshot_hash=canonical_snapshot_hash(textile_dpp_data),
        tx_hash="0x" + "cd" * 32,
        block_number=7,
        anchored_at=datetime(2026, 5, 15, tzinfo=UTC),
        chain="testnet",
        explorer_tx_url=None,
    )

    with patch("opendpp.routers.anchor.get_anchor_service") as mock_get:
        mock_get.return_value.anchor.return_value = fake_receipt
        first = await client.post(f"/api/anchor/{record_id}")
        # Second call should not invoke the chain again
        mock_get.return_value.anchor.reset_mock()
        second = await client.post(f"/api/anchor/{record_id}")

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    mock_get.return_value.anchor.assert_not_called()


async def test_anchor_endpoint_503_when_service_not_configured(
    client, textile_dpp_data
):
    record_id = await _seed_record(client, textile_dpp_data, "01230000000062")
    with patch("opendpp.routers.anchor.get_anchor_service") as mock_get:
        mock_get.return_value.anchor.side_effect = AnchorNotConfigured("no key")
        r = await client.post(f"/api/anchor/{record_id}")
    assert r.status_code == 503


async def test_verify_endpoint_reports_chain_match(client, textile_dpp_data):
    record_id = await _seed_record(client, textile_dpp_data, "01230000000079")
    expected = canonical_snapshot_hash(textile_dpp_data)

    fake_receipt = AnchorReceipt(
        snapshot_hash=expected,
        tx_hash="0x" + "ef" * 32,
        block_number=99,
        anchored_at=datetime(2026, 5, 15, tzinfo=UTC),
        chain="testnet",
        explorer_tx_url=None,
    )
    fake_verify = AnchorVerification(
        snapshot_hash=expected,
        anchored=True,
        on_chain_timestamp=1700000000,
        chain="testnet",
    )

    with patch("opendpp.routers.anchor.get_anchor_service") as mock_get:
        mock_get.return_value.anchor.return_value = fake_receipt
        mock_get.return_value.verify.return_value = fake_verify
        await client.post(f"/api/anchor/{record_id}")
        r = await client.get(f"/api/anchor/{record_id}/verify")

    assert r.status_code == 200
    body = r.json()
    assert body["anchored"] is True
    assert body["matches_stored_proof"] is True
    assert body["current_snapshot_hash"] == "0x" + expected.hex()


async def test_verify_endpoint_reports_no_anchor_when_unanchored(
    client, textile_dpp_data
):
    record_id = await _seed_record(client, textile_dpp_data, "01230000000086")
    expected = canonical_snapshot_hash(textile_dpp_data)
    with patch("opendpp.routers.anchor.get_anchor_service") as mock_get:
        mock_get.return_value.verify.return_value = AnchorVerification(
            snapshot_hash=expected,
            anchored=False,
            on_chain_timestamp=0,
            chain="testnet",
        )
        r = await client.get(f"/api/anchor/{record_id}/verify")
    assert r.status_code == 200
    body = r.json()
    assert body["anchored"] is False
    assert body["matches_stored_proof"] is False


async def test_anchor_404_for_unknown_record(client):
    r = await client.post(
        "/api/anchor/00000000-0000-0000-0000-000000000000"
    )
    assert r.status_code == 404


async def test_list_proofs_empty_for_unanchored_record(client, textile_dpp_data):
    record_id = await _seed_record(client, textile_dpp_data, "01230000000093")
    r = await client.get(f"/api/anchor/{record_id}/proof")
    assert r.status_code == 200
    assert r.json() == []


async def test_list_proofs_includes_anchored_record(client, textile_dpp_data):
    record_id = await _seed_record(client, textile_dpp_data, "01230000000109")
    fake_receipt = AnchorReceipt(
        snapshot_hash=canonical_snapshot_hash(textile_dpp_data),
        tx_hash="0x" + "12" * 32,
        block_number=100,
        anchored_at=datetime(2026, 5, 15, tzinfo=UTC),
        chain="testnet",
        explorer_tx_url=None,
    )
    with patch("opendpp.routers.anchor.get_anchor_service") as mock_get:
        mock_get.return_value.anchor.return_value = fake_receipt
        await client.post(f"/api/anchor/{record_id}")
    r = await client.get(f"/api/anchor/{record_id}/proof")
    assert r.status_code == 200
    proofs = r.json()
    assert len(proofs) == 1
    assert proofs[0]["tx_hash"] == fake_receipt.tx_hash
