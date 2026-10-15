# Proposed plasma requirements: dataset calibration

15 October 2026. Input for [#113](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/113),
not approved requirements. [Protocol](PLASMA_CALIBRATION_PROTOCOL.md) frozen before
outcome access at `64ac4f2`, clarified at `d516c1e`; producer base `ed72af9`.
[Complete evidence and replay](https://github.com/pjckoch/nuclear-fusion-at-home/tree/3ec6875df956cdaeb87df7b4cfeea8bdacd5a6e5/evidence/plasma-requirements-calibration-2026-10-15).

**No comparable stored dataset row meets the proposed QI bound; joint passes are
therefore zero. Flag this for the owner before freezing v1.** This does not
establish physical infeasibility or authorize a relaxed bound. Stored-label
comparability remains conditional on [#112](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/112).

## Population and result

The [pinned default vacuum dataset](https://huggingface.co/datasets/proxima-fusion/constellaration/tree/8da71572eb63ce93e77ce89bec0d7c30b7eba89e/data)
(Proxima Fusion; card declares MIT) contains 182,222 published rows, including
23,537 with missing selection fields. The closed selection `nfp=2`, aspect ratio
`9 <= A <= 11` retains **12,366 rows with unique boundary IDs** and five finite
required metrics. Missing/malformed selection counts are 23,537/0; no selected
IDs are missing or duplicated. Fractions below use all 12,366 selected rows;
valid-metric denominators give the same fractions.

| Proposed exact hard bound | Passes | Fraction |
| --- | ---: | ---: |
| Vacuum well >= 0 | 524 | 4.24% |
| Bad-curvature flux compression <= 0.9 | 1,333 | 10.78% |
| log10 QI <= -4 (raw QI <= 1e-4) | 0 | 0% |
| Absolute edge transform per field period >= 0.25 | 3,555 | 28.75% |
| Edge mirror ratio <= 0.25 | 4,443 | 35.93% |
| All five together | 0 | 0% |

QI and joint prevalence trigger the preregistered strictly-below-1% rarity flag
and the separate zero flag. No thresholds or subpopulations changed. Joint-pass
L-gradient-B and elongation distributions are **empty**, not zero-valued.
For context, selected-population L-gradient-B median is 5.071 (5th–95th percentiles
2.202–6.881), elongation median 5.364 (3.457–7.094); full linear quantiles are in
the evidence. Unique-boundary sensitivity is identical.

## Checks and limits

Primary arithmetic and a separate arithmetic implementation agree on every
marginal/joint count; deterministic replay matches report SHA-256
`31c519c9fa166d0dc2e776a15f22389f292eb1786018229a659f2479e293fb96`.
Analytic exact-bound/missingness/sign/error controls pass; a mutated cached range
is rejected. Python 3.14.8, PyArrow 26.0.0; no native solves. As an explicitly
exploratory diagnosis, selected minimum QI is 2.0216407388e-4; nine rows outside
this selection meet 1e-4. That does not alter this calibration population.

The mapping follows inspected upstream source `d083b75`: QI is sum of squared
residuals and transform uses absolute value (203 selected transforms are negative).
We apply exact draft bounds, without upstream's 1% feasibility tolerance. The
inspected source revision does not establish the dataset producer or fidelity;
#112 controls must qualify comparison with newly scored plasmas.
Forward-model error flags are false for all selected rows; earlier generation
flags often are null. Unknown flags cannot pass the registered joint check, but
**metric-only joint passes already are zero**, so that policy does not cause the
result. Selected rows are not independent families; optimization/selection bias
prevents interpreting these fractions as design feasibility probabilities.

Only projected columns were fetched: 692 individually verified ranges,
21,510,090 cached input bytes within the 128 MiB transfer ceiling; generated
nonrange outputs below 1 MiB within the 20 MiB output ceiling. Published
whole-shard LFS identities are recorded, not independently verified. Raw cache
is retained locally and obtainable by pinned URLs plus range hashes; scripts,
results, manifests and provenance are in the evidence snapshot. No gate, archived
result, plasma requirement or optimization was changed. Owner approval remains
required before freezing `plasma-requirements-v1`.
