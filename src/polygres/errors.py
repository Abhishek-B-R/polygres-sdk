from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from polygres._vendor.polygres_lib.errors import ERROR_CATALOG


class PolygresError(Exception):
    """Base Polygres SDK exception."""


class PolygresValidationError(PolygresError, ValueError):
    """Raised before a request is sent when local validation fails."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        request_id: str | None = None,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.request_id = request_id
        self.code = code
        self.details = details or {}


class PolygresAPIError(PolygresError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        request_id: str | None = None,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.request_id = request_id
        self.code = code
        self.details = details or {}


class PolygresProjectArchivedError(PolygresAPIError):
    """Project access is blocked while archiving, archived, or restoring.

    Inspect ``details["archive_state"]`` for the lifecycle state. Requests are
    not automatically retried and restoration is always an explicit action.
    """


class PolygresAuthError(PolygresAPIError):
    """Raised for authentication failures."""


class PolygresPermissionError(PolygresAPIError):
    """Raised for authorization failures."""


class PolygresNotFoundError(PolygresAPIError):
    """Raised when a requested resource is not found."""


class PolygresRateLimitError(PolygresAPIError):
    """Raised when the API rate limits a request."""


class PolygresMaintenanceError(PolygresAPIError):
    """Raised when Polygres is in read-only or full maintenance."""


class PolygresRuntimeError(PolygresAPIError):
    """Raised for transient API/runtime failures."""


class PolygresAmbiguousWriteError(PolygresRuntimeError):
    """Raised when a row mutation may have committed but acknowledgement was lost."""


def synced_project_surface_unavailable_error() -> PolygresPermissionError:
    """Return the catalog-owned error used by local synced-mode guards.

    Runtime remains the authorization authority. This helper lets a caller that
    already has the authoritative ``project_mode`` fail before constructing a
    legacy request, with the exact exception and message it would receive from
    the Runtime boundary.
    """
    descriptor = ERROR_CATALOG["SYNCED_PROJECT_SURFACE_UNAVAILABLE"]
    return PolygresPermissionError(
        descriptor.message,
        status_code=descriptor.http_status,
        code=descriptor.code,
        details={},
    )


@dataclass(frozen=True, slots=True)
class _CanonicalErrorDetails:
    code: str
    message: str
    status_code: int | None
    details: dict[str, Any]


def canonical_error_details(
    code: object, variant: object, details: dict[str, Any]
) -> _CanonicalErrorDetails | None:
    """Adapt central safe error descriptors to the stable SDK exception hierarchy."""
    if not isinstance(code, str):
        return None
    descriptor = ERROR_CATALOG.get(code)
    if descriptor is None:
        return None
    selected_variant = descriptor.variants.get(variant) if isinstance(variant, str) else None
    return _CanonicalErrorDetails(
        code=code,
        message=selected_variant.message if selected_variant is not None else descriptor.message,
        status_code=(
            selected_variant.http_status if selected_variant is not None else descriptor.http_status
        ),
        details={
            key: value for key, value in details.items() if key in descriptor.safe_detail_fields
        },
    )
