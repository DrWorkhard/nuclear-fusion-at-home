# Plasma metrics: radial sensitivity

**Refining VMEC from 99 to 199 surfaces does not change either target's benchmark
verdict.** Both still have a negative vacuum well and flux compression above 0.9.
This completes the radial probe for [#112](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/112),
not full scorer qualification or physical acceptance.

## Question and matched test

How sensitive are vacuum well, flux compression, normalized L∇B and QI to radial
equilibrium resolution? Run reference401/selected401 at ns99, then both at ns199,
serially. Only the final multigrid step changes: 25/51/99 to 25/51/199. All effective
settings, geometry gates and benchmark methods otherwise stay fixed, including
mpol/ntor10, force tolerances, iteration limits and diagnostic sampling.

The old temporary runtime vanished. A rebuilt runtime matches all 13 recorded
package versions and all 50 ConStellaration Python source files, but its Python
executable differs. A fresh same-runtime ns99 baseline avoids confounding runtime
and resolution. Its metrics, settings and benchmark outputs match the historical
N23 baseline **exactly** for both targets; no parity tolerance was introduced.
Original results stay unchanged. The [pre-run protocol and code](https://github.com/patrickmahlstein/nuclear-fusion-at-home/tree/ba53fd7816030ca0a7c594cda041a4d4ab347986/evidence/radial-recovery-protocol-v2)
and public amendments ([recovery](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/112#issuecomment-6286526941),
[existing resource reservation](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/112#issuecomment-6287043234))
precede execution. There was one invocation and no retry.

## Results

| Metric | Reference ns99 | Reference ns199 | Selected ns99 | Selected ns199 | Largest absolute relative change |
| --- | ---: | ---: | ---: | ---: | ---: |
| Vacuum well | −0.01577017 | −0.01574364 | −0.01581429 | −0.01578692 | 0.1731% |
| Flux compression | 1.39590662 | 1.39670619 | 1.39773886 | 1.39855560 | 0.05843% |
| Normalized L∇B | 6.14038508 | 6.14062668 | 6.13881303 | 6.13885902 | 0.003935% |
| QI residual | 2.37559019e-5 | 2.40203664e-5 | 2.19490742e-5 | 2.22810085e-5 | 1.5123% |

Relative change means |finer − default| / |default|. No component crosses either
its strict bound or the benchmark's unchanged normalized 0.01 tolerance. All three
problem verdicts remain infeasible for both targets. Geometry passes in all four
evaluations; VMEC ier_flag is 0 and force residuals are about 1e-15 or smaller.
Two radial levels establish this sensitivity only, not convergence or total
numerical uncertainty; angular/Boozer/diagnostic resolution was not varied.

## Reproduction and limits

Inputs and environment versions are on the [scorecard](PLASMA_SCORECARD.md).
Scientific source: clean `32fe8ecd198a8615549b1086bca37682290f4e57`; approved scorer
SHA-256 `1b394999a89891c84329e406ed8a80a3849c56151bb922ec291a86d73cf749d6`.
The [immutable evidence snapshot](https://github.com/patrickmahlstein/nuclear-fusion-at-home/tree/785f5ea4ffc889f1d05f9e5ae37e7c21f2e25565/evidence/radial-recovery-result-v1),
tag `evidence-plasma-radial-sensitivity-v1-2026-10-20`, retains both full reports,
four Wouts, actual settings, comparisons, warnings and input/runtime/runner hashes.
Comparison SHA-256: `f004475573e9dd729942e1f13d081ed59b2010cd355b25b32acf8d699f80c11e`.
Upstream evidence mirroring remains an owner action. Runtime is retained locally,
not in Git; original local outputs remain intact. Package/font caches are excluded.

Total 724.790 s, one thread, 17.62 MB local output. Individual model times:
reference99/selected99/reference199/selected199 = 100.11/86.77/225.61/206.30 s.
Limits were 1800 s, 100 MiB and 3/2 GiB start/live disk reserves. No environment
mutation during execution; postflight frozen-file checks pass. Raw stderr preserves
SIMSOPT SyntaxWarnings and the existing SciPy iteration-progress warning, including
its trailing whitespace; source documentation checks are separate.

The recorded booz-xform0.1.0 overrides ConStellaration0.2.6's declared0.0.9 dependency;
this matches N23's recorded version, not default dependency compatibility. The
rebuilt binary environment is not claimed identical to the vanished original.
This is not original #76 bitwise reproduction. Seeded dataset controls and remaining
recorded-plasma scoring remain open; no scientific threshold or past verdict changes.
