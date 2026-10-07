# The failed continuation trace has sampled angular reversals

**Decision: simple monotonic drift does not describe the failed saved samples.**
The [continuation grid](ISSUE48_CONTINUATION_LABELS.md) still qualifies at 19/20
launches. Its failed s=0.5, geometric theta=pi point has one resolved angular
reversal in every one of eleven residue sequences on both section planes.
All four qualifying controls have zero reversals. This narrows the reconstruction
problem; it does not requalify the contour or justify automatically tracing longer.

| Saved launch | 11-turn return RMS, both planes (mm) | Reversals per residue sequence | Final pooled angular gap (rad) |
| --- | ---: | ---: | ---: |
| Continuation theta=0 | 2.590–2.600 | 0 | 0.062805 |
| Continuation theta=pi/2 | 3.348–3.369 | 0 | 0.071860 |
| Continuation theta=pi (failed) | 0.8321–0.8326 | 1 | 1.240256 |
| Continuation theta=3pi/2 | 3.369–3.384 | 0 | 0.058829 |
| Historical reference theta=pi | 2.246–2.253 | 0 | 0.048613 |

The failed point's pooled gaps remain 1.427401, 1.267474 and 1.240256 rad at
160/320/640 crossings. Its same-plane last-160 gaps exceed 1.469 rad. All sampled
polar-spline radii remain positive at the tested Gauss nodes, including the failed
case; that limited check does not establish reliable interpolation. All three
exact-circle controls pass. A regular rational circle also has sparse section
coverage, so gaps and recurrence alone cannot establish islands or lost surfaces.

The prospective comparison froze five saved launches, 10/11/12-turn returns,
eleven residue classes and a 1e-8-rad resolved-step cutoff before processing.
It reused the previous numerical functions and original target-axis polar center.
These are unwrapped finite sampled angles, not continuous winding or a dynamical
classification. The three other continuation phases and historical reference at
the failed phase are controls, not matched realized surfaces. Geometric theta is
not PEST alpha. No field, trajectory, fit, label or acceptance gate was changed.

Clean producer/evaluator and full prospective protocol:
`2baca74707328b27e62a66e6515bda1a553b0f88`. One saved-array attempt completed in
**1.184 s** supervised total. The 60-second driver allowance begins inside its
run function; the 75-second outer allowance includes imports/setup. One thread,
256 MiB output, 3/2 GiB disk reserves and 5-second clock tolerance remained fixed.
All 54 direct source/input bindings and 1,662 recorded native package files matched
before/after; owned process cleanup succeeded. Original outputs remain intact.

Local archive: `10ba631714ac78a35eaa5a35579b6ec35a44af7b`, prepared tag
`evidence-issue48-continuation-recurrence-v1`; not published or remotely verified.
Manifest SHA256:
`07498e69e05a9716a173cdb70ae8ba666497366066c7453028c4e448944a34c1`.
The snapshot preserves code/protocol, all five output files, exact consumed input
subsets, commands, environment identity and replay. A fresh shallow replay checks
25 payload files and all 54 direct bindings and exactly reproduces the five cases,
110 residue sequences and analytic controls in 0.315 s. It uses the same NumPy/SciPy
kernels; it does not reproduce native fields, trajectories, environment or timing.

No nestedness, confinement, common action coordinates or benefit-transfer claim
follows. #48 remains open. Read-only adversarial agent review is separate from
external physics review.
