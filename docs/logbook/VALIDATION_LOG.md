# Current verification

Updated 27 September 2026. Git retains earlier verification records.

## Longer/wider fit and interior check completed

Clean implementation `eb458ef` completes both 300 s searches. The same-box
candidate passes scoped geometry at boundary RMS **0.004712664**. The wider-box
candidate reaches **0.001947576**, but length bounds remain unresolved.
Its interior-vector RMS **0.009769586** passes 0.01 at all three tested levels.
Both boundary gates still fail; no overall physical acceptance or Step 4 closure.

- Search/fine/geometry worker **619.612 s**, supervisor **620.427 s**: within
  660/670 s. Interior worker **2.915 s**, supervisor **3.388 s**. One thread.
- All **82 search** and **96 interior source hashes** verified unchanged.
  Separate saved-array arithmetic checks boundary and interior RMS, independent
  sampled B/A comparisons, flux and the composed geometry classifications.
  No duplicate full continuous-geometry calculation or separate-machine run.
- All **3,225 trial records** checked; selection reproduced from completed
  eligible points. All four fine boundary rows and six interior rows pass
  numerical checks. No interior-score-based selection.
- Complete retained raw-family inventory: **6,504 files / 73,728,182 bytes**,
  within 256 MiB. Its sorted path/hash digest is recorded in the evidence.
- Wider sampled lengths approach 3.5 m; the conservative upper bound is
  **3.519998 m**. This is unresolved, not proof of an actual length violation.
- The interrupted v1 prefix and −15 termination receipt remain. The strict
  shared JSON converter repairs result serialization, not numerical physics.

[Result and limitations](../optimization/LONGER_COIL_EXPLORATION.md) ·
[Source-bound evidence](../../evidence/coherent-longrun-v2.json).

## Software checks

- Active research regression: **410 passed**, 13 known HiGHS-option warnings,
  **22.12 s** in the intact native environment.
- Public suite: **48 passed**, **3.364 s**. Scoped Ruff, documentation structure
  and whitespace checks pass. No dependency sync or hosted CI run.
- The exact-flux input regression and one-ULP poison test remain passing;
  −0.03141592653589793 Wb is unchanged. New strict-JSON tests cover geometry
  pass/fail/unresolved results.

The [headroom experiment](../optimization/LENGTH_HEADROOM_EXPLORATION.md) is
prepared: construction penalty 3.44 m, selection 3.45 m, unchanged 3.5 m
acceptance. Its selection/reuse tests pass: **29 tests**, **0.76 s**. No native
headroom run has completed yet.

The next experiment puts length headroom into construction and selection.
Shared acceptance thresholds stay fixed. Realized topology, Step 3 benefit
transfer, pressure/engineering, independent backup/reproduction and MS1 remain
open. Native source arrays and ignored outputs are not backed up by Git.
