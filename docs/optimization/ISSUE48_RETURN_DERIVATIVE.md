# Explicit derivatives preserve the rejected step's neighborhood decision

The [local periodic-return search](ISSUE48_PERIODIC_RETURN.md) stopped when its
next trial left the frozen 10 mm neighborhood. A bounded derivative check now
finds that the original step magnitude is sensitive to the derivative calculation,
but finer calculations still propose leaving that neighborhood. This does not
resolve the failed continuation contour or change its 19/20 qualification.

At the same seed, central differences of 10 and 5 micrometres at each of two
tracing/coil resolutions produce Newton step norms **36.636776–36.638572 mm**.
Their maximum pairwise difference is **1.796 micrometres**, within the preregistered
1 mm agreement threshold; all exceed the 11 mm diagnostic margin around the
unchanged search boundary. Saved forward differences reconstruct the original
53.168952 mm proposal. The finer residual Jacobians remain ill-conditioned
(condition numbers about 141,330–141,337). Numerical agreement is not a rigorous
error bound or proof that a Newton step leads to a root.

No proposed point was evaluated and no new root search was performed. The result
does not justify widening the neighborhood or establish periodic-orbit existence,
islands, nested surfaces, confinement or benefit transfer. Both resolutions share
the native field kernel. The original failed search and its bounds remain intact.

Clean producer/evaluator: `570660c2674905f5175b47311049f98c88350843`.
One attempt completed in 25.121912 s supervised total, within 180 s driver after
imports / 210 s outer limits, one thread, 256 MiB, 3/2 GiB disk reserves and 5 s
clock discrepancy. Source/input identities and 1,662 native package files matched
before and after; process cleanup was confirmed. The producer passed 303 research
and 65 public tests, documentation, Ruff and diff checks. Agent review preceded
execution; it is not external peer review.

Published evidence: annotated tag [evidence-issue48-return-derivative-v1](https://github.com/DrWorkhard/nuclear-fusion-at-home/tree/evidence-issue48-return-derivative-v1), archive
commit `25ccd53ea487a7b16690443591233a9c715ad7c5`, payload
`evidence/issue48-return-derivative-v1/`, manifest SHA-256
`999f83cea0d64d55ea9cb856c0ec6782a2a537376f27ab4a7560b65eae37c205`.
Its 23-file manifest and 58 source/input bindings preserve samples, reports,
original consumed archive subsets, configuration, protocol, tests and replay.
Raw outputs remain separately at `/private/tmp/issue48-return-derivative-v1`.
The archive is published; remote identities and manifest retrieval verified.
Original local outputs and external native dependencies remain separately retained.

With NumPy, the archive's `replay.py --manifest-sha <above SHA-256>` checks all
identities and independently coded arithmetic for the original and four refined
steps, using the same NumPy linear algebra routines. It does not repeat field
maps, integration, native environment checks or timing. The archive README gives
the exact producer command and relocation instructions; native binaries remain
external. See the [archive procedure](../validation/REPRODUCING_RESULTS.md).
