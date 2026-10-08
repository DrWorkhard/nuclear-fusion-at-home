# Stop the inconclusive local periodic-return search branch

**The bounded-step search also stops at the unchanged 10 mm neighborhood guard.**
It yields no qualified periodic point or topology classification. Together with
the [original search](ISSUE48_PERIODIC_RETURN.md) and
[derivative check](ISSUE48_RETURN_DERIVATIVE.md), this completes the local solver
diagnosis. Stop this branch; another solver variant needs a new decision-relevant
reason. Do not widen the neighborhood or alter the contour gates to obtain a result.
The continuation's failed contour and original 19/20 qualification remain unchanged.

One trust-region attempt used the same seed and direct eleven-period map, explicit
5 micrometre central derivatives, and scaled physical R/Z coordinates/residuals.
Fifteen evaluations completed: three search positions and twelve derivative probes.
The sixteenth trial started **10.000235 mm** from the seed and was rejected before
field evaluation. Box bounds did not override the Euclidean guard. The smallest
evaluated return residual was **2.830969 micrometres**, reduced from 270.266208,
but above the frozen **0.001 micrometre** root threshold. No final solver return,
second-resolution root, independent orbit-field check or matrix classification
was reached. This does not establish either presence or absence of periodic orbits,
islands or usable surfaces, and does not qualify launch matching or benefit transfer.

Clean producer/evaluator: `4bf5eab45b7637b94c052bc7112834e6a30130eb`.
The attempt took 16.858088 s supervised total, within 300 s driver after imports /
330 s outer limits, one thread, 256 MiB, 3/2 GiB reserves and 5 s clock discrepancy.
Scientific and supervisor records remain incomplete; cleanup was confirmed.
A separate post-failure check matched 59 direct sources/inputs and 1,662 native
package files. It is not a successful scientific completion receipt. The producer
passed 306 research / 65 public tests, docs, Ruff and diff checks; adversarial
review preceded execution. Agent review is not external peer review.

Published annotated tag: [evidence-issue48-bounded-return-v1](https://github.com/DrWorkhard/nuclear-fusion-at-home/tree/evidence-issue48-bounded-return-v1); archive commit
`3e908b770f75b0e88979621ef75a45dfd6dbb972`; payload
`evidence/issue48-bounded-return-v1/`; 21-file manifest SHA-256
`556c62bbab0767bd2e84ada02e8b2bcf97d5522c1226122faf3e8363e7b3284f`.
All six original raw files remain at `/private/tmp/issue48-bounded-return-v1`
and are archived byte-for-byte with consumed inputs, code, protocol, configuration,
tests and environment identities. The archive is published; remote identities and manifest retrieval verified.

With NumPy, archive `replay.py --manifest-sha <above SHA-256>` verifies identities,
reconstructs the seed, checks trial statuses/distances and recomputes the minimum
saved residual. It does not repeat fields, integration, optimization, derivatives,
environment checks or timing. The archive README gives full numerical reproduction
and relocation instructions; native binaries remain external, no Wout is needed.
See the [archive procedure](../validation/REPRODUCING_RESULTS.md).
