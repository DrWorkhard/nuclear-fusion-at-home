# Registered joint-target numerical intake

Implemented and checked on 7 October 2026. The decision is whether the
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

At clean producer/evaluator `e0e3104ac954e5ca45e1a13516b802f3bf595d40`,
337 research tests (45 focused) and 61 public tests, docs, Ruff and diff pass.
A reviewed original-Wout software control reproduces the public starter's 64
interior points/fields and original B² exactly. All six field checks pass;
maximum positive representation discrepancy is 5.064e-7, independent geometry
2.053e-15. Out-of-range interior harmonics are rejected before sampling.
Driver 2.064 s, supervision 2.206 s within 60/75 s caps; one thread, 256 MiB,
3/2 GiB disk reserves, unchanged source/input hashes and clock discrepancy below
0.001 s. No equilibrium solve, proposal Wout or coil fit was produced.

Local evidence `evidence-issue37-intake-control-v1` is prepared at archive
`488614e1a9fcf91cb710dc1e187fe852457c5a7b`, payload
`evidence/issue37-intake-control-v1`; all six raw files (23,093 bytes) are preserved.
The 13-entry manifest SHA256 is
`6b8407596f82508b55d9a7d3ea7b83270ec1b17624eb19b9e730a245f24e733d`.
The archive contains the exact control/reproduction command; the original hashed
Wout remains local-only. Synthetic tests need no historical evidence. Publication
is pending. Fresh shallow replay reproduced the intake, starter errors and B²
result exactly; all 13 manifest entries, 24 source hashes and three input bindings
verified. Agent review is not external physics review.

A supplied hash proves byte identity, **not solver provenance**. The separate
[trusted runner](ISSUE37_SOLVER_QUALIFICATION.md) now binds one registered plus
input to a successful budgeted solve, its executable/dependency state and Wout.
Bare numerical intake still reports solver provenance unverified; the runner
verifies it through its trusted parent receipt. Both leave joint execution
disabled and physical admission false. Passing field representations does not
prove global nestedness, stability, physical feasibility or a common action
endpoint. The full protocol remains disabled until its separate prerequisites
and frozen driver implementation are reviewed.
