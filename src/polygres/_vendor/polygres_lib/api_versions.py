"""Dependency-free Runtime API behavior-version contract."""

from __future__ import annotations

import re
from dataclasses import dataclass

API_VERSION_HEADER = "X-Polygres-Api-Version"
CLIENT_INFO_HEADER = "X-Polygres-Client-Info"
DEFAULT_API_VERSION = "2026-08-04"
API_FAMILY = "v1"

_API_VERSION_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True, slots=True)
class ApiBehaviorVersion:
    """A supported Runtime API behavior version."""

    value: str


API_VERSIONS = {
    DEFAULT_API_VERSION: ApiBehaviorVersion(DEFAULT_API_VERSION),
}
SUPPORTED_API_VERSIONS = tuple(sorted(API_VERSIONS))


def is_api_version_syntax(value: str) -> bool:
    """Return whether a value uses the public date-version syntax."""

    return _API_VERSION_RE.fullmatch(value) is not None


def is_supported_api_version(value: str) -> bool:
    """Return whether a value is present in the supported registry."""

    return value in API_VERSIONS


__all__ = [
    "API_FAMILY",
    "API_VERSION_HEADER",
    "API_VERSIONS",
    "CLIENT_INFO_HEADER",
    "DEFAULT_API_VERSION",
    "SUPPORTED_API_VERSIONS",
    "ApiBehaviorVersion",
    "is_api_version_syntax",
    "is_supported_api_version",
]
