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
