import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opendpp.db import get_session
from opendpp.models import DPPRecord, Product
from opendpp.schemas import (
    DPPRecordCreate,
    DPPRecordRead,
    ProductCreate,
    ProductRead,
)
from opendpp.validation import validate_dpp_data

router = APIRouter(prefix="/api", tags=["dpp"])


@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate, session: AsyncSession = Depends(get_session)
) -> Product:
    product = Product(**payload.model_dump())
    session.add(product)
    try:
        await session.commit()
    except Exception as exc:
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "GTIN already exists") from exc
    await session.refresh(product)
    return product


@router.get("/products/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> Product:
    product = await session.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "product not found")
    return product


@router.post("/dpp", response_model=DPPRecordRead, status_code=status.HTTP_201_CREATED)
async def create_dpp(
    payload: DPPRecordCreate, session: AsyncSession = Depends(get_session)
) -> DPPRecord:
    product = await session.get(Product, payload.product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "product not found")

    errors = validate_dpp_data(payload.schema_version, payload.data)
    if errors:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            {
                "message": "DPP data failed schema validation",
                "errors": [
                    {"path": list(e.absolute_path), "error": e.message} for e in errors
                ],
            },
        )

    record = DPPRecord(
        product_id=payload.product_id,
        lot=payload.lot,
        serial=payload.serial,
        schema_version=payload.schema_version,
        data=payload.data,
    )
    session.add(record)
    try:
        await session.commit()
    except Exception as exc:
        await session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "a DPP record for this (product, lot, serial) already exists",
        ) from exc
    await session.refresh(record)
    return record


@router.get("/dpp/{record_id}", response_model=DPPRecordRead)
async def get_dpp(
    record_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> DPPRecord:
    record = await session.get(DPPRecord, record_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "DPP record not found")
    return record


@router.get("/dpp", response_model=list[DPPRecordRead])
async def list_dpp(session: AsyncSession = Depends(get_session)) -> list[DPPRecord]:
    result = await session.execute(select(DPPRecord).order_by(DPPRecord.created_at.desc()))
    return list(result.scalars().all())
