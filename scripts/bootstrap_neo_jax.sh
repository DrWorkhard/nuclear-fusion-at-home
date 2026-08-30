#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

uv sync --project "$project_root/environments/neo-jax" --python 3.12
"$project_root/environments/neo-jax/.venv/bin/python" - <<'PY'
from importlib.metadata import version

assert version("neo-jax") == "1.0.1"
assert version("booz-xform") == "0.1.0"
print("verified: neo-jax 1.0.1 and booz-xform 0.1.0")
PY
