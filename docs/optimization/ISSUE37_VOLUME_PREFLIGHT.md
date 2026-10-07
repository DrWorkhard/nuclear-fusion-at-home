# Joint-proposal volume preflight

The two [frozen joint-feasibility proposals](ISSUE37_JOINT_FEASIBILITY.md) both
pass their prescribed volume screen. This geometry-only preflight removes size
as a reason to reject these proposals before solving equilibria; it does not
enable joint execution, admit a new target or establish coil feasibility.

## Question and result

On 7 October 2026, evaluate the original reference boundary and its registered
+1 mm then −1 mm changes to `rbc(m=2,n=1)`. Every other input value stays fixed;
no rescaling, adaptation or retry. Compare full-torus midpoint 128²/256² volumes
against the original at each resolution, with relative size limit 0.001 and grid
agreement limit 1e-6.

| Change to coefficient | Volume at 256² (m³) | Relative change (%) | Size screen |
| --- | ---: | ---: | --- |
| Original | 0.190067974433 | 0 | Pass |
| +1 mm | 0.190060465318 | −0.0039507525 | Pass |
| −1 mm | 0.190075483933 | +0.0039509550 | Pass |

Both proposals pass at both resolutions. Maximum relative grid difference is
2.93e-16; independent signed formulas agree within 4.39e-16. These are numerical
checks of a surface integral, not a proof of embedding or equilibrium validity.
The full joint-feasibility verdict and actual-coil benefit remain **null**.
The next necessary work is the separately reviewed new-target intake and bounded
implementation already required by the protocol; the volume result bypasses neither.

## Method and evidence

The existing independent boundary reconstruction supplies coordinates and
unit-turn derivatives. Average `x dot (x_theta cross x_phi)/3`, then take the
absolute value; no extra `(2*pi)^2` or normalized area weighting is applied.
An independently reconstructed Fourier cylindrical integral,
`-integral(R^2 Z_theta)/2` with radian derivatives, checks normalization. Analytic
modulated elliptical tori, three field-period counts, off-symmetry coordinates
and reversed orientation provide controls. The source protocol froze this
method and the max-volume relative grid denominator before evaluation.

Clean producer/evaluator: `14e76e6d8928cefffe93013c80dca0b48711b3ff`.
The archive-only script is `scripts/check_joint_volume.py`. Source, prospective
method and exact launcher passed read-only adversarial review before the single
assessment. Driver 0.828 s; supervision 1.095 s within 60/75 s caps; one thread,
256 MiB output, 3/2 GiB disk reserves. Native field/VMEC packages were disabled;
source/input hashes stayed identical and clock disagreement was below 0.001 s.
External host load was unverified. Agent review is not external physics review.

Local immutable evidence tag `evidence-issue37-volume-v1` is prepared at archive
`c71de25f5de3ce588a5759a4505d92e887b9eb1f`, payload
`evidence/issue37-volume-v1`. It preserves all nine raw files (66,271 bytes), all
three input documents, full results, controls, launcher and reproduction command.
The 15-entry manifest SHA256 is
`f719e093cf5bcd5f9e694d7f736368c38dfb90a33c86b55bdaeb77e5199086f4`.
The original reference input and frozen protocol are included; no external Wout
or coil seed is needed for this check. Raw outputs remain intact locally.
Producer validation passed 294 research and 61 public tests, docs, Ruff and diff
checks, with eight existing deprecation warnings. A fresh shallow archive replay
with native packages disabled reproduced all three cases and analytic controls
exactly, verified all 15 manifest entries and 23 source/input hashes, and checked
that each proposal changes only the named coefficient. Publication remains pending.
