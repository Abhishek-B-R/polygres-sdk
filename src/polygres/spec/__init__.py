"""Packaged machine-readable Polygres SDK contracts."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any


def load_runtime_openapi() -> dict[str, Any]:
    """Load the descriptive Runtime v1 OpenAPI snapshot."""

    return _load_json("runtime-v1.openapi.json")


def load_python_method_spec() -> dict[str, Any]:
    """Load the descriptive Python SDK v1 method specification."""

    return _load_json("python-sdk-v1.methods.json")


def load_python_method_schema() -> dict[str, Any]:
    """Load the JSON Schema for the Python SDK method specification."""

    return _load_json("python-sdk-v1.methods.schema.json")


def _load_json(name: str) -> dict[str, Any]:
    value = json.loads(files(__package__).joinpath(name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Packaged SDK contract is not a JSON object: {name}")
    return value


__all__ = [
    "load_python_method_schema",
    "load_python_method_spec",
    "load_runtime_openapi",
]
