# Changelog

All notable changes to `polygres-sdk` are documented in this file.

## 0.2.0 - 2026-08-06

### Added

- Added the `project.context` namespace for configuring, managing, and querying pgContext collections.
- Added `PolygresVersionWarning` for available SDK upgrades.
- Added `PolygresMaintenanceError` so applications can handle maintenance windows separately from other API failures.

### Fixed

- Improved validation and handling of vector result metrics.
- Vector queries now correctly handle identifiers using the source table's configured ID types.
- API errors now provide clearer recovery guidance.

## 0.1.0 - 2026-07-09

### Added

- Initial standalone `polygres-sdk` package.
- Added Runtime API clients for graph, vector, text, and hybrid retrieval.
- Added typed results, cursor pagination, automatic page iteration, readiness checks, passwordless connection information, and structured API exceptions.
