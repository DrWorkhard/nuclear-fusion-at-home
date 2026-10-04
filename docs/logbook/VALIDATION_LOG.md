# Current verification

4 October 2026. Base `8c5753c`; history retains earlier checks.

Deleted eight completed result pages and two retired drivers (sampled geometry
audit and starter exporter). [Status](../STATUS.md) and the
[step index](../steps/README.md) retain conclusions, limits and evidence links;
[reproduction](../validation/REPRODUCING_RESULTS.md) locates full historical methods.
Optimization/step documentation falls from 6,820 words to about 1,340.

| Check | Result |
| --- | --- |
| `python -I -S scripts/test_public.py` | 57 passed |
| Documentation and release-maintenance tests | 40 passed |
| `scripts/check_docs.py`, Ruff, `git diff --check` | Pass |
| `python -I -S scripts/verify_public_release.py --output results/minimal-results-20261004` | All 8 copied-tree operations pass; physical admission false |
| Real native intake | Five snapshots, both target grids and 76 source identities pass |
| Longer-fit / headroom manifests | All 82 / 91 source hashes unchanged |
| Root README, evaluators, evidence, candidate JSON and raw artifacts | Unchanged |

The previous pass's 412-test native regression and fresh-clone core CI passed at
`8c5753c`; this pass does not change their retained code/dependencies and did not
repeat broad regression. No native environment sync, optimization or new physics
claim. These local checks do not establish new hosted/Windows results, external
review or independent scientific reproduction. Fetched main remains the ancestor
of the local cleanup commits; the previously passing hosted jobs cover that base.
[Historical release evidence](../validation/PUBLIC_RELEASE_RESULTS.md) ·
[Review/hosting policy](../validation/REVIEW_POLICY.md).
