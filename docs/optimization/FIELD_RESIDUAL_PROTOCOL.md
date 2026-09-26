# Saved-field residual diagnosis: fixed exploratory analysis

26 September 2026. Registered before loading the saved field arrays for this
analysis. Existing scalar outcomes are known; this is exploratory diagnosis,
not independent confirmation of the earlier improvement. [Index](README.md)

## Question and scope

Does the response of the two fixed, newly certified steps substantially align
with the remaining normal-field error? How different is progress in the raw
normal-field objective from progress in the normalized acceptance metric?
Do this before committing to longer local searches. No new native field calls,
gradients, geometry bounds, candidates, equilibrium solves or threshold changes.

The [fixed field results](FIXED_FIELD_PROBE_RESULTS.md) at result commit `5378d1d`
are the sole input study. Bind `evidence/fixed-field-probe-results-v1.json` SHA-256
`94835d9c3f59552fb2e194d877f1728b2413ba64166ff29453e11e2f05027496`
and its explicitly returned study
`7d881cb3a7cc2f58feca4020e9f32f3430fffba0f7eb0cf285c7a0f5f4f906c2`.
Use both cases, in n6/n8 order, both control/proposal states, boundary levels
0,1,2,3 in order: sixteen stored models, eight paired comparisons. Inner-only
levels 4/5 are omitted by design, not by outcome. Preserve every comparison.

## Intake and mathematical definitions

Follow the explicit result → study → producer/state/model references; verify
exact lengths and SHA-256 before parsing. Check state hashes, roles, case/grid
identity against the bound result and manifest, and original snapshot identities.
Rehash the prior independent review, but do not claim to replay its entire
historical graph. Use bounded no-pickle array loading. Within each pair require
bit-identical boundary points, normals and weights, and identical positive
`B2_scale`. Reject malformed/nonfinite data, nonpositive weights, zero field or
normal, changed shapes or inconsistent source identities. Normalize normals to
unit length and weights to sum one, as in the original metric.

For each control C / proposal P, let `bn = B dot unit_normal`, `m = |B|` and
`<a,b>_w = sum(w*a*b)`. Analyze **signed** residuals, never absolute-value fields:

- Acceptance: `rN = bn/m`; `||rN||_w` reconstructs normal RMS.
- Objective: `rJ = bn/sqrt(B2_scale)`; `||rJ||_w²/2` reconstructs JN, not full J
  (which also includes geometry penalties).

For each residual type set `d = rP-rC`, `A=<rC,rC>_w`, `C=<rC,d>_w`, `D=<d,d>_w`.
Record both norms, the observed change, secant norm, signed alignment
`-C/sqrt(A*D)`, aligned squared-error fraction `C²/(A*D)`, and the unconstrained
algebraic best coefficient `alpha=-C/D`. Here alpha=0 is control and alpha=1 is
the measured proposal; also report proposal-origin `beta=alpha-1`.
Calculate the remaining norm from the explicit vector `rC+alpha*d`, not the
cancellation-prone subtraction `A-C²/D`. Report its fraction of the control norm;
only for rN also report its ratio to the unchanged `1e-4` acceptance limit.
Check orthogonality and the Pythagorean identity independently.
All reported changes (RMS, JN and boundary field RMS) mean **proposal minus
control**. Pythagoras here means `A = ||rC+alpha*d||_w² + alpha²*D`.

If `||d||_w <= 1e-12*max(||rC||_w, ||rP||_w, 1)`, mark the projection unresolved
and leave alignment/fraction/alpha/beta/fit null; retain the measured norms and
secant. If the control residual is zero, alpha may still be defined for a
resolved secant, but alignment and relative fraction are undefined. Do not
regularize or clip a result into a favorable category. This is a numerical
conditioning rule, not a physical significance test.

## Exact numerator/denominator decomposition

For normalized residual change retain the asymmetric, control-denominator split:

`u = (bnP-bnC)/mC`, `v = bnP*(1/mP-1/mC)`, so `dN = u+v`.

Report `||u||²`, `||v||²`, `2<u,v>`, `2<rC,u>`, `2<rC,v>` and check both the
vector identity and the identity for `||rP||²-||rC||²`. These are signed
squared-error terms, not additive RMS percentages or causal attribution.
Explicitly, that difference is
`2<rC,u> + 2<rC,v> + ||u||² + ||v||² + 2<u,v>`.
Uniform positive current scaling cancels from rN; numerator and denominator
terms can therefore be individually large and cancelling without improving
field alignment. rJ changes under that scaling. Report boundary field RMS and
both JN and normal-RMS changes; do not call a denominator contribution a current
or energy-efficiency mechanism without further evidence.

## Verification, work and execution

Use a NumPy implementation and a separately authored scalar/math.fsum checker
that does not import the producer or original metric implementation. Reconstruct
saved RMS/JN within `5e-10` relative OR `1e-12` absolute; use the same limits for
independent scalar comparisons. Identity checks use `1e-12 + 5e-10*natural_scale`
(norm products for orthogonality, A for Pythagoras, squared norms for energy).
Synthetic controls cover known aligned/orthogonal residuals, both alpha origins,
uniform current scaling, nonunit normals, nonuniform weights, zero/nearzero
secants, zero control residual, invalid/nonfinite data and comparison tampering.

The source-only implementation/review and synthetic tests must be committed
before real-array execution, at clean source with before/after identities.
Use one serial saved-data worker, fresh exclusive outputs, a 60 s work deadline
including intake and independent arithmetic and 65 s external hard timeout.
Keep 3 GiB start /2 GiB live disk reserve, 8 MiB total analysis output, 8 MiB
JSON inputs and 64 MiB per NPZ including bounded uncompressed contents. Load at
most one control/proposal pair at a time; avoid dense Jacobians or SVDs. These
bounds do not constitute an enforced process-memory cap. No retries or partial
success: retain failures and incomplete prefixes, without filling missing rows.
Record exactly sixteen model inputs, eight comparisons, sixteen residual fits
and eight decomposition checks. A prefix may be inspected only as incomplete.

## Interpretation and next decision

This is a **one-secant affine residual-space fit**, not a magnetic field at
extrapolated coordinates, a feasible coil displacement or a lower bound on what
this coil class could achieve. Alpha need not be near one or within any geometry
limit. A substantial orthogonal residual explains why repeating this same
observed response cannot remove the mismatch; it does not constrain later
directions or nonlinear motion. A small fitted residual likewise establishes
no physical feasibility. Keep all grid results and show their variation.

A separately reviewed planning proposal specifies one additional fixed 1 mm
normal-objective trial with fixed-direction and actual-direction FD controls,
155 requests per case, original-seed geometry protection and fresh replay.
It is not registered or authorized for native execution by this document.
Use this diagnosis to decide whether that small integration test, an objective
comparison, tighter clearance bounds or a broader coil initialization study has
the best next scientific value. Step 4A–4D and MS1 remain open.
