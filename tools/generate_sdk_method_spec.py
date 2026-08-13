#!/usr/bin/env python3
"""Generate and validate the Python SDK method contract and reference page."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import sys
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised by the Python 3.10 CI job
    import tomli as tomllib

SDK_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = SDK_ROOT.parents[1] if SDK_ROOT.parent.name == "packages" else SDK_ROOT
SOURCE_ROOT = SDK_ROOT / "src"
SPEC_ROOT = SOURCE_ROOT / "polygres" / "spec"
OPENAPI_PATH = SPEC_ROOT / "runtime-v1.openapi.json"
METHOD_SPEC_PATH = SPEC_ROOT / "python-sdk-v1.methods.json"
METHOD_SCHEMA_PATH = SPEC_ROOT / "python-sdk-v1.methods.schema.json"
EXCLUSIONS_PATH = SDK_ROOT / "tools" / "runtime_operation_exclusions.json"
REFERENCE_PATH = SDK_ROOT / "docs" / "reference-v1.md"
PYPROJECT_PATH = SDK_ROOT / "pyproject.toml"
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
EXCEPTION_CATEGORIES = [
    "api",
    "authentication",
    "maintenance",
    "not_found",
    "permission",
    "rate_limit",
    "runtime",
    "validation",
]
REFERENCE_NOTES = {
    "project.context.get_capabilities": (
        "Context retrieval methods fetch this response lazily on their first call and\n"
        "cache it on the project Context namespace. They validate the requested mode,\n"
        "dimensions, result and candidate limits, graph depth, and relationship-type\n"
        "count before sending the retrieval request. Calling `get_capabilities()`\n"
        "explicitly refreshes the cache. Cached capabilities expire after 60 seconds,\n"
        "and an unavailable capability is refreshed on the next attempted call."
    )
}


def build_method_spec() -> dict[str, Any]:
    """Join Python method metadata to the committed Runtime OpenAPI snapshot."""

    sys.path.insert(0, str(SOURCE_ROOT))
    from polygres._api_version import API_FAMILY, DEFAULT_API_VERSION
    from polygres._method_metadata import get_sdk_method_binding
    from polygres.client import (
        GraphNamespace,
        HybridNamespace,
        Project,
        TextNamespace,
        VectorNamespace,
    )
    from polygres.context import ContextNamespace

    openapi_bytes = OPENAPI_PATH.read_bytes()
    openapi = json.loads(openapi_bytes)
    operation_index = _operation_index(openapi)
    classes = (
        Project,
        GraphNamespace,
        VectorNamespace,
        TextNamespace,
        HybridNamespace,
        ContextNamespace,
    )
    methods: list[dict[str, Any]] = []
    uncovered: list[str] = []
    for class_type in classes:
        for name, function in inspect.getmembers(class_type, inspect.isfunction):
            if name.startswith("_"):
                continue
            metadata = get_sdk_method_binding(function)
            if metadata is None:
                uncovered.append(f"{function.__module__}.{function.__qualname__}")
                continue
            description, example = _documentation(function)
            methods.append(
                {
                    **metadata.to_dict(),
                    "python_qualname": f"{function.__module__}.{function.__qualname__}",
                    "operations": [
                        _operation_contract(operation_index, operation_id, openapi)
                        for operation_id in metadata.operation_ids
                    ],
                    "description": description,
                    "example": example,
                    "exception_categories": EXCEPTION_CATEGORIES,
                }
            )
    if uncovered:
        raise ValueError("Public network methods lack metadata: " + ", ".join(uncovered))

    exclusions = _resolved_exclusions(operation_index)
    document = {
        "schema_version": 1,
        "sdk": "polygres-sdk",
        "sdk_version": _project_version(),
        "api_family": API_FAMILY,
        "default_api_version": DEFAULT_API_VERSION,
        "openapi_sha256": hashlib.sha256(openapi_bytes).hexdigest(),
        "excluded_operations": exclusions,
        "methods": sorted(methods, key=lambda item: item["public_name"]),
    }
    validate_method_spec(document, openapi=openapi, classes=classes)
    return document


def validate_method_spec(
    document: dict[str, Any],
    *,
    openapi: dict[str, Any] | None = None,
    classes: tuple[type[Any], ...] | None = None,
    require_current_operation_details: bool = True,
) -> None:
    """Validate the JSON Schema and cross-artifact semantic contract."""

    schema = json.loads(METHOD_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.path))
    if errors:
        details = "; ".join(
            f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
            for error in errors
        )
        raise ValueError(f"Method specification failed JSON Schema validation: {details}")

    methods = document["methods"]
    _require_unique(methods, "public_name")
    _require_unique(methods, "python_qualname")
    exclusions = document["excluded_operations"]
    _require_unique(exclusions, "operation_id")
    for item in exclusions:
        review_date = date.fromisoformat(item["review_date"])
        if review_date < date.today():
            raise ValueError(
                f"Excluded operation review is overdue: {item['operation_id']} ({review_date})"
            )

    if openapi is None:
        openapi = json.loads(OPENAPI_PATH.read_text(encoding="utf-8"))
    operation_index = _operation_index(openapi)
    bound_ids: set[str] = set()
    for method in methods:
        if method["binding_kind"] == "operation" and len(method["operation_ids"]) != 1:
            raise ValueError(
                f"Ordinary method must bind exactly one operation: {method['public_name']}"
            )
        if method["binding_kind"] == "composite" and not method["operation_ids"]:
            raise ValueError(f"Composite method has no operations: {method['public_name']}")
        if method["stability"] == "stable" and (not method["description"] or not method["example"]):
            raise ValueError(f"Stable method lacks documentation: {method['public_name']}")
        if "POLYGRES_API_KEY" in method["example"] or "http" in method["example"]:
            raise ValueError(
                f"Generated method example contains a credential or URL: {method['public_name']}"
            )
        for operation in method["operations"]:
            operation_id = operation["operation_id"]
            if operation_id not in operation_index:
                raise ValueError(f"Unknown operation binding: {operation_id}")
            expected = _operation_contract(operation_index, operation_id, openapi)
            if require_current_operation_details and operation != expected:
                raise ValueError(f"Stale operation details for binding: {operation_id}")
            if not operation_id.startswith("runtime_"):
                raise ValueError(f"SDK operationId is not explicit and stable: {operation_id}")
            bound_ids.add(operation_id)

    excluded_ids = {item["operation_id"] for item in exclusions}
    overlap = bound_ids & excluded_ids
    if overlap:
        raise ValueError(f"Operations are both bound and excluded: {sorted(overlap)}")
    all_ids = set(operation_index)
    if (require_current_operation_details and bound_ids | excluded_ids != all_ids) or not (
        bound_ids | excluded_ids
    ).issubset(all_ids):
        missing = sorted(all_ids - bound_ids - excluded_ids)
        extra = sorted((bound_ids | excluded_ids) - all_ids)
        raise ValueError(f"Operation inventory mismatch; missing={missing}, extra={extra}")

    if classes is not None:
        python_methods = {
            f"{function.__module__}.{function.__qualname__}"
            for class_type in classes
            for name, function in inspect.getmembers(class_type, inspect.isfunction)
            if not name.startswith("_")
        }
        specified = {method["python_qualname"] for method in methods}
        if specified != python_methods:
            raise ValueError(
                "Python method inventory mismatch; "
                f"missing={sorted(python_methods - specified)}, "
                f"extra={sorted(specified - python_methods)}"
            )


def render_json(document: dict[str, Any]) -> str:
    return json.dumps(document, indent=2, sort_keys=True) + "\n"


def render_reference(document: dict[str, Any]) -> str:
    """Render human-readable v1 reference navigation from generated method data."""

    lines = [
        "# Polygres Python SDK v1 method reference",
        "",
        (
            "This file is generated. Edit Python method metadata, docstrings, or the "
            "Runtime OpenAPI contract instead."
        ),
        "",
        f"- SDK package version: `{document['sdk_version']}`",
        f"- HTTP API family: `{document['api_family']}`",
        f"- Default API behavior version: `{document['default_api_version']}`",
        f"- Method specification schema: `{document['schema_version']}`",
        "- Models and exceptions: [SDK README](../README.md)",
        "",
    ]
    namespaces: dict[str, list[dict[str, Any]]] = {}
    for method in document["methods"]:
        namespace = method["public_name"].rsplit(".", 1)[0]
        namespaces.setdefault(namespace, []).append(method)
    for namespace, methods in sorted(namespaces.items()):
        lines.extend(
            [
                f"## `{namespace}`",
                "",
                "| SDK method | HTTP operation | Since | Retry | Pagination | Deprecated |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for method in methods:
            operations = "<br>".join(
                f"`{operation['method']} {operation['path']}` (`{operation['operation_id']}`)"
                for operation in method["operations"]
            )
            deprecated = method["deprecated"] or "No"
            lines.append(
                f"| `{method['public_name']}()` | {operations} | `{method['since']}` | "
                f"`{method['retry_policy']}` | `{method['pagination']}` | {deprecated} |"
            )
        lines.append("")
        for method in methods:
            lines.extend(
                [
                    f"### `{method['public_name']}()`",
                    "",
                    method["description"],
                    "",
                    "```python",
                    method["example"],
                    "```",
                    "",
                ]
            )
            if note := REFERENCE_NOTES.get(method["public_name"]):
                lines.extend([note, ""])
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true", help="fail when generated files are stale")
    modes.add_argument(
        "--validate-only",
        action="store_true",
        help="validate the committed method JSON without writing files",
    )
    args = parser.parse_args(argv)

    if args.validate_only:
        document = json.loads(METHOD_SPEC_PATH.read_text(encoding="utf-8"))
        expected = build_method_spec()
        validate_method_spec(document)
        if document != expected:
            sys.stderr.write("Committed method specification is semantically stale.\n")
            return 1
        sys.stdout.write(f"Method specification is valid: {METHOD_SPEC_PATH}\n")
        return 0

    document = build_method_spec()
    outputs = {
        METHOD_SPEC_PATH: render_json(document),
        REFERENCE_PATH: render_reference(document),
    }
    if args.check:
        stale = [
            path
            for path, expected in outputs.items()
            if not path.exists() or path.read_text(encoding="utf-8") != expected
        ]
        if stale:
            sys.stderr.write(
                "Generated SDK method artifacts are stale: "
                + ", ".join(str(path) for path in stale)
                + "\n"
            )
            return 1
        sys.stdout.write("SDK method specification and reference are current.\n")
        return 0

    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        sys.stdout.write(f"Wrote generated SDK artifact: {path}\n")
    return 0


def _project_version() -> str:
    project = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))["project"]
    return str(project["version"])


def _operation_index(openapi: dict[str, Any]) -> dict[str, tuple[str, str, dict[str, Any]]]:
    operations: dict[str, tuple[str, str, dict[str, Any]]] = {}
    for path, path_item in openapi.get("paths", {}).items():
        for method, operation in path_item.items():
            if method not in HTTP_METHODS:
                continue
            operation_id = operation.get("operationId")
            if not isinstance(operation_id, str) or not operation_id:
                raise ValueError(f"OpenAPI operation has no operationId: {method.upper()} {path}")
            if operation_id in operations:
                raise ValueError(f"Duplicate OpenAPI operationId: {operation_id}")
            operations[operation_id] = (method.upper(), path, operation)
    return operations


def _operation_contract(
    operation_index: dict[str, tuple[str, str, dict[str, Any]]],
    operation_id: str,
    openapi: dict[str, Any],
) -> dict[str, Any]:
    try:
        method, path, operation = operation_index[operation_id]
    except KeyError as exc:
        raise ValueError(f"Method metadata references unknown operationId: {operation_id}") from exc
    request_body = operation.get("requestBody", {})
    if "$ref" in request_body:
        request_schema_value = request_body
    else:
        request_schema_value = (
            request_body.get("content", {}).get("application/json", {}).get("schema")
        )
    request_schema = _schema_identity(request_schema_value)
    request_contract = _schema_contracts(
        request_schema_value,
        openapi.get("components", {}).get("schemas", {}),
    )
    success_contracts: dict[str, list[dict[str, Any]]] = {}
    success_responses: dict[str, Any] = {}
    for status, response in sorted(operation.get("responses", {}).items()):
        if not str(status).startswith("2"):
            continue
        response_schema = response.get("content", {}).get("application/json", {}).get("schema")
        success_responses[str(status)] = _schema_identity(response_schema)
        success_contracts[str(status)] = _schema_contracts(
            response_schema,
            openapi.get("components", {}).get("schemas", {}),
        )
    if not success_responses:
        raise ValueError(f"SDK operation has no documented success response: {operation_id}")
    return {
        "operation_id": operation_id,
        "method": method,
        "path": path,
        "request_schema": request_schema,
        "request_contract": request_contract,
        "success_responses": success_responses,
        "success_contracts": success_contracts,
        "security": deepcopy(operation.get("security", [])),
        "deprecated": bool(operation.get("deprecated", False)),
    }


def _schema_identity(schema: Any) -> str | list[str] | None:
    if not isinstance(schema, dict):
        return None
    names = sorted(_schema_refs(schema))
    if len(names) == 1:
        return names[0]
    if names:
        return names
    title = schema.get("title")
    if isinstance(title, str) and title:
        return title
    schema_type = schema.get("type")
    return f"inline:{schema_type}" if isinstance(schema_type, str) else "inline"


def _schema_refs(value: Any) -> set[str]:
    names: set[str] = set()
    if isinstance(value, dict):
        ref = value.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
            names.add(ref.rsplit("/", 1)[1])
        for item in value.values():
            names.update(_schema_refs(item))
    elif isinstance(value, list):
        for item in value:
            names.update(_schema_refs(item))
    return names


def _schema_contracts(schema: Any, component_schemas: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(schema, dict):
        return []
    variants = schema.get("oneOf") or schema.get("anyOf")
    if isinstance(variants, list):
        contracts = [
            contract
            for variant in variants
            for contract in _schema_contracts(variant, component_schemas)
        ]
        return sorted(contracts, key=lambda item: item["schema"])
    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
        name = ref.rsplit("/", 1)[1]
        if name not in component_schemas:
            raise ValueError(f"Unknown component schema in method contract: {name}")
        return [_schema_contract(name, component_schemas[name])]
    name = schema.get("title") or _schema_identity(schema) or "inline"
    return [_schema_contract(str(name), schema)]


def _schema_contract(name: str, schema: dict[str, Any]) -> dict[str, Any]:
    properties = schema.get("properties", {})
    fields = sorted(properties) if isinstance(properties, dict) else []
    required = schema.get("required", [])
    required_fields = sorted(str(field) for field in required) if isinstance(required, list) else []
    return {
        "schema": name,
        "fields": fields,
        "required_fields": required_fields,
        "allows_additional_fields": schema.get("additionalProperties") is not False,
    }


def _resolved_exclusions(
    operation_index: dict[str, tuple[str, str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    source = json.loads(EXCLUSIONS_PATH.read_text(encoding="utf-8"))
    output = []
    for item in source:
        operation_id = item["operation_id"]
        try:
            method, path, _operation = operation_index[operation_id]
        except KeyError as exc:
            raise ValueError(f"Exclusion references unknown operationId: {operation_id}") from exc
        output.append({**item, "method": method, "path": path})
    return sorted(output, key=lambda item: item["operation_id"])


def _documentation(function: Any) -> tuple[str, str]:
    doc = inspect.getdoc(function) or ""
    paragraphs = doc.split("\n\n")
    description = paragraphs[0].strip() if paragraphs else ""
    marker = "Example:\n"
    example = doc.split(marker, 1)[1].strip() if marker in doc else ""
    if not description or not example:
        raise ValueError(
            f"Stable SDK method lacks a description or example: {function.__qualname__}"
        )
    return description, example


def _require_unique(items: list[dict[str, Any]], key: str) -> None:
    values = [item[key] for item in items]
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise ValueError(f"Duplicate {key} values: {duplicates}")


if __name__ == "__main__":
    raise SystemExit(main())
