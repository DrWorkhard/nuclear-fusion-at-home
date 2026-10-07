# Registered joint-target numerical intake

Prospective implementation check, 7 October 2026. The decision is whether the
[frozen joint proposals](ISSUE37_JOINT_FEASIBILITY.md) can supply internally
consistent target arrays without impersonating either archived target.
[`joint_target.py`](../../src/fusion_baselines/joint_target.py) is a separate
numerical-consistency component. The existing reference401/selected401 registry,
portable checks, fitter and scientific acceptance limits remain unchanged.

## Fixed contract

Only the exact original control and two ±1 mm `rbc(m=2,n=1)` inputs from the
[volume preflight](ISSUE37_VOLUME_PREFLIGHT.md) are recognized. Protocol and input
byte hashes are pinned; every other input value must equal the original.
Recompute both midpoint volume grids inside the caller's budget; no preflight
cache creates uncharged work. The caller must provide an explicit Wout hash.
Bind it before reading and recheck all bound files before returning target arrays.

Require finite complete 401-surface coefficient/profile arrays, valid unique
geometric/Nyquist tables (95 modes through m=4, |n|=10; 809 through m=16,
|n|=24, respectively), fixed symmetry/resolution, matching boundary, fixed linear
flux and its signed derivative, negative Jacobian orientation, fixed-boundary
non-RFP state, success flag and each nonnegative force residual at most the
original 1e-12 tolerance. Pressure must be zero; absolute recorded net current
must be at most 1e-6 A (a numerical zero tolerance). Report these values and require
Wout volume agreement with the independently computed boundary volume to 1e-6.

On all three interior surfaces and both 64²/128² grids, independently reconstruct
geometry with the existing Fourier-loop routine and compare to the matrix sampler
to 1e-12. Reuse the frozen Clebsch/contravariant/field-magnitude checks from
`clebsch_field.compare_fields` at `56181dc4250cb24ce3d2bedf5cec3d894d1ac250`:
positive representation errors at most 1e-3; wrong-sign and missing-2pi controls
above 0.1. Keep `psi=-phiedge/(2*pi)`, radian derivatives and Wout's already
field-period-scaled toroidal modes. Do not flip target fields. Return the existing
32/64 interior-array format with the original reference B² normalization; report
measured target B² separately. Any failed check returns no target arrays.

## Validation and remaining execution prerequisites

Synthetic analytic and mutation tests cover input isolation, malformed Wouts,
force/vacuum/flux checks, representation corruption, geometry normalization and
caller deadlines. Before using new equilibria, freeze and review this component,
then run one bounded original-Wout software positive control: 60 s driver, 75 s
external process-group supervision, one thread, 256 MiB output and 3/2 GiB initial/
live disk reserves. Bind the original Wout hash and compare returned reference
arrays to the public starter and original B² scale. Record both clocks, source/
input hashes before/after, environment, all six field checks and failures; clock
disagreement above 5 s is incomplete. No solves, new targets or fits occur here.

A supplied hash proves byte identity, **not solver provenance**. The future trusted
runner must bind each exact input to a successful budgeted solve, its executable/
dependency state and resulting Wout; that integration remains unimplemented.
This component explicitly reports solver provenance unverified, joint execution
disabled and physical admission false. Passing field representations does not
prove global nestedness, stability, physical feasibility or a common action
endpoint. The full protocol remains disabled until its separate prerequisites
and frozen driver implementation are reviewed.
