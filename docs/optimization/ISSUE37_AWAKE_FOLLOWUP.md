# Joint feasibility follow-up v2: temporary sleep assertions

Prospective registration, 7 October 2026, before any v2 scientific operation.
Question: does either fixed plasma perturbation meet the original joint
feasibility screen when both arms finish without the host suspension that
interrupted [v1](ISSUE37_JOINT_RESULT.md)? This is a distinct attempt, not a retry
within v1 or a pooled result. The [short host check](../validation/JOINT_EXECUTION_HOST.md)
supports temporary assertion availability only.

## Frozen science and limits

Use the unchanged [v1 protocol](ISSUE37_JOINT_FEASIBILITY.json), SHA256
`25a8887544c4861c1e7c40ff0c884730f2ac5784ea3460430a69fd7ece6690b7`,
and reviewed native implementation introduced at
`e55dd75fbc2c1be679ba96e1aa1c9e242039b860`. Freeze the exact clean follow-up
commit and configuration before launch. No evaluator code changes are planned.
Both arms start fresh: C from the original target/seed, J plus then minus with
cold solves and the same original coil seed. No cached C or solved J data from
v1 or qualification studies enters v2. Keep 1800 s search + 900 s diagnostics
per arm, one native thread, all original input/environment hashes, storage/disk
limits, candidate selection and scientific gates. No retry or extension after
this attempt. Every failure remains evidence. The actual-coil endpoint stays
null and physical acceptance false regardless of feasibility verdict.

## Execution conditions and ownership

Before launch, verify source/configuration, both preserved dependency inventories,
original input hashes and disk reserve; complete review and software checks.
Run serially on AC with no other agent-owned heavy job. Do not change permanent
power settings. Host load outside agent-owned jobs is unverified.

Start `/usr/bin/caffeinate -i -s -t 5500` in its own owned tool session, capturing
its PID before `exec`. Observe both `PreventUserIdleSystemSleep` and
`PreventSystemSleep` lines for that PID using `pmset -g assertions`, and confirm
AC with `pmset -g batt`. Retain only owned assertion lines and the power-source
line. Start the existing comparison CLI promptly, within 30 s of assertion
admission, under the recorded minimal environment and all four native thread
limits set to 1. Its fresh output is `artifacts/issue37-joint-comparison-v2`.
Scientific setup remains charged separately inside each arm's original clocks.
The assertion timeout exceeds the combined 5400 s scientific ceiling plus the
launch interval; it never extends any arm budget.

The agent owns and polls both tool sessions, records sampled assertions/AC while
observing progress, and checks assertions/AC after the scientific session exits.
A failed query, observed assertion loss or AC loss makes the enclosing v2 result
inconclusive even if the numerical report completes; preserve both records.
It does not permit a restart. Sampling does not prove continuous AC/assertion
presence or controlled host load. Original scientific clock guards remain the
suspension check, without reset or weakening. The assertion process is separate
from native workers and never acts as their watchdog.

After the scientific session is terminal, send SIGTERM only to the owned
assertion PID if it remains live, poll its session to terminal, and verify owned
assertions absent. The 5500 s automatic expiry bounds sleep prevention if the
agent is interrupted; unlike a watched-parent assertion this setup is not tied
to the scientific PID. Do not kill/restart scientific work on an observation
timeout. Existing native supervisors retain worker cleanup and arm deadlines.

## Evidence and decision

Record the exact reviewed producer/configuration, commands, process handles/PIDs,
assertion timestamps, sampled AC/clock observations, cleanup and original raw
outputs. Archive v2 separately with a manifest and scoped replay; retain v1.
Apply the original continue/change/inconclusive rule only if required work and
the recorded host conditions complete. A failed follow-up does not authorize
another automatic attempt. Adversarial agent review precedes execution and final
publication/merge; it is not external physics peer review.
