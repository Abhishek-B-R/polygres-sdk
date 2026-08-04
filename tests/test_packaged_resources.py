from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from polygres.spec import (
    load_python_method_schema,
    load_python_method_spec,
    load_runtime_openapi,
)


def test_packaged_contract_resources_load_through_importlib_resources() -> None:
    assert load_runtime_openapi()["x-polygres-sdk-openapi-snapshot-version"] == 1
    assert load_python_method_spec()["schema_version"] == 1
    assert load_python_method_schema()["$schema"].endswith("draft/2020-12/schema")
    packaged_migration = files("polygres").joinpath("migrations", "README.md")
    source_migration = Path(__file__).resolve().parents[1] / "migrations" / "README.md"
    assert packaged_migration.is_file() or source_migration.is_file()
