# Supplemental continuous coil-clearance bound — 2026-09-10

This check is declared after inspecting the two normalized candidates, before
executing the new bounding code. It is a **retrospective supplemental diagnostic**,
not a new unseen holdout or a change to the failed flux/length screens. Include
both candidates; keep their existing N=20,000 all-pair sampled minima and the
1.06 m reactor-scale centerline threshold. Do not refine N to obtain a pass.

For two periodic Fourier curves with parameters t,u in [0,1), let
f(t,u)=|r_i(t)-r_j(u)|^2. Bounds valid for every physical coil pair are
V>=sup|r'|, A>=sup|r''| and D>=sup|r_i-r_j|. Then each pure second derivative of
f has absolute value <=M=2V^2+2DA. Tensor linear interpolation on an N by N
grid has error <=M/(4N^2). Since the interpolant is a convex combination of
sampled squared distances, the continuous global pairwise clearance is at least
sqrt(max(0,d_sample^2-M/(4N^2))). A nearest-neighbor search with exact queries
supplies the all-pairs grid minimum without materializing N squared distances.

For each curve, triangle inequalities over its sine/cosine vector coefficients
bound radius around its constant coefficient, speed and acceleration. Apply
the corresponding 2*pi*m and (2*pi*m)^2 factors. Include the symmetry transforms
and use operator-norm bounds for their effect. Bound D by center separation plus
the two Fourier radius bounds. Use ordinary floating point with a small upward
coefficient-bound padding; do not call this directed-rounding interval arithmetic.

If the resulting lower bound is below 1.06 m, mark continuous clearance
unresolved/failed at this resolution, even if the sampled minimum passed.
Additionally report the lower gap between radius-r neighborhoods of **different**
coils for r=sqrt(0.05^2+0.05^2)/2 m at device scale. This condition suffices for
inter-coil nonoverlap of any idealized swept 0.05x0.05 m rectangular sections,
regardless of orientation, **provided** every solid point is within r of the
corresponding exact centerline. It does not prove that the existing tetrahedral
meshes obey that enclosure, prevent self-intersection of a single coil, certify
coil/plasma clearance, or validate mechanical/material physics.

Before real data, test known circle-pair minima not attained on odd sampling
grids, refinement of the conservative bound, touching circles, constant curves,
length-scale covariance and invalid inputs. Preserve input/evaluator hashes and
report every result without retroactive acceptance changes.
