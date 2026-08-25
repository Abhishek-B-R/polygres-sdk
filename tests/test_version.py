from __future__ import annotations

import importlib.metadata
import json
import runpy
from importlib.metadata import version
from pathlib import Path

import pytest

from polygres import __version__


def test_import_version_matches_installed_distribution_metadata() -> None:
    assert __version__ == version("polygres-sdk")
    assert __version__ != "0+unknown"


def test_release_metadata_and_documentation_name_current_sdk_version() -> None:
    root = Path(__file__).resolve().parents[1]
    readme = (root / "README.md").read_text(encoding="utf-8")
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    methods = json.loads(
        (root / "src" / "polygres" / "spec" / "python-sdk-v1.methods.json").read_text(
            encoding="utf-8"
        )
    )

    assert __version__ == "0.4.1"
    assert methods["sdk_version"] == "0.4.1"
    assert "Package version: [`0.4.1`]" in readme
    assert "polygres-sdk-v0.4.1" in readme
    assert "SDK 0.4.1 release notes" in readme
    assert "## 0.4.1 - 2026-08-25" in changelog


def test_uninstalled_source_uses_non_release_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing_distribution(_name: str) -> str:
        raise importlib.metadata.PackageNotFoundError

    monkeypatch.setattr(importlib.metadata, "version", missing_distribution)
    version_module = Path(__file__).resolve().parents[1] / "src" / "polygres" / "_version.py"

    namespace = runpy.run_path(str(version_module))

    assert namespace["__version__"] == "0+unknown"
