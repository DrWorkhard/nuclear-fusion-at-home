# Current verification

Updated 27 September 2026. Git retains earlier verification records.

## Length-headroom follow-up completed

Revision `963793d`: **1,575 bundles completed**, trial1574 selected with all
sampled lengths ≤3.45 m. The shared 1024-node/512²-surface geometry check passes:
length upper bound **3.477734 m**. Boundary RMS **0.002050310** and maximum
0.0101974 fail; interior RMS **0.01165995** also fails. This improves the best
geometry-checked boundary fit, not the full acceptance outcome.

All **91 source hashes** match. Separate saved-array arithmetic checks both
boundary and three interior rows, flux/current identity, independent B/A samples,
the prospective selection across **1,576 records** and bound classification.
Worker **306.360 s**, supervisor **306.938 s**, retained family **36.15 MB**;
all declared resource ceilings respected. No complete geometry rerun.
[Evidence](../../evidence/coil-headroom-v2.json).

The next comparison keeps the same seed, penalty, selection and 300 s budget,
but expands the low/high-mode widths from ±0.16/0.04 to ±0.20/0.06 m. Its
default-box identity is tested. It is prepared, not yet a scientific result.
Focused headroom/shared-search checks: **31 passed**, **12.53 s**; scoped Ruff,
docs and diff checks pass. Public suite passes all **48 tests**.

## Preceding longer/wider check

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

The [headroom experiment](../optimization/LENGTH_HEADROOM_EXPLORATION.md) uses
construction penalty 3.44 m, selection 3.45 m, unchanged 3.5 m acceptance.
The first setup failed before search on native
penalty-object subtraction (2.563 s); direct assembly fixes that unsupported API.
The failed output remains at `artifacts/coil-headroom-v1/`.
All **9 headroom tests pass** (12.91 s), including real native penalty assembly
and a finite-difference check of its derivative. Scoped Ruff/docs/diff pass.

The next experiment keeps headroom and tests more shape freedom.
Shared acceptance thresholds stay fixed. Realized topology, Step 3 benefit
transfer, pressure/engineering, independent backup/reproduction and MS1 remain
open. Native source arrays and ignored outputs are not backed up by Git.
