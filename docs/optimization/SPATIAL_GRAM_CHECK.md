# Independent Gauss-Newton matrix identity — 2026-09-11

Retrospective supplement to the passing factorization qualification. No new
physical evaluations and no optimizer feedback. For A=Dz, u=A^T z, q=z^T z,
outside the discontinuous clipping boundary:

    G_scalar = k^2 u u^T,
    G_spatial = (k^2/4) (q A^T A + 3 u u^T),
    G_spatial - G_scalar = (k^2/4) A^T (q I - z z^T) A.

The last matrix is positive semidefinite by Cauchy-Schwarz. This does not mean
the true Hessian is positive semidefinite, or prove better convergence. It
identifies the exact extra spatial contribution to this Gauss-Newton model.

Reconstruct both residual Jacobians from each hash-checked qualification NPZ.
Compare the resulting Gram difference to the closed form above with max-entry
error/max(1,max|closed form|) <=1e-10. Check the smallest symmetric eigenvalue
>= -1e-10*max(1,spectral norm), retaining the signed observed value. Independently
reconstruct Phi from stored field/normals and compare to z^Tz/2 to relative
1e-10. These are ordinary floating-point algebraic checks, not interval proofs.
