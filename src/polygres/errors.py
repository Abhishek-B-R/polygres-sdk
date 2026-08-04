from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from polygres._vendor.polygres_lib.auth import AUTH_ERROR_CATALOG, AuthErrorCode
from polygres._vendor.polygres_lib.context import (
    CONTEXT_ERROR_CATALOG,
    ContextErrorCode,
)


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


@dataclass(frozen=True, slots=True)
class _CanonicalErrorDetails:
    code: str
    message: str
    status_code: int | None
    details: dict[str, Any]


def canonical_error_details(
    code: object, details: dict[str, Any]
) -> _CanonicalErrorDetails | None:
    """Adapt central safe error descriptors to the stable SDK exception hierarchy."""
    if not isinstance(code, str):
        return None
    try:
        auth_code = AuthErrorCode(code)
    except ValueError:
        pass
    else:
        descriptor = AUTH_ERROR_CATALOG[auth_code]
        return _CanonicalErrorDetails(
            code=descriptor.code.value,
            message=descriptor.safe_message,
            status_code=descriptor.http_status,
            details={
                key: value
                for key, value in details.items()
                if key in descriptor.safe_detail_keys
            },
        )
    try:
        context_code = ContextErrorCode(code)
    except ValueError:
        return None
    context_descriptor = CONTEXT_ERROR_CATALOG[context_code]
    return _CanonicalErrorDetails(
        code=context_code.value,
        message=context_descriptor.message,
        status_code=context_descriptor.status_code,
        details={
            key: value
            for key, value in details.items()
            if key in context_descriptor.safe_detail_fields
        },
    )
