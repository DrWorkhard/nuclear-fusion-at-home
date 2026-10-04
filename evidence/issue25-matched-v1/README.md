# Issue #25: matched original/improved target experiment

Producer/evaluator: `a551289e63e44d7dbae7b5d5a0e5f4b6026db257`, clean tree.
The committed prospective rules are in `docs/optimization/ISSUE25_MATCHED_TARGETS.md`
at that revision. Both sequential arms used the same starting coil geometry,
300 s fitting budgets, frozen target-specific flux/B², and unchanged checks.
`summary.json` holds the scoped conclusion; `commands.json` records actual calls.

**No full benefit-transfer result:** both wide action domains are incomplete at
q=0.03. The reference fails s=0.1/0.25; the improved target also fails s=0.75.
The narrow target-launch diagnostic is 5.07% lower for the improved arm, but neither
arm passes field acceptance or has verified realized flux labels. No selective
wide score or preregistered conditional refinement is reported. Both direct traces
complete 200 transits for 10/10 starts; this is not a nested-surface proof.

## Files and reproduction

All original local study outputs are retained byte-for-byte, including failed
terminal fitting calls, arrays, logs and source hashes. `manifest.json` binds
those files and the summary. Its JSON uses relative archive paths. The two short
post-run control scripts retain their actual local paths and commands.

For a portable numerical replay, with NumPy and SciPy available, run from this
archive checkout:

```bash
python evidence/issue25-matched-v1/replay.py
```

This verifies the archive manifest and recomputes both fine boundary grids, all
interior scores and every ideal/coil action cell and failure from the saved
arrays. It does not rerun native field calculations, geometry bounds, optimization
or field-line integration, and is not independent physical confirmation.

A full native replay requires the preserved environment described in
`docs/validation/ENVIRONMENT.md` and the original reference/selected Wouts with
SHA256 `83dc45b911a1e8290c3e97c7e28d4de28fcff6021b93d55df2f91d6dd3751c5e` and
`8cd6bebfc29963f80645acf25e1a3db194e4db381365b17a89b9844554f51b52`.
They, and the original validation archives used by the control scripts, remain
**maintainer-local and are not distributed here**. Input JSONs are committed;
regenerating a selected Wout is not yet an accepted replacement for its exact
archived identity. No separate-machine native reproduction is claimed.

`reproduce-local.py` and `commands.json` record the actual paths used. Relocate
those explicitly for a native replay; do not expect the historical temporary
checkout path to exist. Start with a fresh output directory. Wall-clock fits may
select different candidates on another machine; the frozen candidates and arrays
permit exact diagnostic replay independent of that search variability.

## Attribution and limits

Underlying target: Alan Goodman, *Data for paper “Constructing Precisely
Quasi-Isodynamic Magnetic Fields”*, DOI:10.5281/zenodo.7220257, CC BY 4.0.
The selected target is the project's modified Step 3 boundary; archived arrays
are derived calculations. Preserve this attribution and the project's existing
`NOTICE.md`/starter data credits. Project source code is MIT-licensed.

Ideal controls and dense target reconstruction reproduce the qualified archived
arrays exactly; these are same-machine controls. Native B/A arithmetic is checked
by the existing independent implementation. Geometry uses padded floating point,
not interval proofs or finite-build qualification. Launch coordinates are target
labels, not demonstrated realized flux coordinates. Field-line survival does not
establish particle/energy confinement. The MPI runtime emitted a sandbox socket
warning; all single-process calculations completed. No original Wout, environment
or prior raw run was modified.
