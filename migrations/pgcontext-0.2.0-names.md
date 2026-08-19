# pgContext 0.2.0-aligned SDK names

**Introduced:** SDK 0.4.0

**Affected users:** Applications using `project.context`

SDK 0.4.0 adds names aligned with the stable pgContext 0.2.0 SQL API. This is
an additive naming migration. SDK 0.3.0 names remain callable, produce the same
HTTP requests and public results, and do not emit deprecation warnings.

This release covers the full stable pgContext 0.2.0 inventory through explicit
aligned, managed, safely partial, SQL-only, or deferred classifications. The
pinned inventory records 38 aligned signatures, 20 managed equivalents, 15
safely scoped partial signatures, 25 SQL-only contracts, and 5 privileged
functions deferred to direct SQL. No stable signature remains marked as a
missing SDK method.

| Preferred SDK 0.4.0 name | SDK 0.3.0-compatible name |
| --- | --- |
| `register_vector()` | `add_vector()` |
| `register_filter_column()` | `add_filter_column()` |
| `register_jsonb_path()` | `add_jsonb_filter_path()` |
| `drop_collection()` | `delete_collection()` |
| `facet()` | `facets()` |
| `query()` | `text_hybrid()` |
| `scroll()` | `scroll_points()` |

Existing code requires no change:

```python
project.context.add_vector(collection_id, "embedding", 768)
facets = project.context.facets("support", "tenant_id")
results = project.context.text_hybrid(
    "support",
    embedding,
    query="refund policy",
)
```

New code should use pgContext terminology:

```python
project.context.register_vector(collection_id, "embedding", 768)
facets = project.context.facet("support", "tenant_id")
results = project.context.query(
    "support",
    embedding,
    query="refund policy",
)
```

`drop_collection()` retains Polygres's explicit UUID confirmation requirement.
`query()` uses the collection's configured text column. These are deliberate
managed safety and configuration differences from direct pgContext SQL.

Index diagnostics, telemetry, query statistics, model-version listings, and
embedding-migration listings require a collection name in the SDK. This
prevents database-wide or cross-collection inspection. Backend-local HNSW
counters, manual query-stat writes, and database-wide telemetry queue health
remain direct-SQL surfaces pending a privileged monitoring authorization
model.

The candidate-point and explicit-array SQL overloads of `pgcontext.search`
are exposed as `candidate_search()` and `raw_vector_search()`. Keeping distinct
Python names preserves the exact SDK 0.3.0 `search()` callable signature while
making both overload families available.

The machine-checked inventory is
`packages/polygres-lib/contracts/context/pgcontext-0.2.0-compatibility.json`.
Its source is pinned to pgContext `v0.2.0` commit
`7d0818ed222e16ef5c74932981d759caf2818d82`.
