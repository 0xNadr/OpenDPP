"""Idempotent seed loader.

Usage (from the repo root, with Postgres running and migrations applied):
    uv run --project api python seed/load_seed.py
"""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from pathlib import Path

from sqlalchemy import select

from opendpp.db import SessionLocal
from opendpp.models import DPPRecord, Product
from opendpp.validation import validate_dpp_data

SEED_FILE = Path(__file__).resolve().parent / "products.json"


async def load() -> None:
    entries = json.loads(SEED_FILE.read_text())
    async with SessionLocal() as session:
        for entry in entries:
            product_payload = entry["product"]
            dpp_payload = entry["dpp"]

            errors = validate_dpp_data(dpp_payload["schema_version"], dpp_payload["data"])
            if errors:
                msgs = "; ".join(e.message for e in errors)
                raise SystemExit(f"seed validation failed for {product_payload['gtin']}: {msgs}")

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

            dpp_exists = (
                await session.execute(
                    select(DPPRecord).where(
                        DPPRecord.product_id == product.id,
                        DPPRecord.lot.is_(dpp_payload.get("lot")) if dpp_payload.get("lot") is None
                        else DPPRecord.lot == dpp_payload.get("lot"),
                        DPPRecord.serial.is_(dpp_payload.get("serial"))
                        if dpp_payload.get("serial") is None
                        else DPPRecord.serial == dpp_payload.get("serial"),
                    )
                )
            ).scalar_one_or_none()
            if dpp_exists is None:
                session.add(
                    DPPRecord(
                        id=uuid.uuid4(),
                        product_id=product.id,
                        lot=dpp_payload.get("lot"),
                        serial=dpp_payload.get("serial"),
                        schema_version=dpp_payload["schema_version"],
                        data=dpp_payload["data"],
                    )
                )
                print(f"seeded DPP for {product_payload['gtin']}")
            else:
                print(f"skipped (already present) {product_payload['gtin']}")
        await session.commit()


if __name__ == "__main__":
    sys.exit(asyncio.run(load()))
