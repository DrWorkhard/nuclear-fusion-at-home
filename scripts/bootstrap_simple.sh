#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

expected_commit="9269e8614e581ede8768e0bccb003b52db87e3be"
libneo_commit="66ef89c2b59420bb8fbd14aa0838d5e88082bef8"

if [[ ! -d external/simple/.git ]]; then
  git clone --filter=blob:none --no-checkout \
    https://github.com/itpplasma/SIMPLE.git external/simple
  git -C external/simple fetch --depth 1 origin "$expected_commit"
  git -C external/simple checkout --detach "$expected_commit"
fi
actual_commit="$(git -C external/simple rev-parse HEAD)"
if [[ "$actual_commit" != "$expected_commit" ]]; then
  echo "ERROR: external/simple is at $actual_commit, expected $expected_commit" >&2
  exit 1
fi

if [[ "$(uname -s)" == "Darwin" ]]; then
  if ! command -v brew >/dev/null 2>&1; then
    echo "ERROR: Homebrew is required for the SIMPLE dependencies on macOS." >&2
    exit 1
  fi
  for formula in gcc cmake ninja netcdf netcdf-fortran lapack libomp; do
    if ! brew list --versions "$formula" >/dev/null 2>&1; then
      brew install "$formula"
    fi
  done
  export CMAKE_PREFIX_PATH="/opt/homebrew/opt/libomp;/opt/homebrew/opt/lapack${CMAKE_PREFIX_PATH:+;$CMAKE_PREFIX_PATH}"
  libomp_root="$(brew --prefix libomp)"
  netcdf_root="$(brew --prefix netcdf)"
  simple_cmake_flags="-DCMAKE_C_FLAGS=-I${netcdf_root}/include -DCMAKE_EXE_LINKER_FLAGS=-L${netcdf_root}/lib -DOpenMP_C_FLAGS='-Xpreprocessor -fopenmp -I${libomp_root}/include' -DOpenMP_C_LIB_NAMES=omp -DOpenMP_CXX_FLAGS='-Xpreprocessor -fopenmp -I${libomp_root}/include' -DOpenMP_CXX_LIB_NAMES=omp -DOpenMP_omp_LIBRARY=${libomp_root}/lib/libomp.dylib"
fi

simple_cmake_flags="${simple_cmake_flags:-} -DLIBNEO_REF=${libneo_commit}"
make -C external/simple build-deterministic-nopy FLAGS="$simple_cmake_flags"
ctest --test-dir external/simple/build/test -L smoke --output-on-failure
