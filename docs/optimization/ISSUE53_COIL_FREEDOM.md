# Coil-freedom probe: order 5 versus order 8

**Coil freedom is not the binding limit.** With 55% more Fourier coefficients the
boundary RMS improves by 3.6%, far from the preregistered factor of two. By the
rule fixed in [issue #53](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/53),
the next route is joint plasma/coil optimization
([#36](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/36)).
Recorded 8 October 2026; this is a route decision, not physical acceptance.

## Question and method

Does the 0.0019–0.0020 boundary-RMS plateau of the
[stalled fixed-target recipe](STEP4_RESEARCH_PROGRAMME.md#decision-of-6-october-2026)
come from too little coil freedom? Two preregistered arms ran sequentially on one
machine (macOS, Python 3.12, SIMSOPT fork `a79006b`, one thread), each with 1800 s
search and 900 s checks, on reference401 through the portable Wout intake:

- **C:** six base coils, Fourier order 5 (198 coefficients), length-headroom seed.
- **P:** the same coils lifted to order 8 (306 coefficients) with exact zeros, so
  both arms start from identical geometry.

Code `ae29c55` (merged unchanged as [#57](https://github.com/DrWorkhard/nuclear-fusion-at-home/pull/57),
`9ecdf27`), using the #55 fitter (`ftol=0`, recoverable trial failures). Objective,
penalties, selection rule, fine-boundary, continuous-geometry, interior and
direct-field tracing checks are unchanged.

## Result (run 2, result of record)

| Diagnostic | C: order 5 | P: order 8 |
| --- | ---: | ---: |
| Search time; termination | 1792 s; budget | 1792 s; budget |
| Fine boundary RMS | 0.0018486 | 0.0017815 |
| Fine boundary maximum (shift 0 / 0.5) | 0.008566 / 0.008426 | 0.008398 / 0.008660 |
| Interior RMS (64/512) | 0.010240 | 0.009859 |
| Continuous geometry | Pass | Pass |
| Maximum length bound | 3.4698 m | 3.4642 m |
| Coil–coil / coil–plasma lower bound | 0.0613 / 0.1387 m | 0.0649 / 0.1451 m |
| Traced lines (10, 200 transits); max \|Δι\| | 10/10; 0.0058 | 10/10; 0.0069 |

**Rule:** P/C boundary RMS = **0.964**, against the required ≤ 0.5. P's geometry
passes and its interior RMS is lower, but the boundary condition fails, so the
alternative is joint plasma/coil optimization. A first run on a superseded fitter
gave 0.963. Both arms still fail the boundary limits by about 18×; P's interior RMS
is below 0.01 in this single run.

## Active margins and open question

Both arms end at the optimizer's construction penalties, not at the acceptance
limits: curvature at about 10 /m (acceptance 12 /m) and length at 3.46–3.47 m
(penalty from 3.44 m, acceptance 3.5 m); C is also near the 0.06 m coil–coil
clearance. A separately preregistered [construction-margin probe](ISSUE70_CONSTRUCTION_MARGINS.md)
later halved every margin and gained 5.8%; it does not change this decision.

## Limits and availability

One seed, one budget and one local optimizer per arm on one machine; order 8 is one
point in coil-family space. Geometry bounds are padded floating point; tracing is a
vacuum diagnostic. Results were reported by the contributor (@pjckoch) and have not
been rerun by the maintainer. The preregistration, logs, selected snapshots and
hashes are retained by the contributor, not archived in this repository. Full
report: [issue #53, run 2](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/53).
