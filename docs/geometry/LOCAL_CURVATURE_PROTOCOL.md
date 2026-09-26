# Local homotopy curvature qualification: protocol v1

26 September 2026. Prospective registration; implementation and execution are
separate gates. No permission for a design search.
[Completed fine pilot](../optimization/PROTECTED_FINE_RESULTS.md) ·
[Method/input review](LOCAL_CURVATURE_REVIEW.md) · [Index](README.md)

## Scope and fixed inputs

Qualify a separate curvature component on the complete straight coefficient path
from the original seed to a candidate, with the unchanged 12/m threshold. Keep
the original producer/auditor, historical decisions and seven other geometry
gates unchanged. No fields, gradients, equilibria or optimization in this study.
These are padded analytical bounds in binary64, not rigorous interval proofs.

Freeze twelve inputs before using this component: original six/eight-coil seeds;
all eight coarse selections in their existing order; and one rejected state per
coil class. Use the reference-N case's final failed iteration and first trial
in recorded order whose old certificate fails only curvature. The
[fixed input manifest](../../evidence/local-curvature-inputs-v1.json) binds n6
trial 94 (iteration 17/backtrack 0) and n8 trial 50 (iteration 12/backtrack 0),
plus the other ten states. Manifest: 39,784 bytes, SHA-256
`ca9c3bac130080cb261660abf18d6de29872c58f7d305114b06ee061969beca5`.
Rejected inputs have complete named coefficients and old certificates, but no
field bundle, value or gradient; do not invent them. Input selection hashes every
read reference and verifies original names and exact saved coordinate bits.

Use every physical copy's actual recorded matrix, Q=M.T, never an ideal symmetry
substitute. Coefficients are [constant,sin1,cos1,...] for each Cartesian axis,
with period-one t and omega=2*pi*m. Input shape/order/name validation is mandatory.

## Exact-arithmetic inequality

For c(t,l)=s(t)+l*d(t), d=candidate-seed, take a rectangle with center(tc,lc),
halfwidths(h,r). Let A>=sup_R|c_tt|, J>=sup_R|c_ttt|, D1>=sup|d_t|,
D2>=sup|d_tt|. At its center v=c_t, a=c_tt:

    E = h*A + r*D1
    Vminus = |v|-E; Vplus = |v|+E
    Nplus = |v cross a| + h*Vplus*J + r*(D1*A + Vplus*D2)
    Kupper = Nplus/Vminus**3, when Vminus>0.

The partial derivatives of v cross a are v cross c_ttt and d_t cross a +
v cross d_tt. Integrating along an axis-aligned path proves this whole-rectangle
bound. Global Fourier bounds at the two l endpoints enclose A/J throughout
the rectangle by convexity. Endpoint curvature alone is insufficient.

## Reproducible floating-point padding

All inputs and arithmetic are finite binary64, with failures recorded as
uncertified. Define e=1024*2**-52; P(z...)=e*max(1,fsum(abs(z)...)),
U(z...)=fsum(z...)+P(z...), L(a,b...)=fsum(a,-b...)-P(a,b...).
No comparison tolerance relaxes 12/m. These specified pads are numerical safety
margins, not a proven enclosure of every platform's transcendental operations.

For each scalar transformed seed/candidate coefficient, compute the nominal
three-term dot product with fsum and attach P(each product) as its error.
For d=T-S, attach U(error_T,error_S,P(T,S)). For C=S+l*d, attach
U(error_S,l*error_d,P(S,l*d)). Constants also keep their errors, although all
derivative calculations omit mode zero. Do not infer d=0 from a small difference.

Define Bk(C,E), k=1,2,3: each mode/axis amplitude is
U(hypot(abs(C_s)+E_s,abs(C_c)+E_c)); its axis sum is
U(omega_m**k * amplitude_m for all m); the result is U(hypot(three axis sums)).
Use the nominal transformed coefficients plus errors, not bounds on ideal
rotation copies. Compute D1/D2 with d and its errors. At the two l endpoints
compute B2/B3 and take each maximum as A/J. These bounds are global in t.

Compute nominal center derivatives with explicit sine/cosine differentiation:
v=sum omega*(C_s*cos-C_c*sin), a=-sum omega**2*(C_s*sin+C_c*cos),
using fsum for each component. Set ev=U(B1(0,E_C),P(B1(C,0))) and
ea=U(B2(0,E_C),P(B2(C,0))). For nominal nv=|v|, na=|a|, let
Nc=U(|v cross a|,ev*na,ea*nv,ev*ea,P(nv*na)). Cross components use two-term
fsum; norms use hypot. Then compute

    E=U(h*A,r*D1)
    Vminus=L(nv,ev,E); Vplus=U(nv,ev,E)
    Nplus=U(Nc,h*Vplus*J,r*U(D1*A,Vplus*D2))
    denominator=L(Vminus**3)
    Kupper=U(Nplus/denominator)

Require Vminus>0 and denominator>0 before division. Nonpositive values return
an unresolved finite node; overflow/nonfinite arithmetic returns an arithmetic
failure leaf. Zero/negative/NaN cannot become a curvature pass.

## Complete deterministic subdivision

Binary dyadic rectangles cover [0,1]t x [0,1]l, including t seam and l endpoints.
Paths concatenate t0/t1 or l0/l1. Derive endpoints exactly from integer dyadic
indices, never trust saved rounded endpoints. Root path is empty. A split node
must have both children; unequal leaf depths are valid. No extra, duplicate,
overlapping, missing or prefix-conflicting terminal nodes are allowed.

Depth-first child0 before child1. A bound <=12 is a passing leaf. Otherwise use
the larger heuristic (tie t):

    T=h*Vplus*J + 36*Vplus**2*h*A
    H=r*(D1*A+Vplus*D2) + 36*Vplus**2*r*D1.

These finite values only choose subdivision, not acceptance. t depth<=14,
l depth<=10; if preferred axis exhausted use the other, if both exhausted keep
an unresolved leaf. Arithmetic-failure leaves do not subdivide. Every attempted
bound, including failed arithmetic, counts toward 16,383 evaluations per curve.
If no evaluations remain, retain every pending frontier leaf as unchecked.
An unresolved or unchecked leaf makes that curve/state uncertified, not violated.

Store every evaluated node as [path,action,Vminus,Kupper,T,H], with nulls for
unavailable values; actions are pass,split_t,split_l,depth,arithmetic,deadline,pending.
Store pending nodes with all numerical values null. Each compact JSON node must
be <=256 bytes; paths are <=48 ASCII characters. A node-size failure is an
execution error, not permission to drop its branch. Preserve complete frontier.
The checker recomputes every attempted node, split choice and work count, not
just passing leaves, without importing/calling the producer bound or traversal.
Arithmetic comparison: relative 5e-12 OR absolute 1e-12; both implementations
separately require <=12, with no slack. Missing nonphysical-scope flags or
promotion of any of them to true rejects the report.

A deadline crossed during a bound retains an attempted `deadline` leaf with
the completed numbers (or an attempted `arithmetic` leaf if calculation failed),
then the still-pending frontier. Before-bound expiration creates only pending
leaves. If expiration occurs after the last node, retain those nodes but mark
the curve/phase deadline-failed. A complete mathematical partition is not a
successful timed phase. Attempted work counts every non-pending row exactly.

The pure curve producer exposes `CurveModel(seed,candidate,matrix).bound(path)`
returning [Vminus,Kupper,T,H], and `certify_curve(seed,candidate,matrix,*,
deadline,clock,caps)` for the traversal. Invalid schema raises; bound arithmetic
failure becomes the explicit negative leaf above. Default caps are exactly the
registered maxima, with keys t_depth/lambda_depth/evaluations; tests may use
smaller caps (depth>=0, evaluations>=1), never larger. A report
contains schema_version 1, kind `local-homotopy-curvature`, caps, nodes, attempted,
curvature_pass, stop_reason (complete/evaluation-budget/deadline), and the false
flags interval_arithmetic, field_pass, step4_pass. The state layer binds named
inputs and physical-copy identity. The independent checker may not call either
producer API; it validates exact schema, node order/coverage, numerical fields,
split choices, limits, stop reason and counts. It never elevates a timed failure
to success simply because its arithmetic is reproducible.

## Operational caps and publication

Process physical copies strictly in original seed.physical list order; do not
sort by difficulty or skip symmetry copies. Each state gets 120 s producer and
separate 120 s audit. Start each parent monotonic clock immediately before phase
launch, before its first input rehash/old-certificate reconstruction; pass the
absolute deadline to the worker. Include startup, mappings, bounds, report
construction and serialization. Check before/after each curve,
each bound and publication. Expiration prevents success even if last bound passed.
No automatic retry, raised caps, new state or silently resumed prefix.

Each curve report is separate, max 8 MiB canonical UTF-8 JSON; sum of published
curve reports plus state index max 64 MiB. Reserve 8 MiB before starting a curve and
64 KiB for the state index. Before launch qualify that fixed schema, <=16,383
evaluated nodes and <=25 pending nodes fit in 8 MiB; enforce actual bytes too.
Remaining curves get explicit unchecked entries if no reservation/time remains.
Keep the complete current frontier on cooperative timeout. After expiration,
only bounded failure/frontier publication is permitted during the remaining 5 s
supervisor grace; no new bounds or success publication. The aggregate phase is
failed even if every earlier published curve passed. A hard supervisor timeout
at 125 s from the same parent start terminates the phase and retains only explicitly
published prefix reports plus failure metadata; an incomplete graph never passes. Parent keeps
at least 3 GiB free before each state; low disk stops without deleting old work.

Pure geometry old-producer and independent old-auditor reconstruction are
required for every state; match the bound old certificate, including its seven
non-curvature gates. New side-by-side classification requires all seven gates
and all physical-copy local bounds. Never overwrite an old decision. Audits
revalidate input identity and coverage; timing cannot be independently replayed
as a claim of identical runtime. Full prefix/failure accounting is mandatory.

## Qualification and execution gates

Controls before real-state work: identical/translated/scaled circles; transformed
copies; sign-reversed-circle homotopy collapse; regular endpoint circles whose
interior homotopy exceeds 12/m; high-mode between-node curvature peaks; missing 2*pi;
zero/near-zero speed; finite overflow; exact/over threshold; malformed names,
matrices and coverage; unequal-depth valid partitions; counter and budget tamper;
clock expiration before/inside/after last bound and report-size/publication limits.
Positive controls have a real margin (e.g. radius 0.2 m); no arbitrary near-limit
finite-subdivision success is required. Direct sampled witnesses are secondary
negative checks, never the passing criterion. No native libraries needed.

Commit protocol, exact inputs and independent method review first. Then separate
producer/checker code, focused tests, internal code review, public/docs/full
regression and committed source identity. Only then run the twelve fixed states
serially into a fresh output; record explicit returned reports, all failures,
resource counts and source-before/after. A valid negative result is publishable.
Success qualifies only this numerical component and the observed fixed-state
comparison. It does not establish formal intervals, a larger useful search
region, field benefit, Step 4, SoTA or MS1. Optimizer integration remains separate.
