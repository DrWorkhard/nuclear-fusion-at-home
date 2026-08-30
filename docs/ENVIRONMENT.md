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
