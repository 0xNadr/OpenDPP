"""Issue a W3C Verifiable Credential in VC-JWT form.

The credential body is embedded in the JWT payload under the `vc` claim,
per the JWT serialization defined in W3C VC Data Model 2.0:
    https://www.w3.org/TR/vc-data-model-2.0/#json-web-token

We sign with Ed25519 (alg=EdDSA), the simplest interoperable choice that
pairs cleanly with did:key.
"""

from __future__ import annotations

import base64
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from opendpp.vc.keys import SupplierKeyMaterial

CREDENTIAL_CONTEXT_V2 = "https://www.w3.org/ns/credentials/v2"
OPENDPP_CONTEXT_V1 = "https://opendpp.org/contexts/v1"


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_credential_body(
    *,
    issuer_did: str,
    subject_id: str,
    attestation_type: str,
    claim: dict[str, Any],
    valid_from: str | None = None,
) -> dict[str, Any]:
    """Return the unsigned W3C VC body (the `vc` claim of the JWT)."""
    return {
        "@context": [CREDENTIAL_CONTEXT_V2, OPENDPP_CONTEXT_V1],
        "id": f"urn:uuid:{uuid.uuid4()}",
        "type": ["VerifiableCredential", attestation_type],
        "issuer": issuer_did,
        "validFrom": valid_from or _now_iso(),
        "credentialSubject": {"id": subject_id, **claim},
    }


def issue_credential(
    *,
    supplier: SupplierKeyMaterial,
    subject_id: str,
    attestation_type: str,
    claim: dict[str, Any],
    valid_from: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Sign a credential and return `(jwt, vc_body)`.

    The returned `vc_body` is the unsigned credential (without `proof`) so
    the API can persist it for inspection in regulator views.
    """
    vc_body = build_credential_body(
        issuer_did=supplier.did,
        subject_id=subject_id,
        attestation_type=attestation_type,
        claim=claim,
        valid_from=valid_from,
    )

    header = {
        "alg": "EdDSA",
        "typ": "vc+jwt",
        "kid": supplier.verification_method,
    }
    payload = {
        "iss": supplier.did,
        "sub": subject_id,
        "jti": vc_body["id"],
        "iat": int(datetime.now(UTC).timestamp()),
        "vc": vc_body,
    }

    signing_input = (
        _b64url(json.dumps(header, separators=(",", ":"), sort_keys=True).encode())
        + "."
        + _b64url(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    )
    signature = supplier.private_key().sign(signing_input.encode("ascii"))
    jwt = f"{signing_input}.{_b64url(signature)}"
    return jwt, vc_body
