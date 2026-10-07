# Lower interior error restores the screened shallow wells

**Decision: test interior field fidelity in joint optimization.** The existing
[interior continuation](../../submissions/interior-pass-headroom-continuation/README.md)
restores both shallow core cells missing from the #25 reference fit, without new
failed cells in this screen. This is a promising association between two existing
geometries, not a causal demonstration or confirmed benefit transfer.

| Same reference401 target | Dense interior RMS | Complete pitch/surface cells |
| --- | ---: | ---: |
| #25 reference fit | 0.01071651709510873 | 33/35 |
| pjckoch's interior continuation | 0.001988031833995526 | 35/35 |
| Ideal target control | — | 35/35 |

The continuation's RMS is 5.39× lower. At both 801 and 1,601 points, the reference
fails exactly (s=0.1,q=0.03) and (s=0.25,q=0.03); the continuation completes both.
At s=0.25, reference alpha indices 10 and 15 have one well, still fewer than the
required two. All failures and raw traces remain recorded. Every successful
cell's individual actions agree across sampling grids within 0.000800409
(limit 0.001); independent field checks agree within 4.96e-16 (limit 1e-12).

The prospective protocol required the continuation's interior RMS ≤0.0021 and
below one quarter of reference, exact reference/ideal controls, stable failure
masks and individual-action refinement. A positive result required recovery of
both core cells with no new failed cells. It used five target launch surfaces,
seven registered pitch values, 16 alpha launches and two field periods.
No new fit, optimization, candidate selection or physical gate changed.

Both shapes were normalized once with the shared 256-node conversion, then
traced directly with frozen signed currents and 512-node fields. The reference
current is 307977.14904565935 A; the continuation's is 305178.2427715842 A.
Native/scalar continuation normalization agrees within 1e-12 relative.
The original reference401 Wout/input, B²=1.6293829620247962 T² and signed flux
−0.03141592653589793 Wb remain fixed. The 801-point grid is a stride of the
1,601-point trace: this checks action sampling, not ODE convergence.

Clean producer/evaluator and full preregistered protocol:
`568a96a428fbb730ff23568ef917ab2b947fa255`. The single attempt completed in 70.792 s
inside 900 s total, using one native thread, a 64 MiB output cap, 3/2 GiB disk
reserves and 5 s clock tolerance. All 43 source/input hashes and the recorded
native package files matched before/after. The 25 raw files total 19,127,287 bytes.

Local evidence archive: `2205e4dfd2716028e04682f738346a1e4ea925ac`, prepared tag
`evidence-issue26-shallow-wells-v1`; not published or remotely verified. Manifest
SHA256: `2609abf2627ee3e6c0580ef8515f038c10d25672cb997c4c2802658d2c50e652`.
The snapshot preserves code, tests, protocol, traces, failures, launcher and replay.
Fresh shallow-checkout replay verifies all 37 manifest files, 42 distributed
source/input bindings and all 210 saved grid/cell records. It repeats saved action
and RMS arithmetic, without retracing fields or re-attesting timing.
Original outputs and native environments remain intact. The original Wout is
identified but external; saved-trace replay does not require it. See the archive
README for commands and attribution; source #25 archive is
`05a4511084912fea9bd8d03e81f01018882396b8`.

Different optimization histories prevent causal attribution. Target launch labels
are not qualified realized-flux coordinates. These results do not establish islands,
transport, confinement, reactor feasibility or benefit transfer, and do not close
#26 or #48. Existing field/geometry acceptance gates remain unchanged.
Read-only adversarial agent review found no result-level blocker; it is not
external physics peer review.
