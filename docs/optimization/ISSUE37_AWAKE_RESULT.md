# Awake joint comparison: the registered two-point recipe misses its hurdle

The separately [registered v2 attempt](ISSUE37_AWAKE_FOLLOWUP.md) completed on
7 October 2026 with verdict **change**. Both fresh cold equilibria and capped
coil fits completed; training selected the +1 mm proposal. Its held-out ideal
action variance was about **9.17% worse** than the control at both resolutions,
so it failed the required 1% improvement. The original [interrupted v1](ISSUE37_JOINT_RESULT.md)
remains inconclusive and is not pooled with this result.

| Diagnostic | Control | Selected joint (+1 mm) |
| --- | ---: | ---: |
| Held-out ideal score, 1601 points | 0.0002389145033 | 0.0002608183924 |
| Refined ideal score, 3201 points | 0.0002389312060 | 0.0002608317758 |
| Worst fine boundary RMS | 0.001905241050 | 0.001922955685 |
| Worst maximum normal error | 0.008944016998 | 0.008842763620 |
| Finest interior RMS | 0.010429552155 | 0.010340522904 |

Boundary/interior ratios **1.00930 / 0.991464** pass the 1.10 nonregression
screens. Geometry, current, flux, all ten 200-turn traces per selected arm and
held-out refinement checks pass. Both still fail absolute boundary RMS/max and
interior limits. Nestedness was not tested; the actual-coil benefit endpoint
remains null and physical acceptance false. Only this fixed basis/recipe is
unsupported; this is not a general verdict against joint optimization.

C completed diagnostics after 2201.54 s and J after 1341.77 s on their original
arm clocks, within the unchanged allowances. Final recorded wall/monotonic
differences were 0.09805 s / 0.00731 s. All 53 admission/run/post-run AC/assertion
observations passed. Post-science cleanup initially hit a sandbox signal denial;
an authorized second signal succeeded and verified assertion removal. Both
attempts remain recorded. The query itself succeeded, and the reviewer found
this resolved cleanup problem did not trigger the registered invalidators.
Sampling does not prove continuous host conditions or controlled external load.

Clean producer/evaluator: `b9cab3190a971d5f75387bdef29432da5bf93f22`.
Local archive: `6241c428d47c8a5d23600915d5e0bb23f7414215`; prepared tag
`evidence-issue37-joint-comparison-v2`, publication pending. It preserves all
7,329 raw files (231,380,753 bytes), exact inputs/configuration, inventories and
host records. The 7,349-entry manifest SHA256 is
`287838c0bd1aeb009baeaf6a4d76e781cc63bdb6644b30f5be60195bc112ca43`.
Original outputs and native environments remain intact.

Fresh shallow replay verified 82 retrospective bindings, zero discrepancy in
fine/interior independent B/A controls, all 245 saved ideal-action cells and 20
trace classifications exactly, and the selected-pair decision. It did not rerun
solves, optimization, native fields, intake, geometry or trajectory integration,
or re-attest timing. Host-condition interpretation was reviewed separately;
agent review is not external physics peer review. The archive supplies the exact
replay command and local input availability.

Both registered offsets also scored worse than C in training. A separately
registered [smaller-step screen](ISSUE37_STEP_SCALE_RESULT.md) subsequently passed
its training threshold; validation is still required before another coil comparison.
This does not change the present comparison's verdict or acceptance gates.
