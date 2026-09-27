# Current verification

Updated 27 September 2026. Git retains earlier verification records.

## Interior-screen intake repair

The prepared screen rejected original snapshots because `-np.pi/100` is one ULP
different from their saved flux. It now uses **−0.03141592653589793 Wb**, exactly
as the hash-bound reference input specifies, and explicitly checks that pairing.
No tolerance was added, snapshot changed or physics threshold relaxed.
The prior failure is preserved in the cleanup commit `fbfbe47`.

- Focused suite: **51 tests pass**, 0.89 s; includes committed-input identity and
  rejection of a one-ULP flux change.
- Real-data intake: all five prospectively fixed snapshots, both target levels
  and **76 source identities** pass; no native fields evaluated.
- All 48 public tests, scoped Ruff, documentation and whitespace checks pass.

The existing one-threaded launcher is bound to the completed restart's actual
result digest. Planned native screen: fifteen rows, 180 s worker/185 s supervisor,
128 MiB output, 3/2 GiB disk reserves. Process inspection found no concurrent
research job; available disk is 39 GiB. The [screen record](../optimization/INTERIOR_FIELD_EXPLORATION.md)
owns the question, conventions and limitations.

## Retained cleanup qualification

At `fbfbe47`: 404 active tests, 48 public tests and eight copied-tree release
checks pass (local Python 3.11/3.12). The tagged removals, unchanged scientific
evidence and source-reference checks remain recorded in that commit.
No dependency sync, hosted CI, separate-machine reproduction or external review.
Optional engineering dependency pruning remains deferred after the earlier
approval-service limit. Step 4/MS1 remain open.
