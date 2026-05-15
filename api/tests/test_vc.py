import base64
import json

import pytest

from opendpp.vc import (
    decode_did_key,
    generate_keypair,
    issue_credential,
    keypair_from_seed,
    public_key_to_did_key,
    verify_credential,
)


def test_did_key_roundtrip():
    keys = generate_keypair()
    assert keys.did.startswith("did:key:z")
    decoded = decode_did_key(keys.did)
    assert decoded == keys.public_key_bytes


def test_keypair_from_seed_is_deterministic():
    a = keypair_from_seed("opendpp:test-seed-1")
    b = keypair_from_seed("opendpp:test-seed-1")
    assert a.did == b.did
    assert a.private_key_bytes == b.private_key_bytes


def test_public_key_to_did_key_validates_length():
    with pytest.raises(ValueError, match="32 bytes"):
        public_key_to_did_key(b"too short")


def test_decode_did_key_rejects_non_key():
    with pytest.raises(ValueError, match="did:key"):
        decode_did_key("did:web:example.com")


def test_decode_did_key_rejects_wrong_multicodec():
    # build a did:key with a bogus multicodec prefix
    import base58

    bogus = base58.b58encode(b"\x00\x01" + b"a" * 32).decode("ascii")
    with pytest.raises(ValueError, match="Ed25519"):
        decode_did_key(f"did:key:z{bogus}")


def test_issue_and_verify_roundtrip():
    keys = keypair_from_seed("test:issuer")
    jwt, body = issue_credential(
        supplier=keys,
        subject_id="urn:gs1-dl:/01/07350053850010/10/ATL-2026-T01",
        attestation_type="OrganicCottonAttestation",
        claim={"material": "Organic Cotton", "share": 95},
    )
    result = verify_credential(jwt)
    assert result.valid
    assert result.issuer == keys.did
    assert result.subject == "urn:gs1-dl:/01/07350053850010/10/ATL-2026-T01"
    assert result.claims["type"] == ["VerifiableCredential", "OrganicCottonAttestation"]
    assert result.claims["credentialSubject"]["share"] == 95
    assert body["issuer"] == keys.did


def test_verify_detects_tampered_signature():
    keys = keypair_from_seed("test:issuer")
    jwt, _ = issue_credential(
        supplier=keys,
        subject_id="urn:example:product/1",
        attestation_type="ExampleAttestation",
        claim={"foo": "bar"},
    )
    tampered = jwt[:-4] + "AAAA"
    result = verify_credential(tampered)
    assert not result.valid
    assert result.error == "signature is invalid"


def test_verify_detects_tampered_payload():
    keys = keypair_from_seed("test:issuer")
    jwt, _ = issue_credential(
        supplier=keys,
        subject_id="urn:example:product/1",
        attestation_type="ExampleAttestation",
        claim={"share": 95},
    )
    header, payload, sig = jwt.split(".")
    decoded = json.loads(base64.urlsafe_b64decode(payload + "=="))
    decoded["vc"]["credentialSubject"]["share"] = 5  # downgrade the claim
    tampered_payload = (
        base64.urlsafe_b64encode(json.dumps(decoded).encode())
        .rstrip(b"=")
        .decode("ascii")
    )
    tampered = f"{header}.{tampered_payload}.{sig}"
    result = verify_credential(tampered)
    assert not result.valid
    assert result.error == "signature is invalid"


def test_verify_rejects_wrong_issuer_key():
    issuer = keypair_from_seed("test:legit-issuer")
    impostor = keypair_from_seed("test:impostor")
    jwt, _ = issue_credential(
        supplier=issuer,
        subject_id="urn:example:product/1",
        attestation_type="ExampleAttestation",
        claim={"foo": "bar"},
    )
    # rewrite the iss claim to point at the impostor — signature won't verify
    header, payload_b64, sig = jwt.split(".")
    payload = json.loads(base64.urlsafe_b64decode(payload_b64 + "=="))
    payload["iss"] = impostor.did
    new_payload_b64 = (
        base64.urlsafe_b64encode(json.dumps(payload).encode())
        .rstrip(b"=")
        .decode("ascii")
    )
    forged = f"{header}.{new_payload_b64}.{sig}"
    result = verify_credential(forged)
    assert not result.valid


def test_verify_rejects_malformed_jwt():
    result = verify_credential("not.a.real.jwt.format")
    assert not result.valid
    assert "three dot-separated parts" in (result.error or "")


async def _seed_supplier_record(client, textile_dpp_data):
    p = await client.post("/api/products", json={"gtin": "07350053850099", "name": "Test"})
    record = await client.post(
        "/api/dpp", json={"product_id": p.json()["id"], "data": textile_dpp_data}
    )
    return record.json()["id"]


async def test_endpoint_issue_returns_signed_jwt(client, textile_dpp_data, engine):
    # Need a supplier in the test DB
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from opendpp.models import Supplier

    keys = keypair_from_seed("test:endpoint-issuer")
    sm = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with sm() as s:
        supplier = Supplier(
            name="Test Supplier",
            did=keys.did,
            public_key_bytes=keys.public_key_bytes,
            private_key_bytes=keys.private_key_bytes,
        )
        s.add(supplier)
        await s.commit()
        await s.refresh(supplier)
        supplier_id = str(supplier.id)

    record_id = await _seed_supplier_record(client, textile_dpp_data)
    r = await client.post(
        "/api/vc/issue",
        json={
            "supplier_id": supplier_id,
            "dpp_record_id": record_id,
            "attestation_type": "ExampleAttestation",
            "claim": {"material": "Organic Cotton", "share": 95},
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["jwt"].count(".") == 2
    assert body["supplier_did"] == keys.did

    # Verify endpoint accepts the freshly minted JWT
    v = await client.post("/api/vc/verify", json={"jwt": body["jwt"]})
    assert v.status_code == 200
    assert v.json()["valid"] is True


async def test_endpoint_verify_tampered(client):
    r = await client.post(
        "/api/vc/verify", json={"jwt": "header.payload.signature"}
    )
    assert r.status_code == 200
    assert r.json()["valid"] is False
