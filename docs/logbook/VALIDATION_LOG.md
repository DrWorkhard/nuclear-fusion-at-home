# Current verification

4 October 2026. Base `8581b1b`; original scientific results are unchanged.
[Scope and counts](../review/ACTIVE_SCOPE.md) · [Research command](../optimization/README.md)

Question: can one explicit-snapshot fitter replace the chain of completed studies
without changing its objective or checks? Inputs: the saved headroom-v3 snapshot
and trusted reference401 archives. The extraction removes historical orchestration,
not acceptance thresholds. New searches have wall-clock/storage bounds instead
of inherited coefficient boxes and bundle caps; they are prospective experiments.

| Check | Result |
| --- | --- |
| Native regression, one thread | 210 passed |
| `python -I -S scripts/test_public.py` | 57 passed |
| `scripts/check_docs.py`, Ruff, `git diff --check` | Pass |
| Old/new native objective comparison | Exactly equal values, all 198 gradient components and all metrics at two points |
| New driver: 5 s search + 120 s check budget | Completed in 21.66 s; startup passes, 18 completed bundles, two fine grids, scoped geometry pass, three interior grids; source hashes unchanged |
| Fresh-clone core checks | Pass: 57 public tests, 40 maintenance tests, docs and Ruff |
| Fresh-clone portable release | All 8 copied-tree operations pass with isolated Python 3.12 |
| Hosted CI | Required on the pushed commit before updating protected main |
| Root README, evidence, public candidate JSON, previous raw runs, native environment | Unchanged |

Comparison: `results/coil-fit-refactor-20261004/compare_models.py` runs the old model
from an exported `8581b1b` tree and the new model on the same snapshot, then at
`x + 1e-6*sin(arange(198)+1)`. Inputs, outputs and hashes remain in that ignored
results directory. End-to-end output is retained at
`artifacts/coil-fit-refactor-smoke-20261004`; reproduce with the documented command
and `--seconds 5 --check-seconds 120` into a fresh directory. This bounded run tests
software integration, not optimizer performance or a new scientific improvement.

Fresh-clone checks ran at `3b4e63b`; the only subsequent edit updates this record.
The first release invocation selected macOS Python 3.9 and failed the documented
minimum-version requirement; that output remains retained. Repeating with the
clone’s Python 3.12 passed.

Conclusion: the extracted objective agrees at the tested points, and the active
workflow executes independently of old study runners. This is not an exhaustive
proof of equivalence. No physical admission, improved-target benefit transfer,
external review or separate-machine native reproduction is claimed. CI must use
a disposable checkout; no native environment sync was performed.
