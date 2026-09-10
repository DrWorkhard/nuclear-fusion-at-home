# Continuous Fourier-curve curvature enclosure v1

Declared 2026-09-10 before implementation and real-curve enclosure evaluations.
This is a retrospective geometry qualification, not a new unseen holdout.

## Purpose

The 200-point curvature penalty misses real violations. Replace a sampled maximum
as an acceptance certificate with an analytic bound covering every point between
nodes. First qualify this evaluator on analytical curves and the three frozen
fields: tracked rejected LPQA warm start and both affine candidates. Do not change
the optimizer or relax the 1/m reactor-scale limit during this qualification.

## Bound

For a regular periodic curve r(t), t in [0,1], write v=r', a=r'', j=r''', b=r'''';
u=v cross a, q=|u|^2 and w=|v|^2. Squared curvature is g=q/w^3. Then

g'' = q''/w^3 - 6 q'w'/w^4 + 12 q(w')^2/w^5 - 3 q w''/w^4.

Use each interval midpoint and radius h=1/(2N). The Fourier triangle inequality
sup|b| <= sum_m (2*pi*m)^4*(|sine_vector_m|+|cosine_vector_m|) supplies S.
Local bounds follow successively: J=|j0|+S*h, A=|a0|+J*h,
V=|v0|+A*h, v_min=|v0|-A*h. Nonpositive v_min is unresolved, never passing.
U=|v0 cross a0|+V*J*h bounds |u|;
P=|v0 cross j0|+(A*J+V*S)*h bounds |u'|;
Q=A*J+V*S bounds |u''|.
W1=2*(|v0 dot a0|+(A^2+V*J)*h), W2=2*(A^2+V*J)
bound |w'| and |w''|. Hence

H = 2*(P^2+U*Q)/v_min^6 + 12*U*P*W1/v_min^8
    + 12*U^2*W1^2/v_min^10 + 3*U^2*W2/v_min^8

bounds |g''| on that interval. Linear interpolation has error <=H/(8*N^2),
so g <= max(g_left,g_right)+H/(8*N^2) throughout the interval. The largest
square root is a global curvature upper bound. Node and midpoint values are
lower bounds on the global maximum and can supply violating witnesses.

Use ordinary double precision with upward padding of derivative/error bounds;
this is an analytic continuum enclosure evaluated numerically, **not** a
directed-rounding interval-arithmetic proof. Near-threshold rounding remains a
limitation. Nonfinite computations or unresolved regularity fail closed.

## Qualification and frozen grids

Use N=200,400,800,1600,3200,6400,12800 for every unique curve in all three fields.
At each level report lower/upper bounds, smallest certified speed, resolution,
and pass (upper<=limit), fail (witness>limit), or unresolved. Report all levels,
without selecting only successful resolutions. At fixed 12,800 accept a field's
curvature only if all four curves pass. Do not call other feasibility gates closed.

Tests: exact circle curvature and scaling, translated/rotated curves, analytical
ellipse with its maximum deliberately between coarse nodes, Fourier derivative
controls, stationary/singular curves and malformed/nonfinite inputs. Compare the
known analytical maximum against the computed enclosure, not just two grids.

Preserve hashes of all fields, code and protocol. Confirm physical copies are
orthogonal transforms of the four bounded Fourier curves before transferring
the curvature result to the 16-coil system. The original failed affine holdouts
remain failed regardless of this supplemental result.
