# Frozen ns101/201 derivative check of the joint protocol (N17)

Runs `frozen_next_check` of `docs/optimization/joint-protocol.json` at #59 head
`9d7c1b8` unchanged (claim and two stated readings on #63, before the run).
Producer: `check.py` (SHA-256 in `sha256.txt`), run from a clean checkout of
`cbc3539`. Environment: macOS, Python 3.12, vmecpp 0.8.0, one thread. Elapsed
2,029 s of the 3,600 s budget; ns101 solve 19.7 s, ns201 solve 59.6 s on average.

**Verdict by the frozen rule: fail. The J arm is not viable at this budget.**

| Base | Resolution, ns101 vs ns201 (≤ 20%, same sign) | h-spread over ns101 h ∈ {5e-6, 1e-5, 2e-5} (≤ 10%) | Pass |
| --- | --- | --- | --- |
| reference401 | pass (max 2.8%) | **fail**: rbc(2,0) 14.3%; zbs(2,0) 9.5% | no |
| selected401 | pass (max 2.9%) | pass (max 0.35%) | yes |

All four components are "big" at both bases. The reference failure comes only from
the largest step. At h = 5e-6 and 1e-5 the rbc(2,0) derivatives agree to 0.08%. Along
−rbc(2,0), the narrow action score's slope halves between −1e-5 and −2e-5, while the +
side stays linear: a one-sided bend at the 1e-5 scale. That is a diagnostic reading,
not part of the verdict. The pilot's ±5e-4 search box is 25 times larger than this
scale.

`result.json` holds every derivative, check value and score; `run.log` is the
script's output. Wouts were deleted after scoring; they are regenerable with the
recorded schedules. Not physical acceptance and not external review.
