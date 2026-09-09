# Expanded action coverage and B-contour topology — preregistered 2026-09-09

This experiment extends, and does not replace or retune, the v1 measurement
screens. Freeze this protocol in Git before implementing or executing the new
real-data checks. Use every pinned Goodman vacuum nfp=1,2,3 wout from v1.

## Fixed inputs and sampling

Use s = [0.10, 0.25, 0.50, 0.75, 0.90]. Keep each case's **v1** frozen common
Bstar interval, without recomputing it on the new surfaces. Sample fractions
q = [0.01, 0.03, 0.10, 0.30, 0.50, 0.70, 0.90, 0.97, 0.99] of that interval.
These are NOT fractions of every surface's entire trapped-particle interval;
some trapped/passing transitions and the magnetic axis/edge remain unexamined.

Use independent geometric traces at (nphi,nalpha,periods) = (801,32,2),
(1601,32,2), (3201,32,2), (3201,64,2). Include all complete wells and report
censored wells. Persist hashed raw B/length/alpha/phi arrays separately from
compact tracked evidence; never overwrite earlier evidence.

For every surface/pitch require complete-well coverage at every alpha. Require
equal ordered complete-well counts and maximum relative action change <=1e-3
for the 1601->3201 phi refinement. The envelope change in every consecutive
level must be <=max(0.002, 0.05*previous envelope), as in v1. The alpha refinement
compares envelopes, not differently sampled individual wells. Keep all failures.
Ordering is a numerical correspondence, NOT a physical well-family certificate.

## Independent surface-contour screen

Evaluate the symmetric VMEC bmnc Fourier representation on periodic uniform
(theta, zeta=nfp*phi) grids of (128,256), (256,512), (512,1024) points, excluding
both duplicated endpoints. Linear half-grid radial interpolation as in v1.
Topology is considered in VMEC surface coordinates; this does not test metric
closeness to a Boozer-coordinate ideal or validity of the equilibrium itself.

Implement a deliberately restricted **two-simple-root graph screen**, not a
general contour solver. At each theta, locate all sign-changing B-Bstar roots
in periodic zeta by linear interpolation, including the periodic seam. Require
exactly two. If any grid vertex is within 1e-12*max(1,abs(Bstar),max(abs(B))) of
the contour, flag the sample as unresolved rather than silently deciding a
tangency. Match the two roots to the next theta slice, including the last->first
slice, by the unique minimum sum of squared shortest periodic displacements.
Reject ambiguous assignments (cost difference <=1e-10 radians squared), any
step >=pi/4, or a nonidentity final permutation. Sum each branch's unwrapped
zeta displacements around theta. Require each sum/(2*pi) to be an integer within
1e-8 and both integers to be zero: two sampled poloidally closed graphs, each
with one poloidal turn and no toroidal turn. Nonzero winding is a negative
topology result; other contour classes are unsupported, NOT proven non-QI.

Every surface/pitch must pass at all three resolutions and classifications must
agree for the bounded topology screen to pass. Finite sampling cannot exclude
subgrid islands or extrema; this is not a continuum certificate.

## Verification before real data

Analytic Fourier/sampled controls must cover: a shifted pure toroidal cosine
(two poloidal contours, pass); a pure poloidal cosine (toroidal contours, no
false pass); a helical phase zeta-theta (nonzero winding, fail); a two-well
toroidal cosine (four roots, unsupported); exact vertex/tangency degeneracy;
periodic seam traversal; invalid/nonfinite data. Surface Fourier reconstruction
must reproduce an analytic synthetic wout, including nfp scaling.

Record protocol, input and evaluator hashes, Git state, package versions,
per-cell classification and failure reasons, plus pytest/Ruff outcomes. A
passing result qualifies only these finite sampled screens. Maximum-J at
finite beta, radial well-family matching, the complete trapped-particle domain,
and a full QI optimization objective remain open. Never infer reactor readiness
or a SoTA advance from these diagnostics.
