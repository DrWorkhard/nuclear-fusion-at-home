# SQuID-C authoritative-data request

## Purpose

This is the minimal request needed to reproduce the published SQuID-C baseline
without reconstructing scientific data from figures. It is intentionally
specific enough to clarify the provisional mapping in
`manifests/squid-c.template.json`. Adapter work and scientific evaluation remain.

## Draft request

Subject: Request for machine-readable SQuID-C equilibrium and coil baseline

Dear Dr Goodman and co-authors,

we are building an open, independently validated baseline for robust stellarator
coil optimization. We would like to reproduce the SQuID-C configuration reported
in *A quasi-isodynamic stellarator configuration towards a fusion power plant*
(DOI 10.1017/S0022377825100974), including the distinction between the target and
the coil-generated equilibrium.

Could you provide, or point us to an authoritative release containing:

1. the fixed-boundary VMEC input and converged `wout` for the stage-1 target;
2. the VMEC input and converged `wout` for the canonical coil-generated,
   2% volume-averaged-beta, linear-pressure state, confirming its boundary mode;
   separately, the free-boundary stability-scan states and profiles;
3. the pressure and current profiles in machine-readable form;
4. all unique coil centre-lines or winding volumes, signed currents, curve
   orientation, stellarator/field-period expansion rule, and physical scale;
5. the MAKEGRID/MGRID construction inputs or exact recipe;
6. VMEC/ONSET versions, Fourier/radial resolution, convergence controls, and any
   patches needed to reproduce the files;
7. the reduction, weighting, field-composition and grid conventions for the
   reported average 0.27% and maximum 1.2% field errors, plus tolerances for beta
   and reference profiles;
8. if available, the Boozer, NEO, SIMPLE, ballooning, and beta-scan inputs/outputs
   used for the paper's protected physics checks; and
9. a license, release URL/version, and checksum list for provenance.

We will preserve the original files and hashes, distinguish author-provided from
locally derived artifacts, report failed reproductions rather than tune them
away, and cite the release and paper. We are happy to return a machine-readable
validation report and any software discrepancies we find.

Best regards,

[name and affiliation]

## Acceptance mapping

| Requested item | Schema-2 role or field |
| --- | --- |
| Fixed-boundary input/output | `fixed_boundary_vmec_input/output` |
| Coil-generated input/output | `free_boundary_vmec_input/output` |
| Pressure/current profiles | `profiles`, `currents` |
| Coil geometry | `coils` |
| MGRID construction | `mgrid_recipe` |
| Versions and controls | `solver_controls`, `equilibria` |
| Scale and symmetry | `scale`, `symmetry`, `conventions` |
| Provenance and license | `source`, per-file origin/URL/hash/bytes |
| Remaining paper data | `metadata` and optional `boozer_output` |

The public-availability audit is recorded in
`evidence/squid-c-availability-audit-2026-08-31.json`. It found no publicly
identified authoritative package as of 2026-08-31; this request should be sent
only after checking for a newer release.
