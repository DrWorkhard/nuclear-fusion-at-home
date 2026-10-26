# Seeded dataset control: incomplete

On 26 October 2026, the [prospective comparison](SEEDED_DATASET_COMPARISON.md)
was attempted once. The first fixed row, **146128**, returned all twelve metrics,
but failed the unchanged VMEC-boundary geometry gate. Rows **141151** and
**116646** were not run. The frozen workflow stopped, retained the failure and
reported `completed=false`, `all_agree=false`. No retry or replacement occurred.

The [complete attempt evidence](https://github.com/patrickmahlstein/nuclear-fusion-at-home/tree/b80e7cd01a46b32c9228f4962a26ae6e56bc6b7b/evidence/seeded-dataset-attempt-v1)
is in the contributor's fork: annotated tag
`evidence-seeded-dataset-attempt-v2-2026-10-26`, tag object
`98fbd4f80ba234d0380967b7057bd3dea03ec8b4`, commit
`b80e7cd01a46b32c9228f4962a26ae6e56bc6b7b`. A fresh shallow remote checkout
verified all seventeen payload hashes. The unchanged v1 tag is retained; v2 only
corrects a pre-run comment citation in its README. Original raw outputs remain local;
runtime binaries remain external and hash-identified. Neither tag custody nor
software review is external scientific validation.

## Observations and limits

- The surface/input sampled residual was **1.11e-15** input units and its Fourier
  coefficient bound was zero. The VMEC-boundary/input sampled residual was
  **0.3845235118440413**, against **9.98755402197538e-11**; its coefficient bound
  was **0.41309806980822056**. The theta-flipped diagnostic also differed
  (**0.448872818175453**) and cannot admit a result.
- VMEC reported `ier_flag=0`, `ns=99`, `mpol=10`, `ntor=10`. Effective settings
  matched the entire frozen dictionary before the solver ran. Solver success
  did not override the geometry rejection.
- All twelve returned scalars fall within the frozen arithmetic tolerance, as
  diagnostics from an invalid report only. They do not qualify even the first
  row, and the other twenty-four comparisons have no new results.
- The scorer checks geometry before its optional Wout save. Consequently no Wout
  was retained, limiting post-hoc diagnosis. Reading the adapter showed direct
  coefficient transfer; this does not establish the cause of the output mismatch.
  Unknown historical producer metadata still prevents attribution. Neither scorer
  fault nor physical infeasibility follows from this failed control.

## Exact execution state

Workflow source was clean `381e3d06ab864e1867c146ab87f952758f349b5e`;
scorer source was clean `32fe8ecd198a8615549b1086bca37682290f4e57`.
The pre-run [protocol](seeded-comparison-v1.json), input order, runtime, tolerances
and geometry checks were unchanged; all **549** bound identities matched afterward.
Report SHA256: `7dd49374e5371ef611dd81ab6bd7ed29956bcb8b08422d32131813b55d943d1f`.

The forward model took **258.517 s**. The child exited **1** after **316.747 s**
monotonic / **316.746 s** UTC, with no supervisor stop. The whole launcher took
**321.074 s** monotonic / **321.073 s** UTC and rejected completion. Execution
used one thread, retained about **135 KiB** at child exit and left **52.1 GiB**
free. Current resource consent, the controller lock and fresh inventories were
checked; only the owned child appeared during execution, and the later inventory
was empty. No deadline, resource or scientific gate was relaxed.

The control remains incomplete. Preserve this result; any further native action
needs a separately justified task and authority, not an automatic retry.
