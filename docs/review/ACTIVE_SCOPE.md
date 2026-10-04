# What the current workflow actually needs

4 October 2026. [Plan](../PROJECT_PLAN.md) · [Scientific assessment](STRATEGIC_REVIEW_RESOLUTION.md)

The maintained runtime is **2,743 Python lines**: 1,996 for native research and
747 for public participation. The entire code footprint falls from 12,068 lines
at `8581b1b` to **6,003**, including tests and maintenance: **50.3% less**.
Counts include blank lines, comments and docstrings; they exclude dependencies,
data, generated output and Git history. This is a measured working implementation,
not proof of a mathematical minimum or sufficient software for a reactor.

| Retained responsibility | Lines | Why keep it? |
| --- | ---: | --- |
| Native fitting: driver, objective/search, sparse surface penalty | 647 | Propose coils with one method and explicit resource limits |
| Native target, field and geometry checks | 1,284 | Detect coordinate/current errors, misleading sampled geometry and failed physics limits |
| Run provenance | 65 | Know which code, inputs and machine produced an observation |
| Public runtime, including root CLI | 747 | Let contributors reproduce and modify candidates without native installation |
| Tests, native and public | 2,711 | Analytic controls, poisoned-input rejection, numerical identity and failure handling |
| Maintenance, packaging entry, publication checks and CI | 549 | Keep the contribution/review workflow reproducible and attributed |
| **All tracked Python, shell and YAML** | **6,003** | Runtime plus verification and collaboration |

## Decisions after questioning the scope

- **Delete:** nine chained experiment scripts, the completed submission runner,
  obsolete geometry/target-building modules, their study-specific tests, unused
  provenance helpers and the redundant installed CLI. No copied archive.
- **Keep:** independent calculations and acceptance controls even where their
  only current consumer is a test. They catch incorrect signs, scales, Stokes
  normalization and false geometry passes; merging them into the optimizer
  would remove an independent check. They do not constitute full acceptance.
- **Keep separate:** the dependency-free public evaluator and native fitter.
  Their currents and sampling differ; unifying their scores would be misleading.
- **Keep provisionally:** documentation/release/attribution checks. They are
  collaboration overhead, not physics. Add no new framework around them.
- **Keep as evidence:** candidate data, failures and raw outputs. Old producers
  belong at their exact Git revisions, not in the active import graph.
- **Do not build yet:** another optimizer family, custom equilibrium solver,
  distributed-compute platform or detailed engineering suite without a decision
  that requires it. Prefer existing scientific software.

## Workflows

**Research:** explicit snapshot → fixed target intake → derivative checks →
bounded fit → frozen-current fine fields and continuous geometry → short result.
Use the [single command](../optimization/README.md). Numerical completion and
physical acceptance are separate. The current driver still fits reference401 only.

**Contribution:** public case → named coefficient change → evaluate → dense
boundary diagnostic → replay/report → reviewed contribution. Public replay is
not an independent physics verdict. [Commands](../validation/PUBLIC_QUICKSTART.md).

**Confirmation:** preregister comparator/selection/holdouts → freeze candidates →
independent numerical and physics checks → retain failures → claim only the
supported scope. [Rules](../validation/RESEARCH_WORKFLOW.md).

**Delivery:** focused tests + public tests + docs + Ruff + diff check → fresh-clone
core/release checks → hosted CI → push the checked commit. Historical numerical
replay starts at the [producer revision](../validation/REPRODUCING_RESULTS.md).

The decisive missing work is matched improved-target input, realized magnetic
surfaces/benefit transfer, and an early reactor feasibility screen. Their necessary
code size is unknown; existing solver adapters should come before new frameworks.
The [24 October decision](../optimization/STEP4_RESEARCH_PROGRAMME.md) determines
whether further work on this recipe is justified.
