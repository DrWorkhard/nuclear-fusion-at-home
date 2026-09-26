# Local curvature implementation and qualification

26 September 2026. [Protocol](LOCAL_CURVATURE_PROTOCOL.md) ·
[Method/input review](LOCAL_CURVATURE_REVIEW.md) · [Index](README.md)

## Current scope

Implementation and internal review are complete after registration at `111d992`;
full regression and the separate execution checkpoint remain required. **The twelve
fixed project states have not been evaluated with the new bound.** No old
certificate, evaluator or acceptance threshold has changed. Step 4 remains open.

The components are separate:

- `local_curvature.py`: constructs padded whole-homotopy bounds and a complete
  dyadic subdivision tree, with fixed depth, work and time limits.
- `local_curvature_audit.py`: independently written scalar arithmetic and
  complete-tree checker; it does not import the producer.
- `run_local_curvature.py`: binds original named coefficients and geometry
  proofs, preserves every physical copy, supervises phases and publishes reports.

The producer has 108 passing synthetic tests. The checker has 49 analytical and
adversarial controls plus nine producer/checker cross-tests, all passing. The
runner has 61 passing controls, including real subprocesses with synthetic data. Tests
include circles, transformations, collapse and excessive curvature inside a path,
between-node high modes, nonfinite arithmetic, exact thresholds, malformed
coverage, counter tampering and expired budgets. These counts do not yet include
the full research regression. The independent producer review additionally
checks 127 possible deadline cutoffs of a 63-bound circle; every saved result
retains a complete, correctly counted negative tree.

Main's combined run passes all **227 focused tests** (2.95 s), 47 public tests
(3.206 s) and 16 documentation/release tests (15.00 s). Full-repository Ruff,
documentation structure, source-only intake and whitespace checks pass. The
[implementation review record](../../evidence/local-curvature-implementation-review-v1.json)
binds 12 sources and 19 artifacts, including failing controls. Main separately
confirms that all six independently reviewed intake/gate function ASTs remain
unchanged by the final publication fixes.

## Retained corrections

An independent checker review found that absolute comparison tolerance could
accept a falsified zero curvature bound when the independently computed bound
was tiny. The failing control is retained in `audit-zero-red.xml`; the correction
requires strictly positive reported and reconstructed bounds before acceptance.
All 49 controls then pass. This was a certificate-validation defect on a synthetic
large circle, not a discovered physical violation in a project design.

The checker also gained explicit nonnegative, nondecreasing clock validation.
The producer's first test run retained one incorrect expected-transpose assertion;
correcting that test expectation gives 108 passes. Lambda caching is tested
against fresh and mixed-order calls and preserves bitwise-identical bounds.

The runner now rejects falsely complete empty results and reconstructs the
expected physical-copy identities, publication prefix and shared byte counts.
Post-link timeouts retain the existing file instead of publishing a duplicate.
The independent intake reviewer found that Python's numeric/boolean equality
admitted `true` as version 1 and numeric 1 as a qualification flag; exact JSON
types are now required and three independent negative controls pass.

Main's final publication review reproduced two further failures before their
fixes (`runner-publication-red.xml`): a late parent could return a negative
in-memory result while its stored acknowledgement still said complete; and
directory persistence failure after linking a curve lost that published file
from the prefix and byte count. The runner now returns an explicit superseding
negative acknowledgement and retains/counts linked curves under failure, without
duplicating the scientific report. All 61 runner controls pass after correction.

## Source-only intake and remaining gates

The source-only intake checks all twelve saved identities without calculating a
new curvature bound. Independent intake checks all 12 states / 336 physical
copies and rehashes 56 references / 12,424,946 bytes with scientific imports
blocked. No old certificate or new bound is reconstructed in this check.
It is a local research entry
point requiring the retained artifacts, not part of the dependency-free starter:

```bash
.venv/bin/python scripts/run_local_curvature.py --intake
```

Before actual execution: finish combined focused/public/docs checks and a clean
full regression; commit implementation qualification and a
separate execution checkpoint. Then run the twelve states serially in fresh
outputs, with all negative and resource-limited outcomes retained. A tighter
geometric bound would still need a separately registered optimization experiment
to demonstrate useful field improvement.
