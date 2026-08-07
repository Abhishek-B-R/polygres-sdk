# Polygres Python SDK v1 method reference

This file is generated. Edit Python method metadata, docstrings, or the Runtime OpenAPI contract instead.

- SDK package version: `0.2.0`
- HTTP API family: `v1`
- Default API behavior version: `2026-08-04`
- Method specification schema: `1`
- Models and exceptions: [SDK README](../README.md)

## `project`

| SDK method | HTTP operation | Since | Retry | Pagination | Deprecated |
| --- | --- | --- | --- | --- | --- |
| `project.connection_info()` | `GET /v1/connection-info` (`runtime_connection_info_get`) | `0.1.0` | `read_only_get` | `none` | No |
| `project.readiness()` | `GET /v1/retrieval/readiness` (`runtime_retrieval_readiness`) | `0.1.0` | `read_only_get` | `none` | No |

### `project.connection_info()`

Return passwordless direct and pooled connection information.

```python
connection = project.connection_info()
```

### `project.readiness()`

Return retrieval readiness for the Runtime project.

```python
readiness = project.readiness()
```

## `project.context`

| SDK method | HTTP operation | Since | Retry | Pagination | Deprecated |
| --- | --- | --- | --- | --- | --- |
| `project.context.acknowledge_onboarding()` | `POST /v1/context/onboarding/acknowledge` (`runtime_context_acknowledge_onboarding`) | `0.2.0` | `idempotent_mutation` | `none` | No |
| `project.context.add_filter_column()` | `POST /v1/context/collections/{collection_id}/filters/columns` (`runtime_context_add_filter_column`) | `0.2.0` | `idempotent_mutation` | `none` | No |
| `project.context.add_jsonb_filter_path()` | `POST /v1/context/collections/{collection_id}/filters/jsonb-paths` (`runtime_context_add_filter_jsonb_path`) | `0.2.0` | `idempotent_mutation` | `none` | No |
| `project.context.cancel_operation()` | `POST /v1/context/operations/{operation_id}/cancel` (`runtime_context_cancel_operation`) | `0.2.0` | `idempotent_mutation` | `none` | No |
| `project.context.count()` | `POST /v1/context/count` (`runtime_context_count`) | `0.2.0` | `read_only_post` | `none` | No |
| `project.context.create_collection()` | `POST /v1/context/collections` (`runtime_context_create_collection`) | `0.2.0` | `idempotent_mutation` | `none` | No |
| `project.context.delete_collection()` | `DELETE /v1/context/collections/{collection_id}` (`runtime_context_delete_collection`) | `0.2.0` | `idempotent_mutation` | `none` | No |
| `project.context.delete_points()` | `POST /v1/context/collections/{collection_id}/points/delete` (`runtime_context_delete_points`) | `0.2.0` | `idempotent_mutation` | `none` | No |
| `project.context.discover_sources()` | `POST /v1/context/discover` (`runtime_context_discover`) | `0.2.0` | `read_only_post` | `none` | No |
| `project.context.dismiss_onboarding()` | `POST /v1/context/onboarding/dismiss` (`runtime_context_dismiss_onboarding`) | `0.2.0` | `idempotent_mutation` | `none` | No |
| `project.context.evaluate_onboarding()` | `POST /v1/context/onboarding/evaluate` (`runtime_context_evaluate_onboarding`) | `0.2.0` | `read_only_post` | `none` | No |
| `project.context.facets()` | `POST /v1/context/facets` (`runtime_context_facets`) | `0.2.0` | `read_only_post` | `none` | No |
| `project.context.get_capabilities()` | `GET /v1/context/capabilities` (`runtime_context_capabilities`) | `0.2.0` | `read_only_get` | `none` | No |
| `project.context.get_collection()` | `GET /v1/context/collections/{collection_id}` (`runtime_context_get_collection`) | `0.2.0` | `read_only_get` | `none` | No |
| `project.context.get_collection_diagnostics()` | `GET /v1/context/collections/{collection_id}/diagnostics` (`runtime_context_get_diagnostics`) | `0.2.0` | `read_only_get` | `none` | No |
| `project.context.get_collection_status()` | `GET /v1/context/collections/{collection_id}/status` (`runtime_context_get_status`) | `0.2.0` | `read_only_get` | `none` | No |
| `project.context.get_onboarding()` | `GET /v1/context/onboarding` (`runtime_context_get_onboarding`) | `0.2.0` | `read_only_get` | `none` | No |
| `project.context.get_operation()` | `GET /v1/context/operations/{operation_id}` (`runtime_context_get_operation`) | `0.2.0` | `read_only_get` | `none` | No |
| `project.context.get_point_status()` | `GET /v1/context/collections/{collection_id}/points/status` (`runtime_context_get_point_status`) | `0.2.0` | `read_only_get` | `none` | No |
| `project.context.graph_first()` | `POST /v1/context/hybrid/graph-first` (`runtime_context_graph_first`) | `0.2.0` | `none` | `none` | No |
| `project.context.grouped_search()` | `POST /v1/context/grouped-search` (`runtime_context_grouped_search`) | `0.2.0` | `none` | `none` | No |
| `project.context.joint()` | `POST /v1/context/hybrid/joint` (`runtime_context_joint`) | `0.2.0` | `none` | `none` | No |
| `project.context.list_collections()` | `GET /v1/context/collections` (`runtime_context_list_collections`) | `0.2.0` | `read_only_get` | `auto_cursor` | No |
| `project.context.list_filters()` | `GET /v1/context/collections/{collection_id}/filters` (`runtime_context_list_filters`) | `0.2.0` | `read_only_get` | `none` | No |
| `project.context.list_operations()` | `GET /v1/context/operations` (`runtime_context_list_operations`) | `0.2.0` | `read_only_get` | `auto_cursor` | No |
| `project.context.preflight()` | `POST /v1/context/preflight` (`runtime_context_preflight`) | `0.2.0` | `read_only_post` | `none` | No |
| `project.context.rank_fusion()` | `POST /v1/context/hybrid/rank-fusion` (`runtime_context_rank_fusion`) | `0.2.0` | `none` | `none` | No |
| `project.context.recall_check()` | `POST /v1/context/recall-check` (`runtime_context_recall_check`) | `0.2.0` | `none` | `none` | No |
| `project.context.reconcile_points()` | `POST /v1/context/collections/{collection_id}/points/reconcile` (`runtime_context_reconcile_points`) | `0.2.0` | `idempotent_mutation` | `none` | No |
| `project.context.refresh_onboarding()` | `POST /v1/context/onboarding/refresh` (`runtime_context_refresh_onboarding`) | `0.2.0` | `read_only_post` | `none` | No |
| `project.context.reindex_collection()` | `POST /v1/context/collections/{collection_id}/reindex` (`runtime_context_reindex_collection`) | `0.2.0` | `idempotent_mutation` | `none` | No |
| `project.context.retry_operation()` | `POST /v1/context/operations/{operation_id}/retry` (`runtime_context_retry_operation`) | `0.2.0` | `idempotent_mutation` | `none` | No |
| `project.context.scroll_points()` | `GET /v1/context/collections/{collection_id}/points` (`runtime_context_scroll_points`) | `0.2.0` | `read_only_get` | `auto_cursor` | No |
| `project.context.search()` | `POST /v1/context/search` (`runtime_context_search`) | `0.2.0` | `none` | `none` | No |
| `project.context.set_default_collection()` | `PATCH /v1/context/collections/{collection_id}` (`runtime_context_update_collection`) | `0.2.0` | `idempotent_mutation` | `none` | No |
| `project.context.text_hybrid()` | `POST /v1/context/hybrid/text` (`runtime_context_text_hybrid`) | `0.2.0` | `none` | `none` | No |
| `project.context.update_collection()` | `PATCH /v1/context/collections/{collection_id}` (`runtime_context_update_collection`) | `0.2.0` | `idempotent_mutation` | `none` | No |
| `project.context.upsert_points()` | `POST /v1/context/collections/{collection_id}/points/upsert` (`runtime_context_upsert_points`) | `0.2.0` | `idempotent_mutation` | `none` | No |
| `project.context.vector_first()` | `POST /v1/context/hybrid/vector-first` (`runtime_context_vector_first`) | `0.2.0` | `none` | `none` | No |
| `project.context.verify_collection()` | `POST /v1/context/collections/{collection_id}/verify` (`runtime_context_verify_collection`) | `0.2.0` | `read_only_post` | `none` | No |
| `project.context.wait_for_operation()` | `GET /v1/context/operations/{operation_id}` (`runtime_context_get_operation`) | `0.2.0` | `polling` | `none` | No |

### `project.context.acknowledge_onboarding()`

Record that the pgContext bridge offer was shown.

```python
onboarding = project.context.acknowledge_onboarding()
```

### `project.context.add_filter_column()`

Register a scalar filter column on a collection.

```python
operation = project.context.add_filter_column(collection_id, "tenant", "tenant_id")
```

### `project.context.add_jsonb_filter_path()`

Register a JSONB filter path on a collection.

```python
operation = project.context.add_jsonb_filter_path(collection_id, "topic", "metadata", ["topic"])
```

### `project.context.cancel_operation()`

Request cancellation of a durable Context operation.

```python
operation = project.context.cancel_operation(operation_id)
```

### `project.context.count()`

Count Context points matching an optional filter.

```python
count = project.context.count("support")
```

### `project.context.create_collection()`

Create a durable Context collection operation.

```python
operation = project.context.create_collection("support", source=source, vector=vector)
```

### `project.context.delete_collection()`

Start deletion of a confirmed Context collection.

```python
operation = project.context.delete_collection(collection_id, confirm_collection_id=collection_id)
```

### `project.context.delete_points()`

Delete selected source rows from Context points.

```python
result = project.context.delete_points(collection_id, ["row-1"])
```

### `project.context.discover_sources()`

Discover tables and columns eligible for Context collections.

```python
sources = project.context.discover_sources()
```

### `project.context.dismiss_onboarding()`

Dismiss the pgContext bridge offer for this project.

```python
onboarding = project.context.dismiss_onboarding()
```

### `project.context.evaluate_onboarding()`

Evaluate and cache pgvector bridge eligibility.

```python
onboarding = project.context.evaluate_onboarding()
```

### `project.context.facets()`

Return facet counts for a registered Context field.

```python
facets = project.context.facets("support", "tenant_id")
```

### `project.context.get_capabilities()`

Return pgContext capabilities for this Runtime.

```python
capabilities = project.context.get_capabilities()
```

### `project.context.get_collection()`

Return one Context collection by UUID.

```python
collection = project.context.get_collection(collection_id)
```

### `project.context.get_collection_diagnostics()`

Return diagnostics for a Context collection.

```python
diagnostics = project.context.get_collection_diagnostics(collection_id)
```

### `project.context.get_collection_status()`

Return the current status of a Context collection.

```python
status = project.context.get_collection_status(collection_id)
```

### `project.context.get_onboarding()`

Return cached pgContext onboarding state without running discovery.

```python
onboarding = project.context.get_onboarding()
```

### `project.context.get_operation()`

Return one durable Context operation.

```python
operation = project.context.get_operation(operation_id)
```

### `project.context.get_point_status()`

Return point synchronization status for a collection.

```python
status = project.context.get_point_status(collection_id)
```

### `project.context.graph_first()`

Run graph-first Context hybrid retrieval.

```python
results = project.context.graph_first("support", embedding, start=start)
```

### `project.context.grouped_search()`

Run grouped dense Context retrieval.

```python
results = project.context.grouped_search("support", embedding, group_by="tenant_id")
```

### `project.context.joint()`

Run coupled Context and graph joint retrieval.

```python
results = project.context.joint("support", embedding)
```

### `project.context.list_collections()`

List Context collections with cursor pagination.

```python
page = project.context.list_collections()
```

### `project.context.list_filters()`

List registered filters for a Context collection.

```python
filters = project.context.list_filters(collection_id)
```

### `project.context.list_operations()`

List durable Context operations with cursor pagination.

```python
page = project.context.list_operations()
```

### `project.context.preflight()`

Validate a proposed Context collection without creating it.

```python
report = project.context.preflight("support", source=source, vector=vector)
```

### `project.context.rank_fusion()`

Fuse Context and graph rankings.

```python
results = project.context.rank_fusion("support", embedding, start=start)
```

### `project.context.recall_check()`

Measure approximate-search recall for a Context collection.

```python
report = project.context.recall_check("support", embedding)
```

### `project.context.reconcile_points()`

Reconcile all source rows with Context points.

```python
operation = project.context.reconcile_points(collection_id)
```

### `project.context.refresh_onboarding()`

Explicitly refresh pgvector bridge eligibility.

```python
onboarding = project.context.refresh_onboarding()
```

### `project.context.reindex_collection()`

Start a durable reindex operation for a collection.

```python
operation = project.context.reindex_collection(collection_id)
```

### `project.context.retry_operation()`

Retry an eligible failed Context operation.

```python
operation = project.context.retry_operation(operation_id)
```

### `project.context.scroll_points()`

Scroll Context point mappings with cursor pagination.

```python
page = project.context.scroll_points(collection_id)
```

### `project.context.search()`

Run dense Context retrieval.

```python
results = project.context.search("support", embedding)
```

### `project.context.set_default_collection()`

Make a Context collection the project default.

```python
operation = project.context.set_default_collection(collection_id)
```

### `project.context.text_hybrid()`

Run dense and lexical Context retrieval.

```python
results = project.context.text_hybrid("support", embedding, query="refund")
```

### `project.context.update_collection()`

Update mutable Context collection settings.

```python
operation = project.context.update_collection(collection_id, result_columns=["title"])
```

### `project.context.upsert_points()`

Upsert selected source rows into Context points.

```python
result = project.context.upsert_points(collection_id, ["row-1"])
```

### `project.context.vector_first()`

Run vector-first Context hybrid retrieval.

```python
results = project.context.vector_first("support", embedding)
```

### `project.context.verify_collection()`

Verify the physical state of a Context collection.

```python
report = project.context.verify_collection(collection_id)
```

### `project.context.wait_for_operation()`

Poll a durable Context operation until it reaches a terminal state.

```python
completed = project.context.wait_for_operation(operation)
```

## `project.graph`

| SDK method | HTTP operation | Since | Retry | Pagination | Deprecated |
| --- | --- | --- | --- | --- | --- |
| `project.graph.connection()` | `POST /v1/graph/connection` (`runtime_graph_connection`) | `0.1.0` | `read_only_post` | `none` | No |
| `project.graph.expand()` | `POST /v1/graph/expand` (`runtime_graph_expand`) | `0.1.0` | `read_only_post` | `auto_cursor` | No |
| `project.graph.neighborhood()` | `POST /v1/graph/neighborhood` (`runtime_graph_neighborhood`) | `0.1.0` | `read_only_post` | `auto_cursor` | No |
| `project.graph.path()` | `POST /v1/graph/path` (`runtime_graph_path`) | `0.1.0` | `read_only_post` | `none` | No |
| `project.graph.related()` | `POST /v1/graph/related` (`runtime_graph_related`) | `0.1.0` | `read_only_post` | `auto_cursor` | No |

### `project.graph.connection()`

Find graph connections among a set of rows.

```python
connections = project.graph.connection(entities)
```

### `project.graph.expand()`

Expand graph relationships from one or more starting rows.

```python
page = project.graph.expand(start)
```

### `project.graph.neighborhood()`

Return a bounded graph neighborhood around a starting row.

```python
page = project.graph.neighborhood(start)
```

### `project.graph.path()`

Find graph paths between a source and target row.

```python
paths = project.graph.path(source, target)
```

### `project.graph.related()`

Return rows related by one graph hop.

```python
page = project.graph.related(start)
```

## `project.hybrid`

| SDK method | HTTP operation | Since | Retry | Pagination | Deprecated |
| --- | --- | --- | --- | --- | --- |
| `project.hybrid.graph_first()` | `POST /v1/hybrid/graph-first` (`runtime_hybrid_graph_first`) | `0.1.0` | `read_only_post` | `auto_cursor` | No |
| `project.hybrid.joint()` | `POST /v1/hybrid/joint` (`runtime_hybrid_joint`) | `0.1.0` | `read_only_post` | `auto_cursor` | No |
| `project.hybrid.vector_first()` | `POST /v1/hybrid/vector-first` (`runtime_hybrid_vector_first`) | `0.1.0` | `read_only_post` | `auto_cursor` | No |

### `project.hybrid.graph_first()`

Run graph-first hybrid retrieval.

```python
page = project.hybrid.graph_first(start, embedding)
```

### `project.hybrid.joint()`

Run joint vector and graph retrieval.

```python
page = project.hybrid.joint(embedding, start)
```

### `project.hybrid.vector_first()`

Run vector-first hybrid retrieval.

```python
page = project.hybrid.vector_first(embedding)
```

## `project.text`

| SDK method | HTTP operation | Since | Retry | Pagination | Deprecated |
| --- | --- | --- | --- | --- | --- |
| `project.text.fuzzy()` | `POST /v1/text/fuzzy` (`runtime_text_fuzzy`) | `0.1.0` | `read_only_post` | `auto_cursor` | No |
| `project.text.tsvector()` | `POST /v1/text/tsvector` (`runtime_text_tsvector`) | `0.1.0` | `read_only_post` | `auto_cursor` | No |

### `project.text.fuzzy()`

Run fuzzy text search with a named configuration.

```python
page = project.text.fuzzy("query", config="documents")
```

### `project.text.tsvector()`

Run PostgreSQL full-text search with a named configuration.

```python
page = project.text.tsvector("query", config="documents")
```

## `project.vector`

| SDK method | HTTP operation | Since | Retry | Pagination | Deprecated |
| --- | --- | --- | --- | --- | --- |
| `project.vector.search()` | `POST /v1/vector/search` (`runtime_vector_search`) | `0.1.0` | `read_only_post` | `auto_cursor` | No |
| `project.vector.similar_to()` | `POST /v1/vector/similar-to` (`runtime_vector_similar_to`) | `0.1.0` | `read_only_post` | `auto_cursor` | No |

### `project.vector.search()`

Search a configured vector index with an embedding.

```python
page = project.vector.search(embedding)
```

### `project.vector.similar_to()`

Find rows similar to an existing indexed row.

```python
page = project.vector.similar_to("row-id")
```
