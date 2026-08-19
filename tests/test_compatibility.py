from __future__ import annotations

import importlib.util
import sys
from copy import deepcopy
from pathlib import Path

SDK_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = SDK_ROOT / "tools" / "check_sdk_compatibility.py"


def _tool():
    spec = importlib.util.spec_from_file_location("sdk_compatibility", TOOL_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _method(public_name: str) -> dict[str, object]:
    return {
        "public_name": public_name,
        "operation_ids": ["runtime_resource_get"],
        "operations": [
            {
                "operation_id": "runtime_resource_get",
                "method": "GET",
                "path": "/v1/resource",
                "success_responses": {"200": "Resource"},
                "request_contract": [],
                "success_contracts": {
                    "200": [
                        {
                            "schema": "Resource",
                            "fields": ["id"],
                            "required_fields": ["id"],
                            "allows_additional_fields": True,
                        }
                    ]
                },
            }
        ],
        "exception_categories": ["api"],
        "deprecated": None,
    }


def test_breaking_change_requires_minor_increment_before_one_dot_zero() -> None:
    tool = _tool()
    baseline = {
        "sdk_version": "0.1.0",
        "default_api_version": "2026-08-04",
        "methods": [_method("project.resource.get")],
    }
    current = {
        "sdk_version": "0.1.1",
        "default_api_version": "2026-08-04",
        "methods": [],
    }

    changes = tool.compare_specs(baseline, current)

    assert tool.required_release(changes) == "major"
    assert tool._effective_required_release("0.1.0", "major") == "minor"
    assert tool.version_satisfies("0.1.0", "0.1.1", "major") is False
    assert tool.version_satisfies("0.1.0", "0.2.0", "major") is True


def test_optional_request_field_is_additive_and_required_field_is_breaking() -> None:
    tool = _tool()
    baseline_method = _method("project.resource.get")
    baseline_method["operations"][0]["request_contract"] = [
        {
            "schema": "Request",
            "fields": ["query"],
            "required_fields": ["query"],
            "allows_additional_fields": False,
        }
    ]
    additive_method = deepcopy(baseline_method)
    additive_method["operations"][0]["request_contract"][0]["fields"].append("limit")
    breaking_method = deepcopy(additive_method)
    breaking_method["operations"][0]["request_contract"][0]["required_fields"].append("limit")
    base = {
        "sdk_version": "0.1.0",
        "default_api_version": "2026-08-04",
        "methods": [baseline_method],
    }

    additive = tool.compare_specs(
        base,
        {**base, "sdk_version": "0.2.0", "methods": [additive_method]},
    )
    breaking = tool.compare_specs(
        base,
        {**base, "sdk_version": "0.2.0", "methods": [breaking_method]},
    )

    assert any(change.classification == "additive" for change in additive)
    assert any(change.classification == "breaking" for change in breaking)


def test_openapi_deprecation_requires_an_informational_migration_note() -> None:
    tool = _tool()
    baseline_method = _method("project.resource.get")
    baseline_method["operations"][0]["deprecated"] = False
    deprecated_method = deepcopy(baseline_method)
    deprecated_method["operations"][0]["deprecated"] = True
    baseline = {
        "sdk_version": "0.1.0",
        "default_api_version": "2026-08-04",
        "methods": [baseline_method],
    }

    changes = tool.compare_specs(
        baseline,
        {**baseline, "sdk_version": "0.2.0", "methods": [deprecated_method]},
    )

    assert any(change.classification == "informational" for change in changes)
