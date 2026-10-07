# Four small surface changes offer no substantial fixed-coil shortcut

The bounded exploratory diagnostic completed once on 7 October 2026. Its
question was whether four small boundary modes could halve normal-field RMS
with the [latest scale035 coils](ISSUE37_FIT_COUPLING_RESULT.md) held fixed.
**The selected step reduces RMS only 1.394%; do not spend an equilibrium solve
on this surface-only candidate.** Retain the earlier ideal-validated target.

The four modes are rbc(1,1), rbc(2,0), zbs(1,1), zbs(2,0), motivated by
[draft PR59](https://github.com/DrWorkhard/nuclear-fusion-at-home/pull/59).
This separate diagnostic does not test that contributor's moving-coil optimizer.
It uses trial 427's fixed physical coils and currents, with no flux normalization,
new equilibrium or ideal scoring. It neither rejects joint optimization nor
rules out other nonlinear steps or global solutions.

Central differences at 10 and 5 micrometres include field-point motion, normals,
|B| normalization and changing area weights. The 64-square linear model's box
solution selected displacements **[+0.24609, +0.07985, +0.29383, −0.00232] mm**,
all inside ±0.5 mm. That single step was frozen before nonlinear evaluation.

| Metric | Frozen baseline | Moved surface |
| --- | ---: | ---: |
| Worst fine area-weighted RMS | 0.001966301619 | 0.001938896861 |
| Worst fine maximum normal error | 0.009205158478 | 0.009622185190 |
| Relative signed-flux error | about 4.4e-16 | 0.00722125 |
| Volume, m³ | 0.1900653462 | 0.1900307095 |

Fine RMS ratios are **0.98606279026 / 0.98606279023** on the two 128-square
shifts, missing the 0.50 hurdle. Derivative-step disagreement ≤5.26e-9, nonlinear
residual disagreement 0.0002763 of baseline RMS and coarse/fine RMS disagreement
≤9.64e-7 pass their respective 1e-3 / 0.01 / 0.001 checks. Independent B checks
at 64 points per fine grid agree within 4.69e-16. The local model is useful,
but its predicted reduction is small. Both absolute field limits still fail;
peak error worsens and the unchanged flux tolerance also fails. The moved
surface is not a qualified equilibrium; geometry, ideal benefit, interior and
topology are untested. No physical acceptance follows.

One attempt took **5.327 s** within 180 s, using one native thread, 32 MiB output
ceiling and 3/2 GiB disk reserves. Clean producer/evaluator:
`617251a65f2342d6e97590db70e810966b4c0cf2`. Local archive:
`44a0049d86a9f93424e04ad9841997232a094d03`; prepared tag
`evidence-issue37-boundary-response-v1`, publication pending. All 25 raw files
(7,897,305 bytes) and original inputs remain intact. The 39-entry manifest SHA256
is `5f80ccca807322d5ebf96f8c30e8701d31978e1ef68beedbd99890305a0f8a14`.
The completed study script/tests resolve in that archive, keeping active code small.

Saved-evidence replay verifies 61 source/input bindings, residuals, derivatives,
linear solution, nonlinear metrics, volumes and decision, plus independent B
samples. It does not rerun native fields, remeasure loop flux, solve equilibria,
qualify geometry or re-attest timing. Reproduction and local-only dependency
availability are documented in the archive. Agent review is not external peer review.
