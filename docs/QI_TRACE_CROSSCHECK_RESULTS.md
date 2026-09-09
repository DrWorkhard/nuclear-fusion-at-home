# Independent tracing cross-check — results, 2026-09-09

Protocol: 399a8fa. Implementation: fc435e3. The execution started from a clean
checkout of the implementation commit. All 27 case/surface/resolution checks
and all 135 pitch cells pass the frozen thresholds. Runtime: 12.93 seconds.

| Case | Finest pointwise relative B difference | Finest normalized length difference | Finest relative action difference |
| --- | ---: | ---: | ---: |
| nfp=1 | 2.0910e-12 | 4.6668e-6 | 6.2645e-6 |
| nfp=2 | 2.8960e-12 | 1.9461e-6 | 3.8171e-6 |
| nfp=3 | 4.2157e-12 | 7.0733e-6 | 9.0674e-6 |

The fixed limits were 1e-8 for B and 1e-3 for normalized cumulative length and
ordered-well action. Every cell has matching complete-well counts and full
alpha coverage. Action and length discrepancies decrease at successive phi
refinements for each case's reported worst-case envelope. This is not evidence
of arbitrarily small error: radial interpolation/staggering is still shared
with the VMEC representation and has not been refined.

The new tracer reconstructs theta using Newton inversion of VMEC lambda, and
arc length from analytic cylindrical geometry derivatives. The published tracer
uses its own root routine and magnetic B/B^phi integration. The new formula
passes a circular-torus analytic-speed test and a nonzero-lambda inversion test.
The tests also reject out-of-grid surfaces and nonfinite input. Only symmetric
wouts are supported. The independent method shares the original Fourier data;
it cannot detect errors already present in that equilibrium.

The suite now passes 64 tests. Ten NumPy/netCDF deprecation warnings arise while
writing synthetic fixture arrays; they are retained, not numerical solver
warnings. Ruff passes. Machine-readable comparison and source/data hashes are in
evidence/qi-measurement-v1/independent-trace-crosscheck.json.

Reproduce from the v1 raw traces without overwriting an existing result:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
  scripts/crosscheck_vmec_traces.py /private/tmp/qi-trace-crosscheck-new.json
```

This closes the bounded independent-tracing check for the sampled vacuum
surfaces. Full QI objective qualification still requires pitch/radial refinement,
well-family treatment and poloidally closed B-contour checks. Maximum-J at
finite pressure remains a separate qualification. No improved design is claimed.
