# Fixed smaller-step phase and resolution validation

Prospective registration, 7 October 2026. The +0.35 mm point passed its
[training screen](ISSUE37_STEP_SCALE_RESULT.md). Decision: does that fixed
ideal-target score gain survive the existing phase and resolution checks before
spending on coils? The [machine-readable registration](ISSUE37_STEP_VALIDATION.json)
pins its exact input, Wout, successful cold-parent and screen receipts, plus the
original reference Wout. No candidate or threshold adapts to validation.

Reuse those frozen equilibria explicitly; no new solve, fit or matched-compute
claim. Run four fresh scores in order: original at 1601 and 3201 toroidal points,
then +0.35 mm at those resolutions. Each uses 32 half-shifted phases, all five
original surfaces and seven pitches, two periods, and unchanged independent
numerical intake. Retain every cell, source identity and failure.

Positive requires all four full-domain scores eligible, candidate score at most
0.99 times original on both grids, and both per-target refinement checks passing
the existing `holdout_agreement` formula (0.1% tolerance). Complete eligible
scores missing either hurdle give a negative validation verdict. Refinement
failure leaves the true-score gain numerically unresolved; it does not establish
worsening. Missing or incomplete domains/intake, unclassified failures, resource,
clock, source or host interruptions are inconclusive.

One **180 s dual-clock total** charges imports/setup, receipt and environment
verification, all four intakes/scores and final checks/reporting. Keep the 5 s
clock-disagreement gate, one native thread, 256 MiB retained-output cap and
3 GiB initial / 2 GiB live disk reserve. No retry, alternative point or extension.
Commit and adversarially review the exact producer/configuration before execution.

Use owned `caffeinate -i -s -t 240` on AC, admit both assertions, launch within
30 s, sample during and query after scientific termination. Failed queries or
observed AC/assertion loss invalidate the enclosing result. Release only the
owned assertion afterward, poll terminal and verify absence, retaining every
attempt. This does not prove continuous host stability or controlled load.

A positive result establishes only this fixed ideal-target score's phase and
resolution robustness. Candidate phases are new, but the score family, machine
and comparator grids are previously used: no external or statistical independence
is claimed. Coil geometry/fields, realized benefit, optimality and physical
acceptance remain unestablished. Preserve prior verdicts; any coil comparison
needs separate registration. Execution remains disabled until implementation,
checks and review prerequisites are met. Agent review is not external peer review.
