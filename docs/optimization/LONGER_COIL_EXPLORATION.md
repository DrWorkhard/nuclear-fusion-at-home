# Longer coherent fits: time and shape freedom

27 September 2026. **Prepared exploration; no new result yet.**
[Programme](STEP4_RESEARCH_PROGRAMME.md) · [Starting result](COHERENT_COIL_EXPLORATION.md)

Question: can more optimization time and a wider shape domain close the remaining
boundary/interior gap while retaining practical geometry? Start both arms from
the checked expanded-low trial 1198, RMS 0.004889 and interior RMS 0.04029.
Reset optimizer history; retain six order-5 coils, all 198 named coordinates,
original reference401, exact flux convention and normalized objective/penalties.

| Arm | Modes 0–2 | Modes 3–5 | Search ceiling |
| --- | --- | --- | --- |
| Same box | ±0.12 m | ±0.02 m | 300 s |
| Wider box | ±0.16 m | ±0.04 m | 300 s |

Both absolute boxes stay centered on shape52, not the new seed. Widths define
the comparison, not new physical acceptance limits. Use the same masked startup
directions inside the smaller box, exact seed replay and unchanged derivative
tolerances. The shared restart search runs with its old bundle cap disabled;
SciPy's integer maxiter/maxfun ceilings are 2³¹−1, so wall time is the practical
budget. This compares achievable endpoints under equal ceilings, not convergence
or a general method advantage.

Select the lowest normal-RMS **completed sampled-feasible** point from each arm;
keep failures and deadline-interrupted prefixes. Then run the existing fine
boundary checker (128²/512 coil nodes, both shifts, frozen current) and shared
continuous geometry/curvature routines. Preserve fail/unresolved outcomes. Only
these checks can distinguish a promising search point from a checked one; they
still do not establish topology or Step 3 benefit transfer.

Script: `scripts/explore_coherent_longrun.py`. Fresh output family:
`artifacts/coherent-longrun-v1/`. Run one thread, with 660 s worker/670 s supervisor,
256 MiB aggregate output and 3/2 GiB initial/live disk reserve. The selected
endpoints will receive the same interior-field diagnostic after optimization,
not be chosen on its values. No other heavy job runs concurrently.

All original thresholds stay fixed: boundary RMS 1e-4, maximum normal 1e-3,
interior RMS 0.01; length 3.5 m, curvature 12/m, coil/plasma clearance 0.06/0.08 m,
current 500 kA and relative loop-flux mismatch 1e-6. The exploratory 1e-2 signal
is already met, not a replacement for these gates.
