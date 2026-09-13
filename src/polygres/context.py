from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

import httpx
from pydantic import BaseModel, ValidationError

from polygres._method_metadata import bind_sdk_method
from polygres._query_input import query_deadline, query_transport
from polygres._vendor.polygres_lib.context import (
    BackfillPointsRequest,
    BulkPointKeysRequest,
    CandidateSearchRequest,
    CapabilitiesResponse,
    ClearPayloadRequest,
    CollectionAliasDropResponse,
    CollectionAliasListResponse,
    CollectionAliasRequest,
    CollectionAliasResponse,
    CollectionCreateRequest,
    CollectionDeleteRequest,
    CollectionGetResponse,
    CollectionLimitsRequest,
    CollectionLimitsResponse,
    CollectionListResponse,
    CollectionSetDefaultRequest,
    CollectionStatusResponse,
    CollectionUpdateRequest,
    CollectionVectorsResponse,
    ContextCollection,
    ContextCollectionStatus,
    ContextJointResponse,
    ContextOnboardingResponse,
    ContextOperation,
    ContextOperationKind,
    ContextOperationStatus,
    ContextPointDiscoveryRequest,
    ContextQueryPlan,
    ContextVectorCreateRequest,
    CountRequest,
    CountResponse,
    CreateEmbeddingMigrationRequest,
    DeletePayloadRequest,
    DenseSearchRequest,
    DiagnosticsResponse,
    DiscoveryRequest,
    DiscoveryResponse,
    EmbeddingMigrationsResponse,
    EmptyRequest,
    FacetsRequest,
    FacetsResponse,
    FilterColumnRequest,
    FilterJsonbPathRequest,
    FilterListResponse,
    GraphFirstSearchRequest,
    GroupedSearchRequest,
    IndexAdvisorResponse,
    IndexDiagnosticsResponse,
    IndexMemoryEstimateResponse,
    IndexStatusResponse,
    JointSearchRequest,
    ModelVersionsResponse,
    OperationEnvelope,
    OperationListResponse,
    OptimizationStatusResponse,
    PayloadMutationResponse,
    PgContextCollectionInfoResponse,
    PgContextScoredResponse,
    PointBatchResponse,
    PointKeysRequest,
    PointMapping,
    PointMutationResponse,
    PointScrollResponse,
    PointStatusResponse,
    PreflightResponse,
    QueryCohortStatsResponse,
    QueryExecuteRequest,
    QueryExecutionResponse,
    QueryExecutionStatsResponse,
    QueryExplainRequest,
    QueryExplainResponse,
    RankedResponse,
    RankFusionSearchRequest,
    RawVectorSearchRequest,
    RawVectorSearchResponse,
    RecallCheckRequest,
    RecallCheckResponse,
    RecommendRequest,
    RegisterModelVersionRequest,
    SetPayloadRequest,
    TelemetryResponse,
    TextHybridSearchRequest,
    UpdateEmbeddingMigrationRequest,
    VacuumAdviceResponse,
    VectorConfigureRequest,
    VectorConfigureResponse,
    VectorFirstSearchRequest,
    VerificationResponse,
)
from polygres.context_validation import (
    context_collection,
    context_idempotency_key,
    context_identifier,
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
_CAPABILITY_CACHE_TTL_SECONDS = 60.0


@dataclass
class ContextNamespace:
    _project: Project
    _capabilities_cache: CapabilitiesResponse | None = field(
        init=False,
        default=None,
        repr=False,
    )
    _capabilities_cached_at: float | None = field(init=False, default=None, repr=False)

    def get_capabilities(self, *, timeout: RequestTimeout = None) -> CapabilitiesResponse:
        capabilities = self._get_model(
            "/context/capabilities",
            CapabilitiesResponse,
            timeout=timeout,
        )
        self._capabilities_cache = capabilities
        self._capabilities_cached_at = time.monotonic()
        return capabilities

    def create_collection_alias(
        self,
        alias_name: str,
        target_collection_name: str,
        *,
        timeout: RequestTimeout = None,
    ) -> CollectionAliasResponse:
        _, payload = context_model(
            CollectionAliasRequest,
            {"alias_name": alias_name, "target_collection_name": target_collection_name},
        )
        return self._post_model(
            "/context/aliases",
            payload,
            CollectionAliasResponse,
            timeout=timeout,
            retryable=False,
        )

    def collection_aliases(
        self,
        *,
        timeout: RequestTimeout = None,
    ) -> CollectionAliasListResponse:
        return self._get_model(
            "/context/aliases",
            CollectionAliasListResponse,
            timeout=timeout,
        )

    def drop_collection_alias(
        self,
        alias_name: str,
        *,
        timeout: RequestTimeout = None,
    ) -> CollectionAliasDropResponse:
        alias = context_identifier(alias_name, field="alias_name")
        response = self._project._client._request(
            "DELETE",
            f"/context/aliases/{alias}",
            timeout=timeout,
            retryable=False,
        )
        return _response_model(CollectionAliasDropResponse, response)

    def collection_info(
        self,
        collection_name: str,
        *,
        timeout: RequestTimeout = None,
    ) -> PgContextCollectionInfoResponse:
        collection = context_identifier(collection_name, field="collection_name")
        return self._get_model(
            f"/context/collections/by-name/{collection}/info",
            PgContextCollectionInfoResponse,
            timeout=timeout,
        )

    def collection_limits(
        self,
        collection_name: str,
        *,
        timeout: RequestTimeout = None,
    ) -> CollectionLimitsResponse:
        collection = context_identifier(collection_name, field="collection_name")
        return self._get_model(
            f"/context/collections/by-name/{collection}/limits",
            CollectionLimitsResponse,
            timeout=timeout,
        )

    def configure_collection_limits(
        self,
        collection_name: str,
        *,
        strict_mode: bool,
        max_dimensions: int | None = None,
        max_vectors: int | None = None,
        max_points: int | None = None,
        max_filter_nodes: int | None = None,
        max_search_limit: int | None = None,
        max_candidate_budget: int | None = None,
        query_timeout_ms: int | None = None,
        max_index_memory_bytes: int | None = None,
        timeout: RequestTimeout = None,
    ) -> CollectionLimitsResponse:
        collection = context_identifier(collection_name, field="collection_name")
        _, payload = context_model(
            CollectionLimitsRequest,
            {
                "strict_mode": strict_mode,
                "max_dimensions": max_dimensions,
                "max_vectors": max_vectors,
                "max_points": max_points,
                "max_filter_nodes": max_filter_nodes,
                "max_search_limit": max_search_limit,
                "max_candidate_budget": max_candidate_budget,
                "query_timeout_ms": query_timeout_ms,
                "max_index_memory_bytes": max_index_memory_bytes,
            },
        )
        response = self._project._client._patch(
            f"/context/collections/by-name/{collection}/limits",
            payload,
            timeout=timeout,
            retryable=False,
        )
        return _response_model(CollectionLimitsResponse, response)

    def collection_vectors(
        self,
        collection_name: str,
        *,
        timeout: RequestTimeout = None,
    ) -> CollectionVectorsResponse:
        collection = context_identifier(collection_name, field="collection_name")
        return self._get_model(
            f"/context/collections/by-name/{collection}/vectors",
            CollectionVectorsResponse,
            timeout=timeout,
        )

    def configure_vector(
        self,
        collection_name: str,
        vector_name: str,
        *,
        hnsw_options: dict[str, Any],
        quantization_options: dict[str, Any],
        status: str,
        timeout: RequestTimeout = None,
    ) -> VectorConfigureResponse:
        collection = context_identifier(collection_name, field="collection_name")
        vector = context_identifier(vector_name, field="vector_name")
        _, payload = context_model(
            VectorConfigureRequest,
            {
                "hnsw_options": hnsw_options,
                "quantization_options": quantization_options,
                "status": status,
            },
        )
        response = self._project._client._patch(
            f"/context/collections/by-name/{collection}/vectors/{vector}",
            payload,
            timeout=timeout,
            retryable=False,
        )
        return _response_model(VectorConfigureResponse, response)

    def get_onboarding(self, *, timeout: RequestTimeout = None) -> ContextOnboardingResponse:
        """Return cached pgContext onboarding state without running discovery."""
        return self._get_model("/context/onboarding", ContextOnboardingResponse, timeout=timeout)

    def evaluate_onboarding(self, *, timeout: RequestTimeout = None) -> ContextOnboardingResponse:
        """Evaluate pgvector bridge eligibility once and cache the result."""
        return self._onboarding_mutation("evaluate", timeout=timeout)

    def refresh_onboarding(self, *, timeout: RequestTimeout = None) -> ContextOnboardingResponse:
        """Explicitly re-evaluate a non-completed onboarding decision."""
        return self._onboarding_mutation("refresh", timeout=timeout)

    def acknowledge_onboarding(
        self, *, timeout: RequestTimeout = None
    ) -> ContextOnboardingResponse:
        return self._onboarding_mutation("acknowledge", timeout=timeout)

    def dismiss_onboarding(self, *, timeout: RequestTimeout = None) -> ContextOnboardingResponse:
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

    def _collection_index_read(
        self, collection: str, index_name: str, suffix: str, response_model, timeout
    ):
        collection = context_identifier(collection, field="collection")
        index_name = context_identifier(index_name, field="index_name")
        return self._get_model(
            f"/context/collections/by-name/{collection}/indexes/{index_name}/{suffix}",
            response_model,
            timeout=timeout,
        )

    def index_status(
        self, collection: str, index_name: str, *, timeout: RequestTimeout = None
    ) -> IndexStatusResponse:
        return self._collection_index_read(
            collection, index_name, "status", IndexStatusResponse, timeout
        )

    def index_diagnostics(
        self, collection: str, index_name: str, *, timeout: RequestTimeout = None
    ) -> IndexDiagnosticsResponse:
        return self._collection_index_read(
            collection, index_name, "diagnostics", IndexDiagnosticsResponse, timeout
        )

    def estimate_index_memory(
        self, collection: str, index_name: str, *, timeout: RequestTimeout = None
    ) -> IndexMemoryEstimateResponse:
        return self._collection_index_read(
            collection, index_name, "memory-estimate", IndexMemoryEstimateResponse, timeout
        )

    def vacuum_advice(
        self, collection: str, index_name: str, *, timeout: RequestTimeout = None
    ) -> VacuumAdviceResponse:
        return self._collection_index_read(
            collection, index_name, "vacuum-advice", VacuumAdviceResponse, timeout
        )

    def index_advisor(
        self, collection: str, *, timeout: RequestTimeout = None
    ) -> IndexAdvisorResponse:
        collection = context_identifier(collection, field="collection")
        return self._get_model(
            f"/context/collections/by-name/{collection}/index-advisor",
            IndexAdvisorResponse,
            timeout=timeout,
        )

    def optimization_status(
        self, collection: str, *, timeout: RequestTimeout = None
    ) -> OptimizationStatusResponse:
        collection = context_identifier(collection, field="collection")
        return self._get_model(
            f"/context/collections/by-name/{collection}/optimization-status",
            OptimizationStatusResponse,
            timeout=timeout,
        )

    def telemetry(self, collection: str, *, timeout: RequestTimeout = None) -> TelemetryResponse:
        collection = context_identifier(collection, field="collection")
        return self._get_model(
            f"/context/collections/by-name/{collection}/telemetry",
            TelemetryResponse,
            timeout=timeout,
        )

    def query_cohort_stats(
        self, collection: str, *, timeout: RequestTimeout = None
    ) -> QueryCohortStatsResponse:
        collection = context_identifier(collection, field="collection")
        return self._get_model(
            f"/context/collections/by-name/{collection}/query-cohort-stats",
            QueryCohortStatsResponse,
            timeout=timeout,
        )

    def query_execution_stats(
        self, collection: str, *, timeout: RequestTimeout = None
    ) -> QueryExecutionStatsResponse:
        collection = context_identifier(collection, field="collection")
        return self._get_model(
            f"/context/collections/by-name/{collection}/query-execution-stats",
            QueryExecutionStatsResponse,
            timeout=timeout,
        )

    def model_versions(
        self, collection: str, *, timeout: RequestTimeout = None
    ) -> ModelVersionsResponse:
        collection = context_identifier(collection, field="collection")
        return self._get_model(
            f"/context/collections/by-name/{collection}/model-versions",
            ModelVersionsResponse,
            timeout=timeout,
        )

    def register_model_version(
        self,
        collection: str,
        model_name: str,
        model_version: str,
        dimensions: int,
        metric: str,
        *,
        timeout: RequestTimeout = None,
    ) -> ModelVersionsResponse:
        collection = context_identifier(collection, field="collection")
        _, payload = context_model(
            RegisterModelVersionRequest,
            {
                "collection": collection,
                "model_name": model_name,
                "model_version": model_version,
                "dimensions": dimensions,
                "metric": metric,
            },
        )
        return self._post_model(
            f"/context/collections/by-name/{collection}/model-versions",
            payload,
            ModelVersionsResponse,
            timeout=timeout,
            retryable=False,
        )

    def embedding_migrations(
        self, collection: str, *, timeout: RequestTimeout = None
    ) -> EmbeddingMigrationsResponse:
        collection = context_identifier(collection, field="collection")
        return self._get_model(
            f"/context/collections/by-name/{collection}/embedding-migrations",
            EmbeddingMigrationsResponse,
            timeout=timeout,
        )

    def create_embedding_migration(
        self,
        collection: str,
        source_model_name: str,
        source_model_version: str,
        target_model_name: str,
        target_model_version: str,
        total_points: int,
        *,
        timeout: RequestTimeout = None,
    ) -> EmbeddingMigrationsResponse:
        collection = context_identifier(collection, field="collection")
        _, payload = context_model(
            CreateEmbeddingMigrationRequest,
            {
                "collection": collection,
                "source_model_name": source_model_name,
                "source_model_version": source_model_version,
                "target_model_name": target_model_name,
                "target_model_version": target_model_version,
                "total_points": total_points,
            },
        )
        return self._post_model(
            f"/context/collections/by-name/{collection}/embedding-migrations",
            payload,
            EmbeddingMigrationsResponse,
            timeout=timeout,
            retryable=False,
        )

    def update_embedding_migration(
        self,
        collection: str,
        migration_id: int,
        processed_points: int,
        status: str,
        *,
        timeout: RequestTimeout = None,
    ) -> EmbeddingMigrationsResponse:
        collection = context_identifier(collection, field="collection")
        if migration_id < 0:
            raise PolygresValidationError(
                "migration_id must not be negative", code="INVALID_ARGUMENT"
            )
        _, payload = context_model(
            UpdateEmbeddingMigrationRequest,
            {"processed_points": processed_points, "status": status},
        )
        response = self._project._client._request(
            "PATCH",
            f"/context/collections/by-name/{collection}/embedding-migrations/{migration_id}",
            json=payload,
            timeout=timeout,
            retryable=False,
        )
        return _response_model(EmbeddingMigrationsResponse, response)

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

    def add_vector(
        self,
        collection_id: str | UUID,
        column_name: str,
        dimensions: int,
        *,
        name: str | None = None,
        mode: str = "existing",
        metric: str = "cosine",
        index_kind: str = "hnsw",
        set_default: bool = False,
        idempotency_key: str | None = None,
        timeout: RequestTimeout = None,
    ) -> ContextOperation:
        return self.register_vector(
            collection_id,
            column_name,
            dimensions,
            name=name,
            mode=mode,
            metric=metric,
            index_kind=index_kind,
            set_default=set_default,
            idempotency_key=idempotency_key,
            timeout=timeout,
        )

    def register_vector(
        self,
        collection_id: str | UUID,
        column_name: str,
        dimensions: int,
        *,
        name: str | None = None,
        mode: str = "existing",
        metric: str = "cosine",
        index_kind: str = "hnsw",
        set_default: bool = False,
        idempotency_key: str | None = None,
        timeout: RequestTimeout = None,
    ) -> ContextOperation:
        """Register a named pgContext vector on a collection."""

        collection_uuid = context_uuid(collection_id, field="collection_id")
        _, payload = context_model(
            ContextVectorCreateRequest,
            {
                "name": name,
                "column_name": column_name,
                "dimensions": dimensions,
                "mode": mode,
                "metric": metric,
                "index_kind": index_kind,
                "set_default": set_default,
            },
        )
        return self._operation_mutation(
            "POST",
            f"/context/collections/{collection_uuid}/vectors",
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
        default_vector_name: str | object = _UNSET,
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
        if default_vector_name is not _UNSET:
            request["default_vector_name"] = default_vector_name
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
        return self.drop_collection(
            collection_id,
            confirm_collection_id=confirm_collection_id,
            idempotency_key=idempotency_key,
            timeout=timeout,
        )

    def drop_collection(
        self,
        collection_id: str | UUID,
        *,
        confirm_collection_id: str | UUID,
        idempotency_key: str | None = None,
        timeout: RequestTimeout = None,
    ) -> ContextOperation:
        """Drop a pgContext collection after explicit UUID confirmation."""

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
        return self.register_filter_column(
            collection_id,
            key,
            column,
            idempotency_key=idempotency_key,
            timeout=timeout,
        )

    def register_filter_column(
        self,
        collection_id: str | UUID,
        key: str,
        column: str,
        *,
        idempotency_key: str | None = None,
        timeout: RequestTimeout = None,
    ) -> ContextOperation:
        """Register an ordinary source column as a pgContext filter."""

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
        return self.register_jsonb_path(
            collection_id,
            key,
            column,
            path,
            idempotency_key=idempotency_key,
            timeout=timeout,
        )

    def register_jsonb_path(
        self,
        collection_id: str | UUID,
        key: str,
        column: str,
        path: list[str],
        *,
        idempotency_key: str | None = None,
        timeout: RequestTimeout = None,
    ) -> ContextOperation:
        """Register an ordered JSONB path as a pgContext filter."""

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
        return self.scroll(
            collection_id,
            limit=limit,
            cursor=cursor,
            timeout=timeout,
        )

    def scroll(
        self,
        collection_id: str | UUID,
        *,
        limit: int = 50,
        cursor: str | None = None,
        timeout: RequestTimeout = None,
    ) -> Page[PointMapping]:
        """Scroll active pgContext point mappings for a collection."""

        collection_uuid = context_uuid(collection_id, field="collection_id")
        _page_limit(limit, field="limit")
        self._validate_capability_request("point_scroll", {}, timeout=timeout)
        response = self._get_model(
            f"/context/collections/{collection_uuid}/points",
            PointScrollResponse,
            params={"limit": limit, "cursor": cursor},
            timeout=timeout,
        )

        def fetch_next(next_cursor: str) -> Page[PointMapping]:
            return self.scroll(
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

    def bulk_upsert_points(
        self,
        collection: str,
        source_keys: list[str],
        *,
        batch_size: int = 1000,
        timeout: RequestTimeout = None,
    ) -> PointBatchResponse:
        _, payload = context_model(
            BulkPointKeysRequest,
            {"collection": collection, "source_keys": source_keys, "batch_size": batch_size},
        )
        return self._post_model(
            "/context/points/bulk-upsert",
            payload,
            PointBatchResponse,
            timeout=timeout,
            retryable=False,
        )

    def bulk_delete_points(
        self,
        collection: str,
        source_keys: list[str],
        *,
        batch_size: int = 1000,
        timeout: RequestTimeout = None,
    ) -> PointBatchResponse:
        _, payload = context_model(
            BulkPointKeysRequest,
            {"collection": collection, "source_keys": source_keys, "batch_size": batch_size},
        )
        return self._post_model(
            "/context/points/bulk-delete",
            payload,
            PointBatchResponse,
            timeout=timeout,
            retryable=False,
        )

    def backfill_points(
        self, collection: str, *, batch_size: int = 1000, timeout: RequestTimeout = None
    ) -> PointBatchResponse:
        _, payload = context_model(
            BackfillPointsRequest, {"collection": collection, "batch_size": batch_size}
        )
        return self._post_model(
            "/context/points/backfill",
            payload,
            PointBatchResponse,
            timeout=timeout,
            retryable=False,
        )

    def set_payload(
        self,
        collection: str,
        source_keys: list[str],
        payload: dict[str, Any],
        *,
        timeout: RequestTimeout = None,
    ) -> PayloadMutationResponse:
        _, body = context_model(
            SetPayloadRequest,
            {"collection": collection, "source_keys": source_keys, "payload": payload},
        )
        response = self._project._client._request(
            "PUT", "/context/points/payload", json=body, timeout=timeout, retryable=False
        )
        return _response_model(PayloadMutationResponse, response)

    def delete_payload(
        self,
        collection: str,
        source_keys: list[str],
        payload_keys: list[str],
        *,
        timeout: RequestTimeout = None,
    ) -> PayloadMutationResponse:
        _, body = context_model(
            DeletePayloadRequest,
            {"collection": collection, "source_keys": source_keys, "payload_keys": payload_keys},
        )
        return self._post_model(
            "/context/points/payload/delete",
            body,
            PayloadMutationResponse,
            timeout=timeout,
            retryable=False,
        )

    def clear_payload(
        self, collection: str, source_keys: list[str], *, timeout: RequestTimeout = None
    ) -> PayloadMutationResponse:
        _, body = context_model(
            ClearPayloadRequest, {"collection": collection, "source_keys": source_keys}
        )
        return self._post_model(
            "/context/points/payload/clear",
            body,
            PayloadMutationResponse,
            timeout=timeout,
            retryable=False,
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
        response = self._project._client._get_response(
            f"/context/operations/{operation_uuid}",
            timeout=timeout,
            sdk_method="project.context.get_operation",
        )
        return _operation_response(response.payload, expected_id=operation_uuid)

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
        self._validate_capability_request("count", payload, timeout=timeout)
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
        return self.facet(
            collection,
            field,
            filter=filter,
            limit=limit,
            timeout=timeout,
        )

    def facet(
        self,
        collection: str | UUID,
        field: str,
        *,
        filter: dict[str, Any] | None = None,
        limit: int = 10,
        timeout: RequestTimeout = None,
    ) -> FacetsResponse:
        """Count values for one registered pgContext filter field."""

        _, payload = context_model(
            FacetsRequest,
            {
                "collection": context_collection(collection),
                "field": field,
                "filter": filter,
                "limit": limit,
            },
        )
        self._validate_capability_request(
            "facets",
            payload,
            timeout=timeout,
            validate_limits=False,
        )
        return self._post_model(
            "/context/facets", payload, FacetsResponse, timeout=timeout, retryable=True
        )

    def search(
        self,
        collection: str | UUID,
        embedding: list[float] | None = None,
        *,
        text: str | None = None,
        use_credits: bool = False,
        idempotency_key: str | None = None,
        vector_name: str | None = None,
        filter: dict[str, Any] | None = None,
        limit: int = 10,
        timeout: RequestTimeout = None,
    ) -> RankedResponse:
        return self._ranked(
            "/context/search",
            "dense_search",
            DenseSearchRequest,
            {
                "collection": context_collection(collection),
                "vector_name": vector_name,
                "embedding": embedding,
                "text": text,
                "use_credits": use_credits,
                "filter": filter,
                "limit": limit,
            },
            timeout,
            idempotency_key=idempotency_key,
        )

    def raw_vector_search(
        self,
        query: list[float],
        point_ids: list[int],
        vectors: list[list[float]],
        metric: str,
        *,
        limit: int = 10,
        timeout: RequestTimeout = None,
    ) -> RawVectorSearchResponse:
        _, payload = context_model(
            RawVectorSearchRequest,
            {
                "query": query,
                "point_ids": point_ids,
                "vectors": vectors,
                "metric": metric,
                "limit": limit,
            },
        )
        return self._post_model(
            "/context/search/raw", payload, RawVectorSearchResponse, timeout=timeout, retryable=True
        )

    def candidate_search(
        self,
        collection: str,
        embedding: list[float] | None = None,
        candidate_point_ids: list[int] | None = None,
        *,
        text: str | None = None,
        use_credits: bool = False,
        idempotency_key: str | None = None,
        vector_name: str | None = None,
        filter: dict[str, Any] | None = None,
        limit: int = 10,
        timeout: RequestTimeout = None,
    ) -> PgContextScoredResponse:
        _, payload = context_model(
            CandidateSearchRequest,
            {
                "collection": collection,
                "embedding": embedding,
                "text": text,
                "use_credits": use_credits,
                "candidate_point_ids": candidate_point_ids,
                "vector_name": vector_name,
                "filter": filter,
                "limit": limit,
            },
        )
        return self._post_model(
            "/context/search/candidates",
            payload,
            PgContextScoredResponse,
            timeout=timeout,
            retryable=True,
            idempotency_key=idempotency_key,
        )

    def recommend(
        self,
        collection: str,
        *,
        positive_point_ids: list[int] | None = None,
        negative_point_ids: list[int] | None = None,
        positive_vectors: list[list[float]] | None = None,
        negative_vectors: list[list[float]] | None = None,
        limit: int = 10,
        timeout: RequestTimeout = None,
    ) -> PgContextScoredResponse:
        _, payload = context_model(
            RecommendRequest,
            {
                "collection": collection,
                "positive_point_ids": positive_point_ids,
                "negative_point_ids": negative_point_ids or [],
                "positive_vectors": positive_vectors,
                "negative_vectors": negative_vectors or [],
                "limit": limit,
            },
        )
        return self._post_model(
            "/context/recommend", payload, PgContextScoredResponse, timeout=timeout, retryable=True
        )

    def discover(
        self,
        collection: str,
        context_point_ids: list[int],
        *,
        limit: int = 10,
        timeout: RequestTimeout = None,
    ) -> PgContextScoredResponse:
        _, payload = context_model(
            ContextPointDiscoveryRequest,
            {"collection": collection, "context_point_ids": context_point_ids, "limit": limit},
        )
        return self._post_model(
            "/context/search/discover",
            payload,
            PgContextScoredResponse,
            timeout=timeout,
            retryable=True,
        )

    def explore(
        self,
        collection: str,
        context_point_ids: list[int],
        *,
        limit: int = 10,
        timeout: RequestTimeout = None,
    ) -> PgContextScoredResponse:
        _, payload = context_model(
            ContextPointDiscoveryRequest,
            {"collection": collection, "context_point_ids": context_point_ids, "limit": limit},
        )
        return self._post_model(
            "/context/explore", payload, PgContextScoredResponse, timeout=timeout, retryable=True
        )

    def grouped_search(
        self,
        collection: str | UUID,
        embedding: list[float] | None = None,
        *,
        text: str | None = None,
        use_credits: bool = False,
        idempotency_key: str | None = None,
        vector_name: str | None = None,
        group_by: str,
        group_limit: int = 1,
        limit: int = 10,
        timeout: RequestTimeout = None,
    ) -> RankedResponse:
        return self._ranked(
            "/context/grouped-search",
            "grouped_search",
            GroupedSearchRequest,
            {
                "collection": context_collection(collection),
                "vector_name": vector_name,
                "embedding": embedding,
                "text": text,
                "use_credits": use_credits,
                "group_by": group_by,
                "group_limit": group_limit,
                "limit": limit,
            },
            timeout,
            idempotency_key=idempotency_key,
        )

    def recall_check(
        self,
        collection: str | UUID,
        embedding: list[float],
        *,
        vector_name: str | None = None,
        filter: dict[str, Any] | None = None,
        limit: int = 10,
        minimum_recall: float = 0.95,
        timeout: RequestTimeout = None,
    ) -> RecallCheckResponse:
        _, payload = context_model(
            RecallCheckRequest,
            {
                "collection": context_collection(collection),
                "vector_name": vector_name,
                "embedding": embedding,
                "filter": filter,
                "limit": limit,
                "minimum_recall": minimum_recall,
            },
        )
        self._validate_capability_request("recall_check", payload, timeout=timeout)
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
        embedding: list[float] | None = None,
        *,
        use_credits: bool = False,
        idempotency_key: str | None = None,
        vector_name: str | None = None,
        query: str,
        limit: int = 10,
        timeout: RequestTimeout = None,
    ) -> RankedResponse:
        return self.query(
            collection,
            embedding,
            vector_name=vector_name,
            query=query,
            limit=limit,
            timeout=timeout,
            use_credits=use_credits,
            idempotency_key=idempotency_key,
        )

    def query(
        self,
        collection: str | UUID,
        embedding: list[float] | None = None,
        *,
        use_credits: bool = False,
        idempotency_key: str | None = None,
        vector_name: str | None = None,
        query: str,
        limit: int = 10,
        timeout: RequestTimeout = None,
    ) -> RankedResponse:
        """Run the stable pgContext dense plus full-text query."""

        return self._ranked(
            "/context/hybrid/text",
            "text_hybrid",
            TextHybridSearchRequest,
            {
                "collection": context_collection(collection),
                "vector_name": vector_name,
                "embedding": embedding,
                "text": query if embedding is None else None,
                "use_credits": use_credits,
                "query": context_query(query),
                "limit": limit,
            },
            timeout,
            idempotency_key=idempotency_key,
        )

    def query_nearest(
        self,
        vector: list[float] | None = None,
        limit: int = 10,
        *,
        text: str | None = None,
        vector_name: str | None = None,
        filter: dict[str, Any] | None = None,
    ) -> ContextQueryPlan:
        request: dict[str, Any] = {"kind": "nearest", "limit": limit}
        if vector is not None:
            request["vector"] = vector
        if text is not None:
            request["text"] = text
        if vector_name is not None or filter is not None:
            request.update({"vector_name": vector_name, "filter": filter})
        return context_model(ContextQueryPlan, request)[0]

    def query_sparse_nearest(
        self,
        vector_name: str,
        vector: str,
        limit: int = 10,
        *,
        filter: dict[str, Any] | None = None,
    ) -> ContextQueryPlan:
        request: dict[str, Any] = {
            "kind": "sparse_nearest",
            "vector_name": vector_name,
            "vector": vector,
            "limit": limit,
        }
        if filter is not None:
            request["filter"] = filter
        return context_model(ContextQueryPlan, request)[0]

    def query_full_text(
        self,
        text_query: str,
        text_column: str,
        limit: int = 10,
    ) -> ContextQueryPlan:
        return context_model(
            ContextQueryPlan,
            {
                "kind": "full_text",
                "text_query": text_query,
                "text_column": text_column,
                "limit": limit,
            },
        )[0]

    def query_late_interaction(
        self,
        query_vectors: list[list[float]],
        candidates_per_query: int,
        limit: int = 10,
    ) -> ContextQueryPlan:
        return context_model(
            ContextQueryPlan,
            {
                "kind": "late_interaction",
                "query_vectors": query_vectors,
                "candidates_per_query": candidates_per_query,
                "limit": limit,
            },
        )[0]

    def query_recommend(
        self,
        positive_point_ids: list[int],
        negative_point_ids: list[int],
        limit: int = 10,
    ) -> ContextQueryPlan:
        return context_model(
            ContextQueryPlan,
            {
                "kind": "recommend",
                "positive_point_ids": positive_point_ids,
                "negative_point_ids": negative_point_ids,
                "limit": limit,
            },
        )[0]

    def query_discover(
        self,
        context_point_ids: list[int],
        limit: int = 10,
    ) -> ContextQueryPlan:
        return context_model(
            ContextQueryPlan,
            {"kind": "discover", "context_point_ids": context_point_ids, "limit": limit},
        )[0]

    def query_lookup(self, point_ids: list[int]) -> ContextQueryPlan:
        return context_model(
            ContextQueryPlan,
            {"kind": "lookup", "point_ids": point_ids},
        )[0]

    def query_prefetch(self, branches: list[ContextQueryPlan]) -> ContextQueryPlan:
        return context_model(
            ContextQueryPlan,
            {"kind": "prefetch", "branches": branches},
        )[0]

    def query_weight(self, branch: ContextQueryPlan, weight: float) -> ContextQueryPlan:
        return context_model(
            ContextQueryPlan,
            {"kind": "weight", "branch": branch, "weight": weight},
        )[0]

    def query_score_threshold(
        self,
        branch: ContextQueryPlan,
        min_score: float | None,
        max_score: float | None,
    ) -> ContextQueryPlan:
        return context_model(
            ContextQueryPlan,
            {
                "kind": "score_threshold",
                "branch": branch,
                "min_score": min_score,
                "max_score": max_score,
            },
        )[0]

    def query_formula(self, branch: ContextQueryPlan, formula: str) -> ContextQueryPlan:
        return context_model(
            ContextQueryPlan,
            {"kind": "formula", "branch": branch, "formula": formula},
        )[0]

    def query_rerank(self, branch: ContextQueryPlan, limit: int) -> ContextQueryPlan:
        return context_model(
            ContextQueryPlan,
            {"kind": "rerank", "branch": branch, "limit": limit},
        )[0]

    def execute_query(
        self,
        collection: str | UUID,
        plan: ContextQueryPlan,
        *,
        use_credits: bool = False,
        idempotency_key: str | None = None,
        timeout: RequestTimeout = None,
    ) -> QueryExecutionResponse:
        _, payload = context_model(
            QueryExecuteRequest,
            {
                "collection": context_collection(collection),
                "plan": plan,
                "use_credits": use_credits,
            },
            exclude_unset=True,
        )
        return self._post_model(
            "/context/query/execute",
            payload,
            QueryExecutionResponse,
            timeout=timeout,
            retryable=False,
            idempotency_key=idempotency_key,
        )

    def explain(
        self,
        collection: str | UUID,
        text_column: str,
        *,
        timeout: RequestTimeout = None,
    ) -> QueryExplainResponse:
        _, payload = context_model(
            QueryExplainRequest,
            {"collection": context_collection(collection), "text_column": text_column},
        )
        return self._post_model(
            "/context/query/explain",
            payload,
            QueryExplainResponse,
            timeout=timeout,
            retryable=False,
        )

    def graph_first(
        self,
        collection: str | UUID,
        embedding: list[float] | None = None,
        *,
        text: str | None = None,
        use_credits: bool = False,
        idempotency_key: str | None = None,
        vector_name: str | None = None,
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
            "graph_first",
            GraphFirstSearchRequest,
            {
                "collection": context_collection(collection),
                "vector_name": vector_name,
                "embedding": embedding,
                "text": text,
                "use_credits": use_credits,
                "start": start,
                "max_depth": max_depth,
                "graph_limit": graph_limit,
                "relationship_types": ([] if relationship_types is None else relationship_types),
                "direction": direction,
                "filter": filter,
                "limit": limit,
            },
            timeout,
            idempotency_key=idempotency_key,
        )

    def vector_first(
        self,
        collection: str | UUID,
        embedding: list[float] | None = None,
        *,
        text: str | None = None,
        use_credits: bool = False,
        idempotency_key: str | None = None,
        vector_name: str | None = None,
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
            "vector_first",
            VectorFirstSearchRequest,
            {
                "collection": context_collection(collection),
                "vector_name": vector_name,
                "embedding": embedding,
                "text": text,
                "use_credits": use_credits,
                "context_limit": context_limit,
                "max_depth": max_depth,
                "graph_limit": graph_limit,
                "relationship_types": ([] if relationship_types is None else relationship_types),
                "direction": direction,
                "filter": filter,
                "limit": limit,
            },
            timeout,
            idempotency_key=idempotency_key,
        )

    def rank_fusion(
        self,
        collection: str | UUID,
        embedding: list[float] | None = None,
        *,
        text: str | None = None,
        use_credits: bool = False,
        idempotency_key: str | None = None,
        vector_name: str | None = None,
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
            "rank_fusion",
            RankFusionSearchRequest,
            {
                "collection": context_collection(collection),
                "vector_name": vector_name,
                "embedding": embedding,
                "text": text,
                "use_credits": use_credits,
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
            idempotency_key=idempotency_key,
        )

    def joint(
        self,
        collection: str | UUID,
        embedding: list[float] | None = None,
        *,
        text: str | None = None,
        use_credits: bool = False,
        idempotency_key: str | None = None,
        vector_name: str | None = None,
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
                "vector_name": vector_name,
                "embedding": embedding,
                "text": text,
                "use_credits": use_credits,
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
        self._validate_capability_request("joint", payload, timeout=timeout)
        return self._post_model(
            "/context/hybrid/joint",
            payload,
            ContextJointResponse,
            timeout=timeout,
            retryable=False,
            idempotency_key=idempotency_key,
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
        capability: str,
        request_model: type[BaseModel],
        request: dict[str, Any],
        timeout: RequestTimeout,
        *,
        idempotency_key: str | None = None,
    ) -> RankedResponse:
        _, payload = context_model(request_model, request)
        self._validate_capability_request(capability, payload, timeout=timeout)
        return self._post_model(
            path,
            payload,
            RankedResponse,
            timeout=timeout,
            retryable=False,
            idempotency_key=idempotency_key,
        )

    def _validate_capability_request(
        self,
        capability: str,
        payload: dict[str, Any],
        *,
        timeout: RequestTimeout,
        validate_limits: bool = True,
    ) -> None:
        capabilities = self._capabilities_cache
        cached_at = self._capabilities_cached_at
        expired = cached_at is None or time.monotonic() - cached_at >= _CAPABILITY_CACHE_TTL_SECONDS
        if capabilities is None or expired or not bool(getattr(capabilities, capability)):
            capabilities = self.get_capabilities(timeout=timeout)
        if not bool(getattr(capabilities, capability)):
            blocker = getattr(capabilities, f"{capability}_blocker")
            blocker_message = getattr(
                capabilities,
                f"{capability}_blocker_message",
                None,
            )
            raise PolygresValidationError(
                blocker_message or f"Context {capability.replace('_', ' ')} is unavailable.",
                code="CONTEXT_CAPABILITY_UNAVAILABLE",
                details={"capability": capability, "blocker": blocker},
            )
        if validate_limits:
            _validate_capability_limits(capabilities, payload)

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

    def _require_query_embeddings(self, *, timeout: RequestTimeout = None) -> None:
        cached = self._capabilities_cache
        expired = (
            self._capabilities_cached_at is None
            or time.monotonic() - self._capabilities_cached_at >= _CAPABILITY_CACHE_TTL_SECONDS
        )
        if cached is None or expired or not cached.query_embedding_generation:
            cached = self.get_capabilities(timeout=timeout)
        if not cached.query_embedding_generation:
            raise PolygresValidationError(
                "This Runtime does not support query embedding generation.",
                code="CONTEXT_CAPABILITY_UNAVAILABLE",
                details={"capability": "query_embedding_generation"},
            )

    def _post_model(
        self,
        path: str,
        payload: dict[str, Any],
        response_model: type[ResponseT],
        *,
        timeout: RequestTimeout,
        retryable: bool,
        idempotency_key: str | None = None,
    ) -> ResponseT:
        payload, headers = query_transport(payload, idempotency_key)
        deadline = None
        if headers:
            deadline = query_deadline(timeout or self._project._client._timeout)
            self._require_query_embeddings(timeout=timeout)
        response = self._project._client._post(
            path,
            payload,
            timeout=timeout,
            retryable=retryable or bool(headers),
            headers=headers,
            deadline=deadline,
        )
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


def _validate_capability_limits(
    capabilities: CapabilitiesResponse,
    payload: dict[str, Any],
) -> None:
    limit_fields = (
        ("limit", "max_search_limit"),
        ("context_limit", "max_context_limit"),
        ("graph_limit", "max_graph_limit"),
        ("seed_limit", "max_joint_seed_limit"),
        ("traversal_limit", "max_joint_traversal_limit"),
        ("max_depth", "max_graph_depth"),
    )
    for field_name, capability_field in limit_fields:
        value = payload.get(field_name)
        if value is None:
            continue
        maximum = int(getattr(capabilities, capability_field))
        if int(value) > maximum:
            raise PolygresValidationError(
                f"{field_name} must be {maximum} or less for this project",
                code="CONTEXT_LIMIT_EXCEEDED",
                details={"field": field_name, "limit": maximum},
            )

    embedding = payload.get("embedding")
    if isinstance(embedding, list) and len(embedding) > capabilities.max_dimensions:
        raise PolygresValidationError(
            f"embedding must contain at most {capabilities.max_dimensions} dimensions",
            code="CONTEXT_LIMIT_EXCEEDED",
            details={"field": "embedding", "limit": capabilities.max_dimensions},
        )

    relationship_types = payload.get("relationship_types")
    if (
        isinstance(relationship_types, list)
        and len(relationship_types) > capabilities.max_relationship_types
    ):
        raise PolygresValidationError(
            "relationship_types exceeds this project's capability limit",
            code="CONTEXT_LIMIT_EXCEEDED",
            details={
                "field": "relationship_types",
                "limit": capabilities.max_relationship_types,
            },
        )


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
            ContextNamespace.add_vector,
            "add_vector",
            "runtime_context_add_vector",
            "Add a vector to a Context collection.",
            ('operation = project.context.add_vector(collection_id, "embedding_v2", 768)'),
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

    aligned_bindings = (
        (
            ContextNamespace.register_vector,
            "register_vector",
            "runtime_context_add_vector",
            "Register a named vector on a pgContext collection.",
            ('operation = project.context.register_vector(collection_id, "embedding_v2", 768)'),
            "idempotent_mutation",
            "none",
        ),
        (
            ContextNamespace.drop_collection,
            "drop_collection",
            "runtime_context_delete_collection",
            "Drop a confirmed pgContext collection.",
            (
                "operation = project.context.drop_collection("
                "collection_id, confirm_collection_id=collection_id)"
            ),
            "idempotent_mutation",
            "none",
        ),
        (
            ContextNamespace.register_filter_column,
            "register_filter_column",
            "runtime_context_add_filter_column",
            "Register a scalar filter column on a pgContext collection.",
            (
                "operation = project.context.register_filter_column("
                'collection_id, "tenant", "tenant_id")'
            ),
            "idempotent_mutation",
            "none",
        ),
        (
            ContextNamespace.register_jsonb_path,
            "register_jsonb_path",
            "runtime_context_add_filter_jsonb_path",
            "Register a JSONB filter path on a pgContext collection.",
            (
                "operation = project.context.register_jsonb_path("
                'collection_id, "topic", "metadata", ["topic"])'
            ),
            "idempotent_mutation",
            "none",
        ),
        (
            ContextNamespace.scroll,
            "scroll",
            "runtime_context_scroll_points",
            "Scroll pgContext point mappings with cursor pagination.",
            "page = project.context.scroll(collection_id)",
            "read_only_get",
            "auto_cursor",
        ),
        (
            ContextNamespace.facet,
            "facet",
            "runtime_context_facets",
            "Return facet counts for one registered pgContext field.",
            'facets = project.context.facet("support", "tenant_id")',
            "read_only_post",
            "none",
        ),
        (
            ContextNamespace.query,
            "query",
            "runtime_context_text_hybrid",
            "Run the stable pgContext dense plus full-text query.",
            'results = project.context.query("support", embedding, query="refund")',
            "none",
            "none",
        ),
    )
    for function, name, operation_id, description, example, retry, pagination in aligned_bindings:
        bind_sdk_method(
            function,
            description=description,
            example=example,
            public_name=f"project.context.{name}",
            operation_ids=(operation_id,),
            since="0.4.0",
            retry_policy=retry,
            pagination=pagination,
        )

    local_query_builders = (
        (
            ContextNamespace.query_nearest,
            "query_nearest",
            "Build a dense nearest query plan.",
            "plan = project.context.query_nearest(embedding, limit=20)",
        ),
        (
            ContextNamespace.query_sparse_nearest,
            "query_sparse_nearest",
            "Build a named sparse nearest query plan.",
            'plan = project.context.query_sparse_nearest("terms", sparse_vector, limit=20)',
        ),
        (
            ContextNamespace.query_full_text,
            "query_full_text",
            "Build a PostgreSQL full-text query plan.",
            'plan = project.context.query_full_text("refund", "content", limit=20)',
        ),
        (
            ContextNamespace.query_late_interaction,
            "query_late_interaction",
            "Build a late-interaction query plan.",
            "plan = project.context.query_late_interaction(query_vectors, 50, limit=20)",
        ),
        (
            ContextNamespace.query_recommend,
            "query_recommend",
            "Build a point recommendation query plan.",
            "plan = project.context.query_recommend([1], [], limit=20)",
        ),
        (
            ContextNamespace.query_discover,
            "query_discover",
            "Build a contextual discovery query plan.",
            "plan = project.context.query_discover([1, 2], limit=20)",
        ),
        (
            ContextNamespace.query_lookup,
            "query_lookup",
            "Build a point lookup query plan.",
            "plan = project.context.query_lookup([1, 2])",
        ),
        (
            ContextNamespace.query_prefetch,
            "query_prefetch",
            "Build a query plan that prefetches multiple branches.",
            "plan = project.context.query_prefetch([dense, lexical])",
        ),
        (
            ContextNamespace.query_weight,
            "query_weight",
            "Weight one query-plan branch.",
            "weighted = project.context.query_weight(dense, 0.7)",
        ),
        (
            ContextNamespace.query_score_threshold,
            "query_score_threshold",
            "Apply score bounds to one query-plan branch.",
            "bounded = project.context.query_score_threshold(dense, None, 0.4)",
        ),
        (
            ContextNamespace.query_formula,
            "query_formula",
            "Apply a pgContext score formula to one query-plan branch.",
            'scored = project.context.query_formula(dense, "score")',
        ),
        (
            ContextNamespace.query_rerank,
            "query_rerank",
            "Rerank one query-plan branch.",
            "plan = project.context.query_rerank(prefetched, 20)",
        ),
    )
    for function, name, description, example in local_query_builders:
        bind_sdk_method(
            function,
            description=description,
            example=example,
            public_name=f"project.context.{name}",
            operation_ids=(),
            since="0.4.0",
            retry_policy="none",
            binding_kind="local",
        )

    for function, name, operation_id, description, example in (
        (
            ContextNamespace.execute_query,
            "execute_query",
            "runtime_context_execute_query",
            "Execute a validated pgContext query plan.",
            'results = project.context.execute_query("support", plan)',
        ),
        (
            ContextNamespace.explain,
            "explain",
            "runtime_context_explain_query",
            "Explain the stable dense plus full-text pgContext query.",
            'explanation = project.context.explain("support", "content")',
        ),
    ):
        bind_sdk_method(
            function,
            description=description,
            example=example,
            public_name=f"project.context.{name}",
            operation_ids=(operation_id,),
            since="0.4.0",
            retry_policy="none",
        )

    for function, name, operation_id, description, example, retry in (
        (
            ContextNamespace.create_collection_alias,
            "create_collection_alias",
            "runtime_context_create_collection_alias",
            "Create or retarget a pgContext collection alias.",
            'alias = project.context.create_collection_alias("support", "support_v2")',
            "none",
        ),
        (
            ContextNamespace.collection_aliases,
            "collection_aliases",
            "runtime_context_list_collection_aliases",
            "List visible pgContext collection aliases.",
            "aliases = project.context.collection_aliases()",
            "read_only_get",
        ),
        (
            ContextNamespace.drop_collection_alias,
            "drop_collection_alias",
            "runtime_context_drop_collection_alias",
            "Drop a pgContext collection alias.",
            'result = project.context.drop_collection_alias("support")',
            "none",
        ),
        (
            ContextNamespace.collection_info,
            "collection_info",
            "runtime_context_collection_info",
            "Return exact pgContext collection metadata by name.",
            'info = project.context.collection_info("support")',
            "read_only_get",
        ),
        (
            ContextNamespace.collection_limits,
            "collection_limits",
            "runtime_context_collection_limits",
            "Return strict-mode limits for a pgContext collection.",
            'limits = project.context.collection_limits("support")',
            "read_only_get",
        ),
        (
            ContextNamespace.configure_collection_limits,
            "configure_collection_limits",
            "runtime_context_configure_collection_limits",
            "Configure strict-mode limits for a pgContext collection.",
            'limits = project.context.configure_collection_limits("support", strict_mode=True)',
            "none",
        ),
        (
            ContextNamespace.collection_vectors,
            "collection_vectors",
            "runtime_context_collection_vectors",
            "List registered dense vectors for a pgContext collection.",
            'vectors = project.context.collection_vectors("support")',
            "read_only_get",
        ),
        (
            ContextNamespace.configure_vector,
            "configure_vector",
            "runtime_context_configure_vector",
            "Configure dense-vector metadata for a pgContext collection.",
            (
                'vector = project.context.configure_vector("support", "embedding", '
                'hnsw_options={}, quantization_options={}, status="ready")'
            ),
            "none",
        ),
        (
            ContextNamespace.bulk_upsert_points,
            "bulk_upsert_points",
            "runtime_context_bulk_upsert_points",
            "Upsert point mappings in bounded pgContext batches.",
            'result = project.context.bulk_upsert_points("support", ["row-1"])',
            "none",
        ),
        (
            ContextNamespace.bulk_delete_points,
            "bulk_delete_points",
            "runtime_context_bulk_delete_points",
            "Delete point mappings in bounded pgContext batches.",
            'result = project.context.bulk_delete_points("support", ["row-1"])',
            "none",
        ),
        (
            ContextNamespace.backfill_points,
            "backfill_points",
            "runtime_context_backfill_points",
            "Backfill point mappings from the source table.",
            'result = project.context.backfill_points("support")',
            "none",
        ),
        (
            ContextNamespace.set_payload,
            "set_payload",
            "runtime_context_set_payload",
            "Set registered payload fields for source rows.",
            'result = project.context.set_payload("support", ["row-1"], {"locale": "en"})',
            "none",
        ),
        (
            ContextNamespace.delete_payload,
            "delete_payload",
            "runtime_context_delete_payload",
            "Delete selected registered payload fields.",
            'result = project.context.delete_payload("support", ["row-1"], ["locale"])',
            "none",
        ),
        (
            ContextNamespace.clear_payload,
            "clear_payload",
            "runtime_context_clear_payload",
            "Clear all registered payload fields.",
            'result = project.context.clear_payload("support", ["row-1"])',
            "none",
        ),
        (
            ContextNamespace.candidate_search,
            "candidate_search",
            "runtime_context_candidate_search",
            "Search within explicit candidate point IDs.",
            'result = project.context.candidate_search("support", embedding, [1, 2])',
            "none",
        ),
        (
            ContextNamespace.recommend,
            "recommend",
            "runtime_context_recommend",
            "Recommend points from positive and negative examples.",
            'result = project.context.recommend("support", positive_point_ids=[1])',
            "none",
        ),
        (
            ContextNamespace.discover,
            "discover",
            "runtime_context_discover_points",
            "Discover points from context point IDs.",
            'result = project.context.discover("support", [1, 2])',
            "none",
        ),
        (
            ContextNamespace.explore,
            "explore",
            "runtime_context_explore",
            "Explore points from context point IDs.",
            'result = project.context.explore("support", [1, 2])',
            "none",
        ),
        (
            ContextNamespace.index_status,
            "index_status",
            "runtime_context_index_status",
            "Return collection-scoped index lifecycle status.",
            'status = project.context.index_status("support", "support_embedding_idx")',
            "read_only_get",
        ),
        (
            ContextNamespace.index_diagnostics,
            "index_diagnostics",
            "runtime_context_index_diagnostics",
            "Return collection-scoped index diagnostics.",
            'status = project.context.index_diagnostics("support", "support_embedding_idx")',
            "read_only_get",
        ),
        (
            ContextNamespace.estimate_index_memory,
            "estimate_index_memory",
            "runtime_context_estimate_index_memory",
            "Estimate collection index memory.",
            'estimate = project.context.estimate_index_memory("support", "support_embedding_idx")',
            "read_only_get",
        ),
        (
            ContextNamespace.vacuum_advice,
            "vacuum_advice",
            "runtime_context_vacuum_advice",
            "Return collection index vacuum advice.",
            'advice = project.context.vacuum_advice("support", "support_embedding_idx")',
            "read_only_get",
        ),
        (
            ContextNamespace.index_advisor,
            "index_advisor",
            "runtime_context_index_advisor",
            "Return collection filter-index recommendations.",
            'advice = project.context.index_advisor("support")',
            "read_only_get",
        ),
        (
            ContextNamespace.optimization_status,
            "optimization_status",
            "runtime_context_optimization_status",
            "Return collection optimization readiness.",
            'status = project.context.optimization_status("support")',
            "read_only_get",
        ),
        (
            ContextNamespace.telemetry,
            "telemetry",
            "runtime_context_telemetry",
            "Return collection-scoped telemetry rollups.",
            'telemetry = project.context.telemetry("support")',
            "read_only_get",
        ),
        (
            ContextNamespace.model_versions,
            "model_versions",
            "runtime_context_model_versions",
            "List embedding model versions for a collection.",
            'models = project.context.model_versions("support")',
            "read_only_get",
        ),
        (
            ContextNamespace.register_model_version,
            "register_model_version",
            "runtime_context_register_model_version",
            "Register an embedding model version.",
            "model = project.context.register_model_version("
            '"support", "embed", "2", 1536, "cosine")',
            "none",
        ),
        (
            ContextNamespace.embedding_migrations,
            "embedding_migrations",
            "runtime_context_embedding_migrations",
            "List embedding migrations for a collection.",
            'migrations = project.context.embedding_migrations("support")',
            "read_only_get",
        ),
        (
            ContextNamespace.create_embedding_migration,
            "create_embedding_migration",
            "runtime_context_create_embedding_migration",
            "Create a collection embedding migration.",
            "migration = project.context.create_embedding_migration("
            '"support", "embed", "1", "embed", "2", 100)',
            "none",
        ),
        (
            ContextNamespace.update_embedding_migration,
            "update_embedding_migration",
            "runtime_context_update_embedding_migration",
            "Update collection embedding migration progress.",
            'migration = project.context.update_embedding_migration("support", 1, 50, "running")',
            "none",
        ),
        (
            ContextNamespace.raw_vector_search,
            "raw_vector_search",
            "runtime_context_raw_vector_search",
            "Search an explicit array of dense vectors.",
            'results = project.context.raw_vector_search(query, [1], [vector], "cosine")',
            "none",
        ),
        (
            ContextNamespace.query_cohort_stats,
            "query_cohort_stats",
            "runtime_context_query_cohort_stats",
            "Return collection-scoped query cohort statistics.",
            'stats = project.context.query_cohort_stats("support")',
            "read_only_get",
        ),
        (
            ContextNamespace.query_execution_stats,
            "query_execution_stats",
            "runtime_context_query_execution_stats",
            "Return collection-scoped query execution statistics.",
            'stats = project.context.query_execution_stats("support")',
            "read_only_get",
        ),
    ):
        bind_sdk_method(
            function,
            description=description,
            example=example,
            public_name=f"project.context.{name}",
            operation_ids=(operation_id,),
            since="0.4.0",
            retry_policy=retry,
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
