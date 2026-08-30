#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

expected_commit="1d7e09941c89210be95b6b20f4d4d555f0a63096"
if [[ ! -d external/vmecpp/.git ]]; then
  git clone --filter=blob:none --no-checkout \
    https://github.com/proximafusion/vmecpp.git external/vmecpp
  git -C external/vmecpp fetch --depth 1 origin "$expected_commit"
  git -C external/vmecpp checkout --detach "$expected_commit"
fi
actual_commit="$(git -C external/vmecpp rev-parse HEAD)"
if [[ "$actual_commit" != "$expected_commit" ]]; then
  echo "ERROR: external/vmecpp is at $actual_commit, expected $expected_commit" >&2
  exit 1
fi

uv sync --project environments/vmecpp --python 3.12
uv run --project environments/vmecpp python -c \
  'from importlib.metadata import version; import vmecpp; print(version("vmecpp"))'
