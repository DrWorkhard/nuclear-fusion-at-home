# Construction length headroom

27 September 2026. **Current-box run completed; expanded-box follow-up prepared.**
[Evidence](../../evidence/coil-headroom-v2.json) ·
[Preceding result](LONGER_COIL_EXPLORATION.md) · [Programme](STEP4_RESEARCH_PROGRAMME.md)

Question: can the wider fit retain its field improvement with enough coil-length
margin for the existing conservative geometry check?

Start: wider-box trial1561 from `coherent-longrun-v2`, six order-5 coils, all 198
named coefficients, original reference401 and exact flux. The first run keeps
its shape52-centered ±0.16/0.04 m low/high-mode box. The follow-up expands this
to ±0.20/0.06 m, restarting the same seed/history rather than the new endpoint.
Both keep current normalization and every acceptance gate.
Only the construction length-penalty target changes: **3.44 m instead of 3.5 m**.
The other penalty terms/weights and field objective stay fixed.

Select the lowest normal RMS among completed non-probe points with sampled
geometry/current passing and **all sampled lengths ≤3.45 m**. No fallback to
the old no-margin seed; no feasible point is a retained negative result.
This prospective construction rule is stricter than the unchanged 3.5 m
acceptance gate. Fine/interior results do not select the candidate.

Script: `scripts/explore_coil_headroom.py`. Reuses the existing search, startup
finite differences, two shifted 128²/512-node boundary checks, continuous
geometry schedule and three-level interior screen. Geometry-penalty seed replay
is deliberately omitted because that objective changes; field-state replay and
full new-objective derivative checks remain. No topology/benefit-transfer claim.

Resources: 300 s startup/search, 360 s total worker, 370 s external cap; one
thread, 256 MiB search/fine and 128 MiB interior outputs; initial/live disk
reserves 3/2 GiB. SciPy's nonbinding integer ceilings are 2³¹−1; no bundle cap.
Raw output: `artifacts/coil-headroom-v2/`; follow-up planned in `coil-headroom-v3`.
The v1 setup failed before
any search because native penalty objects do not support subtraction. Its
2.563 s supervisor receipt and prefix remain; direct assembly of the same
declared objective corrects this. Retain failed prefixes.

Run in the recorded native environment with the four thread variables set to 1:
`python scripts/explore_coil_headroom.py --output artifacts/my-headroom`.
Use `--box expanded` for the new comparison; default `current` is unchanged.
The local supervisor also records the pre-run question and process receipt.

## Current-box result

Revision `963793d`: 1,575 completed bundles; selected trial1574. Boundary RMS
**0.002050310**, maximum 0.0101974, still fail their gates. Scoped geometry passes:
length ≤3.477734 m, coil clearance ≥0.07481 m, plasma clearance ≥0.13292 m,
curvature ≤10.03498/m. Current 308.150 kA. Interior RMS **0.01165995** fails 0.01.
Length headroom resolves the previous geometry uncertainty, at a field cost.

All two boundary and three interior numerical rows pass. Separate saved-array
arithmetic recomputes metrics, selection across all 1,576 records and bound
classification; all 91 source hashes match. Worker 306.360 s, supervisor
306.938 s; retained family 36.15 MB. No realized topology or Step 3 transfer.
