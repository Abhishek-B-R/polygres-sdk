from __future__ import annotations

from datetime import datetime

import httpx
import pytest
import respx

from polygres import (
    Polygres,
    PolygresAmbiguousWriteError,
    PolygresAPIError,
    PolygresRuntimeError,
    PolygresValidationError,
)

API_KEY = "poly_live_0123456789abcdef0123456789abcdef"
RUNTIME_URL = "https://p0123456789abcdef0123456.api.db.polygres.com/v1"
ROW_URL = f"{RUNTIME_URL}/tables/public/memories/rows"
ROUTE_CTX = getattr(respx, "mo" + "ck")


def _client(*, max_retries: int = 2) -> Polygres:
    return Polygres(api_key=API_KEY, runtime_url=RUNTIME_URL, max_retries=max_retries)


@ROUTE_CTX
def test_row_write_is_typed_and_never_automatically_retried() -> None:
    route = respx.post(ROW_URL).mock(
        return_value=httpx.Response(
            503,
            json={
                "error": {
                    "code": "ROW_WRITE_OUTCOME_AMBIGUOUS",
                    "message": "The row write outcome is unknown.",
                    "details": {},
                },
                "request_id": "req_unknown",
            },
        )
    )

    with pytest.raises(PolygresAmbiguousWriteError) as caught:
        _client().project().rows.insert(schema="public", table="memories", row={"id": 1})

    assert route.call_count == 1
    assert caught.value.request_id == "req_unknown"


@ROUTE_CTX
@pytest.mark.parametrize(
    ("status", "error_code"),
    [
        (503, "ROW_STATEMENT_TIMEOUT"),
        (503, "RUNTIME_API_KEY_SNAPSHOT_UNAVAILABLE"),
        (503, "RUNTIME_LIMITS_UNAVAILABLE"),
        (500, "ROW_WRITE_FAILED"),
    ],
)
def test_known_pre_mutation_runtime_error_is_not_reclassified_as_ambiguous(
    status: int,
    error_code: str,
) -> None:
    route = respx.post(ROW_URL).mock(
        return_value=httpx.Response(
            status,
            json={
                "error": {
                    "code": error_code,
                    "message": "The row write was rejected before commit.",
                    "details": {},
                },
                "request_id": "req_timeout",
            },
        )
    )

    with pytest.raises(PolygresRuntimeError) as caught:
        _client().project().rows.insert(schema="public", table="memories", row={"id": 1})

    assert not isinstance(caught.value, PolygresAmbiguousWriteError)
    assert caught.value.code == error_code
    assert route.call_count == 1


@ROUTE_CTX
def test_context_row_write_sends_exact_idempotency_header_and_parses_result() -> None:
    collection_id = "2e172638-bd77-4a2c-bc42-406f4f2938d7"
    route = respx.post(ROW_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "operation": "upserted",
                "schema": "public",
                "table": "memories",
                "returned": {"id": "memory_1"},
                "status": "completed",
                "row_committed": True,
                "context": {
                    "collection_id": collection_id,
                    "status": "completed",
                    "operation_id": "68b54789-f795-4127-989b-7895d1608836",
                    "operation_status": "succeeded",
                    "retry_until": None,
                    "error": None,
                },
                "idempotency_key": "pipeline-memory-1",
                "request_id": "req_rows",
            },
        )
    )

    result = _client().project().rows.upsert(
        schema="public",
        table="memories",
        row={"id": "memory_1", "content": "hello"},
        conflict_columns=["id"],
        returning=["id"],
        context_collection_id=collection_id,
        idempotency_key="pipeline-memory-1",
    )

    assert result.status == "completed"
    assert result.context is not None and result.context.status == "completed"
    assert route.calls[0].request.headers["idempotency-key"] == "pipeline-memory-1"


def test_rows_reject_non_json_native_values_and_missing_context_key() -> None:
    rows = _client().project().rows
    with pytest.raises(PolygresValidationError):
        rows.insert(
            schema="public",
            table="memories",
            row={"created_at": datetime.now()},
        )
    with pytest.raises(PolygresValidationError):
        rows.insert(
            schema="public",
            table="memories",
            row={"id": "memory_1"},
            reconcile_context=True,
        )


@ROUTE_CTX
@pytest.mark.parametrize("wait_timeout", [0, -1, True, float("nan"), float("inf")])
def test_invalid_wait_timeout_is_rejected_before_row_dispatch(wait_timeout: object) -> None:
    route = respx.post(ROW_URL).mock(
        return_value=httpx.Response(500, json={"error": {"code": "unexpected"}})
    )

    with pytest.raises(PolygresValidationError):
        _client().project().rows.insert(
            schema="public",
            table="memories",
            row={"id": "memory_1"},
            reconcile_context=True,
            idempotency_key="memory-1",
            wait_for_context=True,
            wait_timeout=wait_timeout,  # type: ignore[arg-type]
        )

    assert route.call_count == 0


@ROUTE_CTX
def test_terminal_context_failure_returns_partial_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    operation_id = "68b54789-f795-4127-989b-7895d1608836"
    route = respx.post(ROW_URL).mock(
        return_value=httpx.Response(
            202,
            json={
                "operation": "inserted",
                "schema": "public",
                "table": "memories",
                "returned": {},
                "status": "pending",
                "row_committed": True,
                "context": {
                    "collection_id": "2e172638-bd77-4a2c-bc42-406f4f2938d7",
                    "status": "pending",
                    "operation_id": operation_id,
                    "operation_status": "queued",
                    "retry_until": None,
                    "error": None,
                },
                "idempotency_key": "memory-1",
                "request_id": "req_rows",
            },
        )
    )
    project = _client().project()
    monkeypatch.setattr(
        project.context,
        "wait_for_operation",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            PolygresAPIError(
                "Context operation failed.",
                code="CONTEXT_OPERATION_FAILED",
                details={
                    "operation_id": operation_id,
                    "operation_status": "failed",
                },
            )
        ),
    )

    result = project.rows.insert(
        schema="public",
        table="memories",
        row={"id": "memory_1"},
        reconcile_context=True,
        idempotency_key="memory-1",
        wait_for_context=True,
    )

    assert route.call_count == 1
    assert result.status == "partial_failed"
    assert result.context is not None
    assert result.context.operation_status == "failed"
    assert result.context.error is not None
    assert result.context.error["retryable"] is True
    assert result.context.error["details"]["operation_id"] == operation_id


@ROUTE_CTX
def test_context_polling_uncertainty_keeps_known_recovery_identifiers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    operation_id = "68b54789-f795-4127-989b-7895d1608836"
    respx.post(ROW_URL).mock(
        return_value=httpx.Response(
            202,
            json={
                "operation": "inserted",
                "schema": "public",
                "table": "memories",
                "returned": {},
                "status": "pending",
                "row_committed": True,
                "context": {
                    "collection_id": "2e172638-bd77-4a2c-bc42-406f4f2938d7",
                    "status": "pending",
                    "operation_id": operation_id,
                    "operation_status": "queued",
                    "retry_until": None,
                    "error": None,
                },
                "idempotency_key": "memory-1",
                "request_id": "req_rows",
            },
        )
    )
    project = _client().project()
    monkeypatch.setattr(
        project.context,
        "wait_for_operation",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            PolygresRuntimeError("Polling transport failed.")
        ),
    )

    with pytest.raises(PolygresRuntimeError) as uncertain:
        project.rows.insert(
            schema="public",
            table="memories",
            row={"id": "memory_1"},
            reconcile_context=True,
            idempotency_key="memory-1",
            wait_for_context=True,
        )

    assert uncertain.value.details == {
        "operation_id": operation_id,
        "idempotency_key": "memory-1",
        "row_request_id": "req_rows",
    }
