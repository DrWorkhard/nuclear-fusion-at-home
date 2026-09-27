# Near-term research programme

Updated 27 September 2026. [Status](../STATUS.md) · [Step 4](../steps/STEP_4_PLASMA_AND_COILS.md)

## Focus

Use the method that moves field error: penalized normalized coil fitting.
The matched restart reaches **0.004889 with scoped geometry checks**, below the
1e-2 exploratory signal but above the unchanged 1e-4 acceptance limit.
Seven exploration sessions are complete; a failed startup and its diagnosis
remain included in the evidence, not erased from effort.

## Next work

1. Repair the [interior-field screen](INTERIOR_FIELD_EXPLORATION.md)'s exact-flux
   intake mismatch, then run its five fixed candidates. Keep both favorable and
   unfavorable results.
2. Map field error against clearance, curvature, current and coil complexity
   using longer penalized fits, wider justified ranges and the existing
   eight-coil family as a separately labelled comparison.
3. Freeze the best two or three candidates, then use the shared trusted field
   and continuous-geometry checks. Investigate realized-field topology and
   matched realization of the Step 3 target before claiming benefit transfer.

Exploration needs one short record: script/input/output identities, question,
wall-clock/resource ceiling and conclusion. Do not add arbitrary evaluation or
coefficient caps; retain them when needed for a particular matched experiment.
Past studies retain their original rules. No routine full historical regression,
new orchestration framework or separately written checker for every script.

By **24 October 2026**, review the reachability/trade-off map. The 1e-2 signal now
supports further local fitting; it does not promise success. If progress stalls,
change family/target rather than automatically extend a failed method.

## MS0 and community value

Target **26 March 2027**: a useful attributed open coil challenge with calibrated
gate interpretation, positive/negative controls and separate-machine reproduction.
First assess contributing the Goodman case and checked coils to an existing
benchmark such as StellCoilBench. Build only missing adapters, not a parallel
benchmark platform by default.

Near-term contributions: metric crosswalks, portable target/coil exports,
independent checks and replications. Unsolicited approaches remain welcome.
Hosting, publication, external contact and a backup destination still require
the owner's authority. No such external action has occurred.

Pressure, engineering and SQuID-C work are parked until an actual coil set is
within ten times the field-error limit, unless evidence justifies revisiting them.
They remain required for eventual completion; detailed historical plans are at
the [freeze tag](../validation/REPRODUCING_RESULTS.md). Proxima contact waits for MS1.
