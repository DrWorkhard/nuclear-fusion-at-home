# Proposed plasma-requirements calibration protocol

Preregistered 15 October 2026 for issue #113; prepares owner input, does not adopt
or freeze requirements. Base `ed72af9ad4e19633ca280f8bb364893f8822fc87`.

Decision: are the proposed hard bounds jointly attainable among comparable
ConStellaration dataset designs? Use the published vacuum/default metric table,
pin its revision and file hashes before reading outcome columns. No equilibria,
optimization, boundary-payload collection or requirements changes.

## Frozen analysis

Include every published row with finite numeric field-period count exactly 2 and
finite aspect ratio in the closed interval [9, 11]. Report total rows, malformed
and missing selection fields, selected rows and distinct boundary IDs if supplied.
Do not silently deduplicate: report duplicate IDs and conflicting metric rows;
if repeated boundaries exist, also report a unique-boundary sensitivity analysis
using only IDs with identical required metrics. These are dataset prevalence
statistics, not independent-family probabilities or confidence intervals.

Hard bounds, inclusive: vacuum well >= 0; bad-curvature flux compression <= 0.9;
log10 QI residual <= -4; edge rotational transform per field period >= 0.25;
edge mirror ratio <= 0.25. Confirm schema definitions before calculation: convert
raw positive QI residual by log10 only when documented; zero residual passes the
QI upper bound but is counted explicitly; negatives and nonfinite values are
invalid. Never take absolute transform unless the upstream metric defines it.
Do not add elongation or aspect-ratio <= 10 as hard bounds.

Report each hard-bound pass fraction over the entire selected population and
over rows with that metric valid. Unknown/failed/nonfinite metrics cannot pass.
Report joint pass count over the entire selected population and over complete
valid rows. Keep solver/error flags visible; flagged failures cannot jointly pass.
Absent flags are unknown rather than verified solver success. List column
mapping, units, producer/fidelity metadata and missing fields before interpreting
comparability with #112. Missing required columns block a joint-calibration claim.

Flag any marginal or joint pass fraction strictly below 1% as rare; flag zero
passes separately. This is an owner-attention rule, not a bound adjustment.
For joint passes, report normalized minimum L-gradient-B and maximum elongation:
valid/missing counts, minimum, 5th/25th/50th/75th/95th percentiles and maximum.
Use linear interpolation at (N-1)*p; empty populations produce null summaries.
Report overall selected distributions too for context. No adaptive subpopulation,
threshold, rarity rule or exclusion changes after inspecting outcomes.

## Limits and outputs

One metadata inspection plus one analysis and one deterministic replay; at most
60 minutes active work, 128 MiB input transfer, 20 MiB generated output, one
thread, 3 GiB initial / 2 GiB live disk reserve. Stop downloads at the ceiling;
inspect sizes first. Reuse cached immutable data only after identity validation.
No execution of fetched code. Preserve failed checks and original evidence.

Produce one short result page with exact code/data identities, commands, counts,
missingness, distributions and limitations. Stored labels remain conditional on
#112 scorer controls and resolution qualification. Dataset selection bias and
ancestry prevent general feasibility claims. The owner alone approves/freezes
`plasma-requirements-v1`; no optimization may use this draft as an adopted gate.

Schema clarification before outcome access: pinned dataset revision
`8da71572eb63ce93e77ce89bec0d7c30b7eba89e` has three default vacuum shards,
182,222 rows in its card (not the older approximate 158,000). Use `metrics.*`,
`boundary.n_field_periods`, `plasma_config_id` and all five `misc.has_*_error`
columns. QI is raw, so compare valid nonnegative values to 1e-4 (equivalent to
the frozen log bound). Upstream `problems.py` at
`d083b75b79386e95a3490a75b1498ad0958d9da8` explicitly takes absolute edge
transform; apply that convention and report signed-negative counts. Use exact
proposed bounds, without upstream's 1% feasibility tolerance. Any true error
flag excludes a joint pass; missing/nonboolean flags also exclude it. Report
per-flag counts so upstream-generation failures remain distinguishable from
forward-model failures. No outcome metrics have been read at this clarification.
