# Protected pilot: launch-connection qualification

26 September 2026. [Registration](PROTECTED_PILOT_EXECUTION_PROTOCOL.md) ·
[Saved-physics qualification](PROTECTED_PHYSICS_RESULTS.md) · [Index](README.md)

## Current result

The source-bound serial launcher is qualified at `6bb1e45`: **124 synthetic tests
and all 3,487 full-regression tests pass**. Independent internal review has no
remaining blocker within this software scope. The separate
[qualification](../../evidence/protected-pilot-launcher-v1.json) and
[execution checkpoint](../../evidence/protected-pilot-execution-v1.json) bind the
actual sources and evidence. Runtime source-only admission must still pass from
their clean committed checkout before the original eight-case diagnostic pilot.
No new native coil search has run at this qualification checkpoint.

The source gate requires the complete previous source/qualification graph, exact
committed launcher code and a clean repository. The fixed execution-checkpoint
file must match those exact sources, link a separately committed successful
launcher-qualification record and retain all diagnostic-only scope limits.
Neither a physics qualification nor a source commit alone opens execution.

## What the launcher connects

`run_protected_coil_fit.run` runs the original eight cases in order with the
qualified supervisor, explicit native adapter and full graph audit. It consumes
only successfully returned parent acknowledgements, then separately times and
checks the independently returned saved-physics reports. Source/case/context,
control-frame clocks, PID/thread identities, cell references and work counts
must agree. The separate fine phase is explicitly `required-not-run`.

Every completed case retains objective/normal-RMS/normal-max/inner-vector changes
without asserting physical admission, resolved fine-grid improvement, Pareto
dominance, Step 4, SoTA or MS1. The conservative failure policy stops the entire
study on any raised execution/audit/source/resource/publication error, retains
prior returned references and records later cases as unexecuted. No retry, tail
discovery, hidden work or budget transfer.

## Tests and internal review

- Initial source/launcher controls: 120 pass. After one real synthetic subprocess
  linkage: 123 pass. With committed physical qualification pins: 124 pass (1.63 s).
- Independent final rerun: 124 pass, zero failures/errors/skips, 1.53 s console /
  1.522 s JUnit. Four source/test hashes unchanged; no blocking finding remains
  within the software scope. Ruff and whitespace pass.
- Complete regression at clean `6bb1e45`: 3,487 pass, 334 existing warnings,
  zero failures/errors/skips, exit zero; 288.37 s console / 288.153 s JUnit.
  No test paths excluded; all tracked sources unchanged throughout the run.
- Eight-case ordering is tested with explicit mocks. One case additionally uses
  the real qualified parent, worker and saved-graph auditor with the existing
  nonphysical synthetic adapter; a deliberate failure prevents a second launch.
  These tests never calculate a new native field or producer certificate.
- Review caught a missing machine-enforced launcher/checkpoint gate after physics
  pinning, and acceptance of a dirty checkout. Both now have explicit rejection
  controls. The dirty-admission pre-fix probe was a small independently run
  synthetic reproduction, not a retained failing JUnit; do not relabel later
  green tests as red evidence. The first temporary-path probe itself failed due
  to a `/var` versus `/private/var` fixture alias, before the corrected reproduction.
- Review also strengthened exact source/control/acknowledgement/physics linkage,
  forward clocks, scope limits and non-symlink committed checkpoint identities.
  Seven initial Ruff findings in the maintainer prototype were fixed before tests.

Artifacts remain under `artifacts/protected-pilot-v1/`. Maintainer prototyping,
implementation/testing by `protected_runner_map` and review by
`cell_integration_review` are internal work, not external peer review.

## Subsequent execution

The checkpoint at `2015ac5` led to completed clean-source admission and all eight
[native constructions/coarse audits](PROTECTED_COIL_FIT_RESULTS.md).
The separate [fine validation](PROTECTED_FINE_RESULTS.md) is also complete:
numerical and geometry checks pass, physical field limits fail. This launcher
report establishes software qualification, not Step 4A–4D completion. Current
priorities are in the [research programme](STEP4_RESEARCH_PROGRAMME.md).
