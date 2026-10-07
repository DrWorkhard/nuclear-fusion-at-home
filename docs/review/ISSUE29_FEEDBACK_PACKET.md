# Draft technical feedback packet: comparing realized coil fields

**Review question:** what is the smallest defensible common-coordinate diagnostic
for comparing plasma benefit between these two realized coil fields, when one
arm fails toroidal-flux contour reconstruction? Advice on whether the present
admission test is suitable, or on one bounded replacement test, would change the
next experiment before a confirmatory joint-optimization claim. No superiority,
confinement, reactor feasibility or external endorsement is claimed.

This is an unsent proposal for #29. The [roadmap proposal](../PROJECT_PLAN.md)
separates permissioned technical feedback from MS1's comparative-advantage claim;
maintainer adoption and any actual contact remain undecided. Agent review is not
external physics review. Scientific checkpoint: local revision
`c26de6d1c3684279965c0ea7b2db9a2b8010be5d`.

## Question and retained negative evidence

The [matched experiment](../optimization/ISSUE25_MATCHED_TARGETS.md) fits the
original and improved Step 3 targets from the same coil seed with matched 300 s
search budgets. Each fit uses its own frozen target-flux/B² normalization.
Both fail field acceptance. Both wide action diagnostics retain missing-well
failures, so the 5.07% lower narrow target-launch score cannot demonstrate benefit
transfer. Errors against different targets are not a common physics endpoint.

The [full label grid](../optimization/ISSUE48_FULL_GRID.md) qualifies 20/20
original-target launches and 18/20 improved-target launches. A distinct
[lower-error continuation](../optimization/ISSUE48_CONTINUATION_LABELS.md) reaches
19/20. Failed reconstructions remain failed; neither replacing the target axis
nor refining two traces resolves the continuation failure. Local root searches
are inconclusive. These results do not prove islands, loss of surfaces or nestedness.
Geometric launch theta is not PEST alpha; symmetry pooling may mix components.

The requested response is a critique or one minimal discriminating test with
explicit coordinates, failure handling and numerical controls. A negative answer
is useful. No recipient, deadline or obligation to respond is assumed. Leave all
physical gates unchanged; validate any replacement estimator separately.

## Obtainable material and availability limits

| Material | Identity and scope |
| --- | --- |
| Published matched evidence | [Archive `05a4511`](https://github.com/DrWorkhard/nuclear-fusion-at-home/tree/05a4511084912fea9bd8d03e81f01018882396b8/evidence/issue25-matched-v1), tag `evidence-issue25-matched-v1`, producer/evaluator `a551289e63e44d7dbae7b5d5a0e5f4b6026db257`. README gives saved-array replay, commands and failures. NumPy/SciPy replay needs no Wout; it does not repeat native fields or tracing. |
| Published portable starter | [Checker/quickstart at `aab7f9b`](https://github.com/DrWorkhard/nuclear-fusion-at-home/blob/aab7f9bb2b33890971d140ec375b4b9eb8820944/docs/validation/PUBLIC_QUICKSTART.md). Standard-library sampled/dense boundary diagnostics expose conventions; they do not verify realized surfaces. |
| Prepared dense interior checker | [#10 packet](../../examples/clear-coil-interior-v1/README.md), manifest SHA-256 `9f9b32ffb6176b22e149069896500da0ac1aa0c371b5f17be7fa7603ebfb2ccb`. Both frozen targets work without native dependencies; publication is pending. |
| Prepared realized-label evidence | [Original grid](../optimization/ISSUE48_FULL_GRID.md) archive `2ee186bb347245072c98d983a42b06f8e02a16a9`; [continuation](../optimization/ISSUE48_CONTINUATION_LABELS.md) archive `191875d231b396e5960cbd9460a37a6c462b6381`. Summaries bind producers, manifests, failures and replay limits. Both archives remain local-only. |

Published archive manifest SHA-256:
`3f8ddda02e28f018c466d396aa1c93cf81a6cf90f2e63a934b0d44aa67534d1b`;
annotated tag object `fcbdbe28ba77c2f327546dcb6e01fc9743e5bc07`.
Original Wouts/native validation inputs remain maintainer-local. The prepared
packets do not complete native reproduction, supply external physics review or
establish a common realized-surface endpoint. Retain Goodman/CC BY 4.0 data credit
and project source licensing from the linked records.

Before sending a packet relying on new #48 findings, publish and verify their
evidence/source states under separate authority, replace local-only references
with obtainable pinned links, and have another checkout follow the stated replay
instructions. Alternatively, a narrower request can use only the already-published
#25 failure. No contact or publication occurs through this proposal; #29 remains
open for the maintainer's policy decision.
