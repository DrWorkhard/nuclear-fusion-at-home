# Level 3: for a university student

Updated 8 October 2026 · [All five levels](README.md) ·
Previous: [Level 2](LEVEL_2_TEENAGER.md) · Next: [Level 4](LEVEL_4_GRADUATE.md)

## The physics you need

Charged particles gyrate around magnetic field lines. In a torus the field is
stronger on the inside than the outside and the lines are curved, so particles
also drift slowly across them. If the field lines wind around the short way
(poloidally) while going around the long way (toroidally), the drifts largely
average out. The winding per toroidal turn is the **rotational transform ι (iota)**.
In a good configuration, field lines trace out **nested flux surfaces**, like the
layers of an onion, and the plasma pressure is constant on each surface.

A stellarator produces ι with 3D shaping instead of a plasma current. A generic 3D
field, however, loses **trapped particles**, those that bounce back and forth
between strong-field regions, much faster than a tokamak does. Stellarator design
therefore optimizes for a hidden order in the field strength. One option is
**quasi-isodynamic (QI)** fields, where the orbit-averaged radial drift of trapped
particles ideally vanishes. Wendelstein 7-X follows this line of design, and so
does our target.

## The computation

1. **Plasma stage:** choose the shape of the outermost plasma surface. An
   equilibrium code (VMEC; we use VMEC++) computes the magnetic field inside, and
   an optimizer adjusts the shape to improve physics measures.
2. **Coil stage:** represent each coil as a closed curve, a Fourier series in
   x, y and z. Compute its field with the Biot–Savart law. Minimize the field
   component normal to the target surface: if B·n = 0 everywhere on it, that
   surface is a flux surface of the coil field. Penalize coils that are too long,
   too sharply curved or too close to each other or to the plasma.
3. **Checks:** does the coil field also match the target field inside? Do its
   field lines form good surfaces? Is the plasma benefit from stage 1 preserved?

## Our concrete problem

- **Target "reference401":** an open QI configuration from Goodman and coauthors,
  with two field periods and no plasma pressure (a vacuum field), computed on up to
  401 radial surfaces at a reduced, normalized size. It is a research test case,
  not a power plant.
- **Coils:** six base coils of Fourier order 5, i.e. 33 coefficients each, so
  198 numbers to optimize. Symmetry turns them into 24 physical coils.
- **Plasma improvement (Step 3):** four changes to the boundary shape reduced the
  variance of a trapped-particle quantity (the bounce action) by 11.17% in a wide
  test domain and 4.85% in a narrow one. This is a computed diagnostic of a vacuum
  field, not measured confinement.

The acceptance limits are fixed in advance. Our best geometry-checked coil set
(fitted to reference401):

| Check | Limit | Best so far | Result |
| --- | --- | --- | --- |
| Boundary normal-field RMS, B·n/\|B\| | 1e-4 | 0.001932 | Fails, about 19× |
| Maximum boundary normal error | 1e-3 | 0.00907 | Fails |
| Interior field mismatch (RMS) | 0.01 | 0.01072 | Fails |
| Coil length (≤ 3.5 m at this scale), spacing, plasma distance, curvature | Project limits | Within limits | Passes |

A coil set fitted the same way to the improved target scores almost the same
(0.001953 and 0.01089) and also fails.

## Status by step

Steps 1–3 passed their stated scopes: reproduce selected reference calculations,
repeat a design iteration exactly, and improve the plasma target on the diagnostic
above. Step 4, realizing that benefit with practical coils, is in progress. Steps 5
(an advantage over leading designs) and the reactor goal are not reached. See the
[roadmap](../PROJECT_PLAN.md) and the [status page](../STATUS.md).

## Try it yourself

The [public starter](../validation/PUBLIC_QUICKSTART.md) needs only Python 3.11+.
It evaluates a coil candidate on 64 sample points with fixed coil currents, so it is
fast but cruder than the research checks. The starting coils score 0.304 (normal
error) and 0.380 (interior error); our best public candidate scores 0.00174 and
0.0361. Change a coefficient by about 0.01–0.1 mm and see what happens; the
[guide](../../README_agents.md#what-should-i-try) has the commands. A lower public
score is a useful hint, not an accepted design.

## What comes next

The key test is whether the improved target keeps its advantage in the actual coil
field. The first matched comparison could not finish the wide-domain test in either
coil field: some trapped-particle wells the diagnostic needs are missing. In the
narrow domain the improved arm is 5.07% better, but both arms are worse than their
ideal targets. Next, the project investigates why shallow wells are lost and checks
the flux-surface labels used in the coil field.

The coil-fitting recipe itself has stalled. On 6 October 2026 the project recorded
that a 30-minute run lowered the boundary error by only 6%, far from the factor of
two required to continue. A quick test with higher-order (more flexible) coil
shapes then lowered it by only 3.6% ([probe](../optimization/ISSUE53_COIL_FREEDOM.md)), so the project next plans to optimize
plasma and coils together rather than one after the other
([programme](../optimization/STEP4_RESEARCH_PROGRAMME.md)).
