#!/usr/bin/env bash
set -euo pipefail

sdk_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="${POLYGRES_TEST_PYTHON:-${sdk_root}/.venv/bin/python}"

if [[ ! -x "${python_bin}" ]]; then
  echo "Python executable not found: ${python_bin}" >&2
  echo "Set POLYGRES_TEST_PYTHON to an environment with polygres-sdk installed." >&2
  exit 9
fi

if [[ -z "${POLYGRES_API_KEY:-}" ]]; then
  echo "POLYGRES_API_KEY is required." >&2
  exit 2
fi

if [[ -z "${POLYGRES_PROJECT_ID:-}" && -z "${POLYGRES_RUNTIME_URL:-}" ]]; then
  echo "Set POLYGRES_PROJECT_ID or POLYGRES_RUNTIME_URL." >&2
  exit 2
fi

export PYTHONPATH="${sdk_root}/src${PYTHONPATH:+:${PYTHONPATH}}"
exec "${python_bin}" "${sdk_root}/tools/test_context_live.py" \
  --confirm-staging-mutations "$@"
