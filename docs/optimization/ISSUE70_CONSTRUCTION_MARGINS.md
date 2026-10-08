# Construction-margin probe: current versus halved margins

**The construction margins are not the binding limit.** Halving every margin
toward its unchanged acceptance limit improves boundary RMS by 5.8%, far from the
preregistered factor of two. By the rule fixed in
[issue #70](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/70), the route
decision for joint plasma/coil optimization
([#36](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/36)) stands.
Recorded 8 October 2026; this is a route check, not physical acceptance.

## Question and method

Both arms of the [coil-freedom probe](ISSUE53_COIL_FREEDOM.md) ended at the fitter's
construction penalties. Do these self-imposed margins, rather than the coupling
between target and coils, cause the 0.0018–0.0020 boundary-RMS plateau?

| Margin | C: current | M: halved | Acceptance limit (unchanged) |
| --- | ---: | ---: | ---: |
| Length penalty / selection cap | 3.44 / 3.45 m | 3.47 / 3.475 m | 3.5 m |
| Coil–coil penalty | 0.07 m | 0.065 m | 0.06 m |
| Coil–plasma penalty | 0.09 m | 0.085 m | 0.08 m |
| Curvature penalty | 10 /m | 11 /m | 12 /m |

The arms ran sequentially on the maintainer's machine (macOS, Python 3.12.13,
SIMSOPT fork `a79006b`, one thread), each with 1800 s search and 900 s checks:
six order-5 coils from the length-headroom seed, reference401 through the portable
intake with the archived maintainer Wout (`83dc45b9…`). Code: the `--margins`
preset in `scripts/fit_coils.py` on `main`'s fitter. The seed conversion reproduced
the archived boundary RMS 0.0019962675 and interior 0.011483 as a positive control.

## Result

| Diagnostic | C: current | M: halved |
| --- | ---: | ---: |
| Search time (monotonic); termination | 1795 s; budget | 1796 s; budget |
| Fine boundary RMS | 0.0018339 | 0.0017283 |
| Fine boundary maximum (shift 0 / 0.5) | 0.008488 / 0.008384 | 0.008063 / 0.008011 |
| Interior RMS (64/512) | 0.010115 | 0.009015 |
| Continuous geometry | Pass | Pass (needed finer level) |
| Length / coil–coil / coil–plasma bound | 3.4701 / 0.0609 / 0.1392 m | 3.4852 / 0.0606 / 0.1495 m |
| Curvature upper bound | 10.04 /m | 11.05 /m |
| Traced lines (10, 200 transits); max \|Δι\| | 10/10; 0.0065 | 10/10; 0.0058 |

**Rule:** M/C boundary RMS = **0.942**, against the required ≤ 0.5. M passes
continuous geometry at the unchanged limits and its interior RMS is lower (below
0.01 in this run), but the boundary condition fails, so the route decision stands.
Both arms still fail the boundary limits by about 17–18×.

Both selected candidates sit exactly at the length, curvature and coil–coil
penalties; coil–plasma distance is not active. With halved margins the continuous
coil–coil bound leaves 0.6 mm to its limit and the length bound passed only after
refinement, so halving is close to what the acceptance checks admit. As
preregistered, this outcome is passed to the joint pilot protocol
([#59](https://github.com/DrWorkhard/nuclear-fusion-at-home/pull/59)) as information.

C reproduces the #53 control (0.0018486, interior 0.010240) within 0.8% and 1.2%
on a different machine. The Mac slept several times during arm C; the monotonic
search clock does not advance during sleep, so both arms received equal search time.

## Limits and availability

One seed, one budget and one local optimizer per arm on one machine; halving is one
point between the current margins and the limits. Geometry bounds are padded
floating point; tracing is a vacuum diagnostic. Raw outputs (about 390 MB, including
every trial) are retained locally under the ignored
`artifacts/issue70-construction-margins/`; they are not archived under an evidence
tag. Key SHA-256 values: seed `3be11b60…`, selected snapshots C `ae2d6264…` and
M `4eab51eb…`, reports C `da849c1e…` and M `cae5dfbe…`.
