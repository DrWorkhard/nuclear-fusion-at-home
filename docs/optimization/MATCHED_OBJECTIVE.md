# Fitting the error that acceptance v2 scores

[Active coil research](README.md) · [Acceptance v2](../validation/ACCEPTANCE_V2.md) ·
[Leaderboard](../validation/LEADERBOARD.md)

**Question.** In every passing selected401 entry, the binding v2 term is the boundary mean
(ratio 0.76–0.82). Boundary max (≈ 0.6) and interior RMS (≈ 0.17) have slack. The fitter minimizes
SIMSOPT's area-weighted squared flux, but v2 scores the plain per-point mean of |B·n|/|B|. Does
fitting a matching quantity lower the worst v2 ratio at equal budget? This is exploratory, and each
step was preregistered before running.
[Evidence](https://github.com/patrickmahlstein/nuclear-fusion-at-home/tree/929e4f88a6365a3c919dee721b77d24eb84d16ac/evidence/matched-objective).

**Method.** `fit_coils.py --flux-objective mean-abs --flux-power p` replaces the boundary term with
½m², where m = (mean over points of (e² + ε²)^{p/2})^{1/p}, e = B·n/|B| on the search grid and
ε = 1e-4. At p = 1, m is the plain mean that v2 scores; larger p weights peaks. The gradient is checked
against finite differences. The default objective, its recorded bytes and selection are unchanged.

**Inputs.**
- Recipe as #102 arm A: `--order 8 --margins halved --interior-weight 0.05`, 1800 s search and 900 s
  checks, from the length-headroom seed.
- Target: selected401 via `--target-spec` on the regenerated Wout `3d5df9a4…` (B² within 1.5e-11
  of the registered value).
- Each pair runs in parallel on one machine, one thread per fit.
- For a geometry-unresolved final point, `certified_selection.py` picks the latest certified point.
  Its rule is unchanged; it now also accepts `--target-spec`.

| Arm | Boundary mean (ratio) | Max (ratio) | Interior | Worst v2 ratio |
| --- | ---: | ---: | ---: | ---: |
| Default objective, run 1 / run 2 | 0.001436 / 0.001433 (0.80) | 0.0081 / 0.0079 (0.62) | 0.0018 | 0.798 / 0.796 |
| p = 1 | 0.001305 (0.725) | 0.0107 (0.821) | 0.0020 | geometry unresolved |
| p = 1.5 | 0.001336 (0.742) | 0.0084 (0.649) | 0.0020 | **0.742** |
| p = 1.25, certified point, run 1 / run 2 | 0.001318 (0.732) | 0.0094 (0.721) | 0.0020 | **0.732 / 0.732** |
| p = 1.25, interior weight 0.02, run 1 / run 2 | 0.001290 / 0.001289 (0.716) | 0.0092 (0.70) | 0.0020 | **0.717 / 0.716** |
| p = 1.5, interior weight 0.02 | 0.001330 (0.739) | 0.0081 (0.622) | 0.0021 | 0.739 |
| p = 1.25, interior weight 0.01, certified point | — | — | 0.0023 | 0.731 |
| 4-hour search: p = 1.25, interior weight 0.02, certified point | 0.001239 (0.688) | 0.0089 (0.685) | 0.0020 | **0.688** |

All rows marked with a worst ratio pass v2, including continuous geometry. With p = 1.25 the final points sit
at coil spacing 0.0599 m against 0.06 m (unresolved) at interior weight 0.05; the certified point (bundle 3500) passes.

**Result.**
- At equal budget, p = 1.25 lowers the worst v2 ratio by 8% against the paired default (0.732 vs 0.796–0.798).
  The replicate reproduces this within 0.0003.
- Lowering the interior weight from 0.05 to 0.02 with p = 1.25 gives 0.717, about −10% against the
  default, reproduced by a second run (0.716); within the preregistered 5% of 0.732, so "comparable".
  At 0.01 the interior term starts to cost (certified 0.731).
- With a 4-hour search, p = 1.25 at interior weight 0.02 reaches 0.688 at its certified point (bundle 10000;
  the final point, 0.661, has unresolved geometry). This meets the preregistered ≤ 0.723 (5% below #109's
  0.761). It is one run.
- p = 1.5 gives −7% with no certification step.
- p = 1 over-trades: it lowers the mean most but lets peaks and geometry bind.
- For comparison, the best passing leaderboard entries are 0.778 (30 min, #102 arm A) and 0.761
  (4 hours, #109).
- A circular-seed multistart with the default objective was worse (0.819 at best).

**Limits.** This uses the regenerated Wout, not the archived one, so the target identity differs from
the leaderboard's. There are two runs per arm on one machine. The entries need a maintainer run on the
registered selected401 before ranking. Fitting the scored quantity sharpens the trade against the other
v2 limits; it is not a physics gain.
