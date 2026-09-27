# Current verification

Updated 27 September 2026. Latest completed work; Git retains previous records.

## Matched restart closed before repository simplification

At clean `c1fdddf`, both 1,200-bundle arms complete in 478.475 s worker /
479.247 s supervised. Expanded low modes reach fine RMS **0.00488873136**,
55.27% below the original-box control with 8.64% less current. Both endpoints
pass scoped continuous geometry; both boundary-error limits remain failed.
The 1e-2 exploratory signal is met, not Step 4 acceptance.

Independent saved-data audit checks 46 search and seven geometry sources, all
2,400 trial pairs, eight derivative checks, repeats, absolute bounds and selections;
48 fine metrics, four loop integrals and 256 each of B/A comparisons. Geometry
checks compose 552 pair and 48 plasma bounds and twelve tighter-curvature
classifications. No native field or full distance/enclosure recalculation is
claimed by that audit. Geometry execution takes 4.539 s / 4.826 s supervised.

The [canonical result](../optimization/COHERENT_COIL_EXPLORATION.md) and
[evidence](../../evidence/coherent-restart-v1.json) preserve the questions,
execution receipts, sources and 4,827 run files / 52,263,829 bytes.
Earlier failures remain in the predecessor evidence.

## Implementation checks

- Matched restart: **63 combined synthetic tests pass** (2.08 s main);
  independent reviewer reruns 47 (1.37 s).
- Prepared interior screen: **49 synthetic tests pass** (0.58 s main, 0.71 s
  implementer). No actual interior run, optimization or VMEC calculation.
  Source-level review checks reference401 archive identities and exact B² scale.
- Scoped Ruff, documentation structure and whitespace checks pass.
- Latest recorded public run: **47 tests pass** (3.466 s).

The user-requested simplicity review now takes priority. No additional research
run has been launched. The interior screen is preserved but unexecuted.
No full native regression, separate-machine reproduction, external peer review,
hosted release or Step 4 completion is claimed.
