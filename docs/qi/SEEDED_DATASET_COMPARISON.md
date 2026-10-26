# Seeded dataset compatibility protocol v1

Prospective #112 comparison, 25 October 2026. No new seeded model results exist.
[Scorecard](PLASMA_SCORECARD.md) · [Machine-readable freeze](seeded-comparison-v1.json)

## Question and fixed inputs

Do three outcome-independent stored boundaries reproduce all twelve stored scalar
labels under the approved default-high-fidelity pipeline? The cheapest decisive
test is one serial call per fixed boundary, at most three calls, with no replacement
or retry. This protocol freezes the comparison; it does not authorize execution.

The [original public sampling freeze](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/112#issuecomment-6209297730)
selects zero-based physical rows **146128, 141151, 116646** from
`proxima-fusion/constellaration`, default/train, revision
`8da71572eb63ce93e77ce89bec0d7c30b7eba89e`. Rank all 182,222 rows by
SHA-256 of ASCII `C18-112-dataset-v1-20261016:<row>`, ties by row. No metric,
solver outcome or flag filters apply. These rows remain fixed, including failures.

The JSON binds each boundary, raw label JSON and existing VMEC export by SHA-256,
plus plasma/metric IDs and all 36 stored values. Partial Parquet range retrieval
verified the projected rows; full-shard LFS hashes were not checked. The dataset
card attributes Proxima Fusion and declares MIT licensing. Existing raw ranges
and exports remain retained locally; this protocol does not publish those files.

## Comparison fixed before calls

For each raw, signed metric independently, require
`abs(computed - stored) <= 1e-8 + 1e-6 * abs(stored)`, inclusively. Apply this to
every name in the JSON's twelve-metric list, including raw QI, both transforms,
both mirror ratios, triangularity and the aspect/transform ratio. Do not compare
only the scorecard columns, take absolute transforms, log-transform QI, average
errors, or discard an inconvenient metric.

This is a prospective high-precision compatibility convention: one part per
million away from zero and an absolute floor near zero. It is not a measured
discretization uncertainty or an acceptance tolerance. It was chosen after stored
labels were available but before any new sampled forward-model result. No
fallback tolerance, replacement sample or result-driven second protocol applies.

All 36 comparisons must pass for an overall agreement. Report stored/computed
values, signed and absolute differences, limits and individual verdicts. Missing,
nonfinite, incomplete, invalid or unstarted rows prevent an overall pass and remain
visible. Stop new calls on software/solver failure; a completed numerical mismatch
does not justify replacing a row or stopping observation of the remaining fixed rows.

## Frozen pipeline and remaining execution gates

Scorer revision `32fe8ecd198a8615549b1086bca37682290f4e57`, file SHA-256
`1b394999a89891c84329e406ed8a80a3849c56151bb922ec291a86d73cf749d6`,
is unchanged. Use the JSON's recovered runtime versions, default settings and
effective VMEC grid (25/51/99 surfaces, final 10/10 modes). Preserve the recorded
booz-xform 0.1.0 override of the declared 0.0.9 dependency; do not repair packages.
Normalize R00 to one with the existing scorer; preserve
`m*theta-(n*nfp)*phi`, without a theta flip. Historical normalization is unknown.

Run `scripts/compare_seeded_constellaration.py --help` for byte-bound protocol and
report inputs on POSIX systems (macOS/Linux). The comparator imports the scorer,
whose `resource` import is unavailable on Windows; Windows public CI does not
exercise this command. The comparator rechecks identity, finite metrics, runtime, settings,
VMEC convergence and the scorer's unchanged `1e-10*R00` geometry gate. It does not
run a model. The scorer's settings field is a repr fallback; the final native
launcher must separately capture and verify every effective VMEC settings object
against the JSON. The model-free
[`capture_row_settings`](../../scripts/capture_seeded_vmec_settings.py) helper
requires exactly one settings factory call per row, preserves the actual settings,
and compares every field and JSON type before returning the settings to the solver.
It restores the original factory on success or failure. Synthetic tests cover all
three rows. The model-free [`run_rows`](../../scripts/run_seeded_constellaration.py)
workflow integrates that helper with serial scorer calls and the unchanged
comparator. It binds all inputs before starting, restores the scorer arguments,
retains partial reports and all three row statuses, stops on execution/validation
failure, and continues after a valid numerical mismatch. Its required live-check
callback runs before and after each call; a separate supervisor must enforce
limits during blocking calls. It has no executable CLI or resource authorization.
Synthetic scorer tests exercise this integration, not native execution. The final
launcher must bind it and supply the live checks and supervisor. Official benchmark
outputs remain unchanged diagnostics.

The workspace-specific launcher is local tooling, outside the public scripts and
core CI. Its [pre-run source and input/support snapshot](https://github.com/patrickmahlstein/nuclear-fusion-at-home/tree/4df7fde2c2c2a1641cb6f4b6957c50fa25f67b4e/evidence/seeded-native-protocol-v1)
preserves the reviewed runtime/input manifest and exact support bytes, with their
provenance and limitations. The corrected annotated tag in the contributor’s fork is
`evidence-seeded-native-protocol-v2-2026-10-26`; the earlier v1 tag is preserved and
its packaging error documented there. Neither tag is in the upstream repository.
These are reproduction artifacts, not a
requirement to use the contributor's private agent coordination. Other launchers
may use the workflow's documented `check_ready` callback and supply their own
resource supervisor. No native result or execution permission follows from this
snapshot; the local launcher's relocation requires a new path-binding freeze.

Before execution, publish the final hash-bound launcher/task and full runtime/input
manifest. The comparison freeze and PR review do not grant native execution.
Require an explicit current task-specific peer window, controller-owned single-worker
lock, empty process inventory refreshed within 60 seconds, and no STOP. Expired
grants and a general “lane free” note are insufficient. Limits: 1800 seconds total,
child at most 1740 seconds, one thread, 100 MiB output, 3 GiB initial/2 GiB live disk
reserve. Check both UTC and monotonic elapsed time, reject late completion and stop
at the confirmed resource-window end. Preserve all partial outputs.

## Interpretation

The #112 decision is whether the three seeded controls can be recorded as agreeing
with stored labels under this precise compatibility criterion. Agreement fills that
limited scorecard item. A mismatch records failed prospective compatibility and
leaves stored-label reproduction unqualified; a software or solver failure records
an incomplete control instead. Neither outcome blocks descriptive plasma scoring
or supplies a reason to optimize, retry, change tolerance or declare infeasibility.
The strict criterion may fail across runtime stacks; this experiment does not
estimate cross-platform error or choose a more permissive tolerance afterward.

Agreement supports only these rows under this criterion. Historical producer
source, environment and fidelity remain unknown, so neither agreement nor mismatch
identifies their producer. A failed prospective comparison can be reported without
attributing a scorer defect or declaring a plasma physically infeasible. This
does not qualify the scorer globally, freeze #113 requirements, change acceptance
gates, or repeat the completed registered controls, radial study, closed pilot or N21.
