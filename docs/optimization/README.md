# Active coil research

Use penalized normalized fitting, then separate fine-field and continuous-geometry
checks. [Results and evidence](../STATUS.md) ·
[Next experiment and decision](STEP4_RESEARCH_PROGRAMME.md) ·
[Contribution ideas](RESEARCH_HINTS.md)

## Run the existing native fit

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 MKL_NUM_THREADS=1 \
  python scripts/explore_coil_headroom.py --box expanded --output artifacts/my-headroom
```

This requires the recorded local snapshots and [native environment](../validation/ENVIRONMENT.md).
It fits reference401 only; the proposed matched-target study is not implemented.
The [portable candidate](../../submissions/length-headroom-six-coil/README.md) needs
neither those artifacts nor native dependencies.

The retained implementation chain is headroom → longrun → restart → coherent →
constrained → normalized, plus the interior screen. These files contain reused
code and saved-run source dependencies, not separate research programmes.
Acceptance mathematics live in `coupled_coil_audit.py`,
`clear_coil_geometry_audit.py`, `curvature_bounds.py` and
`boundary_control_metrics.py`. Reuse them; optimization penalties do not admit a design.

Completed reports and retired drivers resolve through
[historical reproduction](../validation/REPRODUCING_RESULTS.md). Their results,
including failures, are summarized once in status; raw evidence is unchanged.
