# Active research environment

The public starter requires only Python 3.11+. Its commands do not install or
import the native research stack. [Quickstart](PUBLIC_QUICKSTART.md).

The active fitter uses Python 3.12 with NumPy, SciPy and SIMSOPT, plus the
recorded target/coil artifacts. The existing native environment also contains
historical dependencies such as netCDF4. Keep that environment intact.
Do not run `uv sync` in it to test a dev-only CI configuration; use a disposable
checkout. This cleanup performs no package installation or environment repair.

```bash
.venv/bin/python -m pytest -q
.venv/bin/python scripts/test_public.py
.venv/bin/python scripts/check_docs.py
```

Native field evaluations use one thread:

```bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 MKL_NUM_THREADS=1
```

Retain an initial 3 GiB and live 2 GiB disk reserve for the recorded studies.
Use a fresh output directory and finite wall-clock/storage bounds.

## Portable native setup

The fitter needs the SIMSOPT fork recorded in the historical lockfile:
`PedroFranciscoGil/simsopt@a79006b0bc1e6df8ab48de284e3457d39a49b995`, branch
`auglag_coils`. Its `SquaredFlux(threshold=...)` is required. PyPI SIMSOPT 1.11.1
fails with `unexpected keyword argument 'threshold'`. A disposable environment
works outside the maintainer's workspace:

```bash
uv venv --python 3.12 .native && uv pip install --python .native/bin/python numpy scipy netCDF4 \
  "simsopt @ git+https://github.com/PedroFranciscoGil/simsopt.git@a79006b0bc1e6df8ab48de284e3457d39a49b995"
```

Regenerating the reference401 Wout needs `vmecpp`. Install it in a separate
environment, because vmecpp 0.8 requires SIMSOPT ≥1.8.1 while the fork reports a
development version. With a Wout, `fit_coils.py --wout` and `check_coils.py --wout`
rebuild the interior target and accept it only if it reproduces the public starter.
See the [active research](../optimization/README.md#portable-checks) instructions.

Historical builds, platform patches, VMEC/particle/engineering recipes and exact
versions resolve at the [freeze tag](REPRODUCING_RESULTS.md), together with each
report's recorded source/environment identities. A current editable checkout
does not make old absolute artifact paths portable.

The root package has no runtime dependencies. Its eight-package lockfile covers
the package and development checks only. Unused
`benchmark` and `engineering` extras have been removed; installing the core package
does not install SIMSOPT or qualify a native research environment. The recorded
native stack remains separately managed and unchanged. Inactive VMEC++/NEO-JAX
manifests are available from their historical revisions; their installed local
environments have not been removed.
