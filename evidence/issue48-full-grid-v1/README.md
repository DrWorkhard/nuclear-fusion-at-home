# Full nominal grid: a selected-fit mid-radius coverage failure

The single fixed pair completed all 40 traces and diagnostics. Reference401
qualifies at 20/20 launch points; selected401 at 18/20. The complete paired map
is unqualified. Selected nominal s=0.50, theta=pi/2 has nonpositive spline-radius
failures at 320/640 pooled crossings; theta=3pi/2 has a 1.1793 rad final angular gap
(limit 0.4) and 0.0040333 last-prefix label change (limit 0.0005). These failures
are retained, without retries or qualified aggregate statistics for that surface.
All other surfaces qualify under this numerical method. Their maximum nominal
label offsets reach 0.068137 (reference) and 0.074883 (selected), both at s=0.90.

Clean producer/evaluator: 130347fe29e03852e257a63d0ce6ab9f828d2c85. The prospective
protocol is docs/optimization/ISSUE48_FULL_GRID.md in this archive's parent.
Code, protocol and the exact local launcher received read-only adversarial agent
review before execution. Fresh shallow producer checks passed 308 native and
61 public tests, docs, Ruff and whitespace checks (eight existing deprecation
warnings). Agent review is not external physics review.

Reference/selected drivers took 979.47/972.46 s and supervision 989.71/983.17 s,
within fixed 1800/1860 s per-arm limits. One native thread, 256 MiB per-arm output,
and 3/2 GiB initial/live disk reserves were enforced. Each arm retained about
58.55 MB; UTC and monotonic durations agree within 0.001 s. External host load
remains unverified; no controlled throughput claim follows. All 103 original raw
files (117104041 bytes) are copied byte-for-byte; their original home remains
artifacts/issue48-full-grid-v1 in the maintainer workspace. Source/input hashes
are unchanged before/after both runs. No original matching verdict is revised.

## Inputs and reproduction

The payload includes both frozen issue25 snapshots and target input JSON files.
Their hashes and original Wout locations/hashes are recorded in each arm's
run/result.json. The two original Wouts remain maintainer-local and are not
redistributed; regenerated Wouts are not interchangeable. Source, frozen coils,
currents, targets, all attempts, failed estimates, trajectories and controls are
bound by the recorded identities. The full native command is in run-local.py and
each supervisor result; relocate its paths explicitly rather than treating them
as portable. supervisor.py is the unchanged reviewed implementation from archive
293d0a65601c8293c936617f720fcfe099b3a27f. Each native command requires the original
Wout, snapshot and target JSON with --full-grid --half-period --crossings 320
--seconds 1800; use a new output directory and the preserved native environment.

Saved-array replay requires only NumPy/SciPy and this shallow archive checkout:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 MKL_NUM_THREADS=1 \
  python evidence/issue48-full-grid-v1/replay.py --manifest-sha SHA_FROM_TAG_ANNOTATION
```

The replay verifies manifest and original source identities, then recomputes
final-prefix/subset A flux, gaps and held-out radial residuals wherever recorded
estimates exist, plus dense/sample target-control A flux. It checks earlier-prefix
and separate-plane saved-flux arithmetic and all qualification arithmetic. It
retains the final failed prefix in its skipped-error list; it does not replace it
with a passing estimate. Its fixed elapsed budget is 900 s. Native B-fan values,
trajectories and target geometry are hashed, not recomputed. Subset order-4 values
were not individually saved: the replay compares their derived order changes.
This is post-run numerical verification, not a new confirmatory experiment.

summarize.py produces summary.json. plot_midradius.py (optional Matplotlib)
produces midradius-sections.png directly from saved crossings and target contours.
This exploratory plot illustrates the gaps; it does not identify their dynamical
cause or prove magnetic islands. Geometric theta is not PEST alpha; numerical
qualification does not prove nestedness, confinement, common action coordinates,
continuum-filament accuracy or physical acceptance. No plasma-benefit claim follows.

Code is MIT. Target-derived contours retain Goodman et al. CC BY 4.0 attribution,
DOI 10.5281/zenodo.7220257; upstream notices remain applicable. This archive and
its evidence tag are local pending publication. Original evidence is preserved.
