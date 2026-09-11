# Finite-pressure trace cross-check v1

Declared 2026-09-10 after radial pilot results, before running the second tracer.
Retrospective validation of the frozen four-case pilot; no retuning of its scope.

Use the hash-pinned Goodman `TracedFieldline` routine and existing AST loader /
VMEC adapter, excluding plotting and top-level effects. That routine inverts
field coordinates separately and calculates length from B/B^phi; the pilot uses
Fourier geometry and its analytic derivatives. Both share the input equilibrium
and Fourier conventions, so this is not independent equilibrium validation.

Recompute all 84 trace grids (four cases, seven radii, three resolutions), retaining
stdout/warnings and failing on nonfinite/nonmonotone length or error diagnostics.
Require phi/alpha arrays to match to absolute 1e-12, pointwise relative B error
<=1e-8, normalized cumulative length error <=1e-3 (same thresholds as the earlier
vacuum cross-check). Record new raw NPZ hashes.

Recompute complete actions at the *existing* Bstar values, match to the pilot's
complete wells by the same geometric overlap rule (all trace-window wells, not
only selected central families), and require relative action discrepancy <=1e-3.
Use the frozen pilot family mappings to reconstruct all nine derivative estimates.
Require the finest normalized derivative to differ by <=max(1e-3,0.01*abs(old D)).
The combined diagnostic allowance is old empirical allowance plus four times
the absolute inter-tracer derivative discrepancy. Each originally resolved sign
must remain resolved with this larger allowance. An originally unresolved family
stays unresolved for the report even if the second tracer suggests a sign.

Report all failures unchanged. Success qualifies only sampled finite-pressure
trace/action/derivative consistency; not radial VMEC mesh convergence, gauge
independence, all wells in the plasma, or global maximum-J.
