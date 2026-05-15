"""On-chain snapshot-hash anchoring.

Reads the deployed contract address from the shared deployment artifact
(`/contracts/deployments/{chain}.json`, populated by the hardhat container
on startup) or from `ANCHOR_CONTRACT_ADDRESS` for production targets.

`anchor()` and `verify()` are sync — they're called from FastAPI handlers
via `run_in_threadpool` so the async loop stays unblocked.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from eth_account import Account
from web3 import Web3
from web3.exceptions import TransactionNotFound

from opendpp.anchor.abi import OPENDPP_ANCHOR_ABI
from opendpp.config import get_settings

logger = logging.getLogger(__name__)


def canonical_snapshot_hash(data: dict[str, Any]) -> bytes:
    """Return the 32-byte SHA-256 of the DPP data using a deterministic
    serialization (sorted keys, no whitespace, UTF-8). This is what gets
    anchored on-chain.
    """
    canonical = json.dumps(
        data, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).digest()


@dataclass(frozen=True)
class AnchorReceipt:
    snapshot_hash: bytes
    tx_hash: str
    block_number: int
    anchored_at: datetime
    chain: str
    explorer_tx_url: str | None


@dataclass(frozen=True)
class AnchorVerification:
    snapshot_hash: bytes
    anchored: bool
    on_chain_timestamp: int  # 0 if not anchored
    chain: str


class AnchorNotConfigured(RuntimeError):
    """Raised when the anchor service is asked to do work without a
    deployed contract address or a signing key."""


class AnchorService:
    def __init__(
        self,
        *,
        rpc_url: str,
        private_key: str | None,
        contract_address: str | None,
        chain_label: str,
        explorer_tx_template: str | None,
    ) -> None:
        self._rpc_url = rpc_url
        self._private_key = private_key
        self._contract_address = contract_address
        self._chain_label = chain_label
        self._explorer_tx_template = explorer_tx_template

    @property
    def chain_label(self) -> str:
        return self._chain_label

    @property
    def contract_address(self) -> str | None:
        return self._contract_address

    @property
    def configured(self) -> bool:
        return bool(self._private_key and self._contract_address)

    def _w3(self) -> Web3:
        return Web3(Web3.HTTPProvider(self._rpc_url, request_kwargs={"timeout": 30}))

    def _contract(self, w3: Web3):
        if not self._contract_address:
            raise AnchorNotConfigured("contract address is not configured")
        return w3.eth.contract(
            address=Web3.to_checksum_address(self._contract_address),
            abi=OPENDPP_ANCHOR_ABI,
        )

    def explorer_url(self, tx_hash: str) -> str | None:
        if not self._explorer_tx_template:
            return None
        return self._explorer_tx_template.replace("{tx}", tx_hash)

    def anchor(self, snapshot_hash: bytes) -> AnchorReceipt:
        """Send an `anchor(bytes32)` transaction and wait for the receipt."""
        if not self.configured:
            raise AnchorNotConfigured(
                "anchor service is missing private key or contract address"
            )

        w3 = self._w3()
        contract = self._contract(w3)
        account = Account.from_key(self._private_key)

        nonce = w3.eth.get_transaction_count(account.address)
        # Use legacy `gasPrice` for broad compatibility across Hardhat + Amoy.
        gas_price = w3.eth.gas_price

        tx = contract.functions.anchor(snapshot_hash).build_transaction({
            "from": account.address,
            "nonce": nonce,
            "gasPrice": gas_price,
            "chainId": w3.eth.chain_id,
        })
        # Let web3 fill `gas` if not estimated; explicit estimate keeps it tight.
        tx["gas"] = w3.eth.estimate_gas(tx)

        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        if receipt.status != 1:
            raise RuntimeError(f"anchor tx reverted: {receipt}")

        block = w3.eth.get_block(receipt.blockNumber)
        anchored_at = datetime.fromtimestamp(block.timestamp, tz=UTC)

        tx_hex = receipt.transactionHash.hex()
        if not tx_hex.startswith("0x"):
            tx_hex = "0x" + tx_hex

        return AnchorReceipt(
            snapshot_hash=snapshot_hash,
            tx_hash=tx_hex,
            block_number=int(receipt.blockNumber),
            anchored_at=anchored_at,
            chain=self._chain_label,
            explorer_tx_url=self.explorer_url(tx_hex),
        )

    def verify(self, snapshot_hash: bytes) -> AnchorVerification:
        """Query the contract directly to confirm a hash is anchored.

        This is the path an external auditor would use — no OpenDPP DB
        involved, just the public chain.
        """
        w3 = self._w3()
        contract = self._contract(w3)
        ts = contract.functions.anchoredAt(snapshot_hash).call()
        return AnchorVerification(
            snapshot_hash=snapshot_hash,
            anchored=bool(ts > 0),
            on_chain_timestamp=int(ts),
            chain=self._chain_label,
        )

    def tx_receipt_status(self, tx_hash: str) -> int | None:
        """1 = success, 0 = reverted, None = not found yet. Used by tests."""
        try:
            r = self._w3().eth.get_transaction_receipt(tx_hash)
        except TransactionNotFound:
            return None
        return int(r.status)


def _load_contract_address(settings) -> str | None:
    if settings.anchor_contract_address:
        return settings.anchor_contract_address
    path = Path(settings.anchor_deployment_path)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text()).get("address")
    except (OSError, json.JSONDecodeError):
        logger.exception("could not read anchor deployment artifact at %s", path)
        return None


@lru_cache
def get_anchor_service() -> AnchorService:
    settings = get_settings()
    return AnchorService(
        rpc_url=settings.anchor_rpc_url,
        private_key=settings.anchor_private_key,
        contract_address=_load_contract_address(settings),
        chain_label=settings.anchor_chain_label,
        explorer_tx_template=settings.anchor_explorer_tx_template or None,
    )
