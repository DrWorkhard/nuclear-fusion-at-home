# Local homotopy curvature: method and input review

26 September 2026. [Protocol](LOCAL_CURVATURE_PROTOCOL.md) · [Index](README.md)

## Decision and scope

The prospective method and twelve fixed inputs passed independent internal
review before implementation. This permits implementation and qualification,
not optimizer integration or a physical design claim. No new curvature bound,
field, gradient or equilibrium was calculated during this review.

The exact-arithmetic whole-rectangle inequality is valid. The floating-point
version has explicit safety padding but is not a rigorous interval proof.
Dyadic coverage includes the full original-seed-to-candidate path; endpoint
curvature and sampled maxima cannot substitute for that requirement.

## Findings incorporated

- Use global derivative bounds over each entire rectangle, including the
  third derivative and period-one `2*pi*m` factors. Retain every actual physical
  transformation and the original seven non-curvature gates.
- Specify numerical padding, complete binary trees rather than equal-depth
  leaf pairs, exact caps and independently reconstructed work counts.
- Process physical copies in saved order. The parent owns the absolute clock;
  timeout fails the whole phase even when previously published curves passed.
  Only failure/frontier publication may use the remaining five-second grace.
- Distinguish attempted deadline leaves from unchecked pending leaves, including
  expiration during a bound or after the last bound. Reproducible arithmetic
  cannot turn a timed-out phase into success.
- Retain rejected proposals as named coefficient states with old certificates;
  they have no evaluated field bundle, objective or gradient.

The maximum DFS depth is 24, path length 48 characters and pending frontier 25.
The specified node envelope fits within 8 MiB; implementation must still check
actual serialized bytes, state budgets, publication and failure paths.

## Input verification

The [manifest](../../evidence/local-curvature-inputs-v1.json) is 39,784 bytes,
SHA-256 `ca9c3bac130080cb261660abf18d6de29872c58f7d305114b06ee061969beca5`.
Reviewer `local_curvature_review` independently rehashed all 53 listed references;
including all terminal rejection certificates, it checked 83 unique files /
15,832,331 bytes. All twelve named-coordinate hashes, exact coefficient bits,
seed/report/index/case bindings, physical mappings and old gates agree. The
selector reproduces the final manifest byte-for-byte.

The two preselected rejections are reference-n6-N trial 94 / iteration 17 /
backtrack 0 and reference-n8-N trial 50 / iteration 12 / backtrack 0. Both fail
only the old curvature gate and have no field evaluation. The remaining ten
states are both original seeds and all eight existing coarse selections.

The reviewer corrected two overly strict initial assumptions: constants are
active parameters and selected snapshots also contain current fields. A draft
manifest hash mismatch occurred while the fine evidence was being finalized;
the final stable manifest passes. These were reviewer corrections, not changes
to historical evidence. Process inspection was sandbox-denied; only lightweight
metadata checks ran.

## Retained review

The ignored report `artifacts/local-curvature-v1/method-input-review.json`
contains the full review: 6,798 bytes, SHA-256
`6451234f6f8260e6a7c0b164a6bbe63c6371f1e960c2647e1c93f0c16005c52f`.
It binds the final draft, input manifest and selector. The registered protocol
adds navigation, finalized input references and spacing, without changing the
reviewed equations or rules. Earlier read-only discussion by
`protected_budget_impl` informed the whole-homotopy specification.

This is internal numerical/method review, not external peer review, a second
physical experiment or implementation qualification. Software tests, independent
arithmetic/coverage checking and the actual twelve-state study remain required.
