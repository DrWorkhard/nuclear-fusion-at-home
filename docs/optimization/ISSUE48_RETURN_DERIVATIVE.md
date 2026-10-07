# Prospective derivative check of the rejected return-map proposal

Decision: does the 53.169 mm proposal that stopped the bounded periodic-return
search persist with explicitly scaled central differences? Saved forward trials
use R/Z steps about 14.38 nm / 0.28 nm and reconstruct a residual-Jacobian condition
number around 205,000. This suggests checking derivative sensitivity before any
new root search; it does not establish inaccurate derivatives or physical topology.

Freeze the exact seed, failed trials and snapshot from archives
`5c6940bddd9f799803326c51ac2dc8ced21f69c1` and
`d12b01bedbb3d4e89ab891d03a9e6048f0690918`. Bind both manifests and every consumed
file. Reconstruct the original forward-difference residual Jacobian and Newton
proposal from the five completed evaluations. Preserve the sixth rejected trial.

Reuse the same eleven-field-period map and numerical settings as the failed
study: 512 nodes with rtol=1e-10/atol=1e-12, and 1024 with 1e-11/1e-13;
DOP853 maximum step pi/100. At the same frozen seed, compute the residual and
central return-map derivatives with physical steps 1e-5 and 5e-6 m in R and Z.
Subtract the identity to obtain the residual Jacobian, then solve J delta=-F.
Record samples, full matrices, singular values, condition numbers and proposals.
Do not evaluate fields at the proposed points or start another root search.
No determinant/trace topology classification is appropriate away from a root.

The four new proposals agree for this test only if their maximum pairwise
distance is <=1 mm. If they agree and all norms exceed 11 mm, explicit differences
still propose leaving the frozen 10 mm neighborhood; if all norms are below 9 mm,
the proposal is sensitive enough to the derivative method to change that guard
decision. Otherwise report unresolved. These 1 mm margins are diagnostic,
not a changed search bound or physical acceptance criterion. No rigorous derivative
error bound or attribution to one numerical change follows.

One attempt: 180 s inside the driver after imports / 210 s including supervision,
one thread, 256 MiB, 3/2 GiB reserves and 5 s clock discrepancy. Reuse the recorded
environment and owned-process checks. Analytic affine-map tests qualify subtracting
the identity, the proposed step and ambiguous decisions. No retries or tuning.
Preserve all original outputs and the failed study unchanged. No flux labels,
current, field model, contour qualification or 19/20 verdict changes. Adversarial
review precedes local integration; publication remains unauthorized.
