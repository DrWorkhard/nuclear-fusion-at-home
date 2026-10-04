# Matched target-to-coil benefit experiment

Question: does Step 3's vacuum action improvement survive practical coil realization?
Related to [issue #25](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/25).
This is a prospective exploratory comparison, not physical acceptance or confirmation.

## Frozen inputs and selection

Use reference401 and selected401, with input/Wout SHA256 and target-specific B²
in `coil_check.TARGETS`. The improved input is restored byte-for-byte from archive
`68db098b664bb072854b687040e103aaafee463c`. Both original Wouts are preserved locally;
selected401 currently requires the exact archived Wout, not a regenerated substitute.
Start both arms from `submissions/length-headroom-six-coil/candidate.json`, with
identical 198 named geometric coefficients. Normalize each to its own boundary
flux loop. Freeze the selected current before all diagnostic evaluations.

Run the existing penalized fitter sequentially, with 300 s including intake/model
startup per arm, then 300 s for shared fine/continuous-geometry/interior checks.
Use unchanged candidate selection and acceptance gates. Report startup and search
time separately. No optimizer variants or adaptive extension. A seed selected
again counts as no optimizer improvement. Failed or late calls cannot win.

## Diagnostic rule, fixed before fitting

Trace the selected frozen-current snapshot directly for 200 transits, using the
existing ten starts, signed iota and 0.02 diagnostic tolerance; allow 300 s per arm.
A classifier stop is inconclusive given the known issue #20 / PR #33 limitation.
Do not infer nested surfaces, particle confinement or benefit transfer from this test.

Then compare the original Step 3 narrow (3 surfaces × 5 pitches) and wide
(5 × 7) period-action statistics in ideal-target and actual-coil fields. Reuse the
frozen bounce quadrature and VMEC trace kernels; their restoration supports this
specific transfer question. Launch 16 uniformly spaced target-PEST alpha labels,
trace one full toroidal turn on 801 points, using direct Biot–Savart with 512 coil
nodes. Integrate actual coil trajectories, not paths constrained to target surfaces.
Use the original fixed bounce fields and reject missing, extra, censored or
period-crossing wells. Retain all failed cells; incomplete domains have no aggregate.
Allow 600 s per arm. If both wide domains are complete, repeat both at 1601 points
and 32 alpha labels within another 600 s per arm; otherwise do not refine selectively.

Launch s/alpha label the target, not independently verified realized flux surfaces.
Even a resolved gain is exploratory. No unseen holdout or calibrated realized-flux
coordinate construction exists here; confirmation requires those before any claim
that the physical Step 3 benefit transferred. Ideal controls must reproduce the
original diagnostic at the matching resolution, with relative score error ≤1e-8.

## Resources and decision

One native thread, sequential arms, 256 MiB retained output per arm across stages,
3 GiB initial and 2 GiB live disk reserve. Preserve interrupted stages and output
hashes. Stop on a resource failure and label incomplete evidence accordingly.

Report each target's field errors separately. If diagnostics are complete, report
whether the launch-label action improvement survives, disappears or is unresolved;
otherwise identify the failed prerequisite. The next decision is whether to build
and validate a realized-flux-surface action diagnostic or first change coil/target
realization. None of these outcomes changes acceptance gates or establishes a reactor.
