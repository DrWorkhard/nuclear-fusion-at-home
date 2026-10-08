# The spread 64-point layout improves agreement but misses its accuracy hurdle

**Decision: do not promote or retune this layout here.** A frozen 8x8 midpoint
layout corrects the known headroom/counterexample ranking and improves RMS agreement
for all three tested candidates. It still underestimates the dense RMS by more
than the preregistered 5% limit on both fitted geometries. The original public case
and evaluator remain unchanged; [#8](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/8)
remains open. Dense checking is still needed.

| Frozen candidate | Dense 4096-point RMS | Legacy 64-point RMS | Spread 64-point RMS | Spread relative error |
| --- | ---: | ---: | ---: | ---: |
| Public seed | 0.27605128 | 0.30420703 | 0.26800431 | 2.9150% |
| Length-headroom | 0.0019962704 | 0.0017440323 | 0.0018619177 | 6.7302% |
| Published +2 mm counterexample | 0.0020255546 | 0.0015616344 | 0.0018929757 | 6.5453% |

Values use 512 coil nodes. The maximum relative 256/512 change in any dense or
sampled RMS is 6.04e-14, so filament quadrature does not explain these differences.
Legacy relative errors are 10.1995%, 12.6355% and 22.9034%, respectively. Spatial
coverage helped these known cases, but removing duplicate samples is not itself
an accuracy guarantee. This is not an independent field implementation, hidden
holdout, general ranking guarantee or full independent-constraint count.

The prospective pilot froze indices `64*j+i` on the existing 64x64 boundary grid:
j={2,6,10,14,18,22,26,30}, i={4,12,20,28,36,44,52,60}. The midpoint tensor layout
covers half a field period without mirror pairs or symmetry-plane samples. Surface
area weights are renormalized over each sample. All fields use the unchanged
scalar public kernel and original physical-copy matrices, signed currents and
candidate coefficients. No optimizer or adaptive sample placement was used.

Promotion required every spread RMS to be within 5% of dense and closer than
legacy, every RMS quadrature change to be at most 0.1%, and the counterexample to
remain worse on dense, better on legacy and worse on spread RMS. All checks except
the 5% accuracy requirement pass. No sample retuning, retries, gate relaxation,
new public case or physical acceptance follows from this result.

Clean producer/evaluator and full prospective protocol:
`43d455116a860a745993ed9169cd0484aa8b606c`. One attempt took **68.588 s** supervised
(68.369 s worker), within 300 s worker including startup / 360 s total, one thread,
32 MiB output, 3/2 GiB disk reserve and 5 s clock tolerance. The isolated worker
used only the standard library. Source/input/Python executable identities matched
before/after and owned-process cleanup succeeded. Native environments stayed intact.

Local archive: `d095fe810619da722f213d3c04d9106c3990a7f2`, prepared annotated tag
[evidence-issue8-spread-sampling-v1](https://github.com/DrWorkhard/nuclear-fusion-at-home/tree/evidence-issue8-spread-sampling-v1); published; remote identities and manifest retrieval verified.
Manifest SHA256:
`8d110afdad493bee3d16e09eb6dc6063090b27b1e16c7dba51f4165ac00791a3`.
It preserves the code/protocol, all fourteen original raw files (3,822,740 bytes),
full-grid B arrays, geometry, failures/controls, commands and replay. All eighteen
distributed source/input bindings resolve; the nineteenth is the external Python
executable identity. Original raw outputs remain intact.

Fresh shallow replay verifies all 22 payload files and eighteen distributed
bindings, rebuilds geometry and exactly reproduces all 24,576 saved-field normal
errors, RMS reductions and the negative verdict. It does not rerun field evaluation,
the original interpreter or timing. Agent review is not external peer review.
