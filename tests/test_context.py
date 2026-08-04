from __future__ import annotations

import json
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import Any

import httpx
import pytest

import polygres.client as client_module
from polygres import (
    ContextJointResponse,
    ContextOperation,
    ContextSearchResult,
    Page,
    Polygres,
    PolygresAPIError,
    PolygresNotFoundError,
    PolygresRuntimeError,
    PolygresValidationError,
    __version__,
)
from polygres._api_version import API_VERSION_HEADER, CLIENT_INFO_HEADER, DEFAULT_API_VERSION
from polygres.context_wait import context_poll_interval, wait_for_context_operation

API_KEY = "poly_live_0123456789abcdef0123456789abcdef"
RUNTIME_URL = "https://runtime.example.test/v1"
COLLECTION_ID = "00000000-0000-0000-0000-000000000001"
OPERATION_ID = "00000000-0000-0000-0000-000000000002"
IDEMPOTENCY_KEY = "sdk-context-idempotency"
FIXTURES = json.loads(
    (
        Path(__file__).parent
        / "fixtures"
        / "context"
        / "contract-fixtures.json"
    ).read_text()
)


def _client(handler: Callable[[httpx.Request], httpx.Response], *, retries: int = 0) -> Polygres:
    client = Polygres(api_key=API_KEY, runtime_url=RUNTIME_URL, max_retries=retries)
    client._client.close()
    client._client = httpx.Client(transport=httpx.MockTransport(handler))
    return client


def _response_payload(request: httpx.Request) -> dict[str, Any]:
    path = request.url.path.removeprefix("/v1")
    responses = FIXTURES["responses"]
    if path == "/context/capabilities":
        return deepcopy(responses["CapabilitiesResponse"])
    if path == "/context/discover":
        return deepcopy(responses["DiscoveryResponse"])
    if path == "/context/preflight":
        return deepcopy(responses["PreflightResponse"])
    if path == "/context/collections" and request.method == "GET":
        return deepcopy(responses["CollectionListResponse"])
    if path == f"/context/collections/{COLLECTION_ID}" and request.method == "GET":
        return deepcopy(responses["CollectionGetResponse"])
    if path.endswith("/status") and "/points/" not in path:
        return deepcopy(responses["CollectionStatusResponse"])
    if path.endswith("/verify"):
        return deepcopy(responses["VerificationResponse"])
    if path.endswith("/diagnostics"):
        return deepcopy(responses["DiagnosticsResponse"])
    if path.endswith("/filters"):
        return deepcopy(responses["FilterListResponse"])
    if path.endswith("/points/status"):
        return deepcopy(responses["PointStatusResponse"])
    if path.endswith("/points") and request.method == "GET":
        return deepcopy(responses["PointScrollResponse"])
    if path.endswith(("/points/upsert", "/points/delete")):
        return deepcopy(responses["PointMutationResponse"])
    if path == "/context/operations" and request.method == "GET":
        return deepcopy(responses["OperationListResponse"])
    if path == f"/context/operations/{OPERATION_ID}" and request.method == "GET":
        payload = deepcopy(responses["OperationEnvelope"])
        payload["operation"]["id"] = OPERATION_ID
        return payload
    if path == "/context/count":
        return deepcopy(responses["CountResponse"])
    if path == "/context/facets":
        return deepcopy(responses["FacetsResponse"])
    if path == "/context/recall-check":
        return deepcopy(responses["RecallCheckResponse"])
    if path == "/context/hybrid/joint":
        return deepcopy(responses["ContextJointResponse"])
    if path in {
        "/context/search",
        "/context/grouped-search",
        "/context/hybrid/text",
        "/context/hybrid/graph-first",
        "/context/hybrid/vector-first",
        "/context/hybrid/rank-fusion",
    }:
        payload = deepcopy(responses["RankedResponse"])
        payload["mode"] = {
            "/context/search": "dense",
            "/context/grouped-search": "dense",
            "/context/hybrid/text": "text_hybrid",
            "/context/hybrid/graph-first": "graph_first",
            "/context/hybrid/vector-first": "vector_first",
            "/context/hybrid/rank-fusion": "rank_fusion",
        }[path]
        return payload
    return deepcopy(responses["OperationEnvelope"])


def _json_body(request: httpx.Request) -> dict[str, Any] | None:
    return json.loads(request.content) if request.content else None


def test_flat_context_namespace_and_every_method_route_contract() -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=_response_payload(request))

    project = _client(respond).project()
    context = project.context
    source = {
        "mode": "existing",
        "schema_name": "public",
        "table_name": "documents",
        "source_key_column": "id",
    }
    vector = {"column_name": "embedding", "dimensions": 2, "metric": "cosine"}
    create_options = {
        "source": source,
        "vector": vector,
        "text_column": "content",
        "result_columns": ["title"],
        "filter_columns": ["tenant_id"],
        "jsonb_filter_paths": [{"key": "topic", "column": "metadata", "path": ["topic"]}],
        "max_search_limit": 500,
    }

    context.get_capabilities()
    context.discover_sources(schema_names=["public"])
    context.preflight("support_docs", **create_options)
    collections = context.list_collections(status="ready", limit=25, cursor="collections-cursor")
    context.get_collection(COLLECTION_ID)
    context.get_collection_status(COLLECTION_ID)
    context.verify_collection(COLLECTION_ID)
    context.get_collection_diagnostics(COLLECTION_ID)
    operation = context.create_collection(
        "support_docs", **create_options, idempotency_key=IDEMPOTENCY_KEY
    )
    context.update_collection(
        COLLECTION_ID,
        text_column=None,
        result_columns=["title", "url"],
        max_search_limit=400,
        idempotency_key=IDEMPOTENCY_KEY,
    )
    context.set_default_collection(COLLECTION_ID, idempotency_key=IDEMPOTENCY_KEY)
    context.reindex_collection(COLLECTION_ID, idempotency_key=IDEMPOTENCY_KEY)
    context.delete_collection(
        COLLECTION_ID,
        confirm_collection_id=COLLECTION_ID,
        idempotency_key=IDEMPOTENCY_KEY,
    )
    context.list_filters(COLLECTION_ID)
    context.add_filter_column(
        COLLECTION_ID, "tenant_id", "tenant_id", idempotency_key=IDEMPOTENCY_KEY
    )
    context.add_jsonb_filter_path(
        COLLECTION_ID,
        "topic",
        "metadata",
        ["topic"],
        idempotency_key=IDEMPOTENCY_KEY,
    )
    context.get_point_status(COLLECTION_ID)
    points = context.scroll_points(COLLECTION_ID, limit=25, cursor="points-cursor")
    context.upsert_points(
        COLLECTION_ID, ["doc-1", "doc-1", "doc-2"], idempotency_key=IDEMPOTENCY_KEY
    )
    context.delete_points(COLLECTION_ID, ["doc-1"], idempotency_key=IDEMPOTENCY_KEY)
    context.reconcile_points(COLLECTION_ID, idempotency_key=IDEMPOTENCY_KEY)
    operations = context.list_operations(
        collection_id=COLLECTION_ID,
        kind="points_reconcile",
        status="running",
        limit=25,
        cursor="operations-cursor",
    )
    context.get_operation(OPERATION_ID)
    context.cancel_operation(OPERATION_ID, idempotency_key=IDEMPOTENCY_KEY)
    context.retry_operation(OPERATION_ID, idempotency_key=IDEMPOTENCY_KEY)
    context.count("support_docs", filter={"must": [{"key": "tenant_id", "match": "acme"}]})
    context.facets("support_docs", "tenant_id", limit=5)
    context.search("support_docs", [0.1, 0.2], limit=5)
    context.grouped_search(
        "support_docs", [0.1, 0.2], group_by="tenant_id", group_limit=2, limit=5
    )
    context.recall_check("support_docs", [0.1, 0.2], limit=5, minimum_recall=0.9)
    context.text_hybrid("support_docs", [0.1, 0.2], query="deployment", limit=5)
    context.graph_first(
        "support_docs",
        [0.1, 0.2],
        start={"schema": "public", "table": "accounts", "id": "acct-1"},
        relationship_types=["owns", "owns"],
        direction="both",
        limit=5,
    )
    context.vector_first(
        "support_docs", [0.1, 0.2], context_limit=20, direction="in", limit=5
    )
    context.rank_fusion(
        "support_docs",
        [0.1, 0.2],
        start={"schema": "public", "table": "accounts", "id": "acct-1"},
        context_weight=0.6,
        graph_weight=0.4,
        limit=5,
    )
    joint = context.joint(
        "support_docs",
        [0.1, 0.2],
        query="deployment",
        starts=[
            {"schema": "public", "table": "accounts", "id": "acct-1"},
            {"schema": "public", "table": "accounts", "id": "acct-1"},
        ],
        relationship_types=["owns", "owns"],
        semantic_weight=0.4,
        lexical_weight=0.2,
        graph_weight=0.4,
        limit=5,
    )

    assert isinstance(collections, Page)
    assert isinstance(points, Page)
    assert isinstance(operations, Page)
    assert isinstance(operation, ContextOperation)
    assert isinstance(joint, ContextJointResponse)
    assert not hasattr(context, "collection")
    assert not hasattr(context, "collections")
    assert not hasattr(context, "operations")
    assert not hasattr(operation, "wait")
    assert not hasattr(operation, "cancel")
    assert not hasattr(operation, "retry")
    assert not hasattr(operation, "collection")

    actual = [
        (
            request.method,
            request.url.path.removeprefix("/v1"),
            dict(request.url.params),
            _json_body(request),
        )
        for request in requests
    ]
    assert [(method, path) for method, path, _query, _body in actual] == [
        ("GET", "/context/capabilities"),
        ("POST", "/context/discover"),
        ("POST", "/context/preflight"),
        ("GET", "/context/collections"),
        ("GET", f"/context/collections/{COLLECTION_ID}"),
        ("GET", f"/context/collections/{COLLECTION_ID}/status"),
        ("POST", f"/context/collections/{COLLECTION_ID}/verify"),
        ("GET", f"/context/collections/{COLLECTION_ID}/diagnostics"),
        ("POST", "/context/collections"),
        ("PATCH", f"/context/collections/{COLLECTION_ID}"),
        ("PATCH", f"/context/collections/{COLLECTION_ID}"),
        ("POST", f"/context/collections/{COLLECTION_ID}/reindex"),
        ("DELETE", f"/context/collections/{COLLECTION_ID}"),
        ("GET", f"/context/collections/{COLLECTION_ID}/filters"),
        ("POST", f"/context/collections/{COLLECTION_ID}/filters/columns"),
        ("POST", f"/context/collections/{COLLECTION_ID}/filters/jsonb-paths"),
        ("GET", f"/context/collections/{COLLECTION_ID}/points/status"),
        ("GET", f"/context/collections/{COLLECTION_ID}/points"),
        ("POST", f"/context/collections/{COLLECTION_ID}/points/upsert"),
        ("POST", f"/context/collections/{COLLECTION_ID}/points/delete"),
        ("POST", f"/context/collections/{COLLECTION_ID}/points/reconcile"),
        ("GET", "/context/operations"),
        ("GET", f"/context/operations/{OPERATION_ID}"),
        ("POST", f"/context/operations/{OPERATION_ID}/cancel"),
        ("POST", f"/context/operations/{OPERATION_ID}/retry"),
        ("POST", "/context/count"),
        ("POST", "/context/facets"),
        ("POST", "/context/search"),
        ("POST", "/context/grouped-search"),
        ("POST", "/context/recall-check"),
        ("POST", "/context/hybrid/text"),
        ("POST", "/context/hybrid/graph-first"),
        ("POST", "/context/hybrid/vector-first"),
        ("POST", "/context/hybrid/rank-fusion"),
        ("POST", "/context/hybrid/joint"),
    ]
    assert actual[3][2] == {
        "status": "ready",
        "limit": "25",
        "cursor": "collections-cursor",
    }
    assert actual[17][2] == {"limit": "25", "cursor": "points-cursor"}
    assert actual[21][2] == {
        "collection_id": COLLECTION_ID,
        "kind": "points_reconcile",
        "status": "running",
        "limit": "25",
        "cursor": "operations-cursor",
    }
    assert actual[1][3] == {"schema_names": ["public"]}
    expected_collection_body = {
        "name": "support_docs",
        "source": {
            "mode": "existing",
            "schema_name": "public",
            "table_name": "documents",
            "source_key_column": "id",
            "content_column": None,
            "metadata_column": None,
        },
        "vector": {"column_name": "embedding", "dimensions": 2, "metric": "cosine"},
        "text_column": "content",
        "result_columns": ["title"],
        "filter_columns": ["tenant_id"],
        "jsonb_filter_paths": [
            {"key": "topic", "column": "metadata", "path": ["topic"]}
        ],
        "index_kind": "hnsw",
        "max_search_limit": 500,
    }
    assert actual[2][3] == expected_collection_body
    assert actual[8][3] == expected_collection_body
    assert actual[6][3] == {}
    assert actual[9][3] == {
        "text_column": None,
        "result_columns": ["title", "url"],
        "max_search_limit": 400,
    }
    assert actual[10][3] == {"is_default": True}
    assert actual[11][3] == {}
    assert actual[12][3] == {"confirm_collection_id": COLLECTION_ID}
    assert actual[14][3] == {"key": "tenant_id", "column": "tenant_id"}
    assert actual[15][3] == {"key": "topic", "column": "metadata", "path": ["topic"]}
    assert actual[18][3] == {"source_keys": ["doc-1", "doc-2"]}
    assert actual[19][3] == {"source_keys": ["doc-1"]}
    assert actual[20][3] == {}
    assert actual[23][3] == {}
    assert actual[24][3] == {}
    assert actual[25][3] == {
        "collection": "support_docs",
        "filter": {"must": [{"key": "tenant_id", "match": "acme"}]},
    }
    assert actual[26][3] == {
        "collection": "support_docs",
        "filter": None,
        "field": "tenant_id",
        "limit": 5,
    }
    assert actual[27][3] == {
        "collection": "support_docs",
        "filter": None,
        "embedding": [0.1, 0.2],
        "limit": 5,
    }
    assert actual[28][3] == {
        "collection": "support_docs",
        "embedding": [0.1, 0.2],
        "group_by": "tenant_id",
        "group_limit": 2,
        "limit": 5,
    }
    assert actual[29][3] == {
        "collection": "support_docs",
        "filter": None,
        "embedding": [0.1, 0.2],
        "limit": 5,
        "minimum_recall": 0.9,
    }
    assert actual[30][3] == {
        "collection": "support_docs",
        "embedding": [0.1, 0.2],
        "query": "deployment",
        "limit": 5,
    }
    assert actual[31][3]["relationship_types"] == ["owns"]
    assert actual[31][3]["direction"] == "both"
    assert actual[33][3]["weights"] == {"context": 0.6, "graph": 0.4}
    assert actual[34][3]["starts"] == [
        {"schema": "public", "table": "accounts", "id": "acct-1"}
    ]
    assert actual[34][3]["weights"] == {"semantic": 0.4, "lexical": 0.2, "graph": 0.4}

    mutation_indexes = {8, 9, 10, 11, 12, 14, 15, 18, 19, 20, 23, 24}
    for index, request in enumerate(requests):
        if index in mutation_indexes:
            assert request.headers["Idempotency-Key"] == IDEMPOTENCY_KEY
        else:
            assert "Idempotency-Key" not in request.headers
        assert request.headers["Authorization"] == f"Bearer {API_KEY}"
        assert request.headers["User-Agent"] == f"polygres-python/{__version__}"
        assert request.headers[API_VERSION_HEADER] == DEFAULT_API_VERSION
        assert request.headers[CLIENT_INFO_HEADER].startswith(
            f"polygres-python/{__version__}; python/"
        )


@pytest.mark.parametrize(
    "invoke",
    [
        lambda context: context.get_collection("support_docs"),
        lambda context: context.get_collection_status("support_docs"),
        lambda context: context.verify_collection("support_docs"),
        lambda context: context.get_collection_diagnostics("support_docs"),
        lambda context: context.update_collection("support_docs", max_search_limit=10),
        lambda context: context.set_default_collection("support_docs"),
        lambda context: context.reindex_collection("support_docs"),
        lambda context: context.list_filters("support_docs"),
        lambda context: context.get_point_status("support_docs"),
        lambda context: context.scroll_points("support_docs"),
        lambda context: context.list_operations(collection_id="support_docs"),
        lambda context: context.get_operation("support_docs"),
    ],
)
def test_administrative_methods_reject_names_before_http(invoke: Callable[[Any], Any]) -> None:
    requests: list[httpx.Request] = []
    context = _client(lambda request: requests.append(request)).project().context

    with pytest.raises(PolygresValidationError):
        invoke(context)

    assert requests == []


def test_retrieval_accepts_uuid_or_exact_name_and_rejects_invalid_local_input() -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=_response_payload(request))

    context = _client(respond).project().context
    context.search(COLLECTION_ID, [0.1])
    context.search("support_docs", [0.1])
    before = len(requests)
    with pytest.raises(PolygresValidationError):
        context.search("not-a-name", [0.1])
    with pytest.raises(PolygresValidationError):
        context.search("support_docs", [True])
    with pytest.raises(PolygresValidationError):
        context.delete_collection(
            COLLECTION_ID,
            confirm_collection_id=OPERATION_ID,
        )
    with pytest.raises(PolygresValidationError):
        context.joint("support_docs", [0.1], lexical_weight=0.1)
    with pytest.raises(PolygresValidationError):
        context.joint("support_docs", [0.1], relationship_types="")  # type: ignore[arg-type]
    with pytest.raises(PolygresValidationError):
        context.create_collection(
            "support_docs",
            source={"mode": "existing", "schema_name": "public", "table_name": "documents"},
            vector={"dimensions": 2},
            result_columns="",  # type: ignore[arg-type]
        )
    assert len(requests) == before


def test_point_mutation_preserves_synchronous_or_operation_response() -> None:
    calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        key = "PointMutationResponse" if calls == 1 else "OperationEnvelope"
        return httpx.Response(200, json=deepcopy(FIXTURES["responses"][key]))

    context = _client(respond).project().context
    synchronous = context.upsert_points(COLLECTION_ID, ["doc-1"])
    durable = context.upsert_points(COLLECTION_ID, ["doc-1"])

    assert synchronous.__class__.__name__ == "PointMutationResponse"
    assert isinstance(durable, ContextOperation)


def test_private_operation_result_payload_is_never_exposed() -> None:
    payload = deepcopy(FIXTURES["responses"]["OperationEnvelope"])
    payload["operation"]["result_payload"] = {"private": True}

    operation = _client(
        lambda _request: httpx.Response(200, json=payload)
    ).project().context.create_collection(
        "support_docs",
        source={"mode": "existing", "schema_name": "public", "table_name": "documents"},
        vector={"dimensions": 2},
    )

    assert "result_payload" not in operation.to_dict()
    assert not hasattr(operation, "result_payload")


def test_retry_classification_and_mutation_key_reuse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(client_module.time, "sleep", lambda _seconds: None)
    seen: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        matching = [item for item in seen if item.url.path == request.url.path]
        if len(matching) == 1:
            return httpx.Response(503, json={"error": {"code": "SERVICE_UNAVAILABLE"}})
        return httpx.Response(200, json=_response_payload(request))

    context = _client(respond, retries=1).project().context
    context.count("support_docs")
    with pytest.raises(PolygresRuntimeError):
        context.search("support_docs", [0.1])
    context.reindex_collection(COLLECTION_ID, idempotency_key=IDEMPOTENCY_KEY)

    count_calls = [request for request in seen if request.url.path.endswith("/context/count")]
    search_calls = [request for request in seen if request.url.path.endswith("/context/search")]
    mutation_calls = [request for request in seen if request.url.path.endswith("/reindex")]
    assert len(count_calls) == 2
    assert len(search_calls) == 1
    assert len(mutation_calls) == 2
    assert {request.headers["Idempotency-Key"] for request in mutation_calls} == {
        IDEMPOTENCY_KEY
    }
    assert mutation_calls[0].content == mutation_calls[1].content


@pytest.mark.parametrize(
    "invoke",
    [
        lambda context: context.search("support_docs", [0.1]),
        lambda context: context.grouped_search(
            "support_docs", [0.1], group_by="tenant_id"
        ),
        lambda context: context.recall_check("support_docs", [0.1]),
        lambda context: context.text_hybrid(
            "support_docs", [0.1], query="deployment"
        ),
        lambda context: context.graph_first(
            "support_docs",
            [0.1],
            start={"schema": "public", "table": "accounts", "id": "acct-1"},
        ),
        lambda context: context.vector_first("support_docs", [0.1]),
        lambda context: context.rank_fusion(
            "support_docs",
            [0.1],
            start={"schema": "public", "table": "accounts", "id": "acct-1"},
        ),
        lambda context: context.joint("support_docs", [0.1]),
    ],
)
def test_ranked_requests_never_retry(
    invoke: Callable[[Any], Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(client_module.time, "sleep", lambda _seconds: None)
    attempts = 0

    def respond(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503, json={"error": {"code": "SERVICE_UNAVAILABLE"}})

    with pytest.raises(PolygresRuntimeError):
        invoke(_client(respond, retries=2).project().context)

    assert attempts == 1


def test_context_error_mapping_redacts_secrets_and_preserves_safe_fields() -> None:
    def respond(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            409,
            json={
                "request_id": "req_context_error",
                "error": {
                    "code": "CONTEXT_GRAPH_NOT_READY",
                    "message": f"Graph is unavailable for {API_KEY}",
                    "details": {"graph_status": "not_configured", "api_key": API_KEY},
                },
            },
        )

    with pytest.raises(PolygresAPIError) as exc:
        _client(respond).project().context.graph_first(
            "support_docs",
            [0.1],
            start={"schema": "public", "table": "accounts", "id": "acct-1"},
        )

    assert exc.value.code == "CONTEXT_GRAPH_NOT_READY"
    assert exc.value.request_id == "req_context_error"
    assert exc.value.details == {"graph_status": "not_configured"}
    assert API_KEY not in str(exc.value)
    assert API_KEY not in repr(exc.value.details)


def test_additive_fields_and_ranked_response_shape_are_preserved() -> None:
    payload = deepcopy(FIXTURES["responses"]["RankedResponse"])
    payload["future_envelope"] = {"large": 10**30}
    payload["results"] = [
        {
            "point_id": 1,
            "source": {"schema": "public", "table": "documents", "id": "doc-1"},
            "rank": 1,
            "score": 0.25,
            "score_kind": "context_score",
            "metric": "cosine",
            "properties": {},
            "group_value": None,
            "group_rank": None,
            "future_result": "kept",
        }
    ]

    response = _client(lambda _request: httpx.Response(200, json=payload)).project().context.search(
        "support_docs", [0.1]
    )
    serialized = response.to_dict()

    assert isinstance(response.results[0], ContextSearchResult)
    assert serialized["future_envelope"] == {"large": 10**30}
    assert serialized["results"][0]["future_result"] == "kept"
    assert "next_cursor" not in serialized
    assert "has_more" not in serialized


def test_joint_uses_one_isolated_route_and_preserves_typed_provenance() -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.url.path == "/v1/context/hybrid/joint"
        return httpx.Response(200, json=deepcopy(FIXTURES["joint_examples"]["additive_field"]))

    response = _client(respond, retries=2).project().context.joint(
        "support_docs",
        [0.1, 0.2],
        starts=[{"schema": "public", "table": "accounts", "id": "acct-1"}],
    )

    assert len(requests) == 1
    assert response.mode.value == "joint"
    assert response.results[0].introduced_by_graph is True
    assert response.results[0].baseline_rank is None
    assert response.results[0].rank_lift is None
    assert response.to_dict()["future_additive_field"] == "synthetic"


class _Clock:
    def __init__(self) -> None:
        self.now = 0.0
        self.delays: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.delays.append(seconds)
        self.now += seconds


def _operation(
    *,
    status: str,
    stage: str,
    collection_id: str | None = None,
    error: dict[str, Any] | None = None,
) -> ContextOperation:
    payload = deepcopy(FIXTURES["responses"]["ContextOperation"])
    payload.update(
        {
            "id": OPERATION_ID,
            "collection_id": collection_id,
            "status": status,
            "stage": stage,
            "error": error,
            "request_id": "req_wait",
        }
    )
    return ContextOperation.model_validate(payload)


def test_waiter_adaptive_schedule_stage_reset_retry_after_and_create_result() -> None:
    assert [context_poll_interval(value) for value in (0, 10, 10.1, 60, 60.1, 300, 301)] == [
        2,
        2,
        5,
        5,
        15,
        15,
        30,
    ]
    clock = _Clock()
    responses = [
        (_operation(status="running", stage="building_index"), "7"),
        (
            _operation(
                status="succeeded",
                stage="ready",
                collection_id=COLLECTION_ID,
            ),
            None,
        ),
    ]

    completed = wait_for_context_operation(
        OPERATION_ID,
        initial=_operation(status="queued", stage="queued"),
        fetch=lambda _deadline: responses.pop(0),
        timeout=30,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
    )

    assert clock.delays == [2, 7]
    assert str(completed.collection_id) == COLLECTION_ID


def test_waiter_uses_one_deadline_and_resets_interval_after_stage_change() -> None:
    clock = _Clock()
    stages = ["index"] * 6 + ["verify"] + ["ready"]
    deadlines: list[float] = []

    def fetch(deadline: float) -> tuple[ContextOperation, str | None]:
        deadlines.append(deadline)
        stage = stages.pop(0)
        status = "succeeded" if stage == "ready" else "running"
        return _operation(status=status, stage=stage, collection_id=COLLECTION_ID), None

    completed = wait_for_context_operation(
        OPERATION_ID,
        initial=_operation(status="running", stage="index"),
        fetch=fetch,
        timeout=60,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
    )

    assert completed.status == "succeeded"
    assert clock.delays == [2, 2, 2, 2, 2, 2, 5, 2]
    assert deadlines == [60.0] * 8


def test_waiter_timeout_failure_and_cancellation_do_not_cancel() -> None:
    clock = _Clock()
    fetches = 0

    def fetch(_deadline: float) -> tuple[ContextOperation, str | None]:
        nonlocal fetches
        fetches += 1
        return _operation(status="running", stage="queued"), None

    with pytest.raises(PolygresRuntimeError) as timeout_error:
        wait_for_context_operation(
            OPERATION_ID,
            initial=_operation(status="queued", stage="queued"),
            fetch=fetch,
            timeout=1,
            monotonic=clock.monotonic,
            sleep=clock.sleep,
        )
    assert timeout_error.value.code == "CONTEXT_OPERATION_TIMEOUT"
    assert clock.delays == [1]
    assert fetches == 0

    failure = {
        "code": "CONTEXT_COLLECTION_NOT_FOUND",
        "message": "The collection disappeared.",
        "details": {"collection": "support_docs", "private": "removed"},
        "http_status": 404,
    }
    with pytest.raises(PolygresNotFoundError) as failed:
        wait_for_context_operation(
            OPERATION_ID,
            initial=_operation(status="failed", stage="failed", error=failure),
            fetch=fetch,
            timeout=10,
        )
    assert failed.value.code == "CONTEXT_COLLECTION_NOT_FOUND"
    assert failed.value.request_id == "req_wait"
    assert failed.value.details == {
        "collection": "support_docs",
        "operation_id": OPERATION_ID,
    }

    with pytest.raises(PolygresAPIError) as cancelled:
        wait_for_context_operation(
            OPERATION_ID,
            initial=_operation(status="cancelled", stage="cancelled"),
            fetch=fetch,
            timeout=10,
        )
    assert cancelled.value.code == "CONTEXT_OPERATION_CANCELLED"


def test_namespace_wait_polls_only_operation_route(monkeypatch: pytest.MonkeyPatch) -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        payload = deepcopy(FIXTURES["responses"]["OperationEnvelope"])
        payload["operation"].update(
            {"id": OPERATION_ID, "status": "succeeded", "stage": "ready"}
        )
        return httpx.Response(200, headers={"Retry-After": "3"}, json=payload)

    observed: dict[str, Any] = {}

    def immediate(
        operation_id: str,
        *,
        initial: ContextOperation | None,
        fetch: Callable[[float], tuple[ContextOperation, str | None]],
        timeout: float,
    ) -> ContextOperation:
        observed.update({"id": operation_id, "initial": initial, "timeout": timeout})
        operation, retry_after = fetch(client_module.time.monotonic() + 100.0)
        observed["retry_after"] = retry_after
        return operation

    monkeypatch.setattr("polygres.context.wait_for_context_operation", immediate)
    completed = _client(respond).project().context.wait_for_operation(OPERATION_ID, timeout=9)

    assert str(completed.id) == OPERATION_ID
    assert observed == {
        "id": OPERATION_ID,
        "initial": None,
        "timeout": 9,
        "retry_after": "3",
    }
    assert [(request.method, request.url.path) for request in requests] == [
        ("GET", f"/v1/context/operations/{OPERATION_ID}")
    ]
