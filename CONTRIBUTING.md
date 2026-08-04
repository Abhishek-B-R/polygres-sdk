# Contributing

Thanks for helping improve the Polygres Python SDK.

## Development Setup

Use Python 3.10 or newer.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

## Checks

Run these before opening a pull request:

```bash
pytest
ruff check .
python tools/generate_runtime_openapi_snapshot.py --check
python tools/generate_sdk_method_spec.py --check
python tools/generate_sdk_method_spec.py --validate-only
python tools/check_sdk_compatibility.py \
  --baseline compatibility/0.1.0/python-sdk-v1.methods.json
python -m build
python tools/verify_distribution.py dist/*.whl dist/*.tar.gz
```

The Runtime OpenAPI snapshot can be regenerated only from the Polygres
monorepo, where `services/api` is available. An SDK-only checkout can validate
the committed snapshot structure and canonical formatting, while the monorepo
sync gate performs the byte-for-byte application comparison.

Public methods stay hand-written and typed. Add non-wrapping binding metadata
and a description plus safe example for every new network method, then
regenerate the method JSON and reference page. Neither JSON artifact may be
used to route requests.

Use SemVer for the package. Before 1.0, breaking changes increment the minor
version and require a topic note in `migrations`; additive public changes also
increment the minor version. Internal fixes with unchanged public behavior use
a patch release.

## Publishing

Publishing uses GitHub Actions Trusted Publishing. Do not add PyPI API tokens
or package index passwords to GitHub secrets.

Release rehearsal happens first on TestPyPI:

1. Run the `Publish Python SDK` workflow from the public repository.
2. Select `publish_target = testpypi`.
3. Verify installation from TestPyPI in a clean environment:

   ```bash
   python3 -m venv /tmp/polygres-sdk-testpypi
   /tmp/polygres-sdk-testpypi/bin/python -m pip install --upgrade pip
   /tmp/polygres-sdk-testpypi/bin/python -m pip install \
     --index-url https://test.pypi.org/simple/ \
     --extra-index-url https://pypi.org/simple/ \
     polygres-sdk==0.2.0
   /tmp/polygres-sdk-testpypi/bin/python - <<'PY'
   import importlib.metadata
   from polygres import Polygres

   print(importlib.metadata.version("polygres-sdk"))
   print(Polygres)
   PY
   ```

Publish to PyPI only after the same commit has passed TestPyPI validation. Push
a release tag from the public repository:

```bash
git tag polygres-sdk-v0.2.0
git push origin polygres-sdk-v0.2.0
```

The `pypi` GitHub environment must be approved before the upload proceeds.
Project URLs in `pyproject.toml` must use valid HTTPS URLs accepted by PyPI.

## Scope

This repository contains the public Python SDK. It should stay focused on
client-side API access, models, documentation, and tests.

## Security Issues

Do not report vulnerabilities in public issues. Follow the process in
`SECURITY.md`.
