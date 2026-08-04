from __future__ import annotations

from typing import Any, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, ValidationError

from polygres._vendor.polygres_lib.context import (
    validate_idempotency_key,
    validate_identifier,
    validate_uuid,
)
from polygres.errors import PolygresValidationError

ModelT = TypeVar("ModelT", bound=BaseModel)


def context_model(
    model_type: type[ModelT],
    payload: dict[str, Any],
    *,
    exclude_unset: bool = False,
) -> tuple[ModelT, dict[str, Any]]:
    try:
        model = model_type.model_validate(payload)
    except ValidationError as exc:
        violations = [
            {
                "field": ".".join(str(part) for part in error["loc"]),
                "rule": error["type"],
            }
            for error in exc.errors(
                include_url=False,
                include_context=False,
                include_input=False,
            )
        ]
        raise PolygresValidationError(
            "Context request validation failed.",
            code="CONTEXT_REQUEST_INVALID",
            details={"violations": violations[:20]},
        ) from exc
    return model, model.model_dump(
        mode="json",
        by_alias=True,
        exclude_unset=exclude_unset,
    )


def context_uuid(value: str | UUID, *, field: str) -> str:
    normalized = str(value) if isinstance(value, UUID) else value
    violations = validate_uuid(normalized, field=field)
    if violations:
        violation = violations[0]
        raise PolygresValidationError(
            f"{field.replace('_', ' ').capitalize()} must be a canonical UUID.",
            code="CONTEXT_REQUEST_INVALID",
            details={"field": violation.field, "rule": violation.rule},
        )
    return normalized


def context_collection(value: str | UUID) -> str:
    if isinstance(value, UUID):
        return str(value)
    if not isinstance(value, str) or not value:
        raise PolygresValidationError(
            "Collection must be a UUID or exact Context collection name.",
            code="CONTEXT_REQUEST_INVALID",
            details={"field": "collection", "rule": "uuid_or_identifier"},
        )
    if not validate_uuid(value, field="collection"):
        return value
    violations = validate_identifier(value, field="collection")
    if violations:
        violation = violations[0]
        raise PolygresValidationError(
            "Collection must be a UUID or exact Context collection name.",
            code="CONTEXT_REQUEST_INVALID",
            details={"field": violation.field, "rule": violation.rule},
        )
    return value


def context_idempotency_key(value: str | None) -> str:
    key = value if value is not None else str(uuid4())
    violations = validate_idempotency_key(key)
    if violations:
        violation = violations[0]
        raise PolygresValidationError(
            "Idempotency key must be 1 to 128 printable ASCII characters.",
            code="CONTEXT_REQUEST_INVALID",
            details={"field": violation.field, "rule": violation.rule},
        )
    return key


def context_query(value: str, *, field: str = "query") -> str:
    if not isinstance(value, str) or not value.strip():
        raise PolygresValidationError(
            "Query must contain non-whitespace text.",
            code="CONTEXT_REQUEST_INVALID",
            details={"field": field, "rule": "non_blank"},
        )
    return value
