# Changelog

All notable changes to `polygres-sdk` are documented in this file.

## Unreleased

## 0.5.0 - 2026-09-12

### Added

- Pass text to existing Context, vector, and hybrid searches to generate query
  embeddings with the configured model. Existing vector calls retain their
  arguments and response types.
- Build nearest query-plan branches with text and embed them during execution.
- Control query credit usage and reuse embedding attempts across retries and
  paginated results with idempotency keys.


### Changed

- Refresh the packaged Runtime API reference and validate compatibility against
  the published SDK 0.4.1 contract.
- Include the changelog in source distributions.

Existing SDK methods and query-vector workflows remain available. Configure
embedding generation through the dashboard, CLI, or MCP.

## 0.4.1 - 2026-08-25

### Changed

- Updated the bundled public error catalog so durable Context collection sync,
  timeout, connection, memory, storage, and index failures use their canonical
  messages, statuses, retry guidance, and safe recovery details.

### Compatibility

- Existing SDK methods, signatures, request behavior, and exception classes are
  unchanged from SDK 0.4.0.

## 0.4.0 - 2026-08-16

### Added

- Added pgContext 0.2.0-aligned names for vector and filter registration,
  collection deletion, point scrolling, facets, and dense plus full-text
  queries.
- Added a frozen SDK 0.3.0 method-contract baseline for compatibility checks.
- Added a pinned, CI-checked pgContext 0.2.0 compatibility inventory that
  records aligned, managed, safely partial, SQL-only, deferred privileged, and
  experimental items with no ambiguous missing stable signatures.
- Added typed collection aliases, limits, vector configuration, bulk points,
  payload mutation, candidate and raw-vector search, recommendation,
  discovery, exploration, query-plan builders and execution, index
  diagnostics, collection telemetry, query statistics, model versions, and
  embedding migrations.
- Added additive pgContext compatibility counts to Context capabilities.

### Compatibility

- Existing SDK 0.3.0 method names remain available with unchanged signatures,
  HTTP requests, response types, exceptions, idempotency, and retry behavior.
- Aligned names delegate silently to the existing SDK 0.3.0 implementations.
  Upgrading without changing application code does not select new behavior.

### Changed

- Added synchronized-project mode handling: `connection_info()` raises
  `PolygresPermissionError` with `SYNCED_PROJECT_SURFACE_UNAVAILABLE` while
  readiness, vector, hybrid, graph, text-search, and pgContext stay available.

## 0.3.0 - 2026-08-14

### Added

- Added `project.rows.validate()`, `insert()`, `upsert()`, and `ignore()` for
  single-row Runtime writes with typed results and stable validation errors.
- Added explicit pgContext reconciliation to row writes, including completed,
  pending, and partial-failure outcomes backed by durable operations.
- Added `PolygresAmbiguousWriteError` for write outcomes that cannot be proven.

### Changed

- Row mutations are sent exactly once. Automatic transport and status retries
  are disabled unless an exact Context-backed idempotency replay is requested.

## 0.2.1 - 2026-08-12

### Changed

- pgContext retrieval methods now check the project's supported operations and
  query limits before sending a request.
- Capability checks cover result and candidate limits, embedding dimensions,
  graph depth, and relationship-type limits while preserving existing method
  signatures.
- The bundled Runtime API contract now includes the completed text-search
  configuration and diagnostics operations.
- Release notices are now checked through the central Polygres API, so future
  SDK update notices no longer require project Runtime API restarts.

## 0.2.0 - 2026-08-09

### Added

- Added the `project.context` namespace for configuring, managing, and querying pgContext collections.
- Added `PolygresVersionWarning` for available SDK upgrades.
- Added `PolygresMaintenanceError` so applications can handle maintenance windows separately from other API failures.

### Changed

- The retired vector-configuration creation error is exposed as
  `PolygresValidationError` with pgContext replacement details.

### Fixed

- Improved validation and handling of vector result metrics.
- Vector queries now correctly handle identifiers using the source table's configured ID types.
- API errors now provide clearer recovery guidance.
- Restored Python 3.10 compatibility for retry timing and version-notice date parsing.

## 0.1.0 - 2026-07-09

### Added

- Initial standalone `polygres-sdk` package.
- Added Runtime API clients for graph, vector, text, and hybrid retrieval.
- Added typed results, cursor pagination, automatic page iteration, readiness checks, passwordless connection information, and structured API exceptions.
