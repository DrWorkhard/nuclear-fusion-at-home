# Step results

Purpose: one English results page per roadmap step. Each page states what the
step had to show, the actual result with its key numbers, what it does not show,
failures kept on record, and links to evidence. Closed detailed reports/code/tests
resolve at the [freeze tag](../validation/REPRODUCING_RESULTS.md).
Requirements and next actions stay in the
[roadmap](../PROJECT_PLAN.md); the overall evidence summary is on the
[status page](../STATUS.md).

Current conclusion: Steps 1–3 are complete in their registered scopes. Step 4 is
in progress: selected coils pass scoped continuous geometry, but their fields
fail acceptance limits. Step 5 has no results yet; a future
[Proxima comparison](../squid_c/README.md) needs a matched reference.

[Overview](../README.md) · [Status](../STATUS.md) · [Roadmap](../PROJECT_PLAN.md)

## Documents

- [Step 1: a reliable foundation](STEP_1_FOUNDATION.md). Local toolchain reproduces
  the W7-X/Goodman regressions and correctly accepts or rejects coil candidates;
  first acceptance run rejected for a bookkeeping bug, complete rerun passed.
- [Step 2: reproducible design iteration](STEP_2_ITERATION.md). A real optimizer
  cycle repeats exactly and is independently evaluated; both candidates correctly
  rejected on the flux limit.
- [Step 3: an improved plasma target](STEP_3_PLASMA_TARGET.md). Four boundary
  changes lower the wide bounce-action metric by 11.17% with all ten gates passed;
  the first design stays rejected.
- [Step 4 results so far](STEP_4_PLASMA_AND_COILS.md). Work packages 4A–4D, the
  coil experiments and lessons, calibration/feasibility priority and links to
  detailed numerical and software qualification. Field limits still fail.
