# Structured coil mesh integrity — preregistered 2026-09-09

Before running this expanded audit, freeze the following tests on all six
existing structured LPQA diagnostic meshes at h=0.05,0.04,0.03,0.02,0.015,0.010 m.
Inputs are the two structured_mesh_manifest.json files in
artifacts/structural/lpqa-v1p1-structured{,-fine}/. Verify every mesh hash before
reading. Do not repair, reorder, remesh or overwrite them during this audit.

These checks qualify intrinsic piecewise-linear mesh integrity, not mechanical
physics, absence of nonlocal volume overlaps, coil clearance or manufacturing.
In particular, the generator forces negative signed tetrahedra positive by
swapping indices. Positive volumes alone therefore cannot prove that a sweep
did not fold; shared-face orientation and topology need explicit checks.

For every mesh require finite points, integer/in-range connectivity, four
distinct vertex indices per tetrahedron and no duplicate tetrahedra. Require
positive signed determinant >1e-12*(maximum global coordinate span)^3. Report
min/1st-percentile/median tetrahedron mean-ratio quality:
q=12*(3*V)^(2/3)/sum(six squared edge lengths); require min q>=0.10. This is a
project diagnostic threshold, not an industry or material allowable.

Require exactly four nonempty physical tags. Per tag: every triangular face has
one or two incident tetrahedra; every internal shared face has opposite induced
orientations; every boundary edge has exactly two incident boundary triangles;
the boundary is one connected component with Euler characteristic V-E+F=0,
as expected for each closed swept ring's genus-one boundary. Report all failures.

Test controls before real meshes: regular tetrahedron quality=1; inverted,
degenerate, repeated and out-of-range connectivity rejected or explicitly failed;
a conforming pair has opposite internal-face orientations; overlapping positive
tetrahedra on the same side of a shared face are detected; duplicated tetrahedra
and a nonmanifold face fail; analytic closed periodic ring mesh has one toroidal
boundary. Use no mesh repair to make a result pass. The runner must refuse to
overwrite existing output and record input/protocol/evaluator hashes and versions.

Even if every screen passes, G5 stays open for nonlocal self-intersection,
symmetry-copy/inter-coil/plasma solid clearance, winding-pack orientation,
independent meshing, mesh-independent mechanics and physically valid loads,
supports/materials. Topologically valid meshes can still overlap in space.
