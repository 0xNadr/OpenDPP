"""Ed25519 keypairs + did:key encoding/decoding.

did:key is the simplest DID method — the identifier IS the public key,
self-resolving with no external infrastructure. Spec:
    https://w3c-ccg.github.io/did-method-key/

Wire format for Ed25519:
    did:key:z<base58btc(0xed 0x01 || public_key_bytes)>

The 0xed 0x01 prefix is the multicodec varint for ed25519-pub.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import base58
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

# multicodec varint for ed25519-pub (https://github.com/multiformats/multicodec)
ED25519_PUB_MULTICODEC = b"\xed\x01"


@dataclass(frozen=True)
class SupplierKeyMaterial:
    """A supplier's signing material — keep `private_key_bytes` server-side only."""

    did: str
    private_key_bytes: bytes  # 32 bytes
    public_key_bytes: bytes  # 32 bytes

    @property
    def verification_method(self) -> str:
        """did:key DIDs use `<did>#<key fragment>` where the fragment equals
        the multibase identifier (same string after the last colon)."""
        fragment = self.did.rsplit(":", 1)[1]
        return f"{self.did}#{fragment}"

    def private_key(self) -> Ed25519PrivateKey:
        return Ed25519PrivateKey.from_private_bytes(self.private_key_bytes)

    def public_key(self) -> Ed25519PublicKey:
        return Ed25519PublicKey.from_public_bytes(self.public_key_bytes)


def public_key_to_did_key(public_key_bytes: bytes) -> str:
    if len(public_key_bytes) != 32:
        raise ValueError(f"Ed25519 public key must be 32 bytes, got {len(public_key_bytes)}")
    payload = ED25519_PUB_MULTICODEC + public_key_bytes
    multibase = "z" + base58.b58encode(payload).decode("ascii")
    return f"did:key:{multibase}"


def decode_did_key(did: str) -> bytes:
    """Return the raw 32-byte Ed25519 public key encoded in a did:key DID."""
    if not did.startswith("did:key:z"):
        raise ValueError(f"Not a did:key Ed25519 DID: {did!r}")
    payload = base58.b58decode(did[len("did:key:z") :])
    if not payload.startswith(ED25519_PUB_MULTICODEC):
        raise ValueError(f"did:key DID does not encode an Ed25519 public key: {did!r}")
    pk = payload[len(ED25519_PUB_MULTICODEC) :]
    if len(pk) != 32:
        raise ValueError(f"Decoded public key has {len(pk)} bytes, expected 32")
    return pk


def _key_material(private_key: Ed25519PrivateKey) -> SupplierKeyMaterial:
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return SupplierKeyMaterial(
        did=public_key_to_did_key(public_bytes),
        private_key_bytes=private_bytes,
        public_key_bytes=public_bytes,
    )


def generate_keypair() -> SupplierKeyMaterial:
    return _key_material(Ed25519PrivateKey.generate())


def keypair_from_seed(seed: str) -> SupplierKeyMaterial:
    """Deterministic keypair from an arbitrary seed string.

    SHA-256(seed) gives 32 bytes used as the Ed25519 private key. Used for
    the seeded demo suppliers so the same DIDs appear across clones.
    """
    private_bytes = hashlib.sha256(seed.encode("utf-8")).digest()
    return _key_material(Ed25519PrivateKey.from_private_bytes(private_bytes))
