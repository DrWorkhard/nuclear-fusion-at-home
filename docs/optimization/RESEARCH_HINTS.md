# Research hints — invitations, not requirements

Updated 27 September 2026. Unsolicited ideas, replications and negative results
are welcome; compute-cost disclosure is optional. A useful contribution need not
produce a best score. [Contributing](../../CONTRIBUTING.md) · [Status](../STATUS.md)

## Accessible starting points

- Reproduce the [public starter](../validation/PUBLIC_QUICKSTART.md) on another
  system. Report the exact revision, commands, results and limits.
- Submit a small candidate change with both sampled errors and a replay. Sparse
  scores are exploratory; exposing a sampling failure is valuable too.
  The [lower-error six-coil candidate](../../submissions/length-headroom-six-coil/README.md)
  is available without native research artifacts.
- Improve field kernels or contributor diagnostics with tests. Preserve units,
  signs and named mappings; speed claims need measured timing comparisons.

## Current research priorities

- **Map the working fit's trade-offs.** Use the
  [normalized fitting tools](README.md) for longer searches, wider shape freedom
  and separately labelled coil families. Report field error versus clearance
  and curvature, with current/flux conventions held explicit.
- **Check stopping and conditioning.** The expanded headroom fit stops on
  objective change, away from coefficient bounds and above its gradient target.
  Test scaling/preconditioning with the same physical objective and checks;
  do not assume that a solver success flag proves an optimum.
- **Try to break the promising candidate.** Check interior fields, magnetic
  surfaces and whether the plasma-target benefit survives. A low boundary error
  alone does not answer these questions.
- **Make the result reproducible elsewhere.** Work toward portable full-grid
  data and community evaluation. Assess existing benchmarks before inventing
  infrastructure. The [programme](STEP4_RESEARCH_PROGRAMME.md) owns this work;
  the current sparse starter is not that full challenge.
- **Propose another direction.** Explain its relevance and how it could be
  checked. The six-coil public format and these priorities are not an allowlist.

Detailed pressure/engineering work is deferred in the current programme, not
excluded from contributions. Keep evidence proportional to the claim. Do not
improve a score by weakening the field normalization, dropping difficult cases
or changing the verifier alongside the candidate. Historical failures remain
available through the [freeze tag](../validation/REPRODUCING_RESULTS.md).
