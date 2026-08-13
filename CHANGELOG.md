# Changelog

All notable changes to `polygres-sdk` are documented in this file.

## Unreleased

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
