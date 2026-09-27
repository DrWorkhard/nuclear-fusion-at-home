# Constraint-aware coil fitting

27 September 2026. **Exploration; not independent confirmation.**
[Programme](STEP4_RESEARCH_PROGRAMME.md) · [Static starts](COIL_START_SCREEN.md)

## Question

Can stronger geometry penalties or fewer free Fourier modes turn the observed
field-error reduction into a geometrically usable candidate? The
[first objective comparison](NORMALIZED_OBJECTIVE_EXPLORATION.md) lowered RMS
only by violating curvature (and, for the raw objective, plasma clearance).
The static screen found no better initial field, but circular coils have more
curvature margin. Compare these construction choices before widening the family.
This is exploration session 3 of the programme's ten-session window.

## Inputs and prospective matrix

Use only the unchanged `n6-circle-d100mm` and `n6-shape-d100mm` snapshots and the
reference target identified in the static-screen record. Bind that completed
screen by SHA-256; derive each start's magnetic metadata from its own measured
loop flux and fresh normalization. Do not transfer the shaped coil's current
scale to the circle. Both start with six order-5 base curves, 24 physical coils,
two field periods and stellarator symmetry.

Run four arms, circle then shaped, full then low-order:

- **Full:** all 198 named coefficients free.
- **Low-order:** only constant and sine/cosine modes 1–2 free (90 coefficients);
  all higher coefficients remain exactly those of that start, not zeroed.

All arms minimize half the area-weighted squared local-normalized error, plus
the same construction penalties: length above 3.5 m, coil separation below
0.07 m and plasma clearance below 0.09 m (distance weights 1000), and integrated
quadratic excess curvature above 10/m (weight 0.01, 100 times the previous arm).
The distance margins and penalty weights guide construction; they do **not**
change admission: length ≤3.5 m, curvature ≤12/m, coil separation ≥0.06 m,
plasma clearance ≥0.08 m, current ≤500 kA, RMS ≤1e-4, maximum normal error ≤1e-3,
and relative target-flux error ≤1e-6. Interior/other requirements remain open.

Each active coefficient stays within ±0.02 m of its own start. This is a
coefficient bound, not a bound on pointwise motion. Use the existing named
derivative mapping, current-normalization chain rule, sparse distance evaluator
and native optimizer. Do not modify the previous experiment or its evaluator.

## Execution and checking

Coarse grids: 64² boundary, 256 coil/loop nodes; 128² full-torus surface for
distance penalties. Each arm permits **240 total value/gradient bundles**,
including ten startup bundles, and **300 s startup/search**. Startup requires
matching that case's static seed metrics, sine/cosine directional checks in its
active coordinates at 1e-5 and 5e-6 m (absolute error ≤1e-7 or relative ≤1e-4),
and an exact value/gradient repeat. Failure stops that arm before search.

Persist all trial coordinates, metrics, gradients and attempted/completed counts.
Report the lowest objective and, separately, the lowest RMS among actual seed/
search points meeting sampled geometry and current limits. Probes are ineligible.
Reject late results; the solver's success flag does not imply physical acceptance.

Freeze the best sampled-feasible point per arm (or its seed if no improvement).
Screen it at 128² boundary / 512 coil/loop nodes, unshifted and half-cell shifted,
with its **coarse current fixed**. Save full B/normals and loop A/tangents, plus
independent field comparisons. Fine sampling is adaptive exploration, not an
unseen confirmation set. A passing sample is not a continuous geometry certificate;
any promising point needs a separate continuous check before such a claim.

Use one native thread, 128-point field blocks, a **1,800 s worker / 1,805 s
external process-group cap**, 256 MiB outputs and 3 GiB initial / 2 GiB live disk
reserve. Fresh outputs under `artifacts/constrained-coils-v1/`; retain failures
and bind actual sources before/after. No equilibrium, pressure, topology,
interior-vector, finite-build or load computation in this experiment.

## Decision

Compare both field/current trade-offs and geometry, not just objective values.
Fine RMS below 1e-2 with geometric gates remains a triage signal, not acceptance.
If geometry improves but field quality stays far from that signal, consider a
different initialization/family or parameter freedoms; do not declare an optimum
or target impossibility from this small search. Independent confirmation and
Step 4A–4D remain separate requirements.

Implementation is being prepared; no new search result is claimed yet.
