# Ideal-improved target passes the short fitting comparison

The [registered paired screen](ISSUE37_FIT_COUPLING.md) completed once on
7 October 2026 with verdict **boundary-fitting-nonregression**. The fixed
+0.35 mm target, whose [ideal gain passed validation](ISSUE37_STEP_VALIDATION_RESULT.md),
can be retained as a starting target without making this bounded coil fit
materially harder. Both absolute boundary gates still fail.

| Worst fine metric | Original | Fixed +0.35 mm | Absolute limit |
| --- | ---: | ---: | ---: |
| Boundary RMS | 0.0019755099158508416 | 0.0019663016191886775 | 0.0001 |
| Maximum normal error | 0.009133341056030746 | 0.009205158478052713 | 0.001 |

RMS ratio **0.9953387748** passes the registered 1.10 nonregression hurdle.
Candidate RMS is 0.466% lower but maximum error is 0.786% higher; its RMS remains
**19.66 times** the absolute limit. Geometry, current, flux and independent fine
numerical checks pass. Different-target errors measure fitting burden, not
improvement of a common physical field. This is neither coil feasibility nor
realized-field benefit or physical acceptance. Interior and tracing were not tested.

Both fits reached their inclusive 300 s cap normally, selecting trial 775 for
control and 427 for candidate before diagnostics. The full experiment took
**679.94 s** of its 1200 s allowance, with 0.00813 s final clock disagreement.
Both frozen equilibria and prior ideal receipts were reused explicitly; no new
solve or ideal scoring occurred. All nine admission/sample/post-run host
observations passed; the owned assertion was released and verified absent.
Sampling does not prove continuous host stability or controlled load.

Do not automatically extend fitting or run expensive acceptance diagnostics
while absolute boundary limits fail. The next experiment needs a concrete
field-error improvement hypothesis or a specific topology question; preserve
this target and all earlier verdicts meanwhile.

Clean producer/evaluator: `56fd845f2ff84553092ac1690aa430283e14acdf`.
Local archive: `8a200dae194fc972ee535ad8532525aa17aff749`; prepared tag
`evidence-issue37-fit-coupling-v1`, publication pending. It preserves all
2481 raw files (29,392,180 bytes), both Wouts, original seed, cold and ideal
receipts, configuration, inventories and host records. The 2519-entry manifest
SHA256 is `fee10217d8f7b478ca593b0b4928049c8251f325fd71cac404c86057ef2130c2`.
Original raw outputs and native environments remain intact.

Saved-evidence replay verifies 135 retrospective bindings, frozen selections,
recorded deadlines and the decision. It recomputes independent B/A at 64 sample
points each on all four fine grids; full boundary/flux metrics use saved native
arrays. It does not rerun optimization, equilibria, native fields, intake or
geometry certificates, prove selection optimality, or re-attest historical
timing/host conditions. The archive documents reproduction and local availability.
Agent review is not external physics peer review.
