# Findings log

## F-105 — Newly certified proposals yield small resolved normal-field gains

**Class:** independently reconstructed fixed-state diagnostic improvement
**Date:** 2026-09-26

At clean `4f13685`, four fixed states and six grids each complete 168 requests,
24 initializer/metric checks, 144 sampled B/A statistics, 20 refinements and
24 diagnostic flux checks. Both proposals reduce normal RMS beyond the preset
empirical margin: 0.057038% /0.065190%. The six-coil interior-vector gain also
resolves; the eight-coil gain does not. Both currents decrease (1,375.70/864.31 A)
and original strict counterfactual Armijo decisions pass. Old search decisions
remain unchanged. The intermediate verbal sign error is corrected in the results.

This demonstrates useful movement for these two previously blocked steps, not
a general method advantage. Normal RMS remains about 0.27 versus 1e-4; every
absolute field-error gate fails. No energy-efficiency, full flux/topology,
engineering, Step 4 completion or MS1 claim. Next: a small registered continuation
and saved-field diagnosis, not extrapolation to feasibility.
[Results](../optimization/FIXED_FIELD_PROBE_RESULTS.md).

## F-104 — A tighter path-wide bound certifies two formerly blocked proposals

**Class:** independently checked geometry component, not field improvement
**Date:** 2026-09-26

At clean `c7562ca`, all twelve preregistered fixed states pass local curvature
construction and its separate arithmetic/coverage checker: 336 physical copies,
285,528 bounds per side, 142,932 passing leaves. Both previously rejected states
(reference-n6-N trial 94 and reference-n8-N trial 50) now satisfy the separate
geometry classification. All seven other original gates are reconstructed and
unchanged. Original negative certificates are retained, not rewritten.

This confirms conservatism of the former curvature bound on these two paths
under the padded binary64 model. It does not establish rigorous interval proofs,
measured fields for the proposals, a generally useful larger search region or
physical acceptance. The experiment closes in 45.184 s, without retries, raised
caps, fields or optimizer changes. Next measure these fixed steps' actual field
effects before investing in search integration. Step 4A–4D remain open.
[Results](../geometry/LOCAL_CURVATURE_RESULTS.md).

## F-103 — Fine validation confirms geometry and persistent field mismatch

**Class:** independently reconstructed fixed-candidate negative result
**Date:** 2026-09-26

All eight selected protected-search states complete the registered fine phase at
clean `e0ac3f7`. All 40 refinements, 504 flux checks and 32 direct geometry grids
pass, alongside eight cumulative certificates and 576 sampled B/A statistics.
Largest B/A discrepancy 5.612042e-15; largest relative refinement change 0.019256%.
Every candidate fails only the three field-error gates, with fine normal RMS
0.26794–0.27478 versus 1e-4 and interior-vector RMS 0.35720–0.36411 versus .01.

This rules out failure of these prescribed numerical checks as the explanation
for the large field mismatch; it does not prove global numerical convergence or
physical impossibility. The source graph and all selected coarse currents remain
unchanged. 640 fine requests bring construction-plus-fine work to 2,573, below
2,960. No optimization or equilibrium solve during acceptance.

The pilot's mandatory fine phase is closed. Realization/transfer, coupling,
pressure/confinement and robustness remain open. Small coarse gains do not gain
a resolved fine-grid-improvement claim from these checks alone. Investigate
local homotopy curvature bounds separately, preserving all other constraints;
clearance and actual field improvements remain independent questions.
[Results](../optimization/PROTECTED_FINE_RESULTS.md).

## F-102 — Protected descent improves coarse fields, then hits the curvature certificate

**Class:** independently reconstructed coarse experiment, not physical acceptance
**Date:** 2026-09-26

All eight native cases at clean `2015ac5` complete construction and independent
coarse verification: 213 bundles, 795 certificates, 1,933 native requests. Normal
RMS decreases 0.4463–0.4857%; interior RMS 1.1881–2.1916%. All 117 field-evaluated
search proposals are accepted; 582 other proposals fail geometry certification.
Every search terminates certificate-limited, and every final negative certificate
fails only its curvature gate. Sampled selected curvature is 9.4877–9.6664/m;
the cumulative bound approaches 12/m. This motivates a tighter proof/different
direction, not a claim that the physical limit has been reached or can be waived.

All 795 certificates and 213 saved bundles are independently reconstructed.
Largest sampled direct B/A error is 1.804e-15 across 81,792 vectors. Source graph
unchanged, no automatic retry, no new equilibrium. Mandatory fine acceptance for
all eight selections remains pending, and normal RMS is still about 2,700 times
its limit. Objective decreases of 6.31–9.16% must not substitute for field-error
changes. No resolved fine-grid improvement, feasible baseline, Step 4 or MS1.
[Results](../optimization/PROTECTED_COIL_FIT_RESULTS.md).

## F-101 — Saved-physics reconstruction reproduces all eight negative seeds

**Class:** independent numerical/source qualification, not a new design
**Date:** 2026-09-26

At `2ac95db`, the independent reconstruction component passes 130 synthetic tests
and all 3,363 tracked regression tests (334 existing warnings). All eight actual
saved seeds pass objective/metric and sampled direct B/A reconstruction; maximum
relative discrepancy is 1.316e-15 over 48 comparison statistics / 3,072 vectors.
Two distinct original geometric certificates agree with four recorded producer
proofs. Coarse normal RMS remains 0.269149–0.276109 and inner-vector RMS remains
0.361571–0.372173: the old physical failures are confirmed, not repaired.

The checker traverses negative as well as positive evidence, reconstructs the
registered startup derivatives posthoc and separates large proof reports from the
aggregate. Review corrected swallowed storage failure and disk-minimum reporting.
Eleven sources and 23 artifacts are bound. The inactive next-launcher prototypes
were untracked and excluded from this qualification; no committed test/source was
omitted or changed. No new native model, field request, equilibrium or search ran.
Runtime native qualification, launcher admission and the fine phase remain open.
[Results](../optimization/PROTECTED_PHYSICS_RESULTS.md).

## F-100 — Isolated execution now has tested parent-bound completion

**Class:** local source/software qualification, not an improved reactor design
**Date:** 2026-09-26

At `fd069e9`, 315 new tests and the 3,233-test full regression pass. Eight actual
saved contexts validate against the admitted source graph; eight synthetic cells
traverse real subprocesses and separate graph audits. Source changes, thread drift,
swallowed callback failures and nonzero exits cannot become acknowledged success.
Review also corrected stale process-group cleanup, strict deadline endpoints and
return-time ordering. Failed development controls remain bound with final evidence.

The key distinction is now executable: complete files do not prove a successful
worker return or parent acknowledgement. Scope remains trusted single-writer
POSIX execution, cooperative parent checks and returning parent callbacks, not
untrusted-code isolation or kill-on-parent-death. Thirteen sources and 28 artifacts
are hash-bound. No native optimization ran; independent saved-physics checks,
runtime native qualification, fine acceptance and Step 4A–4D remain open.
[Results](../optimization/PROTECTED_NATIVE_PLUMBING_RESULTS.md).

## F-099 — The complete synthetic search chain passes its integration gate

**Class:** bounded software/recorded-data qualification, not a better coil design
**Date:** 2026-09-26

At `c17123a`, the original-seed startup, fresh search seed, fixed-budget controller
and fresh-model selected replay form one tested cell with complete snapshots/raw
arrays and separate native/controller journals. A read-only graph auditor checks
all operation links, reconstructed counters and checkpoint prefixes. 299 focused
tests and all 2,918 full-regression tests pass; 334 existing warnings remain.

Independent review corrected fixed-target substitution, stale/incorrect live
model state, ineffective cache invalidation, post-completion guard failure and
malformed-archive reporting. Large full certificates stay in immutable manifests;
compact decision references avoid overflowing the unchanged journal size limit.
Negative searches and every failed development test remain recorded. Read-only
schema checks accept eight historical seeds, not a newly optimized design.

Nineteen source files and 22 artifacts are bound. A found result-shaped file is
not proof that execution returned successfully; external acknowledgement remains
the native supervisor's responsibility. Physical reconstruction, native process
limits, fine acceptance and the rest of Step 4 remain open.
[Detailed results](../optimization/PROTECTED_CELL_RESULTS.md).

## F-098 — Execution components qualify after adversarial failures are corrected

**Class:** bounded software/source qualification, not a coil-design improvement
**Date:** 2026-09-26

At `47544d0`, 390 new tests qualify source admission, exact work accounting,
immutable snapshots and low-mode startup/replay helpers. Full native-environment
regression: 2,619 pass, 334 warnings, no failures/errors/skips. The read-only source
preflight admits all eight saved seeds and the unchanged 52-state geometry evidence.

Independent internal review found actual failure modes: reentry overspent a 116-
certificate cap, swallowed callback errors could allow completion, large-coordinate
FD probes could collapse unnoticed, seed-flux equality coerced booleans/arrays,
and parsers allocated metadata before enforcing limits (including a ZIP64 override).
Corrections and red tests are retained; follow-up reviews verify their bounded
fixes. The second method review conditionally supports a diagnostic pilot with
seed-only historical replay and explicit limits on physical-improvement claims.

Thirteen sources and 23 artifacts are hash/size bound. Integrated worker,
independent physical reconstruction, fine acceptance and later 4B–4D work remain;
no new native field fit or design advantage is claimed.
[Detailed results](../optimization/PROTECTED_RUNNER_RESULTS.md).

## F-097 — Event storage passes its scoped software qualification

**Class:** bounded software qualification, not a coil-design improvement
**Date:** 2026-09-25

Registration `7a210ac`, implementation `fc831f3`: exclusive, hash-linked event
files and externally bound receipts survive the specified injected I/O/interrupt
failures without acknowledging incomplete writes or overwriting prior evidence.
47 storage tests and 108 controller/auditor controls pass; completed full-suite
JUnit records 2,229 passes and no failures/errors/skips. Eight source identities
and four local JUnit artifacts are bound. The final full-suite console was not
recovered; warning count and whole-checkout immutability are not claimed.

Scope is a single-writer POSIX workspace, not an adversarial filesystem or a proof
of authorship/physical truth. Native budget/source orchestration, second method
review, independent physical reconstruction and fine-grid acceptance remain.
No field search or design improvement follows from storage qualification.
[Detailed results](../optimization/PROTECTED_RUNNER_STORAGE_RESULTS.md).

## F-096 — README contribution route and like-for-like score feedback verified

**Class:** public usability/software qualification, not a new scientific design
**Date:** 2026-09-25

At `0d9abcf`, the 27-point README follow-up implements and locally verifies 26
recommendations. The real clone URL remains unavailable; a labelled template and
ZIP route are supplied without pretending hosting exists. Candidate PRs now have
a Git-tracked `submissions/` path, a complete edit/evaluate/audit example and a
callable Python loop. Tests execute those commands and stage the actual candidate.

Displayed reference and candidate scores both use 512 nodes, making unchanged-seed
deltas exactly zero. The four hashed evaluator sources, original native-reference
comparison, case data and scientific limits remain unchanged. All 47 public tests
and eight copied-tree checks pass on Python 3.11/3.12/3.14 on macOS. Full native
regression: 2,182 pass, 334 warnings. Two earlier disk-guard failures are retained;
space recovered externally before the successful rerun, with no guard modification.
Step 4 remains unfinished. [Point-by-point record](../review/ROOT_README_RESOLUTION.md).

## F-095 — Protected-search controller passes its synthetic software gate

**Class:** bounded software qualification, not a coil-design improvement
**Date:** 2026-09-24

At `32dc632`, 108 new tests verify fixed low-mode descent, both coil classes,
immutable seed/high modes, failure accounting and a separate scalar completed-trace
auditor. Four draft bookkeeping/publication defects are fixed without changing
search policy. Deliberately inconsistent traces fail; internally consistent invented
physics remains unverified, explicitly, rather than being labelled physical admission.

Full research regression: 2,180 pass, 334 existing warnings, no failures/errors/
skips in 222.05 s. Public tests: 44 pass. Protocol/source/test hashes and the four
JUnit artifacts (including two failing runs) are recorded. The first failing test
source was uncommitted; its exact initial bytes are not separately archived. Source
identity claims are limited accordingly. User README edits remain untouched.

This closes only the synthetic controller gate. Native runner, second internal
method review, independent physical calculations and fine-grid acceptance remain.
No new field search or Step 4/MS1 claim. [Detailed results](../optimization/PROTECTED_SEARCH_SOFTWARE_RESULTS.md).

## F-094 — Release-review fixes pass fresh core and three-Python local qualification

**Class:** operational/UI/portability qualification, not a new physical design
**Date:** 2026-09-24

At clean `be916fb`, the exact core runner succeeds in a fresh locked dev-only clone
without SciPy/meshio/JAX: Ruff, docs, 44 public tests and 14 selected pytest tests.
All 44 public tests and eight actual reference/candidate/replay/rejection operations
also pass on Python 3.11.4, 3.12.13 and 3.14.3. Full native regression: 2,072 pass,
334 existing warnings, no failures/skips in 222.70 s. Whole-tree cp1252-default
simulation passes; actual Python 3.9.6 fails early with useful version guidance.

The UI now explains reference scores and signed changes; named editing checks all
198 positions. English indexes, unified roadmap and scoped public-agent guidance
remove onboarding ambiguities. Original numerical code/data/evidence are preserved.
Two frozen operational files have exact-hash maintenance exceptions, not blanket
permission to edit science. The full historical preservation check remains active.

An extra cross-version byte-equality assumption failed: two Python 3.11 seed metrics
differ by less than 1.12e-16 while every B/A array is identical. Existing replay
tolerances pass; Python 3.12/3.14 reports are byte-identical and direct old-report
replay succeeds. No scientific tolerance changed. Hosted/independent-machine
execution and publication clearance remain open; Step 4 is still In progress.
[Detailed record](../validation/PUBLIC_REVIEW_FIXES.md).

## F-093 — Portable starter success does not clear the historical repository for publication

**Class:** bounded repository inventory / publication-readiness finding, not physics
**Date:** 2026-09-23

At `fae6c87`, HEAD contains 1,541 tracked files / 325,093,781 bytes. All four local
refs reach 285 commits and 2,611 unique blobs / 356,848,583 bytes. A read-only scan
of every reachable blob finds zero matches for five selected credential/key-shaped
patterns, but home-directory indicators occur in 366 historical blobs and 365
HEAD files (362 evidence, one fixture, two documents). No matched values disclosed.

The final saved script agrees with the inline inventory under structured comparison;
seven positive/seven negative pattern controls and three temporary-repository
history/scope/non-disclosure tests pass. Neither a clean regex result nor the
portable starter is a complete secrets/privacy/rights review. Commit messages,
encoded payloads, unreachable/untracked content and later revisions are outside
scope. Individual path indicators are not yet adjudicated as sensitive disclosures.

Decide the release scope and complete its review without mutating historical
evidence or silently rewriting Git history. No publication, deletion or external
contact performed. [Inventory, evidence and remaining checks](../validation/PUBLICATION_INVENTORY.md).

## F-092 — Dependency-free public coil starter passes local copied-tree qualification

**Class:** portable software/arithmetic/interface qualification, not physical improvement
**Date:** 2026-09-23

Clean `02bc42a` completes all eight registered local release operations in a
copied tree without Git, native dependencies, historical artifacts or site packages.
The 36 public controls pass with zero skips. Actual 256-node fields/vector potential
match the six archived native sample arrays with maximum relative difference
9.5879976e-16 against the fixed 5e-10 gate; the largest 256/512 difference is
1.8491317e-15. The reference and the fixed 1-micrometre input variation both replay.
Forged physical admission and overwriting old output are rejected; contribution
metadata without compute or an approved topic is accepted.

All 14 copied files match the recorded Git revision/current source, and all 16
software-qualification source/data digests are unchanged. Operation logs and
environment are committed with the reference result; raw reports are hash-bound.
Earlier JSON-depth and frozen-CI regression failures remain documented, not erased.
The corrected full historical suite has 2,064 passes and 334 retained warnings.

This makes a real calculation accessible to outside contributors; it is not a new
accepted design. Public samples are fixed-current, sparse and exposed. Same-code
report replay is not an independent implementation; the original-native comparison
applies only to the unchanged seed. No hosted CI, independent machine, OS sandbox,
full native portability, automatic merge, Step 4 or SoTA claim. Whole-history
publication review and hosting configuration remain before launch.
[Full release record](../validation/PUBLIC_RELEASE_RESULTS.md).

## F-091 — Cumulative geometry certificate passes its complete real qualification

**Class:** preregistered field-free mathematical/geometry qualification, not field improvement
**Date:** 2026-09-20

Clean930580e completes both registered26-state classes,104 certificate calls,
208 direct grids and exactly2 shared full-torus surfaces. Independent numerical
audit passes all formulas, repeat/source/work checks and available strict
enclosures. Both seeds/repeats and all12 required smallest signed probes certify.
34/52 states certified overall (18 n6,16 n8);18 larger probes are explicitly
uncertified, not omitted or proved physically infeasible.

Both smooth prescribed directions certify through the tested1mm radius in both
classes. The single highest z-sine mode certifies only through0.1mm for n6 and
0.01mm for n8. These are discrete registered observations, not maximum admissible
radii or a universal method ranking. The n8 high mode at0.1mm is rejected solely
by the conservative curvature bound12.98898/m versus12/m. Four extreme high-mode
states correctly retain unavailable curvature bounds where speed lower bounds
are nonpositive; every available quantity still checked.

Independent reconstruction explicitly adds624 Fourier/416 CP/80,288 CC calls
and two surfaces; no fields, field gradients, equilibrium solves, LPs or searches.
All strict enclosure tolerances are0; numerical cross-code tolerance remains
separate. Additional stdlib-only provenance review confirms1371 bound references,
17 source files versus Git, complete counters and immutable checkpoint graphs.
2064 software tests pass; an earlier passing-but-insufficient suite and corrected
mutable-checkpoint-reference defect remain documented. No external peer review.

This closes the safety-oracle prerequisite. Next separately register a bounded
geometry-protected field fit, initially considering smooth directions. No new
magnetically feasible coil design, realized-field transfer, fullstep4 or SoTA.
[Full result and immutable evidence](../geometry/COIL_PERTURBATION_RESULTS.md).

## F-090 — All four clear-coil starts are numerically qualified, physically infeasible

**Class:** completed preregistered numerical startup, negative physical seed admission
**Date:** 2026-09-19

Clean7b1a501 completes reference/selected×n6/n8 with exact registered geometry,
archived targets, B2 and frozen fine current. All1048 native requests counted:
808 values/240 VJPs,40 initializations,80 bundles,24 diagnostics,72 flux grids.
Independent2434-reference audit passes all8 N/V derivative qualifications,
8 exact repeats,768 direct B/A comparisons,20 refinements and252 flux checks.
Max directrelative5.2942e-15; FD2.5941e-11 absolute/1.4486e-9 relative;
max refinement0.019508% and fluxrelative8.8349e-16.

All four seeds retain accepted geometry/current but fail all three field limits:
fine normalRMS0.26915–0.27611 versus1e-4, max0.59792–0.60164 versus1e-3,
inner-vectorRMS0.36150–0.37223 versus0.01. This establishes a reproducible safe
starting geometry with resolved arithmetic, not a feasible coil baseline.
No searches/equilibria, no realized-field/QI transfer or fullstep4 completion.
Next: separately register a bounded field fit that protects geometric safety;
do not relabel original failed pilot or infer impossibility from these seeds.
[Full results, evidence and one-ULP metadata erratum](../optimization/CLEAR_COIL_FIELD_START_RESULTS.md).

## F-089 — Full-grid block-native reference closes separate bounded-resource gate

**Class:** positive preregistered mathematical/resource qualification, not field admission
**Date:** 2026-09-19

Clean3349ce5 completes four fresh serial workers at unchanged128² surface,
24/32 physical curves and256/512 coil nodes. All52 states,336 comparisons to
BOTH original backends,32 FD checks and12 exact repeat/restore pairs pass the
independent659-reference audit. Maximum CP value/gradient differences are
4.2284e-18/6.5053e-19; CC and minimum distances agree exactly.

Whole-worker time16.287–38.186s and peakRSS0.379–0.427GiB meet unchanged
120s/1.5GiB gates. Same native formula and all original data,64 weighted blocks,
no gradient work hidden in values or cache credits. Exact completed CP kernel
counts93,184 values,35,840 per covector,21,504 minimum blocks,560 per curve VJP.
Single measurements, not an isolated-kernel or repeated performance benchmark.

Separate bounded_reference_pass=true; original dense3-RAM-failure decision remains
false and all four old Sparse passes are explicitly rechecked. This closes the
resource prerequisite, not startup, physical seed, search, transfer or step4.
Next: qualify complete field-start execution/source/admission workflow before
new project fields. [Full evidence and table](../optimization/BLOCK_NATIVE_REFERENCE_RESULTS.md).

## F-088 — Full-size sparse distance arithmetic agrees; dense reference exceeds resource gate

**Class:** bounded synthetic mathematical/resource qualification, overall negative
**Date:** 2026-09-19

Clean a5a007c completes all8 fresh processes,104 states,208 J/80 gradient/48
minimum-distance requests. All64 FD,24 exact repeat/restore pairs and168 paired
native/Sparse checks pass at full128² surface and24/32 physical coils with256/512
nodes. Largest CP-value/gradient differences5.3669e-18/4.3369e-19.

All four Sparse workers remain within120s/1.5GiB (0.393–0.474GiB peaks).
Three dense native workers exceed unchanged memory cap: n6/5122.1945GiB,
n8/2561.5237GiB,n8/5121.8765GiB. All timings meet120s. Whole-worker measured
peaks include native CC/JAX/imports; this is not isolated CP or a repeated
performance benchmark. Old dense failures and overall false decision retained;
no automatic exemption or project-field permission despite sparse passes.

Next method to preregister: full-grid native reference accumulation in bounded
blocks, same formula/data/gates, comparing every stored state to both original
backends. No field, equilibrium, candidate, SoTA or step4 claim.
[Full table and limits](../optimization/CLEAR_COIL_FIELD_START_RESULTS.md).

## F-087 — Target-adapted exterior starts pass all twelve independent geometry admissions

**Class:** preregistered geometry-only construction, not magnetic/step4 admission
**Date:** 2026-09-19

After the unchanged negative pilot, commit727dec8 freezes shared reference/new-
plasma support-function starts. All12 sets,168 LPs,84 exact original/repeat pairs
and72 fulltorus direct clearance certificates complete/pass. Independent original
LP/source/export and continuous geometry screens pass; maxprimal4.9081e-13,
maxgap1.8652e-14. Actual exported-curve rounding errors explicitly propagated.

Registered minimum-length selection chooses n6-shape-d100mm/n8-shape-d100mm:
maxcoil lengthupper1.937858/1.935110m (<3.5), curvatureupper<10/m (<12),
worst direct coil lower156.628/113.887mm (>60), plasma lower98.414/98.214mm (>80).
Their analytic base-length sums are15.7366%/16.1911% below matching100mm circles
within this bounded geometric family, not a field/engineering/Pareto advantage.
The former fixed-center initialization defect is avoidable under unchanged
geometric requirements. It did not demonstrate unrealizability of the target.

Zero magnetic/gradient/equilibrium calls. No field quality, QI transfer, pressure,
finite winding-pack or fullstep4 qualification. Next preregister better-resolved
field fitting from these accepted geometry-only snapshots; do not relabel old
failed fits. [Complete matrix and audit](../geometry/CLEAR_COIL_INITIALIZATION_RESULTS.md).

## F-086 — Fine coil admission rejects all six; coarse clearance and method ranking mislead

**Class:** completed independently audited negative pilot, not step4 completion
**Date:** 2026-09-14

All six128-bundle searches and42 fine diagnostic states independently audited.
Six original JSON-write failures preserved; additive output recovery at10a636b
normalizes24/32 NumPy booleans and explicitly reproduces identical negative gates.
No bound kernel or criterion changed. All field arithmetic/source/flux/current
checks pass; all candidates fail normal/vector/geometry/refinement admission.
Only17/30 refinement pairs pass. Fine normal RMS0.1134–0.2877 versus1e-4;
finest vector RMS0.7325–1.0853 versus0.01, not convergence-qualified values.

Fine sampled plasma minima1.812–6.663mm versus coarse34.708–52.384mm and required
80mm. These actual point-pair violations do not depend on conservative covering
bounds. All fine sampled maximum curvatures12.747–25.342/m exceed12/m. The
three coarse V-over-N interior-error rankings all reverse at finest resolution;
failed refinements prevent any robust opposite method ranking. Target-adapted
clear initialization and better-resolved construction are the next hypothesis,
not an unregistered extension or proof the plasma is unrealizable. Physical
transfer, co-design, finite pressure/confinement and robustness remain open.
[Details](../optimization/COUPLED_COIL_PILOT_RESULTS.md).

## F-085 — Real paired-coil start qualification passes six of eight cells

**Class:** independently audited numerical start qualification, not design admission
**Date:** 2026-09-14

Atb5c5a4d all80 registered bundles and all eight repeats complete. Independent
field/potential, named geometry, source-target identity and Stokes checks pass;
max directrelativeerror1.1592e-13 and fluxerror6.6262e-16. Both reference n8 starts
fail the fixed10µm sine-direction FD test (2.2857e-4/2.2869e-4 versus2e-4).
Independent composite values confirm the discrepancy; halved steps reduce it
roughly fourfold. Consistent with truncation, not grounds to waive the failed gate.
Only six cells may search. The missing reference-n8 counterpart prevents a full
paired comparison for that architecture in this pilot.

All physical seeds remain poor: normal RMS0.429–0.482 and sampled plasma
clearance2.372–6.074mm versus80mm. A subsequent read-only agent/root analysis of
saved n8 boundary sections additionally provides continuity-based crossing
witnesses for basecoils1–6 on both targets: exact circle coefficients, section
plane residual≤1.11e-16m and inside/outside sign margins≥87.276/5.657mm. Not a
formal interval audit. Enlarging the same fixed-center circles to enclose the
outermost saved point with80mm clearance requires length≥4.13928m>3.5m; this
does not exclude shifted/shaped coils or target realizability. Initialization
is a priority for a later registered study after this pilot. Qualification is not
physical acceptance or step4 completion. [Details](../optimization/COUPLED_COIL_PILOT_RESULTS.md).

## F-084 — Own vacuum plasma boundary passes the registered step3 design admission

**Class:** preregistered bounded numerical design improvement, independently audited
**Date:** 2026-09-14

After preserving F-083 unchanged, the separately registered two-domain follow-up
evaluates all16 old shapes, then eight tiny central differences and three real
LP proposals. All three proposals meet construction guards; Probe0 is selected.
Exactly13 new cold solves include selected201 repeat and401 fine endpoint.
Final audit atf285fbd passes source/arithmetic and all ten physical-domain gates:
fine broad S2.3894265674165413e-4 →2.122527071486505e-4 (11.170023% lower), narrow
gain4.850630%; maximum mean-action change1.018339% under2%, all70 local guards pass.
Numerical gain47.3762times empirical uncertainty sum (required>5); all20 refinements,
16 trace grids,280 contour cells,24 field grids and both tracer comparisons pass.
Thirteen Wout/solver quantities and narrow actions repeat exactly; broad actions
also checked exact. No failed or omitted domain cells. Final766-test regression
passes with144 known warnings. Historical1266-file preservation and all five
external states match the foundation record.

This closes step3 only in its registered nfp2 vacuum scope, not global QI,
improved measured confinement, fusion power, stability, feasible coils, SoTA or
SQuID-C. Both action domains informed construction; independent finer admission
is not blind generalization. No old physical threshold relaxed;32 total solves
including the first failed study, whose apparent narrow gain remains rejected.
Hand off rather than start steps4/5. [Full result/input/runbook](../qi/PLASMA_BALANCED_RESULTS.md).

## F-083 — First own plasma boundary fails expanded physical admission despite training gain

**Class:** completed preregistered negative design result, independently audited
**Date:** 2026-09-14

At90cdc57, two complete coordinate rounds request17 points and solve16 unique
201-surface equilibria, with one exact cache hit. All16 satisfy producer construction
checks. Selected x=(0,0.0004,0,0)m changes only zbs(1,1); training action variance
falls from1.1546244999075371e-5 to9.889668968130651e-6 (14.347314%). Separate201
cold repeat has13 exactly matching archived arrays. Poll selection and all bound
hashes separately checked; all19 cold solves including401 endpoints complete.
All16 expanded grids,280 contours,24 field grids, two tracer crosschecks and20
refinement comparisons complete/pass. Separate raw Gaussian/source/action audit
passes, but expanded S worsens15.5286% and20 of70 local mean-action guards fail
(four also fail envelope). Maximum mean change34.9135% versus2%. q=.03 contributes
95.8% of baseline expanded S and was excluded from training. Deterioration is48.5
times the observed numerical uncertainty sum; no step3 admission. No convergence, global QI, confinement, coil, SoTA or
SQuID-C claim. Selection stays fixed through later validation. Earlier baseline
and all negative probes remain preserved. [Detail](../qi/PLASMA_OPTIMIZATION_RESULTS.md).

## F-082 — Sharpened foundation and iteration milestones pass, without design admission

**Class:** preregistered bounded capability acceptance, not a performance advance
**Date:** 2026-09-13

At1aa28b6 the complete v2 acceptance passes all eight step1 and three step2 gates:
720 tests, strict six-data regression, unchanged known netCDF exception, exact
two24-bundle native cycles, independent source/ledger audits and all four holdouts.
Both physical candidates correctly fail flux at8.191663957639298e-8 against1e-8.
Selected point is startup replay12; subsequent real solver iterations occurred,
but no solver improvement or convergence claimed. Each candidate's61 closure
checks pass; tested geometry/native conditions pass independently of flux failure.
1266 historical tracked files preserved subject to explicit overview/journal edits;
external source state unchanged. v1 metadata-comparison failure/raw data retained,
fix controlled before the entirely new v2 run. No historical physical threshold
or scientific failure reclassified. GlobalQI/orbits/mechanics/SoTA/SQuID-C remain
unqualified future work. Current task ends with documented/committed handoff.
See [acceptance and runbook](../validation/FOUNDATION_ACCEPTANCE_RESULTS.md).

## F-081 — Nonzero radial drift and phase covariance pass; finite-orbit validity not established

**Class:** preregistered81-cell exact-vacuum matrix and243 independent scalar/FD states
**Date:** 2026-09-13

Both drift components, all three coordinate labels, same physical phase, SI and
all refinements pass. Independent scalar differences<=3.109e-10; worst fixed FD
error1.228e-8. Radial drift nonzero throughout. In the documented example the
angle component changes sign under relabelling while physical phase is unchanged.
Additional diagnostic from saved10keV SI values: relative one-way flux-label step
reaches0.7361, so small departure from the frozen field line is not secured.
These are qualified leading-order identities, not validated finite-energy particle
orbits. No posthoc energy replacement, no actual QI/global/step1 admission.
See [results and limitations](../qi/VACUUM_DRIFT_CONTROL_RESULTS.md).

## F-080 — Absolute one-way drift/action normalization passes analytic mirror control

**Class:** preregistered81-cell Cartesian matrix, independent45-run scalar adaptive/FD audit and SI controls
**Date:** 2026-09-13

All81 cells/27 refinement lines pass without warnings/failures. Direct drift
versus independent analytic action derivative differs<=1.552e-10 relative;
both fixed radial FD scales pass (worst1.471e-8). SI one-way action/time/drift
and charge/energy/mass scalings agree. Grad-B and curvature contributions are
both material; vacuum-only simplification is invalid for this pressure-carrying
mirror. This qualifies the analytic normalization path, not toroidal/QI physics:
radial drift is symmetry-zero, nonzero radial/phase/domain/real-equilibrium checks
remain open. See [complete result](../qi/ABSOLUTE_DRIFT_CONTROL_RESULTS.md).

## F-079 — Curvature-informed follow-up gives only0.754% gain and remains infeasible

**Class:** preregistered two2048-bundle GN searches, independent ledger audit and all four holdout phases
**Date:** 2026-09-13

Complete paths, values, work and startup/GN identities repeat exactly;20 profile
and49 checks per arm pass. Selected attempt2043 has no construction violation.
Fine flux8.129882387125932e-8 improves0.75421072% versus the current-minimized
source but remains8.13 times above1e-8. All geometric/native screens pass; all
resolution levels retained, both physical repeats exact. Curvature/plasma spacing
worsen while length/coil spacing improve: no full Pareto dominance. Both searches
stop at budget, not proven converged; precursor work is not free. No feasible
baseline, SoTA claim or step2 completion. See [results](../optimization/CURRENT_START_GN_RESULTS.md).

## F-078 — Quadratic field curvature explains all six failed finite geometric steps

**Class:** preregistered32-field replay, two full independent native matrices and scalar/spectral audit
**Date:** 2026-09-13

All native qualification gates and independent audits pass. All six quadratic
predictions have the correct worsening sign; minimum error reduction versus
linear99.59975%. This supports curvature-informed search, not a new design gain.
Both full field matrices have numerical rank203/207 at rcond1e-12; geometry and
current-projected geometry200/204. Extreme condition ratios~1e16 are roundoff-
sensitive and must not be read as accurate physical condition estimates.
Currents remain rank3/well-conditioned; geometric tangent current-space fractions
15.5–34.5%AL and~3.28%SLSQP show local coupling, not realized new-shape gains.
Next separately register a classical GN search from the already frozen best
source. No removed DOFs, new feasible baseline or SoTA/readiness claim.
See [complete results](../optimization/GEOMETRIC_CURVATURE_RESULTS.md).

## F-077 — Certified linear descent models fail on all six finite geometric steps

**Class:** preregistered six LPs,32 native bundles, composite derivative gates and independent real-chain-rule audit
**Date:** 2026-09-12

Both fixed current-minimized shapes have certified linearly descending proposals
at radii1e-6/1e-5/1e-4. All six derivative gates pass at both fixed FD steps and
both complex steps; independent real Fourier/chain-rule and250 file/data checks
confirm results. Yet every actual step raises flux and violates the unchanged
construction-selection tolerance. No fine geometry admission was attempted.
The finite linearization is inadequate here, not evidence of global optimality
or a faulty first derivative. Separate curvature/conditioning diagnosis is the
next justified step; static current optimality does not rule out useful coupled
current adjustments under shape changes. See [full results](../optimization/GEOMETRIC_DESCENT_RESULTS.md).

## F-076 — Exact current redistribution cannot close the fixed-shape feasibility gap

**Class:** preregistered two-state affine minimization, independent QR/file audit and all fine holdouts
**Date:** 2026-09-12

Both AL/composite-SLSQP shapes have well-conditioned rank3 current subproblems;
all native gates and114 independent qualification checks pass. All eight frozen
field holdouts complete;28 row/four overall independent checks confirm arithmetic
and negative classification. Fine flux8.95511949056e-8 and8.19166480121e-8 remain
8–9 times above1e-8, despite exact optimum current redistribution. Relative gains
only0.0000166076% and0.00000684724%, not meaningful design progress. All16 physical
coil shapes unchanged; no global shape lower bound, mechanical or SoTA admission.
Further constructive work must address shape optimization, not current-only tuning.
See [complete diagnosis](../optimization/FIXED_GEOMETRY_CURRENT_RESULTS.md).

## F-075 — Separate finest-mesh completion closes the six-resolution nonlocal scope

**Class:** preregistered single-mesh repeat, exact historical prefix and independent full audit
**Date:** 2026-09-12

Finest unchanged327000-tetra mesh completes after2,222,785 SAT calls, zero overlaps/
unresolved pairs. All53,464,336,500 pair possibilities accounted;8,905,300 shared-
vertex candidates explicitly excluded. Old2M witness lines/1,336,562 events are
exact prefixes, full new spatial audit passes. Combined with five old passes,
all six resolutions complete the non-shared-vertex screen; old v2 cap unchanged.
No adjacent-pair/full-assembly/winding-pack/mechanics admission or new feasible
coil design. See [independent completion](../engineering/MESH_FINE_COMPLETION_RESULTS.md).

## F-074 — Common straight-field coordinates explain part, not all, of historical QI differences

**Class:** preregistered complete coordinate-diagnosis matrix and independent scalar audit
**Date:** 2026-09-12

All60 old128-grid fields reproduce exactly, all120 new coordinate grids pass
root/nesting checks,61,440 independent scalar inversions/fields and1116 row
checks pass. Absolute theta disagreement<=1.154e-12. Yet only4/16 new fidelity
and5/16 comparison-refinement screens pass. nfp2 vacuum401/angular2 tangent error
drops from0.0074106 to0.0004742, supporting a parametrization contribution there.
Other tangent errors grow (nfp3 beta2 up to0.16250); these are coordinate-dependent
components, not invariant magnetic-field errors. iota/volume unchanged. Original
F-070 results retained; no source replacement or absolute drift/QI admission.
See [full matrix](../qi/QI_PEST_FIDELITY_RESULTS.md).

## F-073 — Five original meshes pass bounded nonlocal nonoverlap; finest cap remains open

**Class:** preregistered unchanged six-mesh scan and independent spatial certificate audit
**Date:** 2026-09-12

All six scans terminal; h=.05/.04/.03/.02/.015 complete with zero overlaps or
unresolved non-shared-vertex pairs. h=.010 hits its fixed2M SAT-call cap:
822,324,039 of53,464,336,500 broad pair possibilities and61 delivered candidates
remain unprocessed. Independent auditor validates all stored partitions and
3,358,644 separating witnesses, including the negative incomplete classification.
No LP/interval proof or global assembly/neighbor-pair/mechanics admission. Original
magnetically infeasible mesh source, not the newest optimized coils. See
[six-mesh results](../engineering/MESH_NONLOCAL_RESULTS.md).

## F-072 — Composite-gate polishing gives another modest flux reduction, not feasibility

**Class:** preregistered hybrid construction, exact repeats, independent audit and fine holdouts
**Date:** 2026-09-12

Both2048-bundle paths repeat exactly;10 profile/32 per-arm audit checks pass.
All four fine holdouts complete for both candidates. Fine flux8.191665362116152e-8
is about8.53% below the previous AL candidate but8.1917 times over1e-8. Geometry,
native metrics and linking pass. Continuous curvature upper0.8007962530/m,
clearance lower1.0875120845m, length219.9000016604m, sampled plasma gap2.96549m.
Compared with the AL source, length rises and plasma gap falls: not full Pareto
dominance. No convergence, equal-budget ranking, feasible baseline or SoTA claim.
See [completed polishing](../optimization/SLSQP_COMPOSITE_RESULTS.md).

## F-071 — Independent derivatives support cancellation at the failed polishing start

**Class:** preregistered two-direction complex qualification plus independent real chain rule
**Date:** 2026-09-12

All120 pair rows at the original fixed AL start pass three complex steps and
two source-basis directions. Native138-value replay is exact; maximal complex/
native derivative error4.063e-11, step disagreement1.594e-14. Independent scalar
JSON geometry and real Fourier/weighted-chain-rule audit passes35 checks, maximum
real/native derivative difference4.063e-11. Supports cancellation explanation
for the failed tiny real FD, not a global derivative guarantee. Original failed
study remains failed; a separately registered composite-gate search may follow.
See [qualification](../optimization/POLISH_START_DERIVATIVE_RESULTS.md).

## F-070 — Fresh QI angular refinement repairs sampled identities, not historical fidelity

**Class:** preregistered16-cell equilibrium matrix with independent field/arithmetic audit
**Date:** 2026-09-12

All16 cold starts reach all three1e-12 residuals.92/96 field grids pass fixed
Clebsch screens, including all48 at doubled solver angular resolution (maximum
poloidal residual2.585e-6). Radial refinement is not uniformly beneficial.
Only9/16 cells pass evaluation-grid refinement and2/16 historical fidelity;
none passes every screen. Old-loop replay agrees within9.076e-15 and all
classifications are independently confirmed. Historical19/24 stays unchanged;
no source replacement, modal-convergence or absolute drift certificate. See
[complete matrix](../qi/QI_FRESH_RESOLUTION_RESULTS.md).

## F-069 — Stable spectral projection does not reproduce the stored QI field components

**Class:** preregistered spectral hypothesis test with explicit trigonometric audit
**Date:** 2026-09-12

All48 half-surface grids complete; old nested samples reproduce exactly, Parseval
error<=3.955e-16 and64/128 projection refinement<=4.732e-11. Yet no poloidal or
toroidal endpoint comparison meets1e-5: projected Clebsch-vs-stored components
retain errors up to1.60396e-3.96 direct DFT/48 explicit reconstruction calls
independently confirm the band/projection result. Simple component truncation
alone is inadequate; Jacobian truncation/lambda output/producer reconstruction
remain open. No data repair or absolute drift certificate. See
[spectral diagnostic](../qi/QI_CLEBSCH_SPECTRAL_RESULTS.md).

## F-068 — Qualified alternative start improves classical construction but still fails flux

**Class:** preregistered new-start trial, exact repeated search and independent fine rejection
**Date:** 2026-09-12

Both1033-bundle paths and independent audits pass; all four fine holdout phases
complete. Fine flux8.955120977790992e-8 is about2.67 times lower than the same
scaled AL at the old start, but8.955 times above1e-8. Length219.89799m, continuous
curvature upper0.85528686/m, clearance lower1.08240411m and native extra metrics
pass. Mean field0.9461249614T. No feasible baseline, convergence, method ranking
or Pareto dominance; length/clearances are not uniformly improved. See
[complete alternate-start study](../optimization/UPSTREAM_START_RESULTS.md).

## F-067 — Radial product interpolation does not explain the QI poloidal residuals

**Class:** independently audited exact residual decomposition, negative causal test
**Date:** 2026-09-12

All24 old grids reproduce through a separate matrix-Fourier endpoint path within
4.883e-15; residual decomposition agrees within4.506e-15 and independent product
replay passes. Ten of48 original half-grid poloidal identities already exceed1e-3,
maximum1.6114e-3; largest pure interpolation term is3.6134e-6. All48 toroidal
endpoint screens pass. Radial interpolation alone is excluded; spectral/output
convention causes remain hypotheses. No healing of the original19/24 screen or
absolute-drift gate. See [decomposition](../qi/QI_CLEBSCH_INTERPOLATION_RESULTS.md).

## F-066 — Signed QI flux convention supported, full representation screen remains negative

**Class:** preregistered Wout representation check with independent point-array audit
**Date:** 2026-09-12

All24 grids of four fixed Goodman cases complete and independently replay exactly.
Toroidal Clebsch identity, Cartesian vectors and |B| agree within1e-3; opposite
sign/missing2pi controls fail strongly. Five poloidal identities exceed the fixed
limit, maximum1.6005473e-3;19/24 grids pass all requirements. No threshold change,
absolute drift qualification or independent equilibrium validation. Radial product
interpolation is a hypothesis for residuals, not yet an established cause. See
[bounded result](../qi/QI_CLEBSCH_RESULTS.md).

## F-065 — Five reported zero-flux archive fields fail the independent raw-flux gate

**Class:** source-preserving static reconstruction with independent field replay
**Date:** 2026-09-12

All five fixed shortlist sources, physical currents, Fourier coefficients and
symmetry checks pass. Independent direct Biot-Savart agrees within5.534e-16
normalized. All geometric/refinement grid checks pass but raw flux is about
9.9995–9.9997e-7, nearly100 times our1e-8 gate, consistent with their much looser
1e-6 clipping threshold. No universal claim about all5301 records, no admitted
baseline. Reported historical field-strength values are not comparable to our
surface mean; reconstructed means are about0.94606T. See
[static result](../optimization/UPSTREAM_LPQA_RECONSTRUCTION_RESULTS.md).

## F-064 — Jacobian scaling lowers flux in a repeated one-start trial, still infeasible

**Class:** fixed single-option classical comparison with independent negative holdouts
**Date:** 2026-09-12

Both1033-bundle arms match exactly and pass independent profile/work/selection
audits. All four fine holdouts complete: geometry/native checks pass, fine raw
flux2.390957922567119e-7 remains23.91 times over1e-8. Flux is about11.4% lower
than unscaled recovery at the same start/cap, with essentially equal mean field;
curvature rises and gaps shrink slightly. No feasible baseline, Pareto dominance,
convergence or multi-start method ranking. See
[closed scaled trial](../optimization/NATURAL_AUGLAG_JAC_RESULTS.md).

## F-063 — Unchanged natural-AL recovery is reproducible but fails independent flux

**Class:** preregistered repeated classical construction, independently rejected
**Date:** 2026-09-12

Two new1033-bundle arms and old1033/700 prefixes match exactly. Both independent
search audits pass. All four fine holdout phases complete: geometry, continuous
curvature/inter-coil bounds and native extra metrics pass, but fine flux
2.698587472179773e-7 is26.9859 times the unchanged1e-8 limit. The curvature
enclosure is unresolved at200 points and passes from400; all levels retained.
No convergence, feasible-baseline, full-engineering or method-superiority claim.
Original IO-interrupted study remains incomplete. See
[closed recovery](../optimization/NATURAL_AUGLAG_RECOVERY_RESULTS.md).

## F-062 — Fresh local native reconstruction and scientific integration now witnessed

**Class:** fresh-install/build/solver regression with independently archived outputs
**Date:** 2026-09-12

All21 reconstruction phases and six strict scientific tests pass at b32bc88,
including freshly built VMEC8.52 and new W7-X outputs from both solvers. Eleven
raw files are hash-verified in a post-run archive. Separate archive-based comparison
retains exactly60/63 and pres/presf/chipf failures; scoped physics/refined-grid audit
passes. Resource guard maintained at least6381441024bytes free after a preserved
first disk-exhaustion failure. Local G1 fresh integration subgate now satisfied;
same hardware and permitted caches, not global QI/engineering qualification or
complete long-term step1/2. See [result](../validation/FRESH_NATIVE_INTEGRATION_RESULTS.md).

## F-061 — Radial action signs change under gauge relabeling in unchanged nfp3 fields

**Class:** fixed four-case physical diagnostic with independent arithmetic audit
**Date:** 2026-09-12

All84 old traces and every c=0 stencil/sign reproduce exactly. Under c=-1/0/+1
radial field-line relabeling, five nfp3 vacuum and20 nfp3 beta2 families include
both positive and negative classifications. All160 cells match; chain-rule error
<=1.663e-4 normalized, all fixed screens pass. Independent interval/stencil/sign
audits pass for all320 families. nfp2 beta2 remains negative for all80 sampled
families in every tested gauge. This is not a changed field or global maximum-J
certificate; define a physically appropriate measure before optimizing it.
See [results](../qi/QI_RADIAL_GAUGE_RESULTS.md).

## F-060 — Fresh SLSQP repeats agree, but do not reproduce the historical prefix

**Class:** repeated construction with retained failed protocol condition
**Date:** 2026-09-12

Both fresh 1024-bundle arms match exactly and pass independent ledger/selection
checks. Their first historical discrepancy occurs at proposal 62 (2.842e-14
absolute value difference), growing to 0.07436 normalized within the old256
prefix. The entire prefix condition fails; a tiny initial perturbation does not
justify calling the later trajectories identical. Selected proposal 921 has
coarse raw flux 1.26648e-7 and internal violation 8.929e-7, so remains inadmissible.
No demonstrated convergence or method ranking. See
[results](../optimization/DIRECT_SLSQP_1024_RESULTS.md).

## F-059 — Qualified GN curvature does not yield a feasible design within 1024 bundles

**Class:** repeatable budget-limited construction; fine holdouts pending
**Date:** 2026-09-12

The corrected native-covector pilot repeats every proposal/value and the old
failed-prefix exactly; independent accounting/selection audits pass. Selected
proposal 1020 has coarse raw flux 2.4713685440167177e-7 and zero internal
constraint violation. The flux remains 24.714 times the independent limit, so
the useful local quadratic model has not yet produced an admissible design.
Budget termination does not establish convergence. See
[results](../optimization/GN_NATIVE_COVECTOR_RESULTS.md).

## F-058 — GN guard compared gradients built from differently rounded field projections

**Class:** isolated failed-point numerical diagnosis, no construction result
**Date:** 2026-09-12

The archived native gradient reproduces exactly in a fresh field and remains
stable after the local-matrix/perturbation checks. D.T*z_native/1e-6 agrees with
the native full VJP within 3.603e-13; using separately accumulated z_batch gives
the original 1.638e-10 failure. Native single-point rows and affine current-field
differences independently pass. The earlier model qualification used native z;
the new search adapter did not. Next qualify a consistent native-covector guard
at all three frozen states, retaining the original failed flag and unchanged
objective, Jacobian, GN matrix and admission limits. See
[point results](../optimization/GN_FAILED_POINT_RESULTS.md).

## F-057 — Natural quadratic flux model predicts all four frozen probe changes

**Class:** independently qualified local model, not a construction result
**Date:** 2026-09-12

At both original and selected119 states the complete batched spatial Jacobian
matches native single-point reference rows within 8.882e-16. The GN model predicts
all four actual change signs and reduces linear-model absolute error by at least
99.907%, exceeding the predeclared 90% test. Missing nonlinear residual curvature
is measured explicitly; this is not a full-Hessian or global-optimizer claim.
A separate NumPy audit recomputes 23 checks without importing the model helper.
Next qualify a classical constrained search using this curvature, then apply
unchanged independent admission. See [results](../optimization/QUADRATIC_FIELD_MODEL_RESULTS.md).

## F-056 — Larger linear-model descents strongly increase the actual flux objective

**Class:** bounded model/physical-value diagnostic with independent derivative gate
**Date:** 2026-09-11

The separately qualified composite gate passes without changing the old failed
FD flag. All four successful bounded LPs pass primal checks; two smaller original-
state models are infeasible. At the selected point only rho=1e-4 gives a small
actual decrease (-7.007e-5 in flux/1e-6); rho=1e-3/1e-2 instead increase it by
0.03378/3.871 despite predicted decreases. Probes are not admitted designs or
replacements for the fixed pilot candidate. Next test the natural quadratic
spatial-field model against every frozen probe before another search. See
[results](../optimization/DIRECT_DESCENT_COMPOSITE_RESULTS.md).

## F-055 — Independent complex steps distinguish an unreliable difference screen

**Class:** retained failed diagnostic followed by independently qualified derivatives
**Date:** 2026-09-11

The new selected-point finite-difference screen fails at 1.207e-6 versus its
1e-6 limit, so no descent probes run. All four failing rows are pair clearances.
Independent Fourier/complex value evaluation then matches all 120 pair directions
at both frozen states, two seeds and three imaginary steps: maximum normalized
discrepancy 2.402e-12 and step disagreement 1.166e-14. Other original rows pass
unchanged. This supports cancellation in the tiny real difference, not a native
gradient defect. The original failure is retained; a separately declared composite
gate is required for new probes. See [results](../optimization/COMPLEX_CLEARANCE_RESULTS.md).

## F-054 — Direct construction passes geometry and native extras, still fails flux

**Class:** preregistered repeated constrained construction and independent rejection
**Date:** 2026-09-11

Both 256-bundle SLSQP arms reproduce exactly, including 715 requests and candidate
selection at proposal 119. No proposal meets the 1e-8 internal selection screen;
the predeclared least-violation fallback is retained. Independent holdout flux
2.330822133e-7 remains 23.308 times above acceptance. Length, continuous curvature
and inter-coil bounds, plasma-distance screen, refined native MSC/arclength
variance and linking-zero screens pass. The terminal proposal has lower flux
but larger violation and is not substituted after seeing results. No converged,
feasible or SoTA baseline. See [results](../optimization/DIRECT_SLSQP_PILOT_RESULTS.md).

## F-053 — Explicit smooth inequalities pass fixed physical derivative qualification

**Class:** preregistered numerical qualification, no optimization or admission
**Date:** 2026-09-11

Both prescribed physical states pass the raw flux/137-inequality map. Full
138-row directional errors at the fixed 1e-8 step are <=5.738e-7 (limit 1e-6);
all steps, including larger coarse-step errors and finest-step cancellation,
are retained. Independent Fourier metrics, every native pair minimum and the
all-16-coil plasma minimum agree; named replay and sampled symmetry checks pass.
Both fields still violate internal inequalities. This qualifies measurements for
a new constrained construction, not feasibility or a method ranking. See
[the result](../optimization/DIRECT_INEQUALITY_QUALIFICATION_RESULTS.md).

## F-052 — Spatial benefit survives equal time, but no candidate is feasible

**Class:** repeated fixed-start time-budget comparison and independent rejection
**Date:** 2026-09-11

Two 300-second runs per representation pass accounting, shared-prefix repetition
and named archive checks. Spatial raw flux is about 2.34–2.35 times lower than
scalar at this budget, but remains 41.461–41.487 times the fixed limit. All four
candidates fail flux; both scalar candidates additionally violate inter-coil
clearance, with explicit sampled witnesses. Spatial geometry bounds pass. This
is neither Pareto dominance nor a feasible or multi-start SoTA baseline. Next
qualify direct inequalities, not a longer unqualified penalty search. See
TIMED_SPATIAL_PILOT_RESULTS.md.

## F-051 — Per-coil analytic contractions preserve the spatial Jacobian at lower cost

**Class:** independent analytic kernel, physical matrix equivalence and repeated timings
**Date:** 2026-09-11

The ideal-filament field/Jacobian can be assembled with sixteen physical-coil
contractions instead of 1024 separate adjoint traversals. Analytic controls and
both fixed physical states pass; maximum normalized Jacobian discrepancy is
8.882e-16. All three repetitions per state are identical, with assembly times
0.304–0.337 s versus about 1.05 s for the previous reference. A report-serialization
failure was retained and corrected before the successful full retry. No physical
candidate improvement follows without a separately evaluated search. See
BATCHED_SPATIAL_JACOBIAN_RESULTS.md.

## F-050 — Spatial residuals improve this fixed-cap search, but still fail flux acceptance

**Class:** controlled repeated representation pilot, independent work audit and rejection
**Date:** 2026-09-11

Both representations repeat exactly at 128 proposals. Every spatial proposal
preserves the scalar objective/gradient; scalar histories exactly reproduce the
old guarded prefix. Spatial common merit is 5.88 times lower and independent raw
flux 2.43 times lower, but wall time is about 20–26 times greater. Both candidates
pass the declared geometry screens, including continuous curvature/clearance
enclosures. Spatial flux still exceeds the fixed acceptance limit by 44.488 times;
both are rejected. No equal-compute or multi-start ranking, Pareto dominance,
feasible baseline or SoTA claim. See SPATIAL_TRF_PILOT_RESULTS.md.

## F-049 — Spatial flux factorization changes the solver model, not the objective

**Class:** algebraic identity, physical Jacobian qualification and independent matrix check
**Date:** 2026-09-11

Replacing aggregated quadratic flux by a norm-scaled spatial residual preserves
the full scalar merit and exact gradient (errors <=2.046e-14) on both fixed fields.
Effective Jacobian ranks increase from 2/3 to 171/204. A closed-form Gram check
identifies the additional positive-semidefinite Gauss-Newton term; this does not
prove better optimization. A single-point analytic VJP implementation matches the
full-point matrices to <=2.221e-16 and takes about 1.05 s rather than 11.1 s in
these measurements. Extra B/VJP work remains explicit. See
SPATIAL_FLUX_FACTORIZATION_RESULTS.md. Candidate quality requires a separate pilot.

## F-048 — Raw optimization arrays are not portable across runtime object ordering

**Class:** failed independent replay, tested mapping correction and archive audit
**Date:** 2026-09-10

SIMSOPT ancestor ordering uses runtime object names. A fresh replay crossed the
9-to-10 curve numbering boundary and assigned archived blocks to different coils.
Original per-context gradient mapping and direct serialized-field holdouts were
not affected. Explicit physical-coil/current-graph mapping restores all 207 DOFs:
eight-bundle replay passes residuals, exact field/current identity and gradient
checks. All 14 earlier saved vectors exactly match their archived named field
parameters. Both failed replay/mapping attempts are retained. Future array-based
warm starts must use a verified physical mapping, not positional assignment.
See REPLAY_MAPPING_REMEDIATION.md and GUARDED_FEASIBILITY_RESULTS.md.

## F-047 — Guarded construction passes geometry screens but not magnetic acceptance

**Class:** preregistered repeated search followed by independent rejection
**Date:** 2026-09-10

Two identical 3000-bundle trust-region runs pass accounting and repeatability.
The candidate passes length/plasma-distance refinement screens and continuous
curvature/inter-coil bounds. Flux 1.017520282e-6 remains 101.752 times the fixed
1e-8 limit. A 99.955% common-merit decrease mostly removes the initially dominant
length penalty, not the magnetic error. The altered objective scaling makes
scalar merits incomparable with prior studies. No feasible or SoTA baseline.
See GUARDED_FEASIBILITY_RESULTS.md.

## F-046 — A continuum curvature enclosure prevents coarse-grid false acceptance

**Class:** analytic interpolation bound, analytical controls and frozen-field qualification
**Date:** 2026-09-10

The interval-wide squared-curvature bound certifies the original warm start's
curvature below 1/m, while both affine candidates remain failed. At N=200 the
L-BFGS-B candidate is correctly unresolved despite subthreshold samples; refinement
finds a violating witness. Final intervals enclose the maximum over every curve
parameter, subject to ordinary floating-point evaluation rather than directed
rounding. This is a qualified acceptance check, not a feasible-design claim.
See CONTINUOUS_CURVATURE_RESULTS.md.

## F-045 — Zero sampled curvature penalty hides real off-grid violations

**Class:** independent geometry rejection with position-only violating witnesses
**Date:** 2026-09-10

Both affine candidates have zero optimizer curvature penalty, with 200-point
maxima below 1/m at reactor scale. Refined maxima are 1.00355069 and 1.03114211/m.
Compiled derivative evaluation and a three-position circumcircle reconstruction
confirm both violations independently of the NumPy Fourier-derivative holdout.
The two finest position-only estimates agree within 4.36e-6 relative and remain
above the hard limit. No tolerance is relaxed. Before larger search budgets,
qualify curvature control between constraint nodes. See CURVATURE_ALIASING_RESULTS.md.

## F-044 — Fixed coordinate scaling enables an actual equal-bundle pilot

**Class:** preregistered repeated optimizer experiment, followed by failed holdout
**Date:** 2026-09-10

Using x=x0+0.01*y, both methods and both repeats consume exactly 1500 full
physical bundles. L-BFGS-B no longer returns immediately; all proposal histories,
values and counters reproduce. The physical-problem identity and ledger audit
passes. AL has lower common merit for this start, but both candidates fail flux,
length and curvature in the independent holdout. Both best proposals occur at
the budget cap: convergence and feasibility remain unproved. No multi-start
ranking or SoTA claim. See AFFINE_FEASIBILITY_RESULTS.md.

## F-043 — A second field-line calculation preserves the finite-pressure findings

**Class:** retrospective independent trace/integration-path comparison
**Date:** 2026-09-10

The hash-pinned Goodman tracer, using B/B^phi for length instead of geometric
derivatives, passes all 84 trace comparisons and 320 radial-family comparisons.
All 319 previously resolved signs survive an enlarged inter-tracer allowance;
the one unresolved family stays unresolved. This supports the bounded F-042
findings without validating the equilibrium or global maximum-J. Fresh extraction
reproduces every finite-pressure metadata/file-hash record, and all 193 unique
referenced path/hash pairs verify. See QI_PRESSURE_TRACE_RESULTS.md.

## F-042 — Individual radial actions resolve a bounded finite-pressure sign change

**Class:** preregistered four-case pilot with retrospective independent quadrature
**Date:** 2026-09-10

All 160 sampled cells match individual wells across radius and resolution; all
320 families pass the numerical refinement screens. nfp2 vacuum has 80 positive
derivatives; its nominal beta=2% counterpart has 80 negative derivatives. nfp3
at this pressure remains mixed (42 negative, 38 positive); vacuum includes one
unresolved family, retained. No alpha averaging or radial pitch retuning is used.
All 13,440 integrals and all derivative classifications survive independent
Gaussian quadrature. The result is restricted to the declared mid-radius domain,
gauge and empirical error allowance, not global maximum-J or SQuID-C readiness.
See QI_RADIAL_ACTION_RESULTS.md.

## F-041 — Finite-pressure QI data were already present but not imported

**Class:** verified archive inventory; correction of an internal data-access gap
**Date:** 2026-09-10

The existing Goodman release contains 31 finite-pressure wouts and matching
inputs. All 62 files now have recorded hashes and observed equilibrium metadata.
All wouts report normal termination, fixed boundary and stellarator symmetry.
Filename beta values are approximate labels, not exact measured beta or author
tolerances; nfp1 has ns=51, the other families ns=201. Our vacuum-only bootstrap
had omitted these files. Finite-pressure action work can proceed without a new
author package, but neither maximum-J nor SQuID-C readiness is established.
See QI_FINITE_BETA_INVENTORY.md.

## F-040 — Continuous inter-coil distance is bounded, but feasibility is still failed

**Class:** retrospective analytical bound supplementing a finite-grid audit
**Date:** 2026-09-10

After three analytical bound test groups, the existing all-pair N=20,000 samples
and Fourier derivative bounds imply continuous reactor-scale centerline lower
bounds of 1.09245264 m (L-BFGS-B) and 1.06131415 m (AL), both above 1.06 m.
This addresses subgrid inter-coil distances for these two exact Fourier systems
in ordinary floating-point arithmetic. Idealized radius-0.035355 m neighborhoods
of distinct device-scale coils have lower gaps 0.03745/0.03437 m. Existing mesh
enclosure, single-coil self-intersection and plasma/structural validity are not
certified. The failed flux and length checks remain unchanged.

The original rejected warm start is now a tracked fixture. Its numeric content
is unchanged (only a final LF added), with exact parent-hash verification. Its
historical producer record had no project commit and a dirty tree; that provenance
gap is disclosed, not retroactively repaired. New experiments no longer depend
on a private ignored artifact path for this starting field.

## F-039 — Normalization alone fails; the improved AL candidate remains infeasible

**Class:** preregistered negative experiment with independent post-search rejection
**Date:** 2026-09-10

The normalized common-vector study reproduces both methods exactly. L-BFGS-B
still terminates after one iteration: its trial merit jumps from 0.5 to 1.38e18,
then returns to the identical start. Thus small absolute scale alone does not
explain F-038. AL uses 752 bundles and yields about fivefold lower holdout flux,
but still misses the 1e-8 flux cut-in and exceeds the 220 m length bound by
0.842 mm. Both candidates are rejected without loosening criteria. No feasible
improvement or method ranking is established. See NORMALIZED_FEASIBILITY_RESULTS.md.

## F-038 — Exact optimization accounting exposes premature numerical convergence

**Class:** repeated real-coil oracle qualification and retained negative optimization result
**Date:** 2026-09-10

Both methods reproduce identical proposal histories in their two repeats. AL
hits the exact 150-bundle cap; L-BFGS-B stops after 10 total bundles (only three
inside its solver). The latter reports convergence after one iteration despite
flux about 110 times above the cut-in: the common squared-vector merit is near
6e-13. Counters, gradient mapping, cache and deterministic repeats pass; neither
method establishes physical feasibility or superiority. A preparation bug that
dropped finite-section regularizations was retained and corrected before the
successful retry. See OPTIMIZATION_ORACLE_RESULTS.md.

## F-037 — Six structured coil meshes pass intrinsic integrity screens

**Class:** preregistered mesh audit with adversarial analytical controls
**Date:** 2026-09-09

Protocol 2c75cc9 preceded implementation 9ee1796 and the six real mesh checks.
All meshes have positive nondegenerate tetrahedra, no repeated/duplicate cells,
consistent shared-face orientations and mean-ratio quality >=0.10. Each of the
four tagged coil boundaries has two triangles per boundary edge, one connected
component and Euler characteristic zero. The three test groups include an
overlapping pair of positive tetrahedra that fails orientation consistency.

This closes a bounded intrinsic-mesh check, **not** spatial nonoverlap or
engineering validity. Nonlocal intersections can pass these tests. Symmetry
copies were not remeshed, and coil/plasma clearances, winding-pack orientation,
physical supports/materials and valid mechanical predictions remain unqualified.
Evidence: mesh-integrity-2026-09-09.json. Full local suite: 78 passed; Ruff clean.

## F-036 — Wider QI coverage exposes an invalid invariant-domain sample

**Class:** preregistered negative screen with retrospective analytical diagnosis
**Date:** 2026-09-09

The expanded five-radius/nine-pitch study passes for nfp2 and nfp3. nfp1 fails
one of its 45 cells: s=0.10, q=0.01 lies below the minimum possible field and
admits no orbit. A Fourier second-derivative interpolation bound confirms this
beyond the sampled grid. The failed screen is retained, not waived. The other
134/135 cells have stable sampled actions and two poloidally closed contour
graphs. The larger action envelopes also show why numerical convergence is not
itself a confinement-quality criterion. Details: QI_COVERAGE_TOPOLOGY_RESULTS.md.

The strict QI integration command additionally passes five non-skipping data
checks after a fresh extraction in a detached clean clone. Neither result closes
the full QI, native-solver integration, engineering or SQuID-C readiness gates.

## F-035 — Independent geometric tracing agrees on the frozen QI sample

**Class:** independent reconstruction cross-check of the same equilibrium data
**Date:** 2026-09-09

Protocol 399a8fa preceded implementation fc435e3 and the 27 real-data checks.
The new Newton/geometry-based tracer agrees with the published root/magnetic
arc-length tracer for every tested pitch. Finest maximum relative action
differences are 6.2645e-6, 3.8171e-6 and 9.0674e-6, below the frozen 1e-3 limit.
All coordinate, B, cumulative-length, well-count and coverage screens pass.

This supplies an independent tracing check for F-034's bounded measurement
study. It does not validate the source equilibrium, QI contour topology or
finite-pressure maximum-J. See QI_TRACE_CROSSCHECK_RESULTS.md.

## F-034 — Well-resolved bounce-action measurement passes its first frozen study

**Class:** reproduced numerical qualification with independent quadrature
**Date:** 2026-09-09

Protocol 75c0ba8 preceded implementation 372a63f and all real-data runs. The
nfp=1,2,3 cases pass the specified phi/alpha/domain-length refinements and
complete-well coverage screens. The largest final phi action change is 1.0836e-4
relative, below the fixed 1e-3 limit. Independent quadrature verifies 12,960
recorded well integrals with maximum relative discrepancy below 5.5e-10.

This qualifies a bounded measurement study, not QI topology or maximum-J.
Definitions, analytic checks, results and open limitations are in
QI_MEASUREMENT_RESULTS_V1.md. The full scientific qualification remains open.

## F-001 — Host platform is resource-capable but compatibility-sensitive

**Class:** reproduced
**Date:** 2026-08-30

The host is an Apple M1 (`arm64`) with 8 logical CPUs, 16 GiB RAM, macOS 15.7.4,
Python 3.11.4, `uv`, and CMake. Docker, Conda, MPI, and Git LFS were not found on
`PATH` during the initial probe.

**Implication:** native ARM compatibility must be tested before choosing the
canonical environment. Linux/x86 containers or remote HPC may eventually be
needed for selected solvers, but this is not assumed in advance.

## F-002 — StellCoilBench does not currently supply a SQuID-C/QI target surface

**Class:** literature/repository inspection
**Date:** 2026-08-30

The public `plasma_surfaces` directory currently lists NCSX, HSX, Landreman-Paul
QA/QH, W7-X, CFQS, a circular tokamak, a rotating ellipse, MUSE, and another NFP=2
surface. No SQuID-C surface is listed.

Source: <https://github.com/akaptano/stellcoilbench/tree/main/plasma_surfaces>

## F-003 — A publication alone is not yet an authoritative SQuID-C data package

**Class:** literature/repository inspection
**Date:** 2026-08-30

The open SQuID-C paper describes a coil-compatible finite-beta QI equilibrium and
reports central physics and coil metrics, but no linked machine-readable package
containing the complete VMEC input/output, profiles, coils, currents, and run
configuration was identified during the initial search.

Source: <https://doi.org/10.1017/S0022377825100974>

**Implication:** do not reconstruct SQuID-C from figures. Request or locate the
authoritative files while developing against the three-part baseline suite.

## F-004 — SIMSOPT is native on Apple ARM after an SDK include-path correction

**Class:** reproduced
**Date:** 2026-08-30

The pinned SIMSOPT commit `a79006b0bc1e6df8ab48de284e3457d39a49b995`
compiled for `macOS arm64`. The first build failed because an incomplete libc++
header directory in the Command Line Tools shadowed the complete headers in the
active SDK (`cstddef`, `iostream`, and `algorithm` were not found). Prepending
`$(xcrun --show-sdk-path)/usr/include/c++/v1` fixed the build without modifying
SIMSOPT.

**Verification:** 31 upstream Biot-Savart/curve-objective tests and 86 subtests
passed. These include Taylor tests, derivative identities, convergence, symmetry,
and divergence-free checks.

## F-005 — MPI is an import-time dependency of the current benchmark stack

**Class:** reproduced
**Date:** 2026-08-30

Installing `mpi4py` alone was insufficient: importing `simsopt.field` failed
because no `libmpi` was available. Installing OpenMPI 5.0.10 resolved the failure,
after which serial Biot-Savart evaluation and both StellCoilBench case validators
ran successfully.

**Implication:** OpenMPI is part of the canonical environment even for one-process
coil optimization.

## F-006 — The basic Landreman-Paul QA result is deterministic but not Pareto-strong

**Class:** reproduced and cross-checked
**Date:** 2026-08-30

Two independent invocations of the pinned `basic_LandremanPaulQA.yaml` case gave
bit-identical reported scientific metrics and 2,512 function/gradient evaluations.
Wall time changed from 160.55 s to 158.60 s. Principal results were:

- final squared flux: `1.1470641716587582e-06`;
- average `|B·n|/|B|`: `4.420509357430533e-04`;
- reactor-scale coil-surface and coil-coil separations: 2.855 m and 1.060 m;
- reactor-scale total coil length: 242.400 m;
- maximum turns per coil: 488.

StellCoilBench's hard feasibility check passes. Its soft length bound (220 m) and
turn-count bound (300) fail. The separate post-processing path obtained
`4.470778891115039e-04` for average `|B·n|/|B|`, a 1.14% relative difference from
the optimizer report. The composite score is 1.5926, below 2,365 of 4,684 scored
Landreman-Paul QA entries in the pinned leaderboard.

**Implication:** driving filamentary flux error lower is not the promising
research direction by itself. A relevant contribution must move the engineering
Pareto frontier, especially length/current/turns/force/finite-build trade-offs.

## F-007 — `run-case` does not create a self-contained post-processing bundle

**Class:** reproduced
**Date:** 2026-08-30

The upstream `run-case` optimization succeeded, but its automatic post-processing
could not locate a case YAML beside the generated coil JSON. Our wrapper now
copies the exact case and target surface into each run directory and hashes both.
With that bundle, the same post-processing completed.

## F-008 — The W7-X coil baseline is feasible but stops on engineering margins

**Class:** reproduced
**Date:** 2026-08-30

The pinned `basic_W7X.yaml` continuation reached Fourier order 8 and stopped at
the 1,000-iteration limit. Its average normal-field error is 0.297 %, while an
independent post-processing pass gives 0.301 %. Hard feasibility passes, but the
reactor-scale coil-surface clearance (1.115 m), maximum curvature (1.0001 1/m),
arclength-uniformity metric, and 516-turn maximum violate soft targets. The
reactor-scale total coil length is 145.90 m.

**Implication:** normal-field error alone again does not identify the strongest
design. Current/turn count, finite-build clearance, curvature and force belong in
the primary Pareto comparison.

## F-009 — W7-X VMEC++ is locally converged, but full cross-code V&V is not

**Class:** reproduced with partial cross-validation
**Date:** 2026-08-30

VMEC++ 0.7.3 converged on the exact StellCoilBench W7-X input at `ns=201` in
264.3 s. Aspect ratio, volume, total beta and the iota profile agree with the
available Fortran reference to absolute differences of approximately
`2.6e-13`, `1.5e-13`, `5.3e-13`, and `1.4e-8`, respectively. However, only 47 of
59 fields pass the current pinned Proxima fixed-boundary V&V tolerances. The
failures include several half-grid and axis-derived quantities.

**Implication:** the equilibrium is a useful protected-metric regression, but it
must not be called a complete independent validation. This initial comparison is
superseded, but not erased, by the version-compatible investigation in F-031.

## F-010 — The open QI bridge has authoritative inputs, outputs and metric code

**Class:** reproduced provenance
**Date:** 2026-08-30

Zenodo record 7220257 contains the three vacuum `nfp=1,2,3` VMEC inputs and
outputs, edge Boozer transforms, source metric routines, finite-beta scans, and
published neoclassical/particle outputs. The 1,057,077,931-byte archive passed
both its published MD5 (`f6983a41403da28247025be631522caa`) and a full ZIP CRC
test. Only the required 16 MB subset is extracted.

Source: <https://doi.org/10.5281/zenodo.7220257>

## F-011 — The published QI target is reproducible but numerically fragile

**Class:** reproduced
**Date:** 2026-08-30

Executing the unmodified published `QuasiIsodynamicResidual1` against the
published edge Boozer transforms gives objective values `2.5725e-5`, `2.7451e-5`
and `7.0527e-5` for `nfp=1,2,3`. All are finite. SciPy nevertheless warns that the
smoothing spline used in the inverse-square well weighting does not always reach
its requested smoothing residual.

**Implication:** preserve this objective as a legacy regression, while developing
a numerically regularized and resolution-tested QI metric before using it to
rank new designs.

## F-012 — Vacuum QI is not the same as maximum-J

**Class:** reproduced and literature-consistent
**Date:** 2026-08-30

The published second-adiabatic-invariant routine gives maximum-J slope fractions
of 0.0, 0.0 and 0.1 for the three vacuum cases at the recorded screening
resolution. This agrees with the paper's statement that known vacuum cases are
minimum-J and that these configurations become maximum-J only at sufficient
finite beta.

Source: <https://arxiv.org/abs/2211.09829>

**Implication:** a vacuum QI objective cannot stand in for the finite-beta
maximum-J and turbulence physics relevant to SQuID-C.

## F-013 — SQuID-C's published coil design leaves a credible hard-constraint gap

**Class:** literature and inferred research direction
**Date:** 2026-08-30

The SQuID-C paper reports average and maximum relative normal-field errors of
0.27 % and 1.2 %, five modular coil types, and normalized per-type geometry in its
Table 1. It also states that coil optimization began with field error, added
geometric penalties as the solution matured, and enforced no firm constraints.
The authors explicitly flag coil complexity and improved magnetic-gradient scale
length as future concerns.

Source: <https://doi.org/10.1017/S0022377825100974>

**Implication (hypothesis):** the most promising first contribution is a robust,
hard-constrained coil Pareto improvement—finite build, current/turns, clearance,
curvature and loading—while protecting the coil-generated finite-beta QI physics.
This is testable on W7-X and the open QI suite before authoritative SQuID-C files
arrive.

## F-014 — The default coil grid is not a safe geometry holdout

**Class:** reproduced and independently calculated
**Date:** 2026-08-30

Direct Fourier differentiation of the accepted W7-X coils reproduces the reported
lengths to floating-point precision. Increasing the sampling from 200 to 20,000
points changes maximum curvature from `3.24412` to `3.26161 1/m`, a 0.54 %
underestimate at benchmark resolution. The sampled minimum coil-coil distance
decreases from `0.239019` to `0.237633 m`, so the coarse metric overestimates
clearance by 0.58 %. The sampled coil-surface distance similarly decreases from
`0.343595 m` in the optimizer report to approximately `0.342193 m` in the
independent high-resolution audit.

**Implication:** optimization-resolution clearance and curvature cannot certify a
new result. A frozen high-resolution geometry audit is now a mandatory holdout and
may itself change leaderboard ordering near constraints.

## F-015 — The legacy QI objective is not resolution-converged

**Class:** reproduced negative result
**Date:** 2026-08-30

For the published `nfp=1` case, simultaneous refinement from
`(nphi,nalpha,nBj,nphiout)=(301,37,201,1000)` through the published default to
`(801,100,601,3000)` gives objective values `1.3850e-5`, `2.5725e-5`, and
`1.8097e-5`. The sequence is strongly non-monotone and the spline warnings remain.

**Implication:** exact reproduction is useful as a software regression, but this
objective is not admissible as the sole ranking function for new QI designs. A
regularized definition needs independent convergence and physics checks first.

## F-016 — Published transport-screening data pass the generic intake path

**Class:** reproduced data ingestion, not solver reproduction
**Date:** 2026-08-30

The published NEO outputs give median epsilon-effective to the three-halves power
of `6.54e-6`, `1.20e-5`, and `7.83e-6` for `nfp=1,2,3`. The corresponding
published SIMPLE 5,000-particle files give final 0.2 s loss fractions of
approximately 0, 0.36%, and 0.38%. These values were recomputed from the raw text
outputs with the same transformations used by the published plotting script.

**Implication:** the file interfaces and summarization semantics are established.
NEO and SIMPLE themselves have not yet been installed and rerun, so this is not
an independent transport validation.

## F-017 — VMEC++ convergence is stable but not bit-deterministic on this host

**Class:** reproduced
**Date:** 2026-08-30

Two runs of the identical Goodman `nfp=2` input both converged below the force
residual target. Aspect ratio and volume were identical, while axis iota differed
by `2.70e-8`, edge iota by `3.71e-10`, and iteration counts were 5,605 versus
5,677. The serialized NetCDF hashes differ.

**Implication:** equilibrium regressions use declared physical tolerances, not
file-hash identity. Hashes remain provenance identifiers only.

## F-018 — LPQA geometry is even more sensitive to coarse clearance sampling

**Class:** reproduced and independently calculated
**Date:** 2026-08-30

For the accepted LPQA baseline, the 200-point coil-coil distance is `0.104995 m`;
global candidate search at 1,000 points followed by 20,000-point refinement gives
`0.103528 m`, 1.40% lower. The optimizer-reported coil-surface distance is
`0.282696 m`, versus `0.281607 m` on the 512-by-512 surface holdout. Maximum
curvature changes only from `4.72380` to `4.72639 1/m`.

**Implication:** the clearance bias is not W7-X-specific and can cross a hard
constraint. High-resolution reevaluation must happen outside the optimizer.

## F-019 — Stock augmented-Lagrangian evaluation accounting is not comparable

**Class:** source inspection, pending run characterization
**Date:** 2026-08-30

In the pinned stack, StellCoilBench passes `max_iterations` to SIMSOPT as the
inner SciPy `MAXITER` and `max_iter_subopt` as the outer `MAXITER_lag`, despite
the wrapper documentation describing the reverse. It then records
`optimization_nfev = max_iterations` without using the inner solvers' actual
`nfev`. Taylor-test and between-step evaluations are also omitted.

**Implication:** published stock fields cannot support an equal-evaluation-budget
claim for L-BFGS-B versus augmented Lagrangian. Our runner now records actual
inner SciPy counters and labels their exclusions; a globally budget-stopping
counter is required before the headline comparison.

## F-020 — The frozen manufacturing screen separates nominal accuracy and tolerance

**Class:** reproduced screening result
**Date:** 2026-08-30

With a 1 m reactor-scale GP correlation length, 100 common-random-number samples
per amplitude, and the 95th-percentile factor-two rule, both baseline intervals
are validly bracketed. LPQA gives `sigma*=9.066 mm`; W7-X gives `20.372 mm`.
Lower and upper endpoint percentile ratios are `1.002/29.02` and `1.000/6.85`,
respectively. The effective optimization flux threshold `1e-8` is read from each
immutable result record after discovering that the upstream sensitivity YAML
lookup silently selected zero.

**Implication:** nominal field accuracy and tolerance sensitivity are distinct
axes: the much lower-error LPQA result has the smaller factor-two tolerance. The
cross-case ratio is not itself a superiority claim because the degradation is
normalized by different nominal errors and the configurations have different
numbers of physical coil copies. Within-case robust Pareto comparisons are now
well-defined; accepted claims require the 1,000-sample holdout.

## F-021 — The open QI case runs through a real fast-particle solver

**Class:** reproduced smoke-scale solver execution
**Date:** 2026-08-30

Pinned SIMPLE commit `9269e861...` with pinned libneo builds deterministically on
Apple ARM after explicit Homebrew OpenMP and NetCDF paths. Seven upstream smoke
tests pass. Two runs using the exact Goodman `nfp=1` vacuum wout, scaled to
effective minor radius 1.7 m and axis field 5.7 T, produced bit-identical
`confined_fraction.dat`. All 128 isotropic alpha particles initialized at
`s=0.25` were resolved and none was lost by 0.01 s.

**Implication:** the VMEC-to-SIMPLE interface and orbit solver are operational and
deterministic at smoke scale. This does not reproduce the paper's 5,000-particle,
0.2 s statistic; production protocol, current-versus-2022 code sensitivity, and
statistical uncertainty remain required.

## F-022 — No order-4 engineering screening candidate is yet feasible

**Class:** reproduced negative result
**Date:** 2026-08-30

Five LPQA screening runs were reevaluated against a common physical acceptance
set and the independent geometry holdout. None satisfies every condition. The
buffered L-BFGS-B candidate satisfies length, refined clearances, and refined
curvature, but its squared flux is `1.10e-6`, above the declared `1e-8` cut-in.
The longest augmented-Lagrangian run reduces squared flux to `3.98e-7` after
1,665 recorded inner SciPy evaluations, but exceeds 220 m length and its refined
reactor-scale maximum curvature is `1.000036 1/m`.

**Implication:** these runs characterize the constrained landscape and audit
path; none is a publishable classical baseline or an improvement. Higher Fourier
order/continuation and a genuine convergence/budget controller are still needed.

## F-023 — Optimizer completion is not a feasibility certificate

**Class:** source inspection and reproduced counterexample
**Date:** 2026-08-30

The three augmented-Lagrangian screens are labelled `optimization_success=true`
by the stock result builder because the solver result is discarded and `None` is
mapped to `Completed`. This remains true when the outer cap is reached with
nonzero violations. The stock `optimization_nfev=100` also disagrees with the
instrumented inner totals of 370, 668, and 1,665.

**Implication:** acceptance is computed from serialized-coil metrics and holdouts,
never from the wrapper's success field. Equal-budget method claims remain blocked
until all high-fidelity evaluations are counted and a global stop is enforced.

## F-024 — The local neoclassical path works but does not reproduce the paper

**Class:** reproduced solver execution with failed cross-check
**Date:** 2026-08-30

Pinned NEO-JAX 1.0.1 and `booz_xform` 0.1.0 successfully compute finite
`epsilon_eff^(3/2)` on 16 surfaces of the published Goodman nfp=1 equilibrium,
without rational-surface fallback. A radial Boozer file had to be regenerated
because the release contains only an edge Boozer transform. At default settings,
the calculated-to-published ratio has median 3.27 and maximum relative error
797%. At the surface nearest `s=0.21875`, refinement from the low to high and
ultra settings changes the value from `1.238e-5` to `7.841e-6` and `7.773e-6`;
the published value is `2.381e-6`.

**Implication:** the local VMEC-to-Boozer-to-neoclassical interface is exercised,
but paper reproduction fails and cannot be repaired by the tested resolution
increase alone. The missing original radial Boozer file and NEO control deck are
now explicit provenance blockers; no transport-accuracy claim is made.

## F-025 — The W7-X-target coil field has a deterministic Poincare regression

**Class:** reproduced and cross-fidelity checked
**Date:** 2026-08-30

Six field lines from the serialized order-8 W7-X-target coil solution were traced
to four sections per field period for `tmax=2000`. Two interpolated-field repeats
and two direct Biot-Savart repeats are internally bit-identical. Every line remains
inside the boundary stopping surface and supplies at least 130 hits per section.
Interpolated and direct paths give identical hit counts; their section-extrema
differ by at most 4.72 mm, on the outermost sampled line. The inexpensive
interpolant takes 0.26 s after setup versus 80.6 s for direct tracing.

**Implication:** coil-field topology now has a numerical regression in addition
to a plot, with a direct-field holdout. It validates the serialized optimized
filament field and software path, not the authoritative as-built W7-X coils, and
the diagnostic section-angle iota fit is not promoted to an equilibrium metric.

## F-026 — The stock finite-build fallback fails on a real LPQA candidate

**Class:** reproduced failure plus independent geometric holdout
**Date:** 2026-08-31

StellCoilBench's Gmsh fallback passed its selected upstream unit tests but could
not mesh any of the four unique coils of the serialized LPQA engineering
candidate at `h=0.05 m`. The OCC route reported intersecting/overlapping facets,
and the STL route reported an invalid exterior boundary. Source inspection shows
that its nominally rotation-minimizing cross-section frame is actually
reconstructed from a fixed z reference at every point and can be discontinuous
near reference-axis alignment.

An independent periodic parallel-transport sweep produced six mesh levels from
`h=0.05 m` to `0.01 m`, preserving four nonempty physical tags with no zero or
nonfinite tetrahedron volumes. At the finest level the total volume differs from
centerline length times area by `0.0290%`; the two finest volumes differ by
`0.00990%`.

**Implication:** the explicit structured representation passes the frozen
finite-build screen, while the pinned upstream Gmsh path is not qualified for
real optimization outputs. Synthetic meshing tests alone would have produced a
false sense of readiness.

## F-027 — Structural convergence exposes an invalid physical regime

**Class:** predeclared failed test followed by predeclared diagnostic extension
**Date:** 2026-08-31

The frozen `0.03 -> 0.02 m` P1 scikit-fem comparison failed all four 10%
convergence limits: maximum/mean displacement changed by `22.8%/24.9%`, and
p95/mean Von Mises stress by `14.6%/14.7%`. The subsequently declared
`0.015 -> 0.010 m` extension passed at `8.75%`, `9.03%`, `4.41%`, and `4.08%`,
respectively. Repeating the finest solve produced bit-identical acceptance
metrics.

The converged trend is not an absolute engineering prediction. The scikit-fem
backend fixes the lowest 15% of each coil in z even when the upstream driver
labels the configuration as a spring foundation. More decisively, it predicts
`0.978 m` maximum displacement for a `0.05 m` winding-pack width, far outside
the small-deformation regime of linear elasticity. Maximum element stress also
continues upward to `22.3 GPa` and is excluded from the convergence gate.

**Implication:** the load-to-FEM pipeline is deterministic and has an extended
mesh-convergence record, but its absolute displacement/stress values must not be
optimized or cited as reactor limits. Near-term engineering optimization should
use electromagnetic force/load proxies while a geometrically nonlinear,
support-aware, independently cross-checked structural model is developed.

## F-028 — The first immutable free-boundary holdout passes in vacuum

**Class:** predeclared pipeline qualification with response-grid holdout
**Date:** 2026-08-31

The serialized LPQA v1.1 L-BFGS-B coils were exported as one current circuit and
evaluated by VMEC++ 0.7.3 without optimizer writeback. The toroidal flux was
independently obtained from the Biot-Savart vector-potential line integral. Both
the `mpol=6`, `ntor=6`, `ns=31` fixed-boundary reference and the free-boundary
vacuum equilibrium reached the requested `1e-9` force-residual tolerance.

On the standard `101 x 101 x 24` response grid, the free-boundary volume differs
from the truncated target by `0.0266%`, the magnetic-axis R curve differs from
the fixed reference by `0.0383%` RMS, and boundary cross-section RMS distances
at the two frozen toroidal sections are `1.04%` and `0.686%` of the target
minor-radius proxies. Every predeclared screen passes.

Refining the response grid to `151 x 151 x 24` changes volume, aspect, axis iota,
and edge iota by `0.00735%`, `0.00290%`, `0.0956%`, and `0.00961%`. The normalized
cross-section errors change by `0.000411` and `0.000386`, also within the frozen
limits.

**Implication:** free-boundary validation is now operational and strictly
separate from optimization. This is not an improvement claim: the input
candidate still fails the magnetic squared-flux cut-in, and this first run is
vacuum-only at reduced Fourier/radial resolution. A publishable candidate must
repeat the holdout at converged VMEC resolution and finite pressure/current,
including topology and an independent code/version check.

## F-029 — Equilibrium intake no longer requires case-specific code

**Class:** tested generic interface plus real-data transfer control
**Date:** 2026-08-31

A core manifest-to-NetCDF adapter now validates hashes and conventions, extracts
VMEC geometry/physics metadata, checks declared versus actual
`nfp/mpol/ntor/ns/free_boundary`, and optionally summarizes a Boozer transform.
It contains no `case_id`, Goodman, or field-period dispatch. A synthetic unknown
configuration test passes in core CI. The same CLI then ingested the published
Goodman nfp=1 and nfp=2 equilibria from two data-only manifests; all declared
metadata matched in both cases.

**Implication:** a SQuID-C equilibrium/Boozer pair can enter the validation stack
by adding files and a manifest, without changing Python code. Paper-specific
metric reproduction can still require a versioned adapter when the publication
defines a unique objective; that is kept separate from generic intake.

## F-030 — No publicly identified authoritative SQuID-C package was located

**Class:** reproducible bounded primary-source availability audit
**Date:** 2026-08-31

The publisher page exposes an empty `supplementaryMaterials` list, and Crossref
records no DOI relations. Exact Zenodo searches by configuration name, article
DOI, and title returned zero records; DataCite searches by related DOI and title
also returned zero. All 4,035 paths in all nine public Proxima Fusion GitHub
repositories were checked from complete recursive trees without a SQuID-C name
match.

Proxima's four public Hugging Face datasets required an additional check because
ConStellaration and CoilStellaration are directly relevant. All 7,668 repository
paths were checked at recorded revisions without a name match. CoilStellaration's
179-column results schema links to a ConStellaration boundary only by an opaque
ID and exposes no human paper, DOI, citation, or source column. Its multi-gigabyte
row payloads were not exhaustively searched, so an anonymous row cannot be ruled
out—but it also could not serve as an authoritative SQuID-C baseline without a
publisher/author mapping.

**Verification:** `scripts/audit_squid_c_availability.py` reruns the APIs and
publisher metadata checks. The dated evidence records endpoint-response hashes,
repository/dataset revisions, pagination coverage, search limitations, and the
six still-missing artifact classes.

**Implication:** the external SQuID-C intake blocker is now documented rather
than inferred from a general web search. We should request the fixed- and
free-boundary VMEC cases, profiles, coil/current data, MGRID recipe, scale, and
paper run settings from the authors; figures or anonymous dataset rows are not
acceptable substitutes. This does not close the separate internal W7-X V&V and
CI gates.

## F-031 — A matched VMEC 8.52 reference closes the scoped W7-X physics gate

**Audit correction, 2026-09-09:** the real-space tolerance class below was wrong;
the corrected fixed-boundary margin is 16.77x. The expanded local comparison is
60/63, not full-file V&V. The variable selection and grid were retrospective.
See AUDIT_2026-09-09.md and the new dated evidence. Historical text follows.

**Class:** independent implementation reproduction with retained negative controls
**Date:** 2026-08-31

A native STELLOPT `v251`/VMEC 8.52 executable was built from pinned source with
the two patches specified by Proxima's validation repository and one documented
GNU Fortran 16 compatibility change. It completed the exact StellCoilBench W7-X
input normally in 2,922.57 seconds. VMEC++ and VMEC 8.52 both took 3,708 final
iterations and reached the requested `1e-12` force-residual level. Aspect, volume,
beta, iota, magnetic axis, Fourier geometry, and protected magnetic coefficients
pass the pinned comparison tolerances.

Independent real-space reconstruction on the `73 x 72` holdout grid has maximum
normalized differences `3.85e-10` and `1.93e-9` for R and Z, and between
`6.55e-10` and `5.96e-9` for the three cylindrical B components. All are more
than 8,000 times inside the upstream W7-X-class tolerances.

The result is not a full-file pass: 56/59 fields pass. `chipf` differs only at
the axis because the current VMEC++ assembly leaves that element zero; its
interior maximum normalized difference is `2.28e-9`, within the `1e-8`
fixed-boundary tolerance. `presf` and `pres` differ by less than `7.5e-6 Pa`
absolute and `2.7e-11` relative to their L-infinity scale, but still miss the
upstream bit-near array tolerances. No exception is deleted from the evidence.

The older VMEC 9.0 comparison's broad `bsubsmns` failure disappears: the matched
8.52 maximum absolute coefficient difference is `2.10e-8`. This identifies
version/output semantics—not a discrepant reconstructed physical B field—as the
cause of the prior alarming result.

**Implication:** WP2's declared physics regression gate is closed without claiming
full `wout` equivalence. The remaining three output-level warnings should be
reported upstream and retained as regression tests, but they do not block
SQuID-C equilibrium intake.

## F-032 — The first SQuID-C template was structurally under-specified

**Audit correction, 2026-09-09:** the implication that no adapter changes remain
is withdrawn. Empty metrics and failed solver outputs could pass; scientific
admission was not implemented. The revised code and readiness gates distinguish
basic intake from scientific reproduction. Historical text follows.

**Class:** failed contract audit followed by tested schema hardening
**Date:** 2026-08-31

The schema-1 template listed the expected artifacts, but the executable validator
would have admitted `kind=squid_c` with only one VMEC input or output. It did not
require separate fixed- and free-boundary states, MGRID construction, solver
controls, physical scale, symmetry expansion, file sizes, authoritative origin,
or derivation lineage. Thus the prose contract was stronger than the code.

Schema 2 now makes all ten artifact roles mandatory, rejects duplicate roles and
template placeholders, verifies byte sizes and SHA-256 hashes, distinguishes
authoritative files from locally derived files, validates every declared parent
role, and binds both equilibria to code/version/resolution/convergence metadata.
A complete synthetic SQuID-C package passes the contract and both equilibrium
states enter the generic intake. Missing MGRID, wrong byte size, and an undeclared
lineage parent each fail dedicated tests. The core suite now has 13 passing tests.

The paper-level values were rechecked against the publisher text: the coil design
targets 2% volume-averaged beta including the plasma-current background; the
canonical reported state uses `p(s) proportional to 1-s` and includes coil ripple;
and the reported mean/maximum relative field errors are 0.27%/1.2%.

**Implication:** once an authoritative package is supplied, no schema or intake
code change is needed. G6's raw/derived hashes remain correctly open because
inventing them from the publication would defeat the contract.

## F-033 — The first green core-CI run depended on an ignored checkout

**Audit correction, 2026-09-09:** the main-branch clone passed, but a detached
checkout failed because a test assumed branch=main. That test is corrected,
detached HEAD is tested explicitly, and the workflow now pins uv 0.11.2.

**Class:** failed clean-room holdout followed by reproduced remediation
**Date:** 2026-08-31

The locked CI command initially passed in the working repository but failed in a
fresh clone before collecting tests. Although the benchmark extra was not
selected, lock validation still attempted to read the optional editable source
at `external/stellcoilbench`; that ignored checkout existed only in the working
repository. `--no-install-local` did not help because metadata were required
before installation selection.

The optional source is now the exact StellCoilBench Git commit
`c7949edc4ea6378fc3be633304c69c288c3b79b5` rather than a local path. The separate
checkout at the same commit remains the pinned source/data audit tree. A second
fresh clone—with neither `external/` nor an existing virtual environment—resolved
the lock, installed the core package, passed Ruff and all 13 tests, and left the
clone clean.

**Implication:** the core workflow is clean-checkout reproducible. A hosted run is
still unwitnessed because no remote is configured, but that is now an operational
publication step rather than a hidden dependency in the scientific intake path.
