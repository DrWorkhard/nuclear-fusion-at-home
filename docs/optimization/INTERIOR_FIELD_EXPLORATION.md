# Interior fields of the exploratory coil fits

27 September 2026. **Completed exploratory screen; every interior limit still fails.**
[Evidence](../../evidence/coherent-interior-v1.json) · [Boundary fits](COHERENT_COIL_EXPLORATION.md)

## Question and result

Does the improved boundary fit also improve the vector field inside the target?
Yes for these fixed snapshots: the expanded-low endpoint reaches **0.0402915**,
**73.66% below** its matched restart control, but still **4.03× the 0.01 limit**.

| Frozen snapshot | Fine interior-vector RMS | Base current | Scoped geometry |
| --- | ---: | ---: | --- |
| Original shaped seed | 0.3712380 | 294.966 kA | Prior qualification; not reaudited here |
| Shape trial 52 | 0.3123243 | 324.792 kA | Prior pass, exact snapshot joined |
| Coherent trial 598 | 0.1823903 | 349.383 kA | Prior pass, exact snapshot joined |
| Restart, original bounds | 0.1529416 | 345.245 kA | Prior pass, exact snapshot joined |
| Restart, expanded low modes | **0.0402915** | **315.407 kA** | Prior pass, exact snapshot joined |

All five were fixed before this screen; none was optimized or selected on these
interior results. All use the **original reference401**, not the accepted Step 3
target. The geometry joins reuse separate completed reports; this screen does
not recalculate geometry or grant physical acceptance.

## Method and verification

Script: `scripts/screen_coherent_interior.py`, clean revision `8fae8b0`.
Raw output: `artifacts/coherent-interior-v1/run/`; execution receipt and every
output identity are bound by the linked evidence.

Use archived target fields on s=0.25, 0.5 and 0.75, fixed
**B² = 1.6293829620247962 T²**, and the exact signed loop flux
**−0.03141592653589793 Wb**. Six order-5 base curves give 24 physical coils.
Each snapshot keeps its saved current. Report
`sqrt(mean(|Bcoil−Btarget|²)/B²)` at (interior grid, coil nodes)
**(32²,256), (64²,256), (64²,512)**.

All fifteen rows pass native/independent geometry, signed-current and sampled
B/A comparisons. Each row checks 64 B and 64 A points using the shared independent
filament implementation. The 80 source identities remain unchanged. Separate
saved-array arithmetic reproduces all fifteen vector/flux summaries and joins
four prior geometry reports to the exact snapshots.

Largest interior-grid RMS change is 5.723e-5; largest coil-quadrature change is
2.776e-17. The best candidate's grid change is 3.288e-6 and interior field RMS is
1.02854 times the target. All flux/current screens pass; all interior RMS gates
fail. These are numerical refinement observations, not rigorous error bounds.

Execution: **6.747 s worker / 7.292 s supervised**, 14.58 MB family,
within 180/185 s and 128 MiB limits, one thread. No optimizer or VMEC solve.
An MPI TCP bind warning is retained in stderr; execution and numerical checks
completed. No extra permission was requested to enable MPI networking.

## Retained failure and next question

Initial real-data intake rejected a one-ULP difference from recomputing π/100.
The repair binds the exact committed-input value, with no relaxed tolerance;
51 focused tests include that regression and rejection of a one-ULP input change.

This result supports continued normalized fitting. It does not establish
realized magnetic surfaces, confinement or transfer of the Step 3 benefit.
The [longer/wider follow-up](LONGER_COIL_EXPLORATION.md) and subsequent
[headroom comparison](LENGTH_HEADROOM_EXPLORATION.md) now test that direction.
Actual-field topology and matched realization of the selected Step 3 target
remain open; the programme owns current next actions.
