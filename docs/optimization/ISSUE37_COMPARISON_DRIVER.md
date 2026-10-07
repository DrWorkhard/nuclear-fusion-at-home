# Joint comparison integration

Prospective integration of the [frozen feasibility protocol](ISSUE37_JOINT_FEASIBILITY.md).
The numerical components are qualified separately; the complete two-arm experiment
has not run. The next decision requires connecting those components with charged
budgets and immutable selection. No new search basis, metric or acceptance limit
is introduced. Full execution remains disabled until the complete driver, exact
launcher and dependencies receive adversarial review.

`joint_decision` provides the trusted driver's selection and decision rules.
Both proposals must terminate, in fixed plus/minus order. Select on complete
training action variance, then selected inner objective, then proposal index.
A normal fit cap can retain an earlier completed eligible candidate only after
passing startup. The parent must establish that the stop was its declared fit
cap; a generic timeout or interrupted whole arm is insufficient. A probe cannot
win. Explicit numerical rejection requires a documented size, equilibrium or
complete plasma-domain failure; unclassified errors are software failures.

Freeze the chosen input/Wout hashes, target identity, coil coefficients,
normalized currents and selected trial index before any held-out evaluation.
`freeze_selection` checks the named snapshot and fit row, binds the source files,
saves a canonical selection hash and refuses a second selection in the same cell.
The eventual driver must recheck source/receipt hashes and this frozen state
before and after diagnostics; helpers are not a verifier for candidate-supplied
completion flags or arbitrary JSON reports.

Use the maximum fine-boundary RMS and finest 64/512 interior RMS; keep both fine
maxima and all coarser levels. Require the registered action domains and both
refinements, recomputing cell scores from their full phase/family arrays. Frozen
current, independent field controls, direct trace settings and trace summary must
agree. Geometry/current/flux, convergence and tracing failures remain failures.
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

Still required: the operation scheduler, cold-solve and numerical-rejection
handoff, shared dual-clock/storage supervision, reference diagnostics, and tests
of the complete C-then-J sequence. Setup and every failed operation must consume
the arm's frozen budget; cached qualification work cannot become free setup.
Each child operation needs one process-group owner so interruption cannot leave
an orphan solve running alongside another arm. No native comparison is authorized
by a passing unit test of these decision helpers.
