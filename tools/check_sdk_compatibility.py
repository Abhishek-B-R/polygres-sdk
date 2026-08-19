#!/usr/bin/env python3
"""Compare the generated SDK contract with an explicit released baseline."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from jsonschema import Draft202012Validator, FormatChecker

SDK_ROOT = Path(__file__).resolve().parents[1]
CURRENT_SPEC = SDK_ROOT / "src" / "polygres" / "spec" / "python-sdk-v1.methods.json"
METHOD_SCHEMA = SDK_ROOT / "src" / "polygres" / "spec" / "python-sdk-v1.methods.schema.json"
MIGRATIONS_ROOT = SDK_ROOT / "migrations"
SEMVER_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
Classification = Literal["breaking", "additive", "informational", "review"]


@dataclass(frozen=True, slots=True)
class Change:
    classification: Classification
    subject: str
    detail: str


def compare_specs(baseline: dict[str, Any], current: dict[str, Any]) -> list[Change]:
    """Classify public SDK and bound HTTP contract changes."""

    changes: list[Change] = []
    if baseline["default_api_version"] != current["default_api_version"]:
        changes.append(
            Change(
                "review",
                "default_api_version",
                f"{baseline['default_api_version']} -> {current['default_api_version']}",
            )
        )

    old_methods = {item["public_name"]: item for item in baseline["methods"]}
    new_methods = {item["public_name"]: item for item in current["methods"]}
    removed = set(old_methods) - set(new_methods)
    added = set(new_methods) - set(old_methods)
    for old_name in sorted(removed):
        old_operations = set(old_methods[old_name]["operation_ids"])
        rename = next(
            (
                new_name
                for new_name in added
                if old_operations & set(new_methods[new_name]["operation_ids"])
            ),
            None,
        )
        detail = f"renamed to {rename}" if rename else "method removed"
        changes.append(Change("breaking", old_name, detail))
    for name in sorted(added):
        changes.append(Change("additive", name, "public method added"))

    for name in sorted(set(old_methods) & set(new_methods)):
        old = old_methods[name]
        new = new_methods[name]
        old_ids = set(old["operation_ids"])
        new_ids = set(new["operation_ids"])
        for operation_id in sorted(old_ids - new_ids):
            changes.append(Change("breaking", name, f"operation binding removed: {operation_id}"))
        for operation_id in sorted(new_ids - old_ids):
            changes.append(Change("additive", name, f"operation binding added: {operation_id}"))
        if old.get("exception_categories") != new.get("exception_categories"):
            changes.append(Change("breaking", name, "exception categories changed"))
        if old.get("deprecated") is None and new.get("deprecated") is not None:
            changes.append(
                Change(
                    "informational",
                    name,
                    f"deprecated in {new['deprecated']}; migration note required",
                )
            )
        old_operations = {item["operation_id"]: item for item in old["operations"]}
        new_operations = {item["operation_id"]: item for item in new["operations"]}
        for operation_id in sorted(set(old_operations) & set(new_operations)):
            changes.extend(
                _compare_operation(name, old_operations[operation_id], new_operations[operation_id])
            )
    return changes


def required_release(changes: list[Change]) -> Literal["patch", "minor", "major"]:
    """Return the SemVer release level required by the confirmed policy."""

    if any(change.classification == "breaking" for change in changes):
        return "major"
    if any(change.classification == "additive" for change in changes):
        return "minor"
    return "patch"


def version_satisfies(
    baseline_version: str, current_version: str, required: Literal["patch", "minor", "major"]
) -> bool:
    """Enforce SemVer, including minor releases for pre-1.0 breaking changes."""

    old = _semver_tuple(baseline_version)
    new = _semver_tuple(current_version)
    if new <= old:
        return False
    if required == "patch":
        return True
    if required == "minor":
        return new[0] > old[0] or (new[0] == old[0] and new[1] > old[1])
    if old[0] == 0:
        return new[0] > 0 or (new[0] == 0 and new[1] > old[1])
    return new[0] > old[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline",
        type=Path,
        required=True,
        help="explicit released python-sdk-v1.methods.json baseline",
    )
    parser.add_argument("--current", type=Path, default=CURRENT_SPEC)
    parser.add_argument(
        "--expect-current-version",
        help="also require the current artifact to use this release or tag version",
    )
    parser.add_argument(
        "--allow-api-version-change",
        action="store_true",
        help="acknowledge a reviewed default API behavior-version change",
    )
    args = parser.parse_args(argv)
    if args.baseline.resolve() == args.current.resolve():
        parser.error("baseline and current specifications must be different explicit files")
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    current = json.loads(args.current.read_text(encoding="utf-8"))
    _validate_spec_input(baseline, label="baseline")
    _validate_spec_input(current, label="current")
    changes = compare_specs(baseline, current)
    baseline_version = baseline["sdk_version"]
    current_version = current["sdk_version"]
    classification_required = required_release(changes)
    required = _effective_required_release(baseline_version, classification_required)

    for change in changes:
        print(f"{change.classification.upper():13} {change.subject}: {change.detail}")
    if not changes:
        print("NO CONTRACT CHANGES")
    policy = " (pre-1.0 breaking policy)" if classification_required != required else ""
    print(
        f"Required release: {required}{policy}; baseline: {baseline_version}; "
        f"current: {current_version}"
    )

    failed = False
    if not version_satisfies(baseline_version, current_version, required):
        print(
            "Current SDK version does not satisfy the required SemVer increment.", file=sys.stderr
        )
        failed = True
    if args.expect_current_version and current_version != args.expect_current_version:
        print(
            f"Current SDK version {current_version} does not match expected "
            f"{args.expect_current_version}.",
            file=sys.stderr,
        )
        failed = True
    if any(change.classification == "review" for change in changes) and not (
        args.allow_api_version_change
    ):
        print("Default API behavior-version change requires explicit review.", file=sys.stderr)
        failed = True
    migration_required = [
        change
        for change in changes
        if change.classification in {"breaking", "informational"}
    ]
    if migration_required and not _migration_notes_cover(migration_required):
        print(
            "Breaking changes and new deprecations require topic-based migration notes.",
            file=sys.stderr,
        )
        failed = True
    return 1 if failed else 0


def _compare_operation(public_name: str, old: dict[str, Any], new: dict[str, Any]) -> list[Change]:
    changes: list[Change] = []
    operation_id = old["operation_id"]
    if (old["method"], old["path"]) != (new["method"], new["path"]):
        changes.append(
            Change(
                "breaking",
                public_name,
                f"HTTP method or path changed for {operation_id}",
            )
        )
    if not old.get("deprecated", False) and new.get("deprecated", False):
        changes.append(
            Change(
                "informational",
                public_name,
                f"OpenAPI operation deprecated: {operation_id}; migration note required",
            )
        )
    old_success = set(old["success_responses"])
    new_success = set(new["success_responses"])
    for status in sorted(old_success - new_success):
        changes.append(Change("breaking", public_name, f"success response removed: {status}"))
    for status in sorted(new_success - old_success):
        changes.append(Change("additive", public_name, f"success response added: {status}"))
    changes.extend(
        _compare_schema_contracts(
            public_name,
            "request",
            old.get("request_contract", []),
            new.get("request_contract", []),
        )
    )
    for status in sorted(old_success & new_success):
        changes.extend(
            _compare_schema_contracts(
                public_name,
                f"response {status}",
                old.get("success_contracts", {}).get(status, []),
                new.get("success_contracts", {}).get(status, []),
            )
        )
    return changes


def _compare_schema_contracts(
    public_name: str,
    location: str,
    old_contracts: list[dict[str, Any]],
    new_contracts: list[dict[str, Any]],
) -> list[Change]:
    changes: list[Change] = []
    old_by_schema = {item["schema"]: item for item in old_contracts}
    new_by_schema = {item["schema"]: item for item in new_contracts}
    for schema in sorted(set(old_by_schema) - set(new_by_schema)):
        changes.append(Change("breaking", public_name, f"{location} schema removed: {schema}"))
    for schema in sorted(set(new_by_schema) - set(old_by_schema)):
        changes.append(Change("additive", public_name, f"{location} schema added: {schema}"))
    for schema in sorted(set(old_by_schema) & set(new_by_schema)):
        old = old_by_schema[schema]
        new = new_by_schema[schema]
        old_fields = set(old["fields"])
        new_fields = set(new["fields"])
        old_required = set(old["required_fields"])
        new_required = set(new["required_fields"])
        for field in sorted(old_fields - new_fields):
            changes.append(
                Change("breaking", public_name, f"{location} field removed: {schema}.{field}")
            )
        for field in sorted(new_fields - old_fields):
            classification: Classification = (
                "breaking" if location == "request" and field in new_required else "additive"
            )
            detail = (
                f"{location} required field added: {schema}.{field}"
                if classification == "breaking"
                else f"{location} optional field added: {schema}.{field}"
            )
            changes.append(Change(classification, public_name, detail))
        for field in sorted(new_required - old_required):
            if field in old_fields:
                changes.append(
                    Change(
                        "breaking",
                        public_name,
                        f"{location} field became required: {schema}.{field}",
                    )
                )
    return changes


def _semver_tuple(value: str) -> tuple[int, int, int]:
    match = SEMVER_RE.fullmatch(value)
    if match is None:
        raise ValueError(f"Invalid SemVer value: {value}")
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def _effective_required_release(
    baseline_version: str,
    required: Literal["patch", "minor", "major"],
) -> Literal["patch", "minor", "major"]:
    if required == "major" and _semver_tuple(baseline_version)[0] == 0:
        return "minor"
    return required


def _validate_spec_input(document: dict[str, Any], *, label: str) -> None:
    schema = json.loads(METHOD_SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.path))
    if errors:
        detail = "; ".join(
            f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
            for error in errors
        )
        raise ValueError(f"Invalid {label} method specification: {detail}")
    for key in ("public_name", "python_qualname"):
        values = [method[key] for method in document["methods"]]
        if len(values) != len(set(values)):
            raise ValueError(f"Invalid {label} method specification: duplicate {key}")


def _migration_notes_cover(changes: list[Change]) -> bool:
    notes = [path for path in MIGRATIONS_ROOT.glob("*.md") if path.name != "README.md"]
    content = "\n".join(path.read_text(encoding="utf-8") for path in notes)
    return all(change.subject in content for change in changes)


if __name__ == "__main__":
    raise SystemExit(main())
