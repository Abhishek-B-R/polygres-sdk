# Polygres Python SDK v1 method reference

This file is generated. Edit Python method metadata, docstrings, or the Runtime OpenAPI contract instead.

- SDK package version: `0.4.1`
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
| `project.context.add_vector()` | `POST /v1/context/collections/{collection_id}/vectors` (`runtime_context_add_vector`) | `0.2.0` | `idempotent_mutation` | `none` | No |
| `project.context.backfill_points()` | `POST /v1/context/points/backfill` (`runtime_context_backfill_points`) | `0.4.0` | `none` | `none` | No |
| `project.context.bulk_delete_points()` | `POST /v1/context/points/bulk-delete` (`runtime_context_bulk_delete_points`) | `0.4.0` | `none` | `none` | No |
| `project.context.bulk_upsert_points()` | `POST /v1/context/points/bulk-upsert` (`runtime_context_bulk_upsert_points`) | `0.4.0` | `none` | `none` | No |
| `project.context.cancel_operation()` | `POST /v1/context/operations/{operation_id}/cancel` (`runtime_context_cancel_operation`) | `0.2.0` | `idempotent_mutation` | `none` | No |
| `project.context.candidate_search()` | `POST /v1/context/search/candidates` (`runtime_context_candidate_search`) | `0.4.0` | `none` | `none` | No |
| `project.context.clear_payload()` | `POST /v1/context/points/payload/clear` (`runtime_context_clear_payload`) | `0.4.0` | `none` | `none` | No |
| `project.context.collection_aliases()` | `GET /v1/context/aliases` (`runtime_context_list_collection_aliases`) | `0.4.0` | `read_only_get` | `none` | No |
| `project.context.collection_info()` | `GET /v1/context/collections/by-name/{collection_name}/info` (`runtime_context_collection_info`) | `0.4.0` | `read_only_get` | `none` | No |
| `project.context.collection_limits()` | `GET /v1/context/collections/by-name/{collection_name}/limits` (`runtime_context_collection_limits`) | `0.4.0` | `read_only_get` | `none` | No |
| `project.context.collection_vectors()` | `GET /v1/context/collections/by-name/{collection_name}/vectors` (`runtime_context_collection_vectors`) | `0.4.0` | `read_only_get` | `none` | No |
| `project.context.configure_collection_limits()` | `PATCH /v1/context/collections/by-name/{collection_name}/limits` (`runtime_context_configure_collection_limits`) | `0.4.0` | `none` | `none` | No |
| `project.context.configure_vector()` | `PATCH /v1/context/collections/by-name/{collection_name}/vectors/{vector_name}` (`runtime_context_configure_vector`) | `0.4.0` | `none` | `none` | No |
| `project.context.count()` | `POST /v1/context/count` (`runtime_context_count`) | `0.2.0` | `read_only_post` | `none` | No |
| `project.context.create_collection()` | `POST /v1/context/collections` (`runtime_context_create_collection`) | `0.2.0` | `idempotent_mutation` | `none` | No |
| `project.context.create_collection_alias()` | `POST /v1/context/aliases` (`runtime_context_create_collection_alias`) | `0.4.0` | `none` | `none` | No |
| `project.context.create_embedding_migration()` | `POST /v1/context/collections/by-name/{collection_name}/embedding-migrations` (`runtime_context_create_embedding_migration`) | `0.4.0` | `none` | `none` | No |
| `project.context.delete_collection()` | `DELETE /v1/context/collections/{collection_id}` (`runtime_context_delete_collection`) | `0.2.0` | `idempotent_mutation` | `none` | No |
| `project.context.delete_payload()` | `POST /v1/context/points/payload/delete` (`runtime_context_delete_payload`) | `0.4.0` | `none` | `none` | No |
| `project.context.delete_points()` | `POST /v1/context/collections/{collection_id}/points/delete` (`runtime_context_delete_points`) | `0.2.0` | `idempotent_mutation` | `none` | No |
| `project.context.discover()` | `POST /v1/context/search/discover` (`runtime_context_discover_points`) | `0.4.0` | `none` | `none` | No |
| `project.context.discover_sources()` | `POST /v1/context/discover` (`runtime_context_discover`) | `0.2.0` | `read_only_post` | `none` | No |
| `project.context.dismiss_onboarding()` | `POST /v1/context/onboarding/dismiss` (`runtime_context_dismiss_onboarding`) | `0.2.0` | `idempotent_mutation` | `none` | No |
| `project.context.drop_collection()` | `DELETE /v1/context/collections/{collection_id}` (`runtime_context_delete_collection`) | `0.4.0` | `idempotent_mutation` | `none` | No |
| `project.context.drop_collection_alias()` | `DELETE /v1/context/aliases/{alias_name}` (`runtime_context_drop_collection_alias`) | `0.4.0` | `none` | `none` | No |
| `project.context.embedding_migrations()` | `GET /v1/context/collections/by-name/{collection_name}/embedding-migrations` (`runtime_context_embedding_migrations`) | `0.4.0` | `read_only_get` | `none` | No |
| `project.context.estimate_index_memory()` | `GET /v1/context/collections/by-name/{collection_name}/indexes/{index_name}/memory-estimate` (`runtime_context_estimate_index_memory`) | `0.4.0` | `read_only_get` | `none` | No |
| `project.context.evaluate_onboarding()` | `POST /v1/context/onboarding/evaluate` (`runtime_context_evaluate_onboarding`) | `0.2.0` | `read_only_post` | `none` | No |
| `project.context.execute_query()` | `POST /v1/context/query/execute` (`runtime_context_execute_query`) | `0.4.0` | `none` | `none` | No |
| `project.context.explain()` | `POST /v1/context/query/explain` (`runtime_context_explain_query`) | `0.4.0` | `none` | `none` | No |
| `project.context.explore()` | `POST /v1/context/explore` (`runtime_context_explore`) | `0.4.0` | `none` | `none` | No |
| `project.context.facet()` | `POST /v1/context/facets` (`runtime_context_facets`) | `0.4.0` | `read_only_post` | `none` | No |
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
| `project.context.index_advisor()` | `GET /v1/context/collections/by-name/{collection_name}/index-advisor` (`runtime_context_index_advisor`) | `0.4.0` | `read_only_get` | `none` | No |
| `project.context.index_diagnostics()` | `GET /v1/context/collections/by-name/{collection_name}/indexes/{index_name}/diagnostics` (`runtime_context_index_diagnostics`) | `0.4.0` | `read_only_get` | `none` | No |
| `project.context.index_status()` | `GET /v1/context/collections/by-name/{collection_name}/indexes/{index_name}/status` (`runtime_context_index_status`) | `0.4.0` | `read_only_get` | `none` | No |
| `project.context.joint()` | `POST /v1/context/hybrid/joint` (`runtime_context_joint`) | `0.2.0` | `none` | `none` | No |
| `project.context.list_collections()` | `GET /v1/context/collections` (`runtime_context_list_collections`) | `0.2.0` | `read_only_get` | `auto_cursor` | No |
| `project.context.list_filters()` | `GET /v1/context/collections/{collection_id}/filters` (`runtime_context_list_filters`) | `0.2.0` | `read_only_get` | `none` | No |
| `project.context.list_operations()` | `GET /v1/context/operations` (`runtime_context_list_operations`) | `0.2.0` | `read_only_get` | `auto_cursor` | No |
| `project.context.model_versions()` | `GET /v1/context/collections/by-name/{collection_name}/model-versions` (`runtime_context_model_versions`) | `0.4.0` | `read_only_get` | `none` | No |
| `project.context.optimization_status()` | `GET /v1/context/collections/by-name/{collection_name}/optimization-status` (`runtime_context_optimization_status`) | `0.4.0` | `read_only_get` | `none` | No |
| `project.context.preflight()` | `POST /v1/context/preflight` (`runtime_context_preflight`) | `0.2.0` | `read_only_post` | `none` | No |
| `project.context.query()` | `POST /v1/context/hybrid/text` (`runtime_context_text_hybrid`) | `0.4.0` | `none` | `none` | No |
| `project.context.query_cohort_stats()` | `GET /v1/context/collections/by-name/{collection_name}/query-cohort-stats` (`runtime_context_query_cohort_stats`) | `0.4.0` | `read_only_get` | `none` | No |
| `project.context.query_discover()` |  | `0.4.0` | `none` | `none` | No |
| `project.context.query_execution_stats()` | `GET /v1/context/collections/by-name/{collection_name}/query-execution-stats` (`runtime_context_query_execution_stats`) | `0.4.0` | `read_only_get` | `none` | No |
| `project.context.query_formula()` |  | `0.4.0` | `none` | `none` | No |
| `project.context.query_full_text()` |  | `0.4.0` | `none` | `none` | No |
| `project.context.query_late_interaction()` |  | `0.4.0` | `none` | `none` | No |
| `project.context.query_lookup()` |  | `0.4.0` | `none` | `none` | No |
| `project.context.query_nearest()` |  | `0.4.0` | `none` | `none` | No |
| `project.context.query_prefetch()` |  | `0.4.0` | `none` | `none` | No |
| `project.context.query_recommend()` |  | `0.4.0` | `none` | `none` | No |
| `project.context.query_rerank()` |  | `0.4.0` | `none` | `none` | No |
| `project.context.query_score_threshold()` |  | `0.4.0` | `none` | `none` | No |
| `project.context.query_sparse_nearest()` |  | `0.4.0` | `none` | `none` | No |
| `project.context.query_weight()` |  | `0.4.0` | `none` | `none` | No |
| `project.context.rank_fusion()` | `POST /v1/context/hybrid/rank-fusion` (`runtime_context_rank_fusion`) | `0.2.0` | `none` | `none` | No |
| `project.context.raw_vector_search()` | `POST /v1/context/search/raw` (`runtime_context_raw_vector_search`) | `0.4.0` | `none` | `none` | No |
| `project.context.recall_check()` | `POST /v1/context/recall-check` (`runtime_context_recall_check`) | `0.2.0` | `none` | `none` | No |
| `project.context.recommend()` | `POST /v1/context/recommend` (`runtime_context_recommend`) | `0.4.0` | `none` | `none` | No |
| `project.context.reconcile_points()` | `POST /v1/context/collections/{collection_id}/points/reconcile` (`runtime_context_reconcile_points`) | `0.2.0` | `idempotent_mutation` | `none` | No |
| `project.context.refresh_onboarding()` | `POST /v1/context/onboarding/refresh` (`runtime_context_refresh_onboarding`) | `0.2.0` | `read_only_post` | `none` | No |
| `project.context.register_filter_column()` | `POST /v1/context/collections/{collection_id}/filters/columns` (`runtime_context_add_filter_column`) | `0.4.0` | `idempotent_mutation` | `none` | No |
| `project.context.register_jsonb_path()` | `POST /v1/context/collections/{collection_id}/filters/jsonb-paths` (`runtime_context_add_filter_jsonb_path`) | `0.4.0` | `idempotent_mutation` | `none` | No |
| `project.context.register_model_version()` | `POST /v1/context/collections/by-name/{collection_name}/model-versions` (`runtime_context_register_model_version`) | `0.4.0` | `none` | `none` | No |
| `project.context.register_vector()` | `POST /v1/context/collections/{collection_id}/vectors` (`runtime_context_add_vector`) | `0.4.0` | `idempotent_mutation` | `none` | No |
| `project.context.reindex_collection()` | `POST /v1/context/collections/{collection_id}/reindex` (`runtime_context_reindex_collection`) | `0.2.0` | `idempotent_mutation` | `none` | No |
| `project.context.retry_operation()` | `POST /v1/context/operations/{operation_id}/retry` (`runtime_context_retry_operation`) | `0.2.0` | `idempotent_mutation` | `none` | No |
| `project.context.scroll()` | `GET /v1/context/collections/{collection_id}/points` (`runtime_context_scroll_points`) | `0.4.0` | `read_only_get` | `auto_cursor` | No |
| `project.context.scroll_points()` | `GET /v1/context/collections/{collection_id}/points` (`runtime_context_scroll_points`) | `0.2.0` | `read_only_get` | `auto_cursor` | No |
| `project.context.search()` | `POST /v1/context/search` (`runtime_context_search`) | `0.2.0` | `none` | `none` | No |
| `project.context.set_default_collection()` | `PATCH /v1/context/collections/{collection_id}` (`runtime_context_update_collection`) | `0.2.0` | `idempotent_mutation` | `none` | No |
| `project.context.set_payload()` | `PUT /v1/context/points/payload` (`runtime_context_set_payload`) | `0.4.0` | `none` | `none` | No |
| `project.context.telemetry()` | `GET /v1/context/collections/by-name/{collection_name}/telemetry` (`runtime_context_telemetry`) | `0.4.0` | `read_only_get` | `none` | No |
| `project.context.text_hybrid()` | `POST /v1/context/hybrid/text` (`runtime_context_text_hybrid`) | `0.2.0` | `none` | `none` | No |
| `project.context.update_collection()` | `PATCH /v1/context/collections/{collection_id}` (`runtime_context_update_collection`) | `0.2.0` | `idempotent_mutation` | `none` | No |
| `project.context.update_embedding_migration()` | `PATCH /v1/context/collections/by-name/{collection_name}/embedding-migrations/{migration_id}` (`runtime_context_update_embedding_migration`) | `0.4.0` | `none` | `none` | No |
| `project.context.upsert_points()` | `POST /v1/context/collections/{collection_id}/points/upsert` (`runtime_context_upsert_points`) | `0.2.0` | `idempotent_mutation` | `none` | No |
| `project.context.vacuum_advice()` | `GET /v1/context/collections/by-name/{collection_name}/indexes/{index_name}/vacuum-advice` (`runtime_context_vacuum_advice`) | `0.4.0` | `read_only_get` | `none` | No |
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

### `project.context.add_vector()`

Add a vector to a Context collection.

```python
operation = project.context.add_vector(collection_id, "embedding_v2", 768)
```

### `project.context.backfill_points()`

Backfill point mappings from the source table.

```python
result = project.context.backfill_points("support")
```

### `project.context.bulk_delete_points()`

Delete point mappings in bounded pgContext batches.

```python
result = project.context.bulk_delete_points("support", ["row-1"])
```

### `project.context.bulk_upsert_points()`

Upsert point mappings in bounded pgContext batches.

```python
result = project.context.bulk_upsert_points("support", ["row-1"])
```

### `project.context.cancel_operation()`

Request cancellation of a durable Context operation.

```python
operation = project.context.cancel_operation(operation_id)
```

### `project.context.candidate_search()`

Search within explicit candidate point IDs.

```python
result = project.context.candidate_search("support", embedding, [1, 2])
```

### `project.context.clear_payload()`

Clear all registered payload fields.

```python
result = project.context.clear_payload("support", ["row-1"])
```

### `project.context.collection_aliases()`

List visible pgContext collection aliases.

```python
aliases = project.context.collection_aliases()
```

### `project.context.collection_info()`

Return exact pgContext collection metadata by name.

```python
info = project.context.collection_info("support")
```

### `project.context.collection_limits()`

Return strict-mode limits for a pgContext collection.

```python
limits = project.context.collection_limits("support")
```

### `project.context.collection_vectors()`

List registered dense vectors for a pgContext collection.

```python
vectors = project.context.collection_vectors("support")
```

### `project.context.configure_collection_limits()`

Configure strict-mode limits for a pgContext collection.

```python
limits = project.context.configure_collection_limits("support", strict_mode=True)
```

### `project.context.configure_vector()`

Configure dense-vector metadata for a pgContext collection.

```python
vector = project.context.configure_vector("support", "embedding", hnsw_options={}, quantization_options={}, status="ready")
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

### `project.context.create_collection_alias()`

Create or retarget a pgContext collection alias.

```python
alias = project.context.create_collection_alias("support", "support_v2")
```

### `project.context.create_embedding_migration()`

Create a collection embedding migration.

```python
migration = project.context.create_embedding_migration("support", "embed", "1", "embed", "2", 100)
```

### `project.context.delete_collection()`

Start deletion of a confirmed Context collection.

```python
operation = project.context.delete_collection(collection_id, confirm_collection_id=collection_id)
```

### `project.context.delete_payload()`

Delete selected registered payload fields.

```python
result = project.context.delete_payload("support", ["row-1"], ["locale"])
```

### `project.context.delete_points()`

Delete selected source rows from Context points.

```python
result = project.context.delete_points(collection_id, ["row-1"])
```

### `project.context.discover()`

Discover points from context point IDs.

```python
result = project.context.discover("support", [1, 2])
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

### `project.context.drop_collection()`

Drop a confirmed pgContext collection.

```python
operation = project.context.drop_collection(collection_id, confirm_collection_id=collection_id)
```

### `project.context.drop_collection_alias()`

Drop a pgContext collection alias.

```python
result = project.context.drop_collection_alias("support")
```

### `project.context.embedding_migrations()`

List embedding migrations for a collection.

```python
migrations = project.context.embedding_migrations("support")
```

### `project.context.estimate_index_memory()`

Estimate collection index memory.

```python
estimate = project.context.estimate_index_memory("support", "support_embedding_idx")
```

### `project.context.evaluate_onboarding()`

Evaluate and cache pgvector bridge eligibility.

```python
onboarding = project.context.evaluate_onboarding()
```

### `project.context.execute_query()`

Execute a validated pgContext query plan.

```python
results = project.context.execute_query("support", plan)
```

### `project.context.explain()`

Explain the stable dense plus full-text pgContext query.

```python
explanation = project.context.explain("support", "content")
```

### `project.context.explore()`

Explore points from context point IDs.

```python
result = project.context.explore("support", [1, 2])
```

### `project.context.facet()`

Return facet counts for one registered pgContext field.

```python
facets = project.context.facet("support", "tenant_id")
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

Context retrieval methods fetch this response lazily on their first call and
cache it on the project Context namespace. They validate the requested mode,
dimensions, result and candidate limits, graph depth, and relationship-type
count before sending the retrieval request. Calling `get_capabilities()`
explicitly refreshes the cache. Cached capabilities expire after 60 seconds,
and an unavailable capability is refreshed on the next attempted call.

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

### `project.context.index_advisor()`

Return collection filter-index recommendations.

```python
advice = project.context.index_advisor("support")
```

### `project.context.index_diagnostics()`

Return collection-scoped index diagnostics.

```python
status = project.context.index_diagnostics("support", "support_embedding_idx")
```

### `project.context.index_status()`

Return collection-scoped index lifecycle status.

```python
status = project.context.index_status("support", "support_embedding_idx")
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

### `project.context.model_versions()`

List embedding model versions for a collection.

```python
models = project.context.model_versions("support")
```

### `project.context.optimization_status()`

Return collection optimization readiness.

```python
status = project.context.optimization_status("support")
```

### `project.context.preflight()`

Validate a proposed Context collection without creating it.

```python
report = project.context.preflight("support", source=source, vector=vector)
```

### `project.context.query()`

Run the stable pgContext dense plus full-text query.

```python
results = project.context.query("support", embedding, query="refund")
```

### `project.context.query_cohort_stats()`

Return collection-scoped query cohort statistics.

```python
stats = project.context.query_cohort_stats("support")
```

### `project.context.query_discover()`

Build a contextual discovery query plan.

```python
plan = project.context.query_discover([1, 2], limit=20)
```

### `project.context.query_execution_stats()`

Return collection-scoped query execution statistics.

```python
stats = project.context.query_execution_stats("support")
```

### `project.context.query_formula()`

Apply a pgContext score formula to one query-plan branch.

```python
scored = project.context.query_formula(dense, "score")
```

### `project.context.query_full_text()`

Build a PostgreSQL full-text query plan.

```python
plan = project.context.query_full_text("refund", "content", limit=20)
```

### `project.context.query_late_interaction()`

Build a late-interaction query plan.

```python
plan = project.context.query_late_interaction(query_vectors, 50, limit=20)
```

### `project.context.query_lookup()`

Build a point lookup query plan.

```python
plan = project.context.query_lookup([1, 2])
```

### `project.context.query_nearest()`

Build a dense nearest query plan.

```python
plan = project.context.query_nearest(embedding, limit=20)
```

### `project.context.query_prefetch()`

Build a query plan that prefetches multiple branches.

```python
plan = project.context.query_prefetch([dense, lexical])
```

### `project.context.query_recommend()`

Build a point recommendation query plan.

```python
plan = project.context.query_recommend([1], [], limit=20)
```

### `project.context.query_rerank()`

Rerank one query-plan branch.

```python
plan = project.context.query_rerank(prefetched, 20)
```

### `project.context.query_score_threshold()`

Apply score bounds to one query-plan branch.

```python
bounded = project.context.query_score_threshold(dense, None, 0.4)
```

### `project.context.query_sparse_nearest()`

Build a named sparse nearest query plan.

```python
plan = project.context.query_sparse_nearest("terms", sparse_vector, limit=20)
```

### `project.context.query_weight()`

Weight one query-plan branch.

```python
weighted = project.context.query_weight(dense, 0.7)
```

### `project.context.rank_fusion()`

Fuse Context and graph rankings.

```python
results = project.context.rank_fusion("support", embedding, start=start)
```

### `project.context.raw_vector_search()`

Search an explicit array of dense vectors.

```python
results = project.context.raw_vector_search(query, [1], [vector], "cosine")
```

### `project.context.recall_check()`

Measure approximate-search recall for a Context collection.

```python
report = project.context.recall_check("support", embedding)
```

### `project.context.recommend()`

Recommend points from positive and negative examples.

```python
result = project.context.recommend("support", positive_point_ids=[1])
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

### `project.context.register_filter_column()`

Register a scalar filter column on a pgContext collection.

```python
operation = project.context.register_filter_column(collection_id, "tenant", "tenant_id")
```

### `project.context.register_jsonb_path()`

Register a JSONB filter path on a pgContext collection.

```python
operation = project.context.register_jsonb_path(collection_id, "topic", "metadata", ["topic"])
```

### `project.context.register_model_version()`

Register an embedding model version.

```python
model = project.context.register_model_version("support", "embed", "2", 1536, "cosine")
```

### `project.context.register_vector()`

Register a named vector on a pgContext collection.

```python
operation = project.context.register_vector(collection_id, "embedding_v2", 768)
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

### `project.context.scroll()`

Scroll pgContext point mappings with cursor pagination.

```python
page = project.context.scroll(collection_id)
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

### `project.context.set_payload()`

Set registered payload fields for source rows.

```python
result = project.context.set_payload("support", ["row-1"], {"locale": "en"})
```

### `project.context.telemetry()`

Return collection-scoped telemetry rollups.

```python
telemetry = project.context.telemetry("support")
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

### `project.context.update_embedding_migration()`

Update collection embedding migration progress.

```python
migration = project.context.update_embedding_migration("support", 1, 50, "running")
```

### `project.context.upsert_points()`

Upsert selected source rows into Context points.

```python
result = project.context.upsert_points(collection_id, ["row-1"])
```

### `project.context.vacuum_advice()`

Return collection index vacuum advice.

```python
advice = project.context.vacuum_advice("support", "support_embedding_idx")
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

## `project.rows`

| SDK method | HTTP operation | Since | Retry | Pagination | Deprecated |
| --- | --- | --- | --- | --- | --- |
| `project.rows.ignore()` | `POST /v1/tables/{schema_name}/{table_name}/rows` (`runtime_write_row`) | `0.3.0` | `none` | `none` | No |
| `project.rows.insert()` | `POST /v1/tables/{schema_name}/{table_name}/rows` (`runtime_write_row`) | `0.3.0` | `none` | `none` | No |
| `project.rows.upsert()` | `POST /v1/tables/{schema_name}/{table_name}/rows` (`runtime_write_row`) | `0.3.0` | `none` | `none` | No |
| `project.rows.validate()` | `POST /v1/tables/{schema_name}/{table_name}/rows/validate` (`runtime_validate_row_write`) | `0.3.0` | `read_only_post` | `none` | No |

### `project.rows.ignore()`

Insert one row and ignore a matching primary or unique conflict.

```python
result = project.rows.ignore(schema="public", table="events", row={"id": "1"}, conflict_columns=["id"])
```

### `project.rows.insert()`

Insert one row into an eligible project-owned table.

```python
result = project.rows.insert(schema="public", table="events", row={"id": "1"})
```

### `project.rows.upsert()`

Upsert one row through a primary or unique constraint.

```python
result = project.rows.upsert(schema="public", table="events", row={"id": "1"}, conflict_columns=["id"])
```

### `project.rows.validate()`

Validate a single-row write without executing it.

```python
validation = project.rows.validate(schema="public", table="events", row={"id": "1"})
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
