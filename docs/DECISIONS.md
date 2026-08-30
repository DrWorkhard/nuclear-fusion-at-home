# Decision log

## D-001 — Use a baseline suite, not a single substitute for SQuID-C

**Status:** accepted
**Date:** 2026-08-30

W7-X is the physics/software regression, StellCoilBench is the method benchmark,
and an open QI equilibrium is the data-interface and QI-physics bridge. None is
misrepresented as SQuID-C or Stellaris.

## D-002 — Keep optimization method-neutral

**Status:** accepted
**Date:** 2026-08-30

AI is not an objective or privileged baseline. Methods are compared under equal
budgets, constraints, and independent evaluation. Surrogates and active learning
are introduced only after a strong classical baseline exists and only retained if
they show measured benefit.

## D-003 — Target a robust physics-engineering Pareto frontier

**Status:** accepted
**Date:** 2026-08-30

The intended contribution extends beyond filament-coil normal-field error. Finite
build, electromagnetic loading, stress/deformation, clearances, manufacturing
errors, and free-boundary plasma response are part of the target validation stack.

## D-004 — Use all three published Goodman QI vacuum cases

**Status:** accepted
**Date:** 2026-08-30

The one-field-period case is the primary open-QI regression because the source
paper reports that the method works especially well there. The two- and
three-field-period cases are mandatory transfer controls: they reduce the risk of
building a metric or optimizer that works only for the favourable nfp=1 class.

## D-005 — Do not equate local VMEC convergence with cross-code validation

**Status:** accepted
**Date:** 2026-08-30

A VMEC++ run is accepted as locally converged when its force residuals meet the
input tolerance. Cross-validation is reported separately against the supplied
Fortran wout and the pinned Proxima validation tolerances. A subset of matching
global quantities cannot be relabelled as a full validation pass.

## D-006 — Separate legacy QI reproduction from the optimization metric

**Status:** accepted
**Date:** 2026-08-30

The exact published QI residual remains a required regression, but its
non-monotone resolution study disqualifies it as the sole objective for new
designs. A replacement must have a predeclared mathematical definition,
resolution convergence, transfer across all three QI cases, and agreement with
independent trapped-particle or second-invariant diagnostics.

## D-007 — Certify feasibility from outputs, not optimizer status

**Status:** accepted
**Date:** 2026-08-30

An optimizer success flag is diagnostic only. Feasibility is recomputed from the
serialized candidate using predeclared thresholds and the independent
high-resolution holdout. A candidate that is within the optimization grid's
tolerance but crosses a refined clearance or curvature bound is infeasible.
