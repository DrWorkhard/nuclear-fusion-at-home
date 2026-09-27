# Raw versus local-normalized coil fitting

27 September 2026. **Completed exploration; both selected designs fail geometry
and field limits.**
[Programme](STEP4_RESEARCH_PROGRAMME.md) · [Calibration](REFERENCE_CALIBRATION.md)

## Question and prospective comparison

Does directly minimizing local normalized boundary error produce a materially
better Goodman field fit than the previous flux-normalized raw objective,
when both start from the same geometry and have the same search budget?
The saved-response diagnosis motivates this comparison; it does not predict
the outcome. This is exploration session 1 of the programme's ten-session cap.

Use the original reference-n6 shaped 100 mm seed, before any protected fit:
`artifacts/clear-coil-field-start-v1/reference-n6/operations/qualification-N-00-snapshot.json`,
SHA-256 `4c29c1f7afb67f290bd3c7c2ec23829e5f386e7e8c299f8d40a0e0f4e2f03830`.
The target input is `evidence/plasma-design-v2/reference-input-401.json`, SHA-256
`57394ef682f3c6399faa03012abc02da2eb1ce40703a4f99640ece3d07e5691f`.
Keep its complete boundary modes, two field periods and stellarator symmetry.
Six order-5 base curves produce 24 physical coils and 198 named metre-valued
Fourier coefficients. Both arms use that same geometry, fixed equal **100 kA
reference currents** (the legacy “unit-current” convention), and shared current
rescaling to target flux −0.03141592653589793 Wb.

Let `a = target_flux / unit_current_flux`, `A = mean(|surface normal|)` and
`B²_ref = 1.6293829620247962 T²`, frozen from the original target. Compare:

| Arm | Field objective | Derivative |
| --- | --- | --- |
| Raw control | `a² * raw_quadratic_flux / (A * B²_ref)` | Native raw-flux derivative plus the existing current-elimination correction `−2 J dPhi/Phi` |
| Local normalized | `local_flux / A = 0.5 normal_RMS²` | Native local-flux derivative; common nonzero current scale cancels |

Use the same existing sampled geometry penalties in both arms: length above
3.5 m, coil separation below 60 mm, plasma separation below 80 mm and quadratic
curvature penalty above 10/m, with existing weights 1, 1000, 1000 and 1e-4.
The physical curvature limit remains **12/m**; the 10/m soft penalty is not a
new acceptance criterion. Reuse the memory-bounded sparse plasma-distance term,
not the previous memory-intensive dense implementation. Its geometry surface
is 128 × 128 over the full torus.

## Fixed local budget and checks

- Run arms serially; all 198 coordinates, identical ±0.01 m boxes around the
  original seed. L-BFGS-B with at most **80 total coarse value/gradient bundles
  per arm**, including up to ten startup/derivative bundles; at most 300 s per
  arm including startup. This is a deliberately small feasibility probe.
- Coarse field grid 64 × 64 over one field period; 256 coil nodes. Before search,
  two deterministic directional checks at steps 1e-5 and 5e-6 m must agree with
  analytic derivatives (absolute 1e-7 or relative 1e-4). Repeat/reset the seed.
  Do not patch SIMSOPT's small-objective derivative clipping; detect/report it.
- Retain every requested point, error/geometry/current value and terminal reason.
  Select the lowest completed seed/search objective in each arm, excluding
  derivative probes, regardless of geometry verdict, for the exploratory
  endpoint screen; label violations explicitly. No fictitious
  zero gradient is returned for infeasible designs.
- Screen both selected endpoints, not only the favorable one, at 128 × 128 /
  512 coil nodes, unshifted and half-cell shifted. Freeze the selected coarse
  physical current for these checks and report flux refinement separately.
  Use 128-point field blocks and independent filament checks at 64 fixed points.
  These inspected grids are exploration data, not future confirmatory holdouts.
- At most **900 s overall / 905 s external process-group timeout**, one thread,
  256 MiB outputs, 3 GiB initial and 2 GiB live free disk. Fresh output directory;
  retain interrupted attempts. No equilibrium solve, pressure model or publication.

Report unchanged endpoint screens: normal RMS ≤1e-4, sampled maximum ≤1e-3,
current ≤500 kA, length ≤3.5 m, curvature ≤12/m, coil/plasma separation ≥60/80 mm.
Sampled geometry success is **not continuous certification**. Interior-vector
error, field topology, transferred plasma benefit and robustness are unmeasured.
The reference Wout is retained by identity but unnecessary for this boundary-only
question. No endpoint inherits the original seed's geometry certificate.

## Interpretation and next decision

Compare field/geometry/current trade-offs, not only optimization scores.
Equal ceilings do not mean equal consumed computation: the raw arm has an extra
vector-potential derivative and the first arm may pay native/JIT initialization
costs. Report actual bundles, field/derivative requests and stop reasons; this
small serial comparison is not a general timing or optimizer-ranking claim.
RMS below 1e-2 with unchanged geometric gates is the programme's triage signal,
not acceptance. If results remain far above it, use the measured response to
choose a different start, search envelope or family; do not infer impossibility
or extend this experiment's budget retrospectively. Any promising candidate
requires frozen-selection independent confirmation and interior/geometry checks.

## Implementation checks and execution

The isolated experiment reuses the existing field and sparse geometry tools;
it changes neither shared evaluators nor the acceptance gates. Twenty-eight
synthetic/native-circle tests pass, and 101 relevant reused-component
tests pass. Named mapping, seed replay, failed startup, shared output cap and
late-result rejection are covered. Source fingerprints include the actual loaded
native Python/binary and optimizer implementation, before and after execution.

Run `scripts/explore_normalized_coils.py NEW_OUTPUT_DIRECTORY` in the existing
native environment with the stated one-thread settings and an external 905 s
process-group watchdog. Raw outputs are retained in separately identified runs.

## First attempt: adapter failure, not an objective comparison

At clean `e916c8d`, `artifacts/normalized-coils-v1/` exits nonzero after 23.22 s.
Both arms reproduce the original seed, but the raw arm fails all four derivative
checks and stops before search: discrepancies 0.0118–0.0152, not rounding noise.
Its exact seed repeat passes. The local arm completes 80 bundles and two fine
screens, but its recorded coarse current/flux scale stays constant over every
trial; the fine flux differs from the target by 14.22%. This is not a valid
normalized-current comparison or a new admitted design.

The cause is **our instrumentation adapter**, not a changed physical model or
SIMSOPT flux formula. Defining a fresh subclass called `Tracked` for each field
resets the native optimization object's class counter: boundary and loop fields
both become `Tracked1`. Name-based equality merges their parent dependency
references, so the loop vector-potential cache fails to invalidate after coil
changes. Separate source inspection confirms this mechanism. A single shared
wrapper class with per-instance accounting repairs it. A native-circle
regression fails before the repair and passes afterward: both fields' B/A
caches change with perturbed geometry, match fresh unwrapped fields and restore
on reset. Original limits and native libraries are unchanged.

The [failed-attempt manifest](../../evidence/normalized-coils-failed-v1.json)
binds the retained local outputs; Git preserves the executable source. Do not loosen derivative tolerances,
reinterpret the 14.22% discrepancy as harmless quadrature error or claim that one
objective won. The corrected retry below repeats the complete two-arm schedule
in a fresh directory (`artifacts/normalized-coils-v2/`) after regression and review.

## Corrected comparison and independent replay

The full retry at clean `5b744f2` completes in **37.224 s** (38.027 s supervised),
with 80 completed bundles per arm, all eight derivative checks, exact seed
repeats, and both fine screens per endpoint. Both searches stop at the declared
bundle cap, not demonstrated convergence. The
[complete evidence](../../evidence/normalized-coils-exploration-v2.json) binds
every attempted/completed point, selected coefficients, field arrays, sources,
execution and the invalid first attempt. Output is about 7.49 MB.

| Fine endpoint, unshifted 128² / 512 | Raw objective | Local-normalized objective |
| --- | ---: | ---: |
| Area-weighted normal RMS | 0.208694197 | 0.187787976 |
| Sampled maximum normal ratio | 0.574569 | 0.527694 |
| Physical base current, kA | 233.803 | 343.882 |
| Largest sampled curvature, 1/m (limit 12) | **17.3520 — fail** | **16.5284 — fail** |
| Sampled minimum plasma gap, mm (limit 80) | **72.9327 — fail** | 80.7695 — sampled only |
| Sampled minimum coil gap, mm | 93.2766 | 170.4669 |
| Longest coil, m | 2.03912 | 2.05130 |
| Frozen-current relative flux error | 4.42e-16 | 4.42e-16 |

Local-normalized fitting gives **10.02% lower RMS but 47.08% greater current**
than this raw-objective endpoint. Neither is an acceptable design or a Pareto
dominance result. Both miss the 1e-4 RMS / 1e-3 maximum gates by large margins.
Only the unchanged seed among each arm's search points passes all sampled
geometry limits; lower field objectives alone select infeasible points.

The shifted grids agree closely in RMS (raw 0.2086941971, local 0.1877879758);
sampled maxima vary and remain failures. Both currents stay below 500 kA.
The valid retry has 78 distinct unit-flux values per arm, resolving the stale-cache
symptom. Independent field discrepancies are ≤8.712e-16; all four refined flux
checks agree with target within 4.42e-16 relative error at frozen coarse current.

Independent read-only replay verifies 22 source files, nine relevant Git objects
and the prospective question, all 160 attempt/completion pairs, selections,
coordinate boxes and current/objective identities. All eight derivative checks
pass: maximum errors 3.079e-11 raw and 2.223e-11 local. Separate `math.fsum`
arithmetic reproduces 48 fine scalar metrics and checks 256 saved independent/
native field-point comparisons. No new fields are called for that audit.
Independent trigonometric derivatives confirm all twelve base-coil curvature
maxima, including explicit >12/m witnesses. Independent surface/coil sampling
also confirms the raw plasma-gap violation. Loop-A arrays were not saved in
this experiment, so reported flux closure has arithmetic/refinement checks,
not a separate re-integration audit.

The selected raw/local designs hit 140/144 of 198 coefficient-box faces.
This explains why a larger envelope is worth investigating, but increasing it
alone would not resolve the demonstrated geometric violations.

**Decision:** objective choice matters, but the current soft geometry penalty
does not keep these search results buildable. Before a larger search, screen the
existing circle100 and farther-out shaped starts at the same fixed target and
physical normalization. Their pre-existing geometry margins are known, whereas
their field scores are not. Keep the present negative result and all gates;
do not relabel sampled or infeasible improvement as completion of Step 4.
