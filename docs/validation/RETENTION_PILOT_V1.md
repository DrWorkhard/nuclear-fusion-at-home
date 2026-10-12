# Bounded retention proposal, v1

Decision for [#66](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/66):
choose artifact ownership and capacity before substantial collection. This is a
proposal with a local restore control, not provisioned storage or a new budget.

## Measured example and resource envelope

Measured on 12 October 2026 from the manifest-bound
[matched archive](https://github.com/DrWorkhard/nuclear-fusion-at-home/tree/05a4511084912fea9bd8d03e81f01018882396b8/evidence/issue25-matched-v1),
producer/evaluator `a551289e63e44d7dbae7b5d5a0e5f4b6026db257`:

| Payload | Bytes | Retention meaning |
| --- | ---: | --- |
| Manifest-listed matched evidence, 6,258 files | 90,983,338 | Both fits plus controls/diagnostics; excludes manifest itself |
| Reference fit, 3,117 files | 33,271,793 | Includes 26,840,036 trial bytes and 6,261,642 NPZ bytes |
| Selected fit, 3,057 files | 32,751,353 | Includes 26,319,999 trial bytes and 6,261,103 NPZ bytes |
| Reference v1 export | 16,816,581 | Derived duplicate, not a substitute for raw inputs/arrays |

Recorded fit elapsed times are 304.527 / 304.396 seconds; these are historical
single-machine measurements, not forecasts. Regeneration, tracing, setup and
learning costs are separate. Original Wouts and native environments are not
included in these archive sizes and remain local-only inputs.

For capacity planning only, the existing fixed-target ceilings give
`N × (256 + 64) MiB` for raw run plus export, before environments/external inputs.
Ten ceiling-sized runs require 3.125 GiB per copy; primary plus two independent
copies require 9.375 GiB. Optional compression/deduplication is not counted as
guaranteed savings. At the default 300 s search + 120 s checking allocation, ten
runs request 70 minutes, excluding setup, tracing and in-flight overruns. This
does not authorize those runs or qualify the joint optimizer's resource needs.
Re-estimate after one bounded joint control. Monetary cost is unknown until the
owner chooses hardware/storage; no cloud price or paid ceiling is assumed.

## Proposed artifacts, destination and responsibilities

Keep compact records, all failures/interrupted attempts, seeds/selected snapshots,
target inputs, required equilibrium/field arrays, exact code hashes/dirty state,
commands and native environment identities. Preserve every target used for joint
replay and its generation cost; export alone cannot reconstruct an equilibrium.
Keep raw physics components so later reweighting does not erase measurements.

Use the existing [annotated evidence-tag procedure](REPRODUCING_RESULTS.md) for
reviewed, rights-cleared compact public evidence; keep summaries on main.
Propose owner-controlled off-device storage for indispensable ignored raw data
and environment material, plus an independent second copy. A tag/hash or another
directory on the same disk is not that backup. No destination is configured here.

The repository owner chooses the destination/account, access policy, storage and
compute ceiling, funding and backup custodian. The producer retains originals
until retrieval and both copies verify; the evaluator checks restore/replay
dependencies before confirmation. The custodian records location, owner, access,
last verified restore and unavailable artifacts. Respect MIT code and separately
attributed data; unresolved redistribution rights mean restricted retention,
not automatic publication. No upload or purchase is proposed as already approved.

Bind each copy to an immutable manifest of relative paths, byte sizes and SHA-256,
producer/evaluator revisions and obtainable URI/access instructions. Deduplicate
identical payload hashes while retaining every run's references and failure rows.
Never move/delete evidence tags or original raw outputs. Any later retention
change requires an explicit recorded decision. Stop new collection at its declared
ceilings or disk reserves (currently 3 GiB initial / 2 GiB live), preserving failed
work; do not delete failures to fit another run.

## Local restore control and next decision

The committed 14,815-byte reference input was packed locally, restored, deliberately
changed (hash rejected), and restored again. Original bytes stayed unchanged.
Expected SHA-256:
`57394ef682f3c6399faa03012abc02da2eb1ce40703a4f99640ece3d07e5691f`.
The temporary ZIP was 3,231 bytes; this tests one artifact's integrity, not native
replay, durable backup, encryption or remote availability.

Reproduce with standard-library `zipfile`: pack
`evidence/plasma-design-v2/reference-input-401.json` as `input.json` in a temporary
ZIP, restore that member to a new file, and compare SHA-256 with the value above.
Append one space, require mismatch, then restore and verify again. Never extract
arbitrary archive paths or execute archived code.

Owner decision still needed: named custodian, exact destination/access and paid
ceiling (if any). After authorization, verify remote retrieval of this small
artifact and a complete replay-dependency manifest before scale-up. Existing
evidence and native environments have not been newly backed up by this proposal.
