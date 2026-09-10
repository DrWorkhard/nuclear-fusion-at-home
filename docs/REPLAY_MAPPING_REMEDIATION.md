# Runtime DOF ordering: failed replay and scoped remediation — 2026-09-10

The unmodified replay failed: initial residuals matched, but best-point flux
residual became 92.3119 instead of 0.0211731, and coil positions differed by up
to 1.65093 device m. Evidence `guarded-feasibility-v1-replay.json` is retained.
Its best-point spectrum/gradient belongs to the **wrong reordered geometry** and
must not be used as a diagnostic of the actual candidate.

Cause found in pinned SIMSOPT `_core/optimizable.py`: ancestor ordering uses
object names, which include runtime instance numbers. Loading a field before
creating the replay context changes promoted curve names from 5/6/7/8 to
9/10/11/12. Lexical ordering places curve9 last. A global numeric array without
an explicit object mapping therefore assigns its blocks to different coils.
NamedVectorBackend correctly maps local gradients *within* a context; it does
not by itself make global arrays portable *between* contexts.

Before a remediated replay, implement and test a complete explicit permutation:

1. Read the stored SIMSON graph without instantiating it. Recover every saved
   global name's free DOF value; require exact equality to archived best.x.
2. Map original and new curve/current owners by the first four physical coil
   graph entries, not numerical or alphabetical name order. Follow ScaledCurrent
   to its underlying Current; reject unsupported expressions.
3. Require a bijection of all 207 free DOFs; preserve local parameter labels.
4. Apply the permutation to saved x and the canonical seed-44 direction. Require
   the inverse-mapped original point's SHA-256 to match its original ledger hash.
5. Re-run the original residual, field/current/regularization and gradient tests
   without changing tolerances. Keep eight full bundles and new immutable outputs.

Analytical tests cover the 9-to-10 lexical boundary, inverse permutation,
duplicates/missing names, fixed/nonfinite parameters and cyclic current references.
This changes only replay mapping, never search settings, source best arrays,
serialized candidate or the failed flux verdict. The prior direct serialized-field
holdout does not insert raw arrays into a new global context and is unaffected.
Future array-based warm starts must use an equally explicit mapping.
