# One cold-solve provenance qualification

Prospective, 7 October 2026. Before implementing the full
[joint comparison](ISSUE37_JOINT_FEASIBILITY.md), test whether a trusted bounded
runner can bind one registered input to a converged Wout that passes the
[separate numerical intake](ISSUE37_TARGET_INTAKE.md). This is a component
qualification, not either arm of that comparison. The full protocol stays disabled.

## Frozen assessment

Exactly one cold solve of the first registered proposal: original-centered
`rbc(m=2,n=1)` +1 mm, input SHA256
`3ad26eada826bbb0e33cadfbcf9c393acd9bcc6a72b32a4059e052d8675208b9`.
No retry, warm start, changed tolerance, other proposal or fit. Use the preserved
VMEC++ environment (0.7.3), single thread, `restart_from=None`, no supplied magnetic
field and `return_outputs_even_if_not_converged=False`. Require exact input-model
equality both before and after solving. The previously measured volume pass does
not excuse charged recomputation inside this assessment.

Freeze the executable/package inventory before execution at SHA256
`ae9d976eccd366bf8ebe3587d44de3b476a38fb4f583f9acf3bdbf63f15016c4`.
The actual inventory records the resolved interpreter and Python/native files
from VMEC++, NumPy, SciPy, Pydantic and their declared support packages, excluding
bytecode caches. Check it before and after solving; also record the actual imported
VMEC++ Python and extension paths/hashes. This identifies the installed solver
state, not every host system library or an external attestation.

One **600 s total parent budget** includes startup, input/volume checks, dependency
fingerprints, solve, Wout serialization, numerical intake and final hashes.
Use monotonic and UTC deadlines, disagreement limit 5 s, one thread, aggregate
256 MiB output, 3/2 GiB initial/live disk reserve and 0.1 s watchdog polling.
Start fresh; retain logs, requests, partial/failed Wouts and receipts. Kill/reap
the process group on every exit, including descendants of an exited leader;
uncertain cleanup forbids subsequent work. A late result is ineligible regardless
of worker exit code. Report worker time separately from full supervised time.

## Decision and evidence

Pass this component only if the trusted parent's request/input/environment/source
and output bindings survive, native convergence succeeds at the original 1e-12
limits, both clocks/resources pass, and all independent numerical-intake gates
pass within the same budget. Preserve the original reference B² normalization
and signed flux; report measured target B², residuals, all six field checks,
volume and elapsed time. Numerical rejection, software error and resource
interruption remain distinct recorded outcomes; none is a full joint-arm verdict.

Success qualifies only this input/runner combination for subsequent integration.
It does not establish coil feasibility, equal computational cost, actual-field
benefit, nesting or physical acceptance. No cached equilibrium is free setup for
the future joint experiment; solves must be charged to its registered arm budget.
A failure changes the implementation or the scoped feasibility recipe according
to its cause, without adapting proposals or weakening gates in this assessment.

Implementation: [`joint_equilibrium.py`](../../src/fusion_baselines/joint_equilibrium.py)
and its [worker](../../scripts/solve_joint_target.py). The worker reports native
convergence; the parent independently owns eligibility and the intake performs
field checks. Synthetic process/provenance counterexamples and an adversarial
review precede execution. Archive exact source/environment/input identities,
receipts, Wout, logs and all failures; keep only the short conclusion in active docs.
