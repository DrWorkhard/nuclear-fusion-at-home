# Bounce action on realized flux surfaces (#48)

[Active coil research](README.md) · [Matched-target experiment](ISSUE25_MATCHED_TARGETS.md) ·
[Issue #48](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/48)

**Question.** #35 found the selected401 fit's narrow-domain coil action 5.07% below the reference401 fit's.
Its field lines start from *target* labels, and those drift from realized flux surfaces by up to 0.07 (#48).
Does the difference survive when every line starts on its realized surface? This is exploratory, and each step
was preregistered before running.
[Evidence](https://github.com/pjckoch/nuclear-fusion-at-home/tree/ed1b8c30058279acc728b29fdda393f58651288d/evidence/issue48-matched-labels):
preregistrations, scripts, results, SHA-256.

**Inputs.**
- The #35 archive fits (commit `05a45110`): reference401 `ec1f8ce7…` and selected401 `c2ea45c1…`, at their
  frozen currents.
- Wouts regenerated with vmecpp 0.8.0: reference401 `0f2b626c…`, and selected401 `3d5df9a4…`, which substitutes
  for the original `8cd6bebf…`.
- Direct Biot–Savart field, SIMSOPT 1.11.1, one thread.

**Method.**
- **Realized label:** s_real = Φ/Φ_edge. Φ = ∮A·dl is taken on a periodic spline through a line's φ = 0
  crossings, ordered about the realized axis; Φ_edge is the same integral on the target boundary. This is the
  #48 construction. It assumes star-shaped crossings, and a spline is not proof of a surface.
- **Matching:** each launch label σ is root-found (secant) so that |s_real − s| ≤ 1e-3.
- **Qualification at each s:** one curve, meaning the four phases at the same s lie within 1 mm of each
  other's splines; and Δs_real ≤ 1e-3 at 120 transits and at tolerance 1e-11.
- **Diagnostic:** the registered `coil_bounce` (801 φ, 16 α, 2 periods), unchanged except for the launch
  point of each α line.

**Qualification** (worst phase distance; every matched line is star-shaped):

| s | 0.1 | 0.25 | 0.5 | 0.75 | 0.9 |
| --- | --- | --- | --- | --- | --- |
| reference401 fit | 0.03 mm | 0.05 mm | 0.32 mm | 0.08 mm | unmatched |
| selected401 fit | 0.03 mm | 0.05 mm | **1.70 mm (fails)** | 0.08 mm | unmatched |

At s = 0.9, lines launched even at the target boundary reach only s_real 0.87–0.89. The realized s = 0.9
surface lies outside the target, so the wide domain cannot be matched this way.

**Narrow domain** (s 0.25/0.5/0.75 × q 0.1–0.9; all 48 α lines matched in each fit):

| Coil narrow score | reference401 fit | selected401 fit | Selected vs reference |
| --- | ---: | ---: | ---: |
| Target launches (#35 convention) | 4.25476e-5 | 4.03892e-5 | −5.07% |
| Matched realized launches | 4.9114e-5 | 4.9042e-5 | **−0.15%** |

**Controls.** The target-launch scores reproduce the archived C7 values to 2e-10 (reference) and 8.6e-9
(selected). Matching changes s = 0.25 and 0.5 by ≤ 10% per cell. It changes the deeply trapped cells at
s = 0.75 (q 0.1/0.3) by ×1.6–2.3, where the label drift is largest.

**Conclusion.** On realized surfaces, the selected fit's 5% narrow-domain advantage almost disappears. #35's
coil-field difference therefore came mostly from where the lines were launched, and is not evidence of
transfer. This does not show that transfer fails. Confirming it needs the original selected401 Wout and an
explanation of its s = 0.5 phase spread. The joint-versus-fixed comparison (#40) should use matched labels and
report this qualification.
