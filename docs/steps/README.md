# Completed steps

Steps 1–3 passed their registered local scopes. They do not establish a reactor.
[Status](../STATUS.md) · [Roadmap](../PROJECT_PLAN.md) ·
[Active Step 4 requirements](STEP_4_PLASMA_AND_COILS.md)

## Steps 1 and 2: foundation and repeatable iteration

Selected W7-X/Goodman regressions and independent coil checks passed. The broader
W7-X comparison remains 60/63. A real optimizer cycle repeated exactly, but both
candidates failed the raw-flux limit: 8.191664e-8 versus 1e-8. The selected point
came from a start replay, so this established reproducibility, not optimizer gain.
The initial acceptance run failed a bookkeeping check and remains rejected.

Producer `1aa28b6`: [final audit](https://github.com/DrWorkhard/nuclear-fusion-at-home/blob/68db098b664bb072854b687040e103aaafee463c/evidence/foundation-acceptance-v2/summary.json),
[iteration](https://github.com/DrWorkhard/nuclear-fusion-at-home/blob/68db098b664bb072854b687040e103aaafee463c/evidence/foundation-acceptance-v2/cycle-audit.json),
[candidate checks](https://github.com/DrWorkhard/nuclear-fusion-at-home/blob/68db098b664bb072854b687040e103aaafee463c/evidence/foundation-acceptance-v2/holdouts/summary.json).

## Step 3: vacuum plasma diagnostic

Four boundary changes reduced wide-domain bounce-action variance by **11.17%**
and narrow-domain variance by **4.85%**; all ten registered gates passed.
Both domains informed construction. The first design improved the narrow metric
but worsened the wide metric by 15.53% and violated 20 local limits; it remains
rejected. These are diagnostic gains, not measured confinement or fusion power.
Realized coil fields, pressure, transport and engineering remain open.

Recorded base `f285fbdf` is dirty; verify the recorded code hashes.
Evidence was committed at `d429783`: [final audit](https://github.com/DrWorkhard/nuclear-fusion-at-home/blob/68db098b664bb072854b687040e103aaafee463c/evidence/plasma-balanced-v1/final-audit.json),
[diagnostics](../../evidence/plasma-balanced-v1/validation.json),
[selected target](https://github.com/DrWorkhard/nuclear-fusion-at-home/blob/68db098b664bb072854b687040e103aaafee463c/evidence/plasma-balanced-v1/selected-input-401.json),
[reference target](../../evidence/plasma-design-v2/reference-input-401.json).

Detailed methods, budgets, failures and original commands remain at their recorded
Git revisions; see [reproduction](../validation/REPRODUCING_RESULTS.md).
