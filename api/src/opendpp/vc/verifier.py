"""Verify a VC-JWT signed with Ed25519 and a did:key issuer.

Verification path:
  1. Decode JWS header + payload.
  2. Resolve the issuer DID (did:key is self-resolving — the key is in the ID).
  3. Verify the Ed25519 signature over `header.payload`.
  4. Spot-check the credential body invariants (issuer match, expiry).
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from opendpp.vc.keys import decode_did_key


@dataclass(frozen=True)
class VerificationResult:
    valid: bool
    issuer: str | None
    subject: str | None
    claims: dict[str, Any]
    error: str | None = None


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def verify_credential(jwt: str) -> VerificationResult:
    """Verify a VC-JWT and return a structured result. Never raises."""
    parts = jwt.split(".")
    if len(parts) != 3:
        return VerificationResult(
            False, None, None, {}, "JWT must have three dot-separated parts"
        )
    header_b64, payload_b64, signature_b64 = parts

    try:
        header = json.loads(_b64url_decode(header_b64))
        payload = json.loads(_b64url_decode(payload_b64))
        signature = _b64url_decode(signature_b64)
    except (ValueError, json.JSONDecodeError) as exc:
        return VerificationResult(False, None, None, {}, f"malformed JWT: {exc}")

    if header.get("alg") != "EdDSA":
        return VerificationResult(False, None, None, {}, f"unsupported alg: {header.get('alg')!r}")

    issuer = payload.get("iss")
    if not isinstance(issuer, str):
        return VerificationResult(False, None, None, {}, "missing or non-string iss claim")

    try:
        pub_bytes = decode_did_key(issuer)
    except ValueError as exc:
        return VerificationResult(False, issuer, None, {}, f"cannot resolve issuer DID: {exc}")

    pub_key = Ed25519PublicKey.from_public_bytes(pub_bytes)
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    try:
        pub_key.verify(signature, signing_input)
    except InvalidSignature:
        return VerificationResult(False, issuer, payload.get("sub"), {}, "signature is invalid")

    vc = payload.get("vc")
    if not isinstance(vc, dict):
        return VerificationResult(False, issuer, payload.get("sub"), {}, "missing vc claim")
    if vc.get("issuer") != issuer:
        return VerificationResult(
            False,
            issuer,
            payload.get("sub"),
            {},
            "issuer mismatch between JWT iss and vc.issuer",
        )

    # Optional validity-window checks (validFrom / validUntil)
    now = datetime.now(UTC)
    valid_from = vc.get("validFrom")
    if isinstance(valid_from, str):
        try:
            if datetime.fromisoformat(valid_from.replace("Z", "+00:00")) > now:
                return VerificationResult(
                    False, issuer, payload.get("sub"), vc, "credential not yet valid"
                )
        except ValueError:
            pass

    valid_until = vc.get("validUntil")
    if isinstance(valid_until, str):
        try:
            if datetime.fromisoformat(valid_until.replace("Z", "+00:00")) < now:
                return VerificationResult(
                    False, issuer, payload.get("sub"), vc, "credential has expired"
                )
        except ValueError:
            pass

    return VerificationResult(
        valid=True,
        issuer=issuer,
        subject=payload.get("sub"),
        claims=vc,
    )
