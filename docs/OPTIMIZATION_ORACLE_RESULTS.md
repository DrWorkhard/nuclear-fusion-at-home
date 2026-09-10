# Common coil oracle qualification — 2026-09-10

Protocol ec1fc43 preceded implementation 119388f. The first preparation failed
because the adapter lost the serialized coil regularizations on Fourier
promotion. That failure remains in oracle-qualification-v1/summary.json.
Correction ee71fe3 preserves the existing regularizations, without changing the
physical model or thresholds. The new immutable retry directory contains the
completed four-arm qualification.

The promoted order-8 system has 207 free DOFs. Its B values are identical to the
source on the 64 prescribed field-equivalence points (maximum relative difference
0). Shared setup took 0.390 s. The maximum finest directional-derivative error is
1.289e-14 in the specified normalization, below 1e-6. Both methods' repeats have
identical proposed-x hashes, counters, vectors and stop status.

| Arm (each repeated twice) | Actual full bundles | Cache hits | Stop | Best vector merit |
| --- | --- | --- | --- | --- |
| L-BFGS-B | 10 | 0 | Relative reduction, after one optimizer iteration | 6.04289e-13 |
| Pinned AL | 150 | 3561 | Exact budget exhaustion; one denied request | 5.95336e-13 |

The 150 counts include seven charged directional-difference probes per arm.
L-BFGS-B's reported nfev=3 excludes these probes; our count=10 includes them.
AL requests 3,712 component/value/Jacobian accesses; the cache turns these into
exactly 150 full bundles and one rejected new proposal. No backend call occurs
after the cap. Both arms had zero failed backend attempts. Best-x arrays and
serialized fields were saved without another physics evaluation.

**The arms did not consume equal budgets.** This qualifies a common cap and
auditable accounting, not an equal-budget method ranking. It uses only one warm
start and a shared new oracle, not either complete upstream optimizer wrapper.

## Retained negative optimization finding

The best recorded flux components are 1.09935e-6 (L-BFGS-B) and 1.09033e-6 (AL),
while the input cut-in is 1e-8. Neither candidate has established feasibility.
L-BFGS-B terminates after one iteration through its relative-reduction condition;
the merit is only about 6e-13. The backend vector was squared to form the common
least-squares merit. Thus a small absolute objective scale can satisfy a
floating-point optimizer's termination test without meeting the physical bounds.
The stop is reproduced, not interpreted as a good design.

**Subsequent test:** NORMALIZED_FEASIBILITY_RESULTS.md shows that order-one
normalization alone does not cure the one-step stop. Small objective scale is
not a sufficient causal explanation; the failed trial/unchanged return is now
recorded explicitly. The original evidence and its thresholds remain unchanged.

A separate prospective experiment may normalize the **whole common vector** by
its frozen initial norm. That positive scalar preserves its zero set and affects
both methods equally, but changes numerical optimization and must receive its
own protocol and evidence. The original unnormalized result is not overwritten.

## Limits and verification

Five adversarial oracle test groups pass; full local suite 83 passed, Ruff clean.
The real gradient check is directional at the start only and does not certify
nonsmooth threshold crossings. The current pinned squared-flux routine is
thresholded, so physical admission must use a separately computed unthresholded
metric and refined geometry, not the merit or solver-success flag.

This run used the locked benchmark+engineering+dev environment, OMP_NUM_THREADS=1,
OPENBLAS_NUM_THREADS=1, OMPI_MCA_btl=self and a writable temporary Matplotlib
cache. The installed optimizer-source hashes match the pinned checkouts. The
pinned AL emitted SciPy's warning that its legacy `disp` option is unknown; it is
retained as a compatibility warning. No external source or dependency pin changed.

Reproduce with the script's --output/--raw options pointing at fresh directories:
`PYTHONPATH=src .venv/bin/python scripts/qualify_optimization_oracle.py`.
G2 remains open for a strong feasible baseline and actual replicated equal-budget
comparisons; all engineering and reactor-physics limitations remain in force.
