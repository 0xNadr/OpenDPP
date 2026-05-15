"""Verifiable Credential issue / verify / list endpoints."""

import uuid
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opendpp.db import get_session
from opendpp.models import DPPRecord, Supplier, VerifiableCredential
from opendpp.vc import (
    SupplierKeyMaterial,
    issue_credential,
    verify_credential,
)

router = APIRouter(prefix="/api/vc", tags=["vc"])


class IssueRequest(BaseModel):
    supplier_id: uuid.UUID
    dpp_record_id: uuid.UUID
    attestation_type: str = Field(default="RecycledContentAttestation", max_length=128)
    subject_id: str | None = Field(default=None, max_length=512)
    claim: dict[str, Any]


class IssueResponse(BaseModel):
    id: uuid.UUID
    jwt: str
    body: dict[str, Any]
    supplier_did: str


class VerifyRequest(BaseModel):
    jwt: str


class VerifyResponse(BaseModel):
    valid: bool
    issuer: str | None
    subject: str | None
    claims: dict[str, Any]
    error: str | None = None


class CredentialOut(BaseModel):
    id: uuid.UUID
    attestation_type: str
    subject_id: str
    jwt: str
    body: dict[str, Any]
    supplier: dict[str, str]


def _supplier_to_key_material(supplier: Supplier) -> SupplierKeyMaterial:
    return SupplierKeyMaterial(
        did=supplier.did,
        private_key_bytes=supplier.private_key_bytes,
        public_key_bytes=supplier.public_key_bytes,
    )


@router.post("/issue", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
async def issue(
    payload: IssueRequest,
    session: AsyncSession = Depends(get_session),
) -> VerifiableCredential:
    supplier = await session.get(Supplier, payload.supplier_id)
    if supplier is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "supplier not found")
    record = await session.get(DPPRecord, payload.dpp_record_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "DPP record not found")

    subject_id = payload.subject_id or _default_subject_id(record)

    jwt, body = issue_credential(
        supplier=_supplier_to_key_material(supplier),
        subject_id=subject_id,
        attestation_type=payload.attestation_type,
        claim=payload.claim,
    )

    vc = VerifiableCredential(
        dpp_record_id=record.id,
        supplier_id=supplier.id,
        attestation_type=payload.attestation_type,
        subject_id=subject_id,
        jwt=jwt,
        body=body,
    )
    session.add(vc)
    await session.commit()
    await session.refresh(vc)
    return IssueResponse(
        id=vc.id,
        jwt=vc.jwt,
        body=vc.body,
        supplier_did=supplier.did,
    )


@router.post("/verify", response_model=VerifyResponse)
async def verify(payload: VerifyRequest) -> VerifyResponse:
    result = verify_credential(payload.jwt)
    return VerifyResponse(**asdict(result))


@router.get("/dpp/{record_id}", response_model=list[CredentialOut])
async def list_for_dpp(
    record_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> list[CredentialOut]:
    record = await session.get(DPPRecord, record_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "DPP record not found")
    rows = (
        await session.execute(
            select(VerifiableCredential, Supplier)
            .join(Supplier, VerifiableCredential.supplier_id == Supplier.id)
            .where(VerifiableCredential.dpp_record_id == record_id)
            .order_by(VerifiableCredential.created_at.desc())
        )
    ).all()
    return [
        CredentialOut(
            id=vc.id,
            attestation_type=vc.attestation_type,
            subject_id=vc.subject_id,
            jwt=vc.jwt,
            body=vc.body,
            supplier={"name": supplier.name, "did": supplier.did},
        )
        for (vc, supplier) in rows
    ]


def _default_subject_id(record: DPPRecord) -> str:
    """Build a stable subject identifier from the DPP record's GS1 path."""
    parts = [f"01/{record.data['identification']['gtin']}"]
    if record.lot:
        parts.append(f"10/{record.lot}")
    if record.serial:
        parts.append(f"21/{record.serial}")
    return "urn:gs1-dl:/" + "/".join(parts)
