# Receipt-bound direct tracing

Component qualification registered and executed on 7 October 2026. The decision is whether the
[proposal diagnostics](ISSUE37_COIL_DIAGNOSTICS.md) can include the registered
direct-tracing requirement without treating a new target as an archived target.
`joint_coil.direct_trace` reconstructs the target through trusted solver intake,
checks the private frozen snapshot and 512-node physical coil mapping, and verifies
the direct field against the independent kernel at 64 seeded volume points to
1e-12. Its target Wout hash must match the admitted receipt.

Reuse the existing `realized_field.trace` method unchanged: ten target launches
s=0.05,0.15,…,0.95 at theta=phi=0, 200 requested transits, tolerance 1e-10,
128×64 full-torus stopping surface, classifier h=0.02/p=2, original finite
integration-time cap and signed-iota tolerance 0.02. Currents stay frozen.
Classifier stops inside the target remain inconclusive; incomplete transits and
opposite-sign iota cannot pass. These are target launches, not matched realized
flux/phase locations, and do not establish nestedness or physical acceptance.

The shared tracing function optionally retains complete sampled paths including
terminal stopping states. Existing callers still receive the same two outputs.
The joint route archives each path/hit array and its hash, allowing winding and
terminal-state classification to be replayed. Recheck bound sources/receipts after
all tracing and serialization. Native integration's internal B-call count is not
measured; report that limitation explicitly.

## Single cached-seed qualification

Use only the frozen plus-target startup snapshot at SHA256
`6f77179b8d4b973b88ee2a3e4fdc303e21ce9a08a32c9cf013b2b53e91e55c85`
from `evidence-issue37-coil-adapter-v1`, and the already qualified plus
solver receipt/Wout from `evidence-issue37-solver-qualification-v1`.
No new solve, fitting, current adjustment, other proposal or retry.

One **600 s total budget**, both monotonic/UTC clocks (5 s discrepancy limit),
one native thread, 256 MiB aggregate output, 3/2 GiB initial/live disk reserves.
An external process-group watchdog owns timeout and cleanup. Intake, native
startup, field controls, tracing, compression, source checks and final reporting
all consume that budget. Preserve every available failure/partial output; a killed
native batch may leave no paths. Late or resource-interrupted runs are ineligible.

Qualify the software route only if all ten line records/paths return, the kernel
control passes, frozen snapshot/source/receipt identities stay fixed and the saved
paths reproduce winding and stop classification. Report confinement, transit and
signed-iota gates separately, including failures; software qualification does not
require this unoptimized seed to pass those physical diagnostics. Freeze source
and obtain read-only adversarial review of the exact launcher before execution.
Archive full evidence separately. Agent review is not external physics review.
The full joint comparison stays disabled pending ideal-action scoring and
orchestration; a common realized-field endpoint remains unqualified. A cached
qualification solve cannot become free setup for a future joint arm.

## Result

The single cached-seed qualification passed at clean producer/evaluator
`02d6ad8783056f19e6b83c0af1da3b184b711dab`: 243.535 s driver, 243.824 s total
supervision, clock discrepancy below 0.002 s. All ten lines completed 200 transits
without a reported exit or inconclusive classifier stop. Maximum signed-iota
mismatch was 0.00470298050728446; independent volume-field discrepancy 3.917e-16.
No solve, optimization or current change occurred. Earlier boundary/interior gate
failures remain; this tracing result does not establish nestedness or acceptance.

Local archive `0fe500bb082ef96219a0cc0fb35b6fd3685e8ad8`, prepared tag
`evidence-issue37-direct-tracing-v1`, preserves all 20 raw files (19,398,499 bytes),
paths, exact scripts and replay recipe. Its 26-entry manifest SHA256 is
`acf1bedf43d184653552cc0a4ac8018ffe587944ea0f046fabdd85982ba887ee`.
Publication is pending; solver archive and native-file identities are explicit
dependencies. Fresh shallow replay verified 70 source/input/native bindings,
reproduced the independent kernel control with zero discrepancy and all ten line
records and their summary exactly in 1.142 s. It did not reintegrate field lines,
rerun solver/intake or re-attest timing. Fresh shallow producer checks passed
420 research tests (seven new route tests), 61 public tests, docs, Ruff and diff.
Read-only adversarial review preceded execution; full joint execution stays disabled.
