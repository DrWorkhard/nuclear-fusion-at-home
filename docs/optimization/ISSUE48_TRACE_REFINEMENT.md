# The continuation reversals persist under independent integration

**Decision: these two finite traces reproduce under the registered numerical
comparison.** After the [center correction](ISSUE48_AXIS_CENTER.md) left the
failure unchanged, a different integrator with finer coil quadrature reproduced
the failed continuation launch and one qualifying control. This supports treating
the saved geometry as a reconstruction problem; it does not qualify a contour or
prove topology. The continuation grid remains unqualified at 19/20.

| Launch at s=0.5 | Maximum paired crossing difference (micrometres) | RMS difference (micrometres) | Reversals per residue sequence, old/new |
| --- | ---: | ---: | --- |
| theta=pi, failed | 7.850939 | 2.600189 | 1 / 1 |
| theta=0, control | 8.217908 | 2.636192 | 0 / 0 |

Each row compares 640 chronological crossings over 320 toroidal turns. All eleven
residue sequences on both phi=0/pi planes retain their direction-change counts.
The failed pooled gap changes from 1.240256 to 1.240183 rad; the control changes
from 0.062805 to 0.062803 rad. Both satisfy the prospective maximum crossing
difference <=10 micrometres, identical reversal counts and gap change <=0.01 rad.
These differences are agreement measurements, not continuum error bounds.

Original saved trajectories use native compute_fieldlines, 512 coil nodes and
tol=1e-10. The new calculation composes 640 one-field-period SciPy DOP853 R,Z maps,
using the same frozen coils/current, 1024 nodes, rtol=1e-11, atol=1e-13 and maximum
step pi/100. Physical launch points, positive-phi orientation, plane pairing,
target-axis center, eleven residue classes and 1e-8-rad step cutoff stay fixed.
Integrator, parameterization and numerical settings change together. Both paths
use native Biot–Savart fields; independent filament checks at five predetermined
new crossings per launch agree within 1.99e-16 on scale max(1,|B|). A full
independent-field trajectory, island classification and physical acceptance remain
unestablished. No flux label, equilibrium, optimization or acceptance gate changed.

Clean producer/evaluator: `6323ba683698ab55ab00b8f3d8778b5b6e6fb348`.
One attempt completed in 161.563 s supervised total, within 600 s after driver
imports / 630 s including startup/finalization. One thread, 256 MiB output,
3/2 GiB reserves and 5 s clock discrepancy ceiling. Source/input and 1,662 native
package file identities matched before/after; process cleanup passed. Pre-run
analytic map/composition tests and original outputs remain preserved.

Local archive: `d12b01bedbb3d4e89ab891d03a9e6048f0690918`, proposed annotated tag
[evidence-issue48-trace-refinement-v1](https://github.com/DrWorkhard/nuclear-fusion-at-home/tree/evidence-issue48-trace-refinement-v1); published; remote identities and manifest retrieval verified.
Manifest SHA256:
`a6e1708bbb3996752d331cb61485cefc656d40d59948deadabda6f9488ed39f7`.
The snapshot keeps code/protocol/tests, complete new output, exact consumed old
input subsets, commands and environment identity. Original raw output remains at
`/private/tmp/issue48-trace-refinement-v1`; the native installation is external.
No Wout is required. Replay verifies 25 payload files and 54 source bindings,
then reproduces 1,280 paired crossings, 88 residue sequences and both comparison
decisions using stored arrays and the same NumPy kernels. It does not repeat
integrators, native fields, environment or timing. Agent review is not external
physics review; no benefit-transfer claim follows.
