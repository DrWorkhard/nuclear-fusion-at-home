# Bounded retention proposal, v1

Decision for [#66](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/66):
choose capacity and artifact ownership before substantial collection. This proposal
provisions nothing and authorizes no budget or new run.

## Measured example and planning envelope

Measured 12 October 2026 from the manifest-bound
[matched archive](https://github.com/DrWorkhard/nuclear-fusion-at-home/tree/05a4511084912fea9bd8d03e81f01018882396b8/evidence/issue25-matched-v1),
producer/evaluator `a551289e63e44d7dbae7b5d5a0e5f4b6026db257`:

| Payload | Bytes | Scope |
| --- | ---: | --- |
| 6,258 manifest-listed evidence files | 90,983,338 | Both fits and diagnostics; excludes manifest |
| Reference fit, 3,117 files | 33,271,793 | Trials 26,840,036; NPZ arrays 6,261,642 |
| Selected fit, 3,057 files | 32,751,353 | Trials 26,319,999; NPZ arrays 6,261,103 |
| Reference v1 export | 16,816,581 | Derived duplicate; cannot replace inputs/arrays |

Recorded fit elapsed times: 304.527 / 304.396 seconds, not forecasts. Regeneration,
tracing, setup and learning are separate costs. Original Wouts/native environments
are absent from these sizes and remain local-only replay dependencies.

Fixed-target ceilings give `N × (256 + 64) MiB` for raw run plus export, excluding
external inputs/environments. Ten ceiling-sized runs need 3.125 GiB/copy, or
9.375 GiB for primary plus two independent copies. Do not assume compression
savings. Default 300 s search + 120 s checking requests 70 minutes for ten runs,
excluding setup/tracing/in-flight overruns. These are planning examples, not run
authorization or joint-optimizer estimates. Re-estimate after one bounded joint
control. Monetary cost remains unknown until the owner chooses resources.

## Retention, destination and responsibilities

Retain all failures/interrupted attempts, compact records, seeds/snapshots,
indispensable equilibrium/field arrays, every target/input identity, raw physics
components, code hashes/dirty state, commands and native environment identities.
Export alone cannot regenerate an equilibrium or justify new physical labels.

Use the existing [evidence-tag procedure](REPRODUCING_RESULTS.md) for reviewed,
rights-cleared compact public evidence; summaries stay on main. Propose
owner-controlled off-device storage for ignored raw data/environment material,
plus an independent second copy. Another directory or a tag/hash is not backup.

The owner chooses destination/account, access, paid ceiling and custodian.
The producer keeps originals until both copies verify; the evaluator checks
restore/replay dependencies. The custodian records location, access, owner,
last verified restore and unavailable inputs. Unclear data rights require
restricted retention, not automatic publication; code/data licenses stay separate.

Each immutable manifest binds relative paths, sizes, SHA-256, producer/evaluator
revisions and obtainable URI/access instructions. Deduplicate identical payloads
while retaining every run/reference/failure. Never move/delete evidence tags or
original raw outputs. Later retention changes need a recorded decision. Stop new
collection at declared ceilings/disk reserves (currently 3 GiB initial / 2 GiB
live); preserve failures rather than deleting them to fit another run.

## Local restore control and owner decision

The committed 14,815-byte reference input was packed into a 3,231-byte temporary
ZIP, restored, deliberately changed (hash rejected), and restored again. Original
bytes stayed unchanged. Expected SHA-256:
`57394ef682f3c6399faa03012abc02da2eb1ce40703a4f99640ece3d07e5691f`.

Reproduce with standard-library `zipfile`: pack
`evidence/plasma-design-v2/reference-input-401.json` as `input.json`, restore that
member to a new temporary file, and compare SHA-256. Append one space, require
mismatch, then restore and verify again. This tests one artifact, not durable
backup, native replay or remote availability.

Pending owner choices: custodian, exact destination/access and paid ceiling, if
any. After authorization, validate remote retrieval of this small artifact and
a complete replay-dependency manifest before scale-up. Nothing was uploaded,
purchased, removed or newly backed up by this proposal.
