#!/usr/bin/env python3
"""Exercise every public ``project.context`` SDK method against a live Runtime.

The script creates disposable Context collections over an existing synthetic
source table. It never creates, changes, or deletes rows in that source table.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from itertools import islice
from typing import Any, TypeVar
from uuid import UUID

from polygres import ContextOperation, Polygres, PolygresError

PUBLIC_METHODS = {
    "get_capabilities",
    "discover_sources",
    "preflight",
    "list_collections",
    "get_collection",
    "get_collection_status",
    "verify_collection",
    "get_collection_diagnostics",
    "create_collection",
    "update_collection",
    "set_default_collection",
    "reindex_collection",
    "delete_collection",
    "list_filters",
    "add_filter_column",
    "add_jsonb_filter_path",
    "get_point_status",
    "scroll_points",
    "upsert_points",
    "delete_points",
    "reconcile_points",
    "list_operations",
    "get_operation",
    "wait_for_operation",
    "cancel_operation",
    "retry_operation",
    "count",
    "facets",
    "search",
    "grouped_search",
    "recall_check",
    "text_hybrid",
    "graph_first",
    "vector_first",
    "rank_fusion",
    "joint",
}

T = TypeVar("T")
MISSING_UUID = "00000000-0000-0000-0000-000000000099"


def _wire(value: Any) -> str:
    return str(getattr(value, "value", value))


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


@dataclass
class LiveReport:
    api_key: str
    called_methods: set[str] = field(default_factory=set)
    cases: list[dict[str, Any]] = field(default_factory=list)

    def passed(self, name: str, **details: Any) -> None:
        item = {"name": name, "status": "passed", **details}
        self.cases.append(item)
        print(json.dumps(item, default=str), flush=True)

    def invoke(self, method: str, call: Callable[[], T]) -> T:
        self.called_methods.add(method)
        return call()

    def expect_error(
        self,
        name: str,
        method: str,
        expected_codes: set[str],
        call: Callable[[], Any],
    ) -> PolygresError:
        self.called_methods.add(method)
        try:
            call()
        except PolygresError as exc:
            _require(self.api_key not in str(exc), f"{name} exposed the API key")
            code = str(getattr(exc, "code", None))
            _require(code in expected_codes, f"{name} returned unexpected error code {code}")
            self.passed(
                name,
                error_type=type(exc).__name__,
                code=code,
                status_code=getattr(exc, "status_code", None),
                request_id=getattr(exc, "request_id", None),
            )
            return exc
        raise AssertionError(f"{name} unexpectedly succeeded")

    def final_payload(self) -> dict[str, Any]:
        missing = sorted(PUBLIC_METHODS - self.called_methods)
        return {
            "status": "passed" if not missing else "failed",
            "public_methods_expected": len(PUBLIC_METHODS),
            "public_methods_called": len(self.called_methods),
            "missing_methods": missing,
            "cases_passed": len(self.cases),
        }


@dataclass(frozen=True)
class Config:
    runtime_url: str
    source_schema: str
    source_table: str
    source_key_column: str
    vector_column: str
    dimensions: int
    text_column: str
    timeout: float

    @property
    def source(self) -> dict[str, Any]:
        return {
            "mode": "existing",
            "schema_name": self.source_schema,
            "table_name": self.source_table,
            "source_key_column": self.source_key_column,
        }

    @property
    def vector(self) -> dict[str, Any]:
        return {
            "column_name": self.vector_column,
            "dimensions": self.dimensions,
            "metric": "cosine",
        }


class ContextLiveTest:
    def __init__(self, api_key: str, config: Config) -> None:
        self.api_key = api_key
        self.config = config
        self.client = Polygres(api_key=api_key, runtime_url=config.runtime_url, max_retries=2)
        self.project = self.client.project()
        self.context = self.project.context
        self.report = LiveReport(api_key=api_key)
        self.nonce = f"{int(time.time())}"
        self.primary_name = f"sdk_context_live_{self.nonce}"
        self.pagination_name = f"sdk_context_page_{self.nonce}"
        self.collection_ids: list[str] = []
        self.pending_creates: list[ContextOperation] = []
        self.previous_default_id: str | None = None

    def key(self, label: str) -> str:
        return f"sdk-context-live-{self.nonce}-{label}"

    def collection_options(self) -> dict[str, Any]:
        return {
            "source": self.config.source,
            "vector": self.config.vector,
            "text_column": self.config.text_column,
            "result_columns": ["title"],
            "filter_columns": ["tenant_id", "category"],
            "jsonb_filter_paths": [{"key": "topic", "column": "metadata", "path": ["topic"]}],
            "index_kind": "hnsw",
            "max_search_limit": 100,
        }

    def wait_succeeded(
        self, operation_or_id: ContextOperation | str, label: str
    ) -> ContextOperation:
        completed = self.report.invoke(
            "wait_for_operation",
            lambda: self.context.wait_for_operation(operation_or_id, timeout=self.config.timeout),
        )
        _require(_wire(completed.status) == "succeeded", f"{label} did not succeed")
        self.report.passed(
            label,
            operation_id=str(completed.id),
            operation_kind=_wire(completed.kind),
            stage=completed.stage,
            processed_units=completed.processed_units,
        )
        return completed

    def create(self, name: str, label: str) -> tuple[ContextOperation, str]:
        operation = self.report.invoke(
            "create_collection",
            lambda: self.context.create_collection(
                name,
                **self.collection_options(),
                idempotency_key=self.key(label),
            ),
        )
        self.pending_creates.append(operation)
        _require(_wire(operation.kind) == "collection_create", "unexpected create operation kind")
        _require(operation.collection_id is None, "queued create unexpectedly had collection_id")
        completed = self.wait_succeeded(operation, f"{label}_wait")
        _require(completed.collection_id is not None, "completed create omitted collection_id")
        collection_id = str(completed.collection_id)
        self.collection_ids.append(collection_id)
        self.pending_creates.remove(operation)
        return operation, collection_id

    def capture_previous_default(self) -> None:
        page = self.report.invoke(
            "list_collections", lambda: self.context.list_collections(limit=100)
        )
        collections = list(page.auto_paging_iter())
        self.previous_default_id = next(
            (str(collection.id) for collection in collections if collection.is_default), None
        )
        self.report.passed(
            "capture_previous_default",
            collection_count=len(collections),
            previous_default_present=self.previous_default_id is not None,
        )

    def run_planning(self) -> None:
        capabilities = self.report.invoke("get_capabilities", self.context.get_capabilities)
        _require(capabilities.joint is True, "Joint capability is unavailable")
        self.report.passed("get_capabilities", request_id=capabilities.request_id)

        discovery = self.report.invoke(
            "discover_sources",
            lambda: self.context.discover_sources(schema_names=[self.config.source_schema]),
        )
        _require(bool(discovery.candidates), "source discovery returned no candidates")
        self.report.passed("discover_sources", candidates=len(discovery.candidates))

        preflight = self.report.invoke(
            "preflight",
            lambda: self.context.preflight(
                self.primary_name,
                **self.collection_options(),
            ),
        )
        _require(preflight.eligible is True, f"preflight blockers: {preflight.blockers}")
        self.report.passed("preflight", checks=len(preflight.checks))

    def run_collection_administration(self) -> str:
        create_operation, primary_id = self.create(self.primary_name, "create-primary")
        _, pagination_id = self.create(self.pagination_name, "create-pagination")

        self.report.expect_error(
            "create_idempotency_conflict",
            "create_collection",
            {"CONTEXT_IDEMPOTENCY_CONFLICT"},
            lambda: self.context.create_collection(
                f"{self.primary_name}_conflict",
                **self.collection_options(),
                idempotency_key=self.key("create-primary"),
            ),
        )

        first_page = self.report.invoke(
            "list_collections", lambda: self.context.list_collections(limit=1)
        )
        _require(first_page.results and first_page.has_more, "collection pagination unavailable")
        first_two = list(islice(first_page.auto_paging_iter(), 2))
        _require(len(first_two) == 2, "collection second page empty")
        self.report.passed("list_collections_pagination")

        response = self.report.invoke(
            "get_collection", lambda: self.context.get_collection(primary_id)
        )
        _require(response.collection.name == self.primary_name, "collection name mismatch")
        self.report.passed("get_collection", collection_id=primary_id)

        status = self.report.invoke(
            "get_collection_status", lambda: self.context.get_collection_status(primary_id)
        )
        _require(_wire(status.serving_status) == "available", "collection is not available")
        self.report.passed("get_collection_status", observed_status=_wire(status.status))

        verification = self.report.invoke(
            "verify_collection", lambda: self.context.verify_collection(primary_id)
        )
        _require(verification.verified, "collection verification failed")
        self.report.passed("verify_collection", checks=len(verification.checks))

        diagnostics = self.report.invoke(
            "get_collection_diagnostics",
            lambda: self.context.get_collection_diagnostics(primary_id),
        )
        _require(_wire(diagnostics.overall_status) == "healthy", "collection is not healthy")
        self.report.passed("get_collection_diagnostics", checks=len(diagnostics.checks))

        update = self.report.invoke(
            "update_collection",
            lambda: self.context.update_collection(
                primary_id,
                result_columns=["title"],
                max_search_limit=100,
                idempotency_key=self.key("update"),
            ),
        )
        self.wait_succeeded(update, "update_collection")

        default = self.report.invoke(
            "set_default_collection",
            lambda: self.context.set_default_collection(
                primary_id, idempotency_key=self.key("set-default")
            ),
        )
        self.wait_succeeded(default, "set_default_collection")

        reindex = self.report.invoke(
            "reindex_collection",
            lambda: self.context.reindex_collection(
                primary_id, idempotency_key=self.key("reindex")
            ),
        )
        self.wait_succeeded(str(reindex.id), "reindex_collection_by_id")

        inspected_create = self.report.invoke(
            "get_operation", lambda: self.context.get_operation(str(create_operation.id))
        )
        _require(inspected_create.collection_id == UUID(primary_id), "create operation ID mismatch")
        self.report.passed("get_operation_create", operation_id=str(inspected_create.id))

        _require(pagination_id in self.collection_ids, "pagination collection was not tracked")
        return primary_id

    def run_filters(self, collection_id: str) -> None:
        filters = self.report.invoke(
            "list_filters", lambda: self.context.list_filters(collection_id)
        )
        _require(
            {item.key for item in filters.filters} >= {"tenant_id", "category", "topic"},
            "initial filters are incomplete",
        )
        self.report.passed("list_filters_initial", filters=len(filters.filters))

        column = self.report.invoke(
            "add_filter_column",
            lambda: self.context.add_filter_column(
                collection_id,
                "locale",
                "locale",
                idempotency_key=self.key("filter-column"),
            ),
        )
        self.wait_succeeded(column, "add_filter_column")

        jsonb = self.report.invoke(
            "add_jsonb_filter_path",
            lambda: self.context.add_jsonb_filter_path(
                collection_id,
                "language",
                "metadata",
                ["language"],
                idempotency_key=self.key("filter-jsonb"),
            ),
        )
        self.wait_succeeded(jsonb, "add_jsonb_filter_path")

        filters = self.report.invoke(
            "list_filters", lambda: self.context.list_filters(collection_id)
        )
        _require(
            {item.key for item in filters.filters} >= {"locale", "language"},
            "new filters are missing",
        )
        self.report.passed("list_filters_updated", filters=len(filters.filters))

    def _durable_source_keys(self) -> list[str]:
        return [f"00000000-0000-0000-0000-{number:012d}" for number in range(4, 1005)]

    def _wait_point_result(self, result: Any, label: str) -> ContextOperation | None:
        if isinstance(result, ContextOperation):
            return self.wait_succeeded(result, label)
        _require(result.processed >= 0, f"{label} returned invalid processed count")
        self.report.passed(label, response="synchronous", processed=result.processed)
        return None

    def run_points_and_operations(self, collection_id: str) -> None:
        status = self.report.invoke(
            "get_point_status", lambda: self.context.get_point_status(collection_id)
        )
        _require(status.mapped_point_count is not None, "point count is unavailable")
        self.report.passed("get_point_status", mapped=status.mapped_point_count)

        source_one = "00000000-0000-0000-0000-000000000001"
        deleted = self.report.invoke(
            "delete_points",
            lambda: self.context.delete_points(
                collection_id, [source_one], idempotency_key=self.key("point-delete-sync")
            ),
        )
        self._wait_point_result(deleted, "delete_points_sync")
        upserted = self.report.invoke(
            "upsert_points",
            lambda: self.context.upsert_points(
                collection_id, [source_one], idempotency_key=self.key("point-upsert-sync")
            ),
        )
        self._wait_point_result(upserted, "upsert_points_sync")

        source_keys = self._durable_source_keys()
        durable_delete = self.report.invoke(
            "delete_points",
            lambda: self.context.delete_points(
                collection_id,
                source_keys,
                idempotency_key=self.key("point-delete-durable"),
            ),
        )
        self._wait_point_result(durable_delete, "delete_points_durable")

        durable_upsert = self.report.invoke(
            "upsert_points",
            lambda: self.context.upsert_points(
                collection_id,
                source_keys,
                idempotency_key=self.key("point-upsert-durable"),
            ),
        )
        if isinstance(durable_upsert, ContextOperation):
            cancel = self.report.invoke(
                "cancel_operation",
                lambda: self.context.cancel_operation(
                    str(durable_upsert.id), idempotency_key=self.key("cancel")
                ),
            )
            self.report.expect_error(
                "wait_for_cancelled_operation",
                "wait_for_operation",
                {"CONTEXT_OPERATION_CANCELLED"},
                lambda: self.context.wait_for_operation(cancel, timeout=self.config.timeout),
            )
            cancelled = self.report.invoke(
                "get_operation", lambda: self.context.get_operation(str(durable_upsert.id))
            )
            _require(_wire(cancelled.status) == "cancelled", "operation did not cancel")
            self.report.passed("cancel_operation", operation_id=str(cancelled.id))

            retry = self.report.invoke(
                "retry_operation",
                lambda: self.context.retry_operation(
                    str(cancelled.id), idempotency_key=self.key("retry")
                ),
            )
            self.wait_succeeded(retry, "retry_operation")
        else:
            raise AssertionError(
                "durable upsert completed synchronously; cancel/retry was not tested"
            )

        reconcile = self.report.invoke(
            "reconcile_points",
            lambda: self.context.reconcile_points(
                collection_id, idempotency_key=self.key("reconcile")
            ),
        )
        self.wait_succeeded(reconcile, "reconcile_points")

        operations = self.report.invoke(
            "list_operations",
            lambda: self.context.list_operations(collection_id=collection_id, limit=2),
        )
        _require(operations.results, "operation list is empty")
        if operations.has_more:
            _require(
                len(list(islice(operations.auto_paging_iter(), 3))) >= 3,
                "operation second page is unavailable",
            )
        self.report.passed("list_operations", operations=len(operations.results))

        mappings: list[str] = []
        page = self.report.invoke(
            "scroll_points", lambda: self.context.scroll_points(collection_id, limit=100)
        )
        for point in page.auto_paging_iter():
            mappings.append(str(point.source_key))
        _require(mappings, "point scroll is empty")
        _require(len(mappings) == len(set(mappings)), "point mappings contain duplicates")
        _require(
            "00000000-0000-0000-0000-000000000003" not in mappings,
            "RLS-hidden source row was exposed",
        )
        self.report.passed("scroll_points", points=len(mappings))

    def run_aggregates_and_retrieval(self, collection_id: str) -> None:
        embedding = [0.1] * self.config.dimensions
        start = {
            "schema": self.config.source_schema,
            "table": self.config.source_table,
            "id": "00000000-0000-0000-0000-000000000001",
        }

        count = self.report.invoke("count", lambda: self.context.count(collection_id))
        facets = self.report.invoke(
            "facets", lambda: self.context.facets(self.primary_name, "category", limit=100)
        )
        _require(
            sum(item.count for item in facets.facets) == count.count,
            "facet totals do not equal count",
        )
        self.report.passed("count_and_facets", count=count.count, facets=len(facets.facets))

        ranked_calls: list[tuple[str, str, Callable[[], Any]]] = [
            (
                "search",
                "search",
                lambda: self.context.search(self.primary_name, embedding, limit=10),
            ),
            (
                "grouped_search",
                "grouped_search",
                lambda: self.context.grouped_search(
                    collection_id, embedding, group_by="category", group_limit=1, limit=10
                ),
            ),
            (
                "text_hybrid",
                "text_hybrid",
                lambda: self.context.text_hybrid(
                    self.primary_name, embedding, query="synthetic context", limit=10
                ),
            ),
            (
                "graph_first",
                "graph_first",
                lambda: self.context.graph_first(collection_id, embedding, start=start, limit=10),
            ),
            (
                "vector_first",
                "vector_first",
                lambda: self.context.vector_first(self.primary_name, embedding, limit=10),
            ),
            (
                "rank_fusion",
                "rank_fusion",
                lambda: self.context.rank_fusion(collection_id, embedding, start=start, limit=10),
            ),
        ]
        for label, method, call in ranked_calls:
            result = self.report.invoke(method, call)
            _require(result.results, f"{label} returned no results")
            _require(not hasattr(result, "next_cursor"), f"{label} invented next_cursor")
            _require(not hasattr(result, "has_more"), f"{label} invented has_more")
            self.report.passed(label, results=len(result.results), request_id=result.request_id)

        recall = self.report.invoke(
            "recall_check",
            lambda: self.context.recall_check(
                self.primary_name, embedding, limit=10, minimum_recall=0.95
            ),
        )
        _require(0 <= recall.recall <= 1, "recall is outside [0, 1]")
        self.report.passed(
            "recall_check", recall=recall.recall, observed_status=_wire(recall.status)
        )

        joint = self.report.invoke(
            "joint",
            lambda: self.context.joint(
                collection_id,
                embedding,
                query="synthetic context",
                starts=[start],
                semantic_weight=0.4,
                lexical_weight=0.2,
                graph_weight=0.4,
                limit=10,
            ),
        )
        _require(joint.results, "Joint returned no results")
        _require(_wire(joint.mode) == "joint", "Joint returned the wrong mode")
        self.report.passed(
            "joint",
            results=len(joint.results),
            warnings=len(joint.warnings),
            request_id=joint.request_id,
        )

    def run_sad_paths(self, collection_id: str) -> None:
        embedding = [0.1] * self.config.dimensions
        self.report.expect_error(
            "administrative_name_rejected_locally",
            "get_collection",
            {"CONTEXT_REQUEST_INVALID"},
            lambda: self.context.get_collection(self.primary_name),
        )
        self.report.expect_error(
            "collection_not_found",
            "get_collection",
            {"CONTEXT_COLLECTION_NOT_FOUND"},
            lambda: self.context.get_collection(MISSING_UUID),
        )
        self.report.expect_error(
            "operation_not_found",
            "get_operation",
            {"CONTEXT_OPERATION_NOT_FOUND"},
            lambda: self.context.get_operation(MISSING_UUID),
        )
        self.report.expect_error(
            "invalid_collection_cursor",
            "list_collections",
            {"CONTEXT_REQUEST_INVALID"},
            lambda: self.context.list_collections(limit=1, cursor="not-a-valid-cursor"),
        )
        self.report.expect_error(
            "invalid_page_limit_rejected_locally",
            "scroll_points",
            {"CONTEXT_REQUEST_INVALID"},
            lambda: self.context.scroll_points(collection_id, limit=0),
        )
        self.report.expect_error(
            "delete_confirmation_rejected_locally",
            "delete_collection",
            {"CONTEXT_DELETE_CONFIRMATION_INVALID"},
            lambda: self.context.delete_collection(
                collection_id,
                confirm_collection_id=MISSING_UUID,
                idempotency_key=self.key("bad-confirmation"),
            ),
        )
        self.report.expect_error(
            "retrieval_collection_not_found",
            "search",
            {"CONTEXT_COLLECTION_NOT_FOUND"},
            lambda: self.context.search(f"missing_{self.nonce}", embedding, limit=2),
        )
        self.report.expect_error(
            "joint_lexical_query_coupling_rejected_locally",
            "joint",
            {"CONTEXT_REQUEST_INVALID"},
            lambda: self.context.joint(
                collection_id,
                embedding,
                semantic_weight=0.5,
                lexical_weight=0.5,
                graph_weight=0,
            ),
        )

        invalid_key = "poly_live_00000000000000000000000000000000"
        invalid_client = Polygres(api_key=invalid_key, runtime_url=self.config.runtime_url)
        try:
            invalid_context = invalid_client.project().context
            try:
                invalid_context.get_capabilities()
            except PolygresError as exc:
                _require(invalid_key not in str(exc), "invalid key was exposed in error")
                _require(
                    str(getattr(exc, "code", None)) in {"API_KEY_INVALID", "AUTH_REQUIRED"},
                    f"unexpected authentication code {getattr(exc, 'code', None)}",
                )
                self.report.passed(
                    "invalid_authentication",
                    error_type=type(exc).__name__,
                    code=getattr(exc, "code", None),
                    status_code=getattr(exc, "status_code", None),
                )
            else:
                raise AssertionError("invalid API key unexpectedly authenticated")
        finally:
            invalid_client.close()

    def restore_default(self) -> None:
        if self.previous_default_id and self.previous_default_id not in self.collection_ids:
            operation = self.context.set_default_collection(
                self.previous_default_id,
                idempotency_key=self.key("restore-default"),
            )
            self.context.wait_for_operation(operation, timeout=self.config.timeout)
            self.report.passed("restore_previous_default", collection_id=self.previous_default_id)

    def cleanup(self) -> list[str]:
        failures: list[str] = []
        for operation in list(self.pending_creates):
            try:
                completed = self.context.wait_for_operation(operation, timeout=self.config.timeout)
                if completed.collection_id is not None:
                    collection_id = str(completed.collection_id)
                    if collection_id not in self.collection_ids:
                        self.collection_ids.append(collection_id)
            except PolygresError as exc:
                failures.append(
                    f"create {operation.id}: {getattr(exc, 'code', type(exc).__name__)}"
                )

        try:
            self.restore_default()
        except PolygresError as exc:
            failures.append(f"restore default: {getattr(exc, 'code', type(exc).__name__)}")

        for collection_id in reversed(self.collection_ids):
            try:
                operation = self.context.delete_collection(
                    collection_id,
                    confirm_collection_id=collection_id,
                    idempotency_key=self.key(f"cleanup-{collection_id}"),
                )
                self.context.wait_for_operation(operation, timeout=self.config.timeout)
                try:
                    self.context.get_collection(collection_id)
                except PolygresError as exc:
                    if getattr(exc, "code", None) != "CONTEXT_COLLECTION_NOT_FOUND":
                        raise
                else:
                    raise AssertionError(f"collection {collection_id} still exists")
                self.report.passed("cleanup_collection", collection_id=collection_id)
            except (PolygresError, AssertionError) as exc:
                failures.append(
                    f"cleanup {collection_id}: {getattr(exc, 'code', type(exc).__name__)}"
                )
        return failures

    def run(self) -> int:
        failure: BaseException | None = None
        cleanup_failures: list[str] = []
        try:
            self.capture_previous_default()
            self.run_planning()
            collection_id = self.run_collection_administration()
            self.run_filters(collection_id)
            self.run_points_and_operations(collection_id)
            self.run_aggregates_and_retrieval(collection_id)
            self.run_sad_paths(collection_id)
        except BaseException as exc:
            failure = exc
        finally:
            cleanup_failures = self.cleanup()
            self.client.close()

        final = self.report.final_payload()
        if failure is not None:
            _require(self.api_key not in str(failure), "failure exposed the API key")
            final["status"] = "failed"
            final["failure"] = {
                "type": type(failure).__name__,
                "code": getattr(failure, "code", None),
                "message": str(failure),
                "request_id": getattr(failure, "request_id", None),
            }
        if cleanup_failures:
            final["status"] = "failed"
            final["cleanup_failures"] = cleanup_failures
        print(json.dumps(final, indent=2, sort_keys=True, default=str))
        return 0 if final["status"] == "passed" else 1


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--confirm-staging-mutations",
        action="store_true",
        help="required acknowledgement that disposable Context resources will be created",
    )
    parser.add_argument("--project-id", default=os.environ.get("POLYGRES_PROJECT_ID"))
    parser.add_argument("--runtime-url", default=os.environ.get("POLYGRES_RUNTIME_URL"))
    parser.add_argument("--source-schema", default="public")
    parser.add_argument("--source-table", default="pgcontext_postman_documents")
    parser.add_argument("--source-key-column", default="id")
    parser.add_argument("--vector-column", default="embedding")
    parser.add_argument("--dimensions", type=int, default=3)
    parser.add_argument("--text-column", default="content")
    parser.add_argument("--operation-timeout", type=float, default=180.0)
    args = parser.parse_args(argv)
    if not args.confirm_staging_mutations:
        parser.error("--confirm-staging-mutations is required")
    if not args.project_id and not args.runtime_url:
        parser.error("set POLYGRES_PROJECT_ID or POLYGRES_RUNTIME_URL")
    return args


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    api_key = os.environ.get("POLYGRES_API_KEY")
    if not api_key:
        raise SystemExit("POLYGRES_API_KEY is required")
    runtime_url = args.runtime_url or (f"https://{args.project_id}.api.staging.db.polygres.com/v1")
    config = Config(
        runtime_url=runtime_url.rstrip("/"),
        source_schema=args.source_schema,
        source_table=args.source_table,
        source_key_column=args.source_key_column,
        vector_column=args.vector_column,
        dimensions=args.dimensions,
        text_column=args.text_column,
        timeout=args.operation_timeout,
    )
    return ContextLiveTest(api_key, config).run()


if __name__ == "__main__":
    raise SystemExit(main())
