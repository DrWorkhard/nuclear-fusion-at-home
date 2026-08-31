# Validation log

## 2026-08-30 — Core repository

- `uv sync --python 3.12 --extra dev`: succeeded.
- `pytest`: 5/5 initial project tests passed; expanded suite pending rerun.
- `ruff check`: passed before benchmark integration.
- SQuID-C template: structure-only validation passed.

## 2026-08-30 — Native SIMSOPT

- First compilation: failed, missing C++ standard headers due to Command Line
  Tools/SDK search ordering.
- Compilation with SDK libc++ include path: succeeded.
- `mpi4py` import before MPI runtime: failed, no `libmpi`.
- OpenMPI 5.0.10 install: succeeded.
- Upstream `test_biotsavart.py` and `test_curve_objectives.py`: 31 tests and 86
  subtests passed in 30.88 s.
- Direct circular-coil Biot-Savart smoke evaluation: finite field values on ARM.

## 2026-08-30 — StellCoilBench inputs

- `basic_LandremanPaulQA.yaml`: validation passed.
- `basic_W7X.yaml`: validation passed.
- Repository commit and four case/surface SHA-256 values are enforced by
  `fusion-baselines verify-stellcoilbench`.

## 2026-08-30 — Landreman-Paul QA baseline

- Original `run-case`: optimization completed; post-processing failed because the
  output directory lacked its case YAML.
- Self-contained wrapper: optimization and BdotN post-processing completed.
- Two runs: scientific metrics and evaluation counts bit-identical; wall times
  160.55 s and 158.60 s.
- Built-in Taylor test: passed in both runs.
- Hard reactor feasibility: passed.
- Separate post-processing average normalized BdotN differed by 1.14%.
- Output hashes for accepted repeat:
  - results JSON: `462de6605e82f47d26715fd96fd6f7bafb75b92d1fbc97cc239a712850599a8f`;
  - serialized optimized field/coils: `8ab07eec66e378c09a6f0ca3deb8305f0e1c7fc35fefcdc980cbf2bb3b44a323`;
  - run log: `fcbcd50ef1492a00b8db107093987c62bfc3d2d565cdec73fdd76a540ee98c28`.

## 2026-08-30 — W7-X baselines

- Two complete StellCoilBench runs: scientific metrics and evaluation counts are
  bit-identical after removing timestamps, paths and timing records.
- StellCoilBench Fourier order 4: converged after 523 iterations.
- Fourier order 8: stopped at the declared 1,000-iteration budget; result retained
  as a budgeted baseline, not relabelled as optimizer convergence.
- Independent normalized BdotN differs from the optimizer report by 1.40 %.
- VMEC++ 0.7.3 force residuals met the requested tolerance on the exact W7-X
  input.
- Current Proxima fixed-boundary tolerance comparison: 47/59 variables passed.
- Protected global metrics agree closely; the full V&V gate remains failed.
- Independent Fourier audit: lengths agree to floating-point precision.
- Independent resolution audit: 200-point curvature is 0.54 % low and 200-point
  coil-coil clearance is 0.58 % high relative to the refined samples.

## 2026-08-30 — Open QI bridge

- Published archive MD5: passed.
- Full ZIP CRC: passed.
- Manifest file hashes for nfp=1: passed.
- VMEC++ nfp=1,2,3 force-residual convergence: passed.
- Cross-code comparisons against the 2022 Fortran wout: 23/59, 40/59 and 31/59
  variables passed current Proxima tolerances; full comparisons failed.
- Published QI residual at edge: finite for all three cases; legacy spline warnings
  recorded.
- Published J routine: finite at all sampled surfaces and bounce fields. Vacuum
  maximum-J fractions are 0.0, 0.0 and 0.1, consistent with the paper's
  minimum-J-in-vacuum statement.
- Doubling the radial/bounce grids and increasing the field-line grid preserved
  the maximum-J conclusion (0.0, 0.0 and 0.0921).
- Published QI objective resolution study: failed convergence; values were
  strongly non-monotone (`1.3850e-5`, `2.5725e-5`, `1.8097e-5`).
- Published NEO/SIMPLE outputs: generic ingestion and plotting-semantics
  reproduction passed; local solver reruns remain pending.
- VMEC++ nfp=2 repeat: both force-residual converged; aspect and volume identical,
  axis iota differed by `2.70e-8`, and NetCDF hashes differed.

## 2026-08-30 — Independent LPQA geometry holdout

- Direct Fourier lengths agree with the optimizer to floating-point precision.
- Refined coil-coil clearance is 1.40% smaller than the 200-point value.
- Refined maximum curvature is 0.055% larger than the 200-point value.
- The independent 512-by-512 surface sample gives a 0.39% smaller coil-surface
  clearance than the optimizer report.

## 2026-08-30 — Manufacturing sensitivity

- First LPQA screen: rejected after completion because the upstream sensitivity
  YAML lookup used `0` instead of the effective recorded squared-flux threshold
  `1e-8`.
- First W7-X screen: stopped before acceptance for the same reason.
- Corrected wrapper reads the effective threshold from the immutable run result
  and records both value and source.
- Canonical LPQA run: endpoints bracketed the factor-two crossing; reactor-scale
  `sigma*=9.066 mm` from 100 samples per amplitude.
- Canonical W7-X run: endpoints bracketed the factor-two crossing; reactor-scale
  `sigma*=20.372 mm` from 100 samples per amplitude.
- Both remain screening statistics; 1,000-sample holdout and seed sensitivity are
  required before an optimization claim.

## 2026-08-30 — SIMPLE fast-particle solver

- SIMPLE commit `9269e8614e581ede8768e0bccb003b52db87e3be` and libneo commit
  `66ef89c2b59420bb8fbd14aa0838d5e88082bef8` pinned.
- First deterministic configuration: failed because AppleClang could not find a
  C OpenMP runtime although GNU Fortran OpenMP was present.
- Remediation: add Homebrew `libomp` and its CMake prefix; rebuild pending.
- Second configuration exposed the same missing explicit flags for C++, after C
  was resolved; bootstrap now supplies both AppleClang C and C++ OpenMP flags.
- Third configuration succeeded and compiled 530 targets before a C test helper
  failed to find Homebrew's keg-local `netcdf.h`; the bootstrap now passes the
  exact NetCDF-C include directory to CMake.
- The subsequent incremental build reached the same helper's link step but lacked
  the keg-local NetCDF library search path; the exact library directory is now
  supplied as an executable-linker flag.
- Final deterministic build: succeeded. Seven upstream tests carrying the
  `smoke` label passed in 3.59 s.
- Goodman nfp=1 SIMPLE smoke: two runs produced identical confined-fraction
  hashes; 128/128 particles resolved, zero loss at 0.01 s.
- Scope limit: published 5,000-particle, 0.2 s production result not yet rerun.

## 2026-08-30 — Engineering feasibility screens

- Independent audits completed for five order-4 LPQA candidates.
- The first two candidates cross the refined coil-coil bound despite passing at
  optimization resolution.
- A 40 mm reactor-scale optimization buffer makes the original 1.0605 m physical
  clearance pass in the later candidates.
- No candidate passes every acceptance condition; all exceed the squared-flux
  cut-in and the augmented-Lagrangian candidates retain additional violations.
- The longest augmented-Lagrangian run used 1,665 recorded inner evaluations,
  hit the outer cap, and failed refined curvature by `3.6e-5 1/m`.
- Stock augmented-Lagrangian success and evaluation-count fields failed semantic
  validation and are excluded from scientific acceptance.

## 2026-08-30 — NEO-JAX neoclassical path

- NEO-JAX 1.0.1 and `booz_xform` 0.1.0 installed in a separate lockfile.
- Published nfp=1 wout transformed on 16 radial half-grid surfaces; all local
  effective-ripple solves completed without approximate rational fallback.
- Published cross-check failed: median calculated/reference ratio 3.27 and
  maximum relative error 797% at default settings.
- A single-surface resolution study approached `7.77e-6`, still 3.26 times the
  published `2.38e-6` value.
- Scope limit: the release lacks the original radial Boozer file and NEO control
  deck; solver execution is checked, paper reproduction is not.

## 2026-08-30 — W7-X-target coil-field regression

- Two interpolated and two direct Biot-Savart tracing repeats are bit-identical
  within their respective fidelity paths.
- Six of six sampled lines remain unterminated through `tmax=2000`, with at least
  130 hits on each of four sections per field period.
- Interpolated and direct hit counts are identical; section extents agree within
  4.72 mm at worst.
- Scope limit: this checks the optimized StellCoilBench filament field targeting
  the W7-X boundary, not surveyed/as-built W7-X coil geometry.

## 2026-08-31 — Finite-build and structural path

- Added and locked `gmsh 4.15.2`, `meshio 5.3.5`, and `scikit-fem 12.0.2` in
  the engineering extra.
- Selected upstream finite-build/structural tests: 45 passed, 1 skipped.
- Stock Gmsh sweep on the real LPQA v1.1 candidate: zero of four coils meshed;
  both through-sections and STL recovery failed on invalid boundary geometry.
- Independent structured-sweep series: six resolutions, 2,622 to 327,000
  tetrahedra; four physical tags and no degenerate tetrahedra at every level.
- Finest mesh volume error against exact centerline-length times area: 0.0290%;
  finest-step volume change: 0.00990%.
- Primary structural convergence (`0.03 -> 0.02 m`): failed all four predeclared
  10% thresholds.
- Diagnostic extension (`0.015 -> 0.010 m`): passed all four 10% thresholds;
  finest repeat metrics were bit-identical.
- Scope limit: the scikit-fem support is a fixed lower-z region, not the labelled
  spring foundation, and the approximately 0.978 m displacement invalidates
  small-deformation linear elasticity as an absolute engineering model.

## 2026-08-31 — Free-boundary holdout

- Frozen a no-writeback validation protocol before execution.
- Exported 4 unique / 16 physical LPQA coils to one MAKEGRID current circuit;
  source and generated-file hashes recorded.
- Independent vector-potential loop integral: `phiedge=0.0783837406 Wb`.
- VMEC++ fixed-boundary and free-boundary vacuum runs both met `1e-9` residual
  tolerances at `mpol=ntor=6`, `ns=[8,16,31]`.
- Standard response grid: all predeclared volume, axis, and cross-section
  comparisons passed.
- `101 -> 151` R/Z response-grid refinement: all predeclared sensitivity bounds
  passed; largest relative core-metric change was 0.0956% for axis iota.
- Scope limit: the candidate is magnetically infeasible by the earlier cut-in;
  finite-beta/current, VMEC-resolution, topology, and independent-solver
  holdouts remain required before a physics/design claim.

## 2026-08-31 — Generic equilibrium intake

- Added a case-independent manifest-to-VMEC/Boozer summary path and CLI.
- Core test creates an unknown synthetic configuration; no case-id dispatch is
  required. Full core suite: 9 passed.
- Goodman nfp=1 real-data intake: all five declared equilibrium fields matched;
  VMEC and Boozer summaries finite.
- Added Goodman nfp=2 only as a new manifest and ran the identical command; all
  declared fields matched without code changes.

## 2026-08-31 — SQuID-C public-data availability

- Publisher metadata: empty supplementary-material list.
- Crossref: zero article relations.
- Zenodo: zero exact results for name, DOI, and full article title.
- DataCite: zero results for related DOI and full article title.
- Proxima Fusion GitHub: nine public repositories, 4,035 paths, no truncated
  trees, zero SQuID-C path-name matches.
- Proxima Fusion Hugging Face: four datasets, 7,668 fully paginated paths at
  recorded revisions, zero SQuID-C path-name matches.
- CoilStellaration results schema: 179 fields, no paper/DOI/citation/source/name
  field; its opaque boundary IDs cannot establish authoritative identity.
- Repeated end-to-end audit after fixing URL path encoding: passed and wrote
  `evidence/squid-c-availability-audit-2026-08-31.json`.
- Scope limit: GitHub blob contents and multi-gigabyte Hugging Face row payloads
  were not exhaustively searched. The result is “no publicly identified package
  located”, not proof of universal non-existence.

## 2026-08-31 — Version-compatible W7-X equilibrium V&V

- Built STELLOPT `v251`/VMEC 8.52 at commit `e59aff...` with the upstream
  validation patches and recorded Apple Silicon build patch.
- Native reference run terminated normally after 2,922.57 solver seconds;
  binary, input, log, wout, auxiliary outputs, toolchain, and libraries hashed.
- VMEC++ and VMEC 8.52 both reached the requested `1e-12` residual level at
  `ns=201`, `mpol=10`, `ntor=10`.
- Project-protected geometry, aspect, beta, iota, and B metrics: passed.
- Real-space upstream grid and independent doubled-resolution holdout: passed.
- Full fixed-boundary wout comparison: failed, 56/59 fields passed.
- The prior broad `bsubsmns` discrepancy against VMEC 9.0 disappears in the
  matched 8.52 comparison.
- Remaining exceptions: axis-only `chipf` output and two micro-pascal-scale
  pressure-profile differences; all are retained in machine-readable evidence.

## 2026-08-31 — SQuID-C schema-2 dry run

- Audited schema 1 and found it admitted a nominal SQuID-C case with one VMEC
  artifact despite the stronger prose contract.
- Added mandatory distinct fixed/free-boundary inputs and outputs, profiles,
  coils, currents, MGRID recipe, solver controls, and metadata.
- Added bytes/SHA-256/origin or derivation-parent/recipe validation.
- Added scale, conventions, source authority/license/time, and symmetry checks.
- Complete ten-role synthetic package: passed and both wouts reached generic intake.
- Negative tests for missing MGRID, wrong byte count, undeclared lineage parent,
  and the unfilled template: passed by rejecting each invalid package.
- Full core suite: 13 passed.

## 2026-08-31 — Locked core CI

- Replaced moving major action tags with exact commits corresponding to
  `actions/checkout v4.4.0` and `astral-sh/setup-uv v7.6.0`.
- CI runner fixed to Ubuntu 24.04 with read-only contents permission and timeout.
- Environment synchronization now rejects lock drift via `uv sync --locked`.
- Workflow and local execution use the same `scripts/run_core_ci.sh` entry point.
- Exact local execution: Ruff passed and 13 tests passed.
- First fresh-clone holdout: failed before tests because `uv` tried to resolve the
  absent optional `external/stellcoilbench` path; the original local pass had
  been conditioned on that ignored checkout.
- First attempted remediation (`--no-install-local`): failed because lock
  validation still required metadata from the absent path source.
- Final remediation: the optional package source now uses StellCoilBench's exact
  Git commit in the lock. Its separate local checkout remains independently
  pinned for source/data audits, but is no longer required to install core CI.
- Second fresh-clone holdout with no `external/` tree or pre-existing virtual
  environment: Ruff and all 13 tests passed; the clone remained clean.
- Scope limit: no Git remote is configured, so no remote-hosted run URL or runner
  log can yet be recorded.
