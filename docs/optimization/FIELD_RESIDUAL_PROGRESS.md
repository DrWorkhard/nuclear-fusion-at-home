# Saved-field residual diagnostic: preserved implementation checkpoint

26 September 2026. [Fixed exploratory protocol](FIELD_RESIDUAL_PROTOCOL.md) ·
[Index](README.md). No real-array residual analysis yet. Work paused for the
[strategic review response](../review/STRATEGIC_REVIEW_RESOLUTION.md); execution
closure and an independently reviewed actual result remain pending.
The unfinished code is preserved separately at `b01ea4c`; this is not an
execution qualification or a completed residual study.

## Implementation and scope

The NumPy producer (`field_residuals.py`) and separately authored stdlib
`math.fsum` checker (`field_residual_audit.py`) reconstruct both signed residual
spaces, their one-response projection and the exact numerator/denominator split.
The checker imports neither the producer nor the earlier metric implementation.
Both own their arithmetic and validate finite input, identities, conditioning
status and null fields. Invalid extreme arithmetic fails closed; they do not
promise identical representable ranges for every hypothetical binary64 input.

`scripts/analyze_field_residuals.py` follows the fixed result's explicit source
references to sixteen models and eight ordered grid pairs. It rehashes bounded
JSON/NPZ, binds state/seed/grid identities, checks complete matched points,
normals and weights, reconstructs saved endpoint scores and independently checks
every derived statistic. It records clean before/after code identities, validates
input bytes again, and returns an explicit index. No native model or optimizer.
The surrounding recorded launcher must enforce the separate 65 s hard timeout;
the worker checks its 60 s work deadline throughout input, arithmetic and output.

Fresh exclusive output is limited to 8 MiB; scientific writes must complete,
flush, sync and match their expected hash before acknowledgement. Limits and
source changes stop the run with retained prefixes. Existing array readers keep
their 64 MiB, finite numeric, no-pickle and uncompressed-size protections. This
is an offline diagnostic, not a replacement for the native physical verifier.

## Checks and failures retained before real-array work

- Producer controls cover analytical projections, weighting/signs, arbitrary
  normal magnitudes, uniform field scaling, nearzero/nextafter branches,
  zero control residual, input mutation and injected identity errors.
- Independent scalar controls also check strict result schemas, tampered scalars,
  booleans/nulls and shared synthetic examples with nonuniform fields/weights.
  The initial scalar test wrongly expected a representable `hypot` to overflow;
  its failed record and corrected test are retained.
- First integrated synthetic run: 22 pass, one failure. The two independently
  written components used different meanings for `delta_squared_norm`. It now
  consistently means `||rP||² - ||rC||²`, not `||rP-rC||²`; a direct counterexample
  test preserves the distinction. No actual field result informed this fix.
- Independent runner review finds and reproduces incomplete boundary-point
  shape/coverage acceptance. Exact `(N,3)` shapes and the full ordered eight-pair
  schedule are now mandatory. Guard checks after each array read and before
  arithmetic, short-write rejection and output rehashing are also tested.
- Actual metadata-only intake follows 28 references /16 models /8 comparisons
  with array loading and both numerical implementations replaced by rejecting
  sentinels. This confirms source wiring, not any new residual statistic.

These are internal reviews, not external peer review. All original field-study
sources, thresholds and evidence remain unchanged. The last complete native
research regression is the separately recorded 5,654-pass implementation; the
new saved-data modules are checked with scoped synthetic and integration tests.
The preserved implementation at `1c805af` passes all **190 focused tests** within
the combined 222-test documentation/release/residual check; Ruff also passes after
formatting corrections. Initial failed controls remain under
`artifacts/field-residual-v1/`; that combined check is under
`artifacts/strategic-review-v1/initial-checks.xml`. These component checks are not
completed execution qualification or a field diagnosis. The registered 65 s
external launcher, final execution review and real-array analysis remain pending.
