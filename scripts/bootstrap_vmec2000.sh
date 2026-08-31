#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_root="$project_root/external/stellopt-v251"
patch_file="$project_root/patches/stellopt-v251-macos-vmec-validation.patch"
expected_commit="e59affaec7713aee8da1f1bccdf05cc0612c12e3"

if [[ "$(uname -s)" != "Darwin" ]] || [[ "$(uname -m)" != "arm64" ]]; then
  echo "ERROR: this bootstrap is qualified only for Apple Silicon macOS." >&2
  exit 1
fi
if ! command -v brew >/dev/null 2>&1; then
  echo "ERROR: Homebrew is required." >&2
  exit 1
fi
for formula in gcc open-mpi netcdf netcdf-fortran lapack; do
  if ! brew list --versions "$formula" >/dev/null 2>&1; then
    brew install "$formula"
  fi
done

if [[ ! -d "$source_root/.git" ]]; then
  git clone --filter=blob:none --no-checkout \
    https://github.com/PrincetonUniversity/STELLOPT.git "$source_root"
  git -C "$source_root" fetch --depth 1 origin "$expected_commit"
  git -C "$source_root" checkout --detach "$expected_commit"
fi

actual_commit="$(git -C "$source_root" rev-parse HEAD)"
if [[ "$actual_commit" != "$expected_commit" ]]; then
  echo "ERROR: $source_root is at $actual_commit, expected $expected_commit" >&2
  exit 1
fi

if git -C "$source_root" apply --reverse --check "$patch_file" 2>/dev/null; then
  echo "Validation patch is already applied."
elif git -C "$source_root" diff --quiet && \
     git -C "$source_root" diff --cached --quiet && \
     git -C "$source_root" apply --check "$patch_file"; then
  git -C "$source_root" apply "$patch_file"
else
  echo "ERROR: source tree has unexpected modifications or patch does not apply." >&2
  git -C "$source_root" status --short >&2
  exit 1
fi

mkdir -p "$source_root/local"
ln -sfn BENCHMARKS/make_pppl.inc "$source_root/make.inc"
make -C "$source_root/LIBSTELL" release
make -C "$source_root/VMEC2000" release

binary="$source_root/VMEC2000/Release/xvmec2000"
if [[ ! -x "$binary" ]]; then
  echo "ERROR: build did not create $binary" >&2
  exit 1
fi
shasum -a 256 "$patch_file" "$binary"
"$binary" --help >/dev/null 2>&1 || true
