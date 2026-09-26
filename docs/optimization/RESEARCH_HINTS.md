# Research hints — invitations, not requirements

Coordinator's snapshot, 2026-09-26. Our research goal is unchanged: useful,
independently checkable improvements to stellarator plasma/coil design. These
are promising directions, not a closed list. **Unsolicited ideas and results are
welcome. Compute cost disclosure is optional.** A contribution need not produce
a best score: a reproducible counterexample or a better test can be valuable.

Start with the [public quickstart](../validation/PUBLIC_QUICKSTART.md) and
[contribution guide](../../CONTRIBUTING.md). Full scientific context:
[status](../STATUS.md) and [roadmap](../PROJECT_PLAN.md).

## Accessible starting points

| Direction | Why it is useful | A reviewable contribution could be |
| --- | --- | --- |
| Reproduce the public starter on another system | Distinguish portability from success on the maintainer's machine | Exact revision, observed commands/results and limitations; no paid resources required |
| Faster or independently implemented filament fields | Repeated magnetic-field evaluations are a practical bottleneck | A kernel preserving units, signs and named mapping, with analytic/native comparisons; speed claims need timing evidence |
| Find failures of the sparse sample | Low sample error can hide bad full-surface fields | A concrete counterexample and a proposed stronger independent test; do not call the counterexample a better reactor |
| Make contribution/reproduction easier | Contributors should not need our chat history | Clearer docs, tests, diagnostics or a demonstrably portable data adapter |

## Deeper research directions

- **Calibrate and map the bottleneck first.** Reproduce matched author coil/surface
  cases and map our metric conventions; explore attainable field/geometry trade-offs.
  The [current programme](STEP4_RESEARCH_PROGRAMME.md) sets time boxes and offers
  four issue-ready tasks toward a portable full-grid challenge. That challenge is
  not implemented by the present sparse starter.
- **Geometry-preserving coil improvement.** The existing clear starts satisfy
  geometry limits but have large magnetic errors. Explore useful shape directions,
  tighter justified continuous bounds, or different parameterizations. The
  [eight-case protected fit](PROTECTED_COIL_FIT_RESULTS.md) makes small verified
  coarse reductions, but all searches stop at the cumulative curvature bound.
  Its [fine phase](PROTECTED_FINE_RESULTS.md) is complete and retains all field
  failures. A tighter curvature bound and [fixed field comparison](FIXED_FIELD_PROBE_RESULTS.md)
  establish small useful steps, not reachability. Alternative directions remain
  interesting; preserve the original
  seed/path guarantee and physical limits. This is not a new feasible baseline
  or the only permitted approach.
- **Portable full-physics evaluation.** Replace local-only data access with
  source-bound portable equilibrium/field packages and replay the original gates.
  Do not rewrite historical paths/hashes or drop difficult resolution levels.
- **Actual-coil QI transfer.** Determine whether favorable plasma-target metrics
  survive in the realized magnetic field, including topology and independent
  numerical checks. A normal-field fit alone does not answer this.
- **Pressure, finite coils and robustness.** Improve qualified model interfaces
  and assumptions for finite-pressure response, winding geometry, perturbations
  and loads. Clearly separate toy controls from validated physical predictions.
- **A different promising idea.** Explain the connection to the project, what
  evidence exists, and how it might be checked. We will assess it even if it
  does not fit this list or the starter's six-coil candidate format.

## What not to optimize away

Do not lower an error by reducing field strength without preserving the relevant
physical normalization, dropping difficult cases, loosening acceptance thresholds,
or changing the verifier alongside a candidate. For this public starter the current
is frozen and there is no physical admission at all. For broader studies the
original flux, resolution and geometry requirements remain part of the comparison.
Exploratory results should be labelled exploratory; useful failures are welcome.
