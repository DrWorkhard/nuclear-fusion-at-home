# Combining the passing coil methods on the Step 3 target (#102)

[Active coil research](README.md) · [Acceptance v2](../validation/ACCEPTANCE_V2.md) ·
[Issue #102](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/102)

**Combining the methods helps; order 8 on top does not clear the bar.** On the
improved Step 3 target (selected401), halved margins with the interior term reach a
worst v2 ratio of 0.815, and adding order 8 reaches 0.778. The best single method
reached 0.890. Both combined fields complete the wide bounce diagnostic. Recorded
14 October 2026; field and geometry acceptance only, not physical acceptance or
benefit transfer.

## Question and method

Three elements pass [acceptance v2](../validation/ACCEPTANCE_V2.md) on their own:
halved construction margins ([#70](ISSUE70_CONSTRUCTION_MARGINS.md)), Fourier order 8
([#53](ISSUE53_COIL_FREEDOM.md), configuration and code by @pjckoch) and the interior
field term ([#12](../../submissions/interior-pass-headroom-continuation/README.md),
by @pjckoch, in the active fitter since [#98](ISSUE98_INTERIOR_TERM.md)). On
reference401, @pjckoch's #98 arm I combined the first and the last (0.836 against
0.902). Does a combination beat the best single method on selected401, and does
order 8 add to it?

As preregistered in #102, both arms used `scripts/fit_coils.py` on main `49dd45e`,
the archived selected401 Wout (`8cd6bebf…`) and input (`6bec3483…`), #92's seed
(`db836feb…`), 1800 s search and 900 s checks, one thread, run one after the other
on the maintainer's machine:

- **I:** `--margins halved --interior-weight 0.05`, order 5;
- **A:** `--order 8 --margins halved --interior-weight 0.05`; the seed is lifted
  with exact zeros.

The comparators are the [#92–#94 arms](STEP3_V2_METHODS.md) (same target, seed,
budgets and machine), not rerun. A benefit claim needs a v2 pass, continuous
geometry and a worst ratio at least 5% below its comparator; reruns of one
configuration have agreed within about 1–2%. A 30 s smoke run of arm A, disclosed
before preregistration, checked only feasibility. Arm A's provenance marks the tree
dirty because of documentation edits on the branch. Every recorded repository
source matches `49dd45e` before and after both runs.

## Result

| Diagnostic | M: halved margins | X: continuation | I: margins + interior | A: I + order 8 |
| --- | ---: | ---: | ---: | ---: |
| Search | 1796 s, budget | 327 iterations | 1796 s, budget | 1795 s, budget |
| Boundary RMS | 0.0017154 | 0.0020658 | 0.0017699 | **0.0017078** |
| Boundary mean (worse shift) | 0.00143 | 0.00169 | 0.00147 | **0.00140** |
| Boundary maximum (shift 0 / 0.5) | 0.0079 / 0.0080 | 0.0096 / 0.0096 | 0.0080 / 0.0080 | 0.0079 / 0.0082 |
| Interior RMS (three levels) | max 0.00890 | max 0.00200 | 0.00182 / 0.00180 / 0.00180 | **0.00174 / 0.00172 / 0.00172** |
| Worst v2 ratio | 0.890 | 0.937 | 0.815 | **0.778** |
| Length / coil–coil / coil–plasma bound (m) | 3.491 / 0.0602 / 0.149 | 3.474 / 0.0681 / 0.134 | 3.485 / 0.0602 / 0.149 | 3.495 / 0.0601 / 0.148 |
| Curvature upper bound (/m) | 11.02 | 10.04 | 11.04 | 11.07 |
| Frozen current (A) | 307,610 | 305,301 | 305,417 | 305,428 |

Both arms pass v2 and fail v1 (boundary RMS and maximum). Numerical cross-checks,
flux and current limits and continuous geometry pass, the geometry at the finer
level only (the coarser level was unresolved). Against the preregistered rules:

- **Combination benefit: yes.** min(I, A) = 0.778 ≤ 0.846; A is 12.5% and I 8.4%
  below M.
- **Interior term on top of halved margins: yes.** I = 0.815 ≤ 0.845 (0.95 × M).
- **Order 8 on top of both: not shown.** A = 0.778 > 0.774 (0.95 × I); order 8
  lowers the worst ratio by 4.5%, just short of the 5% bar.

Secondary measurements:

- **Search.** I ran 8,227 completed bundles (6,246 solver iterations) and A 8,168
  (5,133). Both stopped on the time budget, and in each the selected point is the
  last completed bundle, so neither search had converged. A 4-hour rerun of A
  ([#105](ISSUE105_SEARCH_BUDGET.md)) lowered its field errors by a further 9% but
  did not pass continuous geometry.
- **Interior on the objective's own surfaces:** 0.00165 (I) and 0.00157 (A), close
  to the checked values.
- **Output:** 51.5 and 64.3 MiB retained (recording v3), against 204 MiB for M.

## Bounce diagnostic (exploratory)

`scripts/measure_coil_bounce.py` with its defaults, as for the
[#92–#94 arms](STEP3_V2_METHODS.md#bounce-diagnostic-exploratory).

| Diagnostic | Ideal target | M | X | I | A |
| --- | ---: | ---: | ---: | ---: | ---: |
| Failed launch lines, s = 0.1 / 0.25 | 0 / 0 | 16 / 8 | 0 / 0 | **0 / 0** | **0 / 0** |
| Wide score | 2.12e-4 | incomplete | 2.51e-4 | 1.79e-4 | 1.84e-4 |
| Narrow score (×10⁻⁵) | 1.10 | 2.79 | 1.84 | 1.86 | 1.87 |
| Lowest B on any s = 0.1 line (threshold 1.02566) | — | 1.02694 | 1.01004 | 1.01094 | 1.01095 |

Both fields have the required wells on every line of all five surfaces. Their
coil/ideal score ratios (I, A) are 0.17, 0.11 at s = 0.1; 0.55, 0.65 at s = 0.25;
0.98, 0.99 at s = 0.5; 1.23, 1.21 at s = 0.75; and 1.13, 1.12 at s = 0.9. The
wide scores below the ideal come from the inner surfaces, where the coil fields
differ from the target: that is a mismatch, not a better plasma. As in X, a low
interior error completes the wide domain; no boundary-only fit measured so far
(#35, [#89](ISSUE89_V2_COIL_BOUNCE.md), arms C, M and P) has. No benefit-transfer
claim: launch labels are target coordinates
([#48](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/48)).

## Reading

- **The interior term moves the binding constraint.** In M the interior RMS binds
  (0.890). The term lowers it about 5× and costs 3% boundary RMS, so in I and A the
  boundary mean binds. On reference401, #98 found the same pattern.
- **Order 8 then lowers the boundary error by 3.5% (RMS)**, close to its 2.6% effect
  alone against the control (#93). One seed cannot separate that from run-to-run
  variation.
- **Margins are thin.** The continuous coil–coil bound is 0.25 mm (I) and 0.13 mm
  (A) above its 0.06 m limit; A's length bound is 5 mm below 3.5 m.
- **Bookkeeping.** @pjckoch's [#98 arm I candidate](../../submissions/interior-term-halved-margin/README.md),
  checked with `scripts/check_coils.py` on the archived reference401 Wout
  (`83dc45b9…`), reproduces the values reported on the contributor's regenerated
  Wout: boundary RMS 0.0018082, mean 0.00150, maximum 0.00833, interior
  0.00184 / 0.00183 / 0.00183, worst ratio 0.836. It now ranks first on reference401
  in the [leaderboard](../validation/LEADERBOARD.md).

Limits: one seed, one interior weight (0.05, from #12 and #98, not tuned), one
machine; unconverged searches; v2 is benchmark-relative and was calibrated with
reference401 results known; vacuum field. Errors against different targets are not
directly comparable. Raw outputs: maintainer's ignored `artifacts/combo-v1/`
(selected snapshots I `c75ad185…`, A `01d28f0a…`).
