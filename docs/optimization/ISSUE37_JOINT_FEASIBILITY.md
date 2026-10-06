# Joint plasma/coil feasibility protocol v1

Prospective, 7 October 2026; **not executed and not a confirmatory protocol**.
[Issue #37](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/37) ·
[Machine-readable settings](ISSUE37_JOINT_FEASIBILITY.json).
The [coil-freedom result](ISSUE53_COIL_FREEDOM.md) selects this next question:
can a small plasma-boundary change preserve ideal-target physics while remaining
tractable for the same practical coils? A bounded feasibility screen precedes
any larger optimizer or claim of realized-field benefit.

## Frozen comparison

C fits the original reference401 target. J polls exactly two perturbations:
`rbc(m=2,n=1)` +1 mm then −1 mm about the original boundary. This is a named
physical Fourier coefficient in metres;
all other input values stay fixed. Every fit starts from the identical original
length-headroom seed, using six order-5 coils. No cross-arm warm starts, adaptive
polls or retries. The JSON pins input, original Wout and seed hashes; the Wout is
local-only. Regenerated inputs would require a new protocol version.

Keep `rbc(0,0)=1 m`, nfp=2, stellarator symmetry, vacuum pressure/current and edge
flux fixed. Reject volume changes above 0.1% from the original boundary; compare
128²/256² full-torus midpoint quadratures to 1e-6 relative agreement before solving. No global
rescaling. Volume is the absolute divergence-theorem surface integral of
`x dot (x_theta cross x_phi)/3` over both angles. Keep signed coil flux and the
reference B² diagnostic scale fixed; report changed target B² separately.
Engineering penalties and acceptance limits remain unchanged.

The outer plasma objective is the complete ideal-target action-variance score
on the original five surfaces and seven fixed bounce fields. The inner coil fit
minimizes its existing local SquaredFlux/area plus its separate geometry penalty.
Retain each term and every failed well. Choose J's lowest complete plasma score
among nonzero proposals with an eligible inner-fit candidate; break ties by inner
objective, then proposal order. Freeze target, Wout, coils and normalized currents
before diagnostics. No fallback selected using validation results.

## Cost, checks and decision

Run C then J, one native thread, **1800 s search + 900 s total diagnostics per arm**.
Start each J inner fit only with 300 s search time remaining; cap it at 300 s.
A normal inner-fit cap (or C's declared search cap) retains an earlier eligible
candidate after passing startup; late trials cannot win. An interrupted whole-arm
budget does not complete an unfinished J proposal. Two solves at
the documented approximate six-minute regeneration scale plus ten minutes of
fitting fit this planning envelope; perturbed-target runtime remains unmeasured.
Intake, volume,
all equilibrium solves, reconstruction and scoring consume the search budget;
failed work is charged. Both arms have 256 MiB total output and 3/2 GiB initial/live
disk reserves. Enforce both wall and monotonic deadlines; clock disagreement
above 5 s makes the comparison incomplete. No sleep allowance or budget reset.

Use the existing fine field, continuous geometry, interior and independent B/A
checks, plus ten direct 200-turn traces. Ideal-action validation uses 32 withheld
half-shifted phases and 1601/3201 toroidal samples, with 0.1% score convergence;
these are withheld samples, not unseen devices. Both J proposals must finish
or be explicitly rejected within budget, and the selected pair must finish checks.
Continue only if geometry/current checks pass, J improves ideal validation score
by at least 1% at both resolutions, its own-target boundary/interior RMS are at
most 10% worse than C's, and all direct traces complete. For this screen, boundary
RMS is the maximum of both fine shifts; interior RMS uses the finest 64/512 level.
Report every coarser level as well. This is a feasibility
screen; cross-target field ratios do not measure a common physics improvement.
Report maximum normal error against its unchanged limit too. Both proposals
explicitly rejected, or a complete selected pair failing the screens, changes this
bounded recipe. A missing C candidate, interrupted proposal or incomplete selected
pair is inconclusive; resource interruption never counts as numerical rejection. Neither verdict establishes a general limit on joint optimization.

## Execution and scientific blockers

Execution stays disabled until a reviewed implementation/dependency state is
frozen. The JSON names existing methods and the prepared typed-trial follow-up;
it does not claim a runnable joint optimizer. New targets require a separately
reviewed intake and independent verifier. Never disable or impersonate the
hash-bound reference401/selected401 checks to admit a perturbed target.

The future common endpoint is actual-coil action variance over all five **realized**
flux surfaces, seven fixed bounce fields and both period families, with a 10%
meaningful-improvement hurdle. It is **blocked and must be reported null**:
[launch matching](ISSUE48_MATCHED_LAUNCHES.md) does not yet supply qualified common
flux/phase coordinates, and the wide well domain is incomplete. Before new
confirmatory candidates, a separate protocol must freeze qualified mappings,
refinement, holdouts and an error budget. Never drop failed cells or substitute
nominal target labels. Even a successful feasibility screen only advances endpoint
qualification; it authorizes no larger search or physical acceptance.
