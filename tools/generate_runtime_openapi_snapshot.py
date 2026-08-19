#!/usr/bin/env python3
"""Generate the deterministic public Runtime v1 OpenAPI snapshot."""

from __future__ import annotations

import argparse
import json
import os
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

SNAPSHOT_VERSION = 1
SDK_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = SDK_ROOT.parents[1] if SDK_ROOT.parent.name == "packages" else SDK_ROOT
SNAPSHOT_PATH = SDK_ROOT / "src" / "polygres" / "spec" / "runtime-v1.openapi.json"
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def build_snapshot() -> dict[str, Any]:
    """Build and validate a deterministic public Runtime API document."""

    if not runtime_source_available():
        raise RuntimeError("Runtime service source is unavailable in this SDK-only checkout.")
    _configure_deterministic_schema_environment()
    sys.path.insert(0, str(REPOSITORY_ROOT / "packages" / "polygres-lib" / "python" / "src"))
    sys.path.insert(0, str(REPOSITORY_ROOT / "services" / "api"))

    from app.runtime_main import create_runtime_app

    source = create_runtime_app().openapi()
    document = _public_runtime_document(source)
    document["x-polygres-sdk-openapi-snapshot-version"] = SNAPSHOT_VERSION
    _validate_snapshot(document)
    return document


def render_snapshot(document: dict[str, Any]) -> str:
    """Render canonical snapshot bytes."""

    return json.dumps(document, indent=2, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the committed snapshot differs from the Runtime application",
    )
    args = parser.parse_args(argv)
    if args.check and not runtime_source_available():
        current = SNAPSHOT_PATH.read_text(encoding="utf-8")
        document = json.loads(current)
        _validate_snapshot(document)
        if current != render_snapshot(document):
            sys.stderr.write(f"{SNAPSHOT_PATH} is not canonically rendered.\n")
            return 1
        sys.stdout.write(
            "Runtime source is unavailable; committed OpenAPI snapshot is structurally "
            f"valid and canonical: {SNAPSHOT_PATH}\n"
        )
        return 0
    rendered = render_snapshot(build_snapshot())

    if args.check:
        try:
            current = SNAPSHOT_PATH.read_text(encoding="utf-8")
        except OSError as exc:
            parser.error(f"could not read {SNAPSHOT_PATH}: {exc}")
        if current != rendered:
            sys.stderr.write(
                f"{SNAPSHOT_PATH} is stale. Run "
                "packages/python-sdk/tools/generate_runtime_openapi_snapshot.py.\n"
            )
            return 1
        sys.stdout.write(f"Runtime OpenAPI snapshot is current: {SNAPSHOT_PATH}\n")
        return 0

    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(rendered, encoding="utf-8")
    sys.stdout.write(f"Wrote Runtime OpenAPI snapshot: {SNAPSHOT_PATH}\n")
    return 0


def _configure_deterministic_schema_environment() -> None:
    os.environ.update(
        {
            "ENVIRONMENT": "local",
            "LOCAL_CONTROL_PLANE": "memory",
            "LOCAL_RUNTIME_MODE": "in_memory",
        }
    )


def runtime_source_available() -> bool:
    return (REPOSITORY_ROOT / "services" / "api" / "app" / "runtime_main.py").is_file()


def _public_runtime_document(source: dict[str, Any]) -> dict[str, Any]:
    paths = {
        path: deepcopy(path_item)
        for path, path_item in source.get("paths", {}).items()
        if path.startswith("/v1/")
    }
    document: dict[str, Any] = {
        key: deepcopy(value)
        for key, value in source.items()
        if key not in {"components", "paths", "servers"}
    }
    document["paths"] = paths
    document["components"] = _referenced_components(source, {"paths": paths})
    return document


def _referenced_components(
    source: dict[str, Any], retained: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    source_components = source.get("components", {})
    output: dict[str, dict[str, Any]] = {}
    pending = list(_component_refs(retained))
    seen: set[tuple[str, str]] = set()
    while pending:
        section, name = pending.pop()
        key = (section, name)
        if key in seen:
            continue
        seen.add(key)
        try:
            value = deepcopy(source_components[section][name])
        except KeyError as exc:
            raise ValueError(
                f"Unresolved component reference: #/components/{section}/{name}"
            ) from exc
        output.setdefault(section, {})[name] = value
        pending.extend(_component_refs(value))

    security_names = _security_scheme_names(retained)
    if security_names:
        schemes = source_components.get("securitySchemes", {})
        for name in security_names:
            if name not in schemes:
                raise ValueError(f"Unresolved security scheme: {name}")
            output.setdefault("securitySchemes", {})[name] = deepcopy(schemes[name])
    return output


def _component_refs(value: Any) -> set[tuple[str, str]]:
    refs: set[tuple[str, str]] = set()
    if isinstance(value, dict):
        ref = value.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/components/"):
            parts = ref.split("/")
            if len(parts) != 4 or not parts[2] or not parts[3]:
                raise ValueError(f"Malformed component reference: {ref}")
            refs.add((parts[2], parts[3]))
        for item in value.values():
            refs.update(_component_refs(item))
    elif isinstance(value, list):
        for item in value:
            refs.update(_component_refs(item))
    return refs


def _security_scheme_names(value: Any) -> set[str]:
    names: set[str] = set()
    if isinstance(value, dict):
        security = value.get("security")
        if isinstance(security, list):
            for requirement in security:
                if isinstance(requirement, dict):
                    names.update(str(name) for name in requirement)
        for item in value.values():
            names.update(_security_scheme_names(item))
    elif isinstance(value, list):
        for item in value:
            names.update(_security_scheme_names(item))
    return names


def _validate_snapshot(document: dict[str, Any]) -> None:
    if not isinstance(document.get("openapi"), str):
        raise ValueError("FastAPI did not produce an OpenAPI version.")
    paths = document.get("paths")
    if not isinstance(paths, dict) or not paths:
        raise ValueError("Runtime OpenAPI schema contains no public /v1 operations.")
    operation_ids: set[str] = set()
    for path, path_item in paths.items():
        if not path.startswith("/v1/") or not isinstance(path_item, dict):
            raise ValueError(f"Unexpected Runtime OpenAPI path: {path}")
        for method, operation in path_item.items():
            if method not in HTTP_METHODS:
                continue
            if not isinstance(operation, dict):
                raise ValueError(f"Malformed operation: {method.upper()} {path}")
            operation_id = operation.get("operationId")
            if not isinstance(operation_id, str) or not operation_id:
                raise ValueError(f"Operation has no operationId: {method.upper()} {path}")
            if operation_id in operation_ids:
                raise ValueError(f"OpenAPI operationId is not unique: {operation_id}")
            operation_ids.add(operation_id)
    _resolve_all_refs(document)


def _resolve_all_refs(document: dict[str, Any]) -> None:
    for section, name in _component_refs(document):
        components = document.get("components", {})
        if section not in components or name not in components[section]:
            raise ValueError(f"Unresolved retained reference: #/components/{section}/{name}")


if __name__ == "__main__":
    raise SystemExit(main())
