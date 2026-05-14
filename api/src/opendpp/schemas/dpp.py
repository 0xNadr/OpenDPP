import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    gtin: str = Field(pattern=r"^[0-9]{8}$|^[0-9]{12}$|^[0-9]{13}$|^[0-9]{14}$")
    name: str = Field(min_length=1, max_length=255)
    category: str = Field(default="textile", max_length=64)
    manufacturer: str | None = Field(default=None, max_length=255)


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    gtin: str
    name: str
    category: str
    manufacturer: str | None
    created_at: datetime


class DPPRecordCreate(BaseModel):
    """Create payload for a DPP record.

    `data` is the schema-bound payload (e.g., textile-dpp.v1). It is validated
    against the JSON Schema named by `schema_version` before persistence.
    """

    product_id: uuid.UUID
    lot: str | None = Field(default=None, max_length=20)
    serial: str | None = Field(default=None, max_length=20)
    schema_version: str = Field(default="textile-dpp.v1")
    data: dict[str, Any]


class DPPRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    lot: str | None
    serial: str | None
    schema_version: str
    data: dict[str, Any]
    created_at: datetime
    updated_at: datetime
