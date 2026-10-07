# Prospective axis-center sensitivity test

Decision: does replacing the target-axis polar center by a numerically resolved
local periodic field-line center remove the continuation failure's saved angular
reversals? A positive result would motivate checking coordinate choice before a
new reconstruction; a negative result rejects this specific explanation. Neither
outcome qualifies a contour or establishes islands, nestedness or confinement.

Use the unchanged frozen continuation and original reference401 coil snapshots
and the five saved launches of the [recurrence diagnosis](ISSUE48_CONTINUATION_RECURRENCE.md).
Inputs resolve in archives `191875d231b396e5960cbd9460a37a6c462b6381`
and `2ee186bb347245072c98d983a42b06f8e02a16a9`; bind their manifests,
snapshots, reports and consumed NPZs before/after. No Wout or equilibrium solve.

For each field, solve the direct one-field-period R,Z return residual from phi=0
to pi, initialized at the recorded target axis. Use DOP853 with maximum step
pi/100 and SciPy hybr with xtol=1e-9. Fail if a root trial leaves the fixed 2 cm
neighborhood. Independently start both 512-node (rtol=1e-10, atol=1e-12) and
1024-node (1e-11, 1e-13) calculations from the target center. Each root must report
success and residual at most 1e-9 m; their centers must agree within 1e-7 m.
These are local periodic fixed-point estimates, not uniqueness or stability proofs.
Check native fields against the existing independent filament kernel at nine
points on each estimated orbit to relative scale max(1,|B|) error at most 1e-12.
An analytic rotating field supplies a known-center control before native execution.

Use the finer center on both equivalent phi=0/pi planes. Reuse the unchanged
five-case recurrence function, 640 pooled/320 per-plane saved crossings,
eleven residue sequences and 1e-8-rad resolved-step cutoff. Report old/new centers,
all direction changes, gaps and physical return RMS. No new long traces, spline
selection, flux labels, launch matching or modifications to acceptance gates.
Original 19/20 continuation and 20/20 reference grid verdicts remain unchanged.

One attempt: 240 s driver / 270 s supervised total including startup and receipts,
one thread, 256 MiB aggregate output, 3/2 GiB initial/live disk reserves and 5 s
clock discrepancy ceiling. Reuse the recorded supervisor/environment verification.
Preserve solver failures and all outputs; no retries or neighborhood/tolerance
retuning based on the outcome. This is exploratory same-machine numerical evidence.
Publish no result until final read-only adversarial review; external publication
still requires authority. Agent review is not external physics review.
