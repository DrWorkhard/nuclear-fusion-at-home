# Realized-flux label qualification

**Exploratory pilot, frozen before tracing.** The decision is whether a reliable
common realized-flux label can support a new action comparison of the two frozen
[#25 fits](ISSUE25_MATCHED_TARGETS.md). [Issue #48](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/48)
reports phase-dependent label shifts in the reference arm. Its contour-construction
assumption needs checking before label correction or benefit claims.

## Inputs and bounded check

Use original hash-bound reference401 and selected401 Wouts, their published
`evidence-issue25-matched-v1` selected snapshots, and frozen currents. Snapshot
SHA256s: `ec1f8ce7073177d31e1dc1d44aad6478169b602189b8e8b204373481da368799`
and `c2ea45c171fd7452d5fc51395617f311bd2067f470dfd9d75a0fcf02896ade79`.
Run [measure_flux_labels.py](../../scripts/measure_flux_labels.py) sequentially,
one thread, at most 900 s and 256 MiB per arm, 3 GiB initial / 2 GiB live reserve.
Native calls are checked before/after; retain any deadline failure. A supervising
process stops an arm after 960 s. No new optimization or acceptance-gate change.

Start at target VMEC `(s, theta, phi) = (0.25, 0, 0)` as a control and
`(0.75, {0, pi/2, pi, 3pi/2}, 0)` for the affected narrow-domain surface.
These are geometric VMEC theta launches, not the action diagnostic's PEST alpha.
Use direct 512-node Biot–Savart at tolerance 1e-10, up to 161 transits with a
finite integration cap and no boundary classifier. Analyze the first 40/80/160
positive-time phi=0 crossings separately. Incomplete traces remain incomplete.

Represent a contour as periodic cubic radius versus geometric angle about the
target axis. Record angular gaps and held-out radial errors using alternating
crossing subsets. Compare toroidal flux from A line integration with B fan
integration, plus 256/512-point line quadrature. Both use the same native field;
this is a Stokes/discretization check, not independent field implementation.
The contour orientation is counterclockwise in R,Z (normal minus e_phi); numerator
and target-boundary denominator use the same orientation. Also check the original
signed target loop flux. Dense target contours and randomly subsampled contours
provide reconstruction controls. Analytic circle/deformed-circle tests check sign
and area; incomplete coverage and multivalued radii must remain visible.

## Decision rule and limits

Proceed to a bounded launch-matching pilot only if controls pass, all 160 crossings
exist, the 80-to-160 label change and subset-label spread are each below 5e-4,
maximum angular gap is below 0.4 rad, held-out radius error is below 0.1 mm,
and quadrature/Stokes label discrepancies are below 1e-5. Control reconstructed
labels must match their dense contours within 5e-4. These are diagnostic
qualification tolerances, not physical acceptance gates. Otherwise record the
specific failure and choose the cheapest check of its cause before any action
rerun. A label alone does not verify nesting, island absence or equal-alpha measure.
No full-domain or benefit-transfer conclusion follows from this five-start pilot.

## One bounded refinement

The clean 160-crossing producer was `23acc8de0892a3a77b669cd9a90dd693a452354a`.
Both arms executed, but several phases fail the stated sampling/convergence checks.
Keep those failures. Before any launch correction, repeat the same five starts
with `--crossings 320`, analyze 80/160/320 prefixes, use 1024/2048 angular and
24 radial quadrature nodes, and a finite native integration cap of 4800.
The extra budget is 900 s / 256 MiB per arm with the same reserves and supervisor.
The same tolerances apply to 160-to-320 changes; this is exploratory refinement,
not a new confirmatory claim. Snapshot hashes are now enforced by the driver;
returned late traces are saved before rejecting completion, as adversarial review
requested. No scientific conclusion depends on a late or missing trace.
