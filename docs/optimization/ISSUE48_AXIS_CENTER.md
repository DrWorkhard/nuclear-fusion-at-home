# The periodic-center correction does not remove the saved reversals

**Decision: target-axis miscentering is not sufficient to explain this failure.**
The [continuation recurrence diagnosis](ISSUE48_CONTINUATION_RECURRENCE.md)
persists when angles are measured about a numerically resolved local periodic
field-line center. Each of the failed launch's eleven residue sequences still
reverses once on both section planes; all four qualifying controls still have
zero reversals. No contour was requalified or flux label recomputed.

| Frozen field | Center shift from target (mm) | Refined R at phi=0 (m) |
| --- | ---: | ---: |
| Continuation | 0.256506 | 0.934286044137 |
| Original reference401 fit | 0.076997 | 0.934106534919 |

The failed launch's pooled angular gap changes from **1.240256 to 1.247492 rad**;
the four controls remain below 0.072 rad. The two resolutions agree on each center
within 2.5e-15 m, with return residuals below 8.7e-15 m. These floating-point
agreements are numerical observations, not error bounds or physical accuracy.
Independent filament fields at nine orbit samples agree with the native field
to at most 3.51e-16 using the scale max(1,|B|).

The prospective test fixes the continuation and original reference snapshots,
five saved launches, 640 pooled crossings, eleven residue classes and existing
1e-8-rad resolved-step cutoff. Direct one-period R,Z maps use 512/1024 coil nodes,
DOP853 and independently initialized local roots within a fixed 2 cm neighborhood.
The finer center is used on equivalent phi=0/pi planes. No long trajectory,
equilibrium solve, optimizer, acceptance gate or original current was changed.
Periodic fixed points do not establish axis uniqueness/stability, islands,
nestedness or confinement. The continuation remains unqualified at 19/20.

Clean successful producer/evaluator:
`5a0d06303a2d0405f52e0f179176bc2ada532536`. One numerical attempt completed in
6.777 s supervised total, within 240 s inside the driver / 270 s including
imports and finalization. One thread, 256 MiB, 3/2 GiB reserves and 5 s clock
tolerance. Source/input identities and 1,662 native package files matched
before/after; owned-process cleanup passed. Analytic controls are pre-run tests.
The earlier 1.700 s attempt at `daff62fbce104b7d48b0210be1f899a69f49bc33`
failed during import, before field calculations. Its traceback is preserved;
only import availability/cache settings changed before the numerical attempt.

Published archive: `039a0a71c9d0e2345b1ddcae6524eb6bae7bcc42`, annotated tag
[evidence-issue48-axis-center-v1](https://github.com/DrWorkhard/nuclear-fusion-at-home/tree/evidence-issue48-axis-center-v1); published; remote identities and manifest retrieval verified.
Manifest SHA256:
`22b915308a8beb37dfafe406a89f28cb1d9dab476467887edf8f4d0c5bfafc86`.
The snapshot preserves both attempts, code/protocol/tests, exact consumed input
subsets, environment identity, commands and arithmetic replay. The native
environment is external; no Wout is needed. Original raw output directories
`/private/tmp/issue48-axis-center-v1` and `...-v2` remain intact.

Replay verifies 41 payload files and both attempts' source bindings, then uses
stored centers and the same NumPy kernels to reproduce five cases and 220 residue
sequences. It does not repeat the root solve, native fields, long tracing or timing.
This narrows a reconstruction question; it does not justify a transfer claim.
