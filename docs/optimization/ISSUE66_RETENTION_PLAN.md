# Bounded retention plan for the learning trajectory

**Decision:** inventory/export at most ten existing closed runs before expanding
collection or training. This proposal for #66 supplies a measured baseline and a
small local restore, not a durable backup. It complements the
[trajectory contract](COIL_TRAJECTORY_V1.md) and
[community-data inventory](COMMUNITY_DATA_READINESS_V1.md); no new simulation,
model training, upload, purchase or storage provisioning is included.

| Retain | Purpose and availability |
| --- | --- |
| Inputs, seed/selected snapshots, trials including failures, gradients, final checks | Preserve named coordinates, signed current/target conventions, selection and fidelity. Original #25 archive is published; exports reference it rather than replacing it. |
| Field/action arrays, crossings and indispensable equilibrium Wouts | Needed to recompute labels. Preserve existing raw arrays; original Wouts remain maintainer-local, with recorded hashes. An export cannot restore missing equilibria. |
| Producer/evaluator revisions, source/input manifests, environment identities, commands, licenses | Bind replay and rights. Environment hashes do not back up binaries; native environments remain external and untouched. |
| Compact JSONL and lineage/failure metadata | Reusable for intake after qualification. Accepted optimizer steps, missing timing and plasma variables stay unknown; evaluations are not independent training families. |

**Measured baseline (7 October 2026):** one frozen reference401 fit contains
3,117 files / **33,271,793 bytes**, including 6,261,642 bytes of NPZ arrays.
The unchanged exporter produced **16,816,581 bytes** in **2.244356 s**, preserving
1,548 completed evaluations and one failure. All source hashes matched the
published manifest before and after. Total measured work was 3.336240 s, excluding
final receipt writing. Historical fit cost is a reported 304.526822 s, not newly
timed. This one case supplies no general throughput or compression guarantee.

**Next-stage estimate and limits:** ten similar runs would occupy about 333 MB
of original files plus 168 MB of exports per copy, before manifests, external
Wouts, environments and filesystem/Git overhead. For a bounded first stage,
allow at most 256 MiB of inventoried source and 64 MiB of export per run; ten
fully populated slots total 3.125 GiB per copy before those exclusions. Two
independent copies require 6.25 GiB plus excluded data/overhead. No second
independent copy has been established. Export-only cost extrapolates to about
22.4 s for ten comparable runs; provision up to ten 60 s processing slots,
stop on overruns and retain partial records. The measured script uses checkpoint
guards, a remaining-time exporter timeout, 128 MiB new-output cap and 3/2 GiB
initial/live free-space reserves; it has no outer deadline watchdog. Stop before
starting another run if reserves or aggregate allocation would be exceeded.
Native compute/training allocation is zero; paid spending remains undecided.

**Proposed custody:** the repository maintainer owns the catalog, verification
receipts and restore schedule; the account owner must accept storage custody,
choose a second off-machine location and set public/private access and any paid
ceiling before provisioning. Use existing annotated evidence tags for small
code/manifests/snapshots. Subject to rights and owner approval, larger retained
payloads can be [GitHub release assets](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)
attached to an evidence tag, each below 2 GiB. Asset URLs alone are not immutable:
the [API permits update/deletion](https://docs.github.com/en/rest/releases/assets).
Record asset ID, byte count, SHA-256 and retrieval URI in the frozen manifest;
keep a second verified copy outside that account/service. Propose public access
only for cleared artifacts; disclose restricted or missing inputs explicitly.

**Retention/restore rule:** deduplicate exact bytes by SHA-256, retaining every
lineage and failure reference; never deduplicate merely equivalent geometry.
No existing raw files/tags are deleted or moved. New releases/manifests are
append-only; corrections receive new identities. Keep irreplaceable raw inputs
and failures until an owner-approved retention decision follows verified copies;
no automatic expiry. After each authorized upload and quarterly thereafter,
the maintainer retrieves a small artifact into a fresh directory on the second
machine, verifies the pinned manifest and all file hashes, tests an altered-copy
rejection, and records time/location/result. Before claiming full-run recovery,
restore a complete run with all external dependencies and replay its labels.
The present **10,675-byte candidate** restored from a **3,001-byte ZIP** locally
with exact SHA agreement and an altered-byte rejection. It tests neither the
full run nor remote availability. Same-disk temporary copies are not backups.

**Evidence:** clean producer/evaluator `d1b90f4975cddcbbef439165beca048a946ea24d`;
source archive `05a4511084912fea9bd8d03e81f01018882396b8` (original #25 producer
`a551289e63e44d7dbae7b5d5a0e5f4b6026db257`). Local-only annotated tag
`evidence-issue66-retention-v1`, archive `db5df07487b8a0fb9db9abfae227b91bb70608ea`,
payload `evidence/issue66-retention-v1/`, 13-file manifest SHA-256
`25c297bc031491609111f9933e89d48cb5385bd91a731c0349d02040a8570fe3`.
Its README gives full measurement/replay commands; original output remains at
`/private/tmp/issue66-retention-v1`. Saved replay checks export counts, hashes
and candidate restoration, not native physics or fresh source-run recovery.
Keep existing Goodman/CC BY 4.0 credit; broader archive-data redistribution scope
must be resolved before publishing a repackaged trajectory. Owner custody/access
decisions and remote restore remain open; #66 is not fully closed by this plan.
