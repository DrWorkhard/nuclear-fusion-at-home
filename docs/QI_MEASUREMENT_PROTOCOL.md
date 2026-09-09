# QI measurement qualification v1 — preregistered 2026-09-09

## Scope and hypothesis

First qualify a bounce-action measurement kernel before proposing a new QI
optimization objective. The reduced action is
`Jtilde(s, alpha, Bstar) = integral(l1,l2) sqrt(1-B(l)/Bstar) dl`, for each
connected trapped well bounded by B=Bstar. Units: metres; one-way bounce integral.
The common particle-dependent prefactor is omitted. At fixed Bstar, dependence
on field-line label probes omnigenity. QI additionally requires poloidally
closed |B| contours; this action diagnostic alone cannot certify QI.

Primary definition: [Goodman et al. (2023), equations 1.1–1.4 and section 1.5](https://doi.org/10.1017/S002237782300065X).
The preserved published PltElephants.py trace routine supplies B and arc length.
The new integrator is independent of its smoothed-spline J_B reduction. It must
retain individual well bounds, actions, alpha labels and incomplete-well counts.
It must never silently drop a failing field line or turn missing data into zero.

## Kernel verification before real-data evaluation

Use piecewise-linear B(l). On a segment, integrate sqrt(1-B/Bstar) analytically,
splitting exactly at bounce points. Zero-length threshold contacts split wells;
intervals touching a trace boundary below threshold are censored, never complete.

Required checks:

1. Triangular mirror well: relative action error <=1e-12 against analytic formula.
2. Smooth parabolic well: relative error <=2e-5 on 4097 points; refinement from
   257 to 1025 to 4097 must decrease error. Include exact-grid turning points.
3. Independent Gauss-Legendre quadrature of the same linear segments: relative
   discrepancy <=1e-6 using 128 points per segment.
4. Constant-B, empty/no complete well, multiple wells, boundary truncation,
   nonmonotone coordinates and nonfinite inputs explicitly exercised.
5. Scaling: coordinate scaling multiplies J; common B/Bstar scaling preserves J.
6. Controlled alpha-dependent length modulation of a perfect well must recover
   spread 0.02 for modulation 1% with symmetric alpha samples. Preserve extrema;
   no alpha averaging may erase a deliberately bad line.

## Frozen real-data experiment

Authoritative Goodman vacuum nfp=1,2,3 wouts and published trace source are
identified by references/goodman_qi_transfer_cases.json hashes; reject mismatches.
Use s=[0.25,0.5,0.75], alpha uniform on [0,2pi), phi starting at zero.

For each case, derive a common trapped-field interval from the coarsest traces:
lower = max over every sampled surface/alpha of min_phi B;
upper = min over every sampled surface/alpha of max_phi B.
Freeze Bstar=lower+q*(upper-lower), q=[0.1,0.3,0.5,0.7,0.9] for all refinements.
This avoids changing particle pitch when comparing radial or numerical results.
If the interval is empty, report failure and do not choose a replacement grid.

Trace sequence (nphi, nalpha, field periods):
`(401,16,2), (801,16,2), (1601,16,2), (1601,32,2), (3201,32,4)`.
All five runs are required for each case. The last tests trace length at the
same angular spacing. Keep raw B/l traces as compressed local artifacts with
hashes; retain all well actions and compact summaries in tracked evidence.

The conservative envelope diagnostic is `(max J - min J)/mean J` over all
complete wells on all alpha lines for a given s/Bstar. This mixes well families:
report it as an envelope, not a branch-matched omnigenity score. Count censored
wells separately and require >=1 complete well on every sampled alpha line.

Qualification screens, applied to every s/Bstar cell rather than just a mean:

- 801->1601 phi: identical per-alpha well counts and ordered-well action changes
  <=1e-3 relative. Bound order is a numerical matching device only.
- Every refinement pair: envelope change <=max(0.002, 0.05*abs(previous envelope)).
- All configurations/surfaces/pitches have complete-well alpha coverage 100%.
- All trace arrays finite, B>0 and arc length strictly monotone up to global sign.

Failures remain failures. Thresholds will not be retuned to fit this run. Full
metric qualification additionally requires independently validated tracing,
well-family matching, pitch/radial-grid studies and contour topology. A passed
screen establishes only this bounded measurement study. Maximum-J requires
radial derivatives at fixed invariants on matched branches; it is deferred.

## Evidence and commits

Commit this protocol before kernel implementation and real-data evaluation.
Then commit implementation/tests, followed by measured results and interpretation.
Record protocol, code, source and raw-input hashes; runtime, warnings and missing
coverage. Any diagnostic extension needs a new protocol commit before execution.
