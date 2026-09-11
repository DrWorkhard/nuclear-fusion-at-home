# Spatial flux factorization qualification v1 — 2026-09-11

Declare before the new numerical qualification; no optimization in this phase.
Hypothesis: representing flux by one aggregated residual hides useful spatial
information from the Gauss-Newton approximation. A different residual
factorization can keep the scalar objective and its exact gradient unchanged.
This is an algebraic construction, not a claim of novelty or better optimization.

For M fixed surface nodes, non-unit normals N_i, and fields B_i, define
z_i = (B_i dot N_i)/sqrt(M |N_i|). Then Phi = ||z||^2/2 is the existing raw
quadratic flux. The guarded common vector uses v_0 = k Phi above its cut-in
8e-9 and zero below. Replace this single residual by

    r = (k/2) ||z|| z,
    Dr = (k/2) [ ||z|| Dz + z (z^T Dz)/||z|| ].

At z=0 use r=0, Dr=0. Below cut-in both are zero. Thus r^T r = v_0^2 and
Dr^T r = Dv_0^T v_0. All seven other residuals remain unchanged. The upstream
cut-in is discontinuous, not a smooth hinge: no derivative claim at that boundary.
Qualify physical fields only if their raw flux is at least 1% away from cut-in.
Use the original guarded normalization; do not retune weights or thresholds.

## Controls and physical cases

- Core analytic/random tests: raw quadrature identity; lifted value/gradient
  identities; directional finite differences; zero and clipped branches;
  malformed/nonfinite input rejection; a 2D example where equal scalar objectives
  have different Gauss-Newton ranks.
- Two fixed states: original promoted warm start and guarded TRF best candidate.
  Rebuild the guarded context; map the archived candidate's DOFs by its physical
  serialized coil/current graph, never by positional array assignment.
- Surface 32x32 half period and 200-point coils, exactly as in guarded search.
- Obtain Dz through 1024 individual analytic field B_vjp calls per state in the
  current global named-DOF basis. This is a qualification implementation, not
  presumed computationally competitive. Record all extra calls and timing.
- Compare raw Phi and dPhi to the pinned upstream objective: relative scalar
  error <=1e-10 and max-component gradient error/max(1,max|reference|) <=1e-10.
- Compare full common merit/gradient after replacement to the eight-component
  original under the same tolerances. No physical acceptance limit is changed.
- Seed-45 canonical physical direction; centered steps 1e-4, 1e-5, 1e-6.
  Evaluate the field-only z/r at six perturbed states, without hidden Jacobian
  calls. Finest max-component directional errors normalized by max(1,max|exact|)
  <=1e-6 for both z and r. Retain every step and any failure.
- Store z, Dz and the original common vector/Jacobian for independent algebraic
  replay. Report singular values/ranks at relative threshold 1e-10, not as an
  acceptance or causality test. A changed rank does not prove better convergence.

## Exit and subsequent work

Only passing qualification permits a separately declared optimizer comparison.
Measure actual additional derivative work before claiming equal budgets: one
spatial Jacobian is not equivalent in cost to one old eight-component bundle.
Frozen high-resolution flux/geometry and continuum checks remain mandatory for
any candidate. No new feasible baseline, engineering validity or SQuID-C readiness
can follow from algebraic qualification alone.

Implementation references are the locally pinned SIMSOPT fluxobjective.py,
biotsavart.py and _core/derivative.py; executing source hashes must be recorded.
