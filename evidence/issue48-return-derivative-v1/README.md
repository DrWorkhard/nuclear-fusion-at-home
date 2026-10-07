# Explicit derivatives still propose leaving the local search neighborhood

Four central-difference calculations at the frozen failed seed give Newton step
norms 36.636776–36.638572 mm. Their maximum pairwise difference is 1.796 micrometres,
below the preregistered 1 mm agreement threshold; all exceed the 11 mm diagnostic
margin around the unchanged 10 mm search neighborhood. The original forward
differences reconstruct a 53.168952 mm step. Its magnitude is derivative-sensitive,
but refinement does not change the neighborhood decision. No proposed point was
evaluated, no root search was performed, and no topology classification follows.
The continuation's original qualification remains 19/20.

Clean producer/evaluator: `570660c2674905f5175b47311049f98c88350843`.
One successful diagnostic attempt took 25.121912 s supervised total (22.063969 s
inside the driver), within 180 s after imports / 210 s outer ceilings. Other
limits: one thread, 256 MiB, 3/2 GiB disk reserves and 5 s clock discrepancy.
The receipt confirms cleanup, unchanged sources and 1,662 native package files
checked before and after. No retry or altered threshold was used.

The four settings use 512/1024 coil nodes and DOP853 rtol/atol 1e-10/1e-12 and
1e-11/1e-13, each with central differences of 10 and 5 micrometres in named R/Z
coordinates. Full matrices, samples, residuals, singular values and steps are
retained. Residual Jacobian condition numbers remain about 141,330–141,337;
agreement is not a rigorous derivative bound or proof of an accurate root step.
Both tracing settings share the native field implementation.

Code, tests and prospective protocol remain at their original paths. All original
raw files remain untouched at `/private/tmp/issue48-return-derivative-v1` and are
copied under `raw/`. `archive/` holds the consumed manifest/snapshot subset of
`d12b01bedbb3d4e89ab891d03a9e6048f0690918`; `failure_archive/` holds the consumed
manifest/report/trials subset of `5c6940bddd9f799803326c51ac2dc8ced21f69c1`.
Those input manifests list additional files not copied here. Metadata binds 58
direct sources/inputs and preserves configuration, native environment identities,
pre-run review, and 303 research / 65 public passing tests. Environment binaries
remain external. All evidence is local-only, unpublished and remotely unverified.

## Verification and reproduction

With NumPy, from a fresh shallow archive checkout:

```bash
python evidence/issue48-return-derivative-v1/replay.py --manifest-sha RECORDED_MANIFEST_SHA256
```

Replay verifies payload/source identities and independently coded arithmetic from
saved central samples and residuals, using the same NumPy linear algebra routines.
It checks the original forward reconstruction and four refined proposals/decision.
It does not repeat field evaluations, trajectories, environment checks or timing;
it cannot establish accuracy of the saved derivative samples.

For numerical reproduction use a clean producer checkout at `570660c`, the
recorded native installation and one-thread settings. The actual command and
environment are in `raw/start.json` and `scripts/run_return_derivative.py`:
`scripts/run_return_derivative.py --config CONFIG --config-sha SHA256 --output
FRESH_PATH --revision 570660c2674905f5175b47311049f98c88350843`.
Relocate the saved configuration's `archive` and `failure_archive` to the matching
payload subdirectories, and `supervisor`/`environment` to the metadata files; hash
and retain the new configuration. No Wout is needed. Native installation identities
are checked by the supervisor. Retain any new attempt separately; archive and
producer revisions have different purposes.

This result warrants no wider neighborhood, alternative seed or acceptance change.
It establishes neither presence nor absence of periodic orbits/islands, valid
contours, confinement or benefit transfer. Agent review is not external peer review.
