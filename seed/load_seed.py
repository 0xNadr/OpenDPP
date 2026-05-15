"""Idempotent seed loader.

Seeds products + DPP records, suppliers (with deterministic keypairs),
and one Verifiable Credential per seeded product.

Usage (from inside the api container):
    python /seed/load_seed.py
"""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from pathlib import Path

from sqlalchemy import select

from opendpp.anchor import (
    AnchorNotConfigured,
    canonical_snapshot_hash,
    get_anchor_service,
)
from opendpp.db import SessionLocal
from opendpp.models import (
    AnchorProof,
    DPPRecord,
    Product,
    Supplier,
    VerifiableCredential,
)
from opendpp.validation import validate_dpp_data
from opendpp.vc import SupplierKeyMaterial, issue_credential, keypair_from_seed

SEED_FILE = Path(__file__).resolve().parent / "products.json"

# Suppliers — keys are deterministic from a fixed seed string so the
# DIDs are reproducible across clones. Tied to GTINs in `products.json`.
DEMO_SUPPLIERS: list[dict] = [
    {
        "name": "Atelier Textiles SA",
        "seed": "opendpp-demo:atelier-textiles-sa",
        "gtin": "07350053850010",
        "attestation_type": "OrganicCottonAttestation",
        "claim_template": {
            "material": "Organic Cotton",
            "share": 95,
            "recycledContentPercentage": 0,
            "biobasedContentPercentage": 100,
            "certificationScheme": "GOTS",
            "certificationId": "GOTS-2026-AT-0114",
        },
    },
    {
        "name": "Northwave Apparel GmbH",
        "seed": "opendpp-demo:northwave-apparel-gmbh",
        "gtin": "07350053850027",
        "attestation_type": "RecycledContentAttestation",
        "claim_template": {
            "material": "Recycled Cotton",
            "share": 70,
            "recycledContentPercentage": 100,
            "biobasedContentPercentage": 0,
            "certificationScheme": "GRS",
            "certificationId": "GRS-2026-NW-0042",
        },
    },
    {
        "name": "Soraya Atelier S.r.l.",
        "seed": "opendpp-demo:soraya-atelier-srl",
        "gtin": "07350053850034",
        "attestation_type": "ResponsibleWoolAttestation",
        "claim_template": {
            "material": "Responsible Wool",
            "share": 60,
            "recycledContentPercentage": 0,
            "biobasedContentPercentage": 100,
            "certificationScheme": "RWS",
            "certificationId": "RWS-2026-SOR-0007",
        },
    },
]


async def _seed_supplier(session, spec: dict) -> Supplier:
    existing = (
        await session.execute(select(Supplier).where(Supplier.name == spec["name"]))
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    keys = keypair_from_seed(spec["seed"])
    supplier = Supplier(
        id=uuid.uuid4(),
        name=spec["name"],
        did=keys.did,
        public_key_bytes=keys.public_key_bytes,
        private_key_bytes=keys.private_key_bytes,
    )
    session.add(supplier)
    await session.flush()
    print(f"seeded supplier {spec['name']} -> {keys.did}")
    return supplier


def _subject_id_for(record: DPPRecord) -> str:
    parts = [f"01/{record.data['identification']['gtin']}"]
    if record.lot:
        parts.append(f"10/{record.lot}")
    if record.serial:
        parts.append(f"21/{record.serial}")
    return "urn:gs1-dl:/" + "/".join(parts)


async def _seed_credential(
    session, supplier: Supplier, record: DPPRecord, spec: dict
) -> None:
    existing = (
        await session.execute(
            select(VerifiableCredential).where(
                VerifiableCredential.dpp_record_id == record.id,
                VerifiableCredential.supplier_id == supplier.id,
                VerifiableCredential.attestation_type == spec["attestation_type"],
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return

    key_material = SupplierKeyMaterial(
        did=supplier.did,
        private_key_bytes=supplier.private_key_bytes,
        public_key_bytes=supplier.public_key_bytes,
    )
    jwt, body = issue_credential(
        supplier=key_material,
        subject_id=_subject_id_for(record),
        attestation_type=spec["attestation_type"],
        claim=spec["claim_template"],
    )
    session.add(
        VerifiableCredential(
            id=uuid.uuid4(),
            dpp_record_id=record.id,
            supplier_id=supplier.id,
            attestation_type=spec["attestation_type"],
            subject_id=_subject_id_for(record),
            jwt=jwt,
            body=body,
        )
    )
    print(f"  issued VC: {spec['attestation_type']} -> {supplier.name}")


async def load() -> None:
    entries = json.loads(SEED_FILE.read_text())
    suppliers_by_gtin: dict[str, dict] = {s["gtin"]: s for s in DEMO_SUPPLIERS}

    async with SessionLocal() as session:
        for entry in entries:
            product_payload = entry["product"]
            dpp_payload = entry["dpp"]

            errors = validate_dpp_data(dpp_payload["schema_version"], dpp_payload["data"])
            if errors:
                msgs = "; ".join(e.message for e in errors)
                raise SystemExit(
                    f"seed validation failed for {product_payload['gtin']}: {msgs}"
                )

            existing = (
                await session.execute(
                    select(Product).where(Product.gtin == product_payload["gtin"])
                )
            ).scalar_one_or_none()
            if existing is None:
                product = Product(id=uuid.uuid4(), **product_payload)
                session.add(product)
                await session.flush()
            else:
                product = existing

            lot = dpp_payload.get("lot")
            serial = dpp_payload.get("serial")
            record = (
                await session.execute(
                    select(DPPRecord).where(
                        DPPRecord.product_id == product.id,
                        DPPRecord.lot.is_(lot) if lot is None else DPPRecord.lot == lot,
                        DPPRecord.serial.is_(serial)
                        if serial is None
                        else DPPRecord.serial == serial,
                    )
                )
            ).scalar_one_or_none()
            if record is None:
                record = DPPRecord(
                    id=uuid.uuid4(),
                    product_id=product.id,
                    lot=lot,
                    serial=serial,
                    schema_version=dpp_payload["schema_version"],
                    data=dpp_payload["data"],
                )
                session.add(record)
                await session.flush()
                print(f"seeded DPP for {product_payload['gtin']}")
            else:
                print(f"skipped (already present) {product_payload['gtin']}")

            spec = suppliers_by_gtin.get(product_payload["gtin"])
            if spec is not None:
                supplier = await _seed_supplier(session, spec)
                await _seed_credential(session, supplier, record, spec)

            await _seed_anchor(session, record)

        await session.commit()


async def _seed_anchor(session, record: DPPRecord) -> None:
    snapshot = canonical_snapshot_hash(record.data)
    existing = (
        await session.execute(
            select(AnchorProof).where(
                AnchorProof.dpp_record_id == record.id,
                AnchorProof.snapshot_hash == snapshot,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return

    service = get_anchor_service()
    if not service.configured:
        print(f"  skipped anchor for {record.data['identification']['gtin']} (service not configured)")
        return

    try:
        receipt = service.anchor(snapshot)
    except AnchorNotConfigured:
        print(f"  skipped anchor for {record.data['identification']['gtin']} (not configured)")
        return
    except Exception as exc:  # noqa: BLE001
        print(f"  failed to anchor {record.data['identification']['gtin']}: {exc}")
        return

    session.add(
        AnchorProof(
            id=uuid.uuid4(),
            dpp_record_id=record.id,
            chain=receipt.chain,
            snapshot_hash=receipt.snapshot_hash,
            tx_hash=receipt.tx_hash,
            block_number=receipt.block_number,
            explorer_tx_url=receipt.explorer_tx_url,
            anchored_at=receipt.anchored_at,
        )
    )
    print(f"  anchored on {receipt.chain}: {receipt.tx_hash}")


if __name__ == "__main__":
    sys.exit(asyncio.run(load()))
