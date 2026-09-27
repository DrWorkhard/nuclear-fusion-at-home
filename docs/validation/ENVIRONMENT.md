# Active research environment

The public starter requires only Python 3.11+. Its commands do not install or
import the native research stack. [Quickstart](PUBLIC_QUICKSTART.md).

The existing native environment uses Python 3.12 with NumPy, SciPy, SIMSOPT and
netCDF4, plus the recorded target/coil artifacts. Keep that environment intact.
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

The optional engineering dependency declarations remain locked for compatibility:
offline lock regeneration was blocked by the approval service's usage limit.
Their implementation is retired, and nothing was installed. Do not present those
optional packages as an active engineering qualification.
