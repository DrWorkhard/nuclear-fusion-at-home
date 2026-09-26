# Protected pilot: launch-connection qualification

26 September 2026. [Registration](PROTECTED_PILOT_EXECUTION_PROTOCOL.md) ·
[Saved-physics qualification](PROTECTED_PHYSICS_RESULTS.md) · [Index](README.md)

## Current result

The source-bound serial launcher is implemented and independently reviewed;
**124 synthetic tests pass**. Full committed-source regression and the separate
execution checkpoint are next. **Native launch remains closed**: real physics
qualification pins are present, but the required committed execution checkpoint
does not yet exist. No native coil search has run.

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

## After qualification

Freeze the complete clean checkout, bind actual qualification and execution
records, perform source-only admission, then run the original diagnostic pilot.
Do not edit tracked sources/docs while it is running; retain intermediate notes
in ignored artifacts and integrate them after source-bound execution ends.
Fine acceptance needs its separate candidate-aware contracts and supervisor;
see the [read-only integration notes](PROTECTED_FINE_DESIGN_NOTES.md).
Completing the pilot alone does not complete Step 4A–4D.
