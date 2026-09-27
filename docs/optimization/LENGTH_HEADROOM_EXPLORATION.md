# Construction length headroom

27 September 2026. **Prepared exploration; no acceptance claim.**
[Preceding result](LONGER_COIL_EXPLORATION.md) · [Programme](STEP4_RESEARCH_PROGRAMME.md)

Question: can the wider fit retain its field improvement with enough coil-length
margin for the existing conservative geometry check?

Start: wider-box trial1561 from `coherent-longrun-v2`, six order-5 coils, all 198
named coefficients, original reference401 and exact flux. Keep its shape52-centered
±0.16/0.04 m low/high-mode box, current normalization and every acceptance gate.
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
Raw output planned at `artifacts/coil-headroom-v1/`. Retain failed prefixes.

Run in the recorded native environment with the four thread variables set to 1:
`python scripts/explore_coil_headroom.py --output artifacts/my-headroom`.
The local supervisor also records the pre-run question and process receipt.
