#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

# Optional FUSION_QI_ARCHIVE is an existing read-only download cache. The archive
# is verified and freshly extracted; no previous solver trees/results are needed.
uv sync --locked --python 3.12 --extra dev
bash scripts/bootstrap_qi_data.sh
FUSION_REQUIRE_QI_DATA=1 uv run --locked pytest -q \
  tests/test_qi_data_integration.py \
  tests/test_scientific_integration.py -k 'not w7x'
