# Canonical environment

## Platform qualified so far

- macOS 15.7.4, Apple M1 (`arm64`), 8 logical CPUs, 16 GiB RAM;
- CPython 3.12.13 managed by `uv`;
- OpenMPI 5.0.10;
- StellCoilBench commit `c7949edc4ea6378fc3be633304c69c288c3b79b5`;
- SIMSOPT commit `a79006b0bc1e6df8ab48de284e3457d39a49b995`.

Run `./scripts/bootstrap_macos.sh`. It verifies repository commits and input
hashes after installation. `uv.lock` pins all Python dependencies, including the
resolved SIMSOPT Git commit.

Finite-build and scikit-fem structural diagnostics additionally use the locked
engineering extra:

```bash
uv sync --extra dev --extra engineering
```

This installs Gmsh, meshio, and scikit-fem. DOLFINx and ParaStell are not part of
the qualified Apple ARM environment.

## Known host-specific corrections

On the qualified host, the Command Line Tools directory
`/Library/Developer/CommandLineTools/usr/include/c++/v1` exists but lacks standard
C++ headers. The bootstrap script prepends the complete libc++ directory from the
active macOS SDK during extension compilation.

`mpi4py` requires a separate MPI runtime. OpenMPI is installed through Homebrew.

## Thread policy

Baseline wall times use one numerical-library thread unless an experiment states
otherwise:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 <command>
```

MPI process count and thread environment are part of every comparison record.

## Isolated physics environments

VMEC++, SIMPLE, and NEO-JAX are kept outside the root Python environment so their
dependency solvers cannot replace the augmented-Lagrangian SIMSOPT fork. The
NEO-JAX environment is recreated with `./scripts/bootstrap_neo_jax.sh` and pins
NEO-JAX 1.0.1 plus `booz-xform` 0.1.0 in
`environments/neo-jax/uv.lock`.
# Strict QI data integration

`bash scripts/run_qi_integration.sh` creates the locked core environment,
downloads/verifies and extracts the pinned Goodman archive, and runs five
real-data tests without permitting missing-data skips. For an existing download
cache, set `FUSION_QI_ARCHIVE=/absolute/path/qifiles.zip`; its published checksum
is still checked and data are extracted into the current checkout. The cache is
read-only to this path. Without a cache the download is about 1 GiB.

The tests check nfp=1/2 metadata and independently retrace/integrate all three
vacuum cases at s=0.5, five frozen pitches and sixteen field lines against tracked
v1 action values (relative tolerance 1e-3). They need neither the original
machine's absolute artifact paths nor an installed legacy SciPy tracer. This is
a bounded QI numerical regression, not a fresh VMEC solve or full scientific
qualification. W7-X/native-solver integration remains a separate, expensive gate.
