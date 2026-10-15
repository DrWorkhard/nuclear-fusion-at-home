# Plasma requirements: unapproved v1 proposal

The [machine-readable proposal](plasma-requirements-v1.proposal.json) transcribes
[#113](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/113) for owner
review. **It is not frozen, approved or usable for optimization.** No runtime
consumer is added. Existing coil acceptance, target identities and recorded
Step 3 outcomes retain their meaning.

## What the proposal fixes, and what it leaves open

The JSON is the single home for proposed numeric values and roles. It separates
five hard bounds from mirror/elongation preferences, flux-compression and
L-gradient-B objectives, and the Step 3 bounce diagnostic. Values follow the
issue's draft table; they have not been tuned after calibration. The geometric
problem's compactness choices are explicitly excluded.

All five hard-bound quantities are dimensionless. `qi` is the upstream raw sum
of squared residuals; its proposed comparison uses log10. The transform metric
uses absolute value, matching the benchmark; realized-field tracing still needs
its existing signed-iota agreement. Exact inclusive comparisons, missingness and
zero-QI behavior are proposed explicitly for owner review. The benchmark's 1%
feasibility allowance is not silently added to the numeric bounds.

The issue leaves decisions that this draft does not invent:

- “Aspect ratio near 10” has no frozen interval. The calibration slice 9–11 is
  an analysis population, not a design gate.
- “Bounce action no worse than selected401” is called an objective, but could
  also mean a non-regression constraint. Its role, tolerance, executable
  diagnostic, domains, units and hash-bound wide/narrow reference values must be
  fixed before use. No archived scalar is silently reused under a new evaluator.
- The qualified scorer/settings/resolution and comparison policy remain
  unspecified. Historical pipeline flags may be inapplicable; unknown flags
  alone do not demonstrate solver failure. Objective weights and search selection
  belong to a later preregistered experiment, before optimization; they are not
  additional plasma-quality bounds.

## Before the owner freezes v1

Review [calibration PR #119](https://github.com/DrWorkhard/nuclear-fusion-at-home/pull/119)
and qualify the scorer through [#112](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/112).
The stored-label calibration flags QI and joint attainability; it does not prove
physical infeasibility or authorize changing a bound. Choose or amend the draft
values openly, resolve the JSON's freeze items, and record explicit owner
approval with the scorer/input identities in a frozen `plasma-requirements-v1`
JSON and this page. This proposal remains visibly unapproved until then.

No optimization may treat this file as an adopted gate. After approval/freezing,
changes require a new requirements version; earlier studies are re-scored on a
scorecard, not retroactively re-graded. These vacuum, ideal-MHD and geometry
proxies do not establish finite-pressure stability, transport, confinement or
reactor acceptance. Those qualifications remain future work.
