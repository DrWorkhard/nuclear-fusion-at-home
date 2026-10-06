# One bounded coil-freedom comparison

Full local evidence for issue #53. The clean producer/evaluator is
`fd99245147308b9dbd23473002968e3283bd08fe`; the archive commit adds evidence only.
The prospective protocol is retained at `docs/optimization/ISSUE53_COIL_FREEDOM.md`
in this checkout. No publication or physical acceptance is implied by this local archive.

## Result and limits

Both arms completed. Order 8 lowers fine boundary RMS from 0.00183501529 to
0.00176571369: P/C = 0.9622337751, a 3.78% improvement, missing the registered
50% hurdle. Finest interior RMS improves from 0.0101035400 to 0.00948113791.
Geometry passes and all ten lines complete 200 turns with the declared signed-iota
tolerance in each arm. The frozen resource-allocation rule selects **joint
plasma/coil optimization next**. Both boundary RMS and maximum gates still fail.

This is one seed and one local search per arm, not a causal test of the ultimate
coil family or a global optimum. The launcher enforces monotonic clocks: search
1800 s including intake/startup, then at most 900 s shared diagnostics. Recorded
wall timestamps show much longer intervals in both arms; suspension or clock
adjustment could explain them, but the cause is unknown. External host idleness
could not be verified. Do not claim controlled elapsed-wall-time throughput or
verified exclusive-host execution. Agent-controlled heavy jobs were kept serial.
See `observer-notes.txt` and the unchanged provenance timestamps.

These target-labelled starts do not establish nested surfaces, equivalent realized
flux labels, plasma-benefit transfer or physical acceptance. `summary.json` retains
the metrics, geometry bounds, selection, timing and exact decision; `summarize.py`
is its post-run reduction, not the scientific producer.

## Contents and identity

`run/` is a byte-preserved copy of the complete local run, including successful,
failed and attempted trials, selected snapshots, native diagnostics, Poincare
crossings, logs, resource reports and source dictionaries. `original-snapshot.json`
is the frozen seed. `manifest.json` hashes every other file in this evidence folder;
its own SHA256 is bound by the immutable annotated tag. Original local output remains
at `artifacts/issue53-coil-freedom-v1/`; no raw output or environment was removed.

Seed SHA256: `84bbdf3eca274981dfff80c967b6fd623a1a40350e583407cbb7262c26820217`.
Original Wout SHA256: `83dc45b911a1e8290c3e97c7e28d4de28fcff6021b93d55df2f91d6dd3751c5e`.
The Wout remains maintainer-local at `artifacts/plasma-design-v2/reference-fine/wout.nc`
and is not distributed here. A regenerated Wout is not this original byte identity.
Project code is MIT; Goodman-derived reference data retain CC BY 4.0 attribution:
Alan Goodman, *Constructing Precisely Quasi-Isodynamic Magnetic Fields*,
https://doi.org/10.5281/zenodo.7220257.

## Reproduce without original Wouts

With Python 3.12+, NumPy and SciPy, from the archive checkout:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 MKL_NUM_THREADS=1 \
  python -I -B evidence/issue53-coil-freedom-v1/replay.py --manifest-sha SHA256_FROM_TAG_ANNOTATION
```

The replay verifies all archive bytes and retained producer source files, identical
zero-extended starts, both fine boundary grids and all three interior levels per arm,
sampled independent filament B/A against native samples, and saved line summaries. It compares
numerics at rtol 1e-12 / atol 1e-14. It needs neither SIMSOPT nor Wouts. It does not
rerun optimization, geometry reconstruction or tracing, and is not external physics review.

For a fresh native study, explicitly fetch the producer with `git fetch --depth 1
--no-tags origin fd99245147308b9dbd23473002968e3283bd08fe`, use a separate clean
worktree at that revision and its documented native environment, and run:

```bash
python scripts/run_coil_freedom.py \
  --snapshot /path/to/original-snapshot.json --wout /path/to/original-wout.nc \
  --output /path/to/fresh-output \
  --revision fd99245147308b9dbd23473002968e3283bd08fe
```

The retained `study.json` and arm supervisor reports record the actual original
paths, commands, serial wrapper, environment choices and source/input hashes.
Timed optimization need not reproduce the exact selected coefficients. This recipe
is for reproduction, not a plan to rerun the registered probe to cross its threshold.
