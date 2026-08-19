#!/usr/bin/env python3
"""Verify wheel and sdist contents required by the SDK contract."""

from __future__ import annotations

import argparse
import tarfile
import zipfile
from pathlib import Path

WHEEL_RESOURCES = {
    "polygres/migrations/README.md",
    "polygres/spec/pgcontext-0.2.0-compatibility.json",
    "polygres/spec/python-sdk-v1.methods.json",
    "polygres/spec/python-sdk-v1.methods.schema.json",
    "polygres/spec/runtime-v1.openapi.json",
}
SDIST_RESOURCES = {
    "migrations/README.md",
    "src/polygres/spec/pgcontext-0.2.0-compatibility.json",
    "src/polygres/spec/python-sdk-v1.methods.json",
    "src/polygres/spec/python-sdk-v1.methods.schema.json",
    "src/polygres/spec/runtime-v1.openapi.json",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifacts", nargs="+", type=Path)
    args = parser.parse_args(argv)
    wheels = [path for path in args.artifacts if path.suffix == ".whl"]
    sdists = [path for path in args.artifacts if path.name.endswith(".tar.gz")]
    if len(wheels) != 1 or len(sdists) != 1:
        parser.error("provide exactly one wheel and one .tar.gz source distribution")
    _verify_wheel(wheels[0])
    _verify_sdist(sdists[0])
    print(f"Verified required SDK resources in {wheels[0]} and {sdists[0]}")
    return 0


def _verify_wheel(path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
    missing = sorted(WHEEL_RESOURCES - names)
    if missing:
        raise SystemExit(f"Wheel is missing required SDK resources: {missing}")


def _verify_sdist(path: Path) -> None:
    with tarfile.open(path, mode="r:gz") as archive:
        relative_names = {
            name.split("/", 1)[1]
            for name in archive.getnames()
            if "/" in name
        }
    missing = sorted(SDIST_RESOURCES - relative_names)
    if missing:
        raise SystemExit(f"Source distribution is missing required SDK resources: {missing}")


if __name__ == "__main__":
    raise SystemExit(main())
