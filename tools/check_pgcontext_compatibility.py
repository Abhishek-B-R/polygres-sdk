#!/usr/bin/env python3
"""Validate the pinned pgContext 0.2.0 compatibility inventory."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

EXPECTED_SOURCE_COMMIT = "7d0818ed222e16ef5c74932981d759caf2818d82"
EXPECTED_SOURCE_SHA256 = "3e74fc6f73fde30dc4a1f6cf0a9fc217be8550813d837b09718a72ed6366bc67"
EXPECTED_COUNTS = {
    "aligned": 38,
    "experimental_not_exposed": 91,
    "managed_equivalent": 20,
    "partial": 15,
    "sql_only": 25,
    "deferred": 5,
}
EXPECTED_INVENTORY_SHAPE = {
    ("experimental", "function"): 69,
    ("experimental", "guc"): 7,
    ("experimental", "sql_contract"): 15,
    ("stable", "enum"): 13,
    ("stable", "function"): 86,
    ("stable", "sql_contract"): 4,
}
ALLOWED_STATUSES = frozenset(EXPECTED_COUNTS)


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _arguments() -> argparse.Namespace:
    package_root = Path(__file__).resolve().parents[1]
    repository_root = package_root.parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=(
            repository_root
            / "packages/polygres-lib/contracts/context/pgcontext-0.2.0-compatibility.json"
        ),
    )
    parser.add_argument(
        "--method-spec",
        type=Path,
        default=package_root / "src/polygres/spec/python-sdk-v1.methods.json",
    )
    parser.add_argument(
        "--packaged-manifest",
        type=Path,
        default=package_root / "src/polygres/spec/pgcontext-0.2.0-compatibility.json",
    )
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    manifest = _load_json(args.manifest)
    packaged_manifest = _load_json(args.packaged_manifest)
    method_spec = _load_json(args.method_spec)
    errors: list[str] = []

    if packaged_manifest != manifest:
        errors.append("packaged pgContext compatibility inventory is stale")

    if manifest.get("pgcontext_version") != "0.2.0":
        errors.append("manifest pgcontext_version must be 0.2.0")
    source = manifest.get("source")
    if not isinstance(source, dict):
        errors.append("manifest source must be an object")
    else:
        if source.get("commit") != EXPECTED_SOURCE_COMMIT:
            errors.append("manifest source commit does not match the pinned v0.2.0 commit")
        if source.get("sha256") != EXPECTED_SOURCE_SHA256:
            errors.append("manifest source hash does not match the pinned v0.2.0 reference")

    raw_items = manifest.get("items")
    if not isinstance(raw_items, list):
        errors.append("manifest items must be a list")
        raw_items = []

    keys: set[str] = set()
    identities: set[tuple[object, object, object]] = set()
    counts: Counter[str] = Counter()
    inventory_shape: Counter[tuple[object, object]] = Counter()
    sdk_methods = {
        item.get("public_name"): item
        for item in method_spec.get("methods", [])
        if isinstance(item, dict)
    }

    for offset, item in enumerate(raw_items, 1):
        if not isinstance(item, dict):
            errors.append(f"item {offset} must be an object")
            continue
        key = item.get("key")
        if not isinstance(key, str) or not key:
            errors.append(f"item {offset} has no key")
        elif key in keys:
            errors.append(f"duplicate key: {key}")
        else:
            keys.add(key)

        identity = (item.get("stability"), item.get("kind"), item.get("signature"))
        if identity in identities:
            errors.append(f"duplicate inventory identity: {identity!r}")
        identities.add(identity)
        inventory_shape[(item.get("stability"), item.get("kind"))] += 1

        status = item.get("status")
        if status not in ALLOWED_STATUSES:
            errors.append(f"{key}: invalid status {status!r}")
            continue
        counts[status] += 1

        method = item.get("sdk_method")
        operation_id = item.get("runtime_operation_id")
        if status in {"aligned", "managed_equivalent", "partial"}:
            public_name = f"project.context.{method}"
            binding = sdk_methods.get(public_name)
            if binding is None:
                errors.append(f"{key}: missing generated SDK binding {public_name}")
                continue
            if operation_id is None and binding.get("binding_kind") != "local":
                errors.append(f"{key}: {public_name} must be a local binding")
            elif operation_id is not None and operation_id not in binding.get("operation_ids", []):
                errors.append(
                    f"{key}: {public_name} is not bound to Runtime operation {operation_id}"
                )
        elif method is not None or operation_id is not None:
            errors.append(f"{key}: {status} item must not claim an SDK binding")

    actual_counts = dict(sorted(counts.items()))
    if actual_counts != EXPECTED_COUNTS:
        errors.append(f"inventory counts changed: expected {EXPECTED_COUNTS}, got {actual_counts}")
    if manifest.get("status_counts") != EXPECTED_COUNTS:
        errors.append("manifest status_counts do not match the reviewed inventory counts")
    if dict(inventory_shape) != EXPECTED_INVENTORY_SHAPE:
        errors.append(
            "inventory shape changed: "
            f"expected {EXPECTED_INVENTORY_SHAPE}, got {dict(inventory_shape)}"
        )

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(
        "pgContext 0.2.0 compatibility inventory valid: "
        + ", ".join(f"{status}={count}" for status, count in actual_counts.items())
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
