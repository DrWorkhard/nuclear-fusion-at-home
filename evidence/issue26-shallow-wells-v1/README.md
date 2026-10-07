# Interior error and shallow-well association

**Result: promising association on the registered target-launched diagnostic.**
The existing interior continuation has dense interior RMS 0.001988031833995526,
versus 0.01071651709510873 for the #25 reference fit. It restores both missing
core pitch/surface cells and completes all 35 cells at both nested grids; the
reference retains exactly two failed cells and the ideal target completes all 35.
At s=0.25 the reference has one well on alpha indices 10 and 15; neither has the
required two wells. Do not describe all reference core lines as having zero wells.

Clean producer/evaluator and preregistered protocol:
`568a96a428fbb730ff23568ef917ab2b947fa255`. The complete protocol is
`docs/optimization/ISSUE26_INTERIOR_WELLS.md` in this snapshot. Existing candidates
are data; no fit, optimization, selection or physical gate changed. The continuation
is pjckoch's `submissions/interior-pass-headroom-continuation/candidate.json`.
Original #25 native producer was `a551289e63e44d7dbae7b5d5a0e5f4b6026db257`,
with published archive `05a4511084912fea9bd8d03e81f01018882396b8`.

Maximum individual-action refinement is 0.0008004088730337866 (limit 0.001),
across every successful cell, alpha and period family, including the ideal control.
The 801-point grid is a stride of the 1,601-point trace: this qualifies action
sampling, not ODE convergence. Independent field checks at 64 points on each
coil surface agree within 4.96e-16. The continuation's frozen current is
305178.2427715842 A; the reference current is 307977.14904565935 A.
The scalar and native continuation normalizations agree within 1e-12 relative.

One attempt completed in 70.792 s, inside 900 s total, with one native thread,
64 MiB output ceiling, 3/2 GiB initial/live disk reserves and 5 s clock tolerance.
The 25 original raw files total 19,127,287 bytes. `raw/` preserves their exact
bytes, all traces, actions, failed lines, snapshots, dense fields, receipts and logs.
`metadata/` retains the launcher, serial wrapper, external configuration, native
package identity record, software checks and agent reviews. All 43 source/input
hashes matched before/after; the environment record covers 1,662 package files.

From a fresh shallow checkout of this archive, using the documented native Python
with NumPy/SciPy (no new environment installation is necessary locally):

```sh
PYTHONDONTWRITEBYTECODE=1 python evidence/issue26-shallow-wells-v1/replay.py --root . --output /tmp/shallow-wells-replay.json
```

Use a fresh output path. Replay verifies every manifest entry, all 42 distributed
source/input bindings and the original receipts. It repeats saved-trace well/action
arithmetic for 210 grid/cell combinations, dense RMS and the frozen verdict using
the original kernels. It does not retrace fields, rerun equilibria, independently
validate the action kernel or re-attest timing. The original Wout is identified in
`source-map.json` but remains external; it is unnecessary for this arithmetic replay.
Full scientific repetition additionally needs that exact Wout and the recorded
native environment. `metadata/runner.py` and `raw/receipt.json` retain the actual
command and original paths; adapt paths explicitly and preserve input hashes.
The first archive replay reproduced all cell records but its final equality check
compared Python tuples with their JSON list representation. The corrected replay
normalizes that representation; the failed replay log remains in `metadata/`.
The original scientific run and its verdict are unchanged.

This archive is local only, not published or remotely verified. Original Wout,
raw files and native environments remain intact, outside this Git backup.
Underlying Goodman-derived data retain CC BY 4.0 attribution
(DOI:10.5281/zenodo.7220257); project source is MIT.
The two geometries have different optimization histories: this comparison cannot
establish causality, realized flux labels, islands, transport, confinement or
benefit transfer. It does not close #26 or #48. Agent review is not external peer review.
