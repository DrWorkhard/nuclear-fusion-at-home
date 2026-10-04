# Current verification

Updated 4 October 2026. Historical checks remain in Git; numerical research
results are summarized in [status](../STATUS.md) and the linked experiment pages.

## Simplification and scientific focus

Base: `d5d395b`, equal to fetched `origin/main` before editing. Latest base runs
[core](https://github.com/DrWorkhard/nuclear-fusion-at-home/actions/runs/37192450027)
and [portable](https://github.com/DrWorkhard/nuclear-fusion-at-home/actions/runs/37192450038)
passed. These hosted results cover the base, not the local simplification.

- Removed two completed leaf experiment drivers and their tests, inactive
  VMEC++/NEO-JAX manifests, unused benchmark/engineering extras, and four
  superseded review/decision documents. Reproduction locations are in the
  [guide](../validation/REPRODUCING_RESULTS.md#later-completed-tools).
- Regenerated `uv.lock` offline with uv: 65 → 12 resolved packages. This is a
  smaller dependency declaration/lock, not a measured runtime speedup. Installed
  native environments and external checkouts were not synchronized or removed.
- Retained all acceptance mathematics and the fitter's imported/hash-bound
  dependency chain. The new programme changes prospective research priorities,
  not historical acceptance limits. No optimization or new physics experiment ran.

## Checks actually run

| Check | Result |
| --- | --- |
| Active native regression, four thread variables set to 1 | 412 passed in 25.51 s; 13 existing HiGHS-option warnings |
| Isolated public suite, Python 3.12.13 | 57 passed |
| Ruff, documentation structure and `git diff --check` | Pass |
| Core CI in disposable local clone with the proposed patch, `UV_OFFLINE=1 ./scripts/run_core_ci.sh` | Locked installation, Ruff, 57 public tests, docs and 40 maintenance tests pass |
| Copied-tree release check, `python -I -S scripts/verify_public_release.py --output results/simplification-20261004` | All 8 operations pass; physical admission remains false |
| Real native input intake | Five snapshots and both interior grids load; 76 source identities verify |
| Saved longer-fit / headroom source manifests | All 82 / 91 source hashes still match |
| Root README and scientific inputs/evaluators/evidence | Unchanged against the base revision |

The disposable clone used Python 3.12.13 on this Mac and required no ignored
research artifacts. This is fresh-checkout software reproduction on the same
machine, not independent scientific reproduction. No new Windows/hosted run,
external expert review, backup/restore qualification or accepted coil design is
claimed. The native suite validates the retained software; it does not execute
the proposed matched-target or reactor-feasibility study.

The [public release record](../validation/PUBLIC_RELEASE_RESULTS.md) owns historical
release evidence; the [review policy](../validation/REVIEW_POLICY.md) owns hosting
protections and remaining rights/reproduction work. A contributor's
[Ubuntu replay](../validation/SERVER_REPRODUCTION_20261002.md) is separate portability
evidence. Raw research artifacts and failed runs remain retained locally; Git does
not back them up.
