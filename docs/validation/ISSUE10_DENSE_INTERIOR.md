# Both dense interior targets work without native libraries

**Decision: use the portable target packet for dense field diagnostics.**
On 7 October 2026, the scalar checker reproduced both frozen #25 fits across all
12,288 target samples, without VMEC, SIMSOPT, NumPy or historical inputs at runtime.
The [packet and commands](../../examples/clear-coil-interior-v1/README.md) support
new six-coil, order-5 candidates with an explicitly selected target. Merge
remains pending; no native intake or physical acceptance gate changed.

| Frozen control | Portable interior RMS | Max component field discrepancy, relative |
| --- | ---: | ---: |
| reference401 | 0.010716517095108489 | 9.68e-16 |
| selected401 | 0.01088795753116107 | 1.29e-15 |

Both still fail the unchanged **0.01** limit. Current recovery errors are below
5.56e-16 relative; aggregate and all three surface RMS differences from native
values are below 4.05e-16 absolute. These are separate target comparisons, not
evidence that one target improves realized-field benefit over the other.

The frozen qualification required current recovery within 1e-12 relative,
full-field agreement within 1e-10 relative and aggregate/surface RMS agreement
within 1e-10 absolute. Each target had one sequential attempt with a 600 s
process ceiling, 32 MiB output cap, 3/2 GiB disk reserves and 5 s clock-agreement
tolerance. Both exited zero in about 45.8 s. A separate copied-release CLI check
in a path containing spaces returned identical selected-target scores without
a Git checkout. This is usability evidence, not an additional scientific sample.

The export verifies the published #25 manifest and copies every target coordinate
and vector exactly. Source native producer/evaluator:
`a551289e63e44d7dbae7b5d5a0e5f4b6026db257`; source archive:
`05a4511084912fea9bd8d03e81f01018882396b8`. Packet manifest SHA256:
`9f9b32ffb6176b22e149069896500da0ac1aa0c371b5f17be7fa7603ebfb2ccb`.
The initial exporter stopped before writing data when a reconstructed pi value
differed from the saved flux; the corrected export retains the exact stored literal.
That failure and the successful byte-identical re-export remain in the evidence.

Clean qualification producer/evaluator:
`f40c53851e99f175f06257c17340e9b79237f3cb`. Published evidence archive:
`c32d3bd0edaeba40648d13fe42c12d09c247da45`, annotated tag
[evidence-issue10-interior-v1](https://github.com/DrWorkhard/nuclear-fusion-at-home/tree/evidence-issue10-interior-v1). Its 24-file manifest SHA256 is
`f5744132dffa27e2df54e77fd16c939ebff45bcc5bdce2a28ef1b1cc0d76bc0f`.
It preserves raw fields, controls, commands, receipts, checks and the completed
export/qualification scripts and regression tests. A fresh shallow stdlib replay
verifies all 24 files, 21 source/input bindings, comparisons and RMS arithmetic;
it does not recompute fields or re-attest timing. Original outputs/environments
remain intact. The active packet is about 2.9 MiB; full evidence stays separate.

The metric equally weights three target-surface grids with frozen B². It is not
a volume integral, realized-flux map or confinement diagnostic. Two controls
qualify this export/kernel path, not arbitrary-candidate quadrature convergence,
geometry, equilibrium regeneration or physical acceptance. Agent review is not
external physics peer review. See the archive README for replay and attribution.
