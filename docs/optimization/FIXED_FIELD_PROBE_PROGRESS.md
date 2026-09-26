# Fixed field comparison: implementation and qualification

26 September 2026. Software qualification passes; **no new proposal fields measured**.
[Scientific protocol](FIXED_FIELD_PROBE_PROTOCOL.md) ·
[Input/method review](FIXED_FIELD_PROBE_REVIEW.md) · [Index](README.md)

## Purpose and boundaries

Test the two newly geometry-certified proposals against their exact immediate
predecessors, before investing in a new optimization run. Four states, six grids
per state, 168 value-only native requests and 804,864 requested points are fixed
in advance. The geometry result is already complete; this document concerns the
new field-comparison software, not a further geometry calculation or design claim.

Implementation qualification and a separate committed execution checkpoint must
precede new fields. Step 4A–4D, physical admission, SoTA and MS1 remain open.

## Implementation

- `scripts/fixed_field_probe_inputs.py`: metadata-only intake rehashes the four
  original states and all completed geometry chains. It independently checks the
  exact predecessor/direction/update/Armijo mapping. Optional current native
  admission reuses the existing archive/environment checker, without replacing
  historical identities or authorizing execution.
- `fixed_field_probe_native.py`: one owned value-only model initialized at the
  original seed, with its exact seven-request schedule. Each state's fresh coarse
  current is frozen for its five refinements. No gradient or optimizer path.
- `fixed_field_probe_audit.py`: independent original-seed flux, metric and sampled
  B/A reconstruction; six diagnostic flux checks, five refinements and two separate
  empirical gain labels. The original strict Armijo decision is reported separately.
- `fixed_field_probe_control.py` and `scripts/run_fixed_field_probe.py`: fixed serial
  pairs, precharged shared storage, durable native events, explicit pipe returns,
  source/checkpoint admission and parent-side identity/coverage checks. Existing
  exclusive JSON/NPZ storage and numerical primitives are reused unchanged.

The parent phase clock includes input/source admission, model startup, all work,
serialization and acknowledgement. The 600 s limit and 605 s hard termination are
unchanged. Group cleanup occurs before reaping the child; on macOS the supervisor
observes exit with kqueue without releasing the owned PID. It checks disk reserve
even while a native call is blocked. No output-file discovery establishes success.

Each pair shares the 512 MiB cap across construction, checking and metadata. Exact
serialized writes are charged before publication, including failed attempts;
64 MiB model and 2 MiB terminal reserves remain. The shared final study index is
conservatively charged in full to each started pair. Logs/control streams are
bounded separately and charged as well. No failed run is resumed or retried.

## Prospective interpretation of negative checks

Recorded before any new field values: a finite, internally consistent measurement
that misses a diagnostic flux or refinement limit remains a **completed negative
measurement**. The saved-data checker retains all six rows and paired deltas;
gain labels remain false when qualification fails. An inconsistent reconstruction,
malformed/missing evidence, native error, changed source, lost callback, resource
failure or late return is an **incomplete/failed operation** and stops that pair's
phase. This distinction changes no threshold, grid, candidate or native budget.
An unfavorable absolute field limit or Armijo result likewise cannot select a
preferred subset of grids. The other pair may proceed only with valid sources and
sufficient disk, without transferring budget.

## Reviews and retained counterexamples

Independent internal agents reviewed intake, the numerical composition, the
native bridge and the process/return layer. This is internal review, not external
peer review. Corrections found before fields include:

- Missing/wrong coarse construction and inconsistent frozen flux metadata.
- Backward timestamps between native requests; both bridge and stored-event
  replay must reject them.
- Individually valid paired reports with different original seed/source identities.
- Parent acknowledgement of an empty or insufficiently bound result envelope.
- Descendants retaining pipes after leader exit, live disk loss during a blocked
  call, and parent publication failures that previously cancelled the second pair.
- Omitted pair-index byte charges and qualification records without distinct
  named evidence roles.

Initial failing controls remain under `artifacts/fixed-field-probe-v1/` and
`artifacts/local-curvature-v1/`. Qualification will bind exact files/hashes rather
than reinterpret an old test record as evidence for changed code. Synthetic tests
do not establish real field improvements or native environment compatibility.

## Current verification

All 544 focused tests pass (78.38 s): native bridge 120, intake 86, numerical checker
73, work/resource controls 130, process supervisor 21, runner integration 38 and
independently authored return-envelope controls 76. Actual metadata intake also
passes with scientific imports blocked. Public tests pass 47/47 (3.243 s);
documentation/release tests pass 16/16 (15.26 s); repository Ruff, documentation
structure and whitespace checks pass. Commands, console output and JUnit remain
under `artifacts/fixed-field-probe-v1/implementation-checks/`.

The complete research suite passes **5,654 tests**, 334 warnings and zero failures,
errors or skips at clean implementation `b10c47f67bd73daf73e1cf654413f47df6f3b911`.
Console duration is 466.15 s; wrapper duration 466.910 s. Before/after Git identities
match and remain clean. Console and JUnit are retained under `full-regression/`.
The [qualification record](../../evidence/fixed-field-probe-qualification-v1.json)
binds 540 source/configuration/protocol references and 45 artifacts, including
distinct evidence for focused, public, documentation, full-regression and review
checks. Prior failing controls and intermediate reviews are retained.

A separate committed execution checkpoint and fresh native admission still precede
new fields. No native environment sync or new native fields occurred.
The existing NumPy/netCDF import warning is retained, not silenced or repaired by
changing the native environment during this study.
