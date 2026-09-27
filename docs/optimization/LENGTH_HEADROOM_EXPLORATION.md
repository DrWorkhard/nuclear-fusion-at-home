# Construction length headroom

27 September 2026. **Both explorations complete; Step 4 remains open.**
[Current-box evidence](../../evidence/coil-headroom-v2.json) ·
[Expanded-box evidence](../../evidence/coil-headroom-v3.json) · [Programme](STEP4_RESEARCH_PROGRAMME.md)

## Question and comparison

Can the [wider fit](LONGER_COIL_EXPLORATION.md) retain its field improvement
with enough length margin for the shared conservative geometry check?

Both runs start wider-box trial1561: six order-5 coils, 198 named coordinates,
original reference401 and exact flux. Construction penalizes lengths above
**3.44 m**, rather than 3.5 m; other penalties/objective stay fixed. Select the
lowest normal RMS among completed non-probe points with sampled geometry/current
passing and all lengths **≤3.45 m**. No fallback to the no-margin seed.

The acceptance limit stays **3.5 m**. Fine/interior results do not select the
candidate. Absolute coefficient boxes remain centered on shape52:

| Box: low/high-mode widths | Boundary RMS | Interior RMS | Geometry |
| --- | ---: | ---: | --- |
| Current: ±0.16/0.04 m | 0.002050310 | 0.01165995 | Scoped pass |
| Expanded: ±0.20/0.06 m | **0.001996268** | **0.01147939** | Scoped pass |

Expanded improves these errors **2.64% / 1.55%** over current, but reduces the
coil-clearance lower bound by 6.49 mm. Both still fail normal RMS 1e-4, maximum
normal error 1e-3 and interior RMS 0.01. The earlier longer-coil candidate passes
the interior component but has unresolved length bounds: a genuine trade-off.

Expanded bounds: length ≤3.474220 m, coil clearance ≥0.06831 m, plasma clearance
≥0.13307 m, curvature ≤10.04691/m. Current 308.141 kA; worst shifted maximum
normal error 0.00942578. These are padded floating-point bounds, not interval
proofs, complete self-disjointness or finite-build engineering.

## Checks and reproduction

Script: `scripts/explore_coil_headroom.py`; revisions `963793d` (current) and
`5a3c1d0` (expanded). Outputs: `artifacts/coil-headroom-v2/` and `v3/` beside it.
Use the recorded native environment, four thread variables set to 1, and:
`python scripts/explore_coil_headroom.py --box expanded --output artifacts/my-headroom`.
Default `--box current` preserves the first box exactly.

Each receives 300 s startup/search and 360/370 s worker/supervisor limits,
256 MiB search/fine plus 128 MiB interior, and 3/2 GiB initial/live disk reserves.
Current completes 1,575 bundles, selecting trial1574; expanded completes 1,462,
selecting trial1459. Workers take 306.360 / 284.409 s; families occupy 36.15 / 34.03 MB.

Shared checks: both shifted 128²/512-node boundary grids, conservative geometry,
and three interior levels. All ten numerical rows pass. Separate saved-array
arithmetic verifies scores, currents/flux, independent B/A samples, selections
and bound classification; 91 source hashes match per run. The new objective's
startup derivatives pass; replay checks the unchanged field state, not its
intentionally changed penalty. No full geometry reimplementation or external review.

The v1 setup failed before search on unsupported penalty-object subtraction;
its prefix and receipt remain. Direct assembly and a native derivative test fix it.

## Conclusion and next test

Headroom resolves geometry, at a field cost. Further box expansion helps only
modestly: the selected point has 3.91 mm minimum coefficient-box slack. The final
gradient maximum is 3.40e-5 against a 1e-9 tolerance; termination was on objective
change. Investigate scaling/stopping and penalty conditioning before blaming
coil count or claiming an optimum.

[Portable candidate](../../submissions/length-headroom-six-coil/README.md).
Realized topology, confinement and transfer of the Step 3 plasma benefit remain open.
