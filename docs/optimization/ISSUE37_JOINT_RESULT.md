# Joint feasibility attempt: interrupted by host clock disagreement

The first [registered joint comparison](ISSUE37_JOINT_FEASIBILITY.md), run on
7 October 2026, is **inconclusive**. It does not answer whether either fixed
plasma perturbation improves the matched coil/plasma result. The
[reviewed native driver](ISSUE37_COMPARISON_DRIVER.md) stopped during the first
cold perturbed equilibrium solve when its clocks disagreed beyond the 5 s limit.
No scientific operation was retried.

The control completed its declared search cap, froze trial 2367 and completed
all diagnostics. Its worst fine boundary RMS **0.00190529**, maximum normal error
**0.00896720** and finest interior RMS **0.01043189** still fail the unchanged
absolute gates. Continuous geometry, current/flux checks and all ten 200-turn
traces pass their existing checks; nestedness was not tested. Held-out ideal
action variance is **0.0002389145**, refining to **0.0002389312** within tolerance.
These are control observations, not a paired improvement or physical acceptance.

The first J solve's parent recorded **30.3844 s monotonic / 44.9361 s wall**,
a **14.5516 s** discrepancy, and successful cleanup after SIGTERM. It produced
no completed Wout or post-execution source/environment attestation. The minus
proposal and J coil fits never began. Intermediate solver residuals do not
establish numerical nonconvergence. A scoped OS log records a 17 s maintenance
sleep overlapping the interruption, consistent with host suspension. C's final
4.1299 s clock difference remained within its registered gate. External host load
was not verified; no controlled-throughput claim is supported.

Clean producer/evaluator: `e55dd75fbc2c1be679ba96e1aa1c9e242039b860`.
Local archive: `0167ff9f4541247739f37db586cfe57bec785e12`, prepared tag
`evidence-issue37-joint-comparison-v1`; publication is pending. It retains all
4,826 original raw files (98,512,278 bytes), seed/Wout, exact configuration and
inventories, review, launch/error and selected sleep-event records. The 4,840-entry
manifest SHA256 is `22866d409aed40373a952e6fe573cc1196294f95249fe8cebf7c1f854597b7c7`.
Original outputs and native environments remain intact.

Fresh shallow replay verified 56 retrospective source/input bindings, reproduced
independent B/A controls with zero discrepancy, all 105 saved ideal-action cells
and all ten saved trace classifications exactly. It did not rerun optimization,
equilibrium/intake, native fields, geometry or trajectory integration, or re-attest
timing. The archive supplies the replay command and availability limits. Review
is by an agent, not external physics peer review.

The next decision is how to obtain an uninterrupted, separately registered
comparison on a suitable host. A short [temporary sleep assertion check](../validation/JOINT_EXECUTION_HOST.md)
supports assertion availability on AC, not long-run stability. Preserve this failed attempt; do not relax the
clock gate, reuse its control as free work, or treat interruption as evidence
against joint optimization. The actual-coil benefit endpoint remains null.

A separately registered [v2 comparison](ISSUE37_AWAKE_RESULT.md) subsequently
completed with verdict change. This v1 record remains inconclusive.
