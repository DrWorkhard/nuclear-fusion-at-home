# Prospective independent-integrator check of the failed continuation trace

Decision: is the failed continuation's saved geometry reproduced by a different
integrator with finer coil quadrature and tighter numerical settings? The
[center check](ISSUE48_AXIS_CENTER.md), recorded in archive
`039a0a71c9d0e2345b1ddcae6524eb6bae7bcc42`, does not resolve the reversals. Before
further reconstruction work, test whether tracing error plausibly explains them.

Freeze continuation launches 10 (known failure) and 8 (qualifying control), both
s=0.5, from archive `191875d231b396e5960cbd9460a37a6c462b6381`. Bind its manifest,
report, exact current/coil snapshot and two NPZs. Start at each recorded physical
R,Z point at phi=0, following positive phi as in the original saved paths.
Original tracing used native compute_fieldlines, 512 coil nodes and tol=1e-10.

Use 1024-node native Biot–Savart fields and the unchanged independently tested
DOP853 period-map function from producer `5a0d06303a2d0405f52e0f179176bc2ada532536`.
Use rtol=1e-11, atol=1e-13, max step pi/100. Compose exactly 640 one-field-period
maps per launch, equivalent under nfp=2 symmetry, to produce chronological pi/0
section points for 320 toroidal turns. This changes integrator/parameterization
and numerical settings together; it is not an isolated attribution of each error.
No equilibrium solve, axis search, optimizer, extended trace or flux reconstruction.

Keep the original target-axis center, eleven residue sequences and 1e-8-rad cutoff.
Report all paired R,Z errors, old/new gaps, direction changes and physical return
RMS. Frozen comparison rule: both launches must have maximum paired crossing
distance <=1e-5 m, identical direction-change counts in all 22 residue sequences,
and pooled gap difference <=0.01 rad. Failure means the tracing comparison is
unresolved; never substitute a contour label or change the original 19/20 verdict.
Check independent filament fields at five predetermined new crossings per launch
(indices 0/79/159/319/639) to error <=1e-12 using scale max(1,|B|).

One attempt, failure then control: 600 s inside the driver after imports, 630 s
supervised total including startup/finalization; one thread, 256 MiB aggregate,
3/2 GiB disk reserves and 5 s clock discrepancy. Reuse reviewed owned-process
supervision and frozen environment verification. Save partial crossings every
40 periods, all failures and final records. No retries or outcome-driven retuning.
Existing analytic rotating-field tests qualify the map before native execution;
add a composition/section-order check. Preserve all original outputs/environment.

A pass supports numerical reproducibility of these two finite traces, not
continuum error bounds, magnetic-surface existence, islands, confinement or
benefit transfer. Failure does not prove that the native trace is wrong. Final
adversarial review precedes local integration; publication remains unauthorized.
