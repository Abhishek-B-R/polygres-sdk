import json

import httpx
import pytest
from test_context import FIXTURES, _available_capabilities, _client

from polygres import PolygresValidationError

START = {"schema": "public", "table": "articles", "id": "1"}


@pytest.mark.parametrize(
    "method,args,options,response",
    [
        ("search", ["articles"], {}, "RankedResponse"),
        ("grouped_search", ["articles"], {"group_by": "category"}, "RankedResponse"),
        ("candidate_search", ["articles"], {"candidate_point_ids": [1]}, "PgContextScoredResponse"),
        ("graph_first", ["articles"], {"start": START}, "RankedResponse"),
        ("vector_first", ["articles"], {}, "RankedResponse"),
        ("rank_fusion", ["articles"], {"start": START}, "RankedResponse"),
        ("joint", ["articles"], {}, "ContextJointResponse"),
        ("query", ["articles"], {}, "RankedResponse"),
        ("text_hybrid", ["articles"], {}, "RankedResponse"),
    ],
)
def test_context_text_queries_preserve_methods_and_typed_results(method, args, options, response):
    requests = []

    def handler(request):
        if request.method == "GET":
            return httpx.Response(
                200, json={**_available_capabilities(), "query_embedding_generation": True}
            )
        requests.append(request)
        return httpx.Response(200, json=FIXTURES["responses"][response])

    with _client(handler) as client:
        key = "query" if method in {"query", "text_hybrid"} else "text"
        result = getattr(client.project().context, method)(
            *args,
            **options,
            **{key: "replication"},
            vector_name="content",
            idempotency_key="same-query",
            use_credits=True,
        )
        assert type(result).__name__ == response
    body = json.loads(requests[0].content)
    assert body["text"] == "replication"
    assert body["vector_name"] == "content"
    assert body["use_credits"] is True
    assert requests[0].headers["Idempotency-Key"] == "same-query"


@pytest.mark.parametrize(
    "options",
    [
        {},
        {"text": " "},
        {"text": "hello", "embedding": [1.0]},
        {"embedding": [1.0], "use_credits": True},
    ],
)
def test_invalid_query_inputs_do_not_send_requests(options):
    def handler(request):
        pytest.fail("invalid input sent a request")

    with _client(handler) as client, pytest.raises(PolygresValidationError):
        client.project().context.search("articles", **options)


def test_old_runtime_rejects_text_without_attempting_search():
    def handler(request):
        assert request.method == "GET"
        return httpx.Response(200, json=_available_capabilities())

    with (
        _client(handler) as client,
        pytest.raises(PolygresValidationError, match="does not support"),
    ):
        client.project().context.search("articles", text="hello")


def test_text_query_retry_reuses_key():
    requests = []

    def handler(request):
        if request.method == "GET":
            return httpx.Response(
                200, json={**_available_capabilities(), "query_embedding_generation": True}
            )
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(
                503, json={"error": {"code": "EMBEDDING_SERVICE_UNAVAILABLE", "message": "Retry"}}
            )
        return httpx.Response(200, json=FIXTURES["responses"]["RankedResponse"])

    with _client(handler, retries=1) as client:
        client.project().context.search("articles", text="hello")
    assert len(requests) == 2
    assert requests[0].headers["Idempotency-Key"] == requests[1].headers["Idempotency-Key"]


def test_text_query_plan_is_local_until_execution():
    requests = []

    def handler(request):
        requests.append(request)
        if request.method == "GET":
            return httpx.Response(
                200, json={**_available_capabilities(), "query_embedding_generation": True}
            )
        return httpx.Response(200, json=FIXTURES["responses"]["QueryExecutionResponse"])

    with _client(handler) as client:
        context = client.project().context
        plan = context.query_prefetch(
            [
                context.query_nearest(text="hello", vector_name="content"),
                context.query_nearest([0.1, 0.2]),
            ]
        )
        assert not requests
        context.execute_query("articles", plan, idempotency_key="plan-1")
    body = json.loads(requests[-1].content)
    assert body["plan"]["branches"][0]["text"] == "hello"
    assert body["plan"]["branches"][1]["vector"] == [0.1, 0.2]


@pytest.mark.parametrize(
    "namespace,method,args,options",
    [
        ("vector", "search", [], {}),
        ("hybrid", "graph_first", [START], {}),
        ("hybrid", "vector_first", [], {}),
        ("hybrid", "joint", [], {"start": START}),
    ],
)
def test_legacy_text_queries_keep_pagination_identity(namespace, method, args, options):
    requests = []

    def handler(request):
        if request.method == "GET":
            return httpx.Response(
                200, json={**_available_capabilities(), "query_embedding_generation": True}
            )
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "request_id": "test",
                "results": [],
                "next_cursor": "next" if len(requests) == 1 else None,
                "has_more": len(requests) == 1,
            },
        )

    with _client(handler) as client:
        page = getattr(getattr(client.project(), namespace), method)(*args, **options, text="hello")
        list(page.auto_paging_iter())
    assert len(requests) == 2
    assert requests[0].headers["Idempotency-Key"] == requests[1].headers["Idempotency-Key"]
    assert json.loads(requests[1].content)["cursor"] == "next"
