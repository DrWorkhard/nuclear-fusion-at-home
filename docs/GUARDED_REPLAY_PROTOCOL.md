# Guarded candidate replay and conditioning diagnostic — 2026-09-10

Retrospective diagnostic after the two frozen 3000-bundle searches, before this
diagnostic is executed. Does not alter candidates or feed back into those runs.

Reconstruct the guarded context from the original warm start in a new process.
Apply the recorded normalization, evaluate the original point once, then the
first repeat's saved best physical array once. Require agreement with both
recorded eight-component vectors to rtol=1e-10, atol=1e-12. Compare all sixteen
serialized and reconstructed curve position arrays (at their unchanged 200
nodes), currents and regularizations to rtol=0, atol=1e-12. This guards against
an array/serialized-field mismatch; it is not a new physical acceptance test.

At the saved best array check the full analytic directional Jacobian with a
seed-44 unit direction and centered eps=1e-4, 1e-5, 1e-6. Require the finest
normalized component error <=1e-6, as in search qualification. Record all steps,
including any failure. Total eight full bundles: original, best, six perturbations.
No optimization is performed. Hash retained original/best Jacobians and arrays.

Report singular values of each 8x207 normalized physical Jacobian and row norms;
effective rank uses singular values >1e-10 times the largest. Rank alone cannot
prove a cause of optimizer stagnation. In particular, zero rows from inactive
hinge penalties are expected. Any explanation of search performance remains a
hypothesis until tested by a separate controlled experiment.
