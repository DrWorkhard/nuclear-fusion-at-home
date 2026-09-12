#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: uv is required: https://docs.astral.sh/uv/" >&2
  exit 1
fi
if ! command -v brew >/dev/null 2>&1; then
  echo "ERROR: Homebrew is required for OpenMPI on the canonical macOS host." >&2
  exit 1
fi
if ! brew list --versions open-mpi >/dev/null 2>&1; then
  if [[ "${FUSION_NO_SYSTEM_INSTALL:-0}" == "1" ]]; then
    echo "ERROR: OpenMPI prerequisite unavailable; system installation forbidden." >&2
    exit 1
  fi
  brew install open-mpi
fi

clone_pinned() {
  local url="$1"
  local destination="$2"
  local commit="$3"
  local branch="$4"
  if [[ ! -d "$destination/.git" ]]; then
    GIT_LFS_SKIP_SMUDGE=1 git clone --filter=blob:none --no-checkout "$url" "$destination"
    git -C "$destination" fetch --depth 1 origin "$commit"
    GIT_LFS_SKIP_SMUDGE=1 git -C "$destination" checkout --detach "$commit"
  fi
  local actual
  actual="$(git -C "$destination" rev-parse HEAD)"
  if [[ "$actual" != "$commit" ]]; then
    echo "ERROR: $destination ($branch) is at $actual, expected $commit" >&2
    exit 1
  fi
}

clone_pinned \
  "https://github.com/akaptano/stellcoilbench.git" \
  "external/stellcoilbench" \
  "c7949edc4ea6378fc3be633304c69c288c3b79b5" \
  "main"
clone_pinned \
  "https://github.com/PedroFranciscoGil/simsopt.git" \
  "external/simsopt" \
  "a79006b0bc1e6df8ab48de284e3457d39a49b995" \
  "auglag_coils"

# On this host, an incomplete Command Line Tools libc++ directory precedes the
# complete SDK headers. Explicitly prepend the SDK copy for C++ extension builds.
sdk_path="$(xcrun --show-sdk-path)"
export CPLUS_INCLUDE_PATH="$sdk_path/usr/include/c++/v1${CPLUS_INCLUDE_PATH:+:$CPLUS_INCLUDE_PATH}"

uv sync --locked --python 3.12 --extra dev --extra benchmark
uv run --locked fusion-baselines verify-stellcoilbench
uv run --locked pytest -q
