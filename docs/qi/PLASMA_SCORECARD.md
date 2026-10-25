# Plasma scorecard — partial

Three plasma rows have complete ConStellaration metrics; all three are infeasible
for every benchmark problem. N21 was attempted but its VMEC solve did not converge;
its metrics and benchmark feasibility remain unknown.
This is partial delivery of [#112](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/112),
not scorer qualification, a regrading of Step 3 or physical acceptance.

## Recorded metrics

The registered-target rows reuse the completed 16 October 2026 replay. The
rejected Step 3 row comes from the separately frozen 25 October run below.
All quantities are dimensionless. Signed transforms retain their sign;
benchmark constraints use their absolute value. Rounded display values do not
control pass/fail. Full precision, settings and benchmark residuals are in the
registered-target [report](https://github.com/patrickmahlstein/nuclear-fusion-at-home/blob/fb6d65d47a0b4e3bb3b52764c16bc55e2f4d0ed0/evidence/plasma-scorecard-replay-v1/report.json)
and the [recorded-boundary evidence](#recorded-boundary-attempt-25-october-2026).

| Plasma | Aspect | Aspect/edge ι | Elongation | Axis ι/Nfp | Edge ι/Nfp | Axis mirror | Edge mirror | Triangularity | Well | L∇B | QI | Flux compression |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| reference401 | 9.9950994 | -19.905864 | 5.9630165 | -0.29555763 | -0.25105917 | 0.21985698 | 0.23330298 | -0.23529794 | -0.015770175 | 6.1403851 | 2.3755902e-05 | 1.3959066 |
| selected401 | 9.9955534 | -19.929579 | 5.9567074 | -0.2957956 | -0.25077182 | 0.22090301 | 0.23493463 | -0.2365782 | -0.015814291 | 6.138813 | 2.1949074e-05 | 1.3977389 |
| rejected-step3 | 9.9952674 | -19.862854 | 5.9296873 | -0.29594396 | -0.25160703 | 0.2162195 | 0.23170566 | -0.23529794 | -0.01570675 | 6.1455334 | 3.3899019e-05 | 1.3917795 |
| n21-repaired (VMEC failed) | — | — | — | — | — | — | — | — | — | — | — | — |

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
| rejected-step3 | fail | fail | fail | fail / 0 |
| n21-repaired | — | — | — | not evaluated |

| Plasma | Simple: aspect ≤ 10 | ι ≥ 0.25 | log QI ≤ −4 | Mirror ≤ 0.2 | Elongation ≤ 5 | Official verdict / score |
| --- | --- | --- | --- | --- | --- | --- |
| reference401 | pass | pass | pass | fail | fail | fail / 0 |
| selected401 | pass | pass | pass | fail | fail | fail / 0 |
| rejected-step3 | pass | pass | pass | fail | fail | fail / 0 |
| n21-repaired | — | — | — | — | — | not evaluated |

| Plasma | MHD: ι ≥ 0.25 | log QI ≤ −3.5 | Mirror ≤ 0.25 | Flux compression ≤ 0.9 | Well ≥ 0 | Official verdict / singleton-set score |
| --- | --- | --- | --- | --- | --- | --- |
| reference401 | pass | pass | pass | fail | fail | fail / 0 |
| selected401 | pass | pass | pass | fail | fail | fail / 0 |
| rejected-step3 | pass | pass | pass | fail | fail | fail / 0 |
| n21-repaired | — | — | — | — | — | not evaluated |

## Inputs, environment and cost

| Plasma | Input SHA-256 | Forward model seconds | State |
| --- | --- | ---: | --- |
| reference401 | `57394ef682f3c6399faa03012abc02da2eb1ce40703a4f99640ece3d07e5691f` | 262.847 | scored |
| selected401 | `6bec3483eaced499bafe7ee94b16aa960d219ec1fec86cc0690012f8ebdb033e` | 219.690 | scored |
| Rejected first Step 3 design | `67237ffbf9c65e3968e18e2c5611bcf567a46bc4f8a743f8f6e6966f382b5820` | 97.293 | scored; remains rejected in Step 3 |
| N21 repaired plasma | `deca897168dc7d56e80d990beebecad27cf23f4cd7b2739dde8585f8a9a48a9c` | — | VMEC nonconvergence; metrics unknown (A-REQ-020) |

The rejected boundary is the archived
[`plasma-design-v2/selected-input-401.json`](https://github.com/DrWorkhard/nuclear-fusion-at-home/blob/68db098b664bb072854b687040e103aaafee463c/evidence/plasma-design-v2/selected-input-401.json),
not the balanced selected401 above. The historical
[archive](https://github.com/DrWorkhard/nuclear-fusion-at-home/blob/68db098b664bb072854b687040e103aaafee463c/evidence/plasma-balanced-v1/archive.json)
and [proposal](https://github.com/DrWorkhard/nuclear-fusion-at-home/blob/68db098b664bb072854b687040e103aaafee463c/evidence/plasma-balanced-v1/propose.json)
contain 16 and 11 candidate records, respectively. Their path/hash references do
not establish local boundary availability or independent candidates. Those input
payloads were not located in the inspected local archive; no metrics are invented.

Registered replay producer/evaluator: clean `60d515001562c5da713be5ec5880629c2f92aa1a`.
Recorded-boundary producer: clean `32fe8ecd198a8615549b1086bca37682290f4e57`, with
the same approved scorer bytes. No scientific verifier or threshold changed.
One thread; Python 3.12.15, macOS 15.7.9 x86_64; constellaration 0.2.6,
vmecpp 0.4.11, booz-xform 0.1.0, simsopt 1.8.1, desc-opt 0.15.0,
jax/jaxlib 0.4.38, numpy 2.2.6, scipy 1.15.3, pymoo 0.6.1.5 and netCDF4 1.7.2.
The model uses its own near-vacuum profiles and ns 25/51/99 schedule; it does not
solve the original input profiles. Registered replay: 504.738 seconds including
conversion and recording. No optimization ran. The original temporary runtime is
missing. The rebuilt runtime matches all 13 pinned versions and 50 ConStellaration
source files; its Python executable differs. The [radial probe](PLASMA_RADIAL_SENSITIVITY.md)
observed exact registered-target metric/settings/benchmark parity. This does not
establish historical binary identity or qualify every boundary.

## Evidence and unfinished work

The [immutable evidence snapshot](https://github.com/patrickmahlstein/nuclear-fusion-at-home/tree/fb6d65d47a0b4e3bb3b52764c16bc55e2f4d0ed0/evidence/plasma-scorecard-replay-v1), annotated tag
`evidence-plasma-scorecard-replay-v1-2026-10-20`, retains unchanged report,
reference, comparison and Wouts. Report SHA-256:
`8d8afa15ed92ae7814638029d68916875bdebfe30c28c0f2525b033b5871ccf1`.
This fork snapshot still needs upstream mirroring by the owner. Original local
execution logs are not included. The [public replay result](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/112#issuecomment-6209013504)
records its frozen protocol and limits.

Registered replay metrics/settings/benchmark fields match N23 exactly; this does not establish
bitwise reproduction of the unavailable original #76 report. The [ns99/ns199 radial probe](PLASMA_RADIAL_SENSITIVITY.md) is complete: no benchmark
bound or verdict changes. Seeded dataset validation, N21 nonconvergence diagnosis and
historical candidate retrieval remain open. Add each future scored plasma with its full input hash,
evaluator/settings identity, cost and benchmark results. Keep missing or failed
rows explicit. Vacuum proxies do not establish pressure stability, confinement,
fusion power or an accepted reactor.

## Recorded-boundary attempt, 25 October 2026

The rejected first design completed in 97.293 model seconds with geometry and
VMEC checks passing. N21 returned `VMEC++ did not converge` after 550.748 CLI
seconds, before metrics or a Wout. This is an evaluator failure for that input,
not a zero benchmark score or proof of physical infeasibility. The batch is
incomplete; the completed first row was verified independently after it stopped.
Its 12 metrics are retained above. Earlier N21 calculations used different solver,
profiles or settings; the cause of this frozen-model failure was not isolated.

[Immutable reports, inputs, Wout, actual settings and failure evidence](https://github.com/patrickmahlstein/nuclear-fusion-at-home/tree/01420490d8b2d81dd3a7e5ebc18d78002b51a9a1/evidence/recorded-plasmas-result-v2),
tag `evidence-recorded-plasma-scores-v1-2026-10-25`.
Completed report SHA-256: `c49cd53010b449d10f780a1dbf2187cdd35a3f2b1bc0fb10eab132fb0980835d`.
Both exact input JSONs are archived, including the previously local-only N21 file.
Owner mirroring remains pending. Prior Step 3 verdicts stay as recorded.

A first attempt exceeded its UTC budget without completing a score; its partial
failure is preserved in the same snapshot. The [public v2 amendment](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/112#issuecomment-6396474498)
preceded this separate repair attempt. It checks both UTC and monotonic elapsed
time, late completion and a current exclusive resource claim. Six stdlib
supervisor/ownership tests pass; scientific settings and limits were unchanged.
V2 used 674.325 UTC seconds (674.334 monotonic), one thread and about 3.2 MB,
within 900 s/100 MiB and 3/2 GiB start/live disk reserves. It exited 1 on the VMEC
error, with no deadline stop. Independent postflight verified all 84 frozen files
and the completed report hash. No further native retry or tolerance change ran.
