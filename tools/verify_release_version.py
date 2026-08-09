#!/usr/bin/env python3
"""Verify SDK release-version parity across source and generated artifacts."""

from __future__ import annotations

import argparse
import json
from importlib.metadata import version
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised by the Python 3.10 CI job
    import tomli as tomllib

SDK_ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", help="optional release tag in polygres-sdk-vX.Y.Z form")
    args = parser.parse_args(argv)
    source_version = str(
        tomllib.loads((SDK_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"][
            "version"
        ]
    )
    method_version = str(
        json.loads(
            (
                SDK_ROOT
                / "src"
                / "polygres"
                / "spec"
                / "python-sdk-v1.methods.json"
            ).read_text(encoding="utf-8")
        )["sdk_version"]
    )
    installed_version = version("polygres-sdk")
    expected = {
        "pyproject.toml": source_version,
        "method specification": method_version,
        "installed distribution": installed_version,
    }
    if args.tag is not None:
        prefix = "polygres-sdk-v"
        if not args.tag.startswith(prefix):
            parser.error(f"release tag must start with {prefix}")
        expected["release tag"] = args.tag.removeprefix(prefix)
    if len(set(expected.values())) != 1:
        raise SystemExit(f"SDK release versions do not match: {expected}")
    print(f"SDK release version is consistent: {source_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
