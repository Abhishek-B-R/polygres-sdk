from __future__ import annotations

import importlib.util
import inspect
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from polygres._method_metadata import get_sdk_method_binding, sdk_method
from polygres.client import Project
from polygres.context import ContextNamespace

SDK_ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = SDK_ROOT / "tools" / "generate_sdk_method_spec.py"
METHOD_SPEC_PATH = SDK_ROOT / "src" / "polygres" / "spec" / "python-sdk-v1.methods.json"
BASELINE_PATH = SDK_ROOT / "compatibility" / "0.1.0" / "python-sdk-v1.methods.json"


def _generator():
    spec = importlib.util.spec_from_file_location("sdk_method_generator", GENERATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_committed_method_spec_is_deterministic_schema_and_semantically_valid() -> None:
    generator = _generator()
    actual = json.loads(METHOD_SPEC_PATH.read_text(encoding="utf-8"))
    expected = generator.build_method_spec()

    assert actual == expected
    generator.validate_method_spec(actual)
    assert len(actual["methods"]) == 55
    assert len(actual["excluded_operations"]) == 23

    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    generator.validate_method_spec(baseline, require_current_operation_details=False)
    assert baseline["sdk_version"] == "0.1.0"
    assert len(baseline["methods"]) == 14


def test_shared_operation_and_composite_bindings_are_explicit() -> None:
    document = json.loads(METHOD_SPEC_PATH.read_text(encoding="utf-8"))
    methods = {item["public_name"]: item for item in document["methods"]}

    assert methods["project.context.update_collection"]["operation_ids"] == [
        "runtime_context_update_collection"
    ]
    assert methods["project.context.set_default_collection"]["operation_ids"] == [
        "runtime_context_update_collection"
    ]
    assert methods["project.context.wait_for_operation"]["binding_kind"] == "composite"
    assert methods["project.context.wait_for_operation"]["operation_ids"] == [
        "runtime_context_get_operation"
    ]
    assert methods["project.context.upsert_points"]["operations"][0][
        "success_responses"
    ] == {"200": "PointMutationResponse", "202": "OperationEnvelope"}


def test_sdk_method_metadata_does_not_wrap_or_change_signatures() -> None:
    def example(value: str, *, limit: int = 1) -> tuple[str, int]:
        return value, limit

    original_signature = inspect.signature(example)
    decorated = sdk_method(
        public_name="project.example.call",
        operation_ids=("runtime_example_call",),
        since="0.2.0",
        retry_policy="read_only_get",
    )(example)

    assert decorated is example
    assert inspect.signature(decorated) == original_signature
    assert decorated("value", limit=2) == ("value", 2)
    assert get_sdk_method_binding(decorated) is not None
    assert get_sdk_method_binding(Project.readiness) is not None
    assert get_sdk_method_binding(ContextNamespace.search) is not None


def test_semantic_validation_rejects_duplicates_and_expired_exclusions() -> None:
    generator = _generator()
    document = generator.build_method_spec()
    duplicate = deepcopy(document)
    duplicate["methods"].append(deepcopy(duplicate["methods"][0]))
    with pytest.raises(ValueError, match="non-unique|Duplicate public_name"):
        generator.validate_method_spec(duplicate)

    expired = deepcopy(document)
    expired["excluded_operations"][0]["review_date"] = "2020-01-01"
    with pytest.raises(ValueError, match="review is overdue"):
        generator.validate_method_spec(expired)


def test_generated_json_is_descriptive_and_not_used_for_request_dispatch() -> None:
    import polygres.client as client_module

    source = inspect.getsource(client_module)
    assert "polygres.spec" not in source
    assert "python-sdk-v1.methods.json" not in source
    assert "runtime-v1.openapi.json" not in source
