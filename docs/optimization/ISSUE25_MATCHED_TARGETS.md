# Matched target-to-coil benefit experiment

**Full benefit transfer remains unresolved.** The wide action diagnostic cannot
be evaluated completely in either fitted coil field. This is a useful negative
result for [issue #25](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/25),
not physical acceptance or a confinement claim.

## Question, inputs and method

Does Step 3's vacuum action improvement survive practical coils? Both arms start
from the same length-headroom geometry and use the original archived reference401
and selected401 Wouts. `coil_check.TARGETS` binds their inputs, Wout hashes and
frozen B² normalizations (1.6293829620247962 / 1.6313464444829588). The improved
input is restored unchanged from archive `68db098`. Currents are normalized to
each target's boundary flux and then frozen for diagnostics.

[Producer/evaluator `a551289`](https://github.com/DrWorkhard/nuclear-fusion-at-home/commit/a551289e63e44d7dbae7b5d5a0e5f4b6026db257)
was clean. Its [prospective rules](https://github.com/DrWorkhard/nuclear-fusion-at-home/blob/a551289e63e44d7dbae7b5d5a0e5f4b6026db257/docs/optimization/ISSUE25_MATCHED_TARGETS.md)
freeze selection, grids, budgets and failure handling before fitting. The two
sequential searches each receive 300 s including intake/model startup, followed
by unchanged shared field/geometry checks. Both exhaust their search budgets;
late/incomplete trials cannot win. Startup/search times are recorded separately.

Direct coil-field tracing uses ten starts and 200 transits. `measure_coil_bounce.py`
then follows actual coil trajectories from target-PEST launch coordinates, using
801 toroidal samples and 16 alpha labels over two field periods. It reuses the
Step 3 fixed bounce fields, period families and action statistic, retaining every
missing/extra/censored well failure. Conditional refinement is skipped because
both wide domains fail. No unseen holdout or verified realized-flux coordinates
exist here; this is exploratory.

## Result

| Diagnostic | Original target fit | Improved target fit |
| --- | ---: | ---: |
| Fine boundary RMS | 0.0019320403 | 0.0019531336 |
| Fine maximum normal error | 0.0090690841 | 0.0092677579 |
| Interior RMS | 0.0107165171 | 0.0108879575 |
| Scoped continuous geometry | Pass | Pass |
| Frozen base current | 307,977 A | 308,134 A |
| Lines completing 200 transits | 10/10 | 10/10 |
| Maximum signed-iota mismatch | 0.005262 | 0.005641 |
| Narrow action-variance score | 4.254756e-5 | 4.038923e-5 |
| Wide action-variance score | Incomplete | Incomplete |

Field errors are against different targets, not a matched benefit measure. Both
fits fail the original field limits. At q=0.03, the original fit lacks required
well coverage at s=0.1/0.25; the improved fit also fails at s=0.75 (an extra well
on one launch line). There are 32 / 33 failed launch lines. No failed cell is
dropped to manufacture a wide score. The narrow diagnostic is 5.07% lower for the
improved arm, but is still degraded relative to each ideal target and does not
establish physical transfer. Ten surviving lines do not prove nested surfaces.

## Evidence, availability and decision

The evidence archive is prepared locally at commit
`05a4511084912fea9bd8d03e81f01018882396b8`, tag `evidence-issue25-matched-v1`.
Publication is pending: the automatic approval review timed out twice.
The archive is not yet available from GitHub.
Dense target reconstruction and ideal controls match the qualified archived arrays
exactly. The archive retains commands, failed trials, snapshots and diagnostic
arrays; `replay.py` reproduces field/action metrics without Wouts or SIMSOPT
(NumPy/SciPy required). Local raw outputs remain in `artifacts/issue25-matched-v1`.
Original Wouts and upstream validation archives remain maintainer-local; no
separate-machine native reproduction or external physics review is claimed.

All stages completed within their declared limits, using one native thread and
less than 256 MiB per arm. Next: diagnose shallow-well fidelity and validate actual
flux-surface labels before confirming benefit transfer. The small fitting gains
and narrow score do not justify scaling the same recipe or relaxing acceptance.
