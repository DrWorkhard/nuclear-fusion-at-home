# Finite-build and structural-convergence protocol

Status: frozen before the first candidate mesh/solve on 2026-08-31.

## Purpose and candidate

This protocol qualifies the finite-build and structural-analysis software path;
it does **not** validate a reactor winding pack or support structure.  The fixed
input is the serialized field
`artifacts/runs/lpqa-engineering-v1p1-lbfgsb/biot_savart_optimized.json` and its
LPQA case.  This candidate passes the refined geometry/length screen but fails
the magnetic squared-flux cut-in.  It is used here only because it is a real,
fully serialized engineering-screen output, not because it is an accepted coil
design.

## Frozen geometry and mesh series

- Four unique modular coils; symmetry copies contribute to the magnetic field
  but are not remeshed.
- Rectangular swept cross-section: `0.05 m x 0.05 m` at device scale.  With the
  recorded LPQA length scale this corresponds to approximately
  `0.505 m x 0.505 m` at ARIES-CS scale.
- Tetrahedral target sizes: `0.05, 0.04, 0.03, 0.02 m`.
- The mesh generator is StellCoilBench's Gmsh sweep-to-volume fallback.  The
  exact package revisions are recorded by the repository lock/provenance.

### Recorded amendment after the first attempted mesh

The frozen Gmsh path failed on all four real coils at `h=0.05 m`: both OCC
through-sections and STL-to-volume reported intersecting or overlapping boundary
facets.  The failed table and log are retained.  The recovery path is an
independent periodic, rotation-minimizing structured sweep, with each swept
hexahedron split into six tetrahedra.  Its along-curve and cross-section spacing
are no larger than the requested `h`.  The same four sizes and all acceptance
criteria remain frozen.  Results from this recovery path qualify that explicit
representation only; they do not retrospectively validate the failed upstream
Gmsh fallback.

The finite-build representation passes this screening protocol only if:

1. all four requested coils have distinct nonempty physical-volume tags;
2. all tetrahedra have finite, nonzero absolute volume;
3. the finest total mesh volume differs by at most 5% from
   `sum(centerline_length) * width * height`;
4. the two finest total volumes differ by at most 2%.

Signed tetrahedron orientation is recorded but is not an acceptance condition:
the finite-element importer may consistently reorient cells.  Volume and
degeneracy checks use the absolute determinant.

## Frozen structural model

- Backend: scikit-fem 12, first-order tetrahedral displacement elements.
- Loading: `J x B` evaluated at quadrature points, including the full
  symmetry-generated coil field and StellCoilBench's regularized rectangular
  self-field.
- Homogenized isotropic linear elasticity: `E = 100 GPa`, `nu = 0.3`.
- Actual scikit-fem support model: all displacement components fixed for nodes
  in the lowest 15% of each coil's z range.  Although the upstream convergence
  driver labels runs `use_spring_bc=true`, the scikit-fem implementation does
  not assemble a Winkler term.  Evidence and conclusions use the actual
  fixed-support model.

The structural discretization screen passes if every run is finite and the
relative change from `h=0.03 m` to `h=0.02 m` is below 10% for each of:

- maximum displacement;
- mean displacement;
- 95th-percentile element Von Mises stress;
- mean element Von Mises stress.

Maximum element stress is recorded but excluded from acceptance because local
stress at an artificial fixed/free transition may not converge.

### Diagnostic refinement declared after failure of the primary series

The primary `0.03 -> 0.02 m` comparison failed every 10% convergence bound.
Before further solves, two diagnostic sizes are added: `0.015 m` and `0.010 m`.
This does not change the failed status of the primary test.  It may establish a
separate extended-series screen if all four acceptance metrics change by less
than 10% from `0.015 m` to `0.010 m`; otherwise the structural discretization
path remains unqualified.

## Interpretation limits

Passing demonstrates that this centerline-to-volume-to-load-to-P1-elasticity
pipeline has a numerically stable result for the frozen input.  It does not
establish absolute stress allowables or manufacturability.  Missing physics
include the real winding-pack layup and anisotropy, cases and insulation,
prestress, joints, thermal cooldown, contacts, nonlinear material behavior,
real supports, load combinations, and free-boundary plasma response.  Any
optimization may use these quantities only as screened proxy objectives until
those omissions are addressed and an independent structural solver is used as
a holdout.
