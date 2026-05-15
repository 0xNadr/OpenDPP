"""LLM-assisted semantic validation for candidate DPP data.

JSON Schema validation already runs on `POST /api/dpp`; this endpoint
catches what the schema can't — internal inconsistencies and implausible
values (percentages that don't sum to 100, expired certifications, etc).
"""

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from opendpp.llm import get_provider
from opendpp.validation import validate_dpp_data

router = APIRouter(prefix="/api/validate", tags=["validate"])


class SemanticValidateRequest(BaseModel):
    schema_version: str = Field(default="textile-dpp.v1")
    data: dict[str, Any]


@router.post("/semantic")
async def validate_semantic(payload: SemanticValidateRequest) -> dict:
    schema_errors = validate_dpp_data(payload.schema_version, payload.data)
    schema_issues = [
        {"path": list(e.absolute_path), "error": e.message} for e in schema_errors
    ]

    provider = get_provider()
    warnings = await provider.validate_semantic(dpp_data=payload.data)
    return {
        "schema_errors": schema_issues,
        "semantic_warnings": [asdict(w) for w in warnings],
        "ok": not schema_issues and not warnings,
    }
