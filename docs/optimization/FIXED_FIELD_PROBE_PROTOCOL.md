# Newly certified fixed proposals: matched field comparison v1

26 September 2026. Prospective scientific registration; native execution follows
separate implementation qualification and a committed execution checkpoint.
No new optimizer, gradient, equilibrium or adaptive candidate selection.
[Geometry results](../geometry/LOCAL_CURVATURE_RESULTS.md) ·
[Method/input review](FIXED_FIELD_PROBE_REVIEW.md) · [Index](README.md)

## Question and inputs

Do the two fixed proposals newly certified by local whole-homotopy curvature
improve their actual coil fields over their immediate accepted predecessors?
This is a diagnostic local comparison, not full physical admission or Step 4.

Fixed order: reference-n6-N selected predecessor trial 93; its rejected trial 94;
reference-n8-N selected predecessor trial 49; its rejected trial 50. These are
indices 2, 10, 4, 11 in local-curvature-inputs-v1, with final geometry results at
`c7562ca`, subsequently committed at `1040bb7`. Freeze exact named coefficient bits,
state hashes, original seeds, every actual physical matrix, geometry evidence,
target input/wout, archived64 normalization, original source graph and saved
search context before implementation. A metadata-only selector must establish
the predecessor relation, not infer it from the selected label. Proposal fields
are absent in original reports and must never be synthesized from old results.

All four states require the successful new producer/auditor geometry results and
their original seven non-curvature gates. Preserve both old negative certificates.
Fresh native admission reuses protected_fine_inputs.archive as an additive current
source/environment check; old graphs remain historical, without rewritten HEADs,
paths or hashes. Use original-seed models, not models initialized at a changed
candidate. Reuse numerical primitives directly; do not forge proposals into the
old selected-candidate adapter schema.

The [fixed manifest](../../evidence/fixed-field-probe-inputs-v1.json) contains
378,385 bytes, SHA-256
`4997daf18d1ec5d94e1e6fd73f74e2a9ca8a83d269986241fdf64fb80c456699`.
It binds 294 read references and all four completed geometry-check chains.

## Exact new native schedule

Two serial pairs, each control then proposal; six models per state in this order:

    index  nphi ntheta ncoil ninner offset
      0      64   64    256    32    0
      1     128  128    256    32    0
      2     128  128    512    32    0
      3     128  128    512    32    0.5
      4      64   64    256    64    0
      5      64   64    512    64    0

Boundary offset shifts only boundary phi/theta. Coil nodes and 256-point
initialization/diagnostic loops remain unshifted. Each fresh original-seed model
performs one loop-A initialization, then candidate boundary B, interior B, loop A,
boundary A, interior A and loop B, in that order. Per model exactly seven native
requests; all 24 models total 168 requests and 804,864 requested points. No VJPs,
warm-ups, derivative checks, extra flux grids, extra acceptance-geometry jobs
or native retry. Existing value/penalty and reconstruction routines still sample
coil geometry at the specified ncoil; preserve those calculations and full J.

At level 0 obtain the flux-normalized current once for each of the four states.
Control replay must match saved coordinates, names, original geometry/matrices,
sources, B² and target flux exactly; compare numerical current/scale and coarse
metrics to the historical control with 5e-10 relative OR 1e-12 absolute tolerance.
Retain each new coarse snapshot without changing its historical counterpart.
Freeze each new snapshot's state-specific current/scale bits and signed physical
copies for levels 1–5; no fine-grid recalibration or mixing historical and new
normalizations. Retain current changes explicitly.

Use value-only snapshot/arrays and the same unfrozen cached metrics at level 0.
Calling frozen diagnostics after that snapshot invalidates the cache and would
add three requests: prohibited. Levels 1–5 use frozen diagnostics/arrays with
same-state cache reuse. Set/validate named coordinate bits and clear cache once
before each model's single candidate evaluation, never between snapshot, metrics,
arrays or supplement calls; never call evaluate(). Native callbacks must
prove the exact dispatch/completion order and point counts, including initializers.

Run all six grids regardless of favorable/unfavorable coarse metrics. Numerical,
source, work, I/O or resource failure stops the affected pair and records every
explicit completed prefix and unchecked operation; it cannot select a preferred
subset. Continue to the other pair if source integrity and disk reserve permit,
without transferring budget or retrying the failed pair.

## Independent checks and labels

Reuse original archived64 target reconstruction, composed_metrics, sampled
direct B/A and original-seed initializer integration. Keep metric tolerances
5e-10 relative OR 1e-12 absolute; direct B/A and initializer 5e-10 relative,
initializer zero absolute slack. Check actual saved arrays, canonical named
snapshots, currents, unit/target/seed flux, initialization geometry and fixed B².
All six grids and raw archives are mandatory. Keep all individual comparisons.

Reconstruct and report each of the six diagnostic loop fluxes from saved loop A
and tangents. For each require abs(flux-target_flux)/abs(target_flux)<=1e-6, with
finite nonzero fixed signed target_flux. Both states must pass all six before a
gain label is eligible. This uses no new native requests and is not the omitted
full line/fan/Stokes flux qualification.

Original five refinement pairs and 1% relative OR 1e-7 absolute checks remain a
separate numerical qualification. Metric improvement cannot excuse their failure.
Report all six J, normal RMS, normal max, interior-vector RMS and current rows.
Report absolute field/current gates (1e-4 normal RMS, 1e-3 normal max, .01 inner
vector RMS, 500 kA), without claiming full flux/geometry/physics acceptance.

Original coarse Armijo is a separate counterfactual decision: reconstruct the
saved predecessor's gradient dot saved direction using explicit canonical names,
alpha and the originally registered Armijo coefficient; compare reconstructed RHS
to saved RHS within existing tolerance. The decision is strictly J_proposal <=
the exact saved RHS, without acceptance slack. Report abs(current)<=500 kA as a
separate current gate. Do not count this as an accepted historical search step.
No new gradient is computed or retrospectively chosen.
The predecessor J is the original search scalar, not its replayed value or an
almost-identical bundle scalar. Reconstruct the registered direction/preconditioner
and active-coordinate update, including exact unchanged inactive bits, before
accepting the stored Armijo context.

Define delta_j=m_control,j-m_proposal,j (positive means lower proposal error).
For normal RMS, use boundary levels 0, 1, 2, 3. For each state separately define
e=max(abs(m0-m1),abs(m1-m2),abs(m2-m3)). The fixed empirical margin is
1e-7+4*(e_control+e_proposal). Label a normal-error gain resolved by this
diagnostic only if both states pass numerical qualification, all four deltas are
strictly positive, and min(delta2,delta3) strictly exceeds that margin.

For interior-vector RMS, relevant levels 0, 4, 5; per-state e=max(abs(m0-m4),
abs(m4-m5)). Require all three deltas>0 and delta5>1e-7+4*(e_control+e_proposal),
again conditional on both numerical qualifications. Record both labels separately.
Normal maximum and current are reported trade-offs, not hidden by an RMS label.
No combined Pareto/physical-improvement flag follows. This sensitivity margin is
empirical and deliberately conservative, not a rigorous discretization-error bound.
Retain and report all deltas even if the margin or sign condition fails.

Here each state's required numerical qualification means all six complete ordered
raw records, all six initializer reconstructions, all six metric reconstructions,
all 36 sampled direct B/A statistics, all five original refinement checks and all
six diagnostic flux checks pass; its coarse value-only replay is valid when it
is a control. Missing, malformed or unchecked data cannot acquire a gain label.

## Bounded execution and storage

POSIX, serial, with OMP_NUM_THREADS, OPENBLAS_NUM_THREADS, MKL_NUM_THREADS and
VECLIB_MAXIMUM_THREADS fixed to 1. Each pair has 600 s construction and a separate
600 s independent saved-data audit. The parent starts each monotonic
phase clock before source admission, mappings/model startup and input rehash;
serialization and final acknowledgement count. At expiry only failure/prefix
publication is allowed, with 5 s grace and hard process-group termination at 605 s.
All late returns are failures, even if prior values were finite or every calculation
finished. No phase budget transfer, altered caps or automatic retry.

Keep 3 GiB free before each pair and 2 GiB during work; stop without deleting old
outputs. New scientific payload cap 512 MiB per pair, shared by producer and audit;
reserve 64 MiB before each model, plus 2 MiB for indexes/failure metadata. Individual
NPZ<=64 MiB, JSON<=8 MiB, using existing exclusive SnapshotStore and strict loaders,
no pickle. Retain attempts, native callbacks, model/operation identity, raw result
hashes and explicit successful returns; file presence cannot establish success.
Bound callback/control stream and metadata, reject extra events and lost errors.

## Qualification before execution

Commit final protocol, four-state metadata manifest and internal method review.
Then test the thin composition: exact 24-model / 168-call / 804,864-point schedule, original
seed vs candidate, frozen/refined currents, cache invalidation/no VJP, wrong named
coordinates or state substitution, extra/missing/out-of-order/swallowed native
events, serialization/deadline failures, storage caps, coarse control replay,
refinement and margin equality/sign/trade-off cases. Independently review the
value-only bridge and saved-data checker. Preserve failed controls.

Run focused/public/docs and the full research regression, commit qualification,
then a separate source-bound execution checkpoint. Admit exact active numerical
environment and sources before work; recheck them after. All results remain
diagnostic, with physical_admission, step4_pass, ms1_reached and sota_advance false.
No success criterion, inputs or budgets may change after new field values are seen.
