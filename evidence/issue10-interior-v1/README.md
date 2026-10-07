# Portable dense interior qualification

Question: can a small packet let contributors evaluate new coil candidates against
both #25 targets without native libraries? **Yes for the qualified scalar diagnostic.**
Clean producer/evaluator: `f40c53851e99f175f06257c17340e9b79237f3cb`.
The source/packet files remain in this archive's tree; original native producer
`a551289e63e44d7dbae7b5d5a0e5f4b6026db257` and published archive
`05a4511084912fea9bd8d03e81f01018882396b8` are unchanged.

One sequential `python -I -S` qualification per target compares all 12,288 field
vectors with the original native arrays. Current recovery errors are 3.34e-16 /
5.56e-16 relative; maximum-component field errors 9.68e-16 / 1.29e-15 relative.
Dense RMS values 0.010716517095108489 / 0.01088795753116107 agree within 4.05e-16
absolute; both still fail 0.01. Each process took about 45.8 s of its 600 s ceiling,
with 32 MiB output caps, 3/2 GiB disk reserves and 5 s dual-clock tolerance.
The nine raw files total 1,536,175 bytes. No throughput or continuous-host claim.
Separately, the selected-target CLI passed from the copied public release in a
path containing spaces, without a Git checkout or native imports; its 45.6 s
interface check returned the same identities and scores. This is not another
independent scientific sample or a retry of a failed qualification.

`raw/` retains every qualification output, launch command and process exit;
`inputs/` contains the frozen native controls. `metadata/` retains check and
export logs, the outer timeout launcher and copied-release qualification.
`source-map.json` maps original source/input paths to these same bytes.
`portable-cli/` retains the separate user-command smoke check.
The exporter validated all 6,258 original manifest entries. Export v1 stopped
before writing data because a reconstructed pi expression differed from the
saved flux by one last bit; v2 preserves the exact saved literal. Both logs remain.
The final exporter re-created all packet/control bytes in a fresh checkout.
The original packet extraction used clean `7a4823a1`; its identical re-export
used `dd917617`. No native Wout or environment was modified.

The active packet is about 2.9 MiB. Target samples retain their ordering and
frozen B² and flux conventions; the two original coil shapes are positive controls.
These samples cover three target surfaces, not a volume integral or qualified
realized-flux map. This result does not establish arbitrary-candidate convergence,
geometry, confinement, reactor feasibility or benefit transfer. Native selected-Wout
intake and all physical gates stay unchanged. Agent review is not external review.

From a fresh shallow checkout of this evidence commit, with Python 3.11+:

```sh
python -I -S evidence/issue10-interior-v1/replay.py --root . --output /tmp/interior-replay.json
```

Use a fresh output path. Replay verifies every manifest/source binding and repeats
the saved full-field comparisons and RMS arithmetic. It does not recalculate fields,
rerun equilibria or re-attest timing. To recompute fields without historical data,
use the `dense-interior` commands in `examples/clear-coil-interior-v1/README.md`.
This evidence snapshot is local only, not remotely verified. Original outputs and
the original archive remain intact. Underlying Goodman-derived data retain
CC BY 4.0 attribution (DOI:10.5281/zenodo.7220257); project source is MIT.
