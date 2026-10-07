# Smaller-step gain survives phase and resolution checks

The separately [registered validation](ISSUE37_STEP_VALIDATION.md) completed once
on 7 October 2026 with a **positive** verdict. The fixed +0.35 mm target's ideal
score is **3.258% lower** than the original on both validation grids, passing the
1% hurdle. Both target refinement checks also pass.

| Score | Original | Fixed +0.35 mm |
| --- | ---: | ---: |
| 1601 toroidal points, 32 shifted phases | 0.00023891450330677452 | 0.00023113042039782 |
| 3201 toroidal points, 32 shifted phases | 0.00023893120600164904 | 0.00023114618386330612 |
| Relative refinement change | 0.000069906 | 0.000068197 |

All 140 surface/pitch cells completed. Four fresh scores with unchanged numerical
intake took **49.83 s** of one 180 s allowance. Both frozen equilibria were reused
explicitly; no solve, fitting or matched-compute claim is involved. Final clock
disagreement was 0.03764 s. All four admission/sample/post-run host observations
passed (one sample followed completion); the owned assertion was released and
verified absent. Sampling does not prove continuous host stability or controlled load.

This establishes limited phase/resolution robustness of the fixed ideal-target
gain. Candidate phases are new, but score family, machine and comparator grids
are previously used. It is not external/statistically independent confirmation,
coil feasibility, realized-field benefit, optimality or physical acceptance.
The [earlier two-point recipe](ISSUE37_AWAKE_RESULT.md) still has verdict **change**.
The next decision concerns coil feasibility for this frozen target under a
separately registered fitting/check budget; the ideal gain cannot answer it.

Clean producer/evaluator: `91a4ef7ec1b3cc1117242ae0abd171002d12edd1`.
Local archive: `5c73b3bdafdc112a4b10435022ad1a391d0c159d`; prepared tag
`evidence-issue37-step-validation-v1`, publication pending. It preserves all
58 raw files (53,360,215 bytes), both Wouts, original cold receipts, exact
configuration/inventories and host records. The 87-entry manifest SHA256 is
`62f0aa9bf8da7705b483d6b9eaa395dc2081e772f660c8b2e584beb1ee23c087`.
Original raw outputs and native environments remain intact.

Saved-array replay verifies 99 retrospective bindings and reproduces all 140
action cells, both refinement checks and the decision exactly. It does not rerun
equilibrium solving, numerical intake or fields, validate coils or re-attest
historical timing/host conditions. The archive documents reproduction and local
availability. Agent review is not external physics peer review.
