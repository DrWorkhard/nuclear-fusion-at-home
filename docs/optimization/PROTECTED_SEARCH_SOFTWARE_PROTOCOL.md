# Protected-search software qualification

Registered 24 September 2026, before new tests or numerical search. This closes
only the pure search-controller gate for the paused
[field-fit draft](PROTECTED_COIL_FIT_PROTOCOL.md). It is not authorization to run
the eight-cell native pilot or evidence of a better coil design.

## Scope and fixed policy

Qualify `src/fusion_baselines/protected_coil_search.py` using synthetic callbacks
only. Preserve the draft's two classes (n6/M5, n8/M7), 90/120 active coordinates,
P=(1+m²)^−2 for m≤2 and zero otherwise, D0-normalized −Pg direction, 1 mm initial
step, 16 halvings, Armijo coefficient 1e-4, 500 kA current limit, 116 proposals
and 20 field trials. Initial evaluation is supplied externally and is not charged
as a trial. Search selection is the earliest minimum among accepted states and
the initial seed; high modes retain their original float64 bits.

For the draft FD helper, k is the zero-based **full canonical coordinate index**:
sin(k+1) or cos(k+1), then multiply by sqrt(P), zero inactive entries, Euclidean
normalize. This makes the existing implementation's meaning explicit before a
native experiment. A future registered native protocol must use that same definition
or explicitly supersede the unrun draft; there is no prior search to reinterpret.

## Required controls

1. Both classes: independent loop-based weights/directions, normalized D0, descent,
   preserved high modes, deterministic repeats and immutable callback arguments.
2. Separate geometric rejection, current rejection and Armijo rejection. Every
   certificate must refer to the original seed, not the last accepted state.
3. All terminal reasons: null active direction, geometry/field budget, certificate
   limitation and failed line search. An algorithmic stop is not convergence.
4. Reservations precede callback work. Count attempted work even when it fails;
   `*_completed` means a returned result passed its schema/numerical validation.
   Malformed returns must not be labelled completed. Never spend after a recording
   failure; preserve successful prior events, including when final publication fails.
5. Reject malformed shapes/types, nonfinite scalars/gradients/certificates, changed
   evaluator coordinates and native/certificate/recording exceptions. Persist
   accurate failure-stage/counter diagnostics when recording is still possible.
6. Build a separate completed-trajectory auditor that does not import/call the
   producer. Reconstruct proposals, direction normalization, backtracking, exact
   physical current decisions, acceptance, selection, counters and event ordering.
   Mutating any of these must fail audit. Auditor work is separate from construction.

Independent floating-point reconstruction uses relative tolerance 5e-12 or
absolute tolerance 1e-12 for numerical policy values only. Schemas, coordinate
identity between records, budgets, current gate, recorded Armijo comparison,
acceptance flags, ordering, selection and inactive-coordinate bits are exact.
The auditor must check that stored numerical values agree with reconstruction
before using them for the exact recorded decision. No tolerance extends a
physical field/geometry threshold.

## Explicit limits and closure

The trajectory audit verifies control flow using stored evaluations and certificate
decisions. It does **not** independently recompute fields, gradients or geometry,
prove source identity, qualify real coil inputs, or accept a physical design.
Its output must state these exclusions. A fabricated internally consistent trace
is not scientific evidence without the later source/array/certificate audits.

Retain initial failures; correct implementation defects without changing this
policy. Run targeted adversarial tests, public controls, documentation/Ruff checks
and full native regression before declaring the controller qualified. Commit the
implementation and exact test outcomes; record source hashes and qualification
limits. No new field/equilibrium solve, optimizer comparison, installation or
external repository change belongs to this phase.

Next gates remain: independent method review, source-bound runner, independently
recomputed physical diagnostics and finer-grid candidate acceptance. The old
field-fit draft remains unqualified for native execution until those gates pass.
