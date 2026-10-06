# Public release evidence

Software portability is not physical acceptance. Usage and metric conventions
live in the [quickstart](PUBLIC_QUICKSTART.md); latest checks live in
[current verification](../logbook/VALIDATION_LOG.md).

| Qualification | Source / evidence | Scope |
| --- | --- | --- |
| Hosted launch | `557a106`; [core](https://github.com/DrWorkhard/nuclear-fusion-at-home/actions/runs/36976443061), [portable](https://github.com/DrWorkhard/nuclear-fusion-at-home/actions/runs/36976443009) | Linux/macOS/Windows × Python 3.11/3.14; exact tested commit integrated |
| Initial hosted release | `631434c`; [core](https://github.com/DrWorkhard/nuclear-fusion-at-home/actions/runs/36971892980), [portable](https://github.com/DrWorkhard/nuclear-fusion-at-home/actions/runs/36971892966) | All six public combinations pass |
| Local multi-Python | `0d9abcf`; [readme-review-v1](https://github.com/DrWorkhard/nuclear-fusion-at-home/blob/68db098b664bb072854b687040e103aaafee463c/evidence/readme-review-v1.json) | Python 3.11/3.12/3.14 on one Mac; public tests and eight copied-tree checks pass |
| Core isolation | [public-review-v2](https://github.com/DrWorkhard/nuclear-fusion-at-home/blob/68db098b664bb072854b687040e103aaafee463c/evidence/public-review-v2.json) | Disposable dev-only environment; Windows encoding simulation is not a Windows run |
| Original export/evaluator | [Software](https://github.com/DrWorkhard/nuclear-fusion-at-home/blob/68db098b664bb072854b687040e103aaafee463c/evidence/public-layer-v1-software.json), [portability](https://github.com/DrWorkhard/nuclear-fusion-at-home/blob/68db098b664bb072854b687040e103aaafee463c/evidence/public-layer-v1-portability.json) | Isolated real-reference replay; native B/A disagreement 9.5879976e-16 versus 5e-10 tolerance |

A fresh anonymous clone of `6bda543` also passed the eight qualification operations
on macOS/Python 3.12.13. These records cover their stated revisions, not later HEAD.
[Contributor Ubuntu replay](SERVER_REPRODUCTION_20261002.md) is separate evidence.

The qualification operations exercise discovery, reference and changed-candidate
replay, forged-admission rejection, optional metadata and output preservation.
Replay uses the same evaluator; `physical_admission` remains false. The attributed
[public packet](../../examples/clear-coil-samples-v1/README.md) does not distribute
the complete native research data or establish confinement/buildability.

Retained failures include JSON-depth handling, frozen CI, disk reserves and a
stricter nonprotocol cross-Python byte comparison affected by last-bit rounding.
Final passes do not erase them or relax numerical tolerances. Full logs, methods
and historical test counts resolve through the evidence and
[reproduction guide](REPRODUCING_RESULTS.md). The [review policy](REVIEW_POLICY.md)
owns live protections and remaining rights/reproduction work.
