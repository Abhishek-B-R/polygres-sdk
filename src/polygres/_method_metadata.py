"""Non-routing metadata attached to hand-written SDK methods."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any, Literal, TypeVar

BindingKind = Literal["operation", "composite", "local"]
Stability = Literal["stable", "experimental"]
RetryPolicy = Literal[
    "none",
    "read_only_get",
    "read_only_post",
    "idempotent_mutation",
    "polling",
]
Pagination = Literal["none", "cursor", "auto_cursor"]


@dataclass(frozen=True, slots=True)
class SdkMethodBinding:
    """Descriptive binding metadata for one public SDK method."""

    public_name: str
    operation_ids: tuple[str, ...]
    since: str
    stability: Stability
    retry_policy: RetryPolicy
    pagination: Pagination
    binding_kind: BindingKind = "operation"
    deprecated: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible metadata."""

        value = asdict(self)
        value["operation_ids"] = list(self.operation_ids)
        return value


FunctionT = TypeVar("FunctionT", bound=Callable[..., Any])


def sdk_method(
    *,
    public_name: str,
    operation_ids: tuple[str, ...],
    since: str,
    stability: Stability = "stable",
    retry_policy: RetryPolicy,
    pagination: Pagination = "none",
    binding_kind: BindingKind = "operation",
    deprecated: str | None = None,
) -> Callable[[FunctionT], FunctionT]:
    """Attach method-spec metadata without wrapping or registering a function."""

    metadata = SdkMethodBinding(
        public_name=public_name,
        operation_ids=operation_ids,
        since=since,
        stability=stability,
        retry_policy=retry_policy,
        pagination=pagination,
        binding_kind=binding_kind,
        deprecated=deprecated,
    )

    def decorate(function: FunctionT) -> FunctionT:
        function.__polygres_sdk_method__ = metadata  # type: ignore[attr-defined]
        return function

    return decorate


def get_sdk_method_binding(function: Callable[..., Any]) -> SdkMethodBinding | None:
    """Read binding metadata from a public method."""

    metadata = getattr(function, "__polygres_sdk_method__", None)
    return metadata if isinstance(metadata, SdkMethodBinding) else None


def bind_sdk_method(
    function: FunctionT,
    *,
    description: str,
    example: str,
    public_name: str,
    operation_ids: tuple[str, ...],
    since: str,
    stability: Stability = "stable",
    retry_policy: RetryPolicy,
    pagination: Pagination = "none",
    binding_kind: BindingKind = "operation",
    deprecated: str | None = None,
) -> FunctionT:
    """Attach a concise public docstring and non-wrapping method metadata."""

    function.__doc__ = f"{description}\n\nExample:\n    {example}"
    return sdk_method(
        public_name=public_name,
        operation_ids=operation_ids,
        since=since,
        stability=stability,
        retry_policy=retry_policy,
        pagination=pagination,
        binding_kind=binding_kind,
        deprecated=deprecated,
    )(function)


__all__ = ["SdkMethodBinding", "bind_sdk_method", "get_sdk_method_binding", "sdk_method"]
