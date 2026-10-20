# Plasma scorecard — partial

The two registered targets have complete ConStellaration metric rows; neither is
feasible for any benchmark problem. Other recorded boundaries remain unscored.
This is partial delivery of [#112](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/112),
not scorer qualification, a regrading of Step 3 or physical acceptance.

## Recorded metrics

Values below reuse the completed 16 October 2026 replay; no new solve was run for
this page. All quantities are dimensionless. Signed transforms retain their sign;
benchmark constraints use their absolute value. Rounded display values do not
control pass/fail. Full precision, settings and benchmark residuals are in the
[report](https://github.com/patrickmahlstein/nuclear-fusion-at-home/blob/fb6d65d47a0b4e3bb3b52764c16bc55e2f4d0ed0/evidence/plasma-scorecard-replay-v1/report.json).

| Plasma | Aspect | Aspect/edge ι | Elongation | Axis ι/Nfp | Edge ι/Nfp | Axis mirror | Edge mirror | Triangularity | Well | L∇B | QI | Flux compression |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| reference401 | 9.9950994 | -19.905864 | 5.9630165 | -0.29555763 | -0.25105917 | 0.21985698 | 0.23330298 | -0.23529794 | -0.015770175 | 6.1403851 | 2.3755902e-05 | 1.3959066 |
| selected401 | 9.9955534 | -19.929579 | 5.9567074 | -0.2957956 | -0.25077182 | 0.22090301 | 0.23493463 | -0.2365782 | -0.015814291 | 6.138813 | 2.1949074e-05 | 1.3977389 |

## Benchmark bounds

These are the benchmark's bounds, not adopted project requirements. Each cell is
the strict bound comparison at full precision. Official problem feasibility uses
its largest normalized violation ≤ 0.01; the whole-problem verdict is taken from
the saved problem-class output. Both conventions give the same verdicts here.
QI columns compare log10(QI); ι columns compare |edge ι/Nfp|.

| Plasma | Geometric: aspect ≤ 4 | Triangularity ≤ −0.5 | ι ≥ 0.3 | Official verdict / score |
| --- | --- | --- | --- | --- |
| reference401 | fail | fail | fail | fail / 0 |
| selected401 | fail | fail | fail | fail / 0 |

| Plasma | Simple: aspect ≤ 10 | ι ≥ 0.25 | log QI ≤ −4 | Mirror ≤ 0.2 | Elongation ≤ 5 | Official verdict / score |
| --- | --- | --- | --- | --- | --- | --- |
| reference401 | pass | pass | pass | fail | fail | fail / 0 |
| selected401 | pass | pass | pass | fail | fail | fail / 0 |

| Plasma | MHD: ι ≥ 0.25 | log QI ≤ −3.5 | Mirror ≤ 0.25 | Flux compression ≤ 0.9 | Well ≥ 0 | Official verdict / singleton-set score |
| --- | --- | --- | --- | --- | --- | --- |
| reference401 | pass | pass | pass | fail | fail | fail / 0 |
| selected401 | pass | pass | pass | fail | fail | fail / 0 |

## Inputs, environment and cost

| Plasma | Input SHA-256 | Forward model seconds | State |
| --- | --- | ---: | --- |
| reference401 | `57394ef682f3c6399faa03012abc02da2eb1ce40703a4f99640ece3d07e5691f` | 262.847 | scored |
| selected401 | `6bec3483eaced499bafe7ee94b16aa960d219ec1fec86cc0690012f8ebdb033e` | 219.690 | scored |
| Rejected first Step 3 design | `67237ffbf9c65e3968e18e2c5611bcf567a46bc4f8a743f8f6e6966f382b5820` | — | boundary available; unscored |
| N21 repaired plasma | `deca897168dc7d56e80d990beebecad27cf23f4cd7b2739dde8585f8a9a48a9c` | — | boundary available locally; unscored (A-REQ-020) |

The rejected boundary is the archived
[`plasma-design-v2/selected-input-401.json`](https://github.com/DrWorkhard/nuclear-fusion-at-home/blob/68db098b664bb072854b687040e103aaafee463c/evidence/plasma-design-v2/selected-input-401.json),
not the balanced selected401 above. The historical
[archive](https://github.com/DrWorkhard/nuclear-fusion-at-home/blob/68db098b664bb072854b687040e103aaafee463c/evidence/plasma-balanced-v1/archive.json)
and [proposal](https://github.com/DrWorkhard/nuclear-fusion-at-home/blob/68db098b664bb072854b687040e103aaafee463c/evidence/plasma-balanced-v1/propose.json)
contain 16 and 11 candidate records, respectively. Their path/hash references do
not establish local boundary availability or independent candidates. Those input
payloads were not located in the inspected local archive; no metrics are invented.

Producer/evaluator: clean `60d515001562c5da713be5ec5880629c2f92aa1a`.
One thread; Python 3.12.15, macOS 15.7.9 x86_64; constellaration 0.2.6,
vmecpp 0.4.11, booz-xform 0.1.0, simsopt 1.8.1, desc-opt 0.15.0,
jax/jaxlib 0.4.38, numpy 2.2.6, scipy 1.15.3, pymoo 0.6.1.5 and netCDF4 1.7.2.
The model uses its own near-vacuum profiles and ns 25/51/99 schedule; it does not
solve the original input profiles. Total invocation: 504.738 seconds including
conversion and recording. No optimization ran. Original temporary runtime is now
missing; package versions alone cannot recover historical binary identity.

## Evidence and unfinished work

The [immutable evidence snapshot](https://github.com/patrickmahlstein/nuclear-fusion-at-home/tree/fb6d65d47a0b4e3bb3b52764c16bc55e2f4d0ed0/evidence/plasma-scorecard-replay-v1), annotated tag
`evidence-plasma-scorecard-replay-v1-2026-10-20`, retains unchanged report,
reference, comparison and Wouts. Report SHA-256:
`8d8afa15ed92ae7814638029d68916875bdebfe30c28c0f2525b033b5871ccf1`.
This fork snapshot still needs upstream mirroring by the owner. Original local
execution logs are not included. The [public replay result](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/112#issuecomment-6209013504)
records its frozen protocol and limits.

All metrics/settings/benchmark fields match N23 exactly; this does not establish
bitwise reproduction of the unavailable original #76 report. The [ns99/ns199 radial probe](PLASMA_RADIAL_SENSITIVITY.md) is complete: no benchmark
bound or verdict changes. Seeded dataset validation, the unscored boundaries and
historical candidate retrieval remain open. Add each future scored plasma with its full input hash,
evaluator/settings identity, cost and benchmark results. Keep missing or failed
rows explicit. Vacuum proxies do not establish pressure stability, confinement,
fusion power or an accepted reactor.
