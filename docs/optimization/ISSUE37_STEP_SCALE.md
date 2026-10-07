# One fixed smaller-step screen

Prospective registration, 7 October 2026. The completed [awake comparison](ISSUE37_AWAKE_RESULT.md)
remains **change**. Its training scores at -1/0/+1 mm are
0.0003584779663072098 / 0.00023817620290847872 / 0.00026038327255955125.
A quadratic through these points has an unvalidated minimum at +0.344170574 mm,
with predicted 3.54% reduction. Three points give no residual/error estimate;
changes in bounce-well topology could invalidate this interpolation.

Decision: is **one fixed +0.35 mm** point worth subsequent validation? Use one
cold equilibrium and the full original training domain, with no coil fitting or
held-out evaluation. The [machine-readable registration](ISSUE37_STEP_SCALE.json)
freezes the exact input hash, original reference report/score, grids and threshold.
The reference report is an explicitly required local archive input; it does not
supply a free control for a matched comparison or imply matched compute cost.

Keep all other target values, 401-surface solver settings, signed flux/current
conventions, size and independent numerical intake gates unchanged. Use a separate
named screen registration; original comparison cases and public target registries
remain distinct. Freeze the clean implementation, configuration and both native
environment inventories and obtain adversarial review before execution.

One **600 s** dual-clock budget charges imports/setup, input/source verification,
one cold solve, intake, scoring, final verification and reporting. Keep the 5 s
clock-disagreement gate, one native thread, 256 MiB retained-output cap, 3 GiB
initial / 2 GiB live disk reserve. No retry, alternative point or extension.
A complete eligible score at most **0.99 times the frozen training reference**
passes this screen; a completed score above it or fully documented ineligible
training domain fails it. Missing work, unfinished solve/intake, unclassified
failure or resource/clock/source interruption is inconclusive.

Use owned `caffeinate -i -s -t 720` on AC, observe both owned assertions before
launch, sample during execution and check after scientific termination. Launch
within 30 s of assertion admission. Retain only owned assertion lines and the
power-source line. Failed queries or observed assertion/AC loss invalidate the
enclosing screen. After the scientific session is terminal, terminate the owned
assertion process, poll it to terminal and verify absence; use authorized sandbox
escalation if needed and preserve every cleanup attempt. This changes no permanent
power setting and does not establish continuous host stability or controlled load.

A positive result is only an in-sample ideal-target score reduction at this point.
It establishes no held-out gain, coil feasibility, realized-field benefit or
optimum. Any validation or coil fit needs its own registration. Preserve every
failure and original output; archive full evidence separately and review the
final exact revision before publication/merge. Agent review is not external
physics peer review. Execution is disabled until implementation/review prerequisites
are met; this document alone is not evidence that they have been met.
