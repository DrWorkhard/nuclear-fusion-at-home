# Joint comparison integration

Implementation of the [frozen feasibility protocol](ISSUE37_JOINT_FEASIBILITY.md).
The numerical components and assembled adapter have been reviewed and tested.
The [first native attempt](ISSUE37_JOINT_RESULT.md) completed its control but was
interrupted by clock disagreement during the first J solve. No new search basis,
metric or acceptance limit was introduced; the paired scientific question remains
unanswered. Further execution requires separately registered conditions and review.

`joint_decision` provides the trusted driver's selection and decision rules.
Both proposals must terminate, in fixed plus/minus order. Select on complete
training action variance, then selected inner objective, then proposal index.
A normal fit cap can retain an earlier completed eligible candidate only after
passing startup. The parent must establish that the stop was its declared fit
cap; a generic timeout or interrupted whole arm is insufficient. A probe cannot
win. Explicit numerical rejection requires a documented size, equilibrium or
complete plasma-domain failure; unclassified errors are software failures.
The rejection handoff includes the exact proposal/input identity, completed
resource state and failed numerical result. Check converged volume quadratures
against the size limit, force residuals/status against the equilibrium gate, or
the full ineligible action report with every failed phase. Failed action records
now retain angular well bounds as well as length bounds, so a claimed period
crossing can be checked explicitly. Nonempty prose or
contradictory success evidence is insufficient; receipt provenance remains the
parent's responsibility.

Freeze the chosen input/Wout hashes, target identity, coil coefficients,
normalized currents and selected trial index before any held-out evaluation.
`freeze_selection` checks the named snapshot and fit row, binds the source files,
saves a canonical selection hash and refuses a second selection in the same cell.
The native parent rechecks source/receipt hashes and this frozen state
before and after diagnostics; helpers are not a verifier for candidate-supplied
completion flags or arbitrary JSON reports.

Use the maximum fine-boundary RMS and finest 64/512 interior RMS; keep both fine
maxima and all coarser levels. Require the registered action domains and both
refinements, recomputing cell scores from their full phase/family arrays. Frozen
current, independent field controls, direct trace settings and trace summary must
agree. Every proposal diagnostic's existing target/parent binding and canonical
snapshot hash must match selection. A zero-score tie is not a relative gain.
Geometry/current/flux, convergence and tracing failures remain failures.
The three-way result never grants physical acceptance or actual-coil benefit:

- **Continue:** the complete selected pair passes the protocol's 1% ideal gain,
  10% own-target field nonregression and all required feasibility screens.
- **Change:** both proposals are explicitly rejected with the control completed,
  or the complete selected pair fails a screen. A witnessed trajectory exit is
  a completed negative observation; a fully evaluated unresolved geometry bound
  cannot pass this bounded recipe.
- **Inconclusive:** a required proposal, candidate, domain or diagnostic is
  missing, an arm is interrupted, a direct trajectory ends at its finite cap
  before 200 turns without a witnessed exit, or its classifier stop is unresolved.

`joint_schedule` now orders C then J with one attempt, plus then minus, no adaptive
poll or retry. Setup, scoring, solves and fitting share each arm's original
1800 s dual-clock deadline. Each J fit starts with at least 300 s on both clocks
and receives exactly that cap. Normal C cap finalization may consume the remaining
900 s diagnostic allowance; it never moves that allowance beyond search-end+900.
Selection serialization consumes the active budget and must finish before any
validation request. Source checks and final reporting also consume that budget.
Clock disagreement is measured from the original arm start through all phases;
neither a new fit window nor diagnostics may reset it. Native operation watchdogs
must retain that same origin as well as their per-operation deadlines.
Any interruption stops the attempt. A missing usable C diagnostic stops before
spending J's budget; a completed negative C screen still permits the fixed J arm.

`joint_native` runs scoring, fits and selected diagnostics in supervised children.
The same parent directly owns each cold VMEC solve; there is no nested watchdog.
Original-reference diagnostics use their own intake and the shared field/geometry
mathematics without changing the archived target registry. Completed numerical
nonconvergence requires bound native measurements; generic solver exceptions
remain inconclusive. Native call records aggregate child components and exclude
unmeasured calls internal to direct tracing.

Tests exercise the assembled schedule, parent/worker receipts, selection and
verdict with synthetic kernels, including late results, changed inputs and failed
solves. Separate tests cover real process cleanup.
Before execution, freeze both installed dependency inventories and review the
exact source commit, configuration and invocation. The original protocol JSON
remains the unchanged preregistration; its disabled state records these prerequisites.

The launcher is `scripts/run_joint_comparison.py --config <json> --output <fresh>
--reviewed-revision <full-commit>`, using the preserved native Python environment
and all four OMP/OpenBLAS/vecLib/MKL thread limits set to 1. The JSON contains the
`joint_native.Operations` constructor fields: original seed/Wout paths, preserved
VMEC virtual-environment launcher, both environment-inventory paths and hashes,
and the reviewed revision. Both arms recheck these sources under their own clock.
`run_joint_stage.py --describe-native <fresh-json>` inventories the native packages;
`solve_joint_target.py --describe <fresh-json>` inventories the VMEC environment
when invoked by its own Python. Neither command solves or fits a target. Keep
these lockfiles and the exact configuration with eventual evidence. A launch flag
records the caller's reviewed revision; it does not itself attest that review.
