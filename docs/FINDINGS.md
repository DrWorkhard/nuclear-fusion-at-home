# Findings log

## F-045 — Zero sampled curvature penalty hides real off-grid violations

**Class:** independent geometry rejection with position-only violating witnesses
**Date:** 2026-09-10

Both affine candidates have zero optimizer curvature penalty, with 200-point
maxima below 1/m at reactor scale. Refined maxima are 1.00355069 and 1.03114211/m.
Compiled derivative evaluation and a three-position circumcircle reconstruction
confirm both violations independently of the NumPy Fourier-derivative holdout.
The two finest position-only estimates agree within 4.36e-6 relative and remain
above the hard limit. No tolerance is relaxed. Before larger search budgets,
qualify curvature control between constraint nodes. See CURVATURE_ALIASING_RESULTS.md.

## F-044 — Fixed coordinate scaling enables an actual equal-bundle pilot

**Class:** preregistered repeated optimizer experiment, followed by failed holdout
**Date:** 2026-09-10

Using x=x0+0.01*y, both methods and both repeats consume exactly 1500 full
physical bundles. L-BFGS-B no longer returns immediately; all proposal histories,
values and counters reproduce. The physical-problem identity and ledger audit
passes. AL has lower common merit for this start, but both candidates fail flux,
length and curvature in the independent holdout. Both best proposals occur at
the budget cap: convergence and feasibility remain unproved. No multi-start
ranking or SoTA claim. See AFFINE_FEASIBILITY_RESULTS.md.

## F-043 — A second field-line calculation preserves the finite-pressure findings

**Class:** retrospective independent trace/integration-path comparison
**Date:** 2026-09-10

The hash-pinned Goodman tracer, using B/B^phi for length instead of geometric
derivatives, passes all 84 trace comparisons and 320 radial-family comparisons.
All 319 previously resolved signs survive an enlarged inter-tracer allowance;
the one unresolved family stays unresolved. This supports the bounded F-042
findings without validating the equilibrium or global maximum-J. Fresh extraction
reproduces every finite-pressure metadata/file-hash record, and all 193 unique
referenced path/hash pairs verify. See QI_PRESSURE_TRACE_RESULTS.md.

## F-042 — Individual radial actions resolve a bounded finite-pressure sign change

**Class:** preregistered four-case pilot with retrospective independent quadrature
**Date:** 2026-09-10

All 160 sampled cells match individual wells across radius and resolution; all
320 families pass the numerical refinement screens. nfp2 vacuum has 80 positive
derivatives; its nominal beta=2% counterpart has 80 negative derivatives. nfp3
at this pressure remains mixed (42 negative, 38 positive); vacuum includes one
unresolved family, retained. No alpha averaging or radial pitch retuning is used.
All 13,440 integrals and all derivative classifications survive independent
Gaussian quadrature. The result is restricted to the declared mid-radius domain,
gauge and empirical error allowance, not global maximum-J or SQuID-C readiness.
See QI_RADIAL_ACTION_RESULTS.md.

## F-041 — Finite-pressure QI data were already present but not imported

**Class:** verified archive inventory; correction of an internal data-access gap
**Date:** 2026-09-10

The existing Goodman release contains 31 finite-pressure wouts and matching
inputs. All 62 files now have recorded hashes and observed equilibrium metadata.
All wouts report normal termination, fixed boundary and stellarator symmetry.
Filename beta values are approximate labels, not exact measured beta or author
tolerances; nfp1 has ns=51, the other families ns=201. Our vacuum-only bootstrap
had omitted these files. Finite-pressure action work can proceed without a new
author package, but neither maximum-J nor SQuID-C readiness is established.
See QI_FINITE_BETA_INVENTORY.md.

## F-040 — Continuous inter-coil distance is bounded, but feasibility is still failed

**Class:** retrospective analytical bound supplementing a finite-grid audit
**Date:** 2026-09-10

After three analytical bound test groups, the existing all-pair N=20,000 samples
and Fourier derivative bounds imply continuous reactor-scale centerline lower
bounds of 1.09245264 m (L-BFGS-B) and 1.06131415 m (AL), both above 1.06 m.
This addresses subgrid inter-coil distances for these two exact Fourier systems
in ordinary floating-point arithmetic. Idealized radius-0.035355 m neighborhoods
of distinct device-scale coils have lower gaps 0.03745/0.03437 m. Existing mesh
enclosure, single-coil self-intersection and plasma/structural validity are not
certified. The failed flux and length checks remain unchanged.

The original rejected warm start is now a tracked fixture. Its numeric content
is unchanged (only a final LF added), with exact parent-hash verification. Its
historical producer record had no project commit and a dirty tree; that provenance
gap is disclosed, not retroactively repaired. New experiments no longer depend
on a private ignored artifact path for this starting field.

## F-039 — Normalization alone fails; the improved AL candidate remains infeasible

**Class:** preregistered negative experiment with independent post-search rejection
**Date:** 2026-09-10

The normalized common-vector study reproduces both methods exactly. L-BFGS-B
still terminates after one iteration: its trial merit jumps from 0.5 to 1.38e18,
then returns to the identical start. Thus small absolute scale alone does not
explain F-038. AL uses 752 bundles and yields about fivefold lower holdout flux,
but still misses the 1e-8 flux cut-in and exceeds the 220 m length bound by
0.842 mm. Both candidates are rejected without loosening criteria. No feasible
improvement or method ranking is established. See NORMALIZED_FEASIBILITY_RESULTS.md.

## F-038 — Exact optimization accounting exposes premature numerical convergence

**Class:** repeated real-coil oracle qualification and retained negative optimization result
**Date:** 2026-09-10

Both methods reproduce identical proposal histories in their two repeats. AL
hits the exact 150-bundle cap; L-BFGS-B stops after 10 total bundles (only three
inside its solver). The latter reports convergence after one iteration despite
flux about 110 times above the cut-in: the common squared-vector merit is near
6e-13. Counters, gradient mapping, cache and deterministic repeats pass; neither
method establishes physical feasibility or superiority. A preparation bug that
dropped finite-section regularizations was retained and corrected before the
successful retry. See OPTIMIZATION_ORACLE_RESULTS.md.

## F-037 — Six structured coil meshes pass intrinsic integrity screens

**Class:** preregistered mesh audit with adversarial analytical controls
**Date:** 2026-09-09

Protocol 2c75cc9 preceded implementation 9ee1796 and the six real mesh checks.
All meshes have positive nondegenerate tetrahedra, no repeated/duplicate cells,
consistent shared-face orientations and mean-ratio quality >=0.10. Each of the
four tagged coil boundaries has two triangles per boundary edge, one connected
component and Euler characteristic zero. The three test groups include an
overlapping pair of positive tetrahedra that fails orientation consistency.

This closes a bounded intrinsic-mesh check, **not** spatial nonoverlap or
engineering validity. Nonlocal intersections can pass these tests. Symmetry
copies were not remeshed, and coil/plasma clearances, winding-pack orientation,
physical supports/materials and valid mechanical predictions remain unqualified.
Evidence: mesh-integrity-2026-09-09.json. Full local suite: 78 passed; Ruff clean.

## F-036 — Wider QI coverage exposes an invalid invariant-domain sample

**Class:** preregistered negative screen with retrospective analytical diagnosis
**Date:** 2026-09-09

The expanded five-radius/nine-pitch study passes for nfp2 and nfp3. nfp1 fails
one of its 45 cells: s=0.10, q=0.01 lies below the minimum possible field and
admits no orbit. A Fourier second-derivative interpolation bound confirms this
beyond the sampled grid. The failed screen is retained, not waived. The other
134/135 cells have stable sampled actions and two poloidally closed contour
graphs. The larger action envelopes also show why numerical convergence is not
itself a confinement-quality criterion. Details: QI_COVERAGE_TOPOLOGY_RESULTS.md.

The strict QI integration command additionally passes five non-skipping data
checks after a fresh extraction in a detached clean clone. Neither result closes
the full QI, native-solver integration, engineering or SQuID-C readiness gates.

## F-035 — Independent geometric tracing agrees on the frozen QI sample

**Class:** independent reconstruction cross-check of the same equilibrium data
**Date:** 2026-09-09

Protocol 399a8fa preceded implementation fc435e3 and the 27 real-data checks.
The new Newton/geometry-based tracer agrees with the published root/magnetic
arc-length tracer for every tested pitch. Finest maximum relative action
differences are 6.2645e-6, 3.8171e-6 and 9.0674e-6, below the frozen 1e-3 limit.
All coordinate, B, cumulative-length, well-count and coverage screens pass.

This supplies an independent tracing check for F-034's bounded measurement
study. It does not validate the source equilibrium, QI contour topology or
finite-pressure maximum-J. See QI_TRACE_CROSSCHECK_RESULTS.md.

## F-034 — Well-resolved bounce-action measurement passes its first frozen study

**Class:** reproduced numerical qualification with independent quadrature
**Date:** 2026-09-09

Protocol 75c0ba8 preceded implementation 372a63f and all real-data runs. The
nfp=1,2,3 cases pass the specified phi/alpha/domain-length refinements and
complete-well coverage screens. The largest final phi action change is 1.0836e-4
relative, below the fixed 1e-3 limit. Independent quadrature verifies 12,960
recorded well integrals with maximum relative discrepancy below 5.5e-10.

This qualifies a bounded measurement study, not QI topology or maximum-J.
Definitions, analytic checks, results and open limitations are in
QI_MEASUREMENT_RESULTS_V1.md. The full scientific qualification remains open.

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
must not be called a complete independent validation. This initial comparison is
superseded, but not erased, by the version-compatible investigation in F-031.

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

## F-025 — The W7-X-target coil field has a deterministic Poincare regression

**Class:** reproduced and cross-fidelity checked
**Date:** 2026-08-30

Six field lines from the serialized order-8 W7-X-target coil solution were traced
to four sections per field period for `tmax=2000`. Two interpolated-field repeats
and two direct Biot-Savart repeats are internally bit-identical. Every line remains
inside the boundary stopping surface and supplies at least 130 hits per section.
Interpolated and direct paths give identical hit counts; their section-extrema
differ by at most 4.72 mm, on the outermost sampled line. The inexpensive
interpolant takes 0.26 s after setup versus 80.6 s for direct tracing.

**Implication:** coil-field topology now has a numerical regression in addition
to a plot, with a direct-field holdout. It validates the serialized optimized
filament field and software path, not the authoritative as-built W7-X coils, and
the diagnostic section-angle iota fit is not promoted to an equilibrium metric.

## F-026 — The stock finite-build fallback fails on a real LPQA candidate

**Class:** reproduced failure plus independent geometric holdout
**Date:** 2026-08-31

StellCoilBench's Gmsh fallback passed its selected upstream unit tests but could
not mesh any of the four unique coils of the serialized LPQA engineering
candidate at `h=0.05 m`. The OCC route reported intersecting/overlapping facets,
and the STL route reported an invalid exterior boundary. Source inspection shows
that its nominally rotation-minimizing cross-section frame is actually
reconstructed from a fixed z reference at every point and can be discontinuous
near reference-axis alignment.

An independent periodic parallel-transport sweep produced six mesh levels from
`h=0.05 m` to `0.01 m`, preserving four nonempty physical tags with no zero or
nonfinite tetrahedron volumes. At the finest level the total volume differs from
centerline length times area by `0.0290%`; the two finest volumes differ by
`0.00990%`.

**Implication:** the explicit structured representation passes the frozen
finite-build screen, while the pinned upstream Gmsh path is not qualified for
real optimization outputs. Synthetic meshing tests alone would have produced a
false sense of readiness.

## F-027 — Structural convergence exposes an invalid physical regime

**Class:** predeclared failed test followed by predeclared diagnostic extension
**Date:** 2026-08-31

The frozen `0.03 -> 0.02 m` P1 scikit-fem comparison failed all four 10%
convergence limits: maximum/mean displacement changed by `22.8%/24.9%`, and
p95/mean Von Mises stress by `14.6%/14.7%`. The subsequently declared
`0.015 -> 0.010 m` extension passed at `8.75%`, `9.03%`, `4.41%`, and `4.08%`,
respectively. Repeating the finest solve produced bit-identical acceptance
metrics.

The converged trend is not an absolute engineering prediction. The scikit-fem
backend fixes the lowest 15% of each coil in z even when the upstream driver
labels the configuration as a spring foundation. More decisively, it predicts
`0.978 m` maximum displacement for a `0.05 m` winding-pack width, far outside
the small-deformation regime of linear elasticity. Maximum element stress also
continues upward to `22.3 GPa` and is excluded from the convergence gate.

**Implication:** the load-to-FEM pipeline is deterministic and has an extended
mesh-convergence record, but its absolute displacement/stress values must not be
optimized or cited as reactor limits. Near-term engineering optimization should
use electromagnetic force/load proxies while a geometrically nonlinear,
support-aware, independently cross-checked structural model is developed.

## F-028 — The first immutable free-boundary holdout passes in vacuum

**Class:** predeclared pipeline qualification with response-grid holdout
**Date:** 2026-08-31

The serialized LPQA v1.1 L-BFGS-B coils were exported as one current circuit and
evaluated by VMEC++ 0.7.3 without optimizer writeback. The toroidal flux was
independently obtained from the Biot-Savart vector-potential line integral. Both
the `mpol=6`, `ntor=6`, `ns=31` fixed-boundary reference and the free-boundary
vacuum equilibrium reached the requested `1e-9` force-residual tolerance.

On the standard `101 x 101 x 24` response grid, the free-boundary volume differs
from the truncated target by `0.0266%`, the magnetic-axis R curve differs from
the fixed reference by `0.0383%` RMS, and boundary cross-section RMS distances
at the two frozen toroidal sections are `1.04%` and `0.686%` of the target
minor-radius proxies. Every predeclared screen passes.

Refining the response grid to `151 x 151 x 24` changes volume, aspect, axis iota,
and edge iota by `0.00735%`, `0.00290%`, `0.0956%`, and `0.00961%`. The normalized
cross-section errors change by `0.000411` and `0.000386`, also within the frozen
limits.

**Implication:** free-boundary validation is now operational and strictly
separate from optimization. This is not an improvement claim: the input
candidate still fails the magnetic squared-flux cut-in, and this first run is
vacuum-only at reduced Fourier/radial resolution. A publishable candidate must
repeat the holdout at converged VMEC resolution and finite pressure/current,
including topology and an independent code/version check.

## F-029 — Equilibrium intake no longer requires case-specific code

**Class:** tested generic interface plus real-data transfer control
**Date:** 2026-08-31

A core manifest-to-NetCDF adapter now validates hashes and conventions, extracts
VMEC geometry/physics metadata, checks declared versus actual
`nfp/mpol/ntor/ns/free_boundary`, and optionally summarizes a Boozer transform.
It contains no `case_id`, Goodman, or field-period dispatch. A synthetic unknown
configuration test passes in core CI. The same CLI then ingested the published
Goodman nfp=1 and nfp=2 equilibria from two data-only manifests; all declared
metadata matched in both cases.

**Implication:** a SQuID-C equilibrium/Boozer pair can enter the validation stack
by adding files and a manifest, without changing Python code. Paper-specific
metric reproduction can still require a versioned adapter when the publication
defines a unique objective; that is kept separate from generic intake.

## F-030 — No publicly identified authoritative SQuID-C package was located

**Class:** reproducible bounded primary-source availability audit
**Date:** 2026-08-31

The publisher page exposes an empty `supplementaryMaterials` list, and Crossref
records no DOI relations. Exact Zenodo searches by configuration name, article
DOI, and title returned zero records; DataCite searches by related DOI and title
also returned zero. All 4,035 paths in all nine public Proxima Fusion GitHub
repositories were checked from complete recursive trees without a SQuID-C name
match.

Proxima's four public Hugging Face datasets required an additional check because
ConStellaration and CoilStellaration are directly relevant. All 7,668 repository
paths were checked at recorded revisions without a name match. CoilStellaration's
179-column results schema links to a ConStellaration boundary only by an opaque
ID and exposes no human paper, DOI, citation, or source column. Its multi-gigabyte
row payloads were not exhaustively searched, so an anonymous row cannot be ruled
out—but it also could not serve as an authoritative SQuID-C baseline without a
publisher/author mapping.

**Verification:** `scripts/audit_squid_c_availability.py` reruns the APIs and
publisher metadata checks. The dated evidence records endpoint-response hashes,
repository/dataset revisions, pagination coverage, search limitations, and the
six still-missing artifact classes.

**Implication:** the external SQuID-C intake blocker is now documented rather
than inferred from a general web search. We should request the fixed- and
free-boundary VMEC cases, profiles, coil/current data, MGRID recipe, scale, and
paper run settings from the authors; figures or anonymous dataset rows are not
acceptable substitutes. This does not close the separate internal W7-X V&V and
CI gates.

## F-031 — A matched VMEC 8.52 reference closes the scoped W7-X physics gate

**Audit correction, 2026-09-09:** the real-space tolerance class below was wrong;
the corrected fixed-boundary margin is 16.77x. The expanded local comparison is
60/63, not full-file V&V. The variable selection and grid were retrospective.
See AUDIT_2026-09-09.md and the new dated evidence. Historical text follows.

**Class:** independent implementation reproduction with retained negative controls
**Date:** 2026-08-31

A native STELLOPT `v251`/VMEC 8.52 executable was built from pinned source with
the two patches specified by Proxima's validation repository and one documented
GNU Fortran 16 compatibility change. It completed the exact StellCoilBench W7-X
input normally in 2,922.57 seconds. VMEC++ and VMEC 8.52 both took 3,708 final
iterations and reached the requested `1e-12` force-residual level. Aspect, volume,
beta, iota, magnetic axis, Fourier geometry, and protected magnetic coefficients
pass the pinned comparison tolerances.

Independent real-space reconstruction on the `73 x 72` holdout grid has maximum
normalized differences `3.85e-10` and `1.93e-9` for R and Z, and between
`6.55e-10` and `5.96e-9` for the three cylindrical B components. All are more
than 8,000 times inside the upstream W7-X-class tolerances.

The result is not a full-file pass: 56/59 fields pass. `chipf` differs only at
the axis because the current VMEC++ assembly leaves that element zero; its
interior maximum normalized difference is `2.28e-9`, within the `1e-8`
fixed-boundary tolerance. `presf` and `pres` differ by less than `7.5e-6 Pa`
absolute and `2.7e-11` relative to their L-infinity scale, but still miss the
upstream bit-near array tolerances. No exception is deleted from the evidence.

The older VMEC 9.0 comparison's broad `bsubsmns` failure disappears: the matched
8.52 maximum absolute coefficient difference is `2.10e-8`. This identifies
version/output semantics—not a discrepant reconstructed physical B field—as the
cause of the prior alarming result.

**Implication:** WP2's declared physics regression gate is closed without claiming
full `wout` equivalence. The remaining three output-level warnings should be
reported upstream and retained as regression tests, but they do not block
SQuID-C equilibrium intake.

## F-032 — The first SQuID-C template was structurally under-specified

**Audit correction, 2026-09-09:** the implication that no adapter changes remain
is withdrawn. Empty metrics and failed solver outputs could pass; scientific
admission was not implemented. The revised code and readiness gates distinguish
basic intake from scientific reproduction. Historical text follows.

**Class:** failed contract audit followed by tested schema hardening
**Date:** 2026-08-31

The schema-1 template listed the expected artifacts, but the executable validator
would have admitted `kind=squid_c` with only one VMEC input or output. It did not
require separate fixed- and free-boundary states, MGRID construction, solver
controls, physical scale, symmetry expansion, file sizes, authoritative origin,
or derivation lineage. Thus the prose contract was stronger than the code.

Schema 2 now makes all ten artifact roles mandatory, rejects duplicate roles and
template placeholders, verifies byte sizes and SHA-256 hashes, distinguishes
authoritative files from locally derived files, validates every declared parent
role, and binds both equilibria to code/version/resolution/convergence metadata.
A complete synthetic SQuID-C package passes the contract and both equilibrium
states enter the generic intake. Missing MGRID, wrong byte size, and an undeclared
lineage parent each fail dedicated tests. The core suite now has 13 passing tests.

The paper-level values were rechecked against the publisher text: the coil design
targets 2% volume-averaged beta including the plasma-current background; the
canonical reported state uses `p(s) proportional to 1-s` and includes coil ripple;
and the reported mean/maximum relative field errors are 0.27%/1.2%.

**Implication:** once an authoritative package is supplied, no schema or intake
code change is needed. G6's raw/derived hashes remain correctly open because
inventing them from the publication would defeat the contract.

## F-033 — The first green core-CI run depended on an ignored checkout

**Audit correction, 2026-09-09:** the main-branch clone passed, but a detached
checkout failed because a test assumed branch=main. That test is corrected,
detached HEAD is tested explicitly, and the workflow now pins uv 0.11.2.

**Class:** failed clean-room holdout followed by reproduced remediation
**Date:** 2026-08-31

The locked CI command initially passed in the working repository but failed in a
fresh clone before collecting tests. Although the benchmark extra was not
selected, lock validation still attempted to read the optional editable source
at `external/stellcoilbench`; that ignored checkout existed only in the working
repository. `--no-install-local` did not help because metadata were required
before installation selection.

The optional source is now the exact StellCoilBench Git commit
`c7949edc4ea6378fc3be633304c69c288c3b79b5` rather than a local path. The separate
checkout at the same commit remains the pinned source/data audit tree. A second
fresh clone—with neither `external/` nor an existing virtual environment—resolved
the lock, installed the core package, passed Ruff and all 13 tests, and left the
clone clean.

**Implication:** the core workflow is clean-checkout reproducible. A hosted run is
still unwitnessed because no remote is configured, but that is now an operational
publication step rather than a hidden dependency in the scientific intake path.
