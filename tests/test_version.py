from __future__ import annotations

import importlib.metadata
import runpy
from importlib.metadata import version
from pathlib import Path

import pytest

from polygres import __version__


def test_import_version_matches_installed_distribution_metadata() -> None:
    assert __version__ == version("polygres-sdk")
    assert __version__ != "0+unknown"


def test_uninstalled_source_uses_non_release_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing_distribution(_name: str) -> str:
        raise importlib.metadata.PackageNotFoundError

    monkeypatch.setattr(importlib.metadata, "version", missing_distribution)
    version_module = Path(__file__).resolve().parents[1] / "src" / "polygres" / "_version.py"

    namespace = runpy.run_path(str(version_module))

    assert namespace["__version__"] == "0+unknown"
