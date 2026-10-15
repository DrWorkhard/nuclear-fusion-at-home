# Can our nfp = 2 plasma be repaired to MHD-stable QI? (#114 route A scoping)

[Plasma physics](README.md) · [Issue #114](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/114) ·
[Programme #116](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/116)

**Question.** selected401 misses two ConStellaration MHD-stable bounds: vacuum well W = −0.0158 (needs ≥ 0) and
flux compression FC = 1.40 (needs ≤ 0.9). Can boundary changes near it meet them at aspect ratio ≈ 10 while
keeping QI? This scopes #114 stage 1. It is exploratory, not the preregistered stage-1 run, which waits for a
frozen v1 (#113). Each step below was preregistered before running.
[Evidence N19–N24](https://github.com/pjckoch/nuclear-fusion-at-home/tree/9b3d62508481ed5f4d5df941accda7757194c2ff/evidence/issue114-route-a-scoping),
[N25–N27](https://github.com/pjckoch/nuclear-fusion-at-home/tree/ed1b8c30058279acc728b29fdda393f58651288d/evidence/issue114-route-a-scoping-2):
preregistrations, deviations, scripts, outputs, SHA-256 sums.

**Tools.**
- A native mirror of ConStellaration 0.2.6's W, FC and edge mirror ratio, computed from a VMEC++ Wout with
  SIMSOPT. On both targets it agrees with #76 to 0.8% (FC) or better.
- `constellaration==0.2.6` itself, in a micromamba environment with booz_xform 0.1.0. It reproduces #76 for
  both targets to every recorded digit.
- Inputs: vmecpp 0.8.0 (mirror) and 0.4.11 (constellaration); one thread per solve; macOS x86_64.

| Step | Method | Result |
| --- | --- | --- |
| N19 | Finite differences on all 170 modes, then a least-norm step at fixed A and ι | W > 0 is cheap: a 0.4%-of-minor-radius step gives W +0.0027. FC barely moves (1.39 → 1.35). FC is not finite-difference smooth at h = 1e-3. |
| N20 | Secant (h = 5e-3) Gauss–Newton/Broyden repair, modes m ≤ 3, \|n\| ≤ 3 | FC stalls at 1.08; edge mirror rises to 0.43. |
| N21 | The same with a mirror ≤ 0.24 goal | W +0.0034, mirror 0.245, A 9.998, FC **1.06**, ι/nfp 0.248. At 401 surfaces the plasma **fails the Step 3 bounce diagnostic** (extra \|B\| wells), so its QI structure is broken. |
| N22 | Dataset correlation (nfp 2, A 9–11, n = 12,366) | FC tracks maximum elongation (Spearman +0.66). Better QI goes with higher FC. No nfp-2 row with QI ≤ −3.5 has FC ≤ 0.9. |
| N23 | ConStellaration ALM-NGOpt from near-axis seeds, nfp 3 (control) vs nfp 2, ~4k evaluations each | Inconclusive: the nfp-3 control is also infeasible at this budget. |
| N24 | ALM-NGOpt from selected401 (modes 4/6, signed-ι defect corrected) | Best normalized violation 0.22. FC floors at **1.09**; QI degrades to −2.77. |
| N25 | ALM-NGOpt from the 3 best-QI MIT-dataset nfp-2 rows already meeting W, FC, mirror and ι | Best normalized violation 0.24–0.31. FC (0.84) and W hold, but QI stays at −2.4 to −2.7 (needs −3.5). |
| N26 | ConStellaration's DESC omnigenity pipeline with an extra well term and elongation ≤ 4.5, on 2 QI-good nfp-2 rows | The control reproduces the stored rows. Capping elongation cuts FC 0.93 → 0.77, but QI falls to −3.17. DESC's well term barely moves W. |

**Two defects found when using the 0.2.6 optimizer on our plasmas.**
1. Its ALM runner constrains *signed* ι, while the problem scores \|ι\|. Our targets have ι < 0, so the runner
   pushes ι through zero.
2. The default 4/4 mode truncation raises selected401's log10 QI from −4.62 to −3.45.

**Leaderboard context** (metrics only; the bench datasets declare no licence):
- None of the 21,049 MHD-stable submissions is nfp 2.
- 5,190 nfp-3 boundaries at A 9–11 are feasible within the benchmark's 1e-2 tolerance. The best exactly
  feasible one has L∇B 12.67, compared with 6.14 for selected401. ConStellaration's own baseline seed is nfp 3.

**Conclusion.** Near selected401, three independent methods meet W ≥ 0 and mirror ≤ 0.25, but not FC ≤ 0.9.
FC floors at 1.06–1.09, and pushing on it costs QI. Starting from the other side does not close the gap either:
low-FC nfp-2 plasmas (N25) and QI-good ones (N26) both trade QI against FC. At nfp 2 and A ≈ 10, QI quality and low flux compression
pull against each other through elongation. This is evidence for the owner's design-class decision (stay at
nfp 2, or allow nfp 3), not proof of infeasibility. A larger budget or another starting family could still
succeed. The coil tools are nfp-2-only today.
