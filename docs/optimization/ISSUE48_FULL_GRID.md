# Full nominal grid exposes a selected-fit coverage failure

**Reference401 qualifies at 20/20 launch points; selected401 at 18/20.** Both
bounded runs completed, but the complete paired flux-label map is unqualified.
The two failures are selected-fit launches at nominal s=0.50, geometric theta
pi/2 and 3pi/2. This tests both original
frozen [issue #25 fits](ISSUE25_MATCHED_TARGETS.md), without changing coils, currents,
targets or launch positions.

The table reports only surfaces whose four phases and controls qualify. Offsets
are absolute differences from nominal s; spreads are maximum minus minimum
estimated label over geometric launch phases, in normalized-flux units.

| Nominal s | Reference max offset | Reference spread | Selected max offset | Selected spread |
| ---: | ---: | ---: | ---: | ---: |
| 0.10 | 0.001236 | 0.002147 | 0.001644 | 0.002432 |
| 0.25 | 0.004145 | 0.006575 | 0.004794 | 0.007053 |
| 0.50 | 0.011721 | 0.013718 | unqualified | unqualified |
| 0.75 | 0.034779 | 0.021184 | 0.035065 | 0.018238 |
| 0.90 | 0.068137 | 0.019374 | 0.074883 | 0.016381 |

## Retained failures and next decision

For selected theta=pi/2 at s=0.50, the 320/640-crossing spline develops a nonpositive
radius; no final label is admitted. For theta=3pi/2, the final angular gap is
1.1793 rad (limit 0.4) and last-prefix label change 0.0040333 (limit 0.0005).
All other points and all analytic/target/edge controls pass. The archived section
plot shows clustered crossings with large gaps for these two launches. It does
not identify their dynamical cause or prove magnetic islands.

Finer quadrature cannot supply missing contour coverage. The qualified outer
surfaces show large nominal-label offsets in both fields, but incomplete mid-radius
coverage blocks a full common-coordinate claim. No failed point is removed or retried.
The separate [continuation grid](ISSUE48_CONTINUATION_LABELS.md) tests a different
candidate and does not replace or requalify these original fits.

## Method and evidence

Clean producer/evaluator `130347fe29e03852e257a63d0ce6ab9f828d2c85` contains the
prospective protocol and received read-only adversarial review before execution.
The archived driver uses both original issue #25 snapshots/Wouts, five nominal
surfaces and four geometric phases per surface.
Direct 512-node tracing provides 320 full turns, with symmetry-checked phi=0/pi
pooling and 160/320/640-crossing prefixes. The previously qualified interval
Gauss 4/8 estimator retains all reconstruction thresholds; independent NumPy A
checks apply to final prefixes. Matching to nominal s is deliberately not a gate.
Separate-plane diagnostics and every attempted launch/trajectory are preserved.

Reference/selected drivers took 979.47/972.46 s; external supervision took
989.71/983.17 s, within fixed 1800/1860 s per-arm limits. One native thread,
256 MiB per arm and 3/2 GiB disk reserves were enforced; each arm used about
58.55 MB. UTC and monotonic clocks agree within 0.001 s. External load is
unverified; no controlled-throughput claim follows.

Published archive [evidence-issue48-full-grid-v1](https://github.com/DrWorkhard/nuclear-fusion-at-home/tree/evidence-issue48-full-grid-v1), commit
`2ee186bb347245072c98d983a42b06f8e02a16a9`, tag object
`c570e13034391224f8c8359941034bb4fb225aa4`; **published; remote identities and manifest retrieval verified**. It preserves
all 103 raw files byte-for-byte, frozen snapshots/target JSON, hashes, exact
commands, summaries, a section plot and NumPy/SciPy replay. Original Wouts remain
local-only. Replay checks final-prefix/subset and target-control A flux plus
saved arithmetic; it does not retrace, rebuild Wout geometry or rerun B-fan fields.
The retained earlier shallow replay recomputed 256 line integrals in 598.59 s, with maximum
recorded-label disagreement 6.67e-16 and native packages disabled. The invalid-radius
final prefix remains unreplayed; its recorded error and both qualification failures
are retained. A wrong-manifest negative control is rejected. The 117-file manifest was verified
again for this integration; SHA256
`4b39d87d53aaa47a4e1ccf599e3b45ffdd586693363689a914943d4bd54f0bb3`.

Issue #25's benefit-transfer conclusion remains inconclusive.
Geometric theta is not PEST alpha; symmetry pooling may mix island components.
No nesting proof, confinement, common action endpoint, plasma-benefit transfer,
continuum-filament error bound or physical acceptance follows. Agent review is
not external physics validation; issue #48's action comparison remains open.
