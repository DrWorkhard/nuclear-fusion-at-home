# Does the ideal-improved target make coil fitting harder?

Prospective registration, 7 October 2026. The fixed +0.35 mm target has a
[validated ideal-score gain](ISSUE37_STEP_VALIDATION_RESULT.md), but existing
boundary errors are about 19 times their absolute limit. Before spending on
interior checks and long traces, test its unmeasured coupling to coil fitting.
The [machine-readable protocol](ISSUE37_FIT_COUPLING.json) freezes exact target,
cold-solver, training/validation receipt and original-seed identities.

Run original control then fixed candidate, each from the same six/order5 coil
geometry with **300 s fitting allowance** including per-arm setup, intake,
startup and search. Retain existing target-specific signed-flux normalization,
penalties, typed trial rejection and eligible boundary-RMS selection. Freeze the
selected coefficients, currents, target and index before diagnostics; no fallback
or winning derivative probe. Both equilibria and ideal-score receipts are reused
explicitly; no new solve, ideal scoring, target tuning or historical compute-cost
equivalence is claimed. All actual work remains charged.

Each arm ends within **600 s from its origin**. The diagnostic deadline is
`min(parent-observed fit-process completion, original fit deadline) + 300 s`,
also capped by the arm and whole-driver deadlines, on both clocks. This charges
fit finalization and bounds early-return cases. Diagnostics include two
128-square/512-node fine-boundary shifts (0, 0.5), continuous geometry and final
source/environment verification/reporting. Total driver budget is at most
1200 s, including initial imports/setup and final report.
Preserve full convergence histories, independent B/A checks, current/flux checks
and the original absolute field limits. No interior or trajectory study is run.

`boundary-fitting-nonregression` requires both eligible completed fits, complete
passing numerical fine/current/flux/geometry checks and candidate worst fine RMS at most
1.10 times control. Complete failures of those hurdles reject this bounded
recipe; so does a normally completed fit with documented no eligible candidate.
Failed independent numerical checks are inconclusive: untrustworthy metrics
cannot classify a target as harder to fit. Missing work, unresolved geometry,
failed intake/startup, unclassified failure or resource/clock/source/host
interruption is also inconclusive. Report both absolute
RMS/max gates separately. Different-target errors measure fitting burden, not
improvement in a common physical field.

A pass retains an ideal-improved starting target; it is **not coil feasibility**.
If absolute boundary limits still fail, do not automatically extend fitting or
run expensive acceptance diagnostics. Further diagnostics need a separately
registered decision tied to substantially improved field errors or a specific
topology question. A failure does not establish global impossibility. No
realized-field benefit, interior/tracing result or physical acceptance is claimed.

Use one native thread, 256 MiB total retained output, 3 GiB initial / 2 GiB live
disk reserve and the unchanged 5 s wall/monotonic disagreement gate. No retry,
extension or alternative target. Use owned `caffeinate -i -s -t 1320` on AC;
admit both assertions and launch within 30 s, sample during and query after
termination. Failed queries or observed loss invalidate the result. Release the
owned assertion, poll terminal and verify absence, retaining every attempt.
Sampling does not establish continuous host stability or controlled load.

Execution stays disabled until exact implementation/configuration, dependency
inventories, software checks and adversarial review are complete. This
registration is not execution approval or a scientific result. Agent review is
not external physics peer review. Preserve prior verdicts and original outputs.
