from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

import httpx
from pydantic import BaseModel, ValidationError

from polygres._method_metadata import bind_sdk_method
from polygres._vendor.polygres_lib.context import (
    CapabilitiesResponse,
    CollectionCreateRequest,
    CollectionDeleteRequest,
    CollectionGetResponse,
    CollectionListResponse,
    CollectionSetDefaultRequest,
    CollectionStatusResponse,
    CollectionUpdateRequest,
    ContextCollection,
    ContextCollectionStatus,
    ContextJointResponse,
    ContextOnboardingResponse,
    ContextOperation,
    ContextOperationKind,
    ContextOperationStatus,
    CountRequest,
    CountResponse,
    DenseSearchRequest,
    DiagnosticsResponse,
    DiscoveryRequest,
    DiscoveryResponse,
    EmptyRequest,
    FacetsRequest,
    FacetsResponse,
    FilterColumnRequest,
    FilterJsonbPathRequest,
    FilterListResponse,
    GraphFirstSearchRequest,
    GroupedSearchRequest,
    JointSearchRequest,
    OperationEnvelope,
    OperationListResponse,
    PointKeysRequest,
    PointMapping,
    PointMutationResponse,
    PointScrollResponse,
    PointStatusResponse,
    PreflightResponse,
    RankedResponse,
    RankFusionSearchRequest,
    RecallCheckRequest,
    RecallCheckResponse,
    TextHybridSearchRequest,
    VectorFirstSearchRequest,
    VerificationResponse,
)
from polygres.context_validation import (
    context_collection,
    context_idempotency_key,
    context_model,
    context_query,
    context_uuid,
)
from polygres.context_wait import wait_for_context_operation
from polygres.errors import PolygresRuntimeError, PolygresValidationError
from polygres.models import Page

if TYPE_CHECKING:
    from polygres.client import Project

ResponseT = TypeVar("ResponseT", bound=BaseModel)
RequestTimeout = float | httpx.Timeout | None
_UNSET = object()


@dataclass
class ContextNamespace:
    _project: Project

    def get_capabilities(self, *, timeout: RequestTimeout = None) -> CapabilitiesResponse:
        return self._get_model("/context/capabilities", CapabilitiesResponse, timeout=timeout)

    def get_onboarding(self, *, timeout: RequestTimeout = None) -> ContextOnboardingResponse:
        """Return cached pgContext onboarding state without running discovery."""
        return self._get_model(
            "/context/onboarding", ContextOnboardingResponse, timeout=timeout
        )

    def evaluate_onboarding(
        self, *, timeout: RequestTimeout = None
    ) -> ContextOnboardingResponse:
        """Evaluate pgvector bridge eligibility once and cache the result."""
        return self._onboarding_mutation("evaluate", timeout=timeout)

    def refresh_onboarding(
        self, *, timeout: RequestTimeout = None
    ) -> ContextOnboardingResponse:
        """Explicitly re-evaluate a non-completed onboarding decision."""
        return self._onboarding_mutation("refresh", timeout=timeout)

    def acknowledge_onboarding(
        self, *, timeout: RequestTimeout = None
    ) -> ContextOnboardingResponse:
        return self._onboarding_mutation("acknowledge", timeout=timeout)

    def dismiss_onboarding(
        self, *, timeout: RequestTimeout = None
    ) -> ContextOnboardingResponse:
        return self._onboarding_mutation("dismiss", timeout=timeout)

    def _onboarding_mutation(
        self, action: str, *, timeout: RequestTimeout
    ) -> ContextOnboardingResponse:
        _, payload = context_model(EmptyRequest, {})
        return self._post_model(
            f"/context/onboarding/{action}",
            payload,
            ContextOnboardingResponse,
            timeout=timeout,
            retryable=True,
        )

    def discover_sources(
        self,
        *,
        schema_names: list[str] | None = None,
        timeout: RequestTimeout = None,
    ) -> DiscoveryResponse:
        _, payload = context_model(DiscoveryRequest, {"schema_names": schema_names})
        return self._post_model(
            "/context/discover", payload, DiscoveryResponse, timeout=timeout, retryable=True
        )

    def preflight(
        self,
        name: str,
        *,
        source: dict[str, Any] | BaseModel,
        vector: dict[str, Any] | BaseModel,
        text_column: str | None = None,
        result_columns: list[str] | None = None,
        filter_columns: list[str] | None = None,
        jsonb_filter_paths: list[dict[str, Any] | BaseModel] | None = None,
        index_kind: str = "hnsw",
        max_search_limit: int = 1_000,
        timeout: RequestTimeout = None,
    ) -> PreflightResponse:
        payload = self._collection_payload(
            name=name,
            source=source,
            vector=vector,
            text_column=text_column,
            result_columns=result_columns,
            filter_columns=filter_columns,
            jsonb_filter_paths=jsonb_filter_paths,
            index_kind=index_kind,
            max_search_limit=max_search_limit,
        )
        return self._post_model(
            "/context/preflight", payload, PreflightResponse, timeout=timeout, retryable=True
        )

    def list_collections(
        self,
        *,
        status: ContextCollectionStatus | str | None = None,
        limit: int = 50,
        cursor: str | None = None,
        timeout: RequestTimeout = None,
    ) -> Page[ContextCollection]:
        _page_limit(limit, field="limit")
        status_value = _enum_query(status, ContextCollectionStatus, "status")
        response = self._get_model(
            "/context/collections",
            CollectionListResponse,
            params={"status": status_value, "limit": limit, "cursor": cursor},
            timeout=timeout,
        )

        def fetch_next(next_cursor: str) -> Page[ContextCollection]:
            return self.list_collections(
                status=status,
                limit=limit,
                cursor=next_cursor,
                timeout=timeout,
            )

        return _page(
            response.collections,
            response.next_cursor,
            response.has_more,
            response.request_id,
            response.model_extra,
            fetch_next,
        )

    def get_collection(
        self, collection_id: str | UUID, *, timeout: RequestTimeout = None
    ) -> CollectionGetResponse:
        collection_uuid = context_uuid(collection_id, field="collection_id")
        return self._get_model(
            f"/context/collections/{collection_uuid}", CollectionGetResponse, timeout=timeout
        )

    def get_collection_status(
        self, collection_id: str | UUID, *, timeout: RequestTimeout = None
    ) -> CollectionStatusResponse:
        collection_uuid = context_uuid(collection_id, field="collection_id")
        return self._get_model(
            f"/context/collections/{collection_uuid}/status",
            CollectionStatusResponse,
            timeout=timeout,
        )

    def verify_collection(
        self, collection_id: str | UUID, *, timeout: RequestTimeout = None
    ) -> VerificationResponse:
        collection_uuid = context_uuid(collection_id, field="collection_id")
        _, payload = context_model(EmptyRequest, {})
        return self._post_model(
            f"/context/collections/{collection_uuid}/verify",
            payload,
            VerificationResponse,
            timeout=timeout,
            retryable=True,
        )

    def get_collection_diagnostics(
        self, collection_id: str | UUID, *, timeout: RequestTimeout = None
    ) -> DiagnosticsResponse:
        collection_uuid = context_uuid(collection_id, field="collection_id")
        return self._get_model(
            f"/context/collections/{collection_uuid}/diagnostics",
            DiagnosticsResponse,
            timeout=timeout,
        )

    def create_collection(
        self,
        name: str,
        *,
        source: dict[str, Any] | BaseModel,
        vector: dict[str, Any] | BaseModel,
        text_column: str | None = None,
        result_columns: list[str] | None = None,
        filter_columns: list[str] | None = None,
        jsonb_filter_paths: list[dict[str, Any] | BaseModel] | None = None,
        index_kind: str = "hnsw",
        max_search_limit: int = 1_000,
        idempotency_key: str | None = None,
        timeout: RequestTimeout = None,
    ) -> ContextOperation:
        payload = self._collection_payload(
            name=name,
            source=source,
            vector=vector,
            text_column=text_column,
            result_columns=result_columns,
            filter_columns=filter_columns,
            jsonb_filter_paths=jsonb_filter_paths,
            index_kind=index_kind,
            max_search_limit=max_search_limit,
        )
        return self._operation_mutation(
            "POST",
            "/context/collections",
            payload,
            idempotency_key=idempotency_key,
            timeout=timeout,
        )

    def update_collection(
        self,
        collection_id: str | UUID,
        *,
        text_column: str | None | object = _UNSET,
        result_columns: list[str] | object = _UNSET,
        max_search_limit: int | object = _UNSET,
        idempotency_key: str | None = None,
        timeout: RequestTimeout = None,
    ) -> ContextOperation:
        collection_uuid = context_uuid(collection_id, field="collection_id")
        request: dict[str, Any] = {}
        if text_column is not _UNSET:
            request["text_column"] = text_column
        if result_columns is not _UNSET:
            request["result_columns"] = result_columns
        if max_search_limit is not _UNSET:
            request["max_search_limit"] = max_search_limit
        _, payload = context_model(CollectionUpdateRequest, request, exclude_unset=True)
        return self._operation_mutation(
            "PATCH",
            f"/context/collections/{collection_uuid}",
            payload,
            idempotency_key=idempotency_key,
            timeout=timeout,
        )

    def set_default_collection(
        self,
        collection_id: str | UUID,
        *,
        idempotency_key: str | None = None,
        timeout: RequestTimeout = None,
    ) -> ContextOperation:
        collection_uuid = context_uuid(collection_id, field="collection_id")
        _, payload = context_model(CollectionSetDefaultRequest, {"is_default": True})
        return self._operation_mutation(
            "PATCH",
            f"/context/collections/{collection_uuid}",
            payload,
            idempotency_key=idempotency_key,
            timeout=timeout,
        )

    def reindex_collection(
        self,
        collection_id: str | UUID,
        *,
        idempotency_key: str | None = None,
        timeout: RequestTimeout = None,
    ) -> ContextOperation:
        collection_uuid = context_uuid(collection_id, field="collection_id")
        _, payload = context_model(EmptyRequest, {})
        return self._operation_mutation(
            "POST",
            f"/context/collections/{collection_uuid}/reindex",
            payload,
            idempotency_key=idempotency_key,
            timeout=timeout,
        )

    def delete_collection(
        self,
        collection_id: str | UUID,
        *,
        confirm_collection_id: str | UUID,
        idempotency_key: str | None = None,
        timeout: RequestTimeout = None,
    ) -> ContextOperation:
        collection_uuid = context_uuid(collection_id, field="collection_id")
        confirmation = context_uuid(confirm_collection_id, field="confirm_collection_id")
        if confirmation != collection_uuid:
            raise PolygresValidationError(
                "confirm_collection_id must exactly match collection_id.",
                code="CONTEXT_DELETE_CONFIRMATION_INVALID",
                details={"collection_id": collection_uuid},
            )
        _, payload = context_model(CollectionDeleteRequest, {"confirm_collection_id": confirmation})
        return self._operation_mutation(
            "DELETE",
            f"/context/collections/{collection_uuid}",
            payload,
            idempotency_key=idempotency_key,
            timeout=timeout,
        )

    def list_filters(
        self, collection_id: str | UUID, *, timeout: RequestTimeout = None
    ) -> FilterListResponse:
        collection_uuid = context_uuid(collection_id, field="collection_id")
        return self._get_model(
            f"/context/collections/{collection_uuid}/filters",
            FilterListResponse,
            timeout=timeout,
        )

    def add_filter_column(
        self,
        collection_id: str | UUID,
        key: str,
        column: str,
        *,
        idempotency_key: str | None = None,
        timeout: RequestTimeout = None,
    ) -> ContextOperation:
        collection_uuid = context_uuid(collection_id, field="collection_id")
        _, payload = context_model(FilterColumnRequest, {"key": key, "column": column})
        return self._operation_mutation(
            "POST",
            f"/context/collections/{collection_uuid}/filters/columns",
            payload,
            idempotency_key=idempotency_key,
            timeout=timeout,
        )

    def add_jsonb_filter_path(
        self,
        collection_id: str | UUID,
        key: str,
        column: str,
        path: list[str],
        *,
        idempotency_key: str | None = None,
        timeout: RequestTimeout = None,
    ) -> ContextOperation:
        collection_uuid = context_uuid(collection_id, field="collection_id")
        _, payload = context_model(
            FilterJsonbPathRequest, {"key": key, "column": column, "path": path}
        )
        return self._operation_mutation(
            "POST",
            f"/context/collections/{collection_uuid}/filters/jsonb-paths",
            payload,
            idempotency_key=idempotency_key,
            timeout=timeout,
        )

    def get_point_status(
        self, collection_id: str | UUID, *, timeout: RequestTimeout = None
    ) -> PointStatusResponse:
        collection_uuid = context_uuid(collection_id, field="collection_id")
        return self._get_model(
            f"/context/collections/{collection_uuid}/points/status",
            PointStatusResponse,
            timeout=timeout,
        )

    def scroll_points(
        self,
        collection_id: str | UUID,
        *,
        limit: int = 50,
        cursor: str | None = None,
        timeout: RequestTimeout = None,
    ) -> Page[PointMapping]:
        collection_uuid = context_uuid(collection_id, field="collection_id")
        _page_limit(limit, field="limit")
        response = self._get_model(
            f"/context/collections/{collection_uuid}/points",
            PointScrollResponse,
            params={"limit": limit, "cursor": cursor},
            timeout=timeout,
        )

        def fetch_next(next_cursor: str) -> Page[PointMapping]:
            return self.scroll_points(
                collection_uuid,
                limit=limit,
                cursor=next_cursor,
                timeout=timeout,
            )

        return _page(
            response.points,
            response.next_cursor,
            response.has_more,
            response.request_id,
            response.model_extra,
            fetch_next,
        )

    def upsert_points(
        self,
        collection_id: str | UUID,
        source_keys: list[str],
        *,
        idempotency_key: str | None = None,
        timeout: RequestTimeout = None,
    ) -> PointMutationResponse | ContextOperation:
        return self._point_mutation(
            collection_id,
            source_keys,
            action="upsert",
            idempotency_key=idempotency_key,
            timeout=timeout,
        )

    def delete_points(
        self,
        collection_id: str | UUID,
        source_keys: list[str],
        *,
        idempotency_key: str | None = None,
        timeout: RequestTimeout = None,
    ) -> PointMutationResponse | ContextOperation:
        return self._point_mutation(
            collection_id,
            source_keys,
            action="delete",
            idempotency_key=idempotency_key,
            timeout=timeout,
        )

    def reconcile_points(
        self,
        collection_id: str | UUID,
        *,
        idempotency_key: str | None = None,
        timeout: RequestTimeout = None,
    ) -> ContextOperation:
        collection_uuid = context_uuid(collection_id, field="collection_id")
        _, payload = context_model(EmptyRequest, {})
        return self._operation_mutation(
            "POST",
            f"/context/collections/{collection_uuid}/points/reconcile",
            payload,
            idempotency_key=idempotency_key,
            timeout=timeout,
        )

    def list_operations(
        self,
        *,
        collection_id: str | UUID | None = None,
        kind: ContextOperationKind | str | None = None,
        status: ContextOperationStatus | str | None = None,
        limit: int = 50,
        cursor: str | None = None,
        timeout: RequestTimeout = None,
    ) -> Page[ContextOperation]:
        _page_limit(limit, field="limit")
        collection_uuid = (
            context_uuid(collection_id, field="collection_id")
            if collection_id is not None
            else None
        )
        kind_value = _enum_query(kind, ContextOperationKind, "kind")
        status_value = _enum_query(status, ContextOperationStatus, "status")
        response = self._get_model(
            "/context/operations",
            OperationListResponse,
            params={
                "collection_id": collection_uuid,
                "kind": kind_value,
                "status": status_value,
                "limit": limit,
                "cursor": cursor,
            },
            timeout=timeout,
        )
        operations = [
            _operation_with_request_id(operation, response.request_id)
            for operation in response.operations
        ]

        def fetch_next(next_cursor: str) -> Page[ContextOperation]:
            return self.list_operations(
                collection_id=collection_id,
                kind=kind,
                status=status,
                limit=limit,
                cursor=next_cursor,
                timeout=timeout,
            )

        return _page(
            operations,
            response.next_cursor,
            response.has_more,
            response.request_id,
            response.model_extra,
            fetch_next,
        )

    def get_operation(
        self, operation_id: str | UUID, *, timeout: RequestTimeout = None
    ) -> ContextOperation:
        operation_uuid = context_uuid(operation_id, field="operation_id")
        response = self._project._client._get(
            f"/context/operations/{operation_uuid}", timeout=timeout
        )
        return _operation_response(response, expected_id=operation_uuid)

    def wait_for_operation(
        self,
        operation_or_id: ContextOperation | str | UUID,
        *,
        timeout: float = 1_800.0,
    ) -> ContextOperation:
        initial: ContextOperation | None
        if isinstance(operation_or_id, ContextOperation):
            initial = operation_or_id
            operation_uuid = context_uuid(operation_or_id.id, field="operation_id")
        else:
            initial = None
            operation_uuid = context_uuid(operation_or_id, field="operation_id")

        def fetch(deadline: float) -> tuple[ContextOperation, str | None]:
            response = self._project._client._get_response(
                f"/context/operations/{operation_uuid}", deadline=deadline
            )
            return (
                _operation_response(response.payload, expected_id=operation_uuid),
                response.headers.get("Retry-After"),
            )

        return wait_for_context_operation(
            operation_uuid,
            initial=initial,
            fetch=fetch,
            timeout=timeout,
        )

    def cancel_operation(
        self,
        operation_id: str | UUID,
        *,
        idempotency_key: str | None = None,
        timeout: RequestTimeout = None,
    ) -> ContextOperation:
        operation_uuid = context_uuid(operation_id, field="operation_id")
        _, payload = context_model(EmptyRequest, {})
        return self._operation_mutation(
            "POST",
            f"/context/operations/{operation_uuid}/cancel",
            payload,
            idempotency_key=idempotency_key,
            timeout=timeout,
        )

    def retry_operation(
        self,
        operation_id: str | UUID,
        *,
        idempotency_key: str | None = None,
        timeout: RequestTimeout = None,
    ) -> ContextOperation:
        operation_uuid = context_uuid(operation_id, field="operation_id")
        _, payload = context_model(EmptyRequest, {})
        return self._operation_mutation(
            "POST",
            f"/context/operations/{operation_uuid}/retry",
            payload,
            idempotency_key=idempotency_key,
            timeout=timeout,
        )

    def count(
        self,
        collection: str | UUID,
        *,
        filter: dict[str, Any] | None = None,
        timeout: RequestTimeout = None,
    ) -> CountResponse:
        _, payload = context_model(
            CountRequest,
            {"collection": context_collection(collection), "filter": filter},
        )
        return self._post_model(
            "/context/count", payload, CountResponse, timeout=timeout, retryable=True
        )

    def facets(
        self,
        collection: str | UUID,
        field: str,
        *,
        filter: dict[str, Any] | None = None,
        limit: int = 10,
        timeout: RequestTimeout = None,
    ) -> FacetsResponse:
        _, payload = context_model(
            FacetsRequest,
            {
                "collection": context_collection(collection),
                "field": field,
                "filter": filter,
                "limit": limit,
            },
        )
        return self._post_model(
            "/context/facets", payload, FacetsResponse, timeout=timeout, retryable=True
        )

    def search(
        self,
        collection: str | UUID,
        embedding: list[float],
        *,
        filter: dict[str, Any] | None = None,
        limit: int = 10,
        timeout: RequestTimeout = None,
    ) -> RankedResponse:
        return self._ranked(
            "/context/search",
            DenseSearchRequest,
            {
                "collection": context_collection(collection),
                "embedding": embedding,
                "filter": filter,
                "limit": limit,
            },
            timeout,
        )

    def grouped_search(
        self,
        collection: str | UUID,
        embedding: list[float],
        *,
        group_by: str,
        group_limit: int = 1,
        limit: int = 10,
        timeout: RequestTimeout = None,
    ) -> RankedResponse:
        return self._ranked(
            "/context/grouped-search",
            GroupedSearchRequest,
            {
                "collection": context_collection(collection),
                "embedding": embedding,
                "group_by": group_by,
                "group_limit": group_limit,
                "limit": limit,
            },
            timeout,
        )

    def recall_check(
        self,
        collection: str | UUID,
        embedding: list[float],
        *,
        filter: dict[str, Any] | None = None,
        limit: int = 10,
        minimum_recall: float = 0.95,
        timeout: RequestTimeout = None,
    ) -> RecallCheckResponse:
        _, payload = context_model(
            RecallCheckRequest,
            {
                "collection": context_collection(collection),
                "embedding": embedding,
                "filter": filter,
                "limit": limit,
                "minimum_recall": minimum_recall,
            },
        )
        return self._post_model(
            "/context/recall-check",
            payload,
            RecallCheckResponse,
            timeout=timeout,
            retryable=False,
        )

    def text_hybrid(
        self,
        collection: str | UUID,
        embedding: list[float],
        *,
        query: str,
        limit: int = 10,
        timeout: RequestTimeout = None,
    ) -> RankedResponse:
        return self._ranked(
            "/context/hybrid/text",
            TextHybridSearchRequest,
            {
                "collection": context_collection(collection),
                "embedding": embedding,
                "query": context_query(query),
                "limit": limit,
            },
            timeout,
        )

    def graph_first(
        self,
        collection: str | UUID,
        embedding: list[float],
        *,
        start: dict[str, str] | BaseModel,
        max_depth: int = 2,
        graph_limit: int = 200,
        relationship_types: list[str] | None = None,
        direction: str = "any",
        filter: dict[str, Any] | None = None,
        limit: int = 10,
        timeout: RequestTimeout = None,
    ) -> RankedResponse:
        return self._ranked(
            "/context/hybrid/graph-first",
            GraphFirstSearchRequest,
            {
                "collection": context_collection(collection),
                "embedding": embedding,
                "start": start,
                "max_depth": max_depth,
                "graph_limit": graph_limit,
                "relationship_types": ([] if relationship_types is None else relationship_types),
                "direction": direction,
                "filter": filter,
                "limit": limit,
            },
            timeout,
        )

    def vector_first(
        self,
        collection: str | UUID,
        embedding: list[float],
        *,
        context_limit: int = 50,
        max_depth: int = 2,
        graph_limit: int = 200,
        relationship_types: list[str] | None = None,
        direction: str = "any",
        filter: dict[str, Any] | None = None,
        limit: int = 10,
        timeout: RequestTimeout = None,
    ) -> RankedResponse:
        return self._ranked(
            "/context/hybrid/vector-first",
            VectorFirstSearchRequest,
            {
                "collection": context_collection(collection),
                "embedding": embedding,
                "context_limit": context_limit,
                "max_depth": max_depth,
                "graph_limit": graph_limit,
                "relationship_types": ([] if relationship_types is None else relationship_types),
                "direction": direction,
                "filter": filter,
                "limit": limit,
            },
            timeout,
        )

    def rank_fusion(
        self,
        collection: str | UUID,
        embedding: list[float],
        *,
        start: dict[str, str] | BaseModel,
        context_limit: int = 50,
        max_depth: int = 2,
        graph_limit: int = 200,
        relationship_types: list[str] | None = None,
        direction: str = "any",
        context_weight: float = 0.7,
        graph_weight: float = 0.3,
        filter: dict[str, Any] | None = None,
        limit: int = 10,
        timeout: RequestTimeout = None,
    ) -> RankedResponse:
        return self._ranked(
            "/context/hybrid/rank-fusion",
            RankFusionSearchRequest,
            {
                "collection": context_collection(collection),
                "embedding": embedding,
                "start": start,
                "context_limit": context_limit,
                "max_depth": max_depth,
                "graph_limit": graph_limit,
                "relationship_types": ([] if relationship_types is None else relationship_types),
                "direction": direction,
                "weights": {"context": context_weight, "graph": graph_weight},
                "filter": filter,
                "limit": limit,
            },
            timeout,
        )

    def joint(
        self,
        collection: str | UUID,
        embedding: list[float],
        *,
        query: str | None = None,
        starts: list[dict[str, str] | BaseModel] | None = None,
        filter: dict[str, Any] | None = None,
        relationship_types: list[str] | None = None,
        direction: str = "any",
        max_depth: int = 2,
        context_limit: int = 50,
        seed_limit: int = 8,
        graph_limit: int = 200,
        traversal_limit: int = 500,
        semantic_weight: float = 0.7,
        lexical_weight: float = 0.0,
        graph_weight: float = 0.3,
        limit: int = 10,
        timeout: RequestTimeout = None,
    ) -> ContextJointResponse:
        _, payload = context_model(
            JointSearchRequest,
            {
                "collection": context_collection(collection),
                "embedding": embedding,
                "query": query,
                "starts": [] if starts is None else starts,
                "filter": filter,
                "relationship_types": ([] if relationship_types is None else relationship_types),
                "direction": direction,
                "max_depth": max_depth,
                "context_limit": context_limit,
                "seed_limit": seed_limit,
                "graph_limit": graph_limit,
                "traversal_limit": traversal_limit,
                "weights": {
                    "semantic": semantic_weight,
                    "lexical": lexical_weight,
                    "graph": graph_weight,
                },
                "limit": limit,
            },
        )
        return self._post_model(
            "/context/hybrid/joint",
            payload,
            ContextJointResponse,
            timeout=timeout,
            retryable=False,
        )

    def _collection_payload(
        self,
        *,
        name: str,
        source: dict[str, Any] | BaseModel,
        vector: dict[str, Any] | BaseModel,
        text_column: str | None,
        result_columns: list[str] | None,
        filter_columns: list[str] | None,
        jsonb_filter_paths: list[dict[str, Any] | BaseModel] | None,
        index_kind: str,
        max_search_limit: int,
    ) -> dict[str, Any]:
        _, payload = context_model(
            CollectionCreateRequest,
            {
                "name": name,
                "source": source,
                "vector": vector,
                "text_column": text_column,
                "result_columns": [] if result_columns is None else result_columns,
                "filter_columns": [] if filter_columns is None else filter_columns,
                "jsonb_filter_paths": ([] if jsonb_filter_paths is None else jsonb_filter_paths),
                "index_kind": index_kind,
                "max_search_limit": max_search_limit,
            },
        )
        return payload

    def _point_mutation(
        self,
        collection_id: str | UUID,
        source_keys: list[str],
        *,
        action: str,
        idempotency_key: str | None,
        timeout: RequestTimeout,
    ) -> PointMutationResponse | ContextOperation:
        collection_uuid = context_uuid(collection_id, field="collection_id")
        _, payload = context_model(PointKeysRequest, {"source_keys": source_keys})
        key = context_idempotency_key(idempotency_key)
        response = self._project._client._post(
            f"/context/collections/{collection_uuid}/points/{action}",
            payload,
            headers={"Idempotency-Key": key},
            timeout=timeout,
            retryable=True,
        )
        if "operation" in response:
            return _operation_response(response)
        return _response_model(PointMutationResponse, response)

    def _ranked(
        self,
        path: str,
        request_model: type[BaseModel],
        request: dict[str, Any],
        timeout: RequestTimeout,
    ) -> RankedResponse:
        _, payload = context_model(request_model, request)
        return self._post_model(path, payload, RankedResponse, timeout=timeout, retryable=False)

    def _get_model(
        self,
        path: str,
        response_model: type[ResponseT],
        *,
        params: dict[str, Any] | None = None,
        timeout: RequestTimeout = None,
    ) -> ResponseT:
        response = self._project._client._get(path, params=params, timeout=timeout)
        return _response_model(response_model, response)

    def _post_model(
        self,
        path: str,
        payload: dict[str, Any],
        response_model: type[ResponseT],
        *,
        timeout: RequestTimeout,
        retryable: bool,
    ) -> ResponseT:
        response = self._project._client._post(path, payload, timeout=timeout, retryable=retryable)
        return _response_model(response_model, response)

    def _operation_mutation(
        self,
        method: str,
        path: str,
        payload: dict[str, Any],
        *,
        idempotency_key: str | None,
        timeout: RequestTimeout,
    ) -> ContextOperation:
        key = context_idempotency_key(idempotency_key)
        response = self._project._client._request(
            method,
            path,
            json=payload,
            headers={"Idempotency-Key": key},
            timeout=timeout,
            retryable=True,
        )
        return _operation_response(response)


def _attach_context_method_metadata() -> None:
    bindings = (
        (
            ContextNamespace.get_capabilities,
            "get_capabilities",
            "runtime_context_capabilities",
            "Return pgContext capabilities for this Runtime.",
            "capabilities = project.context.get_capabilities()",
            "read_only_get",
            "none",
            "operation",
        ),
        (
            ContextNamespace.get_onboarding,
            "get_onboarding",
            "runtime_context_get_onboarding",
            "Return cached pgContext onboarding state without running discovery.",
            "onboarding = project.context.get_onboarding()",
            "read_only_get",
            "none",
            "operation",
        ),
        (
            ContextNamespace.evaluate_onboarding,
            "evaluate_onboarding",
            "runtime_context_evaluate_onboarding",
            "Evaluate and cache pgvector bridge eligibility.",
            "onboarding = project.context.evaluate_onboarding()",
            "read_only_post",
            "none",
            "operation",
        ),
        (
            ContextNamespace.refresh_onboarding,
            "refresh_onboarding",
            "runtime_context_refresh_onboarding",
            "Explicitly refresh pgvector bridge eligibility.",
            "onboarding = project.context.refresh_onboarding()",
            "read_only_post",
            "none",
            "operation",
        ),
        (
            ContextNamespace.acknowledge_onboarding,
            "acknowledge_onboarding",
            "runtime_context_acknowledge_onboarding",
            "Record that the pgContext bridge offer was shown.",
            "onboarding = project.context.acknowledge_onboarding()",
            "idempotent_mutation",
            "none",
            "operation",
        ),
        (
            ContextNamespace.dismiss_onboarding,
            "dismiss_onboarding",
            "runtime_context_dismiss_onboarding",
            "Dismiss the pgContext bridge offer for this project.",
            "onboarding = project.context.dismiss_onboarding()",
            "idempotent_mutation",
            "none",
            "operation",
        ),
        (
            ContextNamespace.discover_sources,
            "discover_sources",
            "runtime_context_discover",
            "Discover tables and columns eligible for Context collections.",
            "sources = project.context.discover_sources()",
            "read_only_post",
            "none",
            "operation",
        ),
        (
            ContextNamespace.preflight,
            "preflight",
            "runtime_context_preflight",
            "Validate a proposed Context collection without creating it.",
            'report = project.context.preflight("support", source=source, vector=vector)',
            "read_only_post",
            "none",
            "operation",
        ),
        (
            ContextNamespace.list_collections,
            "list_collections",
            "runtime_context_list_collections",
            "List Context collections with cursor pagination.",
            "page = project.context.list_collections()",
            "read_only_get",
            "auto_cursor",
            "operation",
        ),
        (
            ContextNamespace.get_collection,
            "get_collection",
            "runtime_context_get_collection",
            "Return one Context collection by UUID.",
            "collection = project.context.get_collection(collection_id)",
            "read_only_get",
            "none",
            "operation",
        ),
        (
            ContextNamespace.get_collection_status,
            "get_collection_status",
            "runtime_context_get_status",
            "Return the current status of a Context collection.",
            "status = project.context.get_collection_status(collection_id)",
            "read_only_get",
            "none",
            "operation",
        ),
        (
            ContextNamespace.verify_collection,
            "verify_collection",
            "runtime_context_verify_collection",
            "Verify the physical state of a Context collection.",
            "report = project.context.verify_collection(collection_id)",
            "read_only_post",
            "none",
            "operation",
        ),
        (
            ContextNamespace.get_collection_diagnostics,
            "get_collection_diagnostics",
            "runtime_context_get_diagnostics",
            "Return diagnostics for a Context collection.",
            "diagnostics = project.context.get_collection_diagnostics(collection_id)",
            "read_only_get",
            "none",
            "operation",
        ),
        (
            ContextNamespace.create_collection,
            "create_collection",
            "runtime_context_create_collection",
            "Create a durable Context collection operation.",
            (
                'operation = project.context.create_collection("support", '
                "source=source, vector=vector)"
            ),
            "idempotent_mutation",
            "none",
            "operation",
        ),
        (
            ContextNamespace.update_collection,
            "update_collection",
            "runtime_context_update_collection",
            "Update mutable Context collection settings.",
            (
                "operation = project.context.update_collection("
                'collection_id, result_columns=["title"])'
            ),
            "idempotent_mutation",
            "none",
            "operation",
        ),
        (
            ContextNamespace.set_default_collection,
            "set_default_collection",
            "runtime_context_update_collection",
            "Make a Context collection the project default.",
            "operation = project.context.set_default_collection(collection_id)",
            "idempotent_mutation",
            "none",
            "operation",
        ),
        (
            ContextNamespace.reindex_collection,
            "reindex_collection",
            "runtime_context_reindex_collection",
            "Start a durable reindex operation for a collection.",
            "operation = project.context.reindex_collection(collection_id)",
            "idempotent_mutation",
            "none",
            "operation",
        ),
        (
            ContextNamespace.delete_collection,
            "delete_collection",
            "runtime_context_delete_collection",
            "Start deletion of a confirmed Context collection.",
            (
                "operation = project.context.delete_collection("
                "collection_id, confirm_collection_id=collection_id)"
            ),
            "idempotent_mutation",
            "none",
            "operation",
        ),
        (
            ContextNamespace.list_filters,
            "list_filters",
            "runtime_context_list_filters",
            "List registered filters for a Context collection.",
            "filters = project.context.list_filters(collection_id)",
            "read_only_get",
            "none",
            "operation",
        ),
        (
            ContextNamespace.add_filter_column,
            "add_filter_column",
            "runtime_context_add_filter_column",
            "Register a scalar filter column on a collection.",
            'operation = project.context.add_filter_column(collection_id, "tenant", "tenant_id")',
            "idempotent_mutation",
            "none",
            "operation",
        ),
        (
            ContextNamespace.add_jsonb_filter_path,
            "add_jsonb_filter_path",
            "runtime_context_add_filter_jsonb_path",
            "Register a JSONB filter path on a collection.",
            (
                "operation = project.context.add_jsonb_filter_path("
                'collection_id, "topic", "metadata", ["topic"])'
            ),
            "idempotent_mutation",
            "none",
            "operation",
        ),
        (
            ContextNamespace.get_point_status,
            "get_point_status",
            "runtime_context_get_point_status",
            "Return point synchronization status for a collection.",
            "status = project.context.get_point_status(collection_id)",
            "read_only_get",
            "none",
            "operation",
        ),
        (
            ContextNamespace.scroll_points,
            "scroll_points",
            "runtime_context_scroll_points",
            "Scroll Context point mappings with cursor pagination.",
            "page = project.context.scroll_points(collection_id)",
            "read_only_get",
            "auto_cursor",
            "operation",
        ),
        (
            ContextNamespace.upsert_points,
            "upsert_points",
            "runtime_context_upsert_points",
            "Upsert selected source rows into Context points.",
            'result = project.context.upsert_points(collection_id, ["row-1"])',
            "idempotent_mutation",
            "none",
            "operation",
        ),
        (
            ContextNamespace.delete_points,
            "delete_points",
            "runtime_context_delete_points",
            "Delete selected source rows from Context points.",
            'result = project.context.delete_points(collection_id, ["row-1"])',
            "idempotent_mutation",
            "none",
            "operation",
        ),
        (
            ContextNamespace.reconcile_points,
            "reconcile_points",
            "runtime_context_reconcile_points",
            "Reconcile all source rows with Context points.",
            "operation = project.context.reconcile_points(collection_id)",
            "idempotent_mutation",
            "none",
            "operation",
        ),
        (
            ContextNamespace.list_operations,
            "list_operations",
            "runtime_context_list_operations",
            "List durable Context operations with cursor pagination.",
            "page = project.context.list_operations()",
            "read_only_get",
            "auto_cursor",
            "operation",
        ),
        (
            ContextNamespace.get_operation,
            "get_operation",
            "runtime_context_get_operation",
            "Return one durable Context operation.",
            "operation = project.context.get_operation(operation_id)",
            "read_only_get",
            "none",
            "operation",
        ),
        (
            ContextNamespace.wait_for_operation,
            "wait_for_operation",
            "runtime_context_get_operation",
            "Poll a durable Context operation until it reaches a terminal state.",
            "completed = project.context.wait_for_operation(operation)",
            "polling",
            "none",
            "composite",
        ),
        (
            ContextNamespace.cancel_operation,
            "cancel_operation",
            "runtime_context_cancel_operation",
            "Request cancellation of a durable Context operation.",
            "operation = project.context.cancel_operation(operation_id)",
            "idempotent_mutation",
            "none",
            "operation",
        ),
        (
            ContextNamespace.retry_operation,
            "retry_operation",
            "runtime_context_retry_operation",
            "Retry an eligible failed Context operation.",
            "operation = project.context.retry_operation(operation_id)",
            "idempotent_mutation",
            "none",
            "operation",
        ),
        (
            ContextNamespace.count,
            "count",
            "runtime_context_count",
            "Count Context points matching an optional filter.",
            'count = project.context.count("support")',
            "read_only_post",
            "none",
            "operation",
        ),
        (
            ContextNamespace.facets,
            "facets",
            "runtime_context_facets",
            "Return facet counts for a registered Context field.",
            'facets = project.context.facets("support", "tenant_id")',
            "read_only_post",
            "none",
            "operation",
        ),
        (
            ContextNamespace.search,
            "search",
            "runtime_context_search",
            "Run dense Context retrieval.",
            'results = project.context.search("support", embedding)',
            "none",
            "none",
            "operation",
        ),
        (
            ContextNamespace.grouped_search,
            "grouped_search",
            "runtime_context_grouped_search",
            "Run grouped dense Context retrieval.",
            'results = project.context.grouped_search("support", embedding, group_by="tenant_id")',
            "none",
            "none",
            "operation",
        ),
        (
            ContextNamespace.recall_check,
            "recall_check",
            "runtime_context_recall_check",
            "Measure approximate-search recall for a Context collection.",
            'report = project.context.recall_check("support", embedding)',
            "none",
            "none",
            "operation",
        ),
        (
            ContextNamespace.text_hybrid,
            "text_hybrid",
            "runtime_context_text_hybrid",
            "Run dense and lexical Context retrieval.",
            'results = project.context.text_hybrid("support", embedding, query="refund")',
            "none",
            "none",
            "operation",
        ),
        (
            ContextNamespace.graph_first,
            "graph_first",
            "runtime_context_graph_first",
            "Run graph-first Context hybrid retrieval.",
            'results = project.context.graph_first("support", embedding, start=start)',
            "none",
            "none",
            "operation",
        ),
        (
            ContextNamespace.vector_first,
            "vector_first",
            "runtime_context_vector_first",
            "Run vector-first Context hybrid retrieval.",
            'results = project.context.vector_first("support", embedding)',
            "none",
            "none",
            "operation",
        ),
        (
            ContextNamespace.rank_fusion,
            "rank_fusion",
            "runtime_context_rank_fusion",
            "Fuse Context and graph rankings.",
            'results = project.context.rank_fusion("support", embedding, start=start)',
            "none",
            "none",
            "operation",
        ),
        (
            ContextNamespace.joint,
            "joint",
            "runtime_context_joint",
            "Run coupled Context and graph joint retrieval.",
            'results = project.context.joint("support", embedding)',
            "none",
            "none",
            "operation",
        ),
    )
    for function, name, operation_id, description, example, retry, pagination, kind in bindings:
        bind_sdk_method(
            function,
            description=description,
            example=example,
            public_name=f"project.context.{name}",
            operation_ids=(operation_id,),
            since="0.2.0",
            retry_policy=retry,
            pagination=pagination,
            binding_kind=kind,
        )


_attach_context_method_metadata()
del _attach_context_method_metadata


def _response_model(model_type: type[ResponseT], payload: dict[str, Any]) -> ResponseT:
    try:
        return model_type.model_validate(_without_private_result_payload(payload))
    except ValidationError as exc:
        raise PolygresRuntimeError(
            "Polygres returned an invalid Context response.",
            status_code=None,
            code="CONTEXT_RESPONSE_INVALID",
        ) from exc


def _operation_response(
    payload: dict[str, Any],
    *,
    expected_id: str | None = None,
) -> ContextOperation:
    envelope = _response_model(OperationEnvelope, payload)
    operation = _operation_with_request_id(envelope.operation, envelope.request_id)
    if expected_id is not None and str(operation.id) != expected_id:
        raise PolygresRuntimeError(
            "Polygres returned a different Context operation.",
            status_code=None,
            request_id=envelope.request_id,
            code="CONTEXT_OPERATION_RESPONSE_INVALID",
            details={"operation_id": expected_id},
        )
    return operation


def _operation_with_request_id(
    operation: ContextOperation,
    request_id: str,
) -> ContextOperation:
    payload = operation.model_dump(mode="python", by_alias=True)
    payload.update(operation.model_extra or {})
    payload["request_id"] = request_id
    return _response_model(ContextOperation, payload)


def _without_private_result_payload(value: Any) -> Any:
    if isinstance(value, list):
        return [_without_private_result_payload(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _without_private_result_payload(item)
            for key, item in value.items()
            if key != "result_payload"
        }
    return value


def _enum_query(value: Any, enum_type: type[Enum], field: str) -> str | None:
    if value is None:
        return None
    try:
        parsed = value if isinstance(value, enum_type) else enum_type(value)
    except (TypeError, ValueError) as exc:
        raise PolygresValidationError(
            f"{field} is invalid.",
            code="CONTEXT_REQUEST_INVALID",
            details={"field": field, "rule": "enum"},
        ) from exc
    return str(parsed.value)


def _page_limit(value: int, *, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 100:
        raise PolygresValidationError(
            f"{field} must be an integer from 1 through 100.",
            code="CONTEXT_REQUEST_INVALID",
            details={"field": field, "rule": "range_1_100"},
        )


def _page(
    results: list[Any],
    next_cursor: str | None,
    has_more: bool,
    request_id: str,
    metadata: dict[str, Any] | None,
    fetch_next: Any,
) -> Page[Any]:
    return Page(
        results=results,
        next_cursor=next_cursor,
        has_more=has_more,
        request_id=request_id,
        metadata=dict(metadata or {}),
        _fetch_next=fetch_next,
    )


__all__ = ["ContextNamespace"]
