import json
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from opendpp.config import get_settings

SUPPORTED_SCHEMAS: dict[str, Path] = {
    "textile-dpp.v1": get_settings().schema_path,
}


@lru_cache
def get_validator(schema_version: str) -> Draft202012Validator:
    if schema_version not in SUPPORTED_SCHEMAS:
        raise ValueError(f"Unsupported schema_version: {schema_version!r}")
    schema = json.loads(SUPPORTED_SCHEMAS[schema_version].read_text())
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate_dpp_data(schema_version: str, data: dict) -> list[ValidationError]:
    """Return a list of validation errors. Empty list means the data is valid."""
    validator = get_validator(schema_version)
    return list(validator.iter_errors(data))
