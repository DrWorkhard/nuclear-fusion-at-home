# Edge checks: reported robustness and remaining uncertainty

**Decision: retain partial robustness evidence; do not claim the original
200-transit confirmation is complete.** [Issue #20](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/20)
asked whether a positive vacuum trace result survives changes in start phase,
edge radius and direct versus interpolated field. The two reports below are
pjckoch's AI-assisted analyses, summarized from issue comments, not new runs or
external peer review. Both use `length-headroom-six-coil`, reference401 regenerated
with vmecpp, flux-normalized current and integration tolerance 1e-10.

## Six-start direct/interpolated comparison

The [4 October report](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/20#issuecomment-5982186760)
requested 200 transits at s={0.85,0.95,0.98}, theta={0,pi/2}. Direct and interpolated
fields gave the same terminations; signed iota agreed to five decimal places on
the four completed lines. The other two stopped early:

| Start | Reported original stop | Follow-up without a stopping rule, three transits |
| --- | --- | --- |
| s=0.95, theta=pi/2 | About 0.5 transit | 0/237 sampled points outside target polygon |
| s=0.98, theta=pi/2 | About 0.4 transit | 9/237 outside; maximum excursion 0.45 mm |

The first stop was attributed to the coarse h=0.02 m classifier. The second
follow-up found a small target-boundary excursion. A planned finer-classifier
200-transit run was stopped for low memory and remains incomplete. Agreement
between field representations in these cases does not generally bound accumulated
trajectory error, and the three-transit checks do not complete the requested test.

## Later direct-field edge check

The [6 October report](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/20#issuecomment-6009648566)
used twelve starts, s={0.95,0.97,0.99} and theta={0,pi/2,pi,3pi/2}, without a stopping
rule. All reached 132.7 transits; every twentieth integration step was checked
against the target-section polygon at its own toroidal angle.

| Nominal s | Reported sampled containment | Largest reported excursion |
| --- | --- | ---: |
| 0.95 | No outside samples at any of four phases | None reported |
| 0.97 | Outside samples at all three nonzero phases; none at theta=0 | 0.61 mm |
| 0.99 | Outside samples at all three nonzero phases; none at theta=0 | 0.90 mm |

The report describes no visible island chain in the phi=0 sections and no escape
over that interval. Sparse containment checks and visual sections cannot exclude
excursions between samples, small islands or longer-time transport. This is neither
particle/energy confinement nor the original six-start 200-transit comparison.

## Verified software change and evidence availability

[PR #33](https://github.com/DrWorkhard/nuclear-fusion-at-home/pull/33), merged as
`8eef532781345bdcb62505f9ae30be54d85f94b5`, makes `boundary` require polygon
confirmation at the stop point. `classifier_stop_inside_target` is inconclusive
and cannot pass the aggregate check. It does not test every trajectory point;
the 2000-vertex polygon is a finite boundary representation.
[Implementation](../../src/fusion_baselines/realized_field.py) and
[regression tests](../../tests/test_realized_field.py) retain that distinction.

The cited issue reports do not provide immutable producer/evaluator commits,
input/output hashes or an obtainable raw-data archive. Their numerical results
have not been independently reproduced for this summary. The separate 4 October
ten-line confirmation linked in the [tracing guide](README.md#realized-field-surfaces)
has its own archived provenance; it must not be used to fill those missing identities.
Resolving the original experiment requires its source-bound evidence and remaining
confirmation, not relabelling these partial reports. No scientific gate changes.
