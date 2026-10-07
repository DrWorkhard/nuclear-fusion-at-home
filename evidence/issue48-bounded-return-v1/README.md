# Bounded-step local search remains inconclusive

The single trust-region attempt stopped at the unchanged Euclidean 10 mm guard.
Fifteen map evaluations completed (three search positions and twelve derivative
probes); the sixteenth trial was rejected before field evaluation. Its distance
from the seed was 10.000235 mm. The smallest evaluated residual was 2.830969 um,
down from the initial 270.266208 um but above the 0.001 um root threshold. No final
solver return, qualified periodic point, refinement or linear classification was
obtained. Stop this local search branch; another solver variant needs a new
decision-relevant reason. Neither existence nor absence of an orbit follows.
The original continuation qualification remains 19/20.

Clean producer/evaluator: `4bf5eab45b7637b94c052bc7112834e6a30130eb`.
One unsuccessful attempt took 16.858088 s supervised total (14.554593 s driver),
within 300 s after imports / 330 s outer ceilings, one thread, 256 MiB, 3/2 GiB
disk reserves and 5 s clock discrepancy. Both scientific report and supervisor
receipt remain incomplete; cleanup was confirmed. A separate read-only
post-failure check matched all 59 direct source/input bindings and 1,662 native
package files. This check does not relabel the search complete. No guard tolerance,
seed, physical field, derivative scale or acceptance criterion was changed.

Code, tests and prospective protocol remain at their original paths. All six
original raw files remain untouched at `/private/tmp/issue48-bounded-return-v1`
and are copied under `raw/`. `inputs/` preserves the exact consumed subset of
trace-refinement archive `d12b01bedbb3d4e89ab891d03a9e6048f0690918`: manifest,
snapshot, refined failed trace and report. That input manifest lists other files
not copied here. The seed averages the first eleven-residue phi=0 sequence.
Configuration, command, source/environment identities, pre-run adversarial review
and passing 306 research / 65 public test logs are retained in metadata.

## Verification and reproduction

With NumPy, from a fresh shallow archive checkout:

```bash
python evidence/issue48-bounded-return-v1/replay.py --manifest-sha RECORDED_MANIFEST_SHA256
```

Replay verifies payload/source identities, reconstructs the saved seed, checks
all sixteen trial statuses/distances and recomputes the minimum stored residual.
It does not repeat native fields, integration, solver iterations, derivatives,
environment checks or timing. Replay success verifies a failed record.

For numerical reproduction, use clean producer `4bf5eab`, the recorded native
Python and one-thread settings. Actual command/environment: `raw/start.json` and
`scripts/run_bounded_return.py --config CONFIG --config-sha SHA256 --output
FRESH_PATH --revision 4bf5eab45b7637b94c052bc7112834e6a30130eb`.
Relocate the metadata configuration's `archive` to this payload's `inputs`, and
`supervisor`/`environment` to the metadata files; hash and retain that new config.
Native binaries remain external and their identities are checked. No Wout is
needed. Archive and producer revisions differ; retain every reproduction separately.

All evidence remains local-only, unpublished and remotely unverified. No valid
contour, island boundary, stability, confinement or benefit transfer is established.
Prior failed experiments remain unchanged. Agent review is not external peer review.
