# Conditional circular-envelope scale screen

Question: can two finite-envelope separation requirements reject scaled copies
of the latest trial 427 coils before reactor-oriented optimization? Clean
producer/evaluator: `532f3b72302ecb75a857072beae1816cbdbee4de`. The original
geometry producer is `56fd845f2ff84553092ac1690aa430283e14acdf`, archive
`8a200dae194fc972ee535ad8532525aa17aff749`. Exact original arm, frozen selection
and boundary input are in `inputs/`; configuration, command, checks, prelaunch
review and process exit are in `metadata/`. No new geometry or field solve occurs.

Use length multiplier λ, field multiplier κ and ampere-turns |I0| λκ. Model a
circular winding cross-section with radius sqrt(|I0| λκ/(π J)), plus fixed casing
allowance c and casing-to-plasma gap g. The 108 cases span λ=6,8,10,12; κ=4,6,8;
J=112,120,124 A/mm²; c=0,0.05,0.10 m; g=1.04 m. See the prospective source page
for definitions and limitations. These quantities are assumptions for this
screen, not transferred engineering qualification or universal requirements.

A single calculation completed in 0.0334 s of 30 s, exit0: 45 cases are excluded,
12 unresolved and 51 clear only the two separation checks. Every λ=6 case is
excluded. With κ=6, J=120 A/mm² and c=0.05 m, λ=8 is excluded and λ=10 clears
both checks; the bounded transition is 8.1983–9.4177. At λ=10 that scenario
requires 18.4719 MA equivalent excitation per coil and has a 0.22136 m winding
radius before its casing. Its lower plasma margin is 0.07413 m and lower
inter-coil margin 0.12624 m. All 108 currents exceed the unchanged pilot cap.

The model uses saved padded-floating-point lower bounds and sampled upper
bounds, not interval proofs. A failed lower bound alone is not exclusion.
Scaling the filament model leaves its failed normalized RMS unchanged; finite
winding-pack fields are untested. Coil self-overlap, supports/access, attainable
current density/peak field, neutronics, stresses, confinement, exhaust and net
power remain unqualified. No operating point, reactor feasibility or physical
acceptance is established. Supplement future design decisions with finite-build
constraints; do not relax existing gates or declare all compact reactors excluded.

The one raw result file and all copied inputs retain their original bytes.
The manifest hashes all payload files except itself; scoped attributes preserve
checkout bytes. The completed script and eight analytic tests resolve in this
archive parent. The cited Stellaris Table8 paper is retained separately at
`/private/tmp/issue27-stellaris-paper-v1.pdf`, SHA256
`7fd72c1242ce3a17a9c4b9a4597fcb9ff5296b942b2d8343a0b463539d8d3865`.
Its title/DOI/primary URL are in the configuration; it is not copied into this
archive. Replay uses the cited scalar assumptions, not PDF text. Original raw
outputs and native environments remain intact. This snapshot is local only.

With Python 3.11+ (standard library only), use a fresh output path:

```sh
python -I -S evidence/issue27-envelope-v1/replay.py --root . --output /tmp/envelope-replay.json
```

Replay verifies manifest/input/source identities, reconstructs the saved bounds,
and independently repeats all 108 cases with 50-digit Decimal arithmetic. It
checks both margins, classifications and critical scales. It does not recompute
geometry, validate the literature's physics or re-attest historical timing.
Agent review is not external physics peer review.
