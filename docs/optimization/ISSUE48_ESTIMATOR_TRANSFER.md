# Interval estimator qualifies the saved matched-launch contours

**Both five-line arms pass this new numerical assessment.** Applying interval
quadrature across all saved round-2 launches resolves the previous integration
blocker without moving launches or retracing. The four adjusted launches in each
field have estimated enclosed-flux labels within 5e-4 of 0.75. The separate
[original matching pilot](ISSUE48_MATCHED_LAUNCHES.md) remains inconclusive under its
original method; this does not retroactively change that verdict.

| Final-prefix diagnostic | Reference fit | Improved-target fit |
| --- | ---: | ---: |
| Numerically qualified lines, including unchanged control | 5/5 | 5/5 |
| Maximum residual from 0.75, four adjusted launches | 3.86e-5 | 7.93e-5 |
| Maximum last-two-prefix label change | 1.84e-6 | 2.03e-7 |
| Largest angular gap, rad | 0.176 | 0.127 |
| Maximum held-out radial error | 18.9 µm | 3.26 µm |
| Maximum alternating-subset label spread | 1.24e-6 | 4.17e-7 |

## Method and evidence

The clean producer/evaluator is `38cd7cff0435416147757d4316792908a0e974d9`;
its [prospective protocol](https://github.com/DrWorkhard/nuclear-fusion-at-home/blob/38cd7cff0435416147757d4316792908a0e974d9/docs/optimization/ISSUE48_ESTIMATOR_TRANSFER.md)
was committed and reviewed before this single assessment. The
[two-contour diagnosis](ISSUE48_KNOT_QUADRATURE.md) supplies the method. This run
extends it to prefixes of 160/320/640 crossings and disjoint alternating subsets
of all ten saved traces, retaining the original symmetry-checked phi=0/pi pooling,
centers, frozen currents, edge denominators and 512-node coil discretization.

Gauss orders 4/8 integrate each spline interval; 24 radial nodes check Stokes.
Original reconstruction thresholds are unchanged. Final subset order changes are
at most 1.95e-11; final independent NumPy A-line discrepancies at most 3.34e-16.
All target reconstruction, edge and analytic controls pass. Both arms retain the
unchanged nominal s=0.25 control; it is not forced to estimated flux 0.25 or 0.75.

The driver completed in 160.16 s and end-to-end supervision in 170.77 s, within the
600/660 s limits. One native thread, 256 MiB output ceiling and 3/2 GiB disk reserves
were enforced; total output was below 1 MiB. UTC and monotonic durations agree to
about 0.004 s. External host load remains unverified; no throughput claim follows.

Prepared archive `evidence-issue48-estimator-transfer-v1`, commit
`48337ac2b458a369b3231ed7bfa65f9d20e6f9e4`; **publication is pending**. It preserves
all original outputs, source/input hashes, controls, commands, timing and replay.
The exact traces/snapshots remain in matching archive `896180e939b0234aea29ab33621a73aad6c5d20a`.
Original Wouts are local-only; saved-contour A-flux and reconstruction replay needs
only NumPy/SciPy. A fresh shallow archive checkout reproduced 190 line integrals
within 5.56e-16 with SIMSOPT/Wout-reading packages disabled. A separate audit checked
162 derived-field identities. This does not rerun native B-fan checks, rebuild
target contours or retrace. [Driver](../../scripts/qualify_saved_flux_labels.py).

## Next decision and limits

No further tracing is justified solely by the old quadrature failure on this set.
The remaining common-physics problem is qualifying realized surfaces and a shared
straight-field-line phase convention over the full action domain. Four geometric
launch phases at one adjusted label do not supply that endpoint. Symmetry pooling
can mix island components; spline agreement does not prove nesting or island
absence. This work establishes no equal PEST-alpha sampling, confinement, benefit
transfer, continuum-filament error bound or physical acceptance. Agent review and
same-machine numerical agreement are not external physics validation.
