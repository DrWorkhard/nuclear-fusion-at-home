# Coil-freedom probe: allocate the next effort to joint optimization

**Decision: move to a bounded joint plasma/coil comparison.** The completed local
[#53](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/53) probe lowers
boundary RMS by **3.78%**, missing its frozen **50%** hurdle. Geometry passes and
interior error improves, but both boundary acceptance gates still fail. This
allocates research effort; it does not prove why the fitter plateaued or rule out
other coil families.

Clean producer/evaluator: `fd99245147308b9dbd23473002968e3283bd08fe`; its full
prospective protocol is preserved at this page's path in the archive. C then P
used the same original length-headroom snapshot and reference401 Wout. P added only
zero Fourier modes 6–8 to the six order-5 coils. Target flux/B², penalties and
acceptance limits stayed fixed; selected currents were frozen for diagnostics.
Each arm had 1800 monotonic seconds for search including intake/startup, then at
most 900 shared diagnostic seconds, one native thread and 256 MiB retained output.
Both searches exhausted their allowance; late trials could not win. No rerun was
used to cross the hurdle.

| Local diagnostic | C: order 5 | P: order 8 |
| --- | ---: | ---: |
| Fine boundary RMS, worst of two shifts | 0.00183501529 | 0.00176571369 |
| Fine maximum normal error | 0.00844233727 | 0.00827467258 |
| Finest interior vector RMS | 0.0101035400 | 0.00948113791 |
| Continuous geometry checks | Pass | Pass |
| Frozen current (A) | 307796.43 | 307603.43 |
| Direct lines completing 200 transits | 10/10 | 10/10 |
| Maximum signed-iota mismatch | 0.00629386 | 0.00584157 |
| Total monotonic seconds, including diagnostics | 2046.71 | 2078.83 |

P/C boundary RMS is **0.9622337751**, above the required 0.5. P passes the individual
0.01 interior limit; neither arm passes boundary RMS 1e-4 or maximum error 1e-3.
Length upper bounds are 3.47012 / 3.46487 m against 3.5 m; coil-clearance lower
bounds are 0.060715 / 0.064766 m against 0.06 m. Full geometry and per-line records
remain in the archive. Target-labelled vacuum traces do not establish nestedness,
common realized flux labels, confinement or benefit transfer.

**Timing qualification:** fit-to-trace wall timestamps span 10239 / 5039 s, versus
1806 / 1819 monotonic seconds for fitting and its checks. The discrepancy's cause
is unknown; suspension or clock adjustment is possible. External host load was not
verified. Do not claim controlled wall-time throughput or a causal/global comparison.

Separately, pjckoch's [reported run 2](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/53#issuecomment-6026203139)
at `ae29c55`, using portable target intake, reports boundary RMS 0.0018486 / 0.0017815
(P/C approximately 0.964) and the same next-step choice. Those are different source/
input states, not the local numbers above. Run 1 was superseded. The comment's run-2
artifacts have not been independently replayed here; agreement in the decision
is not proof that coil freedom is not the binding physical limit.
The [published contributor record](https://github.com/DrWorkhard/nuclear-fusion-at-home/blob/ce5794fdde91bbe38e046e5272cb71f5eb5bb7d9/docs/optimization/ISSUE53_COIL_FREEDOM.md)
retains its full diagnostic table and margins: reported interior RMS 0.010240 /
0.009859, geometry passing, and curvature near the 10/m construction penalty
versus 12/m acceptance. Those artifacts remain contributor-retained; their
publication or independent replay is not supplied by our separate archive.
Relaxing construction margins is untested and does not change this decision.

Published annotated tag [evidence-issue53-coil-freedom-v1](https://github.com/DrWorkhard/nuclear-fusion-at-home/tree/evidence-issue53-coil-freedom-v1) resolves to archive
`293d0a65601c8293c936617f720fcfe099b3a27f`, tag object
`a76dc5d124203a4556d9a5f6eecc96c129bc1d03`; **published; remote identities and manifest retrieval verified**.
Manifest SHA256: `68f33e1f56539610a5b3ae6c2a768100fb8c20062a2094063b589cbef635cfbe`.
All 37,859 evidence entries and 40 producer source hashes were verified again in
the shallow archive checkout. Saved fine/interior metrics, sampled independent B/A
and line summaries replay; optimization, geometry and trajectories do not. The
original Wout remains local; NumPy/SciPy suffice for saved-array replay. The archive
README supplies commands and exact inputs. Original outputs/environments are
preserved. Agent review is not external peer review; [Step 4](../steps/STEP_4_PLASMA_AND_COILS.md)
remains incomplete.
