# Interior field term in the active fitter (#98)

[Active coil research](README.md) · [Acceptance v2](../validation/ACCEPTANCE_V2.md) ·
[Issue #98](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/98)

**Question.** Most fits fail acceptance v2 on interior vector RMS (> 0.01), not on the
boundary. #12 lowered interior error with a weighted interior term, but only in a
retired script. Does the same term in the active normalized fitter give a coil set
that passes v2 with margin on both?

**Method.** `fit_coils.py --interior-weight W` adds W · ½ mean|s·B − B_target|²/B2 at the
flux-normalizing scale s = target_flux/φ(x). The gradient passes through s (native
finite-difference test). The target is sampled from the bound Wout on
s = 0.125/0.375/0.625/0.875 (16 × 16, half-cell shift). The checks keep their surfaces,
s = 0.25/0.5/0.75, so no objective point is a checked point. With W > 0, selection
takes the eligible point with the lowest boundary + interior objective.

**Inputs.** Reference401 through a vmecpp 0.8.0 Wout regenerated from the committed
input (SHA-256 `0f2b626c…`; consistent with the public starter, not dense identity).
The seed is the length-headroom snapshot, order 5. SIMSOPT 1.11.1, one thread, macOS.
The run's recorded hashes of `fit_coils.py`, `coil_fit.py` and `wout_target.py`
equal those at commit `5dbc30c` (rebased from the run's `23788e1`).

**Preregistered arm I** (#98, fixed before the run): `--margins halved
--interior-weight 0.05`, 1800 s search + 900 s checks. The search stopped on its time
budget after 3,900 evaluations (2,858 accepted iterations). The selected point is the
last one, so the search had not converged.

| Fine 128 × 128, both shifts | #70 arm M | #12 | Arm I |
| --- | ---: | ---: | ---: |
| Boundary plain mean (v2 ≤ 0.0018) | 0.00143 | 0.00168 | 0.00150 |
| Boundary maximum (v2 ≤ 0.013) | 0.0081 | 0.0095 | 0.0083 |
| Boundary area RMS | 0.0017283 | — | 0.0018082 |
| Interior RMS, worst of three levels (≤ 0.01) | 0.00902 | 0.00200 | 0.00184 |
| Worst v2 ratio | 0.902 | 0.931 | **0.836** |

Arm I: **v2 pass**, v1 fail (boundary RMS and maximum). The current is 305,275 A.
Continuous geometry passes at the finer level (the coarser level was unresolved).
Length ≤ 3.4853 m, coil–coil ≥ 0.06055 m, coil–plasma ≥ 0.1479 m, and the curvature
enclosure ≤ 11.022 /m. Coil–coil spacing is only 0.55 mm above its limit. The interior
RMS on the objective's own grid (0.00167) is close to the checked value, so the term
does not fit only its own sample points. A 90 s smoke run with current margins, done
before preregistration, also passed v2 (mean 0.00175, interior 0.0022).

**Conclusion.** On reference401, the interior term moves the binding v2 constraint from
interior error back to the boundary mean. It costs about 5% boundary mean against
#70 arm M. The fitted coils are published as
[`interior-term-halved-margin`](../../submissions/interior-term-halved-margin/README.md).

**Limits.** One seed, one weight, one machine, an unconverged search, and a regenerated
Wout file rather than the maintainer's archive. v2 is benchmark-relative and was set
with reference401 results known. The fit targets reference401, not the improved
Step 3 plasma. On selected401, #12's continuation passes v2 and is the only fit to
complete the wide bounce diagnostic ([#99](STEP3_V2_METHODS.md)), so the next test is
this arm on selected401. It needs the archived Wout `8cd6bebf…`; a vmecpp
regeneration hashes `3d5df9a4…`. This is not physical acceptance. **Update
(14 October):** in [#102](ISSUE102_COMBINED_METHODS.md) this arm passes on selected401
(worst ratio 0.815) and completes the wide bounce domain.

Raw outputs (60 MB) are kept outside the repository, in the contributor's
coordination log N16, with SHA-256 identities: result `6b4ee1af…`, selected snapshot
`914bebd9…`, vector store `cbb7b92a…`.
