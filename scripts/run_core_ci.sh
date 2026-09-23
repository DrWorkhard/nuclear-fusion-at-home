#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

uv sync --locked --python 3.12 --extra dev
# This is the lightweight dev-only profile, not the native research regression.
# Run in a disposable checkout: uv sync must not replace the research environment.
uv run --locked --extra dev ruff check .
uv run --locked --extra dev python -I -S scripts/test_public.py
uv run --locked --extra dev python -I -S scripts/check_docs.py
uv run --locked --extra dev pytest -q tests/test_documentation.py tests/test_release_maintenance.py
