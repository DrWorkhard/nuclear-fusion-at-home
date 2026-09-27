# Longer coherent fits: time and shape freedom

27 September 2026. **Completed exploration; no physically accepted design.**
[Evidence](../../evidence/coherent-longrun-v2.json) · [Programme](STEP4_RESEARCH_PROGRAMME.md)

## Comparison and result

Both arms restart expanded-low trial1198, resetting optimizer history. Same
six order-5 coils, 198 named coordinates, reference401, flux, normalized objective
and penalties. Absolute boxes remain centered on shape52.

| Arm | Low/high-mode widths | Fine boundary RMS | Fine interior RMS | Continuous geometry |
| --- | --- | ---: | ---: | --- |
| Same box | ±0.12/0.02 m | 0.004712664 | 0.03648100 | Scoped pass |
| Wider box | ±0.16/0.04 m | **0.001947576** | **0.009769586** | **Unresolved length bounds** |

Each gets 300 s of startup/search, with the old bundle cap disabled. SciPy's
integer ceilings are 2³¹−1; neither is reached. Same-box completes 1,650 bundles,
wider-box 1,573; each retains one final deadline-interrupted attempt. Selection
is the lowest completed sampled-feasible normal RMS: trials 1649 and 1561,
before finer fields/interior checking.

More time in the same box lowers boundary RMS about 3.6%. Wider freedom helps
much more, and its interior score passes 0.01 at all three tested resolutions.
But the wider candidate **is not geometry-qualified**: three sampled lengths
approach 3.5 m, while the finest conservative upper bound is **3.519998 m**.
This is unresolved, not proof of an actual length violation. Coil clearance
≥0.07072 m, plasma clearance ≥0.14316 m and curvature ≤10.04853/m pass.
Both candidates still fail boundary RMS 1e-4 and maximum normal error 1e-3.

## Reproduction and checks

Script: `scripts/explore_coherent_longrun.py`, clean revision `eb458ef`.
Output: `artifacts/coherent-longrun-v2/`, with recorded launchers and receipts.
The evidence includes the short interior adapter's source, fixed snapshot
associations and a digest of the complete retained raw-file inventory.

Shared fine checks use 128² boundary points/512 coil nodes, both shifts; shared
continuous geometry uses up to 2048 coil/1024² surface points. Interior checks
use the established three levels with frozen current and B² scale.
No optimizer was run on interior errors. This remains the original target,
not the selected Step 3 plasma.

All four fine-field rows and six interior rows pass their numerical checks.
Separate saved-data arithmetic checks all 3,225 trial records, both selections,
all boundary/interior RMS values and geometry classifications. All 82 search
and 96 interior source hashes match. Geometry bounds are composed from the
shared routines, not a new verifier or rigorous interval arithmetic.

Search/follow-up worker: **619.612 s**, supervisor 620.427 s, within 660/670 s.
Interior worker: **2.915 s**, supervisor 3.388 s. Raw family: 73.73 MB,
within 256 MiB; one thread, no concurrent heavy job.

## Retained failure and next iteration

The v1 prefix was deliberately terminated after 152.934 s when review caught
NumPy-boolean serialization in result assembly. Its receipt and partial trials
remain; v2 uses the shared strict converter, with unchanged mathematics/budgets.

Next: put length headroom into construction/selection, not relax the 3.5 m
acceptance limit. Boundary error, realized topology and Step 3 benefit transfer
remain open. Passing the interior component alone does not complete Step 4.
