# Findings log

## F-001 — Host platform is resource-capable but compatibility-sensitive

**Class:** reproduced
**Date:** 2026-08-30

The host is an Apple M1 (`arm64`) with 8 logical CPUs, 16 GiB RAM, macOS 15.7.4,
Python 3.11.4, `uv`, and CMake. Docker, Conda, MPI, and Git LFS were not found on
`PATH` during the initial probe.

**Implication:** native ARM compatibility must be tested before choosing the
canonical environment. Linux/x86 containers or remote HPC may eventually be
needed for selected solvers, but this is not assumed in advance.

## F-002 — StellCoilBench does not currently supply a SQuID-C/QI target surface

**Class:** literature/repository inspection
**Date:** 2026-08-30

The public `plasma_surfaces` directory currently lists NCSX, HSX, Landreman-Paul
QA/QH, W7-X, CFQS, a circular tokamak, a rotating ellipse, MUSE, and another NFP=2
surface. No SQuID-C surface is listed.

Source: <https://github.com/akaptano/stellcoilbench/tree/main/plasma_surfaces>

## F-003 — A publication alone is not yet an authoritative SQuID-C data package

**Class:** literature/repository inspection
**Date:** 2026-08-30

The open SQuID-C paper describes a coil-compatible finite-beta QI equilibrium and
reports central physics and coil metrics, but no linked machine-readable package
containing the complete VMEC input/output, profiles, coils, currents, and run
configuration was identified during the initial search.

Source: <https://doi.org/10.1017/S0022377825100974>

**Implication:** do not reconstruct SQuID-C from figures. Request or locate the
authoritative files while developing against the three-part baseline suite.

## F-004 — SIMSOPT is native on Apple ARM after an SDK include-path correction

**Class:** reproduced
**Date:** 2026-08-30

The pinned SIMSOPT commit `a79006b0bc1e6df8ab48de284e3457d39a49b995`
compiled for `macOS arm64`. The first build failed because an incomplete libc++
header directory in the Command Line Tools shadowed the complete headers in the
active SDK (`cstddef`, `iostream`, and `algorithm` were not found). Prepending
`$(xcrun --show-sdk-path)/usr/include/c++/v1` fixed the build without modifying
SIMSOPT.

**Verification:** 31 upstream Biot-Savart/curve-objective tests and 86 subtests
passed. These include Taylor tests, derivative identities, convergence, symmetry,
and divergence-free checks.

## F-005 — MPI is an import-time dependency of the current benchmark stack

**Class:** reproduced
**Date:** 2026-08-30

Installing `mpi4py` alone was insufficient: importing `simsopt.field` failed
because no `libmpi` was available. Installing OpenMPI 5.0.10 resolved the failure,
after which serial Biot-Savart evaluation and both StellCoilBench case validators
ran successfully.

**Implication:** OpenMPI is part of the canonical environment even for one-process
coil optimization.

## F-006 — The basic Landreman-Paul QA result is deterministic but not Pareto-strong

**Class:** reproduced and cross-checked
**Date:** 2026-08-30

Two independent invocations of the pinned `basic_LandremanPaulQA.yaml` case gave
bit-identical reported scientific metrics and 2,512 function/gradient evaluations.
Wall time changed from 160.55 s to 158.60 s. Principal results were:

- final squared flux: `1.1470641716587582e-06`;
- average `|B·n|/|B|`: `4.420509357430533e-04`;
- reactor-scale coil-surface and coil-coil separations: 2.855 m and 1.060 m;
- reactor-scale total coil length: 242.400 m;
- maximum turns per coil: 488.

StellCoilBench's hard feasibility check passes. Its soft length bound (220 m) and
turn-count bound (300) fail. The separate post-processing path obtained
`4.470778891115039e-04` for average `|B·n|/|B|`, a 1.14% relative difference from
the optimizer report. The composite score is 1.5926, below 2,365 of 4,684 scored
Landreman-Paul QA entries in the pinned leaderboard.

**Implication:** driving filamentary flux error lower is not the promising
research direction by itself. A relevant contribution must move the engineering
Pareto frontier, especially length/current/turns/force/finite-build trade-offs.

## F-007 — `run-case` does not create a self-contained post-processing bundle

**Class:** reproduced
**Date:** 2026-08-30

The upstream `run-case` optimization succeeded, but its automatic post-processing
could not locate a case YAML beside the generated coil JSON. Our wrapper now
copies the exact case and target surface into each run directory and hashes both.
With that bundle, the same post-processing completed.

## F-008 — The W7-X coil baseline is feasible but stops on engineering margins

**Class:** reproduced
**Date:** 2026-08-30

The pinned `basic_W7X.yaml` continuation reached Fourier order 8 and stopped at
the 1,000-iteration limit. Its average normal-field error is 0.297 %, while an
independent post-processing pass gives 0.301 %. Hard feasibility passes, but the
reactor-scale coil-surface clearance (1.115 m), maximum curvature (1.0001 1/m),
arclength-uniformity metric, and 516-turn maximum violate soft targets. The
reactor-scale total coil length is 145.90 m.

**Implication:** normal-field error alone again does not identify the strongest
design. Current/turn count, finite-build clearance, curvature and force belong in
the primary Pareto comparison.

## F-009 — W7-X VMEC++ is locally converged, but full cross-code V&V is not

**Class:** reproduced with partial cross-validation
**Date:** 2026-08-30

VMEC++ 0.7.3 converged on the exact StellCoilBench W7-X input at `ns=201` in
264.3 s. Aspect ratio, volume, total beta and the iota profile agree with the
available Fortran reference to absolute differences of approximately
`2.6e-13`, `1.5e-13`, `5.3e-13`, and `1.4e-8`, respectively. However, only 47 of
59 fields pass the current pinned Proxima fixed-boundary V&V tolerances. The
failures include several half-grid and axis-derived quantities.

**Implication:** the equilibrium is a useful protected-metric regression, but it
must not be called a complete independent validation. The W7-X gate remains open.

## F-010 — The open QI bridge has authoritative inputs, outputs and metric code

**Class:** reproduced provenance
**Date:** 2026-08-30

Zenodo record 7220257 contains the three vacuum `nfp=1,2,3` VMEC inputs and
outputs, edge Boozer transforms, source metric routines, finite-beta scans, and
published neoclassical/particle outputs. The 1,057,077,931-byte archive passed
both its published MD5 (`f6983a41403da28247025be631522caa`) and a full ZIP CRC
test. Only the required 16 MB subset is extracted.

Source: <https://doi.org/10.5281/zenodo.7220257>

## F-011 — The published QI target is reproducible but numerically fragile

**Class:** reproduced
**Date:** 2026-08-30

Executing the unmodified published `QuasiIsodynamicResidual1` against the
published edge Boozer transforms gives objective values `2.5725e-5`, `2.7451e-5`
and `7.0527e-5` for `nfp=1,2,3`. All are finite. SciPy nevertheless warns that the
smoothing spline used in the inverse-square well weighting does not always reach
its requested smoothing residual.

**Implication:** preserve this objective as a legacy regression, while developing
a numerically regularized and resolution-tested QI metric before using it to
rank new designs.

## F-012 — Vacuum QI is not the same as maximum-J

**Class:** reproduced and literature-consistent
**Date:** 2026-08-30

The published second-adiabatic-invariant routine gives maximum-J slope fractions
of 0.0, 0.0 and 0.1 for the three vacuum cases at the recorded screening
resolution. This agrees with the paper's statement that known vacuum cases are
minimum-J and that these configurations become maximum-J only at sufficient
finite beta.

Source: <https://arxiv.org/abs/2211.09829>

**Implication:** a vacuum QI objective cannot stand in for the finite-beta
maximum-J and turbulence physics relevant to SQuID-C.

## F-013 — SQuID-C's published coil design leaves a credible hard-constraint gap

**Class:** literature and inferred research direction
**Date:** 2026-08-30

The SQuID-C paper reports average and maximum relative normal-field errors of
0.27 % and 1.2 %, five modular coil types, and normalized per-type geometry in its
Table 1. It also states that coil optimization began with field error, added
geometric penalties as the solution matured, and enforced no firm constraints.
The authors explicitly flag coil complexity and improved magnetic-gradient scale
length as future concerns.

Source: <https://doi.org/10.1017/S0022377825100974>

**Implication (hypothesis):** the most promising first contribution is a robust,
hard-constrained coil Pareto improvement—finite build, current/turns, clearance,
curvature and loading—while protecting the coil-generated finite-beta QI physics.
This is testable on W7-X and the open QI suite before authoritative SQuID-C files
arrive.

## F-014 — The default coil grid is not a safe geometry holdout

**Class:** reproduced and independently calculated
**Date:** 2026-08-30

Direct Fourier differentiation of the accepted W7-X coils reproduces the reported
lengths to floating-point precision. Increasing the sampling from 200 to 20,000
points changes maximum curvature from `3.24412` to `3.26161 1/m`, a 0.54 %
underestimate at benchmark resolution. The sampled minimum coil-coil distance
decreases from `0.239019` to `0.237633 m`, so the coarse metric overestimates
clearance by 0.58 %. The sampled coil-surface distance similarly decreases from
`0.343595 m` in the optimizer report to approximately `0.342193 m` in the
independent high-resolution audit.

**Implication:** optimization-resolution clearance and curvature cannot certify a
new result. A frozen high-resolution geometry audit is now a mandatory holdout and
may itself change leaderboard ordering near constraints.

## F-015 — The legacy QI objective is not resolution-converged

**Class:** reproduced negative result
**Date:** 2026-08-30

For the published `nfp=1` case, simultaneous refinement from
`(nphi,nalpha,nBj,nphiout)=(301,37,201,1000)` through the published default to
`(801,100,601,3000)` gives objective values `1.3850e-5`, `2.5725e-5`, and
`1.8097e-5`. The sequence is strongly non-monotone and the spline warnings remain.

**Implication:** exact reproduction is useful as a software regression, but this
objective is not admissible as the sole ranking function for new QI designs. A
regularized definition needs independent convergence and physics checks first.

## F-016 — Published transport-screening data pass the generic intake path

**Class:** reproduced data ingestion, not solver reproduction
**Date:** 2026-08-30

The published NEO outputs give median epsilon-effective to the three-halves power
of `6.54e-6`, `1.20e-5`, and `7.83e-6` for `nfp=1,2,3`. The corresponding
published SIMPLE 5,000-particle files give final 0.2 s loss fractions of
approximately 0, 0.36%, and 0.38%. These values were recomputed from the raw text
outputs with the same transformations used by the published plotting script.

**Implication:** the file interfaces and summarization semantics are established.
NEO and SIMPLE themselves have not yet been installed and rerun, so this is not
an independent transport validation.

## F-017 — VMEC++ convergence is stable but not bit-deterministic on this host

**Class:** reproduced
**Date:** 2026-08-30

Two runs of the identical Goodman `nfp=2` input both converged below the force
residual target. Aspect ratio and volume were identical, while axis iota differed
by `2.70e-8`, edge iota by `3.71e-10`, and iteration counts were 5,605 versus
5,677. The serialized NetCDF hashes differ.

**Implication:** equilibrium regressions use declared physical tolerances, not
file-hash identity. Hashes remain provenance identifiers only.

## F-018 — LPQA geometry is even more sensitive to coarse clearance sampling

**Class:** reproduced and independently calculated
**Date:** 2026-08-30

For the accepted LPQA baseline, the 200-point coil-coil distance is `0.104995 m`;
global candidate search at 1,000 points followed by 20,000-point refinement gives
`0.103528 m`, 1.40% lower. The optimizer-reported coil-surface distance is
`0.282696 m`, versus `0.281607 m` on the 512-by-512 surface holdout. Maximum
curvature changes only from `4.72380` to `4.72639 1/m`.

**Implication:** the clearance bias is not W7-X-specific and can cross a hard
constraint. High-resolution reevaluation must happen outside the optimizer.

## F-019 — Stock augmented-Lagrangian evaluation accounting is not comparable

**Class:** source inspection, pending run characterization
**Date:** 2026-08-30

In the pinned stack, StellCoilBench passes `max_iterations` to SIMSOPT as the
inner SciPy `MAXITER` and `max_iter_subopt` as the outer `MAXITER_lag`, despite
the wrapper documentation describing the reverse. It then records
`optimization_nfev = max_iterations` without using the inner solvers' actual
`nfev`. Taylor-test and between-step evaluations are also omitted.

**Implication:** published stock fields cannot support an equal-evaluation-budget
claim for L-BFGS-B versus augmented Lagrangian. Our runner now records actual
inner SciPy counters and labels their exclusions; a globally budget-stopping
counter is required before the headline comparison.

## F-020 — The frozen manufacturing screen separates nominal accuracy and tolerance

**Class:** reproduced screening result
**Date:** 2026-08-30

With a 1 m reactor-scale GP correlation length, 100 common-random-number samples
per amplitude, and the 95th-percentile factor-two rule, both baseline intervals
are validly bracketed. LPQA gives `sigma*=9.066 mm`; W7-X gives `20.372 mm`.
Lower and upper endpoint percentile ratios are `1.002/29.02` and `1.000/6.85`,
respectively. The effective optimization flux threshold `1e-8` is read from each
immutable result record after discovering that the upstream sensitivity YAML
lookup silently selected zero.

**Implication:** nominal field accuracy and tolerance sensitivity are distinct
axes: the much lower-error LPQA result has the smaller factor-two tolerance. The
cross-case ratio is not itself a superiority claim because the degradation is
normalized by different nominal errors and the configurations have different
numbers of physical coil copies. Within-case robust Pareto comparisons are now
well-defined; accepted claims require the 1,000-sample holdout.

## F-021 — The open QI case runs through a real fast-particle solver

**Class:** reproduced smoke-scale solver execution
**Date:** 2026-08-30

Pinned SIMPLE commit `9269e861...` with pinned libneo builds deterministically on
Apple ARM after explicit Homebrew OpenMP and NetCDF paths. Seven upstream smoke
tests pass. Two runs using the exact Goodman `nfp=1` vacuum wout, scaled to
effective minor radius 1.7 m and axis field 5.7 T, produced bit-identical
`confined_fraction.dat`. All 128 isotropic alpha particles initialized at
`s=0.25` were resolved and none was lost by 0.01 s.

**Implication:** the VMEC-to-SIMPLE interface and orbit solver are operational and
deterministic at smoke scale. This does not reproduce the paper's 5,000-particle,
0.2 s statistic; production protocol, current-versus-2022 code sensitivity, and
statistical uncertainty remain required.

## F-022 — No order-4 engineering screening candidate is yet feasible

**Class:** reproduced negative result
**Date:** 2026-08-30

Five LPQA screening runs were reevaluated against a common physical acceptance
set and the independent geometry holdout. None satisfies every condition. The
buffered L-BFGS-B candidate satisfies length, refined clearances, and refined
curvature, but its squared flux is `1.10e-6`, above the declared `1e-8` cut-in.
The longest augmented-Lagrangian run reduces squared flux to `3.98e-7` after
1,665 recorded inner SciPy evaluations, but exceeds 220 m length and its refined
reactor-scale maximum curvature is `1.000036 1/m`.

**Implication:** these runs characterize the constrained landscape and audit
path; none is a publishable classical baseline or an improvement. Higher Fourier
order/continuation and a genuine convergence/budget controller are still needed.

## F-023 — Optimizer completion is not a feasibility certificate

**Class:** source inspection and reproduced counterexample
**Date:** 2026-08-30

The three augmented-Lagrangian screens are labelled `optimization_success=true`
by the stock result builder because the solver result is discarded and `None` is
mapped to `Completed`. This remains true when the outer cap is reached with
nonzero violations. The stock `optimization_nfev=100` also disagrees with the
instrumented inner totals of 370, 668, and 1,665.

**Implication:** acceptance is computed from serialized-coil metrics and holdouts,
never from the wrapper's success field. Equal-budget method claims remain blocked
until all high-fidelity evaluations are counted and a global stop is enforced.

## F-024 — The local neoclassical path works but does not reproduce the paper

**Class:** reproduced solver execution with failed cross-check
**Date:** 2026-08-30

Pinned NEO-JAX 1.0.1 and `booz_xform` 0.1.0 successfully compute finite
`epsilon_eff^(3/2)` on 16 surfaces of the published Goodman nfp=1 equilibrium,
without rational-surface fallback. A radial Boozer file had to be regenerated
because the release contains only an edge Boozer transform. At default settings,
the calculated-to-published ratio has median 3.27 and maximum relative error
797%. At the surface nearest `s=0.21875`, refinement from the low to high and
ultra settings changes the value from `1.238e-5` to `7.841e-6` and `7.773e-6`;
the published value is `2.381e-6`.

**Implication:** the local VMEC-to-Boozer-to-neoclassical interface is exercised,
but paper reproduction fails and cannot be repaired by the tested resolution
increase alone. The missing original radial Boozer file and NEO control deck are
now explicit provenance blockers; no transport-accuracy claim is made.
