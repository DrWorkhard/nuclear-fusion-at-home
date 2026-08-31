#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

uv sync --locked --python 3.12 --extra dev
uv run --locked ruff check .
uv run --locked pytest -q
