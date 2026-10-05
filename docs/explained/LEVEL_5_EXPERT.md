# Level 5: for an expert

Updated 5 October 2026 · [All five levels](README.md) · Previous: [Level 4](LEVEL_4_GRADUATE.md)

An open, agent-assisted two-stage stellarator study. The plasma stage improved a
vacuum QI diagnostic on an open target. The coil stage has not yet realized any
target within the pre-registered field tolerances, and no transfer of the plasma
benefit to a coil field has been shown. The front-page press note is a vision,
not a forecast; the [status page](../STATUS.md) states that present evidence does
not support its timeline.

## Claims and non-claims

| We claim | We do not claim |
| --- | --- |
| Selected W7-X and Goodman reference calculations reproduce locally; the broader W7-X comparison stands at 60/63 | A complete reference reproduction |
| A preregistered vacuum bounce-action variance reduction of 11.17% (wide) and 4.85% (narrow) on reference401, ten gates passed | Better confinement, a finite-β result, or a blind holdout: both domains informed construction |
| A geometry-checked six-coil set (24 filaments) with boundary RMS(B·n/\|B\|) 0.001996, maximum 0.00943 and interior RMS 0.01148 | Acceptance: the limits are 1e-4, 1e-3 and 0.01 |
| Ten traced field lines (s = 0.05–0.95) stay confined for 200 transits, signed ι within 0.005 | Nested surfaces, island widths or edge behaviour |
| Portable shared checks reproduce archived boundary/geometry metrics to 1.5e-15 and interior metrics to 8e-11 | Independent reproduction: same machine family, same code |

All coil work targets the original reference401 (nfp = 2, zero β, normalized
scale), not the improved Step 3 target. Detail: [Level 4](LEVEL_4_GRADUATE.md),
[Step 4 requirements](../steps/STEP_4_PLASMA_AND_COILS.md).

## Methodological safeguards

- Construction and acceptance are separate; thresholds are fixed before outcomes
  and never relaxed afterwards. Candidates cannot modify their evaluator.
- Acceptance uses fine boundary grids, continuous geometry bounds, three interior
  resolutions and independent B / A computations, all at frozen currents. A
  solver stop or a low objective value is never acceptance.
- Failures are retained: the rejected first plasma design, coarse clearance
  sampling that missed 1.8–6.7 mm gaps, a certified small-step search on a poorly
  aligned objective, and current-only freedom that could not close the gap.
- Evidence is bound to producer revisions, hashes and immutable `evidence-*` tags;
  see [reproduction](../validation/REPRODUCING_RESULTS.md).
- Public contributions are reviewed by an AI-assisted maintainer routine; merging
  is not scientific acceptance, and agent review is not peer review.

## Weaknesses worth probing

- **Physics relevance of the Step 3 metric.** A few-percent to 11% variance
  reduction in one vacuum diagnostic, with domains used during construction, may
  not survive coil realization, finite β or a broader QI/orbit assessment.
- **Two-stage disconnect.** Coil fidelity at 2e-3 normalized normal error may
  already erase a small plasma-side gain; the diagnostic must be recomputed in
  the realized field before any transfer claim.
- **Tolerance calibration.** The 1e-4 / 1e-3 / 0.01 pilot limits and the
  geometry limits are project choices at a normalized scale. The boundary metric
  itself was checked against QUASR and LPQA boundary components, which does not
  cover the complete Goodman acceptance profile or any engineering standard.
- **Verification depth.** Geometry bounds use padded floating point rather than
  interval arithmetic; numerical independence mostly means separate calculations
  on one machine; the filament model has no finite build, forces or strain.
- **Public versus native metrics.** The public starter uses 64 sparse samples and
  fixed currents; the research checks use dense grids and flux-normalized currents.
  A public score is a hint, not evidence.

## The open decision

The [programme](../optimization/STEP4_RESEARCH_PROGRAMME.md) sets a binding
24 October 2026 decision. The fixed-target recipe continues only if a matched
reference401 comparison at least halves the geometry-checked boundary RMS without
worsening interior RMS, and the realized-field diagnostics support investigating
benefit transfer. Otherwise the project changes to another coil family, another
target, or joint plasma–coil optimization in existing software. A desk-level
reactor feasibility screen is planned alongside it: device scale, field, power balance,
magnet loads, blanket and shield space, heat exhaust and maintenance access.

## Where expert input helps most

- Adversarial review of claims, gates and open pull requests.
- Whether the bounce-action variance target is a sensible proxy, and which
  realized-field diagnostic would settle benefit transfer cheaply.
- Calibrating tolerances against published stage-2 practice, or connecting the
  checks to existing community benchmarks such as StellCoilBench or QUASR.
- A feasibility constraint that would rule out this direction early.
- Independent reproduction on another machine or with an independent code.

Start with [CONTRIBUTING](../../CONTRIBUTING.md); critical and negative results
are welcome. The [assessment](../review/STRATEGIC_REVIEW_RESOLUTION.md) records
the project's own view of its route and simplifications.
