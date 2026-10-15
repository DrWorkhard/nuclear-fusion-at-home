# Target intake for new plasmas (#115)

[Active coil research](README.md#new-targets-115) ·
[Issue #115](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/115) ·
[Programme #116](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/116)

**Question.** Can a plasma other than the two registered targets enter
`fit_coils.py`, `check_coils.py`, `trace_surfaces.py` and `measure_coil_bounce.py`
without changing what reference401 and selected401 mean? #114 stages 1–2 need this.

**Method.** `make_wout.py` solves a hash-bound input with its own explicit 401-surface
schedule. `make_target_spec.py` freezes input/Wout hashes, vmecpp version, B², −phiedge
and a seed. The tools take `--target-spec`; a specification cannot reuse a registered
label, and every tool then binds exactly its Wout. Acceptance code is unchanged.

**Inputs.** Committed reference401/selected401 inputs (`57394ef6…`, `6bec3483…`);
vmecpp 0.8.0, SIMSOPT 1.11.1, Python 3.12, one thread, macOS x86_64. Raw outputs are in
ignored `results/n18/`.

**Wout path.** Both regenerations completed (`ier_flag` 0, about 335 s each) and are
byte-identical to the regenerations from 3–14 October (`0f2b626c…`, `3d5df9a4…`), so the
path is deterministic on one machine and version. They are not the archived Wouts
(`83dc45b9…`, `8cd6bebf…`). Earlier checks already showed numerical agreement on derived
quantities: starter samples to 3.4e-10 and the narrow bounce score to 3.4e-8 for
reference401, and 1.0e-7 for selected401 (see [joint protocol](JOINT_PROTOCOL.md#equilibrium-identities)).
A per-variable comparison against the archived files needs the maintainer:

```bash
.native/bin/python scripts/make_wout.py --compare artifacts/plasma-design-v2/reference-fine/wout.nc \
  --wout results/n18/reference401/wout.nc --output reference401-compare.json
```

**Controls through `--target-spec`** (selected401 regenerated, label
`selected401-regen-vmecpp080`, seed: the public length-headroom candidate):

| Quantity | Spec route | Recorded (archived Wout) | Relative difference |
| --- | ---: | ---: | ---: |
| B² | 1.631346444458323 | 1.6313464444829588 | 1.5e-11 |
| Boundary mean, shift ½ | 0.0017241642811352625 | 0.0017241642811352633 (#35 control) | 5e-16 |
| Boundary max, shift 0 | 0.009415926262974288 | 0.009415926262974272 | 1.7e-15 |
| Interior vector RMS, level 0 | 0.013625228266343844 | 0.013625228265735496 | 4.5e-11 |
| Geometry | pass | pass | — |
| Ideal bounce, wide / narrow | 2.1164e-4 / 1.10089e-5 | 2.12e-4 / 1.10e-5 (#115) | rounding |
| Tracing, 200 transits | 10/10 confined, max \|Δι\| 0.006 | — | — |

The boundary and geometry do not depend on the Wout; interior and bounce differ only
by the regenerated Wout. Unit tests reject registered labels, wrong schemas,
conflicting specifications, flux sign errors, unbound inputs and any other Wout.
One failed run is kept: editing `coil_check.py` during a bounce run tripped its
source guard (`sources changed during diagnostic`), as intended.

**Conclusion.** New plasmas can be admitted under their own labels with the same
checks. **Not shown:** bit-for-bit equality via `--target-spec` built from the
*archived* selected401 Wout. That run needs the maintainer's file and should give
B² = 1.6313464444829588 exactly:
`make_target_spec.py --target-id selected401-archived-check --wout <archived> …`.
Errors against different targets remain incomparable; this is intake, not acceptance.
