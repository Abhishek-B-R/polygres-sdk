from __future__ import annotations

import math
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from polygres._vendor.polygres_lib.errors import ERROR_CATALOG
from polygres.errors import (
    PolygresAmbiguousWriteError,
    PolygresAPIError,
    PolygresError,
    PolygresValidationError,
)
from polygres.models import RowWriteResult, RowWriteValidation

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class RowsNamespace:
    def __init__(self, project: Any) -> None:
        self._project = project

    def validate(
        self,
        *,
        schema: str,
        table: str,
        row: dict[str, Any],
        mode: str = "insert",
        conflict_columns: list[str] | None = None,
        update_columns: list[str] | None = None,
        returning: list[str] | None = None,
        reconcile_context: bool = False,
        context_collection_id: str | UUID | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> RowWriteValidation:
        payload, _ = _payload(
            schema=schema,
            table=table,
            row=row,
            mode=mode,
            conflict_columns=conflict_columns,
            update_columns=update_columns,
            returning=returning,
            reconcile_context=reconcile_context,
            context_collection_id=context_collection_id,
            idempotency_key=None,
            execution=False,
        )
        response = self._project._client._post(
            _path(schema, table, validate=True),
            payload,
            timeout=timeout,
            retryable=True,
        )
        return RowWriteValidation.from_api(response)

    def insert(
        self,
        *,
        schema: str,
        table: str,
        row: dict[str, Any],
        returning: list[str] | None = None,
        reconcile_context: bool = False,
        context_collection_id: str | UUID | None = None,
        idempotency_key: str | None = None,
        wait_for_context: bool = False,
        wait_timeout: float = 300.0,
        timeout: float | httpx.Timeout | None = None,
    ) -> RowWriteResult:
        return self._write(
            schema=schema,
            table=table,
            row=row,
            mode="insert",
            returning=returning,
            reconcile_context=reconcile_context,
            context_collection_id=context_collection_id,
            idempotency_key=idempotency_key,
            wait_for_context=wait_for_context,
            wait_timeout=wait_timeout,
            timeout=timeout,
        )

    def upsert(
        self,
        *,
        schema: str,
        table: str,
        row: dict[str, Any],
        conflict_columns: list[str],
        update_columns: list[str] | None = None,
        returning: list[str] | None = None,
        reconcile_context: bool = False,
        context_collection_id: str | UUID | None = None,
        idempotency_key: str | None = None,
        wait_for_context: bool = False,
        wait_timeout: float = 300.0,
        timeout: float | httpx.Timeout | None = None,
    ) -> RowWriteResult:
        return self._write(
            schema=schema,
            table=table,
            row=row,
            mode="upsert",
            conflict_columns=conflict_columns,
            update_columns=update_columns,
            returning=returning,
            reconcile_context=reconcile_context,
            context_collection_id=context_collection_id,
            idempotency_key=idempotency_key,
            wait_for_context=wait_for_context,
            wait_timeout=wait_timeout,
            timeout=timeout,
        )

    def ignore(
        self,
        *,
        schema: str,
        table: str,
        row: dict[str, Any],
        conflict_columns: list[str],
        returning: list[str] | None = None,
        reconcile_context: bool = False,
        context_collection_id: str | UUID | None = None,
        idempotency_key: str | None = None,
        wait_for_context: bool = False,
        wait_timeout: float = 300.0,
        timeout: float | httpx.Timeout | None = None,
    ) -> RowWriteResult:
        return self._write(
            schema=schema,
            table=table,
            row=row,
            mode="ignore",
            conflict_columns=conflict_columns,
            returning=returning,
            reconcile_context=reconcile_context,
            context_collection_id=context_collection_id,
            idempotency_key=idempotency_key,
            wait_for_context=wait_for_context,
            wait_timeout=wait_timeout,
            timeout=timeout,
        )

    def _write(
        self,
        *,
        schema: str,
        table: str,
        row: dict[str, Any],
        mode: str,
        conflict_columns: list[str] | None = None,
        update_columns: list[str] | None = None,
        returning: list[str] | None = None,
        reconcile_context: bool,
        context_collection_id: str | UUID | None,
        idempotency_key: str | None,
        wait_for_context: bool,
        wait_timeout: float,
        timeout: float | httpx.Timeout | None,
    ) -> RowWriteResult:
        if wait_for_context and (
            isinstance(wait_timeout, bool)
            or not isinstance(wait_timeout, (int, float))
            or wait_timeout <= 0
            or not math.isfinite(float(wait_timeout))
        ):
            raise PolygresValidationError("wait_timeout must be a positive finite number")
        payload, key = _payload(
            schema=schema,
            table=table,
            row=row,
            mode=mode,
            conflict_columns=conflict_columns,
            update_columns=update_columns,
            returning=returning,
            reconcile_context=reconcile_context,
            context_collection_id=context_collection_id,
            idempotency_key=idempotency_key,
            execution=True,
        )
        headers = {"Idempotency-Key": key} if key is not None else None
        try:
            response = self._project._client._post(
                _path(schema, table),
                payload,
                headers=headers,
                timeout=timeout,
                retryable=False,
            )
        except PolygresAPIError as exc:
            if exc.code in ERROR_CATALOG and exc.code != "ROW_WRITE_OUTCOME_AMBIGUOUS":
                raise
            if exc.code == "ROW_WRITE_OUTCOME_AMBIGUOUS" or exc.status_code in {
                None,
                408,
                500,
                502,
                503,
                504,
            }:
                raise PolygresAmbiguousWriteError(
                    str(exc),
                    status_code=exc.status_code,
                    request_id=exc.request_id,
                    code=exc.code or "ROW_WRITE_OUTCOME_AMBIGUOUS",
                    details=exc.details,
                ) from exc
            raise
        result = RowWriteResult.from_api(response)
        if not wait_for_context or result.status != "pending" or result.context is None:
            return result
        try:
            self._project.context.wait_for_operation(
                result.context.operation_id,
                timeout=wait_timeout,
            )
        except PolygresError as exc:
            code = getattr(exc, "code", None)
            details = getattr(exc, "details", {})
            if code in {"TIMEOUT", "CONTEXT_OPERATION_TIMEOUT"}:
                return result
            operation_status = details.get("operation_status")
            if operation_status not in {"failed", "cancelled"}:
                details.setdefault("operation_id", result.context.operation_id)
                details.setdefault("idempotency_key", key)
                details.setdefault("row_request_id", result.request_id)
                raise
            result.status = "partial_failed"
            result.context.status = "partial_failed"
            result.context.operation_status = str(operation_status)
            result.context.error = {
                "code": "ROW_CONTEXT_RECONCILIATION_FAILED",
                "message": "The row committed, but Context reconciliation failed.",
                "retryable": _context_error_retryable(code),
                "details": {
                    "operation_id": result.context.operation_id,
                    "underlying_code": code or "CONTEXT_OPERATION_FAILED",
                },
            }
            return result
        replay = self._project._client._post(
            _path(schema, table),
            payload,
            headers=headers,
            timeout=timeout,
            retryable=False,
        )
        return RowWriteResult.from_api(replay)


def _context_error_retryable(code: str | None) -> bool:
    descriptor = ERROR_CATALOG.get(code or "CONTEXT_OPERATION_FAILED")
    return descriptor is not None and descriptor.retry_class in {
        "after_delay",
        "bounded_retry",
        "user_retry",
    }


def _payload(
    *,
    schema: str,
    table: str,
    row: dict[str, Any],
    mode: str,
    conflict_columns: list[str] | None,
    update_columns: list[str] | None,
    returning: list[str] | None,
    reconcile_context: bool,
    context_collection_id: str | UUID | None,
    idempotency_key: str | None,
    execution: bool,
) -> tuple[dict[str, Any], str | None]:
    _identifier(schema, "schema")
    _identifier(table, "table")
    if mode not in {"insert", "upsert", "ignore"}:
        raise PolygresValidationError("mode must be insert, upsert, or ignore")
    if not isinstance(row, dict) or not row:
        raise PolygresValidationError("row must be a non-empty object")
    _json_native(row, "row")
    for name in row:
        _identifier(name, "row column")
    conflict = _column_list(conflict_columns, "conflict_columns")
    updates = _column_list(update_columns, "update_columns", allow_none=True)
    returned = _column_list(returning or [], "returning")
    if mode == "insert" and (conflict or update_columns is not None):
        raise PolygresValidationError("insert does not accept conflict or update columns")
    if mode in {"upsert", "ignore"} and not conflict:
        raise PolygresValidationError(f"{mode} requires conflict_columns")
    if mode == "ignore" and update_columns is not None:
        raise PolygresValidationError("ignore does not accept update_columns")
    context_requested = reconcile_context or context_collection_id is not None
    if context_requested and execution and not idempotency_key:
        raise PolygresValidationError("Context-backed row writes require idempotency_key")
    if not context_requested and idempotency_key is not None:
        raise PolygresValidationError("idempotency_key requires Context reconciliation")
    if idempotency_key is not None:
        if (
            len(idempotency_key) > 128
            or not idempotency_key.isascii()
            or not idempotency_key.isprintable()
        ):
            raise PolygresValidationError(
                "idempotency_key must be 1-128 printable ASCII characters"
            )
    payload: dict[str, Any] = {"mode": mode, "row": row, "returning": returned}
    if conflict_columns is not None:
        payload["conflict_columns"] = conflict
    if update_columns is not None:
        payload["update_columns"] = updates
    if context_requested:
        context: dict[str, Any] = {"reconcile": True}
        if context_collection_id is not None:
            try:
                context["collection_id"] = str(UUID(str(context_collection_id)))
            except (TypeError, ValueError, AttributeError) as exc:
                raise PolygresValidationError("context_collection_id must be a UUID") from exc
        payload["context"] = context
    return payload, idempotency_key


def _identifier(value: str, field: str) -> None:
    if (
        not isinstance(value, str)
        or _IDENTIFIER.fullmatch(value) is None
        or len(value.encode()) > 63
    ):
        raise PolygresValidationError(
            f"{field} must match ^[A-Za-z_][A-Za-z0-9_]*$ and be at most 63 bytes"
        )


def _column_list(
    value: list[str] | None,
    field: str,
    *,
    allow_none: bool = False,
) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or (allow_none and not value):
        raise PolygresValidationError(f"{field} must be a non-empty list when supplied")
    for item in value:
        _identifier(item, field)
    if len(value) != len(set(value)):
        raise PolygresValidationError(f"{field} must not contain duplicates")
    return list(value)


def _json_native(value: Any, field: str) -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise PolygresValidationError(f"{field} numbers must be finite")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _json_native(item, f"{field}.{index}")
        return
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise PolygresValidationError(f"{field} object keys must be strings")
        for key, item in value.items():
            _json_native(item, f"{field}.{key}")
        return
    if isinstance(value, (UUID, datetime, date, Decimal)):
        raise PolygresValidationError(f"{field} must use JSON-native strings or numbers")
    raise PolygresValidationError(f"{field} contains a non-JSON value")


def _path(schema: str, table: str, *, validate: bool = False) -> str:
    suffix = "/validate" if validate else ""
    return f"/tables/{quote(schema, safe='')}/{quote(table, safe='')}/rows{suffix}"
