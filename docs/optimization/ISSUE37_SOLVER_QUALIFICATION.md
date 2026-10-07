# One cold-solve provenance qualification

Registered and executed on 7 October 2026. Before implementing the full
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
SIGTERM is observed by the watchdog without interrupting process creation or
cleanup; the prior signal handler is restored afterward; uncatchable
SIGKILL is outside this guarantee. Uncertain cleanup forbids subsequent work. A late result is ineligible regardless
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

## Qualification result

The one registered solve **passed** at clean producer/evaluator
`871aeb74e1e2656a9d1b32764b85618f44a94199`: 174.879 s total, 171.492 s worker
(including identity checks/serialization), 172.173 s subprocess supervision;
clock disagreement below 0.0001 s. No retry or environment change. At 401 surfaces,
force residuals (r/z/lambda) were 9.980e-13 / 2.914e-13 / 3.893e-17.
All six field checks passed: maximum positive representation error 5.122e-7,
independent geometry 2.257e-15. Volume was 0.19006046531779677 m³
(-0.0039507525% from original); measured B² 1.625766758078491, with the reference
normalization 1.6293829620247962 and signed flux unchanged.

Local archive `b8d629a192d933ce22de523a57ca854a4c156963`, prepared tag
`evidence-issue37-solver-qualification-v1`, contains all 14 original raw files
(25,333,491 bytes), including Wout, exact launcher/driver, installed-file inventory,
receipts and replay command under `evidence/issue37-solver-qualification-v1`.
The 20-entry manifest SHA256 is
`69270ec9eb466cc8ee71e149692a40f85376a29b2d785ba7a44c25de5e1c1982`.
Publication is pending; raw outputs remain intact locally. Native log whitespace
is retained byte-for-byte. Fresh shallow producer checks passed 360 research tests
(23 focused), 61 public tests, docs, Ruff and source diff checks. Read-only agent
review preceded execution; it is not external physics review.

This clears only the registered plus input and runner for subsequent integration.
No coil fit or joint-arm verdict was produced; the full comparison remains disabled.
