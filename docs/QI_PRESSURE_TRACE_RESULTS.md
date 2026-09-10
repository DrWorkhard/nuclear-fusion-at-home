# Independent finite-pressure trace cross-check — results

Retrospective validation protocol fdcaa36; implementation 9ce3178; execution
2026-09-10. The hash-pinned published Goodman tracer supplies a separate coordinate
inversion and a B/B^phi-based length calculation, against the frozen geometry-based
pilot. This does not independently validate the equilibrium itself.

All 84 trace grids pass coordinate, B and cumulative-length comparisons. All
3,360 alpha/pitch/radius/resolution action comparisons pass geometric well matching
and relative action agreement. All 320 family derivative comparisons pass;
all 319 originally resolved signs survive the combined larger allowance. The
one previously unresolved family stays unresolved in our report.

| Case | Maximum relative B difference | Normalized length difference | Relative action difference | Absolute normalized derivative difference |
| --- | ---: | ---: | ---: | ---: |
| nfp2 vacuum | 2.20e-12 | 7.07e-6 | 2.76e-5 | 6.70e-6 |
| nfp2 beta2 | 2.11e-12 | 6.99e-6 | 2.72e-5 | 1.01e-5 |
| nfp3 vacuum | 3.47e-12 | 3.49e-5 | 1.18e-4 | 2.26e-5 |
| nfp3 beta2 | 3.45e-12 | 3.77e-5 | 1.21e-4 | 4.44e-5 |

Execution took 33.83 s. Data and raw-trace hashes are recorded in
`evidence/qi-pressure-trace-v1.json`. Published-source compilation emitted a
Python SyntaxWarning for its legacy `\p` string escape; the scientific source
was not modified. Trace diagnostics and warnings are retained in the evidence.

Correction to the earlier pilot next-check list: independent finite-pressure
trace consistency is now checked **for these four cases and grids**. Full radial
VMEC mesh convergence, other pressure/radius/pitch/alpha domains, between-sample
well topology and gauge-independent/global maximum-J conclusions remain open.

## Clean reconstruction and integrity audit

The separate detached clone, updated to 9ce3178, passes Ruff and 112 tests with
one absent-W7-X-data skip. The main workspace passes all 113 tests. Eleven
NumPy/netCDF fixture DeprecationWarnings remain visible in each run.

The clone re-extracted all finite-pressure files from the original read-only
archive cache into a fresh directory. All 31 case metadata records, all 62 member
hashes and the archive hash match the original inventory exactly. No prior
extraction tree was reused. The clone remains Git-clean.

A recursive read-only integrity audit over the inventory, four pilot results,
quadrature result and second-tracer result verified all 193 unique referenced
path/SHA-256 pairs against current local files. This includes raw traces and
evaluation sources, not an independent mathematical proof. Hosted CI, independent
download and native W7-X fresh bootstrap remain unwitnessed.
