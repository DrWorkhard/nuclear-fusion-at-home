# Current verification

4 October 2026. Lightweight contributor setup, based on `70f8905`.
No runtime, evaluator, root README or scientific-result changes.
[Quickstart](../validation/PUBLIC_QUICKSTART.md#download-only-current-main) ·
[Archive procedure](../validation/REPRODUCING_RESULTS.md) · [Status](../STATUS.md)

A fresh public HTTPS clone with depth 1, main only and no tags downloaded a
228,000-byte Git pack and checked out 106 files totaling 784,750 bytes.
Git metadata file content totaled 269,437 bytes, including that pack; protocol
and filesystem overhead are additional. The clone contains exactly one commit,
no tags, and persistent main-only/no-tags fetch configuration. Historical
payloads and ignored local raw runs are absent. Measurements describe the base
revision; documentation changes alter the exact bytes.

| Check | Result |
| --- | --- |
| Public tests in the shallow clone | 60 passed with an empty environment |
| Documentation and maintenance tests with the proposed changes | 40 passed |
| Docs, Ruff, `git diff --check` | Pass |
| Root README and runtime diff | Unchanged |
| CI checkout settings | Explicit depth 1 / no tags; pushes run for branches, not archive tags |
| Hosted CI | Required on the pushed commit before protected main advances |

Tests used an existing disposable core environment; the native environment was
not synchronized. No additional research regression is needed for onboarding
and checkout settings. Contributors can create branches/commits and open PRs
without downloading historical evidence. A deliberately deepened clone or
explicit archive fetch can still download old data; a full clone remains full.

The preceding archive migration's hash checks and native-input verification are
recorded at [70f8905](https://github.com/DrWorkhard/nuclear-fusion-at-home/blob/70f8905fcfabe550eb2825e48bc7a62e8192af27/docs/logbook/VALIDATION_LOG.md).
Its seven hosted checks passed on main. Archive identities and protections are
unchanged. Raw local outputs remain intact. This owner-requested change uses
the documented sole-maintainer review exception after required CI passes.
